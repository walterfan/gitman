from __future__ import annotations

import socket

DEFAULT_PORT = 9626
MAX_FALLBACK_ATTEMPTS = 100


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def choose_port(host: str, requested_port: int | None = None) -> int:
    if requested_port is not None:
        if not is_port_available(host, requested_port):
            raise OSError(f"Requested port {requested_port} is unavailable.")
        return requested_port

    for offset in range(MAX_FALLBACK_ATTEMPTS + 1):
        candidate = DEFAULT_PORT + offset
        if is_port_available(host, candidate):
            return candidate

    raise OSError(
        f"No available port found from {DEFAULT_PORT} "
        f"through {DEFAULT_PORT + MAX_FALLBACK_ATTEMPTS}."
    )
