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
from datetime import date, timedelta

from app.bot.states import QuizStates
from app.bot.keyboards import get_level_keyboard, get_main_menu_keyboard
from app.database.models import User

router = Router()


async def delete_messages_fast(bot, chat_id: int, start_id: int, end_id: int):
    """
    Быстрое удаление сообщений параллельно
    """
    tasks = []
    for msg_id in range(start_id, end_id):
        tasks.append(bot.delete_message(chat_id=chat_id, message_id=msg_id))

    # Удаляем все сообщения одновременно
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Логируем результаты
    deleted = sum(1 for r in results if not isinstance(r, Exception))
    print(f"   🧹 Удалено {deleted}/{len(tasks)} сообщений")


async def ensure_anchor(message: Message, session: AsyncSession, user: User, emoji: str = "🏠"):
    """
    Создаёт новый якорь БЕЗ удаления старого
    Старый якорь удалится позже вместе с остальными сообщениями

    ЛОГИКА:
    1. Создаём НОВЫЙ якорь (чат никогда не пустой!)
    2. Возвращаем ID старого якоря для удаления
    """
    old_anchor_id = user.anchor_message_id

    # Создаём новый якорь СРАЗУ (чтобы чат не был пустым)
    try:
        sent = await message.answer(emoji, reply_markup=get_main_menu_keyboard())
        new_anchor_id = sent.message_id

        # Обновляем ID якоря в базе
        user.anchor_message_id = new_anchor_id
        await session.commit()

        print(f"   ✨ Создан новый якорь {new_anchor_id}")

        # Возвращаем ID старого якоря для удаления
        return old_anchor_id, new_anchor_id
    except Exception as e:
        print(f"   ❌ Ошибка создания якоря: {e}")
        return old_anchor_id, None


async def cleanup_messages(message: Message, anchor_id: int, last_content_id: int):
    """
    Удаляет все сообщения между якорем и последним контентом
    """
    print(f"🧹 CLEANUP: Удаляю сообщения от {anchor_id + 1} до {last_content_id}")
    print(f"   Якорь ID: {anchor_id}")
    print(f"   Последний контент ID: {last_content_id}")
    print(f"   Всего удалить: {last_content_id - anchor_id - 1} сообщений")

    deleted_count = 0
    for msg_id in range(anchor_id + 1, last_content_id):
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=msg_id
            )
            deleted_count += 1
            print(f"   ✅ Удалено сообщение {msg_id}")
        except Exception as e:
            print(f"   ❌ Не удалось удалить {msg_id}: {e}")

    print(f"🧹 CLEANUP завершён: удалено {deleted_count} сообщений")


async def update_user_activity(session, user_id):
    user = await session.get(User, user_id)
    today = date.today()
    if user.last_active_date == today:
        return
    elif user.last_active_date == today - timedelta(days=1):
        user.streak_days += 1
    else:
        user.streak_days = 1
    user.last_active_date = today
    await session.commit()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Очищаем state при перезапуске
    await state.clear()

    # Удаляем команду /start из чата
    try:
        await message.delete()
    except:
        pass

    # Проверяем, есть ли пользователь в БД
    user = await session.get(User, user_id)

    if not user:
        # Создаём нового пользователя
        user = User(
            id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name
        )
        session.add(user)
        await session.commit()

    # Обновляем активность ПОСЛЕ того, как пользователь точно есть в БД
    await update_user_activity(session, user_id)

    # Приветственное сообщение
    first_name = message.from_user.first_name or "друг"

    welcome_text = (
        f"👋 <b>Привет, {first_name}!</b>\n\n"
        f"Я <b>GenauLingua</b> — твой помощник в изучении немецкого языка! 🇩🇪\n\n"
        f"🎯 <b>Что я умею:</b>\n"
        f"📚 Викторины со словами разных уровней\n"
        f"🔄 Повтор ошибок для лучшего запоминания\n"
        f"📊 Статистика твоего прогресса\n"
        f"⚙️ Настройка уровня сложности\n\n"
    )

    if user.level:
        welcome_text += f"Твой текущий уровень: <b>{user.level.value}</b>\n\n"
        welcome_text += "Выбери действие из меню ниже 👇"

        # Создаём новый якорь СРАЗУ (возвращает old_anchor_id, new_anchor_id)
        old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="🏠")

        # Удаляем всё старое параллельно (быстро!)
        if old_anchor_id:
            current_msg_id = message.message_id
            await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

        # Отправляем приветствие
        await message.answer(welcome_text)
    else:
        welcome_text += "Для начала выбери свой уровень немецкого:"

        await message.answer(welcome_text)
        await message.answer(
            "Выбери уровень:",
            reply_markup=get_level_keyboard()
        )

        await state.set_state(QuizStates.choosing_level)


@router.callback_query(F.data.startswith("level_"))
async def select_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Обработчик выбора уровня"""
    level = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # Сохраняем выбранный уровень
    user = await session.get(User, user_id)
    user.level = level
    await session.commit()

    # Удаляем сообщение с выбором уровня
    await callback.message.delete()

    # Создаём новый якорь СРАЗУ
    old_anchor_id, new_anchor_id = await ensure_anchor(callback.message, session, user, emoji="🏠")

    # Удаляем всё старое параллельно
    if old_anchor_id:
        current_msg_id = callback.message.message_id
        await delete_messages_fast(callback.bot, callback.message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем подтверждение
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"✅ Отлично! Уровень {level} выбран.\n\nВыбери действие:"
    )

    await state.clear()
    await callback.answer()


@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message, session: AsyncSession):
    """Справка по боту"""
    user_id = message.from_user.id
    user = await session.get(User, user_id)

    help_text = (
        "❓ <b>Помощь — GenauLingua Bot</b>\n\n"
        "🎯 <b>Основные функции:</b>\n\n"
        "📚 <b>Учить слова</b>\n"
        "Викторина из 25 слов с 4 вариантами ответов.\n"
        "Выбирай правильный перевод и улучшай свой словарный запас!\n\n"
        "📊 <b>Статистика</b>\n"
        "Смотри свой прогресс: количество правильных ответов,\n"
        "процент успешности, история последних викторин.\n\n"
        "⚙️ <b>Настройки</b>\n"
        "Меняй уровень сложности от A1 до C2.\n"
        "Выбирай уровень, который соответствует твоим знаниям.\n\n"
        "🔄 <b>Повтор ошибок</b>\n"
        "После викторины можешь повторить только те слова,\n"
        "в которых допустил ошибки.\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "📝 <b>Уровни CEFR:</b>\n"
        "• A1 — Начальный\n"
        "• A2 — Элементарный\n"
        "• B1 — Средний\n"
        "• B2 — Средне-продвинутый\n"
        "• C1 — Продвинутый\n"
        "• C2 — Свободное владение\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "💡 <b>Команды:</b>\n"
        "/start — Перезапустить бота\n"
        "/help — Эта справка\n"
        "/stats — Статистика\n"
        "/settings — Настройки\n\n"
        "Удачи в изучении немецкого! 🇩🇪✨"
    )

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass

    # Создаём новый якорь СРАЗУ
    old_anchor_id, new_anchor_id = await ensure_anchor(message, session, user, emoji="❓")

    # Удаляем всё старое параллельно
    if old_anchor_id:
        current_msg_id = message.message_id
        await delete_messages_fast(message.bot, message.chat.id, old_anchor_id, current_msg_id)

    # Отправляем справку
    await message.answer(help_text)