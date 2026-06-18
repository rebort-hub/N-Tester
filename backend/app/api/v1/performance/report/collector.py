#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
"""
性能测试 - 压测报告收集器

职责：
  1. create_collecting_record()：JMeter 结束后立即写 DB status=1(收集中)，返回 report_id
  2. ReportCollector.run() 执行四步收集流程，通过模块级 _collect_state 字典向 SSE 暴露进度：
       Step 1: SSH连接  (10%)   — 建连 exec 机、验证 worker 连通性（分布式）、探测 MinIO 确定方案
       Step 2: 远端打包 (35%)  — 方案A：3个zip；方案B：单个tar.gz
       Step 3: 文件下载 (65%)  — 仅方案B：SFTP下载tar.gz + 分布式relay下载worker日志
       Step 4: 打包上传 (100%) — 顺序：report → log → jtl
  3. MinIO 对象命名：
       report/{report_code}/jmeter-reports.zip  ← HTML 报告（range-request 预览）
       report/{report_code}/jmeter-logs.zip    ← JMeter 日志
       report/{report_code}/results.zip        ← JTL 结果文件
       report/{report_code}/collector_process.log ← 收集流程日志
  4. SSH 连接全程复用（self._exec_ssh），仅在 finally 中关闭
  5. 分布式始终使用方案B（平台中转）；单机视 MinIO 可达性决定方案A或B
"""
import asyncio
import io
import random
import re
import tarfile
import zipfile
from datetime import datetime
from typing import Optional

from app.corelibs.logger import logger


# ── 模块级进度状态字典，供 collectProcess SSE 接口轮询 ─────────────────────────
# key: report_id  value: {step, pct, step_name, detail, status, plan?, sub_items?}
# status 取值：'running' | 'done' | 'failed' | 'interrupted'
# 收集结束后保留 300 秒供断线重连读取，之后自动清理
_collect_state: dict[int, dict] = {}

# ── 强制停止信号集合，service.stop() 写入，collector.run() 在步骤间检测 ──────────
_stop_requested: set[int] = set()


def _generate_report_code() -> str:
    """RPT + 年月日时分秒(后2位年) + 00 + 2位随机数，示例：RPT2604101035220047"""
    now = datetime.now()
    return f"RPT{now.strftime('%y%m%d%H%M%S')}00{random.randint(10, 99)}"


def _generate_report_name(scenario_name: str) -> str:
    """Report-场景名-年月日时分(后2位年)，示例：Report-登录压测-2604101005

    对场景名中的 URL/文件系统不安全字符（+/\\?%#& 及空白）替换为下划线，
    防止 MinIO 预签名 PUT URL 因 + 号 percent-encode 不一致导致签名校验失败（HTTP 403）。
    """
    now = datetime.now()
    safe_name = re.sub(r'[+/\\?%#&\s]', '_', scenario_name)
    return f"Report-{safe_name}-{now.strftime('%y%m%d%H%M')}"


async def create_collecting_record(
    scenario_id:   int,
    scenario_code: str,
    scenario_name: str,
    exec_ip:       str,
    exec_ssh_port: int,
    trigger_type:  int = 1,
    operator_id:   Optional[int] = None,
    operator_name: Optional[str] = None,
    src_log_md5:    Optional[str] = None,
    src_jtl_md5:    Optional[str] = None,
    src_report_md5: Optional[str] = None,
) -> int:
    """
    JMeter 进程结束后立即调用：在 DB 创建 status=1(收集中) 的报告记录。
    src_*_md5 由调用方（perf_log_collector）在 SSH 连接期间预先采集并传入，
    在创建记录时同步写入，作为后续强制停止恢复时的原始文件指纹。

    Returns:
        report_id（perf_reports 主键），后续传给 collect_report_async。
    """
    from app.db.sqlalchemy import async_session_factory
    from app.core.base_crud import BaseCRUD
    from config import config
    from .model import PerfReportModel

    report_code = _generate_report_code()
    report_name = _generate_report_name(scenario_name)

    # 查操作人用户名
    creator_name = operator_name or ''
    if not creator_name and operator_id:
        try:
            from sqlalchemy import select
            from app.api.v1.system.user.model import UserModel
            async with async_session_factory() as db:
                creator_name = (await db.execute(
                    select(UserModel.username).where(UserModel.id == operator_id)
                )).scalar_one_or_none() or ''
        except Exception:
            pass

    async with async_session_factory() as db:
        obj = await BaseCRUD(PerfReportModel, db).create_crud({
            'report_code':   report_code,
            'scenario_id':   scenario_id,
            'scenario_code': scenario_code,
            'scenario_name': scenario_name,
            'report_name':   report_name,
            'bucket':        config.MINIO_BUCKET,
            'object_key':    f'report/{report_code}/jmeter-reports.zip',
            'file_size':     0,
            'report_status': 1,
            'trigger_type':  trigger_type,
            'remark':        '',
            'generated_at':  None,
            'creator':       creator_name,
            'creator_id':    operator_id,
            'created_by':    operator_id,
            'src_log_md5':    src_log_md5,
            'src_jtl_md5':    src_jtl_md5,
            'src_report_md5': src_report_md5,
        })

    logger.info(f'[ReportCollector] 已创建收集中记录 report_id={obj.id} report_code={report_code}')
    return obj.id


class ReportCollector:
    """
    压测报告收集器。

    使用方式：
        collector = ReportCollector(report_id, scenario_id, remote_dir, exec_ip, exec_ssh_port)
        await collector.run()
    """

    def __init__(
        self,
        report_id:      int,
        scenario_id:    int,
        remote_dir:     str,
        exec_ip:        str,
        exec_ssh_port:  int,
        ssh_user:       Optional[str] = None,
        ssh_password:   Optional[str] = None,
        include_log:    bool = True,
        include_jtl:    bool = True,
        include_report: bool = True,
    ):
        self.report_id      = report_id
        self.scenario_id    = scenario_id
        self.remote_dir     = remote_dir.rstrip('/')
        self.exec_ip        = exec_ip
        self.exec_ssh_port  = exec_ssh_port
        # 恢复收集时指定哪些源文件 MD5 匹配，False 则跳过该类文件
        self.include_log    = include_log
        self.include_jtl    = include_jtl
        self.include_report = include_report
        self._credential: dict = {}
        if ssh_user:
            self._credential['ssh_user'] = ssh_user
        if ssh_password:
            self._credential['ssh_password'] = ssh_password

        # 全程复用的 SSH 连接（建立于 Step 1，关闭于 finally）
        self._exec_ssh = None
        # True = 执行机直传 MinIO（方案A），False = 平台中转（方案B）；分布式恒为 False
        self._plan_a = False

        self._log_lines: list[str] = []

    # ──────────────────────────────────────────────────────────────────────────
    #  日志 + 状态更新
    # ──────────────────────────────────────────────────────────────────────────

    def _log(self, level: str, msg: str) -> None:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._log_lines.append(f"[{ts}] [{level}]  {msg}")
        if level == 'ERROR':
            logger.error(f'[ReportCollector] {msg}')
        elif level == 'WARN':
            logger.warning(f'[ReportCollector] {msg}')
        else:
            logger.info(f'[ReportCollector] {msg}')

    def _set_state(
        self,
        step: int,
        pct: int,
        step_name: str,
        detail: str,
        status: str = 'running',
        sub_items: dict | None = None,
        plan: str | None = None,
    ) -> None:
        """更新模块级进度字典，SSE 接口通过轮询此字典推流到前端。"""
        state: dict = {
            'step':      step,
            'pct':       pct,
            'step_name': step_name,
            'detail':    detail,
            'status':    status,
        }
        if sub_items is not None:
            state['sub_items'] = sub_items
        if plan is not None:
            state['plan'] = plan
        _collect_state[self.report_id] = state
        self._log('INFO', f'[Step {step}/4] {step_name} ({pct}%) — {detail}')

    async def _cleanup_state_later(self) -> None:
        """收集结束后保留状态 300 秒供断线重连读取，之后自动清理。"""
        await asyncio.sleep(300)
        _collect_state.pop(self.report_id, None)

    def _is_stop_requested(self) -> bool:
        """检测是否收到强制停止信号（由 service.stop() 写入 _stop_requested）。"""
        return self.report_id in _stop_requested

    # ──────────────────────────────────────────────────────────────────────────
    #  SSH / SFTP 工具（同步，通过 asyncio.to_thread 执行）
    # ──────────────────────────────────────────────────────────────────────────

    def _exec_cmd(self, cmd: str) -> tuple[int, str, str]:
        """通过 self._exec_ssh 执行命令，返回 (exit_code, stdout, stderr)。"""
        from app.utils.oper_shell import ShellOperationUtils
        return ShellOperationUtils.execute_remote_command(self._exec_ssh, cmd)

    def _sftp_download(self, remote_path: str) -> bytes:
        """通过 self._exec_ssh 的 SFTP 下载单个文件，返回 bytes。"""
        sftp = self._exec_ssh.open_sftp()
        try:
            with sftp.open(remote_path, 'rb') as f:
                return f.read()
        finally:
            sftp.close()

    def _remote_rm(self, path: str) -> None:
        """删除执行机上的临时文件（失败可忽略）。"""
        try:
            self._exec_cmd(f"rm -f '{path}'")
        except Exception:
            pass

    def _cleanup_plan_a_zips(self, report_code: str) -> None:
        """清理方案A在执行机工作目录生成的3个临时zip（须在 SSH 关闭前调用）。"""
        for zip_name in ('jmeter-reports.zip', 'jmeter-logs.zip', 'results.zip'):
            self._remote_rm(f'{self.remote_dir}/{zip_name}')

    # ──────────────────────────────────────────────────────────────────────────
    #  MD5 签名采集
    # ──────────────────────────────────────────────────────────────────────────

    async def _snapshot_src_md5(self) -> None:
        """采集三个源文件的原始 MD5 签名并写库，供恢复收集时校验一致性。
        若 create_collecting_record 已在创建记录时写入 MD5，则跳过重复采集。
        """
        from app.db.sqlalchemy import async_session_factory
        from app.core.base_crud import BaseCRUD
        from .model import PerfReportModel

        # 创建记录时已预写 MD5，直接跳过
        async with async_session_factory() as db:
            report = await BaseCRUD(PerfReportModel, db).get_by_id_crud(self.report_id)
        if report and (report.src_log_md5 or report.src_jtl_md5 or report.src_report_md5):
            self._log('INFO', f'MD5已在创建记录时写入，跳过重复采集  '
                              f'log={report.src_log_md5}  jtl={report.src_jtl_md5}  '
                              f'rpt={report.src_report_md5[:8] if report.src_report_md5 else ""}...')
            return

        from app.common.commands import SNAPSHOT_SRC_MD5
        try:
            cmd = SNAPSHOT_SRC_MD5.format(remote_dir=self.remote_dir)
            _, out, _ = await asyncio.to_thread(self._exec_cmd, cmd)

            log_md5 = jtl_md5 = rpt_md5 = ''
            for part in out.split():
                if part.startswith('LOG_MD5:'):   log_md5 = part[8:]
                elif part.startswith('JTL_MD5:'): jtl_md5 = part[8:]
                elif part.startswith('RPT_MD5:'): rpt_md5 = part[8:]

            if log_md5 or jtl_md5 or rpt_md5:
                async with async_session_factory() as db:
                    await BaseCRUD(PerfReportModel, db).update_crud(self.report_id, {
                        'src_log_md5':    log_md5 or None,
                        'src_jtl_md5':    jtl_md5 or None,
                        'src_report_md5': rpt_md5 or None,
                    })
                self._log('INFO', f'MD5签名已写库  log={log_md5}  jtl={jtl_md5}  rpt={rpt_md5[:8] if rpt_md5 else ""}...')
            else:
                self._log('WARN', 'MD5签名结果为空，源文件可能尚未生成')
        except Exception as e:
            self._log('WARN', f'MD5签名采集失败（不影响本次收集）：{e}')

    # ──────────────────────────────────────────────────────────────────────────
    #  tar.gz 内存解压
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_tar(tar_bytes: bytes) -> tuple[dict[str, bytes], dict[str, bytes], bytes]:
        """
        内存解压 tar.gz，按路径前缀分类：

        Returns:
            report_files: {相对路径: bytes}  — reports/report/ 下的文件
            jtl_files:    {相对路径: bytes}  — results/ 下 .jtl 文件
            master_log:   bytes              — logs/jmeter.log
        """
        report_files: dict[str, bytes] = {}
        jtl_files:    dict[str, bytes] = {}
        master_log:   bytes            = b''

        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode='r:gz') as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                f = tf.extractfile(member)
                if f is None:
                    continue
                data = f.read()
                name = member.name

                if name.startswith('reports/report/'):
                    rel = name[len('reports/report/'):]
                    if rel:
                        report_files[rel] = data
                elif name.startswith('results/') and name.endswith('.jtl'):
                    rel = name[len('results/'):]
                    if rel:
                        jtl_files[rel] = data
                elif name == 'logs/jmeter.log':
                    master_log = data

        return report_files, jtl_files, master_log

    # ──────────────────────────────────────────────────────────────────────────
    #  方案B 内存打包（3 个独立 zip）
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_report_zip(report_files: dict[str, bytes]) -> bytes:
        """将 HTML 报告文件打成 zip，内部路径格式：report/index.html。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for rel, data in report_files.items():
                zf.writestr(f'report/{rel}', data)
        return buf.getvalue()

    @staticmethod
    def _build_logs_zip(
        master_log:     bytes,
        worker_logs:    list[tuple[str, bytes]],
        is_distributed: bool,
    ) -> bytes:
        """
        将日志文件打成 jmeter-logs.zip。
        单机：内部名为 jmeter.log；分布式：jmeter-master.log + jmeter-worker-N.log。
        """
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            arc_name = 'jmeter-master.log' if is_distributed else 'jmeter.log'
            if master_log:
                zf.writestr(arc_name, master_log)
            for filename, data in worker_logs:
                zf.writestr(filename, data)
        return buf.getvalue()

    @staticmethod
    def _build_jtl_zip(jtl_files: dict[str, bytes]) -> bytes:
        """将 JTL 结果文件打成 results.zip，内部路径格式：results/{filename}.jtl。"""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for rel, data in jtl_files.items():
                zf.writestr(f'results/{rel}', data)
        return buf.getvalue()

    # ──────────────────────────────────────────────────────────────────────────
    #  DB 写库
    # ──────────────────────────────────────────────────────────────────────────

    async def _update_db_status(self, status: int, file_size: int, remark: str) -> None:
        """更新 perf_reports 记录状态：2-完成 / 4-失败。"""
        if self._is_stop_requested():
            _stop_requested.discard(self.report_id)
            return

        from app.db.sqlalchemy import async_session_factory
        from app.core.base_crud import BaseCRUD
        from .model import PerfReportModel

        payload: dict = {
            'report_status': status,
            'file_size':     file_size,
            'remark':        remark,
        }
        if status == 2:
            payload['generated_at'] = datetime.now()

        async with async_session_factory() as db:
            await BaseCRUD(PerfReportModel, db).update_crud(self.report_id, payload)

    # ──────────────────────────────────────────────────────────────────────────
    #  主入口
    # ──────────────────────────────────────────────────────────────────────────

    async def run(self) -> None:
        """
        四步收集流程：
          Step 1 SSH连接：建连 exec 机、分布式验证 worker 连通性、探测 MinIO 确定方案
          Step 2 远端打包：方案A 打3个zip；方案B 打1个tar.gz
          Step 3 文件下载：仅方案B；分布式并行relay收集worker日志
          Step 4 打包上传：report → log → jtl
        """
        # 立即写入初始进度状态——在任何可能失败的操作之前，确保 SSE 有数据可推
        _collect_state[self.report_id] = {
            'step': 0, 'pct': 0, 'step_name': '初始化',
            'detail': '正在准备收集...', 'status': 'running',
        }

        # finally 块依赖的变量提前初始化为安全默认值，防止 try 内出错时引发 NameError
        from app.core.minio_client import MinioClient
        bucket            = ''
        collector_log_key = ''
        report_code       = ''
        report_name       = ''
        file_size         = 0

        try:
            from app.db.sqlalchemy import async_session_factory
            from app.core.base_crud import BaseCRUD
            from app.api.v1.performance.scenario.model import PerfScenarioModel
            from app.api.v1.performance.config.crud import PerfMachineCRUD
            from app.utils.oper_shell import ShellOperationUtils
            from config import config
            from .model import PerfReportModel

            bucket = config.MINIO_BUCKET

            # 读取报告记录（获取 report_code、report_name）
            async with async_session_factory() as db:
                report = await BaseCRUD(PerfReportModel, db).get_by_id_crud(self.report_id)
            if not report:
                self._set_state(0, 0, '初始化', f'报告记录不存在 report_id={self.report_id}', status='failed')
                logger.error(f'[ReportCollector] report_id={self.report_id} 不存在，跳过')
                return

            report_code       = report.report_code
            report_name       = report.report_name
            collector_log_key = f'report/{report_code}/collector_process.log'

            report_zip_key = f'report/{report_code}/jmeter-reports.zip'
            log_zip_key    = f'report/{report_code}/jmeter-logs.zip'
            jtl_zip_key    = f'report/{report_code}/results.zip'

            self._log('INFO', f'开始收集压测报告 {report_name}  report_id={self.report_id}')

            # 加载 worker 机器列表（分布式模式）
            async with async_session_factory() as db:
                scenario = await BaseCRUD(PerfScenarioModel, db).get_by_id_crud(self.scenario_id)
            worker_machines = []
            is_distributed = bool(scenario and scenario.is_distributed == 1)
            if is_distributed:
                async with async_session_factory() as db:
                    worker_machines = await PerfMachineCRUD(db).get_available_machines(
                        limit=scenario.node_count or 1, machine_type=2
                    )
                self._log('INFO', f'分布式模式，worker 节点数={len(worker_machines)}')

            # 分布式始终方案B（平台中转），单机视 MinIO 可达性决定
            report_files: dict[str, bytes] = {}
            jtl_files:    dict[str, bytes] = {}
            master_log:   bytes            = b''
            worker_logs:  list[tuple[str, bytes]] = []
            tar_remote_path = ''


            # ────────────────────────────────────────────────────────────────
            # Step 1: SSH 连接
            # ────────────────────────────────────────────────────────────────
            self._set_state(1, 3, 'SSH连接', f'连接 {self.exec_ip}:{self.exec_ssh_port}...')

            def _connect():
                return ShellOperationUtils.get_ssh_client(
                    self.exec_ip, target_port=self.exec_ssh_port,
                    max_retries=2, retry_interval=2.0,
                    credential=self._credential,
                )

            self._exec_ssh = await asyncio.to_thread(_connect)
            self._log('INFO', f'exec 机 SSH 已建连 {self.exec_ip}:{self.exec_ssh_port}')

            # 查询执行机名称（用于前端显示，查不到则降级用IP）
            ssh_user = self._credential.get('ssh_user', 'root')
            exec_machine_name = self.exec_ip
            try:
                from app.api.v1.performance.config.model import PerfConfigMachineModel
                from sqlalchemy import select as _sa_select
                async with async_session_factory() as _mdb:
                    _mname = (await _mdb.execute(
                        _sa_select(PerfConfigMachineModel.name).where(
                            PerfConfigMachineModel.ip == self.exec_ip
                        )
                    )).scalar_one_or_none()
                    if _mname:
                        exec_machine_name = _mname
            except Exception:
                pass

            conn_sub: list[dict] = []

            if is_distributed:
                # 分布式：平台机→Master SSH + Master→各Worker relay 连接条目
                conn_sub.append({
                    'name':   f'平台机→{exec_machine_name}（Master）',
                    'url':    f'{self.exec_ip}:{self.exec_ssh_port}',
                    'status': 'done',
                    'detail': '',
                })
                from app.utils.oper_shell import _RelayClient
                for i, wm in enumerate(worker_machines):
                    w_port = wm.ssh_port or 22
                    try:
                        relay = _RelayClient(
                            self._exec_ssh, wm.ip, w_port, ssh_user,
                            owns_master=False,
                            password=self._credential.get('ssh_password'),
                        )
                        _, out, _ = ShellOperationUtils.execute_remote_command(relay, 'echo ok')
                        ok = 'ok' in out
                        conn_sub.append({
                            'name':   f'Master→{wm.name or wm.ip}（Worker{i + 1}）',
                            'url':    f'{wm.ip}:{w_port}',
                            'status': 'done' if ok else 'failed',
                            'detail': '' if ok else '连通性验证失败',
                        })
                    except Exception as we:
                        conn_sub.append({
                            'name':   f'Master→{wm.name or wm.ip}（Worker{i + 1}）',
                            'url':    f'{wm.ip}:{w_port}',
                            'status': 'failed',
                            'detail': str(we)[:80],
                        })
            else:
                # 单机：探测 MinIO 可达性，结果作为唯一连接条目展示
                # 用 /minio/health/live 健康端点探测（无需认证）；避免 TCP_PROBE 在 HTTPS 场景下端口判断错误
                from app.common.commands import HTTP_PROBE
                protocol  = 'https' if config.MINIO_SECURE else 'http'
                minio_url  = f'{protocol}://{config.MINIO_ENDPOINT}'
                health_url = f'{minio_url}/minio/health/live'
                try:
                    probe_cmd = HTTP_PROBE.format(url=health_url, timeout=10)
                    _, probe_out, _ = await asyncio.to_thread(self._exec_cmd, probe_cmd)
                    # R:curl:0 或 R:wget:0 表示 HTTP 响应可达
                    self._plan_a = 'R:curl:0' in probe_out or 'R:wget:0' in probe_out
                    self._log('INFO', f'MinIO可达性探测：{probe_out.strip()[:80]} → 方案{"A" if self._plan_a else "B"}')
                    conn_sub.append({
                        'name':   '执行机→Minio',
                        'url':    minio_url,
                        'status': 'done' if self._plan_a else 'failed',
                        'detail': '' if self._plan_a else 'MinIO不可达，降级方案B（平台中转）',
                    })
                except Exception as pe:
                    self._log('WARN', f'MinIO可达性探测失败，降级方案B：{pe}')
                    self._plan_a = False
                    conn_sub.append({
                        'name':   '执行机→Minio',
                        'url':    minio_url,
                        'status': 'failed',
                        'detail': f'探测失败：{str(pe)[:60]}',
                    })

            plan_label = 'a' if self._plan_a else 'b'
            plan_desc  = '执行机直传' if self._plan_a else '平台中转'
            self._set_state(
                1, 10, 'SSH连接',
                f'连接成功，{"MinIO可达→方案A("+plan_desc+")" if self._plan_a else "MinIO不可达或分布式→方案B("+plan_desc+")"}',
                plan=plan_label,
                sub_items={'connections': conn_sub},
            )

            await self._snapshot_src_md5()

            if self._is_stop_requested():
                self._log('INFO', '收到强制停止信号，中止收集（Step1后）')
                _stop_requested.discard(self.report_id)
                return

            # ────────────────────────────────────────────────────────────────
            # Step 2: 远端打包
            # ────────────────────────────────────────────────────────────────
            if self._plan_a:
                # 方案A：在执行机工作目录打3个zip
                from app.common.commands import ZIP_REPORT_DIR, ZIP_MASTER_LOG, ZIP_RESULTS_DIR

                self._set_state(2, 12, '远端打包', '打包 HTML 报告...',
                                sub_items={
                                    'report_zip': {'status': 'running',  'detail': ''},
                                    'log_zip':    {'status': 'pending',  'detail': ''},
                                    'jtl_zip':    {'status': 'pending',  'detail': ''},
                                })
                if self.include_report:
                    cmd = ZIP_REPORT_DIR.format(remote_dir=self.remote_dir, report_name=report_code)
                    _, out, _ = await asyncio.to_thread(self._exec_cmd, cmd)
                    if 'ZIP_EXIT:0' not in out:
                        raise RuntimeError(f'HTML报告打包失败：{out[:200]}')
                rpt_status = 'done' if self.include_report else 'skip'

                self._set_state(2, 17, '远端打包', '打包 JMeter 日志...',
                                sub_items={
                                    'report_zip': {'status': rpt_status, 'detail': ''},
                                    'log_zip':    {'status': 'running',  'detail': ''},
                                    'jtl_zip':    {'status': 'pending',  'detail': ''},
                                })
                if self.include_log:
                    cmd = ZIP_MASTER_LOG.format(remote_dir=self.remote_dir, arc_name='jmeter.log')
                    _, out, _ = await asyncio.to_thread(self._exec_cmd, cmd)
                    if 'ZIP_EXIT:0' not in out:
                        raise RuntimeError(f'日志打包失败：{out[:200]}')
                log_status = 'done' if self.include_log else 'skip'

                self._set_state(2, 22, '远端打包', '打包 JTL 结果...',
                                sub_items={
                                    'report_zip': {'status': rpt_status, 'detail': ''},
                                    'log_zip':    {'status': log_status, 'detail': ''},
                                    'jtl_zip':    {'status': 'running',  'detail': ''},
                                })
                if self.include_jtl:
                    cmd = ZIP_RESULTS_DIR.format(remote_dir=self.remote_dir)
                    _, out, _ = await asyncio.to_thread(self._exec_cmd, cmd)
                    if 'ZIP_EXIT:0' not in out:
                        raise RuntimeError(f'JTL打包失败：{out[:200]}')
                jtl_status = 'done' if self.include_jtl else 'skip'

                self._set_state(2, 35, '远端打包', '三个zip打包完成',
                                sub_items={
                                    'report_zip': {'status': rpt_status, 'detail': ''},
                                    'log_zip':    {'status': log_status, 'detail': ''},
                                    'jtl_zip':    {'status': jtl_status, 'detail': ''},
                                })
            else:
                # 方案B：在执行机打单个tar.gz（按 include 标志选择文件）
                self._set_state(2, 12, '远端打包', '在执行机压缩报告文件...')
                tar_remote_path = f'/tmp/{report_code}.tar.gz'

                def _remote_tar():
                    path_checks: list[str] = []
                    if self.include_report:
                        path_checks.append('[ -d reports/report ] && _p="$_p reports/report"')
                    if self.include_jtl:
                        path_checks.append('[ -d results ]        && _p="$_p results"')
                    if self.include_log:
                        path_checks.append('[ -f logs/jmeter.log ] && _p="$_p logs/jmeter.log"')
                    checks_str = '; '.join(path_checks) + '; ' if path_checks else ''
                    cmd = (
                        f"cd '{self.remote_dir}' && "
                        f"_p=''; "
                        f"{checks_str}"
                        f"if [ -n \"$_p\" ]; then tar czf '{tar_remote_path}' $_p 2>/dev/null; echo \"TAR_EXIT:$?\"; "
                        f"else echo 'TAR_EXIT:1'; fi"
                    )
                    _, out, _ = self._exec_cmd(cmd)
                    if 'TAR_EXIT:0' not in out:
                        raise RuntimeError(f'远端tar失败，输出：{out[:200]}')

                await asyncio.to_thread(_remote_tar)
                self._set_state(2, 35, '远端打包', '远端压缩完成')

            if self._is_stop_requested():
                self._log('INFO', '收到强制停止信号，中止收集（Step2后）')
                _stop_requested.discard(self.report_id)
                if tar_remote_path:
                    try: await asyncio.to_thread(self._remote_rm, tar_remote_path)
                    except Exception: pass
                return

            # ────────────────────────────────────────────────────────────────
            # Step 3: 文件下载（仅方案B）
            # ────────────────────────────────────────────────────────────────
            if not self._plan_a:
                self._set_state(3, 37, '文件下载', f'SFTP下载 {self.exec_ip}...',
                                sub_items={'master': {'status': 'running', 'detail': '下载中'}})

                tar_bytes = await asyncio.to_thread(self._sftp_download, tar_remote_path)
                size_mb = len(tar_bytes) / 1024 / 1024
                self._set_state(3, 50, '文件下载', f'下载完成 {size_mb:.1f}MB，解压中...',
                                sub_items={'master': {'status': 'done', 'detail': f'{size_mb:.1f}MB'}})

                asyncio.ensure_future(asyncio.to_thread(self._remote_rm, tar_remote_path))

                report_files, jtl_files, master_log = self._extract_tar(tar_bytes)
                self._log('INFO', f'解压完成：HTML={len(report_files)} 文件，jtl={len(jtl_files)} 文件')

                # 分布式：并行 relay 收集各 worker jmeter.log
                if is_distributed and worker_machines:
                    from app.utils.oper_shell import _RelayClient
                    total = len(worker_machines)
                    master_done = {'status': 'done', 'detail': f'{size_mb:.1f}MB'}
                    worker_status = [{'ip': wm.ip, 'status': 'pending', 'detail': ''} for wm in worker_machines]
                    self._set_state(3, 52, '文件下载', f'并行收集 {total} 个worker日志...',
                                    sub_items={'master': master_done, 'workers': list(worker_status)})

                    async def _fetch_worker_log(idx: int, wm) -> tuple[str, bytes] | None:
                        w_port = wm.ssh_port or 22
                        worker_status[idx]['status'] = 'running'
                        self._set_state(3, 52, '文件下载', f'收集 worker-{idx+1} ({wm.ip}) 日志...',
                                        sub_items={'master': master_done, 'workers': list(worker_status)})
                        try:
                            log_path = f'{self.remote_dir}/logs/jmeter.log'

                            def _relay_cat():
                                relay = _RelayClient(
                                    self._exec_ssh, wm.ip, w_port, ssh_user,
                                    owns_master=False,
                                    password=self._credential.get('ssh_password'),
                                )
                                stdin, stdout, stderr = relay.exec_command(f'cat {log_path}')
                                data = stdout.read()
                                stdout.channel.recv_exit_status()
                                return data

                            data = await asyncio.to_thread(_relay_cat)
                            kb = len(data) / 1024
                            worker_status[idx] = {'ip': wm.ip, 'status': 'done', 'detail': f'{kb:.1f}KB'}
                            done_count = sum(1 for w in worker_status if w['status'] == 'done')
                            pct = 52 + int(done_count / total * 13)
                            self._set_state(3, pct, '文件下载', f'{done_count}/{total} 台完成',
                                            sub_items={'master': master_done, 'workers': list(worker_status)})
                            self._log('INFO', f'worker-{idx+1} ({wm.ip}) 日志={len(data)} 字节')
                            return (f'jmeter-worker-{idx + 1}.log', data)
                        except Exception as e:
                            worker_status[idx] = {'ip': wm.ip, 'status': 'failed', 'detail': str(e)[:60]}
                            self._set_state(3, 52, '文件下载', f'worker-{idx+1} ({wm.ip}) 收集失败',
                                            sub_items={'master': master_done, 'workers': list(worker_status)})
                            self._log('WARN', f'worker-{idx+1} ({wm.ip}) 日志收集失败：{e}')
                            return None

                    results = await asyncio.gather(
                        *[_fetch_worker_log(i, wm) for i, wm in enumerate(worker_machines)]
                    )
                    worker_logs = [r for r in results if r is not None]

                self._set_state(3, 65, '文件下载', '文件下载完成')

                if self._is_stop_requested():
                    self._log('INFO', '收到强制停止信号，中止收集（Step3后）')
                    _stop_requested.discard(self.report_id)
                    return

            # ────────────────────────────────────────────────────────────────
            # Step 4: 打包上传（report → log → jtl）
            # ────────────────────────────────────────────────────────────────
            pct_base = 35 if self._plan_a else 65

            def _sub(rs='pending', ls='pending', js='pending', rd='', ld='', jd='') -> dict:
                return {
                    'report': {'status': rs, 'detail': rd},
                    'log':    {'status': ls, 'detail': ld},
                    'jtl':    {'status': js, 'detail': jd},
                }

            self._set_state(4, pct_base + 3, '打包上传', '上传 HTML 报告...', sub_items=_sub('running'))

            if self._plan_a:
                # 方案A：生成预签名 PUT URL，通过 exec_ssh 执行 curl 直传
                from app.common.commands import MINIO_PUT_ZIP

                async def _put_plan_a(zip_name: str, minio_key: str) -> int:
                    """通过 exec 机 curl PUT 上传，返回文件字节大小。"""
                    put_url = MinioClient.presign_put(bucket, minio_key, expires_minutes=60)
                    cmd = MINIO_PUT_ZIP.format(remote_dir=self.remote_dir, zip_name=zip_name, url=put_url)
                    _, out, _ = await asyncio.to_thread(self._exec_cmd, cmd)
                    # 同时校验 curl 退出码和 HTTP 状态码（需均为成功才算上传完成）
                    exit_ok = 'PUT_EXIT:0' in out
                    http_ok = bool(re.search(r'HTTP:2\d\d', out))
                    if not exit_ok or not http_ok:
                        http_m = re.search(r'HTTP:(\S+)', out)
                        body_m = re.search(r'BODY:(.*)', out, re.DOTALL)
                        http_info = f'HTTP {http_m.group(1)}' if http_m else ''
                        body_info = (body_m.group(1) or '').strip()[:300] if body_m else out[:200]
                        raise RuntimeError(f'curl PUT失败（{zip_name}）：{http_info} {body_info}'.strip())
                    try:
                        def _stat():
                            return MinioClient.get_client().stat_object(bucket, minio_key)
                        stat = await asyncio.to_thread(_stat)
                        return stat.size
                    except Exception:
                        return 0

                rpt_size = 0
                if self.include_report:
                    rpt_size = await _put_plan_a(f'{report_code}.zip', report_zip_key)
                rs = 'done' if self.include_report else 'skip'
                rd = f'{rpt_size / 1024 / 1024:.2f}MB' if rpt_size else ''
                self._set_state(4, pct_base + 20, '打包上传', '上传日志...',
                                sub_items=_sub(rs, 'running', rd=rd))

                log_size = 0
                if self.include_log:
                    log_size = await _put_plan_a('jmeter-logs.zip', log_zip_key)
                ls = 'done' if self.include_log else 'skip'
                ld = f'{log_size / 1024 / 1024:.2f}MB' if log_size else ''
                self._set_state(4, pct_base + 40, '打包上传', '上传 JTL...',
                                sub_items=_sub(rs, ls, 'running', rd=rd, ld=ld))

                jtl_size = 0
                if self.include_jtl:
                    jtl_size = await _put_plan_a('results.zip', jtl_zip_key)
                js = 'done' if self.include_jtl else 'skip'
                jd = f'{jtl_size / 1024 / 1024:.2f}MB' if jtl_size else ''
                file_size = rpt_size + log_size + jtl_size
                self._set_state(4, 100, '打包上传', '全部上传完成', status='done',
                                sub_items=_sub(rs, ls, js, rd=rd, ld=ld, jd=jd))

            else:
                # 方案B：平台内存构建zip后 put_object 上传
                rpt_size = 0
                if self.include_report and report_files:
                    rz = self._build_report_zip(report_files)
                    await MinioClient.put_object(bucket, report_zip_key, rz, 'application/zip')
                    rpt_size = len(rz)
                rs = 'done' if self.include_report else 'skip'
                rd = f'{rpt_size / 1024 / 1024:.2f}MB' if rpt_size else ''
                self._set_state(4, pct_base + 10, '打包上传', '上传日志...',
                                sub_items=_sub(rs, 'running', rd=rd))

                log_size = 0
                if self.include_log and (master_log or worker_logs):
                    lz = self._build_logs_zip(master_log, worker_logs, is_distributed)
                    await MinioClient.put_object(bucket, log_zip_key, lz, 'application/zip')
                    log_size = len(lz)
                ls = 'done' if self.include_log else 'skip'
                ld = f'{log_size / 1024 / 1024:.2f}MB' if log_size else ''
                self._set_state(4, pct_base + 20, '打包上传', '上传 JTL...',
                                sub_items=_sub(rs, ls, 'running', rd=rd, ld=ld))

                jtl_size = 0
                if self.include_jtl and jtl_files:
                    jz = self._build_jtl_zip(jtl_files)
                    await MinioClient.put_object(bucket, jtl_zip_key, jz, 'application/zip')
                    jtl_size = len(jz)
                js = 'done' if self.include_jtl else 'skip'
                jd = f'{jtl_size / 1024 / 1024:.2f}MB' if jtl_size else ''
                file_size = rpt_size + log_size + jtl_size
                self._set_state(4, 100, '打包上传', '全部上传完成', status='done',
                                sub_items=_sub(rs, ls, js, rd=rd, ld=ld, jd=jd))

            skipped: list[str] = []
            if not self.include_report: skipped.append('HTML报告（MD5不一致）')
            if not self.include_jtl:    skipped.append('JTL结果（MD5不一致）')
            if not self.include_log:    skipped.append('日志（MD5不一致）')
            success_remark = '跳过：' + ' / '.join(skipped) if skipped else ''

            # 查询 MinIO 中 report_code 目录下所有已上传文件的实际总大小（含恢复收集时保留的历史文件）
            try:
                def _sum_dir_size():
                    return sum(
                        obj.size or 0
                        for obj in MinioClient.get_client().list_objects(
                            bucket, prefix=f'report/{report_code}/', recursive=True
                        )
                    )
                file_size = await asyncio.to_thread(_sum_dir_size)
            except Exception as _size_err:
                self._log('WARN', f'查询MinIO目录大小失败，使用本次上传量估算：{_size_err}')

            await self._update_db_status(2, file_size, remark=success_remark)
            self._log('INFO', f'报告收集完成 {report_name}，总大小={file_size / 1024 / 1024:.2f}MB')

        except Exception as e:
            if self._is_stop_requested():
                _stop_requested.discard(self.report_id)
                self._log('INFO', f'收集因强制停止中断：{e}')
                return
            remark = str(e)[:500]
            cur = _collect_state.get(self.report_id, {})
            self._set_state(
                cur.get('step', 0), cur.get('pct', 0),
                cur.get('step_name', '初始化'),
                f'失败：{remark}', status='failed',
            )
            self._log('ERROR', f'收集失败：{e}')
            # collector_log_key 为空表示 DB 读取前就失败，report_id 无从确认
            if collector_log_key:
                try:
                    await self._update_db_status(4, file_size, remark=remark)
                except Exception as dbe:
                    self._log('ERROR', f'写DB失败：{dbe}')

        finally:
            # 方案A：在关闭SSH前清理执行机临时zip文件（report_code 已在 try 内设置）
            if self._plan_a and self._exec_ssh and report_code:
                try:
                    self._cleanup_plan_a_zips(report_code)
                except Exception:
                    pass

            if self._exec_ssh:
                try:
                    self._exec_ssh.close()
                except Exception:
                    pass

            # 上传收集流程日志（仅当已知 collector_log_key 时才上传）
            if collector_log_key and bucket:
                try:
                    log_bytes = '\n'.join(self._log_lines).encode('utf-8')
                    await MinioClient.put_object(bucket, collector_log_key, log_bytes, 'text/plain; charset=utf-8')
                except Exception as le:
                    logger.warning(f'[ReportCollector] 流程日志上传失败：{le}')

            asyncio.ensure_future(self._cleanup_state_later())


async def collect_report_async(
    report_id:      int,
    scenario_id:    int,
    remote_dir:     str,
    exec_ip:        str,
    exec_ssh_port:  int,
    ssh_user:       Optional[str] = None,
    ssh_password:   Optional[str] = None,
    include_log:    bool = True,
    include_jtl:    bool = True,
    include_report: bool = True,
) -> None:
    """
    对外异步接口：由 perf_log_collector 在 create_collecting_record 之后 fire-and-forget 调用。
    恢复收集时可通过 include_* 参数指定仅收集 MD5 一致的文件。
    任何异常均在内部捕获，不向上传播。
    """
    try:
        await ReportCollector(
            report_id=report_id,
            scenario_id=scenario_id,
            remote_dir=remote_dir,
            exec_ip=exec_ip,
            exec_ssh_port=exec_ssh_port,
            ssh_user=ssh_user,
            ssh_password=ssh_password,
            include_log=include_log,
            include_jtl=include_jtl,
            include_report=include_report,
        ).run()
    except Exception as e:
        logger.exception(f'[ReportCollector] 未捕获异常 report_id={report_id}: {e}')
