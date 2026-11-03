#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import time
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from app.core.logger import logger
from .service import DesktopAutomationService
from .schema import (
    MenuAddBody, MenuRenameBody, MenuDeleteBody,
    ScriptSaveBody, RunScriptBody, StopScriptBody, ResultListBody,
    SUPPORTED_FRAMEWORKS,
)

router = APIRouter()


# ── 框架列表 ──────────────────────────────────────────────
@router.get("/frameworks")
async def get_frameworks(current_user_id: int = Depends(get_current_user_id)):
    """获取支持的执行框架列表"""
    return success_response(DesktopAutomationService.get_frameworks())


# ── 菜单 ──────────────────────────────────────────────────
@router.post("/menu")
async def get_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request) or {}
        project_id = body.get("project_id")
        data = await DesktopAutomationService.get_menu(
            db, current_user_id, int(project_id) if project_id else None
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] get_menu error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/add_menu")
async def add_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = MenuAddBody(**(await body_to_json(request) or {}))
        if not body.name.strip():
            return error_response("名称不能为空")
        if body.type not in (0, 1, 2):
            return error_response("节点类型无效，只支持 0=目录 1=脚本组 2=脚本")
        data = await DesktopAutomationService.add_menu(
            db, body.name.strip(), body.pid, body.type, current_user_id,
            body.project_id,
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] add_menu error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/rename_menu")
async def rename_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = MenuRenameBody(**(await body_to_json(request) or {}))
        if not body.name.strip():
            return error_response("名称不能为空")
        await DesktopAutomationService.rename_menu(db, body.id, body.name.strip(), current_user_id)
        return success_response({})
    except Exception as e:
        logger.error(f"[desktop] rename_menu error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/del_menu")
async def del_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = MenuDeleteBody(**(await body_to_json(request) or {}))
        await DesktopAutomationService.delete_menu(db, body.id, current_user_id)
        return success_response({})
    except Exception as e:
        logger.error(f"[desktop] del_menu error: {e}", exc_info=True)
        return error_response(str(e))


# ── 脚本 ──────────────────────────────────────────────────
@router.post("/get_script")
async def get_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request) or {}
        menu_id = body.get("id")
        if not menu_id:
            return error_response("缺少 id 参数")
        data = await DesktopAutomationService.get_script(db, int(menu_id), current_user_id)
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] get_script error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/save_script")
async def save_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = ScriptSaveBody(**(await body_to_json(request) or {}))
        if body.framework not in SUPPORTED_FRAMEWORKS:
            return error_response(f"不支持的框架: {body.framework}，可选: {SUPPORTED_FRAMEWORKS}")
        await DesktopAutomationService.save_script(
            db, body.id, body.framework, body.script, current_user_id
        )
        return success_response({})
    except Exception as e:
        logger.error(f"[desktop] save_script error: {e}", exc_info=True)
        return error_response(str(e))


# ── 执行 ──────────────────────────────────────────────────
@router.post("/run_script")
async def run_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = RunScriptBody(**(await body_to_json(request) or {}))
        if body.framework not in SUPPORTED_FRAMEWORKS:
            return error_response(f"不支持的框架: {body.framework}")
        result_id = body.result_id or str(int(time.time() * 1000))
        data = await DesktopAutomationService.run_script(
            db, body.id,
            body.task_name.strip() if body.task_name else "桌面自动化任务",
            result_id, body.framework, current_user_id,
            body.project_id,
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] run_script error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/stop_script")
async def stop_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = StopScriptBody(**(await body_to_json(request) or {}))
        ok = await DesktopAutomationService.stop_script(db, body.result_id, current_user_id)
        return success_response({}, message="已停止" if ok else "未找到执行记录")
    except Exception as e:
        logger.error(f"[desktop] stop_script error: {e}", exc_info=True)
        return error_response(str(e))


# ── 结果 ──────────────────────────────────────────────────
@router.post("/result_list")
async def result_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = ResultListBody(**(await body_to_json(request) or {}))
        data = await DesktopAutomationService.get_result_list(
            db, current_user_id, body.page, body.pageSize, body.search
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] result_list error: {e}", exc_info=True)
        return error_response(str(e))


@router.post("/result_detail")
async def result_detail(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request) or {}
        result_id = body.get("result_id", "").strip()
        if not result_id:
            return error_response("缺少 result_id 参数")
        data = await DesktopAutomationService.get_result_detail(
            db, result_id, current_user_id
        )
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] result_detail error: {e}", exc_info=True)
        return error_response(str(e))


# ── 执行状态查询 ──────────────────────────────────────────
@router.post("/run_status")
async def run_status(
    request: Request,
    current_user_id: int = Depends(get_current_user_id),
):
    """查询执行是否还在运行（轻量接口，不查 DB）"""
    try:
        body = await body_to_json(request) or {}
        result_id = body.get("result_id", "").strip()
        if not result_id:
            return error_response("缺少 result_id 参数")
        data = await DesktopAutomationService.get_run_status(result_id, current_user_id)
        return success_response(data)
    except Exception as e:
        logger.error(f"[desktop] run_status error: {e}", exc_info=True)
        return error_response(str(e))


# ── 删除执行记录 ──────────────────────────────────────────
@router.post("/del_result")
async def del_result(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """删除执行记录（汇总 + 步骤详情）"""
    try:
        body = await body_to_json(request) or {}
        result_id = body.get("result_id", "").strip()
        if not result_id:
            return error_response("缺少 result_id 参数")
        ok = await DesktopAutomationService.delete_result(db, result_id, current_user_id)
        return success_response({}, message="删除成功" if ok else "记录不存在")
    except Exception as e:
        logger.error(f"[desktop] del_result error: {e}", exc_info=True)
        return error_response(str(e))


# ── 复制脚本 ──────────────────────────────────────────────
@router.post("/copy_script")
async def copy_script(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """复制脚本到同级目录"""
    try:
        body = await body_to_json(request) or {}
        menu_id = body.get("id")
        new_name = body.get("name", "").strip()
        if not menu_id:
            return error_response("缺少 id 参数")
        if not new_name:
            return error_response("缺少新名称")
        data = await DesktopAutomationService.copy_script(db, int(menu_id), new_name, current_user_id)
        return success_response(data)
    except ValueError as e:
        return error_response(str(e))
    except Exception as e:
        logger.error(f"[desktop] copy_script error: {e}", exc_info=True)
        return error_response(str(e))
