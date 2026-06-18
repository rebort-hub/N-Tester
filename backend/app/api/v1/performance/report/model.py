#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from sqlalchemy import Column, String, Text, Integer, BigInteger, DateTime

from app.models.base import Base

"""
性能测试 - 压测报告模型
"""


class PerfReportModel(Base):
    """
    压测报告主表（perf_reports）。

    report_status 字典 perf_report_status：1-收集中 2-完成 3-中断 4-失败。
    trigger_type：1-手动触发 2-定时任务。
    MinIO 对象路径规则（均在 report/{report_code}/ 前缀下）：
      object_key    → {report_name}.zip      HTML 报告（range-request 预览）
                    → jmeter-logs.zip        JMeter 日志（单机=jmeter.log，分布式=master+worker-N）
                    → results.zip            JTL 结果文件
                    → collector_process.log  收集流程日志
    src_*_md5 在收集任务初始化时写入，作为原始指纹供强制停止后恢复时校验一致性。
    """
    __tablename__ = 'perf_reports'

    report_code   = Column(String(32),  nullable=False, unique=True,
                           comment='报告唯一编号：RPT+年月日时分秒(后2位年)+00+2位随机数')
    scenario_id   = Column(BigInteger,  nullable=False, index=True,
                           comment='关联场景主键 ID（perf_scenarios.id）')
    scenario_code = Column(String(32),  nullable=False,
                           comment='场景唯一编号（冗余，加速查询）')
    scenario_name = Column(String(200), nullable=False,
                           comment='场景名称（冗余）')
    report_name   = Column(String(300), nullable=False,
                           comment='报告文件展示名：Report-场景名-年月日时分，同时是 zip 基础名')
    bucket        = Column(String(100), nullable=False,
                           comment='Minio bucket 名称')
    object_key    = Column(String(500), nullable=False,
                           comment='HTML报告zip路径：report/{report_code}/{report_name}.zip')
    file_size     = Column(BigInteger,  nullable=False, default=0,
                           comment='zip 文件大小（字节），前端按 KB/MB/GB 显示')
    report_status = Column(Integer,     nullable=False, default=1,
                           comment='报告状态（字典 perf_report_status）：1-收集中 2-完成 3-中断 4-失败')
    trigger_type  = Column(Integer,     nullable=False, default=1,
                           comment='触发方式：1-手动触发 2-定时任务')
    remark        = Column(Text,        nullable=True,
                           comment='备注/失败原因')
    generated_at  = Column(DateTime(),  nullable=True,
                           comment='报告生成完成时间（status=2 时写入）')
    creator       = Column(String(100), nullable=True,
                           comment='报告人（操作人用户名）')
    creator_id    = Column(BigInteger,  nullable=True,
                           comment='报告人用户 ID')
    src_log_md5    = Column(String(32),  nullable=True,
                            comment='收集前 jmeter.log 的 MD5（强制停止恢复时校验）')
    src_jtl_md5    = Column(String(32),  nullable=True,
                            comment='收集前 result.jtl 的 MD5（强制停止恢复时校验）')
    src_report_md5 = Column(String(32),  nullable=True,
                            comment='收集前 HTML 报告目录聚合 MD5（强制停止恢复时校验）')