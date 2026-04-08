"""
Админ-панель для GenauLingua Bot (v2 — исправлено)
Команды доступны только для администратора
"""

import csv
import io
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct, case, desc, or_
from datetime import datetime, timedelta, date
from app.database.models import User, QuizSession, QuizQuestion, UserWord, Word, TranslationReport
from app.services.quiz_service import get_user_progress_stats, get_user_progress_stats_all_levels
from app.config import settings

import logging

logger = logging.getLogger(__name__)

router = Router()

ADMIN_USER_ID = settings.ADMIN_USER


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_USER_ID


def _display_name(user: User) -> str:
    """Имя для отображения в админке"""
    if user.first_name:
        return user.first_name
    elif user.username:
        return f"@{user.username}"
    return f"User {user.id}"


def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 Аналитика", callback_data="admin:analytics"),
            InlineKeyboardButton(text="👥 Когорты", callback_data="admin:cohorts")
        ],
        [
            InlineKeyboardButton(text="⚠️ Churn", callback_data="admin:churn"),
            InlineKeyboardButton(text="📤 Экспорт", callback_data="admin:export")
        ],
        [
            InlineKeyboardButton(text="👤 Топ юзеры", callback_data="admin:top_users"),
            InlineKeyboardButton(text="📊 Детали", callback_data="admin:detailed")
        ],
        [
            InlineKeyboardButton(text="📝 Репорты", callback_data="admin:reports")
        ]
    ])
    return keyboard


async def _get_main_stats(session: AsyncSession) -> str:
    """Собрать базовую статистику для главной панели"""
    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()

    active_24h_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(User.last_active_date >= date.today())
    )
    active_24h = active_24h_result.scalar()

    week_ago = date.today() - timedelta(days=7)
    active_7d_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(User.last_active_date >= week_ago)
    )
    active_7d = active_7d_result.scalar()

    total_quizzes_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(QuizSession.completed_at.isnot(None))
    )
    total_quizzes = total_quizzes_result.scalar()

    day_ago = datetime.utcnow() - timedelta(hours=24)
    quizzes_24h_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(
            QuizSession.completed_at.isnot(None),
            QuizSession.completed_at >= day_ago
        )
    )
    quizzes_24h = quizzes_24h_result.scalar()

    notif_sessions_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(QuizSession.start_source == 'notification', QuizSession.completed_at.isnot(None))
    )
    notif_sessions = notif_sessions_result.scalar() or 0

    active_ever_result = await session.execute(
        select(func.count(distinct(QuizSession.user_id)))
        .select_from(QuizSession)
        .where(QuizSession.completed_at.isnot(None))
    )
    active_ever = active_ever_result.scalar() or 0

    text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"

    text += "📊 <b>Пользователи:</b>\n"
    text += f"├─ Всего: <b>{total_users}</b>\n"
    text += f"├─ Хотя бы 1 викторина: <b>{active_ever}</b>\n"
    text += f"├─ 🟢 Сегодня: <b>{active_24h}</b>\n"
    text += f"└─ 📅 За 7 дней: <b>{active_7d}</b>\n\n"

    text += "🏆 <b>Викторины:</b>\n"
    text += f"├─ Всего: <b>{total_quizzes}</b>\n"
    text += f"├─ За 24ч: <b>{quizzes_24h}</b>\n"
    text += f"└─ Из напоминаний: <b>{notif_sessions}</b>\n\n"

    text += "💡 Выберите раздел:\n"
    return text


# ============================================================================
# ГЛАВНАЯ ПАНЕЛЬ
# ============================================================================

@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    try:
        await message.delete()
    except:
        pass

    text = await _get_main_stats(session)
    await message.answer(text, reply_markup=get_admin_keyboard())


# ============================================================================
# АНАЛИТИКА
# ============================================================================

@router.callback_query(F.data == "admin:analytics")
async def admin_analytics(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar() or 1

    day1_retention_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .join(QuizSession, User.id == QuizSession.user_id)
        .where(
            func.date(QuizSession.completed_at) > func.date(User.created_at)
        )
    )
    day1_returned = day1_retention_result.scalar() or 0
    day1_retention = (day1_returned / total_users * 100) if total_users > 0 else 0

    week_ago = date.today() - timedelta(days=7)
    users_week_ago_result = await session.execute(
        select(func.count()).select_from(User).where(User.created_at <= datetime.combine(week_ago, datetime.min.time()))
    )
    users_week_ago = users_week_ago_result.scalar() or 1

    day7_active_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(
            User.created_at <= datetime.combine(week_ago, datetime.min.time()),
            User.last_quiz_date >= week_ago
        )
    )
    day7_active = day7_active_result.scalar() or 0
    day7_retention = (day7_active / users_week_ago * 100) if users_week_ago > 0 else 0

    sources_result = await session.execute(
        select(QuizSession.start_source, func.count())
        .select_from(QuizSession)
        .where(QuizSession.start_source.isnot(None), QuizSession.completed_at.isnot(None))
        .group_by(QuizSession.start_source)
    )
    sources = sources_result.all()
    total_source_quizzes = sum(count for _, count in sources)

    speed_dist_result = await session.execute(
        select(
            func.count(case((QuizQuestion.response_time_seconds <= 2, 1))).label('fast'),
            func.count(case((and_(QuizQuestion.response_time_seconds > 2, QuizQuestion.response_time_seconds <= 5), 1))).label('normal'),
            func.count(case((and_(QuizQuestion.response_time_seconds > 5, QuizQuestion.response_time_seconds <= 10), 1))).label('slow'),
            func.count(case((QuizQuestion.response_time_seconds > 10, 1))).label('very_slow')
        )
        .select_from(QuizQuestion)
        .where(QuizQuestion.response_time_seconds.isnot(None))
    )
    speed_dist = speed_dist_result.first()
    total_answers = sum(speed_dist) if speed_dist else 0

    exit_points_result = await session.execute(
        select(
            func.count(case((QuizSession.exit_at_question <= 5, 1))).label('q1_5'),
            func.count(case((and_(QuizSession.exit_at_question > 5, QuizSession.exit_at_question <= 10), 1))).label('q6_10'),
            func.count(case((and_(QuizSession.exit_at_question > 10, QuizSession.exit_at_question <= 15), 1))).label('q11_15'),
            func.count(case((and_(QuizSession.exit_at_question > 15, QuizSession.exit_at_question <= 20), 1))).label('q16_20')
        )
        .select_from(QuizSession)
        .where(QuizSession.exit_reason == 'abandoned')
    )
    exit_points = exit_points_result.first()

    difficult_words_result = await session.execute(
        select(
            Word.word_de,
            Word.article,
            func.avg(QuizQuestion.response_time_seconds).label('avg_time')
        )
        .select_from(Word)
        .join(QuizQuestion, Word.id == QuizQuestion.word_id)
        .where(QuizQuestion.response_time_seconds.isnot(None))
        .group_by(Word.id, Word.word_de, Word.article)
        .order_by(desc('avg_time'))
        .limit(5)
    )
    difficult_words = difficult_words_result.all()

    text = "📈 <b>АНАЛИТИКА</b>\n\n"

    text += "🔥 <b>Retention (удержание):</b>\n"
    text += f"├─ Day 1: <b>{day1_retention:.1f}%</b> ({day1_returned}/{total_users})\n"
    text += f"│  └─ <i>вернулись на следующий день</i>\n"
    text += f"├─ Day 7: <b>{day7_retention:.1f}%</b> ({day7_active}/{users_week_ago})\n"
    text += f"│  └─ <i>активны через неделю после регистрации</i>\n\n"

    if sources:
        text += "📊 <b>Откуда начинают викторины:</b>\n"
        for source, count in sources:
            percentage = (count / total_source_quizzes * 100) if total_source_quizzes > 0 else 0
            emoji = "🔔" if source == 'notification' else "📚" if source == 'menu' else "🔄"
            label = "напоминание" if source == 'notification' else "меню" if source == 'menu' else source
            text += f"├─ {emoji} {label}: <b>{count}</b> ({percentage:.0f}%)\n"
        text += "\n"
    else:
        text += "📊 <b>Источники викторин:</b> нет данных\n\n"

    if total_answers > 0:
        text += "⏱️ <b>Скорость ответа:</b>\n"
        text += f"├─ 0-2 сек: <b>{speed_dist[0]/total_answers*100:.0f}%</b> (знает)\n"
        text += f"├─ 3-5 сек: <b>{speed_dist[1]/total_answers*100:.0f}%</b> (думает)\n"
        text += f"├─ 6-10 сек: <b>{speed_dist[2]/total_answers*100:.0f}%</b> (сложно)\n"
        text += f"└─ 10+ сек: <b>{speed_dist[3]/total_answers*100:.0f}%</b> (угадывает)\n\n"

    if exit_points and any(exit_points):
        text += "🚪 <b>Где бросают викторину:</b>\n"
        text += f"├─ Вопросы 1-5: <b>{exit_points[0]}</b>\n"
        text += f"├─ Вопросы 6-10: <b>{exit_points[1]}</b>\n"
        text += f"├─ Вопросы 11-15: <b>{exit_points[2]}</b>\n"
        text += f"└─ Вопросы 16-20: <b>{exit_points[3]}</b>\n\n"

    if difficult_words:
        text += "🎯 <b>Самые сложные слова (по времени):</b>\n"
        for i, (word_de, article, avg_time) in enumerate(difficult_words, 1):
            full_word = f"{article} {word_de}" if article and article != "-" else word_de
            text += f"{i}. <b>{full_word}</b> — ср. {avg_time:.1f} сек\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# КОГОРТЫ
# ============================================================================

@router.callback_query(F.data == "admin:cohorts")
async def admin_cohorts(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    current_month = date.today().replace(day=1)
    prev_month = (current_month - timedelta(days=1)).replace(day=1)

    current_month_users_result = await session.execute(
        select(func.count()).select_from(User).where(User.created_at >= datetime.combine(current_month, datetime.min.time()))
    )
    current_month_users = current_month_users_result.scalar() or 0

    current_month_active_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(
            User.created_at >= datetime.combine(current_month, datetime.min.time()),
            User.last_quiz_date.isnot(None)
        )
    )
    current_month_active = current_month_active_result.scalar() or 0

    prev_month_users_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.created_at >= datetime.combine(prev_month, datetime.min.time()),
            User.created_at < datetime.combine(current_month, datetime.min.time())
        )
    )
    prev_month_users = prev_month_users_result.scalar() or 0

    prev_month_active_result = await session.execute(
        select(func.count(distinct(User.id)))
        .select_from(User)
        .where(
            User.created_at >= datetime.combine(prev_month, datetime.min.time()),
            User.created_at < datetime.combine(current_month, datetime.min.time()),
            User.last_quiz_date.isnot(None)
        )
    )
    prev_month_active = prev_month_active_result.scalar() or 0

    levels_stats_result = await session.execute(
        select(
            User.level,
            func.count(distinct(User.id)).label('users'),
            func.avg(User.quizzes_passed).label('avg_quizzes')
        )
        .select_from(User)
        .where(User.level.isnot(None))
        .group_by(User.level)
    )
    levels_stats = levels_stats_result.all()

    langs_result = await session.execute(
        select(User.interface_language, func.count())
        .select_from(User)
        .group_by(User.interface_language)
    )
    langs = langs_result.all()
    total_lang_users = sum(count for _, count in langs)

    lang_names = {
        'ru': '🏴 Русский',
        'uk': '🇺🇦 Українська',
        'en': '🇬🇧 English',
        'tr': '🇹🇷 Türkçe',
        None: '❓ Не выбран'
    }

    text = "👥 <b>КОГОРТЫ ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"

    text += "📅 <b>По месяцам регистрации:</b>\n"
    text += f"├─ {prev_month.strftime('%B %Y')}: <b>{prev_month_users}</b> зарег.\n"
    if prev_month_users > 0:
        text += f"│  └─ Играли: {prev_month_active} ({prev_month_active/prev_month_users*100:.0f}%)\n"
    text += f"└─ {current_month.strftime('%B %Y')}: <b>{current_month_users}</b> зарег.\n"
    if current_month_users > 0:
        text += f"   └─ Играли: {current_month_active} ({current_month_active/current_month_users*100:.0f}%)\n"
    text += "\n"

    text += "📚 <b>По уровням:</b>\n"
    for level, users, avg_quizzes in levels_stats:
        if level:
            avg_quiz_val = avg_quizzes or 0
            text += f"├─ {level.value}: <b>{users}</b> юзеров | Ср. {avg_quiz_val:.1f} викторин\n"
    text += "\n"

    text += "🌍 <b>По языкам интерфейса:</b>\n"
    for lang, count in langs:
        lang_name = lang_names.get(lang, f"❓ {lang}")
        percentage = (count / total_lang_users * 100) if total_lang_users > 0 else 0
        text += f"├─ {lang_name}: <b>{count}</b> ({percentage:.0f}%)\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# CHURN
# ============================================================================

@router.callback_query(F.data == "admin:churn")
async def admin_churn(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    today = date.today()
    week_ago = today - timedelta(days=7)
    three_days_ago = today - timedelta(days=3)
    month_ago = today - timedelta(days=30)

    high_risk_result = await session.execute(
        select(User.first_name, User.username, User.last_quiz_date)
        .select_from(User)
        .where(
            User.last_quiz_date.isnot(None),
            User.last_quiz_date < week_ago
        )
        .order_by(User.last_quiz_date.asc())
        .limit(10)
    )
    high_risk = high_risk_result.all()

    high_risk_count_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.last_quiz_date.isnot(None),
            User.last_quiz_date < week_ago
        )
    )
    high_risk_count = high_risk_count_result.scalar() or 0

    medium_risk_count_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.last_quiz_date.isnot(None),
            User.last_quiz_date >= week_ago,
            User.last_quiz_date < three_days_ago
        )
    )
    medium_risk_count = medium_risk_count_result.scalar() or 0

    players_month_ago_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.created_at <= datetime.combine(month_ago, datetime.min.time()),
            User.last_quiz_date.isnot(None)
        )
    )
    players_month_ago = players_month_ago_result.scalar() or 0

    churned_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.created_at <= datetime.combine(month_ago, datetime.min.time()),
            User.last_quiz_date.isnot(None),
            User.last_quiz_date < month_ago
        )
    )
    churned = churned_result.scalar() or 0
    churn_rate = (churned / players_month_ago * 100) if players_month_ago > 0 else 0

    never_played_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(User.last_quiz_date.is_(None))
    )
    never_played = never_played_result.scalar() or 0

    text = "⚠️ <b>ОТТОК ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"

    text += f"🔴 <b>Высокий риск: {high_risk_count}</b>\n"
    text += f"<i>Играли, но не заходили 7+ дней</i>\n"
    if high_risk:
        for first_name, username, last_quiz in high_risk[:5]:
            days_ago = (today - last_quiz).days if last_quiz else 999
            name = first_name or (f"@{username}" if username else "—")
            text += f"├─ {name} — {days_ago} дн. назад\n"
        if high_risk_count > 5:
            text += f"└─ ... и ещё {high_risk_count - 5}\n"
    text += "\n"

    text += f"🟡 <b>Средний риск: {medium_risk_count}</b>\n"
    text += f"<i>Не заходили 3-7 дней</i>\n\n"

    text += f"📊 <b>Churn rate (30 дней): {churn_rate:.1f}%</b>\n"
    text += f"<i>Из игравших 30+ дней назад — сколько не вернулись</i>\n"
    if players_month_ago > 0:
        text += f"└─ Ушло: {churned} из {players_month_ago}\n\n"
    else:
        text += f"└─ Нет данных (нет игроков старше 30 дней)\n\n"

    text += f"👻 <b>Никогда не играли: {never_played}</b>\n"
    text += f"<i>Зарегистрировались, но ни разу не начали викторину</i>"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# ЭКСПОРТ
# ============================================================================

@router.callback_query(F.data == "admin:export")
async def admin_export_menu(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    text = "📤 <b>ЭКСПОРТ ДАННЫХ</b>\n\nВыберите формат:"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 CSV - Пользователи", callback_data="admin:export_users")],
        [InlineKeyboardButton(text="🏆 CSV - Викторины", callback_data="admin:export_quizzes")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin:export_users")
async def admin_export_users(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer("⏳ Генерирую файл...")

    result = await session.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'ID', 'Username', 'First Name', 'Created At', 'Level',
        'Streak Days', 'Quizzes Passed', 'Words Learned',
        'Last Quiz Date', 'Interface Language', 'Timezone',
        'Notifications Enabled'
    ])

    for user in users:
        writer.writerow([
            user.id,
            user.username or '',
            user.first_name or '',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
            user.level.value if user.level else '',
            user.streak_days or 0,
            user.quizzes_passed or 0,
            user.words_learned or 0,
            user.last_quiz_date.strftime('%Y-%m-%d') if user.last_quiz_date else '',
            user.interface_language or '',
            user.timezone or '',
            'Yes' if user.notifications_enabled else 'No'
        ])

    output.seek(0)
    csv_bytes = output.getvalue().encode('utf-8-sig')

    file = BufferedInputFile(csv_bytes, filename=f"users_{date.today()}.csv")
    await callback.message.answer_document(file, caption="📊 Экспорт пользователей")
    await callback.message.delete()


@router.callback_query(F.data == "admin:export_quizzes")
async def admin_export_quizzes(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer("⏳ Генерирую файл...")

    result = await session.execute(
        select(QuizSession, User.username, User.first_name)
        .join(User, QuizSession.user_id == User.id)
        .where(QuizSession.completed_at.isnot(None))
        .order_by(QuizSession.started_at.desc())
        .limit(1000)
    )
    quizzes = result.all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Session ID', 'User ID', 'Name', 'Started At', 'Completed At',
        'Level', 'Total Questions', 'Correct Answers', 'Score %',
        'Start Source', 'Exit Reason', 'Exit At Question'
    ])

    for quiz, username, first_name in quizzes:
        score = (quiz.correct_answers / quiz.total_questions * 100) if quiz.total_questions > 0 else 0
        name = first_name or username or ''
        writer.writerow([
            quiz.id,
            quiz.user_id,
            name,
            quiz.started_at.strftime('%Y-%m-%d %H:%M:%S'),
            quiz.completed_at.strftime('%Y-%m-%d %H:%M:%S') if quiz.completed_at else '',
            quiz.level.value if quiz.level else '',
            quiz.total_questions,
            quiz.correct_answers,
            f"{score:.1f}",
            quiz.start_source or '',
            quiz.exit_reason or '',
            quiz.exit_at_question
        ])

    output.seek(0)
    csv_bytes = output.getvalue().encode('utf-8-sig')

    file = BufferedInputFile(csv_bytes, filename=f"quizzes_{date.today()}.csv")
    await callback.message.answer_document(file, caption="🏆 Экспорт викторин")
    await callback.message.delete()


# ============================================================================
# ТОП ЮЗЕРЫ
# ============================================================================

@router.callback_query(F.data == "admin:top_users")
async def admin_top_users_callback(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    result = await session.execute(
        select(User)
        .where(User.last_quiz_date.isnot(None))
        .order_by(User.quizzes_passed.desc(), User.words_learned.desc())
        .limit(15)
    )
    users = result.scalars().all()

    text = "👥 <b>ТОП-15 ПО ВИКТОРИНАМ</b>\n"
    text += "<i>Сортировка: кол-во викторин → выучено слов</i>\n\n"

    for i, user in enumerate(users, 1):
        name = _display_name(user)
        streak = user.streak_days or 0
        quizzes = user.quizzes_passed or 0
        words = user.words_learned or 0
        level = user.level.value if user.level else "—"

        emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"

        text += f"{emoji} <b>#{i}</b> {name} ({level})\n"
        text += f"   🔥 {streak} дн. | 🏆 {quizzes} викт. | 📚 {words} слов\n\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# ДЕТАЛЬНАЯ СТАТИСТИКА
# ============================================================================

@router.callback_query(F.data == "admin:detailed")
async def admin_detailed_callback(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    difficult_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.translation_ru, Word.times_shown, Word.times_correct)
        .select_from(Word)
        .where(Word.times_shown > 5)
        .order_by((Word.times_correct * 1.0 / Word.times_shown).asc())
        .limit(10)
    )
    difficult_words = difficult_words_result.all()

    popular_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.times_shown)
        .select_from(Word)
        .order_by(Word.times_shown.desc())
        .limit(10)
    )
    popular_words = popular_words_result.all()

    text = "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"

    text += "❌ <b>Самые сложные слова:</b>\n"
    text += "<i>Минимум 5 показов, сортировка по % ошибок</i>\n"
    for i, (word_de, article, trans_ru, shown, correct) in enumerate(difficult_words, 1):
        success_rate = (correct / shown * 100) if shown > 0 else 0
        full_word = f"{article} {word_de}" if article and article != "-" else word_de
        text += f"{i}. <b>{full_word}</b> — {trans_ru} ({success_rate:.0f}%)\n"

    text += "\n📈 <b>Самые популярные слова:</b>\n"
    text += "<i>Чаще всего попадаются в викторинах</i>\n"
    for i, (word_de, article, shown) in enumerate(popular_words, 1):
        full_word = f"{article} {word_de}" if article and article != "-" else word_de
        text += f"{i}. <b>{full_word}</b> — {shown} раз\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# РЕПОРТЫ ПЕРЕВОДОВ
# ============================================================================

@router.callback_query(F.data == "admin:reports")
async def admin_reports(callback: CallbackQuery, session: AsyncSession):
    """Топ зарепорченных слов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    # Топ-15 слов по количеству уникальных репортов
    reports_result = await session.execute(
        select(
            Word.id,
            Word.word_de,
            Word.article,
            Word.level,
            Word.translation_ru,
            Word.translation_uk,
            func.count(TranslationReport.id).label('report_count')
        )
        .join(TranslationReport, Word.id == TranslationReport.word_id)
        .where(TranslationReport.status == 'pending')
        .group_by(Word.id, Word.word_de, Word.article, Word.level,
                  Word.translation_ru, Word.translation_uk)
        .order_by(desc(func.count(TranslationReport.id)))
        .limit(15)
    )
    top_words = reports_result.all()

    # Общая статистика
    total_reports_result = await session.execute(
        select(func.count()).select_from(TranslationReport)
    )
    total_reports = total_reports_result.scalar() or 0

    pending_result = await session.execute(
        select(func.count()).select_from(TranslationReport)
        .where(TranslationReport.status == 'pending')
    )
    pending = pending_result.scalar() or 0

    unique_words_result = await session.execute(
        select(func.count(distinct(TranslationReport.word_id)))
        .select_from(TranslationReport)
        .where(TranslationReport.status == 'pending')
    )
    unique_words = unique_words_result.scalar() or 0

    unique_users_result = await session.execute(
        select(func.count(distinct(TranslationReport.user_id)))
        .select_from(TranslationReport)
    )
    unique_users = unique_users_result.scalar() or 0

    text = "📝 <b>РЕПОРТЫ ПЕРЕВОДОВ</b>\n\n"

    text += "📊 <b>Статистика:</b>\n"
    text += f"├─ Всего репортов: <b>{total_reports}</b>\n"
    text += f"├─ Ожидают проверки: <b>{pending}</b>\n"
    text += f"├─ Уникальных слов: <b>{unique_words}</b>\n"
    text += f"└─ Юзеров отправили: <b>{unique_users}</b>\n\n"

    if top_words:
        text += "🔥 <b>Топ-15 по жалобам:</b>\n"
        text += "<i>Сортировка: кол-во жалоб</i>\n\n"
        for i, (wid, word_de, article, level, trans_ru, trans_uk, count) in enumerate(top_words, 1):
            full_word = f"{article} {word_de}" if article and article != "-" else word_de
            trans = trans_ru or trans_uk or "—"
            emoji = "🔴" if count >= 5 else "🟡" if count >= 3 else "⚪"
            text += f"{emoji} <b>{full_word}</b> ({level.value}) — {trans}\n"
            text += f"   └ {count} жалоб | ID: {wid}\n"
    else:
        text += "✅ Нет pending репортов"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# НАЗАД
# ============================================================================

@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, session: AsyncSession):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()
    text = await _get_main_stats(session)
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())


# ============================================================================
# СТАРЫЕ КОМАНДЫ (совместимость)
# ============================================================================

@router.message(Command("admin_users"))
async def admin_users(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    result = await session.execute(
        select(User)
        .where(User.last_quiz_date.isnot(None))
        .order_by(User.quizzes_passed.desc(), User.words_learned.desc())
        .limit(20)
    )
    users = result.scalars().all()

    text = "👥 <b>ТОП-20 ПО ВИКТОРИНАМ</b>\n\n"

    for i, user in enumerate(users, 1):
        name = _display_name(user)
        streak = user.streak_days or 0
        quizzes = user.quizzes_passed or 0
        words = user.words_learned or 0

        emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"

        text += f"{emoji} <b>#{i}</b> {name}\n"
        text += f"   🔥 {streak} дн. | 🏆 {quizzes} викт. | 📚 {words} слов\n\n"

    await message.answer(text)


@router.message(Command("admin_stats"))
async def admin_detailed_stats(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    difficult_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.translation_ru, Word.times_shown, Word.times_correct)
        .select_from(Word)
        .where(Word.times_shown > 5)
        .order_by((Word.times_correct * 1.0 / Word.times_shown).asc())
        .limit(10)
    )
    difficult_words = difficult_words_result.all()

    popular_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.times_shown)
        .select_from(Word)
        .order_by(Word.times_shown.desc())
        .limit(10)
    )
    popular_words = popular_words_result.all()

    text = "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"

    text += "❌ <b>Топ-10 самых сложных слов:</b>\n"
    for i, (word_de, article, trans_ru, shown, correct) in enumerate(difficult_words, 1):
        success_rate = (correct / shown * 100) if shown > 0 else 0
        full_word = f"{article} {word_de}" if article and article != "-" else word_de
        text += f"{i}. <b>{full_word}</b> — {trans_ru}\n"
        text += f"   Показано: {shown} | Правильно: {correct} ({success_rate:.0f}%)\n\n"

    text += "\n📈 <b>Топ-10 популярных слов:</b>\n"
    for i, (word_de, article, shown) in enumerate(popular_words, 1):
        full_word = f"{article} {word_de}" if article and article != "-" else word_de
        text += f"{i}. <b>{full_word}</b> — показано {shown} раз\n"

    await message.answer(text)


@router.message(Command("admin_user"))
async def admin_user_details(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "ℹ️ Использование: /admin_user &lt;id|@username&gt;\n"
            "Пример: /admin_user 123456789 или /admin_user @username"
        )
        return

    raw_identifier = parts[1].strip()
    identifier = raw_identifier.lstrip("@")

    if identifier.isdigit():
        user_result = await session.execute(
            select(User).where(User.id == int(identifier))
        )
    else:
        user_result = await session.execute(
            select(User).where(func.lower(User.username) == identifier.lower())
        )
    user = user_result.scalar_one_or_none()

    if not user:
        await message.answer("❌ Пользователь не найден.")
        return

    overall_progress = await get_user_progress_stats_all_levels(user.id, session)
    level_progress = await get_user_progress_stats(user.id, user.level, session)

    completed_sessions_result = await session.execute(
        select(QuizSession)
        .where(
            QuizSession.user_id == user.id,
            QuizSession.completed_at.isnot(None)
        )
        .order_by(QuizSession.started_at.desc())
    )
    completed_sessions = completed_sessions_result.scalars().all()

    total_quizzes = len(completed_sessions)
    total_questions = sum(s.total_questions for s in completed_sessions)
    total_correct = sum(s.correct_answers for s in completed_sessions)
    avg_score = (total_correct / total_questions * 100) if total_questions > 0 else 0
    best_score = max(
        (s.correct_answers / s.total_questions * 100) for s in completed_sessions
    ) if completed_sessions else 0

    last_sessions = completed_sessions[:5]

    user_avg_response_result = await session.execute(
        select(func.avg(QuizQuestion.response_time_seconds))
        .select_from(QuizQuestion)
        .join(QuizSession, QuizQuestion.session_id == QuizSession.id)
        .where(
            QuizSession.user_id == user.id,
            QuizQuestion.response_time_seconds.isnot(None)
        )
    )
    user_avg_response = user_avg_response_result.scalar() or 0

    sources_result = await session.execute(
        select(QuizSession.start_source, func.count())
        .select_from(QuizSession)
        .where(QuizSession.user_id == user.id, QuizSession.start_source.isnot(None))
        .group_by(QuizSession.start_source)
    )
    sources = sources_result.all()
    sources_text = ", ".join([f"{src}: {cnt}" for src, cnt in sources]) if sources else "—"

    name = _display_name(user)

    header = (
        f"👤 <b>{name}</b>\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: {'@' + user.username if user.username else '—'}\n"
        f"Регистрация: <b>{user.created_at.strftime('%d.%m.%Y')}</b>\n\n"

        "⚙️ <b>Настройки:</b>\n"
        f"├─ Уровень: <b>{user.level.value if user.level else '—'}</b>\n"
        f"├─ Режим: <b>{user.translation_mode.value if user.translation_mode else '—'}</b>\n"
        f"├─ Язык: <b>{user.interface_language or '—'}</b>\n"
        f"└─ Timezone: <b>{user.timezone or 'Europe/Berlin'}</b>\n\n"

        "🔔 <b>Напоминания:</b>\n"
        f"├─ {'✅ Вкл' if user.notifications_enabled else '❌ Выкл'}\n"
        f"├─ Время: <b>{user.notification_time or '—'}</b>\n"
        f"└─ Дни: <b>{len(user.notification_days) if user.notification_days else 0}/7</b>\n\n"

        "📊 <b>Активность:</b>\n"
        f"├─ Последняя викт.: <b>{user.last_quiz_date or '—'}</b>\n"
        f"├─ Стрик: <b>{user.streak_days}</b> дн.\n"
        f"└─ Ср. скорость: <b>{user_avg_response:.1f} сек</b>\n\n"
    )

    overall_block = (
        "🌍 <b>Все уровни:</b>\n"
        f"├─ ✅ Выучено: <b>{overall_progress['learned_words']}</b>\n"
        f"├─ 🔄 В процессе: <b>{overall_progress['seen_words'] - overall_progress['learned_words']}</b>\n"
        f"├─ ❌ Сложные: <b>{overall_progress['struggling_words']}</b>\n"
        f"└─ 🆕 Новых: <b>{overall_progress['new_words']}</b>\n\n"
    )

    level_block = (
        f"🎯 <b>Уровень {user.level.value}:</b>\n"
        f"├─ ✅ Выучено: <b>{level_progress['learned_words']}</b>\n"
        f"├─ 🔄 В процессе: <b>{level_progress['seen_words'] - level_progress['learned_words']}</b>\n"
        f"├─ ❌ Сложные: <b>{level_progress['struggling_words']}</b>\n"
        f"└─ 🆕 Новых: <b>{level_progress['new_words']}</b>\n\n"
    )

    quiz_block = (
        "🏆 <b>Викторины:</b>\n"
        f"├─ Пройдено: <b>{total_quizzes}</b>\n"
        f"├─ Ср. результат: <b>{avg_score:.1f}%</b>\n"
        f"├─ Лучший: <b>{best_score:.1f}%</b>\n"
        f"└─ Источники: {sources_text}\n\n"
    )

    sessions_block = "🕓 <b>Последние 5 сессий:</b>\n"
    if last_sessions:
        for s in last_sessions:
            percent = (s.correct_answers / s.total_questions * 100) if s.total_questions else 0
            date_str = s.started_at.strftime("%d.%m %H:%M")
            sessions_block += (
                f"• {date_str} | {s.level.value} | "
                f"{s.correct_answers}/{s.total_questions} ({percent:.0f}%)\n"
            )
    else:
        sessions_block += "— Нет сессий.\n"

    await message.answer(header + overall_block + level_block + quiz_block + sessions_block)


@router.message(Command("broadcast"))
async def broadcast_message(message: Message, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "ℹ️ Использование: /broadcast &lt;текст&gt;\n"
            "Пример: /broadcast Привет всем! 👋"
        )
        return

    broadcast_text = parts[1]

    result = await session.execute(select(User))
    users = result.scalars().all()

    success = 0
    failed = 0

    for user in users:
        try:
            await message.bot.send_message(user.id, broadcast_text)
            success += 1
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user.id}: {e}")
            failed += 1

    await message.answer(
        f"📢 <b>Рассылка завершена</b>\n\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}"
    )