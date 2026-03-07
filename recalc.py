import asyncio, os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def recalc():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        from app.services.monthly_leaderboard_service import update_monthly_stats
        result = await update_monthly_stats(463491762, session, force_full_recalc=True)
        print(f'Recalc done: score={result.monthly_score}, quizzes={result.monthly_quizzes}, streak={result.monthly_streak}, avg={result.monthly_avg_percent}%')

asyncio.run(recalc())
