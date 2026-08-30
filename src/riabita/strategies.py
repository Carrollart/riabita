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
from riabita.domain.models import Allocation, Dimensions, District
from riabita.engine.simulator import run_turn

_OVERTOURISM_TRIGGER_GAP = 10.0
_OVERTOURISM_SHIFT = 10
_LIFT_AMOUNT = 5

GWR_COEFFICIENTS: dict[int, dict[str, float]] = {
    5: {"mob": 0.41, "cult": 0.32, "tour": 0.27, "socio": -0.05},
    10: {"mob": 0.36, "cult": 0.28, "tour": 0.12, "socio": -0.02},
    15: {"mob": 0.09, "cult": 0.24, "tour": 0.19, "socio": 0.05},
    20: {"mob": -0.03, "cult": 0.18, "tour": 0.04, "socio": 0.21},
    25: {"mob": -0.05, "cult": 0.08, "tour": -0.02, "socio": 0.32},
    30: {"mob": -0.07, "cult": 0.02, "tour": -0.05, "socio": 0.38},
}
_GWR_DEFAULT_BAND = 15
_GWR_GRID_STEP = 5


def ai_allocation(
    baseline: Dimensions,
    budget_total: int = config.BUDGET_TOTAL,
    district_id: str | None = None,
    cumulative_allocation: Allocation | None = None,
) -> Allocation:
    """Return the AI allocation for a turn.

    Calls without a district ID retain the original general-purpose heuristic
    for compatibility. District-aware calls use the GWR planner: authoritative
    game score is the primary objective and the local GWR projection breaks
    ties. The event is intentionally not an input, preserving benchmark
    fairness.
    """
    _validate_budget_total(budget_total)
    if district_id is not None:
        return gwr_allocation(
            district_id,
            baseline,
            budget_total,
            cumulative_allocation or Allocation(0, 0, 0, 0),
        )

    return _heuristic_allocation(baseline, budget_total)


def _heuristic_allocation(
    baseline: Dimensions, budget_total: int
) -> Allocation:
    """Return the pre-GWR deterministic heuristic for compatibility."""
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


def temporal_band(district_id: str) -> int:
    """Map a district ID to its supplied 5–30 minute GWR band."""
    value = str(district_id).strip().upper()
    if value == "A0":
        return 5
    for prefix, lower_band, upper_band in (("A", 5, 10), ("B", 15, 20), ("C", 25, 30)):
        suffix = value[len(prefix):] if value.startswith(prefix) else ""
        if suffix.isdigit():
            return lower_band if int(suffix) <= 4 else upper_band
    return _GWR_DEFAULT_BAND


def gwr_profile(district_id: str) -> tuple[int, dict[str, float]]:
    """Return the active GWR band and a defensive copy of its coefficients."""
    band = temporal_band(district_id)
    return band, dict(GWR_COEFFICIENTS[band])


def gwr_allocation(
    district_id: str,
    baseline: Dimensions,
    budget_total: int,
    cumulative_allocation: Allocation,
) -> Allocation:
    """Optimize a progressive turn using local GWR suitability as a tie-break.

    Candidate allocations use five-credit grid steps when possible, matching
    the reference planner. Small non-multiples of five are enumerated at unit
    steps so every valid partial turn budget remains supported.
    """
    _validate_budget_total(budget_total)
    _, coefficients = gwr_profile(district_id)
    weights = np.array(
        [coefficients[key] for key in ("mob", "cult", "tour", "socio")],
        dtype=float,
    )
    district = District("gwr-candidate", "GWR candidate", baseline)
    step = _GWR_GRID_STEP if budget_total % _GWR_GRID_STEP == 0 else 1
    best_score = -float("inf")
    best_fit = -float("inf")
    best_budget = Allocation(0, 0, 0, 0)

    for mobility in range(0, budget_total + 1, step):
        for culture in range(0, budget_total - mobility + 1, step):
            for tourism in range(0, budget_total - mobility - culture + 1, step):
                socio = budget_total - mobility - culture - tourism
                if socio % step:
                    continue
                candidate = Allocation(mobility, culture, tourism, socio)
                result = run_turn(
                    district,
                    baseline,
                    cumulative_allocation,
                    candidate,
                )
                fit = float(np.dot(result.final.as_array(), weights))
                score = result.riz_final
                if score > best_score or (
                    np.isclose(score, best_score, rtol=0.0, atol=1e-9)
                    and fit > best_fit
                ):
                    best_score = score
                    best_fit = fit
                    best_budget = candidate

    return best_budget


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
