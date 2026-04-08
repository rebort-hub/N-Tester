"""
定时任务业务逻辑服务
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
import time
from .model import MsgNoticeModel, SchedulerTaskModel, TaskExecutionHistoryModel
from .scheduler import add_or_replace_job, build_trigger, get_scheduler


class TaskSchedulerService:
    """定时任务服务"""

    @staticmethod
    def _safe_job_next_run_time(job: Any):
        """ob 对象，安全获取 next_run_time。"""
        if not job:
            return None
        return getattr(job, "next_run_time", None)

    @staticmethod
    def _format_datetime_for_ui(dt: Optional[datetime]) -> str:
        """统一前端时间格式"""
        if not dt:
            return ""
        try:
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone(timedelta(hours=8))).replace(tzinfo=None)
        except Exception:
            pass
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _map_task_type_to_notify_type(task_type: int) -> str:
        if int(task_type) == 3:
            return "API"
        if int(task_type) == 2:
            return "WEB_UI"
        if int(task_type) == 1:
            return "APP"
        return "API"

    @staticmethod
    async def _sync_task_notification_setting(
        db: AsyncSession,
        *,
        task_id: int,
        task_type: int,
        notice_config: Optional[Dict[str, Any]],
        user_id: int,
    ) -> None:
        
        from app.api.v1.notifications.service import task_notification_service
        from app.api.v1.notifications.schema import TaskNotificationSettingCreate, TaskNotificationSettingUpdate

        notify_type = TaskSchedulerService._map_task_type_to_notify_type(task_type)
        status = int((notice_config or {}).get("status") or 0)
        notice_id = (notice_config or {}).get("notice_id")

        existed = await task_notification_service.get_task_settings(
            db=db,
            task_id=int(task_id),
            task_type=notify_type,
        )
        items = existed.get("items") or []

        
        if status != 1 or not notice_id:
            for item in items:
                await task_notification_service.update_task_setting(
                    db=db,
                    setting_id=int(item["id"]),
                    setting_data=TaskNotificationSettingUpdate(is_enabled=False),
                    current_user_id=user_id,
                )
            return

        notice_id = int(notice_id)
        current = next((x for x in items if int(x.get("notification_config_id") or 0) == notice_id), None)

        
        if current:
            await task_notification_service.update_task_setting(
                db=db,
                setting_id=int(current["id"]),
                setting_data=TaskNotificationSettingUpdate(
                    is_enabled=True,
                    notify_on_success=True,
                    notify_on_failure=True,
                ),
                current_user_id=user_id,
            )
            for item in items:
                if int(item["id"]) == int(current["id"]):
                    continue
                await task_notification_service.update_task_setting(
                    db=db,
                    setting_id=int(item["id"]),
                    setting_data=TaskNotificationSettingUpdate(is_enabled=False),
                    current_user_id=user_id,
                )
            return

       
        await task_notification_service.create_task_setting(
            db=db,
            setting_data=TaskNotificationSettingCreate(
                task_id=int(task_id),
                task_type=notify_type,
                notification_config_id=notice_id,
                is_enabled=True,
                notify_on_success=True,
                notify_on_failure=True,
            ),
            current_user_id=user_id,
        )
        for item in items:
            await task_notification_service.update_task_setting(
                db=db,
                setting_id=int(item["id"]),
                setting_data=TaskNotificationSettingUpdate(is_enabled=False),
                current_user_id=user_id,
            )
    
    @staticmethod
    async def get_task_list(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        """获取任务列表"""
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
            next_run_time = TaskSchedulerService._safe_job_next_run_time(job)
            latest_row = (
                await db.execute(
                    select(TaskExecutionHistoryModel)
                    .where(
                        TaskExecutionHistoryModel.task_id == int(t.id),
                        TaskExecutionHistoryModel.enabled_flag == 1,
                    )
                    .order_by(TaskExecutionHistoryModel.id.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
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
                    "next_run_at": TaskSchedulerService._format_datetime_for_ui(t.next_run_at),
                    "total_run_count": t.total_run_count or 0,
                    "creation_date": t.creation_date,
                    "latest_status": latest_row.status if latest_row else "",
                    "latest_run_time": TaskSchedulerService._format_datetime_for_ui(
                        latest_row.end_time if (latest_row and latest_row.end_time) else (latest_row.start_time if latest_row else None)
                    ),
                    "next_time": TaskSchedulerService._format_datetime_for_ui(next_run_time),
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
            next_run_time = TaskSchedulerService._safe_job_next_run_time(job)
            latest_row = (
                await db.execute(
                    select(TaskExecutionHistoryModel)
                    .where(
                        TaskExecutionHistoryModel.task_id == int(t.id),
                        TaskExecutionHistoryModel.enabled_flag == 1,
                    )
                    .order_by(TaskExecutionHistoryModel.id.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
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
                    "next_run_at": TaskSchedulerService._format_datetime_for_ui(t.next_run_at),
                    "total_run_count": t.total_run_count or 0,
                    "creation_date": t.creation_date,
                    "latest_status": latest_row.status if latest_row else "",
                    "latest_run_time": TaskSchedulerService._format_datetime_for_ui(
                        latest_row.end_time if (latest_row and latest_row.end_time) else (latest_row.start_time if latest_row else None)
                    ),
                    "next_time": TaskSchedulerService._format_datetime_for_ui(next_run_time),
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
        await TaskSchedulerService._sync_task_notification_setting(
            db,
            task_id=int(task.id),
            task_type=int(task.type),
            notice_config=task.notice or {},
            user_id=user_id,
        )

        await db.commit()
  
        try:
            from .remote_control import send_command

            await send_command("scheduler.reload", timeout_s=30.0)
        except Exception:
            pass
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

      
        await TaskSchedulerService.unschedule_task(str(task.id))
        task.scheduler_job_id = None
        task.next_run_at = None

        if int(task.status) == 1:
            await TaskSchedulerService.schedule_task(task.id, task.time or {}, task.script or {}, int(task.type), user_id)
            task.scheduler_job_id = str(task.id)
            task.next_run_at = TaskSchedulerService._get_job_next_run_datetime(str(task.id))
        await TaskSchedulerService._sync_task_notification_setting(
            db,
            task_id=int(task.id),
            task_type=int(task.type),
            notice_config=task.notice or {},
            user_id=user_id,
        )

        await db.commit()
        
        try:
            from .remote_control import send_command

            await send_command("scheduler.reload", timeout_s=30.0)
        except Exception:
            pass
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
      
        try:
            from .remote_control import send_command

            await send_command("scheduler.reload", timeout_s=30.0)
        except Exception:
            pass
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
            
            if int(task_config.get("type") or 0) == 3:
                from app.db.sqlalchemy import async_session
                from app.api.v1.api_automation.service import ApiAutomationService
                from app.api.v1.api_automation.model import ApiScriptModel

                script_cfg = task_config.get("script") or {}
                env_id = int(script_cfg.get("env_id") or 0)
                api_script_list = script_cfg.get("api_script_list") or []
                user_id = int(task_config.get("user_id") or 1)
                task_id = int(task_config.get("id") or 0)

                async with async_session() as session:
                    task_name = f"scheduler-api-{task_id}"
                    if task_id:
                        task_row = (
                            await session.execute(
                                select(SchedulerTaskModel).where(
                                    SchedulerTaskModel.id == task_id,
                                    SchedulerTaskModel.enabled_flag == 1,
                                )
                            )
                        ).scalar_one_or_none()
                        if task_row and task_row.name:
                            task_name = str(task_row.name)

                    # 定时任务一次触发 => 生成一个 result_id，汇总到同一份报告里
                    api_result_id = int(time.time() * 1000)
                    merged_run_list: List[Dict[str, Any]] = []
                    for sid in api_script_list:
                        row = (
                            await session.execute(
                                select(ApiScriptModel).where(ApiScriptModel.id == int(sid), ApiScriptModel.enabled_flag == 1)
                            )
                        ).scalar_one_or_none()
                        if not row:
                            continue
                  
                        # ApiScriptModel.script 即 run_list 结构
                        merged_run_list.extend(row.script or [])

                    run_body = {
                        "result_id": api_result_id,
                        "name": task_name,
                        "config": {"env_id": env_id},
                        "run_list": merged_run_list,
                    }
                    await ApiAutomationService.run_api_script(session, run_body, user_id)

                result = {
                    "message": "api automation scheduled executed",
                    "scripts": api_script_list,
                    "api_result_id": api_result_id,
                }
            elif int(task_config.get("type") or 0) == 2:
                from app.db.sqlalchemy import async_session
                from app.api.v1.web_management.service import WebManagementService
                from app.api.v1.web_management.model import WebGroupModel

                script_cfg = task_config.get("script") or {}
                web_group_ids = script_cfg.get("web_group_list") or script_cfg.get("web_script_list") or []
                browser_list = script_cfg.get("browser") or [1]
                width = int(script_cfg.get("width") or 1920)
                height = int(script_cfg.get("height") or 1080)
                user_id = int(task_config.get("user_id") or 1)
                task_id = int(task_config.get("id") or 0)

                merged_scripts: List[Dict[str, Any]] = []
                seen_script_ids: set[int] = set()

                async with async_session() as session:
                    task_name = f"scheduler-web-{task_id}"
                    if task_id:
                        task_row = (
                            await session.execute(
                                select(SchedulerTaskModel).where(
                                    SchedulerTaskModel.id == task_id,
                                    SchedulerTaskModel.enabled_flag == 1,
                                )
                            )
                        ).scalar_one_or_none()
                        if task_row and task_row.name:
                            task_name = str(task_row.name)

                    if web_group_ids:
                        group_rows = (
                            await session.execute(
                                select(WebGroupModel).where(
                                    WebGroupModel.id.in_([int(x) for x in web_group_ids]),
                                    WebGroupModel.enabled_flag == 1,
                                    WebGroupModel.created_by == user_id,
                                )
                            )
                        ).scalars().all()

                        for g in group_rows:
                            for item in (g.script or []):
                                try:
                                    sid = int((item or {}).get("id") or 0)
                                except Exception:
                                    sid = 0
                                if sid <= 0 or sid in seen_script_ids:
                                    continue
                                seen_script_ids.add(sid)
                                merged_scripts.append(
                                    {
                                        "id": sid,
                                        "name": (item or {}).get("name") or f"script-{sid}",
                                    }
                                )

                    run_body = {
                        "result_id": str(int(time.time() * 1000)),
                        "task_name": task_name,
                        "browser": browser_list,
                        "script": merged_scripts,
                        "width": width,
                        "height": height,
                        "browser_type": 1,
                    }
                    await WebManagementService.execute_web_script(session, run_body, browser_list, user_id)

                result = {
                    "message": "web automation scheduled executed",
                    "web_group_list": web_group_ids,
                    "script_count": len(merged_scripts),
                    "web_result_id": run_body.get("result_id"),
                }
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
                            next_run_at=TaskSchedulerService._safe_job_next_run_time(job),
                            total_run_count=(SchedulerTaskModel.total_run_count + 1),
                        )
                    )
                await session.commit()
        except Exception:
            # 落库失败不影响调度器线程继续跑
            pass

        # 执行统一通知
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
        发送任务通知：对接通知模块。
        """
        from app.db.sqlalchemy import async_session
        from app.api.v1.notifications.service import notification_service, task_notification_service
        from app.api.v1.notifications.schema import SendNotificationRequest
        from config import config as app_config

        task_id = int(task_result.get("task_id") or 0)
        if not task_id:
            return False


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

            task_row = (
                await session.execute(
                    select(SchedulerTaskModel).where(
                        SchedulerTaskModel.id == task_id,
                        SchedulerTaskModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()

            task_name = task_row.name if task_row else f"Task-{task_id}"
            task_owner_id = int(getattr(task_row, "created_by", 0) or 0) if task_row else 0


            settings_data = await task_notification_service.get_task_settings(
                db=session,
                task_id=task_id,
                task_type=task_type,
            )
            settings = settings_data.get("items") or []

            if not settings:
                return False

            title = f"[定时任务][{status}] {task_name}"
            frontend_base = str(app_config.FRONTEND_BASE_URL or "").strip() or str(app_config.BASE_URL).rstrip("/")

            # 统计与报告链接（按任务类型）
            executed_cases = 0
            passed_cases = 0
            failed_cases = 0
            pass_percent = 0.0
            extra_lines: List[str] = []
            report_url = ""

            if task_type == "API":
                api_result_id = ((task_result.get("result") or {}) if isinstance(task_result.get("result"), dict) else {}).get("api_result_id")
                if api_result_id:
                    report_url = f"{frontend_base}/api-automation/report?result_id={api_result_id}"
                    try:
                        from app.api.v1.api_automation.model import ApiScriptResultListModel

                        summary = (
                            await session.execute(
                                select(ApiScriptResultListModel).where(
                                    ApiScriptResultListModel.result_id == int(api_result_id),
                                    ApiScriptResultListModel.enabled_flag == 1,
                                )
                            )
                        ).scalar_one_or_none()
                        run_list = (summary.script or []) if summary else []
                        executed_cases = len(run_list)
                        passed_cases = len([c for c in run_list if int((c or {}).get("status") or 0) == 1])
                        failed_cases = len([c for c in run_list if int((c or {}).get("status") or 0) == 0])
                        r = (summary.result or {}) if summary else {}
                        pass_percent = float(r.get("percent") or 0)
                        total_steps = int(r.get("total") or 0)
                        extra_lines.append(f"此次共运行 {total_steps} 个步骤，涉及 {total_steps} 个接口")
                    except Exception:
                        pass

            elif task_type == "WEB_UI":
                web_result_id = ((task_result.get("result") or {}) if isinstance(task_result.get("result"), dict) else {}).get("web_result_id")
                if web_result_id:
                    report_url = f"{frontend_base}/web/report?result_id={web_result_id}"
                    try:
                        from app.api.v1.web_management.model import WebResultListModel

                        row = (
                            await session.execute(
                                select(WebResultListModel).where(
                                    WebResultListModel.result_id == str(web_result_id),
                                    WebResultListModel.enabled_flag == 1,
                                )
                            )
                        ).scalar_one_or_none()
                        script_list = (row.script_list or []) if row else []
                        executed_cases = len(script_list)
                        
                        total_fail = 0
                        if row and isinstance(row.result, list):
                            total_fail = sum([int(x.get("run_false") or 0) for x in row.result if isinstance(x, dict)])
                        failed_cases = int(total_fail or 0)
                        passed_cases = max(executed_cases - failed_cases, 0)
                        pass_percent = round((passed_cases / executed_cases) * 100, 2) if executed_cases else 100.0
                    except Exception:
                        pass

            start_s = str(task_result.get("start_time") or "").replace("T", " ")
            end_s = str(task_result.get("end_time") or "").replace("T", " ")
            duration_s = str(task_result.get("duration") or 0)

            
            lines: List[str] = []
            lines.append(f"**任务ID**：`{task_id}`")
            lines.append(f"**任务名称**：{task_name}")
            lines.append(f"**执行ID**：`{task_result.get('execution_id')}`")
            lines.append(f"**执行状态**：**{status}**")
            lines.append("")
            lines.append(f"**开始时间**：{start_s}")
            lines.append(f"**结束时间**：{end_s}")
            lines.append(f"**耗时（秒）**：{duration_s}")
            lines.append("")
            lines.append("---")
            lines.append("**执行统计**")
            lines.append(f"- 执行：**{executed_cases}** 条用例")
            lines.append(f"- 通过：**{passed_cases}** 条用例")
            lines.append(f"- 失败：**{failed_cases}** 条用例")
            lines.append(f"- 通过率：**{pass_percent}%**")
            if extra_lines:
                lines.append("")
                lines.extend([f"> {x}" for x in extra_lines if x])

            if task_result.get("error_message"):
                lines.append("")
                lines.append(f"**错误信息**：{task_result.get('error_message')}")

            if report_url:
                lines.append("")
                lines.append(f"详情请【[点击此处]({report_url})】查看")

            content = "\n".join([x for x in lines if x is not None])

            
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
        加载启用的任务，并返回同步报告
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
        return TaskSchedulerService._safe_job_next_run_time(job)