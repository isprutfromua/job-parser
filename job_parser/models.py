from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Vacancy:
    source_key: str
    source_name: str
    category: str
    title: str
    link: str
    company: str = ""
    date_text: str = ""
    hash: str = ""


@dataclass
class SourceDefinition:
    key: str
    name: str
    category: str
    url: str
    card_selector: str
    title_selector: str
    link_selector: str | None
    company_selector: str | None
    date_selector: str | None
    next_selector: str | None
    title_attribute: str | None = None
    company_attribute: str | None = None
    date_attribute: str | None = None
    prefer_playwright: bool = False
    wait_for_selector: str | None = None

