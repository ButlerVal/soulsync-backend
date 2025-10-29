import asyncio
import os # Import os to read environment variables
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# Import all models and the Base class
from app.db.base import Base
from app.models.user import User
from app.models.emotional_profile import EmotionalProfile
from app.models.match import Match
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user_block import UserBlock
from app.models.report import Report

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Still read from config for offline mode
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper function to run migrations within a transaction."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """

    # Get the database URL from the OS environment variable
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set or empty")

    # Create engine configuration using the environment variable
    # We pass the URL directly instead of reading from alembic.ini section
    connectable_config = {
        "sqlalchemy.url": db_url # Directly use the environment variable
    }

    # Create the async engine from the modified config
    connectable = async_engine_from_config(
        connectable_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Connect and run migrations
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    # Dispose of the engine
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    try:
        asyncio.run(run_async_migrations())
    except ValueError as ve:
        print(f"Migration Error: {ve}")
        # Optionally exit with an error code if DATABASE_URL is missing
        import sys
        sys.exit(1)


# Determine mode and run migrations
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

