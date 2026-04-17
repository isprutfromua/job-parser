from __future__ import annotations

import logging
import time

from job_parser.config import AppConfig
from job_parser.service import run_once
from job_parser.storage import VacancyStore
from job_parser.telegram import TelegramClient


logger = logging.getLogger(__name__)


def run_worker(config: AppConfig) -> None:
    store = VacancyStore(config.db_path)
    telegram = TelegramClient(config.telegram_bot_token, config.telegram_chat_id)

    while True:
        logger.info("Starting scan cycle")
        run_once(store=store, telegram=telegram)
        logger.info("Scan cycle complete, sleeping for %s seconds", config.interval_seconds)
        time.sleep(config.interval_seconds)

