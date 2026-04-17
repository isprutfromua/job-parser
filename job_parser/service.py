from __future__ import annotations

import logging
from collections import defaultdict

from job_parser.models import SourceDefinition, Vacancy
from job_parser.scraper import iter_source_vacancies
from job_parser.sources import build_sources
from job_parser.storage import VacancyStore
from job_parser.telegram import TelegramClient, format_category_message


logger = logging.getLogger(__name__)

CATEGORY_ORDER = ["remote, it", "vinnytsia, it", "remote, deftech", "vinnytsia, deftech"]


def run_once(store: VacancyStore, telegram: TelegramClient, sources: list[SourceDefinition] | None = None) -> dict[str, list[Vacancy]]:
    return run_scan(store=store, telegram=telegram, sources=sources)


def run_scan(
    store: VacancyStore,
    telegram: TelegramClient,
    sources: list[SourceDefinition] | None = None,
    *,
    max_pages: int | None = None,
) -> dict[str, list[Vacancy]]:
    sources = sources or build_sources()
    grouped_new_vacancies: dict[str, list[Vacancy]] = defaultdict(list)
    errors: list[str] = []
    run_id = store.start_run()

    for source in sources:
        try:
            logger.info("Scanning source %s", source.key)
            scanned_count = 0
            stopped_on_known = False
            for vacancy in iter_source_vacancies(source, max_pages=max_pages):
                scanned_count += 1
                if store.has_hash(vacancy.hash):
                    if source.stop_on_known:
                        stopped_on_known = True
                        logger.info(
                            "Stopping source %s after known vacancy %s",
                            source.key,
                            vacancy.title,
                        )
                        break
                    continue
                if store.save_vacancy(vacancy):
                    grouped_new_vacancies[vacancy.category].append(vacancy)
            logger.info(
                "Finished source %s scanned=%s stopped_on_known=%s",
                source.key,
                scanned_count,
                stopped_on_known,
            )
        except Exception as error:
            message = f"source={source.key}: {error}"
            errors.append(message)
            logger.exception("Source scan failed: %s", source.key)

    for category in CATEGORY_ORDER:
        vacancies = grouped_new_vacancies.get(category, [])
        if not vacancies:
            continue
        try:
            message = format_category_message(category, vacancies)
            telegram.send_message(message)
            logger.info("Sent Telegram message for category %s with %s vacancies", category, len(vacancies))
        except Exception as error:
            message = f"telegram={category}: {error}"
            errors.append(message)
            logger.exception("Telegram send failed for category %s", category)

    status = "success" if not errors else "partial_success"
    store.finish_run(run_id, status, "; ".join(errors)[:500])
    if errors:
        logger.warning("Run completed with errors: %s", errors)
    else:
        logger.info("Run completed successfully")
    return grouped_new_vacancies


