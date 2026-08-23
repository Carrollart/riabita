"""Translation catalog and lookup.

Every user-facing string resolves through `t()`. Adding a language means adding
one entry to CATALOG with the same key set; `tests/test_i18n.py` enforces parity.
"""

from __future__ import annotations

from typing import Final

from riabita import config

DEFAULT_LANGUAGE: Final[str] = "it"

_IT: Final[dict[str, str]] = {
    "app.title": "RIABITA ROMA",
    "app.tagline": "Costruisci il portafoglio della città",
    "app.welcome": "Scegli un quartiere e distribuisci i 100 crediti per iniziare.",
    "app.data_caption": "Indice di Riabitabilità (RIz) — prototipo di simulazione urbana.",
    "language.label": "Lingua",
    "dimension.mobility": "Mobilità",
    "dimension.culture": "Cultura",
    "dimension.tourism": "Turismo",
    "dimension.socio": "Comunità",
    "sidebar.district_header": "1. Scegli il quartiere",
    "sidebar.district_label": "Quartiere",
    "sidebar.baseline_header": "Valori iniziali",
    "sidebar.budget_header": "2. Distribuisci il budget",
    "sidebar.budget_help": "Hai {total} crediti da distribuire.",
    "sidebar.allocated": "Allocato: {allocated} / {total}",
    "sidebar.remaining": "Restano {remaining} crediti.",
    "sidebar.reset": "Reimposta",
    "sidebar.simulate": "Simula investimenti",
    "budget.add": "Aggiungi {count} crediti per arrivare a {total}.",
    "budget.remove": "Rimuovi {count} crediti per arrivare a {total}.",
    "budget.concentration_warning": "Più di {limit} crediti su una dimensione: scatta la penalità di concentrazione.",
    "results.header": "Risultati della simulazione",
    "results.before": "Prima degli investimenti",
    "results.after": "Dopo gli investimenti",
    "results.dimension": "Dimensione",
    "results.initial": "Iniziale",
    "results.final": "Finale",
    "results.delta": "Δ",
    "results.riz_initial": "RIz iniziale",
    "results.riz_final": "RIz finale",
    "results.yield": "Rendimento urbano",
    "results.change_pct": "Variazione",
    "results.risk": "Rischio urbano",
    "results.sharpe": "Sharpe urbano",
    "results.radar_header": "Equilibrio delle dimensioni",
    "results.radar_initial": "Situazione iniziale",
    "results.radar_final": "Dopo gli investimenti",
    "results.modifiers_header": "Bonus e penalità",
    "results.no_modifiers": "Nessun bonus o penalità applicati.",
    "results.profile_header": "La tua città",
    "event.header": "Evento casuale",
    "event.impact": "Effetti dell'evento",
    "event.transport_line.name": "Nuova linea di trasporto",
    "event.transport_line.description": "Una nuova infrastruttura migliora l'accessibilità urbana.",
    "event.cultural_festival.name": "Festival culturale",
    "event.cultural_festival.description": "Un grande evento accresce vitalità e attrattività del quartiere.",
    "event.tourist_boom.name": "Boom turistico",
    "event.tourist_boom.description": "Il quartiere attira un numero inatteso di visitatori.",
    "event.housing_crisis.name": "Crisi abitativa",
    "event.housing_crisis.description": "La pressione immobiliare penalizza i residenti.",
    "event.heat_wave.name": "Ondata di calore",
    "event.heat_wave.description": "Un evento climatico estremo riduce la qualità urbana.",
    "modifier.equilibrium": "Bonus equilibrio",
    "modifier.overtourism_gap": "Penalità overtourism",
    "modifier.concentration": "Penalità concentrazione",
    "modifier.diversification": "Bonus diversificazione",
    "profile.stagnant": "Città in Stallo",
    "profile.vulnerable": "Città Vulnerabile",
    "profile.resilient": "Città Resiliente",
    "profile.transitional": "Città in Transizione",
    "compare.header": "Confronto strategie",
    "compare.you": "Tu",
    "compare.ai": "AI Planner",
    "compare.random": "Visitatore casuale",
    "map.header": "Mappa del quartiere",
    "map.unavailable": "Nessuna geometria disponibile per questo quartiere.",
    "leaderboard.header": "Classifica",
    "leaderboard.nickname_label": "Il tuo nome",
    "leaderboard.submit": "Invia punteggio",
    "leaderboard.submitted": "Punteggio inviato.",
    "leaderboard.empty": "Nessun punteggio registrato finora.",
    "leaderboard.unavailable": "La classifica non è disponibile al momento. La partita funziona comunque.",
    "leaderboard.filter_label": "Filtra per quartiere",
    "leaderboard.all_districts": "Tutti i quartieri",
    "leaderboard.rank": "#",
    "leaderboard.player": "Giocatore",
    "leaderboard.district": "Quartiere",
    "data.demo_notice": "Dati dimostrativi: valori e geometrie sono segnaposto, non dati di ricerca.",
    "error.allocation_length": "Servono esattamente quattro valori di investimento.",
    "error.allocation_not_integer": "Gli investimenti devono essere numeri interi.",
    "error.allocation_out_of_range": "Ogni investimento deve essere tra {minimum} e {maximum}.",
    "error.allocation_sum": "Il totale deve essere esattamente {expected}.",
    "error.dimension_out_of_range": "I valori del quartiere devono essere tra 0 e 100.",
    "error.nickname_invalid": "Usa da {minimum} a {maximum} caratteri: lettere, numeri, spazi, trattini.",
}

_EN: Final[dict[str, str]] = {
    "app.title": "RIABITA ROMA",
    "app.tagline": "Build the city portfolio",
    "app.welcome": "Pick a district and allocate the 100 credits to begin.",
    "app.data_caption": "Riabitability Index (RIz) — urban simulation prototype.",
    "language.label": "Language",
    "dimension.mobility": "Mobility",
    "dimension.culture": "Culture",
    "dimension.tourism": "Tourism",
    "dimension.socio": "Community",
    "sidebar.district_header": "1. Select the district",
    "sidebar.district_label": "District",
    "sidebar.baseline_header": "Baseline values",
    "sidebar.budget_header": "2. Allocate the budget",
    "sidebar.budget_help": "You have {total} credits to distribute.",
    "sidebar.allocated": "Allocated: {allocated} / {total}",
    "sidebar.remaining": "{remaining} credits remaining.",
    "sidebar.reset": "Reset",
    "sidebar.simulate": "Simulate investments",
    "budget.add": "Add {count} credits to reach {total}.",
    "budget.remove": "Remove {count} credits to reach {total}.",
    "budget.concentration_warning": "More than {limit} credits on one dimension triggers the concentration penalty.",
    "results.header": "Simulation results",
    "results.before": "Before investments",
    "results.after": "After investments",
    "results.dimension": "Dimension",
    "results.initial": "Initial",
    "results.final": "Final",
    "results.delta": "Δ",
    "results.riz_initial": "Initial RIz",
    "results.riz_final": "Final RIz",
    "results.yield": "Urban yield",
    "results.change_pct": "Change",
    "results.risk": "Urban risk",
    "results.sharpe": "Urban Sharpe",
    "results.radar_header": "Dimensional equilibrium",
    "results.radar_initial": "Initial state",
    "results.radar_final": "After investments",
    "results.modifiers_header": "Bonuses and penalties",
    "results.no_modifiers": "No bonuses or penalties applied.",
    "results.profile_header": "Your city",
    "event.header": "Random event",
    "event.impact": "Event effects",
    "event.transport_line.name": "New transport line",
    "event.transport_line.description": "New infrastructure improves urban accessibility.",
    "event.cultural_festival.name": "Cultural festival",
    "event.cultural_festival.description": "A major event boosts local vitality and appeal.",
    "event.tourist_boom.name": "Tourist boom",
    "event.tourist_boom.description": "The district attracts an unexpected surge of visitors.",
    "event.housing_crisis.name": "Housing crisis",
    "event.housing_crisis.description": "Rising property pressure penalizes residents.",
    "event.heat_wave.name": "Heatwave",
    "event.heat_wave.description": "An extreme weather event reduces urban quality.",
    "modifier.equilibrium": "Equilibrium bonus",
    "modifier.overtourism_gap": "Overtourism penalty",
    "modifier.concentration": "Concentration penalty",
    "modifier.diversification": "Diversification bonus",
    "profile.stagnant": "Stagnant City",
    "profile.vulnerable": "Vulnerable City",
    "profile.resilient": "Resilient City",
    "profile.transitional": "Transitional City",
    "compare.header": "Strategy comparison",
    "compare.you": "You",
    "compare.ai": "AI Planner",
    "compare.random": "Casual visitor",
    "map.header": "District map",
    "map.unavailable": "No geometry available for this district.",
    "leaderboard.header": "Leaderboard",
    "leaderboard.nickname_label": "Your name",
    "leaderboard.submit": "Submit score",
    "leaderboard.submitted": "Score submitted.",
    "leaderboard.empty": "No scores recorded yet.",
    "leaderboard.unavailable": "The leaderboard is unavailable right now. The game still works.",
    "leaderboard.filter_label": "Filter by district",
    "leaderboard.all_districts": "All districts",
    "leaderboard.rank": "#",
    "leaderboard.player": "Player",
    "leaderboard.district": "District",
    "data.demo_notice": "Demo data: values and geometries are placeholders, not research output.",
    "error.allocation_length": "Exactly four investment values are required.",
    "error.allocation_not_integer": "Investments must be whole numbers.",
    "error.allocation_out_of_range": "Each investment must be between {minimum} and {maximum}.",
    "error.allocation_sum": "The total must be exactly {expected}.",
    "error.dimension_out_of_range": "District values must be between 0 and 100.",
    "error.nickname_invalid": "Use {minimum} to {maximum} characters: letters, numbers, spaces, hyphens.",
}

CATALOG: Final[dict[str, dict[str, str]]] = {"it": _IT, "en": _EN}

LANGUAGE_NAMES: Final[dict[str, str]] = {"it": "Italiano", "en": "English"}


def available_languages() -> tuple[str, ...]:
    return tuple(CATALOG)


def language_name(language: str) -> str:
    return LANGUAGE_NAMES.get(language, language.upper())


def t(key: str, language: str = DEFAULT_LANGUAGE, **params: object) -> str:
    """Resolve a key in `language`, falling back to Italian, then to the key."""
    template = CATALOG.get(language, {}).get(key)
    if template is None:
        template = CATALOG[DEFAULT_LANGUAGE].get(key, key)
    if not params:
        return template
    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template


def dimension_labels(language: str = DEFAULT_LANGUAGE) -> tuple[str, ...]:
    """The four dimension labels in (M, C, T, S) order."""
    return tuple(t(f"dimension.{key}", language) for key in config.DIMENSION_KEYS)
