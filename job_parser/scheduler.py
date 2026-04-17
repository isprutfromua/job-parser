from __future__ import annotations

from datetime import datetime, timedelta
import logging
import time
from zoneinfo import ZoneInfo

from job_parser.config import AppConfig
from job_parser.storage import VacancyStore
from job_parser.telegram import TelegramClient


logger = logging.getLogger(__name__)


def _is_quiet_time(now: datetime, quiet_start_hour: int, quiet_end_hour: int) -> bool:
    if quiet_start_hour == quiet_end_hour:
        return False
    if quiet_start_hour < quiet_end_hour:
        return quiet_start_hour <= now.hour < quiet_end_hour
    return now.hour >= quiet_start_hour or now.hour < quiet_end_hour


def _seconds_until_quiet_end(now: datetime, quiet_start_hour: int, quiet_end_hour: int) -> int:
    if not _is_quiet_time(now, quiet_start_hour, quiet_end_hour):
        return 0

    end_at = now.replace(hour=quiet_end_hour, minute=0, second=0, microsecond=0)
    if now.hour >= quiet_start_hour and quiet_start_hour > quiet_end_hour:
        end_at = end_at + timedelta(days=1)
    elif quiet_start_hour < quiet_end_hour and now >= end_at:
        end_at = end_at + timedelta(days=1)

    return max(1, int((end_at - now).total_seconds()))


def run_worker(config: AppConfig) -> None:
    from job_parser.service import run_once

    store = VacancyStore(config.db_path)
    telegram = TelegramClient(config.telegram_bot_token, config.telegram_chat_id)
    timezone = ZoneInfo(config.timezone)

    while True:
        now = datetime.now(timezone)
        if _is_quiet_time(now, config.quiet_start_hour, config.quiet_end_hour):
            sleep_for = _seconds_until_quiet_end(now, config.quiet_start_hour, config.quiet_end_hour)
            logger.info(
                "Quiet hours active in %s (%s:00-%s:00), sleeping for %s seconds",
                config.timezone,
                config.quiet_start_hour,
                config.quiet_end_hour,
                sleep_for,
            )
            time.sleep(sleep_for)
            continue

        logger.info("Starting scan cycle")
        run_once(store=store, telegram=telegram)
        logger.info("Scan cycle complete, sleeping for %s seconds", config.interval_seconds)
        time.sleep(config.interval_seconds)

