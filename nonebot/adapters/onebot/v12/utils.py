"""OneBot v12 杂项。

FrontMatter:
    sidebar_position: 8
    description: onebot.v12.utils 模块
"""

from base64 import b64encode
from typing import Any, Dict, TypeVar, Optional

from nonebot.typing import overrides
from nonebot.utils import DataclassEncoder, logger_wrapper

from .exception import (
    BadParam,
    IAmTired,
    BadHandler,
    BadRequest,
    LogicError,
    ActionFailed,
    HandlerError,
    RequestError,
    DatabaseError,
    ExtendedError,
    PlatformError,
    BadSegmentData,
    ExecutionError,
    FileSystemError,
    ExecNetworkError,
    UnsupportedParam,
    UnsupportedAction,
    ActionMissingField,
    UnsupportedSegment,
    InternalHandlerError,
    UnsupportedSegmentData,
    ActionFailedWithRetcode,
)

T = TypeVar("T")


log = logger_wrapper("OneBot V12")


def handle_api_result(result: Any) -> Any:
    """处理 API 请求返回值。

    参数:
        result: API 返回数据

    返回:
        API 调用返回数据

    异常:
        ActionFailed: API 调用失败
    """
    if not isinstance(result, dict):
        raise ActionMissingField(result)
    elif not set(result.keys()).issuperset({"status", "retcode", "data", "message"}):
        raise ActionMissingField(result)

    if result["status"] == "failed":
        retcode = result["retcode"]
        if not isinstance(retcode, int):
            raise ActionMissingField(result)

        if 10000 <= retcode < 20000:
            if retcode == 10001:
                raise BadRequest(**result)
            elif retcode == 10002:
                raise UnsupportedAction(**result)
            elif retcode == 10003:
                raise BadParam(**result)
            elif retcode == 10004:
                raise UnsupportedParam(**result)
            elif retcode == 10005:
                raise UnsupportedSegment(**result)
            elif retcode == 10006:
                raise BadSegmentData(**result)
            elif retcode == 10007:
                raise UnsupportedSegmentData(**result)
            else:
                raise RequestError(**result)
        elif 20000 <= retcode < 30000:
            if retcode == 20001:
                raise BadHandler(**result)
            elif retcode == 20002:
                raise InternalHandlerError(**result)
            else:
                raise HandlerError(**result)
        elif 30000 <= retcode < 40000:
            if 31000 <= retcode < 32000:
                raise DatabaseError(**result)
            elif 32000 <= retcode < 33000:
                raise FileSystemError(**result)
            elif 33000 <= retcode < 34000:
                raise ExecNetworkError(**result)
            elif 34000 <= retcode < 35000:
                raise PlatformError(**result)
            elif 35000 <= retcode < 36000:
                raise LogicError(**result)
            elif 36000 <= retcode < 37000:
                raise IAmTired(**result)
            else:
                raise ExecutionError(**result)
        elif 60000 <= retcode < 100000:
            raise ExtendedError(**result)
        else:
            raise ActionFailedWithRetcode(**result)
    return result.get("data")


def flattened_to_nested(data: T) -> T:
    """将扁平键值转为嵌套字典。"""
    if isinstance(data, dict):
        pairs = [
            (
                key.split(".") if isinstance(key, str) else key,
                flattened_to_nested(value),
            )
            for key, value in data.items()
        ]
        result = {}
        for key_list, value in pairs:
            target = result
            for key in key_list[:-1]:
                target = target.setdefault(key, {})
            target[key_list[-1]] = value
        return result  # type: ignore
    elif isinstance(data, list):
        return [flattened_to_nested(item) for item in data]  # type: ignore
    return data


class CustomEncoder(DataclassEncoder):
    """OneBot V12 使用的 `JSONEncoder`"""

    @overrides(DataclassEncoder)
    def default(self, o):
        if isinstance(o, bytes):
            return b64encode(o).decode()
        return super(CustomEncoder, self).default(o)
