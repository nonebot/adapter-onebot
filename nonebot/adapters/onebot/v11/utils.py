import sys
import asyncio
from typing import Any, Dict, Tuple, Optional

from nonebot.utils import logger_wrapper

from .exception import ActionFailed, NetworkError

log = logger_wrapper("OneBot V11")


def get_auth_bearer(access_token: Optional[str] = None) -> Optional[str]:
    if not access_token:
        return None
    scheme, _, param = access_token.partition(" ")
    if scheme.lower() not in ["bearer", "token"]:
        return None
    return param


def escape(s: str, *, escape_comma: bool = True) -> str:
    """
    :说明:

      对字符串进行 CQ 码转义。

    :参数:

      * ``s: str``: 需要转义的字符串
      * ``escape_comma: bool``: 是否转义逗号（``,``）。
    """
    s = s.replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")
    if escape_comma:
        s = s.replace(",", "&#44;")
    return s


def unescape(s: str) -> str:
    """
    :说明:

      对字符串进行 CQ 码去转义。

    :参数:

      * ``s: str``: 需要转义的字符串
    """
    return (
        s.replace("&#44;", ",")
        .replace("&#91;", "[")
        .replace("&#93;", "]")
        .replace("&amp;", "&")
    )


def _b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


def _handle_api_result(result: Optional[Dict[str, Any]]) -> Any:
    """
    :说明:

      处理 API 请求返回值。

    :参数:

      * ``result: Optional[Dict[str, Any]]``: API 返回数据

    :返回:

        - ``Any``: API 调用返回数据

    :异常:

        - ``ActionFailed``: API 调用失败
    """
    if isinstance(result, dict):
        if result.get("status") == "failed":
            raise ActionFailed(**result)
        return result.get("data")


class ResultStore:
    _seq = 1
    _futures: Dict[Tuple[str, int], asyncio.Future] = {}

    @classmethod
    def get_seq(cls) -> int:
        s = cls._seq
        cls._seq = (cls._seq + 1) % sys.maxsize
        return s

    @classmethod
    def add_result(cls, self_id: str, result: Dict[str, Any]):
        if isinstance(result.get("echo"), dict) and isinstance(
            result["echo"].get("seq"), int
        ):
            future = cls._futures.get((self_id, result["echo"]["seq"]))
            if future:
                future.set_result(result)

    @classmethod
    async def fetch(
        cls, self_id: str, seq: int, timeout: Optional[float]
    ) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[(self_id, seq)] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise NetworkError("WebSocket API call timeout") from None
        finally:
            del cls._futures[(self_id, seq)]
