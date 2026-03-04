"""
Утилиты для системы рейтингов
Включает функции форматирования, титулов, прогресс-баров
"""


def get_win_streak_emoji(current_streak: int) -> str:
    """
    Эмодзи для активной win streak

    Args:
        current_streak: текущая серия побед

    Returns:
        Эмодзи с количеством побед
    """
    if current_streak >= 5:
        return f"💎×{current_streak}"  # Бессмертный
    elif current_streak >= 3:
        return f"👑×{current_streak}"  # Легенда
    elif current_streak >= 2:
        return f"🔥×{current_streak}"  # Двукратный
    elif current_streak == 1:
        return "🔥"  # Чемпион
    return ""


def get_words_emoji(learned_words: int) -> str:
    """
    Эмодзи для постоянных титулов (по количеству выученных слов)

    Args:
        learned_words: количество выученных слов

    Returns:
        Эмодзи титула
    """
    if learned_words >= 2000:
        return "🌍"  # Полиглот
    elif learned_words >= 1000:
        return "🧠"  # Профессор
    elif learned_words >= 500:
        return "🎯"  # Эксперт
    elif learned_words >= 100:
        return "📚"  # Ученик
    return ""


def get_user_title(win_streak: dict, learned_words: int) -> str:
    """
    Получить титул пользователя

    Приоритет:
    1. Активная win streak (если > 0)
    2. Постоянный титул по словам

    Args:
        win_streak: словарь с данными win streak {'current': int, 'best': int}
        learned_words: количество выученных слов

    Returns:
        Эмодзи титула или пустая строка
    """
    current_streak = win_streak.get('current', 0) if win_streak else 0

    # Приоритет 1: активная серия побед
    if current_streak > 0:
        return get_win_streak_emoji(current_streak)

    # Приоритет 2: титул по словам
    return get_words_emoji(learned_words)


def format_month_name(month: int, lang: str = "ru") -> str:
    """
    Форматировать название месяца

    Args:
        month: номер месяца (1-12)
        lang: язык интерфейса

    Returns:
        Название месяца на выбранном языке
    """
    months_ru = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    months_uk = {
        1: "Січень", 2: "Лютий", 3: "Березень", 4: "Квітень",
        5: "Травень", 6: "Червень", 7: "Липень", 8: "Серпень",
        9: "Вересень", 10: "Жовтень", 11: "Листопад", 12: "Грудень"
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

    months = months_uk if lang == "uk" else months_en if lang == "en" else months_tr if lang == "tr" else months_ru
    return months.get(month, str(month))


def create_progress_bar(current: int, target: int, length: int = 10) -> str:
    """
    Создать визуальный прогресс-бар

    Args:
        current: текущее значение
        target: целевое значение
        length: длина прогресс-бара в символах

    Returns:
        Строка с прогресс-баром и процентом
    """
    if target <= current:
        return "▓" * length + " ✓"

    percentage = min(100, int((current / target) * 100))
    filled = int((current / target) * length)
    empty = length - filled

    bar = "▓" * filled + "░" * empty
    return f"{bar} {percentage}%"


def format_user_card(entry: dict, rank: int, is_current_user: bool, lang: str = "ru") -> str:
    """
    Форматировать карточку пользователя в рейтинге

    Логика отображения:
    - Топ-3: только медали, БЕЗ титулов
    - Остальные: показываем титулы (win streak → слова)
    - Текущий пользователь: жирный шрифт

    Args:
        entry: данные пользователя из рейтинга
        rank: позиция в рейтинге
        is_current_user: это текущий пользователь?
        lang: язык интерфейса

    Returns:
        Красиво оформленная карточка пользователя
    """
    display_name = entry["display_name"]
    score = entry["monthly_score"]

    # Эмодзи медалей для топ-3
    if rank == 1:
        rank_emoji = "🥇"
    elif rank == 2:
        rank_emoji = "🥈"
    elif rank == 3:
        rank_emoji = "🥉"
    else:
        rank_emoji = f"{rank}."

    # ТОП-3 — только медали, БЕЗ титулов
    if rank <= 3:
        if is_current_user:
            # Твоя карточка в топ-3 — жирный шрифт
            card = f"{rank_emoji} <b>{display_name}</b>\n"
            card += f"   💎 {score} баллов"
        else:
            card = f"{rank_emoji} {display_name}\n"
            card += f"   💎 {score} баллов"

    # ОСТАЛЬНЫЕ (4+) — показываем титулы
    else:
        # Получаем титул (win streak или слова)
        title = get_user_title(
            entry.get("win_streak"),
            entry.get("monthly_words", 0)
        )

        # Добавляем пробел перед титулом если он есть
        title_str = f" {title}" if title else ""

        if is_current_user:
            # Твоя карточка — жирный шрифт
            card = f"{rank_emoji} <b>{display_name}{title_str}</b> — {score} баллов"
        else:
            card = f"{rank_emoji} {display_name}{title_str} — {score} баллов"

    return card


def get_leaderboard_keyboard_text(lang: str, current_tab: str) -> dict:
    """
    Получить тексты кнопок для клавиатуры рейтинга

    Args:
        lang: язык интерфейса
        current_tab: текущая вкладка ('monthly' или 'alltime')

    Returns:
        Словарь с текстами кнопок
    """
    if current_tab == "monthly":
        monthly_text = "• Месяц •" if lang == "ru" else "• Місяць •" if lang == "uk" else "• Month •" if lang == "en" else "• Ay •"
        alltime_text = "За всё время" if lang == "ru" else "За весь час" if lang == "uk" else "All-Time" if lang == "en" else "Tüm Zamanlar"
    else:
        monthly_text = "Месяц" if lang == "ru" else "Місяць" if lang == "uk" else "Month" if lang == "en" else "Ay"
        alltime_text = "• За всё время •" if lang == "ru" else "• За весь час •" if lang == "uk" else "• All-Time •" if lang == "en" else "• Tüm Zamanlar •"

    return {
        'monthly': monthly_text,
        'alltime': alltime_text
    }


def get_localized_text(key: str, lang: str = "ru") -> str:
    """
    Получить локализованный текст

    Args:
        key: ключ текста
        lang: язык

    Returns:
        Локализованная строка
    """
    texts = {
        "title_monthly": {
            "ru": "🏆 Рейтинг {month} {year}",
            "uk": "🏆 Рейтинг {month} {year}",
            "en": "🏆 {month} {year} Leaderboard",
            "tr": "🏆 {month} {year} Sıralaması"
        },
        "title_alltime": {
            "ru": "🏆 За всё время",
            "uk": "🏆 За весь час",
            "en": "🏆 All-Time",
            "tr": "🏆 Tüm Zamanlar"
        },
        "no_participants": {
            "ru": "Пока никто не участвует в рейтинге.\nПройди викторину первым!\n",
            "uk": "Поки ніхто не бере участь у рейтингу.\nПройди вікторину першим!\n",
            "en": "No participants yet.\nBe the first to take a quiz!\n",
            "tr": "Henüz katılımcı yok.\nİlk sen ol!\n"
        },
        "your_position": {
            "ru": "📍 <b>Твоя позиция: #{rank}</b>",
            "uk": "📍 <b>Твоя позиція: #{rank}</b>",
            "en": "📍 <b>Your position: #{rank}</b>",
            "tr": "📍 <b>Pozisyonun: #{rank}</b>"
        },
        "points": {
            "ru": "💎 Баллы: {score}",
            "uk": "💎 Бали: {score}",
            "en": "💎 Points: {score}",
            "tr": "💎 Puanlar: {score}"
        },
        "goal_top3": {
            "ru": "🎯 До топ-3: {diff} баллов",
            "uk": "🎯 До топ-3: {diff} балів",
            "en": "🎯 To top-3: {diff} points",
            "tr": "🎯 İlk 3'e: {diff} puan"
        },
        "no_participation": {
            "ru": "📍 Ты еще не участвуешь в рейтинге.\nПройди первую викторину!\n",
            "uk": "📍 Ти ще не берешь участь у рейтингу.\nПройди першу вікторину!\n",
            "en": "📍 You haven't participated yet.\nTake your first quiz!\n",
            "tr": "📍 Henüz katılmadın.\nİlk testini çöz!\n"
        },
        "scoring_title": {
            "ru": "📊 <b>Как начисляются баллы:</b>",
            "uk": "📊 <b>Як нараховуються бали:</b>",
            "en": "📊 <b>How points are earned:</b>",
            "tr": "📊 <b>Puanlar nasıl kazanılır:</b>"
        }
    }

    return texts.get(key, {}).get(lang, texts.get(key, {}).get("ru", ""))