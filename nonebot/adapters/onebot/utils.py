"""OneBot 辅助函数。

FrontMatter:
    sidebar_position: 3
    description: onebot.utils 模块
"""

from typing import Optional


def get_auth_bearer(access_token: Optional[str] = None) -> Optional[str]:
    if not access_token:
        return None
    scheme, _, param = access_token.partition(" ")
    return param if scheme.lower() in ["bearer", "token"] else None


def b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


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
