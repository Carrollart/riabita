"""Streamlit render functions. The only module that draws UI."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from riabita import config, i18n
from riabita.data.loader import DistrictCatalog
from riabita.domain.errors import LeaderboardUnavailable
from riabita.domain.models import Allocation, District, SimulationResult
from riabita.domain.validation import (
    RULE_ALLOCATION_EXCEEDS_REMAINING,
    validate_turn_allocation,
)
from riabita.leaderboard import service
from riabita.leaderboard.repository import LeaderboardRepository
from riabita.ui import charts, state

_DECIMALS = config.VALUE_DECIMALS


def _round(value: float) -> float:
    return round(value, _DECIMALS)


def _signed(value: float) -> str:
    return f"{value:+.{_DECIMALS}f}"


def render_language_selector() -> str:
    languages = i18n.available_languages()
    current = state.language()
    chosen = st.sidebar.selectbox(
        i18n.t("language.label", current),
        options=languages,
        index=languages.index(current) if current in languages else 0,
        format_func=i18n.language_name,
    )
    if chosen != current:
        state.set_language(chosen)
        st.rerun()
    return chosen


def render_district_picker(catalog: DistrictCatalog, lang: str) -> District:
    st.sidebar.header(i18n.t("sidebar.district_header", lang))
    if catalog.used_fallback:
        st.sidebar.info(i18n.t("data.demo_notice", lang))

    names = list(catalog.names)
    selected = st.sidebar.selectbox(i18n.t("sidebar.district_label", lang), names)
    district = next(d for d in catalog.districts if d.name == selected)

    st.sidebar.caption(i18n.t("sidebar.baseline_header", lang))
    baseline = district.baseline.as_array()
    st.sidebar.dataframe(
        pd.DataFrame(
            {
                i18n.t("results.dimension", lang): list(i18n.dimension_labels(lang)),
                i18n.t("results.initial", lang): [_round(v) for v in baseline],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )
    return district


def render_budget_controls(district: District, lang: str) -> None:
    """Draw controls for the next investment turn."""
    st.sidebar.header(i18n.t("sidebar.budget_header", lang))
    st.sidebar.caption(i18n.t("sidebar.budget_help", lang, total=config.BUDGET_TOTAL))

    current = state.current_round()
    remaining = state.remaining_credits()
    committed = state.committed_allocation()
    st.sidebar.markdown(
        f"**{i18n.t('sidebar.allocated', lang, allocated=committed.total, total=config.BUDGET_TOTAL)}**"
    )
    st.sidebar.caption(i18n.t("sidebar.remaining", lang, remaining=remaining))

    if current is not None and current.is_complete:
        st.sidebar.success(
            i18n.t("sidebar.game_complete", lang, turns=current.turn_count)
        )
        st.sidebar.button(
            i18n.t("sidebar.restart", lang),
            on_click=state.reset_game,
            use_container_width=True,
        )
        return

    labels = i18n.dimension_labels(lang)
    for label, key in zip(labels, state.SLIDER_KEYS):
        st.sidebar.slider(
            label,
            min_value=config.ALLOCATION_MIN,
            max_value=remaining,
            step=1,
            key=key,
        )

    allocation = state.current_allocation()
    st.sidebar.markdown(
        f"**{i18n.t('sidebar.turn_allocated', lang, allocated=allocation.total)}**"
    )

    issues = validate_turn_allocation(allocation.as_array().tolist(), remaining)
    exceeds = next(
        (i for i in issues if i.rule == RULE_ALLOCATION_EXCEEDS_REMAINING), None
    )
    if exceeds is not None:
        st.sidebar.warning(
            i18n.t(
                "budget.exceeds_remaining",
                lang,
                count=int(exceeds.detail["difference"]),
                remaining=remaining,
            )
        )

    candidate = committed.plus(allocation)
    if candidate.largest > config.CONCENTRATION_LIMIT:
        st.sidebar.warning(
            i18n.t(
                "budget.concentration_warning",
                lang,
                limit=config.CONCENTRATION_LIMIT,
            )
        )

    st.sidebar.button(
        i18n.t("sidebar.reset", lang),
        on_click=state.reset_budget,
        use_container_width=True,
    )
    st.sidebar.button(
        i18n.t("sidebar.simulate", lang),
        type="primary",
        disabled=bool(issues),
        on_click=state.commit_turn,
        args=(district,),
        use_container_width=True,
    )

    if current is not None:
        st.sidebar.button(
            i18n.t("sidebar.restart", lang),
            on_click=state.reset_game,
            use_container_width=True,
        )


def render_dimension_table(result: SimulationResult, lang: str) -> None:
    initial = result.initial.as_array()
    final = result.final.as_array()
    st.dataframe(
        pd.DataFrame(
            {
                i18n.t("results.dimension", lang): list(i18n.dimension_labels(lang)),
                i18n.t("results.initial", lang): [_round(v) for v in initial],
                i18n.t("results.final", lang): [_round(v) for v in final],
                i18n.t("results.delta", lang): [
                    _signed(f - i) for i, f in zip(initial, final)
                ],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )


def render_scores(result: SimulationResult, lang: str) -> None:
    left, middle, right = st.columns(3)
    left.metric(i18n.t("results.riz_initial", lang), f"{_round(result.riz_initial)}")
    middle.metric(
        i18n.t("results.riz_final", lang),
        f"{_round(result.riz_final)}",
        _signed(result.urban_yield),
    )
    right.metric(
        i18n.t("results.change_pct", lang), f"{_signed(result.riz_change_pct)}%"
    )

    risk_col, sharpe_col = st.columns(2)
    risk_col.metric(i18n.t("results.risk", lang), f"{_round(result.risk)}")
    sharpe_col.metric(
        i18n.t("results.sharpe", lang), f"{result.sharpe:.{config.SHARPE_DECIMALS}f}"
    )


def render_profile(result: SimulationResult, lang: str) -> None:
    st.subheader(i18n.t("results.profile_header", lang))
    st.success(i18n.t(f"profile.{result.profile_id}", lang))

    applied = [m for m in result.modifiers if m.points != 0]
    st.caption(i18n.t("results.modifiers_header", lang))
    if not applied:
        st.write(i18n.t("results.no_modifiers", lang))
        return
    for modifier in applied:
        st.write(f"{_signed(modifier.points)} — {i18n.t(modifier.reason_key, lang)}")


def render_event(result: SimulationResult, lang: str) -> None:
    st.subheader(i18n.t("event.header", lang))
    event = result.event
    if event is None:
        return
    st.info(
        f"**{i18n.t(event.name_key, lang)}**\n\n{i18n.t(event.description_key, lang)}"
    )
    st.caption(i18n.t("event.impact", lang))
    st.dataframe(
        pd.DataFrame(
            {
                i18n.t("results.dimension", lang): list(i18n.dimension_labels(lang)),
                i18n.t("results.delta", lang): [
                    _signed(v) for v in event.impact.as_array()
                ],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )


def render_turn_status(current: state.Round, lang: str) -> None:
    """Show progress through the shared 100-credit game budget."""
    if current.is_complete:
        st.success(
            i18n.t(
                "game.complete",
                lang,
                total=config.BUDGET_TOTAL,
                turns=current.turn_count,
            )
        )
        return
    st.info(
        i18n.t(
            "game.progress",
            lang,
            turn=current.turn_count,
            remaining=current.remaining_credits,
        )
    )


def render_turn_history(current: state.Round, lang: str) -> None:
    """List completed turns and their independently drawn events."""
    st.subheader(i18n.t("turns.header", lang))
    st.dataframe(
        pd.DataFrame(
            {
                i18n.t("turns.turn", lang): [turn.number for turn in current.turns],
                i18n.t("turns.credits", lang): [
                    turn.credits_spent for turn in current.turns
                ],
                i18n.t("turns.event", lang): [
                    i18n.t(turn.event.name_key, lang) if turn.event is not None else ""
                    for turn in current.turns
                ],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )


def render_radar(result: SimulationResult, lang: str) -> None:
    st.subheader(i18n.t("results.radar_header", lang))
    st.plotly_chart(
        charts.build_radar(
            result.initial.as_array().tolist(),
            result.final.as_array().tolist(),
            i18n.dimension_labels(lang),
            i18n.t("results.radar_initial", lang),
            i18n.t("results.radar_final", lang),
        ),
        use_container_width=True,
    )


def render_comparison(current: state.Round, lang: str) -> None:
    st.subheader(i18n.t("compare.header", lang))
    st.plotly_chart(
        charts.build_comparison(
            {
                i18n.t("compare.you", lang): current.player.riz_final,
                i18n.t("compare.ai", lang): current.ai.riz_final,
                i18n.t("compare.random", lang): current.random.riz_final,
            }
        ),
        use_container_width=True,
    )


def render_map(district: District, lang: str) -> None:
    st.subheader(i18n.t("map.header", lang))
    geometry = district.geometry
    if not geometry:
        st.caption(i18n.t("map.unavailable", lang))
        return
    points = _boundary_points(geometry)
    if not points:
        st.caption(i18n.t("map.unavailable", lang))
        return
    st.map(pd.DataFrame(points, columns=["lon", "lat"]), zoom=12)


def _boundary_points(geometry: dict) -> list[tuple[float, float]]:
    coordinates = geometry.get("coordinates") or []
    rings = coordinates if geometry.get("type") == "Polygon" else [
        ring for polygon in coordinates for ring in polygon
    ]
    points: list[tuple[float, float]] = []
    for ring in rings:
        for point in ring:
            if isinstance(point, (list, tuple)) and len(point) >= 2:
                points.append((float(point[0]), float(point[1])))
    return points


def render_leaderboard(
    repository: LeaderboardRepository | None,
    current: state.Round,
    catalog: DistrictCatalog,
    limit: int,
    lang: str,
) -> None:
    st.subheader(i18n.t("leaderboard.header", lang))
    if repository is None:
        st.info(i18n.t("leaderboard.unavailable", lang))
        return

    _render_submission(repository, current, lang)

    options = [None] + [d.district_id for d in catalog.districts]
    selected = st.selectbox(
        i18n.t("leaderboard.filter_label", lang),
        options=options,
        index=options.index(current.district_id)
        if current.district_id in options
        else 0,
        format_func=lambda value: i18n.t("leaderboard.all_districts", lang)
        if value is None
        else _district_name(catalog, value),
    )

    try:
        entries = service.top_entries(repository, limit, selected)
    except LeaderboardUnavailable:
        st.info(i18n.t("leaderboard.unavailable", lang))
        return

    if not entries:
        st.write(i18n.t("leaderboard.empty", lang))
        return

    st.dataframe(
        pd.DataFrame(
            {
                i18n.t("leaderboard.rank", lang): list(range(1, len(entries) + 1)),
                i18n.t("leaderboard.player", lang): [e.nickname for e in entries],
                i18n.t("leaderboard.district", lang): [
                    _district_name(catalog, e.district_id) for e in entries
                ],
                i18n.t("results.riz_final", lang): [
                    _round(e.riz_final) for e in entries
                ],
                i18n.t("results.yield", lang): [
                    _signed(e.urban_yield) for e in entries
                ],
                i18n.t("results.risk", lang): [_round(e.risk) for e in entries],
            }
        ),
        hide_index=True,
        use_container_width=True,
    )


def _district_name(catalog: DistrictCatalog, district_id: str) -> str:
    district = catalog.get(district_id)
    return district.name if district else district_id


def _render_submission(
    repository: LeaderboardRepository, current: state.Round, lang: str
) -> None:
    if state.is_submitted(current.round_id):
        st.success(i18n.t("leaderboard.submitted", lang))
        return

    with st.form("submit_score"):
        nickname = st.text_input(
            i18n.t("leaderboard.nickname_label", lang),
            max_chars=config.NICKNAME_MAX_LENGTH,
        )
        submitted = st.form_submit_button(i18n.t("leaderboard.submit", lang))

    if not submitted:
        return
    if not service.is_valid_nickname(nickname):
        st.warning(
            i18n.t(
                "error.nickname_invalid",
                lang,
                minimum=config.NICKNAME_MIN_LENGTH,
                maximum=config.NICKNAME_MAX_LENGTH,
            )
        )
        return
    try:
        service.submit_result(
            repository,
            current.player,
            nickname,
            state.player_id(),
            current.round_id,
        )
    except LeaderboardUnavailable:
        st.info(i18n.t("leaderboard.unavailable", lang))
        return
    state.mark_submitted(current.round_id)
    st.success(i18n.t("leaderboard.submitted", lang))


def render_locked_leaderboard(lang: str) -> None:
    """Explain why an in-progress game cannot be submitted yet."""
    st.subheader(i18n.t("leaderboard.header", lang))
    st.info(i18n.t("leaderboard.complete_budget", lang))
