try:
    from aiogram.utils.exceptions import MessageNotModified, MessageToEditNotFound
except ImportError:
    MessageNotModified, MessageToEditNotFound = Exception, Exception

import asyncio
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import QuizStates
from app.bot.keyboards import get_level_keyboard, get_main_menu_keyboard
from app.database.enums import CEFRLevel
from app.database.models import User

router = Router()

MODE_DICT = {
    "de_to_ru": "🇩🇪 DE → 🏴 RU",
    "ru_to_de": "🏴 RU → 🇩🇪 DE",
    "de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
}


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
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


async def cleanup_messages(message: Message, anchor_id: int, last_content_id: int):
    deleted_count = 0
    for msg_id in range(anchor_id + 1, last_content_id):
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
            deleted_count += 1
        except Exception:
            pass
    print(f"🧹 CLEANUP завершён: удалено {deleted_count} сообщений")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    user_id = message.from_user.id

    await state.clear()

    try:
        await message.delete()
    except:
        pass

    user = await session.get(User, user_id)

    if not user:
        user = User(
            id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()

    # Стрик НЕ обновляем при /start — только при завершении викторины

    first_name = message.from_user.first_name or "друг"

    welcome_text = (
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        f"🇩🇪 <b>GenauLingua</b> — учи немецкий каждый день.\n"
        f"Бот анализирует твои результаты и подбирает слова именно для тебя.\n\n"
        f"──────────────────\n"
        f"📚 <b>Учить слова</b>\n"
        f"Игровые викторины по немецким словам. Чем больше занимаешься — тем точнее подбираются слова.\n\n"
        f"📊 <b>Статистика</b>\n"
        f"Прогресс по уровням, история викторин, сравнение с другими пользователями.\n\n"
        f"🦾 <b>Настройки</b>\n"
        f"Уровень (A1–C2), язык интерфейса, режим викторины.\n\n"
        f"❓ <b>Помощь</b>\n"
        f"Подсказки, актуальные обновления и обратная связь.\n"
        f"──────────────────\n\n"
    )

    if user.level:
        mode = MODE_DICT.get(user.translation_mode.value, user.translation_mode.value)
        welcome_text += f"Твой уровень: <b>{user.level.value}</b> · Режим: <b>{mode}</b>\n\n"
        welcome_text += "Нажми 📚 Учить слова — и начнём!"

        old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🏠")

        if old_anchor_id:
            current_msg_id = message.message_id
            await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

        await message.answer(welcome_text)
    else:
        welcome_text += "Для начала выбери свой уровень немецкого:"

        await message.answer(welcome_text)
        await message.answer("Выбери уровень:", reply_markup=get_level_keyboard())
        await state.set_state(QuizStates.choosing_level)


@router.callback_query(F.data.startswith("level_"))
async def select_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    level = callback.data.split("_")[1]

    if level == "locked":
        await callback.answer("🔒 Этот уровень пока в разработке", show_alert=True)
        return

    user_id = callback.from_user.id
    user = await session.get(User, user_id)
    user.level = CEFRLevel(level.upper())
    await session.commit()

    await callback.message.delete()

    old_anchor_id, new_anchor_id = await ensure_anchor(callback.message, session, user, emoji="🏠")

    if old_anchor_id:
        current_msg_id = callback.message.message_id
        await delete_messages_fast(callback.bot, callback.message.chat.id, old_anchor_id, current_msg_id)

    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"✅ Уровень <b>{level.upper()}</b> выбран.\n\nНажми 📚 Учить слова — и начнём!"
    )

    await state.clear()
    await callback.answer()