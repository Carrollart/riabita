"""Leaderboard orchestration: nickname rules, submission, and ranked reads."""

from __future__ import annotations

import re
import uuid

from riabita import config
from riabita.domain.models import LeaderboardEntry, SimulationResult
from riabita.leaderboard.models import utcnow
from riabita.leaderboard.repository import LeaderboardRepository

_NICKNAME = re.compile(config.NICKNAME_PATTERN)


def normalize_nickname(nickname: str) -> str:
    return " ".join(nickname.split())


def is_valid_nickname(nickname: str) -> bool:
    """Length and character allowlist. Rejects markup and control characters."""
    cleaned = normalize_nickname(nickname)
    if not (
        config.NICKNAME_MIN_LENGTH <= len(cleaned) <= config.NICKNAME_MAX_LENGTH
    ):
        return False
    return bool(_NICKNAME.fullmatch(cleaned))


def new_id() -> str:
    return str(uuid.uuid4())


def submit_result(
    repository: LeaderboardRepository,
    result: SimulationResult,
    nickname: str,
    player_id: str,
    round_id: str,
) -> LeaderboardEntry | None:
    """Persist a round. Returns None when the round was already submitted.

    Every metric comes from `result`, which the engine produced server-side.
    Raises LeaderboardUnavailable when storage is unreachable.
    """
    cleaned = normalize_nickname(nickname)
    if not is_valid_nickname(cleaned):
        raise ValueError("invalid nickname")

    if repository.exists(round_id):
        return None

    entry = LeaderboardEntry(
        entry_id=new_id(),
        round_id=round_id,
        player_id=player_id,
        nickname=cleaned,
        district_id=result.district_id,
        allocation=result.allocation,
        event_id=result.event.event_id if result.event else None,
        riz_final=result.riz_final,
        urban_yield=result.urban_yield,
        risk=result.risk,
        sharpe=result.sharpe,
        profile_id=result.profile_id,
        rules_version=result.rules_version,
        created_at=utcnow(),
    )
    repository.add(entry)
    return entry


def top_entries(
    repository: LeaderboardRepository,
    limit: int = config.DEFAULT_LEADERBOARD_LIMIT,
    district_id: str | None = None,
) -> tuple[LeaderboardEntry, ...]:
    """Highest RIz first, ties broken by the earliest submission."""
    return repository.top(max(1, limit), district_id)
