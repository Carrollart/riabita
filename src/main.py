"""RIABITA ROMA — Streamlit entry point.

Composition only: resolve settings, load data, wire the views. Run with
`streamlit run src/main.py`.
"""

from __future__ import annotations

import streamlit as st

from riabita import config, i18n
from riabita.domain.errors import LeaderboardUnavailable
from riabita.leaderboard.repository import LeaderboardRepository, build_repository
from riabita.ui import state, views


@st.cache_resource(show_spinner=False)
def _repository(database_url: str | None) -> LeaderboardRepository | None:
    try:
        return build_repository(database_url)
    except LeaderboardUnavailable:
        return None


def main() -> None:
    st.set_page_config(page_title="RIABITA ROMA", layout="wide")

    settings = config.get_settings()
    state.init_state(settings.default_language)
    lang = views.render_language_selector()

    st.title(i18n.t("app.title", lang))
    st.caption(i18n.t("app.tagline", lang))

    catalog = state.load_catalog(settings.districts_path)
    district = views.render_district_picker(catalog, lang)
    allocation, simulate = views.render_budget_controls(lang)

    if simulate:
        state.store_round(state.play_round(district, allocation))

    current = state.current_round()
    if current is None or current.district_id != district.district_id:
        st.info(i18n.t("app.welcome", lang))
        views.render_map(district, lang)
        st.caption(i18n.t("app.data_caption", lang))
        return

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

    views.render_comparison(current, lang)
    views.render_map(district, lang)
    views.render_leaderboard(
        _repository(settings.database_url),
        current,
        catalog,
        settings.leaderboard_limit,
        lang,
    )
    st.caption(i18n.t("app.data_caption", lang))


main()
