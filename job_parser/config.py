from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _parse_env_value(raw_value: str) -> str:
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _load_env_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        os.environ[key] = _parse_env_value(raw_value)


def _load_local_env() -> None:
    project_root = Path(__file__).resolve().parents[1]
    for candidate in (Path.cwd() / ".env", project_root / ".env"):
        _load_env_file(candidate)


@dataclass
class AppConfig:
    db_path: Path
    telegram_bot_token: str
    telegram_chat_id: str
    interval_seconds: int = 7200
    timezone: str = "Europe/Kyiv"
    quiet_start_hour: int = 22
    quiet_end_hour: int = 8

    @classmethod
    def from_env(cls) -> "AppConfig":
        _load_local_env()
        db_path = Path(os.getenv("JOB_PARSER_DB_PATH", "./data/job_parser.sqlite3"))
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        interval_minutes = int(os.getenv("JOB_PARSER_INTERVAL_MINUTES", "120"))
        timezone = os.getenv("JOB_PARSER_TIMEZONE", "Europe/Kyiv").strip() or "Europe/Kyiv"
        quiet_start_hour = int(os.getenv("JOB_PARSER_QUIET_START_HOUR", "22"))
        quiet_end_hour = int(os.getenv("JOB_PARSER_QUIET_END_HOUR", "8"))
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID is required")
        if not (0 <= quiet_start_hour <= 23 and 0 <= quiet_end_hour <= 23):
            raise ValueError("JOB_PARSER_QUIET_START_HOUR and JOB_PARSER_QUIET_END_HOUR must be between 0 and 23")
        return cls(
            db_path=db_path,
            telegram_bot_token=token,
            telegram_chat_id=chat_id,
            interval_seconds=interval_minutes * 60,
            timezone=timezone,
            quiet_start_hour=quiet_start_hour,
            quiet_end_hour=quiet_end_hour,
        )

