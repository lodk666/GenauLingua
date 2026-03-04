"""
Регистрация всех роутеров бота
"""

from aiogram import Dispatcher

# Основные хэндлеры из handlers/
from app.bot.handlers import admin, reminders, start

# Квизы из handlers/quiz/
from app.bot.handlers.quiz import game, help, settings, stats

# Рейтинги из handlers/leaderboard/
from app.bot.handlers.leaderboard import monthly, alltime, personal


def setup_handlers(dp: Dispatcher):
    """Регистрация всех хэндлеров"""

    # Основные хэндлеры
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(reminders.router)

    # Квизы
    dp.include_router(game.router)
    dp.include_router(help.router)
    dp.include_router(settings.router)
    dp.include_router(stats.router)

    # Рейтинги
    dp.include_router(monthly.router)
    dp.include_router(alltime.router)
    dp.include_router(personal.router)