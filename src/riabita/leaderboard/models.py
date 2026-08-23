"""SQLAlchemy mapping for persisted round results."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, Index, SmallInteger, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime

from riabita import config


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for the leaderboard schema."""


class LeaderboardEntryRow(Base):
    """One submitted score. Metrics are always engine-computed, never client input."""

    __tablename__ = "leaderboard_entries"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    round_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    player_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    nickname: Mapped[str] = mapped_column(
        String(config.NICKNAME_MAX_LENGTH), nullable=False
    )
    district_id: Mapped[str] = mapped_column(String(64), nullable=False)

    alloc_mobility: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    alloc_culture: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    alloc_tourism: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    alloc_socio: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    event_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    riz_final: Mapped[float] = mapped_column(Float, nullable=False)
    urban_yield: Mapped[float] = mapped_column(Float, nullable=False)
    risk: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe: Mapped[float] = mapped_column(Float, nullable=False)

    profile_id: Mapped[str] = mapped_column(String(32), nullable=False)
    rules_version: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    __table_args__ = (
        Index(
            "ix_leaderboard_ranking",
            "district_id",
            riz_final.desc(),
            "created_at",
        ),
    )
