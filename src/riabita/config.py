"""Central configuration: every tunable game constant and runtime setting.

No other module may define a game constant. See
`.github/skills/riabita-implementation/references/simulation-rules.md`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np

RULES_VERSION: Final[str] = "2.0.0"

# --- Dimensions -------------------------------------------------------------

DIMENSION_KEYS: Final[tuple[str, str, str, str]] = (
    "mobility",
    "culture",
    "tourism",
    "socio",
)

DIMENSION_MIN: Final[float] = 0.0
DIMENSION_MAX: Final[float] = 100.0

# --- Budget -----------------------------------------------------------------

BUDGET_TOTAL: Final[int] = 100
ALLOCATION_MIN: Final[int] = 0
ALLOCATION_MAX: Final[int] = 100
CREDITS_PER_STEP: Final[float] = 10.0

# --- Strategy autoplay -------------------------------------------------------
# Turn horizons used when a strategy plays out the rest of the game for the
# player instead of a single one-shot allocation.

RANDOM_AUTOPLAY_MIN_TURNS: Final[int] = 3
RANDOM_AUTOPLAY_MAX_TURNS: Final[int] = 6
AI_AUTOPLAY_TURNS: Final[int] = 4

# --- Impact matrix ----------------------------------------------------------
# Rows are the investment area, columns the affected dimension, both in
# (mobility, culture, tourism, socio) order. Values are change per 10 credits.

IMPACT_MATRIX: Final[np.ndarray] = np.array(
    [
        [1.0, 0.4, 0.3, 0.2],
        [0.2, 1.0, 0.5, 0.4],
        [0.2, 0.3, 1.0, 0.0],
        [0.2, 0.3, -0.1, 1.0],
    ],
    dtype=float,
)

WEIGHTS: Final[np.ndarray] = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)

# --- Tourism pressure -------------------------------------------------------
# (threshold, coefficient), ordered high to low. Only the first match applies.

TOURISM_PRESSURE_TIERS: Final[tuple[tuple[float, float], ...]] = (
    (85.0, 0.5),
    (70.0, 0.2),
)

# --- Modifiers --------------------------------------------------------------

MODIFIER_EQUILIBRIUM: Final[str] = "equilibrium"
MODIFIER_OVERTOURISM_GAP: Final[str] = "overtourism_gap"
MODIFIER_CONCENTRATION: Final[str] = "concentration"
MODIFIER_DIVERSIFICATION: Final[str] = "diversification"

# Equilibrium bands on the population standard deviation of the four
# dimensions. The neutral band is inclusive at its upper bound: sigma of
# exactly 25 scores zero, and only sigma above 25 is penalized.
EQUILIBRIUM_EXCELLENT_BELOW: Final[float] = 10.0
EQUILIBRIUM_GOOD_BELOW: Final[float] = 15.0
EQUILIBRIUM_NEUTRAL_AT_MOST: Final[float] = 25.0

EQUILIBRIUM_EXCELLENT_POINTS: Final[float] = 10.0
EQUILIBRIUM_GOOD_POINTS: Final[float] = 5.0
EQUILIBRIUM_NEUTRAL_POINTS: Final[float] = 0.0
EQUILIBRIUM_HIGH_RISK_POINTS: Final[float] = -5.0

# (gap above socio, points), ordered high to low. Only the first match applies.
OVERTOURISM_GAP_TIERS: Final[tuple[tuple[float, float], ...]] = (
    (40.0, -10.0),
    (25.0, -5.0),
)

CONCENTRATION_LIMIT: Final[int] = 60
CONCENTRATION_POINTS: Final[float] = -5.0

# Funded dimension count -> bonus points. Documented assumption, not sourced
# from the research brief, which specifies only "low" and "high".
DIVERSIFICATION_BONUS: Final[dict[int, float]] = {4: 5.0, 3: 2.0}

# --- Metrics ----------------------------------------------------------------

SHARPE_RISK_EPSILON: Final[float] = 1e-9

PROFILE_STAGNANT: Final[str] = "stagnant"
PROFILE_VULNERABLE: Final[str] = "vulnerable"
PROFILE_RESILIENT: Final[str] = "resilient"
PROFILE_TRANSITIONAL: Final[str] = "transitional"

PROFILE_VULNERABLE_RISK: Final[float] = 25.0
PROFILE_RESILIENT_RISK: Final[float] = 15.0

# --- Display ----------------------------------------------------------------

VALUE_DECIMALS: Final[int] = 1
SHARPE_DECIMALS: Final[int] = 2

# --- Leaderboard ------------------------------------------------------------

NICKNAME_MIN_LENGTH: Final[int] = 3
NICKNAME_MAX_LENGTH: Final[int] = 24
NICKNAME_PATTERN: Final[str] = r"^[\w\s-]+$"

# --- Runtime settings -------------------------------------------------------

DEFAULT_LANGUAGE: Final[str] = "it"
DEFAULT_LEADERBOARD_LIMIT: Final[int] = 10
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH: Final[Path] = PROJECT_ROOT / ".data" / "riabita.sqlite3"
DEFAULT_DATABASE_URL: Final[str] = (
    f"sqlite+pysqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
)


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings. Never log or render these values."""

    database_url: str | None
    districts_path: str | None
    default_language: str
    leaderboard_limit: int


def _secret(key: str) -> str | None:
    """Read a Streamlit secret, returning None when unavailable."""
    try:
        import streamlit as st
    except ImportError:
        return None
    try:
        return str(st.secrets[key])
    except (KeyError, FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return None


def _resolve(key: str) -> str | None:
    value = os.environ.get(key)
    if value is not None and value.strip():
        return value.strip()
    secret = _secret(key)
    return secret.strip() if secret and secret.strip() else None


def get_settings() -> Settings:
    """Resolve settings from the environment, then Streamlit secrets."""
    raw_limit = _resolve("RIABITA_LEADERBOARD_LIMIT")
    try:
        limit = int(raw_limit) if raw_limit else DEFAULT_LEADERBOARD_LIMIT
    except ValueError:
        limit = DEFAULT_LEADERBOARD_LIMIT

    language = _resolve("RIABITA_DEFAULT_LANGUAGE") or DEFAULT_LANGUAGE

    return Settings(
        database_url=_resolve("RIABITA_DATABASE_URL") or DEFAULT_DATABASE_URL,
        districts_path=_resolve("RIABITA_DISTRICTS_PATH"),
        default_language=language.lower(),
        leaderboard_limit=max(1, limit),
    )
