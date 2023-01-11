"""OneBot v11 杂项。

FrontMatter:
    sidebar_position: 9
    description: onebot.v11.utils 模块
"""

from typing import Any, Dict, Optional

from nonebot.utils import logger_wrapper

from .exception import ActionFailed

log = logger_wrapper("OneBot V11")


def escape(s: str, *, escape_comma: bool = True) -> str:
    """对字符串进行 CQ 码转义。

    参数:
        s: 需要转义的字符串
        escape_comma: 是否转义逗号（`,`）。
    """
    s = s.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
    if escape_comma:
        s = s.replace(",", "&#44;")
    return s


def unescape(s: str) -> str:
    """对字符串进行 CQ 码去转义。

    参数:
        s: 需要转义的字符串
    """
    return (
        s.replace("&#44;", ",")
        .replace("&#91;", "[")
        .replace("&#93;", "]")
        .replace("&amp;", "&")
    )


def handle_api_result(result: Optional[Dict[str, Any]]) -> Any:
    """处理 API 请求返回值。

    参数:
        result: API 返回数据

    返回:
        API 调用返回数据

    异常:
        ActionFailed: API 调用失败
    """
    if isinstance(result, dict):
        if result.get("status") == "failed":
            raise ActionFailed(**result)
        return result.get("data")


def truncate(
    s: str,
    length: int = 70,
    kill_words: bool = True,
    end: str = "...",
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

    result = s[: length - len(end)].rsplit(" ", 1)[0]
    return result + end
