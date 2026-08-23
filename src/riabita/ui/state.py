"""Round lifecycle and session state.

Owns the fairness guarantees: one seed per round, one event shared by all three
strategies, and benchmark allocations built without seeing that event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import numpy as np
import streamlit as st

from riabita import config, events, strategies
from riabita.data.loader import DistrictCatalog, load_districts
from riabita.domain.models import Allocation, District, Event, SimulationResult
from riabita.engine.simulator import run_simulation
from riabita.leaderboard.service import new_id

KEY_LANGUAGE = "language"
KEY_PLAYER_ID = "player_id"
KEY_ROUND = "round"
KEY_SUBMITTED = "submitted_round_ids"
SLIDER_KEYS = tuple(f"budget_{key}" for key in config.DIMENSION_KEYS)


@dataclass(frozen=True)
class Round:
    """One completed simulation and its benchmarks, all sharing an event."""

    round_id: str
    district_id: str
    event: Event | None
    player: SimulationResult
    ai: SimulationResult
    random: SimulationResult
    ai_allocation: Allocation
    random_allocation: Allocation


@st.cache_data(show_spinner=False)
def _cached_districts(path: str | None, cache_token: float) -> DistrictCatalog:
    return load_districts(path)


def load_catalog(path: str | None) -> DistrictCatalog:
    """Load districts once per source, refreshing when the file changes."""
    token = 0.0
    if path:
        try:
            import os

            token = os.path.getmtime(path)
        except OSError:
            token = 0.0
    return _cached_districts(path, token)


def init_state(default_language: str) -> None:
    st.session_state.setdefault(KEY_LANGUAGE, default_language)
    st.session_state.setdefault(KEY_PLAYER_ID, str(uuid.uuid4()))
    st.session_state.setdefault(KEY_ROUND, None)
    st.session_state.setdefault(KEY_SUBMITTED, set())
    for key in SLIDER_KEYS:
        st.session_state.setdefault(key, config.BUDGET_TOTAL // 4)


def language() -> str:
    return st.session_state[KEY_LANGUAGE]


def set_language(value: str) -> None:
    st.session_state[KEY_LANGUAGE] = value


def player_id() -> str:
    return st.session_state[KEY_PLAYER_ID]


def current_round() -> Round | None:
    return st.session_state[KEY_ROUND]


def reset_budget() -> None:
    for key in SLIDER_KEYS:
        st.session_state[key] = config.BUDGET_TOTAL // 4


def current_allocation() -> Allocation:
    return Allocation.from_array([st.session_state[k] for k in SLIDER_KEYS])


def mark_submitted(round_id: str) -> None:
    st.session_state[KEY_SUBMITTED].add(round_id)


def is_submitted(round_id: str) -> bool:
    return round_id in st.session_state[KEY_SUBMITTED]


def play_round(
    district: District,
    allocation: Allocation,
    seed: int | None = None,
) -> Round:
    """Score the player and both benchmarks against one shared event."""
    rng = np.random.default_rng(seed)

    # Benchmarks allocate first, from the baseline only, so no strategy can
    # react to the event that is about to be drawn.
    ai_credits = strategies.ai_allocation(district.baseline)
    random_credits = strategies.random_allocation(rng)

    event = events.draw_event(rng)

    return Round(
        round_id=new_id(),
        district_id=district.district_id,
        event=event,
        player=run_simulation(district, allocation, event),
        ai=run_simulation(district, ai_credits, event),
        random=run_simulation(district, random_credits, event),
        ai_allocation=ai_credits,
        random_allocation=random_credits,
    )


def store_round(value: Round) -> None:
    st.session_state[KEY_ROUND] = value
