# -*- coding: utf-8 -*-
"""路径常量：backend 根目录及常用子路径。"""

from __future__ import annotations

from pathlib import Path

# backend/（含 main.py、.env、alembic.ini）
BACKEND_ROOT = Path(__file__).resolve().parents[2]

STATIC_DIR = BACKEND_ROOT / "static"
LOG_DIR = BACKEND_ROOT / "logs"
SQL_DIR = BACKEND_ROOT / "sql"
SEED_DIR = SQL_DIR / "seed"
ALEMBIC_DIR = BACKEND_ROOT / "app" / "alembic"
ALEMBIC_VERSION_DIR = ALEMBIC_DIR / "versions"
FILES_DIR = BACKEND_ROOT / "files"
