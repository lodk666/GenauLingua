import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import MasterWord, CEFRLevel, PartOfSpeech


async def generate_question(level: str, session: AsyncSession, exclude_ids: list[int] = None,
                            mode: str = "DE-RU") -> dict | None:
    """Генерирует вопрос для викторины"""
    if exclude_ids is None:
        exclude_ids = []

    # Получаем слова, исключая уже использованные
    query = select(MasterWord).where(MasterWord.cefr == level)

    if exclude_ids:
        query = query.where(MasterWord.id.not_in(exclude_ids))

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
    if mode == "RU-DE":
        # RU→DE: показываем немецкие слова как варианты
        options = []
        correct_display = correct_word.lemma
        if correct_word.article and correct_word.article.value != '-':
            correct_display = f"{correct_word.article.value} {correct_word.lemma}"

        options.append((correct_word.id, correct_display))

        for d in distractors[:3]:
            distractor_display = d.lemma
            if d.article and d.article.value != '-':
                distractor_display = f"{d.article.value} {d.lemma}"
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