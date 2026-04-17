from __future__ import annotations

from pathlib import Path

from job_parser.config import AppConfig


def test_app_config_loads_values_from_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("JOB_PARSER_DB_PATH", raising=False)
    monkeypatch.delenv("JOB_PARSER_INTERVAL_MINUTES", raising=False)

    Path(".env").write_text(
        """
        TELEGRAM_BOT_TOKEN=123456:ABCDEF
        TELEGRAM_CHAT_ID=-1001234567890
        JOB_PARSER_DB_PATH=./data/test.sqlite3
        JOB_PARSER_INTERVAL_MINUTES=15
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    config = AppConfig.from_env()

    assert config.telegram_bot_token == "123456:ABCDEF"
    assert config.telegram_chat_id == "-1001234567890"
    assert str(config.db_path) == "data/test.sqlite3"
    assert config.interval_seconds == 900
