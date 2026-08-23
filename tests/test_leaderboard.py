"""Leaderboard validation, submission integrity, ranking, and storage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from riabita import config
from riabita.domain.errors import LeaderboardUnavailable
from riabita.domain.models import Allocation, Dimensions, District, LeaderboardEntry
from riabita.engine.simulator import run_simulation
from riabita.events import get_event
from riabita.leaderboard import service
from riabita.leaderboard.repository import (
    InMemoryLeaderboardRepository,
    SqlAlchemyLeaderboardRepository,
    build_repository,
)

DISTRICT = District("san-lorenzo", "San Lorenzo", Dimensions(55, 40, 80, 35))
EVEN = Allocation(25, 25, 25, 25)


@pytest.fixture
def repo() -> InMemoryLeaderboardRepository:
    return InMemoryLeaderboardRepository()


@pytest.fixture
def result():
    return run_simulation(DISTRICT, EVEN, get_event("tourist_boom"))


def entry(
    riz: float, created_at: datetime, district_id: str = "san-lorenzo", **kwargs
) -> LeaderboardEntry:
    defaults = dict(
        entry_id=service.new_id(),
        round_id=service.new_id(),
        player_id=service.new_id(),
        nickname="Player",
        district_id=district_id,
        allocation=EVEN,
        event_id=None,
        riz_final=riz,
        urban_yield=1.0,
        risk=10.0,
        sharpe=0.1,
        profile_id=config.PROFILE_RESILIENT,
        rules_version=config.RULES_VERSION,
        created_at=created_at,
    )
    defaults.update(kwargs)
    return LeaderboardEntry(**defaults)  # type: ignore[arg-type]


# --- Nickname rules ---------------------------------------------------------


@pytest.mark.parametrize("nickname", ["Ana", "mario_rossi", "Roma 2024", "Jean-Luc"])
def test_valid_nicknames_are_accepted(nickname: str) -> None:
    assert service.is_valid_nickname(nickname)


@pytest.mark.parametrize(
    "nickname",
    ["ab", "", "   ", "x" * 25, "<script>alert(1)</script>", "drop; --", "a\x00b", "bell\x07"],
)
def test_invalid_nicknames_are_rejected(nickname: str) -> None:
    assert not service.is_valid_nickname(nickname)


def test_whitespace_control_characters_are_normalized_not_rejected() -> None:
    assert service.normalize_nickname("a\nb") == "a b"
    assert service.is_valid_nickname("a\nb")


def test_nickname_whitespace_is_normalized() -> None:
    assert service.normalize_nickname("  Anna   Maria ") == "Anna Maria"


# --- Submission -------------------------------------------------------------


def test_submission_copies_engine_metrics(repo, result) -> None:
    saved = service.submit_result(repo, result, "Ana", service.new_id(), service.new_id())
    assert saved is not None
    assert saved.riz_final == result.riz_final
    assert saved.urban_yield == result.urban_yield
    assert saved.risk == result.risk
    assert saved.sharpe == result.sharpe
    assert saved.profile_id == result.profile_id
    assert saved.rules_version == config.RULES_VERSION
    assert saved.event_id == "tourist_boom"


def test_submission_is_idempotent_per_round(repo, result) -> None:
    round_id = service.new_id()
    player = service.new_id()
    first = service.submit_result(repo, result, "Ana", player, round_id)
    second = service.submit_result(repo, result, "Ana", player, round_id)
    assert first is not None
    assert second is None
    assert len(service.top_entries(repo, 10)) == 1


def test_submission_rejects_an_invalid_nickname(repo, result) -> None:
    with pytest.raises(ValueError):
        service.submit_result(repo, result, "x", service.new_id(), service.new_id())


def test_submission_does_not_trust_a_client_score(repo, result) -> None:
    # The service signature accepts no score argument at all.
    import inspect

    parameters = set(inspect.signature(service.submit_result).parameters)
    assert not {"riz", "riz_final", "score"} & parameters


# --- Ranking ----------------------------------------------------------------


def test_top_orders_by_score_descending(repo) -> None:
    now = datetime.now(timezone.utc)
    for score in (10.0, 90.0, 50.0):
        repo.add(entry(score, now))
    assert [e.riz_final for e in service.top_entries(repo, 10)] == [90.0, 50.0, 10.0]


def test_ties_are_broken_by_earliest_submission(repo) -> None:
    now = datetime.now(timezone.utc)
    later = entry(50.0, now + timedelta(minutes=5), nickname="Later")
    earlier = entry(50.0, now, nickname="Earlier")
    repo.add(later)
    repo.add(earlier)
    assert [e.nickname for e in service.top_entries(repo, 10)] == ["Earlier", "Later"]


def test_top_respects_the_limit(repo) -> None:
    now = datetime.now(timezone.utc)
    for score in range(20):
        repo.add(entry(float(score), now))
    assert len(service.top_entries(repo, 5)) == 5


def test_filtering_by_district(repo) -> None:
    now = datetime.now(timezone.utc)
    repo.add(entry(80.0, now, district_id="eur"))
    repo.add(entry(70.0, now, district_id="san-lorenzo"))
    filtered = service.top_entries(repo, 10, district_id="eur")
    assert [e.district_id for e in filtered] == ["eur"]


def test_empty_repository_returns_an_empty_tuple(repo) -> None:
    assert service.top_entries(repo, 10) == ()


# --- Storage ----------------------------------------------------------------


def test_default_database_url_is_local_sqlite(monkeypatch) -> None:
    monkeypatch.delenv("RIABITA_DATABASE_URL", raising=False)
    monkeypatch.setattr(config, "_secret", lambda key: None)

    settings = config.get_settings()

    assert settings.database_url == config.DEFAULT_DATABASE_URL
    assert settings.database_url.startswith("sqlite+pysqlite:///")


def test_configured_sqlite_url_is_preserved(monkeypatch, tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'configured.sqlite3'}"
    monkeypatch.setenv("RIABITA_DATABASE_URL", database_url)

    assert config.get_settings().database_url == database_url


def test_no_database_url_means_no_repository() -> None:
    assert build_repository(None) is None
    assert build_repository("") is None


@pytest.fixture
def sql_repo():
    repository = SqlAlchemyLeaderboardRepository("sqlite+pysqlite:///:memory:")
    yield repository
    repository.dispose()


def test_sql_repository_round_trips_an_entry(sql_repo, result) -> None:
    saved = service.submit_result(
        sql_repo, result, "Ana", service.new_id(), service.new_id()
    )
    assert saved is not None
    stored = service.top_entries(sql_repo, 10)
    assert len(stored) == 1
    assert stored[0].nickname == "Ana"
    assert stored[0].riz_final == pytest.approx(result.riz_final)
    assert stored[0].allocation == EVEN


def test_sql_repository_enforces_round_idempotency(sql_repo, result) -> None:
    round_id = service.new_id()
    player = service.new_id()
    service.submit_result(sql_repo, result, "Ana", player, round_id)
    assert service.submit_result(sql_repo, result, "Ana", player, round_id) is None
    assert len(service.top_entries(sql_repo, 10)) == 1


def test_sql_repository_ranks_and_filters(sql_repo, result) -> None:
    for nickname in ("Alfa", "Beta"):
        service.submit_result(
            sql_repo, result, nickname, service.new_id(), service.new_id()
        )
    assert len(service.top_entries(sql_repo, 10, district_id="san-lorenzo")) == 2
    assert service.top_entries(sql_repo, 10, district_id="nowhere") == ()


def test_file_sqlite_persists_across_repository_instances(
    tmp_path: Path, result
) -> None:
    database_path = tmp_path / "nested" / "leaderboard.sqlite3"
    database_url = f"sqlite+pysqlite:///{database_path}"

    first = SqlAlchemyLeaderboardRepository(database_url)
    service.submit_result(first, result, "Ana", service.new_id(), service.new_id())
    first.dispose()

    second = SqlAlchemyLeaderboardRepository(database_url)
    stored = service.top_entries(second, 10)
    second.dispose()

    assert database_path.is_file()
    assert len(stored) == 1
    assert stored[0].nickname == "Ana"


def test_sql_metacharacters_are_stored_literally(sql_repo, result) -> None:
    nickname = "Bobby Tables"
    service.submit_result(sql_repo, result, nickname, service.new_id(), service.new_id())
    hostile_filter = "san-lorenzo'; DROP TABLE leaderboard_entries; --"
    assert service.top_entries(sql_repo, 10, district_id=hostile_filter) == ()
    # The table survived the parameterized query.
    assert service.top_entries(sql_repo, 10)[0].nickname == nickname


def test_unreachable_database_raises_leaderboard_unavailable() -> None:
    with pytest.raises(LeaderboardUnavailable):
        SqlAlchemyLeaderboardRepository("postgresql+psycopg://user@127.0.0.1:1/none")


def test_unavailable_message_hides_connection_details() -> None:
    try:
        SqlAlchemyLeaderboardRepository("postgresql+psycopg://secret:pw@127.0.0.1:1/x")
    except LeaderboardUnavailable as error:
        assert "secret" not in str(error)
        assert "pw" not in str(error)
    else:  # pragma: no cover - the connection must not succeed
        pytest.fail("expected LeaderboardUnavailable")
