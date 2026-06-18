#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import asyncio
import collections
import json
import threading
import zlib
import zipfile
from typing import Optional, Dict, AsyncGenerator

from fastapi import HTTPException, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.minio_client import MinioClient
from .collector import _collect_state, _stop_requested
from .crud import PerfReportCRUD
from .model import PerfReportModel
from .schema import PerfReportListRespSchema, PerfReportIdReqSchema

"""
性能测试 - 压测报告 Service
"""

# ── 三级预览缓存 ──────────────────────────────────────────────────────────────
# 1. DB 结果缓存：report_code → zip_key（避免每次预览都查 DB）
_report_zip_key_cache: dict[str, str] = {}
_MAX_ZIP_KEY_CACHE = 200

# 2. ZIP 元数据缓存：report_code → {'size': int, 'cd': {filename: ZipInfo}}
#    首次访问读取 EOCD + Central Directory（几KB），后续请求直接复用
_zip_meta_cache: dict[str, dict] = {}
_MAX_META_CACHE = 50

# 3. 文件内容缓存："{report_code}:{zip_path}" → bytes（命中时 0 次 MinIO 调用）
_file_cache: collections.OrderedDict[str, bytes] = collections.OrderedDict()
_file_etag_cache: dict[str, str] = {}
_file_cache_lock = threading.Lock()
_file_cache_total_bytes = 0
_FILE_CACHE_MAX_BYTES  = 200 * 1024 * 1024  # 200MB 总上限
_FILE_CACHE_MAX_SINGLE =   5 * 1024 * 1024  # 单文件 > 5MB 不缓存


def _fcache_get(key: str) -> bytes | None:
    with _file_cache_lock:
        if key not in _file_cache:
            return None
        _file_cache.move_to_end(key)
        return _file_cache[key]


def _fcache_put(key: str, data: bytes, etag: str) -> None:
    global _file_cache_total_bytes
    if len(data) > _FILE_CACHE_MAX_SINGLE:
        return
    with _file_cache_lock:
        if key in _file_cache:
            return
        _file_cache_total_bytes += len(data)
        _file_cache[key] = data
        _file_etag_cache[key] = etag
        while _file_cache_total_bytes > _FILE_CACHE_MAX_BYTES and _file_cache:
            evicted_key, old = _file_cache.popitem(last=False)
            _file_cache_total_bytes -= len(old)
            _file_etag_cache.pop(evicted_key, None)


def _preview_cache_invalidate(report_code: str) -> None:
    """删除/停止报告时清理该报告的所有预览缓存。"""
    global _file_cache_total_bytes
    _report_zip_key_cache.pop(report_code, None)
    _zip_meta_cache.pop(report_code, None)
    prefix = f'{report_code}:'
    with _file_cache_lock:
        keys = [k for k in _file_cache if k.startswith(prefix)]
        for k in keys:
            _file_cache_total_bytes -= len(_file_cache.pop(k))
            _file_etag_cache.pop(k, None)


# ── ZIP 直接提取（不重新读 CD） ────────────────────────────────────────────────
_LOCAL_HDR_FIXED = 30  # ZIP 本地文件头固定部分长度


class _RangeMinioIO:
    """同步可 seek 的 MinIO 对象读取器，每次 read 只发起对应字节区间的 range GET。

    zipfile.ZipFile 在初始化时通过 seek(-22, 2) + seek(cd_offset, 0) 读取
    EOCD 和 Central Directory；实际文件读取再通过 seek+read。
    所有 IO 均为小范围随机访问，不会触发全量下载。
    """

    def __init__(self, client, bucket: str, key: str, size: int):
        self._client = client
        self._bucket = bucket
        self._key    = key
        self._size   = size
        self._pos    = 0

    def seek(self, pos: int, whence: int = 0) -> int:
        if   whence == 0: self._pos = pos
        elif whence == 1: self._pos += pos
        elif whence == 2: self._pos = self._size + pos
        self._pos = max(0, min(self._pos, self._size))
        return self._pos

    def tell(self) -> int:
        return self._pos

    def read(self, n: int = -1) -> bytes:
        if n < 0:
            n = self._size - self._pos
        n = min(n, self._size - self._pos)
        if n <= 0:
            return b''
        resp = self._client.get_object(self._bucket, self._key, offset=self._pos, length=n)
        try:
            data = resp.read()
        finally:
            resp.close()
            resp.release_conn()
        self._pos += len(data)
        return data

    def readable(self) -> bool:  return True
    def seekable(self) -> bool:  return True
    def writable(self) -> bool:  return False


def _read_zip_entry(rio: '_RangeMinioIO', info: zipfile.ZipInfo) -> bytes:
    """直接按本地文件头偏移读取并解压 zip 条目。

    相比 zipfile.ZipFile.read()，跳过了重新读 EOCD + Central Directory 的开销，
    每次提取只需 2 次 MinIO range GET（本地头 30B + 压缩数据）。
    """
    rio.seek(info.header_offset)
    lhdr = rio.read(_LOCAL_HDR_FIXED)
    fname_len  = int.from_bytes(lhdr[26:28], 'little')
    extra_len  = int.from_bytes(lhdr[28:30], 'little')
    rio.seek(info.header_offset + _LOCAL_HDR_FIXED + fname_len + extra_len)
    raw = rio.read(info.compress_size)
    if info.compress_type == zipfile.ZIP_STORED:
        return raw
    if info.compress_type == zipfile.ZIP_DEFLATED:
        return zlib.decompress(raw, -15)
    raise ValueError(f'不支持的压缩类型: {info.compress_type}')


class PerfReportService:
    """压测报告业务逻辑：列表查询、下载、在线预览、日志查看、删除。"""

    def __init__(self, db: AsyncSession):
        self.db   = db
        self.crud = PerfReportCRUD(db)

    async def get_list(
        self,
        report_name:        Optional[str] = None,
        scenario_code:      Optional[str] = None,
        creator:            Optional[str] = None,
        generated_at_start: Optional[str] = None,
        generated_at_end:   Optional[str] = None,
        page:               int = 1,
        page_size:          int = 20,
    ) -> Dict:
        """分页查询压测报告列表。"""
        items, total = await self.crud.get_list_with_filter(
            report_name=report_name,
            scenario_code=scenario_code,
            creator=creator,
            generated_at_start=generated_at_start,
            generated_at_end=generated_at_end,
            page=page,
            page_size=page_size,
        )
        return {
            'items': [PerfReportListRespSchema.model_validate(r).model_dump() for r in items],
            'total': total,
            'page':  page,
            'page_size': page_size,
        }

    async def get_download_url(self, report_id: int, types: list[str] | None = None) -> dict:
        """生成报告各文件的 Minio 预签名下载 URL（有效期 30 分钟）。

        Args:
            types: 要下载的文件类型列表，可选值 report/log/jtl，缺省=全部三类
        Returns:
            dict: { 'report': url|None, 'log': url|None, 'jtl': url|None }
        """
        report = await self._get_or_404(report_id)
        from config import config
        if not types:
            types = ['report', 'log', 'jtl']
        type_map = {
            'report': (report.object_key,                                          f'{report.report_name}.zip'),
            'log':    (f'report/{report.report_code}/jmeter-logs.zip',             f'{report.report_name}-日志.zip'),
            'jtl':    (f'report/{report.report_code}/results.zip',                 f'{report.report_name}-结果.zip'),
        }
        urls: dict[str, str | None] = {}
        for t in types:
            if t not in type_map:
                continue
            obj_key, fname = type_map[t]
            try:
                urls[t] = MinioClient.presign_get(config.MINIO_BUCKET, obj_key, expires_minutes=30, file_name=fname)
            except Exception:
                urls[t] = None
        return urls


    async def download_batch(self, report_id: int, types: list[str] | None = None):
        """将勾选的报告文件打包进以 report_name 命名的目录后供整体下载。

        外层 zip 使用 ZIP_STORED（无重新压缩），内部路径：
          {report_name}/{report_code}-报告.zip
          {report_name}/{report_code}-日志.zip
          {report_name}/{report_code}-结果.zip
        """
        import io, zipfile
        from urllib.parse import quote
        from fastapi.responses import Response
        from config import config

        report = await self._get_or_404(report_id)
        if not types:
            types = ['report', 'log', 'jtl']

        safe_name = report.report_name.replace('/', '-').replace('\\', '-')

        type_map = {
            'report': (report.object_key,                              f'{safe_name}/{report.report_code}-报告.zip'),
            'log':    (f'report/{report.report_code}/jmeter-logs.zip', f'{safe_name}/{report.report_code}-日志.zip'),
            'jtl':    (f'report/{report.report_code}/results.zip',     f'{safe_name}/{report.report_code}-结果.zip'),
        }

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as zf:
            for t in types:
                if t not in type_map:
                    continue
                obj_key, inner_path = type_map[t]
                try:
                    data = await MinioClient.get_object_bytes(config.MINIO_BUCKET, obj_key)
                    zf.writestr(inner_path, data)
                except Exception:
                    pass

        zip_bytes = buf.getvalue()
        encoded_name = quote(safe_name, safe='')
        return Response(
            content=zip_bytes,
            media_type='application/zip',
            headers={
                'Content-Disposition': (
                    f"attachment; filename=\"{safe_name}.zip\"; "
                    f"filename*=UTF-8''{encoded_name}.zip"
                ),
                'Content-Length': str(len(zip_bytes)),
            },
        )

    async def get_log(self, report_id: int, log_type: str, filename: str | None = None) -> dict:
        """获取日志内容及文件列表。

        Returns:
            dict with keys:
              files   : list of filenames in jmeter-logs.zip (console only)
              content : log text（filename 指定时为单文件；否则合并所有文件）
        """
        report = await self._get_or_404(report_id)

        if log_type == 'collector':
            from config import config
            collector_key = f'report/{report.report_code}/collector_process.log'
            try:
                content = await MinioClient.get_object_bytes(config.MINIO_BUCKET, collector_key)
                return {'files': [], 'content': content.decode('utf-8', errors='replace')}
            except Exception:
                return {'files': [], 'content': '暂无收集流程日志（可能尚未生成或上传失败）'}

        # console：从 jmeter-logs.zip 提取（单文件/指定文件/全部合并）
        try:
            import io as _io
            from config import config
            log_key   = f'report/{report.report_code}/jmeter-logs.zip'
            zip_bytes = await MinioClient.get_object_bytes(config.MINIO_BUCKET, log_key)
            with zipfile.ZipFile(_io.BytesIO(zip_bytes)) as zf:
                names = sorted(zf.namelist())
                if not names:
                    return {'files': [], 'content': '日志文件不存在（jmeter-logs.zip 为空）'}
                if filename:
                    if filename not in names:
                        return {'files': names, 'content': f'文件不存在：{filename}'}
                    return {'files': names, 'content': zf.read(filename).decode('utf-8', errors='replace')}
                if len(names) == 1:
                    return {'files': names, 'content': zf.read(names[0]).decode('utf-8', errors='replace')}
                parts = []
                for name in names:
                    parts.append(f'===== {name} =====')
                    parts.append(zf.read(name).decode('utf-8', errors='replace'))
                return {'files': names, 'content': '\n'.join(parts)}
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f'读取日志失败：{e}')


    async def stream_preview_file(
        self, report_code: str, path: str, base_url: str,
        if_none_match: str | None = None,
    ) -> StreamingResponse | Response:
        """从 Minio zip 包内读取预览文件，三级缓存加速：

        - 方案一：HTTP 缓存头（ETag + Cache-Control），浏览器刷新时静态资源 0 请求
        - 方案二：内存文件缓存，命中时 0 次 MinIO 调用
        - 方案三：DB/stat/CD 元数据缓存，首次访问后仅需 2 次 MinIO range GET 提取文件
        """
        from config import config
        from app.utils.common import get_content_type

        zip_path  = f'report/{path}'
        cache_key = f'{report_code}:{zip_path}'
        is_index  = path in ('index.html', 'index.htm')

        # ── 方案一 + 二：静态资源直接命中内存文件缓存，0 MinIO 调用 ──────────
        if not is_index:
            cached = _fcache_get(cache_key)
            if cached is not None:
                etag = _file_etag_cache.get(cache_key, '')
                if if_none_match and etag and if_none_match == etag:
                    return Response(
                        status_code=304,
                        headers={'ETag': etag, 'Cache-Control': 'public, max-age=3600'},
                    )
                return StreamingResponse(
                    iter([cached]), media_type=get_content_type(path),
                    headers={'Cache-Control': 'public, max-age=3600', 'ETag': etag},
                )

        # ── 方案三：DB 结果缓存，获取 zip_key ────────────────────────────────
        zip_key = _report_zip_key_cache.get(report_code)
        if not zip_key:
            from sqlalchemy import select
            stmt = select(PerfReportModel.object_key).where(
                PerfReportModel.report_code == report_code,
                PerfReportModel.enabled_flag == 1,
            )
            row = (await self.db.execute(stmt)).first()
            if not row:
                raise HTTPException(status_code=404, detail='报告不存在')
            zip_key = row.object_key
            _report_zip_key_cache[report_code] = zip_key
            if len(_report_zip_key_cache) > _MAX_ZIP_KEY_CACHE:
                _report_zip_key_cache.pop(next(iter(_report_zip_key_cache)))

        # ── 提取文件（同步 IO 在线程中执行） ─────────────────────────────────
        def _extract() -> tuple[bytes | None, str]:
            import time
            from config import config as _cfg
            client = MinioClient.get_client()

            # 方案三：zip 元数据缓存（stat + CD），未命中时仅读一次
            # stat_object 在服务重启后首次调用可能因连接池冷启动失败，重试一次
            if report_code not in _zip_meta_cache:
                last_exc: BaseException | None = None
                for attempt in range(2):
                    try:
                        stat = client.stat_object(_cfg.MINIO_BUCKET, zip_key)
                        last_exc = None
                        break
                    except Exception as e:
                        last_exc = e
                        if attempt == 0:
                            time.sleep(0.3)
                if last_exc is not None:
                    raise last_exc
                rio  = _RangeMinioIO(client, _cfg.MINIO_BUCKET, zip_key, stat.size)
                with zipfile.ZipFile(rio) as zf:
                    cd = {info.filename: info for info in zf.infolist()}
                _zip_meta_cache[report_code] = {'size': stat.size, 'cd': cd}
                if len(_zip_meta_cache) > _MAX_META_CACHE:
                    _zip_meta_cache.pop(next(iter(_zip_meta_cache)))

            meta = _zip_meta_cache[report_code]
            if zip_path not in meta['cd']:
                return None, ''

            info = meta['cd'][zip_path]
            etag = f'"{info.CRC:08x}"'

            # 方案三：直接按偏移读取，省去重新读 EOCD + CD 的 2 次 MinIO 调用
            rio  = _RangeMinioIO(client, _cfg.MINIO_BUCKET, zip_key, meta['size'])
            data = _read_zip_entry(rio, info)
            return data, etag

        data, etag = await asyncio.to_thread(_extract)
        if data is None:
            raise HTTPException(status_code=404, detail=f'预览文件不存在：{path}')

        content_type = get_content_type(path)

        # ── index.html：注入 base 标签，不写内容缓存（base_url 含动态主机）────
        if is_index:
            api_prefix = config.API_PREFIX.strip('/')
            base       = f'{base_url}{api_prefix}/v1/performance/reports/preview/{report_code}/'
            html       = data.decode('utf-8', errors='replace').replace(
                '<head>', f'<head><base href="{base}">', 1,
            )
            data       = html.encode('utf-8')
            index_etag = f'{etag[:-1]}-base"'
            if if_none_match and if_none_match == index_etag:
                return Response(status_code=304, headers={'ETag': index_etag, 'Cache-Control': 'no-cache'})
            return StreamingResponse(
                iter([data]), media_type=content_type,
                headers={'Cache-Control': 'no-cache', 'ETag': index_etag},
            )

        # ── 静态资源：写入内存文件缓存 + 返回强缓存头 ────────────────────────
        _fcache_put(cache_key, data, etag)
        if if_none_match and if_none_match == etag:
            return Response(
                status_code=304,
                headers={'ETag': etag, 'Cache-Control': 'public, max-age=3600'},
            )
        return StreamingResponse(
            iter([data]), media_type=content_type,
            headers={'Cache-Control': 'public, max-age=3600', 'ETag': etag},
        )

    async def collect_process_sse(self, report_id: int) -> StreamingResponse:
        """
        报告收集进度 SSE 流：轮询 _collect_state 内存字典，每秒推送一次状态。

        - 若收集已完成（status=2/3），立即返回最终状态后关闭流。
        - 若 _collect_state 中无条目（服务重启等情况），从 DB 读取当前状态推送后关闭。
        - status=running 时持续推流；收到 done/failed 后推最终事件并关闭。
        """
        report = await self._get_or_404(report_id)

        async def _generator() -> AsyncGenerator[str, None]:
            last_pct    = -1
            last_detail = ''

            def _make_terminal(rpt) -> dict:
                status_map = {
                    2: ('done',        5, 100, '完成',    '收集完成'),
                    3: ('interrupted', 0,   0, '中断',    '收集被强制停止'),
                    4: ('failed',      0,   0, '失败',    '收集失败'),
                }
                sse_status, step, pct, step_name, default_detail = status_map.get(
                    rpt.report_status, ('failed', 0, 0, '未知', '未知状态')
                )
                return {
                    'step':      step,
                    'pct':       pct,
                    'step_name': step_name,
                    'detail':    rpt.remark or default_detail,
                    'status':    sse_status,
                }

            # 若 DB 已非收集中状态（可能是重启后重新查看），直接推终态
            if report.report_status != 1:
                yield f"data: {json.dumps(_make_terminal(report), ensure_ascii=False)}\n\n"
                return

            # 轮询内存字典，最多等待 15 分钟（900次 × 1秒）
            for _ in range(900):
                state = _collect_state.get(report_id)

                if state:
                    cur_pct    = state.get('pct', 0)
                    cur_detail = state.get('detail', '')
                    # pct 或 detail 任一变化时推送，确保 worker 失败（pct 不变）也能及时推送
                    if cur_pct != last_pct or cur_detail != last_detail or state.get('status') in ('done', 'failed', 'interrupted'):
                        last_pct    = cur_pct
                        last_detail = cur_detail
                        yield f"data: {json.dumps(state, ensure_ascii=False)}\n\n"
                        if state.get('status') in ('done', 'failed', 'interrupted'):
                            return
                else:
                    # 内存字典中无条目：查 DB 判断是否已结束
                    try:
                        from app.db.sqlalchemy import async_session_factory
                        from app.core.base_crud import BaseCRUD
                        async with async_session_factory() as db:
                            latest = await BaseCRUD(PerfReportModel, db).get_by_id_crud(report_id)
                        if latest and latest.report_status != 1:
                            yield f"data: {json.dumps(_make_terminal(latest), ensure_ascii=False)}\n\n"
                            return
                    except Exception:
                        pass

                await asyncio.sleep(1)

            # 超时兜底
            yield f"data: {json.dumps({'status': 'failed', 'detail': '等待超时'}, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            _generator(),
            media_type='text/event-stream',
            headers={
                'Cache-Control':   'no-cache',
                'X-Accel-Buffering': 'no',
            },
        )

    async def stop(self, data: PerfReportIdReqSchema) -> None:
        """强制停止收集中的报告（status=1 → 3）。

        1. 发送停止信号（_stop_requested），collector.run() 在步骤间检测后返回
        2. 立即更新 DB status=3（中断）
        3. 清理 Minio 残留 zip 和预览文件
        """
        report = await self._get_or_404(data.id)
        if report.report_status != 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='仅收集中（status=1）的报告可强制停止',
            )

        # 发送停止信号，collector.run() 在下一个检测点退出
        _stop_requested.add(data.id)

        # 立即写库，避免 _update_db_status 因检测到停止信号跳过后无人更新
        await self.crud.update_crud(data.id, {
            'report_status': 3,
            'remark':        '用户强制停止',
        })

        # 清理内存进度字典，让 SSE 轮询到 DB 的中断状态
        _collect_state.pop(data.id, None)
        # 清理预览三级缓存，下次预览时重新读取
        _preview_cache_invalidate(report.report_code)

        # 清理 Minio 残留（zip + 预览文件），恢复时将重新上传
        try:
            await MinioClient.remove_object(report.bucket, report.object_key)
        except Exception:
            pass
        try:
            await self._remove_preview_objects(report)
        except Exception:
            pass

    async def resume(self, data: PerfReportIdReqSchema) -> None:
        """恢复中断（status=3）的报告收集。

        通过场景 ID 获取执行机信息，SSH 采集当前源文件 MD5，与 DB 原始签名对比，
        仅对 MD5 一致（未被覆盖）的文件类型启动部分收集；全部不一致则拒绝恢复。
        """
        from sqlalchemy import select
        from app.api.v1.performance.scenario.model import PerfScenarioModel
        from app.api.v1.performance.config.crud import PerfMachineCRUD, PerfParamCRUD
        from app.common.commands import SNAPSHOT_SRC_MD5
        from app.utils.oper_shell import ShellOperationUtils
        from .collector import collect_report_async

        report = await self._get_or_404(data.id)
        if report.report_status not in (3, 4):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='仅中断（status=3）或失败（status=4）的报告可恢复收集',
            )

        # 获取关联场景
        stmt = select(PerfScenarioModel).where(
            PerfScenarioModel.id == report.scenario_id,
            PerfScenarioModel.enabled_flag == 1,
        )
        scenario = (await self.db.execute(stmt)).scalar_one_or_none()
        if not scenario:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='关联场景不存在')

        # 通过场景类型确定执行机
        machine_crud = PerfMachineCRUD(self.db)
        if scenario.is_distributed == 1:
            machine = await machine_crud.get_master_machine()
        else:
            machines = await machine_crud.get_available_machines(limit=1, machine_type=3)
            machine = machines[0] if machines else None
        if not machine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='未找到可用的执行机')

        # 远端工作目录
        param_crud = PerfParamCRUD(self.db)
        remote_dir = (await param_crud.get_param_value('PERF_WORKER_DATA_DIR', '/data/jmeter/')).rstrip('/')

        # SSH 凭证（密码 Fernet 解密）
        exec_ip   = machine.ip
        exec_port = machine.ssh_port or 22
        ssh_user: Optional[str] = machine.ssh_user or None
        ssh_pwd:  Optional[str] = None
        if machine.ssh_password:
            try:
                from app.utils.crypto import decrypt_field
                ssh_pwd = decrypt_field(machine.ssh_password)
            except Exception:
                pass

        # SSH 采集当前源文件 MD5
        _cred: dict = {}
        if ssh_user: _cred['ssh_user']     = ssh_user
        if ssh_pwd:  _cred['ssh_password'] = ssh_pwd

        def _fetch_md5() -> str:
            ssh = ShellOperationUtils.get_ssh_client(
                exec_ip, target_port=exec_port, max_retries=2, retry_interval=2.0,
                credential=_cred,
            )
            try:
                cmd = SNAPSHOT_SRC_MD5.format(remote_dir=remote_dir)
                _, out, _ = ShellOperationUtils.execute_remote_command(ssh, cmd)
                return out
            finally:
                try: ssh.close()
                except Exception: pass

        try:
            md5_out = await asyncio.to_thread(_fetch_md5)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f'SSH 连接失败，无法校验 MD5：{e}',
            )

        # 解析当前 MD5
        cur_log = cur_jtl = cur_rpt = ''
        for part in md5_out.split():
            if part.startswith('LOG_MD5:'):   cur_log = part[8:]
            elif part.startswith('JTL_MD5:'): cur_jtl = part[8:]
            elif part.startswith('RPT_MD5:'): cur_rpt = part[8:]

        # 与 DB 存储的原始签名对比，确定恢复范围
        orig_log = report.src_log_md5    or ''
        orig_jtl = report.src_jtl_md5    or ''
        orig_rpt = report.src_report_md5 or ''

        if not (orig_log or orig_jtl or orig_rpt):
            # 原始签名均为空（快照在中止前未完成），无法校验，允许完整恢复
            include_log = include_jtl = include_report = True
        else:
            include_log    = bool(orig_log and cur_log and orig_log == cur_log)
            include_jtl    = bool(orig_jtl and cur_jtl and orig_jtl == cur_jtl)
            include_report = bool(orig_rpt and cur_rpt and orig_rpt == cur_rpt)
            if not (include_log or include_jtl or include_report):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='源文件 MD5 全部不一致（源文件可能已被新压测覆盖），无法恢复收集',
                )

        # 清理 Minio 残留（上次中断前可能已部分上传）
        try:
            await MinioClient.remove_object(report.bucket, report.object_key)
        except Exception:
            pass
        try:
            await self._remove_preview_objects(report)
        except Exception:
            pass
        # 清理预览三级缓存
        _preview_cache_invalidate(report.report_code)

        # 恢复 DB status=1（收集中）
        await self.crud.update_crud(data.id, {'report_status': 1, 'remark': ''})

        # 清除可能残留的停止信号（上次强制停止后原任务未消费该信号即已结束）
        _stop_requested.discard(data.id)

        # fire-and-forget 启动收集任务
        asyncio.ensure_future(collect_report_async(
            report_id=data.id,
            scenario_id=report.scenario_id,
            remote_dir=remote_dir,
            exec_ip=exec_ip,
            exec_ssh_port=exec_port,
            ssh_user=ssh_user,
            ssh_password=ssh_pwd,
            include_log=include_log,
            include_jtl=include_jtl,
            include_report=include_report,
        ))

    async def delete(self, data: PerfReportIdReqSchema) -> None:
        """删除报告：移除 Minio zip 文件和预览文件目录，软删 DB 记录。

        收集中(status=1)的报告同样支持删除：清理内存进度状态后软删 DB，
        后台收集任务会在下次写库时静默失败（软删后 enabled_flag=0，不影响其他数据）。
        """
        report = await self._get_or_404(data.id)

        # 若正在收集，清理内存进度字典，使关联的 SSE 流在下次轮询时感知到结束
        _collect_state.pop(data.id, None)
        # 清理预览三级缓存
        _preview_cache_invalidate(report.report_code)

        # 删除 zip
        try:
            await MinioClient.remove_object(report.bucket, report.object_key)
        except Exception as e:
            from app.corelibs.logger import logger
            logger.warning(f'[PerfReport] 删除 zip 失败 id={data.id}: {e}')

        # 删除预览文件（遍历 report_code 前缀下所有对象）
        try:
            await self._remove_preview_objects(report)
        except Exception as e:
            from app.corelibs.logger import logger
            logger.warning(f'[PerfReport] 删除预览文件失败 id={data.id}: {e}')

        # 软删 DB
        await self.crud.soft_delete_crud([data.id])

    async def _remove_preview_objects(self, report: PerfReportModel) -> None:
        """枚举并删除 Minio report/{report_code}/ 前缀下所有对象（3个zip + 过程日志 + 预览文件）。"""
        import asyncio
        from config import config

        preview_prefix = f'report/{report.report_code}/'

        def _list_and_delete():
            client = MinioClient.get_client()
            objects = list(client.list_objects(config.MINIO_BUCKET, prefix=preview_prefix, recursive=True))
            for obj in objects:
                client.remove_object(config.MINIO_BUCKET, obj.object_name)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _list_and_delete)

    async def _get_or_404(self, report_id: int) -> PerfReportModel:
        """查询报告记录，不存在或已软删除时抛 404。"""
        obj = await self.crud.get_by_id_crud(report_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='报告不存在')
        return obj