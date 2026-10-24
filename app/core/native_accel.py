"""
Bridge to the optional Rust native accelerator (`tmms_native`).

Used for CPU-bound parallel spintax batch expansion and compact multi-account
pacing schedules so campaign prep stays off the Python GIL and uses less
transient memory than equivalent pure-Python loops.

Fallback: if the binary is missing, disabled, or returns an error, callers use
pure Python implementations (see `spintax.py` / `throttler` helpers here).
"""

from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

# Batch size where IPC overhead is typically offset by rayon parallelism.
_NATIVE_BATCH_MIN = 8
_DEFAULT_TIMEOUT_SEC = 120


def _env_flag(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


def native_accel_enabled() -> bool:
    """Whether native acceleration may be used (env / settings)."""
    if not _env_flag("TMMS_NATIVE_ACCEL", True):
        return False
    try:
        from ..services.settings import get_settings

        return bool(getattr(get_settings(), "native_accel_enabled", True))
    except Exception:
        return True


def _candidate_binaries() -> List[Path]:
    """Search order for the sidecar binary."""
    names = ["tmms_native", "tmms_native.exe"]
    env_bin = os.environ.get("TMMS_NATIVE_BIN")
    candidates: List[Path] = []
    if env_bin:
        candidates.append(Path(env_bin))

    # Package / repo roots relative to this file: app/core/native_accel.py
    here = Path(__file__).resolve()
    roots = [
        here.parents[2],  # repo root when running from source
        Path.cwd(),
        Path(sys.prefix),
        Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "_MEIPASS", None) else None,
    ]
    for root in roots:
        if root is None or str(root) == ".":
            continue
        for name in names:
            candidates.append(root / "bin" / name)
            candidates.append(root / "native" / "tmms_native" / "target" / "release" / name)

    for name in names:
        which = shutil.which(name)
        if which:
            candidates.append(Path(which))

    # Deduplicate while preserving order
    seen = set()
    unique: List[Path] = []
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


@lru_cache(maxsize=1)
def resolve_native_binary() -> Optional[Path]:
    """Return path to an executable `tmms_native`, or None."""
    if not native_accel_enabled():
        return None
    for path in _candidate_binaries():
        try:
            if path.is_file() and os.access(path, os.X_OK):
                return path
        except OSError:
            continue
    return None


def clear_native_cache() -> None:
    """Clear cached binary resolution (for tests)."""
    resolve_native_binary.cache_clear()


def is_native_available() -> bool:
    """True if the Rust sidecar is present and responds to ping."""
    binary = resolve_native_binary()
    if not binary:
        return False
    result = _invoke({"op": "ping"}, timeout=5)
    return bool(result and result.get("ok"))


def _invoke(request: Dict[str, Any], timeout: float = _DEFAULT_TIMEOUT_SEC) -> Optional[Dict[str, Any]]:
    """Run one JSON request against the sidecar. Returns None on any failure."""
    binary = resolve_native_binary()
    if not binary:
        return None
    try:
        payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
        completed = subprocess.run(
            [str(binary)],
            input=payload,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if completed.returncode != 0 and not completed.stdout:
            return None
        raw = completed.stdout.decode("utf-8", errors="replace").strip()
        if not raw:
            return None
        data = json.loads(raw)
        if not isinstance(data, dict) or not data.get("ok"):
            return None
        return data
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, ValueError):
        return None


def spintax_expand_batch(
    text: str, count: int, seed: Optional[int] = None, *, force: bool = False
) -> Optional[List[str]]:
    """
    Parallel spintax expansion via Rust.

    Returns None to signal Python fallback. Skips native for tiny batches unless
    `force=True` (IPC cost would dominate).
    """
    if count <= 0:
        return []
    if not force and count < _NATIVE_BATCH_MIN:
        return None
    req: Dict[str, Any] = {"op": "spintax_expand", "text": text or "", "count": int(count)}
    if seed is not None:
        req["seed"] = int(seed) & 0xFFFFFFFFFFFFFFFF
    # Scale timeout with workload
    timeout = max(_DEFAULT_TIMEOUT_SEC, min(600, 5 + count // 500))
    data = _invoke(req, timeout=timeout)
    if not data:
        return None
    texts = data.get("texts")
    if not isinstance(texts, list) or len(texts) != count:
        return None
    return [str(t) for t in texts]


def spintax_process_native(text: str, seed: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Single expansion via Rust (usually not worth IPC; used for parity tests)."""
    req: Dict[str, Any] = {"op": "spintax_process", "text": text or ""}
    if seed is not None:
        req["seed"] = int(seed) & 0xFFFFFFFFFFFFFFFF
    data = _invoke(req, timeout=10)
    if not data or "text" not in data:
        return None
    return {
        "text": str(data["text"]),
        "variants_count": int(data.get("variants_count") or 1),
        "backend": "rust",
    }


def pace_schedule(
    recipient_count: int,
    account_ids: List[int],
    messages_per_minute: int,
    messages_per_hour: int = 60,
    jitter_seconds: float = 0.0,
    max_concurrent_accounts: int = 1,
    seed: Optional[int] = None,
) -> Optional[List[Dict[str, Any]]]:
    """Build send slots via Rust. Returns None for Python fallback."""
    if recipient_count <= 0:
        return []
    req: Dict[str, Any] = {
        "op": "pace_schedule",
        "recipient_count": int(recipient_count),
        "account_ids": [int(a) for a in account_ids],
        "messages_per_minute": int(max(1, messages_per_minute)),
        "messages_per_hour": int(max(1, messages_per_hour)),
        "jitter_seconds": float(max(0.0, jitter_seconds)),
        "max_concurrent_accounts": int(max(1, max_concurrent_accounts)),
    }
    if seed is not None:
        req["seed"] = int(seed) & 0xFFFFFFFFFFFFFFFF
    timeout = max(30, min(300, 5 + recipient_count // 10_000))
    data = _invoke(req, timeout=timeout)
    if not data:
        return None
    slots = data.get("slots")
    if not isinstance(slots, list) or len(slots) != recipient_count:
        return None
    out: List[Dict[str, Any]] = []
    for slot in slots:
        if not isinstance(slot, dict):
            return None
        out.append(
            {
                "recipient_index": int(slot["recipient_index"]),
                "account_id": int(slot["account_id"]),
                "wait_before_ms": int(slot["wait_before_ms"]),
            }
        )
    return out


def pace_schedule_python(
    recipient_count: int,
    account_ids: List[int],
    messages_per_minute: int,
    messages_per_hour: int = 60,
    jitter_seconds: float = 0.0,
    max_concurrent_accounts: int = 1,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Pure-Python pacing schedule (fallback; mirrors Rust semantics closely)."""
    if recipient_count <= 0:
        return []
    accounts = list(account_ids) if account_ids else [0]
    mpm = max(1, messages_per_minute)
    mph = max(1, messages_per_hour)
    min_global = max(60.0 / mpm, 3600.0 / mph)
    concurrent = float(max(1, max_concurrent_accounts))
    per_account = min_global * min(len(accounts), concurrent) / max(concurrent, 1.0)

    rng = random.Random(seed) if seed is not None else random.Random()
    next_account = [0.0] * len(accounts)
    next_global = 0.0
    prev_send_at = 0.0
    slots: List[Dict[str, Any]] = []

    for i in range(recipient_count):
        acct_idx = i % len(accounts)
        send_at = max(next_global, next_account[acct_idx])
        if jitter_seconds > 0:
            send_at += rng.uniform(0.0, jitter_seconds)
        wait_before = 0.0 if i == 0 else max(0.0, send_at - prev_send_at)
        slots.append(
            {
                "recipient_index": i,
                "account_id": int(accounts[acct_idx]),
                "wait_before_ms": int(round(wait_before * 1000.0)),
            }
        )
        prev_send_at = send_at
        next_global = send_at + min_global
        next_account[acct_idx] = send_at + per_account

    return slots


def build_pace_schedule(
    recipient_count: int,
    account_ids: List[int],
    messages_per_minute: int,
    messages_per_hour: int = 60,
    jitter_seconds: float = 0.0,
    max_concurrent_accounts: int = 1,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Native schedule with automatic Python fallback."""
    native = pace_schedule(
        recipient_count,
        account_ids,
        messages_per_minute,
        messages_per_hour=messages_per_hour,
        jitter_seconds=jitter_seconds,
        max_concurrent_accounts=max_concurrent_accounts,
        seed=seed,
    )
    if native is not None:
        return native
    return pace_schedule_python(
        recipient_count,
        account_ids,
        messages_per_minute,
        messages_per_hour=messages_per_hour,
        jitter_seconds=jitter_seconds,
        max_concurrent_accounts=max_concurrent_accounts,
        seed=seed,
    )


def native_status() -> Dict[str, Any]:
    """Diagnostic snapshot for logs / about panel."""
    binary = resolve_native_binary()
    available = False
    version = None
    if binary:
        ping = _invoke({"op": "ping"}, timeout=5)
        if ping and ping.get("ok"):
            available = True
            version = ping.get("version")
    return {
        "enabled": native_accel_enabled(),
        "available": available,
        "binary": str(binary) if binary else None,
        "version": version,
        "backend": "rust" if available else "python",
    }
