from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings


# Создание движка БД
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncSession:
    """Получение сессии БД"""
    async with AsyncSessionLocal() as session:
        yield session