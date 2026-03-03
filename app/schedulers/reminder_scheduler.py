"""
Планировщик напоминаний для бота
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

    Args:
        bot: экземпляр бота
        user: пользователь из БД

    Returns:
        True если успешно отправлено, False при ошибке
    """
    lang = user.interface_language or "ru"

    # Имя пользователя
    name = user.first_name or get_text("notif_default_name", lang)

    # Выбираем случайную мотивацию
    motivation_key = random.choice(MOTIVATION_KEYS)
    motivation = get_text(motivation_key, lang)

    # Формируем прогресс
    progress_lines = []

    # Серия (если есть)
    if user.streak_days > 0:
        progress_lines.append(
            get_text("notif_progress_streak", lang, days=user.streak_days)
        )

    # Викторины
    progress_lines.append(
        get_text("notif_progress_quizzes", lang, count=user.quizzes_passed)
    )

    # Слова
    progress_lines.append(
        get_text("notif_progress_words", lang, count=user.words_learned)
    )

    # Точность
    progress_lines.append(
        get_text("notif_progress_accuracy", lang, percent=user.success_rate)
    )

    # Собираем текст
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
        # Получаем всех пользователей с включенными уведомлениями
        result = await session.execute(
            select(User).where(User.notifications_enabled == True)
        )
        users: List[User] = result.scalars().all()

        logger.debug(f"🔍 Найдено {len(users)} пользователей с включенными уведомлениями")

        for user in users:
            try:
                # Проверка 1: Есть ли timezone
                if not user.timezone:
                    logger.warning(f"⚠️ У пользователя {user.id} не настроен timezone")
                    continue

                # Конвертируем UTC в локальное время пользователя
                try:
                    user_tz = ZoneInfo(user.timezone)
                    now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
                except Exception as e:
                    logger.error(f"❌ Неверный timezone для пользователя {user.id}: {user.timezone}")
                    continue

                # Проверка 2: Сегодня рабочий день?
                current_weekday = now_local.weekday()  # 0 = Понедельник, 6 = Воскресенье
                if current_weekday not in user.notification_days:
                    logger.debug(f"⏭️ Сегодня ({current_weekday}) не день напоминания для пользователя {user.id}")
                    continue

                # Проверка 3: Уже отправляли сегодня? (ПЕРВАЯ проверка - экономим CPU)
                if user.last_notification_sent:
                    last_sent_local = user.last_notification_sent.replace(tzinfo=ZoneInfo("UTC")).astimezone(user_tz)
                    if last_sent_local.date() == now_local.date():
                        logger.debug(f"⏭️ Пользователю {user.id} уже отправлено напоминание сегодня")
                        continue

                # Проверка 4: Парсинг времени уведомления
                try:
                    if ':' not in user.notification_time:
                        logger.warning(f"⚠️ Неверный формат времени для пользователя {user.id}: {user.notification_time}")
                        continue

                    time_parts = user.notification_time.split(':')
                    if len(time_parts) != 2:
                        logger.warning(f"⚠️ Неверный формат времени для пользователя {user.id}: {user.notification_time}")
                        continue

                    notification_hour = int(time_parts[0])
                    notification_minute = int(time_parts[1])

                    # Валидация
                    if not (0 <= notification_hour <= 23 and 0 <= notification_minute <= 59):
                        logger.warning(f"⚠️ Некорректное время для пользователя {user.id}: {user.notification_time}")
                        continue

                except (ValueError, IndexError) as e:
                    logger.error(f"❌ Ошибка парсинга времени для пользователя {user.id}: {user.notification_time}")
                    continue

                # Проверка 5: Время совпадает? (диапазон ±2 минуты)
                notification_datetime = now_local.replace(
                    hour=notification_hour,
                    minute=notification_minute,
                    second=0,
                    microsecond=0
                )
                time_diff_minutes = abs((now_local - notification_datetime).total_seconds() / 60)

                if time_diff_minutes > 2:
                    continue

                logger.info(f"⏰ Отправляю напоминание пользователю {user.id} (локальное время: {now_local.strftime('%H:%M')})")

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


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Настроить и запустить планировщик задач

    Args:
        bot: экземпляр бота

    Returns:
        настроенный планировщик
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    # Запускаем проверку каждую минуту
    scheduler.add_job(
        check_and_send_notifications,
        trigger="cron",
        minute="*",  # Каждую минуту
        args=[bot],
        id="check_notifications",
        replace_existing=True
    )

    scheduler.start()
    logger.info("⏰ Планировщик напоминаний запущен")

    return scheduler