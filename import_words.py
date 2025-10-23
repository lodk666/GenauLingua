import asyncio
import re
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.database.models import MasterWord, Category, WordCategory, CEFRLevel, Article, PartOfSpeech


async def parse_word_line(line: str) -> dict | None:
    """Парсит строку формата | слово | перевод |"""
    # Убираем пробелы и разделяем по |
    parts = [p.strip() for p in line.split('|') if p.strip()]

    if len(parts) < 2:
        return None

    word_raw = parts[0]
    translation_raw = parts[1]

    # Убираем пометки из перевода: *(наречие)*, *(прилагательное)* и т.д.
    translation = re.sub(r'\s*\*\([^)]+\)\*', '', translation_raw).strip()

    # Определяем артикль и часть речи
    article = Article.NONE
    pos = PartOfSpeech.OTHER
    lemma = word_raw

    # Проверяем артикли
    if word_raw.startswith('der '):
        article = Article.DER
        lemma = word_raw[4:]
        pos = PartOfSpeech.NOUN
    elif word_raw.startswith('die '):
        article = Article.DIE
        lemma = word_raw[4:]
        pos = PartOfSpeech.NOUN
    elif word_raw.startswith('das '):
        article = Article.DAS
        lemma = word_raw[4:]
        pos = PartOfSpeech.NOUN
    else:
        # Определяем часть речи без артикля
        if '*(прилагательное)*' in translation_raw or '*(прич.)*' in translation_raw:
            pos = PartOfSpeech.ADJECTIVE
        elif '*(наречие)*' in translation_raw:
            pos = PartOfSpeech.ADVERB
        elif lemma.endswith(('en', 'n')) and not lemma.endswith(('nen', 'len', 'ren', 'sen')):
            # Вероятно глагол (оканчивается на -en)
            # Но исключаем существительные типа "Kissen"
            if not word_raw[0].isupper():  # Глаголы с маленькой буквы
                pos = PartOfSpeech.VERB
        elif '*(местоимение)*' in translation_raw or '*(предлог)*' in translation_raw or '*(союз)*' in translation_raw or '*(междометие)*' in translation_raw:
            pos = PartOfSpeech.OTHER

    # Убираем пометки типа *(Pl.)* из леммы
    lemma = re.sub(r'\s*\*\([^)]+\)\*', '', lemma).strip()

    # Определяем категорию по смыслу (базовая логика)
    categories = determine_category(lemma, translation)

    return {
        'lemma': lemma,
        'article': article,
        'pos': pos,
        'translation_ru': translation,
        'categories': categories
    }


def determine_category(lemma: str, translation: str) -> list[str]:
    """Определяет категорию слова"""
    categories = []

    # Словарь ключевых слов → категории
    keywords = {
        'еда': ['Brot', 'Butter', 'Käse', 'Fleisch', 'Ei', 'Kuchen', 'Salat', 'Suppe', 'Essen'],
        'напитки': ['Wasser', 'Milch', 'Kaffee', 'Tee', 'Saft', 'Bier', 'Wein'],
        'семья': ['Mutter', 'Vater', 'Kind', 'Sohn', 'Tochter', 'Familie', 'Eltern', 'Großeltern'],
        'дом': ['Haus', 'Wohnung', 'Zimmer', 'Küche', 'Bad', 'Tür', 'Fenster'],
        'мебель': ['Tisch', 'Stuhl', 'Bett', 'Schrank', 'Lampe'],
        'транспорт': ['Auto', 'Bus', 'Zug', 'Fahrrad', 'Flugzeug'],
        'учёба': ['Schule', 'Lehrer', 'Schüler', 'Buch', 'Heft', 'lernen', 'lesen', 'schreiben'],
        'работа': ['Arbeit', 'Beruf', 'arbeiten'],
        'время': ['Tag', 'Jahr', 'Monat', 'Woche', 'Stunde', 'Minute', 'Uhr', 'Zeit'],
        'погода': ['Wetter', 'Sonne', 'Regen', 'Schnee'],
        'животные': ['Hund', 'Katze', 'Tier', 'Pferd'],
        'город': ['Stadt', 'Straße', 'Park', 'Supermarkt'],
        'люди': ['Mann', 'Frau', 'Freund', 'Freundin', 'Leute'],
    }

    for category, words in keywords.items():
        if lemma in words:
            categories.append(category)

    # Если категорий нет — ставим общую
    if not categories:
        categories = ['базовые слова']

    return categories


async def import_words():
    """Импортирует слова из файла в БД"""
    print("🚀 Начинаем импорт слов...")

    async with AsyncSessionLocal() as session:
        # Читаем файл
        try:
            with open('words_goethe_a1.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print("❌ Файл words_goethe_a1.txt не найден!")
            return

        print(f"📄 Прочитано {len(lines)} строк")

        imported_count = 0
        skipped_count = 0

        for line in lines:
            line = line.strip()

            # Пропускаем пустые строки и заголовки
            if not line or 'Немецкое слово' in line or 'Перевод' in line:
                continue

            # Парсим строку
            word_data = await parse_word_line(line)

            if not word_data:
                skipped_count += 1
                continue

            # Проверяем, есть ли уже такое слово
            result = await session.execute(
                select(MasterWord).where(
                    MasterWord.lemma == word_data['lemma'],
                    MasterWord.cefr == CEFRLevel.A1
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                skipped_count += 1
                continue

            # Создаём слово
            word = MasterWord(
                lemma=word_data['lemma'],
                article=word_data['article'],
                pos=word_data['pos'],
                cefr=CEFRLevel.A1,
                translation_ru=word_data['translation_ru'],
                example_de=None,
                example_ru=None,
                plural=None,
                separable_prefix=None
            )

            session.add(word)
            await session.flush()

            # Добавляем категории
            for cat_name in word_data['categories']:
                # Ищем или создаём категорию
                result = await session.execute(
                    select(Category).where(Category.slug == cat_name)
                )
                category = result.scalar_one_or_none()

                if not category:
                    category = Category(
                        slug=cat_name,
                        title_ru=cat_name.capitalize()
                    )
                    session.add(category)
                    await session.flush()

                # Связываем слово с категорией
                word_cat = WordCategory(
                    word_id=word.id,
                    category_id=category.id,
                    weight=1
                )
                session.add(word_cat)

            imported_count += 1

            if imported_count % 50 == 0:
                print(f"✅ Импортировано {imported_count} слов...")

        await session.commit()

        print(f"\n🎉 Импорт завершён!")
        print(f"✅ Импортировано: {imported_count} слов")
        print(f"⏭️ Пропущено: {skipped_count} строк")


if __name__ == "__main__":
    asyncio.run(import_words())