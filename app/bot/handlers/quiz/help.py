"""
Помощь и поддержка
"""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User

router = Router()

CHAT_URL = "t.me/genaulingua_chat"


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
    from app.bot.keyboards import get_main_menu_keyboard
    old_anchor_id = user.anchor_message_id
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard())
        new_anchor_id = sent.message_id
        user.anchor_message_id = new_anchor_id
        await session.commit()
        print(f"   ✨ Создан новый якорь {new_anchor_id}")
        return old_anchor_id, new_anchor_id
    except Exception as e:
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


def get_help_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Как пользоваться", callback_data="help_how_to_use")],
            [InlineKeyboardButton(text="🚀 Скоро в боте", callback_data="help_roadmap")],
            [InlineKeyboardButton(text="💬 Сообщество", callback_data="help_community")],
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="help_about")],
        ]
    )


# ============================================================================
# ГЛАВНОЕ МЕНЮ ПОМОЩИ
# ============================================================================

@router.message(F.text == "❓ Помощь")
async def show_help(message: Message, session: AsyncSession):
    user = await session.get(User, message.from_user.id)

    help_text = (
        "❓ <b>Помощь — GenauLingua</b>\n\n"
        "Здесь ты найдёшь инструкции, узнаешь что скоро появится в боте и как связаться с сообществом.\n\n"
        "Выбери раздел:"
    )

    try:
        await message.delete()
    except:
        pass

    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="❓")

    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    await message.answer(help_text, reply_markup=get_help_keyboard())


# ============================================================================
# КАК ПОЛЬЗОВАТЬСЯ
# ============================================================================

@router.callback_query(F.data == "help_how_to_use")
async def show_how_to_use(callback: CallbackQuery):
    await callback.answer()

    text = (
        "📖 <b>Как пользоваться ботом</b>\n\n"

        "1️⃣ <b>Настрой уровень и режим</b>\n"
        "🦾 Настройки → выбери уровень A1–B1, режим перевода и язык.\n\n"

        "2️⃣ <b>Учи слова каждый день</b>\n"
        "📚 Учить слова → викторина из 25 слов.\n"
        "Бот запоминает твои ошибки и чаще показывает сложные слова.\n\n"

        "3️⃣ <b>Повторяй ошибки</b>\n"
        "После викторины можешь сразу повторить слова в которых ошибся.\n\n"

        "4️⃣ <b>Следи за прогрессом</b>\n"
        "📊 Статистика → сколько выучено, история викторин, стрик.\n\n"

        "━━━━━━━━━━━━━━━━━\n"
        "💡 Слово <b>выучено</b> — если ответил правильно 3 раза подряд.\n"
        "🔥 <b>Стрик</b> растёт если прошёл хотя бы 1 викторину в этот день.\n\n"
        f"Вопросы? → {CHAT_URL}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# СКОРО В БОТЕ
# ============================================================================

@router.callback_query(F.data == "help_roadmap")
async def show_roadmap(callback: CallbackQuery):
    await callback.answer()

    text = (
        "🚀 <b>Скоро в GenauLingua</b>\n\n"

        "🏆 <b>Достижения</b>\n"
        "Бейджи за прогресс — первая викторина, 7 дней подряд, 100 слов выучено, викторина на 100% и другие.\n\n"

        "🥇 <b>Таблица лидеров</b>\n"
        "Рейтинг среди всех пользователей — по словам, стрику и результатам викторин. Сравнивай себя с другими.\n\n"

        "🎯 <b>Челленджи</b>\n"
        "Еженедельные задания — пройди 7 викторин подряд, выучи 100 слов за неделю, набери 3 результата на 90%+.\n\n"

        "🔔 <b>Напоминания</b>\n"
        "Настрой время — бот напомнит позаниматься и покажет текущий стрик.\n\n"

        "📚 <b>Уровни B2–C2</b>\n"
        "Сейчас доступны A1–B1. В работе база для B2, C1 и C2.\n\n"

        "🎤 <b>Произношение</b>\n"
        "Озвучка слов — слушай как звучит немецкое слово.\n\n"

        "━━━━━━━━━━━━━━━━━\n"
        f"💬 Идеи и пожелания — пиши в чат:\n{CHAT_URL}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# СООБЩЕСТВО
# ============================================================================

@router.callback_query(F.data == "help_community")
async def show_community(callback: CallbackQuery):
    await callback.answer()

    text = (
        "💬 <b>Сообщество GenauLingua</b>\n\n"
        f"👉 <b>{CHAT_URL}</b>\n\n"
        "В чате:\n"
        "📢 Первыми узнаёшь об обновлениях\n"
        "🐛 Нашёл баг — пиши или присылай скриншот\n"
        "📝 Ошибка в переводе — сообщай, исправим\n"
        "💡 Идеи и пожелания — всё читаем и берём в работу\n"
        "👥 Общение с другими учениками\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "Чем активнее сообщество — тем лучше становится бот. Не стесняйся! 🙌"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# О БОТЕ
# ============================================================================

@router.callback_query(F.data == "help_about")
async def show_about(callback: CallbackQuery):
    await callback.answer()

    text = (
        "ℹ️ <b>О боте</b>\n\n"
        "🤖 <b>GenauLingua</b> — персональный помощник в изучении немецкого.\n\n"
        "✨ <b>Что умеет сейчас:</b>\n"
        "• База слов A1–B1 (3000+ слов)\n"
        "• Умный подбор слов — SRS алгоритм\n"
        "• Режимы DE→RU, RU→DE, DE→UA, UA→DE\n"
        "• Повтор ошибок после викторины\n"
        "• Статистика и стрик\n"
        "• Интерфейс на русском и украинском\n\n"
        "📅 <b>Обновлено:</b> Февраль 2026\n\n"
        f"💬 Следи за обновлениями: {CHAT_URL}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="help_back")]]
    )

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================================
# НАВИГАЦИЯ
# ============================================================================

@router.callback_query(F.data == "help_back")
async def back_to_help(callback: CallbackQuery):
    await callback.answer()

    help_text = (
        "❓ <b>Помощь — GenauLingua</b>\n\n"
        "Здесь ты найдёшь инструкции, узнаешь что скоро появится в боте и как связаться с сообществом.\n\n"
        "Выбери раздел:"
    )

    await callback.message.edit_text(help_text, reply_markup=get_help_keyboard())


@router.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer()
    try:
        await callback.message.delete()
    except:
        pass