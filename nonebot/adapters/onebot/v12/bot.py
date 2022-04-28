import re
from typing import Callable, Union, Any

from nonebot.adapters import Bot as BaseBot
from nonebot.typing import overrides
from nonebot.message import handle_event

from .utils import log
from .event import Event, MessageEvent
from .message import Message, MessageSegment


def _check_to_me(bot: "Bot", event: MessageEvent) -> None:
    """检查消息开头或结尾是否存在 @机器人，去除并赋值 `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    if not isinstance(event, MessageEvent):
        return

    # ensure message not empty
    if not event.message:
        event.message.append(MessageSegment.text(""))

    if event.detail_type == "private":
        event.to_me = True
    else:

        def _is_mention_me_seg(segment: MessageSegment) -> bool:
            return (
                segment.type == "mention"
                and str(segment.data.get("user_id", "")) == event.self_id
            )

        # check the first segment
        if _is_mention_me_seg(event.message[0]):
            event.to_me = True
            event.message.pop(0)
            if event.message and event.message[0].type == "text":
                event.message[0].data["text"] = event.message[0].data["text"].lstrip()
                if not event.message[0].data["text"]:
                    del event.message[0]
            if event.message and _is_mention_me_seg(event.message[0]):
                event.message.pop(0)
                if event.message and event.message[0].type == "text":
                    event.message[0].data["text"] = (
                        event.message[0].data["text"].lstrip()
                    )
                    if not event.message[0].data["text"]:
                        del event.message[0]

        if not event.to_me:
            # check the last segment
            i = -1
            last_msg_seg = event.message[i]
            if (
                last_msg_seg.type == "text"
                and not last_msg_seg.data["text"].strip()
                and len(event.message) >= 2
            ):
                i -= 1
                last_msg_seg = event.message[i]

            if _is_mention_me_seg(last_msg_seg):
                event.to_me = True
                del event.message[i:]

        if not event.message:
            event.message.append(MessageSegment.text(""))


def _check_nickname(bot: "Bot", event: MessageEvent) -> None:
    """检查消息开头是否存在昵称，去除并赋值 `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    first_msg_seg = event.message[0]
    if first_msg_seg.type != "text":
        return

    first_text = first_msg_seg.data["text"]

    nicknames = set(filter(lambda n: n, bot.config.nickname))
    if nicknames:
        # check if the user is calling me with my nickname
        nickname_regex = "|".join(nicknames)
        m = re.search(rf"^({nickname_regex})([\s,，]*|$)", first_text, re.IGNORECASE)
        if m:
            nickname = m.group(1)
            log("DEBUG", f"User is calling me {nickname}")
            event.to_me = True
            first_msg_seg.data["text"] = first_text[m.end() :]


async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = False,
    **params: Any,
) -> Any:
    """默认回复消息处理函数。"""
    event_dict = event.dict()

    if "user_id" in event_dict:  # copy the user_id to the API params if exists
        params.setdefault("user_id", event_dict["user_id"])
    else:
        at_sender = False  # if no user_id, force disable at_sender

    if "group_id" in event_dict:  # copy the group_id to the API params if exists
        params.setdefault("group_id", event_dict["group_id"])

    if "detail_type" not in params:  # guess the detail_type
        if "group_id" in params:
            params["detail_type"] = "group"
        elif "user_id" in params:
            params["detail_type"] = "private"
        else:
            raise ValueError("Cannot guess message type to reply!")

    full_message = Message()  # create a new message with at sender segment
    if at_sender and params["detail_type"] != "private":
        full_message += MessageSegment.mention(params["user_id"]) + " "
    full_message += message
    params.setdefault("message", full_message)

    return await bot.send_message(**params)


class Bot(BaseBot):

    send_handler: Callable[
        ["Bot", Event, Union[str, Message, MessageSegment]], Any
    ] = send

    @overrides(BaseBot)
    async def call_api(self, api: str, **data: Any) -> Any:
        return await super().call_api(api, **data)

    async def handle_event(self, event: Event) -> None:
        if isinstance(event, MessageEvent):
            _check_to_me(self, event)
            _check_nickname(self, event)
        await handle_event(self, event)

    @overrides(BaseBot)
    async def send(
        self, event: Event, message: Union[str, Message, MessageSegment], **kwargs: Any
    ) -> Any:
        return await self.__class__.send_handler(self, event, message, **kwargs)
