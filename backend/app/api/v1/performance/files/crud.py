#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from _operator import and_
from typing import Optional, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.base_crud import BaseCRUD
from .model import PerfFileModel

"""
性能测试 - 文件管理 CRUD
在 BaseCRUD 基础上扩展复合查询方法，将主列表查询与 JMX 引用数据文件查询
合并为两次有序 SQL，避免 service 层多次独立连库。
"""
class PerfFileCRUD(BaseCRUD[PerfFileModel]):
    """性能测试文件 CRUD，扩展 JMX 引用数据文件的复合查询。"""

    def __init__(self, db: AsyncSession):
        super().__init__(PerfFileModel, db)

    async def get_files_with_refs(self, conditions: list, order_by: list, skip: int, limit: int,
    ) -> tuple[list, int, dict[int, PerfFileModel]]:
        """
        复合查询：主文件列表 + JMX 引用数据文件，共 2 次 SQL。

        SQL-1：带窗口函数的主列表查询（含操作人 LEFT JOIN），同 get_list_with_operator。
        SQL-2：按收集到的所有 ref_file_ids 批量 IN 查询引用数据文件（仅当存在 JMX 引用时执行）。

        Args:
            conditions: WHERE 条件列表
            order_by:   排序条件列表
            skip:       分页偏移量
            limit:      每页条数
        Returns:
            tuple:
              - rows:    主列表行结果（含 operator_name 字段）
              - total:   总记录数（窗口函数计算）
              - ref_map: {data_file_id: PerfFileModel}，JMX 引用数据文件映射表；无引用时为空字典
        """
        # SQL-1：主列表 + 操作人（窗口函数 COUNT + LEFT JOIN sys_user，单次查询）
        rows, total = await self.get_list_with_operator(
            conditions=conditions, order_by=order_by, skip=skip, limit=limit,)

        # 从当前页结果中收集所有 JMX 文件的 ref_file_ids，去重合并
        all_ref_ids: set[int] = set()
        for row in rows:
            obj = row[0]
            if obj.file_type == "jmx" and obj.ref_file_ids:
                all_ref_ids.update(obj.ref_file_ids)

        # SQL-2：批量 IN 查询引用数据文件基础信息（仅当页内存在 JMX 引用时执行）
        ref_map: dict[int, PerfFileModel] = {}
        if all_ref_ids:
            stmt = select(PerfFileModel).where(
                PerfFileModel.enabled_flag == 1, PerfFileModel.id.in_(all_ref_ids),)
            result = await self.db.execute(stmt)
            ref_map = {f.id: f for f in result.scalars().all()}

        return rows, total, ref_map

    # ------------------------------------------------------------------ #
    #  下拉选项（轻量）
    # ------------------------------------------------------------------ #

    @staticmethod
    async def get_options(db: AsyncSession, file_type: Optional[str] = None) -> List[Dict]:
        """查询文件下拉选项，返回 id、name 及 parsed_thread_config，供场景创建表单自动识别线程组类型并预填参数。"""
        conditions = [PerfFileModel.enabled_flag == 1, PerfFileModel.upload_status == 1]
        if file_type:
            conditions.append(PerfFileModel.file_type == file_type)
        stmt = (
            select(PerfFileModel.id, PerfFileModel.file_name, PerfFileModel.parsed_thread_config)
            .where(and_(*conditions))
            .order_by(PerfFileModel.id.desc())
        )
        result = await db.execute(stmt)
        return [
            {"id": row.id, "name": row.file_name, "parsed_thread_config": row.parsed_thread_config}
            for row in result.all()
        ]
