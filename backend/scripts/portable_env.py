#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows ，backend 的上一级目录（仓库根或便携根）
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


def _portable_roots() -> list[Path]:
    roots: list[Path] = []
    raw = (os.environ.get("NT_PORTABLE_ROOT") or "").strip()
    if raw:
        roots.append(Path(raw).resolve())
    roots.append(Path.cwd().resolve())
    # backend/scripts/portable_env.py -> scripts -> backend -> 仓库/便携根
    here = Path(__file__).resolve().parent
    roots.append(here.parent.parent.resolve())
    roots.append(here.parent.resolve())  # backend 目录（兜底）
    # 去重保持顺序
    seen: set[Path] = set()
    out: list[Path] = []
    for r in roots:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def _find_config_yaml() -> Optional[Path]:
    for root in _portable_roots():
        p = root / "config.yaml"
        if p.is_file():
            return p
    return None


def _as_abs(root: Path, value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    p = Path(value)
    if p.is_absolute():
        return str(p.resolve())
    return str((root / p).resolve())


def _celery_redis_default(redis_uri: str) -> str:
    """Derive Celery broker URL from REDIS_URI when celery block is omitted."""
    from urllib.parse import urlsplit, urlunsplit

    parts = urlsplit(redis_uri)
    path = parts.path or ""
    if path in {"", "/"}:
        path = "/5"
    else:
        path = "/5"
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


def _apply_mapping(root: Path, data: Dict[str, Any]) -> None:
    """将 YAML 嵌套结构映射为现有环境变量名。"""
    server = data.get("server") or {}
    if isinstance(server, dict):
        if server.get("host"):
            os.environ["UVICORN_HOST"] = str(server["host"]).strip()
        if server.get("port") is not None:
            os.environ["UVICORN_PORT"] = str(int(server["port"]))

    db = data.get("database") or {}
    if isinstance(db, dict):
        if db.get("type"):
            os.environ["DATABASE_TYPE"] = str(db["type"]).strip().lower()
        if db.get("async_url") or db.get("sync_url"):
            if db.get("async_url"):
                os.environ["MYSQL_DATABASE_URI"] = str(db["async_url"]).strip()
            if db.get("sync_url"):
                os.environ["MYSQL_DATABASE_URI_SYNC"] = str(db["sync_url"]).strip()
            # 避免分项字段与完整 URI 同时存在时互相覆盖
            for k in (
                "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME",
                "DATABASE_HOST", "DATABASE_PORT", "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_NAME",
            ):
                os.environ.pop(k, None)
        else:
            if db.get("host"):
                os.environ["DATABASE_HOST"] = str(db["host"]).strip()
            if db.get("port") is not None:
                os.environ["DATABASE_PORT"] = str(int(db["port"]))
            if db.get("user"):
                os.environ["DATABASE_USER"] = str(db["user"]).strip()
            if db.get("password") is not None:
                os.environ["DATABASE_PASSWORD"] = str(db["password"])
            if db.get("name"):
                os.environ["DATABASE_NAME"] = str(db["name"]).strip()

    redis = data.get("redis") or {}
    if isinstance(redis, dict) and redis.get("uri"):
        redis_uri = str(redis["uri"]).strip()
        os.environ["REDIS_URI"] = redis_uri
        # Portable installs often omit celery; default to same Redis host, db 5.
        if not os.environ.get("CELERY_BROKER_URL"):
            os.environ["CELERY_BROKER_URL"] = _celery_redis_default(redis_uri)
        if not os.environ.get("CELERY_RESULT_BACKEND"):
            os.environ["CELERY_RESULT_BACKEND"] = os.environ["CELERY_BROKER_URL"]

    celery = data.get("celery") or {}
    if isinstance(celery, dict):
        if celery.get("broker_url"):
            os.environ["CELERY_BROKER_URL"] = str(celery["broker_url"]).strip()
        if celery.get("result_backend"):
            os.environ["CELERY_RESULT_BACKEND"] = str(celery["result_backend"]).strip()
        if celery.get("beat_db_url"):
            os.environ["CELERY_BEAT_DB_URL"] = str(celery["beat_db_url"]).strip()

    sec = data.get("security") or {}
    if isinstance(sec, dict) and sec.get("secret_key"):
        os.environ["SECRET_KEY"] = str(sec["secret_key"]).strip()

    fe = data.get("frontend") or {}
    if isinstance(fe, dict):
        if fe.get("dist_path"):
            os.environ["FRONTEND_DIST_PATH"] = _as_abs(root, str(fe["dist_path"]))
        if fe.get("public_base_url"):
            u = str(fe["public_base_url"]).strip().rstrip("/")
            os.environ["BASE_URL"] = u
            os.environ["FRONTEND_BASE_URL"] = u

    opt = data.get("optional") or {}
    if isinstance(opt, dict) and "grant_admin_oauth" in opt:
        os.environ["GRANT_ADMIN_TO_OAUTH_USER"] = "true" if bool(opt["grant_admin_oauth"]) else "false"

    paths = data.get("paths") or {}
    if isinstance(paths, dict):
        if paths.get("app_project_root"):
            os.environ["APP_PROJECT_ROOT"] = _as_abs(root, str(paths["app_project_root"]))
        if paths.get("project_path"):
            os.environ["PROJECT_PATH"] = _as_abs(root, str(paths["project_path"]))

def load_portable_yaml_into_environ() -> bool:
    """
    若找到 config.yaml 则加载并写入 os.environ，并设置 NT_PORTABLE_ROOT。
    返回是否已加载文件。
    """
    if yaml is None:
        return False
    path = _find_config_yaml()
    if not path:
        return False
    root = path.parent.resolve()
    os.environ.setdefault("NT_PORTABLE_ROOT", str(root))
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        return True
    _apply_mapping(root, raw)
    return True
