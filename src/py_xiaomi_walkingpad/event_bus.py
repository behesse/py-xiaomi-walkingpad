from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator


class AsyncEventBus:
    """Simple fan-out async event bus using per-subscriber queues."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[object]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: object) -> None:
        async with self._lock:
            subscribers = tuple(self._subscribers)
        for queue in subscribers:
            queue.put_nowait(event)

    async def stream(self) -> AsyncIterator[object]:
        queue: asyncio.Queue[object] = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

