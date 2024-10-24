"""OneBot v12 协议适配。

协议详情请看: [OneBot V12](https://12.1bot.dev/)

FrontMatter:
    sidebar_position: 0
    description: onebot.v12 模块
"""

from .bot import Bot as Bot
from .utils import log as log
from .event import *  # noqa: F403
from .exception import *  # noqa: F403
from .adapter import Adapter as Adapter
from .message import Message as Message
from .permission import *  # noqa: F403
from .message import MessageSegment as MessageSegment
