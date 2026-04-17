from __future__ import annotations

import argparse
import logging

from job_parser.config import AppConfig
from job_parser.scheduler import run_worker
from job_parser.service import run_once
from job_parser.storage import VacancyStore
from job_parser.telegram import TelegramClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-parser")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("once", help="Run a single scan")
    subparsers.add_parser("worker", help="Run the continuous 2-hour worker")
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    config = AppConfig.from_env()

    if args.command == "once":
        store = VacancyStore(config.db_path)
        telegram = TelegramClient(config.telegram_bot_token, config.telegram_chat_id)
        run_once(store=store, telegram=telegram)
    elif args.command == "worker":
        run_worker(config)


if __name__ == "__main__":
    main()

