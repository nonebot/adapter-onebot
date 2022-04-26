"""OneBot v12 协议适配

协议详情请看: [OneBot V12](https://12.1bot.dev/)
"""

from .event import *
from .permission import *
from .bot import Bot as Bot
from .utils import log as log
from .adapter import Adapter as Adapter
from .message import Message as Message
from .exception import ActionFailed as ActionFailed
from .exception import NetworkError as NetworkError
from .message import MessageSegment as MessageSegment
from .exception import ApiNotAvailable as ApiNotAvailable
from .exception import OneBotAdapterException as OneBotAdapterException
