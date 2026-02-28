"""
Клавиатуры для настройки напоминаний и часовых поясов
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.timezones import TIMEZONE_CITIES, get_main_cities, get_extended_cities
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
            text="🇬🇧 Лондон (UTC+0)",
            callback_data="tz:london"
        ),
        InlineKeyboardButton(
            text="🇩🇪 Берлин (UTC+1)",
            callback_data="tz:berlin"
        )
    )

    # Второй ряд: Киев, Стамбул
    builder.row(
        InlineKeyboardButton(
            text="🇺🇦 Київ (UTC+2)",
            callback_data="tz:kyiv"
        ),
        InlineKeyboardButton(
            text="🇹🇷 İstanbul (UTC+3)",
            callback_data="tz:istanbul"
        )
    )

    # Кнопка "Выбрать другой город"
    builder.row(
        InlineKeyboardButton(
            text="🌍 Выбрать другой город ▼",
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
                text=TIMEZONE_CITIES[city1][0],
                callback_data=f"tz:{city1}"
            ),
            InlineKeyboardButton(
                text=TIMEZONE_CITIES[city2][0],
                callback_data=f"tz:{city2}"
            )
        )

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
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
            text="◀️ Назад",
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

    # Дни недели
    days = [
        (0, "Пн"), (1, "Вт"), (2, "Ср"), (3, "Чт"),
        (4, "Пт"), (5, "Сб"), (6, "Вс")
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
            text="📅 Все дни",
            callback_data="notif_day:all"
        ),
        InlineKeyboardButton(
            text="🗓️ Будни (Пн-Пт)",
            callback_data="notif_day:weekdays"
        )
    )

    # Кнопка "Сохранить"
    builder.row(
        InlineKeyboardButton(
            text="💾 Сохранить",
            callback_data="notif_save"
        )
    )

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
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

    # Статус напоминаний
    status_emoji = "🔔" if notifications_enabled else "🔕"
    status_text = "Включено" if notifications_enabled else "Выключено"

    builder.row(
        InlineKeyboardButton(
            text=f"{status_emoji} Напоминания: {status_text}",
            callback_data="notif_toggle"
        )
    )

    # Если напоминания включены - показываем дополнительные настройки
    if notifications_enabled:
        # Убираем секунды если есть, показываем только HH:MM
        time_display = notification_time if len(notification_time) == 5 else notification_time[:5]
        builder.row(
            InlineKeyboardButton(
                text=f"🕐 Время: {time_display}",
                callback_data="notif_change_time"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text="📅 Выбрать дни",
                callback_data="notif_change_days"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text="🌍 Изменить часовой пояс",
                callback_data="notif_change_timezone"
            )
        )

    # Кнопка "Назад в настройки"
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад в настройки",
            callback_data="back_to_settings"
        )
    )

    return builder.as_markup()


def get_quiz_word_count_keyboard(current_count: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """
    Выбор количества слов в викторине

    Args:
        current_count: текущее количество слов
        lang: язык интерфейса

    Returns:
        Клавиатура с вариантами: 10, 15, 25
    """
    builder = InlineKeyboardBuilder()

    counts = [10, 15, 25]

    for count in counts:
        emoji = "✅" if count == current_count else "⬜"
        builder.add(InlineKeyboardButton(
            text=f"{emoji} {count} слов",
            callback_data=f"quiz_count:{count}"
        ))

    builder.adjust(3)

    # Кнопка "Назад"
    builder.row(
        InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_settings"
        )
    )

    return builder.as_markup()