import asyncio, os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    e = create_async_engine(os.getenv('DATABASE_URL'))
    async with e.connect() as c:
        r = await c.execute(text("SELECT enum_range(NULL::translationmode)"))
        print(r.scalar())

asyncio.run(check())