"""
check_stats.py - Проверить статистику БД без psql
Место: в корне проекта (GenauLingua/)
"""

import asyncio
import sys
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Импортируем модели
from app.database.models import MonthlyStats, User, MonthlySeason, MonthlyQuizEvent

# Импортируем конфиг БД
from app.config import DATABASE_URL


async def check_monthly_stats():
    """Проверить месячную статистику"""

    print("=" * 60)
    print("🔍 ПРОВЕРКА МЕСЯЧНОЙ СТАТИСТИКИ")
    print("=" * 60)

    # Подключение к БД
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:

            # 1. Проверить сезон
            print("\n1️⃣ ТЕКУЩИЙ СЕЗОН:")
            result = await session.execute(
                select(MonthlySeason).where(MonthlySeason.is_active == True)
            )
            season = result.scalar_one_or_none()

            if season:
                print(f"   ✅ Сезон существует: {season.month}/{season.year}")
                print(f"   📅 Даты: {season.start_date} - {season.end_date}")
                print(f"   ID: {season.id}")
            else:
                print("   ❌ Активного сезона нет!")
                return

            # 2. Проверить статистику
            print("\n2️⃣ СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ:")
            result = await session.execute(
                select(MonthlyStats)
                .where(MonthlyStats.season_id == season.id)
                .order_by(MonthlyStats.updated_at.desc())
                .limit(10)
            )
            stats_list = result.scalars().all()

            if not stats_list:
                print("   ⚠️ Статистика ещё не записана!")
                print("   💡 Нужно пройти хотя бы одну викторину")
            else:
                print(f"   ✅ Найдено {len(stats_list)} записей статистики:")

                for i, stat in enumerate(stats_list, 1):
                    user = await session.get(User, stat.user_id)
                    print(f"\n   [{i}] 👤 {user.display_name} (ID: {user.id})")
                    print(f"       📝 Викторин: {stat.monthly_quizzes}")
                    print(f"       📊 Средний %: {stat.monthly_avg_percent}%")
                    print(f"       💎 Баллов: {stat.monthly_score}")
                    print(f"       🔥 Стрик (дни): {stat.monthly_streak}")
                    print(f"       📚 Слова: {stat.monthly_words}")
                    print(f"       ⏰ Обновлено: {stat.updated_at}")

            # 3. Проверить события викторин (идемпотентность)
            print("\n3️⃣ СОБЫТИЯ ВИКТОРИН (идемпотентность):")
            result = await session.execute(
                select(MonthlyQuizEvent)
                .where(MonthlyQuizEvent.season_id == season.id)
                .order_by(MonthlyQuizEvent.created_at.desc())
                .limit(5)
            )
            events = result.scalars().all()

            if events:
                print(f"   ✅ Записано {len(events)} событий:")
                for event in events:
                    user = await session.get(User, event.user_id)
                    print(f"      • Quiz {event.quiz_session_id}: {user.display_name}")
            else:
                print("   ⚠️ События ещё не записаны")

            # 4. Итоговый вывод
            print("\n" + "=" * 60)
            if stats_list:
                top_stat = stats_list[0]
                top_user = await session.get(User, top_stat.user_id)
                print(f"🏆 ЛИДЕР: {top_user.display_name}")
                print(f"   Баллов: {top_stat.monthly_score}")
                print(f"   Викторин: {top_stat.monthly_quizzes}")
                print(f"\n✅ СИСТЕМА МЕСЯЧНОГО РЕЙТИНГА РАБОТАЕТ!")
            else:
                print("⚠️ Статистика пока пуста")
                print("💡 Пройди викторину и повтори проверку")

            print("=" * 60)

    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        print("\nПроверь:")
        print("  1. PostgreSQL запущен?")
        print("  2. DATABASE_URL в app/config.py правильный?")
        print("  3. Миграции применены? (alembic upgrade head)")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_monthly_stats())