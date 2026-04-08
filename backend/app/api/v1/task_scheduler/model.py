"""
定时数据模型
"""
from sqlalchemy import Column, String, Integer, Text, JSON, DateTime, Boolean, BigInteger
from sqlalchemy.sql import func
from app.models.base import Base


class SchedulerTaskModel(Base):
    """定时任务模型"""
    __tablename__ = 'legacy_scheduler_tasks'
    
    name = Column(String(255), nullable=False, comment='任务名称')

    # 1-APP自动化, 2-Web UI自动化, 3-接口自动化
    type = Column(Integer, nullable=False, comment='任务类型: 1-APP自动化, 2-Web UI自动化, 3-接口自动化')
    status = Column(Integer, nullable=False, comment='任务状态: 0-停用, 1-启用')
    script = Column(JSON, comment='任务脚本配置')
    time = Column(JSON, comment='时间配置')
    notice = Column(JSON, comment='通知配置')
    description = Column(String(255), comment='任务描述')
    
    # APScheduler相关字段
    scheduler_job_id = Column(String(255), comment='调度器任务ID')
    last_run_at = Column(DateTime, comment='上次运行时间')
    next_run_at = Column(DateTime, comment='下次运行时间')
    total_run_count = Column(Integer, default=0, comment='总运行次数')


class MsgNoticeModel(Base):
    """消息通知配置模型"""
    __tablename__ = 'legacy_msg_notices'
    
    name = Column(String(255), nullable=False, comment='通知名称')
    type = Column(Integer, nullable=False, comment='通知类型: 1-邮件, 2-钉钉, 3-企业微信, 4-飞书')
    value = Column(String(255), nullable=False, comment='通知地址/Webhook')
    status = Column(Integer, nullable=False, comment='通知状态: 0-停用, 1-启用')
    script = Column(JSON, comment='通知脚本配置')
    description = Column(String(255), comment='通知描述')


class TaskExecutionHistoryModel(Base):
    """任务执行历史模型"""
    __tablename__ = 'legacy_task_execution_histories'
    
    task_id = Column(BigInteger, nullable=False, comment='任务ID')
    execution_id = Column(String(255), nullable=False, comment='执行ID')
    status = Column(String(20), nullable=False, comment='执行状态: success/failed/running')
    start_time = Column(DateTime, server_default=func.now(), comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    duration = Column(Integer, comment='执行时长(秒)')
    result = Column(JSON, comment='执行结果')
    error_message = Column(Text, comment='错误信息')
    trigger_type = Column(String(20), comment='触发类型: scheduled/manual')


class TaskNotificationLogModel(Base):
    """任务通知日志模型"""
    __tablename__ = 'legacy_task_notification_logs'
    
    task_id = Column(BigInteger, nullable=False, comment='任务ID')
    execution_id = Column(String(255), nullable=False, comment='执行ID')
    notice_id = Column(BigInteger, nullable=False, comment='通知配置ID')
    status = Column(String(20), nullable=False, comment='通知状态: success/failed')
    send_time = Column(DateTime, server_default=func.now(), comment='发送时间')
    response = Column(JSON, comment='通知响应')
    error_message = Column(Text, comment='错误信息')