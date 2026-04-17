from __future__ import annotations

import base64


def normalize_field(value: str) -> str:
    return " ".join(value.split()).strip().lower()


def vacancy_hash(company: str, title: str) -> str:
    payload = f"{normalize_field(company)}\n{normalize_field(title)}".encode("utf-8")
    return base64.b64encode(payload).decode("ascii")

