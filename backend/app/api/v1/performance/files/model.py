#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from sqlalchemy import Column, String, Text, Integer, BigInteger, DateTime, JSON

from app.models.base import Base

"""
性能测试 - 文件管理模型
"""
class PerfFileModel(Base):
    """
    性能测试文件主表（perf_files）。

    支持两种上传模式：
      - 方案 B（小文件 ≤50MB）：后端接收后直接推送到 MinIO，upload_status 直接置 1。
      - 方案 C（大文件 >50MB）：先写 upload_status=0 的预占位记录，前端直传 MinIO 后
        调用 confirm 接口将 upload_status 更新为 1。

    JMX 脚本与数据文件的引用关系通过 ref_file_ids（JSON 数组）直接存在本表，
    无需额外关联表，适合当前单向查询（JMX → 数据文件）的使用场景。
    """
    __tablename__ = 'perf_files'

    # ---- 文件基础信息 ----
    file_name    = Column(String(200),  nullable=False, comment='文件名称（原始文件名，最长200字符）')
    file_type    = Column(String(20),   nullable=False, comment='文件类型：jmx/csv/txt/json/other...')
    file_size    = Column(BigInteger,    nullable=False, default=0,     comment='文件大小（字节）')
    content_type = Column(String(100),  nullable=True,  comment='MIME 类型，如 text/csv/jmx等')

    # ---- 业务属性 ----
    env_type     = Column(String(50),   nullable=True, comment='所属环境（取字典表值：1-开发，2-测试，3-预发布，4-生产，5-性能）')
    ref_status   = Column(Integer,      nullable=False, default=0, comment='引用状态：0-未引用 1-已引用 2-已关联 3-使用中')
    dist_status  = Column(Integer,      nullable=False, default=0, comment='分发状态：0-未分发 1-已共享 2-已分割')
    dist_worker_ids = Column(JSON, nullable=True, comment='分发到的压力机ID列表，如 [1, 2, 3]')
    dist_time    = Column(DateTime(),   nullable=True,  comment='最后分发时间')

    # ---- JMX 引用数据文件（仅 jmx 类型有值）----
    ref_file_ids = Column(JSON,         nullable=True, comment='引用的数据文件 ID 列表，仅 jmx 类型有值，如 [1, 2, 3]')

    # ---- JMX 线程组配置缓存（仅 jmx 类型有值）----
    parsed_thread_config = Column(Text, nullable=True,
                                  comment='JMX线程组配置缓存（JSON），上传时解析；含启用线程组的tg_index和各类型字段，供场景创建表单自动识别类型并预填参数')

    # ---- MinIO 存储定位 ----
    bucket       = Column(String(100),  nullable=False, comment='MinIO Bucket 名称')
    object_key   = Column(String(1000), nullable=False, comment='MinIO 对象路径，如 performance/jmx/2026/04/uuid.jmx')

    # ---- 上传状态（两阶段提交） ----
    upload_status = Column(Integer,     nullable=False, default=0, comment='上传状态：0-待上传(预签名已签发) 1-上传完成 2-上传失败')

    # ---- 其他 ----
    status       = Column(Integer,      nullable=False, default=1, comment='记录状态：1启用 0禁用')
    remark       = Column(Text,         nullable=True,  comment='备注')
