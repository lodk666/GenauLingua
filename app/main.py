"""
Главный файл запуска бота GenauLingua
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.bot.handlers.start import router as start_router
from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.reminders import router as reminders_router

# РЕЙТИНГИ
from app.bot.handlers.leaderboard.monthly import router as monthly_router
from app.bot.handlers.leaderboard.alltime import router as alltime_router
from app.bot.handlers.leaderboard.personal import router as personal_router
from app.bot.handlers.leaderboard.leaderboard_table import router as table_router

# КВИЗЫ ПО ОТДЕЛЬНОСТИ (НЕ ЧЕРЕЗ quiz_router!)
from app.bot.handlers.quiz.game import router as game_router
from app.bot.handlers.quiz.settings import router as settings_router
from app.bot.handlers.quiz.stats import router as stats_router
from app.bot.handlers.quiz.help import router as help_router

from app.database.session import AsyncSessionLocal
from app.core.logging import setup_logging
from app.core.sentry import setup_sentry
from app.schedulers import setup_scheduler

logger = logging.getLogger(__name__)


async def main():
    setup_logging()
    setup_sentry()

    logger.info("🚀 Starting GenauLingua Bot...")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())

    @dp.errors()
    async def global_error_handler(event: ErrorEvent):
        logger.exception("Unhandled error: %s", event.exception)
        return True

    # ВАЖНО: ПОРЯДОК РЕГИСТРАЦИИ!
    # Рейтинги ПЕРВЫМИ (чтобы перехватить show_my_rating)
    dp.include_router(monthly_router)
    dp.include_router(alltime_router)
    dp.include_router(personal_router)
    dp.include_router(table_router)

    # Потом всё остальное
    dp.include_router(start_router)
    dp.include_router(game_router)
    dp.include_router(settings_router)
    dp.include_router(stats_router)
    dp.include_router(help_router)
    dp.include_router(reminders_router)
    dp.include_router(admin_router)

    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)

    logger.info("📦 Routers loaded:")
    logger.info("   ✅ leaderboard/monthly.py")
    logger.info("   ✅ leaderboard/alltime.py")
    logger.info("   ✅ leaderboard/personal.py")
    logger.info("   ✅ leaderboard/leaderboard_table.py")
    logger.info("   ✅ start.py")
    logger.info("   ✅ quiz/game.py")
    logger.info("   ✅ quiz/settings.py")
    logger.info("   ✅ quiz/stats.py")
    logger.info("   ✅ quiz/help.py")
    logger.info("   ✅ reminders.py")
    logger.info("   ✅ admin.py")

    scheduler = setup_scheduler(bot)
    logger.info("⏰ Notification scheduler started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())