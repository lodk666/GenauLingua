import random
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.enums import CEFRLevel
from app.database.models import Word, PartOfSpeech, UserWord, User
from typing import Optional

# ==================== КОНСТАНТЫ SRS ====================
MIN_ATTEMPTS_FOR_LEARNED = 3  # Минимум 3 раза нужно показать слово
LEARNED_SUCCESS_RATE = 90  # 90%+ правильных = выучено
LEARNED_SHOW_PROBABILITY = 0.01  # 1% вероятность показа выученного слова

# Распределение типов слов в викторине (25 вопросов)
STRUGGLING_WORDS_RATIO = 0.60  # 60% (15 слов) - слова с ошибками
NEW_WORDS_RATIO = 0.30  # 30% (7 слов) - новые слова
REVIEW_WORDS_RATIO = 0.09  # 9% (2 слова) - на повторение
LEARNED_WORDS_RATIO = 0.01  # 1% (1 слово) - выученные

# Пороги success_rate для категорий
STRUGGLING_THRESHOLD = 70  # < 70% = сложное слово
REVIEW_THRESHOLD = 90  # 70-90% = на повторение


# > 90% = выученное


# ==================== ОСНОВНАЯ ФУНКЦИЯ ГЕНЕРАЦИИ ВОПРОСА ====================
async def generate_question(
        level: CEFRLevel,
        session: AsyncSession,
        user_id: int,
        exclude_ids: list[int] = None,
        mode: str = "DE_TO_RU"
) -> dict | None:
    """
    Генерирует вопрос для викторины с учётом персонального прогресса (SRS)

    Args:
        level: Уровень сложности (A1, A2, B1, B2, C1, C2)
        session: Сессия БД
        user_id: ID пользователя
        exclude_ids: Список ID слов, которые уже были в викторине
        mode: Режим перевода (DE_TO_RU или RU_TO_DE)

    Returns:
        dict с correct_word, options, correct_answer_index или None
    """
    if exclude_ids is None:
        exclude_ids = []

    # Выбираем слово по приоритету SRS
    correct_word = await select_word_by_priority(
        user_id=user_id,
        level=level,
        session=session,
        exclude_ids=exclude_ids
    )

    if not correct_word:
        return None

    # Подбираем дистракторы (неправильные варианты)
    distractors = await get_distractors(correct_word, session)

    # Если дистракторов меньше 3 - добираем случайных
    if len(distractors) < 3:
        additional = await get_additional_distractors(
            correct_word=correct_word,
            current_distractors=distractors,
            level=level,
            session=session,
            count=3 - len(distractors)
        )
        distractors.extend(additional)

    # Формируем варианты ответов в зависимости от режима
    if mode.value == "ru_to_de":
        # RU→DE: показываем немецкие слова как варианты
        options = []
        correct_display = correct_word.word_de
        if correct_word.article and correct_word.article != '-':
            correct_display = f"{correct_word.article} {correct_word.word_de}"

        options.append((correct_word.id, correct_display))

        for d in distractors[:3]:
            distractor_display = d.word_de
            if d.article and d.article != '-':
                distractor_display = f"{d.article} {d.word_de}"
            options.append((d.id, distractor_display))
    else:
        # DE→RU: показываем русские переводы как варианты
        options = [(correct_word.id, correct_word.translation_ru.capitalize())]
        options.extend([(d.id, d.translation_ru.capitalize()) for d in distractors[:3]])

    # Перемешиваем варианты
    random.shuffle(options)

    # Находим индекс правильного ответа
    correct_answer_index = next(
        i for i, (word_id, _) in enumerate(options)
        if word_id == correct_word.id
    )

    return {
        'correct_word': correct_word,
        'options': options,
        'correct_answer_index': correct_answer_index
    }


# ==================== ВЫБОР СЛОВА ПО ПРИОРИТЕТУ SRS ====================
async def select_word_by_priority(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    """
    Выбирает слово по приоритету SRS (интервальные повторения)

    Приоритеты:
    1. Слова с ошибками (60% вероятность)
    2. Новые слова (30% вероятность)
    3. Слова на повторение (9% вероятность)
    4. Выученные слова (1% вероятность)
    """

    # Определяем категорию слова случайным образом с учётом вероятностей
    rand = random.random()

    if rand < STRUGGLING_WORDS_RATIO:
        # 60% - слова с ошибками
        word = await get_struggling_words(user_id, level, session, exclude_ids)
        if word:
            return word

    if rand < STRUGGLING_WORDS_RATIO + NEW_WORDS_RATIO:
        # 30% - новые слова
        word = await get_new_words(user_id, level, session, exclude_ids)
        if word:
            return word

    if rand < STRUGGLING_WORDS_RATIO + NEW_WORDS_RATIO + REVIEW_WORDS_RATIO:
        # 9% - слова на повторение
        word = await get_review_words(user_id, level, session, exclude_ids)
        if word:
            return word

    # 1% - выученные слова
    word = await get_learned_words(user_id, level, session, exclude_ids)
    if word:
        return word

    # Если ничего не нашли - берём любое новое слово
    return await get_any_word(user_id, level, session, exclude_ids)


# ==================== ПОЛУЧЕНИЕ СЛОВ ПО КАТЕГОРИЯМ ====================
async def get_struggling_words(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    """
    Возвращает слово с низким success_rate (< 70%)
    Это слова, в которых пользователь допускает ошибки
    """
    from datetime import timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    query = (
        select(Word)
        .join(UserWord, and_(
            UserWord.word_id == Word.id,
            UserWord.user_id == user_id
        ))
        .where(
            Word.level == level,
            UserWord.learned == False,
            UserWord.times_shown > 0,  # Должно быть хоть раз показано
            (UserWord.times_correct * 100.0 / UserWord.times_shown) < STRUGGLING_THRESHOLD,
            or_(
                UserWord.last_seen_at.is_(None),
                UserWord.last_seen_at < one_hour_ago  # Не показывали последний час
            )
        )
    )

    if exclude_ids:
        query = query.where(Word.id.not_in(exclude_ids))

    result = await session.execute(query)
    words = result.scalars().all()

    return random.choice(words) if words else None


async def get_new_words(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    """
    Возвращает новое слово (которое ещё не показывали пользователю)
    """
    # Получаем ID слов, которые уже видел пользователь
    seen_words_query = (
        select(UserWord.word_id)
        .where(UserWord.user_id == user_id)
    )
    seen_result = await session.execute(seen_words_query)
    seen_word_ids = [row[0] for row in seen_result.all()]

    # Выбираем слова, которых нет в seen_word_ids
    query = select(Word).where(
        Word.level == level,
        Word.id.not_in(seen_word_ids + exclude_ids)
    )

    result = await session.execute(query)
    words = result.scalars().all()

    return random.choice(words) if words else None


async def get_review_words(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    """
    Возвращает слово на повторение (success_rate 70-90%)
    Это слова, которые пользователь знает, но ещё не выучил идеально
    """
    from datetime import timedelta
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    query = (
        select(Word)
        .join(UserWord, and_(
            UserWord.word_id == Word.id,
            UserWord.user_id == user_id
        ))
        .where(
            Word.level == level,
            UserWord.learned == False,
            UserWord.times_shown > 0,
            and_(
                (UserWord.times_correct * 100.0 / UserWord.times_shown) >= STRUGGLING_THRESHOLD,
                (UserWord.times_correct * 100.0 / UserWord.times_shown) < REVIEW_THRESHOLD
            ),
            or_(
                UserWord.last_seen_at.is_(None),
                UserWord.last_seen_at < one_hour_ago  # Не показывали последний час
            )
        )
    )

    if exclude_ids:
        query = query.where(Word.id.not_in(exclude_ids))

    result = await session.execute(query)
    words = result.scalars().all()

    return random.choice(words) if words else None


async def get_learned_words(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    """
    Возвращает выученное слово (success_rate >= 90% и показано >= 3 раз)
    Показывается редко (1%), для закрепления
    """
    query = (
        select(Word)
        .join(UserWord, and_(
            UserWord.word_id == Word.id,
            UserWord.user_id == user_id
        ))
        .where(
            Word.level == level,
            UserWord.learned == True,
            UserWord.times_shown >= MIN_ATTEMPTS_FOR_LEARNED,
            (UserWord.times_correct * 100.0 / UserWord.times_shown) >= LEARNED_SUCCESS_RATE
        )
    )

    if exclude_ids:
        query = query.where(Word.id.not_in(exclude_ids))

    result = await session.execute(query)
    words = result.scalars().all()

    return random.choice(words) if words else None


async def get_any_word(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    """
    Возвращает любое слово (fallback, если другие категории пусты)
    """
    query = select(Word).where(Word.level == level)

    if exclude_ids:
        query = query.where(Word.id.not_in(exclude_ids))

    result = await session.execute(query)
    words = result.scalars().all()

    return random.choice(words) if words else None


# ==================== ДИСТРАКТОРЫ ====================
async def get_distractors(word: Word, session: AsyncSession) -> list[Word]:
    """
    Подбирает дистракторы (неправильные варианты) для слова

    Критерии:
    - Та же часть речи
    - Тот же уровень
    - Для существительных - другой артикль
    """
    query = select(Word).where(
        Word.id != word.id,
        Word.level == word.level,
        Word.pos == word.pos
    )

    # Для существительных подбираем с другим артиклем
    if word.pos == PartOfSpeech.NOUN and word.article:
        query = query.where(Word.article != word.article)

    result = await session.execute(query)
    candidates = result.scalars().all()

    if len(candidates) >= 3:
        return random.sample(candidates, 3)

    return list(candidates)


async def get_additional_distractors(
        correct_word: Word,
        current_distractors: list[Word],
        level: CEFRLevel,
        session: AsyncSession,
        count: int
) -> list[Word]:
    """
    Добирает недостающие дистракторы из всех слов уровня
    """
    exclude_ids = [correct_word.id] + [d.id for d in current_distractors]

    query = select(Word).where(
        Word.level == level,
        Word.id.not_in(exclude_ids)
    )

    result = await session.execute(query)
    words = result.scalars().all()

    if not words:
        return []

    return random.sample(words, min(count, len(words)))


# ==================== ОБНОВЛЕНИЕ ПРОГРЕССА ====================
async def update_word_progress(
        user_id: int,
        word_id: int,
        is_correct: bool,
        session: AsyncSession
) -> None:
    """
    Обновляет прогресс пользователя по слову после ответа

    Args:
        user_id: ID пользователя
        word_id: ID слова
        is_correct: Правильно ли ответил пользователь
        session: Сессия БД
    """
    # Обновляем глобальную статистику слова (для аналитики)
    word = await session.get(Word, word_id)
    if word:
        word.times_shown += 1
        if is_correct:
            word.times_correct += 1

    # Получаем или создаём запись UserWord
    result = await session.execute(
        select(UserWord).where(
            UserWord.user_id == user_id,
            UserWord.word_id == word_id
        )
    )
    user_word = result.scalar_one_or_none()

    if not user_word:
        # Создаём новую запись
        user_word = UserWord(
            user_id=user_id,
            word_id=word_id,
            correct_streak=1 if is_correct else 0,
            times_shown=1,
            times_correct=1 if is_correct else 0,
            last_seen_at=datetime.utcnow(),
            learned=False
        )
        session.add(user_word)
    else:
        # Обновляем существующую
        user_word.last_seen_at = datetime.utcnow()
        user_word.times_shown += 1

        if is_correct:
            user_word.correct_streak += 1
            user_word.times_correct += 1
        else:
            # Неправильный ответ - сбрасываем streak
            user_word.correct_streak = 0

    # Проверяем статус "выученного" по streak (серия правильных ответов подряд)
    # Если ответил правильно 3 раза подряд - выучено!
    if user_word.correct_streak >= MIN_ATTEMPTS_FOR_LEARNED:
        user_word.learned = True
    else:
        user_word.learned = False

    await session.commit()


# ==================== СТАТИСТИКА ====================
async def get_user_progress_stats(user_id: int, level: CEFRLevel, session: AsyncSession) -> dict:
    """
    Возвращает статистику прогресса пользователя по уровню

    Returns:
        {
            'total_words': int,
            'seen_words': int,
            'learned_words': int,
            'struggling_words': int,
            'new_words': int
        }
    """
    # Всего слов на уровне
    total_result = await session.execute(
        select(func.count(Word.id)).where(Word.level == level)
    )
    total_words = total_result.scalar()

    # Слова, которые видел пользователь
    seen_result = await session.execute(
        select(func.count(UserWord.word_id))
        .where(UserWord.user_id == user_id)
        .join(Word, Word.id == UserWord.word_id)
        .where(Word.level == level)
    )
    seen_words = seen_result.scalar()

    # Выученные слова
    learned_result = await session.execute(
        select(func.count(UserWord.word_id))
        .where(
            UserWord.user_id == user_id,
            UserWord.learned == True
        )
        .join(Word, Word.id == UserWord.word_id)
        .where(Word.level == level)
    )
    learned_words = learned_result.scalar()

    # Слова с ошибками
    struggling_result = await session.execute(
        select(func.count(Word.id))
        .join(UserWord, and_(
            UserWord.word_id == Word.id,
            UserWord.user_id == user_id
        ))
        .where(
            Word.level == level,
            UserWord.learned == False,
            UserWord.times_shown > 0,
            (UserWord.times_correct * 100.0 / UserWord.times_shown) < STRUGGLING_THRESHOLD
        )
    )
    struggling_words = struggling_result.scalar()

    return {
        'total_words': total_words or 0,
        'seen_words': seen_words or 0,
        'learned_words': learned_words or 0,
        'struggling_words': struggling_words or 0,
        'new_words': (total_words or 0) - (seen_words or 0)
    }


async def get_user_progress_stats_all_levels(user_id: int, session: AsyncSession) -> dict:
    """
    Возвращает статистику прогресса пользователя по всем уровням.

    Returns:
        {
            'total_words': int,
            'seen_words': int,
            'learned_words': int,
            'struggling_words': int,
            'new_words': int
        }
    """
    total_result = await session.execute(select(func.count(Word.id)))
    total_words = total_result.scalar()

    seen_result = await session.execute(
        select(func.count(UserWord.word_id))
        .where(UserWord.user_id == user_id)
    )
    seen_words = seen_result.scalar()

    learned_result = await session.execute(
        select(func.count(UserWord.word_id))
        .where(
            UserWord.user_id == user_id,
            UserWord.learned == True
        )
    )
    learned_words = learned_result.scalar()

    struggling_result = await session.execute(
        select(func.count(Word.id))
        .join(UserWord, and_(
            UserWord.word_id == Word.id,
            UserWord.user_id == user_id
        ))
        .where(
            UserWord.learned == False,
            UserWord.times_shown > 0,
            (UserWord.times_correct * 100.0 / UserWord.times_shown) < STRUGGLING_THRESHOLD
        )
    )
    struggling_words = struggling_result.scalar()

    return {
        'total_words': total_words or 0,
        'seen_words': seen_words or 0,
        'learned_words': learned_words or 0,
        'struggling_words': struggling_words or 0,
        'new_words': (total_words or 0) - (seen_words or 0)
    }
