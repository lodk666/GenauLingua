"""
Планировщик напоминаний и сезонов для бота
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List
import random

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.database.models import User
from app.locales import get_text

logger = logging.getLogger(__name__)


# Мотивационные сообщения (ключи локализации)
MOTIVATION_KEYS = [
    "notif_motivation_1",
    "notif_motivation_2",
    "notif_motivation_3",
    "notif_motivation_4",
    "notif_motivation_5",
    "notif_motivation_6"
]


async def send_notification_to_user(bot: Bot, user: User) -> bool:
    """
    Отправить напоминание конкретному пользователю
    """
    lang = user.interface_language or "ru"
    name = user.first_name or get_text("notif_default_name", lang)
    motivation_key = random.choice(MOTIVATION_KEYS)
    motivation = get_text(motivation_key, lang)

    progress_lines = []
    if user.streak_days > 0:
        progress_lines.append(
            get_text("notif_progress_streak", lang, days=user.streak_days)
        )
    progress_lines.append(
        get_text("notif_progress_quizzes", lang, count=user.quizzes_passed)
    )
    progress_lines.append(
        get_text("notif_progress_words", lang, count=user.words_learned)
    )
    progress_lines.append(
        get_text("notif_progress_accuracy", lang, percent=user.success_rate)
    )

    text = get_text("notif_message_greeting", lang, name=name) + "\n\n"
    text += get_text("notif_message_progress_title", lang) + "\n"
    text += "\n".join(progress_lines) + "\n\n"
    text += f"💡 {motivation}\n\n"
    text += get_text("notif_message_cta", lang)

    try:
        await bot.send_message(
            chat_id=user.id,
            text=text,
            parse_mode="HTML"
        )
        logger.info(f"✅ Напоминание отправлено пользователю {user.id} ({user.username})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминания пользователю {user.id}: {e}")
        return False


async def check_and_send_notifications(bot: Bot):
    """
    Проверить и отправить напоминания пользователям
    """
    from app.database.session import AsyncSessionLocal

    now_utc = datetime.utcnow()
    sent_count = 0

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.notifications_enabled == True)
        )
        users: List[User] = result.scalars().all()

        logger.debug(f"🔍 Найдено {len(users)} пользователей с включенными уведомлениями")

        for user in users:
            try:
                if not user.timezone:
                    continue

                try:
                    user_tz = ZoneInfo(user.timezone)
                    now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
                except Exception:
                    logger.error(f"❌ Неверный timezone для пользователя {user.id}: {user.timezone}")
                    continue

                current_weekday = now_local.weekday()
                if current_weekday not in user.notification_days:
                    continue

                if user.last_notification_sent:
                    last_sent_local = user.last_notification_sent.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
                    if last_sent_local.date() == now_local.date():
                        continue

                try:
                    if ':' not in user.notification_time:
                        continue
                    time_parts = user.notification_time.split(':')
                    if len(time_parts) != 2:
                        continue
                    notification_hour = int(time_parts[0])
                    notification_minute = int(time_parts[1])
                    if not (0 <= notification_hour <= 23 and 0 <= notification_minute <= 59):
                        continue
                except (ValueError, IndexError):
                    continue

                notification_datetime = now_local.replace(
                    hour=notification_hour,
                    minute=notification_minute,
                    second=0,
                    microsecond=0
                )
                time_diff_minutes = abs((now_local - notification_datetime).total_seconds() / 60)

                if time_diff_minutes > 2:
                    continue

                logger.info(f"⏰ Отправляю напоминание пользователю {user.id}")

                success = await send_notification_to_user(bot, user)

                if success:
                    user.last_notification_sent = now_utc
                    await session.commit()
                    sent_count += 1

            except Exception as e:
                logger.error(f"❌ Ошибка обработки пользователя {user.id}: {e}")
                continue

    if sent_count > 0:
        logger.info(f"✅ Отправлено {sent_count} напоминаний")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Настроить и запустить планировщик задач
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    # ═══════════════ НАПОМИНАНИЯ ═══════════════
    # Каждую минуту — проверка и отправка напоминаний
    scheduler.add_job(
        check_and_send_notifications,
        trigger="cron",
        minute="*",
        args=[bot],
        id="check_notifications",
        replace_existing=True
    )

    # ═══════════════ СЕЗОНЫ РЕЙТИНГА ═══════════════
    from app.schedulers.season_scheduler import (
        finalize_and_create_new_season,
        hourly_season_check
    )

    # 1 числа каждого месяца в 00:05 UTC — завершение старого + создание нового
    scheduler.add_job(
        finalize_and_create_new_season,
        trigger="cron",
        day=1,
        hour=0,
        minute=5,
        id="finalize_season",
        replace_existing=True
    )

    # Каждый час — страховочная проверка (если бот был выключен 1 числа)
    scheduler.add_job(
        hourly_season_check,
        trigger="cron",
        minute=30,  # каждый час в :30
        id="hourly_season_check",
        replace_existing=True
    )

    scheduler.start()
    logger.info("⏰ Планировщик запущен: напоминания + сезоны рейтинга")

    return scheduler