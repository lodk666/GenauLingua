#!/usr/bin/env python3
"""
Рассылка обновления всем пользователям на их языке

Использование:
  1. Отредактируй тексты MESSAGES ниже
  2. Запусти: python app/scripts/broadcast_update.py
  3. Скрипт отправит каждому юзеру сообщение на его языке

Запуск:
  python app/scripts/broadcast_update.py          — отправить всем
  python app/scripts/broadcast_update.py --dry-run — только показать кому отправит (без отправки)
  python app/scripts/broadcast_update.py --test 463491762 — отправить только одному юзеру (для теста)
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


# ============================================================================
# СООБЩЕНИЯ — РЕДАКТИРУЙ ЗДЕСЬ
# ============================================================================

MESSAGES = {
    "ru": """🎉 <b>Большое обновление GenauLingua!</b>

Привет! Вот что нового:

🌍 <b>4 языка интерфейса</b>
Теперь бот работает на украинском, русском, английском и турецком.

🏆 <b>Рейтинг и таблица лидеров</b>
Соревнуйся с другими! Месячный рейтинг, lifetime баллы и топ-10.

🔔 <b>Напоминания</b>
Настрой время и дни — бот напомнит позаниматься.

📊 <b>Улучшенная статистика</b>
Прогресс-бар, достижения, история викторин.

Нажми /start чтобы увидеть обновления! 🚀""",

    "uk": """🎉 <b>Велике оновлення GenauLingua!</b>

Привіт! Ось що нового:

🌍 <b>4 мови інтерфейсу</b>
Тепер бот працює українською, російською, англійською та турецькою.

🏆 <b>Рейтинг та таблиця лідерів</b>
Змагайся з іншими! Місячний рейтинг, lifetime бали та топ-10.

🔔 <b>Нагадування</b>
Налаштуй час і дні — бот нагадає позайматися.

📊 <b>Покращена статистика</b>
Прогрес-бар, досягнення, історія вікторин.

Натисни /start щоб побачити оновлення! 🚀""",

    "en": """🎉 <b>Big GenauLingua Update!</b>

Hey! Here's what's new:

🌍 <b>4 interface languages</b>
The bot now works in Ukrainian, Russian, English and Turkish.

🏆 <b>Rating and leaderboard</b>
Compete with others! Monthly rating, lifetime points and top-10.

🔔 <b>Reminders</b>
Set time and days — the bot will remind you to practice.

📊 <b>Improved statistics</b>
Progress bar, achievements, quiz history.

Tap /start to see the updates! 🚀""",

    "tr": """🎉 <b>Büyük GenauLingua Güncellemesi!</b>

Merhaba! İşte yenilikler:

🌍 <b>4 arayüz dili</b>
Bot artık Ukraynaca, Rusça, İngilizce ve Türkçe çalışıyor.

🏆 <b>Sıralama ve liderlik tablosu</b>
Diğerleriyle yarış! Aylık sıralama, lifetime puanlar ve ilk 10.

🔔 <b>Hatırlatıcılar</b>
Saat ve gün ayarla — bot pratik yapmayı hatırlatır.

📊 <b>Geliştirilmiş istatistikler</b>
İlerleme çubuğu, başarılar, test geçmişi.

Güncellemeleri görmek için /start'a bas! 🚀""",
}

# Fallback для юзеров без языка
DEFAULT_LANG = "ru"


# ============================================================================
# ЛОГИКА РАССЫЛКИ
# ============================================================================

async def run_broadcast(dry_run: bool = False, test_user_id: int = None):
    db_url = os.getenv("DATABASE_URL")
    bot_token = os.getenv("BOT_TOKEN")

    if not db_url:
        print("❌ DATABASE_URL не задан!")
        return
    if not bot_token:
        print("❌ BOT_TOKEN не задан!")
        return

    engine = create_async_engine(db_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    async with Session() as session:
        from app.database.models import User

        if test_user_id:
            result = await session.execute(select(User).where(User.id == test_user_id))
            users = result.scalars().all()
            if not users:
                print(f"❌ Юзер {test_user_id} не найден!")
                return
        else:
            result = await session.execute(select(User))
            users = result.scalars().all()

        print(f"📨 Рассылка: {len(users)} пользователей")
        print(f"   Режим: {'DRY RUN (без отправки)' if dry_run else 'ОТПРАВКА'}")
        print()

        # Статистика по языкам
        lang_stats = {}
        for user in users:
            lang = user.interface_language or DEFAULT_LANG
            lang_stats[lang] = lang_stats.get(lang, 0) + 1

        print("📊 По языкам:")
        for lang, count in sorted(lang_stats.items()):
            print(f"   {lang}: {count}")
        print()

        if dry_run:
            print("🔍 DRY RUN — показываю что будет отправлено:\n")
            for lang, text in MESSAGES.items():
                print(f"--- {lang.upper()} ---")
                # Убираем HTML теги для превью
                preview = text.replace("<b>", "").replace("</b>", "")
                print(preview[:100] + "...")
                print()
            print("Для реальной отправки запусти без --dry-run")
            await bot.session.close()
            return

        # Отправка
        success = 0
        failed = 0
        blocked = 0

        for i, user in enumerate(users, 1):
            lang = user.interface_language or DEFAULT_LANG
            text = MESSAGES.get(lang, MESSAGES[DEFAULT_LANG])

            try:
                await bot.send_message(chat_id=user.id, text=text)
                success += 1
                print(f"  ✅ [{i}/{len(users)}] {user.display_name} ({lang})")
            except Exception as e:
                error_str = str(e).lower()
                if "blocked" in error_str or "deactivated" in error_str:
                    blocked += 1
                    print(f"  🚫 [{i}/{len(users)}] {user.display_name} — заблокировал бота")
                else:
                    failed += 1
                    print(f"  ❌ [{i}/{len(users)}] {user.display_name} — {e}")

            # Пауза чтобы не упереться в лимит Telegram API
            if i % 25 == 0:
                await asyncio.sleep(1)

        print()
        print("=" * 40)
        print(f"📨 ИТОГО:")
        print(f"   ✅ Отправлено: {success}")
        print(f"   🚫 Заблокировали: {blocked}")
        print(f"   ❌ Ошибок: {failed}")
        print(f"   📊 Всего: {len(users)}")

    await bot.session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Рассылка обновления")
    parser.add_argument("--dry-run", action="store_true", help="Показать что отправит, без реальной отправки")
    parser.add_argument("--test", type=int, help="Отправить только одному юзеру (для теста)")
    args = parser.parse_args()

    asyncio.run(run_broadcast(dry_run=args.dry_run, test_user_id=args.test))