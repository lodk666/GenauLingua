import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from import_csv import import_words_from_csv, DATABASE_URL


async def main():
    files = [
        ("13.csv", "Основной файл"),
        ("A1_missing_90_words.csv", "90 недостающих слов"),
        ("A1_additional_71_words.csv", "71 дополнительное слово")
    ]

    total_imported = 0

    for filename, description in files:
        print(f"\n{'=' * 60}")
        print(f"📥 Импорт: {description}")
        print(f"📁 Файл: {filename}")
        print('=' * 60)

        await import_words_from_csv(
            csv_path=filename,
            level="A1",
            clear_existing=False
        )

    print(f"\n{'=' * 60}")
    print("✅ ВСЕ ФАЙЛЫ ИМПОРТИРОВАНЫ!")
    print('=' * 60)


if __name__ == "__main__":
    asyncio.run(main())