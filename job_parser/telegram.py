from __future__ import annotations

import json
from collections import OrderedDict
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from job_parser.models import Vacancy


MAX_MESSAGE_LENGTH = 3500


def _chunk_message(text: str, limit: int = MAX_MESSAGE_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    for line in text.splitlines():
        candidate = line if not current else f"{current}\n{line}"
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        while len(line) > limit:
            chunks.append(line[:limit])
            line = line[limit:]

        current = line

    if current:
        chunks.append(current)

    return chunks


@dataclass
class TelegramClient:
    bot_token: str
    chat_id: str
    timeout_seconds: int = 30

    def send_message(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        for chunk in _chunk_message(text):
            payload = urlencode(
                {
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "disable_web_page_preview": "true",
                }
            ).encode("utf-8")
            request = Request(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read().decode("utf-8")
                    data = json.loads(body)
                    if not data.get("ok"):
                        raise RuntimeError(f"Telegram API error: {data}")
            except (HTTPError, URLError) as error:
                raise RuntimeError(f"Failed to send Telegram message: {error}") from error


def format_category_message(category: str, vacancies: Iterable[Vacancy]) -> str:
    grouped_by_source: OrderedDict[str, list[Vacancy]] = OrderedDict()
    total = 0

    for vacancy in vacancies:
        source_label = vacancy.source_name.strip() or vacancy.source_key.strip() or "Unknown source"
        grouped_by_source.setdefault(source_label, []).append(vacancy)
        total += 1

    lines = [f"📌 Категорія: {category}", f"📊 Вакансій: {total}"]
    for source, source_vacancies in grouped_by_source.items():
        lines.append("")
        lines.append(f"🧭 {source} ({len(source_vacancies)}):")
        for vacancy in source_vacancies:
            lines.append(f"• {vacancy.title} — {vacancy.link}")

    return "\n".join(lines)

