"""Plotly figure builders.

These return figures and never call Streamlit, so they are unit-testable.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypeVar

import plotly.graph_objects as go

from riabita import config
from riabita.domain.models import District

_BASELINE_COLOR = "rgba(120, 120, 120, 0.9)"
_FINAL_COLOR = "rgba(29, 145, 96, 1.0)"
_BAR_COLORS = ("#1d9160", "#3b6ea5", "#9a6f3f")
_Value = TypeVar("_Value")


def _close(values: Sequence[_Value]) -> list[_Value]:
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
    categories = list(labels) + list(labels[:1])
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


def build_selection_map(
    districts: Sequence[District], selected_district_id: str | None = None
) -> go.Figure:
    """Build a token-free Mapbox choropleth for the available districts."""
    features = []
    locations = []
    values = []
    text = []
    for district in districts:
        if not district.geometry:
            continue
        locations.append(district.district_id)
        values.append(float(district.baseline.as_array().mean()))
        text.append(district.name)
        features.append({
            "type": "Feature",
            "id": district.district_id,
            "properties": {"name": district.name},
            "geometry": district.geometry,
        })

    geojson = {"type": "FeatureCollection", "features": features}
    figure = go.Figure(
        go.Choroplethmapbox(
            geojson=geojson,
            locations=locations,
            z=values,
            text=text,
            hovertemplate="%{text}<br>Baseline: %{z:.1f}<extra></extra>",
            colorscale="Viridis",
            marker_opacity=0.65,
            marker_line_width=1,
            colorbar_title="Baseline",
        )
    )
    if selected_district_id in locations:
        selected_feature = next(
            feature for feature in features if feature["id"] == selected_district_id
        )
        figure.add_trace(
            go.Choroplethmapbox(
                geojson={
                    "type": "FeatureCollection",
                    "features": [selected_feature],
                },
                locations=[selected_district_id],
                z=[1],
                colorscale=[
                    [0, "rgba(245, 158, 11, 0.18)"],
                    [1, "rgba(245, 158, 11, 0.18)"],
                ],
                showscale=False,
                marker_opacity=0.25,
                marker_line_color="#f59e0b",
                marker_line_width=4,
                hoverinfo="skip",
            )
        )
    figure.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 41.889, "lon": 12.482},
            zoom=12.5,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
    )
    return figure
