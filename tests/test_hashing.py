from job_parser.hashing import vacancy_hash


def test_vacancy_hash_is_stable_and_normalized() -> None:
    first = vacancy_hash("Acme  LLC", "Senior Python Developer")
    second = vacancy_hash("acme llc", "  Senior   Python Developer  ")
    assert first == second

