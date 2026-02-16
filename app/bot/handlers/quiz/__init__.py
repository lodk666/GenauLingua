"""
Модуль quiz - игровая логика, настройки, статистика, помощь
"""

from aiogram import Router

# Импортируем роутеры из всех подмодулей
from .game import router as game_router
from .settings import router as settings_router
from .stats import router as stats_router
from .help import router as help_router

# Создаём главный роутер для модуля quiz
router = Router()

# Подключаем все роутеры
router.include_router(game_router)
router.include_router(settings_router)
router.include_router(stats_router)
router.include_router(help_router)

__all__ = ['router']