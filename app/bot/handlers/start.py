from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.states import QuizStates
from app.bot.keyboards import get_level_keyboard, get_main_menu_keyboard
from app.database.models import User

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    await message.delete()

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

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я помогу тебе учить немецкие слова.\n"
        f"Выбери свой уровень:",
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
    user.selected_level = level
    await session.commit()

    # Удаляем сообщение с выбором уровня
    await callback.message.delete()

    # Отправляем только меню
    await callback.message.answer(
        f"✅ Отлично! Уровень {level} выбран.\n\n"
        f"Выбери действие:",
        reply_markup=get_main_menu_keyboard()
    )

    await state.clear()
    await callback.answer()