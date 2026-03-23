"""
APP 抓包 - 数据模型
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, BigInteger
from sqlalchemy.sql import func
from app.models.base import Base


class MitmproxyApi(Base):
    """抓包接口记录"""

    __tablename__ = "app_mitmproxy_api"
    __table_args__ = {"comment": "mitmproxy 抓包接口记录表"}

    result_id = Column(String(255), nullable=False, comment="结果ID")
    device_id = Column(Integer, ForeignKey("app_devices.id"), nullable=False, comment="设备ID（app_devices.id）")
    user_id = Column(BigInteger, ForeignKey("sys_user.id"), nullable=False, comment="用户ID")

    url = Column(Text, nullable=False, default="", comment="接口请求地址")
    method = Column(String(255), nullable=False, default="POST", comment="请求方法")

    request_body = Column(JSON, nullable=True, comment="请求体")
    request_headers = Column(JSON, nullable=True, comment="请求头")
    response_headers = Column(JSON, nullable=True, comment="响应头")
    response_body = Column(JSON, nullable=True, comment="响应体")

    status = Column(Integer, nullable=False, default=0, comment="状态(0失败/1成功)")
    res_time = Column(String(255), nullable=True, comment="响应时间(ms)")

    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")

