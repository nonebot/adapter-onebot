"""OneBot API 回调存储。

FrontMatter:
    sidebar_position: 2
    description: onebot.store 模块
"""

import sys
import asyncio
from typing import Any, Optional


class ResultStore:
    def __init__(self) -> None:
        self._seq: int = 1
        self._futures: dict[int, asyncio.Future] = {}

    @property
    def current_seq(self) -> int:
        return self._seq

    def get_seq(self) -> int:
        s = self._seq
        self._seq = (self._seq + 1) % sys.maxsize
        return s

    def add_result(self, result: dict[str, Any]):
        echo = result.get("echo")
        if isinstance(echo, str) and echo.isdecimal():
            if future := self._futures.get(int(echo)):
                future.set_result(result)

    async def fetch(self, seq: int, timeout: Optional[float]) -> dict[str, Any]:
        future = asyncio.get_event_loop().create_future()
        self._futures[seq] = future
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            del self._futures[seq]
