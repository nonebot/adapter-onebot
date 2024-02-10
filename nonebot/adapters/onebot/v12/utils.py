"""OneBot v12 杂项。

FrontMatter:
    sidebar_position: 8
    description: onebot.v12.utils 模块
"""

import datetime
from base64 import b64encode
from functools import partial
from typing import Any, TypeVar
from typing_extensions import override

from nonebot.compat import PYDANTIC_V2
from nonebot.utils import DataclassEncoder, logger_wrapper

T = TypeVar("T")


log = logger_wrapper("OneBot V12")


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

    @override
    def default(self, o):
        if isinstance(o, bytes):
            return b64encode(o).decode()
        return super().default(o)


def timestamp(obj: datetime.datetime):
    return obj.timestamp()


# https://12.onebot.dev/connect/data-protocol/basic-types/
msgpack_type_encoders = {
    datetime.datetime: timestamp,
}

if PYDANTIC_V2:
    from pydantic_core import to_jsonable_python

    def msgpack_encoder(obj: Any):
        for type_, encoder in msgpack_type_encoders.items():
            if isinstance(obj, type_):
                return encoder(obj)
        return to_jsonable_python(obj)

else:
    from pydantic.json import custom_pydantic_encoder

    msgpack_encoder = partial(
        custom_pydantic_encoder,
        msgpack_type_encoders,  # type: ignore
    )
