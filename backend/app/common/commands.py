#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
"""
性能模块 Linux 命令模板集中管理。

用法：
    from app.common.commands import JMETER_DIR_INIT
    cmd = JMETER_DIR_INIT.format(remote_dir='/data/jmeter/')

占位符统一使用 {name} 格式；命令中原有的 shell { } 均转义为 {{ }}。
"""

# ─────────────────────────────────────────────────────────────────────────────
# §1  目录与文件管理
# ─────────────────────────────────────────────────────────────────────────────

"""
递归创建目录（幂等，目录已存在时静默忽略）
{path}: 目标路径，如 '/data/jmeter/results'
"""
MKDIR_P = "mkdir -p '{path}'"

"""
强制删除单个文件（文件不存在时静默忽略）
{path}: 文件完整路径，如 '/tmp/report.tar.gz'
"""
RM_FILE = "rm -f '{path}'"

"""
计算文件 MD5（输出仅含 hash 值）
{path}: 文件完整路径，如 '/data/jmeter/data.csv'
"""
MD5SUM_FILE = "md5sum '{path}' | awk '{{print $1}}'"

"""
获取文件字节大小（文件不存在时输出 0）
{path}: 文件完整路径，如 '/data/jmeter/data.csv'
"""
STAT_FILESIZE = "stat -c '%s' '{path}' 2>/dev/null || echo 0"

"""
初始化 JMeter 工作目录：创建 results/logs/reports 子目录，
清空上次 HTML 报告目录，清空 jmeter.log 文件，输出 dir_done 供调用方校验。
{remote_dir}: JMeter 工作目录，如 '/data/jmeter/'
"""
JMETER_DIR_INIT = (
    'bash -l -c "'
    "cd '{remote_dir}' && mkdir -p results logs reports && "
    "rm -rf ./reports/report && > ./logs/jmeter.log && echo dir_done"
    '"'
)

# ─────────────────────────────────────────────────────────────────────────────
# §2  JMeter 进程管理
# ─────────────────────────────────────────────────────────────────────────────

"""
统计当前运行的 JMeter 进程数（精确匹配 ApacheJMeter.jar，输出纯数字）
"""
JMETER_PROC_COUNT = (
    "pgrep -f ApacheJMeter 2>/dev/null | wc -l || "
    "ps aux 2>/dev/null | grep -v grep | grep -c ApacheJMeter || echo 0"
)

"""
查找 ApacheJMeter.jar 进程的 PID（取第一条，无则输出空）
"""
JMETER_FIND_PID = (
    "ps -ef | grep -v grep | grep 'ApacheJMeter.jar' | awk '{print $2}' | head -1"
)

"""
检测指定 PID 的进程是否存活，输出 alive 或 dead
{pid}: 进程 PID，如 '12345'
"""
PID_ALIVE_CHECK = "kill -0 {pid} 2>/dev/null && echo alive || echo dead"

"""
强制 kill 指定 PID（SIGKILL，进程不存在时静默忽略）
{pid}: 进程 PID，如 '12345'
"""
KILL_JMETER_BY_PID = "kill -9 {pid} 2>/dev/null || true"

"""
按进程名强制结束所有 JMeter 进程（用于 stop 兜底）
"""
KILL_JMETER_BY_NAME = "pkill -9 -f ApacheJMeter 2>/dev/null || true"

"""
后台 nohup 启动 JMeter（bash -l 加载 .bash_profile 环境变量）。
stdout/stderr 重定向到 /dev/null 使 SSH 信道即时返回，nohup 日志写入 jmeter_nohup.out。
{remote_dir}  : JMeter 工作目录，如 '/data/jmeter/'
{jmeter_args} : 完整 JMeter 命令行参数（不含 nohup 和重定向），
                如 'jmeter -n -t test.jmx -l results/result.jtl'
"""
JMETER_NOHUP_START = (
    'bash -l -c "'
    "cd '{remote_dir}' && "
    "nohup {jmeter_args} </dev/null > ./logs/jmeter_nohup.out 2>&1 &"
    '" > /dev/null 2>&1'
)

# ─────────────────────────────────────────────────────────────────────────────
# §3  日志读取与完成检测
# ─────────────────────────────────────────────────────────────────────────────

"""
增量读取 jmeter_nohup.out（从第 N 行开始，输出新增行）；
分隔符 ---PROC_CHECK--- 后附 PID 存活检测结果，二者合并为一次 SSH 调用。
{remote_dir}  : JMeter 工作目录，如 '/data/jmeter/'
{file_offset} : 已读取的行偏移（下一次从该行开始），初始值为 1
{proc_check}  : 存活检测子命令，如 "kill -0 12345 2>/dev/null && echo 12345 || echo ''"
"""
TAIL_LOG_INCREMENTAL = (
    "cd '{remote_dir}' && "
    "tail -n +{file_offset} ./logs/jmeter_nohup.out 2>/dev/null; "
    "echo '---PROC_CHECK---'; "
    "{proc_check}"
)

"""
一次 SSH 读取压测完成判断所需全部信息：
jmeter.log 是否存在 / result.jtl 是否存在 / jmeter.log 后50行 / nohup.out 后20行。
{remote_dir}: JMeter 工作目录，如 '/data/jmeter/'
"""
JMETER_COMPLETION_CHECK = (
    "cd '{remote_dir}' 2>/dev/null; "
    "echo '---LOG_EXISTS---'; [ -f logs/jmeter.log ] && echo yes || echo no; "
    "echo '---JTL_EXISTS---'; [ -f results/result.jtl ] && echo yes || echo no; "
    "echo '---LOG_TAIL---'; tail -50 logs/jmeter.log 2>/dev/null; "
    "echo '---NOHUP_TAIL---'; tail -20 logs/jmeter_nohup.out 2>/dev/null; "
    "echo '---END---'"
)

# ─────────────────────────────────────────────────────────────────────────────
# §4  网络连通性探测
# ─────────────────────────────────────────────────────────────────────────────

"""
在远端机器用 curl/wget 探测 HTTP URL 可达性（任意 HTTP 响应均视为连通）。
输出格式：R:curl:<exit_code> / R:wget:<exit_code> / R:none:0
{url}    : 目标 HTTP URL，如 'http://minio:9000/health/live'
{timeout}: 超时秒数，如 10
"""
HTTP_PROBE = (
    "if command -v curl >/dev/null 2>&1; then "
    "  curl -s --head --max-time {timeout} '{url}' >/dev/null 2>&1; echo \"R:curl:$?\"; "
    "elif command -v wget >/dev/null 2>&1; then "
    "  wget -q --spider --timeout={timeout} '{url}' >/dev/null 2>&1; echo \"R:wget:$?\"; "
    "else echo 'R:none:0'; fi"
)

"""
在远端机器用 python3 socket 探测 TCP 端口（无 nc 依赖）。
输出：0（通）或 1（不通）
{host}   : 目标主机，如 '192.168.1.10'
{port}   : 目标端口，如 8086
{timeout}: 超时秒数，如 5
"""
TCP_PROBE = (
    "python3 -c \""
    "import socket; s=socket.socket(); s.settimeout({timeout}); "
    "r=s.connect_ex(('{host}', {port})); s.close(); "
    "print(0 if r==0 else 1)\""
)

"""
在远端机器探测 MinIO 预签名 URL 可达性（curl/wget Range 请求，同时校验网络 + 凭证有效性）。
输出格式：R:curl:<exit_code>:<error> / R:wget:<exit_code>:<error> / R:none:127:curl/wget 均未安装
{minio_url}: MinIO 预签名 URL
{timeout}  : 超时秒数，如 10
"""
MINIO_URL_PROBE = (
    "if command -v curl >/dev/null 2>&1; then "
    "  ERR=$(curl -fsS --max-time {timeout} -r 0-0 -o /dev/null '{minio_url}' 2>&1); CODE=$?; "
    "  echo \"R:curl:$CODE:$ERR\"; "
    "elif command -v wget >/dev/null 2>&1; then "
    "  ERR=$(wget -q --timeout={timeout} --header='Range: bytes=0-0' -O /dev/null '{minio_url}' 2>&1); CODE=$?; "
    "  echo \"R:wget:$CODE:$ERR\"; "
    "else echo 'R:none:127:curl/wget 均未安装'; fi"
)

# ─────────────────────────────────────────────────────────────────────────────
# §5  文件下载与分发
# ─────────────────────────────────────────────────────────────────────────────

"""
在压力机上按优先级下载文件：curl → wget → python3 urllib（绕过 Cloudflare 拦截）。
{remote_dir} : 压力机目标目录，如 '/data/jmeter/'
{remote_file}: 压力机目标文件完整路径，如 '/data/jmeter/data.csv'
{minio_url}  : MinIO 预签名下载 URL
"""
DOWNLOAD_FROM_URL = (
    "mkdir -p '{remote_dir}' && ("
    "  (command -v curl >/dev/null 2>&1"
    "   && curl -fsSL --max-time 3600 -o '{remote_file}' '{minio_url}') ||"
    "  (command -v wget >/dev/null 2>&1"
    "   && wget -qO '{remote_file}' --timeout=3600 '{minio_url}') ||"
    "  python3 -c \""
    "import urllib.request; urllib.request.urlretrieve('{minio_url}', '{remote_file}')\""
    ")"
)

"""
Master 通过 SCP 将文件推送到 Worker（BatchMode=yes 避免密码提示阻塞）。
{worker_port}    : Worker SSH 端口，如 22
{tmp_master_path}: Master 上的临时文件路径，如 '/tmp/.ntdist_abc.csv'
{ssh_user}       : SSH 用户名，如 'root'
{worker_ip}      : Worker IP，如 '192.168.1.20'
{remote_file}    : Worker 目标文件完整路径，如 '/data/jmeter/data.csv'
"""
SCP_PUSH_TO_WORKER = (
    "scp -o StrictHostKeyChecking=no -o BatchMode=yes "
    "-o ConnectTimeout=60 -P {worker_port} "
    "'{tmp_master_path}' {ssh_user}@{worker_ip}:'{remote_file}'"
)

"""
Master 通过 SSH 中继在 Worker 上创建目录（base64 编码防特殊字符）。
{worker_port}: Worker SSH 端口，如 22
{ssh_user}   : SSH 用户名，如 'root'
{worker_ip}  : Worker IP，如 '192.168.1.20'
{encoded}    : base64 编码后的 mkdir 命令，如 'bWtkaXIgLXAgL2RhdGEvam1ldGVyLw=='
"""
MKDIR_VIA_RELAY = (
    "ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
    "-o ConnectTimeout=30 -p {worker_port} "
    "{ssh_user}@{worker_ip} "
    "'echo {encoded} | base64 -d | bash'"
)

"""
Master 通过 SSH 中继轮询 Worker 文件大小（追踪 SCP 传输进度）。
{worker_port}: Worker SSH 端口，如 22
{ssh_user}   : SSH 用户名，如 'root'
{worker_ip}  : Worker IP，如 '192.168.1.20'
{p_encoded}  : base64 编码后的 stat 命令
"""
POLL_FILESIZE_VIA_RELAY = (
    "ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
    "-p {worker_port} {ssh_user}@{worker_ip} "
    "'echo {p_encoded} | base64 -d | bash'"
)

# ─────────────────────────────────────────────────────────────────────────────
# §6  SSH 中继执行（Master → Worker）
# ─────────────────────────────────────────────────────────────────────────────

"""
密钥认证（BatchMode=yes，密钥不通立即返回非零）
{worker_port}: Worker SSH 端口，如 22
{ssh_user}   : SSH 用户名，如 'root'
{worker_ip}  : Worker IP，如 '192.168.1.20'
{worker_cmd} : 在 Worker 上执行的命令，如 'echo ok'
"""
SSH_RELAY_KEY = (
    "ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
    "-o ConnectTimeout=10 -p {worker_port} {ssh_user}@{worker_ip} "
    "'{worker_cmd}' 2>/dev/null"
)

"""
sshpass 密码认证（密码 base64 编码防特殊字符注入）
{pwd_b64}    : base64 编码后的 SSH 密码
{worker_port}: Worker SSH 端口，如 22
{ssh_user}   : SSH 用户名，如 'root'
{worker_ip}  : Worker IP，如 '192.168.1.20'
{worker_cmd} : 在 Worker 上执行的命令，如 'echo ok'
"""
SSH_RELAY_SSHPASS = (
    "SSHPASS=$(echo {pwd_b64} | base64 -d) "
    "sshpass -e ssh -o StrictHostKeyChecking=no "
    "-o ConnectTimeout=10 -p {worker_port} {ssh_user}@{worker_ip} "
    "'{worker_cmd}' 2>/dev/null"
)

"""
密钥优先，失败自动降级 sshpass 密码认证（联调/分发场景通用）
{worker_port}: Worker SSH 端口，如 22
{ssh_user}   : SSH 用户名，如 'root'
{worker_ip}  : Worker IP，如 '192.168.1.20'
{worker_cmd} : 在 Worker 上执行的命令，如 'hostname'
{pwd_b64}    : base64 编码后的 SSH 密码（密钥失败时使用）
"""
SSH_RELAY_KEY_PWD_FALLBACK = (
    "{{ "
    "ssh -o StrictHostKeyChecking=no -o BatchMode=yes "
    "-o ConnectTimeout=10 -p {worker_port} {ssh_user}@{worker_ip} "
    "'{worker_cmd}' 2>/dev/null && echo 'AUTH:key'; "
    "}} || {{"
    "SSHPASS=$(echo {pwd_b64} | base64 -d) "
    "sshpass -e ssh -o StrictHostKeyChecking=no "
    "-o ConnectTimeout=10 -p {worker_port} {ssh_user}@{worker_ip} "
    "'{worker_cmd}' 2>/dev/null && echo 'AUTH:password'; "
    "}}"
)

# ─────────────────────────────────────────────────────────────────────────────
# §7  报告收集
# ─────────────────────────────────────────────────────────────────────────────

"""
在执行机压缩报告目录为单个 tar.gz（用变量累积实际存在的路径，避免 tar 因路径不存在报错）。
{remote_dir}: JMeter 工作目录，如 '/data/jmeter/'
{tar_path}  : 远端 tar 包输出路径，如 '/tmp/RPT260613103022.tar.gz'
"""
TAR_REPORT_FILES = (
    "cd '{remote_dir}' && "
    "_p=''; "
    "[ -d reports/report ] && _p=\"$_p reports/report\"; "
    "[ -d results ]        && _p=\"$_p results\"; "
    "[ -f logs/jmeter.log ] && _p=\"$_p logs/jmeter.log\"; "
    "if [ -n \"$_p\" ]; then tar czf '{tar_path}' $_p 2>/dev/null; echo \"TAR_EXIT:$?\"; "
    "else echo 'TAR_EXIT:1'; fi"
)

"""
压测完成、收集任务初始化时一次 SSH 采集 3 个原始 MD5 签名：
jmeter.log（单文件）/ result.jtl（单文件）/ reports/report 目录（全文件有序聚合哈希）。
结果写库后作为唯一原始指纹，强制停止后恢复收集时用于校验源文件是否被覆盖。
输出格式：LOG_MD5:<hash> JTL_MD5:<hash> RPT_MD5:<hash>（文件不存在时对应 hash 为空串）
{remote_dir}: JMeter 工作目录，如 '/data/jmeter/'
"""
SNAPSHOT_SRC_MD5 = (
    "cd '{remote_dir}' && "
    "L=$(md5sum logs/jmeter.log 2>/dev/null | awk '{{print $1}}'); "
    "J=$(md5sum results/result.jtl 2>/dev/null | awk '{{print $1}}'); "
    "R=$(find reports/report -type f 2>/dev/null | sort | xargs md5sum 2>/dev/null | md5sum | awk '{{print $1}}'); "
    "echo \"LOG_MD5:$L JTL_MD5:$J RPT_MD5:$R\""
)

# ─────────────────────────────────────────────────────────────────────────────
# §8  压测报告打包上传（方案 A：执行机直传 MinIO）
# ─────────────────────────────────────────────────────────────────────────────

"""
在执行机上将 HTML 报告目录（reports/report/）打成 {report_name}.zip，输出在工作目录。
zip 内路径格式：report/index.html，与 stream_preview_file 预览路径匹配。
{remote_dir}  : JMeter 工作目录（PERF_WORKER_DATA_DIR）
{report_name} : 报告展示名称，即 zip 文件名前缀
"""
ZIP_REPORT_DIR = (
    "cd '{remote_dir}' && "
    "python3 -c \"import shutil; shutil.make_archive('{report_name}','zip','reports','report')\""
    "; echo ZIP_EXIT:$?"
)

"""
在执行机上将 logs/jmeter.log 打成 jmeter-logs.zip，输出在工作目录。
{remote_dir}: JMeter 工作目录
{arc_name}  : zip 内文件名；单机='jmeter.log'；分布式 master='jmeter-master.log'
"""
ZIP_MASTER_LOG = (
    "cd '{remote_dir}' && "
    "python3 -c \"import zipfile; z=zipfile.ZipFile('jmeter-logs.zip','w',zipfile.ZIP_DEFLATED); z.write('logs/jmeter.log','{arc_name}'); z.close()\""
    "; echo ZIP_EXIT:$?"
)

"""
在执行机上将 results/ 目录打成 results.zip，输出在工作目录。
{remote_dir}: JMeter 工作目录
"""
ZIP_RESULTS_DIR = (
    "cd '{remote_dir}' && "
    "python3 -c \"import shutil; shutil.make_archive('results','zip','.','results')\""
    "; echo ZIP_EXIT:$?"
)

"""
在执行机上通过 curl 将工作目录中的 zip PUT 到 MinIO 预签名 URL。
响应体写入临时文件，HTTP 状态码和响应摘要一并输出，方便定位 Cloudflare/签名等错误。
{remote_dir}: JMeter 工作目录（cd 后用相对路径引用 zip）
{zip_name}  : zip 文件名（在 remote_dir 下），如 'jmeter-logs.zip'
{url}       : MinIO 预签名 PUT URL
"""
MINIO_PUT_ZIP = (
    "cd '{remote_dir}' && "
    "TF=$(mktemp); "
    "HTTP=$(curl -sS -X PUT --data-binary @'{zip_name}' "
    "--max-time 3600 -o \"$TF\" -w '%{{http_code}}' '{url}' 2>&1); "
    "EXIT=$?; "
    "BODY=$(head -c 300 \"$TF\" 2>/dev/null | tr '\\n' ' '); "
    "rm -f \"$TF\"; "
    "echo \"PUT_EXIT:$EXIT HTTP:$HTTP BODY:$BODY\""
)