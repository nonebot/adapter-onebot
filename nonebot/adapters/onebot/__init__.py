"""OneBot 协议适配器。

包含 v11 与 ~~v12~~ 两个版本的协议。

参考: [OneBot](https://onebot.dev/), [OneBot v11](https://11.onebot.dev/), [OneBot v12](https://12.onebot.dev/)
"""

from .v11 import Bot as V11Bot
from .v11 import event as V11Event
from .v11 import Adapter as V11Adapter
from .v11 import Message as V11Message
from .v11 import MessageSegment as V11MessageSegment
