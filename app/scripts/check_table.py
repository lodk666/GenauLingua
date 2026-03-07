#!/usr/bin/env python3
"""
Проверка таблицы лидеров + рейтинга

Запуск:
  python app/scripts/check_table.py
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime, date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

OK = "✅"
FAIL = "❌"
WARN = "⚠️"
INFO = "ℹ️"

errors = []
warnings = []

def ok(msg): print(f"  {OK} {msg}")
def fail(msg): print(f"  {FAIL} {msg}"); errors.append(msg)
def warn(msg): print(f"  {WARN} {msg}"); warnings.append(msg)
def info(msg): print(f"  {INFO} {msg}")


async def run_checks():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print(f"{FAIL} DATABASE_URL не задан!")
        return

    engine = create_async_engine(db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:

        from app.database.models import (
            MonthlySeason, MonthlyStats, User, QuizSession
        )
        from app.services.monthly_leaderboard_service import (
            get_monthly_leaderboard, get_user_monthly_rank,
            get_current_season, get_lifetime_leaderboard
        )

        # ==================================================================
        print("\n" + "=" * 55)
        print("  1. МЕСЯЧНЫЙ РЕЙТИНГ — ДАННЫЕ")
        print("=" * 55)

        season = await get_current_season(session)
        if not season:
            fail("Нет активного сезона!")
            return

        ok(f"Сезон: {season.month}/{season.year}")

        leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)
        info(f"В месячном лидерборде: {len(leaderboard)} записей")

        for entry in leaderboard:
            rank = entry["rank"]
            name = entry["display_name"]
            score = entry["monthly_score"]
            quizzes = entry["monthly_quizzes"]
            words = entry["monthly_words"]
            streak = entry["monthly_streak"]
            avg = entry["monthly_avg_percent"]

            # Проверяем что все поля не None
            fields_ok = all(v is not None for v in [score, quizzes, words, streak, avg])
            if fields_ok:
                ok(f"#{rank} {name}: score={score}, quizzes={quizzes}, words={words}, streak={streak}, avg={avg}%")
            else:
                fail(f"#{rank} {name}: есть None поля!")

            # Проверяем display_name не пустой
            if not name or name.startswith("User "):
                warn(f"#{rank}: display_name='{name}' — нет имени")

            # Проверяем что awards не падает
            try:
                awards = entry.get("awards", [])
                for a in awards:
                    _ = a["emoji"]  # должно быть строкой из _award_type_to_emoji
                ok(f"#{rank}: awards OK ({len(awards)} шт)")
            except Exception as e:
                fail(f"#{rank}: awards ошибка: {e}")

            # Проверяем win_streak
            ws = entry.get("win_streak")
            if ws is not None:
                try:
                    _ = ws["current"]
                    _ = ws["emoji"]
                    ok(f"#{rank}: win_streak OK")
                except Exception as e:
                    fail(f"#{rank}: win_streak ошибка: {e}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  2. ПОЗИЦИЯ КАЖДОГО ЮЗЕРА")
        print("=" * 55)

        # Проверяем get_user_monthly_rank для всех юзеров с MonthlyStats
        stats_result = await session.execute(
            select(MonthlyStats).where(MonthlyStats.season_id == season.id)
        )
        all_stats = stats_result.scalars().all()

        for stat in all_stats:
            user = await session.get(User, stat.user_id)
            rank_data = await get_user_monthly_rank(stat.user_id, session, season_id=season.id)

            if not rank_data:
                fail(f"{user.display_name}: get_user_monthly_rank → None")
                continue

            # Сверяем score
            if rank_data['monthly_score'] != stat.monthly_score:
                fail(f"{user.display_name}: rank_data score={rank_data['monthly_score']} ≠ stat score={stat.monthly_score}")
            else:
                ok(f"{user.display_name}: позиция #{rank_data['rank']}, score={rank_data['monthly_score']}")

            # Сверяем quizzes
            if rank_data.get('monthly_quizzes') != stat.monthly_quizzes:
                fail(f"{user.display_name}: rank_data quizzes={rank_data.get('monthly_quizzes')} ≠ stat={stat.monthly_quizzes}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  3. LIFETIME РЕЙТИНГ")
        print("=" * 55)

        lifetime_lb = await get_lifetime_leaderboard(session, limit=10)

        if lifetime_lb is None:
            fail("get_lifetime_leaderboard → None!")
        else:
            ok(f"Lifetime лидерборд: {len(lifetime_lb)} записей")

            for entry in lifetime_lb:
                rank = entry["rank"]
                name = entry["display_name"]
                score = entry["lifetime_score"]
                wins = entry["total_wins"]
                words = entry["words_learned"]

                ok(f"#{rank} {name}: lifetime={score}, wins={wins}, words={words}")

                # Сверяем с User
                users_result = await session.execute(select(User))
                all_users = users_result.scalars().all()
                for u in all_users:
                    if u.display_name == name:
                        if u.lifetime_score != score:
                            fail(f"{name}: lifetime в лидерборде={score} ≠ User.lifetime_score={u.lifetime_score}")
                        if u.total_monthly_wins != wins:
                            fail(f"{name}: wins в лидерборде={wins} ≠ User.total_monthly_wins={u.total_monthly_wins}")
                        break

        # ==================================================================
        print("\n" + "=" * 55)
        print("  4. ТАБЛИЦА ЛИДЕРОВ — ЛОГИКА ОТОБРАЖЕНИЯ")
        print("=" * 55)

        try:
            from app.bot.handlers.leaderboard.leaderboard_table import (
                build_monthly_table, build_alltime_table, _rank_emoji, _shorten_name
            )
            ok("leaderboard_table.py импортируется")

            # Тест _rank_emoji
            assert _rank_emoji(1) == "🥇"
            assert _rank_emoji(2) == "🥈"
            assert _rank_emoji(3) == "🥉"
            assert _rank_emoji(4) == "4."
            assert _rank_emoji(10) == "10."
            ok("_rank_emoji работает")

            # Тест _shorten_name
            assert _shorten_name("K.") == "K."
            assert len(_shorten_name("Очень длинное имя пользователя")) <= 15
            ok("_shorten_name работает")

            # Тест build_monthly_table с реальными данными
            user = await session.get(User, all_stats[0].user_id) if all_stats else None
            if user:
                user_rank = await get_user_monthly_rank(user.id, session, season_id=season.id)
                text = build_monthly_table(leaderboard, user_rank, season, user.id, "ru")

                if "Таблица лидеров" in text:
                    ok("build_monthly_table: заголовок на месте")
                else:
                    fail("build_monthly_table: нет заголовка")

                if user.display_name in text or f"<b>{user.display_name}</b>" in text:
                    ok("build_monthly_table: юзер подсвечен жирным")
                else:
                    warn("build_monthly_table: юзер не найден в тексте")

                if "Ты:" in text:
                    ok("build_monthly_table: блок 'Ты:' на месте")
                else:
                    fail("build_monthly_table: нет блока 'Ты:'")

            # Тест build_alltime_table
            if user and lifetime_lb:
                text_at = build_alltime_table(lifetime_lb, user, "ru")

                if "За всё время" in text_at:
                    ok("build_alltime_table: заголовок на месте")
                else:
                    fail("build_alltime_table: нет заголовка")

                if "Ты:" in text_at:
                    ok("build_alltime_table: блок 'Ты:' на месте")
                else:
                    fail("build_alltime_table: нет блока 'Ты:'")

        except ImportError as e:
            fail(f"Не удалось импортировать leaderboard_table: {e}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  5. СИМУЛЯЦИЯ: ЮЗЕ НЕ В ТОП-10")
        print("=" * 55)

        # Создаём фейковый лидерборд где юзера нет
        if user:
            fake_leaderboard = []
            for i in range(10):
                fake_leaderboard.append({
                    "rank": i + 1,
                    "user_id": 999999900 + i,  # фейковые ID
                    "display_name": f"Player {i+1}",
                    "monthly_score": 100 - i * 10,
                    "monthly_quizzes": 10 - i,
                    "monthly_words": 5,
                    "monthly_streak": 3,
                    "monthly_avg_percent": 80,
                    "monthly_reverse": 0,
                    "win_streak": None,
                    "awards": []
                })

            fake_rank = {
                'rank': 15,
                'total_users': 20,
                'monthly_score': 25,
                'monthly_quizzes': 2,
                'monthly_words': 0,
                'monthly_streak': 1,
                'monthly_avg_percent': 50,
            }

            try:
                text_sim = build_monthly_table(fake_leaderboard, fake_rank, season, user.id, "ru")

                # Юзер НЕ должен быть в топ-10 (жирным)
                if f"<b>{user.display_name}</b>" not in text_sim:
                    ok("Юзер не в топ-10 — не подсвечен жирным (правильно)")
                else:
                    warn("Юзер подсвечен жирным хотя не в топ-10")

                # Должен быть показан отдельно с позицией #15
                if "#15" in text_sim and "25 баллов" in text_sim:
                    ok("Юзер показан отдельно: #15 — 25 баллов")
                else:
                    fail("Юзер вне топ-10 не отображается корректно")

            except Exception as e:
                fail(f"Симуляция упала: {e}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  6. CALLBACK-МАРШРУТЫ ТАБЛИЦЫ")
        print("=" * 55)

        try:
            import inspect
            from app.bot.handlers.leaderboard import leaderboard_table
            source = inspect.getsource(leaderboard_table)

            expected_callbacks = [
                "leaderboard_table_monthly",
                "leaderboard_table_alltime",
                "table_monthly",
                "table_alltime",
                "rating_monthly",  # кнопка назад
            ]

            for cb in expected_callbacks:
                if cb in source:
                    ok(f"callback '{cb}' найден")
                else:
                    fail(f"callback '{cb}' НЕ найден!")

        except Exception as e:
            fail(f"Ошибка проверки callbacks: {e}")

    # ==================================================================
    print("\n" + "=" * 55)
    print("  ИТОГИ")
    print("=" * 55)

    if not errors and not warnings:
        print(f"\n{OK} ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!\n")
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