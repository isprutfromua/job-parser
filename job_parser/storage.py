from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from job_parser.models import Vacancy


class VacancyStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                create table if not exists seen_vacancies (
                    hash text primary key,
                    source_key text not null,
                    source_name text not null,
                    category text not null,
                    title text not null,
                    company text not null,
                    link text not null,
                    date_text text not null default '',
                    first_seen_at text not null default (datetime('now'))
                );

                create table if not exists runs (
                    id integer primary key autoincrement,
                    started_at text not null default (datetime('now')),
                    finished_at text,
                    status text not null,
                    note text not null default ''
                );
                """
            )

    def has_hash(self, hash_value: str) -> bool:
        with self.connection() as connection:
            row = connection.execute(
                "select 1 from seen_vacancies where hash = ? limit 1",
                (hash_value,),
            ).fetchone()
            return row is not None

    def save_vacancy(self, vacancy: Vacancy) -> bool:
        try:
            with self.connection() as connection:
                connection.execute(
                    """
                    insert into seen_vacancies (
                        hash, source_key, source_name, category, title, company, link, date_text
                    ) values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        vacancy.hash,
                        vacancy.source_key,
                        vacancy.source_name,
                        vacancy.category,
                        vacancy.title,
                        vacancy.company,
                        vacancy.link,
                        vacancy.date_text,
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def start_run(self) -> int:
        with self.connection() as connection:
            cursor = connection.execute(
                "insert into runs (status, note) values (?, ?)",
                ("running", ""),
            )
            return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str, note: str = "") -> None:
        with self.connection() as connection:
            connection.execute(
                """
                update runs
                set finished_at = datetime('now'), status = ?, note = ?
                where id = ?
                """,
                (status, note, run_id),
            )

