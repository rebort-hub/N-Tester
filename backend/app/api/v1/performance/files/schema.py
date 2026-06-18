#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

"""
性能测试 - 文件管理 Schema
"""
# ===================================================================== #
#  方案 B：小文件（≤100MB）后端代理上传
# ===================================================================== #

class PerfFileUploadRespSchema(BaseModel):
    """小文件后端代理上传成功后的响应体。"""
    id:            int
    file_name:     str
    file_type:     str
    file_size:     int
    object_key:    str
    upload_status: int  # 直接为 1（已完成）


# ===================================================================== #
#  方案 C：大文件（>100MB）预签名两阶段直传
# ===================================================================== #

class PerfFilePresignReqSchema(BaseModel):
    """申请预签名 PUT URL 的请求体。"""
    file_name: str           = Field(..., max_length=200, description="原始文件名，用于推断文件类型")
    file_size: int           = Field(..., gt=0,           description="文件大小（字节），前端 File.size 传入")
    remark:    Optional[str] = Field(None, max_length=500)


class PerfFilePresignRespSchema(BaseModel):
    """预签名 URL 申请成功的响应体。"""
    file_id:    int  # 预占位的 DB 记录 ID，confirm 时原样回传
    upload_url: str  # 预签名 PUT URL（有效期 30 分钟）
    object_key: str  # 对象路径，confirm 时原样回传用于防篡改校验


class PerfFileConfirmReqSchema(BaseModel):
    """前端上传完成后通知后端确认的请求体。"""
    file_id:    int = Field(..., description="presign 接口返回的 file_id")
    object_key: str = Field(..., description="presign 接口返回的 object_key，原样回传")


class PerfFilePresignReuploadReqSchema(BaseModel):
    """大文件替换预签名请求体（第一阶段）。"""
    file_id:   int           = Field(..., description="待替换的文件 DB 记录 ID")
    file_name: str           = Field(..., max_length=200, description="新文件名，用于推断类型并校验扩展名与原文件一致")
    file_size: int           = Field(..., gt=0,           description="文件大小（字节）")
    remark:    Optional[str] = Field(None, max_length=500)


class PerfFileConfirmReuploadReqSchema(BaseModel):
    """大文件替换确认请求体（第二阶段）。"""
    file_id:    int = Field(..., description="待替换的文件 DB 记录 ID")
    object_key: str = Field(..., description="presignReupload 返回的 object_key，原样回传")
    file_name:  str = Field(..., description="新文件名，用于更新 DB 的 file_name / file_type / content_type")


# ===================================================================== #
#  文件替换更新（表单字段，配合 UploadFile 使用）
# ===================================================================== #
class PerfFileUpdateSchema(BaseModel):
    """替换上传时的附加表单字段（env_type、remark 可选）。"""
    # env_type: Optional[str] = None
    remark:   Optional[str] = None


# ===================================================================== #
#  JMX 引用数据文件（JSON 字段方案）
# ===================================================================== #

class PerfFileSetRefsSchema(BaseModel):
    """更新 JMX 文件名称及引用的数据文件 ID 列表（覆盖式更新）。"""
    file_name:    Optional[str]  = Field(None, description="JMX 文件名称，不传或为 None 则不修改")
    ref_file_ids: List[int]      = Field(...,  description="数据文件 ID 列表，传空列表表示清空引用")
    clear_dist:   bool           = Field(False, description="是否清除分发记录（重置 dist_status=0，不 SSH 删除机器文件）")


class PerfFileRefItemSchema(BaseModel):
    """引用数据文件的简要信息（列表展示用）。"""
    model_config = {"from_attributes": True}

    id:        int
    file_name: str
    file_type: str
    file_size: int  # 文件大小（字节）


# ===================================================================== #
#  下拉选项（轻量，仅 id + name）
# ===================================================================== #

class PerfFileOptionSchema(BaseModel):
    """文件下拉选项，供表单选择器使用。
    JMX 文件附带 parsed_thread_config（上传时解析缓存），前端可据此自动识别线程组类型并预填子配置参数。
    parsed_thread_config 为已反序列化的线程组列表，直接可用，无需前端再次 JSON.parse。
    """
    id:                   int
    name:                 str
    parsed_thread_config: list = []


# ===================================================================== #
#  列表 & 详情响应
# ===================================================================== #

class PerfFileRespSchema(BaseModel):
    """文件列表 / 详情的统一响应体。"""
    model_config = {"from_attributes": True}

    id:              int
    file_name:       str
    file_type:       str
    file_size:       int  # 文件大小（字节）
    content_type:    Optional[str]
    ref_status:      int
    dist_status:     int
    dist_worker_ids: Optional[List[int]] = []
    dist_time:       Optional[datetime]
    ref_file_ids:    Optional[List[int]] = []
    bucket:          str
    object_key:      str
    upload_status:   int
    remark:          Optional[str]
    status:          int

    # 时间（继承自 Base）
    creation_date:   Optional[datetime]
    updation_date:   Optional[datetime]

    # 由 Service 层注入
    operator_name:   Optional[str] = None
    # 引用数据文件详情（JMX 文件专用，由 Service 层注入）
    ref_files:       List[PerfFileRefItemSchema] = []


# ===================================================================== #
#  下载 URL 响应
# ===================================================================== #
class PerfFileDownloadUrlRespSchema(BaseModel):
    """获取下载链接的响应体。"""
    download_url: str  # 预签名 GET URL
    file_name:    str  # 原始文件名（前端用于 a.download 属性）
    expires_in:   int  # URL 有效秒数


# ===================================================================== #
#       分发请求：共享分发、分割分发、清除分发
# ===================================================================== #
class DistributeReqSchema(BaseModel):
    """文件分发请求（共享分发、分割分发）"""
    file_id: int = Field(..., description="要分发的文件 ID")
    worker_count: int = Field(..., ge=1, description="需要分发的压力机数量")
    machine_type: int = Field(2, description="压力机类型：2-Slave，3-单机")

class SplitDistributeReqSchema(BaseModel):
    """分割分发请求（至少 2 台 Worker）"""
    file_id: int = Field(..., description="要分发的文件 ID")
    worker_count: int = Field(..., ge=2, description="需要分发的压力机数量，分割分发最少 2 台")
    machine_type: int = Field(2, description="压力机类型：2-Slave，3-单机")

class ClearDistributeReqSchema(BaseModel):
    """清除分发请求"""
    file_id: int = Field(..., ge=1, description="要清除的文件ID（对应 perf_files.id）")
    worker_count: int = Field(0, ge=0, description="清除的压力机数量，0=全部")

# ===================================================================== #
#       分发响应Schema：分发结果、分发响应
# ===================================================================== #
class DistributeNodeResultSchema(BaseModel):
    """各节点机分发结果"""
    machine_id: int
    machine_name: str
    ip: str
    success: bool
    message: str
    failure_stage: Optional[str] = None  # 'connect' | 'transfer' | None（成功时）


class DistributeRespSchema(BaseModel):
    """分发响应体"""
    total: int
    success_count: int
    failed_count: int
    results: List[DistributeNodeResultSchema]
    dist_status: Optional[int] = Field(None, description="0-未分发，1-已共享，2-已分割")


class DistributeEventSchema(BaseModel):
    """
    SSE 流式分发事件 Schema（文档用）。
    type 取值：
      start        — 任务开始（message 说明当前步骤）
      master       — Master 连接状态（status: connecting|success|failed；auth_method: key|password）
      node_pending — 预渲染等待行（每台 Slave 推送一次）
      method       — 分发/连接方案（use_direct=True→方案A直拉；False→方案B中转；tunnel_type: direct_tcpip|ssh_relay）
      node_done    — 单台机器完成（success=True/False + message）
      done         — 全部完成汇总（success_count, failed_count, dist_status）
      error        — 任务级别错误，流终止
    """
    type:          str
    status:        Optional[str]  = None   # master 事件专用
    auth_method:   Optional[str]  = None   # master 事件专用: key | password
    tunnel_type:   Optional[str]  = None   # method 事件专用: direct_tcpip | ssh_relay | unknown
    machine_id:    Optional[int]  = None
    name:          Optional[str]  = None
    ip:            Optional[str]  = None
    success:       Optional[bool] = None
    use_direct:    Optional[bool] = None
    message:       Optional[str]  = None
    success_count: Optional[int]  = None
    failed_count:  Optional[int]  = None
    dist_status:   Optional[int]  = None