"""Pure validation of player input. Returns issues; never raises."""

from __future__ import annotations

from collections.abc import Sequence

from riabita import config
from riabita.domain.errors import ValidationIssue

RULE_ALLOCATION_LENGTH = "allocation_length"
RULE_ALLOCATION_NOT_INTEGER = "allocation_not_integer"
RULE_ALLOCATION_OUT_OF_RANGE = "allocation_out_of_range"
RULE_ALLOCATION_SUM = "allocation_sum"
RULE_ALLOCATION_EMPTY = "allocation_empty"
RULE_ALLOCATION_EXCEEDS_REMAINING = "allocation_exceeds_remaining"
RULE_DIMENSION_OUT_OF_RANGE = "dimension_out_of_range"

_EXPECTED_LENGTH = 4


def _is_integral(value: object) -> bool:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return number.is_integer()


def _allocation_components(
    values: Sequence[object],
) -> tuple[list[ValidationIssue], list[float] | None]:
    issues: list[ValidationIssue] = []

    if len(values) != _EXPECTED_LENGTH:
        issues.append(
            ValidationIssue(
                RULE_ALLOCATION_LENGTH,
                {"expected": float(_EXPECTED_LENGTH), "actual": float(len(values))},
            )
        )
        return issues, None

    if not all(_is_integral(v) for v in values):
        issues.append(ValidationIssue(RULE_ALLOCATION_NOT_INTEGER))
        return issues, None

    numbers = [float(v) for v in values]  # type: ignore[arg-type]

    out_of_range = [
        n for n in numbers if n < config.ALLOCATION_MIN or n > config.ALLOCATION_MAX
    ]
    if out_of_range:
        issues.append(
            ValidationIssue(
                RULE_ALLOCATION_OUT_OF_RANGE,
                {
                    "minimum": float(config.ALLOCATION_MIN),
                    "maximum": float(config.ALLOCATION_MAX),
                    "offending": out_of_range[0],
                },
            )
        )
    return issues, numbers


def validate_allocation(values: Sequence[object]) -> tuple[ValidationIssue, ...]:
    """Check a complete 100-credit allocation."""
    issues, numbers = _allocation_components(values)
    if numbers is None:
        return tuple(issues)

    total = sum(numbers)
    if total != config.BUDGET_TOTAL:
        issues.append(
            ValidationIssue(
                RULE_ALLOCATION_SUM,
                {
                    "total": total,
                    "expected": float(config.BUDGET_TOTAL),
                    "difference": total - config.BUDGET_TOTAL,
                },
            )
        )

    return tuple(issues)


def validate_turn_allocation(
    values: Sequence[object], remaining_credits: int
) -> tuple[ValidationIssue, ...]:
    """Check a non-empty turn allocation against the game's remaining credits."""
    if not 0 <= remaining_credits <= config.BUDGET_TOTAL:
        raise ValueError("remaining_credits must be within the game budget")

    issues, numbers = _allocation_components(values)
    if numbers is None:
        return tuple(issues)

    total = sum(numbers)
    if total == 0:
        issues.append(ValidationIssue(RULE_ALLOCATION_EMPTY))
    elif total > remaining_credits:
        issues.append(
            ValidationIssue(
                RULE_ALLOCATION_EXCEEDS_REMAINING,
                {
                    "total": total,
                    "remaining": float(remaining_credits),
                    "difference": total - remaining_credits,
                },
            )
        )
    return tuple(issues)


def validate_cumulative_allocation(
    values: Sequence[object],
) -> tuple[ValidationIssue, ...]:
    """Check committed credits, allowing any total from zero through 100."""
    issues, numbers = _allocation_components(values)
    if numbers is None:
        return tuple(issues)

    total = sum(numbers)
    if total > config.BUDGET_TOTAL:
        issues.append(
            ValidationIssue(
                RULE_ALLOCATION_EXCEEDS_REMAINING,
                {
                    "total": total,
                    "remaining": float(config.BUDGET_TOTAL),
                    "difference": total - config.BUDGET_TOTAL,
                },
            )
        )
    return tuple(issues)


def validate_dimensions(values: Sequence[object]) -> tuple[ValidationIssue, ...]:
    """Check that baseline dimensions are four values within range."""
    if len(values) != _EXPECTED_LENGTH:
        return (
            ValidationIssue(
                RULE_DIMENSION_OUT_OF_RANGE,
                {"expected": float(_EXPECTED_LENGTH), "actual": float(len(values))},
            ),
        )

    for value in values:
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return (ValidationIssue(RULE_DIMENSION_OUT_OF_RANGE),)
        if number < config.DIMENSION_MIN or number > config.DIMENSION_MAX:
            return (
                ValidationIssue(
                    RULE_DIMENSION_OUT_OF_RANGE,
                    {
                        "minimum": config.DIMENSION_MIN,
                        "maximum": config.DIMENSION_MAX,
                        "offending": number,
                    },
                ),
            )
    return ()
