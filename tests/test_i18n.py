"""Translation catalog completeness and lookup behavior."""

from __future__ import annotations

import re

import pytest

from riabita import config, events, i18n
from riabita.domain import validation

PLACEHOLDER = re.compile(r"\{(\w+)\}")


def test_every_language_defines_the_same_keys() -> None:
    reference = set(i18n.CATALOG[i18n.DEFAULT_LANGUAGE])
    for language, catalog in i18n.CATALOG.items():
        missing = reference - set(catalog)
        extra = set(catalog) - reference
        assert not missing, f"{language} is missing {sorted(missing)}"
        assert not extra, f"{language} has unexpected {sorted(extra)}"


@pytest.mark.parametrize("language", i18n.available_languages())
def test_no_value_is_blank(language: str) -> None:
    blank = [k for k, v in i18n.CATALOG[language].items() if not v.strip()]
    assert not blank


def test_placeholders_match_across_languages() -> None:
    reference = i18n.CATALOG[i18n.DEFAULT_LANGUAGE]
    for language, catalog in i18n.CATALOG.items():
        for key, template in catalog.items():
            assert set(PLACEHOLDER.findall(template)) == set(
                PLACEHOLDER.findall(reference[key])
            ), f"{language}:{key} placeholder mismatch"


@pytest.mark.parametrize("language", i18n.available_languages())
def test_every_event_has_a_name_and_description(language: str) -> None:
    for event_id in events.event_ids():
        for suffix in ("name", "description"):
            key = f"event.{event_id}.{suffix}"
            assert i18n.t(key, language) != key


@pytest.mark.parametrize("language", i18n.available_languages())
def test_every_modifier_profile_and_error_has_a_label(language: str) -> None:
    keys = [
        f"modifier.{m}"
        for m in (
            config.MODIFIER_EQUILIBRIUM,
            config.MODIFIER_OVERTOURISM_GAP,
            config.MODIFIER_CONCENTRATION,
            config.MODIFIER_DIVERSIFICATION,
        )
    ]
    keys += [
        f"profile.{p}"
        for p in (
            config.PROFILE_STAGNANT,
            config.PROFILE_VULNERABLE,
            config.PROFILE_RESILIENT,
            config.PROFILE_TRANSITIONAL,
        )
    ]
    keys += [
        f"error.{r}"
        for r in (
            validation.RULE_ALLOCATION_LENGTH,
            validation.RULE_ALLOCATION_NOT_INTEGER,
            validation.RULE_ALLOCATION_OUT_OF_RANGE,
            validation.RULE_ALLOCATION_SUM,
            validation.RULE_ALLOCATION_EMPTY,
            validation.RULE_ALLOCATION_EXCEEDS_REMAINING,
            validation.RULE_DIMENSION_OUT_OF_RANGE,
        )
    ]
    for key in keys:
        assert i18n.t(key, language) != key


def test_unknown_key_returns_the_key() -> None:
    assert i18n.t("nope.missing", "en") == "nope.missing"


def test_unknown_language_falls_back_to_italian() -> None:
    assert i18n.t("dimension.tourism", "de") == "Turismo"


def test_parameters_are_interpolated() -> None:
    assert "42" in i18n.t("sidebar.budget_help", "en", total=42)


def test_missing_parameter_does_not_raise() -> None:
    assert i18n.t("sidebar.budget_help", "en") == i18n.CATALOG["en"]["sidebar.budget_help"]


def test_dimension_labels_follow_vector_order() -> None:
    assert i18n.dimension_labels("en") == ("Mobility", "Culture", "Tourism", "Community")


def test_french_translation_and_flag_are_available() -> None:
    assert i18n.t("language.label", "fr") == "Langue"
    assert i18n.t("sidebar.reset", "fr") == "Réinitialiser l'investissement"
    assert i18n.language_option("fr") == "🇫🇷 Français"


def test_italian_is_the_default_language() -> None:
    assert i18n.DEFAULT_LANGUAGE == "it"
    assert i18n.t("dimension.socio") == "Comunità"
