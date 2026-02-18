from __future__ import annotations

from dataclasses import dataclass

from py_xiaomi_walkingpad.app.event_bus import AsyncEventBus
from py_xiaomi_walkingpad.app.service import AsyncWalkingPadService
from py_xiaomi_walkingpad.infra.config import AppConfig, load_config
from py_xiaomi_walkingpad.infra.miio_adapter import WalkingPadAdapter


@dataclass(slots=True)
class AppContainer:
    config: AppConfig
    service: AsyncWalkingPadService


def build_container() -> AppContainer:
    config = load_config()
    adapter = WalkingPadAdapter(
        ip=config.walkingpad_ip,
        token=config.walkingpad_token,
        model=config.walkingpad_model,
        timeout_seconds=config.request_timeout_seconds,
    )
    service = AsyncWalkingPadService(adapter=adapter, event_bus=AsyncEventBus())
    return AppContainer(config=config, service=service)
