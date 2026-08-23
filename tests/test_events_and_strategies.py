"""Event catalog and benchmark strategy behavior."""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from riabita import events, strategies
from riabita.domain.models import Dimensions
from riabita.domain.validation import validate_allocation

DEMO_BASELINES = {
    "Centro": (70, 90, 100, 25),
    "San Lorenzo": (55, 40, 80, 35),
    "Trastevere": (40, 85, 95, 30),
    "Montesacro": (45, 50, 20, 65),
    "Trieste-Parioli": (60, 70, 40, 75),
    "EUR": (75, 50, 30, 60),
    "Ostia": (40, 35, 85, 50),
    "Tuscolano": (65, 45, 30, 55),
    "Magliana": (40, 30, 10, 45),
    "Nomentano": (60, 55, 25, 65),
}


# --- Events -----------------------------------------------------------------


def test_catalog_contains_the_five_documented_events() -> None:
    assert set(events.event_ids()) == {
        events.TRANSPORT_LINE,
        events.CULTURAL_FESTIVAL,
        events.TOURIST_BOOM,
        events.HOUSING_CRISIS,
        events.HEAT_WAVE,
    }


def test_tourist_boom_impact_matches_the_brief() -> None:
    boom = events.get_event(events.TOURIST_BOOM)
    assert boom is not None
    assert boom.impact.as_array() == pytest.approx([0.0, 0.0, 10.0, -5.0])


def test_unknown_event_returns_none() -> None:
    assert events.get_event("earthquake") is None


def test_draw_is_reproducible_under_a_seed() -> None:
    first = events.draw_event(np.random.default_rng(7))
    second = events.draw_event(np.random.default_rng(7))
    assert first == second


def test_draw_covers_every_event() -> None:
    drawn = {events.draw_event(np.random.default_rng(s)).event_id for s in range(200)}
    assert drawn == set(events.event_ids())


def test_event_translation_keys_are_derived_from_the_id() -> None:
    boom = events.get_event(events.TOURIST_BOOM)
    assert boom is not None
    assert boom.name_key == "event.tourist_boom.name"
    assert boom.description_key == "event.tourist_boom.description"


# --- AI strategy ------------------------------------------------------------


def test_ai_worked_example_for_san_lorenzo() -> None:
    allocation = strategies.ai_allocation(Dimensions(55, 40, 80, 35))
    assert allocation.as_array().tolist() == [25.0, 25.0, 10.0, 40.0]


@pytest.mark.parametrize("baseline", DEMO_BASELINES.values(), ids=DEMO_BASELINES)
def test_ai_allocation_is_valid_for_every_demo_district(
    baseline: tuple[int, int, int, int],
) -> None:
    allocation = strategies.ai_allocation(Dimensions(*baseline))
    assert validate_allocation(allocation.as_array().tolist()) == ()
    assert allocation.largest <= 60


def test_ai_allocation_is_deterministic() -> None:
    baseline = Dimensions(55, 40, 80, 35)
    assert strategies.ai_allocation(baseline) == strategies.ai_allocation(baseline)


def test_ai_shifts_credits_away_from_dominant_tourism() -> None:
    allocation = strategies.ai_allocation(Dimensions(50, 50, 90, 20))
    assert allocation.tourism < allocation.socio


@pytest.mark.parametrize("budget_total", [1, 7, 25, 60])
def test_ai_can_allocate_a_partial_turn_budget(budget_total: int) -> None:
    allocation = strategies.ai_allocation(
        Dimensions(55, 40, 80, 35), budget_total
    )
    assert allocation.total == budget_total
    assert allocation.largest <= 60


# --- Random strategy --------------------------------------------------------


@pytest.mark.parametrize("seed", range(50))
def test_random_allocation_always_totals_the_budget(seed: int) -> None:
    allocation = strategies.random_allocation(np.random.default_rng(seed))
    assert validate_allocation(allocation.as_array().tolist()) == ()


def test_random_allocation_is_reproducible_under_a_seed() -> None:
    first = strategies.random_allocation(np.random.default_rng(11))
    second = strategies.random_allocation(np.random.default_rng(11))
    assert first == second


def test_random_allocation_varies_between_seeds() -> None:
    results = {
        strategies.random_allocation(np.random.default_rng(s)).as_array().tobytes()
        for s in range(20)
    }
    assert len(results) > 1


@pytest.mark.parametrize("budget_total", [1, 7, 25, 60])
def test_random_can_allocate_a_partial_turn_budget(budget_total: int) -> None:
    allocation = strategies.random_allocation(
        np.random.default_rng(11), budget_total
    )
    assert allocation.total == budget_total


@pytest.mark.parametrize("budget_total", [0, 101, 2.5, True])
def test_strategies_reject_invalid_turn_budgets(budget_total) -> None:
    with pytest.raises(ValueError):
        strategies.ai_allocation(Dimensions(50, 50, 50, 50), budget_total)
    with pytest.raises(ValueError):
        strategies.random_allocation(np.random.default_rng(1), budget_total)


# --- Fairness ---------------------------------------------------------------


@pytest.mark.parametrize(
    "function", [strategies.ai_allocation, strategies.random_allocation]
)
def test_strategies_cannot_observe_the_event(function) -> None:
    parameters = set(inspect.signature(function).parameters)
    assert "event" not in parameters
