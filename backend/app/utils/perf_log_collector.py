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
  5. 解析新增 summariser 区间行（"summary +"）→ 实时指标快照（QPS/平均RT/并发线程数/错误率）
  6. 增量 tail result.jtl → 按 sampler(label) 聚合样本数/错误数/错误明细 → 重算 Top5 Errors 快照
     （5、6 与 1 合并在同一次 SSH 往返内完成，见 TAIL_LOG_AND_JTL_INCREMENTAL）

Redis 键：
  perf:jmeter_log:{id}       List，当前保留的日志行（滑动窗口，最多 _MAX_LOG_LINES 行）
  perf:jmeter_foffset:{id}   Integer，已读取的文件行偏移（tail -n +N 的 N）
  perf:jmeter_pid:{id}       String，JMeter 进程 PID
  perf:jmeter_levicted:{id}  Integer，累计从 List 头部裁剪掉的行数（用于 offset 修正）
  perf:stage:{id}            String，定时任务 Stage1-3 最新一条结构化状态 JSON（供 monitor_sse 补发阶段事件）
  perf:metric:{id}           List，summariser 解析出的实时指标快照（QPS/平均RT/并发线程数/错误率）
  perf:jtl_offset:{id}       Integer，result.jtl 已读取的字节偏移（tail -c +N 的 N）
  perf:label_samples:{id}    Hash，按 sampler(label) 累计的样本数
  perf:label_errors:{id}     Hash，按 sampler(label) 累计的错误数
  perf:label_error_detail:{id} Hash，field="label\terrorKey"，按具体错误累计的出现次数
  perf:top5:{id}             String，Top5 Errors by Sampler 最新快照 JSON（供 monitor_sse 推送 top_errors 事件）
所有键 TTL=24h。
"""
import asyncio
import json
import re
import threading
from datetime import datetime

from app.core.logger import logger
from app.common.rediskeys import (
    _log_key, _offset_key, _pid_key, _evicted_key, _metric_series_key, _jtl_offset_key, _label_samples_key,
    _label_errors_key, _label_error_detail_key, _top5_key, _last_threads_key,
)

# Redis List 最大保留行数；超出时从头裁剪，保留最新的 N 行
_MAX_LOG_LINES = 10000

# 实时指标快照 List 最大保留条数（summariser 默认 10s 一条，1000 条约 2.7 小时）
_MAX_METRIC_POINTS = 1000

# 解析 JMeter summariser 区间增量行（"summary +"），累计行（"summary ="）缺少 Active/Started/Finished，
# 不适合做实时曲线，故只解析区间增量行；示例：
# summary +   5878 in 00:00:10 =  588.0/s Avg:    34 Min:    18 Max:   104 Err:    12 (0.20%) Active: 22 Started: 22 Finished: 0
_SUMMARY_PLUS_RE = re.compile(
    r'summary \+\s*\d+ in [\d:]+ =\s*([\d.]+)/s Avg:\s*(\d+) .*?'
    r'Err:\s*(\d+)\s*\(([\d.]+)%\)(?:\s*Active:\s*(\d+))?'
)



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


async def _recompute_top5(redis, scenario_id: int) -> None:
    """基于累计的 label 样本数/错误数/错误明细 三个 Hash，重新计算 Top5 Errors by Sampler 快照。

    行按错误数降序排列（最容易出错的接口排最前面），每行内部错误按出现次数取 Top5，
    与前端 monitor.vue 现有表格结构（sampler/samples/errors/top[]）一一对应。
    首行为跨所有 sampler 的 Total 汇总，与 JMeter HTML 报告格式保持一致。
    """
    samples_map = await redis.hgetall(_label_samples_key(scenario_id))
    errors_map  = await redis.hgetall(_label_errors_key(scenario_id))
    detail_map  = await redis.hgetall(_label_error_detail_key(scenario_id))

    def _d(v) -> str:
        return v.decode('utf-8') if isinstance(v, bytes) else v

    samples = {_d(k): int(_d(v)) for k, v in samples_map.items()}
    errors  = {_d(k): int(_d(v)) for k, v in errors_map.items()}

    by_label: dict = {}
    all_err_agg: dict = {}  # 跨所有 label 的错误聚合，用于 Total 行
    for k, v in detail_map.items():
        key = _d(k)
        if '\t' not in key:
            continue
        label, err_key = key.split('\t', 1)
        cnt = int(_d(v))
        by_label.setdefault(label, []).append({'error': err_key, 'count': cnt})
        all_err_agg[err_key] = all_err_agg.get(err_key, 0) + cnt

    rows = []
    for label, err_count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
        top = sorted(by_label.get(label, []), key=lambda x: x['count'], reverse=True)[:5]
        rows.append({
            'sampler': label,
            'samples': samples.get(label, 0),
            'errors':  err_count,
            'top':     top,
        })

    # Total 汇总行（置于最前），与 JMeter HTML 报告 Top5 Errors 格式一致
    total_samples = sum(samples.values())
    total_errors  = sum(errors.values())
    if total_samples > 0:
        total_top = sorted(all_err_agg.items(), key=lambda x: x[1], reverse=True)[:5]
        rows.insert(0, {
            'sampler': 'Total',
            'samples': total_samples,
            'errors':  total_errors,
            'top':     [{'error': e, 'count': c} for e, c in total_top],
        })

    await redis.set(_top5_key(scenario_id), json.dumps(rows, ensure_ascii=False), ex=86400)


async def collect_jmeter_log(
    scenario_id: int,
    is_distributed: int,
    remote_dir: str,
    exec_machine_ip: str,
    exec_machine_ssh_port: int,
    ssh_user: 'str | None' = None,
    ssh_password: 'str | None' = None,
    poll_interval: int = 5,
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
    from app.core.redis import get_redis_pool
    from app.core.database import async_session_factory
    from app.core.base_crud import BaseCRUD
    from app.api.v1.Ntesterc_module.Ntesterc_performance.scenario.model import PerfScenarioModel

    redis = get_redis_pool().get_redis()
    log_key    = _log_key(scenario_id)
    offset_key = _offset_key(scenario_id)

    # ── 1. 读取当前文件行偏移（nohup.out 行偏移 + result.jtl 字节偏移）───────
    raw_offset = await redis.get(offset_key)
    file_offset = int(raw_offset) if raw_offset is not None else 1  # tail -n +1 = 从第1行开始
    raw_jtl_offset = await redis.get(_jtl_offset_key(scenario_id))
    jtl_offset = int(raw_jtl_offset) if raw_jtl_offset is not None else 1  # tail -c +1 = 从第1字节开始

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

    from app.common.commands import TAIL_LOG_AND_JTL_INCREMENTAL
    cmd = TAIL_LOG_AND_JTL_INCREMENTAL.format(
        remote_dir=remote_dir,
        file_offset=file_offset,
        proc_check=proc_check,
        jtl_offset=jtl_offset,
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

    # ── 3. 解析输出（nohup.out 增量 / 存活检测 / label 聚合增量）───────────
    if '---PROC_CHECK---' in output:
        log_part, _rest1 = output.split('---PROC_CHECK---', 1)
    else:
        log_part, _rest1 = output, ''
    if '---JTL_AGG---' in _rest1:
        proc_part, jtl_agg_part = _rest1.split('---JTL_AGG---', 1)
    else:
        proc_part, jtl_agg_part = _rest1, ''
    jtl_agg_part = jtl_agg_part.split('---END---', 1)[0]

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

    # ── 解析 summariser 区间行，提取全局 Active 线程数（用于指标图 threads 系列）──
    # 无新 summary+ 行时沿用 Redis 中上一次有效值，避免因 JMeter 10s 写一次而前端每 5s 收到 0 产生锯齿
    threads_active: int | None = None
    for line in new_lines:
        if 'summary +' not in line:
            continue
        m = _SUMMARY_PLUS_RE.search(line)
        if m and m.group(5):
            threads_active = int(m.group(5))
    last_threads_key = _last_threads_key(scenario_id)
    if threads_active is not None:
        await redis.set(last_threads_key, threads_active, ex=86400)
    else:
        raw = await redis.get(last_threads_key)
        threads_active = int(raw) if raw else 0

    # ── result.jtl 增量聚合：S/E/D 累计写 Redis Hash，M 行用于本轮 per-label 指标 ──
    agg_lines = [l for l in jtl_agg_part.split('\n') if l.strip()]
    is_first_jtl_round = (jtl_offset == 1)  # 首轮读全量文件，QPS 无法准确归一，跳过指标推送
    round_per_label: dict = {}  # label → (sum_elapsed, count, errors)
    consumed_bytes = 0  # 本轮 python 脚本实际消费的字节数（仅到最后一个完整行），用于推进游标
    has_agg_data = False
    if agg_lines:
        samples_key = _label_samples_key(scenario_id)
        errors_key  = _label_errors_key(scenario_id)
        detail_key  = _label_error_detail_key(scenario_id)
        for line in agg_lines:
            parts = line.split('\t')
            try:
                if parts[0] == 'S' and len(parts) == 3:
                    await redis.hincrby(samples_key, parts[1], int(parts[2]))
                    has_agg_data = True
                elif parts[0] == 'E' and len(parts) == 3:
                    await redis.hincrby(errors_key, parts[1], int(parts[2]))
                    has_agg_data = True
                elif parts[0] == 'D' and len(parts) == 4:
                    await redis.hincrby(detail_key, f'{parts[1]}\t{parts[2]}', int(parts[3]))
                    has_agg_data = True
                elif parts[0] == 'M' and len(parts) == 5:
                    # per-round per-label: sum_elapsed / count / errors
                    round_per_label[parts[1]] = (int(parts[2]), int(parts[3]), int(parts[4]))
                    has_agg_data = True
                elif parts[0] == 'C' and len(parts) == 2:
                    consumed_bytes = int(parts[1])
            except (ValueError, IndexError):
                continue
        if has_agg_data:
            for k in (samples_key, errors_key, detail_key):
                await redis.expire(k, 86400)
            await _recompute_top5(redis, scenario_id)

    # 按脚本实际消费的完整行字节数推进游标（而非单独测量的文件总大小），
    # 避免与远端文件持续写入并发导致的窗口错位、重复计数或半行解析
    if consumed_bytes > 0:
        await redis.set(_jtl_offset_key(scenario_id), jtl_offset + consumed_bytes, ex=86400)

    # ── 推送 per-label 实时指标快照（首轮跳过，后续每轮一个 metric point）──────────
    # QPS = count / poll_interval；首轮因读全量文件导致 count 跨越整个测试时长，跳过以免曲线失真
    # 注意：不再要求 round_per_label 非空才推送——线程阶梯式退出时，正在退出的线程当轮往往
    # 没有新完成的请求（round_per_label 为空），若继续以此为推送前提，会丢失 threads_active
    # 已经解析到的 ramp-down 中间阶梯值，导致并发线程数图表峰值后直接水平到结束，而非真实阶梯下降
    if not is_first_jtl_round:
        labels_data = {}
        for label, (sum_el, count, err_count) in round_per_label.items():
            ok_count = count - err_count
            labels_data[label] = {
                'qps_ok':  round(ok_count / poll_interval, 2),
                'qps_err': round(err_count / poll_interval, 2),
                'avg_rt':  round(sum_el / count) if count > 0 else 0,
                'err_rate': round(err_count / count * 100, 2) if count > 0 else 0.0,
            }
        metric_point = {
            'time':    datetime.now().strftime('%H:%M:%S'),
            'threads': threads_active,
            'labels':  labels_data,
        }
        metric_key = _metric_series_key(scenario_id)
        await redis.rpush(metric_key, json.dumps(metric_point, ensure_ascii=False))
        metric_len = await redis.llen(metric_key)
        if metric_len > _MAX_METRIC_POINTS:
            await redis.ltrim(metric_key, metric_len - _MAX_METRIC_POINTS, -1)
        await redis.expire(metric_key, 86400)

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
                from app.api.v1.Ntesterc_module.Ntesterc_performance.scenario.model import PerfScenarioConfigModel
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

        # 压测完成：同步关联定时任务状态、触发报告收集、更新场景状态
        if not process_running:
            # 同步关联定时任务状态为已结束，并判断触发方式（供报告记录使用）
            trigger_type = 1  # 默认手动触发
            try:
                from sqlalchemy import select, and_
                from app.api.v1.Ntesterc_module.Ntesterc_performance.scheduler.model import PerfSchedulerModel
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

            # 重新读取场景状态，防止 stop_running_scenario 竞争：
            # stop 会先将 status 置 4（已取消），此处再校验避免对强制停止的场景误触发收集
            try:
                fresh_scenario = await scenario_crud.get_by_id_crud(scenario_id)
                if not fresh_scenario or fresh_scenario.status == 4:
                    logger.info(f'[LogCollector] 场景已被强制停止，跳过报告收集 scenario_id={scenario_id}')
                else:
                    from app.api.v1.Ntesterc_module.Ntesterc_performance.report.collector import (
                        create_collecting_record, collect_report_async,
                    )
                    # 先写 DB status=1(收集中)，再更新场景完成状态，消除时序窗口：
                    # 确保前端看到场景"已完成"时报告收集记录已存在。
                    # MD5 由 collect_report_async 内 _snapshot_src_md5 在 SSH 建连后自动采集写库。
                    report_id = await create_collecting_record(
                        scenario_id=scenario_id,
                        scenario_code=fresh_scenario.code or f'S{scenario_id}',
                        scenario_name=fresh_scenario.name or f'场景{scenario_id}',
                        exec_ip=exec_machine_ip,
                        exec_ssh_port=exec_machine_ssh_port,
                        trigger_type=trigger_type,
                        operator_id=scenario.updated_by or scenario.created_by,
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

            # 场景完成状态在报告记录创建后更新，确保前端看到"已完成"时记录已存在
            if update_payload:
                await scenario_crud.update_crud(scenario_id, update_payload)

        await db.commit()

    # 进程已结束：停止本 APScheduler 任务，并清理 Redis 日志缓存
    if not process_running:
        _remove_job(scenario_id)
        try:
            from app.core.redis import get_redis_pool
            _redis = get_redis_pool().get_redis()
            await _redis.delete(
                _log_key(scenario_id), _offset_key(scenario_id),
                _evicted_key(scenario_id), _pid_key(scenario_id),
                _metric_series_key(scenario_id), _jtl_offset_key(scenario_id),
                _label_samples_key(scenario_id), _label_errors_key(scenario_id),
                _label_error_detail_key(scenario_id), _top5_key(scenario_id),
            )
        except Exception as _e:
            logger.warning(f'[LogCollector] 清理 Redis 日志缓存失败 scenario={scenario_id}: {_e}')


def _remove_job(scenario_id: int) -> None:
    """安全移除 APScheduler 日志收集任务并释放 SSH 连接池。"""
    _release_connection(scenario_id)
    try:
        from app.api.v1.Ntesterc_module.Ntesterc_task_scheduler.scheduler import get_scheduler
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
    from app.api.v1.Ntesterc_module.Ntesterc_task_scheduler.scheduler import get_scheduler

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
              ssh_user, ssh_password, poll_interval],
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