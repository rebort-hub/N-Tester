#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseCRUD
from .model import PerfSchedulerModel

"""
性能测试 - 定时任务 CRUD
"""


class PerfSchedulerCRUD(BaseCRUD):
    """定时任务 CRUD，扩展列表查询，联查场景编号/脚本名/操作人。"""

    def __init__(self, db: AsyncSession):
        super().__init__(PerfSchedulerModel, db)

    async def get_list_with_scenario(
        self, conditions: list = None, order_by: list = None, skip: int = 0, limit: int = 20,
    ) -> tuple[list, int]:
        """分页查询定时任务列表，单次 SQL 联查场景编号、脚本名和操作人名称。

        Args:
            conditions: WHERE 条件列表
            order_by:   排序条件列表
            skip:       分页偏移
            limit:      每页条数
        Returns:
            (Row 列表, 总数)：每行含 PerfSchedulerModel 及 scenario_code/script_name/operator_name
        """
        from app.api.v1.performance.scenario.model import PerfScenarioModel
        from app.api.v1.system.user.model import UserModel

        count_col     = func.count().over().label('total')
        scenario_code = PerfScenarioModel.code.label('scenario_code')
        script_name   = PerfScenarioModel.script_name.label('script_name')
        operator_col  = UserModel.username.label('operator_name')

        stmt = (
            select(PerfSchedulerModel, count_col, scenario_code, script_name, operator_col)
            .outerjoin(
                PerfScenarioModel,
                PerfScenarioModel.id == PerfSchedulerModel.scenario_id,
            )
            .outerjoin(
                UserModel,
                UserModel.id == func.coalesce(PerfSchedulerModel.updated_by, PerfSchedulerModel.created_by),
            )
        )
        if conditions:
            stmt = stmt.where(and_(*conditions))
        if order_by:
            for o in order_by:
                stmt = stmt.order_by(o)
        stmt = stmt.offset(skip).limit(limit)

        rows = (await self.db.execute(stmt)).all()
        total = rows[0].total if rows else 0
        return rows, total