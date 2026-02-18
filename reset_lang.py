"""
Скрипт для сброса языка ВСЕМ пользователям
После этого все при /start увидят выбор языка
"""
import asyncpg
import asyncio


async def reset_all_users():
    conn = await asyncpg.connect(
        user='genau_user',
        password='genau_password',
        database='genaulingua_db',
        host='localhost'
    )

    # Сбрасываем язык всем пользователям
    result = await conn.execute(
        'UPDATE users SET interface_language = NULL'
    )

    print(f"✅ Язык сброшен для ВСЕХ пользователей")
    print(f"   Обновлено записей: {result.split()[-1]}")
    print(f"\n💡 Теперь все пользователи при /start увидят выбор языка")

    await conn.close()


if __name__ == "__main__":
    print("⚠️  ВНИМАНИЕ: Этот скрипт сбросит язык ВСЕМ пользователям!")
    print("   Вы уверены? (y/n): ", end="")

    confirm = input().lower()
    if confirm == 'y':
        asyncio.run(reset_all_users())
    else:
        print("❌ Отменено")