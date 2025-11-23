from __future__ import with_statement

import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
from flask import current_app

config = context.config

if config.config_file_name is not None:
    config_path = config.config_file_name
    if not os.path.isabs(config_path) and not os.path.exists(config_path):
        base_dir = os.path.dirname(__file__)
        candidate = os.path.join(base_dir, '..', os.path.basename(config_path))
        if os.path.exists(candidate):
            config_path = candidate
        else:
            config_path = os.path.join(base_dir, '..', config_path)
    fileConfig(config_path)

config.set_main_option('sqlalchemy.url', str(current_app.config.get('SQLALCHEMY_DATABASE_URI')))

target_metadata = current_app.extensions['migrate'].db.metadata

def run_migrations_offline() -> None:
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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


def run_migrations() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


run_migrations()
