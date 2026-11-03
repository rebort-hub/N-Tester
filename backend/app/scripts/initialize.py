# -*- coding: utf-8 -*-
"""数据库自举"""

from __future__ import annotations
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from loguru import logger
from sqlalchemy import func, inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db_base import Base
from app.core.database import async_session, create_tables, engine
from app.utils.import_util import ImportUtil
from app.config.path_conf import BACKEND_ROOT
from app.config.setting import config


ImportUtil.find_models(Base)

SEED_DIR = BACKEND_ROOT / "sql" / "seed"
ALEMBIC_VERSION_DIR = BACKEND_ROOT / "app" / "alembic" / "versions"
SENTINEL_TABLE = "sys_menu"


SEED_ORDER: list[str] = [
    "sys_menu",
    "sys_role",
    "sys_dict_type",
    "sys_dict_data",
    "sys_user",
    "sys_user_role",
    "sys_role_menu",
]


class InitializeData:
    """初始化数据库结构与种子数据。"""

    async def init_db(self) -> None:
        await self.__apply_schema()
        async with async_session() as session:
            try:
                await self.__init_seed(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def __apply_schema(self) -> None:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(BACKEND_ROOT / "app" / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", config.DATABASE_URI_SYNC.replace("%", "%%"))

        async with engine.connect() as conn:
            has_sentinel = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table(SENTINEL_TABLE)
            )
        empty_db = not has_sentinel

        if empty_db:
            await create_tables()
            has_revisions = any(
                p.name != "__init__.py" and p.suffix == ".py"
                for p in ALEMBIC_VERSION_DIR.glob("*.py")
            )
            if has_revisions:
                await asyncio.to_thread(command.stamp, alembic_cfg, "head")
                logger.info(f"[OK] empty DB: create_all + stamp head ({config.DATABASE_TYPE})")
            else:
                logger.info(f"[OK] empty DB: create_all, no revisions to stamp ({config.DATABASE_TYPE})")
        else:
            await self.__clear_unresolvable_alembic_version(alembic_cfg)
            has_revisions = any(
                p.name != "__init__.py" and p.suffix == ".py"
                for p in ALEMBIC_VERSION_DIR.glob("*.py")
            )
            if has_revisions:
                await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
                logger.info("[OK] alembic upgrade head applied")
            else:
                await create_tables()
                logger.info("[OK] existing DB: create_all filled missing tables")

    @staticmethod
    async def __clear_unresolvable_alembic_version(alembic_cfg) -> None:
        from alembic.script import ScriptDirectory

        known = {script.revision for script in ScriptDirectory.from_config(alembic_cfg).walk_revisions()}
        async with engine.begin() as conn:
            has_version_table = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).has_table("alembic_version")
            )
            if not has_version_table:
                return
            current = {row[0] for row in await conn.execute(text("select version_num from alembic_version"))}
            stale = current - known
            if not stale:
                return
            for rev in stale:
                await conn.execute(
                    text("delete from alembic_version where version_num = :rev"),
                    {"rev": rev},
                )
            logger.warning(f"[WARN] cleared unresolvable alembic revisions: {sorted(stale)}")

    async def __init_seed(self, db: AsyncSession) -> None:
        skipped: list[str] = []
        for table_name in SEED_ORDER:
            data = self.__load_json(table_name)
            if not data:
                logger.info(f"[SKIP] {table_name}: no seed file")
                continue

            table = Base.metadata.tables.get(table_name)
            if table is None:
                logger.warning(f"[WARN] table {table_name} not in metadata, skip")
                continue

            count = await db.execute(select(func.count()).select_from(table))
            if count.scalar():
                skipped.append(table_name)
                continue

            rows = [self.__normalize_row(item) for item in data]
            col_names = {c.name for c in table.columns}
            rows = [{k: v for k, v in row.items() if k in col_names} for row in rows]

            await db.execute(table.insert(), rows)
            await db.flush()
            logger.info(f"[OK] seeded {table_name}: {len(rows)} rows")

        if skipped:
            logger.info(f"[SKIP] {len(skipped)} tables already have data: {', '.join(skipped)}")

        if config.DATABASE_TYPE == "postgres":
            await self.__reset_postgres_sequences(db)

    @staticmethod
    async def __reset_postgres_sequences(db: AsyncSession) -> None:
        """显式写入 id 后同步序列，避免后续插入主键冲突。"""
        for table_name in SEED_ORDER:
            table = Base.metadata.tables.get(table_name)
            if table is None or "id" not in table.c:
                continue
            # table_name 来自 SEED_ORDER 常量白名单
            await db.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table_name}), 1), true)"
                )
            )

    @staticmethod
    def __normalize_row(item: dict[str, Any]) -> dict[str, Any]:
        row = dict(item)
        for key, value in list(row.items()):
            if isinstance(value, str) and key.endswith(("_at", "_date", "_time")):
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        row[key] = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
        return row

    @staticmethod
    def __load_json(table_name: str) -> list[dict]:
        path = SEED_DIR / f"{table_name}.json"
        if not path.exists():
            return []
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"❌️ 读取种子 {path} 失败: {e}")
            raise
