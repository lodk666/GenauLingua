"""
Обработчики для настройки напоминаний и часовых поясов
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.bot.keyboards.notifications import (
    get_timezone_main_keyboard,
    get_timezone_extended_keyboard,
    get_notification_time_keyboard,
    get_notification_days_keyboard,
    get_notifications_settings_keyboard,
)

from app.utils.timezones import get_timezone, get_utc_offset, get_city_name
from app.locales import get_text

router = Router()


# ============================================================================
# НАСТРОЙКИ НАПОМИНАНИЙ - ГЛАВНОЕ МЕНЮ
# ============================================================================

@router.callback_query(F.data == "settings:notifications")
async def show_notifications_settings(callback: CallbackQuery, session: AsyncSession):
    """Показать меню настроек напоминаний"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    # Формируем текст с текущими настройками
    status = get_text("notif_status_on", lang) if user.notifications_enabled else get_text("notif_status_off", lang)
    timezone_text = f"{user.timezone}" if user.timezone else "—"

    text = f"{get_text('notif_title', lang)}\n\n{get_text('notif_status', lang, status=status)}\n"

    if user.notifications_enabled:
        # Показываем детали только если напоминания включены
        days_map = {
            0: get_text("day_mon", lang), 1: get_text("day_tue", lang),
            2: get_text("day_wed", lang), 3: get_text("day_thu", lang),
            4: get_text("day_fri", lang), 5: get_text("day_sat", lang),
            6: get_text("day_sun", lang)
        }
        days_str = ", ".join([days_map[d] for d in sorted(user.notification_days)])

        # Убираем секунды если есть, показываем только HH:MM
        time_display = user.notification_time if len(user.notification_time) == 5 else user.notification_time[:5]

        text += (
            f"{get_text('notif_time', lang, time=time_display)}\n"
            f"{get_text('notif_days', lang, days=days_str)}\n"
            f"{get_text('notif_timezone', lang, timezone=timezone_text)}\n\n"
            f"{get_text('notif_hint', lang)}"
        )
    else:
        text += f"\n{get_text('notif_hint_off', lang)}"

    keyboard = get_notifications_settings_keyboard(
        notifications_enabled=user.notifications_enabled,
        notification_time=user.notification_time,
        lang=lang
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


# ============================================================================
# ВКЛЮЧИТЬ/ВЫКЛЮЧИТЬ НАПОМИНАНИЯ
# ============================================================================

@router.callback_query(F.data == "notif_toggle")
async def toggle_notifications(callback: CallbackQuery, session: AsyncSession):
    """Включить/выключить напоминания"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    if user.notifications_enabled:
        # Выключаем напоминания
        user.notifications_enabled = False
        await session.commit()
        await callback.answer(get_text("notif_toggle_off", lang), show_alert=False)
    else:
        # Включаем напоминания - сначала нужно настроить timezone
        if not user.timezone or user.timezone == "Europe/Berlin":
            # Если timezone не настроен - предлагаем выбрать
            await callback.answer()
            text = f"{get_text('notif_timezone_title', lang)}\n\n{get_text('notif_timezone_prompt', lang)}"
            keyboard = get_timezone_main_keyboard(lang)
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            return
        else:
            # Timezone уже настроен - просто включаем
            user.notifications_enabled = True
            await session.commit()
            await callback.answer(get_text("notif_toggle_on", lang), show_alert=False)

    # Обновляем меню настроек
    await show_notifications_settings(callback, session)


# ============================================================================
# ВЫБОР ЧАСОВОГО ПОЯСА
# ============================================================================

@router.callback_query(F.data == "notif_change_timezone")
async def change_timezone_start(callback: CallbackQuery, session: AsyncSession):
    """Начать изменение часового пояса"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"{get_text('notif_timezone_title', lang)}\n\n"
        f"{get_text('notif_timezone_current', lang, timezone=user.timezone)}\n\n"
        f"{get_text('notif_timezone_prompt', lang)}"
    )

    keyboard = get_timezone_main_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "tz:more_cities")
async def show_extended_cities(callback: CallbackQuery, session: AsyncSession):
    """Показать расширенный список городов"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = get_text('notif_timezone_title', lang)

    keyboard = get_timezone_extended_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "tz:back_to_main")
async def back_to_main_timezones(callback: CallbackQuery, session: AsyncSession):
    """Вернуться к основным 4 городам"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = f"{get_text('notif_timezone_title', lang)}\n\n{get_text('notif_timezone_prompt', lang)}"

    keyboard = get_timezone_main_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("tz:"))
async def set_timezone(callback: CallbackQuery, session: AsyncSession):
    """Установить часовой пояс"""
    # Извлекаем код города (например, "london" из "tz:london")
    city_code = callback.data.split(":")[1]

    # Игнорируем служебные команды
    if city_code in ["more_cities", "back_to_main"]:
        return

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    # Получаем данные о городе
    city_name = get_city_name(city_code, lang)
    timezone = get_timezone(city_code)
    utc_offset = get_utc_offset(city_code)

    # Сохраняем в базу
    user.timezone = timezone
    user.utc_offset = utc_offset

    # Если это первая настройка - включаем напоминания
    if not user.notifications_enabled:
        user.notifications_enabled = True

    await session.commit()

    await callback.answer(get_text("notif_timezone_set", lang, city=city_name), show_alert=False)

    # Возвращаемся к настройкам напоминаний
    await show_notifications_settings(callback, session)


# ============================================================================
# ИЗМЕНЕНИЕ ВРЕМЕНИ НАПОМИНАНИЯ
# ============================================================================

@router.callback_query(F.data == "notif_change_time")
async def change_notification_time(callback: CallbackQuery, session: AsyncSession):
    """Показать выбор времени"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    time_display = user.notification_time if len(user.notification_time) == 5 else user.notification_time[:5]

    text = (
        f"{get_text('notif_time_title', lang)}\n\n"
        f"{get_text('notif_time_current', lang, time=time_display)}\n"
        f"{get_text('notif_time_timezone', lang, timezone=user.timezone)}\n\n"
        f"{get_text('notif_time_hint', lang)}"
    )

    keyboard = get_notification_time_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("notif_time:"))
async def set_notification_time(callback: CallbackQuery, session: AsyncSession):
    """Установить время напоминания"""
    time_str = callback.data.split(":", 1)[1]  # "14:00" или "14"

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    # Нормализация формата времени
    if len(time_str) <= 2:  # только часы ("14")
        time_str = f"{time_str.zfill(2)}:00"  # → "14:00"
    elif len(time_str) == 5 and ':' in time_str:  # уже HH:MM
        # Проверяем валидность
        try:
            h, m = time_str.split(':')
            hour = int(h)
            minute = int(m)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Неверное время")
            time_str = f"{hour:02d}:{minute:02d}"  # Форматируем 09:05 вместо 9:5
        except:
            time_str = "20:00"  # Fallback на дефолт
    else:
        time_str = "20:00"  # Странный формат → дефолт

    user.notification_time = time_str
    await session.commit()

    await callback.answer(get_text("notif_time_set", lang, time=time_str), show_alert=False)

    # Возвращаемся к настройкам напоминаний
    await show_notifications_settings(callback, session)

# ============================================================================
# ИЗМЕНЕНИЕ ДНЕЙ НАПОМИНАНИЯ
# ============================================================================

@router.callback_query(F.data == "notif_change_days")
async def change_notification_days(callback: CallbackQuery, session: AsyncSession):
    """Показать выбор дней"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = get_text("notif_days_title", lang) + "\n\n" + get_text("notif_days_hint", lang)

    keyboard = get_notification_days_keyboard(
        selected_days=user.notification_days,
        lang=lang
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("notif_day:"))
async def toggle_notification_day(callback: CallbackQuery, session: AsyncSession):
    """Переключить день недели"""
    day_param = callback.data.split(":")[1]

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"
    current_days = list(user.notification_days) if user.notification_days else []

    if day_param == "all":
        # Выбрать все дни
        new_days = [0, 1, 2, 3, 4, 5, 6]
        user.notification_days = new_days
        await session.commit()
        await callback.answer(get_text("notif_days_all_selected", lang), show_alert=False)

    elif day_param == "weekdays":
        # Выбрать только будни (Пн-Пт)
        new_days = [0, 1, 2, 3, 4]
        user.notification_days = new_days
        await session.commit()
        await callback.answer(get_text("notif_days_weekdays_selected", lang), show_alert=False)

    else:
        # Переключить конкретный день
        day_num = int(day_param)

        if day_num in current_days:
            current_days.remove(day_num)
        else:
            current_days.append(day_num)

        # Сохраняем даже если пусто (пользователь сможет выбрать позже)
        user.notification_days = sorted(current_days)
        await session.commit()
        await callback.answer()

    # Обновляем клавиатуру
    text = get_text("notif_days_title", lang) + "\n\n" + get_text("notif_days_hint", lang)

    keyboard = get_notification_days_keyboard(
        selected_days=user.notification_days,
        lang=lang
    )

    try:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        # Игнорируем ошибку если сообщение не изменилось
        pass


@router.callback_query(F.data == "notif_save")
async def save_notification_days(callback: CallbackQuery, session: AsyncSession):
    """Сохранить выбранные дни и вернуться"""
    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    # Проверяем что выбран хотя бы 1 день
    if not user.notification_days or len(user.notification_days) == 0:
        await callback.answer(get_text("notif_days_none", lang), show_alert=True)
        return

    await callback.answer(get_text("notif_days_saved", lang), show_alert=False)

    # Возвращаемся к настройкам напоминаний
    await show_notifications_settings(callback, session)
