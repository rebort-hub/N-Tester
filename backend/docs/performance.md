# 性能测试文件管理与分发模块说明

> 本文档覆盖文件上传、下载、替换、删除，以及共享分发、分割分发、清除分发的完整业务逻辑、前置配置和使用说明。

---

## 目录

1. [模块概述](#1-模块概述)
2. [前置配置](#2-前置配置)
3. [文件上传](#3-文件上传)
4. [文件下载](#4-文件下载)
5. [文件替换与删除](#5-文件替换与删除)
6. [共享分发](#6-共享分发)
7. [分割分发](#7-分割分发)
8. [清除分发](#8-清除分发)
9. [SSH 连接机制](#9-ssh-连接机制)
10. [常见问题](#10-常见问题)

---

## 1. 模块概述

性能测试文件管理模块负责 JMX 脚本、CSV 数据文件等测试资源的全生命周期管理。

**架构角色说明：**

本模块涉及三类机器，概念不同，请勿混淆：

| 角色 | 说明                                                      |
|------|---------------------------------------------------------|
| **平台机** | 部署本测试平台后端服务的机器；文件上传/下载/分发指令均从这里发出                       |
| **控制机（Master）** | JMeter 压测主控节点，与压力机处于同一内网/集群；平台机通过 SSH 连接控制机，再由控制机转发到压力机 |
| **压力机（Worker）** | 执行 JMeter 压测的节点，分发的最终目标机器，可有多台                          |
| **MinIO** | 对象存储，持久化保存所有上传文件，可与平台机同机部署或单独部署                         |

**文件核心状态字段：**

| 字段 | 说明 | 取值 |
|------|------|------|
| `upload_status` | 上传状态 | `0` 上传中 / `1` 已完成 |
| `ref_status` | 是否被 JMX 引用 | `0` 未引用 / `1` 已引用 |
| `dist_status` | 分发状态 | `0` 未分发 / `1` 已共享 / `2` 已分割 |

---

## 2. 前置配置

### 2.1 MinIO 连接配置

在 `config.py` 或 `.env` 中配置：

```env
MINIO_ENDPOINT   = 127.0.0.1:9000       # Minio API访问域名（如minoapi.xxx.com） 
MINIO_ACCESS_KEY = minioadmin           # Minio登录用户名
MINIO_SECRET_KEY = minioadmin           # Minio登录密码
MINIO_BUCKET     = performance          # Minio的Bucket名称（建议不要修改）
MINIO_USE_SSL    = False                # 实际环境根据Http协议类型动态设置，生产环境建议True
```

### 2.2 SSH 连接配置（分发功能必需）

```env
SSH_DEFAULT_USER     = root              # 登录控制机/压力机的用户名（建议Root用户）
SSH_DEFAULT_KEY_PATH = /root/.ssh/id_rsa # 【首选】本机私钥文件的绝对路径，用于以密钥方式 SSH 登录控制机/压力机
SSH_DEFAULT_PASSWORD =                   # 【备用】控制机/压力机的 SSH 登录密码，私钥认证失败或未配置私钥时自动降级使用
```

> **推荐**：使用私钥认证。将平台机的公钥（`id_rsa.pub`）追加到控制机和所有压力机的 `~/.ssh/authorized_keys`，一次配置、长期生效，无密码泄露风险。

SSH公钥分发到Master机：
```bash
# Windows中打开Git bash执行命令，Linux直接执行：
ssh-copy-id -p <port> root@<Master控制机IP或者域名>
```
SSH公钥分发到压力机（多台时循环分发）：
```bash
# 假设 Worker 主机名为 jmeter-worker-1, jmeter-worker-2, ...
# 需要输入一次 Worker 的 root 密码（仅一次）
for i in $(seq 1 n); do
    ssh-copy-id root@jmeter-worker-${i}
done
```
- 该命令会自动将 ~/.ssh/id_rsa.pub 追加到 Worker 的 ~/.ssh/authorized_keys 文件中。
- 如果 Worker 的 SSH 端口不是 22，使用 -p 参数：ssh-copy-id -p <port> root@jmeter-worker-1。
在Master机执行下面命令测试SSH登录
```bash
ssh root@jmeter-worker-1
# 执行 exit 或 Ctrl+D 退出 SSH 会话，返回到你的控制机（Master）。
```

### 2.3 系统参数（参数配置页面维护，实时生效）

| 参数名 | 默认值 | 说明 |
|--------|--------|------|
| `PROXY_UPLOAD_MAX_BYTES` | `200MB` | 后端代理上传的文件大小上限。超过此值需改用预签名直传接口 |
| `PERF_WORKER_DATA_DIR` | `data/jmeter/` | 压力机上存放数据文件的目录（POSIX 路径，末尾可带 `/`） |
| `SHARE_DIST_MAX_WORKERS` | `10` | 共享分发最大并发节点数。两种分发方案（直拉 MinIO / 平台机中转）均受此上限约束，建议不超过 `20` |
| `CTRL_BANDWIDTH_MBPS` | `500` | 平台机到控制机/压力机的可用上行带宽，**单位 Mbps**（如 500Mbps 填 `500`，1Gbps 填 `1000`，100Mbps 填 `100`）。仅在共享分发走平台机中转时生效，用于动态计算安全并发数 |

### 2.4 文件类型白名单（数据字典维护）

在「数据字典 → 性能测试数据文件类型（perf_file_type）」中维护允许上传的扩展名。

默认支持：`jmx`、`csv`、`txt`、`json`、`yaml`、`jtl`

新增类型只需在数据字典添加条目，无需修改代码，5 分钟缓存自动刷新。

---

## 3. 文件上传

### 3.1 小文件代理上传（文件 ≤ `PROXY_UPLOAD_MAX_BYTES`）

**接口**：`POST /v1/performance/files/upload`（`multipart/form-data`）

```
前端 ──multipart/form-data──▶ 后端 ──put_object──▶ MinIO
                              （后端接收全部内容后上传）
```

**流程：**
1. 校验文件扩展名是否在字典白名单内
2. 读取文件内容，校验大小 ≤ `PROXY_UPLOAD_MAX_BYTES`（超出返回 400）
3. 上传至 MinIO，路径格式：`{file_type}/{yyyyMMdd}/{uuid}_{原始文件名}`
4. 写入 DB 元数据，`upload_status=1`

**适用场景**：JMX 脚本、小型 CSV 参数文件。

---

### 3.2 大文件预签名两阶段直传（文件 > `PROXY_UPLOAD_MAX_BYTES`）

文件内容完全不经过后端，适合 GB 级超大文件。

```
①  前端 ──请求预签名──▶ 后端（写 DB 占位，upload_status=0）──签发──▶ MinIO 预签名 PUT URL
②  前端 ──PUT 文件────▶ MinIO（直接上传，不占平台机带宽，URL 有效期 30 分钟）
③  前端 ──确认上传────▶ 后端 ──stat_object 验证文件实际存在──▶ upload_status=1
```

**接口：**
- `POST /v1/performance/files/presign-upload` → 返回 `{ file_id, upload_url, object_key }`
- `POST /v1/performance/files/confirm-upload` → 传入 `{ file_id, object_key }`，后端验证后更新状态

> **注意**：`presign-upload` 会创建 `upload_status=0` 的预占位记录。若前端上传中途取消且未调用 `confirm-upload`，DB 中会留有僵尸记录（`upload_status=0`），需定期清理。

---

### 3.3 MinIO 存储路径规则

所有文件统一按以下规则生成 `object_key`：

```
{file_type}/{yyyyMMdd}/{uuid}_{原始文件名}

示例：
  csv/20260101/a1b2c3d4_users.csv
  jmx/20260101/e5f6g7h8_stress_test.jmx
```

---

## 4. 文件下载

**接口**：`GET /v1/performance/files/{file_id}/download-url`

后端签发带 `Content-Disposition` 头的预签名 GET URL（有效期 **5 分钟**），前端拿到后直接跳转，由浏览器触发下载，文件内容不经过后端。

```
前端 ──① 请求──▶ 后端 ──签发──▶ MinIO 预签名 GET URL（5 分钟）
前端 ──② 跳转──▶ MinIO（浏览器直接下载）
```

> 下载链接有时效性（5 分钟），不可缓存或分享给他人使用。

---

## 5. 文件替换与删除

### 5.1 替换上传

**接口**：`PUT /v1/performance/files/{file_id}/upload`（`multipart/form-data`）

- 保留原 `file_id`，JMX 引用关系不中断
- 先删除 MinIO 旧对象，再上传新文件（生成新 `object_key`）
- 新文件名、类型可与原文件不同（需在白名单内）
- 支持代理上传（≤ `PROXY_UPLOAD_MAX_BYTES`），大文件替换请先删除再走预签名直传

### 5.2 软删除

**接口**：`DELETE /v1/performance/files/{file_id}`

1. 从 MinIO 删除对象（`upload_status=1` 时）
2. DB 记录 `enabled_flag=0`（软删除，保留历史）

> 已被 JMX 引用（`ref_status=1`）或已分发（`dist_status≠0`）的文件仍可删除，但 JMX 引用和分发记录不会自动清除，需手动处理。

---

## 6. 共享分发

### 6.1 使用场景

将**同一份完整文件**分发到多台压力机，每台机器持有相同的数据副本。

**典型场景：**
- 通用账号池 CSV（每台压力机都需要全量账号）
- 配置文件、JMX 所需参数文件（内容相同，每机一份）
- 机器数量少（≤ 5 台）且文件不大时也可用于替代分割分发

**前置条件：**
- 文件 `upload_status=1`（已上传完成）
- 压力机 SSH 可达（已配置密钥或密码）
- 可用压力机数量 ≥ 填写的 worker_count（`machine_type` 为 Slave 或单机，状态启用）

---

### 6.2 工作原理

启动时自动探测压力机是否能直连 MinIO，根据结果选择方案：

```
share_distribute()
    │
    ├─ 读取参数：SHARE_DIST_MAX_WORKERS、CTRL_BANDWIDTH_MBPS
    ├─ 生成 MinIO 预签名 URL（有效期 60 分钟）
    │
    ├─ [探测] SSH 到第 1 台压力机，curl/wget HEAD 请求预签名 URL（5 秒超时）
    │
    ├─ 探测成功 ──▶ 方案A：压力机直拉 MinIO
    └─ 探测失败 ──▶ 方案B：平台机中转 SFTP 推送
```

---

#### 方案A：压力机直拉 MinIO（优先）

```
平台机 ──SSH 命令──▶ Worker1 ──HTTP GET──▶ MinIO ┐
        ──SSH 命令──▶ Worker2 ──HTTP GET──▶ MinIO │  并发
        ──SSH 命令──▶ WorkerN ──HTTP GET──▶ MinIO ┘
```

- 文件内容**完全不经过平台机**，平台机仅通过控制机中继传递 SSH 指令
- 各压力机自动选择可用工具（依次降级）：`curl` → `wget（含 busybox）` → `python3 urllib`
- 并发数 = `min(SHARE_DIST_MAX_WORKERS, 实际节点数)`

**适用网络条件：** 压力机能访问 MinIO HTTP 端口（同 K8S 集群内 Service DNS 可达，或同内网且 MinIO 端口已暴露）

---

#### 方案B：平台机中转 SFTP（兜底）

```
MinIO ──下载（1 次）──▶ 平台机临时目录
平台机 ──SFTP 并发──▶ Worker1  ┐
        ──SFTP 并发──▶ Worker2  │  并发（含断点续传）
        ──SFTP 并发──▶ WorkerN  ┘
        ──自动清理──▶ 平台机临时文件
```

- 压力机仅需 `sshd`，无需任何额外工具
- SFTP 支持**断点续传**，中断后重新分发可跳过已传字节
- 并发数受带宽和文件大小联合约束（见下节）

**适用网络条件：** 压力机与 MinIO 网络不通（跨机房、MinIO 未对外暴露等）

---

### 6.3 并发控制策略

#### 方案A（直拉 MinIO）

MinIO 天然支持高并发拉取，并发数仅受系统参数上限约束：

```
max_workers = min(SHARE_DIST_MAX_WORKERS, 实际节点数)
```

#### 方案B（平台机中转 SFTP）

并发数由**带宽 × 文件大小**联合决定，目标：每个并发连接的传输时间 ≤ 5 分钟（300 秒）。

**计算公式：**

```python
ctrl_bw_mb_s  = CTRL_BANDWIDTH_MBPS / 8         # Mbps → MB/s
bw_limit      = int(300 × ctrl_bw_mb_s / file_size_mb)  # 不超过 5 分钟完成所需并发上限
max_workers   = min(SHARE_DIST_MAX_WORKERS, node_count, max(1, bw_limit))
```

**不同带宽和文件大小下的实际最大并发数（`SHARE_DIST_MAX_WORKERS = 10`）：**

| 文件大小 | 100 Mbps（12.5 MB/s） | 500 Mbps（62.5 MB/s） | 1000 Mbps（125 MB/s） |
|---------|----------------------|-----------------------|-----------------------|
| ≤ 200 MB | 10 | 10 | 10 |
| 500 MB | **7** | 10 | 10 |
| 1000 MB | **3** | 10 | 10 |
| 2000 MB | **1**（串行） | **9** | 10 |
| 5000 MB | **1**（串行） | **3** | **7** |

> - 默认 `CTRL_BANDWIDTH_MBPS = 500`（即 500Mbps），对应第二列
> - 实际并发数已取 `sys_max`、节点数、带宽限制三者的最小值
> - 并发数为 **1** 时退化为串行，适用于带宽严重受限场景，保证单次传输稳定完成
> - 若平台机带宽更高（如 1Gbps），在参数配置中将 `CTRL_BANDWIDTH_MBPS` 改为 `1000` 即可解锁更高并发

---

### 6.4 分发结果字段

| 情况 | `dist_status` | `dist_worker_ids` | `dist_time` | `remark` |
|------|--------------|-------------------|-------------|---------|
| 全部成功 | `1`（已共享） | 全部机器 ID | 当前时间 | `null`（清空） |
| 部分成功 | `1`（已共享） | 成功机器 ID | 当前时间 | 失败详情（见下方格式） |
| 全部失败 | 不变 | 不变 | 不变 | 失败详情（见下方格式） |

**`remark` 格式**（多条失败时换行分隔，鼠标悬停可见完整内容）：
```
【1】worker-01：SSH连接失败: Connection refused
【3】worker-03：下载失败: curl exit 7
```

---

## 7. 分割分发

### 7.1 使用场景

将文件**按压力机数量等比切割**，每台压力机得到独立的数据分片，各节点数据不重叠。

**典型场景：**
- 千万级用户账号 CSV 分片（每台压力机执行不同账号段，避免并发冲突）
- 大流量测试中的数据去重（确保每个虚拟用户使用唯一身份）
- 节省压力机磁盘：每台只存全量数据的 `1/N`

**前置条件：**
- 文件 `upload_status=1`
- 平台机有足够临时磁盘空间（需完整下载文件后切割）
- SSH 可达，可用压力机数量 ≥ `worker_count`

---

### 7.2 工作原理

```
① MinIO ──下载（完整文件）──▶ 平台机临时目录
② 平台机本地切割：
     file.csv → file.csv.part0（字节 0 ~ chunk_size-1）
             → file.csv.part1（字节 chunk_size ~ 2*chunk_size-1）
             → ...
             → file.csv.partN-1（余下全部字节）
③ 并发 SFTP 推送：
     Worker1 ← part0（落盘文件名：file.csv）
     Worker2 ← part1（落盘文件名：file.csv）
     ...
     WorkerN ← partN-1（落盘文件名：file.csv）
④ 平台机临时文件（完整文件 + 所有分片）自动清理
```

**关键设计：**
- 切割算法：`chunk_size = file_size // N`，末片补全余数字节，总量完整无丢失
- 各压力机上的文件均以**原始文件名**落盘（非 `.partN` 后缀），JMX 脚本中的文件名引用无需修改
- 传输通道：全程 SFTP，不依赖压力机任何工具，仅需 `sshd`
- **SSE `node_pending` 事件**额外携带 `chunk_size` 字段（如 `"12.5 MB"`），在连接建立前即可在进度页面展示各节点分配的文件大小

---

### 7.3 并发控制

分割分发单节点传输量为 `file_size / N`，远小于共享分发。

```
max_chunk_size  = file_size // N + remainder   # 末片最大（包含所有余数字节）
max_workers     = min(20, max(10, N // 2))     # 节点 ≤ 20 且分片 ≤ 200MB 则全并发
```

规则：
- 节点数 ≤ 20 **且** 每片 ≤ 200 MB → 全并发（`max_workers = N`）
- 否则 → `max_workers = min(20, max(10, N // 2))`，限制在 10 ~ 20 之间

---

### 7.4 注意事项

**CSV 表头处理**：切割按字节操作，若 CSV 含表头行，分片中仅 `part0` 有表头，其他分片没有。建议在 JMeter 的 `CSV Data Set Config` 中将 `Header line` 设为首行读取并在各 Worker 上一致处理；或使用无表头 CSV 文件（推荐）。

**数据完整性**：切割只保证字节完整，不识别行边界。对于 CSV 文件，最后一行可能被截断跨片。推荐预先确保文件中的行数能被 `N` 整除，或在数据准备阶段按行数均匀切割再上传。

---

### 7.5 分发结果字段

| 情况 | `dist_status` | `dist_worker_ids` | `dist_time` | `remark` |
|------|--------------|-------------------|-------------|---------|
| 全部成功 | `2`（已分割） | 全部机器 ID | 当前时间 | `null`（清空） |
| 部分成功 | `2`（已分割） | 成功机器 ID | 当前时间 | 失败详情（格式同 6.4） |
| 全部失败 | 不变 | 不变 | 不变 | 失败详情（格式同 6.4） |

---

## 8. 清除分发

### 8.1 使用场景

删除压力机上已分发的文件，释放磁盘空间或为重新分发做准备。

**典型场景：**
- 更换数据版本前清理旧文件
- 压测任务完成后清理压力机
- 分发失败后重新分发前（幂等，可重复执行）

---

### 8.2 工作原理

```
读取 dist_worker_ids
  │
  ├─ 并发 SSH 连接各压力机
  │     执行：rm -f '{PERF_WORKER_DATA_DIR}/{file_name}'
  │
  └─ 汇总结果 → 更新 DB
```

- 仅操作 `dist_worker_ids` 记录的机器（上次成功分发的节点），不影响其他机器
- 共享分发和分割分发的文件在压力机上均以**原始文件名**存储，清除命令统一，无差异
- `rm -f` 文件不存在时静默退出（幂等，重复执行安全）

---

### 8.3 结果处理策略

| 情况 | DB 更新行为 |
|------|-----------|
| **全部成功** | `dist_status=0`、`dist_worker_ids=[]`、`dist_time=null`、`remark=null`，状态恢复为未分发 |
| **部分成功** | `dist_worker_ids` 更新为**失败节点 ID 列表**（仅保留未清除的机器），`remark` 记录失败详情，可再次执行清除 |
| **全部失败** | `dist_worker_ids` 保持原值，`remark` 记录失败详情，DB 其余字段不变 |

**`remark` 格式**（多条失败时换行分隔）：
```
【1】worker-01：SSH连接失败: Connection refused
【3】worker-03：rm 命令执行失败: exit 1
```

> 部分清除成功后，`dist_worker_ids` 仅剩失败节点，下次再次点击「清除分发」可只针对失败节点重试，无需处理已清除的机器。

---

## 9. SSH 连接机制

### 9.1 重试策略

每个节点的 SSH 连接失败后自动重试，最多尝试 **3 次**（含首次），每次间隔 **3 秒**：

```
第 1 次 ──失败──▶ 等 3s ──▶ 第 2 次 ──失败──▶ 等 3s ──▶ 第 3 次 ──失败──▶ 节点标记失败
```

- 认证方式：优先私钥（`SSH_DEFAULT_KEY_PATH`），备选密码（`SSH_DEFAULT_PASSWORD`）
- 连接超时：每次 30 秒
- 3 次全部失败才放弃，避免网络瞬断导致误判

### 9.2 断点续传（仅 SFTP 中转模式）

每次 SFTP 上传前，先检查压力机已有字节数：

| 远端文件状态 | 处理行为 |
|-------------|---------|
| 不存在 | 全量上传（`sftp.put`） |
| `0 < 远端大小 < 本地大小` | 从断点追加（`sftp.open('ab')`，跳过已传字节） |
| 远端大小 = 本地大小 | 已完整，跳过上传，直接返回成功 |
| 远端大小 > 本地大小 | 远端文件损坏，覆盖重传 |

> 方案A（压力机直拉 MinIO）目前不支持断点续传；网络中断后节点会标记失败，需重新执行分发任务。

### 9.3 上传进度日志

SFTP 上传每完成约 20% 写入一条日志，格式：

```
[worker-01 users.csv] 上传进度 40%  (40,960,000/102,400,000 bytes)  → /data/jmeter/users.csv
[worker-01 users.csv] 上传进度 60%  (61,440,000/102,400,000 bytes)  → /data/jmeter/users.csv
```

---

### 9.4 Master SSH 连接复用

每次分发任务（共享 / 分割 / 清除）在整个流程中**共享同一条 Master SSH 连接**，避免每台压力机各自重复握手。

**复用策略：**

1. 步骤4（Master 连通性检测）建立连接后，该连接**不关闭**，后续全程复用
2. 隧道类型探测直接通过复用连接发起，不额外握手
3. N 台压力机的分发任务所对应的 `_RelayClient` 实例均共享同一条 Master Transport（paramiko Transport 线程安全，支持多通道并发）
4. 分发任务全部完成（或异常/中断）后，由 `finally` 块统一关闭该连接

**优化效果（Relay 模式，4 台压力机为例）：**

| | 优化前 | 优化后 |
|---|--------|--------|
| Master SSH 握手次数 | 11（探测 1 + 隧道探测失败再 relay 2 + 每台 Worker 各 2） | **1** |
| direct-tcpip 探测 | 每台 Worker 各尝试一次 | **仅首台探测一次**，结果缓存供所有 Worker 使用 |

> 无 Master 跳板机时（直连部署），以上复用逻辑不生效，各压力机直接 SSH 连接，无额外影响。

---

## 10. 常见问题

**Q：共享分发和分割分发有什么区别，如何选择？**

| | 共享分发 | 分割分发 |
|---|---------|---------|
| 每台机器数据 | 完整副本 | 独立分片（`1/N`） |
| 压力机磁盘 | 全量 × N | 全量（各存 `1/N`） |
| 平台机磁盘 | 方案B 需临时下载 | 必须临时下载 |
| 数据重叠 | 有（所有机器相同） | 无（各机不重叠） |
| 适合场景 | 同一数据集所有机器都要用 | 大数据集拆分执行，避免重复 |

---

**Q：共享分发走方案A还是方案B，如何知道？**

系统会自动探测，无需手动选择。在分发日志中可查看：
- `"共享分发成功（直连MinIO）"` → 方案A
- `"共享分发成功"` + 有上传进度日志 → 方案B

---

**Q：MinIO 部署在平台机上，压力机在另一个网段，会选方案B吗？**

是的。探测阶段平台机通过控制机 SSH 到压力机执行 curl/wget 请求 MinIO 地址，若超时（5 秒）则判定不可达，自动切换方案B（平台机中转 SFTP）。

---

**Q：压力机既没有 curl 也没有 wget，方案A 会失败吗？**

会触发探测失败，自动切换方案B（SFTP 中转）。方案B 仅依赖 `sshd`，无需压力机上的任何额外工具。

---

**Q：分割分发数据如何保证不重叠？**

切割按字节严格等分，每个分片字节范围不重叠，总量完整。若 CSV 有表头行，建议使用无表头文件或在 JMeter `CSV Data Set Config` 中统一处理。

---

**Q：`CTRL_BANDWIDTH_MBPS` 填错了影响什么？**

- 填写**偏大**：并发数高于实际安全值，大文件中转可能导致带宽打满、传输超时
- 填写**偏小**：并发被不必要地限制，传输效率低（退化为串行）

在参数配置页修改后，下次分发任务实时生效，无需重启服务。

---

**Q：分发任务执行中途服务重启怎么办？**

- **方案B（SFTP 中转）**：重新发起分发，对已传完的节点支持断点续传，跳过已传字节，仅补传未完成的部分
- **方案A（直拉 MinIO）**：压力机上的临时/不完整文件需手动清除后重试（或先执行「清除分发」再重新分发）

---

**Q：清除分发后可以重新分发同一文件吗？**

可以。清除分发将 `dist_status` 重置为 `0`（未分发），之后可再次执行共享分发或分割分发，选择相同或不同的压力机数量。

---

**Q：共享分发报错”Administratively prohibited”**
```
“message”: “ChannelException(1, 'Administratively prohibited')”
```
Master 的 sshd 将 `AllowTcpForwarding` 设为 `no`，导致 Paramiko 的 `direct-tcpip` 通道被拒绝。

**系统已内置自动回退机制，无需修改任何配置，无需安装额外工具：**

当 `direct-tcpip` 报 `Administratively prohibited` 时，自动切换到 **SSH Relay 方案**：
- 平台机 SSH 到控制机（直接连接）
- 控制机的 shell 执行 `ssh worker 'command'` 或 `scp /tmp/file worker:/path`
- 整个链路不使用 TCP 转发，控制机只需能正常 SSH 到 Worker 即可

两种策略的自动选择逻辑：

| 策略 | 触发条件 | 控制机要求 |
|------|----------|-------------|
| `direct-tcpip`（优先） | 正常情况 | `AllowTcpForwarding yes` |
| **SSH Relay**（自动回退） | 收到 `Administratively prohibited` | 能 SSH 到 Worker（无需额外工具） |

> Relay 模式下文件传输走「先 SFTP 到控制机 /tmp，再控制机 scp 到 Worker」两步流程，
> 性能略低于直连模式，但功能完全等价。

---

## 11. SSH 连接测试指南

运行 `python ssh_connection.py` 可验证三机链路。脚本从 `.env` 和数据库自动读取配置，支持 4 个场景逐项验证。

### 11.1 三机架构与 SSH 认证总览

```
平台机（脚本运行处）
  │
  ├─ SSH 私钥/密码 ──▶ 控制机（Master，machine_type=1）
  │                         │
  │                         ├─ direct-tcpip 隧道 ──▶ 压力机（场景3，需 AllowTcpForwarding yes）
  │                         └─ shell ssh 中继  ──▶ 压力机（场景4，无需 TCP 转发）
  │
  └─ SSH 认证凭据来自 .env：
       SSH_DEFAULT_KEY_PATH  =  平台机私钥路径（优先）
       SSH_DEFAULT_PASSWORD  =  控制机/压力机登录密码（备用）
```

### 11.2 场景1 — 平台机私钥连接控制机（基础）

**验证目的**：所有分发功能的基础链路。

**前置步骤（在平台机上执行）：**

```bash
# ① 生成平台机密钥对（已有则跳过）
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# ② 将平台机公钥授权到控制机
ssh-copy-id -i ~/.ssh/id_rsa.pub -p <MASTER_PORT> root@<MASTER_IP>
# 或手动将 ~/.ssh/id_rsa.pub 内容追加到控制机 ~/.ssh/authorized_keys

# ③ 验证免密登录
ssh -p <MASTER_PORT> -i ~/.ssh/id_rsa root@<MASTER_IP> echo ok

# ④ 在 .env 中配置
# SSH_DEFAULT_KEY_PATH=/root/.ssh/id_rsa   # 平台机私钥绝对路径
```

**常见失败原因：**

| 现象 | 原因 | 修复 |
|------|------|------|
| `Permission denied (publickey)` | 公钥未授权或私钥不匹配 | 重新 `ssh-copy-id` |
| `Permission denied (publickey)` + 无法 `ssh-copy-id` | `PasswordAuthentication no` | 控制机修改 `/etc/ssh/sshd_config` 后 `reload sshd` |
| `No such file` | `SSH_DEFAULT_KEY_PATH` 配置错误 | 检查 .env 中私钥路径 |
| 连接超时 | 网络/防火墙 | `telnet MASTER_IP MASTER_PORT` |

---

### 11.3 场景2 — 平台机密码连接控制机（备用）

**验证目的**：私钥不可用时的备选方案。

**前置步骤：**

```bash
# ① 确认控制机允许密码认证
grep PasswordAuthentication /etc/ssh/sshd_config
# 若为 no：sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
#          systemctl reload sshd

# ② 在 .env 中配置密码，私钥路径留空
# SSH_DEFAULT_KEY_PATH=
# SSH_DEFAULT_PASSWORD=your_master_password
```

> 私钥和密码均配置时，优先使用私钥。密码仅在 `SSH_DEFAULT_KEY_PATH` 未配置或文件不存在时生效。

---

### 11.4 场景3 — direct-tcpip 连接压力机（平台机→控制机→压力机）

**验证目的**：验证 TCP 隧道方式是否可用（性能最优）。

**前置步骤：**

```bash
# ① 完成场景1（平台机私钥已授权到控制机）

# ② 将平台机公钥授权到所有压力机
#    方法A：在平台机上直接执行
ssh-copy-id -i ~/.ssh/id_rsa.pub root@<WORKER_IP>
#    方法B：通过控制机跳转
ssh -J root@<MASTER_IP> -i ~/.ssh/id_rsa root@<WORKER_IP> echo ok

# ③ 确认控制机 sshd 允许 TCP 转发
grep AllowTcpForwarding /etc/ssh/sshd_config
# 若为 no（或如 K8s 环境禁用转发）：
#   方案A 修改控制机配置：
#     sed -i 's/AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config
#     systemctl reload sshd
#   方案B 改用场景4（SSH Relay），无需修改任何配置
```

**失败提示：**
- `Administratively prohibited` → 控制机 `AllowTcpForwarding=no`，改用场景4
- `Connection refused` → 压力机 sshd 未运行或端口不对
- `Permission denied` → 平台机公钥未授权到压力机

---

### 11.5 场景4 — SSH Relay 连接压力机（推荐，无需 TCP 转发）

**验证目的**：AllowTcpForwarding=no 场景下的标准方案（系统自动回退此方案）。

**前置步骤：**

```bash
# ① 完成场景1（平台机私钥已授权到控制机）

# ② 在控制机上建立到压力机的免密 SSH（Relay 的核心前提）
#    在控制机上执行：
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""   # 生成控制机密钥（已有则跳过）
ssh-copy-id -i ~/.ssh/id_rsa.pub root@<WORKER_IP>   # 授权到压力机
ssh root@<WORKER_IP> echo ok                        # 验证：无密码提示直接输出 ok

# ③ 无需修改 sshd 配置，AllowTcpForwarding 保持 no 亦可
```

**排查密钥认证不生效（仍提示密码）：**

```bash
# 在控制机上执行，观察认证过程
ssh -v root@<WORKER_IP> echo ok 2>&1 | grep -E "Offering|Trying|accept|denied"

# 修复压力机文件权限（最常见原因）
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# 重新确认公钥内容一致
cat ~/.ssh/id_rsa.pub           # 控制机公钥
ssh root@<WORKER_IP> cat ~/.ssh/authorized_keys  # 压力机已授权内容
```

> **注意**：`ssh -o BatchMode=yes` 会禁用密码提示，直接报 `Permission denied`，
> 这是脚本 probe 命令使用的参数。如果不加 `BatchMode=yes` 需要密码，说明密钥认证未生效，需按上方步骤排查。

---

### 11.6 分发功能就绪判断

| 场景1 | 场景4 | 分发功能状态 |
|-------|-------|------------|
| ✓ | ✓ | **正常可用**，走 SSH Relay 路由（AllowTcpForwarding=no 环境标准方案） |
| ✓ | ✓ + 场景3 ✓ | **正常可用**，优先 direct-tcpip（性能更优） |
| ✓ | ✗ | 分发不可用，需在控制机上完成到压力机的免密授权（见 11.5） |
| ✗ | — | 分发不可用，需先完成平台机→控制机的 SSH 私钥认证（见 11.2） |