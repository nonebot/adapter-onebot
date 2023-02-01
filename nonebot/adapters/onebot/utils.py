"""OneBot 辅助函数。

FrontMatter:
    sidebar_position: 3
    description: onebot.utils 模块
"""

from io import BytesIO
from pathlib import Path
from base64 import b64encode
from typing import Union, Optional


def get_auth_bearer(access_token: Optional[str] = None) -> Optional[str]:
    if not access_token:
        return None
    scheme, _, param = access_token.partition(" ")
    return param if scheme.lower() in ["bearer", "token"] else None


def b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


def f2s(file: Union[str, bytes, BytesIO, Path]) -> str:
    if isinstance(file, BytesIO):
        file = file.getvalue()
    if isinstance(file, bytes):
        file = f"base64://{b64encode(file).decode()}"
    elif isinstance(file, Path):
        file = file.resolve().as_uri()
    return file


def truncate(
    s: str, length: int = 70, kill_words: bool = True, end: str = "..."
) -> str:
    """将给定字符串截断到指定长度。

    参数:
        s: 需要截取的字符串
        length: 截取长度
        kill_words: 是否不保留完整单词
        end: 截取字符串的结尾字符

    返回:
        截取后的字符串
    """
    if len(s) <= length:
        return s

    if kill_words:
        return s[: length - len(end)] + end

    result = s[: length - len(end)].rsplit(maxsplit=1)[0]
    return result + end
