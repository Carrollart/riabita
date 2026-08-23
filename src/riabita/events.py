"""The random event catalog.

Impact vectors are in (mobility, culture, tourism, socio) order. Selection uses
an injected generator so a seeded round always draws the same event.
"""

from __future__ import annotations

from typing import Final, Protocol

from riabita.domain.models import Dimensions, Event

TRANSPORT_LINE: Final = "transport_line"
CULTURAL_FESTIVAL: Final = "cultural_festival"
TOURIST_BOOM: Final = "tourist_boom"
HOUSING_CRISIS: Final = "housing_crisis"
HEAT_WAVE: Final = "heat_wave"

EVENTS: Final[tuple[Event, ...]] = (
    Event(TRANSPORT_LINE, Dimensions(10.0, 2.0, 0.0, 2.0)),
    Event(CULTURAL_FESTIVAL, Dimensions(2.0, 10.0, 8.0, 0.0)),
    Event(TOURIST_BOOM, Dimensions(0.0, 0.0, 10.0, -5.0)),
    Event(HOUSING_CRISIS, Dimensions(0.0, 0.0, 2.0, -10.0)),
    Event(HEAT_WAVE, Dimensions(-2.0, -2.0, -2.0, -5.0)),
)

_BY_ID: Final[dict[str, Event]] = {event.event_id: event for event in EVENTS}


class SupportsIntegers(Protocol):
    """The slice of a random generator this module needs."""

    def integers(self, low: int, high: int) -> int: ...


def draw_event(rng: SupportsIntegers) -> Event:
    """Pick one event with uniform probability using the injected generator."""
    return EVENTS[int(rng.integers(0, len(EVENTS)))]


def get_event(event_id: str) -> Event | None:
    """Look up a specific event for scripted scenarios and tests."""
    return _BY_ID.get(event_id)


def event_ids() -> tuple[str, ...]:
    return tuple(_BY_ID)
