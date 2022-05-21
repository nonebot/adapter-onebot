from typing import Any, Dict, Optional

from .exception import ActionFailed


def get_auth_bearer(access_token: Optional[str] = None) -> Optional[str]:
    if not access_token:
        return None
    scheme, _, param = access_token.partition(" ")
    if scheme.lower() not in ["bearer", "token"]:
        return None
    return param


def b2s(b: Optional[bool]) -> Optional[str]:
    """转换布尔值为字符串。"""
    return b if b is None else str(b).lower()


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
