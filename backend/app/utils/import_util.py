# -*- coding: utf-8 -*-
"""扫描工程中的 ORM 模型文件。"""

from __future__ import annotations
import importlib
import inspect
import os
from functools import lru_cache
from pathlib import Path
from typing import Any
from loguru import logger
from sqlalchemy import inspect as sa_inspect


class ImportUtil:
    """遍历SQLAlchemy 模型。"""

    @classmethod
    def find_project_root(cls) -> Path:
        """backend 根目录（含 ``app/``、``.env``）。"""
        return Path(__file__).resolve().parents[2]

    @classmethod
    def is_valid_model(cls, obj: Any, base_class: type) -> bool:
        if not (inspect.isclass(obj) and issubclass(obj, base_class) and obj is not base_class):
            return False
        if not hasattr(obj, "__tablename__") or getattr(obj, "__tablename__", None) is None:
            return False
        try:
            inspected = sa_inspect(obj)
            return inspected is not None and len(inspected.columns) > 0
        except Exception:
            return False

    @classmethod
    @lru_cache(maxsize=256)
    def find_models(cls, base_class: type) -> list[Any]:

        models: list[Any] = []
        seen_models: set[Any] = set()
        seen_tables: set[str] = set()
        processed_model_files: set[str] = set()

        project_root = cls.find_project_root()
        app_root = project_root / "app"

        exclude_dirs = {
            "venv",
            ".env",
            ".git",
            "__pycache__",
            "migrations",
            "alembic",
            "tests",
            "test",
            "docs",
            "examples",
            "scripts",
            ".venv",
            "static",
            "templates",
            "sql",
            "env",
        }

        model_files: list[tuple[Path, Path]] = []
        walk_root = app_root if app_root.is_dir() else project_root
        for root, dirs, files in os.walk(walk_root):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in ("model.py", "models.py"):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(project_root)
                    model_files.append((file_path, relative_path))


        extra_modules = [
            "app.api.v1.system.permission.rbac_model",
            "app.api.v1.Ntesterc_module.Ntesterc_task_scheduler.celery_beat_model",
            "app.api.v1.Ntesterc_module.Ntesterc_project.legacy_api_model",
            "app.api.v1.Ntesterc_module.Ntesterc_ai.conversation.message_model",
            "app.api.v1.Ntesterc_module.Ntesterc_ai.conversation.mcp_execution_record",
        ]

        model_files.sort(key=lambda x: str(x[1]))

        for file_path, relative_path in model_files:
            if str(file_path) in processed_model_files:
                continue
            processed_model_files.add(str(file_path))

            module_parts = (*relative_path.parts[:-1], relative_path.stem)
            module_name = ".".join(module_parts)
            cls._collect_from_module(module_name, base_class, models, seen_models, seen_tables)

        for module_name in extra_modules:
            cls._collect_from_module(module_name, base_class, models, seen_models, seen_tables)

        return models

    @classmethod
    def _collect_from_module(
        cls,
        module_name: str,
        base_class: type,
        models: list[Any],
        seen_models: set[Any],
        seen_tables: set[str],
    ) -> None:
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            if "cannot import name" not in str(e):
                logger.warning(f"无法导入模块 {module_name}: {e}")
            return
        except Exception:
            logger.exception(f"处理模块失败: {module_name}")
            raise

        for _name, obj in inspect.getmembers(module, inspect.isclass):
            if not cls.is_valid_model(obj, base_class):
                continue
            if obj in seen_models:
                continue
            table_name = getattr(obj, "__tablename__", None)
            if table_name is None or table_name in seen_tables:
                continue
            seen_models.add(obj)
            seen_tables.add(table_name)
            models.append(obj)
