"""
Главный файл запуска бота GenauLingua
Обновлённая версия с модульной структурой
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings
from app.bot.handlers.start import router as start_router
from app.bot.handlers.quiz import router as quiz_router  # ← НОВЫЙ МОДУЛЬ!
from app.bot.handlers.admin import router as admin_router
from app.database.session import AsyncSessionLocal

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""

    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(start_router)  # Стартовое меню
    dp.include_router(quiz_router)  # Модуль quiz (game + settings + stats + help)
    dp.include_router(admin_router)  # Админка

    # Middleware для передачи сессии БД в хэндлеры
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with AsyncSessionLocal() as session:
            data['session'] = session
            return await handler(event, data)

    # Запуск бота
    logger.info("🚀 GenauLingua Bot запущен!")
    logger.info("📦 Модульная структура загружена:")
    logger.info("   ✅ quiz/game.py - Игровая логика")
    logger.info("   ✅ quiz/settings.py - Настройки")
    logger.info("   ✅ quiz/stats.py - Статистика")
    logger.info("   ✅ quiz/help.py - Помощь")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())