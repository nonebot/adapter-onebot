import inspect
import asyncio
import json

from pygtrie import StringTrie
from typing import Any, Dict, List, Optional, Type, cast

from requests import request

from nonebot.adapters import Adapter as BaseAdapter
from nonebot.exception import ApiNotAvailable, WebSocketClosed
from nonebot.typing import overrides
from nonebot.drivers import (
    URL,
    Driver,
    Request,
    Response,
    WebSocket,
    ReverseDriver,
    ForwardDriver,
    HTTPServerSetup,
    WebSocketServerSetup,
)
from nonebot.utils import DataclassEncoder, escape_tag

from . import event
from .bot import Bot
from .event import Event
from .config import Config
from .exception import NetworkError
from .utils import get_auth_bearer, log, ResultStore, _handle_api_result

RECONNECT_INTERVAL = 3.0


class Adapter(BaseAdapter):
    event_models = StringTrie = StringTrie(separator=".")

    for model_name in dir(event):
        model = getattr(event, model_name)
        if not inspect.isclass(model) or not issubclass(model, Event):
            continue
        event_models["." + model.__event__] = model

    @classmethod
    @overrides(BaseAdapter)
    def get_name(cls) -> str:
        return "OneBot V12"

    @overrides(BaseAdapter)
    def __init__(self, driver: Driver, **kwargs: Any):
        super().__init__(driver, **kwargs)
        self.onebot_config: Config = Config(**self.config.dict())
        self.connections: Dict[str, WebSocket] = {}
        self.tasks: List["asyncio.Task"] = []
        self._setup()

    def _setup(self) -> None:
        if isinstance(self.driver, ReverseDriver):
            self.setup_http_server(
                HTTPServerSetup(
                    URL("/onebot/v12/"),
                    "POST",
                    self.get_name(),
                    self._handle_http_webhook,
                )
            )
            self.setup_websocket_server(
                WebSocketServerSetup(
                    URL("/onebot/v12/"), self.get_name(), self._handle_ws
                )
            )
        if self.onebot_config.onebot_ws_urls:
            if isinstance(self.driver, ReverseDriver):
                log(
                    "WARNING",
                    f"Current driver {self.config.driver} don't support forward connections! Ignored",
                )
            else:
                self.driver.on_startup(self._start_forward)
                self.driver.on_shutdown(self._stop_forward)

    @overrides(BaseAdapter)
    async def _call_api(self, bot: Bot, api: str, **data: Any) -> Any:
        websocket = self.connections.get(bot.self_id, None)
        timeout: float = data.get("_timeout", self.config.api_timeout)
        log("DEBUG", f"Calling API <y>{api}</y>")

        if websocket:
            seq = ResultStore.get_seq()
            json_data = json.dumps(
                {"action": api, "params": data, "echo": seq},
                cls=DataclassEncoder,
            )
            await websocket.send(json_data)
            return _handle_api_result(
                await ResultStore.fetch(bot.self_id, seq, timeout)
            )

        elif isinstance(self.driver, ForwardDriver):
            api_url = self.onebot_config.onebot_http_urls.get(bot.self_id)
            if not api_url:
                raise ApiNotAvailable
            elif not api_url.endswith("/"):
                api_url += "/"

            headers = {"Content-Type": "application/json"}
            if self.onebot_config.onebot_access_token is not None:
                headers["Authorization"] = (
                    "Bearer " + self.onebot_config.onebot_access_token
                )

            request = Request(
                "POST",
                api_url + api,
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
                    return _handle_api_result(result)
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

    async def _handle_http_webhook(self, req: Request) -> Response:
        self_id = req.headers.get("X-Self-Id")

        # check self_id
        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            return Response(400, content="Missing X-Self-ID Header")

        # check access_token
        resp = self._check_access_token(req)
        if resp is not None:
            return resp

        data = req.content
        if data is not None:
            json_data = json.loads(data)
            event = self.json2event(json_data)
            if event:
                bot = self.bots.get(self_id)
                if not bot:
                    bot = Bot(self, self_id)
                    self.bot_connect(bot)
                    log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")
                bot = cast(Bot, bot)
                asyncio.create_task(bot.handle_event(event))
        return Response(204)

    async def _handle_ws(self, websocket: WebSocket) -> None:
        self_id = websocket.request.headers.get("X-Self-Id")

        if not self_id:
            log("WARNING", "Missing X-Self-ID Header")
            await websocket.close(1008, "Missing X-Self-ID Header")
            return
        elif self_id in self.bots:
            log("WARNING", f"There's already a bot {self_id}, ignored")
            await websocket.close(1008, "Duplicate X-Self-ID")
            return

        response = self._check_access_token(websocket.request)
        if response is not None:
            content = cast(str, response.content)
            await websocket.close(1008, content)
            return

        await websocket.accept()
        bot = Bot(self, self_id)
        self.connections[self_id] = websocket
        self.bot_connect(bot)

        log("INFO", f"<y>Bot {escape_tag(self_id)}</y> connected")

        try:
            while True:
                data = await websocket.receive()
                json_data = json.loads(data)
                event = self.json2event(json_data, self_id)
                if event:
                    asyncio.create_task(bot.handle_event(event))
        except WebSocketClosed as e:
            log("WARNING", f"WebSocket for Bot {escape_tag(self_id)} closed by peer")
        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Error while process data from websocket"
                f"for bot {escape_tag(self_id)}.</bg #f8bbd0></r>",
                e,
            )
        finally:
            try:
                await websocket.close()
            except Exception:
                pass
            self.connections.pop(self_id, None)
            self.bot_disconnect(bot)

    async def _start_forward(self) -> None:
        for url in self.onebot_config.onebot_ws_urls:
            try:
                ws_url = URL(url)
                self.tasks.append(asyncio.create_task(self._forward_ws(ws_url)))
            except Exception as e:
                log(
                    "ERROR",
                    f"<r><bg #f8bbd0>Bad url {escape_tag(url)} "
                    "in onebot forward websocket config</bg #f8bbd0></r>",
                    e,
                )

    async def _stop_forward(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

    async def _forward_ws(self, url: URL) -> None:
        headers = {}
        if self.onebot_config.onebot_access_token:
            headers[
                "Authorization"
            ] = f"Bearer {self.onebot_config.onebot_access_token}"
        req = Request("GET", url, headers=headers, timeout=30.0)
        bot: Optional[Bot] = None
        while True:
            try:
                async with self.websocket(req) as ws:
                    log(
                        "DEBUG",
                        f"WebSocket Connection to {escape_tag(str(url))} established",
                    )
                    try:
                        while True:
                            data = await ws.receive()
                            json_data = json.loads(data)
                            event = self.json2event(json_data, bot and bot.self_id)
                            if not event:
                                continue
                            if not bot:
                                self_id = event.self_id
                                bot = Bot(self, self_id)
                                self.connections[self_id] = ws
                                self.bot_connect(bot)
                                log(
                                    "INFO",
                                    f"<y>Bot {escape_tag(str(self_id))}</y> connected",
                                )
                            asyncio.create_task(bot.handle_event(event))
                    except WebSocketClosed as e:
                        log(
                            "ERROR",
                            f"<r><bg #f8bbd0>WebSocket Closed</bg #f8bbd0></r>",
                            e,
                        )
                    except Exception as e:
                        log(
                            "ERROR",
                            "<r><bg #f8bbd0>Error while process data from websocket"
                            f"{escape_tag(str(url))}. Trying to reconnect...</bg #f8bbd0></r>",
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
    def get_event_model(cls, event_type: str) -> List[Type[Event]]:
        return [model.value for model in cls.event_models.prefixes("." + event_type)][
            ::-1
        ]

    @classmethod
    def json2event(
        cls, json_data: Any, self_id: Optional[str] = None
    ) -> Optional[Event]:
        if not isinstance(json_data, dict):
            return None

        if "type" not in json_data:
            if self_id is not None:
                ResultStore.add_result(self_id, json_data)
            return None

        try:
            event_type = json_data["type"]
            detail_type = json_data.get("detail_type", "")
            event_type = event_type + f".{detail_type}" if detail_type else event_type
            sub_type = json_data.get("sub_type", "")
            event_type = event_type + f".{sub_type}" if sub_type else event_type
            for model in cls.get_event_model(event_type):
                try:
                    event = model.parse_obj(json_data)
                    break
                except Exception as e:
                    log("DEBUG", "Event Parse Error", e)
            else:
                event = Event.parse_obj(json_data)
            return event

        except Exception as e:
            log(
                "ERROR",
                "<r><bg #f8bbd0>Failed to parse event. "
                f"Raw: {str(json_data)}</bg #f8bbd0></r>",
                e,
            )
            return None

    def _check_access_token(self, request: Request) -> Optional[Response]:
        token = get_auth_bearer(request.headers.get("Authorization"))

        access_token = self.onebot_config.onebot_access_token
        if access_token and access_token != token:
            msg = (
                "Authorization Header is invalid"
                if token
                else "Missing Authorization Header"
            )
            log("WARNING", msg)
            return Response(403, content=msg)
