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
from app.bot.handlers.quiz import router as quiz_router
from app.bot.handlers.admin import router as admin_router
from app.bot.handlers.reminders import router as reminders_router
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

    # ✅ Global error handler (aiogram v3)
    @dp.errors()
    async def global_error_handler(event: ErrorEvent):
        logger.exception("Unhandled error: %s", event.exception)
        return True

    # Routers
    dp.include_router(start_router)
    dp.include_router(quiz_router)
    dp.include_router(reminders_router)
    dp.include_router(admin_router)

    # ✅ DB session middleware
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)

    logger.info("📦 Routers loaded:")
    logger.info("   ✅ quiz/game.py")
    logger.info("   ✅ quiz/settings.py")
    logger.info("   ✅ quiz/stats.py")
    logger.info("   ✅ quiz/help.py")
    logger.info("   ✅ reminder_scheduler.py")

    # Запускаем планировщик напоминаний
    scheduler = setup_scheduler(bot)
    logger.info("⏰ Notification scheduler started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())