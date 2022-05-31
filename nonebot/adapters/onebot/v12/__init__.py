"""OneBot v12 协议适配。

协议详情请看: [OneBot V12](https://12.1bot.dev/)

FrontMatter:
    sidebar_position: 0
    description: onebot.v12 模块
"""

from nonebot.adapters.onebot.exception import ActionFailed as ActionFailed
from nonebot.adapters.onebot.exception import NetworkError as NetworkError
from nonebot.adapters.onebot.exception import ApiNotAvailable as ApiNotAvailable
from nonebot.adapters.onebot.exception import (
    OneBotAdapterException as OneBotAdapterException,
)

from .event import *
from .permission import *
from .bot import Bot as Bot
from .log import log as log
from .adapter import Adapter as Adapter
from .message import Message as Message
from .message import MessageSegment as MessageSegment
