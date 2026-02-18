from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import timedelta

import typer

from py_xiaomi_walkingpad.app.container import build_container
from py_xiaomi_walkingpad.domain.models import PadMode, PadSensitivity, PadStatus
from py_xiaomi_walkingpad.interface.tui import WalkingPadTuiApp

app = typer.Typer(help="WalkingPad CLI")


def _status_to_dict(status: PadStatus) -> dict[str, object]:
    data = asdict(status)
    wt = data.get("walking_time")
    if isinstance(wt, timedelta):
        data["walking_time"] = int(wt.total_seconds())
    data["mode"] = status.mode.value if status.mode else None
    data["sensitivity"] = status.sensitivity.value if status.sensitivity else None
    return data


@app.command("status")
def status(quick: bool = typer.Option(False, "--quick", help="Use quick status read")) -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.get_status(quick=quick)
        typer.echo(json.dumps(_status_to_dict(result), indent=2))

    asyncio.run(_run())


@app.command("start")
def start() -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.start()
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("stop")
def stop() -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.stop()
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("power-on")
def power_on() -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.power_on()
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("power-off")
def power_off() -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.power_off()
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("lock")
def lock() -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.lock()
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("unlock")
def unlock() -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.unlock()
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("set-speed")
def set_speed(speed: float = typer.Argument(..., help="Speed in km/h (0..6)")) -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.set_speed(speed)
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("set-start-speed")
def set_start_speed(speed: float = typer.Argument(..., help="Start speed in km/h (0..6)")) -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.set_start_speed(speed)
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("set-mode")
def set_mode(mode: PadMode = typer.Argument(..., help="auto|manual|off")) -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.set_mode(mode)
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("set-sensitivity")
def set_sensitivity(sensitivity: PadSensitivity = typer.Argument(..., help="high|medium|low")) -> None:
    async def _run() -> None:
        container = build_container()
        result = await container.service.set_sensitivity(sensitivity)
        typer.echo(result.message)

    asyncio.run(_run())


@app.command("tui")
def tui() -> None:
    WalkingPadTuiApp(build_container).run()

