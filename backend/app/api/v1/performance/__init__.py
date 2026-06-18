#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from fastapi import APIRouter

from app.api.v1.performance.config.controller import router as config_router
from app.api.v1.performance.files.controller import router as files_router
from app.api.v1.performance.report.controller import router as report_router
from app.api.v1.performance.scenario.controller import router as scenario_router
from app.api.v1.performance.scheduler.controller import router as scheduler_router

# 导入模型以确保注册到 metadata（用于数据库迁移）
from app.api.v1.performance.config import model
from app.api.v1.performance.files import model
from app.api.v1.performance.report import model
from app.api.v1.performance.scenario import model
from app.api.v1.performance.scheduler import model

router = APIRouter()
router.include_router(config_router)
router.include_router(files_router)
router.include_router(scenario_router)
router.include_router(scheduler_router)
router.include_router(report_router)