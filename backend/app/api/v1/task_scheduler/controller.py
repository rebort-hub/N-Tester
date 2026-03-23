"""
定时任务模块 - 控制器
处理定时任务管理、通知配置等相关API请求
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json

from .service import TaskSchedulerService
from .remote_control import send_command, SchedulerRemoteError

router = APIRouter()


@router.post("/task_list")
async def get_task_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取任务列表"""
    try:
        body = await body_to_json(request)
        page = int(body.get("page", 1) or 1)
        size = int(body.get("size", 10) or 10)
        name = body.get("name") or None
        task_type = body.get("type") if body.get("type") is not None else None
        status = body.get("status") if body.get("status") is not None else None

        data = await TaskSchedulerService.get_task_list_with_page(
            db,
            current_user_id,
            name=name,
            task_type=task_type,
            status=status,
            page=page,
            size=size,
        )
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@router.post("/add_task")
async def create_task(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """新增任务"""
    try:
        data = await body_to_json(request)
        res = await TaskSchedulerService.create_task(db, data, current_user_id)
        return success_response(res)
    except Exception as e:
        return error_response(str(e))


@router.post("/edit_task")
async def update_task(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """编辑任务"""
    try:
        data = await body_to_json(request)
        task_id = int(data.get("task_id") or data.get("id"))
        res = await TaskSchedulerService.update_task(db, task_id, data, current_user_id)
        if res.get("success") is False:
            return error_response(res.get("message", "更新失败"))
        return success_response({})
    except Exception as e:
        return error_response(str(e))


@router.post("/del_task")
async def delete_task(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除任务"""
    try:
        data = await body_to_json(request)
        task_id = int(data.get("task_id") or data.get("id"))
        await TaskSchedulerService.delete_task(db, task_id, current_user_id)
        return success_response({})
    except Exception as e:
        return error_response(str(e))


@router.post("/notice_list")
async def get_notice_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取通知列表"""
    try:
        body = await body_to_json(request)
        page = int(body.get("page", 1) or 1)
        size = int(body.get("size", 10) or 10)
        name = body.get("name") or None
        notice_type = body.get("type") if body.get("type") is not None else None
        status = body.get("status") if body.get("status") is not None else None

        data = await TaskSchedulerService.get_notice_list(
            db,
            current_user_id,
            name=name,
            notice_type=notice_type,
            status=status,
            page=page,
            size=size,
        )
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@router.post("/add_notice")
async def create_notice(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """新增通知"""
    try:
        data = await body_to_json(request)
        res = await TaskSchedulerService.create_notice(db, data, current_user_id)
        return success_response(res)
    except Exception as e:
        return error_response(str(e))


@router.post("/edit_notice")
async def update_notice(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """编辑通知"""
    try:
        data = await body_to_json(request)
        notice_id = int(data.get("notice_id") or data.get("id"))
        res = await TaskSchedulerService.update_notice(db, notice_id, data, current_user_id)
        if res.get("success") is False:
            return error_response(res.get("message", "更新失败"))
        return success_response({})
    except Exception as e:
        return error_response(str(e))


@router.post("/del_notice")
async def delete_notice(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除通知"""
    try:
        data = await body_to_json(request)
        notice_id = int(data.get("notice_id") or data.get("id"))
        await TaskSchedulerService.delete_notice(db, notice_id, current_user_id)
        return success_response({})
    except Exception as e:
        return error_response(str(e))


@router.post("/task_history")
async def get_task_history(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取任务执行历史"""
    try:
        data = await body_to_json(request)
        task_id = data.get("task_id")
        status = data.get("status")
        page = int(data.get("page", 1) or 1)
        size = int(data.get("size", 10) or 10)

        res = await TaskSchedulerService.get_task_history(
            db,
            task_id,
            current_user_id,
            status=status,
            page=page,
            size=size,
        )
        return success_response(res)
    except Exception as e:
        return error_response(str(e))


# ==================== 调度器控制（远程调用 scheduler_runner） ====================


@router.get("/scheduler/status")
async def scheduler_status(current_user_id: int = Depends(get_current_user_id)):
    try:
        data = await send_command("scheduler.status")
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))


@router.get("/scheduler/jobs")
async def scheduler_jobs(current_user_id: int = Depends(get_current_user_id)):
    try:
        data = await send_command("scheduler.jobs")
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))


@router.post("/scheduler/reload")
async def scheduler_reload(current_user_id: int = Depends(get_current_user_id)):
    try:
        # reload 可能涉及 DB 扫描与重建，放宽超时时间
        data = await send_command("scheduler.reload", timeout_s=30.0)
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))


@router.post("/job/pause")
async def pause_job(request: Request, current_user_id: int = Depends(get_current_user_id)):
    try:
        body = await body_to_json(request)
        job_id = body.get("job_id") or body.get("task_id") or body.get("id")
        data = await send_command("job.pause", {"job_id": str(job_id)})
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(str(e))


@router.post("/job/resume")
async def resume_job(request: Request, current_user_id: int = Depends(get_current_user_id)):
    try:
        body = await body_to_json(request)
        job_id = body.get("job_id") or body.get("task_id") or body.get("id")
        data = await send_command("job.resume", {"job_id": str(job_id)})
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(str(e))


@router.post("/job/run_now")
async def run_job_now(request: Request, current_user_id: int = Depends(get_current_user_id)):
    try:
        body = await body_to_json(request)
        job_id = body.get("job_id") or body.get("task_id") or body.get("id")
        data = await send_command("job.run_now", {"job_id": str(job_id)})
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(str(e))


@router.post("/job/remove")
async def remove_job(request: Request, current_user_id: int = Depends(get_current_user_id)):
    try:
        body = await body_to_json(request)
        job_id = body.get("job_id") or body.get("task_id") or body.get("id")
        data = await send_command("job.remove", {"job_id": str(job_id)})
        return success_response(data)
    except SchedulerRemoteError as e:
        return error_response(str(e))
    except Exception as e:
        return error_response(str(e))