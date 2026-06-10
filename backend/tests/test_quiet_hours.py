"""Quiet-hours window logic (pure)."""
from __future__ import annotations

from datetime import time

from app.notifications.preferences import _in_window


def test_overnight_window_wraps_midnight() -> None:
    start, end = time(22, 0), time(8, 0)
    assert _in_window(time(23, 0), start, end) is True   # late night
    assert _in_window(time(2, 0), start, end) is True    # early morning
    assert _in_window(time(12, 0), start, end) is False  # midday — notify ok


def test_same_day_window() -> None:
    start, end = time(1, 0), time(5, 0)
    assert _in_window(time(3, 0), start, end) is True
    assert _in_window(time(6, 0), start, end) is False


def test_empty_window_never_quiet() -> None:
    assert _in_window(time(3, 0), time(0, 0), time(0, 0)) is False
