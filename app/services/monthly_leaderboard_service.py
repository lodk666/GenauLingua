"""
Сервис для месячной системы рейтинга

Файл: app/services/monthly_leaderboard_service.py
"""

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import (
    User, MonthlySeason, MonthlyStats, MonthlyQuizEvent, MonthlyAward, WinStreak,
    QuizSession, UserWord
)
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
import calendar

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# УПРАВЛЕНИЕ СЕЗОНАМИ
# ============================================================================

async def get_current_season(session: AsyncSession) -> Optional[MonthlySeason]:
    """Получить текущий активный сезон"""
    result = await session.execute(
        select(MonthlySeason)
        .where(MonthlySeason.is_active == True)
        .order_by(MonthlySeason.created_at.desc())
    )
    return result.scalar_one_or_none()


async def create_new_season(year: int, month: int, session: AsyncSession) -> MonthlySeason:
    """Создать новый месячный сезон"""
    existing = await session.execute(
        select(MonthlySeason).where(
            MonthlySeason.year == year,
            MonthlySeason.month == month
        )
    )
    if existing.scalar_one_or_none():
        logger.warning(f"Сезон {month}/{year} уже существует")
        return existing.scalar_one_or_none()

    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    prev_seasons = await session.execute(
        select(MonthlySeason).where(MonthlySeason.is_active == True)
    )
    for prev in prev_seasons.scalars():
        prev.is_active = False

    season = MonthlySeason(
        year=year,
        month=month,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        winners_finalized=False
    )
    session.add(season)
    await session.commit()
    await session.refresh(season)

    logger.info(f"Создан новый сезон: {month}/{year} (id={season.id})")
    return season


async def get_or_create_current_season(session: AsyncSession) -> MonthlySeason:
    """Получить текущий сезон или создать если нет"""
    season = await get_current_season(session)
    if not season:
        today = date.today()
        season = await create_new_season(today.year, today.month, session)
    return season


# ============================================================================
# ОБНОВЛЕНИЕ МЕСЯЧНОЙ СТАТИСТИКИ
# ============================================================================

async def _recalc_monthly_stats_full(user_id: int, session: AsyncSession) -> MonthlyStats:
    """Полный пересчёт (медленно). Оставлено для отладки/миграций."""
    season = await get_or_create_current_season(session)

    result = await session.execute(
        select(MonthlyStats).where(
            MonthlyStats.user_id == user_id,
            MonthlyStats.season_id == season.id
        )
    )
    monthly_stat = result.scalar_one_or_none()
    if not monthly_stat:
        monthly_stat = MonthlyStats(user_id=user_id, season_id=season.id)
        session.add(monthly_stat)

    quizzes_result = await session.execute(
        select(QuizSession).where(
            QuizSession.user_id == user_id,
            QuizSession.completed_at.isnot(None),
            QuizSession.started_at >= season.start_date,
            QuizSession.started_at <= datetime.combine(season.end_date, datetime.max.time())
        )
    )
    month_quizzes = quizzes_result.scalars().all()

    monthly_stat.monthly_quizzes = len(month_quizzes)
    monthly_stat.monthly_reverse = len([
        q for q in month_quizzes
        if q.translation_mode.value in ("ru_to_de", "uk_to_de")
    ])

    total_correct = sum(q.correct_answers for q in month_quizzes)
    total_questions = sum(q.total_questions for q in month_quizzes)
    monthly_stat.total_correct = total_correct
    monthly_stat.total_questions = total_questions
    monthly_stat.monthly_avg_percent = int((total_correct / total_questions * 100) if total_questions > 0 else 0)

    user_words_result = await session.execute(
        select(UserWord).where(
            UserWord.user_id == user_id,
            UserWord.learned == True,
            UserWord.last_seen_at >= datetime.combine(season.start_date, datetime.min.time()),
            UserWord.last_seen_at <= datetime.combine(season.end_date, datetime.max.time())
        )
    )
    monthly_stat.monthly_words = len(user_words_result.scalars().all())

    monthly_stat.monthly_streak = await calculate_monthly_streak(user_id, season, month_quizzes, session)

    if month_quizzes:
        last_quiz = max((q.completed_at or q.started_at) for q in month_quizzes)
        monthly_stat.last_quiz_date = (last_quiz.date() if last_quiz else None)

    monthly_stat.monthly_score = monthly_stat.calculate_monthly_score()
    monthly_stat.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(monthly_stat)
    return monthly_stat


async def update_monthly_stats(
        user_id: int,
        session: AsyncSession,
        quiz_session_id: Optional[int] = None,
        force_full_recalc: bool = False
) -> MonthlyStats:
    """
    Инкрементально обновить статистику пользователя за текущий месяц.
    Идемпотентно через monthly_quiz_events.
    """
    if force_full_recalc or quiz_session_id is None:
        return await _recalc_monthly_stats_full(user_id, session)

    season = await get_or_create_current_season(session)

    quiz = await session.get(QuizSession, quiz_session_id)
    if not quiz or quiz.user_id != user_id:
        return await _recalc_monthly_stats_full(user_id, session)

    if quiz.completed_at is None:
        return await _recalc_monthly_stats_full(user_id, session)

    quiz_dt = quiz.completed_at or quiz.started_at
    quiz_date = quiz_dt.date()
    if not (season.start_date <= quiz_date <= season.end_date):
        return await _recalc_monthly_stats_full(user_id, session)

    stat_result = await session.execute(
        select(MonthlyStats).where(
            MonthlyStats.user_id == user_id,
            MonthlyStats.season_id == season.id
        )
    )
    monthly_stat = stat_result.scalar_one_or_none()
    if not monthly_stat:
        monthly_stat = MonthlyStats(user_id=user_id, season_id=season.id)
        session.add(monthly_stat)
        await session.flush()

    # Идемпотентность
    event_result = await session.execute(
        select(MonthlyQuizEvent).where(MonthlyQuizEvent.quiz_session_id == quiz_session_id)
    )
    if event_result.scalar_one_or_none():
        return monthly_stat

    session.add(MonthlyQuizEvent(
        quiz_session_id=quiz_session_id,
        user_id=user_id,
        season_id=season.id
    ))

    monthly_stat.monthly_quizzes = (monthly_stat.monthly_quizzes or 0) + 1

    if quiz.translation_mode.value in ("ru_to_de", "uk_to_de"):
        monthly_stat.monthly_reverse = (monthly_stat.monthly_reverse or 0) + 1

    monthly_stat.total_correct = (monthly_stat.total_correct or 0) + (quiz.correct_answers or 0)
    monthly_stat.total_questions = (monthly_stat.total_questions or 0) + (quiz.total_questions or 0)
    if monthly_stat.total_questions > 0:
        monthly_stat.monthly_avg_percent = int((monthly_stat.total_correct / monthly_stat.total_questions) * 100)
    else:
        monthly_stat.monthly_avg_percent = 0

    last_date = monthly_stat.last_quiz_date
    if last_date == quiz_date:
        pass
    elif last_date == (quiz_date - timedelta(days=1)):
        monthly_stat.monthly_streak = (monthly_stat.monthly_streak or 0) + 1
    else:
        monthly_stat.monthly_streak = 1
    monthly_stat.last_quiz_date = quiz_date

    if (monthly_stat.monthly_quizzes % 10 == 0) or (monthly_stat.monthly_words == 0):
        user_words_result = await session.execute(
            select(func.count()).select_from(UserWord).where(
                UserWord.user_id == user_id,
                UserWord.learned == True,
                UserWord.last_seen_at >= datetime.combine(season.start_date, datetime.min.time()),
                UserWord.last_seen_at <= datetime.combine(season.end_date, datetime.max.time())
            )
        )
        monthly_stat.monthly_words = int(user_words_result.scalar() or 0)

    monthly_stat.monthly_score = monthly_stat.calculate_monthly_score()
    monthly_stat.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(monthly_stat)
    return monthly_stat


async def calculate_monthly_streak(
        user_id: int,
        season: MonthlySeason,
        month_quizzes: list,
        session: AsyncSession
) -> int:
    """Подсчитать стрик в рамках текущего месяца"""
    if not month_quizzes:
        return 0

    days_with_quizzes = set()
    for quiz in month_quizzes:
        quiz_date = quiz.started_at.date()
        days_with_quizzes.add(quiz_date)

    if not days_with_quizzes:
        return 0

    current_date = min(date.today(), season.end_date)
    streak = 0

    while current_date >= season.start_date:
        if current_date in days_with_quizzes:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return streak


# ============================================================================
# УТИЛИТА: тип награды → эмодзи
# ============================================================================

def _award_type_to_emoji(award_type: str) -> str:
    """Конвертировать тип награды в эмодзи"""
    mapping = {
        "gold": "🥇",
        "silver": "🥈",
        "bronze": "🥉",
        "top10": "🏅",
    }
    return mapping.get(award_type, "🏅")


# ============================================================================
# ПОЛУЧЕНИЕ МЕСЯЧНОГО РЕЙТИНГА (для таблицы лидеров)
# ============================================================================

async def get_monthly_leaderboard(
        session: AsyncSession,
        season_id: Optional[int] = None,
        limit: int = 50
) -> List[Dict]:
    """Получить месячный рейтинг — список для таблицы лидеров"""
    if season_id is None:
        season = await get_current_season(session)
        if not season:
            return []
        season_id = season.id

    result = await session.execute(
        select(MonthlyStats, User)
        .join(User, MonthlyStats.user_id == User.id)
        .where(MonthlyStats.season_id == season_id)
        .order_by(MonthlyStats.monthly_score.desc())
        .limit(limit)
    )

    stats_users = result.all()

    leaderboard = []
    for rank, (stat, user) in enumerate(stats_users, 1):
        awards_result = await session.execute(
            select(MonthlyAward)
            .where(MonthlyAward.user_id == user.id)
            .order_by(MonthlyAward.created_at.desc())
            .limit(5)
        )
        user_awards = awards_result.scalars().all()

        win_streak_result = await session.execute(
            select(WinStreak).where(WinStreak.user_id == user.id)
        )
        win_streak = win_streak_result.scalar_one_or_none()

        leaderboard.append({
            'rank': rank,
            'user_id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'monthly_score': stat.monthly_score,
            'monthly_streak': stat.monthly_streak,
            'monthly_quizzes': stat.monthly_quizzes,
            'monthly_words': stat.monthly_words,
            'monthly_reverse': stat.monthly_reverse,
            'monthly_avg_percent': stat.monthly_avg_percent,
            'awards': [
                {
                    'type': a.award_type,
                    'emoji': _award_type_to_emoji(a.award_type),
                    'season_id': a.season_id
                }
                for a in user_awards
            ],
            'win_streak': {
                'current': win_streak.current_streak if win_streak else 0,
                'emoji': win_streak.streak_emoji if win_streak else '',
                'title': win_streak.streak_title if win_streak else ''
            } if win_streak else None
        })

    return leaderboard


# ============================================================================
# ПОЗИЦИЯ ПОЛЬЗОВАТЕЛЯ + ВСЕ ДЕТАЛИ (FIX: теперь возвращает полные данные)
# ============================================================================

async def get_user_monthly_rank(
        user_id: int,
        session: AsyncSession,
        season_id: Optional[int] = None
) -> Optional[Dict]:
    """
    Получить позицию пользователя + все его месячные данные.
    Не зависит от leaderboard limit — всегда точные данные.
    """
    if season_id is None:
        season = await get_current_season(session)
        if not season:
            return None
        season_id = season.id

    # Стата пользователя
    stat_result = await session.execute(
        select(MonthlyStats).where(
            MonthlyStats.user_id == user_id,
            MonthlyStats.season_id == season_id
        )
    )
    stat = stat_result.scalar_one_or_none()
    if not stat:
        return None

    # Всего участников
    total_result = await session.execute(
        select(func.count()).select_from(MonthlyStats).where(MonthlyStats.season_id == season_id)
    )
    total_users = int(total_result.scalar() or 0)
    if total_users == 0:
        return None

    # Ранг
    higher_result = await session.execute(
        select(func.count()).select_from(MonthlyStats).where(
            MonthlyStats.season_id == season_id,
            MonthlyStats.monthly_score > stat.monthly_score
        )
    )
    rank = int(higher_result.scalar() or 0) + 1

    return {
        'rank': rank,
        'total_users': total_users,
        'monthly_score': stat.monthly_score,
        'monthly_quizzes': stat.monthly_quizzes,
        'monthly_words': stat.monthly_words,
        'monthly_streak': stat.monthly_streak,
        'monthly_avg_percent': stat.monthly_avg_percent,
        'monthly_reverse': stat.monthly_reverse,
    }


# ============================================================================
# ПОДВЕДЕНИЕ ИТОГОВ МЕСЯЦА
# ============================================================================

async def finalize_season(season_id: int, session: AsyncSession):
    """Подвести итоги месяца"""
    season = await session.get(MonthlySeason, season_id)
    if not season:
        logger.error(f"Сезон {season_id} не найден")
        return

    if season.winners_finalized:
        logger.warning(f"Сезон {season_id} уже завершён")
        return

    results = await session.execute(
        select(MonthlyStats)
        .where(MonthlyStats.season_id == season_id)
        .order_by(MonthlyStats.monthly_score.desc())
    )
    results = results.scalars().all()

    logger.info(f"Подводим итоги сезона {season.month}/{season.year}")
    logger.info(f"Участников: {len(results)}")

    for rank, stat in enumerate(results, 1):
        stat.final_rank = rank

    awards_config = {
        1: ('gold', 100),
        2: ('silver', 50),
        3: ('bronze', 25),
    }

    for rank, stat in enumerate(results[:10], 1):
        user = await session.get(User, stat.user_id)

        if rank <= 3:
            award_type, lifetime_bonus = awards_config[rank]
        else:
            award_type, lifetime_bonus = ('top10', 10)

        award = MonthlyAward(
            user_id=stat.user_id,
            season_id=season_id,
            rank=rank,
            award_type=award_type,
            lifetime_bonus=lifetime_bonus
        )
        session.add(award)

        user.lifetime_score += lifetime_bonus

        if rank == 1:
            user.total_monthly_wins += 1
            await update_win_streak(stat.user_id, season_id, session)

        logger.info(f"#{rank} - {user.display_name} - {stat.monthly_score} баллов - {award_type}")

    season.winners_finalized = True
    season.is_active = False

    await session.commit()
    logger.info(f"Сезон {season.month}/{season.year} завершён")


async def update_win_streak(user_id: int, season_id: int, session: AsyncSession):
    """Обновить серию побед пользователя"""
    result = await session.execute(
        select(WinStreak).where(WinStreak.user_id == user_id)
    )
    win_streak = result.scalar_one_or_none()

    if not win_streak:
        win_streak = WinStreak(user_id=user_id)
        session.add(win_streak)

    season = await session.get(MonthlySeason, season_id)

    prev_month = season.month - 1 if season.month > 1 else 12
    prev_year = season.year if season.month > 1 else season.year - 1

    prev_season_result = await session.execute(
        select(MonthlySeason).where(
            MonthlySeason.year == prev_year,
            MonthlySeason.month == prev_month
        )
    )
    prev_season = prev_season_result.scalar_one_or_none()

    if prev_season and win_streak.last_win_season == prev_season.id:
        win_streak.current_streak += 1
    else:
        win_streak.current_streak = 1

    if win_streak.current_streak > win_streak.best_streak:
        win_streak.best_streak = win_streak.current_streak

    win_streak.total_wins += 1
    win_streak.last_win_season = season_id
    win_streak.updated_at = datetime.utcnow()

    await session.commit()
    logger.info(f"Серия побед: {win_streak.current_streak}")


# ============================================================================
# LIFETIME РЕЙТИНГ
# ============================================================================

async def get_lifetime_leaderboard(
        session: AsyncSession,
        limit: int = 50
) -> List[Dict]:
    """Получить lifetime рейтинг"""
    result = await session.execute(
        select(User, WinStreak)
        .outerjoin(WinStreak, User.id == WinStreak.user_id)
        .where(User.quizzes_passed > 0)
        .order_by(User.lifetime_score.desc())
        .limit(limit)
    )

    users_streaks = result.all()

    leaderboard = []
    for rank, (user, win_streak) in enumerate(users_streaks, 1):
        awards_result = await session.execute(
            select(MonthlyAward)
            .where(MonthlyAward.user_id == user.id)
            .order_by(MonthlyAward.created_at.desc())
        )
        awards = awards_result.scalars().all()

        leaderboard.append({
            'rank': rank,
            'user_id': user.id,
            'display_name': user.display_name,
            'lifetime_score': user.lifetime_score,
            'total_wins': user.total_monthly_wins,
            'words_learned': user.words_learned,
            'best_streak_days': user.best_streak_days,
            'awards_count': len(awards),
            'win_streak': {
                'current': win_streak.current_streak if win_streak else 0,
                'best': win_streak.best_streak if win_streak else 0,
                'total': win_streak.total_wins if win_streak else 0
            } if win_streak else None
        })

    return leaderboard