import random
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.enums import CEFRLevel
from app.database.models import Word, PartOfSpeech, UserWord, User
from typing import Optional

# ==================== КОНСТАНТЫ SRS ====================
MIN_ATTEMPTS_FOR_LEARNED = 3
LEARNED_SUCCESS_RATE = 90
LEARNED_SHOW_PROBABILITY = 0.01

STRUGGLING_WORDS_RATIO = 0.60
NEW_WORDS_RATIO = 0.30
REVIEW_WORDS_RATIO = 0.09
LEARNED_WORDS_RATIO = 0.01

STRUGGLING_THRESHOLD = 70
REVIEW_THRESHOLD = 90


async def generate_question(
        level: CEFRLevel,
        session: AsyncSession,
        user_id: int,
        exclude_ids: list[int] = None,
        mode: str = "DE_TO_RU"
) -> dict | None:
    if exclude_ids is None:
        exclude_ids = []

    correct_word = await select_word_by_priority(
        user_id=user_id,
        level=level,
        session=session,
        exclude_ids=exclude_ids
    )

    if not correct_word:
        return None

    distractors = await get_distractors(correct_word, session)

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
    if mode.value in ("ru_to_de", "uk_to_de"):
        # RU→DE или UK→DE: показываем немецкие слова как варианты
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

    elif mode.value == "de_to_uk":
        # DE→UK: показываем украинские переводы как варианты
        options = [(correct_word.id, correct_word.translation_uk.capitalize())]
        options.extend([(d.id, d.translation_uk.capitalize()) for d in distractors[:3]])

    else:  # de_to_ru
        # DE→RU: показываем русские переводы как варианты
        options = [(correct_word.id, correct_word.translation_ru.capitalize())]
        options.extend([(d.id, d.translation_ru.capitalize()) for d in distractors[:3]])

    random.shuffle(options)

    correct_answer_index = next(
        i for i, (word_id, _) in enumerate(options)
        if word_id == correct_word.id
    )

    return {
        'correct_word': correct_word,
        'options': options,
        'correct_answer_index': correct_answer_index
    }


async def select_word_by_priority(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
    rand = random.random()

    if rand < STRUGGLING_WORDS_RATIO:
        word = await get_struggling_words(user_id, level, session, exclude_ids)
        if word:
            return word

    if rand < STRUGGLING_WORDS_RATIO + NEW_WORDS_RATIO:
        word = await get_new_words(user_id, level, session, exclude_ids)
        if word:
            return word

    if rand < STRUGGLING_WORDS_RATIO + NEW_WORDS_RATIO + REVIEW_WORDS_RATIO:
        word = await get_review_words(user_id, level, session, exclude_ids)
        if word:
            return word

    word = await get_learned_words(user_id, level, session, exclude_ids)
    if word:
        return word

    return await get_any_word(user_id, level, session, exclude_ids)


async def get_struggling_words(
        user_id: int,
        level: CEFRLevel,
        session: AsyncSession,
        exclude_ids: list[int]
) -> Optional[Word]:
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
            (UserWord.times_correct * 100.0 / UserWord.times_shown) < STRUGGLING_THRESHOLD,
            or_(
                UserWord.last_seen_at.is_(None),
                UserWord.last_seen_at < one_hour_ago
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
    seen_words_query = (
        select(UserWord.word_id)
        .where(UserWord.user_id == user_id)
    )
    seen_result = await session.execute(seen_words_query)
    seen_word_ids = [row[0] for row in seen_result.all()]

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
                UserWord.last_seen_at < one_hour_ago
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
    query = select(Word).where(Word.level == level)

    if exclude_ids:
        query = query.where(Word.id.not_in(exclude_ids))

    result = await session.execute(query)
    words = result.scalars().all()

    return random.choice(words) if words else None


async def get_distractors(word: Word, session: AsyncSession) -> list[Word]:
    query = select(Word).where(
        Word.id != word.id,
        Word.level == word.level,
        Word.pos == word.pos
    )

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


async def update_word_progress(
        user_id: int,
        word_id: int,
        is_correct: bool,
        session: AsyncSession
) -> None:
    word = await session.get(Word, word_id)
    if word:
        word.times_shown += 1
        if is_correct:
            word.times_correct += 1

    result = await session.execute(
        select(UserWord).where(
            UserWord.user_id == user_id,
            UserWord.word_id == word_id
        )
    )
    user_word = result.scalar_one_or_none()

    if not user_word:
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
        user_word.last_seen_at = datetime.utcnow()
        user_word.times_shown += 1

        if is_correct:
            user_word.correct_streak += 1
            user_word.times_correct += 1
        else:
            user_word.correct_streak = 0

    if user_word.correct_streak >= MIN_ATTEMPTS_FOR_LEARNED:
        user_word.learned = True
    else:
        user_word.learned = False

    await session.commit()


async def get_user_progress_stats(user_id: int, level: CEFRLevel, session: AsyncSession) -> dict:
    total_result = await session.execute(
        select(func.count(Word.id)).where(Word.level == level)
    )
    total_words = total_result.scalar()

    seen_result = await session.execute(
        select(func.count(UserWord.word_id))
        .where(UserWord.user_id == user_id)
        .join(Word, Word.id == UserWord.word_id)
        .where(Word.level == level)
    )
    seen_words = seen_result.scalar()

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