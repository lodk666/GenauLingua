"""
Планировщик для автоматической отправки напоминаний
"""

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def send_notification_to_user(bot: Bot, user: User):
    """
    Отправить напоминание конкретному пользователю

    Args:
        bot: экземпляр бота
        user: пользователь из БД
    """
    lang = user.interface_language or "ru"

    # Текст напоминания
    streak_emoji = "🔥" if user.streak_days > 0 else "📚"

    if lang == "ru":
        text = (
            f"{streak_emoji} <b>Время заниматься!</b>\n\n"
            f"{'🔥 Стрик: ' + str(user.streak_days) + ' дней подряд' if user.streak_days > 0 else ''}\n"
            f"📊 Выучено слов: {user.words_learned}\n\n"
            f"💪 Не прерывай свою серию!"
        )
        button_text = "📚 Начать викторину"
    elif lang == "uk":
        text = (
            f"{streak_emoji} <b>Час займатися!</b>\n\n"
            f"{'🔥 Стрік: ' + str(user.streak_days) + ' днів поспіль' if user.streak_days > 0 else ''}\n"
            f"📊 Вивчено слів: {user.words_learned}\n\n"
            f"💪 Не перериваю свою серію!"
        )
        button_text = "📚 Почати вікторину"
    elif lang == "en":
        text = (
            f"{streak_emoji} <b>Time to practice!</b>\n\n"
            f"{'🔥 Streak: ' + str(user.streak_days) + ' days' if user.streak_days > 0 else ''}\n"
            f"📊 Words learned: {user.words_learned}\n\n"
            f"💪 Keep your streak going!"
        )
        button_text = "📚 Start quiz"
    elif lang == "tr":
        text = (
            f"{streak_emoji} <b>Çalışma zamanı!</b>\n\n"
            f"{'🔥 Seri: ' + str(user.streak_days) + ' gün' if user.streak_days > 0 else ''}\n"
            f"📊 Öğrenilen kelimeler: {user.words_learned}\n\n"
            f"💪 Serini kırma!"
        )
        button_text = "📚 Quiz başlat"
    else:
        text = (
            f"{streak_emoji} <b>Время заниматься!</b>\n\n"
            f"{'🔥 Стрик: ' + str(user.streak_days) + ' дней' if user.streak_days > 0 else ''}\n"
            f"📊 Выучено слов: {user.words_learned}\n\n"
            f"💪 Не прерывай свою серию!"
        )
        button_text = "📚 Начать викторину"

    # Клавиатура
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=button_text,
                callback_data="start_quiz"
            )],
            [InlineKeyboardButton(
                text="🔕 Отключить напоминания" if lang == "ru" else "🔕 Вимкнути нагадування" if lang == "uk" else "🔕 Disable reminders" if lang == "en" else "🔕 Hatırlatıcıları kapat",
                callback_data="notif_toggle"
            )]
        ]
    )

    try:
        await bot.send_message(
            chat_id=user.id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        logger.info(f"✅ Напоминание отправлено пользователю {user.id} ({user.username})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминания пользователю {user.id}: {e}")
        return False


async def check_and_send_notifications(bot: Bot):
    """
    Проверить всех пользователей и отправить напоминания тем, кому пора

    Эта функция вызывается каждую минуту планировщиком

    Args:
        bot: экземпляр бота
    """
    logger.debug("🔍 Checking for notifications to send...")

    async with AsyncSessionLocal() as session:
        # Получаем текущее UTC время
        now_utc = datetime.utcnow()

        # Получаем всех пользователей с включенными напоминаниями
        stmt = select(User).where(User.notifications_enabled == True)
        result = await session.execute(stmt)
        users = result.scalars().all()

        logger.debug(f"📊 Найдено {len(users)} пользователей с включенными напоминаниями")

        sent_count = 0

        for user in users:
            try:
                # Пропускаем если нет timezone
                if not user.timezone:
                    continue

                # Получаем локальное время пользователя
                try:
                    user_tz = ZoneInfo(user.timezone)
                    now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
                except Exception as e:
                    logger.error(f"❌ Неверный timezone для пользователя {user.id}: {user.timezone}, ошибка: {e}")
                    continue

                # Проверяем день недели (0=понедельник, 6=воскресенье)
                current_weekday = now_local.weekday()

                # Если сегодня не входит в выбранные дни - пропускаем
                if current_weekday not in user.notification_days:
                    continue

                # Проверяем время
                try:
                    # Парсим время из формата "HH:MM"
                    if ':' not in user.notification_time:
                        logger.warning(f"⚠️ Неверный формат времени для пользователя {user.id}: {user.notification_time}")
                        continue

                    time_parts = user.notification_time.split(':')
                    if len(time_parts) != 2:
                        logger.warning(f"⚠️ Неверный формат времени для пользователя {user.id}: {user.notification_time}")
                        continue

                    notification_hour = int(time_parts[0])
                    notification_minute = int(time_parts[1])
                except (ValueError, IndexError) as e:
                    logger.error(f"❌ Ошибка парсинга времени для пользователя {user.id}: {user.notification_time}, ошибка: {e}")
                    continue

                current_hour = now_local.hour
                current_minute = now_local.minute

                # Если время НЕ совпадает - пропускаем
                if current_hour != notification_hour or current_minute != notification_minute:
                    continue

                # Проверяем, не отправляли ли уже сегодня
                if user.last_notification_sent:
                    last_sent_local = user.last_notification_sent.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)

                    # Если уже отправляли сегодня - пропускаем
                    if last_sent_local.date() == now_local.date():
                        logger.debug(f"⏭️ Пользователю {user.id} уже отправлено напоминание сегодня")
                        continue

                # Отправляем напоминание
                success = await send_notification_to_user(bot, user)

                if success:
                    # Обновляем время последней отправки
                    user.last_notification_sent = now_utc
                    await session.commit()
                    sent_count += 1

            except Exception as e:
                logger.error(f"❌ Ошибка обработки пользователя {user.id}: {e}")
                continue

        if sent_count > 0:
            logger.info(f"✅ Отправлено {sent_count} напоминаний")
        else:
            logger.debug("📭 Нет напоминаний для отправки в эту минуту")


def setup_scheduler(bot: Bot):
    """
    Настроить и запустить планировщик

    Args:
        bot: экземпляр бота

    Returns:
        Экземпляр планировщика
    """
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    scheduler = AsyncIOScheduler(timezone="UTC")

    # Запускаем проверку каждую минуту
    scheduler.add_job(
        check_and_send_notifications,
        trigger="cron",
        minute="*",  # каждую минуту
        args=[bot],
        id="check_notifications",
        replace_existing=True
    )

    scheduler.start()
    logger.info("⏰ Планировщик напоминаний запущен (проверка каждую минуту)")

    return scheduler