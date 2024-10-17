"""OneBot API 回调存储。

FrontMatter:
    sidebar_position: 2
    description: onebot.store 模块
"""

import sys
from typing import Any

import anyio
from anyio.abc import TaskStatus


class ResultStore:
    def __init__(self) -> None:
        self._seq: int = 1
        self._events: dict[int, tuple[TaskStatus[dict[str, Any]], anyio.Event]] = {}

    @property
    def current_seq(self) -> int:
        return self._seq

    def get_seq(self) -> int:
        s = self._seq
        self._seq = (self._seq + 1) % sys.maxsize
        return s

    def add_result(self, result: dict[str, Any]):
        echo = result.get("echo")
        if (
            isinstance(echo, str)
            and echo.isdecimal()
            and (echo := int(echo)) in self._events
        ):
            task_status, event = self._events[echo]
            task_status.started(result)
            event.set()

    async def fetch(
        self,
        seq: int,
        task_status: TaskStatus[dict[str, Any]] = anyio.TASK_STATUS_IGNORED,
    ) -> None:
        event = anyio.Event()
        self._events[seq] = (task_status, event)
        try:
            await event.wait()
        finally:
            self._events.pop(seq, None)
