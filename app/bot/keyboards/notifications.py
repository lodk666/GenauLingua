"""
Клавиатуры для настройки напоминаний и часовых поясов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.timezones import TIMEZONE_CITIES, get_main_cities, get_extended_cities, get_city_name, get_utc_offset
from app.locales import get_text


def get_timezone_main_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Основные 4 города для выбора часового пояса

    Args:
        lang: язык интерфейса

    Returns:
        Клавиатура с 4 основными городами + кнопка "Другой город"
    """
    builder = InlineKeyboardBuilder()

    # Первый ряд: Лондон, Берлин
    builder.row(
        InlineKeyboardButton(
            text=f"{get_city_name('london', lang)} (UTC{get_utc_offset('london')})",
            callback_data="tz:london"
        ),
        InlineKeyboardButton(
            text=f"{get_city_name('berlin', lang)} (UTC{get_utc_offset('berlin')})",
            callback_data="tz:berlin"
        )
    )

    # Второй ряд: Киев, Стамбул
    builder.row(
        InlineKeyboardButton(
            text=f"{get_city_name('kyiv', lang)} (UTC{get_utc_offset('kyiv')})",
            callback_data="tz:kyiv"
        ),
        InlineKeyboardButton(
            text=f"{get_city_name('istanbul', lang)} (UTC{get_utc_offset('istanbul')})",
            callback_data="tz:istanbul"
        )
    )

    # Кнопка "Выбрать другой город"
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_timezone_more", lang),
            callback_data="tz:more_cities"
        )
    )

    return builder.as_markup()


def get_timezone_extended_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Расширенный список 16 городов (в 2 колонки)

    Args:
        lang: язык интерфейса

    Returns:
        Клавиатура с 16 дополнительными городами
    """
    builder = InlineKeyboardBuilder()

    # Список пар городов для отображения в 2 колонки
    city_pairs = [
        ("los_angeles", "chicago"),
        ("new_york", "toronto"),
        ("mexico_city", "sao_paulo"),
        ("dubai", "almaty"),
        ("tashkent", "delhi"),
        ("bangkok", "hanoi"),
        ("beijing", "tokyo"),
        ("seoul", "sydney"),
    ]

    for city1, city2 in city_pairs:
        builder.row(
            InlineKeyboardButton(
                text=get_city_name(city1, lang),
                callback_data=f"tz:{city1}"
            ),
            InlineKeyboardButton(
                text=get_city_name(city2, lang),
                callback_data=f"tz:{city2}"
            )
        )

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_timezone_back", lang),
            callback_data="tz:back_to_main"
        )
    )

    return builder.as_markup()


def get_notification_time_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Выбор времени для напоминания

    Args:
        lang: язык интерфейса

    Returns:
        Клавиатура с временными слотами (по 3 кнопки в ряд)
    """
    builder = InlineKeyboardBuilder()

    # Популярные времена для напоминаний
    times = [
        "08:00", "09:00", "10:00",
        "12:00", "14:00", "16:00",
        "18:00", "19:00", "20:00",
        "21:00", "22:00", "23:00"
    ]

    # Добавляем кнопки по 3 в ряд
    for i in range(0, len(times), 3):
        row_buttons = []
        for j in range(3):
            if i + j < len(times):
                time = times[i + j]
                row_buttons.append(
                    InlineKeyboardButton(
                        text=time,
                        callback_data=f"notif_time:{time}"
                    )
                )
        builder.row(*row_buttons)

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_timezone_back", lang),
            callback_data="settings:notifications"
        )
    )

    return builder.as_markup()


def get_notification_days_keyboard(selected_days: list[int], lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Выбор дней недели для напоминаний

    Args:
        selected_days: список выбранных дней (0=пн, 6=вс)
        lang: язык интерфейса

    Returns:
        Клавиатура с днями недели (можно выбрать несколько)
    """
    builder = InlineKeyboardBuilder()

    # Дни недели с локализацией
    days = [
        (0, get_text("day_mon", lang)), (1, get_text("day_tue", lang)),
        (2, get_text("day_wed", lang)), (3, get_text("day_thu", lang)),
        (4, get_text("day_fri", lang)), (5, get_text("day_sat", lang)),
        (6, get_text("day_sun", lang))
    ]

    # Первый ряд: Пн-Чт
    for day_num, day_name in days[:4]:
        emoji = "✅" if day_num in selected_days else "❌"
        builder.add(InlineKeyboardButton(
            text=f"{emoji} {day_name}",
            callback_data=f"notif_day:{day_num}"
        ))
    builder.adjust(4)

    # Второй ряд: Пт-Вс
    for day_num, day_name in days[4:]:
        emoji = "✅" if day_num in selected_days else "❌"
        builder.add(InlineKeyboardButton(
            text=f"{emoji} {day_name}",
            callback_data=f"notif_day:{day_num}"
        ))
    builder.adjust(3)

    # Быстрые кнопки
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_days_all", lang),
            callback_data="notif_day:all"
        ),
        InlineKeyboardButton(
            text=get_text("notif_days_weekdays", lang),
            callback_data="notif_day:weekdays"
        )
    )

    # Кнопка "Сохранить"
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_days_save", lang),
            callback_data="notif_save"
        )
    )

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_timezone_back", lang),
            callback_data="settings:notifications"
        )
    )

    return builder.as_markup()


def get_notifications_settings_keyboard(
        notifications_enabled: bool,
        notification_time: str,
        lang: str = "ru"
) -> InlineKeyboardMarkup:
    """
    Главное меню настроек напоминаний

    Args:
        notifications_enabled: включены ли напоминания
        notification_time: текущее время напоминания
        lang: язык интерфейса

    Returns:
        Клавиатура с настройками напоминаний
    """
    builder = InlineKeyboardBuilder()

    # Статус напоминаний с локализацией
    toggle_text = get_text("notif_btn_toggle_on", lang) if notifications_enabled else get_text("notif_btn_toggle_off",
                                                                                               lang)

    builder.row(
        InlineKeyboardButton(
            text=toggle_text,
            callback_data="notif_toggle"
        )
    )

    # Если напоминания включены - показываем дополнительные настройки
    if notifications_enabled:
        # Убираем секунды если есть, показываем только HH:MM
        time_display = notification_time if len(notification_time) == 5 else notification_time[:5]
        builder.row(
            InlineKeyboardButton(
                text=get_text("notif_btn_time", lang, time=time_display),
                callback_data="notif_change_time"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=get_text("notif_btn_days", lang),
                callback_data="notif_change_days"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=get_text("notif_btn_timezone", lang),
                callback_data="notif_change_timezone"
            )
        )

    # Кнопка "Назад в настройки"
    builder.row(
        InlineKeyboardButton(
            text=get_text("notif_btn_back", lang),
            callback_data="back_to_settings"
        )
    )

    return builder.as_markup()