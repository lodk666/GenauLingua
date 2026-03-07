import asyncio, os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def fix():
    e = create_async_engine(os.getenv('DATABASE_URL'))
    async with e.begin() as c:
        await c.execute(text("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'DE_TO_EN'"))
        await c.execute(text("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'EN_TO_DE'"))
        await c.execute(text("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'DE_TO_TR'"))
        await c.execute(text("ALTER TYPE translationmode ADD VALUE IF NOT EXISTS 'TR_TO_DE'"))
        print("Done! Added UPPERCASE enum values.")

    async with e.connect() as c:
        r = await c.execute(text("SELECT enum_range(NULL::translationmode)"))
        print(f"Current values: {r.scalar()}")

asyncio.run(fix())