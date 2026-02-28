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
    get_quiz_word_count_keyboard,
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
    status = "🔔 Включены" if user.notifications_enabled else "🔕 Выключены"
    timezone_text = f"{user.timezone}" if user.timezone else "Не установлен"

    text = (
        f"🔔 <b>Настройки напоминаний</b>\n\n"
        f"Статус: {status}\n"
    )

    if user.notifications_enabled:
        # Показываем детали только если напоминания включены
        days_map = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
        days_str = ", ".join([days_map[d] for d in sorted(user.notification_days)])

        # Убираем секунды если есть, показываем только HH:MM
        time_display = user.notification_time if len(user.notification_time) == 5 else user.notification_time[:5]

        text += (
            f"Время: {time_display}\n"
            f"Дни: {days_str}\n"
            f"Часовой пояс: {timezone_text}\n\n"
            f"💡 Напоминания будут приходить в указанное время по вашему часовому поясу."
        )
    else:
        text += (
            f"\n💡 Включите напоминания, чтобы не забывать заниматься каждый день!"
        )

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
        await callback.answer("🔕 Напоминания выключены", show_alert=False)
    else:
        # Включаем напоминания - сначала нужно настроить timezone
        if not user.timezone or user.timezone == "Europe/Berlin":
            # Если timezone не настроен - предлагаем выбрать
            await callback.answer()
            text = (
                f"🌍 <b>Выберите ваш часовой пояс</b>\n\n"
                f"Это нужно для того, чтобы напоминания приходили в правильное время."
            )
            keyboard = get_timezone_main_keyboard(lang)
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            return
        else:
            # Timezone уже настроен - просто включаем
            user.notifications_enabled = True
            await session.commit()
            await callback.answer("🔔 Напоминания включены!", show_alert=False)

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
        f"🌍 <b>Выберите ваш часовой пояс</b>\n\n"
        f"Текущий: {user.timezone}\n\n"
        f"Выберите город в вашем часовом поясе:"
    )

    keyboard = get_timezone_main_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "tz:more_cities")
async def show_extended_cities(callback: CallbackQuery, session: AsyncSession):
    """Показать расширенный список городов"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = f"🌍 <b>Выберите ваш город:</b>"

    keyboard = get_timezone_extended_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "tz:back_to_main")
async def back_to_main_timezones(callback: CallbackQuery, session: AsyncSession):
    """Вернуться к основным 4 городам"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"🌍 <b>Выберите ваш часовой пояс</b>\n\n"
        f"Выберите город в вашем часовом поясе:"
    )

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

    await callback.answer(f"✅ Часовой пояс установлен: {city_name}", show_alert=False)

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

    text = (
        f"🕐 <b>Выберите время напоминания</b>\n\n"
        f"Текущее время: {user.notification_time}\n"
        f"Часовой пояс: {user.timezone}\n\n"
        f"Напоминание будет приходить каждый день в выбранное время."
    )

    keyboard = get_notification_time_keyboard(lang)
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("notif_time:"))
async def set_notification_time(callback: CallbackQuery, session: AsyncSession):
    """Установить время напоминания"""
    time_str = callback.data.split(":", 1)[1]  # Берем всё после первого ':'

    # Убеждаемся что формат HH:MM (добавляем :00 если нет секунд)
    if ':' not in time_str:
        time_str = f"{time_str}:00"
    elif len(time_str) == 2:  # если только "14"
        time_str = f"{time_str}:00"

    user = await session.get(User, callback.from_user.id)
    user.notification_time = time_str
    await session.commit()

    await callback.answer(f"✅ Время установлено: {time_str}", show_alert=False)

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

    text = (
        f"📅 <b>Выберите дни для напоминаний</b>\n\n"
        f"Нажмите на день, чтобы включить/выключить его.\n"
        f"✅ Зелёная галочка - день включен\n"
        f"❌ Красный крестик - день выключен\n\n"
        f"Когда закончите - нажмите 'Сохранить'."
    )

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
        await callback.answer("✅ Выбраны все дни", show_alert=False)

    elif day_param == "weekdays":
        # Выбрать только будни (Пн-Пт)
        new_days = [0, 1, 2, 3, 4]
        user.notification_days = new_days
        await session.commit()
        await callback.answer("✅ Выбраны будни (Пн-Пт)", show_alert=False)

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
    text = (
        f"📅 <b>Выберите дни для напоминаний</b>\n\n"
        f"Нажмите на день, чтобы включить/выключить его.\n"
        f"✅ Зелёная галочка - день включен\n"
        f"❌ Красный крестик - день выключен\n\n"
        f"Когда закончите - нажмите 'Сохранить'."
    )

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

    # Проверяем что выбран хотя бы 1 день
    if not user.notification_days or len(user.notification_days) == 0:
        await callback.answer("⚠️ Выберите хотя бы один день для напоминаний!", show_alert=True)
        return

    await callback.answer("✅ Дни сохранены!", show_alert=False)

    # Возвращаемся к настройкам напоминаний
    await show_notifications_settings(callback, session)


# ============================================================================
# НАСТРОЙКА КОЛИЧЕСТВА СЛОВ В ВИКТОРИНЕ
# ============================================================================

@router.callback_query(F.data == "settings:quiz_count")
async def change_quiz_word_count(callback: CallbackQuery, session: AsyncSession):
    """Показать выбор количества слов"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    text = (
        f"📊 <b>Количество слов в викторине</b>\n\n"
        f"Текущее: {user.quiz_word_count} слов\n\n"
        f"Выберите удобное для вас количество:"
    )

    keyboard = get_quiz_word_count_keyboard(
        current_count=user.quiz_word_count,
        lang=lang
    )

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("quiz_count:"))
async def set_quiz_word_count(callback: CallbackQuery, session: AsyncSession):
    """Установить количество слов"""
    count = int(callback.data.split(":")[1])

    user = await session.get(User, callback.from_user.id)
    user.quiz_word_count = count
    await session.commit()

    await callback.answer(f"✅ Установлено: {count} слов", show_alert=False)

    # Возвращаемся к главным настройкам
    # (предполагается что есть обработчик back_to_settings)
    from app.bot.handlers.quiz.settings import show_settings_callback
    await show_settings_callback(callback, session)