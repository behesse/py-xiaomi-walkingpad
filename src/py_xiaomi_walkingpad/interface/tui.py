from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import timedelta

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Footer, Header, Input, Log, Select, Static

from py_xiaomi_walkingpad.app.container import AppContainer
from py_xiaomi_walkingpad.domain.models import PadMode, PadSensitivity, PadStatus


def _fmt_time(value: timedelta | None) -> str:
    if value is None:
        return "-"
    secs = int(value.total_seconds())
    h = secs // 3600
    m = (secs % 3600) // 60
    s = secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


class WalkingPadTuiApp(App[None]):
    CSS = """
    #root {
        layout: vertical;
        padding: 1;
    }
    #status {
        height: 12;
        border: round $accent;
        padding: 1;
    }
    #actions {
        height: 14;
        border: round $secondary;
        padding: 1;
    }
    #log {
        height: 1fr;
        border: round $primary;
    }
    .row {
        height: auto;
    }
    Button {
        margin-right: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("escape", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("s", "start", "Start"),
        ("x", "stop", "Stop"),
        ("+", "speed_up", "Speed +0.5"),
        ("-", "speed_down", "Speed -0.5"),
    ]

    status_text: reactive[str] = reactive("No data yet")

    def __init__(self, container_factory: Callable[[], AppContainer]) -> None:
        super().__init__()
        self._container_factory = container_factory
        self._container: AppContainer | None = None
        self._event_task: asyncio.Task[None] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="root"):
            yield Static("Status", classes="title")
            yield Static(self.status_text, id="status")
            with Container(id="actions"):
                with Horizontal(classes="row"):
                    yield Button("Refresh", id="btn-refresh", variant="primary")
                    yield Button("Start", id="btn-start", variant="success")
                    yield Button("Stop", id="btn-stop", variant="warning")
                    yield Button("Power On", id="btn-on")
                    yield Button("Power Off", id="btn-off")
                    yield Button("Lock", id="btn-lock")
                    yield Button("Unlock", id="btn-unlock")
                with Horizontal(classes="row"):
                    yield Button("Speed -0.5", id="btn-speed-down")
                    yield Button("Speed +0.5", id="btn-speed-up")
                    yield Input(placeholder="Speed 0..6", id="speed-input")
                    yield Button("Set Speed", id="btn-set-speed")
                    yield Input(placeholder="Start speed 0..6", id="start-speed-input")
                    yield Button("Set Start", id="btn-set-start-speed")
                with Horizontal(classes="row"):
                    yield Select(
                        options=[("auto", "auto"), ("manual", "manual"), ("off", "off")],
                        value="manual",
                        id="mode-select",
                    )
                    yield Button("Set Mode", id="btn-set-mode")
                    yield Select(
                        options=[("high", "high"), ("medium", "medium"), ("low", "low")],
                        value="medium",
                        id="sensitivity-select",
                    )
                    yield Button("Set Sensitivity", id="btn-set-sensitivity")
            yield Log(id="log", highlight=True)
        yield Footer()

    async def on_mount(self) -> None:
        self._container = self._container_factory()
        await self._container.service.start_polling(self._container.config.polling_interval_seconds)
        self._event_task = asyncio.create_task(self._consume_events())
        asyncio.create_task(self._refresh_status())
        self.query_one("#log", Log).write_line("Started polling")

    async def on_unmount(self) -> None:
        if self._container is not None:
            await self._container.service.stop_polling()
        if self._event_task is not None:
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass

    def _render_status(self, status: PadStatus) -> str:
        return (
            f"Power: {status.power}\n"
            f"On: {status.is_on}\n"
            f"Mode: {status.mode.value if status.mode else '-'}\n"
            f"Speed: {status.speed_kmh}\n"
            f"Start speed: {status.start_speed_kmh}\n"
            f"Sensitivity: {status.sensitivity.value if status.sensitivity else '-'}\n"
            f"Steps: {status.step_count}\n"
            f"Distance: {status.distance_m} m\n"
            f"Calories: {status.calories}\n"
            f"Time: {_fmt_time(status.walking_time)}"
        )

    async def _refresh_status(self) -> None:
        if not self._container:
            return
        log = self.query_one("#log", Log)
        try:
            status = await self._container.service.get_status(quick=False)
            self.status_text = self._render_status(status)
            self.query_one("#status", Static).update(self.status_text)
        except Exception as exc:  # noqa: BLE001
            log.write_line(f"refresh: ERROR {exc}")

    async def _consume_events(self) -> None:
        if not self._container:
            return
        log = self.query_one("#log", Log)
        async for event in self._container.service.event_stream():
            name = type(event).__name__
            log.write_line(f"event: {name}")
            if hasattr(event, "wait_ms") and hasattr(event, "run_ms") and hasattr(event, "total_ms"):
                log.write_line(
                    "timing "
                    f"op={getattr(event, 'operation', '?')} "
                    f"wait={getattr(event, 'wait_ms', 0.0):.1f}ms "
                    f"run={getattr(event, 'run_ms', 0.0):.1f}ms "
                    f"total={getattr(event, 'total_ms', 0.0):.1f}ms "
                    f"ok={getattr(event, 'success', False)}"
                )
            if hasattr(event, "status"):
                status = getattr(event, "status")
                if isinstance(status, PadStatus):
                    self.status_text = self._render_status(status)
                    self.query_one("#status", Static).update(self.status_text)
            if hasattr(event, "message") and hasattr(event, "operation"):
                log.write_line(f"error in {event.operation}: {event.message}")

    async def _run_action(self, label: str, coro) -> None:
        log = self.query_one("#log", Log)
        self.query_one("#status", Static).update(f"Executing: {label} ...")
        try:
            result = await coro
            log.write_line(f"{label}: {result.message}")
            # Let polling update status naturally; avoid extra immediate full read.
        except Exception as exc:  # noqa: BLE001
            log.write_line(f"{label}: ERROR {exc}")

    async def _adjust_speed(self, delta: float) -> None:
        if not self._container:
            return
        status = self._container.service.latest_status
        if status is None or status.speed_kmh is None:
            status = await self._container.service.get_status(quick=False)

        base = status.speed_kmh or 0.0
        new_speed = max(0.0, min(6.0, round(base + delta, 1)))
        await self._run_action("set_speed", self._container.service.set_speed(new_speed))

    @on(Button.Pressed, "#btn-refresh")
    async def _btn_refresh(self) -> None:
        await self._refresh_status()

    @on(Button.Pressed, "#btn-start")
    async def _btn_start(self) -> None:
        await self._run_action("start", self._container.service.start())

    @on(Button.Pressed, "#btn-stop")
    async def _btn_stop(self) -> None:
        await self._run_action("stop", self._container.service.stop())

    @on(Button.Pressed, "#btn-on")
    async def _btn_on(self) -> None:
        await self._run_action("power_on", self._container.service.power_on())

    @on(Button.Pressed, "#btn-off")
    async def _btn_off(self) -> None:
        await self._run_action("power_off", self._container.service.power_off())

    @on(Button.Pressed, "#btn-lock")
    async def _btn_lock(self) -> None:
        await self._run_action("lock", self._container.service.lock())

    @on(Button.Pressed, "#btn-unlock")
    async def _btn_unlock(self) -> None:
        await self._run_action("unlock", self._container.service.unlock())

    @on(Button.Pressed, "#btn-set-speed")
    async def _btn_set_speed(self) -> None:
        value = self.query_one("#speed-input", Input).value.strip()
        await self._run_action("set_speed", self._container.service.set_speed(float(value)))

    @on(Button.Pressed, "#btn-speed-down")
    async def _btn_speed_down(self) -> None:
        await self._adjust_speed(-0.5)

    @on(Button.Pressed, "#btn-speed-up")
    async def _btn_speed_up(self) -> None:
        await self._adjust_speed(0.5)

    @on(Button.Pressed, "#btn-set-start-speed")
    async def _btn_set_start_speed(self) -> None:
        value = self.query_one("#start-speed-input", Input).value.strip()
        await self._run_action(
            "set_start_speed",
            self._container.service.set_start_speed(float(value)),
        )

    @on(Button.Pressed, "#btn-set-mode")
    async def _btn_set_mode(self) -> None:
        value = str(self.query_one("#mode-select", Select).value)
        await self._run_action("set_mode", self._container.service.set_mode(PadMode(value)))

    @on(Button.Pressed, "#btn-set-sensitivity")
    async def _btn_set_sensitivity(self) -> None:
        value = str(self.query_one("#sensitivity-select", Select).value)
        await self._run_action(
            "set_sensitivity",
            self._container.service.set_sensitivity(PadSensitivity(value)),
        )

    async def action_refresh(self) -> None:
        await self._refresh_status()

    async def action_start(self) -> None:
        await self._btn_start()

    async def action_stop(self) -> None:
        await self._btn_stop()

    async def action_quit(self) -> None:
        self.exit()

    async def action_speed_up(self) -> None:
        await self._adjust_speed(0.5)

    async def action_speed_down(self) -> None:
        await self._adjust_speed(-0.5)
