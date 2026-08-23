"""The eight-step simulation pipeline.

Pure and deterministic: no I/O, no randomness, no global state. The caller draws
the event and passes it in, which is what lets one event be shared by the player
and both benchmark strategies.
"""

from __future__ import annotations

import numpy as np

from riabita import config
from riabita.domain.errors import ValidationError
from riabita.domain.models import (
    Allocation,
    Dimensions,
    District,
    Event,
    SimulationResult,
)
from riabita.domain.validation import (
    validate_allocation,
    validate_cumulative_allocation,
    validate_dimensions,
    validate_turn_allocation,
)
from riabita.engine import metrics

_TOURISM_INDEX = 2
_SOCIO_INDEX = 3


def apply_matrix(baseline: np.ndarray, allocation: np.ndarray) -> np.ndarray:
    """Apply all cross-dimensional effects at once, from the baseline values."""
    delta = (allocation / config.CREDITS_PER_STEP) @ config.IMPACT_MATRIX
    return baseline + delta


def apply_tourism_pressure(values: np.ndarray, allocation: np.ndarray) -> np.ndarray:
    """Reduce socio-demographics when tourism crosses a pressure threshold.

    Evaluated against tourism after the complete matrix step, so the
    socio-demographic row's negative tourism effect is already included.
    """
    tourism = values[_TOURISM_INDEX]
    tourism_steps = allocation[_TOURISM_INDEX] / config.CREDITS_PER_STEP
    result = values.copy()
    for threshold, coefficient in config.TOURISM_PRESSURE_TIERS:
        if tourism > threshold:
            result[_SOCIO_INDEX] -= tourism_steps * coefficient
            break
    return result


def clamp(values: np.ndarray) -> np.ndarray:
    return np.clip(values, config.DIMENSION_MIN, config.DIMENSION_MAX)


def run_simulation(
    district: District,
    allocation: Allocation,
    event: Event | None = None,
) -> SimulationResult:
    """Score one round. Raises ValidationError on invalid input."""
    baseline = district.baseline.as_array()
    budget = allocation.as_array()

    issues = validate_allocation(budget.tolist()) + validate_dimensions(
        baseline.tolist()
    )
    if issues:
        raise ValidationError(issues)

    values = apply_matrix(baseline, budget)
    values = apply_tourism_pressure(values, budget)
    if event is not None:
        values = values + event.impact.as_array()
    final = Dimensions.from_array(clamp(values))

    return _build_result(district, allocation, final, event)


def run_turn(
    district: District,
    current: Dimensions,
    cumulative_allocation: Allocation,
    turn_allocation: Allocation,
    event: Event | None = None,
) -> SimulationResult:
    """Apply and score one progressive investment turn.

    The returned result is cumulative: its initial dimensions come from the
    original district, while its final dimensions include every completed turn.
    """
    previous_budget = cumulative_allocation.as_array()
    turn_budget = turn_allocation.as_array()
    remaining = config.BUDGET_TOTAL - cumulative_allocation.total
    issues = (
        validate_dimensions(district.baseline.as_array().tolist())
        + validate_dimensions(current.as_array().tolist())
        + validate_cumulative_allocation(previous_budget.tolist())
    )
    if 0 <= remaining <= config.BUDGET_TOTAL:
        issues += validate_turn_allocation(turn_budget.tolist(), remaining)
    if issues:
        raise ValidationError(issues)

    values = apply_matrix(current.as_array(), turn_budget)
    values = apply_tourism_pressure(values, turn_budget)
    if event is not None:
        values = values + event.impact.as_array()
    final = Dimensions.from_array(clamp(values))

    return _build_result(
        district,
        cumulative_allocation.plus(turn_allocation),
        final,
        event,
    )


def _build_result(
    district: District,
    allocation: Allocation,
    final: Dimensions,
    event: Event | None,
) -> SimulationResult:
    """Build cumulative metrics from original and current dimensions."""

    risk = metrics.population_std(final.as_array())
    modifiers = metrics.compute_modifiers(final, allocation, risk)
    modifier_total = sum(m.points for m in modifiers)

    riz_initial = float(
        np.clip(
            metrics.riz(district.baseline), config.DIMENSION_MIN, config.DIMENSION_MAX
        )
    )
    riz_final = float(
        np.clip(
            metrics.riz(final) + modifier_total,
            config.DIMENSION_MIN,
            config.DIMENSION_MAX,
        )
    )

    urban_yield = riz_final - riz_initial

    return SimulationResult(
        district_id=district.district_id,
        allocation=allocation,
        initial=district.baseline,
        final=final,
        event=event,
        modifiers=modifiers,
        riz_initial=riz_initial,
        riz_final=riz_final,
        urban_yield=urban_yield,
        risk=risk,
        sharpe=metrics.sharpe_ratio(urban_yield, risk),
        profile_id=metrics.classify_profile(urban_yield, risk),
        rules_version=config.RULES_VERSION,
    )
