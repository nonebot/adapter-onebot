from nonebot.permission import Permission

from .event import GroupMessageEvent, PrivateMessageEvent


async def _private(event: PrivateMessageEvent) -> bool:
    return True


PRIVATE: Permission = Permission(_private)
""" 匹配任意私聊消息类型事件"""


async def _group(event: GroupMessageEvent) -> bool:
    return True


GROUP: Permission = Permission(_group)
"""匹配任意群聊消息类型事件"""

__all__ = ["PRIVATE", "GROUP"]
