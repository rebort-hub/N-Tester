#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
"""
JMeter 实时日志收集任务 —— 由 APScheduler 以 AsyncIOExecutor 调度。

每 JMETER_LOG_POLL_INTERVAL 秒执行一次，职责：
  1. SSH 增量读取 jmeter_nohup.out 新增行（summariser 汇总数据）→ 追加到 Redis List
  2. Redis List 超过 _MAX_LOG_LINES（10000）时从头裁剪（LTRIM），
     累计裁剪行数记录到 perf:jmeter_levicted:{id}，
     供 monitor_sse 修正客户端 offset，保证断线重连不错位
  3. 基于 elapsed/estimated_duration 更新 perf_scenarios.progress
  4. kill -0 {pid} 检测 JMeter 进程：
     - 进程存活 → 继续下一轮
     - 进程结束 → 读完剩余日志 → 停止任务 → 更新场景 status=3/progress=100

Redis 键：
  perf:jmeter_log:{id}      List，当前保留的日志行（滑动窗口，最多 _MAX_LOG_LINES 行）
  perf:jmeter_foffset:{id}  Integer，已读取的文件行偏移（tail -n +N 的 N）
  perf:jmeter_pid:{id}      String，JMeter 进程 PID
  perf:jmeter_levicted:{id} Integer，累计从 List 头部裁剪掉的行数（用于 offset 修正）
所有键 TTL=24h。
"""
import asyncio
import threading
from datetime import datetime

from app.corelibs.logger import logger

# Redis List 最大保留行数；超出时从头裁剪，保留最新的 N 行
_MAX_LOG_LINES = 10000


# ── Redis 键模板 ────────────────────────────────────────────────────────────
def _log_key(scenario_id: int) -> str:
    return f'perf:jmeter_log:{scenario_id}'

def _offset_key(scenario_id: int) -> str:
    return f'perf:jmeter_foffset:{scenario_id}'

def _pid_key(scenario_id: int) -> str:
    return f'perf:jmeter_pid:{scenario_id}'

def _evicted_key(scenario_id: int) -> str:
    """累计从 Redis List 头部裁剪掉的行数，供 monitor_sse 修正客户端 offset。"""
    return f'perf:jmeter_levicted:{scenario_id}'


# ── SSH 连接池（per-scenario，避免每轮 LogCollector 都重新握手）────────────────
_ssh_pool: dict = {}
_ssh_pool_lock  = threading.Lock()


def _get_or_connect(scenario_id: int, ip: str, port: int, credential: dict):
    """从连接池获取或新建 SSH 连接；连接断开时自动重连。"""
    from app.utils.oper_shell import ShellOperationUtils
    with _ssh_pool_lock:
        ssh = _ssh_pool.get(scenario_id)
        if ssh is not None:
            try:
                transport = ssh.get_transport()
                if transport and transport.is_active():
                    return ssh
            except Exception:
                pass
            # 连接已断开，移除旧实例
            try: ssh.close()
            except Exception: pass
            del _ssh_pool[scenario_id]
        ssh = ShellOperationUtils.get_ssh_client(ip, target_port=port, credential=credential)
        _ssh_pool[scenario_id] = ssh
        return ssh


def _release_connection(scenario_id: int) -> None:
    """关闭并移除连接池中的连接（场景结束或连接失败时调用）。"""
    with _ssh_pool_lock:
        ssh = _ssh_pool.pop(scenario_id, None)
    if ssh:
        try: ssh.close()
        except Exception: pass


async def _check_jmeter_completion(
    scenario_id: int,
    remote_dir: str,
    exec_machine_ip: str,
    exec_machine_ssh_port: int,
    target_threads: int,
    estimated_duration: 'int | None',
    executed_at: 'datetime | None',
    ssh_user: 'str | None',
    ssh_password: 'str | None',
) -> 'tuple[int, str | None]':
    """
    方法用途：进程结束后 SSH 到执行机读取日志文件，综合判断本次压测是成功(3)还是失败(5)。

    核心业务链路：
      1. 通过一条 SSH 命令读取：jmeter.log 是否存在、result.jtl 是否存在、
         jmeter.log 后50行内容、jmeter_nohup.out 后20行内容
      2. 失败条件1：jmeter.log 不存在 → 失败（JMeter 未正常启动）
      3. 失败条件2：result.jtl 不存在 → 失败（压测未执行到写结果阶段）
      4. 成功条件1：jmeter.log 后50行含 "Notifying test listeners of end of test" → 已完成
         （同时校验实际运行时间不低于预计耗时50%，否则仍判失败）
      5. 成功条件2：无结束标志但 Active=0 且 Finished=目标总线程数 → 已完成
      6. 其余情形（Active!=0 / Finished 不符 / 时间过短）→ 失败，拼接错误信息

    Args:
        scenario_id:           压测场景 ID，用于日志标识和 SSH 连接池 key
        remote_dir:            JMeter 工作目录（含 logs/、results/ 子目录）
        exec_machine_ip:       执行机 IP
        exec_machine_ssh_port: 执行机 SSH 端口
        target_threads:        目标总线程数（单机=各启用配置 thread_count 之和；分布式×node_count）
        estimated_duration:    场景预计总耗时（秒），None 时跳过时间条件检测
        executed_at:           压测开始时间，用于计算实际运行时长
        ssh_user:              SSH 用户名（可为 None）
        ssh_password:          SSH 密码（可为 None）
    Returns:
        tuple[int, str | None]：
          (3, None)          — 已完成（压测成功）
          (5, error_msg)     — 失败，error_msg 为具体失败原因
    """
    import re as _re

    # 一条 SSH 命令一次读取所有判断所需信息，减少 SSH 往返次数
    from app.common.commands import JMETER_COMPLETION_CHECK
    cmd = JMETER_COMPLETION_CHECK.format(remote_dir=remote_dir)

    def _ssh_check() -> 'str | None':
        from app.utils.oper_shell import ShellOperationUtils
        try:
            credential: dict = {}
            if ssh_user:     credential['ssh_user']     = ssh_user
            if ssh_password: credential['ssh_password'] = ssh_password
            ssh = _get_or_connect(scenario_id, exec_machine_ip, exec_machine_ssh_port, credential)
            _, out, _ = ShellOperationUtils.execute_remote_command(ssh, cmd)
            return out
        except Exception as e:
            logger.warning(f'[LogCollector] scenario={scenario_id} 完成状态检测SSH失败：{e}')
            return None

    output = await asyncio.to_thread(_ssh_check)
    if not output:
        return 5, '压测结果检测失败（SSH连接错误），默认标记为失败'

    # 按分隔标记拆分各段内容
    def _extract(start_m: str, end_m: str) -> str:
        s = output.find(f'---{start_m}---')
        e = output.find(f'---{end_m}---')
        if s == -1:
            return ''
        return output[s + len(f'---{start_m}---'): e if e != -1 else None].strip()

    log_exists = _extract('LOG_EXISTS',  'JTL_EXISTS').lower() == 'yes'
    jtl_exists = _extract('JTL_EXISTS',  'LOG_TAIL').lower()   == 'yes'
    log_tail   = _extract('LOG_TAIL',    'NOHUP_TAIL')
    nohup_tail = _extract('NOHUP_TAIL',  'END')

    # 失败条件1：jmeter.log 不存在（JMeter 根本没有正常启动）
    if not log_exists:
        err = 'JMeter运行失败：未生成 jmeter.log（JMeter可能未正常启动）'
        if nohup_tail:
            err += f'\n\njmeter_nohup.out:\n{nohup_tail}'
        logger.info(f'[LogCollector] scenario={scenario_id} 完成判定→失败：jmeter.log 不存在')
        return 5, err

    # 失败条件2：result.jtl 不存在（压测未执行到写结果阶段）
    if not jtl_exists:
        err = 'JMeter运行失败：未生成 result.jtl（压测未执行或启动即失败）'
        if nohup_tail:
            err += f'\n\njmeter_nohup.out:\n{nohup_tail}'
        logger.info(f'[LogCollector] scenario={scenario_id} 完成判定→失败：result.jtl 不存在')
        return 5, err

    # 解析后50行中最后一条含 Active/Started/Finished 的 summary 行
    has_end_marker = 'Notifying test listeners of end of test' in log_tail
    last_active    = None
    last_finished  = None
    for line in reversed(log_tail.splitlines()):
        m = _re.search(r'Active:\s*(\d+)\s+Started:\s*(\d+)\s+Finished:\s*(\d+)', line)
        if m:
            last_active   = int(m.group(1))
            last_finished = int(m.group(3))
            break

    logger.info(
        f'[LogCollector] scenario={scenario_id} 完成检测数据：'
        f'has_end_marker={has_end_marker} '
        f'last_active={last_active} last_finished={last_finished} target_threads={target_threads}'
    )

    # 成功条件1：有正常结束标志（同时校验失败条件4：时间严重偏短）
    if has_end_marker:
        if executed_at and estimated_duration:
            elapsed = (datetime.now() - executed_at).total_seconds()
            if elapsed < estimated_duration * 0.5:
                logger.info(
                    f'[LogCollector] scenario={scenario_id} 完成判定→失败：'
                    f'有结束标志但运行时间({elapsed:.0f}s)<预计耗时50%({estimated_duration * 0.5:.0f}s)'
                )
                return 5, (
                    f'JMeter虽有结束标志，但实际运行时间（{elapsed:.0f}s）'
                    f'不足预计耗时的50%（{estimated_duration * 0.5:.0f}s），疑似异常提前结束'
                )
        logger.info(f'[LogCollector] scenario={scenario_id} 完成判定→已完成：检测到正常结束标志(Notifying test listeners of end of test)')
        return 3, None

    # 成功条件2：无结束标志但 Active=0 且 Finished=目标线程数（正常跑完无标志情形）
    if last_active == 0 and target_threads > 0 and last_finished == target_threads:
        logger.info(
            f'[LogCollector] scenario={scenario_id} 完成判定→已完成：'
            f'Active=0 且 Finished({last_finished})==目标线程数({target_threads})'
        )
        return 3, None

    # 以下均为失败情形，拼接详细原因
    err_parts = ['JMeter进程异常退出（jmeter.log 中未检测到正常结束标志）']
    if last_active is not None:
        err_parts.append(
            f'最后线程状态：Active={last_active}，Finished={last_finished}，目标线程数={target_threads}'
        )
    # 失败条件4：实际运行时间 < 预计耗时50%
    if executed_at and estimated_duration:
        elapsed = (datetime.now() - executed_at).total_seconds()
        if elapsed < estimated_duration * 0.5:
            err_parts.append(
                f'实际运行时间（{elapsed:.0f}s）不足预计耗时的50%（{estimated_duration * 0.5:.0f}s）'
            )
    err_msg = '\n'.join(err_parts)
    if nohup_tail:
        err_msg += f'\n\njmeter_nohup.out:\n{nohup_tail}'
    return 5, err_msg


async def collect_jmeter_log(
    scenario_id: int,
    is_distributed: int,
    remote_dir: str,
    exec_machine_ip: str,
    exec_machine_ssh_port: int,
    ssh_user: 'str | None' = None,
    ssh_password: 'str | None' = None,
) -> None:
    """
    APScheduler 异步任务：增量收集 JMeter 日志并更新压测进度。

    进程存活检测使用 Redis 中缓存的 PID（perf:jmeter_pid:{id}），
    执行 kill -0 {pid} 检测，避免 pgrep 在多场景共用同一 JMX 文件名时误匹配。

    Args:
        scenario_id:           压测场景 ID
        is_distributed:        是否分布式（0/1，仅用于日志标记）
        remote_dir:            JMeter 工作目录（含 logs/ 子目录）
        exec_machine_ip:       执行机 IP（分布式=Master，单机=单机压力机）
        exec_machine_ssh_port: 执行机 SSH 端口
    """
    from app.db import get_redis_pool
    from app.db.sqlalchemy import async_session_factory
    from app.core.base_crud import BaseCRUD
    from app.api.v1.performance.scenario.model import PerfScenarioModel

    redis = get_redis_pool().get_redis()
    log_key    = _log_key(scenario_id)
    offset_key = _offset_key(scenario_id)

    # ── 1. 读取当前文件行偏移 ─────────────────────────────────────────────
    raw_offset = await redis.get(offset_key)
    file_offset = int(raw_offset) if raw_offset is not None else 1  # tail -n +1 = 从第1行开始

    # ── 2. SSH 增量读日志 + PID 存活检测 ─────────────────────────────────
    # 从 Redis 读取启动时缓存的 PID，用 kill -0 检测进程是否存活，
    # 避免 pgrep 在多场景共用同一 JMX 文件名时误匹配其他场景的进程
    pid_raw = await redis.get(_pid_key(scenario_id))
    pid = (pid_raw.decode() if isinstance(pid_raw, bytes) else pid_raw) or ''
    # 标记是否有可用 PID——无 PID 时跳过存活检测，避免误判进程已结束
    pid_known = bool(pid and pid.strip().isdigit())

    if pid_known:
        proc_check = f"kill -0 {pid.strip()} 2>/dev/null && echo {pid.strip()} || echo ''"
    else:
        # PID 未缓存（启动过慢或已超时清理），本轮跳过存活检测
        logger.warning(f'[LogCollector] scenario={scenario_id} Redis中无PID，本轮跳过进程存活检测')
        proc_check = "echo ''"

    from app.common.commands import TAIL_LOG_INCREMENTAL
    cmd = TAIL_LOG_INCREMENTAL.format(
        remote_dir=remote_dir,
        file_offset=file_offset,
        proc_check=proc_check,
    )

    def _ssh_read() -> 'str | None':
        """SSH 读取日志及进程检测；复用连接池中的持久连接。
        返回命令 stdout 字符串；连接或执行失败时返回 None（区别于空输出），
        调用方检测到 None 应跳过本轮，不更新任何状态，避免误判进程已结束。
        """
        from app.utils.oper_shell import ShellOperationUtils
        try:
            credential: dict = {}
            if ssh_user:
                credential['ssh_user'] = ssh_user
            if ssh_password:
                credential['ssh_password'] = ssh_password
            ssh = _get_or_connect(scenario_id, exec_machine_ip, exec_machine_ssh_port, credential)
            _, stdout, _ = ShellOperationUtils.execute_remote_command(ssh, cmd)
            return stdout
        except Exception as e:
            logger.warning(f'[LogCollector] scenario={scenario_id} SSH读取日志失败：{e}')
            _release_connection(scenario_id)  # 连接失败时释放，下次重连
            return None

    output = await asyncio.to_thread(_ssh_read)

    # SSH 连接/执行失败：跳过本轮，等待下次调度重试；file_offset 不更新，下次从断点补读
    if output is None:
        logger.warning(f'[LogCollector] scenario={scenario_id} SSH输出为None，跳过本轮')
        return

    # ── 3. 解析输出 ────────────────────────────────────────────────────────
    if '---PROC_CHECK---' in output:
        log_part, proc_part = output.split('---PROC_CHECK---', 1)
    else:
        log_part, proc_part = output, ''

    # 过滤空行，但保留 JMeter 汇总行（含空格）
    new_lines = [l.rstrip('\r') for l in log_part.split('\n') if l.rstrip('\r')]
    proc_pid = proc_part.strip()
    # PID 未知时保守地视为运行中，避免因无 PID 信息而误判进程已结束
    process_running = bool(proc_pid and proc_pid.isdigit()) if pid_known else True

    # PID 未缓存时的兜底完成检测：扫描本轮新增日志行，发现 JMeter 结束标志即触发完成流程
    if not pid_known and process_running and new_lines:
        _end_markers = ('... end of run', 'Tidying up ...')
        if any(m in line for line in new_lines for m in _end_markers):
            process_running = False
            logger.info(
                f'[LogCollector] scenario={scenario_id} '
                f'PID未缓存，从日志行检测到压测结束标志，触发完成检测'
            )

    # ── 4. 追加日志到 Redis，超限时裁剪头部 ───────────────────────────────
    if new_lines:
        for line in new_lines:
            await redis.rpush(log_key, line)
        await redis.expire(log_key, 86400)

        # 超过最大行数时从头裁剪，保留最新的 _MAX_LOG_LINES 行；
        # 累计裁剪量写入 evicted_key，供 monitor_sse 修正客户端 offset
        current_len = await redis.llen(log_key)
        if current_len > _MAX_LOG_LINES:
            trim_count = current_len - _MAX_LOG_LINES
            await redis.ltrim(log_key, trim_count, -1)
            await redis.incrby(_evicted_key(scenario_id), trim_count)
            await redis.expire(_evicted_key(scenario_id), 86400)
            logger.info(
                f'[LogCollector] scenario={scenario_id} '
                f'Redis日志裁剪 {trim_count} 行，保留最新 {_MAX_LOG_LINES} 行'
            )

        new_file_offset = file_offset + len(new_lines)
        await redis.set(offset_key, new_file_offset, ex=86400)

    # ── 单条轮询摘要日志 ───────────────────────────────────────────────────
    pid_str = pid.strip() if pid_known else '无'
    offset_str = f'{file_offset}→{file_offset + len(new_lines)}' if new_lines else str(file_offset)
    logger.info(
        f'[LogCollector] 轮询 scenario={scenario_id} pid={pid_str} '
        f'offset={offset_str} process_running={process_running} new_lines={len(new_lines)}'
    )

    # ── 5. 更新进度 + 检查进程 ─────────────────────────────────────────────
    async with async_session_factory() as db:
        scenario_crud = BaseCRUD(PerfScenarioModel, db)
        scenario = await scenario_crud.get_by_id_crud(scenario_id)

        if not scenario or scenario.status != 2:
            # 场景已被外部修改（手动取消等），停止任务
            _remove_job(scenario_id)
            return

        update_payload: dict = {}

        if not process_running:
            # 查询目标线程数，用于 _check_jmeter_completion 中 Finished 对比
            target_threads = 0
            try:
                from sqlalchemy import select as _sa_select, and_ as _sa_and_
                from app.api.v1.performance.scenario.model import PerfScenarioConfigModel
                cfg_stmt = _sa_select(PerfScenarioConfigModel).where(
                    _sa_and_(
                        PerfScenarioConfigModel.scenario_id == scenario_id,
                        PerfScenarioConfigModel.status      == 1,
                        PerfScenarioConfigModel.enabled_flag == 1,
                    )
                )
                active_cfgs  = (await db.execute(cfg_stmt)).scalars().all()
                workers      = (scenario.node_count or 1) if scenario.is_distributed else 1
                target_threads = sum(c.thread_count or 0 for c in active_cfgs) * workers
            except Exception as _e:
                logger.warning(f'[LogCollector] 获取目标线程数失败 scenario={scenario_id}: {_e}')

            # 综合判断压测成功/失败（替代原来的 status=3 硬编码）
            final_status, error_info = await _check_jmeter_completion(
                scenario_id=scenario_id,
                remote_dir=remote_dir,
                exec_machine_ip=exec_machine_ip,
                exec_machine_ssh_port=exec_machine_ssh_port,
                target_threads=target_threads,
                estimated_duration=scenario.estimated_duration,
                executed_at=scenario.executed_at,
                ssh_user=ssh_user,
                ssh_password=ssh_password,
            )
            logger.info(
                f'[LogCollector] scenario={scenario_id} JMeter进程已结束，'
                f'判定结果：{"已完成" if final_status == 3 else "失败"}'
            )
            update_payload['status'] = final_status
            if final_status == 3:
                update_payload['progress'] = 100
            elif scenario.estimated_duration and scenario.executed_at:
                elapsed = (datetime.now() - scenario.executed_at).total_seconds()
                update_payload['progress'] = min(99, int(elapsed / scenario.estimated_duration * 100))
            if error_info:
                update_payload['error_info'] = error_info

        if update_payload:
            await scenario_crud.update_crud(scenario_id, update_payload)

        # 压测完成：同步关联定时任务状态、触发报告收集
        if not process_running:
            # 同步关联定时任务状态为已结束，并判断触发方式（供报告记录使用）
            trigger_type = 1  # 默认手动触发
            try:
                from sqlalchemy import select, and_
                from app.api.v1.performance.scheduler.model import PerfSchedulerModel
                sched_crud = BaseCRUD(PerfSchedulerModel, db)
                stmt = (
                    select(PerfSchedulerModel)
                    .where(and_(
                        PerfSchedulerModel.scenario_id == scenario_id,
                        PerfSchedulerModel.task_status == 1,
                        PerfSchedulerModel.enabled_flag == 1,
                    ))
                    .limit(1)
                )
                sched_obj = (await db.execute(stmt)).scalars().first()
                if sched_obj:
                    await sched_crud.update_crud(sched_obj.id, {
                        'task_status': 2,
                        'is_active':   0,
                        'end_time':    datetime.now(),
                    })
                    trigger_type = 2  # 定时任务触发
                    logger.info(f'[LogCollector] 定时任务已更新为已结束 scheduler_id={sched_obj.id}')
            except Exception as e:
                logger.warning(f'[LogCollector] 回写定时任务状态失败 scenario_id={scenario_id}: {e}')

            # 触发报告收集前重新读取场景状态，防止 stop_running_scenario 竞争：
            # stop 会先将 status 置 4（已取消），此处再校验避免对强制停止的场景误触发收集
            try:
                fresh_scenario = await scenario_crud.get_by_id_crud(scenario_id)
                if not fresh_scenario or fresh_scenario.status == 4:
                    logger.info(f'[LogCollector] 场景已被强制停止，跳过报告收集 scenario_id={scenario_id}')
                else:
                    from app.api.v1.performance.report.collector import (
                        create_collecting_record, collect_report_async,
                    )

                    # 在创建记录前采集源文件 MD5（复用 SSH 连接池中的现有连接，无需重新建连）
                    src_log_md5 = src_jtl_md5 = src_report_md5 = None
                    try:
                        from app.common.commands import SNAPSHOT_SRC_MD5
                        from app.utils.oper_shell import ShellOperationUtils
                        _cred: dict = {}
                        if ssh_user:     _cred['ssh_user']     = ssh_user
                        if ssh_password: _cred['ssh_password'] = ssh_password

                        def _get_md5() -> str:
                            _ssh = _get_or_connect(scenario_id, exec_machine_ip, exec_machine_ssh_port, _cred)
                            _, _out, _ = ShellOperationUtils.execute_remote_command(
                                _ssh, SNAPSHOT_SRC_MD5.format(remote_dir=remote_dir)
                            )
                            return _out

                        _md5_out = await asyncio.to_thread(_get_md5)
                        for _part in _md5_out.split():
                            if _part.startswith('LOG_MD5:'):   src_log_md5    = _part[8:] or None
                            elif _part.startswith('JTL_MD5:'): src_jtl_md5    = _part[8:] or None
                            elif _part.startswith('RPT_MD5:'): src_report_md5 = _part[8:] or None
                        logger.info(
                            f'[LogCollector] 源文件MD5已采集 scenario={scenario_id} '
                            f'log={src_log_md5} jtl={src_jtl_md5} '
                            f'rpt={src_report_md5[:8] + "..." if src_report_md5 else None}'
                        )
                    except Exception as _me:
                        logger.warning(f'[LogCollector] 采集MD5失败（不影响收集）scenario={scenario_id}: {_me}')

                    # 立即写 DB status=1(收集中)，MD5 随初始记录一同写入
                    report_id = await create_collecting_record(
                        scenario_id=scenario_id,
                        scenario_code=fresh_scenario.code or f'S{scenario_id}',
                        scenario_name=fresh_scenario.name or f'场景{scenario_id}',
                        exec_ip=exec_machine_ip,
                        exec_ssh_port=exec_machine_ssh_port,
                        trigger_type=trigger_type,
                        operator_id=scenario.updated_by or scenario.created_by,
                        src_log_md5=src_log_md5,
                        src_jtl_md5=src_jtl_md5,
                        src_report_md5=src_report_md5,
                    )
                    asyncio.ensure_future(collect_report_async(
                        report_id=report_id,
                        scenario_id=scenario_id,
                        remote_dir=remote_dir,
                        exec_ip=exec_machine_ip,
                        exec_ssh_port=exec_machine_ssh_port,
                        ssh_user=ssh_user,
                        ssh_password=ssh_password,
                    ))
                    logger.info(f'[LogCollector] 已触发报告收集任务 scenario_id={scenario_id} report_id={report_id}')
            except Exception as e:
                logger.warning(f'[LogCollector] 触发报告收集失败 scenario_id={scenario_id}: {e}')

        await db.commit()

    # 进程已结束：停止本 APScheduler 任务
    if not process_running:
        _remove_job(scenario_id)


def _remove_job(scenario_id: int) -> None:
    """安全移除 APScheduler 日志收集任务并释放 SSH 连接池。"""
    _release_connection(scenario_id)
    try:
        from app.api.v1.task_scheduler.scheduler import get_scheduler
        scheduler = get_scheduler()
        job_id = f'perf_log_{scenario_id}'
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f'[LogCollector] APScheduler 任务已移除：{job_id}')
        else:
            logger.info(f'[LogCollector] APScheduler 任务不存在（已由完成流程移除）：{job_id}')
    except Exception as e:
        logger.warning(f'[LogCollector] 移除 APScheduler 任务失败：{e}')


def start_log_collector(
    scenario_id: int,
    is_distributed: int,
    remote_dir: str,
    exec_machine_ip: str,
    exec_machine_ssh_port: int,
    poll_interval: int = 5,
    ssh_user: 'str | None' = None,
    ssh_password: 'str | None' = None,
) -> None:
    """
    注册并启动日志收集 APScheduler 任务（同步接口，供 service 调用）。

    Args:
        scenario_id:           压测场景 ID
        is_distributed:        是否分布式（0/1）
        remote_dir:            JMeter 工作目录
        exec_machine_ip:       执行机 IP
        exec_machine_ssh_port: 执行机 SSH 端口
        poll_interval:         轮询间隔秒数（从 DB 参数读取后传入）
    """
    from apscheduler.triggers.interval import IntervalTrigger
    from app.api.v1.task_scheduler.scheduler import get_scheduler

    scheduler = get_scheduler()
    job_id = f'perf_log_{scenario_id}'

    # 移除同名旧任务（场景重复启动防护）
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    scheduler.add_job(
        collect_jmeter_log,
        trigger=IntervalTrigger(seconds=poll_interval),
        args=[scenario_id, is_distributed,
              remote_dir, exec_machine_ip, exec_machine_ssh_port,
              ssh_user, ssh_password],
        id=job_id,
        replace_existing=True,
        executor='default',       # AsyncIOExecutor，与 FastAPI 事件循环共享
        max_instances=1,
        coalesce=True,
    )
    logger.info(
        f'[LogCollector] 任务已启动：{job_id}，轮询间隔={poll_interval}s，'
        f'目标={exec_machine_ip}:{exec_machine_ssh_port}'
    )


def stop_log_collector(scenario_id: int) -> None:
    """手动停止日志收集任务（场景取消/手动终止时调用）。"""
    _remove_job(scenario_id)