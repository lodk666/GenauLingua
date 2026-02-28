"""
Система локализации для GenauLingua Bot
"""

from typing import Optional
import app.locales.ru as ru
import app.locales.uk as uk
import app.locales.en as en
import app.locales.tr as tr

# Доступные локали
LOCALES = {
    "uk": uk.TEXTS,
    "en": en.TEXTS,
    "tr": tr.TEXTS,
    "ru": ru.TEXTS,
}

# Язык по умолчанию
DEFAULT_LOCALE = "uk"


def get_text(key: str, lang: Optional[str] = None, **kwargs) -> str:
    if lang not in LOCALES:
        lang = DEFAULT_LOCALE

    texts = LOCALES[lang]
    text = texts.get(key)

    if text is None:
        # Fallback to Russian if key missing in current locale
        text = LOCALES["uk"].get(key)
    if text is None:
        return f"[MISSING: {key}]"

    try:
        return text.format(**kwargs)
    except KeyError as e:
        return f"[ERROR: {key} missing parameter {e}]"


def get_available_languages() -> list[str]:
    return list(LOCALES.keys())


def pluralize(number: int, forms: tuple, lang: str = "ru") -> str:
    n = abs(number)
    n %= 100
    if n >= 5 and n <= 20:
        return forms[2]
    n %= 10
    if n == 1:
        return forms[0]
    if n >= 2 and n <= 4:
        return forms[1]
    return forms[2]


def is_language_supported(lang: str) -> bool:
    return lang in LOCALES