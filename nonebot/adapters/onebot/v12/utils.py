import sys
import asyncio
from typing import Any, Dict, Tuple, Optional

from nonebot.utils import logger_wrapper

from .exception import ActionFailed, NetworkError

log = logger_wrapper("OneBot V12")


def get_auth_bearer(access_token: Optional[str] = None) -> Optional[str]:
    if not access_token:
        return None
    scheme, _, param = access_token.partition(" ")
    if scheme.lower() not in ["bearer", "token"]:
        return None
    return param


def _b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


def _handle_api_result(result: Optional[Dict[str, Any]]) -> Any:
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


class ResultStore:
    _seq = 1
    _futures: Dict[Tuple[str, str], asyncio.Future] = {}

    @classmethod
    def get_seq(cls) -> str:
        s = cls._seq
        cls._seq = (cls._seq + 1) % sys.maxsize
        return str(s)

    @classmethod
    def add_result(cls, self_id: str, result: Dict[str, Any]):
        if isinstance(result.get("echo"), str):
            future = cls._futures.get((self_id, result["echo"]))
            if future:
                future.set_result(result)

    @classmethod
    async def fetch(
        cls, self_id: str, seq: int, timeout: Optional[float]
    ) -> Dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        cls._futures[(self_id, str(seq))] = future
        try:
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            raise NetworkError("WebSocket API call timeout") from None
        finally:
            del cls._futures[(self_id, seq)]
