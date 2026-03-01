"""
Админ-панель для GenauLingua Bot (Полная версия)
Команды доступны только для администратора
"""

import os
import csv
import io
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, distinct, case, desc, or_
from datetime import datetime, timedelta, date
from app.database.models import User, QuizSession, QuizQuestion, UserWord, Word
from app.services.quiz_service import get_user_progress_stats, get_user_progress_stats_all_levels
from app.config import settings

router = Router()

# ID администратора из settings
ADMIN_USER_ID = settings.ADMIN_USER


def is_admin(user_id: int) -> bool:
    """Проверка что пользователь - админ"""
    return user_id == ADMIN_USER_ID


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура админ-панели"""
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
        ]
    ])
    return keyboard


# ============================================================================
# ГЛАВНАЯ ПАНЕЛЬ
# ============================================================================

@router.message(Command("admin"))
async def admin_panel(message: Message, session: AsyncSession):
    """Главная админ-панель с кнопками"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели")
        return

    try:
        await message.delete()
    except:
        pass

    # Собираем базовую статистику
    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()

    day_ago = datetime.utcnow() - timedelta(hours=24)
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

    quizzes_24h_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(
            QuizSession.completed_at.isnot(None),
            QuizSession.completed_at >= day_ago
        )
    )
    quizzes_24h = quizzes_24h_result.scalar()

    # Эффективность напоминаний
    notif_sessions_result = await session.execute(
        select(func.count())
        .select_from(QuizSession)
        .where(QuizSession.start_source == 'notification', QuizSession.completed_at.isnot(None))
    )
    notif_sessions = notif_sessions_result.scalar() or 0

    # Формируем текст
    admin_text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
    admin_text += "📊 <b>Пользователи:</b>\n"
    admin_text += f"├─ Всего: <b>{total_users}</b>\n"
    admin_text += f"├─ 🟢 За 24ч: <b>{active_24h}</b>\n"
    admin_text += f"└─ 📅 За 7 дней: <b>{active_7d}</b>\n\n"

    admin_text += "🏆 <b>Викторины:</b>\n"
    admin_text += f"├─ Всего: <b>{total_quizzes}</b>\n"
    admin_text += f"├─ За 24ч: <b>{quizzes_24h}</b>\n"
    admin_text += f"└─ Из уведомлений: <b>{notif_sessions}</b>\n\n"

    admin_text += "💡 Выберите раздел:\n"

    await message.answer(admin_text, reply_markup=get_admin_keyboard())


# ============================================================================
# АНАЛИТИКА (callback)
# ============================================================================

@router.callback_query(F.data == "admin:analytics")
async def admin_analytics(callback: CallbackQuery, session: AsyncSession):
    """Глубокая аналитика вовлечённости"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    # 1. Retention анализ
    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()

    # Day 1 retention (вернулись на следующий день)
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

    # Day 7 retention
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

    # 2. Викторины по источникам
    sources_result = await session.execute(
        select(QuizSession.start_source, func.count())
        .select_from(QuizSession)
        .where(QuizSession.start_source.isnot(None), QuizSession.completed_at.isnot(None))
        .group_by(QuizSession.start_source)
    )
    sources = sources_result.all()
    total_source_quizzes = sum(count for _, count in sources)

    # 3. Распределение по скорости ответа
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

    # 4. Точки выхода
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

    # 5. Самые сложные слова (по времени ответа)
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

    # Формируем текст
    text = "📈 <b>ГЛУБОКАЯ АНАЛИТИКА</b>\n\n"

    text += "🔥 <b>Retention:</b>\n"
    text += f"├─ Day 1: <b>{day1_retention:.1f}%</b> ({day1_returned}/{total_users})\n"
    text += f"└─ Day 7: <b>{day7_retention:.1f}%</b> ({day7_active}/{users_week_ago})\n\n"

    text += "📊 <b>Викторины по источникам:</b>\n"
    for source, count in sources:
        percentage = (count / total_source_quizzes * 100) if total_source_quizzes > 0 else 0
        emoji = "📱" if source == 'notification' else "📚" if source == 'menu' else "🔄"
        text += f"├─ {emoji} {source}: <b>{count}</b> ({percentage:.0f}%)\n"
    text += "\n"

    if total_answers > 0:
        text += "⏱️ <b>Скорость ответа:</b>\n"
        text += f"├─ 0-2 сек: <b>{speed_dist[0]/total_answers*100:.0f}%</b> (быстрые)\n"
        text += f"├─ 3-5 сек: <b>{speed_dist[1]/total_answers*100:.0f}%</b> (норма)\n"
        text += f"├─ 6-10 сек: <b>{speed_dist[2]/total_answers*100:.0f}%</b> (медленные)\n"
        text += f"└─ 10+ сек: <b>{speed_dist[3]/total_answers*100:.0f}%</b> (долго)\n\n"

    if exit_points and any(exit_points):
        text += "🚪 <b>Где бросают викторины:</b>\n"
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
# КОГОРТЫ (callback)
# ============================================================================

@router.callback_query(F.data == "admin:cohorts")
async def admin_cohorts(callback: CallbackQuery, session: AsyncSession):
    """Анализ когорт пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    # 1. По месяцам регистрации
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

    # 2. По уровням
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

    # 3. По языкам интерфейса
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
        'tr': '🇹🇷 Türkçe'
    }

    # Формируем текст
    text = "👥 <b>КОГОРТЫ ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"

    text += "📅 <b>По месяцам регистрации:</b>\n"
    text += f"├─ {prev_month.strftime('%B %Y')}: <b>{prev_month_users}</b> юзеров\n"
    if prev_month_users > 0:
        text += f"│  └─ Активных: {prev_month_active} ({prev_month_active/prev_month_users*100:.0f}%)\n"
    text += f"└─ {current_month.strftime('%B %Y')}: <b>{current_month_users}</b> юзеров\n"
    if current_month_users > 0:
        text += f"   └─ Активных: {current_month_active} ({current_month_active/current_month_users*100:.0f}%)\n"
    text += "\n"

    text += "📚 <b>По уровням (активность):</b>\n"
    for level, users, avg_quizzes in levels_stats:
        if level:
            avg_quiz_val = avg_quizzes or 0
            text += f"├─ {level.value}: <b>{users}</b> юзеров | Ср. {avg_quiz_val:.1f} викторин\n"
    text += "\n"

    text += "🌍 <b>По языкам:</b>\n"
    for lang, count in langs:
        lang_name = lang_names.get(lang, lang)
        percentage = (count / total_lang_users * 100) if total_lang_users > 0 else 0
        text += f"├─ {lang_name}: <b>{count}</b> ({percentage:.0f}%)\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# CHURN (callback)
# ============================================================================

@router.callback_query(F.data == "admin:churn")
async def admin_churn(callback: CallbackQuery, session: AsyncSession):
    """Анализ риска оттока пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    today = date.today()
    week_ago = today - timedelta(days=7)
    three_days_ago = today - timedelta(days=3)

    # Высокий риск (7+ дней)
    high_risk_result = await session.execute(
        select(User.username, User.last_quiz_date)
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

    # Средний риск (3-7 дней)
    medium_risk_count_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.last_quiz_date >= week_ago,
            User.last_quiz_date < three_days_ago
        )
    )
    medium_risk_count = medium_risk_count_result.scalar() or 0

    # Churn rate за последние 30 дней
    month_ago = today - timedelta(days=30)
    users_month_ago_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(User.created_at <= datetime.combine(month_ago, datetime.min.time()))
    )
    users_month_ago = users_month_ago_result.scalar() or 1

    churned_result = await session.execute(
        select(func.count())
        .select_from(User)
        .where(
            User.created_at <= datetime.combine(month_ago, datetime.min.time()),
            or_(User.last_quiz_date.is_(None), User.last_quiz_date < month_ago)
        )
    )
    churned = churned_result.scalar() or 0
    churn_rate = (churned / users_month_ago * 100) if users_month_ago > 0 else 0

    # Формируем текст
    text = "⚠️ <b>РИСК ОТТОКА</b>\n\n"

    text += f"🔴 <b>Высокий риск (7+ дней): {high_risk_count}</b>\n"
    if high_risk:
        for username, last_quiz in high_risk[:5]:
            days_ago = (today - last_quiz).days if last_quiz else 999
            user_display = f"@{username}" if username else "без username"
            text += f"├─ {user_display} — {days_ago} дней назад\n"
        if len(high_risk) > 5:
            text += f"└─ ... и ещё {len(high_risk) - 5}\n"
    text += "\n"

    text += f"🟡 <b>Средний риск (3-7 дней): {medium_risk_count}</b>\n\n"

    text += f"📊 <b>Churn rate (30 дней): {churn_rate:.1f}%</b>\n"
    text += f"   Ушло: {churned} из {users_month_ago}"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# ЭКСПОРТ (callback)
# ============================================================================

@router.callback_query(F.data == "admin:export")
async def admin_export_menu(callback: CallbackQuery, session: AsyncSession):
    """Меню экспорта данных"""
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
    """Экспорт списка пользователей в CSV"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer("⏳ Генерирую файл...")

    # Получаем всех пользователей
    result = await session.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    # Создаём CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow([
        'ID', 'Username', 'First Name', 'Created At', 'Level',
        'Streak Days', 'Quizzes Passed', 'Words Learned',
        'Last Quiz Date', 'Interface Language', 'Timezone',
        'Notifications Enabled'
    ])

    # Данные
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
            user.interface_language or 'ru',
            user.timezone or '',
            'Yes' if user.notifications_enabled else 'No'
        ])

    # Конвертируем в bytes
    output.seek(0)
    csv_bytes = output.getvalue().encode('utf-8-sig')  # BOM для Excel

    # Отправляем файл
    file = BufferedInputFile(csv_bytes, filename=f"users_{date.today()}.csv")
    await callback.message.answer_document(file, caption="📊 Экспорт пользователей")

    await callback.message.delete()


@router.callback_query(F.data == "admin:export_quizzes")
async def admin_export_quizzes(callback: CallbackQuery, session: AsyncSession):
    """Экспорт истории викторин в CSV"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer("⏳ Генерирую файл...")

    # Получаем все викторины
    result = await session.execute(
        select(QuizSession, User.username)
        .join(User, QuizSession.user_id == User.id)
        .where(QuizSession.completed_at.isnot(None))
        .order_by(QuizSession.started_at.desc())
        .limit(1000)  # Последние 1000
    )
    quizzes = result.all()

    # Создаём CSV
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Session ID', 'User ID', 'Username', 'Started At', 'Completed At',
        'Level', 'Total Questions', 'Correct Answers', 'Score %',
        'Start Source', 'Exit Reason', 'Exit At Question'
    ])

    for quiz, username in quizzes:
        score = (quiz.correct_answers / quiz.total_questions * 100) if quiz.total_questions > 0 else 0
        writer.writerow([
            quiz.id,
            quiz.user_id,
            username or '',
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
# ТОП ПОЛЬЗОВАТЕЛИ (callback)
# ============================================================================

@router.callback_query(F.data == "admin:top_users")
async def admin_top_users_callback(callback: CallbackQuery, session: AsyncSession):
    """Топ пользователей (через callback)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    result = await session.execute(
        select(User)
        .order_by(User.streak_days.desc(), User.quizzes_passed.desc())
        .limit(15)
    )
    users = result.scalars().all()

    text = "👥 <b>ТОП-15 АКТИВНЫХ</b>\n\n"

    for i, user in enumerate(users, 1):
        username = user.username or "без username"
        streak = user.streak_days or 0
        quizzes = user.quizzes_passed or 0
        words = user.words_learned or 0

        emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"

        text += f"{emoji} <b>#{i}</b> @{username}\n"
        text += f"   🔥 {streak} дней | 🏆 {quizzes} викторин | 📚 {words} слов\n\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# ДЕТАЛЬНАЯ СТАТИСТИКА (callback)
# ============================================================================

@router.callback_query(F.data == "admin:detailed")
async def admin_detailed_callback(callback: CallbackQuery, session: AsyncSession):
    """Детальная статистика (через callback)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещён")
        return

    await callback.answer()

    # Самые сложные слова (по % правильных)
    difficult_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.translation_ru, Word.times_shown, Word.times_correct)
        .select_from(Word)
        .where(Word.times_shown > 5)
        .order_by((Word.times_correct * 1.0 / Word.times_shown).asc())
        .limit(10)
    )
    difficult_words = difficult_words_result.all()

    # Самые популярные слова
    popular_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.times_shown)
        .select_from(Word)
        .order_by(Word.times_shown.desc())
        .limit(10)
    )
    popular_words = popular_words_result.all()

    text = "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"

    text += "❌ <b>Самые сложные слова:</b>\n"
    for i, (word_de, article, trans_ru, shown, correct) in enumerate(difficult_words, 1):
        success_rate = (correct / shown * 100) if shown > 0 else 0
        full_word = f"{article} {word_de}" if article and article != "-" else word_de
        text += f"{i}. <b>{full_word}</b> — {trans_ru} ({success_rate:.0f}%)\n"

    text += "\n📈 <b>Самые популярные слова:</b>\n"
    for i, (word_de, article, shown) in enumerate(popular_words, 1):
        full_word = f"{article} {word_de}" if article and article != "-" else word_de
        text += f"{i}. <b>{full_word}</b> — показано {shown} раз\n"

    back_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin:back")]
    ])

    await callback.message.edit_text(text, reply_markup=back_btn)


# ============================================================================
# НАЗАД (callback)
# ============================================================================

@router.callback_query(F.data == "admin:back")
async def admin_back(callback: CallbackQuery, session: AsyncSession):
    """Возврат в главное меню админки"""
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    # Повторяем логику из admin_panel
    total_users_result = await session.execute(select(func.count()).select_from(User))
    total_users = total_users_result.scalar()

    day_ago = datetime.utcnow() - timedelta(hours=24)
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

    admin_text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ</b>\n\n"
    admin_text += "📊 <b>Пользователи:</b>\n"
    admin_text += f"├─ Всего: <b>{total_users}</b>\n"
    admin_text += f"├─ 🟢 За 24ч: <b>{active_24h}</b>\n"
    admin_text += f"└─ 📅 За 7 дней: <b>{active_7d}</b>\n\n"

    admin_text += "🏆 <b>Викторины:</b>\n"
    admin_text += f"├─ Всего: <b>{total_quizzes}</b>\n"
    admin_text += f"├─ За 24ч: <b>{quizzes_24h}</b>\n"
    admin_text += f"└─ Из уведомлений: <b>{notif_sessions}</b>\n\n"

    admin_text += "💡 Выберите раздел:\n"

    await callback.message.edit_text(admin_text, reply_markup=get_admin_keyboard())


# ============================================================================
# СТАРЫЕ КОМАНДЫ (сохранены для совместимости)
# ============================================================================

@router.message(Command("admin_users"))
async def admin_users(message: Message, session: AsyncSession):
    """Список топ пользователей (старая команда)"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    result = await session.execute(
        select(User)
        .order_by(User.streak_days.desc(), User.quizzes_passed.desc())
        .limit(20)
    )
    users = result.scalars().all()

    text = "👥 <b>ТОП-20 АКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ</b>\n\n"

    for i, user in enumerate(users, 1):
        username = user.username or "без username"
        streak = user.streak_days or 0
        quizzes = user.quizzes_passed or 0
        words = user.words_learned or 0

        emoji = "🏆" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📍"

        text += f"{emoji} <b>#{i}</b> @{username}\n"
        text += f"   🔥 Стрик: {streak} дней | 🏆 Викторин: {quizzes} | 📚 Слов: {words}\n\n"

    await message.answer(text)


@router.message(Command("admin_stats"))
async def admin_detailed_stats(message: Message, session: AsyncSession):
    """Детальная статистика (старая команда)"""
    if not is_admin(message.from_user.id):
        return

    try:
        await message.delete()
    except:
        pass

    # Самые сложные слова
    difficult_words_result = await session.execute(
        select(Word.word_de, Word.article, Word.translation_ru, Word.times_shown, Word.times_correct)
        .select_from(Word)
        .where(Word.times_shown > 5)
        .order_by((Word.times_correct * 1.0 / Word.times_shown).asc())
        .limit(10)
    )
    difficult_words = difficult_words_result.all()

    # Самые популярные слова
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
    """Детальная статистика конкретного пользователя"""
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

    # Средняя скорость ответа пользователя
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

    # Источники викторин
    sources_result = await session.execute(
        select(QuizSession.start_source, func.count())
        .select_from(QuizSession)
        .where(QuizSession.user_id == user.id, QuizSession.start_source.isnot(None))
        .group_by(QuizSession.start_source)
    )
    sources = sources_result.all()
    sources_text = ", ".join([f"{src}: {cnt}" for src, cnt in sources]) if sources else "—"

    header = (
        "👤 <b>Пользователь</b>\n"
        f"ID: <b>{user.id}</b>\n"
        f"Username: <b>@{user.username or 'без username'}</b>\n"
        f"Имя: <b>{user.first_name or '—'} {user.last_name or ''}</b>\n"
        f"Регистрация: <b>{user.created_at.strftime('%d.%m.%Y')}</b>\n\n"

        "⚙️ <b>Настройки:</b>\n"
        f"├─ Уровень: <b>{user.level.value if user.level else '—'}</b>\n"
        f"├─ Режим: <b>{user.translation_mode.value if user.translation_mode else '—'}</b>\n"
        f"├─ Язык интерфейса: <b>{user.interface_language or 'ru'}</b>\n"
        f"└─ Timezone: <b>{user.timezone or 'Europe/Berlin'}</b>\n\n"

        "🔔 <b>Напоминания:</b>\n"
        f"├─ Статус: <b>{'✅ Включены' if user.notifications_enabled else '❌ Выключены'}</b>\n"
        f"├─ Время: <b>{user.notification_time or '—'}</b>\n"
        f"└─ Дни: <b>{len(user.notification_days) if user.notification_days else 0}/7</b>\n\n"

        "📊 <b>Активность:</b>\n"
        f"├─ Последняя викторина: <b>{user.last_quiz_date or '—'}</b>\n"
        f"├─ Стрик: <b>{user.streak_days}</b> дней\n"
        f"└─ ⚡ Средняя скорость: <b>{user_avg_response:.1f} сек</b>\n\n"
    )

    overall_block = (
        "🌍 <b>Вся статистика (все уровни):</b>\n"
        f"Всего слов: <b>{overall_progress['total_words']}</b>\n"
        f"├─ ✅ Выучено: <b>{overall_progress['learned_words']}</b>\n"
        f"├─ 🔄 В процессе: <b>{overall_progress['seen_words'] - overall_progress['learned_words']}</b>\n"
        f"├─ ❌ Сложные: <b>{overall_progress['struggling_words']}</b>\n"
        f"└─ 🆕 Новых: <b>{overall_progress['new_words']}</b>\n\n"
    )

    level_block = (
        f"🎯 <b>Текущий уровень ({user.level.value}):</b>\n"
        f"Всего слов: <b>{level_progress['total_words']}</b>\n"
        f"├─ ✅ Выучено: <b>{level_progress['learned_words']}</b>\n"
        f"├─ 🔄 В процессе: <b>{level_progress['seen_words'] - level_progress['learned_words']}</b>\n"
        f"├─ ❌ Сложные: <b>{level_progress['struggling_words']}</b>\n"
        f"└─ 🆕 Новых: <b>{level_progress['new_words']}</b>\n\n"
    )

    quiz_block = (
        "🏆 <b>Викторины:</b>\n"
        f"├─ Пройдено: <b>{total_quizzes}</b>\n"
        f"├─ Средний результат: <b>{avg_score:.1f}%</b>\n"
        f"├─ Лучший результат: <b>{best_score:.1f}%</b>\n"
        f"└─ Источники: <b>{sources_text}</b>\n\n"
    )

    sessions_block = "🕓 <b>Последние сессии:</b>\n"
    if last_sessions:
        for s in last_sessions:
            percent = (s.correct_answers / s.total_questions * 100) if s.total_questions else 0
            date_str = s.started_at.strftime("%d.%m %H:%M")
            source_emoji = "📱" if s.start_source == 'notification' else "📚" if s.start_source == 'menu' else "🔄"
            sessions_block += (
                f"• {date_str} | {s.level.value} | "
                f"{s.correct_answers}/{s.total_questions} ({percent:.0f}%) {source_emoji}\n"
            )
    else:
        sessions_block += "— Сессий ещё нет.\n"

    await message.answer(header + overall_block + level_block + quiz_block + sessions_block)


@router.message(Command("broadcast"))
async def broadcast_message(message: Message, session: AsyncSession):
    """Рассылка сообщения всем пользователям"""
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
            print(f"❌ Ошибка отправки пользователю {user.id}: {e}")
            failed += 1

    await message.answer(
        f"📢 <b>Рассылка завершена</b>\n\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}"
    )