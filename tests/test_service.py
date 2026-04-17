from __future__ import annotations

from job_parser.models import SourceDefinition, Vacancy
from job_parser.service import run_once


def test_run_once_persists_only_new_vacancy_and_stops_on_known(monkeypatch) -> None:
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
    saved: list[Vacancy] = []
    sent_messages: list[str] = []

    class FakeStore:
        def start_run(self) -> int:
            return 1

        def has_hash(self, hash_value: str) -> bool:
            return hash_value == "known"

        def save_vacancy(self, vacancy: Vacancy) -> bool:
            saved.append(vacancy)
            return True

        def finish_run(self, run_id: int, status: str, note: str = "") -> None:
            assert run_id == 1
            assert status == "success"

    class FakeTelegram:
        def send_message(self, text: str) -> None:
            sent_messages.append(text)

    def fake_iter_source_vacancies(source_definition, max_pages=None):
        yield Vacancy(
            source_key=source_definition.key,
            source_name=source_definition.name,
            category=source_definition.category,
            title="Job 1",
            link="https://example.com/job-1",
            hash="new",
        )
        yield Vacancy(
            source_key=source_definition.key,
            source_name=source_definition.name,
            category=source_definition.category,
            title="Known Job",
            link="https://example.com/job-known",
            hash="known",
        )

    monkeypatch.setattr("job_parser.service.iter_source_vacancies", fake_iter_source_vacancies)

    grouped = run_once(store=FakeStore(), telegram=FakeTelegram(), sources=[source])

    assert len(saved) == 1
    assert saved[0].title == "Job 1"
    assert grouped["remote, it"][0].title == "Job 1"
    assert len(sent_messages) == 1


def test_run_once_continues_past_known_vacancy_when_source_disables_stop(monkeypatch) -> None:
    source = SourceDefinition(
        key="work_like",
        name="work_like",
        category="remote, it",
        url="https://example.com/page-1",
        card_selector=".card",
        title_selector="a",
        link_selector="a",
        company_selector=None,
        date_selector=None,
        next_selector=None,
        stop_on_known=False,
    )
    saved: list[Vacancy] = []

    class FakeStore:
        def start_run(self) -> int:
            return 1

        def has_hash(self, hash_value: str) -> bool:
            return hash_value == "known"

        def save_vacancy(self, vacancy: Vacancy) -> bool:
            saved.append(vacancy)
            return True

        def finish_run(self, run_id: int, status: str, note: str = "") -> None:
            assert run_id == 1
            assert status == "success"

    class FakeTelegram:
        def send_message(self, text: str) -> None:
            pass

    def fake_iter_source_vacancies(source_definition, max_pages=None):
        yield Vacancy(
            source_key=source_definition.key,
            source_name=source_definition.name,
            category=source_definition.category,
            title="Known Job",
            link="https://example.com/job-known",
            hash="known",
        )
        yield Vacancy(
            source_key=source_definition.key,
            source_name=source_definition.name,
            category=source_definition.category,
            title="Job 2",
            link="https://example.com/job-2",
            hash="new",
        )

    monkeypatch.setattr("job_parser.service.iter_source_vacancies", fake_iter_source_vacancies)

    grouped = run_once(store=FakeStore(), telegram=FakeTelegram(), sources=[source])

    assert len(saved) == 1
    assert saved[0].title == "Job 2"
    assert grouped["remote, it"][0].title == "Job 2"