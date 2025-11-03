"""
Скрипт для импорта слов из CSV файла в базу данных
"""
import asyncio
import csv
from pathlib import Path
from typing import Optional, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.database.models import Base, Word, PartOfSpeech, CEFRLevel


# Настройки подключения к БД
DATABASE_URL = "postgresql+asyncpg://genau_user:genau_password@localhost:5432/genaulingua_db"


def parse_categories(categories_str: Optional[str]) -> List[str]:
    """Парсинг категорий из строки"""
    if not categories_str or categories_str.strip() == "":
        return []
    return [cat.strip() for cat in categories_str.split("|") if cat.strip()]


def parse_pos(pos_str: str) -> PartOfSpeech:
    """Конвертация части речи из строки в enum"""
    pos_mapping = {
        "noun": PartOfSpeech.NOUN,
        "verb": PartOfSpeech.VERB,
        "adjective": PartOfSpeech.ADJECTIVE,
        "adverb": PartOfSpeech.ADVERB,
        "phrase": PartOfSpeech.PHRASE,
        "pronoun": PartOfSpeech.PRONOUN,
        "preposition": PartOfSpeech.PREPOSITION,
        "conjunction": PartOfSpeech.CONJUNCTION,
    }
    return pos_mapping.get(pos_str.lower(), PartOfSpeech.OTHER)


def clean_string(value: Optional[str]) -> Optional[str]:
    """Очистка строки от лишних пробелов и пустых значений"""
    if not value or value.strip() == "":
        return None
    return value.strip()


async def import_words_from_csv(
    csv_path: str,
    level: CEFRLevel = CEFRLevel.A1,
    clear_existing: bool = False
):
    """
    Импорт слов из CSV файла
    
    Args:
        csv_path: Путь к CSV файлу
        level: Уровень CEFR для всех слов
        clear_existing: Удалить существующие слова перед импортом
    """
    # Создание подключения к БД
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    # Создание таблиц если их нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        # Очистка существующих слов если нужно
        if clear_existing:
            print("🗑️ Удаление существующих слов...")
            await session.execute(select(Word))
            await session.commit()
            print("✅ Существующие слова удалены")
        
        # Чтение CSV
        csv_file = Path(csv_path)
        if not csv_file.exists():
            print(f"❌ Файл не найден: {csv_path}")
            return
        
        print(f"📖 Чтение файла: {csv_path}")
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            words_added = 0
            words_skipped = 0
            
            for row_num, row in enumerate(reader, start=2):  # start=2 т.к. первая строка - заголовки
                try:
                    # Пропускаем пустые строки или строки без немецкого слова
                    word_de = clean_string(row.get('word_de'))
                    if not word_de:
                        words_skipped += 1
                        print(f"⚠️ Строка {row_num}: пропущена (пустое немецкое слово)")
                        continue
                    
                    # Проверяем есть ли хотя бы один перевод
                    translation_ru = clean_string(row.get('translation_ru'))
                    translation_uk = clean_string(row.get('translation_uk'))
                    
                    if not translation_ru and not translation_uk:
                        words_skipped += 1
                        print(f"⚠️ Строка {row_num}: пропущена '{word_de}' (нет переводов)")
                        continue
                    
                    # Создание объекта слова
                    word = Word(
                        word_de=word_de,
                        article=clean_string(row.get('article')),
                        pos=parse_pos(clean_string(row.get('pos', 'other')) or 'other'),
                        level=level,
                        translation_ru=translation_ru,
                        translation_uk=translation_uk,
                        example_de=clean_string(row.get('example_de')),
                        example_ru=clean_string(row.get('example_ru')),
                        example_uk=clean_string(row.get('example_uk')),
                        categories=parse_categories(row.get('categories'))
                    )
                    
                    session.add(word)
                    words_added += 1
                    
                    # Коммитим каждые 100 слов
                    if words_added % 100 == 0:
                        await session.commit()
                        print(f"💾 Сохранено {words_added} слов...")
                
                except Exception as e:
                    print(f"❌ Ошибка в строке {row_num}: {e}")
                    print(f"   Данные: {row}")
                    words_skipped += 1
                    continue
            
            # Финальный коммит
            await session.commit()
            
            print("\n" + "="*50)
            print(f"✅ Импорт завершён!")
            print(f"📊 Добавлено слов: {words_added}")
            print(f"⚠️ Пропущено строк: {words_skipped}")
            print("="*50)
    
    await engine.dispose()


async def main():
    """Основная функция"""
    import sys
    
    # Путь к CSV файлу
    csv_path = "Word base/A1/A1 cvc/A1_missing_90_words.csv"
    
    # Параметры из аргументов командной строки
    level_str = sys.argv[1] if len(sys.argv) > 1 else "A1"
    clear_existing = "--clear" in sys.argv
    
    # Конвертация уровня
    level_mapping = {
        "A1": CEFRLevel.A1,
        "A2": CEFRLevel.A2,
        "B1": CEFRLevel.B1,
        "B2": CEFRLevel.B2,
        "C1": CEFRLevel.C1,
        "C2": CEFRLevel.C2,
    }
    level = level_mapping.get(level_str.upper(), CEFRLevel.A1)
    
    print(f"🚀 Запуск импорта...")
    print(f"📁 Файл: {csv_path}")
    print(f"📚 Уровень: {level.value}")
    print(f"🗑️ Очистка БД: {'Да' if clear_existing else 'Нет'}")
    print()
    
    await import_words_from_csv(
        csv_path=csv_path,
        level=level,
        clear_existing=clear_existing
    )


if __name__ == "__main__":
    asyncio.run(main())
