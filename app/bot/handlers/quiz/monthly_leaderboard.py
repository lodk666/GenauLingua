"""
Обработчик месячного рейтинга

Файл: app/bot/handlers/quiz/monthly_leaderboard.py
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, MonthlySeason
from app.services.monthly_leaderboard_service import (
    get_monthly_leaderboard,
    get_user_monthly_rank,
    get_lifetime_leaderboard,
    get_current_season
)
from app.locales import get_text

router = Router()


def get_monthly_leaderboard_keyboard(lang: str, view: str = "monthly") -> InlineKeyboardMarkup:
    """
    Клавиатура переключения между месячным и lifetime рейтингом

    Args:
        lang: Язык интерфейса
        view: "monthly" или "lifetime"
    """
    # Определяем тексты для каждого языка
    if lang == "ru":
        monthly_base = "🗓️ Месяц"
        lifetime_base = "🌟 Всё время"
    elif lang == "uk":
        monthly_base = "🗓️ Місяць"
        lifetime_base = "🌟 Весь час"
    elif lang == "en":
        monthly_base = "🗓️ Month"
        lifetime_base = "🌟 All-time"
    else:  # tr
        monthly_base = "🗓️ Ay"
        lifetime_base = "🌟 Her zaman"

    # Добавляем галочку к активной вкладке
    if view == "monthly":
        monthly_text = f"✓ {monthly_base}"
        lifetime_text = lifetime_base
    else:
        monthly_text = monthly_base
        lifetime_text = f"✓ {lifetime_base}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=monthly_text, callback_data="monthly_leaderboard:monthly"),
            InlineKeyboardButton(text=lifetime_text, callback_data="monthly_leaderboard:lifetime")
        ],
        [
            InlineKeyboardButton(
                text=get_text("btn_back", lang),
                callback_data="back_to_stats"
            )
        ]
    ])


def format_monthly_leaderboard_text(
        leaderboard: list,
        user_rank: dict,
        season: MonthlySeason,
        lang: str
) -> str:
    """Форматирование месячного рейтинга"""

    # Заголовок с сезоном
    months_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }
    months_uk = {
        1: "січня", 2: "лютого", 3: "березня", 4: "квітня",
        5: "травня", 6: "червня", 7: "липня", 8: "серпня",
        9: "вересня", 10: "жовтня", 11: "листопада", 12: "грудня"
    }
    months_en = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }
    months_tr = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }

    # Выбираем месяц на нужном языке
    if lang == "ru":
        month_name = months_ru[season.month]
    elif lang == "uk":
        month_name = months_uk[season.month]
    elif lang == "en":
        month_name = months_en[season.month]
    else:  # tr
        month_name = months_tr[season.month]

    # Считаем оставшиеся дни
    from datetime import date
    today = date.today()
    if today <= season.end_date:
        days_left = (season.end_date - today).days
        if lang == "ru":
            days_text = f"Осталось: {days_left} дн"
        elif lang == "uk":
            days_text = f"Залишилось: {days_left} дн"
        elif lang == "en":
            days_text = f"Days left: {days_left}"
        else:  # tr
            days_text = f"Kalan: {days_left} gün"
    else:
        if lang == "ru":
            days_text = "Сезон завершён"
        elif lang == "uk":
            days_text = "Сезон завершено"
        elif lang == "en":
            days_text = "Season ended"
        else:  # tr
            days_text = "Sezon bitti"

    text = f"🏆 <b>Рейтинг {month_name} {season.year}</b>\n"
    text += f"{days_text}\n\n"

    # Позиция пользователя
    if user_rank:
        rank = user_rank['rank']
        rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📍"

        percentile_text = f"топ {user_rank['percentile']:.0f}%"

        if lang == "ru":
            text += f"{rank_emoji} <b>Твоя позиция: #{rank}</b> из {user_rank['total_users']}\n"
            text += f"💎 Баллов: <b>{user_rank['monthly_score']}</b> ({percentile_text})\n\n"
        elif lang == "uk":
            text += f"{rank_emoji} <b>Твоя позиція: #{rank}</b> з {user_rank['total_users']}\n"
            text += f"💎 Балів: <b>{user_rank['monthly_score']}</b> (топ {user_rank['percentile']:.0f}%)\n\n"
        elif lang == "en":
            text += f"{rank_emoji} <b>Your position: #{rank}</b> of {user_rank['total_users']}\n"
            text += f"💎 Points: <b>{user_rank['monthly_score']}</b> (top {percentile_text})\n\n"
        else:  # tr
            text += f"{rank_emoji} <b>Konumun: #{rank}</b> / {user_rank['total_users']}\n"
            text += f"💎 Puan: <b>{user_rank['monthly_score']}</b> (ilk {percentile_text})\n\n"

        # Показываем награды пользователя
        user_entry = next((e for e in leaderboard if e['rank'] == rank), None)
        if user_entry and user_entry.get('awards'):
            if lang == "ru":
                awards_text = "Твои награды: "
            elif lang == "uk":
                awards_text = "Твої нагороди: "
            elif lang == "en":
                awards_text = "Your awards: "
            else:  # tr
                awards_text = "Ödülleriniz: "

            awards_emojis = " ".join([a['emoji'] for a in user_entry['awards'][:3]])
            text += f"{awards_text}{awards_emojis}\n\n"

        text += "━━━━━━━━━━━━━━━━━\n\n"

    # Топ-20
    if lang == "ru":
        text += "<b>Топ-20:</b>\n\n"
    elif lang == "uk":
        text += "<b>Топ-20:</b>\n\n"
    elif lang == "en":
        text += "<b>Top 20:</b>\n\n"
    else:  # tr
        text += "<b>En İyi 20:</b>\n\n"

    for entry in leaderboard[:20]:
        rank = entry['rank']

        # Эмодзи для топ-3
        if rank == 1:
            emoji = "🥇"
        elif rank == 2:
            emoji = "🥈"
        elif rank == 3:
            emoji = "🥉"
        else:
            emoji = f"{rank}."

        # Имя с эмодзи серии побед
        name = entry['display_name']
        if entry.get('win_streak') and entry['win_streak']['emoji']:
            name = f"{name} {entry['win_streak']['emoji']}"

        if len(name) > 25:
            name = name[:22] + "..."

        # Статистика
        score = entry['monthly_score']
        streak = entry['monthly_streak']
        words = entry['monthly_words']

        text += f"{emoji} <b>{name}</b>\n"
        if lang == "ru":
            text += f"   💎 {score} • 🔥 {streak} дн • 📚 {words} слов\n"
        elif lang == "uk":
            text += f"   💎 {score} • 🔥 {streak} дн • 📚 {words} слів\n"
        elif lang == "en":
            text += f"   💎 {score} • 🔥 {streak} days • 📚 {words} words\n"
        else:  # tr
            text += f"   💎 {score} • 🔥 {streak} gün • 📚 {words} kelime\n"

        # Показываем награды (макс 3 последние)
        if entry.get('awards') and len(entry['awards']) > 0:
            awards_line = "   " + " ".join([a['emoji'] for a in entry['awards'][:3]])
            text += f"{awards_line}\n"

        text += "\n"

    # Формула
    text += "━━━━━━━━━━━━━━━━━\n"
    if lang == "ru":
        text += "💡 <b>Формула месячного рейтинга:</b>\n"
        text += "• Стрик × 15\n"
        text += "• Викторины × 8\n"
        text += "• Слова × 5\n"
        text += "• Реверс × 5\n"
        text += "• Средний % × 3"
    elif lang == "uk":
        text += "💡 <b>Формула місячного рейтингу:</b>\n"
        text += "• Стрік × 15\n"
        text += "• Вікторини × 8\n"
        text += "• Слова × 5\n"
        text += "• Реверс × 5\n"
        text += "• Середній % × 3"
    elif lang == "en":
        text += "💡 <b>Monthly rating formula:</b>\n"
        text += "• Streak × 15\n"
        text += "• Quizzes × 8\n"
        text += "• Words × 5\n"
        text += "• Reverse × 5\n"
        text += "• Average % × 3"
    else:  # tr
        text += "💡 <b>Aylık derecelendirme formülü:</b>\n"
        text += "• Seri × 15\n"
        text += "• Testler × 8\n"
        text += "• Kelimeler × 5\n"
        text += "• Ters × 5\n"
        text += "• Ortalama % × 3"

    return text


def format_lifetime_leaderboard_text(leaderboard: list, user_id: int, lang: str) -> str:
    """Форматирование lifetime рейтинга"""

    # Защита от None (на случай, если сервис вернул None из-за ошибки)
    leaderboard = leaderboard or []

    if lang == "ru":
        text = "🌟 <b>Lifetime Рейтинг</b>\n\n"
    elif lang == "uk":
        text = "🌟 <b>Lifetime Рейтинг</b>\n\n"
    elif lang == "en":
        text = "🌟 <b>Lifetime Rating</b>\n\n"
    else:  # tr
        text = "🌟 <b>Yaşam Boyu Derecelendirme</b>\n\n"

    # Ищем пользователя
    user_entry = next((e for e in leaderboard if e['user_id'] == user_id), None)

    if user_entry:
        rank = user_entry['rank']
        rank_emoji = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "📍"

        total_users = len(leaderboard)
        percentile = (1 - (rank / total_users)) * 100

        if lang == "ru":
            text += f"{rank_emoji} <b>Твоя позиция: #{rank}</b> из {total_users}\n"
            text += f"💎 Баллов: <b>{user_entry['lifetime_score']}</b> (топ {percentile:.0f}%)\n"
            text += f"🏆 Побед месяца: {user_entry['total_wins']}\n"
            text += f"📚 Всего слов: {user_entry['words_learned']}\n\n"
        elif lang == "uk":
            text += f"{rank_emoji} <b>Твоя позиція: #{rank}</b> з {total_users}\n"
            text += f"💎 Балів: <b>{user_entry['lifetime_score']}</b> (топ {percentile:.0f}%)\n"
            text += f"🏆 Перемог місяця: {user_entry['total_wins']}\n"
            text += f"📚 Всього слів: {user_entry['words_learned']}\n\n"
        elif lang == "en":
            text += f"{rank_emoji} <b>Your position: #{rank}</b> of {total_users}\n"
            text += f"💎 Points: <b>{user_entry['lifetime_score']}</b> (top {percentile:.0f}%)\n"
            text += f"🏆 Monthly wins: {user_entry['total_wins']}\n"
            text += f"📚 Total words: {user_entry['words_learned']}\n\n"
        else:  # tr
            text += f"{rank_emoji} <b>Konumun: #{rank}</b> / {total_users}\n"
            text += f"💎 Puan: <b>{user_entry['lifetime_score']}</b> (ilk {percentile:.0f}%)\n"
            text += f"🏆 Aylık kazanımlar: {user_entry['total_wins']}\n"
            text += f"📚 Toplam kelimeler: {user_entry['words_learned']}\n\n"

        text += "━━━━━━━━━━━━━━━━━\n\n"

    # Топ-10
    if lang == "ru":
        text += "<b>Топ-10 всех времён:</b>\n\n"
    elif lang == "uk":
        text += "<b>Топ-10 всіх часів:</b>\n\n"
    elif lang == "en":
        text += "<b>Top 10 all-time:</b>\n\n"
    else:  # tr
        text += "<b>Her Zamanın En İyi 10:</b>\n\n"

    for entry in leaderboard[:10]:
        rank = entry['rank']

        # Эмодзи
        if rank == 1:
            emoji = "👑"
        elif rank == 2:
            emoji = "🥇"
        elif rank == 3:
            emoji = "🥈"
        else:
            emoji = f"{rank}."

        name = entry['display_name']
        if len(name) > 25:
            name = name[:22] + "..."

        score = entry['lifetime_score']
        wins = entry['total_wins']
        words = entry['words_learned']

        text += f"{emoji} <b>{name}</b>\n"
        text += f"   💎 {score} • 🥇×{wins} • 📚 {words}\n\n"

    return text


@router.callback_query(F.data.startswith("monthly_leaderboard:"))
async def show_monthly_leaderboard(callback: CallbackQuery, session: AsyncSession):
    """Показать месячный или lifetime рейтинг"""
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    view = callback.data.split(":")[1]  # "monthly" или "lifetime"

    if view == "monthly":
        # Месячный рейтинг
        season = await get_current_season(session)
        if not season:
            await callback.message.answer("❌ Активный сезон не найден")
            return

        leaderboard = await get_monthly_leaderboard(session, season.id, limit=20)
        user_rank = await get_user_monthly_rank(user.id, session, season.id)

        text = format_monthly_leaderboard_text(leaderboard, user_rank, season, lang)

    else:
        # Lifetime рейтинг
        leaderboard = await get_lifetime_leaderboard(session, limit=50)
        leaderboard = leaderboard or []
        text = format_lifetime_leaderboard_text(leaderboard, user.id, lang)

    await callback.message.edit_text(
        text,
        reply_markup=get_monthly_leaderboard_keyboard(lang, view)
    )


@router.callback_query(F.data == "show_leaderboard")
async def show_leaderboard_initial(callback: CallbackQuery, session: AsyncSession):
    """
    Первоначальный показ рейтинга
    Вызывается при нажатии кнопки "Рейтинг" под статистикой
    """
    await callback.answer()

    user = await session.get(User, callback.from_user.id)
    lang = user.interface_language or "ru"

    # Показываем месячный рейтинг по умолчанию
    season = await get_current_season(session)
    if not season:
        await callback.message.answer("❌ Активный сезон не найден")
        return

    leaderboard = await get_monthly_leaderboard(session, season.id, limit=20)
    user_rank = await get_user_monthly_rank(user.id, session, season.id)

    text = format_monthly_leaderboard_text(leaderboard, user_rank, season, lang)

    await callback.message.edit_text(
        text,
        reply_markup=get_monthly_leaderboard_keyboard(lang, "monthly")
    )