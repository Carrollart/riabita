"""Benchmark allocation strategies.

Neither strategy sees the event for the current turn. Both receive the same
number of credits the player chose to spend in that turn.

The `*_turn_plan` functions split a budget across several turns so a strategy
can be played out over the long term: the random plan invests a random amount
each turn, and the AI plan re-evaluates `ai_allocation` every turn against the
baseline left by the previous turn's event, so it reacts to events as they
happen rather than committing to a single upfront guess.
"""

from __future__ import annotations

import numpy as np

from riabita import config
from riabita.domain.models import Allocation, Dimensions

_OVERTOURISM_TRIGGER_GAP = 10.0
_OVERTOURISM_SHIFT = 10
_LIFT_AMOUNT = 5


def ai_allocation(
    baseline: Dimensions, budget_total: int = config.BUDGET_TOTAL
) -> Allocation:
    """Deterministic heuristic: even split, defuse overtourism, lift the weakest."""
    _validate_budget_total(budget_total)
    even_share, remainder = divmod(budget_total, 4)
    budget = [
        even_share + (1 if index < remainder else 0) for index in range(4)
    ]
    values = baseline.as_array()

    if values[2] > values[3] + _OVERTOURISM_TRIGGER_GAP:
        shift = min(_OVERTOURISM_SHIFT, budget[2])
        budget[2] -= shift
        budget[3] += shift

    lowest = int(np.argmin(values))
    highest = int(np.argmax(values))
    if lowest != highest:
        shift = min(_LIFT_AMOUNT, budget[highest])
        target_ok = budget[lowest] + shift <= config.CONCENTRATION_LIMIT
        if shift > 0 and target_ok:
            budget[highest] -= shift
            budget[lowest] += shift

    return Allocation.from_array(budget)


def random_allocation(
    rng: np.random.Generator, budget_total: int = config.BUDGET_TOTAL
) -> Allocation:
    """Uniformly random integer split of the credits available this turn."""
    _validate_budget_total(budget_total)
    weights = rng.dirichlet(np.ones(4)) * budget_total
    return Allocation.from_array(_largest_remainder(weights, budget_total))


def random_turn_plan(rng: np.random.Generator, budget_total: int) -> list[int]:
    """Split the budget across a random number of turns of random size.

    Every turn gets at least one credit; the rest of the budget is shared out
    with the same random, largest-remainder rounding used for dimensions.
    """
    _validate_budget_total(budget_total)
    max_turns = min(config.RANDOM_AUTOPLAY_MAX_TURNS, budget_total)
    min_turns = min(config.RANDOM_AUTOPLAY_MIN_TURNS, max_turns)
    turn_count = int(rng.integers(min_turns, max_turns + 1))
    extra = budget_total - turn_count
    if extra == 0:
        return [1] * turn_count
    weights = rng.dirichlet(np.ones(turn_count)) * extra
    return [1 + share for share in _largest_remainder(weights, extra)]


def ai_turn_plan(budget_total: int) -> list[int]:
    """Split the budget evenly across the AI planner's long-term turn horizon."""
    _validate_budget_total(budget_total)
    turn_count = min(config.AI_AUTOPLAY_TURNS, budget_total)
    even_share, remainder = divmod(budget_total, turn_count)
    return [
        even_share + (1 if index < remainder else 0) for index in range(turn_count)
    ]


def _largest_remainder(weights: np.ndarray, budget_total: int) -> list[int]:
    """Round to integers that sum to the budget, avoiding naive rounding drift."""
    floors = np.floor(weights).astype(int)
    shortfall = budget_total - int(floors.sum())
    if shortfall > 0:
        remainders = weights - floors
        # Negate so argsort puts the largest remainder first; ties keep the
        # lower index, which makes the result reproducible.
        for index in np.argsort(-remainders, kind="stable")[:shortfall]:
            floors[index] += 1
    return floors.tolist()


def _validate_budget_total(budget_total: int) -> None:
    if (
        isinstance(budget_total, bool)
        or not isinstance(budget_total, int)
        or not config.ALLOCATION_MIN < budget_total <= config.BUDGET_TOTAL
    ):
        raise ValueError("budget_total must be an integer between 1 and 100")
