from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # Ensure async_sessionmaker is imported
from app.core.config import settings
import logging # Add logging

logger = logging.getLogger(__name__) # Add logger

# --- FIX: Ensure asyncpg driver is specified in URL ---
db_url = settings.DATABASE_URL
logger.info(f"Original DATABASE_URL from settings: {db_url[:db_url.find('@')] if '@' in db_url else db_url}") # Log URL safely

if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    logger.info("Modified DATABASE_URL to use asyncpg.")
elif not db_url.startswith("postgresql+asyncpg://"):
    logger.error(f"DATABASE_URL does not specify asyncpg driver: {db_url}")
    # Depending on strictness, you might raise an error here
    # raise ValueError(f"DATABASE_URL must use 'postgresql+asyncpg://' driver, got: {db_url}")
# --- END FIX ---


# Create the async engine using the potentially modified db_url
engine = create_async_engine(
    db_url, # Use the modified URL
    pool_pre_ping=True,
    echo=settings.DEBUG, # Log SQL queries if in debug mode
)

# Create a configured "AsyncSession" class (using async_sessionmaker from your previous fix)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# get_db_session function remains the same
from typing import AsyncGenerator # Keep this import

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    Ensures the session is always closed.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

