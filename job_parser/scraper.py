from __future__ import annotations

from typing import Iterable
from urllib.error import HTTPError
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from job_parser.hashing import vacancy_hash
from job_parser.html_fetcher import fetch_html, fetch_html_with_playwright
from job_parser.models import SourceDefinition, Vacancy

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    PLAYWRIGHT_TIMEOUT_ERRORS = (TimeoutError, PlaywrightTimeoutError)
except ImportError:
    PLAYWRIGHT_TIMEOUT_ERRORS = (TimeoutError,)

def _fetch_with_playwright_fallback(url: str, wait_for_selector: str | None) -> str:
    """Fetch page HTML with Playwright and retry once without selector wait on timeout."""
    try:
        return fetch_html_with_playwright(url, wait_for_selector=wait_for_selector)
    except PLAYWRIGHT_TIMEOUT_ERRORS:
        if wait_for_selector is None:
            raise
        return fetch_html_with_playwright(url, wait_for_selector=None)


def _text_or_attr(element, attribute: str | None) -> str:
    if element is None:
        return ""
    if attribute:
        value = element.get(attribute)
        if value:
            return str(value).strip()
    return element.get_text(" ", strip=True)


def _clean_robota_title(title: str) -> str:
    """Extract title from robota alt format: 'Title — вакансія в Company' -> 'Title'"""
    if " — вакансія в " in title:
        return title.split(" — вакансія в ")[0].strip()
    return title


def _resolve_link(base_url: str, href: str | None) -> str:
    if not href:
        return ""
    resolved = urljoin(base_url, href)
    scheme = urlparse(resolved).scheme.lower()
    if scheme and scheme not in {"http", "https"}:
        return ""
    return resolved


def parse_vacancies(html: str, source: SourceDefinition, page_url: str | None = None) -> tuple[list[Vacancy], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select(source.card_selector)
    vacancies: list[Vacancy] = []

    for card in cards:
        title_element = card.select_one(source.title_selector)
        # For robota sources, link is the card itself
        link_element = card if source.link_selector is None else card.select_one(source.link_selector)
        company_element = card.select_one(source.company_selector) if source.company_selector else None
        date_element = card.select_one(source.date_selector) if source.date_selector else None

        title = _text_or_attr(title_element, source.title_attribute)
        # For robota sources, clean the title from the alt format
        if source.key.startswith("robota_"):
            title = _clean_robota_title(title)
        
        link = _resolve_link(page_url or source.url, link_element.get("href") if link_element else None)
        company = _text_or_attr(company_element, source.company_attribute)
        date_text = _text_or_attr(date_element, source.date_attribute)

        if not title or not link:
            continue

        vacancies.append(
            Vacancy(
                source_key=source.key,
                source_name=source.name,
                category=source.category,
                title=title,
                link=link,
                company=company,
                date_text=date_text,
            )
        )

    next_url = None
    if source.next_selector:
        next_element = soup.select_one(source.next_selector)
        if next_element is not None:
            next_url = _resolve_link(page_url or source.url, next_element.get("href"))

    return vacancies, next_url


def iter_source_vacancies(source: SourceDefinition, max_pages: int | None = None) -> Iterable[Vacancy]:
    current_url = source.url
    pages_scanned = 0
    while current_url:
        if max_pages is not None and pages_scanned >= max_pages:
            break

        used_playwright = source.prefer_playwright
        if source.prefer_playwright:
            html = _fetch_with_playwright_fallback(current_url, wait_for_selector=source.wait_for_selector)
        else:
            try:
                html = fetch_html(current_url)
            except HTTPError as error:
                if error.code != 403:
                    raise
                html = _fetch_with_playwright_fallback(current_url, wait_for_selector=source.wait_for_selector)
                used_playwright = True
        pages_scanned += 1
        vacancies, next_url = parse_vacancies(html, source, current_url)

        # Some sources return a JS shell or anti-bot page to plain HTTP requests.
        # Retry once with Playwright when parsing returns no vacancy cards.
        if not vacancies and not used_playwright:
            html = _fetch_with_playwright_fallback(
                current_url,
                wait_for_selector=source.wait_for_selector or source.card_selector,
            )
            vacancies, next_url = parse_vacancies(html, source, current_url)

        for vacancy in vacancies:
            vacancy.hash = vacancy_hash(vacancy.company, vacancy.title)
            yield vacancy
        if max_pages is not None and pages_scanned >= max_pages:
            break
        if not next_url or next_url == current_url:
            break
        current_url = next_url
