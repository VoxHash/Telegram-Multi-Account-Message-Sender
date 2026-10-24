"""
Network connectivity helpers for cloud backup / restore UX.
"""

from __future__ import annotations

import socket
from typing import Optional, Tuple

# User-facing markers used by the GUI to pick offline-specific copy.
OFFLINE_ERROR_MARKER = "OFFLINE_OR_UNREACHABLE"
DRIVE_UNAVAILABLE_MARKER = "DRIVE_UNAVAILABLE"

_NETWORK_ERROR_TOKENS = (
    "nameresolutionerror",
    "temporary failure in name resolution",
    "failed to establish a new connection",
    "connection refused",
    "connection reset",
    "connection aborted",
    "network is unreachable",
    "no route to host",
    "timed out",
    "timeout",
    "unreachable",
    "offline",
    "ssl",
    "eof occurred in violation",
    "getaddrinfo failed",
    "nodename nor servname",
    "[errno 101]",
    "[errno 110]",
    "[errno 111]",
    "httplib2.error",
    "socket.gaierror",
)


def check_network_available(timeout: float = 3.0) -> bool:
    """
    Return True when a basic outbound UDP/TCP path appears available.

    Uses public DNS resolvers as a lightweight reachability probe (no HTTP).
    """
    endpoints: Tuple[Tuple[str, int], ...] = (
        ("8.8.8.8", 53),
        ("1.1.1.1", 53),
        ("9.9.9.9", 53),
    )
    for host, port in endpoints:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            continue
    return False


def is_network_exception(exc: BaseException) -> bool:
    """Return True when ``exc`` (or its cause chain) looks like a network failure."""
    seen: set[int] = set()
    current: Optional[BaseException] = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(
            current,
            (
                ConnectionError,
                TimeoutError,
                socket.timeout,
                socket.gaierror,
                OSError,
            ),
        ):
            # OSError is broad; only treat clearly network-related subclasses/messages.
            if isinstance(current, OSError) and not isinstance(
                current, (ConnectionError, TimeoutError, socket.timeout, socket.gaierror)
            ):
                message = str(current).lower()
                if not any(token in message for token in _NETWORK_ERROR_TOKENS):
                    current = current.__cause__ or current.__context__
                    continue
            return True
        message = str(current).lower()
        if any(token in message for token in _NETWORK_ERROR_TOKENS):
            return True
        current = current.__cause__ or current.__context__
    return False


def format_offline_error(operation: str = "cloud operation") -> str:
    """Build a stable, parseable offline error message for service → GUI."""
    return (
        f"{OFFLINE_ERROR_MARKER}: Cannot complete {operation} while offline or "
        "when cloud storage is unreachable. Check your internet connection, "
        "VPN/firewall, and try again when online. Local data was not modified."
    )


def format_drive_unavailable_error(detail: str = "") -> str:
    """Build a Drive-unavailable message (auth/API down, not necessarily no IP)."""
    suffix = f" Details: {detail}" if detail else ""
    return (
        f"{DRIVE_UNAVAILABLE_MARKER}: Google Drive is temporarily unavailable.{suffix} "
        "Verify network access to googleapis.com and try again. "
        "If you were restoring, your local database was not replaced."
    )


def is_offline_error_message(message: str) -> bool:
    """True when a service error string should use offline restore UX copy."""
    text = (message or "").upper()
    return OFFLINE_ERROR_MARKER in text or DRIVE_UNAVAILABLE_MARKER in text
