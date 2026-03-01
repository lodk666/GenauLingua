"""
Скрипт для создания первого месячного сезона

Использование:
1. Скопируй этот файл в корень проекта как create_first_season.py
2. Запусти: docker compose exec app python create_first_season.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import date

# Добавляем корень проекта в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database.session import AsyncSessionLocal
from app.services.monthly_leaderboard_service import create_new_season, get_current_season


async def main():
    """Создать первый месячный сезон"""

    print("🏆 СОЗДАНИЕ ПЕРВОГО МЕСЯЧНОГО СЕЗОНА")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        # Проверяем есть ли уже активный сезон
        existing_season = await get_current_season(session)

        if existing_season:
            print(f"⚠️ Активный сезон уже существует:")
            print(f"   ID: {existing_season.id}")
            print(f"   Месяц: {existing_season.month}/{existing_season.year}")
            print(f"   Даты: {existing_season.start_date} - {existing_season.end_date}")
            print()

            answer = input("Хочешь создать новый сезон? (yes/no): ")
            if answer.lower() not in ['yes', 'y', 'да']:
                print("❌ Отменено")
                return

        # Запрашиваем месяц и год
        today = date.today()

        print()
        print(f"Текущая дата: {today}")
        print()

        year_input = input(f"Введи год (Enter = {today.year}): ").strip()
        year = int(year_input) if year_input else today.year

        month_input = input(f"Введи месяц 1-12 (Enter = {today.month}): ").strip()
        month = int(month_input) if month_input else today.month

        # Проверка
        if month < 1 or month > 12:
            print("❌ Месяц должен быть от 1 до 12")
            return

        print()
        print(f"Создаём сезон: {month}/{year}")
        print()

        # Создаём сезон
        try:
            season = await create_new_season(year, month, session)

            print("✅ СЕЗОН СОЗДАН!")
            print()
            print(f"📋 Детали:")
            print(f"   ID: {season.id}")
            print(f"   Месяц: {season.month}/{season.year}")
            print(f"   Начало: {season.start_date}")
            print(f"   Конец: {season.end_date}")
            print(f"   Активен: {season.is_active}")
            print()
            print("🎉 Теперь пользователи могут соревноваться!")

        except Exception as e:
            print(f"❌ Ошибка при создании сезона: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())