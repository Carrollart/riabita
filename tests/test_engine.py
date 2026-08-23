"""Engine arithmetic, thresholds, ordering, and purity."""

from __future__ import annotations

import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from riabita import config
from riabita.domain.errors import ValidationError
from riabita.domain.models import Allocation, Dimensions, District, Event
from riabita.engine import metrics
from riabita.engine.simulator import (
    apply_matrix,
    apply_tourism_pressure,
    run_simulation,
)

TOLERANCE = 1e-9


def district(m: float, c: float, t: float, s: float, name: str = "test") -> District:
    return District(district_id=name, name=name, baseline=Dimensions(m, c, t, s))


SAN_LORENZO = district(55, 40, 80, 35, "san-lorenzo")
EVEN_SPLIT = Allocation(25, 25, 25, 25)


# --- Golden example ---------------------------------------------------------


@pytest.fixture
def golden():
    return run_simulation(SAN_LORENZO, EVEN_SPLIT)


def test_golden_final_dimensions(golden) -> None:
    assert golden.final.as_array() == pytest.approx([59.0, 45.0, 84.25, 38.5])


def test_golden_scores(golden) -> None:
    assert golden.riz_initial == pytest.approx(52.5)
    assert golden.riz_final == pytest.approx(51.6875)
    assert golden.urban_yield == pytest.approx(-0.8125)


def test_golden_risk_and_sharpe(golden) -> None:
    assert golden.risk == pytest.approx(17.5529, abs=1e-4)
    assert golden.sharpe == pytest.approx(-0.0463, abs=1e-4)


def test_golden_modifiers(golden) -> None:
    points = {m.modifier_id: m.points for m in golden.modifiers}
    assert points == {
        config.MODIFIER_EQUILIBRIUM: 0.0,
        config.MODIFIER_OVERTOURISM_GAP: -10.0,
        config.MODIFIER_CONCENTRATION: 0.0,
        config.MODIFIER_DIVERSIFICATION: 5.0,
    }
    assert golden.modifier_total == pytest.approx(-5.0)


def test_golden_profile_is_stagnant(golden) -> None:
    assert golden.profile_id == config.PROFILE_STAGNANT


def test_golden_reports_percentage_change(golden) -> None:
    assert golden.riz_change_pct == pytest.approx(-0.8125 / 52.5 * 100.0)


# --- Impact matrix ----------------------------------------------------------


def test_single_dimension_allocation_equals_ten_times_matrix_row() -> None:
    result = apply_matrix(np.zeros(4), np.array([100.0, 0.0, 0.0, 0.0]))
    assert result == pytest.approx([10.0, 4.0, 3.0, 2.0])


def test_socio_investment_reduces_tourism() -> None:
    result = apply_matrix(np.zeros(4), np.array([0.0, 0.0, 0.0, 100.0]))
    assert result[2] == pytest.approx(-1.0)


def test_pressure_uses_tourism_after_the_complete_matrix_step() -> None:
    """The socio row's -0.1 on tourism must be included before the check.

    Checking tourism early would see 70.2, cross the threshold, and wrongly
    reduce socio-demographics.
    """
    baseline = np.array([50.0, 50.0, 65.2, 50.0])
    budget = np.array([0.0, 0.0, 50.0, 50.0])

    after_matrix = apply_matrix(baseline, budget)
    assert after_matrix[2] == pytest.approx(69.7)

    after_pressure = apply_tourism_pressure(after_matrix, budget)
    assert after_pressure[3] == pytest.approx(after_matrix[3])


# --- Tourism pressure tiers -------------------------------------------------


@pytest.mark.parametrize(
    ("tourism", "expected_coefficient"),
    [(70.0, 0.0), (70.1, 0.2), (85.0, 0.2), (85.1, 0.5)],
)
def test_tourism_pressure_tiers(tourism: float, expected_coefficient: float) -> None:
    values = np.array([50.0, 50.0, tourism, 50.0])
    budget = np.array([0.0, 0.0, 50.0, 50.0])
    result = apply_tourism_pressure(values, budget)
    assert result[3] == pytest.approx(50.0 - 5.0 * expected_coefficient)


def test_no_tourism_investment_means_no_pressure() -> None:
    values = np.array([50.0, 50.0, 90.0, 50.0])
    budget = np.array([50.0, 50.0, 0.0, 0.0])
    assert apply_tourism_pressure(values, budget)[3] == pytest.approx(50.0)


# --- Modifier boundaries ----------------------------------------------------


@pytest.mark.parametrize(
    ("gap", "expected"), [(25.0, 0.0), (25.1, -5.0), (40.0, -5.0), (40.1, -10.0)]
)
def test_overtourism_gap_tiers(gap: float, expected: float) -> None:
    final = Dimensions(0.0, 0.0, 20.0 + gap, 20.0)
    assert metrics.overtourism_gap_modifier(final).points == expected


@pytest.mark.parametrize(
    ("risk", "expected"),
    [(9.9, 10.0), (10.0, 5.0), (14.9, 5.0), (15.0, 0.0), (25.0, 0.0), (25.1, -5.0)],
)
def test_equilibrium_tiers(risk: float, expected: float) -> None:
    assert metrics.equilibrium_modifier(risk).points == expected


@pytest.mark.parametrize(
    ("allocation", "expected"),
    [
        (Allocation(60, 40, 0, 0), 0.0),
        (Allocation(61, 39, 0, 0), -5.0),
        (Allocation(70, 30, 0, 0), -5.0),
    ],
)
def test_concentration_penalty_is_flat(allocation: Allocation, expected: float) -> None:
    assert metrics.concentration_modifier(allocation).points == expected


@pytest.mark.parametrize(
    ("allocation", "expected"),
    [
        (Allocation(25, 25, 25, 25), 5.0),
        (Allocation(40, 30, 30, 0), 2.0),
        (Allocation(50, 50, 0, 0), 0.0),
        (Allocation(100, 0, 0, 0), 0.0),
    ],
)
def test_diversification_bonus(allocation: Allocation, expected: float) -> None:
    assert metrics.diversification_modifier(allocation).points == expected


def test_all_modifiers_are_reported_even_when_zero() -> None:
    result = run_simulation(district(50, 50, 50, 50), EVEN_SPLIT)
    assert len(result.modifiers) == 4


# --- Statistics -------------------------------------------------------------


def test_risk_uses_population_standard_deviation() -> None:
    assert metrics.population_std(np.array([0.0, 0.0, 0.0, 100.0])) == pytest.approx(
        43.3013, abs=1e-4
    )


def test_zero_risk_yields_zero_sharpe_without_raising() -> None:
    assert metrics.sharpe_ratio(5.0, 0.0) == 0.0


# --- Clamping ---------------------------------------------------------------


def test_dimensions_clamp_at_the_upper_bound() -> None:
    result = run_simulation(district(98, 98, 98, 98), Allocation(25, 25, 25, 25))
    assert max(result.final.as_array()) <= config.DIMENSION_MAX


def test_dimensions_clamp_at_the_lower_bound() -> None:
    heatwave = Event("heat_wave", Dimensions(-2.0, -2.0, -2.0, -5.0))
    result = run_simulation(district(2, 2, 2, 2), Allocation(0, 0, 0, 100), heatwave)
    assert min(result.final.as_array()) >= config.DIMENSION_MIN


def test_final_riz_stays_within_range() -> None:
    result = run_simulation(district(100, 100, 100, 100), EVEN_SPLIT)
    assert config.DIMENSION_MIN <= result.riz_final <= config.DIMENSION_MAX


# --- Events -----------------------------------------------------------------


def test_event_impact_is_added_after_investments() -> None:
    boom = Event("tourist_boom", Dimensions(0.0, 0.0, 10.0, -5.0))
    without = run_simulation(SAN_LORENZO, EVEN_SPLIT)
    with_event = run_simulation(SAN_LORENZO, EVEN_SPLIT, boom)
    delta = with_event.final.as_array() - without.final.as_array()
    assert delta == pytest.approx([0.0, 0.0, 10.0, -5.0])


def test_event_does_not_retrigger_tourism_pressure() -> None:
    boom = Event("tourist_boom", Dimensions(0.0, 0.0, 10.0, -5.0))
    result = run_simulation(district(50, 50, 60, 50), Allocation(0, 0, 50, 50), boom)
    # Post-matrix tourism is 64.5, below the threshold; only the event's -5 applies.
    assert result.final.socio == pytest.approx(50.0 + 5.0 - 5.0)


# --- Profiles ---------------------------------------------------------------


def test_zero_yield_is_stagnant_not_resilient() -> None:
    assert metrics.classify_profile(0.0, 1.0) == config.PROFILE_STAGNANT


def test_high_risk_with_gain_is_vulnerable() -> None:
    assert metrics.classify_profile(10.0, 30.0) == config.PROFILE_VULNERABLE


def test_low_risk_with_gain_is_resilient() -> None:
    assert metrics.classify_profile(10.0, 5.0) == config.PROFILE_RESILIENT


def test_middle_risk_with_gain_is_transitional() -> None:
    assert metrics.classify_profile(10.0, 20.0) == config.PROFILE_TRANSITIONAL


# --- Contract ---------------------------------------------------------------


def test_invalid_allocation_raises_validation_error() -> None:
    with pytest.raises(ValidationError) as excinfo:
        run_simulation(SAN_LORENZO, Allocation(10, 10, 10, 10))
    assert "allocation_sum" in excinfo.value.rules


def test_simulation_does_not_mutate_inputs() -> None:
    before = SAN_LORENZO.baseline.as_array().copy()
    run_simulation(SAN_LORENZO, EVEN_SPLIT)
    assert SAN_LORENZO.baseline.as_array() == pytest.approx(before)


def test_simulation_is_deterministic() -> None:
    first = run_simulation(SAN_LORENZO, EVEN_SPLIT)
    second = run_simulation(SAN_LORENZO, EVEN_SPLIT)
    assert first == second


def test_result_carries_the_rules_version() -> None:
    assert run_simulation(SAN_LORENZO, EVEN_SPLIT).rules_version == config.RULES_VERSION


def test_engine_does_not_depend_on_frameworks() -> None:
    """The engine must import with no UI, geo, or database library present.

    Runs in a subprocess because the shared module table is polluted by other
    tests in the same session.
    """
    probe = (
        "import sys; import riabita.engine.simulator;"
        "leaked = {'streamlit', 'geopandas', 'sqlalchemy', 'plotly'} & set(sys.modules);"
        "print(sorted(leaked))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
    )
    assert completed.stdout.strip() == "[]"


def test_percentage_change_is_zero_when_initial_riz_is_zero() -> None:
    result = run_simulation(district(0, 0, 0, 0), Allocation(0, 0, 0, 100))
    assert math.isfinite(result.riz_change_pct)
