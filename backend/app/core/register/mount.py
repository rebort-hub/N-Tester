# -*- coding: utf-8 -*-
# @author: rebort
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.setting import config


def _portable_root() -> str | None:
    """安装包启动时 start-backend 会设置 NT_PORTABLE_ROOT=安装目录。"""
    root = (os.environ.get("NT_PORTABLE_ROOT") or "").strip()
    return os.path.abspath(root) if root else None


def init_mount(app: FastAPI):
    """ 挂载静态文件 -- https://fastapi.tiangolo.com/zh/tutorial/static-files/ """

    portable = _portable_root()
    # 源码开发：backend/app/init -> backend
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # 优先级：安装目录 static（与头像落盘 Path("static/...") + chdir 安装根一致）
    #       > 打包 data/static
    #       > 源码 backend/static
    #       > 项目根 static
    candidates = []
    if portable:
        candidates.append(os.path.join(portable, config.STATIC_DIR))
        candidates.append(os.path.join(portable, "runtime", "backend", "data", config.STATIC_DIR))
    candidates.append(os.path.join(backend_root, config.STATIC_DIR))
    candidates.append(os.path.join(config.BASEDIR, config.STATIC_DIR))

    static_abs = next((p for p in candidates if os.path.isdir(p)), None)
    if static_abs is None:
        static_abs = candidates[0] if portable else os.path.join(backend_root, config.STATIC_DIR)
    os.makedirs(static_abs, exist_ok=True)
    app.mount(f"/{config.STATIC_DIR}", StaticFiles(directory=static_abs), name=config.STATIC_DIR)

    # 单独挂载 /media，对齐后端存储路径 /media/playwright/...
    media_abs = os.path.join(static_abs, "media")
    os.makedirs(media_abs, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_abs), name="media")

    # 挂载 uploads（用于 Skill runtime 截图/产物直链访问）
    if portable:
        uploads_abs = os.path.join(portable, "uploads")
    else:
        uploads_abs = os.path.join(backend_root, "uploads")
    os.makedirs(uploads_abs, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_abs), name="uploads")
