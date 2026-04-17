from __future__ import annotations

from pathlib import Path

from job_parser.config import AppConfig


def test_app_config_loads_values_from_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("JOB_PARSER_DB_PATH", raising=False)
    monkeypatch.delenv("JOB_PARSER_INTERVAL_MINUTES", raising=False)
    monkeypatch.delenv("JOB_PARSER_TIMEZONE", raising=False)
    monkeypatch.delenv("JOB_PARSER_QUIET_START_HOUR", raising=False)
    monkeypatch.delenv("JOB_PARSER_QUIET_END_HOUR", raising=False)

    Path(".env").write_text(
        """
        TELEGRAM_BOT_TOKEN=123456:ABCDEF
        TELEGRAM_CHAT_ID=-1001234567890
        JOB_PARSER_DB_PATH=./data/test.sqlite3
        JOB_PARSER_INTERVAL_MINUTES=15
        JOB_PARSER_TIMEZONE=Europe/Kyiv
        JOB_PARSER_QUIET_START_HOUR=22
        JOB_PARSER_QUIET_END_HOUR=8
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    config = AppConfig.from_env()

    assert config.telegram_bot_token == "123456:ABCDEF"
    assert config.telegram_chat_id == "-1001234567890"
    assert str(config.db_path) == "data/test.sqlite3"
    assert config.interval_seconds == 900
    assert config.timezone == "Europe/Kyiv"
    assert config.quiet_start_hour == 22
    assert config.quiet_end_hour == 8
