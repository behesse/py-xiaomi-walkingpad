from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


class PadMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    OFF = "off"


class PadSensitivity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(slots=True)
class PadStatus:
    is_on: bool | None
    power: str | None
    mode: PadMode | None
    speed_kmh: float | None
    start_speed_kmh: float | None
    sensitivity: PadSensitivity | None
    step_count: int | None
    distance_m: int | None
    calories: int | None
    walking_time: timedelta | None


@dataclass(slots=True)
class CommandResult:
    command: str
    success: bool
    message: str

