from job_parser.models import Vacancy
from job_parser.telegram import TelegramClient, format_category_message


def test_format_category_message_groups_as_requested() -> None:
    message = format_category_message(
        "remote, it",
        [
            Vacancy(
                source_key="dou_remote_it",
                source_name="DOU",
                category="remote, it",
                title="Python Developer",
                link="https://example.com/job/1",
            ),
            Vacancy(
                source_key="djinni_remote_it",
                source_name="Djinni",
                category="remote, it",
                title="Backend Engineer",
                link="https://example.com/job/2",
            ),
            Vacancy(
                source_key="dou_remote_it",
                source_name="DOU",
                category="remote, it",
                title="DevOps Engineer",
                link="https://example.com/job/3",
            ),
        ],
    )
    assert message == (
        "📌 Категорія: remote, it\n"
        "📊 Вакансій: 3\n"
        "\n"
        "🧭 DOU (2):\n"
        "• Python Developer — https://example.com/job/1\n"
        "• DevOps Engineer — https://example.com/job/3\n"
        "\n"
        "🧭 Djinni (1):\n"
        "• Backend Engineer — https://example.com/job/2"
    )


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

