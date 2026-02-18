from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from py_xiaomi_walkingpad.domain.errors import ConfigurationError


@dataclass(slots=True)
class AppConfig:
    walkingpad_ip: str
    walkingpad_token: str
    walkingpad_model: str = "ksmb.walkingpad.v1"
    polling_interval_seconds: float = 1.0
    request_timeout_seconds: float = 5.0


def load_config() -> AppConfig:
    load_dotenv()

    ip = os.getenv("WALKINGPAD_IP", "").strip()
    token = os.getenv("WALKINGPAD_TOKEN", "").strip()
    model = os.getenv("WALKINGPAD_MODEL", "ksmb.walkingpad.v1").strip() or "ksmb.walkingpad.v1"
    polling_interval_raw = os.getenv("WALKINGPAD_POLLING_INTERVAL", "1.0").strip() or "1.0"
    request_timeout_raw = os.getenv("WALKINGPAD_REQUEST_TIMEOUT", "5.0").strip() or "5.0"

    missing: list[str] = []
    if not ip:
        missing.append("WALKINGPAD_IP")
    if not token:
        missing.append("WALKINGPAD_TOKEN")
    if missing:
        raise ConfigurationError(f"Missing required environment variables: {', '.join(missing)}")

    try:
        polling_interval = float(polling_interval_raw)
    except ValueError as exc:
        raise ConfigurationError("WALKINGPAD_POLLING_INTERVAL must be a number") from exc

    if polling_interval <= 0:
        raise ConfigurationError("WALKINGPAD_POLLING_INTERVAL must be > 0")

    try:
        request_timeout = float(request_timeout_raw)
    except ValueError as exc:
        raise ConfigurationError("WALKINGPAD_REQUEST_TIMEOUT must be a number") from exc

    if request_timeout <= 0:
        raise ConfigurationError("WALKINGPAD_REQUEST_TIMEOUT must be > 0")

    return AppConfig(
        walkingpad_ip=ip,
        walkingpad_token=token,
        walkingpad_model=model,
        polling_interval_seconds=polling_interval,
        request_timeout_seconds=request_timeout,
    )
