#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas

from typing import Optional

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from app.api.v1.performance.config.model import PerfConfigMachineModel, PerfConfigParamModel
from app.core import BaseCRUD
from app.utils.crypto import encrypt_field


def _prepare_ssh_password(new_val: Optional[str], existing_val: Optional[str] = None) -> Optional[str]:
    """
    处理 SSH 密码字段：
      None          → 不更新（update 场景保留原值）
      ''            → 清空
      startswith gAAAAA → 已是 Fernet token（复制场景），原样存库
      其他非空字符串 → 明文新密码，Fernet 加密后存库
    """
    if new_val is None:
        return existing_val
    if new_val == '':
        return None
    if new_val.startswith('gAAAAA'):
        return new_val
    return encrypt_field(new_val)


class PerfMachineCRUD(BaseCRUD[PerfConfigMachineModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(PerfConfigMachineModel, db)

    async def get_master_machine(self) -> PerfConfigMachineModel | None:
        """获取第一台启用的 Master 控制机（machine_type=1），用作 SSH 跳板。无 Master 则返回 None（直连）。"""
        stmt = select(self.model).where(
            self.model.enabled_flag == 1,
            self.model.status == 1,
            self.model.machine_type == 1,
        ).order_by(self.model.id.asc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_available_machines(self, limit: int = -1, machine_type: int = 2) -> list[PerfConfigMachineModel]:
        """
        获取可用的压力机信息（状态启用，未软删除）。
        Args:
            limit: 限制的机器数量（前端输入），默认-1表示无限制
            machine_type: 压力机类型，2-Slave，3-单机，默认2
        Returns:
            list[PerfConfigMachineModel]: 压力机数据列表
        """
        stmt = select(self.model).where(
            self.model.enabled_flag == 1, self.model.status == 1,
            self.model.machine_type == machine_type
        ).order_by(self.model.id.asc())

        # 判断是否限制压力机数量
        if limit >= 1:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_machines_by_ids(self, ids: list[int]) -> list[PerfConfigMachineModel]:
        """按 ID 列表查询压力机（用于清除分发时精准定位已分发的机器）。"""
        if not ids:
            return []
        stmt = select(self.model).where(
            self.model.enabled_flag == 1,
            self.model.id.in_(ids),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class PerfParamCRUD(BaseCRUD[PerfConfigParamModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(PerfConfigParamModel, db)

    async def get_param_value(self, param_key: str, default: str = None) -> str:
        """
        根据参数名获取参数值方法（param_key）。

        Args:
            param_key: 参数配置列表的参数名
            default: 未找到时设定的默认值
        Returns:
            参数配置列表的参数值（一条或者空）
        """
        stmt = select(PerfConfigParamModel.param_value).where(
            PerfConfigParamModel.param_key == param_key,
            PerfConfigParamModel.enabled_flag == 1,
            PerfConfigParamModel.status == 1
        )
        result = await self.db.execute(stmt)
        value = result.scalar_one_or_none()
        return value if value is not None else default