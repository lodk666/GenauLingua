import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import MasterWord, CEFRLevel, PartOfSpeech


async def generate_question(level: str, session: AsyncSession) -> dict | None:
    """Генерирует вопрос для викторины"""
    result = await session.execute(
        select(MasterWord).where(MasterWord.cefr == level)
    )
    words = result.scalars().all()

    if not words:
        return None

    correct_word = random.choice(words)
    distractors = await get_distractors(correct_word, session)

    if len(distractors) < 3:
        all_other = [w for w in words if w.id != correct_word.id and w not in distractors]
        distractors.extend(random.sample(all_other, min(3 - len(distractors), len(all_other))))

    options = [(correct_word.id, correct_word.translation_ru)]
    options.extend([(d.id, d.translation_ru) for d in distractors[:3]])
    random.shuffle(options)

    correct_answer_index = next(i for i, (word_id, _) in enumerate(options) if word_id == correct_word.id)

    return {
        'correct_word': correct_word,
        'options': options,
        'correct_answer_index': correct_answer_index
    }


async def get_distractors(word: MasterWord, session: AsyncSession) -> list[MasterWord]:
    """Подбирает дистракторы для слова"""
    query = select(MasterWord).where(
        MasterWord.id != word.id,
        MasterWord.cefr == word.cefr,
        MasterWord.pos == word.pos
    )

    if word.pos == PartOfSpeech.NOUN and word.article:
        query = query.where(MasterWord.article != word.article)

    result = await session.execute(query)
    candidates = result.scalars().all()

    if len(candidates) >= 3:
        return random.sample(candidates, 3)

    return list(candidates)