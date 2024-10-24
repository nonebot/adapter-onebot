"""OneBot v12 适配器。

FrontMatter:
    sidebar_position: 1
    description: onebot.v12.adapter 模块
"""

import json
import asyncio
import inspect
import contextlib
from collections.abc import Generator
from typing_extensions import override
from typing import Any, Union, Callable, ClassVar, Optional, cast

import msgpack
from pygtrie import CharTrie
from nonebot.utils import escape_tag
from nonebot.exception import WebSocketClosed
from nonebot.compat import type_validate_python
from nonebot.drivers import (
    URL,
    Driver,
    Request,
    Response,
    ASGIMixin,
    WebSocket,
    HTTPClientMixin,
    HTTPServerSetup,
    WebSocketClientMixin,
    WebSocketServerSetup,
)

from nonebot import get_plugin_config
from nonebot.adapters import Adapter as BaseAdapter
from nonebot.adapters.onebot.collator import Collator
from nonebot.adapters.onebot.store import ResultStore
from nonebot.adapters.onebot.utils import get_auth_bearer

from .bot import Bot, send
from .config import Config
from . import event, exception
from .message import Message, MessageSegment
from .utils import CustomEncoder, log, msgpack_encoder, flattened_to_nested
from .event import Event, BotEvent, MetaEvent, ConnectMetaEvent, StatusUpdateMetaEvent
from .exception import (
    NetworkError,
    ApiNotAvailable,
    ActionMissingField,
    ActionFailedWithRetcode,
)

RECONNECT_INTERVAL = 3.0
COLLATOR_KEY = ("type", "detail_type", "sub_type")
DEFAULT_MODELS: list[type[Event]] = []
for model_name in dir(event):
    model = getattr(event, model_name)
    if not inspect.isclass(model) or not issubclass(model, Event):
        continue
    DEFAULT_MODELS.append(model)

DEFAULT_EXCEPTIONS: list[type[ActionFailedWithRetcode]] = []
for exc_name in dir(exception):
    Exc = getattr(exception, exc_name)
    if not inspect.isclass(Exc) or not issubclass(Exc, ActionFailedWithRetcode):
        continue
    DEFAULT_EXCEPTIONS.append(Exc)


class Adapter(BaseAdapter):
    event_models: ClassVar[dict[str, Collator[Event]]] = {
        "": Collator(
            "OneBot V12",
            DEFAULT_MODELS,
            COLLATOR_KEY,
        )
    }

    send_handlers: ClassVar[
        dict[str, Callable[[Bot, Event, Union[str, Message, MessageSegment]], Any]]
    ] = {}

    exc_classes: ClassVar[CharTrie] = CharTrie(
        (retcode, Exc) for Exc in DEFAULT_EXCEPTIONS for retcode in Exc.__retcode__
    )

    _result_store: ClassVar[ResultStore] = ResultStore()

    @classmethod
    @override
    def get_name(cls) -> str:
        return "OneBot V12"

    @override
    def __init__(self, driver: Driver, **kwargs: Any) -> None:
        super().__init__(driver, **kwargs)
        self.onebot_config: Config = get_plugin_config(Config)
        self.connections: dict[str, WebSocket] = {}
        self.tasks: set["asyncio.Task"] = set()
        self._setup()

    def _setup(self) -> None:
        if isinstance(self.driver, ASGIMixin):
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/"),
                    "POST",
                    f"{self.get_name()} Root HTTP",
                    self._handle_http,
                )
            )
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/http"),
                    "POST",
                    f"{self.get_name()} HTTP",
                    self._handle_http,
                )
            )
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/http/"),
                    "POST",
                    f"{self.get_name()} HTTP Slash",
                    self._handle_http,
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/"), f"{self.get_name()} Root WS", self._handle_ws
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/ws"), f"{self.get_name()} WS", self._handle_ws
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/ws/"),
                    f"{self.get_name()} WS Slash",
                    self._handle_ws,
                )
            )
        if self.onebot_config.onebot_ws_urls:
            if not isinstance(self.driver, WebSocketClientMixin):
                log(
                    "WARNING",
                    (
                        f"Current driver {self.config.driver} does not support "
                        "websocket client connections! Ignored"
                    ),
                )
            else:
                self.on_ready(self._start_forward)

        self.driver.on_shutdown(self._stop)

    async def _start_forward(self) -> None:
        for url in self.onebot_config.onebot_ws_urls:
            url = str(url)
            try:
                ws_url = URL(url)
                task = asyncio.create_task(self._forward_ws(ws_url))
                task.add_done_callback(self.tasks.discard)
                self.tasks.add(task)
            except Exception as e:
                log(
                    "ERROR",
                    f"<r><bg #f8bbd0>Bad url {escape_tag(url)} "
                    "in onebot forward websocket config</bg #f8bbd0></r>",
                    e,
                )

    async def _stop(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

        await asyncio.gather(
            *(asyncio.wait_for(task, timeout=10) for task in self.tasks),
            return_exceptions=True,
        )

    @override
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        websocket = self.connections.get(bot.self_id)
        timeout: float = data.get("_timeout", self.config.api_timeout)
        log("DEBUG", f"Calling API <y>{api}</y>")

        action_data = {
            "action": api,
            "params": data,
            "self": {"platform": bot.platform, "user_id": bot.self_id},
        }

        # 根据实现的不同，判断是否使用 msgpack
        # 因为不同实现对于 msgpack 的支持程度不同
        if isinstance(self.onebot_config.onebot_use_msgpack, dict):
            use_msgpack = self.onebot_config.onebot_use_msgpack.get(bot.impl, False)
        else:
            use_msgpack = self.onebot_config.onebot_use_msgpack

        if websocket:
            seq = self._result_store.get_seq()
            action_data["echo"] = str(seq)
            encoded_data = (
                msgpack.packb(action_data, default=msgpack_encoder)
                if use_msgpack
                else json.dumps(action_data, cls=CustomEncoder)
            )
            await websocket.send(encoded_data)  # type: ignore
            try:
                return self._handle_api_result(
                    await self._result_store.fetch(seq, timeout)
                )
            except asyncio.TimeoutError:
                raise NetworkError(f"WebSocket call api {api} timeout") from None

        elif isinstance(self.driver, HTTPClientMixin):
            api_url = str(self.onebot_config.onebot_api_roots.get(bot.self_id))
            if not api_url:
                raise ApiNotAvailable

            headers = {
                "Content-Type": (
                    "application/msgpack" if use_msgpack else "application/json"
                )
            }
            if self.onebot_config.onebot_access_token is not None:
                headers["Authorization"] = (
                    "Bearer " + self.onebot_config.onebot_access_token
                )

            encoded_data = (
                msgpack.packb(action_data, default=msgpack_encoder)
                if use_msgpack
                else json.dumps(action_data, cls=CustomEncoder)
            )
            request = Request(
                "POST",
                api_url,
                headers=headers,
                timeout=timeout,
                content=encoded_data,
            )

            try:
                response = await self.driver.request(request)

                if 200 <= response.status_code < 300:
                    if not response.content:
                        raise ValueError("Empty response")
                    if response.headers.get("Content-Type") == "application/msgpack":
                        result = msgpack.unpackb(response.content)
                    else:
                        result = json.loads(response.content)
                    return self._handle_api_result(result)
                raise NetworkError(
                    f"HTTP request received unexpected "
                    f"status code: {response.status_code}"
                )
            except NetworkError:
                raise
            except Exception as e:
                raise NetworkError("HTTP request failed") from e
        else:
            raise ApiNotAvailable

    def _handle_api_result(self, result: Any) -> Any:
        """处理 API 请求返回值。

        参数:
            result: API 返回数据

        返回:
            API 调用返回数据

        异常:
            ActionFailed: API 调用失败
        """
        if not isinstance(result, dict):
            raise ActionMissingField(result)
        elif not set(result.keys()).issuperset(
            {"status", "retcode", "data", "message"}
        ):
            raise ActionMissingField(result)

        if result["status"] == "failed":
            retcode = result["retcode"]
            if not isinstance(retcode, int):
                raise ActionMissingField(result)

            Exc = self.get_exception(retcode)

            raise Exc(**result)
        return result["data"]

    async def _handle_http(self, request: Request) -> Response:
        impl = request.headers.get("X-Impl")
        # check impl
        if not impl:
            log("WARNING", "Missing X-Impl Header")
            return Response(400, content="Missing X-Impl Header")

        # check access_token
        response = self._check_access_token(request)
        if response is not None:
            return response

        data = request.content
        if data is not None:
            json_data = json.loads(data)
            if event := self.json_to_event(json_data, impl):
                if isinstance(event, StatusUpdateMetaEvent):
                    self._handle_status_update(event, impl)
                if isinstance(event, MetaEvent):
                    for bot in self.bots.values():
                        bot = cast(Bot, bot)
                        task = asyncio.create_task(bot.handle_event(event))
                        task.add_done_callback(self.tasks.discard)
                        self.tasks.add(task)
                else:
                    event = cast(BotEvent, event)
                    self_id = event.self.user_id
                    bot = self.bots.get(self_id, None)
                    if not bot:
                        bot = Bot(self, self_id, impl, event.self.platform)
                        self.bot_connect(bot)
                        log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")
                    bot = cast(Bot, bot)
                    task = asyncio.create_task(bot.handle_event(event))
                    task.add_done_callback(self.tasks.discard)
                    self.tasks.add(task)
        return Response(204)

    async def _handle_ws(self, websocket: WebSocket) -> None:
        # check access_token
        response = self._check_access_token(websocket.request)
        if response is not None:
            content = cast(str, response.content)
            await websocket.close(1008, content)
            return

        await websocket.accept()

        bots: dict[str, Bot] = {}
        try:
            # 等待 connect 事件
            log(
                "DEBUG",
                "Waiting for connect meta event",
            )
            data = await websocket.receive()
            raw_data = (
                json.loads(data) if isinstance(data, str) else msgpack.unpackb(data)
            )
            event = self.json_to_event(raw_data)
            if not isinstance(event, ConnectMetaEvent):
                log(
                    "WARNING",
                    "Missing connect meta event",
                )
                await websocket.close(1008, "Missing connect meta event")
                return

            impl = event.version.impl
            log(
                "DEBUG",
                f"Connect meta event received, impl is {impl}",
            )

            while True:
                data = await websocket.receive()
                raw_data = (
                    json.loads(data) if isinstance(data, str) else msgpack.unpackb(data)
                )
                if event := self.json_to_event(raw_data, impl):
                    if isinstance(event, StatusUpdateMetaEvent):
                        self._handle_status_update(event, impl, bots, websocket)
                    if isinstance(event, MetaEvent):
                        for bot in bots.values():
                            task = asyncio.create_task(bot.handle_event(event))
                            task.add_done_callback(self.tasks.discard)
                            self.tasks.add(task)
                    else:
                        event = cast(BotEvent, event)
                        self_id = event.self.user_id
                        bot = bots.get(self_id)
                        if not bot:
                            bot = Bot(self, self_id, impl, event.self.platform)
                            self.bot_connect(bot)
                            bots[self_id] = bot
                            self.connections[self_id] = websocket
                            log(
                                "INFO",
                                (
                                    f"<y>Bot {escape_tag(event.self.user_id)}</y> "
                                    "connected"
                                ),
                            )
                        task = asyncio.create_task(bot.handle_event(event))
                        task.add_done_callback(self.tasks.discard)
                        self.tasks.add(task)

        except WebSocketClosed:
            self_id = ", ".join(bots)
            log("WARNING", f"WebSocket for Bot {escape_tag(self_id)} closed by peer")
        except Exception as e:
            self_id = ", ".join(bots)
            log(
                "ERROR",
                "<r><bg #f8bbd0>Error while process data from websocket "
                f"for bot {escape_tag(self_id)}.</bg #f8bbd0></r>",
                e,
            )

        finally:
            with contextlib.suppress(Exception):
                await websocket.close()
            for self_id, bot in bots.items():
                self.connections.pop(self_id, None)
                self.bot_disconnect(bot)

    def _check_access_token(self, request: Request) -> Optional[Response]:
        token = get_auth_bearer(request.headers.get("Authorization"))
        if token is None:
            token = request.url.query.get("access_token")

        access_token = self.onebot_config.onebot_access_token
        if access_token and access_token != token:
            msg = (
                "Authorization Header is invalid"
                if token
                else "Missing Authorization Header"
            )
            log("WARNING", msg)
            return Response(403, content=msg)

    async def _forward_ws(self, url: URL) -> None:
        headers = {}
        if self.onebot_config.onebot_access_token:
            headers["Authorization"] = (
                f"Bearer {self.onebot_config.onebot_access_token}"
            )
        req = Request("GET", url, headers=headers, timeout=30.0)
        bots: dict[str, Bot] = {}
        while True:
            try:
                async with self.websocket(req) as ws:
                    log(
                        "DEBUG",
                        f"WebSocket Connection to {escape_tag(str(url))} established",
                    )
                    try:
                        # 等待 connect 事件
                        log(
                            "DEBUG",
                            "Waiting for connect meta event",
                        )
                        data = await ws.receive()
                        raw_data = (
                            json.loads(data)
                            if isinstance(data, str)
                            else msgpack.unpackb(data)
                        )
                        event = self.json_to_event(raw_data)
                        if not isinstance(event, ConnectMetaEvent):
                            raise Exception("Missing connect meta event")

                        impl = event.version.impl
                        log(
                            "DEBUG",
                            f"Connect meta event received, impl is {impl}",
                        )

                        while True:
                            data = await ws.receive()
                            raw_data = (
                                json.loads(data)
                                if isinstance(data, str)
                                else msgpack.unpackb(data)
                            )
                            event = self.json_to_event(raw_data, impl)
                            if not event:
                                continue
                            if isinstance(event, StatusUpdateMetaEvent):
                                self._handle_status_update(event, impl, bots, ws)
                            if isinstance(event, MetaEvent):
                                for bot in bots.values():
                                    task = asyncio.create_task(bot.handle_event(event))
                                    task.add_done_callback(self.tasks.discard)
                                    self.tasks.add(task)
                            else:
                                event = cast(BotEvent, event)
                                self_id = event.self.user_id
                                bot = bots.get(self_id)
                                if not bot:
                                    bot = Bot(self, self_id, impl, event.self.platform)
                                    self.bot_connect(bot)
                                    bots[self_id] = bot
                                    self.connections[self_id] = ws
                                    log(
                                        "INFO",
                                        (
                                            "<y>"
                                            f"Bot {escape_tag(event.self.user_id)}"
                                            "</y> connected"
                                        ),
                                    )
                                task = asyncio.create_task(bot.handle_event(event))
                                task.add_done_callback(self.tasks.discard)
                                self.tasks.add(task)
                    except WebSocketClosed as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>WebSocket Closed</bg #f8bbd0></r>",
                            e,
                        )
                    except Exception as e:
                        log(
                            "ERROR",
                            (
                                "<r><bg #f8bbd0>"
                                "Error while process data from websocket"
                                f"{escape_tag(str(url))}. Trying to reconnect..."
                                "</bg #f8bbd0></r>"
                            ),
                            e,
                        )
                    finally:
                        for self_id, bot in bots.items():
                            self.connections.pop(self_id, None)
                            self.bot_disconnect(bot)
                        bots.clear()

            except Exception as e:
                log(
                    "ERROR",
                    "<r><bg #f8bbd0>Error while setup websocket to "
                    f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                    e,
                )

            await asyncio.sleep(RECONNECT_INTERVAL)

    def _handle_status_update(
        self,
        event: StatusUpdateMetaEvent,
        impl: str,
        bots: Optional[dict[str, Bot]] = None,
        websocket: Optional[WebSocket] = None,
    ) -> None:
        """处理状态更新事件"""
        for bot_status in event.status.bots:
            self_id = bot_status.self.user_id
            platform = bot_status.self.platform
            if not bot_status.online:
                if bot := self.bots.get(self_id):
                    if bots is not None and websocket is not None:
                        bots.pop(self_id, None)
                        self.connections.pop(self_id, None)
                    self.bot_disconnect(bot)

                    log(
                        "INFO",
                        f"<y>Bot {escape_tag(self_id)}</y> disconnected",
                    )
            elif self_id not in self.bots:
                bot = Bot(self, self_id, impl, platform, bot_status)

                # 先尝试连接，如果失败则不保存连接信息
                self.bot_connect(bot)
                # 正向与反向 WebSocket 连接需要额外保存连接信息
                if bots is not None and websocket is not None:
                    bots[self_id] = bot
                    self.connections[self_id] = websocket

                log(
                    "INFO",
                    f"<y>Bot {escape_tag(self_id)}</y> connected",
                )

    @classmethod
    def add_custom_model(
        cls,
        *model: type[Event],
        impl: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> None:
        if platform is not None and impl is None:
            raise ValueError("Impl must be specified")
        if impl is not None and platform is None:
            raise ValueError("platform must be specified")
        key = f"/{impl}/{platform}" if impl and platform else ""
        if key not in cls.event_models:
            cls.event_models[key] = Collator(
                "OneBot V12",
                [],
                COLLATOR_KEY,
            )
        cls.event_models[key].add_model(*model)  # type: ignore

    @classmethod
    def get_event_model(
        cls, data: dict[str, Any], impl: Optional[str] = None
    ) -> Generator[type[Event], None, None]:
        """根据事件获取对应 `Event Model` 及 `FallBack Event Model` 列表。"""
        # 元事件没有 self 字段
        platform = data.get("self", {}).get("platform")
        key = f"/{impl}/{platform}" if impl and platform else ""
        if key in cls.event_models:
            yield from cls.event_models[key].get_model(data)
        yield from cls.event_models[""].get_model(data)

    @classmethod
    def add_custom_exception(cls, exc: type[ActionFailedWithRetcode]) -> None:
        for retcode in exc.__retcode__:
            if retcode in cls.exc_classes:
                log(
                    "DEBUG",
                    f"Exception for retcode {retcode} is is overridden by {exc}",
                )
            cls.exc_classes[retcode] = exc

    @classmethod
    def get_exception(cls, retcode: int) -> type[ActionFailedWithRetcode]:
        if retcode < 100000:
            Exc = cls.exc_classes.longest_prefix(str(retcode).rjust(5, "0"))
            Exc = Exc.value if Exc else ActionFailedWithRetcode
        else:
            Exc = ActionFailedWithRetcode
        return Exc

    @classmethod
    def json_to_event(
        cls, json_data: Any, impl: Optional[str] = None
    ) -> Optional[Event]:
        if not isinstance(json_data, dict):
            return None

        # transform flattened dict to nested
        json_data = flattened_to_nested(json_data)

        if "type" not in json_data:
            cls._result_store.add_result(json_data)
            return None

        try:
            for model in cls.get_event_model(json_data, impl):
                try:
                    event = type_validate_python(model, json_data)
                    break
                except Exception as e:
                    log("DEBUG", "Event Parse Error", e)
            else:
                event = type_validate_python(Event, json_data)
            return event

        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Failed to parse event. "
                f"Raw: {json_data!s}</bg #f8bbd0></r>",
                e,
            )
            return None

    @classmethod
    def custom_send(
        cls,
        send_func: Callable[[Bot, Event, Union[str, Message, MessageSegment]], Any],
        impl: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> None:
        """自定义 Bot 的回复函数。"""
        if platform is not None and impl is None:
            raise ValueError("Impl must be specified")
        if impl is not None and platform is None:
            raise ValueError("platform must be specified")
        key = f"/{impl}/{platform}" if impl and platform else ""
        cls.send_handlers[key] = send_func

    @classmethod
    def get_send(
        cls, impl: Optional[str] = None, platform: Optional[str] = None
    ) -> Callable[[Bot, Event, Union[str, Message, MessageSegment]], Any]:
        key = f"/{impl}/{platform}" if impl and platform else ""
        return cls.send_handlers.get(key, cls.send_handlers.get("", send))
