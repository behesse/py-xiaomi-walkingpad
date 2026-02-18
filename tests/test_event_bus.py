from __future__ import annotations

import asyncio

import pytest

from py_xiaomi_walkingpad.event_bus import AsyncEventBus


@pytest.mark.asyncio
async def test_event_bus_fanout():
    bus = AsyncEventBus()
    stream1 = bus.stream()
    stream2 = bus.stream()

    task1 = asyncio.create_task(stream1.__anext__())
    task2 = asyncio.create_task(stream2.__anext__())

    await asyncio.sleep(0)
    await bus.publish({"kind": "status"})

    event1 = await task1
    event2 = await task2

    assert event1 == {"kind": "status"}
    assert event2 == {"kind": "status"}

    await stream1.aclose()
    await stream2.aclose()

