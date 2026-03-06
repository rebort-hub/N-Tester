"""
UI自动化模块 - CRUD操作
"""
import logging
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.core.base_crud import BaseCRUD
from .model import (
    UIProjectModel,
    UIElementGroupModel,
    UIElementModel,
    UIPageObjectModel,
    UIPageObjectElementModel,
    UITestCaseModel,
    UITestStepModel,
    UITestSuiteModel,
    UISuiteCaseModel,
    UIExecutionModel
)

logger = logging.getLogger(__name__)


class UIProjectCRUD(BaseCRUD[UIProjectModel]):
    """UI项目CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UIProjectModel, db)
    
    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        filters: List = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UIProjectModel], int]:
        """根据过滤条件获取UI项目列表"""
        if filters is None:
            filters = []
        
        # 添加enabled_flag过滤
        filters.append(self.model.enabled_flag == 1)
        
        # 查询总数
        count_query = select(func.count(self.model.id)).where(and_(*filters))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model).where(and_(*filters)).offset(skip).limit(limit).order_by(self.model.id.desc())
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def get_by_project_id(
        self,
        db: AsyncSession,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UIProjectModel], int]:
        """根据项目ID获取UI项目列表"""
        # 查询总数
        count_query = select(func.count(self.model.id)).where(
            and_(
                self.model.project_id == project_id,
                self.model.enabled_flag == 1
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model).where(
            and_(
                self.model.project_id == project_id,
                self.model.enabled_flag == 1
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total


class UIElementGroupCRUD(BaseCRUD[UIElementGroupModel]):
    """UI元素分组CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UIElementGroupModel, db)
    
    async def get_by_ui_project_id(
        self,
        db: AsyncSession,
        ui_project_id: int
    ) -> List[UIElementGroupModel]:
        """根据UI项目ID获取分组列表（树形结构）"""
        query = select(self.model).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        ).order_by(self.model.order_num, self.model.id)
        
        result = await db.execute(query)
        return list(result.scalars().all())


class UIElementCRUD(BaseCRUD[UIElementModel]):
    """UI元素CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UIElementModel, db)
    
    async def get_by_group_id(
        self,
        db: AsyncSession,
        group_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UIElementModel], int]:
        """根据分组ID获取元素列表"""
        # 查询总数
        count_query = select(func.count(self.model.id)).where(
            and_(
                self.model.group_id == group_id,
                self.model.enabled_flag == 1
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model).where(
            and_(
                self.model.group_id == group_id,
                self.model.enabled_flag == 1
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def get_by_ui_project_id(
        self,
        db: AsyncSession,
        ui_project_id: int
    ) -> List[UIElementModel]:
        """根据UI项目ID获取所有元素"""
        # 需要通过group关联查询
        query = select(self.model).join(
            UIElementGroupModel,
            self.model.group_id == UIElementGroupModel.id
        ).where(
            and_(
                UIElementGroupModel.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1,
                UIElementGroupModel.enabled_flag == 1
            )
        ).order_by(self.model.group_id, self.model.id)
        
        result = await db.execute(query)
        return list(result.scalars().all())


class UIPageObjectCRUD(BaseCRUD[UIPageObjectModel]):
    """UI页面对象CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UIPageObjectModel, db)
    
    async def get_by_ui_project_id(
        self,
        db: AsyncSession,
        ui_project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UIPageObjectModel], int]:
        """根据UI项目ID获取页面对象列表"""
        # 查询总数
        count_query = select(func.count(self.model.id)).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total


class UIPageObjectElementCRUD(BaseCRUD[UIPageObjectElementModel]):
    """页面对象元素关联CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UIPageObjectElementModel, db)
    
    async def get_by_page_object_id(
        self,
        db: AsyncSession,
        page_object_id: int
    ) -> List[UIPageObjectElementModel]:
        """根据页面对象ID获取关联的元素"""
        query = select(self.model).where(
            self.model.page_object_id == page_object_id
        ).order_by(self.model.order_num)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_by_page_object_id(
        self,
        db: AsyncSession,
        page_object_id: int,
        user_id: int
    ):
        """删除页面对象的所有元素关联（物理删除）"""
        from sqlalchemy import delete as sql_delete
        
        # 物理删除所有关联记录
        query = sql_delete(self.model).where(
            self.model.page_object_id == page_object_id
        )
        await db.execute(query)
        await db.commit()
        
        await db.commit()


class UITestCaseCRUD(BaseCRUD[UITestCaseModel]):
    """UI测试用例CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UITestCaseModel, db)
    
    async def get_by_ui_project_id(
        self,
        db: AsyncSession,
        ui_project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UITestCaseModel], int]:
        """根据UI项目ID获取测试用例列表"""
        # 查询总数
        count_query = select(func.count(self.model.id)).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total


class UITestStepCRUD(BaseCRUD[UITestStepModel]):
    """UI测试步骤CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UITestStepModel, db)
    
    async def get_by_test_case_id(
        self,
        db: AsyncSession,
        test_case_id: int
    ) -> List[UITestStepModel]:
        """根据测试用例ID获取步骤列表"""
        query = select(self.model).where(
            self.model.test_case_id == test_case_id
        ).order_by(self.model.step_number)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_by_test_case_id(
        self,
        db: AsyncSession,
        test_case_id: int
    ):
        """删除测试用例的所有步骤"""
        query = select(self.model).where(
            self.model.test_case_id == test_case_id
        )
        result = await db.execute(query)
        items = result.scalars().all()
        
        for item in items:
            await db.delete(item)
        
        await db.commit()


class UITestSuiteCRUD(BaseCRUD[UITestSuiteModel]):
    """UI测试套件CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UITestSuiteModel, db)
    
    async def get_by_ui_project_id(
        self,
        db: AsyncSession,
        ui_project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[UITestSuiteModel], int]:
        """根据UI项目ID获取测试套件列表"""
        # 查询总数
        count_query = select(func.count(self.model.id)).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(self.model).where(
            and_(
                self.model.ui_project_id == ui_project_id,
                self.model.enabled_flag == 1
            )
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total


class UISuiteCaseCRUD(BaseCRUD[UISuiteCaseModel]):
    """套件用例关联CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(UISuiteCaseModel, db)
    
    async def get_by_suite_id(
        self,
        db: AsyncSession,
        suite_id: int
    ) -> List[UISuiteCaseModel]:
        """根据套件ID获取关联的用例"""
        query = select(self.model).where(
            and_(
                self.model.suite_id == suite_id,
                self.model.enabled_flag == 1
            )
        ).order_by(self.model.order_num)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_by_suite_id(
        self,
        db: AsyncSession,
        suite_id: int,
        user_id: int
    ):
        """删除套件的所有用例关联（物理删除）"""
        from sqlalchemy import delete as sql_delete
        
        # 物理删除所有关联记录
        query = sql_delete(self.model).where(
            self.model.suite_id == suite_id
        )
        await db.execute(query)
        await db.commit()


class UIExecutionCRUD(BaseCRUD):
    """UI执行记录CRUD"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(model=UIExecutionModel, db=db)
    
    async def get_by_suite_id(
        self,
        db: AsyncSession,
        suite_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[UIExecutionModel], int]:
        """根据套件ID获取执行记录"""
        # 查询总数
        count_query = select(func.count(UIExecutionModel.id)).where(
            UIExecutionModel.suite_id == suite_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(UIExecutionModel).where(
            UIExecutionModel.suite_id == suite_id
        ).order_by(UIExecutionModel.start_time.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def get_by_test_case_id(
        self,
        db: AsyncSession,
        test_case_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[UIExecutionModel], int]:
        """根据测试用例ID获取执行记录"""
        # 查询总数
        count_query = select(func.count(UIExecutionModel.id)).where(
            UIExecutionModel.test_case_id == test_case_id
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 查询数据
        query = select(UIExecutionModel).where(
            UIExecutionModel.test_case_id == test_case_id
        ).order_by(UIExecutionModel.start_time.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        return list(items), total
    
    async def get_list_with_filters(
        self,
        db: AsyncSession,
        ui_project_id: Optional[int] = None,
        suite_id: Optional[int] = None,
        test_case_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[UIExecutionModel], int]:
        """根据条件获取执行记录列表"""
        from datetime import datetime
        
        # 打印调试信息
        logger.info(f"查询参数: ui_project_id={ui_project_id}, status={status}, start_date={start_date}, end_date={end_date}")
        
        # 构建查询条件
        conditions = []
        if ui_project_id:
            conditions.append(UIExecutionModel.ui_project_id == ui_project_id)
        if suite_id:
            conditions.append(UIExecutionModel.suite_id == suite_id)
        if test_case_id:
            conditions.append(UIExecutionModel.test_case_id == test_case_id)
        if status:
            conditions.append(UIExecutionModel.status == status)
        
        # 日期过滤
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                conditions.append(UIExecutionModel.start_time >= start_dt)
                logger.info(f"开始日期过滤: >= {start_dt}")
            except ValueError as e:
                logger.error(f"开始日期解析失败: {start_date}, 错误: {e}")
        
        if end_date:
            try:
                # 结束日期包含当天，所以加1天
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                from datetime import timedelta
                end_dt = end_dt + timedelta(days=1)
                conditions.append(UIExecutionModel.start_time < end_dt)
                logger.info(f"结束日期过滤: < {end_dt}")
            except ValueError as e:
                logger.error(f"结束日期解析失败: {end_date}, 错误: {e}")
        
        # 查询总数
        count_query = select(func.count(UIExecutionModel.id))
        if conditions:
            count_query = count_query.where(*conditions)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        logger.info(f"查询结果: 总数={total}, skip={skip}, limit={limit}")
        
        # 查询数据
        query = select(UIExecutionModel)
        if conditions:
            query = query.where(*conditions)
        query = query.order_by(UIExecutionModel.start_time.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        logger.info(f"返回记录数: {len(items)}")
        
        return list(items), total
    
    async def get_by_id(
        self,
        db: AsyncSession,
        execution_id: int
    ) -> Optional[UIExecutionModel]:
        """根据ID获取执行记录"""
        query = select(UIExecutionModel).where(
            UIExecutionModel.id == execution_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
