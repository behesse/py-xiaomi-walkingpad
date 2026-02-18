from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from py_xiaomi_walkingpad.types.models import CommandResult, PadStatus


@dataclass(slots=True)
class StatusUpdatedEvent:
    timestamp: datetime
    status: PadStatus
    quick: bool


@dataclass(slots=True)
class CommandExecutedEvent:
    timestamp: datetime
    result: CommandResult


@dataclass(slots=True)
class ErrorEvent:
    timestamp: datetime
    operation: str
    message: str


@dataclass(slots=True)
class OperationTimingEvent:
    timestamp: datetime
    operation: str
    wait_ms: float
    run_ms: float
    total_ms: float
    success: bool
