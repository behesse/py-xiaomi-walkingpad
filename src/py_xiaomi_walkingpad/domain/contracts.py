from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol

from py_xiaomi_walkingpad.domain.models import CommandResult, PadMode, PadSensitivity, PadStatus


@dataclass(slots=True)
class ServiceCapabilities:
    supported_models: tuple[str, ...]
    model_hint: str
    supports_power: bool = True
    supports_lock: bool = True
    supports_mode: bool = True
    supports_sensitivity: bool = True


class WalkingPadService(Protocol):
    async def get_status(self, *, quick: bool = False) -> PadStatus:
        ...

    async def start(self) -> CommandResult:
        ...

    async def stop(self) -> CommandResult:
        ...

    async def power_on(self) -> CommandResult:
        ...

    async def power_off(self) -> CommandResult:
        ...

    async def lock(self) -> CommandResult:
        ...

    async def unlock(self) -> CommandResult:
        ...

    async def set_speed(self, speed_kmh: float) -> CommandResult:
        ...

    async def set_start_speed(self, speed_kmh: float) -> CommandResult:
        ...

    async def set_mode(self, mode: PadMode) -> CommandResult:
        ...

    async def set_sensitivity(self, sensitivity: PadSensitivity) -> CommandResult:
        ...

    async def get_capabilities(self) -> ServiceCapabilities:
        ...

    async def event_stream(self) -> AsyncIterator[object]:
        ...

    async def start_polling(self, interval_seconds: float = 1.0) -> None:
        ...

    async def stop_polling(self) -> None:
        ...

