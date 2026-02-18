from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from miio import DeviceException
from miio.walkingpad import (
    OperationMode,
    OperationSensitivity,
    Walkingpad,
    WalkingpadException,
    WalkingpadStatus,
)

from py_xiaomi_walkingpad.domain.errors import CommandValidationError, DeviceCommunicationError
from py_xiaomi_walkingpad.domain.models import CommandResult, PadMode, PadSensitivity, PadStatus


@dataclass(slots=True)
class WalkingPadAdapter:
    """Synchronous adapter around python-miio walking pad operations."""

    ip: str
    token: str
    model: str
    timeout_seconds: float = 5.0
    _device: Walkingpad = field(init=False, repr=False)

    def __post_init__(self) -> None:
        timeout = max(1, int(round(self.timeout_seconds)))
        self._device = Walkingpad(
            ip=self.ip,
            token=self.token,
            model=self.model,
            timeout=timeout,
        )

    @property
    def supported_models(self) -> tuple[str, ...]:
        return tuple(self._device.supported_models)

    def status(self, *, quick: bool = False) -> PadStatus:
        try:
            raw = self._device.quick_status() if quick else self._device.status()
            return self._map_status(raw)
        except KeyError:
            # Some models/firmwares do not return the full property set expected by
            # python-miio status(); fall back to quick status payload.
            try:
                raw = self._device.quick_status()
                return self._map_status(raw)
            except Exception as exc:  # noqa: BLE001
                raise DeviceCommunicationError(str(exc)) from exc
        except (DeviceException, WalkingpadException) as exc:
            raise DeviceCommunicationError(str(exc)) from exc

    def start(self) -> CommandResult:
        # Avoid python-miio start() pre-status check (extra IO round-trip).
        # Try run directly first, then fallback to power-on + run.
        try:
            self._device.send("set_state", ["run"])
        except (WalkingpadException, DeviceException):
            self._run_command("power_on", self._device.on)
            self._run_command("start", lambda: self._device.send("set_state", ["run"]))
        return CommandResult(command="start", success=True, message="ok")

    def stop(self) -> CommandResult:
        return self._run_command("stop", self._device.stop)

    def power_on(self) -> CommandResult:
        return self._run_command("power_on", self._device.on)

    def power_off(self) -> CommandResult:
        return self._run_command("power_off", self._device.off)

    def lock(self) -> CommandResult:
        return self._run_command("lock", self._device.lock)

    def unlock(self) -> CommandResult:
        return self._run_command("unlock", self._device.unlock)

    def set_speed(self, speed_kmh: float) -> CommandResult:
        if speed_kmh < 0 or speed_kmh > 6:
            raise CommandValidationError("speed_kmh must be between 0 and 6")
        # Use raw send to avoid python-miio set_speed() pre-status check.
        return self._run_command(
            "set_speed",
            lambda: self._device.send("set_speed", [float(speed_kmh)]),
        )

    def set_start_speed(self, speed_kmh: float) -> CommandResult:
        if speed_kmh < 0 or speed_kmh > 6:
            raise CommandValidationError("start_speed_kmh must be between 0 and 6")
        return self._run_command(
            "set_start_speed",
            lambda: self._device.send("set_start_speed", [float(speed_kmh)]),
        )

    def set_mode(self, mode: PadMode) -> CommandResult:
        mapped = {
            PadMode.AUTO: OperationMode.Auto,
            PadMode.MANUAL: OperationMode.Manual,
            PadMode.OFF: OperationMode.Off,
        }[mode]
        return self._run_command("set_mode", lambda: self._device.set_mode(mapped))

    def set_sensitivity(self, sensitivity: PadSensitivity) -> CommandResult:
        mapped = {
            PadSensitivity.HIGH: OperationSensitivity.High,
            PadSensitivity.MEDIUM: OperationSensitivity.Medium,
            PadSensitivity.LOW: OperationSensitivity.Low,
        }[sensitivity]
        return self._run_command("set_sensitivity", lambda: self._device.set_sensitivity(mapped))

    def _run_command(self, command: str, func) -> CommandResult:
        try:
            func()
        except WalkingpadException as exc:
            raise CommandValidationError(str(exc)) from exc
        except DeviceException as exc:
            raise DeviceCommunicationError(str(exc)) from exc
        return CommandResult(command=command, success=True, message="ok")

    @staticmethod
    def _map_status(raw: WalkingpadStatus) -> PadStatus:
        mode_map = {
            OperationMode.Auto: PadMode.AUTO,
            OperationMode.Manual: PadMode.MANUAL,
            OperationMode.Off: PadMode.OFF,
        }
        sensitivity_map = {
            OperationSensitivity.High: PadSensitivity.HIGH,
            OperationSensitivity.Medium: PadSensitivity.MEDIUM,
            OperationSensitivity.Low: PadSensitivity.LOW,
        }

        mode = None
        sensitivity = None

        data = getattr(raw, "data", {}) or {}

        raw_mode = None
        if "mode" in data:
            try:
                raw_mode = OperationMode(data["mode"])
            except Exception:
                raw_mode = None
        mode = mode_map.get(raw_mode) if raw_mode is not None else None

        raw_sensitivity = None
        if "sensitivity" in data:
            try:
                raw_sensitivity = OperationSensitivity(data["sensitivity"])
            except Exception:
                raw_sensitivity = None
        sensitivity = sensitivity_map.get(raw_sensitivity) if raw_sensitivity is not None else None

        walking_time = None
        if "time" in data:
            try:
                walking_time = timedelta(seconds=int(data["time"]))
            except Exception:
                walking_time = None

        if walking_time is not None and not isinstance(walking_time, timedelta):
            walking_time = timedelta(seconds=int(walking_time))

        return PadStatus(
            is_on=(data.get("power") == "on") if "power" in data else None,
            power=data.get("power"),
            mode=mode,
            speed_kmh=float(data["sp"]) if "sp" in data else None,
            start_speed_kmh=float(data["start_speed"]) if "start_speed" in data else None,
            sensitivity=sensitivity,
            step_count=int(data["step"]) if "step" in data else None,
            distance_m=int(data["dist"]) if "dist" in data else None,
            calories=int(data["cal"]) if "cal" in data else None,
            walking_time=walking_time,
        )
