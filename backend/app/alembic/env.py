from logging.config import fileConfig
import sys
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config.setting import config as app_config

config = context.config


config.set_main_option("sqlalchemy.url", app_config.DATABASE_URI_SYNC.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.db_base import Base
from app.utils.import_util import ImportUtil


ImportUtil.find_models(Base)
target_metadata = Base.metadata

print(f"成功导入 {len(target_metadata.tables)} 个表（DATABASE_TYPE={app_config.DATABASE_TYPE}）")


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


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
