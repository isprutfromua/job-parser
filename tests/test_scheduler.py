from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from job_parser.scheduler import _is_quiet_time, _seconds_until_quiet_end


def test_is_quiet_time_overnight_window() -> None:
    tz = ZoneInfo("Europe/Kyiv")

    assert _is_quiet_time(datetime(2026, 4, 17, 22, 0, tzinfo=tz), 22, 8)
    assert _is_quiet_time(datetime(2026, 4, 18, 1, 30, tzinfo=tz), 22, 8)
    assert not _is_quiet_time(datetime(2026, 4, 18, 8, 0, tzinfo=tz), 22, 8)
    assert not _is_quiet_time(datetime(2026, 4, 18, 12, 0, tzinfo=tz), 22, 8)


def test_seconds_until_quiet_end_overnight_window() -> None:
    tz = ZoneInfo("Europe/Kyiv")

    at_23 = datetime(2026, 4, 17, 23, 0, tzinfo=tz)
    at_07_30 = datetime(2026, 4, 18, 7, 30, tzinfo=tz)

    assert _seconds_until_quiet_end(at_23, 22, 8) == 9 * 3600
    assert _seconds_until_quiet_end(at_07_30, 22, 8) == 30 * 60
