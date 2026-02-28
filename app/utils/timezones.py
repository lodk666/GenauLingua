"""
Утилиты для работы с часовыми поясами

Сохранить как: app/utils/timezones.py
"""

from typing import Dict, Tuple

# Маппинг городов → (название, timezone, UTC offset)
TIMEZONE_CITIES: Dict[str, Tuple[str, str, str]] = {
    # ============================================
    # ПЕРВЫЙ ЭКРАН (4 основных города)
    # ============================================
    "london": ("🇬🇧 Лондон", "Europe/London", "+00:00"),
    "berlin": ("🇩🇪 Берлин", "Europe/Berlin", "+01:00"),
    "kyiv": ("🇺🇦 Київ", "Europe/Kyiv", "+02:00"),
    "istanbul": ("🇹🇷 İstanbul", "Europe/Istanbul", "+03:00"),

    # ============================================
    # ВТОРОЙ ЭКРАН (16 дополнительных городов)
    # ============================================

    # Америка
    "los_angeles": ("🇺🇸 Лос-Анджелес", "America/Los_Angeles", "-08:00"),
    "chicago": ("🇺🇸 Чикаго", "America/Chicago", "-06:00"),
    "new_york": ("🇺🇸 Нью-Йорк", "America/New_York", "-05:00"),
    "toronto": ("🇨🇦 Торонто", "America/Toronto", "-05:00"),
    "mexico_city": ("🇲🇽 Мехико", "America/Mexico_City", "-06:00"),
    "sao_paulo": ("🇧🇷 Сан-Паулу", "America/Sao_Paulo", "-03:00"),

    # Азия
    "dubai": ("🇦🇪 Дубай", "Asia/Dubai", "+04:00"),
    "almaty": ("🇰🇿 Алматы", "Asia/Almaty", "+05:00"),
    "tashkent": ("🇺🇿 Ташкент", "Asia/Tashkent", "+05:00"),
    "delhi": ("🇮🇳 Дели", "Asia/Kolkata", "+05:30"),
    "bangkok": ("🇹🇭 Бангкок", "Asia/Bangkok", "+07:00"),
    "hanoi": ("🇻🇳 Ханой", "Asia/Ho_Chi_Minh", "+07:00"),
    "beijing": ("🇨🇳 Пекин", "Asia/Shanghai", "+08:00"),
    "tokyo": ("🇯🇵 Токио", "Asia/Tokyo", "+09:00"),
    "seoul": ("🇰🇷 Сеул", "Asia/Seoul", "+09:00"),
    "sydney": ("🇦🇺 Сидней", "Australia/Sydney", "+11:00"),
}


def get_city_name(city_code: str, lang: str = "ru") -> str:
    """
    Получить название города

    Args:
        city_code: код города (например, "london")
        lang: язык интерфейса (пока не используется)

    Returns:
        Название города с флагом
    """
    if city_code not in TIMEZONE_CITIES:
        return "🌍 Неизвестный город"

    return TIMEZONE_CITIES[city_code][0]


def get_timezone(city_code: str) -> str:
    """
    Получить timezone по коду города

    Args:
        city_code: код города (например, "london")

    Returns:
        Timezone string (например, "Europe/London")
    """
    if city_code not in TIMEZONE_CITIES:
        return "Europe/Berlin"  # default

    return TIMEZONE_CITIES[city_code][1]


def get_utc_offset(city_code: str) -> str:
    """
    Получить UTC offset по коду города

    Args:
        city_code: код города (например, "london")

    Returns:
        UTC offset string (например, "+00:00")
    """
    if city_code not in TIMEZONE_CITIES:
        return "+01:00"  # default для Берлина

    return TIMEZONE_CITIES[city_code][2]


def get_all_cities() -> Dict[str, Tuple[str, str, str]]:
    """Получить все доступные города"""
    return TIMEZONE_CITIES


def get_main_cities() -> list[str]:
    """Получить коды 4 основных городов"""
    return ["london", "berlin", "kyiv", "istanbul"]


def get_extended_cities() -> list[str]:
    """Получить коды 16 дополнительных городов"""
    main = get_main_cities()
    return [code for code in TIMEZONE_CITIES.keys() if code not in main]