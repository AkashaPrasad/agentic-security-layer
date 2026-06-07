"""
Alembic environment configuration for async SQLAlchemy migrations.

This file is executed by Alembic whenever a migration command is run.
It configures the connection to use our async engine and imports all
models so autogenerate can detect schema changes.
"""

import asyncio
import ssl as _ssl
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings

# Import Base *after* all models so metadata is fully populated.
from app.storage.models import Base  # noqa: E402  (registers all models)

# --------------------------------------------------------------------------
# Alembic Config
# --------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url with our computed value (uses sync driver for DDL).
# Escape '%' → '%%' because configparser interprets % as interpolation syntax.
config.set_main_option(
    "sqlalchemy.url",
    settings.sync_database_url.replace("%", "%%"),
)

# Interpret the config file for Python logging (alembic.ini [loggers]).
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData target for autogenerate support.
target_metadata = Base.metadata


# --------------------------------------------------------------------------
# Offline mode — emit SQL to stdout instead of executing.
# --------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --------------------------------------------------------------------------
# Online mode — connect to the database and run migrations.
# --------------------------------------------------------------------------
def do_run_migrations(connection) -> None:  # noqa: ANN001
    """Execute migrations within a connection context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.async_database_url

    extra_kwargs: dict = {}
    if settings.postgres_requires_ssl:
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        extra_kwargs["connect_args"] = {
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "ssl": ctx,
        }

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        **extra_kwargs,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
