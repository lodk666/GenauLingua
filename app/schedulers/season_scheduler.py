"""
Планировщик сезонов рейтинга

Задачи:
1. 1 числа каждого месяца в 00:05 UTC:
   - Завершить предыдущий сезон (раздать награды, обновить lifetime)
   - Создать новый сезон

2. Каждый час — проверка что активный сезон соответствует текущему месяцу
   (страховка на случай если бот был выключен 1 числа)
"""

import logging
from datetime import date

from app.database.session import AsyncSessionLocal
from app.services.monthly_leaderboard_service import (
    get_current_season,
    create_new_season,
    finalize_season
)

logger = logging.getLogger(__name__)


async def finalize_and_create_new_season():
    """
    Завершить старый сезон + создать новый.
    Вызывается 1 числа каждого месяца.
    """
    today = date.today()
    logger.info(f"🔄 Проверка смены сезона: {today}")

    async with AsyncSessionLocal() as session:
        # 1. Получаем текущий активный сезон
        current_season = await get_current_season(session)

        if not current_season:
            # Нет активного сезона — просто создаём новый
            logger.info(f"📅 Нет активного сезона, создаю {today.month}/{today.year}")
            await create_new_season(today.year, today.month, session)
            return

        # 2. Проверяем — сезон от текущего месяца или от прошлого?
        if current_season.year == today.year and current_season.month == today.month:
            # Сезон уже текущий — ничего делать не нужно
            logger.debug(f"✅ Сезон {current_season.month}/{current_season.year} актуален")
            return

        # 3. Сезон от прошлого месяца — завершаем его!
        logger.info(f"🏁 Завершаю сезон {current_season.month}/{current_season.year} (id={current_season.id})")

        if not current_season.winners_finalized:
            try:
                await finalize_season(current_season.id, session)
                logger.info(f"✅ Сезон {current_season.month}/{current_season.year} завершён, награды розданы!")
            except Exception as e:
                logger.error(f"❌ Ошибка завершения сезона: {e}")
                # Не прерываем — всё равно создаём новый сезон
        else:
            logger.info(f"ℹ️ Сезон {current_season.month}/{current_season.year} уже был завершён")

        # 4. Создаём новый сезон
        logger.info(f"📅 Создаю новый сезон {today.month}/{today.year}")
        try:
            new_season = await create_new_season(today.year, today.month, session)
            logger.info(f"✅ Новый сезон создан: {new_season.month}/{new_season.year} (id={new_season.id})")
        except Exception as e:
            logger.error(f"❌ Ошибка создания нового сезона: {e}")


async def hourly_season_check():
    """
    Страховочная проверка каждый час.
    Если бот был выключен 1 числа — подхватит смену сезона.
    """
    today = date.today()

    async with AsyncSessionLocal() as session:
        current_season = await get_current_season(session)

        if not current_season:
            # Нет сезона — создаём
            logger.warning(f"⚠️ Нет активного сезона! Создаю {today.month}/{today.year}")
            await create_new_season(today.year, today.month, session)
            return

        # Если сезон от прошлого месяца — запускаем полную процедуру
        if current_season.year != today.year or current_season.month != today.month:
            logger.warning(f"⚠️ Активный сезон {current_season.month}/{current_season.year} устарел!")
            await finalize_and_create_new_season()