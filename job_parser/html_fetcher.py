from __future__ import annotations

from urllib.request import Request, urlopen


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
}


def fetch_html(url: str, timeout_seconds: int = 30) -> str:
    request = Request(url, headers=DEFAULT_HEADERS)
    with urlopen(request, timeout=timeout_seconds) as response:
        content = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return content.decode(charset, errors="replace")


def fetch_html_with_playwright(
    url: str,
    timeout_seconds: int = 30000,
    wait_for_selector: str | None = None,
) -> str:
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "Playwright is not installed. Install it and run `playwright install` to use browser rendering."
        ) from error

    # Keep backward compatibility for callers that might pass timeout in seconds.
    timeout_ms = timeout_seconds * 1000 if timeout_seconds <= 1000 else timeout_seconds

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        # Add stealth script to bypass bot detection
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
              get: () => false,
            });
        """)

        # Some job portals keep background requests open, causing networkidle
        # navigation to time out in CI. Retry with progressively less strict states.
        wait_until_states = ["domcontentloaded", "load"]
        last_timeout_error: Exception | None = None

        try:
            for wait_until in wait_until_states:
                try:
                    page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                    if wait_for_selector:
                        page.wait_for_selector(wait_for_selector, timeout=timeout_ms)
                    return page.content()
                except PlaywrightTimeoutError as error:
                    last_timeout_error = error
            if last_timeout_error is not None:
                raise last_timeout_error
            raise RuntimeError("Playwright navigation failed for an unknown reason")
        finally:
            browser.close()

