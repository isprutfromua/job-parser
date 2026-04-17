from job_parser.models import SourceDefinition
from job_parser.scraper import iter_source_vacancies, parse_vacancies
from job_parser.sources import build_sources


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

