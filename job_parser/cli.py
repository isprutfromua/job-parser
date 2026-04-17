from __future__ import annotations

import argparse
import logging

from job_parser.config import AppConfig
from job_parser.models import Vacancy
from job_parser.scheduler import run_worker
from job_parser.service import run_dry_run, run_once
from job_parser.sources import build_sources
from job_parser.storage import VacancyStore
from job_parser.telegram import TelegramClient


def print_dry_run_results(grouped_vacancies: dict[str, list[Vacancy]]) -> None:
    """Print dry run results grouped by source."""
    sources_by_key = {s.key: s for s in build_sources()}
    
    source_vacancies: dict[str, list[Vacancy]] = {}
    for vacancy in [v for vacancies in grouped_vacancies.values() for v in vacancies]:
        if vacancy.source_key not in source_vacancies:
            source_vacancies[vacancy.source_key] = []
        source_vacancies[vacancy.source_key].append(vacancy)
    
    print("\n" + "=" * 100)
    print("DRY RUN RESULTS (не записано в БД)")
    print("=" * 100)
    
    for source in build_sources():
        vacancies = source_vacancies.get(source.key, [])
        print(f"\n📌 {source.key} ({source.name})")
        print(f"   Категорія: {source.category}")
        print(f"   Вакансій знайдено: {len(vacancies)}")
        
        if vacancies:
            for i, v in enumerate(vacancies[:10], 1):
                print(f"   {i}. {v.title}")
                print(f"      📞 {v.company}")
                print(f"      🔗 {v.link}")
            if len(vacancies) > 10:
                print(f"   ... та ще {len(vacancies) - 10} вакансій")
        else:
            print("   ❌ Вакансій не знайдено")
    
    total = sum(len(v) for v in source_vacancies.values())
    print(f"\n{'=' * 100}")
    print(f"ВСЬОГО: {total} вакансій")
    print("=" * 100 + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="job-parser")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("once", help="Run a single scan")
    dry_run_parser = subparsers.add_parser("dry-run", help="Run a single scan without writing to the database or Telegram")
    dry_run_parser.add_argument("--pages", type=int, default=5, help="Maximum pages to scan per source")
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
    elif args.command == "dry-run":
        results = run_dry_run(max_pages=args.pages)
        print_dry_run_results(results)
    elif args.command == "worker":
        run_worker(config)


if __name__ == "__main__":
    main()

