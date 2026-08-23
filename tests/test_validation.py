"""Validation rules and domain immutability."""

from __future__ import annotations

import dataclasses

import pytest

from riabita.domain import validation
from riabita.domain.errors import ValidationError, ValidationIssue
from riabita.domain.models import Allocation, Dimensions


def rules(issues: tuple[ValidationIssue, ...]) -> set[str]:
    return {issue.rule for issue in issues}


def test_even_split_is_valid() -> None:
    assert validation.validate_allocation([25, 25, 25, 25]) == ()


def test_full_concentration_is_valid_input() -> None:
    # Valid to submit; the concentration penalty is applied later by scoring.
    assert validation.validate_allocation([100, 0, 0, 0]) == ()


@pytest.mark.parametrize("values", [[25, 25, 50], [20, 20, 20, 20, 20]])
def test_wrong_length_is_rejected(values: list[int]) -> None:
    assert rules(validation.validate_allocation(values)) == {
        validation.RULE_ALLOCATION_LENGTH
    }


def test_non_integer_allocation_is_rejected() -> None:
    assert rules(validation.validate_allocation([25.5, 24.5, 25, 25])) == {
        validation.RULE_ALLOCATION_NOT_INTEGER
    }


def test_integral_float_is_accepted() -> None:
    assert validation.validate_allocation([25.0, 25.0, 25.0, 25.0]) == ()


@pytest.mark.parametrize("offending", [-1, 101])
def test_out_of_range_allocation_is_rejected(offending: int) -> None:
    values = [offending, 100 - offending, 0, 0]
    assert validation.RULE_ALLOCATION_OUT_OF_RANGE in rules(
        validation.validate_allocation(values)
    )


@pytest.mark.parametrize(
    ("values", "difference"),
    [([25, 25, 25, 24], -1.0), ([25, 25, 25, 26], 1.0)],
)
def test_sum_error_reports_signed_difference(
    values: list[int], difference: float
) -> None:
    issues = validation.validate_allocation(values)
    issue = next(i for i in issues if i.rule == validation.RULE_ALLOCATION_SUM)
    assert issue.detail["difference"] == difference


def test_partial_turn_allocation_is_valid() -> None:
    assert validation.validate_turn_allocation([10, 5, 0, 0], 100) == ()


def test_turn_allocation_must_invest_at_least_one_credit() -> None:
    assert rules(validation.validate_turn_allocation([0, 0, 0, 0], 100)) == {
        validation.RULE_ALLOCATION_EMPTY
    }


def test_turn_allocation_cannot_exceed_remaining_credits() -> None:
    issues = validation.validate_turn_allocation([20, 10, 0, 0], 25)
    assert rules(issues) == {validation.RULE_ALLOCATION_EXCEEDS_REMAINING}
    assert issues[0].detail["difference"] == 5.0


def test_cumulative_allocation_accepts_zero_and_partial_totals() -> None:
    assert validation.validate_cumulative_allocation([0, 0, 0, 0]) == ()
    assert validation.validate_cumulative_allocation([20, 10, 0, 0]) == ()


@pytest.mark.parametrize("values", [[50, 50, 101, -50], [0, 0, 0, 0]])
def test_invalid_allocations_report_at_least_one_rule(values: list[int]) -> None:
    assert validation.validate_allocation(values)


def test_dimensions_within_range_are_valid() -> None:
    assert validation.validate_dimensions([0, 50, 100, 35]) == ()


@pytest.mark.parametrize("values", [[0, 0, 0, 101], [-1, 0, 0, 0], [1, 2, 3]])
def test_out_of_range_dimensions_are_rejected(values: list[float]) -> None:
    assert rules(validation.validate_dimensions(values)) == {
        validation.RULE_DIMENSION_OUT_OF_RANGE
    }


def test_validation_error_exposes_rules() -> None:
    error = ValidationError([ValidationIssue(validation.RULE_ALLOCATION_SUM)])
    assert error.rules == (validation.RULE_ALLOCATION_SUM,)


def test_dimensions_are_immutable() -> None:
    dims = Dimensions(1.0, 2.0, 3.0, 4.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        dims.mobility = 9.0  # type: ignore[misc]


def test_dimensions_round_trip_preserves_order() -> None:
    dims = Dimensions(55.0, 40.0, 80.0, 35.0)
    assert dims.as_array().tolist() == [55.0, 40.0, 80.0, 35.0]
    assert Dimensions.from_array([55, 40, 80, 35]) == dims


def test_allocation_summary_properties() -> None:
    allocation = Allocation(60, 40, 0, 0)
    assert allocation.total == 100
    assert allocation.largest == 60
    assert allocation.funded_count == 2


def test_allocations_add_component_by_component() -> None:
    assert Allocation(10, 0, 5, 0).plus(Allocation(0, 20, 0, 5)) == Allocation(
        10, 20, 5, 5
    )
