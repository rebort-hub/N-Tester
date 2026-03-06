# 用例评审模块 - 数据模型层

from sqlalchemy import Column, BigInteger, String, Text, DateTime, Boolean, Integer, JSON, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.base_model import BaseModel
from app.models.base import Base


class TestCaseReview(BaseModel):
    """测试用例评审表"""
    __tablename__ = 'test_case_reviews'
    
    project_id = Column(BigInteger, nullable=False, comment='关联项目ID')
    title = Column(String(500), nullable=False, comment='评审标题')
    description = Column(Text, comment='评审描述')
    status = Column(String(20), default='pending', comment='评审状态: pending/in_progress/completed/cancelled')
    priority = Column(String(20), default='medium', comment='优先级: low/medium/high/urgent')
    deadline = Column(DateTime, comment='截止日期')
    template_id = Column(BigInteger, comment='使用的模板ID')
    creator_id = Column(BigInteger, nullable=False, comment='创建人ID')
    completed_at = Column(DateTime, comment='完成时间')
    
    __table_args__ = (
        Index('idx_project', 'project_id'),
        Index('idx_status', 'status'),
        Index('idx_creator', 'creator_id'),
    )


class ReviewTestCase(BaseModel):
    """评审用例关联表"""
    __tablename__ = 'review_test_cases'
    
    review_id = Column(BigInteger, nullable=False, comment='评审ID')
    test_case_id = Column(BigInteger, nullable=False, comment='测试用例ID')
    
    __table_args__ = (
        UniqueConstraint('review_id', 'test_case_id', name='uk_review_case'),
        Index('idx_review', 'review_id'),
        Index('idx_test_case', 'test_case_id'),
    )


class ReviewAssignment(BaseModel):
    """评审分配表"""
    __tablename__ = 'review_assignments'
    
    review_id = Column(BigInteger, nullable=False, comment='评审ID')
    reviewer_id = Column(BigInteger, nullable=False, comment='评审人ID')
    status = Column(String(20), default='pending', comment='评审状态: pending/in_progress/completed/rejected')
    comment = Column(Text, comment='评审意见')
    checklist_results = Column(JSON, comment='检查清单结果')
    reviewed_at = Column(DateTime, comment='评审时间')
    assigned_at = Column(DateTime, default=func.now(), comment='分配时间')
    
    __table_args__ = (
        UniqueConstraint('review_id', 'reviewer_id', name='uk_review_reviewer'),
        Index('idx_review', 'review_id'),
        Index('idx_reviewer', 'reviewer_id'),
        Index('idx_status', 'status'),
    )


class ReviewComment(BaseModel):
    """评审意见表"""
    __tablename__ = 'review_comments'
    
    review_id = Column(BigInteger, nullable=False, comment='评审ID')
    test_case_id = Column(BigInteger, comment='相关用例ID')
    author_id = Column(BigInteger, nullable=False, comment='评论者ID')
    comment_type = Column(String(20), default='general', comment='意见类型: general/suggestion/issue/question')
    content = Column(Text, nullable=False, comment='意见内容')
    step_number = Column(Integer, comment='步骤序号')
    is_resolved = Column(Boolean, default=False, comment='是否已解决')
    
    __table_args__ = (
        Index('idx_review', 'review_id'),
        Index('idx_test_case', 'test_case_id'),
        Index('idx_author', 'author_id'),
        Index('idx_resolved', 'is_resolved'),
    )


class ReviewTemplate(BaseModel):
    """评审模板表"""
    __tablename__ = 'review_templates'
    
    name = Column(String(200), nullable=False, comment='模板名称')
    description = Column(Text, comment='模板描述')
    checklist = Column(JSON, comment='检查清单')
    is_active = Column(Boolean, default=True, comment='是否启用')
    creator_id = Column(BigInteger, nullable=False, comment='创建人ID')
    
    __table_args__ = (
        Index('idx_creator', 'creator_id'),
        Index('idx_active', 'is_active'),
    )


class ReviewResult(Base):
    """评审结果表"""
    __tablename__ = 'review_results'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    review_id = Column(BigInteger, nullable=False, comment='评审ID')
    test_case_id = Column(BigInteger, nullable=False, comment='测试用例ID')
    reviewer_id = Column(BigInteger, nullable=False, comment='评审人ID')
    result = Column(String(20), nullable=False, comment='评审结果: pass/fail/modify')
    comment = Column(Text, comment='评审意见')
    reviewed_at = Column(DateTime, default=func.now(), comment='评审时间')
    
    # 使用与数据库表匹配的字段名
    creation_date = Column(DateTime, default=func.now(), comment='创建时间')
    created_by = Column(BigInteger, comment='创建人')
    updation_date = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
    updated_by = Column(BigInteger, comment='更新人')
    enabled_flag = Column(Integer, default=1, comment='启用标志')
    trace_id = Column(String(36), comment='追踪ID')
    
    __table_args__ = (
        UniqueConstraint('review_id', 'test_case_id', 'reviewer_id', name='uk_review_case_reviewer'),
        Index('idx_review', 'review_id'),
        Index('idx_test_case', 'test_case_id'),
        Index('idx_reviewer', 'reviewer_id'),
        Index('idx_result', 'result'),
    )


class TemplateProject(BaseModel):
    """模板项目关联表"""
    __tablename__ = 'template_projects'
    
    template_id = Column(BigInteger, nullable=False, comment='模板ID')
    project_id = Column(BigInteger, nullable=False, comment='项目ID')
    
    __table_args__ = (
        UniqueConstraint('template_id', 'project_id', name='uk_template_project'),
        Index('idx_template', 'template_id'),
        Index('idx_project', 'project_id'),
    )


class TemplateDefaultReviewer(BaseModel):
    """模板默认评审人关联表"""
    __tablename__ = 'template_default_reviewers'
    
    template_id = Column(BigInteger, nullable=False, comment='模板ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    
    __table_args__ = (
        UniqueConstraint('template_id', 'user_id', name='uk_template_user'),
        Index('idx_template', 'template_id'),
        Index('idx_user', 'user_id'),
    )