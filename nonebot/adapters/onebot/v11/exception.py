from typing import Optional

from nonebot.exception import AdapterException
from nonebot.exception import ActionFailed as BaseActionFailed
from nonebot.exception import NetworkError as BaseNetworkError
from nonebot.exception import NoLogException as BaseNoLogException
from nonebot.exception import ApiNotAvailable as BaseApiNotAvailable


class OneBotAdapterException(AdapterException):
    def __init__(self):
        super().__init__("onebot")


class NoLogException(BaseNoLogException, OneBotAdapterException):
    pass


class ActionFailed(BaseActionFailed, OneBotAdapterException):
    """
    :说明:

      API 请求返回错误信息。

    :参数:

      * ``retcode: Optional[int]``: 错误码
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.info = kwargs

    def __repr__(self):
        return (
            f"<ActionFailed "
            + ", ".join(f"{k}={v}" for k, v in self.info.items())
            + ">"
        )

    def __str__(self):
        return self.__repr__()


class NetworkError(BaseNetworkError, OneBotAdapterException):
    """
    :说明:

      网络错误。

    :参数:

      * ``retcode: Optional[int]``: 错误码
    """

    def __init__(self, msg: Optional[str] = None):
        super().__init__()
        self.msg = msg

    def __repr__(self):
        return f"<NetWorkError message={self.msg}>"

    def __str__(self):
        return self.__repr__()


class ApiNotAvailable(BaseApiNotAvailable, OneBotAdapterException):
    pass
