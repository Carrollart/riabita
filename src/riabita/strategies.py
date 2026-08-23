"""Benchmark allocation strategies.

Neither strategy sees the drawn event: both take only the district baseline, so
the comparison against the player is fair.
"""

from __future__ import annotations

import numpy as np

from riabita import config
from riabita.domain.models import Allocation, Dimensions

_EVEN_SHARE = config.BUDGET_TOTAL // 4
_OVERTOURISM_TRIGGER_GAP = 10.0
_OVERTOURISM_SHIFT = 10
_LIFT_AMOUNT = 5


def ai_allocation(baseline: Dimensions) -> Allocation:
    """Deterministic heuristic: even split, defuse overtourism, lift the weakest."""
    budget = [_EVEN_SHARE] * 4
    values = baseline.as_array()

    if values[2] > values[3] + _OVERTOURISM_TRIGGER_GAP:
        budget[2] -= _OVERTOURISM_SHIFT
        budget[3] += _OVERTOURISM_SHIFT

    lowest = int(np.argmin(values))
    highest = int(np.argmax(values))
    if lowest != highest:
        source_ok = budget[highest] - _LIFT_AMOUNT >= config.ALLOCATION_MIN
        target_ok = budget[lowest] + _LIFT_AMOUNT <= config.CONCENTRATION_LIMIT
        if source_ok and target_ok:
            budget[highest] -= _LIFT_AMOUNT
            budget[lowest] += _LIFT_AMOUNT

    return Allocation.from_array(budget)


def random_allocation(rng: np.random.Generator) -> Allocation:
    """Uniformly random split, rounded so the credits still total exactly 100."""
    weights = rng.dirichlet(np.ones(4)) * config.BUDGET_TOTAL
    return Allocation.from_array(_largest_remainder(weights))


def _largest_remainder(weights: np.ndarray) -> list[int]:
    """Round to integers that sum to the budget, avoiding naive rounding drift."""
    floors = np.floor(weights).astype(int)
    shortfall = config.BUDGET_TOTAL - int(floors.sum())
    if shortfall > 0:
        remainders = weights - floors
        # Negate so argsort puts the largest remainder first; ties keep the
        # lower index, which makes the result reproducible.
        for index in np.argsort(-remainders, kind="stable")[:shortfall]:
            floors[index] += 1
    return floors.tolist()
