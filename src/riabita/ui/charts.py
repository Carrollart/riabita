"""Plotly figure builders.

These return figures and never call Streamlit, so they are unit-testable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import plotly.graph_objects as go

from riabita import config

_BASELINE_COLOR = "rgba(120, 120, 120, 0.9)"
_FINAL_COLOR = "rgba(29, 145, 96, 1.0)"
_BAR_COLORS = ("#1d9160", "#3b6ea5", "#9a6f3f")


def _close(values: Sequence[float]) -> list[float]:
    """Repeat the first point so the polygon closes instead of drawing an arc."""
    items = list(values)
    return items + items[:1]


def build_radar(
    initial: Sequence[float],
    final: Sequence[float],
    labels: Sequence[str],
    initial_name: str = "Initial",
    final_name: str = "Final",
) -> go.Figure:
    """Overlay the baseline and outcome profiles on a fixed 0..100 axis."""
    categories = _close(labels)
    figure = go.Figure()

    figure.add_trace(
        go.Scatterpolar(
            r=_close(initial),
            theta=categories,
            fill="toself",
            name=initial_name,
            line=dict(color=_BASELINE_COLOR, dash="dash"),
            fillcolor="rgba(120, 120, 120, 0.15)",
        )
    )
    figure.add_trace(
        go.Scatterpolar(
            r=_close(final),
            theta=categories,
            fill="toself",
            name=final_name,
            line=dict(color=_FINAL_COLOR, dash="solid"),
            fillcolor="rgba(29, 145, 96, 0.25)",
        )
    )

    figure.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[config.DIMENSION_MIN, config.DIMENSION_MAX],
            )
        ),
        showlegend=True,
        margin=dict(l=40, r=40, t=30, b=30),
    )
    return figure


def build_comparison(scores: Mapping[str, float]) -> go.Figure:
    """Rank the player against both benchmarks, labelling every value."""
    ranked = sorted(scores.items(), key=lambda item: item[1])
    names = [name for name, _ in ranked]
    values = [value for _, value in ranked]
    colors = list(_BAR_COLORS)[: len(ranked)][::-1]

    figure = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{value:.{config.VALUE_DECIMALS}f}" for value in values],
            textposition="outside",
            cliponaxis=False,
        )
    )
    figure.update_layout(
        xaxis=dict(
            title="RIz",
            range=[config.DIMENSION_MIN, config.DIMENSION_MAX + 5],
        ),
        yaxis=dict(title=""),
        showlegend=False,
        margin=dict(l=40, r=40, t=30, b=30),
    )
    return figure
