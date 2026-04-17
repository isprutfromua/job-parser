from __future__ import annotations

from job_parser.models import SourceDefinition, Vacancy
from job_parser.service import run_dry_run


def test_run_dry_run_does_not_touch_store_or_telegram(monkeypatch) -> None:
    source = SourceDefinition(
        key="example",
        name="example",
        category="remote, it",
        url="https://example.com/page-1",
        card_selector=".card",
        title_selector="a",
        link_selector="a",
        company_selector=None,
        date_selector=None,
        next_selector=None,
    )

    def fake_iter_source_vacancies(source_definition, max_pages=None):
        yield Vacancy(
            source_key=source_definition.key,
            source_name=source_definition.name,
            category=source_definition.category,
            title="Job 1",
            link="https://example.com/job-1",
        )

    monkeypatch.setattr("job_parser.service.iter_source_vacancies", fake_iter_source_vacancies)

    grouped = run_dry_run(sources=[source], max_pages=5)

    assert grouped["remote, it"][0].title == "Job 1"