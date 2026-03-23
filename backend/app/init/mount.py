# -*- coding: utf-8 -*-
# @author: rebort
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import config


def init_mount(app: FastAPI):
    """ 挂载静态文件 -- https://fastapi.tiangolo.com/zh/tutorial/static-files/ """

    # 优先使用 backend/static（上传文件实际落盘目录），避免 BASEDIR 指向项目根导致 404
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    backend_static = os.path.join(backend_root, config.STATIC_DIR)
    project_static = os.path.join(config.BASEDIR, config.STATIC_DIR)
    static_abs = backend_static if os.path.isdir(backend_static) else project_static
    os.makedirs(static_abs, exist_ok=True)
    app.mount(f"/{config.STATIC_DIR}", StaticFiles(directory=static_abs), name=config.STATIC_DIR)

    # 单独挂载 /media，对齐后端存储路径 /media/playwright/...
    media_abs = os.path.join(static_abs, "media")
    os.makedirs(media_abs, exist_ok=True)
    app.mount("/media", StaticFiles(directory=media_abs), name="media")