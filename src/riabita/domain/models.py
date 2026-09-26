"""Frozen value types shared by every layer.

All four-element vectors use the order (mobility, culture, tourism, socio).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

from riabita import config


@dataclass(frozen=True)
class Dimensions:
    """The four RIz dimension values, each normally within 0..100."""

    mobility: float
    culture: float
    tourism: float
    socio: float

    def as_array(self) -> np.ndarray:
        return np.array(
            [self.mobility, self.culture, self.tourism, self.socio], dtype=float
        )

    @classmethod
    def from_array(cls, values: Iterable[float]) -> "Dimensions":
        m, c, t, s = (float(v) for v in values)
        return cls(mobility=m, culture=c, tourism=t, socio=s)

    def as_mapping(self) -> dict[str, float]:
        return dict(zip(config.DIMENSION_KEYS, self.as_array().tolist()))


@dataclass(frozen=True)
class Allocation:
    """Credits assigned to each dimension for a turn or cumulatively."""

    mobility: int
    culture: int
    tourism: int
    socio: int

    def as_array(self) -> np.ndarray:
        return np.array(
            [self.mobility, self.culture, self.tourism, self.socio], dtype=float
        )

    @classmethod
    def from_array(cls, values: Iterable[float]) -> "Allocation":
        m, c, t, s = (int(v) for v in values)
        return cls(mobility=m, culture=c, tourism=t, socio=s)

    @property
    def total(self) -> int:
        return self.mobility + self.culture + self.tourism + self.socio

    @property
    def largest(self) -> int:
        return max(self.mobility, self.culture, self.tourism, self.socio)

    @property
    def funded_count(self) -> int:
        return sum(
            1
            for v in (self.mobility, self.culture, self.tourism, self.socio)
            if v > 0
        )

    def plus(self, other: "Allocation") -> "Allocation":
        """Return the component-wise sum of two allocations."""
        return Allocation(
            mobility=self.mobility + other.mobility,
            culture=self.culture + other.culture,
            tourism=self.tourism + other.tourism,
            socio=self.socio + other.socio,
        )


@dataclass(frozen=True)
class District:
    """A playable district and its baseline indicators."""

    district_id: str
    name: str
    baseline: Dimensions
    geometry: Any | None = None


@dataclass(frozen=True)
class Event:
    """A random shock applied once per round."""

    event_id: str
    impact: Dimensions

    @property
    def name_key(self) -> str:
        return f"event.{self.event_id}.name"

    @property
    def description_key(self) -> str:
        return f"event.{self.event_id}.description"


@dataclass(frozen=True)
class Modifier:
    """One bonus or penalty, retained even when it scores zero."""

    modifier_id: str
    points: float
    detail: Mapping[str, float] = field(default_factory=dict)

    @property
    def reason_key(self) -> str:
        return f"modifier.{self.modifier_id}"


@dataclass(frozen=True)
class SimulationResult:
    """Everything one scored round produced."""

    district_id: str
    allocation: Allocation
    initial: Dimensions
    final: Dimensions
    event: Event | None
    modifiers: tuple[Modifier, ...]
    riz_initial: float
    riz_final: float
    urban_yield: float
    risk: float
    sharpe: float
    profile_id: str
    rules_version: str

    @property
    def modifier_total(self) -> float:
        return sum(m.points for m in self.modifiers)

    @property
    def riz_change_pct(self) -> float:
        """Percentage change in RIz, zero when the initial score is zero."""
        if abs(self.riz_initial) < config.SHARPE_RISK_EPSILON:
            return 0.0
        return (self.urban_yield / self.riz_initial) * 100.0


@dataclass(frozen=True)
class LeaderboardEntry:
    """A persisted round result."""

    entry_id: str
    round_id: str
    player_id: str
    nickname: str
    district_id: str
    allocation: Allocation
    event_id: str | None
    riz_final: float
    urban_yield: float
    risk: float
    sharpe: float
    profile_id: str
    rules_version: str
    created_at: datetime
