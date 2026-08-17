from __future__ import annotations

import pytest

from gitman import ports
from gitman.ports import DEFAULT_PORT, choose_port


def test_choose_port_returns_default_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ports, "is_port_available", lambda _host, _port: True)
    assert DEFAULT_PORT == 9626
    assert choose_port("127.0.0.1") == DEFAULT_PORT


def test_choose_port_falls_back_from_occupied_default(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_available(_host: str, port: int) -> bool:
        return port != DEFAULT_PORT

    monkeypatch.setattr(ports, "is_port_available", fake_available)
    assert choose_port("127.0.0.1") == DEFAULT_PORT + 1


def test_choose_port_skips_multiple_occupied_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_available(_host: str, port: int) -> bool:
        return port not in {9626, 9627}

    monkeypatch.setattr(ports, "is_port_available", fake_available)
    assert choose_port("127.0.0.1") == 9628


def test_choose_port_raises_for_unavailable_explicit_port(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ports, "is_port_available", lambda _host, _port: False)
    with pytest.raises(OSError, match="unavailable"):
        choose_port("127.0.0.1", 9999)
