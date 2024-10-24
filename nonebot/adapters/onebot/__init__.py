"""OneBot 协议适配器。

包含 v11 与 v12 两个版本的协议。

参考: [OneBot](https://onebot.dev/), [OneBot v11](https://11.onebot.dev/), [OneBot v12](https://12.onebot.dev/)

FrontMatter:
    sidebar_position: 0
    description: onebot 模块
"""

from .v11 import Bot as V11Bot  # noqa: F401
from .v12 import Bot as V12Bot  # noqa: F401
from .v11 import event as V11Event  # noqa: F401
from .v12 import event as V12Event  # noqa: F401
from .v11 import Adapter as V11Adapter  # noqa: F401
from .v11 import Message as V11Message  # noqa: F401
from .v12 import Adapter as V12Adapter  # noqa: F401
from .v12 import Message as V12Message  # noqa: F401
from .v11 import MessageSegment as V11MessageSegment  # noqa: F401
from .v12 import MessageSegment as V12MessageSegment  # noqa: F401
