"""
Система локализации для GenauLingua Bot
"""

from typing import Optional
import app.locales.ru as ru
import app.locales.uk as uk

# Доступные локали
LOCALES = {
    "ru": ru.TEXTS,
    "uk": uk.TEXTS,
}

# Язык по умолчанию
DEFAULT_LOCALE = "ru"


def get_text(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Получить локализованный текст по ключу

    Args:
        key: Ключ текста (например, "welcome_title")
        lang: Код языка ("ru" или "uk"). Если None, используется DEFAULT_LOCALE
        **kwargs: Параметры для форматирования (например, name="Иван")

    Returns:
        Отформатированный текст

    Examples:
        >>> get_text("welcome_title", "ru", name="Иван")
        "👋 <b>Привет, Иван!</b>"

        >>> get_text("quiz_correct", "uk")
        "✅ <b>Правильно!</b>"
    """
    # Если язык не указан или не существует, используем русский
    if lang not in LOCALES:
        lang = DEFAULT_LOCALE

    # Получаем текст из словаря локали
    texts = LOCALES[lang]
    text = texts.get(key)

    # Если ключ не найден, возвращаем ключ как есть (для дебага)
    if text is None:
        return f"[MISSING: {key}]"

    # Форматируем текст с параметрами
    try:
        return text.format(**kwargs)
    except KeyError as e:
        # Если не хватает параметра для форматирования
        return f"[ERROR: {key} missing parameter {e}]"


def get_available_languages() -> list[str]:
    """Получить список доступных языков"""
    return list(LOCALES.keys())




def pluralize(number: int, forms: tuple, lang: str = "ru") -> str:
    """
    Склонение существительных по числу

    Args:
        number: Число
        forms: Кортеж форм (один, два, пять) например ("слово", "слова", "слов")
        lang: Язык (ru или uk)

    Returns:
        Правильная форма слова

    Examples:
        >>> pluralize(1, ("слово", "слова", "слов"))
        "слово"
        >>> pluralize(2, ("слово", "слова", "слов"))
        "слова"
        >>> pluralize(5, ("слово", "слова", "слов"))
        "слов"
    """
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
    """Проверить, поддерживается ли язык"""
    return lang in LOCALES