# py-xiaomi-walkingpad

Control a Xiaomi WalkingPad from Python using [`python-miio`](https://python-miio.readthedocs.io/en/latest/index.html), with both:

- a command-line interface (CLI)
- a keyboard-driven terminal UI (TUI)

The codebase is split into reusable layers so future interfaces (for example a REST API) can reuse the same backend service.

## Features

- Async-ready application service on top of synchronous `python-miio`
- Device command support for start/stop, power, lock, speed, start speed, mode, and sensitivity
- Live status polling and event stream for interface consumers
- Keyboard-only TUI controls (no mouse required)
- Built-in timing diagnostics for command latency analysis

## Device compatibility

Default model is `ksmb.walkingpad.v1` (configured via `.env`).

> `python-miio` may report `ksmb.walkingpad.v3` in its internal model list depending on version/implementation. This project still allows explicit model configuration and wraps the available WalkingPad command surface.

## Installation

```bash
python -m venv .venv
python -m pip install -e '.[dev]'
```

## Configuration

Create a local environment file:

```bash
cp .env.example .env
```

Example [`.env`](.env):

```dotenv
WALKINGPAD_IP=192.168.1.100
WALKINGPAD_TOKEN=YOUR_32_CHAR_TOKEN
WALKINGPAD_MODEL=ksmb.walkingpad.v1
WALKINGPAD_POLLING_INTERVAL=1.0
WALKINGPAD_REQUEST_TIMEOUT=5.0
```

## Usage

### CLI

```bash
py-xiaomi-walkingpad status
py-xiaomi-walkingpad status --quick
py-xiaomi-walkingpad start
py-xiaomi-walkingpad stop
py-xiaomi-walkingpad power-on
py-xiaomi-walkingpad power-off
py-xiaomi-walkingpad lock
py-xiaomi-walkingpad unlock
py-xiaomi-walkingpad set-speed 3.0
py-xiaomi-walkingpad set-start-speed 2.0
py-xiaomi-walkingpad set-mode manual
py-xiaomi-walkingpad set-sensitivity medium
```

### TUI

```bash
py-xiaomi-walkingpad tui
```

Core shortcuts:

- `q`, `Esc`, `Ctrl+C` — quit
- `r` — refresh status
- `s` — start
- `x` — stop
- `+` / `-` — speed adjust in 0.5 km/h steps
## Performance diagnostics

The TUI log prints timing entries:

`timing op=<name> wait=<ms> run=<ms> total=<ms> ok=<bool>`

Interpretation:

- `wait`: time waiting for internal service IO lock
- `run`: device call execution time
- `total`: end-to-end operation time

This helps separate app-side contention from device/network delay.

## Architecture overview

- Infra layer: [`WalkingPadAdapter`](src/py_xiaomi_walkingpad/infra/miio_adapter.py), config loading
- Application layer: [`AsyncWalkingPadService`](src/py_xiaomi_walkingpad/app/service.py), event bus
- Interface layer: CLI + TUI

The service contract lives in [`contracts.py`](src/py_xiaomi_walkingpad/domain/contracts.py), enabling additional interfaces without coupling to TUI internals.

## Testing

```bash
PYTHONPATH=src python -m pytest -q
```

Current tests cover configuration, event bus fan-out, and service polling/snapshot behavior.

## License

MIT. See [`LICENSE`](LICENSE).
