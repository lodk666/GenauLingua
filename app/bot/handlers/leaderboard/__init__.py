from .monthly import router as monthly_router
from .alltime import router as alltime_router
from .leaderboard_table import router as table_router

__all__ = ['monthly_router', 'alltime_router', 'table_router']