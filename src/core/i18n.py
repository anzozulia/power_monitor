"""
Simple i18n helpers for alerting and diagrams.
"""

from __future__ import annotations

from typing import Dict, List


_SUPPORTED_LANGUAGES = {"en", "ru", "uk"}

_ALERT_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "power_off": "POWER OFF",
        "power_on": "POWER ON",
        "power_was_on_for": "Power was ON for",
        "power_was_off_for": "Power was OFF for",
        "unit_s": "s",
        "unit_m": "m",
        "unit_h": "h",
    },
    "ru": {
        "power_off": "СВЕТ ВЫКЛЮЧИЛСЯ",
        "power_on": "СВЕТ ВЕРНУЛСЯ",
        "power_was_on_for": "Свет был",
        "power_was_off_for": "Света не было ",
        "unit_s": "с",
        "unit_m": "м",
        "unit_h": "ч",
    },
    "uk": {
        "power_off": "СВІТЛО ЗНИКЛО",
        "power_on": "СВІТЛО ПОВЕРНУЛОСЯ",
        "power_was_on_for": "Світло було",
        "power_was_off_for": "Світла не було",
        "unit_s": "с",
        "unit_m": "хв",
        "unit_h": "год",
    },
}

_DIAGRAM_STRINGS: Dict[str, Dict[str, str | List[str]]] = {
    "en": {
        "title": "Power outages",
        "weekdays": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
    },
    "ru": {
        "title": "Отключения света",
        "weekdays": ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"],
    },
    "uk": {
        "title": "Відключення світла",
        "weekdays": ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "НД"],
    },
}

_CAPTION_STRINGS: Dict[str, str] = {
    "en": "Weekly Power Status",
    "ru": "Недельный статус питания",
    "uk": "Тижневий статус живлення",
}


def _normalize_language(language: str | None) -> str:
    if language in _SUPPORTED_LANGUAGES:
        return language
    return "en"


def get_alert_strings(language: str | None) -> Dict[str, str]:
    lang = _normalize_language(language)
    return _ALERT_STRINGS[lang]


def get_diagram_strings(language: str | None) -> Dict[str, str | List[str]]:
    lang = _normalize_language(language)
    return _DIAGRAM_STRINGS[lang]


def get_diagram_caption(language: str | None) -> str:
    lang = _normalize_language(language)
    return _CAPTION_STRINGS[lang]
