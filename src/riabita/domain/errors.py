"""Exception hierarchy and validation issue records shared across layers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationIssue:
    """A single failed rule, with the data needed to explain it to a player."""

    rule: str
    detail: Mapping[str, float] = field(default_factory=dict)


class RiabitaError(Exception):
    """Base class for every error raised by this package."""


class ValidationError(RiabitaError):
    """Raised when input violates a documented game rule."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues: tuple[ValidationIssue, ...] = tuple(issues)
        super().__init__(f"invalid input: {', '.join(self.rules)}")

    @property
    def rules(self) -> tuple[str, ...]:
        return tuple(issue.rule for issue in self.issues)


class DataSourceError(RiabitaError):
    """Raised when district data cannot be read or fails schema validation."""


class LeaderboardUnavailable(RiabitaError):
    """Raised when the shared score store cannot be reached."""

