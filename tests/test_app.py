"""Chart construction and the Streamlit application behavior."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from riabita import config, i18n
from riabita.domain.models import Allocation
from riabita.ui import charts, state

APP = str(Path(__file__).resolve().parents[1] / "src" / "main.py")
LABELS = ("Mobility", "Culture", "Tourism", "Community")


@pytest.fixture(autouse=True)
def local_database(tmp_path: Path, monkeypatch) -> None:
    """Give every app test an isolated file-backed development leaderboard."""
    database_url = f"sqlite+pysqlite:///{tmp_path / 'leaderboard.sqlite3'}"
    monkeypatch.setenv("RIABITA_DATABASE_URL", database_url)


# --- Charts -----------------------------------------------------------------


@pytest.fixture
def radar():
    return charts.build_radar([10, 20, 30, 40], [15, 25, 35, 45], LABELS)


def test_radar_has_a_baseline_and_an_outcome_trace(radar) -> None:
    assert len(radar.data) == 2


def test_radar_polygons_are_closed(radar) -> None:
    for trace in radar.data:
        assert trace.r[0] == trace.r[-1]
        assert trace.theta[0] == trace.theta[-1]
        assert len(trace.r) == len(LABELS) + 1


def test_radar_axis_is_pinned_to_the_full_scale(radar) -> None:
    assert radar.layout.polar.radialaxis.range == (
        config.DIMENSION_MIN,
        config.DIMENSION_MAX,
    )


def test_radar_baseline_uses_a_dashed_line(radar) -> None:
    assert radar.data[0].line.dash == "dash"
    assert radar.data[1].line.dash == "solid"


def test_radar_traces_are_named_for_the_legend(radar) -> None:
    assert all(trace.name for trace in radar.data)


def test_comparison_ranks_descending_with_value_labels() -> None:
    figure = charts.build_comparison({"You": 51.7, "AI Planner": 60.2, "Random": 45.0})
    bar = figure.data[0]
    # Plotly draws horizontal bars bottom-up, so the highest value is last.
    assert list(bar.y) == ["Random", "You", "AI Planner"]
    assert list(bar.text) == ["45.0", "51.7", "60.2"]


def test_charts_do_not_import_streamlit() -> None:
    import inspect

    assert "streamlit" not in inspect.getsource(charts)


# --- Application ------------------------------------------------------------


def run_app(timeout: float = 30) -> AppTest:
    app = AppTest.from_file(APP, default_timeout=timeout)
    return app.run()


def sidebar_button(app: AppTest, label: str):
    return next(button for button in app.sidebar.button if button.label == label)


def district_selectbox(app: AppTest):
    return app.sidebar.selectbox[1]


def set_turn_allocation(app: AppTest, values: tuple[int, int, int, int]) -> AppTest:
    for index, value in enumerate(values):
        if app.sidebar.slider[index].value != value:
            app.sidebar.slider[index].set_value(value).run()
    return app


def commit_turn(app: AppTest) -> AppTest:
    sidebar_button(app, i18n.t("sidebar.simulate", "it")).click().run()
    return app


def test_app_starts_with_demo_data_and_local_database() -> None:
    app = run_app()
    assert not app.exception
    assert app.title[0].value == "RIABITA ROMA"


def test_demo_notice_is_shown() -> None:
    app = run_app()
    assert any(i18n.t("data.demo_notice", "it") in info.value for info in app.info)


def test_turn_is_disabled_until_at_least_one_credit_is_allocated() -> None:
    app = run_app()
    confirm = sidebar_button(app, i18n.t("sidebar.simulate", "it"))
    assert confirm.disabled is True


def test_partial_turn_is_enabled_without_spending_all_credits() -> None:
    app = run_app()
    app.sidebar.slider[0].set_value(40).run()
    confirm = sidebar_button(app, i18n.t("sidebar.simulate", "it"))
    assert confirm.disabled is False


def test_partial_turn_produces_results_and_preserves_remaining_credits() -> None:
    app = run_app()
    set_turn_allocation(app, (40, 0, 0, 0))
    commit_turn(app)

    assert not app.exception
    assert any(i18n.t("results.header", "it") in h.value for h in app.header)
    current = app.session_state[state.KEY_ROUND]
    assert current.turn_count == 1
    assert current.remaining_credits == 60
    assert current.player.allocation == Allocation(40, 0, 0, 0)


def test_all_three_strategies_share_one_event() -> None:
    app = run_app()
    set_turn_allocation(app, (20, 10, 0, 0))
    commit_turn(app)
    current = app.session_state[state.KEY_ROUND]
    assert current is not None
    event_ids = {
        current.player.event.event_id,
        current.ai.event.event_id,
        current.random.event.event_id,
    }
    assert len(event_ids) == 1
    assert current.event is not None


def test_benchmarks_receive_the_same_number_of_credits_each_turn() -> None:
    app = run_app()
    set_turn_allocation(app, (12, 8, 0, 0))
    commit_turn(app)
    turn = app.session_state[state.KEY_ROUND].turns[0]
    assert turn.player_allocation.total == 20
    assert turn.ai_allocation.total == 20
    assert turn.random_allocation.total == 20


def test_multiple_turns_accumulate_until_the_budget_is_exhausted() -> None:
    app = run_app()
    set_turn_allocation(app, (40, 0, 0, 0))
    commit_turn(app)
    first = app.session_state[state.KEY_ROUND]

    set_turn_allocation(app, (0, 60, 0, 0))
    commit_turn(app)
    completed = app.session_state[state.KEY_ROUND]

    assert first.remaining_credits == 60
    assert completed.remaining_credits == 0
    assert completed.is_complete
    assert completed.turn_count == 2
    assert completed.player.allocation == Allocation(40, 60, 0, 0)
    assert completed.round_id == first.round_id
    assert not app.sidebar.slider


def test_rerender_does_not_change_the_event_or_scores() -> None:
    app = run_app()
    set_turn_allocation(app, (30, 0, 0, 0))
    commit_turn(app)
    before = app.session_state[state.KEY_ROUND]
    app.run()
    after = app.session_state[state.KEY_ROUND]
    assert before == after


def test_player_id_is_stable_and_never_an_input() -> None:
    app = run_app()
    first = app.session_state[state.KEY_PLAYER_ID]
    app.run()
    assert app.session_state[state.KEY_PLAYER_ID] == first
    assert all(first not in (widget.value or "") for widget in app.text_input)


def test_leaderboard_is_enabled_with_local_sqlite() -> None:
    app = run_app()
    set_turn_allocation(app, (100, 0, 0, 0))
    commit_turn(app)
    assert not any(
        i18n.t("leaderboard.unavailable", "it") in info.value for info in app.info
    )
    assert any(
        i18n.t("leaderboard.header", "it") in heading.value
        for heading in app.subheader
    )
    assert app.text_input


def test_leaderboard_submission_is_locked_while_credits_remain() -> None:
    app = run_app()
    set_turn_allocation(app, (50, 0, 0, 0))
    commit_turn(app)
    assert not app.text_input
    assert any(
        i18n.t("leaderboard.complete_budget", "it") in info.value
        for info in app.info
    )


def test_language_switch_translates_the_interface() -> None:
    app = run_app()
    app.sidebar.selectbox[0].set_value("en").run()
    assert not app.exception
    assert any("Confirm investment" in b.label for b in app.sidebar.button)


def test_language_switch_preserves_the_round() -> None:
    app = run_app()
    set_turn_allocation(app, (25, 0, 0, 0))
    commit_turn(app)
    before = app.session_state[state.KEY_ROUND]
    app.sidebar.selectbox[0].set_value("en").run()
    assert app.session_state[state.KEY_ROUND] == before
    assert not app.exception


def test_clear_turn_restores_zero_allocations() -> None:
    app = run_app()
    app.sidebar.slider[0].set_value(70).run()
    reset = next(b for b in app.sidebar.button if b.label == i18n.t("sidebar.reset", "it"))
    reset.click().run()
    assert all(slider.value == 0 for slider in app.sidebar.slider)


def test_restart_restores_the_full_budget() -> None:
    app = run_app()
    set_turn_allocation(app, (30, 0, 0, 0))
    commit_turn(app)
    sidebar_button(app, i18n.t("sidebar.restart", "it")).click().run()
    assert app.session_state[state.KEY_ROUND] is None
    assert all(slider.value == 0 for slider in app.sidebar.slider)


def test_concentration_warning_uses_the_cumulative_allocation() -> None:
    app = run_app()
    set_turn_allocation(app, (50, 0, 0, 0))
    commit_turn(app)
    app.sidebar.slider[0].set_value(11).run()
    assert any("60" in w.value for w in app.sidebar.warning)


def test_district_is_selectable_before_the_first_investment() -> None:
    app = run_app()
    assert district_selectbox(app).disabled is False


def test_district_locks_once_a_turn_is_committed() -> None:
    app = run_app()
    set_turn_allocation(app, (30, 0, 0, 0))
    commit_turn(app)
    assert district_selectbox(app).disabled is True
    assert any(
        i18n.t("sidebar.district_locked", "it") in caption.value
        for caption in app.sidebar.caption
    )


def test_district_unlocks_after_restarting_the_game() -> None:
    app = run_app()
    set_turn_allocation(app, (30, 0, 0, 0))
    commit_turn(app)
    sidebar_button(app, i18n.t("sidebar.restart", "it")).click().run()
    assert district_selectbox(app).disabled is False


def test_district_unlocks_once_the_budget_is_exhausted() -> None:
    app = run_app()
    set_turn_allocation(app, (100, 0, 0, 0))
    commit_turn(app)
    assert district_selectbox(app).disabled is False


def test_random_strategy_button_plays_the_whole_game_in_several_turns() -> None:
    app = run_app()
    sidebar_button(app, i18n.t("sidebar.use_random", "it")).click().run()
    current = app.session_state[state.KEY_ROUND]
    assert current.is_complete
    assert current.player.allocation.total == config.BUDGET_TOTAL
    assert current.turn_count >= config.RANDOM_AUTOPLAY_MIN_TURNS
    assert not app.sidebar.slider


def test_ai_strategy_button_plays_the_whole_game_over_its_turn_horizon() -> None:
    app = run_app()
    sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    current = app.session_state[state.KEY_ROUND]
    assert current.is_complete
    assert current.player.allocation.total == config.BUDGET_TOTAL
    assert current.turn_count == config.AI_AUTOPLAY_TURNS
    assert not app.sidebar.slider


def test_strategy_buttons_only_spend_the_credits_left_after_a_manual_turn() -> None:
    app = run_app()
    set_turn_allocation(app, (40, 0, 0, 0))
    commit_turn(app)
    sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    current = app.session_state[state.KEY_ROUND]
    assert current.is_complete
    assert current.player.allocation.total == config.BUDGET_TOTAL
    # The manual turn plus the AI's own turn horizon on the remaining 60 credits.
    assert current.turn_count == 1 + config.AI_AUTOPLAY_TURNS


def strategy_checkbox(app: AppTest):
    return app.sidebar.checkbox[0]


def test_step_mode_plays_a_single_turn_per_click() -> None:
    app = run_app()
    strategy_checkbox(app).set_value(True).run()
    sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    current = app.session_state[state.KEY_ROUND]
    assert current.turn_count == 1
    assert not current.is_complete
    queue = app.session_state[state.KEY_STRATEGY_QUEUE]
    assert queue is not None
    assert queue.kind == state.AI_STRATEGY
    assert len(queue.turns) == config.AI_AUTOPLAY_TURNS - 1
    assert any(
        i18n.t("sidebar.strategy_step_pending", "it", remaining=len(queue.turns))
        in info.value
        for info in app.sidebar.info
    )


def test_step_mode_needs_one_click_per_turn_to_finish_the_ai_strategy() -> None:
    app = run_app()
    strategy_checkbox(app).set_value(True).run()
    for _ in range(config.AI_AUTOPLAY_TURNS):
        sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    current = app.session_state[state.KEY_ROUND]
    assert current.is_complete
    assert current.turn_count == config.AI_AUTOPLAY_TURNS
    assert app.session_state[state.KEY_STRATEGY_QUEUE] is None


def test_disabling_step_mode_drains_the_rest_of_the_queue_on_the_next_click() -> None:
    app = run_app()
    strategy_checkbox(app).set_value(True).run()
    sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    strategy_checkbox(app).set_value(False).run()
    sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    current = app.session_state[state.KEY_ROUND]
    assert current.is_complete
    assert app.session_state[state.KEY_STRATEGY_QUEUE] is None


def test_a_manual_turn_clears_a_pending_strategy_queue() -> None:
    app = run_app()
    strategy_checkbox(app).set_value(True).run()
    sidebar_button(app, i18n.t("sidebar.use_ai", "it")).click().run()
    assert app.session_state[state.KEY_STRATEGY_QUEUE] is not None

    remaining = app.session_state[state.KEY_ROUND].remaining_credits
    set_turn_allocation(app, (remaining, 0, 0, 0))
    commit_turn(app)
    assert app.session_state[state.KEY_STRATEGY_QUEUE] is None
