#!/usr/bin/env python3
"""
Полная диагностика GenauLingua: напоминания, сезоны, рейтинг

Запуск:
  python app/scripts/check_full_system.py
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

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

        from app.database.models import (
            MonthlySeason, MonthlyStats, MonthlyQuizEvent,
            MonthlyAward, WinStreak, User, QuizSession, UserWord
        )

        # ==================================================================
        print("\n" + "=" * 55)
        print("  1. СЕЗОНЫ")
        print("=" * 55)

        all_seasons_result = await session.execute(select(MonthlySeason).order_by(MonthlySeason.year, MonthlySeason.month))
        all_seasons = all_seasons_result.scalars().all()
        info(f"Всего сезонов в БД: {len(all_seasons)}")

        active_seasons = [s for s in all_seasons if s.is_active]
        if len(active_seasons) == 1:
            ok(f"Ровно 1 активный сезон")
        elif len(active_seasons) == 0:
            fail("Нет активного сезона!")
        else:
            fail(f"Активных сезонов: {len(active_seasons)} (должен быть 1)")

        season = active_seasons[0] if active_seasons else None

        if season:
            ok(f"Активный: {season.month}/{season.year} (id={season.id})")
            today = date.today()
            if season.year == today.year and season.month == today.month:
                ok(f"Сезон соответствует текущему месяцу ({today.month}/{today.year})")
            else:
                fail(f"Сезон {season.month}/{season.year} НЕ соответствует текущему {today.month}/{today.year}!")
                warn("hourly_season_check должен это исправить при следующем запуске")

            if season.start_date <= today <= season.end_date:
                ok(f"Сегодня ({today}) в рамках сезона")
            else:
                fail(f"Сегодня вне рамок: {season.start_date} — {season.end_date}")

            if season.winners_finalized:
                fail("Активный сезон уже finalized — это ошибка!")
            else:
                ok("Сезон ещё не завершён (winners_finalized=False)")

        # Проверяем завершённые сезоны
        finalized = [s for s in all_seasons if s.winners_finalized]
        info(f"Завершённых сезонов: {len(finalized)}")
        for s in finalized:
            if s.is_active:
                fail(f"Сезон {s.month}/{s.year} finalized=True но is_active=True!")
            else:
                ok(f"Сезон {s.month}/{s.year} завершён и деактивирован")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  2. SCHEDULER — ПРОВЕРКА КОДА")
        print("=" * 55)

        # Проверяем что season_scheduler импортируется
        try:
            from app.schedulers.season_scheduler import finalize_and_create_new_season, hourly_season_check
            ok("season_scheduler.py импортируется")
            ok("finalize_and_create_new_season() доступна")
            ok("hourly_season_check() доступна")
        except ImportError as e:
            fail(f"Не удалось импортировать season_scheduler: {e}")

        # Проверяем что reminder_scheduler содержит сезонные задачи
        try:
            import inspect
            from app.schedulers.reminder_scheduler import setup_scheduler
            source = inspect.getsource(setup_scheduler)
            if "finalize_season" in source or "finalize_and_create_new_season" in source:
                ok("setup_scheduler содержит задачу finalize_season")
            else:
                fail("setup_scheduler НЕ содержит задачу finalize_season!")

            if "hourly_season_check" in source:
                ok("setup_scheduler содержит hourly_season_check")
            else:
                fail("setup_scheduler НЕ содержит hourly_season_check!")

            if "check_and_send_notifications" in source:
                ok("setup_scheduler содержит check_and_send_notifications")
            else:
                fail("setup_scheduler НЕ содержит напоминания!")
        except Exception as e:
            fail(f"Ошибка проверки scheduler: {e}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  3. MONTHLY STATS — ДАННЫЕ")
        print("=" * 55)

        if not season:
            warn("Нет активного сезона — пропускаю проверку stats")
        else:
            stats_result = await session.execute(
                select(MonthlyStats).where(MonthlyStats.season_id == season.id)
            )
            all_stats = stats_result.scalars().all()
            info(f"Записей MonthlyStats: {len(all_stats)}")

            for stat in all_stats:
                user = await session.get(User, stat.user_id)
                name = user.display_name if user else f"ID:{stat.user_id}"

                # Формула
                expected = stat.calculate_monthly_score()
                if stat.monthly_score == expected:
                    ok(f"{name}: баллы={stat.monthly_score} (формула ОК)")
                else:
                    fail(f"{name}: баллы={stat.monthly_score} ≠ ожидаемые {expected}")

                # Средний %
                if stat.total_questions > 0:
                    expected_avg = int((stat.total_correct / stat.total_questions) * 100)
                    if stat.monthly_avg_percent == expected_avg:
                        ok(f"{name}: avg={stat.monthly_avg_percent}% (корректно)")
                    else:
                        fail(f"{name}: avg={stat.monthly_avg_percent}% ≠ {expected_avg}%")

                # Сверка с QuizSession
                real_q = await session.execute(
                    select(func.count()).select_from(QuizSession).where(
                        QuizSession.user_id == stat.user_id,
                        QuizSession.completed_at.isnot(None),
                        QuizSession.started_at >= season.start_date,
                        QuizSession.started_at <= datetime.combine(season.end_date, datetime.max.time())
                    )
                )
                real_count = real_q.scalar() or 0
                if stat.monthly_quizzes == real_count:
                    ok(f"{name}: викторин={stat.monthly_quizzes} (совпадает)")
                else:
                    warn(f"{name}: stats={stat.monthly_quizzes} vs real={real_count}")

                # Events идемпотентность
                ev = await session.execute(
                    select(func.count()).select_from(MonthlyQuizEvent).where(
                        MonthlyQuizEvent.user_id == stat.user_id,
                        MonthlyQuizEvent.season_id == season.id
                    )
                )
                ev_count = ev.scalar() or 0
                if ev_count == stat.monthly_quizzes:
                    ok(f"{name}: events={ev_count} (идемпотентность ОК)")
                else:
                    warn(f"{name}: events={ev_count} vs quizzes={stat.monthly_quizzes}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  4. СЕРВИСНЫЕ ФУНКЦИИ")
        print("=" * 55)

        # get_user_monthly_rank — полнота данных
        from app.services.monthly_leaderboard_service import get_user_monthly_rank
        users_result = await session.execute(select(User))
        all_users = users_result.scalars().all()

        if season:
            for user in all_users:
                rank_data = await get_user_monthly_rank(user.id, session, season_id=season.id)
                if rank_data is None:
                    info(f"{user.display_name}: нет данных за сезон (не играл)")
                    continue

                required = ['rank', 'total_users', 'monthly_score', 'monthly_quizzes',
                           'monthly_words', 'monthly_streak', 'monthly_avg_percent']
                missing = [f for f in required if f not in rank_data]
                if missing:
                    fail(f"{user.display_name}: get_user_monthly_rank — нет полей: {missing}")
                else:
                    ok(f"{user.display_name}: get_user_monthly_rank — все 7 полей на месте")

        # get_lifetime_leaderboard — возвращает list
        from app.services.monthly_leaderboard_service import get_lifetime_leaderboard
        lb = await get_lifetime_leaderboard(session, limit=10)
        if lb is None:
            fail("get_lifetime_leaderboard → None (нет return!)")
        elif isinstance(lb, list):
            ok(f"get_lifetime_leaderboard → list ({len(lb)} записей)")
        else:
            fail(f"get_lifetime_leaderboard → {type(lb)}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  5. DISPLAY NAME")
        print("=" * 55)

        for user in all_users:
            dn = user.display_name
            if user.first_name and dn.startswith(user.first_name):
                ok(f"{user.id}: '{dn}' (имя приоритет)")
            elif dn.startswith("@"):
                warn(f"{user.id}: '{dn}' (username вместо имени)")
            elif dn.startswith("User "):
                warn(f"{user.id}: '{dn}' (нет данных)")
            else:
                ok(f"{user.id}: '{dn}'")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  6. МОНЕТАРНАЯ AWARD — МОДЕЛЬ")
        print("=" * 55)

        if hasattr(MonthlyAward, 'emoji'):
            fail("MonthlyAward имеет атрибут .emoji — это вызовет crash!")
        else:
            ok("MonthlyAward НЕ имеет .emoji (правильно)")

        # Проверяем _award_type_to_emoji
        try:
            from app.services.monthly_leaderboard_service import _award_type_to_emoji
            assert _award_type_to_emoji("gold") == "🥇"
            assert _award_type_to_emoji("silver") == "🥈"
            assert _award_type_to_emoji("bronze") == "🥉"
            assert _award_type_to_emoji("top10") == "🏅"
            ok("_award_type_to_emoji работает корректно")
        except ImportError:
            fail("_award_type_to_emoji не найдена в сервисе!")
        except AssertionError:
            fail("_award_type_to_emoji возвращает неверные значения!")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  7. НАПОМИНАНИЯ")
        print("=" * 55)

        notif_users = [u for u in all_users if u.notifications_enabled]
        info(f"Юзеров с напоминаниями: {len(notif_users)}")

        for user in notif_users:
            issues = []

            if not user.timezone:
                issues.append("нет timezone")
            if not user.notification_time or ':' not in user.notification_time:
                issues.append(f"кривое время: '{user.notification_time}'")
            if not user.notification_days:
                issues.append("нет дней")

            # Валидация времени
            if user.notification_time and ':' in user.notification_time:
                try:
                    parts = user.notification_time.split(':')
                    h, m = int(parts[0]), int(parts[1])
                    if not (0 <= h <= 23 and 0 <= m <= 59):
                        issues.append(f"время вне диапазона: {h}:{m}")
                except:
                    issues.append(f"не парсится время: '{user.notification_time}'")

            # Валидация timezone
            if user.timezone:
                try:
                    ZoneInfo(user.timezone)
                except:
                    issues.append(f"невалидный timezone: '{user.timezone}'")

            if issues:
                warn(f"{user.display_name}: {', '.join(issues)}")
            else:
                ok(f"{user.display_name}: tz={user.timezone}, time={user.notification_time}, "
                   f"days={user.notification_days}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  8. LIFETIME & WINS")
        print("=" * 55)

        for user in all_users:
            if user.lifetime_score < 0:
                fail(f"{user.display_name}: lifetime_score={user.lifetime_score} (отрицательный!)")
            if user.total_monthly_wins < 0:
                fail(f"{user.display_name}: total_monthly_wins={user.total_monthly_wins} (отрицательный!)")

        finalized_count = len(finalized)
        for user in all_users:
            if user.total_monthly_wins > finalized_count:
                fail(f"{user.display_name}: wins={user.total_monthly_wins} > завершённых сезонов={finalized_count}")

        info(f"Юзеров с lifetime > 0: {len([u for u in all_users if u.lifetime_score > 0])}")
        info(f"Юзеров с wins > 0: {len([u for u in all_users if u.total_monthly_wins > 0])}")
        ok(f"Завершённых сезонов: {finalized_count}")

        # ==================================================================
        print("\n" + "=" * 55)
        print("  9. CALLBACK-МАРШРУТЫ (ПРОВЕРКА КОДА)")
        print("=" * 55)

        # Проверяем что callback'и не конфликтуют
        try:
            from app.bot.handlers.leaderboard.monthly import router as monthly_router
            from app.bot.handlers.leaderboard.alltime import router as alltime_router

            monthly_callbacks = set()
            alltime_callbacks = set()

            for observer in monthly_router.callback_query.handlers:
                for filt in observer.filters:
                    if hasattr(filt, 'text'):
                        monthly_callbacks.add(str(filt.text))

            ok("monthly.py router импортируется")
            ok("alltime.py router импортируется")

            # Проверяем что rating_monthly и rating_alltime существуют
            import inspect
            monthly_src = inspect.getsource(monthly_router.callback_query.handlers[0].callback) if monthly_router.callback_query.handlers else ""

            # Простая проверка наличия нужных callback_data в файлах
            from app.bot.handlers.leaderboard import monthly as monthly_mod
            from app.bot.handlers.leaderboard import alltime as alltime_mod
            monthly_source = inspect.getsource(monthly_mod)
            alltime_source = inspect.getsource(alltime_mod)

            for cb in ["rating_monthly", "rating_alltime", "show_my_rating", "leaderboard_table_monthly"]:
                if cb in monthly_source:
                    ok(f"monthly.py: callback '{cb}' найден")

            for cb in ["rating_alltime", "leaderboard_table_alltime"]:
                if cb in alltime_source:
                    ok(f"alltime.py: callback '{cb}' найден")

            # Проверяем что старые callback'и НЕ используются
            for old_cb in ["leaderboard_monthly", "leaderboard_alltime", "leaderboard_lifetime"]:
                if old_cb in monthly_source:
                    warn(f"monthly.py: старый callback '{old_cb}' всё ещё присутствует")
                if old_cb in alltime_source:
                    warn(f"alltime.py: старый callback '{old_cb}' всё ещё присутствует")

        except Exception as e:
            warn(f"Не удалось проверить callback'и: {e}")

    # ==================================================================
    print("\n" + "=" * 55)
    print("  ИТОГИ")
    print("=" * 55)

    total_checks = len(errors) + len(warnings)

    if not errors and not warnings:
        print(f"\n{OK} ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Система работает корректно.\n")
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