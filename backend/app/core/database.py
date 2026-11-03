# -*- coding: utf-8 -*-
# @author: rebort
import asyncio
import functools
import traceback
import typing
from asyncio import current_task
from contextlib import asynccontextmanager


from loguru import logger
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.engine import Engine

from app.utils.context import SQLAlchemySession
from app.config.setting import config


def _create_async_engine() -> AsyncEngine:
    """按 DATABASE_TYPE 创建异步引擎（sqlite 无连接池 + WAL）。"""
    if config.DATABASE_TYPE == "sqlite":
        eng = create_async_engine(
            url=config.DATABASE_URI,
            echo=config.DATABASE_ECHO,
            pool_pre_ping=config.POOL_PRE_PING,
            pool_recycle=config.POOL_RECYCLE,
            connect_args={"timeout": 30},
        )

        @event.listens_for(eng.sync_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        return eng

    return create_async_engine(
        url=config.DATABASE_URI,
        echo=config.DATABASE_ECHO,
        pool_size=config.POOL_SIZE,
        max_overflow=config.MAX_OVERFLOW,
        pool_pre_ping=config.POOL_PRE_PING,
        pool_recycle=config.POOL_RECYCLE,
    )


def create_sync_engine(db_url: str | None = None) -> Engine:
    """同步引擎：Alembic / Celery Beat 等场景。"""
    return create_engine(
        url=db_url or config.DATABASE_URI_SYNC,
        echo=config.DATABASE_ECHO,
        pool_pre_ping=config.POOL_PRE_PING,
        pool_recycle=config.POOL_RECYCLE,
    )


engine = _create_async_engine()

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

async_session = async_scoped_session(async_session_factory, scopefunc=current_task)


def _dedupe_index_names(metadata) -> None:
    """SQLite 要求索引名全局唯一"""
    used: set[str] = set()
    for table in metadata.tables.values():
        for idx in table.indexes:
            name = idx.name
            if not name:
                continue
            if name not in used:
                used.add(name)
                continue
            candidate = f"{table.name}_{name}"
            n = 1
            while candidate in used:
                n += 1
                candidate = f"{table.name}_{name}_{n}"
            idx.name = candidate
            used.add(candidate)


async def create_tables() -> None:
    """根据 ORM创建全部表。"""
    from app.core.db_base import Base
    from app.utils.import_util import ImportUtil

    ImportUtil.find_models(Base)
    _dedupe_index_names(Base.metadata)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def provide_session(func: typing.Callable):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        arg_session = "session"
        func_params = func.__code__.co_varnames
        session_in_args = arg_session in func_params and func_params.index(arg_session) < len(args)
        session_in_kwargs = arg_session in kwargs

        if session_in_kwargs or session_in_args:
            return await func(*args, **kwargs)

        async with async_session() as session:
            fs = functools.partial(func, session=session, *args, **kwargs)
            try:
                return await fs()
            except IntegrityError:
                logger.error(traceback.format_exc())
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise

    return wrapper


@asynccontextmanager
async def content_transaction():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


def async_transaction(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        async with content_transaction() as session:
            SQLAlchemySession.set(session)
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)

    return wrapper


async def get_db() -> typing.AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


try:
    from app.core.db_base import Base
except ImportError:
    Base = None

__all__ = [
    "engine",
    "async_session",
    "provide_session",
    "async_transaction",
    "get_db",
    "Base",
    "create_tables",
    "create_sync_engine",
]
