from job_parser.models import SourceDefinition
from job_parser.scraper import iter_source_vacancies, parse_vacancies
from job_parser.sources import build_sources
from urllib.error import HTTPError


def test_parse_dou_like_vacancy_card() -> None:
    source = next(item for item in build_sources() if item.key == "dou_remote_it")
    html = """
    <div class="l-items">
      <div class="l-vacancy">
        <strong>Acme</strong>
        <a href="/vacancies/1">Senior Python Developer</a>
        <div class="date">15 квітня 2026</div>
      </div>
    </div>
    <div class="more-btn"><a href="/jobs/?page=2">more</a></div>
    """
    vacancies, next_url = parse_vacancies(html, source, "https://jobs.dou.ua/vacancies/?remote")
    assert len(vacancies) == 1
    assert vacancies[0].title == "Senior Python Developer"
    assert vacancies[0].company == "Acme"
    assert vacancies[0].link == "https://jobs.dou.ua/vacancies/1"
    assert vacancies[0].date_text == "15 квітня 2026"
    assert next_url == "https://jobs.dou.ua/jobs/?page=2"


def test_parse_ignores_javascript_next_links() -> None:
    source = next(item for item in build_sources() if item.key == "dou_remote_it")
    html = """
    <div class="l-items">
      <div class="l-vacancy">
        <strong>Acme</strong>
        <a href="/vacancies/1">Senior Python Developer</a>
      </div>
    </div>
    <div class="more-btn"><a href="javascript:;">more</a></div>
    """
    vacancies, next_url = parse_vacancies(html, source, "https://jobs.dou.ua/vacancies/?remote")
    assert len(vacancies) == 1
    assert vacancies[0].link == "https://jobs.dou.ua/vacancies/1"
    assert next_url == ""


def test_parse_work_ua_with_updated_container_id() -> None:
    source = next(item for item in build_sources() if item.key == "work_remote_it")
    html = """
    <div id="pjax-job-list">
      <div>
        <img alt="Acme" />
        <h2><a href="/jobs/1/" title="сьогодні">Senior Python Developer</a></h2>
      </div>
    </div>
    """
    vacancies, next_url = parse_vacancies(html, source, "https://www.work.ua/jobs-remote-it-industry-it/?days=123")
    assert len(vacancies) == 1
    assert vacancies[0].title == "Senior Python Developer"
    assert vacancies[0].company == "Acme"
    assert vacancies[0].link == "https://www.work.ua/jobs/1/"
    assert vacancies[0].date_text == "сьогодні"
    assert next_url is None


def test_iter_source_vacancies_honors_max_pages(monkeypatch) -> None:
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
        next_selector=".next",
        prefer_playwright=False,
    )
    html_by_url = {
        "https://example.com/page-1": '<div class="card"><a href="/job-1">Job 1</a></div><a class="next" href="/page-2">next</a>',
        "https://example.com/page-2": '<div class="card"><a href="/job-2">Job 2</a></div><a class="next" href="/page-3">next</a>',
        "https://example.com/page-3": '<div class="card"><a href="/job-3">Job 3</a></div><a class="next" href="/page-4">next</a>',
        "https://example.com/page-4": '<div class="card"><a href="/job-4">Job 4</a></div><a class="next" href="/page-5">next</a>',
        "https://example.com/page-5": '<div class="card"><a href="/job-5">Job 5</a></div><a class="next" href="/page-6">next</a>',
    }
    seen_urls: list[str] = []

    def fake_fetch_html(url: str, timeout_seconds: int = 30) -> str:
        seen_urls.append(url)
        return html_by_url[url]

    monkeypatch.setattr("job_parser.scraper.fetch_html", fake_fetch_html)

    vacancies = list(iter_source_vacancies(source, max_pages=5))

    assert seen_urls == [
        "https://example.com/page-1",
        "https://example.com/page-2",
        "https://example.com/page-3",
        "https://example.com/page-4",
        "https://example.com/page-5",
    ]
    assert len(vacancies) == 5


def test_iter_source_vacancies_falls_back_to_playwright_on_403(monkeypatch) -> None:
    source = SourceDefinition(
        key="example_work",
        name="example_work",
        category="remote, it",
        url="https://example.com/page-1",
        card_selector=".card",
        title_selector="a",
        link_selector="a",
        company_selector=None,
        date_selector=None,
        next_selector=None,
        prefer_playwright=False,
    )

    def fake_fetch_html(url: str, timeout_seconds: int = 30) -> str:
        raise HTTPError(url, 403, "Forbidden", hdrs=None, fp=None)

    def fake_fetch_html_with_playwright(
        url: str,
        timeout_seconds: int = 30000,
        wait_for_selector: str | None = None,
    ) -> str:
        return '<div class="card"><a href="/job-1">Job 1</a></div>'

    monkeypatch.setattr("job_parser.scraper.fetch_html", fake_fetch_html)
    monkeypatch.setattr("job_parser.scraper.fetch_html_with_playwright", fake_fetch_html_with_playwright)

    vacancies = list(iter_source_vacancies(source, max_pages=1))

    assert len(vacancies) == 1
    assert vacancies[0].title == "Job 1"
    assert vacancies[0].link == "https://example.com/job-1"


def test_iter_source_vacancies_retries_with_playwright_when_static_parse_is_empty(monkeypatch) -> None:
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
        prefer_playwright=False,
        wait_for_selector=".card a",
    )

    def fake_fetch_html(url: str, timeout_seconds: int = 30) -> str:
        # Simulate a bot/check page that contains no matching vacancy cards.
        return "<html><body><div>checking your browser...</div></body></html>"

    def fake_fetch_html_with_playwright(
        url: str,
        timeout_seconds: int = 30000,
        wait_for_selector: str | None = None,
    ) -> str:
        assert wait_for_selector == ".card a"
        return '<div class="card"><a href="/job-1">Job 1</a></div>'

    monkeypatch.setattr("job_parser.scraper.fetch_html", fake_fetch_html)
    monkeypatch.setattr("job_parser.scraper.fetch_html_with_playwright", fake_fetch_html_with_playwright)

    vacancies = list(iter_source_vacancies(source, max_pages=1))

    assert len(vacancies) == 1
    assert vacancies[0].title == "Job 1"
    assert vacancies[0].link == "https://example.com/job-1"


def test_iter_source_vacancies_playwright_timeout_retry(monkeypatch) -> None:
    source = SourceDefinition(
        key="test_source_with_timeout",
        name="test_source_with_timeout",
        category="remote, it",
        url="https://example.com/page-1",
        card_selector=".card",
        title_selector="a",
        link_selector="a",
        company_selector=None,
        date_selector=None,
        next_selector=None,
        prefer_playwright=False,
        wait_for_selector=".card a",
    )
    playwright_calls: list[str | None] = []

    def fake_fetch_html(url: str, timeout_seconds: int = 30) -> str:
        return "<html><body>checking...</body></html>"

    def fake_fetch_html_with_playwright(
        url: str,
        timeout_seconds: int = 30000,
        wait_for_selector: str | None = None,
    ) -> str:
        playwright_calls.append(wait_for_selector)
        if wait_for_selector is not None:
            raise TimeoutError("Page.wait_for_selector: Timeout 30000ms exceeded.")
        return '<div class="card"><a href="/job-1">Job 1</a></div>'

    monkeypatch.setattr("job_parser.scraper.fetch_html", fake_fetch_html)
    monkeypatch.setattr("job_parser.scraper.fetch_html_with_playwright", fake_fetch_html_with_playwright)

    vacancies = list(iter_source_vacancies(source, max_pages=1))

    assert playwright_calls == [".card a", None]
    assert len(vacancies) == 1
    assert vacancies[0].title == "Job 1"
