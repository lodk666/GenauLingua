"""
Проверка что роутеры правильно импортированы
"""

print("🔍 ПРОВЕРКА РОУТЕРОВ")
print("=" * 50)

try:
    from app.bot.handlers.quiz import router as quiz_router

    print("✅ Главный quiz router импортирован")

    # Смотрим сколько роутеров внутри
    print(f"   Подроутеров: {len(quiz_router.sub_routers)}")

    for i, sub in enumerate(quiz_router.sub_routers, 1):
        print(f"   {i}. {sub}")

except Exception as e:
    print(f"❌ Ошибка импорта quiz router: {e}")
    import traceback

    traceback.print_exc()

print()

try:
    from app.bot.handlers.quiz.stats import router as stats_router

    print("✅ Stats router импортирован")
    print(f"   Обработчиков: {len(stats_router.observers)}")

except Exception as e:
    print(f"❌ Ошибка импорта stats router: {e}")
    import traceback

    traceback.print_exc()

print()

try:
    from app.bot.handlers.quiz.monthly_leaderboard import router as monthly_router

    print("✅ Monthly leaderboard router импортирован")
    print(f"   Обработчиков: {len(monthly_router.observers)}")

except Exception as e:
    print(f"❌ Ошибка импорта monthly_leaderboard router: {e}")
    import traceback

    traceback.print_exc()

print()
print("=" * 50)
print("Проверка завершена!")