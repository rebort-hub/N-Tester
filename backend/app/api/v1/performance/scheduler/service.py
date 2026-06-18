#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from datetime import datetime
from typing import Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .crud import PerfSchedulerCRUD
from .jobs import register_scheduler_job, remove_scheduler_job
from .model import PerfSchedulerModel
from .schema import (
    PerfSchedulerCreateReqSchema,
    PerfSchedulerListRespSchema,
    PerfSchedulerUpdateReqSchema,
)

"""
性能测试 - 定时任务 Service

任务状态流转：
  待触发(0) → 进行中(1)：APScheduler 到达 plan_time 后触发（jobs.py 驱动）
  进行中(1) → 已结束(2)：压测执行完成后由 perf_log_collector 回写
  进行中(1) → 已取消(3)：用户主动取消，同时终止 JMeter 进程
  已取消(3) → 可重新修改后等待触发

业务校验规则：
  修改/删除：task_status in (0, 3) 才允许
  取消：task_status == 1 才允许
"""

# 允许修改/删除的任务状态（待触发/已取消/失败）
_EDITABLE_STATUSES = (0, 3, 4)


class PerfSchedulerService:
    """定时任务业务逻辑。"""

    def __init__(self, db: AsyncSession):
        self.db   = db
        self.crud = PerfSchedulerCRUD(db)

    async def create(self, data: PerfSchedulerCreateReqSchema, user_id: int) -> Dict:
        """新建定时任务，写入 DB 后注册 APScheduler 触发任务。

        Args:
            data:    新建请求体
            user_id: 当前操作人 ID
        Returns:
            Dict: {'id': 新建记录主键}
        """
        obj = await self.crud.create_crud({
            **data.model_dump(),
            'created_by': user_id,
        })
        await self.db.flush()

        # 注册到 APScheduler（is_active=0 时 register 内部只清理不注册）
        register_scheduler_job(obj.id, obj.plan_time, obj.is_active)
        return {'id': obj.id}

    async def get_list(
        self,
        page: int,
        page_size: int,
        name: Optional[str] = None,
        task_status: Optional[int] = None,
        is_active: Optional[int] = None,
    ) -> Dict:
        """分页查询定时任务列表，支持任务名称/任务状态/启用状态过滤。

        Args:
            page:        页码，从 1 开始
            page_size:   每页条数
            name:        任务名称，模糊匹配
            task_status: 任务状态精确匹配（0/1/2/3）
            is_active:   启用状态精确匹配（0/1）
        Returns:
            Dict: {items, total, page, page_size}
        """
        conditions = [PerfSchedulerModel.enabled_flag == 1]
        if name:
            conditions.append(PerfSchedulerModel.name.like(f'%{name}%'))
        if task_status is not None:
            conditions.append(PerfSchedulerModel.task_status == task_status)
        if is_active is not None:
            conditions.append(PerfSchedulerModel.is_active == is_active)

        rows, total = await self.crud.get_list_with_scenario(
            conditions=conditions,
            order_by=[PerfSchedulerModel.id.desc()],
            skip=(page - 1) * page_size,
            limit=page_size,
        )

        items = []
        for row in rows:
            item = PerfSchedulerListRespSchema.model_validate(row[0]).model_dump()
            item['scenario_code'] = row.scenario_code
            item['script_name']   = row.script_name
            item['operator_name'] = row.operator_name
            items.append(item)

        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

    async def update(self, data: PerfSchedulerUpdateReqSchema, user_id: int) -> None:
        """修改定时任务，仅允许状态为 待触发(0) 或 已取消(3) 时修改。
        修改后重新注册 APScheduler 触发任务（使用新 plan_time 和 is_active）。

        Args:
            data:    修改请求体（含 id）
            user_id: 当前操作人 ID
        Raises:
            HTTPException 404: 任务不存在
            HTTPException 400: 任务状态不允许修改
        """
        obj = await self._get_or_404(data.id)
        if obj.task_status not in _EDITABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'当前任务状态（{obj.task_status}）不允许修改，仅 待触发/已取消 状态可编辑',
            )
        update_data = data.model_dump(exclude={'id'}, exclude_unset=True)
        update_data['updated_by'] = user_id
        await self.crud.update_crud(data.id, update_data)
        await self.db.flush()

        # 读取更新后的最新值用于重注册
        updated = await self.crud.get_by_id_crud(data.id)
        register_scheduler_job(data.id, updated.plan_time, updated.is_active)

    async def delete(self, scheduler_id: int) -> None:
        """软删除定时任务，仅允许状态为 待触发(0) 或 已取消(3) 时删除。
        删除前先移除 APScheduler 任务。

        Args:
            scheduler_id: 任务主键 ID
        Raises:
            HTTPException 404: 任务不存在
            HTTPException 400: 任务状态不允许删除
        """
        obj = await self._get_or_404(scheduler_id)
        if obj.task_status not in _EDITABLE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'当前任务状态（{obj.task_status}）不允许删除，仅 待触发/已取消 状态可删除',
            )
        remove_scheduler_job(scheduler_id)
        await self.crud.soft_delete_crud([scheduler_id])

    async def cancel(self, scheduler_id: int, user_id: int) -> None:
        """取消进行中的定时任务：更新状态为已取消，并强制终止关联的 JMeter 压测进程。

        Args:
            scheduler_id: 任务主键 ID
            user_id:      当前操作人 ID
        Raises:
            HTTPException 404: 任务不存在
            HTTPException 400: 任务不处于进行中状态
        """
        obj = await self._get_or_404(scheduler_id)
        if obj.task_status != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'当前任务状态（{obj.task_status}）不允许取消，仅 进行中 状态可取消',
            )

        now = datetime.now()
        await self.crud.update_crud(scheduler_id, {
            'task_status': 3,
            'is_active':   0,
            'end_time':    now,
            'updated_by':  user_id,
        })

        # 强制终止关联压测进程并还原场景/文件/Redis 状态
        try:
            from app.api.v1.performance.scenario.service import stop_running_scenario
            await stop_running_scenario(obj.scenario_id, user_id, self.db)
        except Exception as e:
            from app.corelibs.logger import logger
            logger.warning(f"[Scheduler.cancel] 停止压测异常 scheduler_id={scheduler_id}: {e}")

    async def _get_or_404(self, scheduler_id: int) -> PerfSchedulerModel:
        """查询任务记录，不存在或已软删除时抛 404。"""
        obj = await self.crud.get_by_id_crud(scheduler_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='定时任务不存在')
        return obj