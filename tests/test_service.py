from __future__ import annotations

import asyncio
from datetime import timedelta

import pytest

from py_xiaomi_walkingpad.service import AsyncWalkingPadService
from py_xiaomi_walkingpad.types.models import CommandResult, PadMode, PadSensitivity, PadStatus


class FakeAdapter:
    model = "ksmb.walkingpad.v1"
    supported_models = ("ksmb.walkingpad.v1",)

    def status(self, *, quick: bool = False) -> PadStatus:
        return PadStatus(
            is_on=True,
            power="on",
            mode=PadMode.MANUAL,
            speed_kmh=3.0,
            start_speed_kmh=2.0,
            sensitivity=PadSensitivity.MEDIUM,
            step_count=10,
            distance_m=12,
            calories=3,
            walking_time=timedelta(seconds=5),
        )

    def start(self) -> CommandResult:
        return CommandResult(command="start", success=True, message="ok")

    def stop(self) -> CommandResult:
        return CommandResult(command="stop", success=True, message="ok")

    def power_on(self) -> CommandResult:
        return CommandResult(command="power_on", success=True, message="ok")

    def power_off(self) -> CommandResult:
        return CommandResult(command="power_off", success=True, message="ok")

    def lock(self) -> CommandResult:
        return CommandResult(command="lock", success=True, message="ok")

    def unlock(self) -> CommandResult:
        return CommandResult(command="unlock", success=True, message="ok")

    def set_speed(self, _: float) -> CommandResult:
        return CommandResult(command="set_speed", success=True, message="ok")

    def set_start_speed(self, _: float) -> CommandResult:
        return CommandResult(command="set_start_speed", success=True, message="ok")

    def set_mode(self, _: PadMode) -> CommandResult:
        return CommandResult(command="set_mode", success=True, message="ok")

    def set_sensitivity(self, _: PadSensitivity) -> CommandResult:
        return CommandResult(command="set_sensitivity", success=True, message="ok")


@pytest.mark.asyncio
async def test_get_status_and_latest_snapshot():
    service = AsyncWalkingPadService(adapter=FakeAdapter())
    status = await service.get_status()
    assert status.is_on is True
    assert service.latest_status == status


@pytest.mark.asyncio
async def test_start_polling_updates_snapshot():
    service = AsyncWalkingPadService(adapter=FakeAdapter())
    await service.start_polling(interval_seconds=0.01)
    await asyncio.sleep(0.03)
    await service.stop_polling()
    assert service.latest_status is not None
    assert service.latest_status.mode == PadMode.MANUAL

