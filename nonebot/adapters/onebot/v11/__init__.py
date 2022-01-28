"""OneBot v11 协议适配

协议详情请看: [OneBot V11](https://11.onebot.dev/)
"""

from .event import *
from .permission import *
from .bot import Bot as Bot
from .utils import log as log
from .utils import escape as escape
from .adapter import Adapter as Adapter
from .message import Message as Message
from .utils import unescape as unescape
from .exception import ActionFailed as ActionFailed
from .exception import NetworkError as NetworkError
from .message import MessageSegment as MessageSegment
from .exception import ApiNotAvailable as ApiNotAvailable
from .exception import OneBotAdapterException as OneBotAdapterException
