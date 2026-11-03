# -*- coding: utf-8 -*-
# @author: rebort

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.api.v1.Ntesterc_module.Ntesterc_api.mock_controller import router as mock_router
from app.config.setting import config


def init_router(app: FastAPI):
    """ 注册路由 """
    # 公开 Mock 服务：/mock/*（无需登录）
    app.include_router(mock_router)
    # 注册v1版本API路由
    app.include_router(v1_router, prefix=config.API_PREFIX)

