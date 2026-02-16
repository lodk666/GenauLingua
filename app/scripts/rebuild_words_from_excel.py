import asyncio
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


# ---------------------------
# Настройка подключения к БД
# ---------------------------

def load_dotenv_if_exists(project_root: Path) -> None:
    """
    Мини-лоадер .env без зависимости python-dotenv.
    Поддержка строк вида KEY=VALUE (без хитрых кавычек).
    """
    env_path = project_root / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


def get_database_url(project_root: Path) -> str:
    """
    Приоритет:
    1) DATABASE_URL из env
    2) DATABASE_URL_ASYNC из env (если у тебя так называется)
    3) Собрать дефолт под локальный docker compose postgres
    """
    load_dotenv_if_exists(project_root)

    db_url = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_URL_ASYNC")
    if db_url:
        # если у тебя синхронный драйвер postgresql://, переведём в asyncpg
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return db_url

    # Дефолт: под твой контейнер с пробросом 5432 наружу
    # ⚠️ пароль подставь свой, если он не "genau_password"
    user = os.environ.get("POSTGRES_USER", "genau_user")
    password = os.environ.get("POSTGRES_PASSWORD", "genau_password")
    host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("POSTGRES_PORT", "5432")
    dbname = os.environ.get("POSTGRES_DB", "genaulingua_db")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"


# ---------------------------
# Excel -> DB
# ---------------------------

COLUMN_ALIASES = {
    "Слово (DE)": "word_de",
    "Слово": "word_de",
    "word_de": "word_de",

    "Артикль": "article",
    "article": "article",

    "POS": "pos",
    "pos": "pos",

    "Перевод (RU)": "translation_ru",
    "translation_ru": "translation_ru",

    "Переклад (UA)": "translation_uk",
    "Перeклад (UA)": "translation_uk",
    "translation_uk": "translation_uk",

    "Пример (DE)": "example_de",
    "example_de": "example_de",

    "Пример (RU)": "example_ru",
    "example_ru": "example_ru",

    "Приклад (UA)": "example_uk",
    "example_uk": "example_uk",

    "Категории": "categories",
    "categories": "categories",
}

ALLOWED_POS = {
    "NOUN", "VERB", "ADJECTIVE", "ADVERB", "PHRASE",
    "PRONOUN", "PREPOSITION", "CONJUNCTION", "OTHER"
}

POS_MAP = {
    "noun": "NOUN",
    "n": "NOUN",
    "verb": "VERB",
    "v": "VERB",
    "adjective": "ADJECTIVE",
    "adj": "ADJECTIVE",
    "adverb": "ADVERB",
    "adv": "ADVERB",
    "phrase": "PHRASE",
    "pronoun": "PRONOUN",
    "preposition": "PREPOSITION",
    "prep": "PREPOSITION",
    "conjunction": "CONJUNCTION",
    "conj": "CONJUNCTION",

    # всё прочее — в OTHER, чтобы импорт не падал
    "particle": "OTHER",
    "numeral": "OTHER",
    "interjection": "OTHER",
    "article": "OTHER",
    "determiner": "OTHER",
    "modal": "OTHER",
    "aux": "OTHER",
    "other": "OTHER",
}


def s(x) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    return str(x).strip()


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        c_str = str(c).strip()
        if c_str in COLUMN_ALIASES:
            rename[c_str] = COLUMN_ALIASES[c_str]
    return df.rename(columns=rename)


def parse_categories(raw) -> list[str]:
    raw = s(raw)
    if not raw:
        return []
    sep = ";" if ";" in raw else ","
    out = [p.strip() for p in raw.split(sep)]
    return [p for p in out if p]


async def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    words_dir = project_root / "Words"

    files = [
        ("А1 v2(ua).xlsx", "A1"),
        ("А2 v2(ua).xlsx", "A2"),
        ("В1 v2(ua).xlsx", "B1"),
    ]

    db_url = get_database_url(project_root)
    print(f"🔌 DB: {db_url}")

    engine = create_async_engine(db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # created_at NOT NULL -> NOW()
    # categories NOT NULL -> :categories (передаем list[str], может быть пустым)
    insert_sql = text("""
        INSERT INTO words
          (word_de, article, pos, level,
           translation_ru, translation_uk,
           example_de, example_ru, example_uk,
           categories, times_shown, times_correct, created_at)
        VALUES
          (:word_de, :article,
           CAST(:pos AS partofspeech),
           CAST(:level AS cefrlevel),
           :translation_ru, :translation_uk,
           :example_de, :example_ru, :example_uk,
           :categories, 0, 0, NOW())
    """)

    async with Session() as session:
        print("🗑️ TRUNCATE: words + user progress + quiz_*")

        # Если у тебя названия quiz-таблиц отличаются — поменяешь тут.
        # words чистим последней, чтобы CASCADE сработал корректно.
        await session.execute(text("TRUNCATE TABLE user_words CASCADE"))
        await session.execute(text("TRUNCATE TABLE quiz_questions CASCADE"))
        await session.execute(text("TRUNCATE TABLE quiz_sessions CASCADE"))
        await session.execute(text("TRUNCATE TABLE words RESTART IDENTITY CASCADE"))
        await session.commit()

        inserted_total = 0

        for filename, level in files:
            path = words_dir / filename
            if not path.exists():
                raise FileNotFoundError(f"Не найден файл: {path}")

            print(f"📚 Импорт {level}: {path.name}")

            df = pd.read_excel(path)
            df = normalize_df(df)

            required = ["word_de", "article", "pos", "example_de", "translation_ru"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                raise RuntimeError(
                    f"{path.name}: не найдены колонки {missing}. "
                    f"Найдено: {list(df.columns)}"
                )

            inserted = 0
            skipped = 0

            for _, row in df.iterrows():
                word_de = s(row.get("word_de"))
                if not word_de:
                    skipped += 1
                    continue

                raw_pos = s(row.get("pos")).lower()
                pos = POS_MAP.get(raw_pos, "OTHER")
                if pos not in ALLOWED_POS:
                    pos = "OTHER"

                payload = {
                    "word_de": word_de,
                    "article": s(row.get("article")) or "-",
                    "pos": pos,
                    "level": level,
                    "translation_ru": s(row.get("translation_ru")),
                    "translation_uk": s(row.get("translation_uk")),
                    "example_de": s(row.get("example_de")),
                    "example_ru": s(row.get("example_ru")),
                    "example_uk": s(row.get("example_uk")),
                    "categories": parse_categories(row.get("categories")),
                }

                await session.execute(insert_sql, payload)
                inserted += 1
                inserted_total += 1

                if inserted % 300 == 0:
                    await session.commit()
                    print(f"  ✅ {level}: {inserted}...")

            await session.commit()
            print(f"✅ {level}: импортировано {inserted}, пропущено {skipped}\n")

        print(f"🎉 ГОТОВО. Всего слов залито: {inserted_total}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
