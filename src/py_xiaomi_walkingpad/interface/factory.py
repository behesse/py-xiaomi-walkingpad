from __future__ import annotations

from py_xiaomi_walkingpad.event_bus import AsyncEventBus
from py_xiaomi_walkingpad.service import AsyncWalkingPadService
from py_xiaomi_walkingpad.interface.config import AppConfig, load_config
from py_xiaomi_walkingpad.miio_adapter import WalkingPadAdapter


def create_service(config: AppConfig | None = None) -> tuple[AppConfig, AsyncWalkingPadService]:
    cfg = config or load_config()
    adapter = WalkingPadAdapter(
        ip=cfg.walkingpad_ip,
        token=cfg.walkingpad_token,
        model=cfg.walkingpad_model,
        timeout_seconds=cfg.request_timeout_seconds,
    )
    service = AsyncWalkingPadService(adapter=adapter, event_bus=AsyncEventBus())
    return cfg, service

