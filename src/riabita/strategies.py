"""Benchmark allocation strategies.

Neither strategy sees the event for the current turn. Both receive the same
number of credits the player chose to spend in that turn.
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
