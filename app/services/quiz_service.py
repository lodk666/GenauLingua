import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import Word, CEFRLevel, PartOfSpeech


async def generate_question(level: str, session: AsyncSession, exclude_ids: list[int] = None,
                            mode: str = "DE_TO_RU") -> dict | None:
    """Генерирует вопрос для викторины"""
    if exclude_ids is None:
        exclude_ids = []

    # Получаем слова, исключая уже использованные
    query = select(Word).where(Word.level == level)

    if exclude_ids:
        query = query.where(Word.id.not_in(exclude_ids))

    result = await session.execute(query)
    words = result.scalars().all()

    if not words:
        return None

    correct_word = random.choice(words)
    distractors = await get_distractors(correct_word, session)

    if len(distractors) < 3:
        all_other = [w for w in words if w.id != correct_word.id and w not in distractors]
        if all_other:
            needed = min(3 - len(distractors), len(all_other))
            distractors.extend(random.sample(all_other, needed))

    # Формируем варианты ответов в зависимости от режима
    if mode == "RU_TO_DE":
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

    random.shuffle(options)

    correct_answer_index = next(i for i, (word_id, _) in enumerate(options) if word_id == correct_word.id)

    return {
        'correct_word': correct_word,
        'options': options,
        'correct_answer_index': correct_answer_index
    }

async def get_distractors(word: Word, session: AsyncSession) -> list[Word]:
    """Подбирает дистракторы для слова"""
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