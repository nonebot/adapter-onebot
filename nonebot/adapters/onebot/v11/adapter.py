"""OneBot v11 适配器。

FrontMatter:
    sidebar_position: 1
    description: onebot.v11.adapter 模块
"""

import hmac
import json
import asyncio
import inspect
import contextlib
from collections.abc import Generator
from typing_extensions import override
from typing import Any, Union, Callable, Optional, cast

from nonebot.exception import WebSocketClosed
from nonebot.compat import type_validate_python
from nonebot.utils import DataclassEncoder, escape_tag
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

from . import event
from .bot import Bot
from .config import Config
from .utils import log, handle_api_result
from .event import Event, LifecycleMetaEvent
from .message import Message, MessageSegment
from .exception import NetworkError, ApiNotAvailable, OneBotV11AdapterException

RECONNECT_INTERVAL = 3.0
DEFAULT_MODELS: list[type[Event]] = []
for model_name in dir(event):
    model = getattr(event, model_name)
    if not inspect.isclass(model) or not issubclass(model, Event):
        continue
    DEFAULT_MODELS.append(model)


class Adapter(BaseAdapter):
    event_models = Collator(
        "OneBot V11",
        DEFAULT_MODELS,
        (
            "post_type",
            ("message_type", "notice_type", "request_type", "meta_event_type"),
            "sub_type",
        ),
    )

    _result_store = ResultStore()

    @override
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.onebot_config: Config = get_plugin_config(Config)
        """OneBot V11 配置"""
        self.connections: dict[str, WebSocket] = {}
        self.tasks: set["asyncio.Task"] = set()
        self._setup()

    @classmethod
    @override
    def get_name(cls) -> str:
        """适配器名称: `OneBot V11`"""
        return "OneBot V11"

    def _setup(self) -> None:
        if isinstance(self.driver, ASGIMixin):
            http_setup = HTTPServerSetup(
                URL("/onebot/v11/"),
                "POST",
                f"{self.get_name()} Root HTTP",
                self._handle_http,
            )
            self.setup_http_server(http_setup)
            http_setup = HTTPServerSetup(
                URL("/onebot/v11/http"),
                "POST",
                f"{self.get_name()} HTTP",
                self._handle_http,
            )
            self.setup_http_server(http_setup)
            http_setup = HTTPServerSetup(
                URL("/onebot/v11/http/"),
                "POST",
                f"{self.get_name()} HTTP Slash",
                self._handle_http,
            )
            self.setup_http_server(http_setup)

            ws_setup = WebSocketServerSetup(
                URL("/onebot/v11/"), f"{self.get_name()} Root WS", self._handle_ws
            )
            self.setup_websocket_server(ws_setup)
            ws_setup = WebSocketServerSetup(
                URL("/onebot/v11/ws"), f"{self.get_name()} WS", self._handle_ws
            )
            self.setup_websocket_server(ws_setup)
            ws_setup = WebSocketServerSetup(
                URL("/onebot/v11/ws/"), f"{self.get_name()} WS Slash", self._handle_ws
            )
            self.setup_websocket_server(ws_setup)

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
        websocket = self.connections.get(bot.self_id, None)
        timeout: float = data.get("_timeout", self.config.api_timeout)
        log("DEBUG", f"Calling API <y>{api}</y>")

        if websocket:
            seq = self._result_store.get_seq()
            json_data = json.dumps(
                {"action": api, "params": data, "echo": str(seq)},
                cls=DataclassEncoder,
            )
            await websocket.send(json_data)
            try:
                return handle_api_result(await self._result_store.fetch(seq, timeout))
            except asyncio.TimeoutError:
                raise NetworkError(f"WebSocket call api {api} timeout") from None

        elif isinstance(self.driver, HTTPClientMixin):
            api_root = str(self.onebot_config.onebot_api_roots.get(bot.self_id))
            if not api_root:
                raise ApiNotAvailable
            elif not api_root.endswith("/"):
                api_root += "/"

            headers = {"Content-Type": "application/json"}
            if self.onebot_config.onebot_access_token is not None:
                headers["Authorization"] = (
                    "Bearer " + self.onebot_config.onebot_access_token
                )

            request = Request(
                "POST",
                api_root + api,
                headers=headers,
                timeout=timeout,
                content=json.dumps(data, cls=DataclassEncoder),
            )

            try:
                response = await self.driver.request(request)

                if 200 <= response.status_code < 300:
                    if not response.content:
                        raise ValueError("Empty response")
                    result = json.loads(response.content)
                    return handle_api_result(result)
                raise NetworkError(
                    f"HTTP request received unexpected "
                    f"status code: {response.status_code}"
                )
            except OneBotV11AdapterException:
                raise
            except Exception as e:
                raise NetworkError("HTTP request failed") from e
        else:
            raise ApiNotAvailable

    async def _handle_http(self, request: Request) -> Response:
        self_id = request.headers.get("x-self-id")

        # check self_id
        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            return Response(400, content="Missing X-Self-ID Header")

        # check signature
        response = self._check_signature(request)
        if response is not None:
            return response

        if data := request.content:
            json_data = json.loads(data)
            if event := self.json_to_event(json_data):
                if not (bot := self.bots.get(self_id, None)):
                    bot = Bot(self, self_id)
                    self.bot_connect(bot)
                    log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")
                bot = cast(Bot, bot)
                task = asyncio.create_task(bot.handle_event(event))
                task.add_done_callback(self.tasks.discard)
                self.tasks.add(task)
        else:
            return Response(400, content="Invalid request body")
        return Response(204)

    async def _handle_ws(self, websocket: WebSocket) -> None:
        self_id = websocket.request.headers.get("x-self-id")

        # check self_id
        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            await websocket.close(1008, "Missing X-Self-ID Header")
            return
        elif self_id in self.bots:
            log("WARNING", f"There's already a bot {self_id}, ignored")
            await websocket.close(1008, "Duplicate X-Self-ID")
            return

        # check access_token
        response = self._check_access_token(websocket.request)
        if response is not None:
            content = cast(str, response.content)
            await websocket.close(1008, content)
            return

        await websocket.accept()
        bot = Bot(self, self_id)
        self.bot_connect(bot)
        self.connections[self_id] = websocket

        log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")

        try:
            while True:
                data = await websocket.receive()
                json_data = json.loads(data)
                if event := self.json_to_event(json_data):
                    task = asyncio.create_task(bot.handle_event(event))
                    task.add_done_callback(self.tasks.discard)
                    self.tasks.add(task)
        except WebSocketClosed:
            log("WARNING", f"WebSocket for Bot {escape_tag(self_id)} closed by peer")
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Error while process data from websocket "
                f"for bot {escape_tag(self_id)}.</bg #f8bbd0></r>",
                e,
            )
        finally:
            with contextlib.suppress(Exception):
                await websocket.close()
            self.connections.pop(self_id, None)
            self.bot_disconnect(bot)

    def _check_signature(self, request: Request) -> Optional[Response]:
        x_signature = request.headers.get("x-signature")

        if secret := self.onebot_config.onebot_secret:
            if not x_signature:
                log("WARNING", "Missing Signature Header")
                return Response(401, content="Missing Signature", request=request)

            if request.content is None:
                return Response(400, content="Missing Content", request=request)

            body: bytes = (
                request.content
                if isinstance(request.content, bytes)
                else request.content.encode("utf-8")
            )
            sig = hmac.new(secret.encode("utf-8"), body, "sha1").hexdigest()
            if x_signature != "sha1=" + sig:
                log("WARNING", "Signature Header is invalid")
                return Response(403, content="Signature is invalid")

    def _check_access_token(self, request: Request) -> Optional[Response]:
        token = get_auth_bearer(request.headers.get("authorization"))

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
        request = Request("GET", url, headers=headers, timeout=30.0)

        bot: Optional[Bot] = None

        while True:
            try:
                async with self.websocket(request) as ws:
                    log(
                        "DEBUG",
                        f"WebSocket Connection to {escape_tag(str(url))} established",
                    )
                    try:
                        while True:
                            data = await ws.receive()
                            json_data = json.loads(data)
                            event = self.json_to_event(json_data)
                            if not event:
                                continue
                            if not bot:
                                if (
                                    not isinstance(event, LifecycleMetaEvent)
                                    or event.sub_type != "connect"
                                ):
                                    continue
                                self_id = event.self_id
                                bot = Bot(self, str(self_id))
                                self.bot_connect(bot)
                                self.connections[str(self_id)] = ws
                                log(
                                    "INFO",
                                    f"<y>Bot {escape_tag(str(self_id))}</y> connected",
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
                        if bot:
                            self.connections.pop(bot.self_id, None)
                            self.bot_disconnect(bot)
                            bot = None

            except Exception as e:
                log(
                    "ERROR",
                    "<r><bg #f8bbd0>Error while setup websocket to "
                    f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
                    e,
                )

            await asyncio.sleep(RECONNECT_INTERVAL)

    @classmethod
    def add_custom_model(cls, *model: type[Event]) -> None:
        """插入或覆盖一个自定义的 Event 类型。

        参数:
            model: 自定义的 Event 类型
        """
        cls.event_models.add_model(*model)

    @classmethod
    def get_event_model(
        cls, data: dict[str, Any]
    ) -> Generator[type[Event], None, None]:
        """根据事件获取对应 `Event Model` 及 `FallBack Event Model` 列表。"""
        yield from cls.event_models.get_model(data)

    @classmethod
    def json_to_event(cls, json_data: Any) -> Optional[Event]:
        """将 json 数据转换为 Event 对象。

        如果为 API 调用返回数据且提供了 Event 对应 Bot，则将数据存入 ResultStore。

        参数:
            json_data: json 数据
            self_id: 当前 Event 对应的 Bot

        返回:
            Event 对象，如果解析失败或为 API 调用返回数据，则返回 None
        """
        if not isinstance(json_data, dict):
            return None

        if "post_type" not in json_data:
            cls._result_store.add_result(json_data)
            return

        try:
            for model in cls.get_event_model(json_data):
                try:
                    event = type_validate_python(model, json_data)
                    break
                except Exception as e:
                    log("DEBUG", "Event Parser Error", e)
            else:
                event = type_validate_python(Event, json_data)

            return event
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Failed to parse event. "
                f"Raw: {escape_tag(str(json_data))}</bg #f8bbd0></r>",
                e,
            )

    @classmethod
    def custom_send(
        cls,
        send_func: Callable[[Bot, Event, Union[str, Message, MessageSegment]], Any],
    ):
        """自定义 Bot 的回复函数。"""
        setattr(Bot, "send_handler", send_func)
