"""OneBot v11 机器人定义。

FrontMatter:
    sidebar_position: 3
    description: onebot.v11.bot 模块
"""

import re
from typing_extensions import override
from typing import Any, Union, Callable

from nonebot.message import handle_event
from nonebot.compat import model_dump, type_validate_python

from nonebot.adapters import Bot as BaseBot

from .utils import log
from .message import Message, MessageSegment
from .event import Event, Reply, MessageEvent


async def _check_reply(bot: "Bot", event: MessageEvent) -> None:
    """检查消息中存在的回复，去除并赋值 `event.reply`, `event.to_me`。

    参数:
        bot: Bot 对象
        event: MessageEvent 对象
    """
    try:
        index = [x.type == "reply" for x in event.message].index(True)
    except ValueError:
        return
    msg_seg = event.message[index]
    try:
        event.reply = type_validate_python(
            Reply, await bot.get_msg(message_id=int(msg_seg.data["id"]))
        )
    except Exception as e:
        log("WARNING", f"Error when getting message reply info: {e!r}")
        return

    if event.reply.sender.user_id is not None:
        # ensure string comparation
        if str(event.reply.sender.user_id) == str(event.self_id):
            event.to_me = True
        del event.message[index]

        if (
            len(event.message) > index
            and event.message[index].type == "at"
            and event.message[index].data.get("qq") == str(event.reply.sender.user_id)
        ):
            del event.message[index]

    if len(event.message) > index and event.message[index].type == "text":
        event.message[index].data["text"] = event.message[index].data["text"].lstrip()
        if not event.message[index].data["text"]:
            del event.message[index]

    if not event.message:
        event.message.append(MessageSegment.text(""))


def _check_at_me(bot: "Bot", event: MessageEvent) -> None:
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

    if event.message_type == "private":
        event.to_me = True
    else:

        def _is_at_me_seg(segment: MessageSegment):
            return segment.type == "at" and str(segment.data.get("qq", "")) == str(
                event.self_id
            )

        # check the first segment
        if _is_at_me_seg(event.message[0]):
            event.to_me = True
            event.message.pop(0)
            if event.message and event.message[0].type == "text":
                event.message[0].data["text"] = event.message[0].data["text"].lstrip()
                if not event.message[0].data["text"]:
                    del event.message[0]
            if event.message and _is_at_me_seg(event.message[0]):
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

            if _is_at_me_seg(last_msg_seg):
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

    nicknames = {re.escape(n) for n in bot.config.nickname}
    if not nicknames:
        return

    # check if the user is calling me with my nickname
    nickname_regex = "|".join(nicknames)
    first_text = first_msg_seg.data["text"]
    if m := re.search(rf"^({nickname_regex})([\s,，]*|$)", first_text, re.IGNORECASE):
        log("DEBUG", f"User is calling me {m[1]}")
        event.to_me = True
        first_msg_seg.data["text"] = first_text[m.end() :]


async def send(
    bot: "Bot",
    event: Event,
    message: Union[str, Message, MessageSegment],
    at_sender: bool = False,
    reply_message: bool = False,
    **params: Any,  # extra options passed to send_msg API
) -> Any:
    """默认回复消息处理函数。"""
    event_dict = model_dump(event)

    if "message_id" not in event_dict:
        reply_message = False  # if no message_id, force disable reply_message

    if "user_id" in event_dict:  # copy the user_id to the API params if exists
        params.setdefault("user_id", event_dict["user_id"])
    else:
        at_sender = False  # if no user_id, force disable at_sender

    if "group_id" in event_dict:  # copy the group_id to the API params if exists
        params.setdefault("group_id", event_dict["group_id"])

    # guess the message_type
    if "message_type" in event_dict:
        params.setdefault("message_type", event_dict["message_type"])

    if "message_type" not in params:
        if params.get("group_id") is not None:
            params["message_type"] = "group"
        elif params.get("user_id") is not None:
            params["message_type"] = "private"
        else:
            raise ValueError("Cannot guess message type to reply!")

    full_message = Message()  # create a new message with at sender segment
    if reply_message:
        full_message += MessageSegment.reply(event_dict["message_id"])
    if at_sender and params["message_type"] != "private":
        full_message += MessageSegment.at(params["user_id"]) + " "
    full_message += message
    params.setdefault("message", full_message)

    return await bot.send_msg(**params)


class Bot(BaseBot):
    """
    OneBot v11 协议 Bot 适配。
    """

    send_handler: Callable[["Bot", Event, Union[str, Message, MessageSegment]], Any] = (
        send
    )

    async def handle_event(self, event: Event) -> None:
        """处理收到的事件。"""
        if isinstance(event, MessageEvent):
            event.message.reduce()
            await _check_reply(self, event)
            _check_at_me(self, event)
            _check_nickname(self, event)

        await handle_event(self, event)

    @override
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs: Any,
    ) -> Any:
        """根据 `event` 向触发事件的主体回复消息。

        参数:
            event: Event 对象
            message: 要发送的消息
            at_sender (bool): 是否 @ 事件主体
            reply_message (bool): 是否回复事件消息
            kwargs: 其他参数，可以与
                {ref}`nonebot.adapters.onebot.v11.adapter.Adapter.custom_send` 配合使用

        返回:
            API 调用返回数据

        异常:
            ValueError: 缺少 `user_id`, `group_id`
            NetworkError: 网络错误
            ActionFailed: API 调用失败
        """
        return await self.__class__.send_handler(self, event, message, **kwargs)
