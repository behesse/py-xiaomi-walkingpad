from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import datetime, UTC
from time import perf_counter

from py_xiaomi_walkingpad.event_bus import AsyncEventBus
from py_xiaomi_walkingpad.types.events import (
    CommandExecutedEvent,
    ErrorEvent,
    OperationTimingEvent,
    StatusUpdatedEvent,
)
from py_xiaomi_walkingpad.types.models import CommandResult, PadMode, PadSensitivity, PadStatus
from py_xiaomi_walkingpad.miio_adapter import WalkingPadAdapter


class AsyncWalkingPadService:
    """Async-facing service wrapping synchronous miio operations."""

    def __init__(self, adapter: WalkingPadAdapter, event_bus: AsyncEventBus | None = None) -> None:
        self._adapter = adapter
        self._event_bus = event_bus or AsyncEventBus()
        self._polling_task: asyncio.Task[None] | None = None
        self._latest_status: PadStatus | None = None
        self._io_lock = asyncio.Lock()

    async def get_status(self, *, quick: bool = False) -> PadStatus:
        status = await self._run_blocking(lambda: self._adapter.status(quick=quick), "get_status")
        self._latest_status = status
        await self._event_bus.publish(
            StatusUpdatedEvent(timestamp=datetime.now(UTC), status=status, quick=quick)
        )
        return status

    async def start(self) -> CommandResult:
        return await self._run_command(self._adapter.start, "start")

    async def stop(self) -> CommandResult:
        return await self._run_command(self._adapter.stop, "stop")

    async def power_on(self) -> CommandResult:
        return await self._run_command(self._adapter.power_on, "power_on")

    async def power_off(self) -> CommandResult:
        return await self._run_command(self._adapter.power_off, "power_off")

    async def lock(self) -> CommandResult:
        return await self._run_command(self._adapter.lock, "lock")

    async def unlock(self) -> CommandResult:
        return await self._run_command(self._adapter.unlock, "unlock")

    async def set_speed(self, speed_kmh: float) -> CommandResult:
        return await self._run_command(lambda: self._adapter.set_speed(speed_kmh), "set_speed")

    async def set_start_speed(self, speed_kmh: float) -> CommandResult:
        return await self._run_command(
            lambda: self._adapter.set_start_speed(speed_kmh), "set_start_speed"
        )

    async def set_mode(self, mode: PadMode) -> CommandResult:
        return await self._run_command(lambda: self._adapter.set_mode(mode), "set_mode")

    async def set_sensitivity(self, sensitivity: PadSensitivity) -> CommandResult:
        return await self._run_command(
            lambda: self._adapter.set_sensitivity(sensitivity),
            "set_sensitivity",
        )

    async def event_stream(self) -> AsyncIterator[object]:
        async for event in self._event_bus.stream():
            yield event

    async def start_polling(self, interval_seconds: float = 1.0) -> None:
        if self._polling_task and not self._polling_task.done():
            return

        async def _poll_loop() -> None:
            while True:
                try:
                    # Do not queue polling behind interactive commands.
                    if self._io_lock.locked():
                        await asyncio.sleep(interval_seconds)
                        continue
                    await self.get_status(quick=False)
                except Exception as exc:  # noqa: BLE001
                    await self._event_bus.publish(
                        ErrorEvent(
                            timestamp=datetime.now(UTC),
                            operation="poll",
                            message=str(exc),
                        )
                    )
                await asyncio.sleep(interval_seconds)

        self._polling_task = asyncio.create_task(_poll_loop(), name="walkingpad-poll")

    async def stop_polling(self) -> None:
        if not self._polling_task:
            return
        self._polling_task.cancel()
        try:
            await self._polling_task
        except asyncio.CancelledError:
            pass
        finally:
            self._polling_task = None

    @property
    def latest_status(self) -> PadStatus | None:
        return self._latest_status

    async def _run_command(self, func: Callable[[], CommandResult], operation: str) -> CommandResult:
        result = await self._run_blocking(func, operation)
        await self._event_bus.publish(CommandExecutedEvent(timestamp=datetime.now(UTC), result=result))
        return result

    async def _run_blocking(self, func: Callable[[], object], operation: str):
        start = perf_counter()
        wait_ms = 0.0
        run_ms = 0.0
        try:
            lock_wait_start = perf_counter()
            async with self._io_lock:
                wait_ms = (perf_counter() - lock_wait_start) * 1000.0
                run_start = perf_counter()
                result = await asyncio.to_thread(func)
                run_ms = (perf_counter() - run_start) * 1000.0
            total_ms = (perf_counter() - start) * 1000.0
            await self._event_bus.publish(
                OperationTimingEvent(
                    timestamp=datetime.now(UTC),
                    operation=operation,
                    wait_ms=wait_ms,
                    run_ms=run_ms,
                    total_ms=total_ms,
                    success=True,
                )
            )
            return result
        except Exception as exc:  # noqa: BLE001
            total_ms = (perf_counter() - start) * 1000.0
            await self._event_bus.publish(
                OperationTimingEvent(
                    timestamp=datetime.now(UTC),
                    operation=operation,
                    wait_ms=wait_ms,
                    run_ms=run_ms,
                    total_ms=total_ms,
                    success=False,
                )
            )
            await self._event_bus.publish(
                ErrorEvent(timestamp=datetime.now(UTC), operation=operation, message=str(exc))
            )
            raise
