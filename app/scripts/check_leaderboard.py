#!/usr/bin/env python3
"""
Диагностика системы рейтинга GenauLingua

Запуск:
  docker compose exec app python app/scripts/check_leaderboard.py

Проверяет:
  1. Сезон существует и активен
  2. MonthlyStats данные корректны
  3. Формула подсчёта баллов совпадает
  4. get_user_monthly_rank возвращает полные данные
  5. get_lifetime_leaderboard возвращает данные (не None)
  6. User.display_name показывает имя (не @username)
  7. MonthlyAward не имеет .emoji (проверка модели)
  8. Сверка данных MonthlyStats с реальными QuizSession
"""

import sys
import os
from pathlib import Path

# Добавляем корень проекта
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime, date
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


# Цвета для вывода
OK = "✅"
FAIL = "❌"
WARN = "⚠️"
INFO = "ℹ️"

errors = []
warnings = []


def ok(msg):
    print(f"  {OK} {msg}")


def fail(msg):
    print(f"  {FAIL} {msg}")
    errors.append(msg)


def warn(msg):
    print(f"  {WARN} {msg}")
    warnings.append(msg)


def info(msg):
    print(f"  {INFO} {msg}")


async def run_checks():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{FAIL} DATABASE_URL не задан!")
        return

    engine = create_async_engine(db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:

        # ==================================================================
        print("\n" + "=" * 50)
        print("1. ПРОВЕРКА СЕЗОНА")
        print("=" * 50)

        from app.database.models import (
            MonthlySeason, MonthlyStats, MonthlyQuizEvent,
            MonthlyAward, WinStreak, User, QuizSession, UserWord
        )

        # Текущий сезон
        result = await session.execute(
            select(MonthlySeason).where(MonthlySeason.is_active == True)
        )
        season = result.scalar_one_or_none()

        if season:
            ok(f"Активный сезон: {season.month}/{season.year} (id={season.id})")
            ok(f"Период: {season.start_date} — {season.end_date}")
            today = date.today()
            if season.start_date <= today <= season.end_date:
                ok(f"Сегодня ({today}) входит в рамки сезона")
            else:
                fail(f"Сегодня ({today}) НЕ входит в рамки сезона {season.start_date}—{season.end_date}")
        else:
            fail("Нет активного сезона! Рейтинг не будет работать.")
            print("\n⛔ Без сезона дальнейшие проверки невозможны.")
            return

        # Все сезоны
        all_seasons = await session.execute(select(MonthlySeason))
        seasons_list = all_seasons.scalars().all()
        active_count = sum(1 for s in seasons_list if s.is_active)
        info(f"Всего сезонов: {len(seasons_list)}, активных: {active_count}")
        if active_count > 1:
            fail(f"Более 1 активного сезона! Должен быть только 1.")

        # ==================================================================
        print("\n" + "=" * 50)
        print("2. ПРОВЕРКА ПОЛЬЗОВАТЕЛЕЙ И MONTHLY STATS")
        print("=" * 50)

        # Все юзеры
        users_result = await session.execute(select(User))
        all_users = users_result.scalars().all()
        info(f"Всего пользователей: {len(all_users)}")

        # MonthlyStats за текущий сезон
        stats_result = await session.execute(
            select(MonthlyStats).where(MonthlyStats.season_id == season.id)
        )
        all_stats = stats_result.scalars().all()
        info(f"Записей MonthlyStats за текущий сезон: {len(all_stats)}")

        if not all_stats:
            warn("Нет записей MonthlyStats — никто ещё не проходил викторины в этом сезоне")

        for stat in all_stats:
            user = await session.get(User, stat.user_id)
            user_name = user.display_name if user else f"ID:{stat.user_id}"

            print(f"\n  --- {user_name} ---")

            # Проверяем формулу
            expected_score = stat.calculate_monthly_score()
            if stat.monthly_score == expected_score:
                ok(f"Баллы: {stat.monthly_score} (формула совпадает)")
            else:
                fail(f"Баллы: {stat.monthly_score} ≠ ожидаемые {expected_score} (формула не совпадает!)")

            # Проверяем avg_percent
            if stat.total_questions > 0:
                expected_avg = int((stat.total_correct / stat.total_questions) * 100)
                if stat.monthly_avg_percent == expected_avg:
                    ok(f"Средний %: {stat.monthly_avg_percent}% (корректно)")
                else:
                    fail(f"Средний %: {stat.monthly_avg_percent}% ≠ ожидаемые {expected_avg}%")
            else:
                info(f"Средний %: {stat.monthly_avg_percent}% (нет вопросов)")

            # Сверяем кол-во викторин с реальными QuizSession
            real_quizzes_result = await session.execute(
                select(func.count()).select_from(QuizSession).where(
                    QuizSession.user_id == stat.user_id,
                    QuizSession.completed_at.isnot(None),
                    QuizSession.started_at >= season.start_date,
                    QuizSession.started_at <= datetime.combine(season.end_date, datetime.max.time())
                )
            )
            real_quiz_count = real_quizzes_result.scalar() or 0

            if stat.monthly_quizzes == real_quiz_count:
                ok(f"Викторин: {stat.monthly_quizzes} (совпадает с QuizSession)")
            else:
                warn(f"Викторин: stats={stat.monthly_quizzes} vs real={real_quiz_count} (расхождение, возможно нужен recalc)")

            # Проверяем идемпотентность
            events_result = await session.execute(
                select(func.count()).select_from(MonthlyQuizEvent).where(
                    MonthlyQuizEvent.user_id == stat.user_id,
                    MonthlyQuizEvent.season_id == season.id
                )
            )
            events_count = events_result.scalar() or 0
            if events_count == stat.monthly_quizzes:
                ok(f"Quiz events: {events_count} (идемпотентность OK)")
            else:
                warn(f"Quiz events: {events_count} vs stats: {stat.monthly_quizzes}")

            info(f"Слов: {stat.monthly_words} | Стрик: {stat.monthly_streak} дн. | Реверс: {stat.monthly_reverse}")

        # ==================================================================
        print("\n" + "=" * 50)
        print("3. ПРОВЕРКА get_user_monthly_rank()")
        print("=" * 50)

        from app.services.monthly_leaderboard_service import get_user_monthly_rank

        for stat in all_stats:
            user = await session.get(User, stat.user_id)
            rank_data = await get_user_monthly_rank(stat.user_id, session, season_id=season.id)

            if rank_data is None:
                fail(f"{user.display_name}: get_user_monthly_rank вернул None!")
                continue

            # Проверяем что все поля присутствуют
            required_fields = ['rank', 'total_users', 'monthly_score', 'monthly_quizzes',
                             'monthly_words', 'monthly_streak', 'monthly_avg_percent']
            missing = [f for f in required_fields if f not in rank_data]

            if missing:
                fail(f"{user.display_name}: отсутствуют поля: {missing}")
            else:
                ok(f"{user.display_name}: rank=#{rank_data['rank']}, score={rank_data['monthly_score']}, "
                   f"quizzes={rank_data['monthly_quizzes']}, words={rank_data['monthly_words']}, "
                   f"streak={rank_data['monthly_streak']}, avg={rank_data['monthly_avg_percent']}%")

        # ==================================================================
        print("\n" + "=" * 50)
        print("4. ПРОВЕРКА get_lifetime_leaderboard()")
        print("=" * 50)

        from app.services.monthly_leaderboard_service import get_lifetime_leaderboard

        leaderboard = await get_lifetime_leaderboard(session, limit=10)

        if leaderboard is None:
            fail("get_lifetime_leaderboard вернул None! (отсутствует return)")
        elif isinstance(leaderboard, list):
            ok(f"Вернул list, {len(leaderboard)} записей")
            for entry in leaderboard[:3]:
                ok(f"  #{entry['rank']} {entry['display_name']} — {entry['lifetime_score']} lifetime")
        else:
            fail(f"Вернул неожиданный тип: {type(leaderboard)}")

        # ==================================================================
        print("\n" + "=" * 50)
        print("5. ПРОВЕРКА display_name")
        print("=" * 50)

        for user in all_users[:5]:
            dn = user.display_name
            if dn.startswith("@"):
                warn(f"User {user.id}: display_name='{dn}' — начинается с @, приоритет username")
            elif dn.startswith("User "):
                warn(f"User {user.id}: display_name='{dn}' — нет имени/фамилии/username")
            else:
                ok(f"User {user.id}: display_name='{dn}'")

            # Проверяем логику
            if user.first_name and not dn.startswith(user.first_name):
                fail(f"User {user.id}: first_name='{user.first_name}' но display_name='{dn}'")

        # ==================================================================
        print("\n" + "=" * 50)
        print("6. ПРОВЕРКА MonthlyAward (отсутствие .emoji)")
        print("=" * 50)

        awards_result = await session.execute(select(MonthlyAward).limit(5))
        awards = awards_result.scalars().all()

        if not awards:
            info("Наград пока нет (это нормально, сезон не завершён)")
        else:
            for award in awards:
                if hasattr(award, 'emoji'):
                    fail(f"MonthlyAward #{award.id} имеет .emoji — это не должно существовать!")
                else:
                    ok(f"Award #{award.id}: type={award.award_type}, rank={award.rank} (без .emoji — OK)")

        # ==================================================================
        print("\n" + "=" * 50)
        print("7. ПРОВЕРКА User.lifetime_score и total_monthly_wins")
        print("=" * 50)

        for user in all_users:
            if user.lifetime_score < 0:
                fail(f"{user.display_name}: lifetime_score={user.lifetime_score} — отрицательный!")
            if user.total_monthly_wins < 0:
                fail(f"{user.display_name}: total_monthly_wins={user.total_monthly_wins} — отрицательный!")

        users_with_score = [u for u in all_users if u.lifetime_score > 0]
        users_with_wins = [u for u in all_users if u.total_monthly_wins > 0]
        info(f"Юзеров с lifetime_score > 0: {len(users_with_score)}")
        info(f"Юзеров с total_monthly_wins > 0: {len(users_with_wins)}")

        # Проверяем что wins <= количество завершённых сезонов
        finalized_seasons = sum(1 for s in seasons_list if s.winners_finalized)
        for user in users_with_wins:
            if user.total_monthly_wins > finalized_seasons:
                fail(f"{user.display_name}: wins={user.total_monthly_wins} > завершённых сезонов={finalized_seasons}")

        ok(f"Завершённых сезонов: {finalized_seasons}")

    # ==================================================================
    print("\n" + "=" * 50)
    print("ИТОГИ")
    print("=" * 50)

    if not errors and not warnings:
        print(f"\n{OK} Все проверки пройдены! Система рейтинга работает корректно.\n")
    else:
        if errors:
            print(f"\n{FAIL} Ошибок: {len(errors)}")
            for e in errors:
                print(f"   • {e}")
        if warnings:
            print(f"\n{WARN} Предупреждений: {len(warnings)}")
            for w in warnings:
                print(f"   • {w}")
        print()


if __name__ == "__main__":
    asyncio.run(run_checks())