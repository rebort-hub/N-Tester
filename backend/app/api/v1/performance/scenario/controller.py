#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from app.corelibs.logger import logger
from app.db.sqlalchemy import get_db
from .schema import (
    PerfScenarioConfigCreateReqSchema, PerfScenarioConfigUpdateReqSchema,
    PerfScenarioCreateReqSchema, PerfScenarioUpdateReqSchema,
    ScenarioExecuteReqSchema, ConfigSyncStatsReqSchema,
    ScenarioUpdateStatusReqSchema,
)
from .service import PerfScenarioConfigService, PerfScenarioService, ScenarioExecuteService, stop_running_scenario

router = APIRouter(prefix="/performance/scenario", tags=["性能测试 - 压测场景"])

"""
=========================================================================
性能测试 - 压测场景 Controller
API 路由入口：
----------------------------压测场景接口------------------------
POST   /add                                  新增压测场景
GET    /list                                 查询压测场景列表（分页）
PUT    /update/{scenario_id}                 更新压测场景
DELETE /delete/{scenario_id}                 删除压测场景
PUT    /updateStatus                         更新场景状态（如：确认联调通过→待开始）
POST   /{scenario_id}/config/add             新增场景子配置
GET    /{scenario_id}/config/list            查询场景子配置列表
PUT    /{scenario_id}/config/update/{id}     更新场景子配置
DELETE /{scenario_id}/config/delete/{id}     删除场景子配置
POST   /config/sync_stats           切换子配置状态并同步场景并发数与预计耗时
----------------------------联调 / 执行接口------------------------
GET    /{scenario_id}/inspect                SSE 流式检查预览 JMX 摘要信息
POST   /{scenario_id}/execute                SSE 流式联调（action=inspect）/ 正式执行（action=execute）
GET    /{scenario_id}/monitor                SSE 实时监控：推送 Redis 日志行 + 进度 + 心跳
POST   /{scenario_id}/stop                   强制停止正在运行的压测任务
=========================================================================
"""

# ========================= 压测场景 =========================

@router.post("/add", summary="新增压测场景")
async def create_scenario(
    data: PerfScenarioCreateReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await PerfScenarioService(db).create(data, user_id)
    return success_response(data=result, message="新建成功")


@router.get("/list", summary="查询压测场景列表（分页）")
async def list_scenarios(
    name:          Optional[str] = Query(None, description="场景名称，模糊匹配"),
    code:          Optional[str] = Query(None, description="场景编号，精确匹配"),
    script_name:   Optional[str] = Query(None, description="脚本名称，模糊匹配"),
    status:        Optional[int] = Query(None, description="执行状态（整数：0待联调 1待开始 2进行中 3已完成 4已取消 5失败）"),
    test_type:     Optional[str] = Query(None, description="测试类型（字典值）"),
    created_by:    Optional[int] = Query(None, description="创建人 ID"),
    page:          int           = Query(1,  ge=1,        description="页码"),
    page_size:     int           = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await PerfScenarioService(db).get_list(
        page, page_size, name, code, script_name, status, test_type, created_by
    )
    return success_response(data=result)


@router.put("/update/{scenario_id}", summary="更新压测场景")
async def update_scenario(
    scenario_id: int,
    data: PerfScenarioUpdateReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await PerfScenarioService(db).update(scenario_id, data, user_id)
    return success_response(data=[], message="更新成功")


@router.delete("/delete/{scenario_id}", summary="删除压测场景（软删除，同步删除子配置）")
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await PerfScenarioService(db).delete(scenario_id, user_id)
    return success_response(data=[], message="删除成功")


@router.put("/updateStatus", summary="更新压测场景状态")
async def update_scenario_status(
    data: ScenarioUpdateStatusReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    更新场景状态。当前支持：
      - status=1：确认联调通过，将场景从【待联调(0)】更新为【待开始(1)】，status=1 时幂等
    """
    await PerfScenarioService(db).update_scenario_status(data.scenario_id, data.status, user_id)
    return success_response(data=[], message="状态更新成功")


# ========================= 子配置 =========================

@router.post("/{scenario_id}/config/add", summary="新增场景子配置")
async def create_config(
    scenario_id: int,
    data: PerfScenarioConfigCreateReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await PerfScenarioConfigService(db).create(scenario_id, data, user_id)
    return success_response(data=result, message="新建成功")


@router.get("/{scenario_id}/config/list", summary="查询场景子配置列表")
async def list_configs(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    result = await PerfScenarioConfigService(db).get_list(scenario_id)
    return success_response(data=result)


@router.put("/{scenario_id}/config/update/{config_id}", summary="更新场景子配置")
async def update_config(
    scenario_id: int,
    config_id: int,
    data: PerfScenarioConfigUpdateReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await PerfScenarioConfigService(db).update(scenario_id, config_id, data, user_id)
    return success_response(data=[], message="更新成功")


@router.delete("/{scenario_id}/config/delete/{config_id}", summary="删除场景子配置")
async def delete_config(
    scenario_id: int,
    config_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    await PerfScenarioConfigService(db).delete(scenario_id, config_id, user_id)
    return success_response(data=[], message="删除成功")


@router.post("/config/sync_stats", summary="切换子配置状态并同步场景并发数与预计耗时")
async def sync_config_stats(
    data: ConfigSyncStatsReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    切换子配置启用/禁用状态，并在同一次调用内完成：
      - 互斥类型（'1'/'2'/'3'）的同类配置自动禁用
      - 场景总并发数重新聚合
      - 预计耗时重新估算并写回场景主表
    返回 { configs, concurrent_count, estimated_duration, estimated_note }
    """
    result = await PerfScenarioConfigService(db).sync_stats(data, user_id)
    return success_response(data=result)


# ========================= 联调 / 执行 =========================

@router.get("/{scenario_id}/inspect", summary="SSE 流式检查预览 JMX 摘要信息接口")
async def inspect_preview(
    scenario_id: int, db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),):
    """
    SSE 流式联调检查接口，依次推送：
      - 场景加载进度
      - JMX 全量摘要（线程组 / 用户变量 / 监听器 / CSV 文件列表等）
      - 将要应用的联调参数预览（来自 perf_config_params 预置配置）
    全程只读，不修改任何数据，不推送到压力机。
    """
    svc = ScenarioExecuteService(db)

    async def event_gen():
        try:
            async for chunk in svc.inspect_sse(scenario_id):
                yield chunk
        except Exception as e:
            logger.error(f"inspect SSE 事件流异常 scenario_id={scenario_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{scenario_id}/execute", summary="SSE 流式联调 / 正式执行压测")
async def execute_scenario(
    scenario_id: int,
    data: ScenarioExecuteReqSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    SSE 流式接口，分两种模式推送三阶段进度事件：

    **action=inspect**（启动联调）
      - 校验：场景 status 必须为 0（待联调），status=2 时拒绝
      - 阶段1 注入联调参数（从 perf_config_params 读取预置调试配置覆写 JMX）
      - 阶段2 上传 JMX 到执行机或者Master机
      - 阶段3 前台阻塞运行 JMeter，实时推送 stdout 日志行；
              exit_code=0 → status=1（待开始）；否则 status=0 + error 事件

    **action=execute**（正式执行压测）
      - 校验：场景 status 必须为 1（待开始，即已完成联调）
      - 阶段1 注入正式参数（子配置线程数/时长等）
      - 阶段2 上传 JMX 到执行机
      - 阶段3 nohup 后台启动 JMeter，5s 后获取 PID 存入 Redis；
              status → 2（进行中），启动 APScheduler 日志收集任务

    SSE 事件格式（data 字段为 JSON）：
      {"type": "stage",    "stage": 1|2|3, "message": "阶段描述"}
      {"type": "log",      "message": "日志行"}
      {"type": "progress", "value": 0-100}
      {"type": "done",     "message": "操作成功"}
      {"type": "error",    "message": "错误详情"}
    """
    svc = ScenarioExecuteService(db)

    async def event_gen():
        try:
            async for chunk in svc.execute_sse(scenario_id, data.action):
                yield chunk
        except Exception as e:
            logger.error(f"execute SSE 事件流异常 scenario_id={scenario_id} action={data.action}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{scenario_id}/monitor", summary="SSE 实时压测监控接口")
async def monitor_scenario(
    scenario_id: int,
    offset: int = Query(0, ge=0, description="从 Redis 日志列表第几条开始读取（断线续传用），默认 0"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """
    SSE 长连接接口，用于正式压测执行期间的实时监控页面。推送 Redis 日志行 + 进度 + 心跳。

    工作机制：
      - 循环从 Redis List（perf:jmeter_log:{id}）按 offset 增量拉取 JMeter 日志行
      - 每批日志推送 log 事件，同时推送 progress 事件（来自 DB perf_scenarios.progress）
      - 无新日志时等待 JMETER_MONITOR_HEARTBEAT 秒后推送 ping 心跳，防止连接超时
      - 场景 status ≠ 2（进行中）时自动终止：推送最后一批日志 + done/error 事件后关闭流

    客户端断线重连：
      - 重连时携带上次收到的最大 offset 参数，即可从断点续传，不重复推送旧日志

    SSE 事件格式（data 字段为 JSON）：
      {"type": "log",      "message": "jmeter.log 日志行", "offset": N}
      {"type": "progress", "value": 0-100}
      {"type": "ping"}
      {"type": "done",     "message": "压测已完成"}
      {"type": "error",    "message": "错误详情（场景失败/取消）"}
    """
    svc = ScenarioExecuteService(db)

    async def event_gen():
        try:
            async for chunk in svc.monitor_sse(scenario_id, offset):
                yield chunk
        except Exception as e:
            logger.error(f"monitor SSE 事件流异常 scenario_id={scenario_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{scenario_id}/stop", summary="强制停止正在运行的压测任务")
async def stop_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """强制终止压测任务：kill JMeter 进程、更新场景 status=4（已取消）、停止日志收集、清理 Redis。"""
    await stop_running_scenario(scenario_id, user_id, db)
    return success_response(data=[], message="压测任务已停止")