"""
Проверка месячной статистики после викторины
"""

import asyncio
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.models import User, MonthlySeason, MonthlyStats, QuizSession


async def main():
    print("🔍 ПРОВЕРКА МЕСЯЧНОЙ СТАТИСТИКИ")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        # 1. Проверяем текущий сезон
        season_result = await session.execute(
            select(MonthlySeason).where(MonthlySeason.is_active == True)
        )
        season = season_result.scalar_one_or_none()

        if season:
            print(f"✅ Активный сезон: {season.month}/{season.year}")
            print(f"   ID: {season.id}")
            print(f"   Даты: {season.start_date} - {season.end_date}")
        else:
            print("❌ Нет активного сезона!")
            return

        print()

        # 2. Проверяем все викторины
        quizzes_result = await session.execute(
            select(QuizSession)
            .where(QuizSession.completed_at.isnot(None))
            .order_by(QuizSession.completed_at.desc())
            .limit(5)
        )
        quizzes = quizzes_result.scalars().all()

        print(f"📝 Последние {len(quizzes)} викторин:")
        for q in quizzes:
            print(f"   User {q.user_id}: {q.correct_answers}/{q.total_questions} ({q.completed_at})")

        print()

        # 3. Проверяем месячную статистику
        stats_result = await session.execute(
            select(MonthlyStats, User)
            .join(User, MonthlyStats.user_id == User.id)
            .where(MonthlyStats.season_id == season.id)
        )
        stats_users = stats_result.all()

        print(f"📊 Месячная статистика ({len(stats_users)} пользователей):")
        print()

        for stat, user in stats_users:
            print(f"👤 {user.username or user.id}:")
            print(f"   🔥 Стрик: {stat.monthly_streak} дней")
            print(f"   ✅ Викторины: {stat.monthly_quizzes}")
            print(f"   📚 Слова: {stat.monthly_words}")
            print(f"   🔄 Реверс: {stat.monthly_reverse}")
            print(f"   📊 Средний %: {stat.monthly_avg_percent}%")
            print(f"   💎 ИТОГО: {stat.monthly_score} баллов")
            print(f"   📅 Обновлено: {stat.updated_at}")

            # Проверяем формулу
            calculated = stat.calculate_monthly_score()
            if calculated != stat.monthly_score:
                print(f"   ⚠️ ОШИБКА! Пересчёт даёт {calculated}, но записано {stat.monthly_score}")
            else:
                print(f"   ✅ Формула верна")

            print()

        # 4. Проверяем lifetime поля в User
        users_result = await session.execute(
            select(User).where(User.quizzes_passed > 0).limit(5)
        )
        users = users_result.scalars().all()

        print(f"👥 Lifetime данные ({len(users)} пользователей):")
        for user in users:
            print(f"   {user.username or user.id}:")
            print(f"      💎 Lifetime: {user.lifetime_score}")
            print(f"      🔥 Best streak: {user.best_streak_days}")
            print(f"      🏆 Месячных побед: {user.total_monthly_wins}")

        print()
        print("=" * 50)
        print("Проверка завершена!")


if __name__ == "__main__":
    asyncio.run(main())