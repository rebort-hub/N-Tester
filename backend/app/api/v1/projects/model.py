"""
项目管理数据模型
"""

from sqlalchemy import Column, String, Text, Integer, JSON, Boolean, Index, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class ProjectModel(Base):
    """项目模型"""
    
    __tablename__ = "projects"
    __table_args__ = (
        Index("idx_project_owner", "owner_id"),
        Index("idx_project_status", "status"),
        {'comment': '项目表', 'mysql_charset': 'utf8mb4'}
    )
    
    name = Column(String(200), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    status = Column(String(20), default="active", comment="状态: active/paused/completed/archived")
    owner_id = Column(BigInteger, ForeignKey("sys_user.id", use_alter=True, name="fk_project_owner"), nullable=False, comment="负责人ID")
    
    # 关系定义
    members = relationship("ProjectMemberModel", back_populates="project", lazy="select")
    environments = relationship("ProjectEnvironmentModel", back_populates="project", lazy="select")
    owner = relationship("app.api.v1.system.user.model.UserModel", foreign_keys=[owner_id], lazy="select")


class ProjectMemberModel(Base):
    """项目成员模型"""
    
    __tablename__ = "project_members"
    __table_args__ = (
        Index("idx_pm_project_user", "project_id", "user_id", unique=True),
        Index("idx_pm_user", "user_id"),
        {'comment': '项目成员表', 'mysql_charset': 'utf8mb4'}
    )
    
    project_id = Column(BigInteger, ForeignKey("projects.id", use_alter=True, name="fk_pm_project"), nullable=False, comment="项目ID")
    user_id = Column(BigInteger, ForeignKey("sys_user.id", use_alter=True, name="fk_pm_user"), nullable=False, comment="用户ID")
    role = Column(String(20), default="tester", comment="角色: owner/admin/developer/tester/viewer")
    
    # 关系定义
    project = relationship("ProjectModel", back_populates="members")
    user = relationship("app.api.v1.system.user.model.UserModel", foreign_keys=[user_id])


class ProjectEnvironmentModel(Base):
    """项目环境模型"""
    
    __tablename__ = "project_environments"
    __table_args__ = (
        Index("idx_pe_project", "project_id"),
        {'comment': '项目环境表', 'mysql_charset': 'utf8mb4'}
    )
    
    project_id = Column(BigInteger, ForeignKey("projects.id", use_alter=True, name="fk_pe_project"), nullable=False, comment="项目ID")
    name = Column(String(100), nullable=False, comment="环境名称")
    base_url = Column(String(500), comment="基础URL")
    description = Column(Text, comment="环境描述")
    variables = Column(JSON, comment="环境变量")
    is_default = Column(Boolean, default=False, comment="是否默认")
    
    # 关系定义
    project = relationship("ProjectModel", back_populates="environments")


class ProjectMCPConfigModel(Base):
    """用户级 MCP 远程配置（通过项目路由做权限校验，与 ntest 行为一致）"""

    __tablename__ = "project_mcp_config"
    __table_args__ = (
        Index("uq_project_mcp_user_name", "user_id", "name", unique=True),
        {"comment": "MCP 配置表", "mysql_charset": "utf8mb4"},
    )

    user_id = Column(BigInteger, ForeignKey("sys_user.id", use_alter=True, name="fk_mcp_user"), nullable=False, comment="所属用户")
    name = Column(String(255), nullable=False, comment="配置名称")
    url = Column(String(2048), nullable=False, comment="MCP 服务 URL")
    transport = Column(String(50), default="streamable-http", comment="传输协议")
    headers = Column(JSON, nullable=True, comment="请求头 JSON")
    is_enabled = Column(Boolean, default=True, comment="是否启用")


class ProjectApiKeyModel(Base):
    """用户级第三方 API 密钥（项目路由鉴权）"""

    __tablename__ = "project_api_key"
    __table_args__ = (
        Index("uq_project_apikey_user_name", "user_id", "name", unique=True),
        {"comment": "API 密钥表", "mysql_charset": "utf8mb4"},
    )

    user_id = Column(BigInteger, ForeignKey("sys_user.id", use_alter=True, name="fk_pak_user"), nullable=False, comment="所属用户")
    name = Column(String(100), nullable=False, comment="密钥名称")
    service_type = Column(String(50), nullable=False, comment="服务类型 openai/claude/...")
    key_value = Column(String(2000), nullable=False, comment="密钥值")
    description = Column(Text, nullable=True, comment="描述")
    is_active = Column(Boolean, default=True, comment="是否启用")


class KnowledgeBaseModel(Base):
    """项目知识库"""

    __tablename__ = "knowledge_base"
    __table_args__ = (
        Index("idx_kb_project", "project_id"),
        {"comment": "知识库表", "mysql_charset": "utf8mb4"},
    )

    project_id = Column(BigInteger, ForeignKey("projects.id", use_alter=True, name="fk_kb_project"), nullable=False, comment="项目ID")
    name = Column(String(200), nullable=False, comment="名称")
    description = Column(Text, nullable=True, comment="描述")
    chunk_size = Column(Integer, default=1000, comment="分块大小")
    chunk_overlap = Column(Integer, default=200, comment="分块重叠")
    is_active = Column(Boolean, default=True, comment="是否启用")


class KnowledgeDocumentModel(Base):
    """知识库文档（简化版：本地存储 + 文本提取，向量检索可后续扩展）"""

    __tablename__ = "knowledge_document"
    __table_args__ = (
        Index("idx_kdoc_kb", "knowledge_base_id"),
        {"comment": "知识库文档表", "mysql_charset": "utf8mb4"},
    )

    knowledge_base_id = Column(
        BigInteger, ForeignKey("knowledge_base.id", use_alter=True, name="fk_kdoc_kb"), nullable=False, comment="知识库ID"
    )
    title = Column(String(500), nullable=False, comment="标题")
    document_type = Column(String(20), nullable=False, comment="类型 pdf/docx/txt/md/...")
    file_path = Column(String(2000), nullable=True, comment="相对存储路径")
    content = Column(Text, nullable=True, comment="提取的纯文本（用于关键词检索）")
    status = Column(String(20), default="pending", comment="pending/processing/completed/failed")
    error_message = Column(Text, nullable=True, comment="错误信息")
    file_size = Column(Integer, nullable=True, comment="字节大小")
    word_count = Column(Integer, nullable=True, comment="字数")


class KnowledgeGlobalConfigModel(Base):
    """知识库全局嵌入配置（按用户）"""

    __tablename__ = "knowledge_global_config"
    __table_args__ = (
        Index("uq_kgc_user", "user_id", unique=True),
        {"comment": "知识库全局配置", "mysql_charset": "utf8mb4"},
    )

    user_id = Column(BigInteger, ForeignKey("sys_user.id", use_alter=True, name="fk_kgc_user"), nullable=False, comment="用户ID")
    embedding_service = Column(String(50), default="openai", comment="嵌入服务类型")
    api_base_url = Column(String(500), nullable=True, comment="API Base URL")
    api_key = Column(String(2000), nullable=True, comment="API Key")
    model_name = Column(String(200), default="text-embedding-3-small", comment="嵌入模型名")
    chunk_size = Column(Integer, default=1000, comment="默认分块大小")
    chunk_overlap = Column(Integer, default=200, comment="默认分块重叠")
