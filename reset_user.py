from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os

async def reset():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    async with engine.connect() as conn:
        await conn.execute(text(
            "UPDATE users SET interface_language = '' WHERE id = 463491762"
        ))
        await conn.commit()
        print('Done — user reset')

asyncio.run(reset())