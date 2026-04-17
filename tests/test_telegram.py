from job_parser.models import Vacancy
from job_parser.telegram import TelegramClient, format_category_message


def test_format_category_message_groups_as_requested() -> None:
    message = format_category_message(
        "remote, it",
        [
            Vacancy(
                source_key="x",
                source_name="y",
                category="remote, it",
                title="Python Developer",
                link="https://example.com/job/1",
            )
        ],
    )
    assert message == "нові вакансії в категорії remote, it:\n- Python Developer, https://example.com/job/1"


def test_send_message_splits_long_payloads(monkeypatch) -> None:
    calls: list[bytes] = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return b'{"ok": true, "result": {}}'

    def fake_urlopen(request, timeout):
        calls.append(request.data)
        return FakeResponse()

    monkeypatch.setattr("job_parser.telegram.urlopen", fake_urlopen)

    client = TelegramClient(bot_token="token", chat_id="chat")
    client.send_message("x" * 7000)

    assert len(calls) == 2

