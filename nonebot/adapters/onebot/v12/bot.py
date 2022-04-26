from typing import Callable, Union, Any

from nonebot.adapters import Bot as BaseBot
from nonebot.typing import overrides
from nonebot.message import handle_event

from .event import Event, MessageEvent
from .message import Message, MessageSegment


async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = False,
    **params: Any,
) -> Any:
    # todo
    pass


class Bot(BaseBot):

    send_handler: Callable[
        ["Bot", Event, Union[str, Message, MessageSegment]], Any
    ] = send

    @overrides(BaseBot)
    async def call_api(self, api: str, **data: Any) -> Any:
        return await super().call_api(api, **data)

    async def handle_event(self, event: Event) -> None:
        if isinstance(event, MessageEvent):
            # todo
            pass
        await handle_event(self, event)

    @overrides(BaseBot)
    async def send(
        self, event: Event, message: Union[str, Message, MessageSegment], **kwargs: Any
    ) -> Any:
        return await self.__class__.send_handler(self, event, message, **kwargs)
