# -*- coding: utf-8 -*-
# @author: rebort

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from config import config


def init_router(app: FastAPI):
    """ 注册路由 """
    # 注册v1版本API路由
    app.include_router(v1_router, prefix=config.API_PREFIX)
    # 旧架构兼容路由已移除：仅保留新架构 v1 接口
