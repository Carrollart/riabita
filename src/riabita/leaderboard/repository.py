"""Leaderboard storage.

The protocol keeps query construction out of the engine and the views. Two
implementations exist: SQLAlchemy for local SQLite or production PostgreSQL,
and in-memory for isolated tests.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Protocol

from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from riabita.domain.errors import LeaderboardUnavailable
from riabita.domain.models import Allocation, LeaderboardEntry
from riabita.leaderboard.models import Base, LeaderboardEntryRow


class LeaderboardRepository(Protocol):
    """Everything the leaderboard service needs from storage."""

    def add(self, entry: LeaderboardEntry) -> None: ...

    def exists(self, round_id: str) -> bool: ...

    def top(
        self, limit: int, district_id: str | None = None
    ) -> tuple[LeaderboardEntry, ...]: ...


def _rank_key(entry: LeaderboardEntry) -> tuple[float, float]:
    return (-entry.riz_final, entry.created_at.timestamp())


class InMemoryLeaderboardRepository:
    """Test double with the same ordering semantics as the SQL implementation."""

    def __init__(self) -> None:
        self._entries: list[LeaderboardEntry] = []

    def add(self, entry: LeaderboardEntry) -> None:
        self._entries.append(entry)

    def exists(self, round_id: str) -> bool:
        return any(e.round_id == round_id for e in self._entries)

    def top(
        self, limit: int, district_id: str | None = None
    ) -> tuple[LeaderboardEntry, ...]:
        matching = [
            e
            for e in self._entries
            if district_id is None or e.district_id == district_id
        ]
        return tuple(sorted(matching, key=_rank_key)[:limit])


class SqlAlchemyLeaderboardRepository:
    """SQLite/PostgreSQL storage. All access uses ORM constructs."""

    def __init__(self, database_url: str, *, create_schema: bool = True) -> None:
        try:
            _ensure_sqlite_parent(database_url)
            self._engine = create_engine(database_url, pool_pre_ping=True, future=True)
            if create_schema:
                Base.metadata.create_all(self._engine)
        except SQLAlchemyError as error:
            raise LeaderboardUnavailable("cannot open the score store") from error
        self._session_factory = sessionmaker(bind=self._engine, future=True)

    def add(self, entry: LeaderboardEntry) -> None:
        try:
            with self._session_factory() as session, session.begin():
                session.add(_to_row(entry))
        except SQLAlchemyError as error:
            raise LeaderboardUnavailable("cannot save the score") from error

    def exists(self, round_id: str) -> bool:
        statement = select(LeaderboardEntryRow.id).where(
            LeaderboardEntryRow.round_id == uuid.UUID(round_id)
        )
        try:
            with self._session_factory() as session:
                return session.execute(statement).first() is not None
        except SQLAlchemyError as error:
            raise LeaderboardUnavailable("cannot read the score store") from error

    def top(
        self, limit: int, district_id: str | None = None
    ) -> tuple[LeaderboardEntry, ...]:
        statement = select(LeaderboardEntryRow)
        if district_id is not None:
            statement = statement.where(LeaderboardEntryRow.district_id == district_id)
        statement = statement.order_by(
            LeaderboardEntryRow.riz_final.desc(),
            LeaderboardEntryRow.created_at.asc(),
        ).limit(limit)
        try:
            with self._session_factory() as session:
                rows = session.execute(statement).scalars().all()
        except SQLAlchemyError as error:
            raise LeaderboardUnavailable("cannot read the score store") from error
        return tuple(_to_entry(row) for row in rows)

    def dispose(self) -> None:
        self._engine.dispose()


def _to_row(entry: LeaderboardEntry) -> LeaderboardEntryRow:
    return LeaderboardEntryRow(
        id=uuid.UUID(entry.entry_id),
        round_id=uuid.UUID(entry.round_id),
        player_id=uuid.UUID(entry.player_id),
        nickname=entry.nickname,
        district_id=entry.district_id,
        alloc_mobility=entry.allocation.mobility,
        alloc_culture=entry.allocation.culture,
        alloc_tourism=entry.allocation.tourism,
        alloc_socio=entry.allocation.socio,
        event_id=entry.event_id,
        riz_final=entry.riz_final,
        urban_yield=entry.urban_yield,
        risk=entry.risk,
        sharpe=entry.sharpe,
        profile_id=entry.profile_id,
        rules_version=entry.rules_version,
        created_at=entry.created_at,
    )


def _to_entry(row: LeaderboardEntryRow) -> LeaderboardEntry:
    return LeaderboardEntry(
        entry_id=str(row.id),
        round_id=str(row.round_id),
        player_id=str(row.player_id),
        nickname=row.nickname,
        district_id=row.district_id,
        allocation=Allocation(
            row.alloc_mobility,
            row.alloc_culture,
            row.alloc_tourism,
            row.alloc_socio,
        ),
        event_id=row.event_id,
        riz_final=row.riz_final,
        urban_yield=row.urban_yield,
        risk=row.risk,
        sharpe=row.sharpe,
        profile_id=row.profile_id,
        rules_version=row.rules_version,
        created_at=row.created_at,
    )


def build_repository(database_url: str | None) -> LeaderboardRepository | None:
    """Return the configured SQL repository, or None when explicitly disabled."""
    if not database_url:
        return None
    return SqlAlchemyLeaderboardRepository(database_url)


def _ensure_sqlite_parent(database_url: str) -> None:
    """Create the parent directory for a file-backed SQLite database."""
    url = make_url(database_url)
    database = url.database
    if url.get_backend_name() != "sqlite" or not database:
        return
    if database == ":memory:" or database.startswith("file:"):
        return
    try:
        Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise LeaderboardUnavailable("cannot prepare the score store") from error
