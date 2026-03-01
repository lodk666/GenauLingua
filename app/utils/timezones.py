"""
Утилиты для работы с часовыми поясами
"""

from typing import Dict, Tuple

# Маппинг городов → (names_by_lang, timezone, UTC offset)
# Структура: city_code -> ({"ru": "name", "uk": "name", "en": "name", "tr": "name"}, timezone, offset)
TIMEZONE_CITIES: Dict[str, Tuple[Dict[str, str], str, str]] = {
    # ============================================
    # ПЕРВЫЙ ЭКРАН (4 основных города)
    # ============================================
    "london": (
        {"ru": "🇬🇧 Лондон", "uk": "🇬🇧 Лондон", "en": "🇬🇧 London", "tr": "🇬🇧 Londra"},
        "Europe/London", "+00:00"
    ),
    "berlin": (
        {"ru": "🇩🇪 Берлин", "uk": "🇩🇪 Берлін", "en": "🇩🇪 Berlin", "tr": "🇩🇪 Berlin"},
        "Europe/Berlin", "+01:00"
    ),
    "kyiv": (
        {"ru": "🇺🇦 Київ", "uk": "🇺🇦 Київ", "en": "🇺🇦 Kyiv", "tr": "🇺🇦 Kiev"},
        "Europe/Kyiv", "+02:00"
    ),
    "istanbul": (
        {"ru": "🇹🇷 Стамбул", "uk": "🇹🇷 Стамбул", "en": "🇹🇷 Istanbul", "tr": "🇹🇷 İstanbul"},
        "Europe/Istanbul", "+03:00"
    ),

    # ============================================
    # ВТОРОЙ ЭКРАН (16 дополнительных городов)
    # ============================================

    # Америка
    "los_angeles": (
        {"ru": "🇺🇸 Лос-Анджелес", "uk": "🇺🇸 Лос-Анджелес", "en": "🇺🇸 Los Angeles", "tr": "🇺🇸 Los Angeles"},
        "America/Los_Angeles", "-08:00"
    ),
    "chicago": (
        {"ru": "🇺🇸 Чикаго", "uk": "🇺🇸 Чикаго", "en": "🇺🇸 Chicago", "tr": "🇺🇸 Chicago"},
        "America/Chicago", "-06:00"
    ),
    "new_york": (
        {"ru": "🇺🇸 Нью-Йорк", "uk": "🇺🇸 Нью-Йорк", "en": "🇺🇸 New York", "tr": "🇺🇸 New York"},
        "America/New_York", "-05:00"
    ),
    "toronto": (
        {"ru": "🇨🇦 Торонто", "uk": "🇨🇦 Торонто", "en": "🇨🇦 Toronto", "tr": "🇨🇦 Toronto"},
        "America/Toronto", "-05:00"
    ),
    "mexico_city": (
        {"ru": "🇲🇽 Мехико", "uk": "🇲🇽 Мехіко", "en": "🇲🇽 Mexico City", "tr": "🇲🇽 Mexico City"},
        "America/Mexico_City", "-06:00"
    ),
    "sao_paulo": (
        {"ru": "🇧🇷 Сан-Паулу", "uk": "🇧🇷 Сан-Паулу", "en": "🇧🇷 São Paulo", "tr": "🇧🇷 São Paulo"},
        "America/Sao_Paulo", "-03:00"
    ),

    # Азия
    "dubai": (
        {"ru": "🇦🇪 Дубай", "uk": "🇦🇪 Дубай", "en": "🇦🇪 Dubai", "tr": "🇦🇪 Dubai"},
        "Asia/Dubai", "+04:00"
    ),
    "almaty": (
        {"ru": "🇰🇿 Алматы", "uk": "🇰🇿 Алмати", "en": "🇰🇿 Almaty", "tr": "🇰🇿 Almatı"},
        "Asia/Almaty", "+05:00"
    ),
    "tashkent": (
        {"ru": "🇺🇿 Ташкент", "uk": "🇺🇿 Ташкент", "en": "🇺🇿 Tashkent", "tr": "🇺🇿 Taşkent"},
        "Asia/Tashkent", "+05:00"
    ),
    "delhi": (
        {"ru": "🇮🇳 Дели", "uk": "🇮🇳 Делі", "en": "🇮🇳 Delhi", "tr": "🇮🇳 Delhi"},
        "Asia/Kolkata", "+05:30"
    ),
    "bangkok": (
        {"ru": "🇹🇭 Бангкок", "uk": "🇹🇭 Бангкок", "en": "🇹🇭 Bangkok", "tr": "🇹🇭 Bangkok"},
        "Asia/Bangkok", "+07:00"
    ),
    "hanoi": (
        {"ru": "🇻🇳 Ханой", "uk": "🇻🇳 Ханой", "en": "🇻🇳 Hanoi", "tr": "🇻🇳 Hanoi"},
        "Asia/Ho_Chi_Minh", "+07:00"
    ),
    "beijing": (
        {"ru": "🇨🇳 Пекин", "uk": "🇨🇳 Пекін", "en": "🇨🇳 Beijing", "tr": "🇨🇳 Pekin"},
        "Asia/Shanghai", "+08:00"
    ),
    "tokyo": (
        {"ru": "🇯🇵 Токио", "uk": "🇯🇵 Токіо", "en": "🇯🇵 Tokyo", "tr": "🇯🇵 Tokyo"},
        "Asia/Tokyo", "+09:00"
    ),
    "seoul": (
        {"ru": "🇰🇷 Сеул", "uk": "🇰🇷 Сеул", "en": "🇰🇷 Seoul", "tr": "🇰🇷 Seul"},
        "Asia/Seoul", "+09:00"
    ),
    "sydney": (
        {"ru": "🇦🇺 Сидней", "uk": "🇦🇺 Сідней", "en": "🇦🇺 Sydney", "tr": "🇦🇺 Sidney"},
        "Australia/Sydney", "+11:00"
    ),
}


def get_city_name(city_code: str, lang: str = "ru") -> str:
    """
    Получить название города

    Args:
        city_code: код города (например, "london")
        lang: язык интерфейса (ru, uk, en, tr)

    Returns:
        Название города с флагом на выбранном языке
    """
    if city_code not in TIMEZONE_CITIES:
        unknown_city = {
            "ru": "🌍 Неизвестный город",
            "uk": "🌍 Невідоме місто",
            "en": "🌍 Unknown city",
            "tr": "🌍 Bilinmeyen şehir"
        }
        return unknown_city.get(lang, unknown_city["ru"])

    city_names = TIMEZONE_CITIES[city_code][0]
    return city_names.get(lang, city_names["ru"])


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