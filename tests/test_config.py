from __future__ import annotations

from py_xiaomi_walkingpad.types.errors import ConfigurationError
from py_xiaomi_walkingpad.interface.config import load_config


def test_load_config_success(monkeypatch):
    monkeypatch.setenv("WALKINGPAD_IP", "192.168.1.10")
    monkeypatch.setenv("WALKINGPAD_TOKEN", "abc123")
    monkeypatch.setenv("WALKINGPAD_MODEL", "ksmb.walkingpad.v1")
    monkeypatch.setenv("WALKINGPAD_POLLING_INTERVAL", "1.5")
    monkeypatch.setenv("WALKINGPAD_REQUEST_TIMEOUT", "4.0")

    cfg = load_config()

    assert cfg.walkingpad_ip == "192.168.1.10"
    assert cfg.walkingpad_token == "abc123"
    assert cfg.walkingpad_model == "ksmb.walkingpad.v1"
    assert cfg.polling_interval_seconds == 1.5
    assert cfg.request_timeout_seconds == 4.0


def test_load_config_missing_required(monkeypatch):
    monkeypatch.setenv("WALKINGPAD_IP", "")
    monkeypatch.setenv("WALKINGPAD_TOKEN", "")

    try:
        load_config()
        assert False, "Expected ConfigurationError"
    except ConfigurationError as exc:
        assert "WALKINGPAD_IP" in str(exc)
        assert "WALKINGPAD_TOKEN" in str(exc)


def test_load_config_invalid_polling_interval(monkeypatch):
    monkeypatch.setenv("WALKINGPAD_IP", "192.168.1.10")
    monkeypatch.setenv("WALKINGPAD_TOKEN", "abc123")
    monkeypatch.setenv("WALKINGPAD_POLLING_INTERVAL", "0")

    try:
        load_config()
        assert False, "Expected ConfigurationError"
    except ConfigurationError as exc:
        assert "must be > 0" in str(exc)


def test_load_config_invalid_request_timeout(monkeypatch):
    monkeypatch.setenv("WALKINGPAD_IP", "192.168.1.10")
    monkeypatch.setenv("WALKINGPAD_TOKEN", "abc123")
    monkeypatch.setenv("WALKINGPAD_REQUEST_TIMEOUT", "abc")

    try:
        load_config()
        assert False, "Expected ConfigurationError"
    except ConfigurationError as exc:
        assert "WALKINGPAD_REQUEST_TIMEOUT" in str(exc)
