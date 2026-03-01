"""
Комплексная проверка базы данных
"""

import asyncio
from sqlalchemy import select, text
from app.database.session import AsyncSessionLocal
from app.database.models import User, Word, MonthlySeason


async def main():
    print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        # 1. Проверка подключения
        try:
            result = await session.execute(text("SELECT 1"))
            print("✅ Подключение к БД работает")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return

        # 2. Проверка таблицы users
        try:
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if user:
                print(f"✅ Таблица users работает (найден user: {user.id})")
            else:
                print("⚠️ Таблица users пустая")
        except Exception as e:
            print(f"❌ Ошибка таблицы users: {e}")

        # 3. Проверка таблицы words
        try:
            result = await session.execute(select(Word).limit(1))
            word = result.scalar_one_or_none()
            if word:
                print(f"✅ Таблица words работает (найдено слово: {word.word_de})")
            else:
                print("⚠️ Таблица words пустая")
        except Exception as e:
            print(f"❌ Ошибка таблицы words: {e}")

        # 4. Проверка новых таблиц месячного рейтинга
        try:
            result = await session.execute(select(MonthlySeason))
            seasons = result.scalars().all()
            if seasons:
                print(f"✅ Таблица monthly_seasons работает ({len(seasons)} сезонов)")
                for s in seasons:
                    print(f"   - Сезон {s.month}/{s.year} (активен: {s.is_active})")
            else:
                print("⚠️ Таблица monthly_seasons пустая")
        except Exception as e:
            print(f"❌ Ошибка таблицы monthly_seasons: {e}")

        # 5. Проверка новых полей в users
        try:
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if user:
                print(f"✅ Новые поля в User:")
                print(f"   - lifetime_score: {user.lifetime_score}")
                print(f"   - best_streak_days: {user.best_streak_days}")
                print(f"   - total_monthly_wins: {user.total_monthly_wins}")
        except AttributeError as e:
            print(f"❌ Ошибка: новые поля отсутствуют в User: {e}")
        except Exception as e:
            print(f"❌ Ошибка проверки полей: {e}")

        print()
        print("=" * 50)
        print("Проверка завершена!")


if __name__ == "__main__":
    asyncio.run(main())