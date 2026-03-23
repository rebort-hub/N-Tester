"""
定时任务模块 - 业务逻辑服务
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
import time

from .model import MsgNoticeModel, SchedulerTaskModel, TaskExecutionHistoryModel
from .scheduler import add_or_replace_job, build_trigger, get_scheduler


class TaskSchedulerService:
    """定时任务服务"""
    
    @staticmethod
    async def get_task_list(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取任务列表（原始方法，暂保留兼容）"""
        stmt = (
            select(SchedulerTaskModel)
            .where(
                SchedulerTaskModel.enabled_flag == 1,
                SchedulerTaskModel.created_by == user_id,
            )
            .order_by(SchedulerTaskModel.id.desc())
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()
        scheduler = get_scheduler()

        data: List[Dict[str, Any]] = []
        for t in tasks:
            job = scheduler.get_job(job_id=str(t.id))
            data.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type,
                    "status": t.status,
                    "script": t.script,
                    "time": t.time,
                    "notice": t.notice,
                    "description": t.description,
                    "scheduler_job_id": t.scheduler_job_id,
                    "last_run_at": t.last_run_at,
                    "next_run_at": t.next_run_at,
                    "total_run_count": t.total_run_count or 0,
                    "creation_date": t.creation_date,
                    # 兼容旧接口 task_list 里的 next_time 字段
                    "next_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if (job and job.next_run_time) else "",
                }
            )
        return data

    @staticmethod
    async def get_task_list_with_page(
        db: AsyncSession,
        user_id: int,
        *,
        name: Optional[str] = None,
        task_type: Optional[int] = None,
        status: Optional[int] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """获取任务列表（支持筛选 + 分页）"""
        conditions = [
            SchedulerTaskModel.enabled_flag == 1,
            SchedulerTaskModel.created_by == user_id,
        ]
        if name:
            conditions.append(SchedulerTaskModel.name.like(f"%{name}%"))
        if task_type is not None:
            conditions.append(SchedulerTaskModel.type == int(task_type))
        if status is not None:
            conditions.append(SchedulerTaskModel.status == int(status))

        # 统计总数
        total_result = await db.execute(select(func.count()).where(*conditions))
        total = int(total_result.scalar() or 0)

        # 分页查询
        stmt = (
            select(SchedulerTaskModel)
            .where(*conditions)
            .order_by(SchedulerTaskModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(stmt)
        tasks = result.scalars().all()

        scheduler = get_scheduler()
        content: List[Dict[str, Any]] = []
        for t in tasks:
            job = scheduler.get_job(job_id=str(t.id))
            content.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "type": t.type,
                    "status": t.status,
                    "script": t.script,
                    "time": t.time,
                    "notice": t.notice,
                    "description": t.description,
                    "scheduler_job_id": t.scheduler_job_id,
                    "last_run_at": t.last_run_at,
                    "next_run_at": t.next_run_at,
                    "total_run_count": t.total_run_count or 0,
                    "creation_date": t.creation_date,
                    "next_time": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if (job and job.next_run_time) else "",
                }
            )

        return {
            "content": content,
            "total": total,
            "page": page,
            "size": size,
        }
    
    @staticmethod
    async def create_task(db: AsyncSession, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """创建定时任务"""
        task = SchedulerTaskModel(
            name=task_data["name"],
            type=int(task_data["type"]),
            status=int(task_data.get("status", 0)),
            script=task_data.get("script") or {},
            time=task_data.get("time") or {},
            notice=task_data.get("notice") or {},
            description=task_data.get("description"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(task)
        await db.flush()

        if task.status == 1:
            await TaskSchedulerService.schedule_task(task.id, task.time or {}, task.script or {}, int(task.type), user_id)
            task.scheduler_job_id = str(task.id)
            task.next_run_at = TaskSchedulerService._get_job_next_run_datetime(str(task.id))

        await db.commit()
        return {"id": task.id}
    
    @staticmethod
    async def update_task(db: AsyncSession, task_id: int, task_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """更新定时任务"""
        result = await db.execute(
            select(SchedulerTaskModel).where(
                SchedulerTaskModel.id == task_id,
                SchedulerTaskModel.enabled_flag == 1,
                SchedulerTaskModel.created_by == user_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            return {"success": False, "message": "任务不存在"}

        for field in ("name", "type", "status", "script", "time", "notice", "description"):
            if field in task_data and task_data[field] is not None:
                setattr(task, field, task_data[field])
        task.updated_by = user_id

        # 重建调度（兼容旧 edit_task 行为：status=1 就重新 add_scheduler_task）
        await TaskSchedulerService.unschedule_task(str(task.id))
        task.scheduler_job_id = None
        task.next_run_at = None

        if int(task.status) == 1:
            await TaskSchedulerService.schedule_task(task.id, task.time or {}, task.script or {}, int(task.type), user_id)
            task.scheduler_job_id = str(task.id)
            task.next_run_at = TaskSchedulerService._get_job_next_run_datetime(str(task.id))

        await db.commit()
        return {"success": True}
    
    @staticmethod
    async def delete_task(db: AsyncSession, task_id: int, user_id: int) -> bool:
        """删除定时任务"""
        await TaskSchedulerService.unschedule_task(str(task_id))
        await db.execute(
            update(SchedulerTaskModel)
            .where(
                SchedulerTaskModel.id == task_id,
                SchedulerTaskModel.enabled_flag == 1,
                SchedulerTaskModel.created_by == user_id,
            )
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()
        return True
    
    @staticmethod
    async def get_notice_list(
        db: AsyncSession,
        user_id: int,
        *,
        name: Optional[str] = None,
        notice_type: Optional[int] = None,
        status: Optional[int] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """获取通知列表（支持筛选 + 分页）"""
        conditions = [
            MsgNoticeModel.enabled_flag == 1,
            MsgNoticeModel.created_by == user_id,
        ]
        if name:
            conditions.append(MsgNoticeModel.name.like(f"%{name}%"))
        if notice_type is not None:
            conditions.append(MsgNoticeModel.type == int(notice_type))
        if status is not None:
            conditions.append(MsgNoticeModel.status == int(status))

        total_result = await db.execute(select(func.count()).where(*conditions))
        total = int(total_result.scalar() or 0)

        stmt = (
            select(MsgNoticeModel)
            .where(*conditions)
            .order_by(MsgNoticeModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(stmt)
        notices = result.scalars().all()

        content = [
            {
                "id": n.id,
                "name": n.name,
                "type": n.type,
                "value": n.value,
                "status": n.status,
                "script": n.script,
                "description": n.description,
                "creation_date": n.creation_date,
            }
            for n in notices
        ]

        return {
            "content": content,
            "total": total,
            "page": page,
            "size": size,
        }
    
    @staticmethod
    async def create_notice(db: AsyncSession, notice_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """创建通知配置"""
        notice = MsgNoticeModel(
            name=notice_data["name"],
            type=int(notice_data["type"]),
            value=str(notice_data["value"]),
            status=int(notice_data.get("status", 1)),
            script=notice_data.get("script") or {},
            description=notice_data.get("description"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(notice)
        await db.commit()
        return {"id": notice.id}
    
    @staticmethod
    async def update_notice(db: AsyncSession, notice_id: int, notice_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """更新通知配置"""
        result = await db.execute(
            select(MsgNoticeModel).where(
                MsgNoticeModel.id == notice_id,
                MsgNoticeModel.enabled_flag == 1,
                MsgNoticeModel.created_by == user_id,
            )
        )
        notice = result.scalar_one_or_none()
        if not notice:
            return {"success": False, "message": "通知不存在"}

        for field in ("name", "type", "value", "status", "script", "description"):
            if field in notice_data and notice_data[field] is not None:
                setattr(notice, field, notice_data[field])
        notice.updated_by = user_id
        await db.commit()
        return {"success": True}
    
    @staticmethod
    async def delete_notice(db: AsyncSession, notice_id: int, user_id: int) -> bool:
        """删除通知配置"""
        await db.execute(
            update(MsgNoticeModel)
            .where(
                MsgNoticeModel.id == notice_id,
                MsgNoticeModel.enabled_flag == 1,
                MsgNoticeModel.created_by == user_id,
            )
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()
        return True
    
    @staticmethod
    async def get_task_history(
        db: AsyncSession,
        task_id: Optional[int],
        user_id: int,
        *,
        status: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> Dict[str, Any]:
        """获取任务执行历史（支持筛选 + 分页）"""
        conditions = [TaskExecutionHistoryModel.enabled_flag == 1]
        if task_id:
            conditions.append(TaskExecutionHistoryModel.task_id == int(task_id))
        if status:
            conditions.append(TaskExecutionHistoryModel.status == str(status))

        total_result = await db.execute(select(func.count()).where(*conditions))
        total = int(total_result.scalar() or 0)

        stmt = (
            select(TaskExecutionHistoryModel)
            .where(*conditions)
            .order_by(TaskExecutionHistoryModel.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        content = [
            {
                "id": r.id,
                "task_id": r.task_id,
                "execution_id": r.execution_id,
                "status": r.status,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "duration": r.duration,
                "result": r.result,
                "error_message": r.error_message,
                "trigger_type": r.trigger_type,
            }
            for r in rows
        ]

        return {
            "content": content,
            "total": total,
            "page": page,
            "size": size,
        }
    
    @staticmethod
    async def schedule_task(
        task_id: int,
        time_config: Dict[str, Any],
        script_config: Dict[str, Any],
        task_type: int,
        user_id: int,
    ) -> str:
        """调度任务（使用APScheduler）"""
        trigger = build_trigger(time_config)
        job_id = str(task_id)

        add_or_replace_job(
            job_id=job_id,
            func=TaskSchedulerService.execute_scheduled_task,
            trigger=trigger,
            args=[
                {
                    "id": task_id,
                    "type": task_type,
                    "script": script_config,
                    "time": time_config,
                    "user_id": user_id,
                }
            ]
        )
        return job_id
    
    @staticmethod
    async def unschedule_task(task_id: str) -> bool:
        """取消任务调度"""
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id=str(task_id))
        if job:
            scheduler.remove_job(str(task_id))
        return True
    
    @staticmethod
    async def execute_scheduled_task(task_config: Dict[str, Any]) -> Dict[str, Any]:
        """执行定时任务"""
        # 先实现“触发 + 记录”，执行引擎后续再接入（与 Celery 解耦）
        execution_id = str(uuid.uuid4())
        start = datetime.now()
        status = "success"
        error_message = None
        result: Dict[str, Any] = {"message": "scheduled trigger ok (execution engine not integrated yet)"}

        try:
            # 根据 task_config["type"] 调用对应模块执行入口
            # - API(3) -> api_automation（对齐旧 gitlab_ci_notice / 定时执行接口自动化脚本）
            if int(task_config.get("type") or 0) == 3:
                from app.db.sqlalchemy import async_session
                from app.api.v1.api_automation.service import ApiAutomationService
                from app.api.v1.api_automation.model import ApiScriptModel

                script_cfg = task_config.get("script") or {}
                env_id = int(script_cfg.get("env_id") or 0)
                api_script_list = script_cfg.get("api_script_list") or []
                user_id = int(task_config.get("user_id") or 1)

                async with async_session() as session:
                    for sid in api_script_list:
                        row = (
                            await session.execute(
                                select(ApiScriptModel).where(ApiScriptModel.id == int(sid), ApiScriptModel.enabled_flag == 1)
                            )
                        ).scalar_one_or_none()
                        if not row:
                            continue
                        # ApiScriptModel.script 在旧架构里就是 run_list 结构
                        run_body = {
                            "result_id": int(time.time() * 1000),
                            "name": f"{task_config.get('id')}-{row.name}",
                            "config": {"env_id": env_id},
                            "run_list": row.script or [],
                        }
                        await ApiAutomationService.run_api_script(session, run_body, user_id)
                result = {"message": "api automation scheduled executed", "scripts": api_script_list}
        except Exception as e:
            status = "failed"
            error_message = str(e)
            result = {"message": "execution failed"}
        finally:
            end = datetime.now()
            duration = int((end - start).total_seconds())

        # APScheduler 回调不走 FastAPI Depends，这里单独创建 session 做落库与状态更新
        try:
            from app.db.sqlalchemy import async_session
            from .scheduler import get_scheduler

            async with async_session() as session:
                # 执行历史由调度器事件监听统一记录，避免重复写入
                # 这里只更新 task 的运行信息（last/next/total_run_count）
                task_id = int(task_config.get("id") or 0)
                if task_id:
                    scheduler = get_scheduler()
                    job = scheduler.get_job(job_id=str(task_id))
                    await session.execute(
                        update(SchedulerTaskModel)
                        .where(SchedulerTaskModel.id == task_id, SchedulerTaskModel.enabled_flag == 1)
                        .values(
                            last_run_at=end,
                            next_run_at=job.next_run_time if (job and job.next_run_time) else None,
                            total_run_count=(SchedulerTaskModel.total_run_count + 1),
                        )
                    )
                await session.commit()
        except Exception:
            # 落库失败不影响调度器线程继续跑
            pass

        # 执行统一通知（使用新架构 notifications 配置）
        try:
            await TaskSchedulerService.send_task_notification(
                {
                    "task_id": task_config.get("id"),
                    "execution_id": execution_id,
                    "status": status,
                    "start_time": start,
                    "end_time": end,
                    "duration": duration,
                    "result": result,
                    "error_message": error_message,
                    "type": task_config.get("type"),
                },
                task_config.get("notice") or {},
            )
        except Exception:
            # 通知失败不影响调度主流程
            pass

        return {
            "task_id": task_config.get("id"),
            "execution_id": execution_id,
            "status": status,
            "start_time": start,
            "end_time": end,
            "duration": duration,
            "result": result,
            "error_message": error_message,
        }
    
    @staticmethod
    async def send_task_notification(task_result: Dict[str, Any], notice_config: Dict[str, Any]) -> bool:
        """
        发送任务通知：对接新架构统一通知模块。

        - 根据任务 ID + 任务类型，读取 `task_notification_settings`
        - 按照 notify_on_success / notify_on_failure 策略发送
        """
        from app.db.sqlalchemy import async_session
        from app.api.v1.notifications.service import notification_service, task_notification_service
        from app.api.v1.notifications.schema import SendNotificationRequest

        task_id = int(task_result.get("task_id") or 0)
        if not task_id:
            return False

        # 将 legacy 任务类型(int) 映射为通知系统中的 task_type 字符串
        raw_type = int(task_result.get("type") or 0)
        if raw_type == 3:
            task_type = "API"
        elif raw_type == 2:
            task_type = "WEB_UI"
        elif raw_type == 1:
            task_type = "APP"
        else:
            task_type = "API"

        status = str(task_result.get("status") or "")

        async with async_session() as session:
            # 读取任务本身信息（名称等），用于通知内容
            task_row = (
                await session.execute(
                    select(SchedulerTaskModel).where(
                        SchedulerTaskModel.id == task_id,
                        SchedulerTaskModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()

            task_name = task_row.name if task_row else f"Task-{task_id}"

            # 读取任务通知设置
            settings_data = await task_notification_service.get_task_settings(
                db=session,
                task_id=task_id,
                task_type=task_type,
            )
            settings = settings_data.get("items") or []

            if not settings:
                return False

            title = f"[定时任务][{status}] {task_name}"
            # 简单组织通知内容（后续可以根据需要扩展模板）
            content_lines = [
                f"任务ID: {task_id}",
                f"任务名称: {task_name}",
                f"执行ID: {task_result.get('execution_id')}",
                f"执行状态: {status}",
                f"开始时间: {task_result.get('start_time')}",
                f"结束时间: {task_result.get('end_time')}",
                f"耗时(秒): {task_result.get('duration')}",
            ]
            if task_result.get("error_message"):
                content_lines.append(f"错误信息: {task_result.get('error_message')}")
            content = "\n".join([str(x) for x in content_lines if x is not None])

            # 遍历所有通知设置并按策略发送
            for s in settings:
                if not s.get("is_enabled", True):
                    continue
                if status == "success" and not s.get("notify_on_success", False):
                    continue
                if status != "success" and not s.get("notify_on_failure", True):
                    continue

                req = SendNotificationRequest(
                    config_id=int(s["notification_config_id"]),
                    title=title,
                    content=content,
                    recipient=str(s.get("task_type") or task_type),
                )
                await notification_service.send_notification(
                    db=session,
                    request=req,
                    current_user_id=0,
                )

        return True
    
    @staticmethod
    async def load_enabled_tasks(db: AsyncSession) -> List[Dict[str, Any]]:
        """加载启用的任务（系统启动时调用）"""
        result = await db.execute(
            select(SchedulerTaskModel).where(
                SchedulerTaskModel.enabled_flag == 1,
                SchedulerTaskModel.status == 1,
            )
        )
        tasks = result.scalars().all()
        loaded: List[Dict[str, Any]] = []
        for t in tasks:
            try:
                await TaskSchedulerService.schedule_task(
                    task_id=int(t.id),
                    time_config=t.time or {},
                    script_config=t.script or {},
                    task_type=int(t.type),
                    user_id=int(t.created_by or 0),
                )
                t.scheduler_job_id = str(t.id)
                t.next_run_at = TaskSchedulerService._get_job_next_run_datetime(str(t.id))
                loaded.append({"id": t.id})
            except Exception:
                continue
        await db.commit()
        return loaded

    @staticmethod
    async def load_enabled_tasks_report(db: AsyncSession) -> Dict[str, Any]:
        """
        加载启用的任务，并返回同步报告（用于 scheduler.reload）。

        返回：
        - total: DB 中符合条件的任务数
        - loaded_ids: 成功装载的任务 id 列表（字符串）
        - failed: 失败列表 [{id, error}]
        """
        result = await db.execute(
            select(SchedulerTaskModel).where(
                SchedulerTaskModel.enabled_flag == 1,
                SchedulerTaskModel.status == 1,
            )
        )
        tasks = result.scalars().all()

        loaded_ids: List[str] = []
        failed: List[Dict[str, Any]] = []
        for t in tasks:
            try:
                await TaskSchedulerService.schedule_task(
                    task_id=int(t.id),
                    time_config=t.time or {},
                    script_config=t.script or {},
                    task_type=int(t.type),
                    user_id=int(t.created_by or 0),
                )
                t.scheduler_job_id = str(t.id)
                t.next_run_at = TaskSchedulerService._get_job_next_run_datetime(str(t.id))
                loaded_ids.append(str(t.id))
            except Exception as e:
                failed.append({"id": str(t.id), "error": str(e)})
                continue

        await db.commit()
        return {
            "total": len(tasks),
            "loaded_ids": loaded_ids,
            "failed": failed,
        }

    @staticmethod
    def _get_job_next_run_datetime(job_id: str):
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id=str(job_id))
        return job.next_run_time if job else None