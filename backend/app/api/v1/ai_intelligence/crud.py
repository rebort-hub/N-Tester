# -*- coding: utf-8 -*-
"""
AI智能化模块数据访问层
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from app.core.base_crud import BaseCRUD
from .model import (
    RequirementDocumentModel,
    RequirementAnalysisModel,
    BusinessRequirementModel,
    GeneratedTestCaseModel,
    TestCaseGenerationTaskModel,
    AIModelConfigModel,
    PromptConfigModel,
    GenerationConfigModel,
    AICaseModel,
    AIExecutionRecordModel,
    FigmaConfigModel
)


class RequirementDocumentCRUD(BaseCRUD[RequirementDocumentModel]):
    """需求文档CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(RequirementDocumentModel, db)
    
    async def get_by_project(self, project_id: int) -> List[RequirementDocumentModel]:
        """获取项目下的所有需求文档"""
        conditions = [
            self.model.project_id == project_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items
    
    async def get_with_analysis(self, document_id: int) -> Optional[RequirementDocumentModel]:
        """获取包含分析结果的需求文档"""
        stmt = select(self.model).where(
            and_(self.model.id == document_id, self.model.enabled_flag == 1)
        ).options(selectinload(self.model.analysis))
        result = await self.db.execute(stmt)
        return result.scalars().first()


class RequirementAnalysisCRUD(BaseCRUD[RequirementAnalysisModel]):
    """需求分析CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(RequirementAnalysisModel, db)
    
    async def get_by_document(self, document_id: int) -> Optional[RequirementAnalysisModel]:
        """根据文档ID获取分析结果"""
        stmt = select(self.model).where(
            and_(self.model.document_id == document_id, self.model.enabled_flag == 1)
        ).options(selectinload(self.model.requirements))
        result = await self.db.execute(stmt)
        return result.scalars().first()


class BusinessRequirementCRUD(BaseCRUD[BusinessRequirementModel]):
    """业务需求CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(BusinessRequirementModel, db)
    
    async def get_by_analysis(self, analysis_id: int) -> List[BusinessRequirementModel]:
        """获取分析下的所有业务需求"""
        conditions = [
            self.model.analysis_id == analysis_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.requirement_id]
        )
        return items


class GeneratedTestCaseCRUD(BaseCRUD[GeneratedTestCaseModel]):
    """生成测试用例CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(GeneratedTestCaseModel, db)
    
    async def get_by_requirement(self, requirement_id: int) -> List[GeneratedTestCaseModel]:
        """获取需求下的所有生成测试用例"""
        conditions = [
            self.model.requirement_id == requirement_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.case_id]
        )
        return items


class TestCaseGenerationTaskCRUD(BaseCRUD[TestCaseGenerationTaskModel]):
    """测试用例生成任务CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(TestCaseGenerationTaskModel, db)
    
    async def get_by_task_id(self, task_id: str) -> Optional[TestCaseGenerationTaskModel]:
        """根据任务ID获取任务"""
        stmt = select(self.model).where(
            and_(self.model.task_id == task_id, self.model.enabled_flag == 1)
        ).options(
            selectinload(self.model.writer_model_config),
            selectinload(self.model.reviewer_model_config),
            selectinload(self.model.writer_prompt_config),
            selectinload(self.model.reviewer_prompt_config)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_project(self, project_id: int) -> List[TestCaseGenerationTaskModel]:
        """获取项目下的所有生成任务"""
        conditions = [
            self.model.project_id == project_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items
    
    async def get_by_status(self, status: str) -> List[TestCaseGenerationTaskModel]:
        """根据状态获取任务"""
        conditions = [
            self.model.status == status,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items


class AIModelConfigCRUD(BaseCRUD[AIModelConfigModel]):
    """AI模型配置CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AIModelConfigModel, db)
    
    async def get_active_by_role(self, role: str) -> Optional[AIModelConfigModel]:
        """获取指定角色的活跃配置"""
        stmt = select(self.model).where(and_(
            self.model.role == role,
            self.model.is_active == True,
            self.model.enabled_flag == 1
        )).order_by(self.model.creation_date.desc())
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_model_type_and_role(self, model_type: str, role: str) -> List[AIModelConfigModel]:
        """获取指定模型类型和角色的配置"""
        conditions = [
            self.model.model_type == model_type,
            self.model.role == role,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items
    
    async def get_active_configs(self) -> List[AIModelConfigModel]:
        """获取所有活跃的配置"""
        conditions = [
            self.model.is_active == True,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.model_type, self.model.role]
        )
        return items


class PromptConfigCRUD(BaseCRUD[PromptConfigModel]):
    """提示词配置CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(PromptConfigModel, db)
    
    async def get_active_by_type(self, prompt_type: str) -> Optional[PromptConfigModel]:
        """获取指定类型的活跃提示词配置"""
        stmt = select(self.model).where(and_(
            self.model.prompt_type == prompt_type,
            self.model.is_active == True,
            self.model.enabled_flag == 1
        )).order_by(self.model.creation_date.desc())
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_type(self, prompt_type: str) -> List[PromptConfigModel]:
        """获取指定类型的所有提示词配置"""
        conditions = [
            self.model.prompt_type == prompt_type,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items


class GenerationConfigCRUD(BaseCRUD[GenerationConfigModel]):
    """生成行为配置CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(GenerationConfigModel, db)
    
    async def get_active_config(self) -> Optional[GenerationConfigModel]:
        """获取活跃的生成配置"""
        stmt = select(self.model).where(and_(
            self.model.is_active == True,
            self.model.enabled_flag == 1
        )).order_by(self.model.creation_date.desc())
        result = await self.db.execute(stmt)
        return result.scalars().first()


class AICaseCRUD(BaseCRUD[AICaseModel]):
    """AI智能浏览器用例CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AICaseModel, db)
    
    async def get_by_ui_project(self, ui_project_id: int) -> List[AICaseModel]:
        """获取UI项目下的所有AI用例"""
        conditions = [
            self.model.ui_project_id == ui_project_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items


class AIExecutionRecordCRUD(BaseCRUD[AIExecutionRecordModel]):
    """AI执行记录CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(AIExecutionRecordModel, db)
    
    async def get_by_case(self, ai_case_id: int) -> List[AIExecutionRecordModel]:
        """获取AI用例的所有执行记录"""
        conditions = [
            self.model.ai_case_id == ai_case_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.start_time.desc()]
        )
        return items
    
    async def get_by_ui_project(self, ui_project_id: int) -> List[AIExecutionRecordModel]:
        """获取UI项目下的所有AI执行记录"""
        conditions = [
            self.model.ui_project_id == ui_project_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.start_time.desc()]
        )
        return items



class TestCaseTemplateCRUD(BaseCRUD):
    """测试用例模板CRUD"""
    
    def __init__(self, db: AsyncSession):
        from .model import TestCaseTemplateModel
        super().__init__(TestCaseTemplateModel, db)
    
    async def get_by_type(self, template_type: str) -> List:
        """根据类型获取模板"""
        conditions = [
            self.model.template_type == template_type,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.is_default.desc(), self.model.creation_date.desc()]
        )
        return items
    
    async def get_default_template(self, template_type: str = 'ui'):
        """获取默认模板"""
        stmt = select(self.model).where(
            and_(
                self.model.template_type == template_type,
                self.model.is_default == True,
                self.model.enabled_flag == 1
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()



class FigmaConfigCRUD(BaseCRUD):
    """Figma配置CRUD"""
    
    def __init__(self, db: AsyncSession):
        from .model import FigmaConfigModel
        super().__init__(FigmaConfigModel, db)
    
    async def get_by_project(self, project_id: int) -> List:
        """获取项目的Figma配置"""
        conditions = [
            self.model.project_id == project_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items
    
    async def get_by_file_key(self, file_key: str):
        """根据文件ID获取配置"""
        stmt = select(self.model).where(
            and_(
                self.model.file_key == file_key,
                self.model.enabled_flag == 1
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()


class FigmaExtractionTaskCRUD(BaseCRUD):
    """Figma提取任务CRUD"""
    
    def __init__(self, db: AsyncSession):
        from .model import FigmaExtractionTaskModel
        super().__init__(FigmaExtractionTaskModel, db)
    
    async def get_by_task_id(self, task_id: str):
        """根据任务ID获取任务"""
        stmt = select(self.model).where(
            and_(
                self.model.task_id == task_id,
                self.model.enabled_flag == 1
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    async def get_by_config(self, config_id: int) -> List:
        """获取配置的所有任务"""
        conditions = [
            self.model.config_id == config_id,
            self.model.enabled_flag == 1
        ]
        items, _ = await self.get_list_crud(
            conditions=conditions,
            order_by=[self.model.creation_date.desc()]
        )
        return items
    
    async def get_latest_by_config(self, config_id: int):
        """获取配置的最新任务"""
        stmt = select(self.model).where(
            and_(
                self.model.config_id == config_id,
                self.model.enabled_flag == 1
            )
        ).order_by(self.model.creation_date.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalars().first()

