"""RIABITA ROMA — Streamlit entry point.

Composition only: resolve settings, load data, wire the views. Run with
`streamlit run src/main.py`.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

_IS_STREAMLIT = bool(
    getattr(getattr(st, "runtime", None), "exists", lambda: False)()
)


def _repository_impl(database_url: str | None) -> Any:
    from riabita.domain.errors import LeaderboardUnavailable
    from riabita.leaderboard.repository import build_repository

    try:
        return build_repository(database_url)
    except LeaderboardUnavailable:
        return None


_repository: Callable[[str | None], Any] = _repository_impl
if _IS_STREAMLIT:
    _repository = st.cache_resource(show_spinner=False)(_repository_impl)


def main() -> None:
    from riabita import config, i18n
    from riabita.domain.errors import DataSourceError
    from riabita.ui import state, views

    st.set_page_config(page_title="RIABITA ROMA", layout="wide")

    settings = config.get_settings()
    state.init_state(settings.default_language)
    lang = views.render_language_selector()

    st.title(i18n.t("app.title", lang))
    st.caption(i18n.t("app.tagline", lang))

    try:
        catalog = state.load_catalog(settings.districts_path)
    except DataSourceError:
        st.error(i18n.t("data.source_error", lang))
        return
    for district_id in catalog.warnings:
        print(i18n.t("data.district_skipped", lang, district=district_id))
    district = views.render_district_picker(catalog, lang)
    state.select_district(district.district_id)
    views.render_selection_map(catalog, lang, selected_district_id=district.district_id)
    views.render_budget_controls(district, lang)

    current = state.current_round()
    if current is None or current.district_id != district.district_id:
        st.info(i18n.t("app.welcome", lang))
        st.caption(i18n.t("app.data_caption", lang))
        return

    views.render_turn_status(current, lang)
    st.header(i18n.t("results.header", lang))
    results, profile = st.columns([3, 2])
    with results:
        views.render_dimension_table(current.player, lang)
        views.render_scores(current.player, lang)
    with profile:
        views.render_profile(current.player, lang)

    radar, event = st.columns(2)
    with radar:
        views.render_radar(current.player, lang)
    with event:
        views.render_event(current.player, lang)

    views.render_turn_history(current, lang)
    repository = _repository(settings.database_url)
    views.render_comparison(current, repository, lang)
    if current.is_complete:
        views.render_leaderboard(
            repository,
            current,
            catalog,
            settings.leaderboard_limit,
            lang,
        )
    else:
        views.render_locked_leaderboard(lang)
    st.caption(i18n.t("app.data_caption", lang))


if _IS_STREAMLIT:
    main()
else:
    print(
        "RIABITA ROMA deve essere avviato con Streamlit. "
        "Usa: .venv/bin/python -m streamlit run src/main.py"
    )
