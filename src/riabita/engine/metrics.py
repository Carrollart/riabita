"""Scoring: modifiers, the RIz index, risk, Sharpe, and profile classification."""

from __future__ import annotations

import numpy as np

from riabita import config
from riabita.domain.models import Allocation, Dimensions, Modifier


def population_std(values: np.ndarray) -> float:
    """Population standard deviation, the project's definition of urban risk."""
    return float(np.std(values))


def riz(dimensions: Dimensions) -> float:
    """Weighted sum of the four dimensions, before any modifier."""
    return float(np.dot(dimensions.as_array(), config.WEIGHTS))


def equilibrium_modifier(risk: float) -> Modifier:
    if risk < config.EQUILIBRIUM_EXCELLENT_BELOW:
        points = config.EQUILIBRIUM_EXCELLENT_POINTS
    elif risk < config.EQUILIBRIUM_GOOD_BELOW:
        points = config.EQUILIBRIUM_GOOD_POINTS
    elif risk <= config.EQUILIBRIUM_NEUTRAL_AT_MOST:
        points = config.EQUILIBRIUM_NEUTRAL_POINTS
    else:
        points = config.EQUILIBRIUM_HIGH_RISK_POINTS
    return Modifier(config.MODIFIER_EQUILIBRIUM, points, {"risk": risk})


def overtourism_gap_modifier(final: Dimensions) -> Modifier:
    gap = final.tourism - final.socio
    points = 0.0
    for threshold, tier_points in config.OVERTOURISM_GAP_TIERS:
        if gap > threshold:
            points = tier_points
            break
    return Modifier(config.MODIFIER_OVERTOURISM_GAP, points, {"gap": gap})


def concentration_modifier(allocation: Allocation) -> Modifier:
    largest = allocation.largest
    points = (
        config.CONCENTRATION_POINTS if largest > config.CONCENTRATION_LIMIT else 0.0
    )
    return Modifier(config.MODIFIER_CONCENTRATION, points, {"largest": float(largest)})


def diversification_modifier(allocation: Allocation) -> Modifier:
    funded = allocation.funded_count
    points = config.DIVERSIFICATION_BONUS.get(funded, 0.0)
    return Modifier(
        config.MODIFIER_DIVERSIFICATION, points, {"funded": float(funded)}
    )


def compute_modifiers(
    final: Dimensions, allocation: Allocation, risk: float
) -> tuple[Modifier, ...]:
    """Every modifier, including those scoring zero, so the UI can explain them."""
    return (
        equilibrium_modifier(risk),
        overtourism_gap_modifier(final),
        concentration_modifier(allocation),
        diversification_modifier(allocation),
    )


def sharpe_ratio(urban_yield: float, risk: float) -> float:
    """Yield per unit of risk; zero when the city is perfectly balanced."""
    if risk <= config.SHARPE_RISK_EPSILON:
        return 0.0
    return urban_yield / risk


def classify_profile(urban_yield: float, risk: float) -> str:
    """First matching rule wins; see references/simulation-rules.md."""
    if urban_yield <= 0:
        return config.PROFILE_STAGNANT
    if risk > config.PROFILE_VULNERABLE_RISK:
        return config.PROFILE_VULNERABLE
    if risk < config.PROFILE_RESILIENT_RISK:
        return config.PROFILE_RESILIENT
    return config.PROFILE_TRANSITIONAL
