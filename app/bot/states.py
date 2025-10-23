from aiogram.fsm.state import State, StatesGroup


class QuizStates(StatesGroup):
    # Выбор уровня
    choosing_level = State()

    # Прохождение викторины
    answering = State()

    # Просмотр результатов
    viewing_results = State()

    # Повтор ошибок
    repeating_errors = State()