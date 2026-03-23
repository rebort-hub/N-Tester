"""
文件管理数据模型
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, LargeBinary
from app.models.base import Base


class FileModel(Base):
    """文件模型"""
    
    __tablename__ = "sys_file"
    __table_args__ = {'comment': '文件管理表'}
    
    file_name = Column(String(255), nullable=False, comment="存储的文件名")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_url = Column(String(500), nullable=True, comment="文件访问URL")
    
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_type = Column(String(100), nullable=True, comment="文件MIME类型")
    file_ext = Column(String(20), nullable=True, comment="文件扩展名")
    
    upload_type = Column(String(20), nullable=False, default="local", comment="上传类型（local/oss/database）")
    storage_path = Column(String(500), nullable=True, comment="存储路径")
    
    # 新增：文件内容字段，用于直接存储文件二进制数据
    file_content = Column(LargeBinary, nullable=True, comment="文件二进制内容（用于数据库存储模式）")
    
    description = Column(Text, nullable=True, comment="文件描述")
    tags = Column(String(500), nullable=True, comment="文件标签")
    
    download_count = Column(Integer, nullable=False, default=0, comment="下载次数")
    is_public = Column(Integer, nullable=False, default=1, comment="是否公开（0:私有 1:公开）")
    
    uploaded_by = Column(Integer, nullable=False, comment="上传用户ID")
    uploaded_at = Column(DateTime, nullable=False, comment="上传时间")