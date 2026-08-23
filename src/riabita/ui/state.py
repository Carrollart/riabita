"""Progressive round lifecycle and session state.

Owns the fairness guarantees: one event per turn shared by all three strategies,
and benchmark allocations built without seeing that turn's event.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import streamlit as st

from riabita import config, events, strategies
from riabita.data.loader import DistrictCatalog, load_districts
from riabita.domain.errors import ValidationError
from riabita.domain.models import Allocation, Dimensions, District, Event, SimulationResult
from riabita.domain.validation import validate_turn_allocation
from riabita.engine.simulator import run_turn
from riabita.leaderboard.service import new_id

KEY_LANGUAGE = "language"
KEY_PLAYER_ID = "player_id"
KEY_ROUND = "round"
KEY_DISTRICT = "active_district_id"
KEY_SUBMITTED = "submitted_round_ids"
KEY_STEP_MODE = "strategy_step_mode"
KEY_STRATEGY_QUEUE = "strategy_queue"
SLIDER_KEYS = tuple(f"budget_{key}" for key in config.DIMENSION_KEYS)

RANDOM_STRATEGY = "random"
AI_STRATEGY = "ai"


@dataclass
class StrategyQueue:
    """Turns still to be played for an in-progress autoplay strategy."""

    kind: str
    turns: list[int] = field(default_factory=list)
    rng: np.random.Generator = field(default_factory=np.random.default_rng)


@dataclass(frozen=True)
class Turn:
    """One completed investment turn and its shared event."""

    number: int
    credits_spent: int
    event: Event | None
    player_allocation: Allocation
    ai_allocation: Allocation
    random_allocation: Allocation


@dataclass(frozen=True)
class Round:
    """A progressive 100-credit game and its latest cumulative results."""

    round_id: str
    district_id: str
    event: Event | None
    player: SimulationResult
    ai: SimulationResult
    random: SimulationResult
    ai_allocation: Allocation
    random_allocation: Allocation
    remaining_credits: int
    turns: tuple[Turn, ...]

    @property
    def is_complete(self) -> bool:
        """Whether all credits in the game have been invested."""
        return self.remaining_credits == 0

    @property
    def turn_count(self) -> int:
        """Number of completed investment turns."""
        return len(self.turns)


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
    st.session_state.setdefault(KEY_DISTRICT, None)
    st.session_state.setdefault(KEY_SUBMITTED, set())
    st.session_state.setdefault(KEY_STEP_MODE, False)
    st.session_state.setdefault(KEY_STRATEGY_QUEUE, None)
    for key in SLIDER_KEYS:
        st.session_state.setdefault(key, config.ALLOCATION_MIN)


def language() -> str:
    return st.session_state[KEY_LANGUAGE]


def set_language(value: str) -> None:
    st.session_state[KEY_LANGUAGE] = value


def player_id() -> str:
    return st.session_state[KEY_PLAYER_ID]


def current_round() -> Round | None:
    return st.session_state[KEY_ROUND]


def is_district_locked() -> bool:
    """Whether the district must stay fixed until the active game ends."""
    current = current_round()
    return current is not None and not current.is_complete


def select_district(district_id: str) -> None:
    """Start fresh when the player changes district."""
    if is_district_locked() or st.session_state[KEY_DISTRICT] == district_id:
        return
    st.session_state[KEY_DISTRICT] = district_id
    reset_game()


def reset_turn_allocation() -> None:
    """Clear the controls for the next investment turn."""
    for key in SLIDER_KEYS:
        st.session_state[key] = config.ALLOCATION_MIN


def reset_budget() -> None:
    """Reset the current turn controls without discarding completed turns."""
    reset_turn_allocation()


def reset_game() -> None:
    """Discard the current game and restore the full 100-credit budget."""
    st.session_state[KEY_ROUND] = None
    st.session_state[KEY_STRATEGY_QUEUE] = None
    reset_turn_allocation()


def current_allocation() -> Allocation:
    return Allocation.from_array([st.session_state[k] for k in SLIDER_KEYS])


def committed_allocation() -> Allocation:
    """Return the player's cumulative allocation in the active game."""
    current = current_round()
    if current is None:
        return Allocation(0, 0, 0, 0)
    return current.player.allocation


def remaining_credits() -> int:
    """Return credits still available in the active game."""
    current = current_round()
    return config.BUDGET_TOTAL if current is None else current.remaining_credits


def is_step_mode() -> bool:
    return st.session_state[KEY_STEP_MODE]


def pending_strategy_queue() -> StrategyQueue | None:
    """The in-progress autoplay queue, if a strategy has steps left to play."""
    return st.session_state[KEY_STRATEGY_QUEUE]


def mark_submitted(round_id: str) -> None:
    st.session_state[KEY_SUBMITTED].add(round_id)


def is_submitted(round_id: str) -> bool:
    return round_id in st.session_state[KEY_SUBMITTED]


def play_turn(
    district: District,
    allocation: Allocation,
    seed: int | None = None,
) -> Round:
    """Advance a game by one turn for the player and both benchmarks."""
    previous = current_round()
    if previous is not None and previous.district_id != district.district_id:
        raise ValueError("the active game belongs to a different district")

    remaining = config.BUDGET_TOTAL if previous is None else previous.remaining_credits
    issues = validate_turn_allocation(allocation.as_array().tolist(), remaining)
    if issues:
        raise ValidationError(issues)

    rng = np.random.default_rng(seed)
    credits_spent = allocation.total

    if previous is None:
        player_current = district.baseline
        ai_current = district.baseline
        random_current = district.baseline
        player_cumulative = Allocation(0, 0, 0, 0)
        ai_cumulative = Allocation(0, 0, 0, 0)
        random_cumulative = Allocation(0, 0, 0, 0)
        turns: tuple[Turn, ...] = ()
        round_id = new_id()
    else:
        player_current = previous.player.final
        ai_current = previous.ai.final
        random_current = previous.random.final
        player_cumulative = previous.player.allocation
        ai_cumulative = previous.ai.allocation
        random_cumulative = previous.random.allocation
        turns = previous.turns
        round_id = previous.round_id

    # Benchmarks allocate first from the state produced by earlier turns, so
    # neither can react to the event that is about to be drawn.
    ai_credits = strategies.ai_allocation(ai_current, credits_spent)
    random_credits = strategies.random_allocation(rng, credits_spent)

    event = events.draw_event(rng)
    player_result = run_turn(
        district,
        player_current,
        player_cumulative,
        allocation,
        event,
    )
    ai_result = run_turn(
        district,
        ai_current,
        ai_cumulative,
        ai_credits,
        event,
    )
    random_result = run_turn(
        district,
        random_current,
        random_cumulative,
        random_credits,
        event,
    )
    turn = Turn(
        number=len(turns) + 1,
        credits_spent=credits_spent,
        event=event,
        player_allocation=allocation,
        ai_allocation=ai_credits,
        random_allocation=random_credits,
    )

    return Round(
        round_id=round_id,
        district_id=district.district_id,
        event=event,
        player=player_result,
        ai=ai_result,
        random=random_result,
        ai_allocation=ai_result.allocation,
        random_allocation=random_result.allocation,
        remaining_credits=config.BUDGET_TOTAL - player_result.allocation.total,
        turns=turns + (turn,),
    )


def store_round(value: Round) -> None:
    st.session_state[KEY_ROUND] = value


def commit_turn(district: District) -> None:
    """Button callback that atomically plays a turn and clears its controls."""
    store_round(play_turn(district, current_allocation()))
    st.session_state[KEY_STRATEGY_QUEUE] = None
    reset_turn_allocation()


def _advance_strategy_queue(
    district: District,
    queue: StrategyQueue,
    allocation_for: Callable[[int], Allocation],
) -> None:
    """Play one queued turn in step mode, or drain the whole queue otherwise."""
    step_count = 1 if is_step_mode() else len(queue.turns)
    for _ in range(step_count):
        if not queue.turns:
            break
        turn_credits = queue.turns.pop(0)
        store_round(play_turn(district, allocation_for(turn_credits)))
    st.session_state[KEY_STRATEGY_QUEUE] = queue if queue.turns else None
    reset_turn_allocation()


def autoplay_random_strategy(district: District) -> None:
    """Button callback: play the random strategy's turns, one queued at a time.

    In step mode this plays a single turn per click; otherwise it drains the
    rest of the queue immediately.
    """
    queue = pending_strategy_queue()
    if queue is None or queue.kind != RANDOM_STRATEGY:
        remaining = remaining_credits()
        if remaining <= 0:
            return
        rng = np.random.default_rng()
        queue = StrategyQueue(RANDOM_STRATEGY, strategies.random_turn_plan(rng, remaining), rng)
    rng = queue.rng
    _advance_strategy_queue(
        district, queue, lambda turn_credits: strategies.random_allocation(rng, turn_credits)
    )


def autoplay_ai_strategy(district: District) -> None:
    """Button callback: play the AI planner's turns, one queued at a time.

    Re-evaluates the heuristic every turn against the baseline left by the
    previous turn's event, so later turns react to events already resolved.
    In step mode this plays a single turn per click; otherwise it drains the
    rest of the queue immediately.
    """
    queue = pending_strategy_queue()
    if queue is None or queue.kind != AI_STRATEGY:
        remaining = remaining_credits()
        if remaining <= 0:
            return
        queue = StrategyQueue(AI_STRATEGY, strategies.ai_turn_plan(remaining))

    def allocation_for(turn_credits: int) -> Allocation:
        current = current_round()
        baseline: Dimensions = (
            district.baseline if current is None else current.player.final
        )
        return strategies.ai_allocation(baseline, turn_credits)

    _advance_strategy_queue(district, queue, allocation_for)
