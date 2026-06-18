#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import asyncio
import base64
import hashlib
import json
import os
import re
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.performance.config.crud import PerfMachineCRUD, PerfParamCRUD
from app.api.v1.performance.files.model import PerfFileModel
from app.api.v1.performance.files.service import _build_credential
from app.core.base_crud import BaseCRUD
from app.core.minio_client import MinioClient
from app.corelibs.logger import logger
from app.common.constants import JMETER_DEBUG_GUI_LABEL
from app.utils.common import get_next_code, format_sse_event, get_temp_file_path, fmt_cloudflare_html_resp
from app.utils.oper_jmx import apply_jmx_by_type, parse_jmx_summary
from app.utils.oper_shell import ShellOperationUtils
from .crud import PerfScenarioConfigCRUD, _calc_config_duration
from .model import PerfScenarioModel, PerfScenarioConfigModel
from .schema import (
    PerfScenarioConfigCreateReqSchema, PerfScenarioConfigUpdateReqSchema,
    PerfScenarioConfigStandardRespSchema, PerfScenarioConfigSteppingRespSchema,
    PerfScenarioConfigUltimateRespSchema, PerfScenarioCreateReqSchema,
    PerfScenarioListRespSchema, PerfScenarioUpdateReqSchema,
    ConfigSyncStatsReqSchema,
)

"""
性能测试 - 压测场景 Service
"""
# ====================== 压测场景 Service ======================

class PerfScenarioService:
    """压测场景主表业务逻辑。

    职责：场景的增删改查；子配置变动时更新父场景 updated_by。
    通过 __init__ 注入 db，统一初始化所需 CRUD 实例，避免方法内重复实例化。
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scenario_crud = BaseCRUD(PerfScenarioModel, db)
        self.config_crud   = PerfScenarioConfigCRUD(db)
        self.file_crud     = BaseCRUD(PerfFileModel, db)

    async def _sync_file_ref_status(self, file_id: int, user_id: int) -> None:
        """根据场景关联情况同步 JMX 文件的引用状态（ref_status）。

        有活跃场景引用 → 2（已关联）
        无活跃场景引用 → 0（未引用），仅当前为 2 时才还原，不覆盖 1-已引用 / 3-使用中
        """
        stmt = select(func.count()).where(
            and_(
                PerfScenarioModel.script_id == file_id,
                PerfScenarioModel.enabled_flag == 1,
            )
        )
        count = (await self.db.execute(stmt)).scalar() or 0
        if count > 0:
            await self.file_crud.update_crud(file_id, {'ref_status': 2, 'updated_by': user_id})
        else:
            file_obj = await self.file_crud.get_by_id_crud(file_id)
            if file_obj and file_obj.ref_status == 2:
                await self.file_crud.update_crud(file_id, {'ref_status': 0, 'updated_by': user_id})

    async def create(self, data: PerfScenarioCreateReqSchema, user_id: int) -> Dict:
        """新建压测场景。

        Args:
            data: 新建请求体，包含场景基本信息及可选的子配置列表（高级设置）
            user_id: 当前操作人 ID，写入 created_by
        Returns:
            Dict: {"id": int} — 新建场景的主键 ID
        Raises:
            400 JMX 脚本文件不存在 / 所选文件不是 JMX 脚本
            500 系统繁忙，场景编号冲突（5 次随机重试均失败，极低概率）

        流程：
          1. 校验关联 JMX 文件存在且类型合法
          2. 随机生成 6 位场景编号，unique 约束兜底，冲突时最多重试 5 次
          3. 写入场景主记录（concurrent_count 初始为 0）
          4. 若携带子配置（高级设置），批量写入后回算并更新 concurrent_count
        """
        # 1. 校验关联的 JMX 脚本文件
        file_obj = await self.file_crud.get_by_id_crud(data.script_id)
        if not file_obj or not file_obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='JMX 脚本文件不存在')
        if file_obj.file_type.lower() != 'jmx':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='所选文件不是 JMX 脚本')

        # 2. 生成唯一场景编号：随机 6 位，unique 约束兜底，碰撞时重试
        scenario_obj = None
        for _ in range(5):
            code = get_next_code('JMX', 6)
            try:
                # 3. 写入场景主记录，script_name 冗余快照避免频繁联查
                scenario_obj = await self.scenario_crud.create_crud({
                    **data.model_dump(exclude={'configs'}),
                    'code': code, 'script_name': file_obj.file_name,
                    'status': 0, 'created_by': user_id,
                })
                break
            except IntegrityError:
                await self.db.rollback()    # code 碰撞，回滚后换号重试

        if scenario_obj is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='系统繁忙，场景编号冲突，请稍后重试',
            )

        # 4. 写入子配置（高级设置）
        if data.configs:
            for cfg in data.configs:
                cfg_data = _prepare_config_data(cfg.model_dump(), user_id)
                await self.config_crud.create_crud(cfg_data | {'scenario_id': scenario_obj.id})

        # 5. 同步 JMX 文件 ref_status → 已关联
        await self._sync_file_ref_status(data.script_id, user_id)

        return {'id': scenario_obj.id}

    async def get_list(self, page: int, page_size: int, name: Optional[str] = None, code: Optional[str] = None,
        script_name: Optional[str] = None, status_filter: Optional[int] = None, test_type: Optional[str] = None,
        created_by: Optional[int] = None,) -> Dict:
        """分页查询场景列表，支持多条件过滤。

        Args:
            page:          页码（从 1 开始）
            page_size:     每页条数
            name:          场景名称，模糊匹配
            code:          场景编号，精确匹配
            script_name:   脚本名称，模糊匹配
            status_filter: 执行状态，精确匹配（整数 0-4）
            test_type:     测试类型，精确匹配（字典值）
            created_by:    创建人 ID，精确匹配
        Returns:
            Dict: {
                "items":     list[PerfScenarioListRespSchema] — 当页场景列表（含 operator_name）,
                "total":     int  — 符合条件的总记录数,
                "page":      int  — 当前页码,
                "page_size": int  — 每页条数
            }
        """
        # 基础条件：仅返回未软删除的记录
        conditions = [PerfScenarioModel.enabled_flag == 1]

        # 动态追加过滤条件（仅传入时生效）
        if name:
            conditions.append(PerfScenarioModel.name.like(f'%{name}%'))
        if code:
            conditions.append(PerfScenarioModel.code == code)
        if script_name:
            conditions.append(PerfScenarioModel.script_name.like(f'%{script_name}%'))
        if status_filter is not None:
            conditions.append(PerfScenarioModel.status == status_filter)
        if test_type:
            conditions.append(PerfScenarioModel.test_type == test_type)
        if created_by:
            conditions.append(PerfScenarioModel.created_by == created_by)

        # 单次 SQL 获取总数 + 数据 + 操作人名称（窗口函数 + LEFT JOIN）
        rows, total = await self.scenario_crud.get_list_with_operator(
            conditions=conditions,
            order_by=[PerfScenarioModel.id.desc()],
            skip=(page - 1) * page_size,
            limit=page_size,
        )

        # 实时聚合每行场景的 concurrent_count / known_times / has_unknown_times（不存数据库，按需计算）
        scenario_ids = [row[0].id for row in rows]
        concurrent_map                    = await self.config_crud.get_concurrent_count_map(scenario_ids)
        known_times_map, has_unknown_set  = await self.config_crud.get_sub_duration_stats_map(scenario_ids)

        # operator_name 为联查字段，不在 ORM 模型中，需手动注入
        items = []
        for row in rows:
            item = PerfScenarioListRespSchema.model_validate(row[0]).model_dump()
            item['operator_name']     = row.operator_name
            item['concurrent_count']  = concurrent_map.get(row[0].id, 0)
            item['has_unknown_times'] = row[0].id in has_unknown_set
            item['known_times']       = known_times_map.get(row[0].id)
            items.append(item)

        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

    async def update(self, scenario_id: int, data: PerfScenarioUpdateReqSchema, user_id: int) -> None:
        """修改场景主信息，支持高级设置下同步修改子配置。

        Args:
            scenario_id: 待修改的场景主键 ID
            data:        修改请求体，仅传入需变更的字段（exclude_unset）；
                         data.configs 不为空时表示高级设置开启，携带子配置变更
            user_id:     当前操作人 ID，写入 updated_by
        Returns:
            None
        Raises:
            404 场景不存在
            400 JMX 脚本文件不存在 / 所选文件不是 JMX 脚本

        流程：
          1. 校验场景存在
          2. 若更换脚本，重新校验文件并刷新 script_name 快照
          3. 高级设置开启时，逐条更新子配置，完成后回算 concurrent_count
          4. 写入场景主表变更
        """
        # 1. 校验场景是否存在且未被软删除
        obj = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='场景不存在')

        # 仅取前端实际传入的字段，避免覆盖未传字段
        update_data = data.model_dump(exclude={'configs'}, exclude_unset=True)
        old_script_id = obj.script_id

        # 2. 更换脚本时重新校验并刷新 script_name 冗余快照
        if 'script_id' in update_data:
            file_obj = await self.file_crud.get_by_id_crud(update_data['script_id'])
            if not file_obj or not file_obj.enabled_flag:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='JMX 脚本文件不存在')
            if file_obj.file_type.lower() != 'jmx':
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='所选文件不是 JMX 脚本')
            update_data['script_name'] = file_obj.file_name

        # 3. 高级设置：逐条更新子配置
        if data.configs:
            for cfg in data.configs:
                cfg_data = cfg.model_dump(exclude={'id', 'thread_type'}, exclude_unset=True)
                if cfg_data:
                    # ultimate 类型更新时重新汇总 thread_count
                    cfg_obj = await self.config_crud.get_by_id_crud(cfg.id)
                    if cfg_obj and cfg_obj.thread_type == '3' and 'ultimate_rows' in cfg_data:
                        rows = cfg_data['ultimate_rows'] or []
                        cfg_data['thread_count'] = sum(r.get('start_threads', 0) for r in rows)
                    await self.config_crud.update_crud(cfg.id, {**cfg_data, 'updated_by': user_id})

        # 4. 写入主表
        await self.scenario_crud.update_crud(scenario_id, {**update_data, 'updated_by': user_id})

        # 5. 脚本变更时同步新旧文件 ref_status
        new_script_id = update_data.get('script_id')
        if new_script_id and new_script_id != old_script_id:
            await self._sync_file_ref_status(old_script_id, user_id)
            await self._sync_file_ref_status(new_script_id, user_id)

    async def delete(self, scenario_id: int, user_id: int) -> None:
        """软删除场景及其全部子配置。

        Args:
            scenario_id: 待删除的场景主键 ID
        Returns:
            None
        Raises:
            404 场景不存在
            400 运行中的场景不可删除（status=2 时禁止，防止误中断正在执行的压测任务）
        """
        obj = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='场景不存在')
        if obj.status == 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='运行中的场景不可删除')

        script_id = obj.script_id
        # 软删除主记录，再级联软删除所有子配置
        await self.scenario_crud.soft_delete_crud([scenario_id])
        configs = await self.config_crud.get_configs(scenario_id)
        if configs:
            await self.config_crud.soft_delete_crud([c.id for c in configs])

        # 同步 JMX 文件 ref_status（若无其他场景引用则还原为 0-未引用）
        await self._sync_file_ref_status(script_id, user_id)

    async def update_scenario_status(self, scenario_id: int, target_status: int, user_id: int) -> None:
        """更新场景状态。

        当前支持的目标状态：
          1（待开始）—— 确认联调通过，status=0/1 时可操作，status=1 时幂等

        Args:
            scenario_id:   场景主键 ID
            target_status: 目标状态值
            user_id:       操作人 ID
        Raises:
            404 场景不存在
            400 状态不合法 / 当前状态不允许此次操作
        """
        obj = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='场景不存在')
        if obj.status == 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='场景正在压测中，不可修改状态')

        if target_status == 1:
            # 确认联调通过：除进行中(2)外所有状态均允许
            await self.scenario_crud.update_crud(scenario_id, {
                'status': 1,
                'error_info': None,
                'updated_by': user_id,
            })
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'暂不支持将状态更新为 {target_status}',
            )


# ====================== 子配置 Service ======================

def _prepare_config_data(raw: dict, user_id: int) -> dict:
    """
    预处理子配置数据：
      - ultimate 类型：自动汇总 ultimate_rows 中各行 start_threads 作为 thread_count
      - 统一注入 created_by（仅新建时调用，更新路径不经此函数）

    Args:
        raw:     来自 Schema.model_dump() 的原始字典
        user_id: 操作人 ID，写入 created_by
    Returns:
        处理后的 dict，可直接传入 create_crud
    """
    data = {k: v for k, v in raw.items() if v is not None or k in ('loop_forever', 'status')}
    data['created_by'] = user_id

    # ultimate 类型：thread_count 由行数据汇总，忽略前端传入值
    if data.get('thread_type') == '3':
        rows = data.get('ultimate_rows') or []
        # UltimateRowReqSchema 对象列表需转为 dict 再存储
        if rows and hasattr(rows[0], 'model_dump'):
            rows = [r.model_dump() for r in rows]
            data['ultimate_rows'] = rows
        data['thread_count'] = sum(r.get('start_threads', 0) for r in rows)

    return data


def _validate_estimated_duration(
    thread_type: str,
    estimated_duration: int | None,
    loop_forever: int | bool,
    ramp_up_time: int | None,
    startup_delay: int | None,
) -> None:
    """校验标准线程组 estimated_duration 须大于已知耗时（ramp-up + 启动延迟）。

    仅对使用循环次数控制（loop_forever=False）的标准线程组生效；
    loop_forever 或未填写 estimated_duration 时跳过校验。
    """
    if thread_type not in ('0', '1') or estimated_duration is None or loop_forever:
        return
    known = (ramp_up_time or 0) + (startup_delay or 0)
    if known > 0 and estimated_duration <= known:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f'预计耗时须大于已知耗时'
                f'（ramp-up {ramp_up_time or 0}s + 启动延迟 {startup_delay or 0}s = {known}s）'
            ),
        )


def _serialize_config(config: PerfScenarioConfigModel) -> dict:
    """按 thread_type 选择对应的响应 Schema 序列化子配置 ORM 对象。"""
    schema_map = {
        '0': PerfScenarioConfigStandardRespSchema,   # SetUp 与 ThreadGroup 字段相同
        '1': PerfScenarioConfigStandardRespSchema,
        '2': PerfScenarioConfigSteppingRespSchema,
        '3': PerfScenarioConfigUltimateRespSchema,
    }
    schema_cls = schema_map.get(config.thread_type, PerfScenarioConfigStandardRespSchema)
    return schema_cls.model_validate(config).model_dump()

# ====================== 压测场景子配置 Service ======================
class PerfScenarioConfigService:
    """
    场景子配置业务逻辑。
    职责：子配置的增删改查；每次变更后更新父场景 updated_by。
    thread_type 在创建时确定，不允许修改；更新时服务端据此决定处理哪类字段。
    """

    def __init__(self, db: AsyncSession):
        self.scenario_crud = BaseCRUD(PerfScenarioModel, db)
        self.config_crud   = PerfScenarioConfigCRUD(db)

    async def create(self, scenario_id: int, data: PerfScenarioConfigCreateReqSchema, user_id: int) -> Dict:
        """新增子配置并回写父场景 concurrent_count。

        Args:
            scenario_id: 父场景主键 ID（URL 路径参数）
            data:        子配置新建请求体（线程数、节点数、循环策略等）
            user_id:     当前操作人 ID，写入 created_by
        Returns:
            Dict: {"id": int} — 新建子配置的主键 ID
        Raises:
            404 场景不存在
        """
        # 校验父场景存在
        scenario = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not scenario or not scenario.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='场景不存在')

        raw = data.model_dump()
        _validate_estimated_duration(
            thread_type=raw.get('thread_type', '1'),
            estimated_duration=raw.get('estimated_duration'),
            loop_forever=raw.get('loop_forever', 0),
            ramp_up_time=raw.get('ramp_up_time'),
            startup_delay=raw.get('startup_delay'),
        )
        cfg_data = _prepare_config_data(raw, user_id)
        cfg_data['scenario_id'] = scenario_id
        obj = await self.config_crud.create_crud(cfg_data)

        # 回写父场景操作人
        await self.scenario_crud.update_crud(scenario_id, {'updated_by': user_id})

        return {'id': obj.id}

    async def get_list(self, scenario_id: int) -> List[Dict]:
        """查询场景下全部子配置（含启用与禁用），供前端展开行懒加载。

        Args:
            scenario_id: 场景主键 ID（URL 路径参数）
        Returns:
            list[Dict]: PerfScenarioConfigRespSchema 序列化后的子配置列表；无数据时返回空列表
        Raises:
            404 场景不存在
        """
        scenario = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not scenario or not scenario.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='场景不存在')
        configs = await self.config_crud.get_configs(scenario_id)
        return [_serialize_config(c) for c in configs]

    async def update(self, scenario_id: int, config_id: int, data: PerfScenarioConfigUpdateReqSchema, user_id: int) -> None:
        """修改单条子配置并回写父场景 concurrent_count。

        thread_type 不可修改；服务端读取 DB 中的 thread_type，
        确保只处理对应类型的字段，防止跨类型字段污染。

        Args:
            scenario_id: 父场景主键 ID（用于归属校验，防跨场景越权）
            config_id:   待修改的子配置主键 ID
            data:        子配置修改请求体，仅传入需变更的字段（exclude_unset）
            user_id:     当前操作人 ID，写入 updated_by
        Returns:
            None
        Raises:
            404 子配置不存在
            400 子配置不属于该场景（scenario_id 与记录不符）
        """
        obj = await self.config_crud.get_by_id_crud(config_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='子配置不存在')
        # 归属校验：防止用 A 场景的 scenario_id 修改 B 场景的配置
        if obj.scenario_id != scenario_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='子配置不属于该场景')

        update_data = data.model_dump(exclude={'thread_type'}, exclude_unset=True)
        if obj.thread_type in ('0', '1') and update_data.get('estimated_duration') is not None:
            _validate_estimated_duration(
                thread_type=obj.thread_type,
                estimated_duration=update_data['estimated_duration'],
                loop_forever=update_data.get('loop_forever', obj.loop_forever),
                ramp_up_time=update_data.get('ramp_up_time', obj.ramp_up_time),
                startup_delay=update_data.get('startup_delay', obj.startup_delay),
            )
        if obj.thread_type == '3' and 'ultimate_rows' in update_data:
            rows = update_data.get('ultimate_rows') or []
            if rows and hasattr(rows[0], 'model_dump'):
                rows = [r.model_dump() for r in rows]
                update_data['ultimate_rows'] = rows
            update_data['thread_count'] = sum(r.get('start_threads', 0) for r in rows)

        await self.config_crud.update_crud(config_id, {**update_data, 'updated_by': user_id})

        # 回写父场景操作人
        await self.scenario_crud.update_crud(obj.scenario_id, {'updated_by': user_id})

    async def delete(self, scenario_id: int, config_id: int, user_id: int) -> None:
        """软删除单条子配置并回写父场景 concurrent_count。

        Args:
            scenario_id: 父场景主键 ID（用于归属校验）
            config_id:   待删除的子配置主键 ID
            user_id:     当前操作人 ID，写入父场景 updated_by
        Returns:
            None
        Raises:
            404 子配置不存在
            400 子配置不属于该场景
        """
        obj = await self.config_crud.get_by_id_crud(config_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='子配置不存在')
        if obj.scenario_id != scenario_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='子配置不属于该场景')

        # 提前记录 scenario_id，软删除后 obj 状态不可依赖
        sid = obj.scenario_id
        await self.config_crud.soft_delete_crud([config_id])
        await self.scenario_crud.update_crud(sid, {'updated_by': user_id})

    async def sync_stats(self, data: ConfigSyncStatsReqSchema, user_id: int) -> dict:
        """切换子配置启用状态，一次性完成并发数 + 预计耗时同步。

        步骤：
          1. 校验子配置归属
          2. 更新目标配置状态
          3. 重新读取全量子配置，计算并发数与耗时
          4. 耗时 = 各启用子配置 estimated_duration 之和（存在未填则标记 has_unknown）
          5. 写回场景 estimated_duration（部分耗时也写入，供进度条参考）
          6. 返回 { configs(仅启用), concurrent_count, known_times, has_unknown_times }

        互斥规则说明：
          '0'(SetUp/TearDown) 前端禁用开关，不经此接口切换；
          '1'/'2'/'3' 均可多个同时启用（顺序执行+启动延迟场景），后端不再做互斥处理。
        """
        scenario_id = data.scenario_id
        config_id   = data.config_id

        # 1. 校验
        obj = await self.config_crud.get_by_id_crud(config_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='子配置不存在')
        if obj.scenario_id != scenario_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='子配置不属于该场景')

        # 2. 更新目标配置状态
        await self.config_crud.update_crud(config_id, {'status': data.status, 'updated_by': user_id})

        # 3. 读取更新后的全量子配置
        all_configs    = await self.config_crud.get_configs(scenario_id)
        active_configs = [c for c in all_configs if c.status == 1]

        # 4. 并发数（SQL 聚合）
        cc_map           = await self.config_crud.get_concurrent_count_map([scenario_id])
        concurrent_count = cc_map.get(scenario_id, 0)

        # 5. 耗时计算：逐条累加各子配置已知耗时；loop_count 场景部分已知，标记 has_unknown
        known_secs = 0
        has_unknown = False
        for c in active_configs:
            secs, unknown = _calc_config_duration(c)
            known_secs += secs
            if unknown:
                has_unknown = True
        known_secs_result: int | None = known_secs if known_secs > 0 else None

        # 6. 写回场景 estimated_duration（有部分耗时也写入，用于进度条参考）
        update_payload: dict = {'updated_by': user_id}
        if known_secs_result is not None:
            update_payload['estimated_duration'] = known_secs_result
        await self.scenario_crud.update_crud(scenario_id, update_payload)

        return {
            'configs':           [_serialize_config(c) for c in active_configs],
            'concurrent_count':  concurrent_count,
            'known_times':       known_secs_result,
            'has_unknown_times': has_unknown,
        }


# ── 联调核查项辅助函数（模块级，供 inspect_sse 调用）────────────────────

def _build_api_interfaces(http_samplers: list) -> dict:
    """整理 HTTP 请求清单，按线程组分组，过滤禁用采样器，统计总接口数。"""
    groups = []
    for g in http_samplers:
        enabled_samplers = [s for s in g.get("samplers", []) if s.get("enabled", True)]
        if enabled_samplers:
            groups.append({**g, "samplers": enabled_samplers})
    total = sum(len(g["samplers"]) for g in groups)
    return {"total": total, "groups": groups}


def _build_used_vars(http_samplers: list, vars_map: dict, var_descs: dict = None) -> dict:
    """收集 HTTP 请求中实际引用的用户变量（仅取 vars_map 中已定义的），含备注描述。"""
    var_descs = var_descs or {}
    used_names: set = set()
    for group in http_samplers:
        for sampler in group.get("samplers", []):
            used_names.update(sampler.get("referenced_vars", []))
    items = [
        {"name": k, "value": vars_map.get(k, ""), "desc": var_descs.get(k, "")}
        for k in sorted(used_names)
    ]
    return {"total": len(items), "vars": items}


def _build_debug_components(result_collectors: list) -> dict:
    """
    整理调试组件（is_debug=True）的关闭状态，按（类型+名称）去重聚合，供联调页面展示。

    同名同类型组件（跨线程组可重复存在）合并为一行，显示已关闭数/总数。
    Returns:
        {
          total:        调试组件总数（实例数，含重复）,
          closed_count: 已关闭实例数,
          open_count:   仍开启实例数,
          items:        [{type_label, testname, total, closed_count, open_count}]  按(类型+名称)聚合
        }
    """
    debug_items = [c for c in result_collectors if c.get("is_debug")]

    # 按 (type_label, testname) 聚合，保持首次出现顺序
    _groups: dict[tuple, dict] = {}
    for c in debug_items:
        label    = JMETER_DEBUG_GUI_LABEL.get(c.get("gui_class", ""), c.get("gui_class", "未知"))
        testname = c.get("testname", "")
        key      = (label, testname)
        if key not in _groups:
            _groups[key] = {"type_label": label, "testname": testname,
                            "total": 0, "closed_count": 0, "open_count": 0}
        _groups[key]["total"] += 1
        if c["enabled"]:
            _groups[key]["open_count"] += 1
        else:
            _groups[key]["closed_count"] += 1

    items        = list(_groups.values())
    total        = len(debug_items)
    open_count   = sum(1 for c in debug_items if c["enabled"])
    closed_count = total - open_count
    return {
        "total":        total,
        "closed_count": closed_count,
        "open_count":   open_count,
        "items":        items,
    }


def _build_thread_config_from_db(active_configs: list, workers: int) -> dict:
    """基于已加载的 DB 启用子配置构建线程配置面板数据，与子列表保持严格一致。

    替代基于 JMX 解析的 _build_thread_config，不重复查库，
    直接使用 inspect_sse 已加载的 configs 列表（过滤 status=1）。

    Args:
        active_configs: status=1（启用）的子配置 ORM 列表
        workers:        压力机节点数（分布式=node_count，单机=1）
    Returns:
        {"workers": int, "rows": list}，结构与 _build_thread_config 相同
    """
    import json as _json

    _TYPE_LABEL = {
        '0': 'SetUp',
        '1': 'Standard',
        '2': 'Stepping',
        '3': 'Ultimate',
    }
    _TG_TYPE_MAP = {
        '0': 'standard',
        '1': 'standard',
        '2': 'stepping',
        '3': 'ultimate',
    }

    rows = []
    for cfg in active_configs:
        tt      = cfg.thread_type or '1'
        tg_type = _TG_TYPE_MAP.get(tt, 'standard')
        threads = cfg.thread_count or 0

        row: dict = {
            'name':             cfg.tg_name or '',
            'tg_type':          tg_type,
            'type_label':       _TYPE_LABEL.get(tt, tt),
            'threads':          threads,
            'workers':          workers,
            'total_concurrent': threads * workers,
        }

        if tg_type == 'standard':
            forever = bool(cfg.loop_forever)
            row.update({
                'ramp_time':    cfg.ramp_up_time,
                'loop_count':   None if forever else cfg.loop_count,
                'duration':     cfg.duration if forever else None,
                'start_delay':  cfg.startup_delay or 0,
                'loop_forever': forever,
            })
        elif tg_type == 'stepping':
            start_count  = cfg.step_start_users_count  or 0
            start_period = cfg.step_start_users_period or 0
            ramp_up      = cfg.step_ramp_up             or 0
            stop_count   = cfg.step_stop_users_count   or 0
            stop_period  = cfg.step_stop_users_period  or 0
            row.update({
                'start_delay':     cfg.step_initial_delay or 0,
                'initial_threads': cfg.step_start_users_burst or 0,
                'step_up':         f"{start_count}个/{start_period}s(爬坡{ramp_up}s)",
                'flight_time':     cfg.step_flight_time or 0,
                'step_down':       f"{stop_count}个/{stop_period}s" if stop_count else "—",
            })
        elif tg_type == 'ultimate':
            raw_rows = cfg.ultimate_rows or []
            if isinstance(raw_rows, str):
                try:
                    raw_rows = _json.loads(raw_rows)
                except Exception:
                    raw_rows = []
            if not isinstance(raw_rows, list):
                raw_rows = []
            row['ultimate_rows'] = [
                {
                    'phase':         i + 1,
                    'start_threads': r.get('start_threads', 0),
                    'initial_delay': r.get('initial_delay', 0),
                    'startup_time':  r.get('startup_time', 0),
                    'hold_load_for': r.get('hold_load_for', 0),
                    'shutdown_time': r.get('shutdown_time', 0),
                }
                for i, r in enumerate(raw_rows)
            ]

        rows.append(row)

    return {'workers': workers, 'rows': rows}


def _build_thread_config(summary: dict, workers: int) -> dict:
    """组装线程配置表格，仅含启用的线程组，按类型携带不同字段供前端分类展示。"""
    _TAG_DISPLAY = {
        "ThreadGroup":          "ThreadGroup",
        "SetupThreadGroup":     "SetUp",
        "TearDownThreadGroup":  "TearDown",
        "kg.apc.jmeter.threads.SteppingThreadGroup": "Stepping",
        "kg.apc.jmeter.threads.UltimateThreadGroup": "Ultimate",
    }
    rows = []
    for tg in summary.get("thread_groups", []):
        if not tg.get("enabled", True):
            continue
        tg_type = tg.get("tg_type", "standard")
        threads = tg.get("num_threads") or 0
        tag     = tg.get("tag", "")

        row: dict = {
            "name":             tg.get("testname", ""),
            "tg_type":          tg_type,
            "type_label":       _TAG_DISPLAY.get(tag, tg_type),
            "threads":          threads,
            "workers":          workers,
            "total_concurrent": threads * workers,
        }

        if tg_type == "stepping":
            # Stepping 独有：阶梯加压参数，格式化为前端可直接展示的字符串
            s            = tg.get("stepping") or {}
            start_count  = s.get("start_users_count", 0)
            start_period = s.get("start_users_period", 0)
            ramp_up      = s.get("ramp_up", 0)
            stop_count   = s.get("stop_users_count", 0)
            stop_period  = s.get("stop_users_period", 0)
            row.update({
                "start_delay":     s.get("initial_delay", 0),
                "initial_threads": s.get("start_users_burst", 0),
                "step_up":         f"{start_count}线程/{start_period}s(爬坡{ramp_up}s)",
                "flight_time":     s.get("flight_time", 0),
                "step_down":       f"{stop_count}线程/{stop_period}s" if stop_count else "—",
            })
        elif tg_type == "ultimate":
            # Ultimate 独有：各阶段行数据
            ultimate_rows = tg.get("ultimate_rows") or []
            row["ultimate_rows"] = [
                {
                    "phase":         i + 1,
                    "start_threads": r.get("start_threads", 0),
                    "initial_delay": r.get("initial_delay", 0),
                    "startup_time":  r.get("startup_time", 0),
                    "hold_load_for": r.get("hold_load_for", 0),
                    "shutdown_time": r.get("shutdown_time", 0),
                }
                for i, r in enumerate(ultimate_rows)
            ]
        else:
            # Standard：循环/调度参数
            forever = tg.get("loop_forever", False)
            row.update({
                "ramp_time":   tg.get("ramp_time"),
                "loop_count":  None if forever else tg.get("loop_count"),
                "duration":    tg.get("duration") if forever else None,
                "start_delay": tg.get("delay") or 0,
                "loop_forever": forever,
            })

        rows.append(row)

    return {"workers": workers, "rows": rows}


# ── SSH 连通性探测辅助函数（模块级同步，供 asyncio.to_thread 调用）──────────────

def _probe_http(ssh, url: str, timeout: int = 10) -> tuple[bool, str]:
    """在远端机器上用 curl/wget HEAD 请求探测 URL 可达性，返回 (ok, reason)。
    任意 HTTP 响应（含 4xx/5xx）均视为连通；网络不通时返回具体失败原因。
    """
    # 输出格式：ok / R:curl:<exit_code> / R:wget:<exit_code> / R:none:0
    cmd = (
        f"if command -v curl >/dev/null 2>&1; then "
        f"  curl -s --head --max-time {timeout} '{url}' >/dev/null 2>&1; echo \"R:curl:$?\"; "
        f"elif command -v wget >/dev/null 2>&1; then "
        f"  wget -q --spider --timeout={timeout} '{url}' >/dev/null 2>&1; echo \"R:wget:$?\"; "
        f"else echo 'R:none:0'; fi"
    )
    _, out, _ = ShellOperationUtils.execute_remote_command(ssh, cmd)

    # 取最后一个非空行，过滤 SSH banner / MOTD 等杂项输出
    lines = [l for l in (out or '').splitlines() if l.strip()]
    last  = lines[-1].strip() if lines else ''

    parts = last.split(':')
    if len(parts) != 3 or parts[0] != 'R':
        hint = f'（原始输出：{last[:60]}）' if last else ''
        return False, f'探测命令无响应{hint}'

    tool, code_str = parts[1], parts[2]
    code = int(code_str) if code_str.isdigit() else -1

    if tool == 'none':
        return False, '远端无 curl/wget 工具'
    if code == 0:
        return True, ''

    # curl exit code → 中文原因（wget 错误码体系不同，统一映射为通用描述）
    _CURL_MAP = {
        5:  'SOCKS5代理错误',
        6:  'DNS解析失败（域名无法解析）',
        7:  '端口不通（连接被拒绝/防火墙拦截）',
        22: 'HTTP响应错误状态码（4xx/5xx）',
        28: f'连接超时（>{timeout}s）',
        35: 'SSL/TLS握手失败',
        51: 'SSL证书主机名不匹配',
        60: 'SSL证书验证失败（CA不受信任）',
    }
    if tool == 'curl':
        return False, _CURL_MAP.get(code, f'curl连接失败（exit={code}）')
    else:
        return False, f'wget连接失败（exit={code}）'


def _probe_tcp(ssh, host: str, port: int, timeout: int = 5) -> bool:
    """在远端机器上用 python3 socket 探测任意 TCP 端口（无 nc 依赖，python3 是标准依赖）。"""
    cmd = (
        f"python3 -c \""
        f"import socket; s=socket.socket(); s.settimeout({timeout}); "
        f"r=s.connect_ex(('{host}', {port})); s.close(); "
        f"print('ok' if r==0 else 'fail')\" 2>/dev/null"
    )
    _, out, _ = ShellOperationUtils.execute_remote_command(ssh, cmd)
    return out.strip() == 'ok'


def _check_master_to_minio(master, minio_url: str, is_dist: bool) -> dict:
    """SSH 到 Master，探测 Master → MinIO 的 TCP 连通性。
    单机模式无 Master 控制机，此项直接忽略（ok=None）。
    MinIO 为本地部署（localhost/127.0.0.1）时，Master 网络不可达，直接返回 ok=False。
    :param minio_url: Minio访问完整URL地址
    :param is_dist: 是否分布式，True-是，False-否。
    """
    if not is_dist:
        return {"ok": None, "detail": "单机模式不适用", "sub": []}
    for host in ('localhost', '127.0.0.1', '::1'):
        if host in minio_url:
            return {
                "ok": False,
                "detail": f"Master({master.ip}): MinIO 为控制机本地部署（{host}），网络不可达",
                "sub": [],
            }

    ssh = None
    try:
        ssh = ShellOperationUtils.get_ssh_client(
            master.ip, target_port=master.ssh_port or 22, max_retries=1, retry_interval=1.0,
            credential=_build_credential(master)
        )
        ok, reason = _probe_http(ssh, minio_url+"minio/health/live")
        detail = f"连通（{minio_url}）" if ok else f"不可达（{minio_url}）：{reason}"
        return {"ok": ok, "detail": f"Master({master.ip}): {detail}", "sub": []}
    except Exception as e:
        return {"ok": False, "detail": f"Master({master.ip}): SSH连接失败 — {e}", "sub": []}
    finally:
        if ssh:
            try: ssh.close()
            except Exception: pass


def _check_workers_to_minio(master, workers: list, minio_url: str, is_dist: bool,
                            ssh_pool: dict = None) -> dict:
    """探测各 Worker/单机 → MinIO 的连通性。
    分布式模式经 Master Relay；单机模式直连（无需 Master 跳板）。
    先验证 SSH 可达性，SSH 通后再探测 MinIO，失败原因精确区分。

    :param master:    Master 控制机对象（分布式模式用于 Relay 跳板）
    :param workers:   Worker 或单机压力机列表
    :param minio_url: MinIO 访问完整 URL
    :param is_dist:   是否分布式模式
    :param ssh_pool:  可复用的 SSH 连接池 {ip: SSHClient}；单机模式下若有对应连接则借用（不关闭）
    :return:          {"ok": bool|None, "detail": str, "sub": list}
    """
    if not workers:
        role = "Slave Worker" if is_dist else "单机压力机"
        return {"ok": None, "detail": f"未配置 {role}", "sub": []}

    sub = []

    def _do_check(ssh_conn, ip: str):
        """在已建立的 SSH 连接上先验证 SSH 通断，再探测 MinIO。"""
        # ① SSH 连通性验证
        exit_code, out, err = ShellOperationUtils.execute_remote_command(ssh_conn, "echo ok")
        if out.strip() != "ok":
            reason = err.strip() or f"SSH认证失败（exit={exit_code}，密钥和密码均不通）"
            return {"ip": ip, "ok": False, "msg": f"SSH连接失败：{reason}"}
        # ② MinIO 连通性探测
        ok, reason = _probe_http(ssh_conn, minio_url + "minio/health/live")
        if ok:
            return {"ip": ip, "ok": True,  "msg": f"连通（{minio_url}）"}
        return {"ip": ip, "ok": False, "msg": f"不可达（{minio_url}）：{reason}"}

    if not is_dist:
        # 单机模式：直连单机压力机；优先复用 ssh_pool 中已有连接
        for w in workers:
            pooled = ssh_pool.get(w.ip) if ssh_pool else None
            if pooled:
                # 借用连接池中的连接，不负责关闭
                sub.append(_do_check(pooled, w.ip))
            else:
                ssh = None
                try:
                    ssh = ShellOperationUtils.get_ssh_client(
                        w.ip, target_port=w.ssh_port or 22, max_retries=1, retry_interval=1.0,
                        credential=_build_credential(w)
                    )
                    sub.append(_do_check(ssh, w.ip))
                except Exception as e:
                    sub.append({"ip": w.ip, "ok": False, "msg": f"SSH连接失败：{e}"})
                finally:
                    if ssh:
                        try: ssh.close()
                        except Exception: pass
    else:
        # 分布式模式：通过 _RelayClient 中继到各 Worker 执行 curl 探测
        # _RelayClient 内部已处理 base64 编码和密钥/密码回退；
        # execute_remote_command 已修正为先读 stdout 再取退出码，relay 可正常返回 Worker 输出
        master_ssh = None
        try:
            master_ssh = ShellOperationUtils.get_ssh_client(
                master.ip, target_port=master.ssh_port or 22, max_retries=1, retry_interval=1.0,
                credential=_build_credential(master)
            )
            for w in workers:
                try:
                    relay = ShellOperationUtils.get_ssh_client(
                        w.ip, jump_host=master.ip, jump_port=master.ssh_port or 22,
                        target_port=w.ssh_port or 22, max_retries=1,
                        reuse_master_ssh=master_ssh, credential=_build_credential(w)
                    )
                    ok, reason = _probe_http(relay, minio_url + "minio/health/live")
                    if ok:
                        sub.append({"ip": w.ip, "ok": True,  "msg": f"连通（{minio_url}）"})
                    else:
                        sub.append({"ip": w.ip, "ok": False, "msg": f"不可达（{minio_url}）：{reason}"})
                except Exception as e:
                    sub.append({"ip": w.ip, "ok": False, "msg": f"SSH连接失败：{e}"})
        except Exception as e:
            return {"ok": False, "detail": f"SSH到Master失败 — {e}", "sub": []}
        finally:
            if master_ssh:
                try: master_ssh.close()
                except Exception: pass

    all_ok = all(s["ok"] for s in sub)
    fail_ips = [s["ip"] for s in sub if not s["ok"]]
    detail = (f"全部 {len(sub)} 台可达 MinIO" if all_ok
              else f"{len(fail_ips)}/{len(sub)} 台不可达：{'、'.join(fail_ips)}")
    return {"ok": all_ok, "detail": detail, "sub": sub}


def _exec_on_worker_via_master(
    master_ssh, worker_ip: str, worker_port: int, worker_cmd: str, ssh_user: str, ssh_pwd: str | None,
) -> tuple[str, str]:
    """从 master_ssh 向 Worker 发起嵌套 SSH 执行命令，先密钥认证，输出为空时回退密码认证。

    worker_cmd 会被单引号包裹传给 SSH；含特殊字符时由调用方先 base64 编码再传入。
    返回 (last_line, auth_method)：
      last_line   — 输出的最后非空行（取最后一行可过滤 SSH banner/MOTD 杂项）
      auth_method — 'key'（密钥成功）| 'password'（密码成功）| ''（均无有效输出）
    """
    # ① 密钥认证（BatchMode=yes，密钥不通立即返回非零，不阻塞等待输入）
    from app.common.commands import SSH_RELAY_KEY
    key_cmd = SSH_RELAY_KEY.format(worker_port=worker_port, ssh_user=ssh_user, worker_ip=worker_ip, worker_cmd=worker_cmd)
    _, k_out, _ = ShellOperationUtils.execute_remote_command(master_ssh, key_cmd)
    k_lines = [l for l in (k_out or '').splitlines() if l.strip()]
    if k_lines:
        return k_lines[-1].strip(), 'key'

    # ② 密码认证（sshpass，密码 base64 编码防特殊字符注入）
    if ssh_pwd:
        pwd_b64 = base64.b64encode(ssh_pwd.encode()).decode('ascii')
        from app.common.commands import SSH_RELAY_SSHPASS
        pwd_cmd = SSH_RELAY_SSHPASS.format(
            pwd_b64=pwd_b64, worker_port=worker_port,
            ssh_user=ssh_user, worker_ip=worker_ip, worker_cmd=worker_cmd,
        )
        _, p_out, _ = ShellOperationUtils.execute_remote_command(master_ssh, pwd_cmd)
        p_lines = [l for l in (p_out or '').splitlines() if l.strip()]
        if p_lines:
            return p_lines[-1].strip(), 'password'

    return '', ''


def _check_master_to_workers(master, workers: list, is_dist: bool) -> dict:
    """SSH 到 Master，依次用密钥/密码探测 Master → 各 Worker 的 SSH 连通性。
    先尝试密钥认证（BatchMode=yes），失败后若配置了密码则用 sshpass 兜底。
    返回结果标注实际认证方式（密钥认证 / 密码认证 / 不可达）。
    """
    if not is_dist:
        return {"ok": None, "detail": "单机模式不适用", "sub": []}
    if not workers:
        return {"ok": None, "detail": "未配置 Slave Worker 压力机", "sub": []}

    from config import config as _cfg
    ssh_user = _cfg.SSH_DEFAULT_USER
    ssh_pwd  = _cfg.SSH_DEFAULT_PASSWORD

    master_ssh = None
    sub = []
    try:
        master_ssh = ShellOperationUtils.get_ssh_client(
            master.ip, target_port=master.ssh_port or 22, max_retries=1, retry_interval=1.0,
            credential=_build_credential(master)
        )
        for w in workers:
            port = w.ssh_port or 22
            try:
                last, auth = _exec_on_worker_via_master(
                    master_ssh, w.ip, port, 'echo ok', ssh_user, ssh_pwd
                )
                if last == 'ok':
                    method = '密钥认证' if auth == 'key' else '密码认证'
                    sub.append({"ip": w.ip, "ok": True, "msg": f"SSH 连通（{method}）"})
                elif not ssh_pwd:
                    sub.append({"ip": w.ip, "ok": False, "msg": "SSH 不可达：密钥认证失败（未配置备用密码）"})
                else:
                    sub.append({"ip": w.ip, "ok": False, "msg": "SSH 不可达：密钥和密码均认证失败"})
            except Exception as e:
                sub.append({"ip": w.ip, "ok": False, "msg": f"连接异常：{e}"})
    except Exception as e:
        return {"ok": False, "detail": f"SSH到Master失败 — {e}", "sub": []}
    finally:
        if master_ssh:
            try: master_ssh.close()
            except Exception: pass

    all_ok = all(s["ok"] for s in sub)
    fail_ips = [s["ip"] for s in sub if not s["ok"]]
    detail = (f"全部 {len(sub)} 台 Worker SSH 可达" if all_ok
              else f"{len(fail_ips)}/{len(sub)} 台不可达：{'、'.join(fail_ips)}")
    return {"ok": all_ok, "detail": detail, "sub": sub}


def _check_jmeter_running(master, workers: list, is_dist: bool,
                          ssh_pool: dict = None) -> dict:
    """SSH 到目标压力机，检测 JMeter 进程是否在运行。
    单机模式直连单机机器；分布式模式 SSH 到 Master 再 Relay 到各 Worker。

    :param master:   Master 控制机对象（分布式模式用于 SSH 跳板）
    :param workers:  Worker 或单机压力机列表
    :param is_dist:  是否分布式模式
    :param ssh_pool: 可复用的 SSH 连接池 {ip: SSHClient}；单机模式下若有对应连接则借用（不关闭）
    :return:         {"ok": bool|None, "detail": str, "sub": list}
    """
    # 精确匹配 ApacheJMeter.jar 进程，避免 jmeter 壳脚本/日志路径被误计入
    JMX_CHK = "pgrep -f ApacheJMeter 2>/dev/null | wc -l || ps aux 2>/dev/null | grep -v grep | grep -c ApacheJMeter || echo 0"
    sub = []

    if not is_dist:
        # 单机模式：直连单机压力机；优先复用 ssh_pool 中已有连接
        if not workers:
            return {"ok": None, "detail": "未配置单机压力机", "sub": []}
        for w in workers:
            pooled = ssh_pool.get(w.ip) if ssh_pool else None
            if pooled:
                try:
                    _, out, _ = ShellOperationUtils.execute_remote_command(pooled, JMX_CHK)
                    count = int(out.strip()) if out.strip().isdigit() else 0
                    sub.append({"role": "单机", "ip": w.ip, "ok": count > 0,
                                 "msg": f"运行中（{count} 个进程）" if count > 0 else "未检测到 JMeter 进程"})
                except Exception as e:
                    sub.append({"role": "单机", "ip": w.ip, "ok": False, "msg": f"SSH失败: {e}"})
            else:
                ssh = None
                try:
                    ssh = ShellOperationUtils.get_ssh_client(
                        w.ip, target_port=w.ssh_port or 22, max_retries=1, retry_interval=1.0,
                        credential=_build_credential(w)
                    )
                    _, out, _ = ShellOperationUtils.execute_remote_command(ssh, JMX_CHK)
                    count = int(out.strip()) if out.strip().isdigit() else 0
                    sub.append({"role": "单机", "ip": w.ip, "ok": count > 0,
                                 "msg": f"运行中（{count} 个进程）" if count > 0 else "未检测到 JMeter 进程"})
                except Exception as e:
                    sub.append({"role": "单机", "ip": w.ip, "ok": False, "msg": f"SSH失败: {e}"})
                finally:
                    if ssh:
                        try: ssh.close()
                        except Exception: pass
        all_ok = all(s["ok"] for s in sub)
        not_running = [f"单机({s['ip']})" for s in sub if not s["ok"]]
        detail = (f"全部 {len(sub)} 台 JMeter 进程正常" if all_ok
                  else f"{'、'.join(not_running)} 未检测到 JMeter 进程")
        return {"ok": all_ok, "detail": detail, "sub": sub}

    # 分布式模式：SSH 到 Master，再 Relay 到各 Worker
    master_ssh = None
    try:
        master_ssh = ShellOperationUtils.get_ssh_client(
            master.ip, target_port=master.ssh_port or 22, max_retries=1, retry_interval=1.0,
            credential=_build_credential(master)
        )
        _, m_out, _ = ShellOperationUtils.execute_remote_command(master_ssh, JMX_CHK)
        m_count = int(m_out.strip()) if m_out.strip().isdigit() else 0
        sub.append({"role": "Master", "ip": master.ip, "ok": m_count > 0,
                     "msg": f"运行中（{m_count} 个进程）" if m_count > 0 else "未检测到 JMeter 进程"})

        if workers:
            for w in workers:
                try:
                    relay = ShellOperationUtils.get_ssh_client(
                        w.ip, jump_host=master.ip, jump_port=master.ssh_port or 22,
                        target_port=w.ssh_port or 22, max_retries=1,
                        reuse_master_ssh=master_ssh, credential=_build_credential(w)
                    )
                    exit_code, w_out, w_err = ShellOperationUtils.execute_remote_command(relay, JMX_CHK)
                    w_out = w_out.strip()
                    if w_out.isdigit():
                        w_count = int(w_out)
                        sub.append({"role": "Worker", "ip": w.ip, "ok": w_count > 0,
                                     "msg": f"运行中（{w_count} 个进程）" if w_count > 0 else "未检测到 JMeter 进程"})
                    else:
                        reason = w_err.strip() or f"无响应（exit={exit_code}，密钥和密码均不通）"
                        sub.append({"role": "Worker", "ip": w.ip, "ok": False,
                                     "msg": f"SSH连接失败：{reason}"})
                except Exception as e:
                    sub.append({"role": "Worker", "ip": w.ip, "ok": False, "msg": f"SSH失败: {e}"})
    except Exception as e:
        return {"ok": False,
                "detail": f"SSH到Master失败 — {e}",
                "sub": [{"role": "Master", "ip": master.ip, "ok": False, "msg": str(e)}]}
    finally:
        if master_ssh:
            try: master_ssh.close()
            except Exception: pass
    all_ok = all(s["ok"] for s in sub)
    not_running = [f"{s['role']}({s['ip']})" for s in sub if not s["ok"]]
    detail = (f"全部 {len(sub)} 台 JMeter 进程正常" if all_ok
              else f"{'、'.join(not_running)} 未检测到 JMeter 进程")
    return {"ok": all_ok, "detail": detail, "sub": sub}


def _check_influxdb_via_ssh(machine, url: str) -> tuple:
    """SSH 到目标压力机（单机或 Master），用 curl/wget 探测 InfluxDB URL 可达性。
    分布式模式传入 Master；单机模式传入单机压力机。返回 (ok: bool, message: str)。
    """
    if not url:
        return False, "URL 为空"
    ssh = None
    try:
        ssh = ShellOperationUtils.get_ssh_client(
            machine.ip, target_port=machine.ssh_port or 22, max_retries=1, retry_interval=1.0,
            credential=_build_credential(machine)
        )
        ok, reason = _probe_http(ssh, url)
        if ok:
            return True, "连通"
        return False, f"不可达：{reason}"
    except Exception as e:
        return False, f"SSH连接失败 — {e}"
    finally:
        if ssh:
            try: ssh.close()
            except Exception: pass

# ====================== 联调 / 执行 Service ======================
class ScenarioExecuteService:
    """联调与执行业务逻辑。

    职责：
      inspect_sse : SSE 流式解析 JMX 摘要 + 预览联调参数（只读，不推送）
      execute     : 按 action 执行联调（预置参数→Master）或正式压测（子配置正式参数→Master）

    联调参数 param_key 选取规则（thread_type 优先，standard 类型再按 test_type 区分）：
      stepping              → STEPPING_THREAD_GROUP_INSPECT
      ultimate              → ULTIMATE_THREAD_GROUP_INSPECT
      standard + 负载测试   → LOAD_THREAD_GROUP_INSPECT   （test_type='2'）
      standard + 其他测试   → BASE_THREAD_GROUP_INSPECT
    """

    # 负载测试对应的 dict_value（来自 perf_test_category 字典）
    _LOAD_TEST_TYPE_VALUE = '2'

    # param_key 常量
    _KEY_BASE     = 'BASE_THREAD_GROUP_INSPECT'
    _KEY_LOAD     = 'LOAD_THREAD_GROUP_INSPECT'
    _KEY_STEPPING = 'STEPPING_THREAD_GROUP_INSPECT'
    _KEY_ULTIMATE = 'ULTIMATE_THREAD_GROUP_INSPECT'

    # DB thread_type 字典值 → oper_jmx 内部类型标识（JMX 概念层不依赖字典表）
    # '0'（SetUp）与 '1'（ThreadGroup）均为标准线程组，共用 'standard' 注入逻辑
    _DB_TO_JMX_TYPE = {'0': 'standard', '1': 'standard', '2': 'stepping', '3': 'ultimate'}

    def __init__(self, db: AsyncSession):
        self.db            = db
        self.scenario_crud = BaseCRUD(PerfScenarioModel, db)
        self.config_crud   = PerfScenarioConfigCRUD(db)
        self.file_crud     = BaseCRUD(PerfFileModel, db)
        self.param_crud    = PerfParamCRUD(db)
        self.machine_crud  = PerfMachineCRUD(db)

    # ──────────────────── 公共接口 ────────────────────

    async def inspect_sse(self, scenario_id: int) -> AsyncGenerator[str, None]:
        """
        SSE 流式联调核查：依次推送 5 个核查项，不执行任何写操作。

        事件序列：
          start → item(api_interfaces) → item(used_vars) → item(thread_config)
                → item(data_files)     → item(backend_listeners) → done
          error → 任意阶段异常时立即终止
        """
        yield format_sse_event({'type': 'start', 'message': '开始解析场景信息...'})

        # ── 1. 读取场景 ──
        scenario = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not scenario or not scenario.enabled_flag:
            yield format_sse_event({'type': 'error', 'message': '场景不存在'})
            return

        # ── 2. 读取 JMX 文件记录 ──
        file_obj = await self.file_crud.get_by_id_crud(scenario.script_id)
        if not file_obj or not file_obj.enabled_flag:
            yield format_sse_event({'type': 'error', 'message': 'JMX 脚本文件不存在，请重新关联'})
            return

        # ── 3. 从 MinIO 下载 JMX ──
        try:
            from config import config as app_config
            jmx_bytes = await MinioClient.get_object_bytes(app_config.MINIO_BUCKET, file_obj.object_key)
        except Exception as e:
            logger.error(f'下载 JMX 脚本失败 scenario_id={scenario_id}：{fmt_cloudflare_html_resp(e, "请检查 MinIO 地址或网络配置")}')
            yield format_sse_event({'type': 'error', 'message': f'下载 JMX 脚本失败：{fmt_cloudflare_html_resp(e, "请检查 MinIO 地址或网络配置")}'})
            return

        # ── 4. 解析 JMX 摘要 ──
        try:
            summary = parse_jmx_summary(jmx_bytes)
        except Exception as e:
            logger.exception(f'JMX 解析失败 scenario_id={scenario_id}')
            yield format_sse_event({'type': 'error', 'message': f'JMX 解析失败：{e}'})
            return

        # 从场景主表取压力机数量（is_distributed/node_count 已迁移至主表）
        configs = await self.config_crud.get_configs(scenario_id)
        active_configs = [c for c in configs if c.status == 1]
        worker_count = (scenario.node_count or 1) if scenario.is_distributed == 1 else 1

        # 只取启用线程组下的 HTTP 采样器（过滤 thread_group_enabled=False 的条目）
        http_samplers = [s for s in summary.get("http_samplers", []) if s.get("thread_group_enabled", True)]
        vars_map      = summary.get("user_vars", {})
        var_descs     = summary.get("user_var_descs", {})

        # ── ① 压测接口 ──
        yield format_sse_event({
            'type': 'item',
            'key':  'api_interfaces',
            'data': _build_api_interfaces(http_samplers),
        })

        # ── ② 引用变量 ──
        yield format_sse_event({
            'type': 'item',
            'key':  'used_vars',
            'data': _build_used_vars(http_samplers, vars_map, var_descs),
        })

        # ── ③ 线程配置（直接使用已加载的 DB 启用子配置，与子列表保持一致，不重复查库）──
        yield format_sse_event({
            'type': 'item',
            'key':  'thread_config',
            'data': _build_thread_config_from_db(active_configs, worker_count),
        })

        # ── ④ 引用数据文件 ──
        csv_files = summary.get("csv_data_files", [])
        yield format_sse_event({
            'type': 'item',
            'key':  'data_files',
            'data': await self._get_data_file_statuses(csv_files),
        })

        # ── ⑤ 后端监听器（含 InfluxDB 连通性探测）──
        # 探测视角：分布式→Master，单机→单机压力机（从压力机角度验证能否访问 InfluxDB）
        # 按 testname 去重：有 influxdb_url 的优先（保留配置完整的条目）；
        # 都有 URL 时再以启用状态为次要优先级
        _raw_listeners = summary.get("backend_listeners", [])
        _seen: dict = {}  # testname → 已选条目
        for bl in _raw_listeners:
            key = bl.get("testname") or ""
            if key not in _seen:
                _seen[key] = bl
            else:
                cur = _seen[key]
                new_has_url = bool(bl.get("influxdb_url"))
                cur_has_url = bool(cur.get("influxdb_url"))
                if new_has_url and not cur_has_url:
                    _seen[key] = bl  # 有 URL 的替换无 URL 的
                elif new_has_url and cur_has_url and bl.get("enabled") and not cur.get("enabled"):
                    _seen[key] = bl  # 都有 URL 时启用的优先
        backend_listeners = list(_seen.values())

        _is_dist_for_bl = scenario.is_distributed == 1
        if _is_dist_for_bl:
            _influxdb_machine = await self.machine_crud.get_master_machine()
        else:
            _singles = await self.machine_crud.get_available_machines(machine_type=3)
            _influxdb_machine = _singles[0] if _singles else None
        listeners_result = []
        for bl in backend_listeners:
            raw_url = bl.get("influxdb_url") or ""
            masked_url = re.sub(r'(://[^:/@]+:)[^@]+(@)', r'\1***\2', raw_url) if '@' in raw_url else raw_url
            if not bl.get("enabled"):
                listeners_result.append({**bl, "influxdb_url": masked_url, "connectivity": None, "connectivity_msg": ""})
                continue
            url = raw_url
            if url:
                if _influxdb_machine:
                    ok, msg = await asyncio.to_thread(_check_influxdb_via_ssh, _influxdb_machine, url)
                else:
                    ok, msg = False, "未配置压力机，无法探测"
            else:
                ok, msg = False, "未配置 InfluxDB URL"
            listeners_result.append({**bl, "influxdb_url": masked_url, "connectivity": ok, "connectivity_msg": msg})
        yield format_sse_event({
            'type': 'item',
            'key':  'backend_listeners',
            'data': {'total': len(listeners_result), 'listeners': listeners_result},
        })

        # ── ⑥ 调试组件（检查是否存在未关闭的调试取样器/监听器）──
        yield format_sse_event({
            'type': 'item',
            'key':  'debug_components',
            'data': _build_debug_components(summary.get("result_collectors", [])),
        })

        # ── ⑦ 压测前置准备 ──
        yield format_sse_event({
            'type': 'item',
            'key':  'precheck',
            'data': await self._build_precheck_config(scenario),
        })

        # ── ⑦ 服务连接状态检测（SSH 并发探测，耗时较长）──
        yield format_sse_event({
            'type': 'item',
            'key':  'service_check',
            'data': await self._check_service_connections(scenario),
        })

        yield format_sse_event({'type': 'done', 'message': '联调核查完成'})

    async def execute_sse(self, scenario_id: int, action: str) -> AsyncGenerator[str, None]:
        """SSE 入口：联调（action=inspect）或正式启动压测（action=execute）。

        前置校验通过后，根据 action 分发到 _inspect_sse 或 _execute_sse。
        两者均以 text/event-stream 协议实时推送阶段进度与日志。

        Args:
            scenario_id: 压测场景主键 ID
            action:      'inspect'=执行联调  'execute'=正式启动压测
        Yields:
            SSE 格式字符串，事件类型见各子方法说明
        Raises:
            不直接抛异常，所有异常均转为 {'type':'error'} 事件推送给前端
        """
        yield format_sse_event({'type': 'start', 'message': '准备中...'})

        # ── 1. 加载并校验场景 ────────────────────────────────────────────
        scenario = await self.scenario_crud.get_by_id_crud(scenario_id)
        if not scenario or not scenario.enabled_flag:
            yield format_sse_event({'type': 'error', 'message': '场景不存在'})
            return

        # ── 2. 获取启用的子配置 ──────────────────────────────────────────
        configs = await self.config_crud.get_configs(scenario_id)
        active_configs = [c for c in configs if c.status == 1]
        if not active_configs:
            yield format_sse_event({
                'type': 'error',
                'message': '未配置启用的子配置，请先在高级设置中添加并启用一条配置',
            })
            return

        # ── 3. 分发 ─────────────────────────────────────────────────────
        if action == 'inspect':
            if scenario.status not in (0,):
                # 已联调（status>=1）允许重新联调，只拦截正在运行中的场景
                if scenario.status == 2:
                    yield format_sse_event({'type': 'error', 'message': '场景正在压测中，不可重新联调'})
                    return
            async for chunk in self._inspect_sse(scenario, active_configs):
                yield chunk
        elif action == 'recover':
            if scenario.status not in (4, 5):
                yield format_sse_event({'type': 'error', 'message': '只有【已取消】或【失败】状态的场景才可恢复执行'})
                return
            async for chunk in self._recover_sse(scenario):
                yield chunk
        else: # 启动压测逻辑
            if scenario.status != 1:
                if scenario.status == 0:
                    yield format_sse_event({'type': 'error', 'message': '场景当前状态：待联调，请先场景联调通过。'})
                elif scenario.status == 2:
                    yield format_sse_event({'type': 'error', 'message': '场景正在压测中，请勿重复启动'})
                else:
                    yield format_sse_event({'type': 'error', 'message': f'当前场景状态（{scenario.status}）不支持启动压测'})
                return
            # 前置条件②：预计耗时统计正确（循环次数线程组需手动填写 estimated_duration）
            known_secs = 0
            has_unknown = False
            for cfg in active_configs:
                secs, unknown = _calc_config_duration(cfg)
                known_secs += secs
                if unknown:
                    has_unknown = True
            if has_unknown:
                yield format_sse_event({
                    'type': 'error',
                    'message': '存在启用的子配置预计耗时未知（循环次数线程组需在高级设置中手动填写预计耗时），请完善后再启动压测',
                })
                return
            if known_secs == 0:
                yield format_sse_event({
                    'type': 'error',
                    'message': '预计总耗时为0秒，请检查子配置参数是否正确（持续时间/循环次数/阶段配置等）',
                })
                return
            async for chunk in self._execute_sse(scenario, active_configs):
                yield chunk

    # ──────────────────── 联调 SSE ────────────────────

    async def _inspect_sse(self, scenario: PerfScenarioModel, active_configs: List[PerfScenarioConfigModel],
    ) -> AsyncGenerator[str, None]:
        """执行联调全流程，全程 SSE 推送。

        流程：
          Stage 1 — 将联调预置参数注入 JMX，保存到本地 uploads/ 目录供核查
          Stage 2 — SFTP 上传更新后的 JMX 到执行机（分布式→Master，单机→单机压力机）
          Stage 3 — SSH 前台执行 JMeter 命令，逐行推送控制台日志
                    进程正常退出（exit_code=0）→ status=1（待开始），推送 done
                    进程异常退出（exit_code≠0）→ status=0（待联调），remark 记错误，推送 error

        Args:
            scenario:       压测场景 ORM 对象
            active_configs: 当前所有启用（status=1）的子配置列表
        Yields:
            SSE 事件：start / stage_start / stage_done / log / done / error
        """
        # ── Stage 1：注入联调参数 ────────────────────────────────────────
        yield format_sse_event({'type': 'stage_start', 'stage': 1,
                                'stage_name': '更新JMX线程组配置',
                                'message': '正在将联调预置参数写入JMX脚本...'})
        try:
            jmx_bytes   = await self._download_jmx(scenario)
            modified    = await self._apply_inspect_params(scenario, active_configs, jmx_bytes)
            local_path  = self._save_jmx_locally(scenario.script_name, modified)
        except HTTPException as e:
            yield format_sse_event({'type': 'error', 'stage': 1, 'message': e.detail})
            return
        except Exception as e:
            logger.exception(f'_inspect_sse Stage1 失败 scenario={scenario.id}')
            yield format_sse_event({'type': 'error', 'stage': 1, 'message': f'JMX参数写入失败：{e}'})
            return

        yield format_sse_event({'type': 'stage_done', 'stage': 1,
                                'stage_name': '更新JMX线程组配置',
                                'message': 'JMX线程组配置已更新，副本保存至本地 uploads/ 目录',
                                'detail': {'local_path': str(local_path)}})

        # ── Stage 2：上传 JMX ────────────────────────────────────────────
        try:
            machine, remote_dir = await self._get_exec_machine_info(scenario)
        except HTTPException as e:
            yield format_sse_event({'type': 'error', 'stage': 2, 'message': e.detail})
            return

        # 建立 SSH 连接（Stage 2 SFTP 上传与 Stage 3 执行复用，避免重复握手）
        try:
            ssh_conn = await asyncio.to_thread(
                ShellOperationUtils.get_ssh_client, machine.ip,
                target_port=machine.ssh_port or 22,
                credential=_build_credential(machine),
            )
        except Exception as e:
            yield format_sse_event({'type': 'error', 'stage': 2, 'message': f'SSH 连接失败：{e}'})
            return

        try:
            yield format_sse_event({'type': 'stage_start', 'stage': 2,
                                    'stage_name': '上传JMX到压力机',
                                    'message': f'正在SFTP上传到 {machine.ip}:{remote_dir}...'})
            remote_jmx = f'{remote_dir}/{scenario.script_name}'
            try:
                upload_result = await self._upload_jmx_to_machine(str(local_path), machine, remote_dir, scenario.script_name,
                                                                   reuse_ssh=ssh_conn)
            except Exception as e:
                yield format_sse_event({'type': 'error', 'stage': 2, 'message': f'上传失败：{e}'})
                return
            upload_skipped = isinstance(upload_result, str) and upload_result.startswith('skipped:')
            if upload_skipped:
                yield format_sse_event({'type': 'log', 'stage': 2,
                                        'message': upload_result[len('skipped:'):]})
            yield format_sse_event({'type': 'stage_done', 'stage': 2,
                                    'stage_name': '上传JMX到压力机',
                                    'message': '已跳过（MD5一致，文件未变）' if upload_skipped else '上传完成',
                                    'detail': {'target': f'{machine.ip}', 'remote_path': remote_jmx}})

            # ── Stage 3：前台执行 JMeter，实时推送日志 ──────────────────────
            workers = await self._get_slave_workers(scenario)
            summariser_interval = await self.param_crud.get_param_value('JMETER_SUMMARISER_INTERVAL', '10')
            cmd_template = await self.param_crud.get_param_value('JMETER_START_CMD')
            cmd = self._build_jmeter_cmd(
                jmx_name=scenario.script_name,
                remote_dir=remote_dir,
                workers=workers,
                summariser_interval=summariser_interval,
                background=False,
                cmd_template=cmd_template,
            )

            yield format_sse_event({'type': 'stage_start', 'stage': 3,
                                    'stage_name': '执行联调',
                                    'message': '正在启动JMeter，实时输出控制台日志...'})

            exit_code = -1
            error_lines: List[str] = []
            try:
                async for kind, value in self._stream_ssh_cmd(ssh_conn, cmd):
                    if kind == 'log':
                        yield format_sse_event({'type': 'log', 'line': value})
                        if 'ERROR' in value or 'error' in value.lower():
                            error_lines.append(value)
                    elif kind == 'exit':
                        exit_code = value
                    elif kind == 'error':
                        yield format_sse_event({'type': 'error', 'stage': 3, 'message': f'SSH异常：{value}'})
                        return
            except Exception as e:
                logger.exception(f'_inspect_sse Stage3 SSH 失败 scenario={scenario.id}')
                yield format_sse_event({'type': 'error', 'stage': 3, 'message': f'SSH执行失败：{e}'})
                return
        finally:
            try: ssh_conn.close()
            except Exception: pass

        # ── 根据退出码更新场景状态 ───────────────────────────────────────
        if exit_code == 0 and not error_lines:
            await self.scenario_crud.update_crud(scenario.id, {
                'status': 1,        # 待开始（联调通过）
                'error_info': None,
            })
            yield format_sse_event({'type': 'stage_done', 'stage': 3,
                                    'stage_name': '执行联调',
                                    'message': 'JMeter联调执行完成，无错误'})
            yield format_sse_event({'type': 'done', 'status': 1, 'message': '联调通过，场景状态已更新为【待开始】'})
        else:
            err_summary = '；'.join(error_lines[:3]) if error_lines else f'退出码={exit_code}'
            await self.scenario_crud.update_crud(scenario.id, {
                'status': 0,        # 待联调（联调失败）
                'error_info': err_summary,
            })
            yield format_sse_event({'type': 'error', 'stage': 3,
                                    'message': f'联调失败（exit_code={exit_code}）：{err_summary}'})

    # ──────────────────── 正式压测 SSE ────────────────────

    async def _execute_sse(self, scenario: PerfScenarioModel, active_configs: List[PerfScenarioConfigModel],
    ) -> AsyncGenerator[str, None]:
        """正式启动压测全流程，全程 SSE 推送（nohup 后台模式，不等待进程结束）。

        流程：
          Stage 1 — 将正式子配置参数注入 JMX，保存到本地 uploads/ 目录
          Stage 2 — SFTP 上传更新后的 JMX 到执行机
          Stage 3 — SSH 执行 nohup JMeter 命令（后台）：
                    → 先单独初始化工作目录（mkdir/清空日志）
                    → 向控制台推送格式化后的启动命令预览
                    → 后台 nohup 启动 JMeter，更新 scenario.status=2（进行中）、executed_at
                    → 等待5秒验证 PID 存活 → 写入 Redis（TTL=24h）
                    → 启动 APScheduler 日志收集任务（collect_jmeter_log）
          推送 done 事件（压测后台运行，不等待结束）

        Args:
            scenario:       压测场景 ORM 对象
            active_configs: 当前所有启用（status=1）的子配置列表
        Yields:
            SSE 事件：stage_start / stage_done / done / error
        """
        from datetime import datetime

        # ── 立即将状态变更为"进行中"，防止并发重复启动，让监控页面即时感知 ─────────
        # executed_at 将在 PID 验证通过后更新，确保 monitor_sse 以 JMeter 实际启动时刻为基准
        await self.scenario_crud.update_crud(scenario.id, {
            'status':      2,
            'progress':    0,
            'error_info':  None,
        })

        async def _fail(stage: int, msg: str) -> None:
            """将场景标记为失败（status=5）并写入 error_info。"""
            try:
                await self.scenario_crud.update_crud(scenario.id, {
                    'status': 5, 'error_info': msg[:2000]
                })
            except Exception:
                pass

        # ── Stage 1：注入正式参数 ────────────────────────────────────────
        yield format_sse_event({'type': 'stage_start', 'stage': 1,
                                'stage_name': '更新JMX线程组配置',
                                'message': '正在将子配置参数写入JMX脚本...'})
        try:
            jmx_bytes  = await self._download_jmx(scenario)
            modified   = self._apply_execute_params(scenario, active_configs, jmx_bytes)
            local_path = self._save_jmx_locally(scenario.script_name, modified)
        except HTTPException as e:
            await _fail(1, e.detail)
            yield format_sse_event({'type': 'error', 'stage': 1, 'message': e.detail})
            return
        except Exception as e:
            logger.exception(f'_execute_sse Stage1 失败 scenario={scenario.id}')
            msg = f'JMX参数写入失败：{e}'
            await _fail(1, msg)
            yield format_sse_event({'type': 'error', 'stage': 1, 'message': msg})
            return

        yield format_sse_event({'type': 'stage_done', 'stage': 1,
                                'stage_name': '更新JMX线程组配置',
                                'message': 'JMX线程组配置已更新',
                                'detail': {'local_path': str(local_path)}})

        # ── Stage 2：上传 JMX ────────────────────────────────────────────
        try:
            machine, remote_dir = await self._get_exec_machine_info(scenario)
        except HTTPException as e:
            await _fail(2, e.detail)
            yield format_sse_event({'type': 'error', 'stage': 2, 'message': e.detail})
            return

        # 建立 SSH 连接（Stage 2 SFTP 上传与 Stage 3 执行复用，避免重复握手）
        try:
            ssh_conn = await asyncio.to_thread(
                ShellOperationUtils.get_ssh_client, machine.ip,
                target_port=machine.ssh_port or 22,
                credential=_build_credential(machine),
            )
        except Exception as e:
            msg = f'SSH 连接失败：{e}'
            await _fail(2, msg)
            yield format_sse_event({'type': 'error', 'stage': 2, 'message': msg})
            return

        pid_str      = ''
        jmeter_alive = True   # 进程是否存活；仅 kill -0 明确返回 dead 时置 False
        nohup_err    = ''     # PID dead 时读取的 nohup.out 内容，写入 error_info
        try:
            remote_jmx = f'{remote_dir}/{scenario.script_name}'
            yield format_sse_event({'type': 'stage_start', 'stage': 2,
                                    'stage_name': '上传JMX到压力机',
                                    'message': f'正在SFTP上传到 {machine.ip}:{remote_dir}...'})
            try:
                upload_result = await self._upload_jmx_to_machine(str(local_path), machine, remote_dir, scenario.script_name,
                                                                   reuse_ssh=ssh_conn)
            except Exception as e:
                msg = f'上传失败：{e}'
                await _fail(2, msg)
                yield format_sse_event({'type': 'error', 'stage': 2, 'message': msg})
                return
            upload_skipped = isinstance(upload_result, str) and upload_result.startswith('skipped:')
            if upload_skipped:
                yield format_sse_event({'type': 'log', 'stage': 2,
                                        'message': upload_result[len('skipped:'):]})
            yield format_sse_event({'type': 'stage_done', 'stage': 2,
                                    'stage_name': '上传JMX到压力机',
                                    'message': '' if upload_skipped else '上传完成',
                                    'detail': {'target': machine.ip, 'remote_path': remote_jmx}})

            # 上传成功后更新文件分发状态（共享分发，worker=1）
            try:
                machine_label = f'Master({machine.ip})' if scenario.is_distributed == 1 else f'单机({machine.ip})'
                await BaseCRUD(PerfFileModel, self.db).update_crud(scenario.script_id, {
                    'dist_status':    1,
                    'dist_worker_ids': [machine.id],
                    'dist_time':       datetime.now(),
                    'remark':          f'脚本已上传到{machine_label}',
                })
            except Exception as _fe:
                logger.warning(f'[Execute] 更新文件分发状态失败 scenario_id={scenario.id}: {_fe}')

            # ── Stage 3：目录初始化 + 格式化命令展示 + nohup 启动 ──────────────
            workers = await self._get_slave_workers(scenario)
            summariser_interval = await self.param_crud.get_param_value('JMETER_SUMMARISER_INTERVAL', '10')
            cmd_template = await self.param_crud.get_param_value('JMETER_START_CMD')

            # 构建 jmeter_args（不含 dir_init 和 nohup 包装）
            if cmd_template:
                jmeter_args = cmd_template.format(
                    jmx_file=scenario.script_name,
                    summariser_interval=summariser_interval,
                )
            else:
                jmeter_args = (
                    f"jmeter -n -t {scenario.script_name} "
                    f"-l ./results/result.jtl -f "
                    f"-j ./logs/jmeter.log "
                    f"-J summariser.name=summary "
                    f"-J summariser.interval={summariser_interval} "
                    f"-e -o ./reports/report "
                    f"-X"
                )
            if workers:
                rmi_hosts = ','.join(f"{w.ip}:{w.rmi_port or 1099}" for w in workers)
                jmeter_args += f" -R {rmi_hosts} -Dserver.rmi.ssl.disable=true"

            # 目录初始化命令（使用 commands.py 统一常量）
            from app.common.commands import JMETER_DIR_INIT
            dir_init_cmd = JMETER_DIR_INIT.format(remote_dir=remote_dir)

            # nohup 启动：bash -l 的 stdout/stderr 整体重定向到 /dev/null，
            # 切断 .bash_profile 后台进程对 SSH 信道 FD1 的占用，使 stdout.read() 即时返回。
            # PID 通过 ps 查找 ApacheJMeter.jar 子进程获取，无需写文件。
            from app.common.commands import JMETER_NOHUP_START, JMETER_FIND_PID
            nohup_cmd = JMETER_NOHUP_START.format(remote_dir=remote_dir, jmeter_args=jmeter_args)
            find_pid_cmd = JMETER_FIND_PID

            yield format_sse_event({'type': 'stage_start', 'stage': 3,
                                    'stage_name': '启动JMeter压测',
                                    'message': '正在初始化工作目录...'})

            # 3a. 执行目录初始化
            yield format_sse_event({'type': 'log', 'stage': 3,
                                    'message': f'$ {dir_init_cmd}'})

            def _run_dir_init() -> str:
                _, out, _ = ShellOperationUtils.execute_remote_command(ssh_conn, dir_init_cmd)
                return (out or '').strip()

            try:
                dir_out = await asyncio.to_thread(_run_dir_init)
                yield format_sse_event({'type': 'log', 'stage': 3,
                                        'message': f'工作目录初始化：{dir_out or "ok"}'})
            except Exception as e:
                logger.exception(f'_execute_sse Stage3 dir_init 失败 scenario={scenario.id}')
                msg = f'目录初始化失败：{e}'
                await _fail(3, msg)
                yield format_sse_event({'type': 'error', 'stage': 3, 'message': msg})
                return

            # 3b. 推送 JMeter 启动命令（原始格式）
            yield format_sse_event({'type': 'log', 'stage': 3,
                                    'message': f'启动命令：{jmeter_args}'})
            logger.info(f'[Execute] scenario={scenario.id} Stage3 nohup命令：{nohup_cmd}')

            # 3c. 执行 nohup 启动，等待 1s 后用 ps 查找 ApacheJMeter.jar 子进程 PID
            def _launch_nohup() -> str:
                import time as _time
                ShellOperationUtils.execute_remote_command(ssh_conn, nohup_cmd)
                _time.sleep(1)
                _, pid_out, _ = ShellOperationUtils.execute_remote_command(ssh_conn, find_pid_cmd)
                return (pid_out or '').strip()

            try:
                nohup_stdout = await asyncio.to_thread(_launch_nohup)
            except Exception as e:
                logger.exception(f'_execute_sse Stage3 nohup 失败 scenario={scenario.id}')
                msg = f'启动JMeter失败：{e}'
                await _fail(3, msg)
                yield format_sse_event({'type': 'error', 'stage': 3, 'message': msg})
                return

            logger.info(f'[Execute] scenario={scenario.id} jmeter.pid 内容：{repr(nohup_stdout)}')

            # 解析 PID（从 jmeter.pid 文件读取）
            pid_lines = [l.strip() for l in (nohup_stdout or '').split('\n') if l.strip()]
            pid_str   = pid_lines[-1] if pid_lines and pid_lines[-1].isdigit() else ''
            logger.info(f'[Execute] scenario={scenario.id} 解析 PID={pid_str!r}')

            # 等待 3s 后用 kill -0 验证进程（复用 ssh_conn，无需重连）
            if pid_str.isdigit():
                yield format_sse_event({'type': 'log', 'stage': 3,
                                        'message': f'获取到 PID={pid_str}，等待 3 秒后验证进程状态...'})
                await asyncio.sleep(3)
                from app.common.commands import PID_ALIVE_CHECK
                def _verify_pid():
                    _, out, _ = ShellOperationUtils.execute_remote_command(
                        ssh_conn,
                        PID_ALIVE_CHECK.format(pid=pid_str),
                    )
                    return out.strip()
                try:
                    pid_status = await asyncio.to_thread(_verify_pid)
                    logger.info(f'[Execute] scenario={scenario.id} PID={pid_str} kill -0 结果：{pid_status!r}')
                    if pid_status == 'alive':
                        pass  # stage_done 消息已含 PID，此处不重复推送
                    else:
                        # 进程已退出：读取 nohup.out 获取错误详情（ssh_conn 此时仍在 try 块内可复用）
                        def _read_nohup():
                            _, out, _ = ShellOperationUtils.execute_remote_command(
                                ssh_conn,
                                f"tail -50 '{remote_dir}/logs/jmeter_nohup.out' 2>/dev/null",
                            )
                            return out or ''
                        try:
                            nohup_err = await asyncio.to_thread(_read_nohup)
                        except Exception:
                            pass
                        jmeter_alive = False

                        # 立即更新场景状态为失败，不延迟到 finally 之后
                        # （finally 后的代码可能因 GeneratorExit 或连接关闭而不执行）
                        _err_detail = f'JMeter进程启动后立即退出（PID={pid_str}）'
                        if nohup_err.strip():
                            _err_detail += f'\n\njmeter_nohup.out（最后50行）:\n{nohup_err}'
                        try:
                            await self.scenario_crud.update_crud(scenario.id, {
                                'status':     5,
                                'error_info': _err_detail[:2000],
                            })
                        except Exception as ue:
                            logger.error(f'[Execute] scenario={scenario.id} 更新失败状态异常: {ue}')

                        logger.error(
                            f'[Execute] scenario={scenario.id} PID={pid_str} 进程已退出，'
                            f'nohup.out:\n{nohup_err}'
                        )
                        yield format_sse_event({'type': 'log', 'stage': 3,
                                                'message': f'PID={pid_str} 进程已退出，压测启动失败，请检查压力机日志'})
                except Exception as ve:
                    logger.warning(f'PID验证失败 scenario={scenario.id}: {ve}')
            else:
                yield format_sse_event({'type': 'log', 'stage': 3,
                                        'message': '未获取到 PID，进程可能启动缓慢，将由日志收集任务持续检测'})
        finally:
            try: ssh_conn.close()
            except Exception: pass

        # PID 验证失败（进程启动后立即退出）→ 状态已在检测分支中写入 DB，此处只终止流
        if not jmeter_alive:
            yield format_sse_event({'type': 'error', 'stage': 3,
                                    'message': f'JMeter进程启动后立即退出（PID={pid_str}），请检查压力机日志'})
            return

        # PID 验证通过，此时 JMeter 已真正后台运行，将 executed_at 更新为实际启动时刻
        # monitor_sse 以此时间为进度基准，确保进度条与日志出现时间高度同步
        await self.scenario_crud.update_crud(scenario.id, {'executed_at': datetime.now()})

        from app.db import get_redis_pool
        from app.utils.perf_log_collector import _pid_key, _log_key, _offset_key, _evicted_key
        redis = get_redis_pool().get_redis()
        # 清理上一次压测遗留的 Redis 状态，避免日志行偏移错位、监控页面显示旧日志
        await redis.delete(_log_key(scenario.id), _offset_key(scenario.id), _evicted_key(scenario.id))
        if pid_str.isdigit():
            await redis.set(_pid_key(scenario.id), pid_str, ex=86400)
        else:
            await redis.delete(_pid_key(scenario.id))

        # ── 启动 APScheduler 日志收集任务 ────────────────────────────────
        poll_interval = int(await self.param_crud.get_param_value('JMETER_LOG_POLL_INTERVAL', '5'))
        cred = _build_credential(machine)
        try:
            from app.utils.perf_log_collector import start_log_collector
            start_log_collector(
                scenario_id=scenario.id,
                is_distributed=scenario.is_distributed,
                remote_dir=remote_dir,
                exec_machine_ip=machine.ip,
                exec_machine_ssh_port=machine.ssh_port or 22,
                poll_interval=poll_interval,
                ssh_user=cred.get('ssh_user'),
                ssh_password=cred.get('ssh_password'),
            )
        except Exception as e:
            logger.warning(f'启动日志收集任务失败（不影响压测）：{e}')

        pid_info = f'PID={pid_str}' if pid_str.isdigit() else '（PID未获取到，进程可能启动缓慢）'
        yield format_sse_event({'type': 'stage_done', 'stage': 3,
                                'stage_name': '启动JMeter压测',
                                'message': f'JMeter已启动，{pid_info}',
                                'detail': {'pid': pid_str}})
        yield format_sse_event({'type': 'done', 'status': 2,
                                'message': '压测已成功启动，场景状态已更新为【进行中】'})

    # ──────────────────── 恢复执行 SSE ────────────────────

    async def _recover_sse(self, scenario: PerfScenarioModel) -> AsyncGenerator[str, None]:
        """恢复已取消/失败的压测：直接 SSH 执行 JMeter，不重新注入参数或上传 JMX。

        与 _execute_sse 的区别：仅执行 Stage3（SSH 启动进程），跳过 Stage1/2。
        适用场景：用户手动停止或压测失败后，确认 JMX 已在压力机本地，直接恢复运行。
        """
        from datetime import datetime

        yield format_sse_event({'type': 'stage_start', 'stage': 1,
                                'stage_name': '恢复启动JMeter',
                                'message': '正在连接执行机并恢复启动 JMeter...'})

        try:
            machine, remote_dir = await self._get_exec_machine_info(scenario)
        except HTTPException as e:
            yield format_sse_event({'type': 'error', 'stage': 1, 'message': e.detail})
            return

        workers = await self._get_slave_workers(scenario)
        summariser_interval = await self.param_crud.get_param_value('JMETER_SUMMARISER_INTERVAL', '10')
        cmd_template = await self.param_crud.get_param_value('JMETER_START_CMD')

        # 构建 jmeter_args（不含 dir_init 和 nohup 包装）
        if cmd_template:
            jmeter_args = cmd_template.format(
                jmx_file=scenario.script_name,
                summariser_interval=summariser_interval,
            )
        else:
            jmeter_args = (
                f"jmeter -n -t {scenario.script_name} "
                f"-l ./results/result.jtl -f "
                f"-j ./logs/jmeter.log "
                f"-J summariser.name=summary "
                f"-J summariser.interval={summariser_interval} "
                f"-e -o ./reports/report "
                f"-X"
            )
        if workers:
            rmi_hosts = ','.join(f"{w.ip}:{w.rmi_port or 1099}" for w in workers)
            jmeter_args += f" -R {rmi_hosts} -Dserver.rmi.ssl.disable=true"

        # 目录初始化命令（单独执行）
        dir_init_inner = (
            f"cd '{remote_dir}' && "
            f"{{ [ ! -d results ] && mkdir -p results || true; }} && "
            f"{{ [ ! -d logs ]   && mkdir -p logs   || true; }} && "
            f"{{ [ ! -d reports ] && mkdir -p reports || true; }} && "
            f"rm -rf ./reports/report && "
            f"> ./logs/jmeter.log && echo dir_done"
        )
        dir_init_cmd = f'bash -l -c "{dir_init_inner}"'
        dir_init_display = dir_init_inner.replace('} && rm -rf', '} &&\n  rm -rf', 1)

        # nohup 启动：bash -l 的 stdout/stderr 整体重定向到 /dev/null，
        # 切断 .bash_profile 后台进程对 SSH 信道 FD1 的占用，使 stdout.read() 即时返回。
        # PID 通过 ps 查找 ApacheJMeter.jar 子进程获取，无需写文件。
        from app.common.commands import JMETER_NOHUP_START, JMETER_FIND_PID
        nohup_cmd = JMETER_NOHUP_START.format(remote_dir=remote_dir, jmeter_args=jmeter_args)
        find_pid_cmd = JMETER_FIND_PID

        try:
            ssh_conn = await asyncio.to_thread(
                ShellOperationUtils.get_ssh_client, machine.ip,
                target_port=machine.ssh_port or 22,
                credential=_build_credential(machine),
            )
        except Exception as e:
            yield format_sse_event({'type': 'error', 'stage': 1, 'message': f'SSH 连接失败：{e}'})
            return

        pid_str      = ''
        jmeter_alive = True   # 进程是否存活；仅 kill -0 明确返回 dead 时置 False
        nohup_err    = ''     # PID dead 时读取的 nohup.out 内容，写入 error_info
        try:
            # 3a. 目录初始化
            yield format_sse_event({'type': 'log', 'stage': 1,
                                    'message': f'$ {dir_init_display}'})

            def _run_dir_init_r() -> str:
                _, out, _ = ShellOperationUtils.execute_remote_command(ssh_conn, dir_init_cmd)
                return (out or '').strip()

            try:
                dir_out = await asyncio.to_thread(_run_dir_init_r)
                yield format_sse_event({'type': 'log', 'stage': 1,
                                        'message': f'工作目录初始化：{dir_out or "ok"}'})
            except Exception as e:
                logger.exception(f'_recover_sse dir_init 失败 scenario={scenario.id}')
                yield format_sse_event({'type': 'error', 'stage': 1, 'message': f'目录初始化失败：{e}'})
                return

            # 3b. 推送 JMeter 启动命令（原始格式）
            yield format_sse_event({'type': 'log', 'stage': 1,
                                    'message': f'启动命令：{jmeter_args}'})
            logger.info(f'[Recover] scenario={scenario.id} nohup命令：{nohup_cmd}')

            # 3c. 执行 nohup，等待 1s 后用 ps 查找 ApacheJMeter.jar 子进程 PID
            def _launch():
                import time as _time
                ShellOperationUtils.execute_remote_command(ssh_conn, nohup_cmd)
                _time.sleep(1)
                _, pid_out, _ = ShellOperationUtils.execute_remote_command(ssh_conn, find_pid_cmd)
                return (pid_out or '').strip()

            try:
                nohup_stdout = await asyncio.to_thread(_launch)
            except Exception as e:
                logger.exception(f'_recover_sse nohup 失败 scenario={scenario.id}')
                yield format_sse_event({'type': 'error', 'stage': 1, 'message': f'启动 JMeter 失败：{e}'})
                return

            pid_lines = [l.strip() for l in (nohup_stdout or '').split('\n') if l.strip()]
            pid_str   = pid_lines[-1] if pid_lines and pid_lines[-1].isdigit() else ''

            if pid_str.isdigit():
                yield format_sse_event({'type': 'log', 'stage': 1,
                                        'message': f'获取到 PID={pid_str}，等待 3 秒后验证进程状态...'})
                await asyncio.sleep(3)
                from app.common.commands import PID_ALIVE_CHECK
                def _verify():
                    _, out, _ = ShellOperationUtils.execute_remote_command(
                        ssh_conn, PID_ALIVE_CHECK.format(pid=pid_str))
                    return out.strip()
                try:
                    pid_status = await asyncio.to_thread(_verify)
                    if pid_status == 'alive':
                        pass  # stage_done 消息已含 PID，此处不重复推送
                    else:
                        # 进程已退出：读取 nohup.out 获取错误详情
                        def _read_nohup_r():
                            _, out, _ = ShellOperationUtils.execute_remote_command(
                                ssh_conn,
                                f"tail -50 '{remote_dir}/logs/jmeter_nohup.out' 2>/dev/null",
                            )
                            return out or ''
                        try:
                            nohup_err = await asyncio.to_thread(_read_nohup_r)
                        except Exception:
                            pass
                        jmeter_alive = False
                        yield format_sse_event({'type': 'log', 'stage': 1,
                                                'message': f'PID={pid_str} 进程已退出，压测启动失败，请检查压力机日志'})
                except Exception as ve:
                    logger.warning(f'_recover_sse PID验证失败 scenario={scenario.id}: {ve}')
            else:
                yield format_sse_event({'type': 'log', 'stage': 1,
                                        'message': '未获取到 PID，进程可能启动缓慢，将由日志收集任务持续检测'})
        finally:
            try: ssh_conn.close()
            except Exception: pass

        # PID 验证失败（进程启动后立即退出）→ 标记为失败(5)，不启动日志收集任务
        if not jmeter_alive:
            err_detail = f'JMeter进程恢复启动后立即退出（PID={pid_str}）'
            if nohup_err.strip():
                err_detail += f'\n\njmeter_nohup.out（最后50行）:\n{nohup_err}'
            await self.scenario_crud.update_crud(scenario.id, {
                'status':     5,      # 失败
                'error_info': err_detail[:2000],
            })
            yield format_sse_event({'type': 'error', 'stage': 1,
                                    'message': f'JMeter进程恢复启动后立即退出（PID={pid_str}），请检查压力机日志'})
            return

        now = datetime.now()
        await self.scenario_crud.update_crud(scenario.id, {
            'status':      2,
            'executed_at': now,
            'progress':    0,
            'error_info':  None,
        })

        from app.db import get_redis_pool
        from app.utils.perf_log_collector import _pid_key, _log_key, _offset_key, _evicted_key
        redis = get_redis_pool().get_redis()
        # 清理上一次压测遗留的 Redis 状态，避免日志行偏移错位、监控页面显示旧日志
        await redis.delete(_log_key(scenario.id), _offset_key(scenario.id), _evicted_key(scenario.id))
        if pid_str.isdigit():
            await redis.set(_pid_key(scenario.id), pid_str, ex=86400)
        else:
            await redis.delete(_pid_key(scenario.id))

        poll_interval = int(await self.param_crud.get_param_value('JMETER_LOG_POLL_INTERVAL', '5'))
        cred = _build_credential(machine)
        try:
            from app.utils.perf_log_collector import start_log_collector
            start_log_collector(
                scenario_id=scenario.id,
                is_distributed=scenario.is_distributed,
                remote_dir=remote_dir,
                exec_machine_ip=machine.ip,
                exec_machine_ssh_port=machine.ssh_port or 22,
                poll_interval=poll_interval,
                ssh_user=cred.get('ssh_user'),
                ssh_password=cred.get('ssh_password'),
            )
        except Exception as e:
            logger.warning(f'恢复压测：启动日志收集任务失败（不影响压测）：{e}')

        pid_info = f'PID={pid_str}' if pid_str.isdigit() else '（PID未获取到，进程可能启动缓慢）'
        yield format_sse_event({'type': 'stage_done', 'stage': 1,
                                'stage_name': '恢复启动JMeter',
                                'message': f'JMeter已恢复启动，{pid_info}'})
        yield format_sse_event({'type': 'done', 'status': 2,
                                'message': '压测已恢复，场景状态已更新为【进行中】'})

    # ──────────────────── 实时监控 SSE ────────────────────
    async def monitor_sse(self, scenario_id: int, offset: int = 0) -> AsyncGenerator[str, None]:
        """SSE 实时监控：从 Redis 推送日志行、进度与心跳，支持断线重连续传。
        连接建立后依次执行：
          1. 将 Redis List 中 [offset, current_end) 的历史行一次性批量推送（补偿断线期间遗漏）
          2. 进入轮询循环（间隔 JMETER_LOG_POLL_INTERVAL 秒）：
             - 有新行 → 推送 log 事件，更新本地 offset
             - 推送 progress 事件（含已用时间与预计耗时）
             - 超过 JMETER_MONITOR_HEARTBEAT 秒无新日志 → 推送 ping 心跳
          3. 场景 status ≠ 2（压测结束/失败/取消） → 推送 done/error 关闭流

        前端心跳检测建议：
          收到 ping 事件重置客户端超时计时器；
          超过 heartbeat*2 秒未收到任何事件 → 显示提示并自动重连（携带 offset 参数）。

        Args:
            scenario_id: 压测场景主键 ID
            offset:      客户端已接收到的 Redis List 行索引（断线重连时携带）
        Yields:
            SSE 事件类型：
              connected — 连接建立确认（含 offset）
              log       — 一行 JMeter 控制台日志
              progress  — 当前进度（value/elapsed/estimated）
              ping      — 心跳保活（含服务端时间戳）
              done      — 压测结束（含最终 status）
              error     — 场景异常
        """
        import time as _time
        from app.db import get_redis_pool
        from app.utils.perf_log_collector import _log_key, _evicted_key

        redis = get_redis_pool().get_redis()
        log_key     = _log_key(scenario_id)
        evicted_key = _evicted_key(scenario_id)

        poll_interval        = int(await self.param_crud.get_param_value('JMETER_LOG_POLL_INTERVAL', '5'))
        heartbeat_secs       = int(await self.param_crud.get_param_value('JMETER_MONITOR_HEARTBEAT', '20'))
        summariser_interval  = int(await self.param_crud.get_param_value('JMETER_SUMMARISER_INTERVAL', '10'))
        # 启动宽限：首条 summary 到达前允许按时间推进进度（首次汇总最多需要 summariser_interval 秒）
        _startup_grace   = summariser_interval + poll_interval + 10
        # 超过此时长无新日志则冻结进度条（2 个汇总周期 + 1 个轮询周期）
        _log_freeze_secs = summariser_interval * 2 + poll_interval
        _last_log_at     = None   # 最近一次收到新日志行的 datetime；None=尚未收到
        _frozen_progress = 0      # 冻结时保持的最后进度值

        # 修正客户端传入的 offset：减去已被 LTRIM 裁剪掉的行数，映射到当前 Redis List 下标
        evicted      = int(await redis.get(evicted_key) or 0)
        list_offset  = max(0, offset - evicted)   # Redis List 内的实际起始下标
        current_offset = list_offset              # 本次连接从此处开始读
        last_log_time  = _time.monotonic()

        yield format_sse_event({
            'type': 'connected', 'offset': offset,
            'evicted': evicted,
            'message': (
                f'已连接实时监控，等待日志数据...'
                if evicted == 0 else
                f'已连接实时监控（早期 {evicted} 行日志因超出缓存上限已被清理）'
            ),
        })

        while True:
            # ── 检查场景状态 ──────────────────────────────────────────────
            # 【根本修复】MySQL REPEATABLE READ 隔离级别：同一事务内的 SELECT 始终读取
            # 事务开始时的快照，导致 collect_jmeter_log 提交的 status=3 对本 Session 不可见。
            # 每轮循环前 rollback 结束当前事务，下一次 SELECT 重新开启事务读取最新已提交数据。
            try:
                await self.db.rollback()
            except Exception:
                pass
            from sqlalchemy import select as _sa_select
            _stmt = (_sa_select(PerfScenarioModel)
                     .where(PerfScenarioModel.id == scenario_id)
                     .execution_options(populate_existing=True))
            scenario = (await self.db.execute(_stmt)).scalar_one_or_none()
            if not scenario:
                yield format_sse_event({'type': 'error', 'message': '场景不存在'})
                return

            # ── 推送新日志行（按 Redis List 下标增量读取）────────────────
            # 每轮同步最新裁剪量，防止本次连接期间再次发生 LTRIM 导致 offset 偏移
            new_evicted = int(await redis.get(evicted_key) or 0)
            if new_evicted > evicted:
                # 本轮期间又发生了裁剪，将 current_offset 向前收缩对应行数
                current_offset = max(0, current_offset - (new_evicted - evicted))
                evicted = new_evicted

            total = await redis.llen(log_key)
            if total > current_offset:
                raw_lines = await redis.lrange(log_key, current_offset, total - 1)
                for raw in raw_lines:
                    line = raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else raw
                    yield format_sse_event({'type': 'log', 'message': line})
                current_offset = total
                last_log_time  = _time.monotonic()
                _last_log_at   = datetime.now()

            # ── 推送进度（日志活跃时推进，卡住/失败无输出时冻结）──────────────
            if scenario.estimated_duration and scenario.executed_at:
                elapsed_secs = (datetime.now() - scenario.executed_at).total_seconds()
                in_startup   = elapsed_secs <= _startup_grace
                log_fresh    = (_last_log_at is not None and
                                (datetime.now() - _last_log_at).total_seconds() <= _log_freeze_secs)
                if in_startup or log_fresh:
                    _frozen_progress = min(99, int(elapsed_secs / scenario.estimated_duration * 100))
                yield format_sse_event({
                    'type': 'progress', 'value': _frozen_progress,
                    'elapsed': int(elapsed_secs), 'estimated': scenario.estimated_duration,
                })
            else:
                yield format_sse_event({'type': 'progress', 'value': 0})

            # ── 场景结束判断 ──────────────────────────────────────────────
            if scenario.status != 2:
                if scenario.status == 3:
                    yield format_sse_event({'type': 'progress', 'value': 100})
                final_msg = {3: '压测已完成', 4: '压测已取消', 5: '压测失败',}.get(scenario.status, '压测已结束')
                yield format_sse_event({'type': 'done', 'status': scenario.status, 'message': final_msg})
                return

            # ── 心跳（无新日志超过 heartbeat_secs 时发送）────────────────
            if _time.monotonic() - last_log_time >= heartbeat_secs:
                yield format_sse_event({'type': 'ping', 'ts': int(_time.time())})
                last_log_time = _time.monotonic()

            try:
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                # 服务器关闭或客户端断连导致任务取消，静默退出避免日志噪音
                return

    # ──────────────────── 内部实现 ────────────────────

    @staticmethod
    async def _stream_ssh_cmd(ssh, cmd: str) -> AsyncGenerator[tuple, None]:
        """在 SSH 上执行前台命令，通过 threading+asyncio.Queue 实时 yield 控制台输出。

        使用线程读取 paramiko 阻塞的 stdout，通过 run_coroutine_threadsafe 将行投递到
        asyncio.Queue，再由异步生成器 yield 出去，避免阻塞事件循环。

        Args:
            ssh: paramiko.SSHClient 或 _RelayClient
            cmd: 要执行的远端命令（前台阻塞）
        Yields:
            ('log',  line_str)  — 一行标准输出
            ('error', msg_str)  — 读取过程异常
            ('exit',  exit_code)— 进程退出码（最后一项）
        """
        import threading

        loop  = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _reader():
            _, stdout, _ = ssh.exec_command(cmd, get_pty=False)
            try:
                for raw in iter(stdout.readline, ''):
                    if not raw:
                        break
                    asyncio.run_coroutine_threadsafe(
                        queue.put(('log', raw.rstrip('\n\r'))), loop
                    )
            except Exception as exc:
                asyncio.run_coroutine_threadsafe(queue.put(('error', str(exc))), loop)
            finally:
                try:
                    code = stdout.channel.recv_exit_status()
                except Exception:
                    code = -1
                asyncio.run_coroutine_threadsafe(queue.put(('exit', code)), loop)

        threading.Thread(target=_reader, daemon=True).start()

        while True:
            kind, value = await queue.get()
            yield kind, value
            if kind in ('exit', 'error'):
                break

    async def _apply_inspect_params(self, scenario: PerfScenarioModel, active_configs: List[PerfScenarioConfigModel],
                jmx_bytes: bytes,) -> bytes:
        """将联调预置参数（来自 perf_config_params）注入 JMX bytes，返回修改后的 bytes。

        每种 jmx_type 取 ID 最小的配置确定 param_key，广播写入该类型所有已启用线程组。

        Args:
            scenario:       压测场景对象（提供 test_type）
            active_configs: 启用的子配置列表
            jmx_bytes:      原始 JMX 文件内容
        Returns:
            注入联调参数后的 JMX bytes
        Raises:
            HTTPException 400 — 联调参数配置未找到或格式错误
        """
        import json as _json
        seen_types: dict = {}
        for cfg in sorted(active_configs, key=lambda c: c.id):
            jt = self._DB_TO_JMX_TYPE.get(cfg.thread_type, 'standard')
            if jt not in seen_types:
                seen_types[jt] = cfg

        modified = jmx_bytes
        for jmx_type, cfg in seen_types.items():
            param_key = self._get_inspect_param_key(cfg.thread_type, scenario.test_type)
            raw_json  = await self.param_crud.get_param_value(param_key)
            if not raw_json:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f'联调参数配置未找到（param_key={param_key}），请在参数配置中初始化预置值')
            try:
                inspect_params = _json.loads(raw_json)
            except _json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f'联调参数配置格式错误（param_key={param_key}），值必须是合法的 JSON')
            modified = apply_jmx_by_type(modified, jmx_type, inspect_params)
        return modified

    def _apply_execute_params(
        self,
        scenario: PerfScenarioModel,
        active_configs: List[PerfScenarioConfigModel],
        jmx_bytes: bytes,
    ) -> bytes:
        """将正式子配置参数注入 JMX bytes，返回修改后的 bytes。

        单配置类型广播写入；多配置类型按 ID 升序与 JMX 解析顺序位置配对精确注入。

        Args:
            scenario:       压测场景对象
            active_configs: 启用的子配置列表
            jmx_bytes:      原始 JMX 文件内容
        Returns:
            注入正式参数后的 JMX bytes
        """
        from collections import defaultdict
        type_groups: dict = defaultdict(list)
        for cfg in sorted(active_configs, key=lambda c: c.id):
            jt = self._DB_TO_JMX_TYPE.get(cfg.thread_type, 'standard')
            type_groups[jt].append(cfg)

        modified = jmx_bytes
        for jmx_type, cfgs in type_groups.items():
            if len(cfgs) == 1:
                db_params = self._config_to_db_params(cfgs[0])
                modified  = apply_jmx_by_type(modified, jmx_type, db_params)
            else:
                summary = parse_jmx_summary(modified)
                jmx_tgs = [
                    tg for tg in summary.get('thread_groups', [])
                    if tg.get('tg_type') == jmx_type and tg.get('enabled', True)
                ]
                for cfg, tg in zip(cfgs, jmx_tgs):
                    db_params = self._config_to_db_params(cfg)
                    modified  = apply_jmx_by_type(modified, jmx_type, db_params,
                                                   tg_index=tg['index'])
        return modified

    @staticmethod
    def _save_jmx_locally(jmx_name: str, jmx_bytes: bytes) -> 'os.PathLike':
        """将更新后的 JMX bytes 保存到本地 uploads/ 目录供人工核查。

        路径：{project_root}/uploads/{jmx_name}
        目录不存在时自动创建，同名文件直接覆盖。

        Args:
            jmx_name:  JMX 原始文件名（含 .jmx 扩展名，与场景引用的脚本同名）
            jmx_bytes: JMX 文件内容
        Returns:
            保存后的本地文件路径（Path 对象）
        """
        from pathlib import Path
        project_root = Path(__file__).resolve().parents[4]
        uploads_dir  = project_root / 'uploads'
        uploads_dir.mkdir(parents=True, exist_ok=True)
        local_path = uploads_dir / jmx_name
        local_path.write_bytes(jmx_bytes)
        logger.info(f'JMX 已保存本地：{local_path}')
        return local_path

    async def _get_exec_machine_info(self, scenario: PerfScenarioModel):
        """获取执行机配置和 JMeter 工作目录。

        分布式（is_distributed=1）→ 返回 Master 控制机
        单机（is_distributed=0）  → 返回第一台单机压力机（machine_type=3）

        Args:
            scenario: 压测场景对象
        Returns:
            (machine: PerfConfigMachineModel, remote_dir: str)
            remote_dir 来自系统参数 PERF_WORKER_DATA_DIR，默认 /data/jmeter
        Raises:
            HTTPException 400 — 未配置对应类型的压力机
        """
        is_dist    = scenario.is_distributed == 1
        remote_dir = (await self.param_crud.get_param_value('PERF_WORKER_DATA_DIR', '/data/jmeter')).rstrip('/')

        if is_dist:
            machine = await self.machine_crud.get_master_machine()
            if not machine:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='未配置启用的 Master 控制机，请在配置管理-压力机中添加 machine_type=1 的记录')
        else:
            machines = await self.machine_crud.get_available_machines(limit=1, machine_type=3)
            if not machines:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail='未配置启用的单机压力机，请在配置管理-压力机中添加 machine_type=3 的记录')
            machine = machines[0]

        return machine, remote_dir

    async def _get_slave_workers(self, scenario: PerfScenarioModel) -> list:
        """获取分布式 Slave 压力机列表；单机模式返回空列表。

        Args:
            scenario: 压测场景对象（提供 is_distributed、node_count）
        Returns:
            list[PerfConfigMachineModel]，单机模式返回 []
        """
        if scenario.is_distributed != 1:
            return []
        node_limit = scenario.node_count or 1
        return await self.machine_crud.get_available_machines(limit=node_limit, machine_type=2)

    @staticmethod
    def _build_jmeter_cmd(
        jmx_name: str,
        remote_dir: str,
        workers: list,
        summariser_interval: str,
        background: bool,
        cmd_template: str | None = None,
    ) -> str:
        """构建 JMeter 非 GUI 执行命令字符串。

        联调（background=False）：前台阻塞执行，stdout 可被 SSH channel 实时读取
        压测（background=True）： nohup 后台执行，echo $! 输出 PID

        目录初始化：检查 results/logs/reports 是否存在再创建，避免重建已有目录。
        分布式模式自动追加 -R 和 -Dserver.rmi.ssl.disable=true 参数。

        Args:
            jmx_name:            JMX 原始文件名（含 .jmx 扩展名，与场景引用的脚本同名）
            remote_dir:          执行机上的 JMeter 工作目录（含 JMX 文件）
            workers:             Slave 压力机列表（PerfConfigMachineModel）；空列表=单机模式
            summariser_interval: JMeter summariser 打印间隔（秒），对应 -J summariser.interval
            background:          True=nohup 后台；False=前台阻塞
            cmd_template:        来自参数配置 JMETER_START_CMD 的命令模板，
                                 支持占位符 {jmx_file}、{summariser_interval}；
                                 为 None 时使用内置默认命令
        Returns:
            完整的 shell 命令字符串，可直接传给 SSH exec_command
        """
        # 目录初始化：只在不存在时创建；
        # reports/report 由 JMeter -e -o 生成，目录已存在时 JMeter 报错，每次必须清理；
        # jmeter.log 每次截断清空，避免新旧日志混淆导致日志收集偏移错位或完成状态误判
        dir_init = (
            f"cd '{remote_dir}' && "
            f"[ ! -d results ] && mkdir -p results; "
            f"[ ! -d logs ]   && mkdir -p logs; "
            f"[ ! -d reports ] && mkdir -p reports; "
            f"rm -rf ./reports/report; "
            f"> ./logs/jmeter.log; "
        )

        # 核心 JMeter 参数：优先使用参数配置中的命令模板，缺省时使用内置默认值
        if cmd_template:
            jmeter_args = cmd_template.format(
                jmx_file=jmx_name,
                summariser_interval=summariser_interval,
            )
        else:
            jmeter_args = (
                f"jmeter -n -t {jmx_name} "
                f"-l ./results/result.jtl -f "
                f"-j ./logs/jmeter.log "
                f"-J summariser.name=summary "
                f"-J summariser.interval={summariser_interval} "
                f"-e -o ./reports/report "
                f"-X"
            )

        # 分布式参数
        if workers:
            rmi_hosts = ','.join(
                f"{w.ip}:{w.rmi_port or 1099}" for w in workers
            )
            jmeter_args += f" -R {rmi_hosts} -Dserver.rmi.ssl.disable=true"

        # 用 bash -l 登录 shell 包裹，确保 SSH 非交互式会话也能加载完整 PATH（含 jmeter）；
        # background 模式：\\$! 在 Python 层产生 \$!，外层 /bin/sh 处理后传给 bash -l 的是 $!，
        # bash -l 正确展开为后台 nohup 进程的 PID
        if background:
            inner = (
                f"{dir_init}"
                f"nohup {jmeter_args} "
                f"> ./logs/jmeter_nohup.out 2>&1 & echo \\$!"
            )
            return f'bash -l -c "{inner}"'
        else:
            return f'bash -l -c "{dir_init}{jmeter_args}"'

    async def _upload_jmx_to_machine(
        self, local_path: str, machine, remote_dir: str, jmx_name: str,
        reuse_ssh=None,
    ) -> None:
        """将本地 JMX 文件通过 SFTP 上传到执行机的工作目录。

        远端目录不存在时自动创建（mkdir -p）。
        使用 asyncio.to_thread 包装同步 paramiko 操作，避免阻塞事件循环。
        reuse_ssh：传入已建立的 SSH 连接时直接复用，不重复握手，调用方负责关闭。

        Args:
            local_path: 本地 JMX 文件绝对路径
            machine:    目标执行机（PerfConfigMachineModel）
            remote_dir: 执行机上的目标目录（PERF_WORKER_DATA_DIR）
            jmx_name:   JMX 原始文件名（含 .jmx 扩展名），用作远端文件名
            reuse_ssh:  可选，已建立的 SSH 连接；为 None 时自行建连并在结束后关闭
        Raises:
            RuntimeError — SSH 连接或 SFTP 上传失败
        """
        remote_file = f'{remote_dir}/{jmx_name}'
        own_conn = reuse_ssh is None

        def _sync_upload() -> str:
            """返回操作说明：'skipped:<reason>' 表示跳过，'uploaded' 表示已上传。"""
            ssh = None
            try:
                ssh = reuse_ssh if not own_conn else ShellOperationUtils.get_ssh_client(
                    machine.ip, target_port=machine.ssh_port or 22,
                    credential=_build_credential(machine))
                ShellOperationUtils.execute_remote_command(ssh, f"mkdir -p '{remote_dir}'")

                # MD5 预检：内容未变时跳过上传，避免每次重传相同文件
                with open(local_path, 'rb') as fp:
                    local_md5 = hashlib.md5(fp.read()).hexdigest()
                _, md5_out, _ = ShellOperationUtils.execute_remote_command(
                    ssh, f"md5sum '{remote_file}' 2>/dev/null | awk '{{print $1}}'"
                )
                remote_md5 = (md5_out or '').strip()
                if remote_md5 == local_md5:
                    msg = f'JMX 内容未变（MD5={local_md5[:8]}...），跳过上传，直接使用压力机现有文件'
                    logger.info(f'[Upload] {msg}: {remote_file}')
                    return f'skipped:{msg}'

                # 内容有变（或远端文件不存在）：强制全量覆盖上传
                ShellOperationUtils.upload_file_via_sftp(
                    ssh, local_path, remote_file,
                    resume=False,
                    progress_label=f'{machine.ip} {jmx_name}',
                )
                return 'uploaded'
            except Exception as e:
                logger.exception(f'SFTP 上传 JMX 失败 → {machine.ip}')
                raise RuntimeError(f'上传 JMX 到 {machine.ip} 失败：{e}') from e
            finally:
                if own_conn and ssh:
                    try: ssh.close()
                    except Exception: pass

        try:
            return await asyncio.to_thread(_sync_upload)
        except RuntimeError:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f'SFTP 上传异常：{e}')

    async def _download_jmx(self, scenario: PerfScenarioModel) -> bytes:
        """从 MinIO 下载场景关联的 JMX 文件 bytes。

        始终从原始模板下载，不使用本地缓存，保证每次操作基于干净的脚本。

        Args:
            scenario: 压测场景 ORM 对象（含 script_id）
        Returns:
            JMX 文件原始 bytes
        Raises:
            400 JMX 脚本文件不存在
            500 MinIO 下载失败
        """
        file_obj = await self.file_crud.get_by_id_crud(scenario.script_id)
        if not file_obj or not file_obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail='JMX 脚本文件不存在，请重新关联')
        try:
            from config import config as app_config
            return await MinioClient.get_object_bytes(app_config.MINIO_BUCKET, file_obj.object_key)
        except Exception as e:
            logger.error(f'MinIO 下载 JMX 失败 scenario_id={scenario.id}：{fmt_cloudflare_html_resp(e, "请检查 MinIO 地址或网络配置")}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f'下载 JMX 脚本失败：{fmt_cloudflare_html_resp(e, "请检查 MinIO 地址或网络配置")}')

    async def _get_data_file_statuses(self, csv_file_names: list) -> dict:
        """批量查询 JMX 引用的 CSV 数据文件在 DB 中的状态。

        支持三种 CSV 文件名格式：
          1. 普通文件名：login.csv
          2. __P 表达式：${__P(csv.path,login.csv)} → 逗号后取默认文件名
          3. 写死路径：/data/jmeter/login.csv 或 C:\\data\\login.csv → 取最后段文件名

        返回字段中，expression 仅在原始名非普通文件名时存在，供前端展示原始表达式/路径。

        状态优先级：不存在(danger) > 未引用(warning) > 未分发(info) > 已共享/已分割(success)
        使用 IN 批量查询，避免 N+1 DB 往返。
        """
        def _extract_filename(raw: str) -> tuple[str, str | None]:
            """从原始 CSV 名称中提取实际文件名，返回 (文件名, 原始表达式或None)。"""
            s = raw.strip()
            # __P 表达式：${__P(csv.path,xxx.csv)} 或 ${__P(csv.path, xxx.csv)}
            if s.startswith('${__P(') and ',' in s:
                after_comma = s.split(',', 1)[1]
                filename = after_comma.rstrip(')}').strip()
                return filename, s
            # 写死路径：含 / 或 \
            if '/' in s or '\\' in s:
                import posixpath, ntpath
                filename = posixpath.basename(s.replace('\\', '/'))
                return filename, s
            return s, None

        if not csv_file_names:
            return {"total": 0, "files": []}

        parsed = [_extract_filename(n) for n in csv_file_names]
        lookup_names = [p[0] for p in parsed]

        stmt = (
            select(PerfFileModel)
            .where(and_(
                PerfFileModel.file_name.in_(lookup_names),
                PerfFileModel.enabled_flag == 1,
                PerfFileModel.upload_status == 1,
            ))
        )
        result  = await self.db.execute(stmt)
        db_map  = {obj.file_name: obj for obj in result.scalars().all()}

        files = []
        for display_name, expression in parsed:
            obj  = db_map.get(display_name)
            base = {"name": display_name}
            if expression:
                base["expression"] = expression
            if obj is None:
                files.append({**base, "status": "不存在", "status_type": "danger",
                              "ref_status": None, "dist_status": None})
            elif obj.ref_status == 0:
                files.append({**base, "status": "未引用", "status_type": "warning",
                              "ref_status": obj.ref_status, "dist_status": obj.dist_status})
            elif obj.dist_status == 0:
                files.append({**base, "status": "未分发", "status_type": "primary",
                              "ref_status": obj.ref_status, "dist_status": obj.dist_status})
            elif obj.dist_status == 1:
                files.append({**base, "status": "已共享", "status_type": "success",
                              "ref_status": obj.ref_status, "dist_status": obj.dist_status})
            elif obj.dist_status == 2:
                files.append({**base, "status": "已分割", "status_type": "success",
                              "ref_status": obj.ref_status, "dist_status": obj.dist_status})
            else:
                files.append({**base, "status": "未知", "status_type": "info",
                              "ref_status": obj.ref_status, "dist_status": obj.dist_status})
        return {"total": len(files), "files": files}

    @staticmethod
    async def _check_influxdb_connectivity(url: str, timeout: float = 3.0) -> tuple:
        """对 InfluxDB URL 进行 TCP 连通性探测（从后端服务器发起）。

        解析 URL 中的 host 和 port，尝试建立 TCP 连接，3s 超时。
        """
        import urllib.parse
        if not url:
            return False, "URL 为空"
        try:
            parsed = urllib.parse.urlparse(url)
            host   = parsed.hostname
            port   = parsed.port or (443 if parsed.scheme == "https" else 8086)
            if not host:
                return False, f"无法解析 host：{url}"
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True, f"连通（{host}:{port}）"
        except asyncio.TimeoutError:
            return False, f"连接超时（{timeout}s）"
        except Exception as e:
            return False, f"连接失败：{e}"

    async def _build_precheck_config(self, scenario: PerfScenarioModel) -> dict:
        """读取压测前置准备开关配置（非系统参数），展示是否清理进程/日志。"""
        pid_val = await self.param_crud.get_param_value('IS_CLEAR_JMETER_PID', 'true')
        log_val = await self.param_crud.get_param_value('IS_CLEAR_JMETER_LOG', 'true')
        is_dist = scenario.is_distributed == 1
        return {
            "is_distributed": is_dist,
            "items": [
                {
                    "label":      "清理 JMeter 进程",
                    "key":        "IS_CLEAR_JMETER_PID",
                    "enabled":    (pid_val or 'true').lower().strip() == 'true',
                    "script":     "ssh_kill_jmeter.sh",
                    "applicable": is_dist,
                },
                {
                    "label":      "清理日志/数据文件",
                    "key":        "IS_CLEAR_JMETER_LOG",
                    "enabled":    (log_val or 'true').lower().strip() == 'true',
                    "script":     "ssh_remve_csv_log",
                    "applicable": is_dist,
                },
            ],
        }

    async def _check_service_connections(self, scenario: PerfScenarioModel) -> dict:
        """检测 Master/Worker 与 MinIO、JMeter 的连通性（SSH 远端探测，4 项并发执行）。

        单机模式下并发的 _check_workers_to_minio 和 _check_jmeter_running 会连接同一批
        压力机，为避免重复建立 SSH 连接，gather 前预先建立 ssh_pool 并复用。
        """
        from config import config as app_config

        endpoint = getattr(app_config, 'MINIO_ENDPOINT', '') or ''
        minio_secure = getattr(app_config, 'MINIO_SECURE', False) or False
        # IP + 端口访问Minio
        if ':' in endpoint:
            minio_host, _p = endpoint.rsplit(':', 1)
            minio_port = int(_p) if _p.isdigit() else 9000
        # 通过域名访问Minio
        else:
            minio_host, minio_port = endpoint or 'localhost', None

        # 解析使用的协议
        scheme = 'https' if minio_secure else 'http'
        # 构造合规Minio访问URL地址
        if minio_port is not None:
            minio_url = f"{scheme}://{minio_host}:{minio_port}/"
        else:
            minio_url = f"{scheme}://{minio_host}/"

        is_dist    = scenario.is_distributed == 1
        node_limit = (scenario.node_count or 1) if is_dist else 1
        master     = await self.machine_crud.get_master_machine()
        workers    = await self.machine_crud.get_available_machines(limit=node_limit, machine_type=2 if is_dist else 3)

        if not master and is_dist:
            items = [
                {"label": lbl, "ok": False, "detail": "未配置 Master 控制机", "sub": []}
                for lbl in ["Master访问MinIO", "Worker/单机访问MinIO", "Master访问Worker", "JMeter启动状态"]
            ]
            return {"is_distributed": is_dist, "total": len(items), "items": items}

        # 单机模式下预建 SSH 连接池，_check_workers_to_minio / _check_jmeter_running 共享复用，
        # 避免两个并发任务对同一压力机各自建立独立连接
        ssh_pool: dict = {}
        if not is_dist and workers:
            def _connect_worker(w):
                try:
                    conn = ShellOperationUtils.get_ssh_client(
                        w.ip, target_port=w.ssh_port or 22, max_retries=1, retry_interval=1.0,
                        credential=_build_credential(w)
                    )
                    return w.ip, conn
                except Exception:
                    return w.ip, None

            pairs = await asyncio.gather(
                *[asyncio.to_thread(_connect_worker, w) for w in workers]
            )
            for ip, conn in pairs:
                if conn is not None:
                    ssh_pool[ip] = conn

        try:
            results = await asyncio.gather(
                asyncio.to_thread(_check_master_to_minio,      master, minio_url, is_dist),
                asyncio.to_thread(_check_workers_to_minio,     master, workers, minio_url, is_dist, ssh_pool),
                asyncio.to_thread(_check_master_to_workers, master, workers, is_dist),
                asyncio.to_thread(_check_jmeter_running,    master, workers, is_dist, ssh_pool),
                return_exceptions=True,
            )
        finally:
            for conn in ssh_pool.values():
                try: conn.close()
                except Exception: pass

        labels = ["Master访问MinIO", "Worker/单机访问MinIO", "Master访问Worker", "JMeter启动状态"]
        items  = []
        for lbl, r in zip(labels, results):
            if isinstance(r, Exception):
                items.append({"label": lbl, "ok": False, "detail": str(r), "sub": []})
            else:
                items.append({"label": lbl, **r})

        return {"is_distributed": is_dist, "total": len(items), "items": items}

    # ──────────────────── 工具方法 ────────────────────

    def _get_inspect_param_key(self, thread_type: str, test_type: Optional[str]) -> str:
        """根据线程组类型字典值和测试类型确定联调参数配置的 param_key。"""
        if thread_type == '2':
            return self._KEY_STEPPING
        if thread_type == '3':
            return self._KEY_ULTIMATE
        if test_type == self._LOAD_TEST_TYPE_VALUE:
            return self._KEY_LOAD
        return self._KEY_BASE

    @staticmethod
    def _config_to_db_params(config: PerfScenarioConfigModel) -> dict:
        """将子配置 ORM 对象转换为 apply_jmx_by_type 所需的 db_params 字典。

        字段名与 PerfScenarioConfigModel 保持一致，apply_jmx_by_type 内部完成到 JMX 字段名的映射。
        """
        base = {
            'thread_count':  config.thread_count,
            'ramp_up_time':  config.ramp_up_time,
            'loop_count':    config.loop_count,
            'loop_forever':  bool(config.loop_forever),
            'duration':      config.duration,
            'startup_delay': config.startup_delay,
        }
        if config.thread_type == '2':
            base.update({
                'step_initial_delay':      config.step_initial_delay,
                'step_start_users_count':  config.step_start_users_count,
                'step_start_users_burst':  config.step_start_users_burst,
                'step_start_users_period': config.step_start_users_period,
                'step_stop_users_count':   config.step_stop_users_count,
                'step_stop_users_period':  config.step_stop_users_period,
                'step_flight_time':        config.step_flight_time,
                'step_ramp_up':            config.step_ramp_up,
            })
        elif config.thread_type == '3':
            base['ultimate_rows'] = config.ultimate_rows or []
        return base


# ====================== 压测停止工具函数 ======================

async def stop_running_scenario(scenario_id: int, user_id: int, db: AsyncSession) -> None:
    """强制终止正在运行的压测场景并还原相关状态。

    步骤：
      1. 加载场景，校验 status=2（进行中），非进行中则跳过
      2. 立即更新 scenario.status=4（已取消），缩小与日志收集任务的竞争窗口
      3. 从 Redis 读取 JMeter PID，SSH 到执行机执行 kill
      4. 移除 perf_log_collector APScheduler 轮询任务
      5. 清理 Redis 中该场景的所有日志/PID/偏移键

    Args:
        scenario_id: 压测场景主键 ID
        user_id:     操作人 ID
        db:          当前异步数据库会话
    """
    from app.db import get_redis_pool
    from app.utils.perf_log_collector import (
        _pid_key, _log_key, _offset_key, _evicted_key, _remove_job,
    )

    scenario_crud = BaseCRUD(PerfScenarioModel, db)
    scenario = await scenario_crud.get_by_id_crud(scenario_id)

    if not scenario or scenario.status != 2:
        # 场景不在进行中，无需操作
        logger.info(f"[StopScenario] 场景不在进行中，跳过 scenario_id={scenario_id} status={getattr(scenario, 'status', None)}")
        return

    redis = get_redis_pool().get_redis()

    # ── 1. 先更新场景状态为已取消，防止日志收集任务在 kill 完成前误触发报告收集 ──
    cancel_payload: dict = {'status': 4, 'updated_by': user_id}
    if scenario.estimated_duration and scenario.executed_at:
        elapsed = (datetime.now() - scenario.executed_at).total_seconds()
        cancel_payload['progress'] = min(99, int(elapsed / scenario.estimated_duration * 100))
    await scenario_crud.update_crud(scenario_id, cancel_payload)

    # ── 2. SSH kill JMeter 进程 ────────────────────────────────────────────
    pid_raw = await redis.get(_pid_key(scenario_id))
    pid = (pid_raw.decode() if isinstance(pid_raw, bytes) else (pid_raw or '')).strip()

    # 不论是否有 PID 缓存，都尝试 SSH 到执行机终止 JMeter，
    # 避免 PID 未写入 Redis 时进程残留（此场景即"强制停止无响应"的根因）
    try:
        machine_crud = PerfMachineCRUD(db)

        if scenario.is_distributed == 1:
            machine = await machine_crud.get_master_machine()
        else:
            machines = await machine_crud.get_available_machines(limit=1, machine_type=3)
            machine = machines[0] if machines else None

        if machine:
            if pid.isdigit():
                # PID 已知：先 kill -0 检查进程是否存活，存活才执行 kill 链；已结束则跳过
                # 详见 commands.KILL_JMETER_BY_PID / KILL_JMETER_BY_NAME
                kill_cmd = (
                    f"kill -0 {pid} 2>/dev/null "
                    f"&& (pkill -9 -P {pid} 2>/dev/null; pkill -9 -f ApacheJMeter.jar 2>/dev/null; kill -9 {pid} 2>/dev/null; echo 'killed') "
                    f"|| echo 'jmeter_already_exited'; echo done"
                )
            else:
                # PID 未缓存：先 pgrep 确认是否有 JMeter 进程，有才 pkill，无则跳过
                # 详见 commands.KILL_JMETER_BY_PID / KILL_JMETER_BY_NAME
                kill_cmd = (
                    "pgrep -f ApacheJMeter.jar > /dev/null 2>&1 "
                    "&& pkill -9 -f ApacheJMeter.jar 2>/dev/null && echo 'killed' "
                    "|| echo 'no_jmeter_process'; echo done"
                )

            def _ssh_kill() -> None:
                ssh = None
                try:
                    ssh = ShellOperationUtils.get_ssh_client(
                        machine.ip, target_port=machine.ssh_port or 22,
                        credential=_build_credential(machine),
                    )
                    ShellOperationUtils.execute_remote_command(ssh, kill_cmd)
                finally:
                    if ssh:
                        try:
                            ssh.close()
                        except Exception:
                            pass

            await asyncio.to_thread(_ssh_kill)
            logger.info(f"[StopScenario] 已发送 kill 信号 scenario_id={scenario_id} PID={pid or '无(按名称终止)'}")
        else:
            logger.warning(f"[StopScenario] 未找到执行机，跳过 kill scenario_id={scenario_id}")
    except Exception as e:
        logger.warning(f"[StopScenario] kill 异常 scenario_id={scenario_id} PID={pid}: {e}")

    # ── 3. 停止日志收集轮询任务 ───────────────────────────────────────────
    _remove_job(scenario_id)

    # ── 4. 清理 Redis 键 ──────────────────────────────────────────────────
    for key_fn in [_pid_key, _log_key, _offset_key, _evicted_key]:
        try:
            await redis.delete(key_fn(scenario_id))
        except Exception:
            pass

    logger.info(f"[StopScenario] 场景已强制停止 scenario_id={scenario_id}")

