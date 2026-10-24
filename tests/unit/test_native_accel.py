"""
Tests for optional Rust native accelerator bridge and pacing fallback.
"""

import os

from app.core.native_accel import (
    build_pace_schedule,
    clear_native_cache,
    native_status,
    pace_schedule_python,
    resolve_native_binary,
    spintax_expand_batch,
)
from app.core.spintax import SpintaxProcessor


class TestPaceSchedulePython:
    def test_first_slot_zero_wait(self):
        slots = pace_schedule_python(
            4,
            [10, 20],
            messages_per_minute=30,
            messages_per_hour=500,
            jitter_seconds=0.0,
            max_concurrent_accounts=2,
            seed=1,
        )
        assert len(slots) == 4
        assert slots[0]["wait_before_ms"] == 0
        assert slots[0]["account_id"] == 10
        assert slots[1]["account_id"] == 20

    def test_build_pace_schedule_always_returns(self):
        slots = build_pace_schedule(
            3,
            [1],
            messages_per_minute=60,
            jitter_seconds=0.0,
            seed=42,
        )
        assert len(slots) == 3
        assert all("wait_before_ms" in s for s in slots)


class TestSpintaxBatch:
    def test_expand_batch_matches_count(self):
        processor = SpintaxProcessor(seed=99)
        samples = processor.expand_batch("Hello {A|B|C}", 12)
        assert len(samples) == 12
        for sample in samples:
            assert sample in {"Hello A", "Hello B", "Hello C"}

    def test_preview_samples_count(self):
        processor = SpintaxProcessor()
        samples = processor.get_preview_samples("Hi {x|y}", 5)
        assert len(samples) == 5


class TestNativeBridge:
    def test_status_dict_shape(self):
        clear_native_cache()
        status = native_status()
        assert "enabled" in status
        assert "available" in status
        assert "backend" in status
        assert status["backend"] in {"rust", "python"}

    def test_disabled_via_env(self):
        clear_native_cache()
        old = os.environ.get("TMMS_NATIVE_ACCEL")
        try:
            os.environ["TMMS_NATIVE_ACCEL"] = "0"
            clear_native_cache()
            assert resolve_native_binary() is None
            assert spintax_expand_batch("Hi {a|b}", 20, force=True) is None
        finally:
            if old is None:
                os.environ.pop("TMMS_NATIVE_ACCEL", None)
            else:
                os.environ["TMMS_NATIVE_ACCEL"] = old
            clear_native_cache()
