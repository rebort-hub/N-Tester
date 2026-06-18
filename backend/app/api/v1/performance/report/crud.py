#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseCRUD
from .model import PerfReportModel

"""
性能测试 - 压测报告 CRUD
"""


class PerfReportCRUD(BaseCRUD):
    """压测报告 CRUD，扩展分页列表联查操作人名称。"""

    def __init__(self, db: AsyncSession):
        super().__init__(PerfReportModel, db)

    async def get_list_with_filter(
        self,
        report_name:        Optional[str]      = None,
        scenario_code:      Optional[str]      = None,
        creator:            Optional[str]      = None,
        generated_at_start: Optional[str]      = None,
        generated_at_end:   Optional[str]      = None,
        page:               int                = 1,
        page_size:          int                = 20,
    ) -> tuple[list, int]:
        """分页查询压测报告列表，支持多字段组合过滤。

        Args:
            report_name:        报告文件名称，模糊匹配
            scenario_code:      场景编号，精确匹配
            creator:            报告人，模糊匹配
            generated_at_start: 报告生成时间起（含）
            generated_at_end:   报告生成时间止（含）
            page:               页码，从 1 开始
            page_size:          每页条数
        Returns:
            (记录列表, 总数)
        """
        conditions = [PerfReportModel.enabled_flag == 1]

        if report_name:
            conditions.append(PerfReportModel.report_name.like(f'%{report_name}%'))
        if scenario_code:
            conditions.append(PerfReportModel.scenario_code == scenario_code)
        if creator:
            conditions.append(PerfReportModel.creator.like(f'%{creator}%'))
        if generated_at_start:
            conditions.append(PerfReportModel.generated_at >= generated_at_start)
        if generated_at_end:
            conditions.append(PerfReportModel.generated_at <= generated_at_end)

        count_col = func.count().over().label('total')
        stmt = (
            select(PerfReportModel, count_col)
            .where(and_(*conditions))
            .order_by(PerfReportModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        rows = (await self.db.execute(stmt)).all()
        total = rows[0].total if rows else 0
        return [r[0] for r in rows], total