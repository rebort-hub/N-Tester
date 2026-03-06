"""
数据工厂模型
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, Index, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base


class DataFactoryRecord(Base):
    """数据工厂使用记录表"""
    
    __tablename__ = 'data_factory_records'
    
    # 用户ID
    user_id = Column(Integer, nullable=False, comment='用户ID', index=True)
    
    # 工具信息
    tool_name = Column(String(100), nullable=False, comment='工具名称', index=True)
    tool_category = Column(String(20), nullable=False, comment='工具分类', index=True)
    tool_scenario = Column(String(20), nullable=False, comment='使用场景', index=True)
    
    # 数据
    input_data = Column(JSON, comment='输入数据')
    output_data = Column(JSON, nullable=False, comment='输出数据')
    
    # 保存状态
    is_saved = Column(Boolean, default=True, comment='是否保存')
    
    # 标签
    tags = Column(JSON, comment='标签')
    
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'creation_date'),
        Index('idx_tool_category', 'tool_category'),
        Index('idx_tool_scenario', 'tool_scenario'),
        {'comment': '数据工厂使用记录表'}
    )
    
    def __repr__(self):
        return f"<DataFactoryRecord(id={self.id}, tool_name={self.tool_name}, user_id={self.user_id})>"
