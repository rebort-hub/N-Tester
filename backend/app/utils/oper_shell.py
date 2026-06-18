#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
import base64
import os
import time
import uuid
from typing import Optional, Tuple

import paramiko

from app.common import SSH_CONN_ERROR_SIGNS
from config import config
from app.corelibs.logger import logger


def _is_ssh_conn_error(exit_code: int, stderr: str) -> bool:
    """判断 SSH 命令失败是否属于连接/认证问题（而非远端应用错误）。
        SSH exit_code=255 表示 SSH 本身失败（连接/认证），不是远端命令失败；
        同时检查 stderr 中的关键词，覆盖部分非标准实现。
    """
    if exit_code == 255:
        return True
    lower = stderr.lower()
    return any(sign in lower for sign in SSH_CONN_ERROR_SIGNS)


class _RelayClient:
    """
    通过 Master 中继连接 Worker 的 SSH 客户端代理（不需要 TCP 转发）。

    控制机 SSH 到 Master，由 Master 的 shell 执行 `ssh worker 'command'` 或
    `scp master_tmp worker:path`，无需 AllowTcpForwarding，无需额外工具。

    接口与 paramiko.SSHClient 兼容（exec_command / close），
    文件上传由 ShellOperationUtils.upload_file_via_sftp 检测后走 relay 路径。

    命令编码策略：
      命令先 base64 编码再传给 worker，彻底规避嵌套 SSH 的引号转义问题，
      支持 URL、路径、管道、|| 等任意内容。
    """

    def __init__(self, master_ssh: paramiko.SSHClient,
                 worker_ip: str, worker_port: int, worker_user: str,
                 owns_master: bool = True, password: Optional[str] = None,
                 worker_key_path: Optional[str] = None):
        self._master = master_ssh
        self._worker_ip = worker_ip
        self._worker_port = worker_port
        self._user = worker_user
        self._owns_master = owns_master
        self._password = password  # 密码兜底，密钥认证失败时通过 sshpass 重试
        # Master 执行 ssh/scp 到 Worker 时使用的私钥路径（DEFAULT_SSH_KEY_PATH）
        self._worker_key_path = worker_key_path or config.DEFAULT_SSH_KEY_PATH

    # noinspection PyMethodMayBeStatic
    def exec_command(self, command: str):
        """
        将 command base64 编码后通过 Master 的 shell 在 Worker 上执行。
        返回值与 paramiko.SSHClient.exec_command 相同：(stdin, stdout, stderr)。
        认证策略：先用密钥（BatchMode=yes），若 SSH 返回 exit=255（认证失败）
        且配置了密码，则自动通过 sshpass 重试；密码经 base64 传递，规避特殊字符注入。
        """
        encoded = base64.b64encode(command.encode("utf-8")).decode("ascii")
        inner = f"'echo {encoded} | base64 -d | bash'"
        key_opt = f"-i {self._worker_key_path} " if self._worker_key_path else ""

        if self._password:
            pwd_b64 = base64.b64encode(self._password.encode()).decode("ascii")
            # 先尝试密钥；exit=255 表示 SSH 认证/连接失败，再通过 sshpass 兜底
            relay_cmd = (
                f"ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
                f"{key_opt}-o ConnectTimeout=30 -p {self._worker_port} "
                f"{self._user}@{self._worker_ip} {inner} 2>/dev/null; "
                f"_r=$?; [ $_r -ne 255 ] && exit $_r; "
                f"SSHPASS=$(echo {pwd_b64} | base64 -d) "
                f"sshpass -e ssh -o StrictHostKeyChecking=no "
                f"-o ConnectTimeout=30 -p {self._worker_port} "
                f"{self._user}@{self._worker_ip} {inner}"
            )
        else:
            relay_cmd = (
                f"ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
                f"{key_opt}-o ConnectTimeout=30 -p {self._worker_port} "
                f"{self._user}@{self._worker_ip} {inner}"
            )
        return self._master.exec_command(relay_cmd)

    def close(self):
        if not self._owns_master:
            return
        try:
            self._master.close()
        except Exception:
            pass


class ShellOperationUtils:
    """操作Linux工具类：建立连接、执行sh脚本."""

    # ------------------------------------------------------------------ #
    #  跳板机通道策略
    # ------------------------------------------------------------------ #

    @staticmethod
    def _load_private_key(key_path: str):
        """
        从文件加载私钥，返回 PKey 实例；加载失败返回 None（不抛出异常）。

        与 SSH 连接过程完全解耦：加载阶段的格式/口令问题在此消化，
        不会影响后续连接阶段的网络错误（SSHException / OSError 等）正常向上传播。

        兼容 paramiko 2.x（逐类型尝试）和 3.x（PKey.from_path 统一接口，DSSKey 已移除）。

        :param key_path: 私钥文件绝对路径
        :return: 加载成功的 PKey 实例；
                 格式无效 / 类型不支持 / 有口令保护（无交互环境无法解密）时返回 None
        """
        # paramiko 3.x 统一接口
        if hasattr(paramiko.PKey, 'from_path'):
            try:
                return paramiko.PKey.from_path(key_path)
            except paramiko.PasswordRequiredException:
                logger.warning(f"密钥 {key_path} 有口令保护，无法在无交互环境中使用")
                return None
            except Exception as e:
                logger.warning(f"密钥 {key_path} 加载失败: {e}")
                return None
        # paramiko 2.x fallback：逐类型尝试（DSSKey 在 2.x 中存在，3.x 已移除）
        key_classes = [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]
        if hasattr(paramiko, 'DSSKey'):
            key_classes.insert(1, paramiko.DSSKey)
        for cls in key_classes:
            try:
                return cls.from_private_key_file(key_path)
            except paramiko.PasswordRequiredException:
                logger.warning(f"密钥 {key_path} 有口令保护，无法在无交互环境中使用")
                return None
            except Exception:
                continue
        logger.warning(f"密钥 {key_path} 格式无效或类型不支持，跳过密钥认证")
        return None

    @staticmethod
    def _ssh_connect(
        client: paramiko.SSHClient,
        hostname: str, port: int,
        user: str, key_path: Optional[str], password: Optional[str],
        sock=None,
    ) -> None:
        """
        在已创建的 paramiko.SSHClient 上建立 SSH 连接。

        认证策略（优先级从高到低）：
          1. key_path 有效 → _load_private_key 预加载密钥（与连接解耦）
             → 加载成功：密钥认证，只尝试一次；
               - AuthenticationException（服务端明确拒绝）属确定性失败，不重试，直接降级密码；
               - 网络级 SSHException / OSError 等直接向上传播，由外层 get_ssh_client 重试循环处理。
             → 加载失败（格式无效 / 口令保护）：跳过密钥认证，直接尝试密码。
          2. 密钥不可用或认证失败 → 若有 password 则降级密码认证。
          3. 均无可用凭据 → 抛出 ValueError。
        look_for_keys=False / allow_agent=False 确保只使用显式传入的凭据，
        避免 paramiko 默认混入 ~/.ssh/ 或系统 SSH Agent 中的其他密钥。

        :param client:   已创建但尚未连接的 paramiko.SSHClient 实例（原地修改）
        :param hostname: 目标主机 IP 或域名
        :param port:     目标 SSH 端口
        :param user:     SSH 登录用户名
        :param key_path: 本地私钥文件绝对路径；None / 不存在 / 加载失败时跳过密钥认证
        :param password: SSH 登录密码；密钥不可用或认证失败后作为降级凭据
        :param sock:     已建立的 TCP 通道（direct-tcpip），为 None 则直接 TCP 连接
        :raises paramiko.AuthenticationException:
                         密钥认证失败且无密码可用时透传认证异常
        :raises ValueError: 无可用凭据（key_path 无效且 password 为空）时抛出
        :raises paramiko.SSHException | OSError 等:
                         网络级错误（banner 读取失败、连接超时等）直接向上传播
        :return:         None（连接状态写入 client 实例）
        """
        base: dict = {
            "hostname": hostname, "port": port,
            "username": user, "timeout": 30,
            "look_for_keys": False, "allow_agent": False,
        }
        if sock:
            base["sock"] = sock

        if key_path and os.path.exists(key_path):
            pkey = ShellOperationUtils._load_private_key(key_path)
            if pkey is None:
                logger.warning(
                    f"节点 {hostname} 密钥 {key_path} 无法加载，跳过密钥认证"
                )
            else:
                try:
                    # 使用预加载的 PKey 对象，避免 connect 阶段再次解析文件
                    client.connect(**base, pkey=pkey)
                    return
                except paramiko.AuthenticationException as e:
                    # 服务端明确拒绝（目标机未添加此公钥），属确定性失败，不重试
                    if not password:
                        raise
                    logger.warning(
                        f"节点 {hostname} 密钥认证失败，降级密码认证。原因: {e}"
                    )
                # 注意：网络级错误（SSHException / OSError）不在此捕获，直接向上传播

        if password:
            client.connect(**base, password=password)
        else:
            raise ValueError(
                f"节点 {hostname} 缺少 SSH 认证凭据（私钥或密码均未配置）"
            )


    @staticmethod
    def _make_direct_tcpip(
        jump_host: str, jump_port: int,
        target_host: str, target_port: int,
        user: str, key_path: Optional[str], password: Optional[str],
    ) -> Tuple[paramiko.Channel, paramiko.SSHClient]:
        """
        策略1: direct-tcpip 通道（要求 Master AllowTcpForwarding yes）。
        返回 (channel, jump_client)；jump_client 需在 target client 关闭时一并关闭。
        """
        jc = paramiko.SSHClient()
        jc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ShellOperationUtils._ssh_connect(jc, jump_host, jump_port, user, key_path, password)
        try:
            ch = jc.get_transport().open_channel(
                "direct-tcpip", (target_host, target_port), ("", 0)
            )
        except Exception:
            jc.close()
            raise
        return ch, jc

    @staticmethod
    def _make_relay_client(
        jump_host: str, jump_port: int,
        target_host: str, target_port: int,
        user: str, key_path: Optional[str], password: Optional[str],
        reuse_master_ssh: paramiko.SSHClient = None,
    ) -> "_RelayClient":
        """
        策略2: SSH Relay 方案（不需要 TCP 转发，不需要额外工具）。
        控制机 SSH 到 Master，Master 再 SSH/SCP 到 Worker。
        返回 _RelayClient，接口与 paramiko.SSHClient 兼容。

        reuse_master_ssh: 传入已建立的 Master 连接时直接复用，不重新握手；
                          此时 _RelayClient.owns_master=False，close() 不会关闭该连接。
        """
        if reuse_master_ssh is not None:
            return _RelayClient(reuse_master_ssh, target_host, target_port, user,
                                owns_master=False, password=password)

        master_ssh = paramiko.SSHClient()
        master_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ShellOperationUtils._ssh_connect(master_ssh, jump_host, jump_port, user, key_path, password)
        logger.info(
            f"SSH Relay 模式: 控制机→Master({jump_host}:{jump_port})"
            f"→Worker({target_host}:{target_port})"
        )
        return _RelayClient(master_ssh, target_host, target_port, user, password=password)

    # ------------------------------------------------------------------ #
    #  公共接口
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_ssh_client(host: str, service: str = None,
                       max_retries: int = 3, retry_interval: float = 3.0,
                       jump_host: str = None, jump_port: int = 22,
                       target_port: int = 22,
                       reuse_master_ssh: paramiko.SSHClient = None,
                       credential: dict = None) -> paramiko.SSHClient:
        """
        建立 SSH 连接，失败时自动重试（最多 max_retries 次，含首次）。
        优先使用私钥认证，备选密码认证。

        跳板机支持两种通道策略（自动选择，无需手动配置）：
          策略1: direct-tcpip（要求 Master AllowTcpForwarding yes）
          策略2: SSH Relay —— 控制机→Master→Worker，Master 执行 ssh/scp 命令
                 （不需要 AllowTcpForwarding，不需要 nc/ncat 等额外工具）

        :param host: 目标压力机 IP 或 DNS 域名
        :param service: 服务名（host 为空时使用）
        :param max_retries: 最大尝试次数，默认 3
        :param retry_interval: 重试间隔秒数，默认 3s
        :param jump_host: 跳板机地址（为空则直连）
        :param jump_port: 跳板机 SSH 端口，默认 22
        :param target_port: 目标节点 SSH 端口，默认 22
        :param reuse_master_ssh: 传入已建立的 Master 连接时直接复用，跳过 direct-tcpip 探测，
                                  不重新握手 Master。仅在 jump_host 非空时有效。
        :param credential: 机器级 SSH 凭证 dict（ssh_user, ssh_password），优先于全局 .env 配置
        :return: paramiko.SSHClient 或 _RelayClient（接口兼容）
        """
        hostname = host if host is not None else service
        user     = (credential or {}).get("ssh_user") or config.SSH_DEFAULT_USER or "root"
        key_path = config.PLATFORM_SSH_KEY_PATH
        password = (credential or {}).get("ssh_password") or (config.SSH_DEFAULT_PASSWORD or None)

        # ── 快速路径：复用已有 Master 连接，直接构造 _RelayClient，跳过握手和 direct-tcpip 探测 ──
        if jump_host and reuse_master_ssh is not None:
            return ShellOperationUtils._make_relay_client(
                jump_host, jump_port, hostname, target_port,
                user, key_path, password,
                reuse_master_ssh=reuse_master_ssh,
            )

        last_exc: Exception = None
        for attempt in range(1, max_retries + 1):
            jump_client = None
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                # ── 有跳板机：先尝试 direct-tcpip，失败则回退 Relay ──
                if jump_host:
                    try:
                        sock, jump_client = ShellOperationUtils._make_direct_tcpip(
                            jump_host, jump_port, hostname, target_port,
                            user, key_path, password,
                        )
                        ShellOperationUtils._ssh_connect(
                            client, hostname, target_port, user, key_path, password, sock=sock
                        )

                        # jump_client 需随 client 一起关闭
                        _orig = client.close
                        _j = jump_client
                        def _patched(orig=_orig, j=_j):
                            try: orig()
                            except Exception: pass
                            try: j.close()
                            except Exception: pass
                        client.close = _patched
                        return client

                    except Exception as e:
                        if "administratively prohibited" not in str(e).lower():
                            raise
                        logger.warning(
                            f"Master ({jump_host}) AllowTcpForwarding=no，"
                            f"自动回退 SSH Relay 方案: {e}"
                        )
                        if jump_client:
                            try: jump_client.close()
                            except Exception: pass
                        # Relay 方案直接返回（内部已建立 Master 连接）
                        return ShellOperationUtils._make_relay_client(
                            jump_host, jump_port, hostname, target_port,
                            user, key_path, password,
                        )

                # ── 无跳板机：直连 ──
                ShellOperationUtils._ssh_connect(
                    client, hostname, target_port, user, key_path, password
                )
                return client

            except Exception as e:
                last_exc = e
                try: client.close()
                except Exception: pass
                if jump_client:
                    try: jump_client.close()
                    except Exception: pass
                if attempt < max_retries:
                    logger.warning(
                        f"节点 {hostname} SSH 连接失败（第 {attempt}/{max_retries} 次），"
                        f"{retry_interval}s 后重试: {e}"
                    )
                    time.sleep(retry_interval)
                else:
                    logger.error(
                        f"节点 {hostname} SSH 连接失败，已重试 {max_retries} 次，放弃: {e}"
                    )
        raise last_exc

    @staticmethod
    def execute_remote_command(ssh_client, command: str):
        """
        在远程目标机器上执行 Linux 命令。
        兼容 paramiko.SSHClient 和 _RelayClient。

        :param ssh_client: paramiko.SSHClient 或 _RelayClient
        :param command: 要执行的远程 Linux 命令
        :return: (退出码, 标准输出内容, 标准错误内容)
        """
        stdin, stdout, stderr = ssh_client.exec_command(command)
        # 先读完 stdout/stderr 再取退出码，避免 paramiko 竞态：
        # recv_exit_status() 在 stdout.read() 前调用时，exit status 报文可能比最后一段
        # stdout 数据先到达，导致 stdout.read() 对耗时命令读到空内容。
        out = stdout.read().decode()
        err = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, out, err

    @staticmethod
    def _upload_via_relay(relay: _RelayClient, local_file: str,
                          remote_file: str, progress_label: str = "",
                          progress_callback=None) -> None:
        """
        通过 Master Relay 上传文件到 Worker（两步走）：
          1. 控制机 SFTP 文件到 Master 临时目录（进度 0→90%）
          2. Master 执行 scp 将文件推送到 Worker（完成后 100%）
        不需要 TCP 转发，不需要任何额外工具（Master 有 scp 即可）。
        """
        label = f"[{progress_label}]" if progress_label else ""
        master = relay._master
        worker_user = relay._user
        worker_ip = relay._worker_ip
        worker_port = relay._worker_port

        # Step1: 上传到 Master /tmp（避免 Master 磁盘权限问题，用随机名防冲突）
        tmp_name = f"/tmp/.ntdist_{uuid.uuid4().hex}_{os.path.basename(local_file)}"
        logger.info(f"{label} [Relay] 上传到 Master 临时目录: {tmp_name}")
        _last_pct = [-1]

        def _sftp_progress(sent: int, total: int) -> None:
            if total <= 0:
                return
            # SFTP→Master 阶段占 0-90%，保留 10% 给 SCP→Worker
            pct = min(90, int(sent * 90 / total))
            if pct > _last_pct[0]:
                _last_pct[0] = pct
                logger.info(f"{label} [Relay] SFTP→Master {pct}%  ({sent:,}/{total:,} bytes)")
                if progress_callback:
                    progress_callback(pct)

        with master.open_sftp() as sftp:
            sftp.put(local_file, tmp_name, callback=_sftp_progress)

        try:
            # Step2: 确保 Worker 目标目录存在
            remote_dir = os.path.dirname(remote_file).replace("\\", "/")
            if remote_dir:
                exit_code, _, err = ShellOperationUtils.execute_remote_command(
                    relay, f"mkdir -p '{remote_dir}'"
                )
                if exit_code == 255:
                    # SSH 本身失败（Master→Worker 认证/连接问题），提前抛出连接错误
                    raise ConnectionError(f"Master→Worker SSH连接失败（mkdir）: {err.strip()}")

            # Step3: Master scp 推送到 Worker
            if progress_callback:
                progress_callback(92)  # SCP 开始
            key_opt = f"-i {relay._worker_key_path} " if relay._worker_key_path else ""
            scp_cmd = (
                f"scp -o StrictHostKeyChecking=no -o BatchMode=yes "
                f"{key_opt}-o ConnectTimeout=60 -P {worker_port} "
                f"'{tmp_name}' {worker_user}@{worker_ip}:'{remote_file}'"
            )
            logger.info(f"{label} [Relay] Master→Worker scp: {remote_file}")
            _, stdout, stderr = master.exec_command(scp_cmd)
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:
                err = stderr.read().decode().strip()
                if _is_ssh_conn_error(exit_code, err):
                    raise ConnectionError(f"Master→Worker SSH连接失败: {err}")
                raise IOError(f"Master→Worker scp 失败 (exit={exit_code}): {err}")
            logger.info(f"{label} [Relay] 文件已送达 Worker: {remote_file}")
            if progress_callback:
                progress_callback(100)
        finally:
            # 清理 Master 临时文件（忽略错误）
            master.exec_command(f"rm -f '{tmp_name}'")

    @staticmethod
    def master_download_from_minio(
        master_ssh: paramiko.SSHClient,
        minio_url: str,
        tmp_path: str,
        total_size: int,
        progress_callback=None,
        timeout: int = 3600,
    ) -> int:
        """
        通过已建立的 Master SSH 连接，在 Master 机器上执行 curl/wget 从 MinIO 下载文件。
        每2秒轮询 Master 上的文件大小以追踪下载进度，通过 progress_callback 上报 0-100%。

        :param master_ssh: 平台机→Master 的 paramiko.SSHClient
        :param minio_url:  MinIO 预签名下载 URL
        :param tmp_path:   文件在 Master 上的目标路径（如 /tmp/.ntdist_xxx_file.csv）
        :param total_size: 文件总字节数（用于计算百分比）
        :param progress_callback: 可选进度回调 callback(pct: int)，0-100
        :param timeout:    curl/wget 超时秒数，默认 3600
        :return: 命令退出码（0=成功）
        """
        tmp_dir = os.path.dirname(tmp_path)
        # curl 优先，wget 次之，python3 兜底；工具降级与方案A保持一致
        cmd = (
            f"mkdir -p '{tmp_dir}' && ("
            f"  (command -v curl >/dev/null 2>&1"
            f"   && curl -fsSL --max-time {timeout} -o '{tmp_path}' '{minio_url}') ||"
            f"  (command -v wget >/dev/null 2>&1"
            f"   && wget -qO '{tmp_path}' --timeout={timeout} '{minio_url}') ||"
            f"  python3 -c \"import urllib.request; urllib.request.urlretrieve('{minio_url}', '{tmp_path}')\""
            f")"
        )
        _, stdout, stderr = master_ssh.exec_command(cmd)

        # stat 只读 inode 元数据，开销极小；4s 间隔兼顾实时性与 SSH channel 复用压力
        _last_pct = [-1]
        while not stdout.channel.exit_status_ready():
            time.sleep(4)
            try:
                _, p_out, _ = master_ssh.exec_command(
                    f"stat -c '%s' '{tmp_path}' 2>/dev/null || echo 0"
                )
                p_out.channel.recv_exit_status()
                current = int(p_out.read().decode().strip() or "0")
                if total_size > 0:
                    pct = min(99, current * 100 // total_size)
                    if pct != _last_pct[0]:
                        _last_pct[0] = pct
                        if progress_callback:
                            progress_callback(pct)
            except Exception:
                pass

        exit_code = stdout.channel.recv_exit_status()
        if exit_code == 0 and progress_callback:
            progress_callback(100)
        return exit_code

    @staticmethod
    def upload_file_via_sftp(ssh_client, local_file: str, remote_file: str,
                              resume: bool = True, progress_label: str = "",
                              progress_callback=None) -> None:
        """
        上传文件到远端，支持断点续传和进度日志。
        自动识别连接类型：
          - paramiko.SSHClient → 直接 SFTP（含断点续传）
          - _RelayClient       → 通过 Master 中继（先到 Master /tmp，再 scp 到 Worker）

        注意：Relay 模式下不支持断点续传（每次全量覆盖）。

        :param ssh_client: paramiko.SSHClient 或 _RelayClient
        :param local_file: 控制机本地源文件路径
        :param remote_file: 压力机远端目标文件完整路径（POSIX 格式）
        :param resume: 是否启用断点续传（仅直连模式有效）
        :param progress_label: 进度日志前缀，如 "机器名 文件名"
        :param progress_callback: 可选进度回调 callback(pct: int)，在 10% 整数倍时触发
        """
        # Relay 模式：两步中继上传
        if isinstance(ssh_client, _RelayClient):
            ShellOperationUtils._upload_via_relay(ssh_client, local_file, remote_file,
                                                   progress_label, progress_callback)
            return

        # 直连模式：SFTP 含断点续传
        local_size = os.path.getsize(local_file)
        label = f"[{progress_label}]" if progress_label else ""

        with ssh_client.open_sftp() as sftp:
            start_offset = 0

            if resume:
                try:
                    r_size = sftp.stat(remote_file).st_size
                    if r_size == local_size:
                        logger.info(f"{label} 文件已完整，跳过上传: {remote_file}")
                        if progress_callback:
                            progress_callback(100)
                        return
                    if 0 < r_size < local_size:
                        start_offset = r_size
                        logger.info(
                            f"{label} 断点续传：已有 {r_size}/{local_size} 字节，从断点继续"
                        )
                except IOError:
                    pass

            _last_milestone = [-1]

            def _log_pct(sent: int, total: int) -> None:
                if total <= 0:
                    return
                pct = sent * 100 // total
                milestone = pct // 10
                if milestone > _last_milestone[0]:
                    _last_milestone[0] = milestone
                    logger.info(
                        f"{label} 上传进度 {pct}%"
                        f"  ({sent:,}/{total:,} bytes)  → {remote_file}"
                    )
                    if progress_callback:
                        progress_callback(pct)

            if start_offset == 0:
                sftp.put(local_file, remote_file,
                         callback=lambda sent, total: _log_pct(sent, total))
                return

            with open(local_file, "rb") as lf:
                lf.seek(start_offset)
                with sftp.open(remote_file, "ab") as rf:
                    rf.set_pipelined(True)
                    sent = start_offset
                    while True:
                        chunk = lf.read(262144)
                        if not chunk:
                            break
                        rf.write(chunk)
                        sent += len(chunk)
                        _log_pct(sent, local_size)