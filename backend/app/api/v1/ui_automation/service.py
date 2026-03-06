"""
UI自动化模块 - 业务逻辑层
"""
import asyncio
import logging
import traceback
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from datetime import datetime

logger = logging.getLogger(__name__)
from .crud import (
    UIProjectCRUD,
    UIElementGroupCRUD,
    UIElementCRUD,
    UIPageObjectCRUD,
    UIPageObjectElementCRUD,
    UITestCaseCRUD,
    UITestStepCRUD,
    UITestSuiteCRUD,
    UISuiteCaseCRUD,
    UIExecutionCRUD
)
from .model import UIExecutionModel, UIProjectModel, UITestCaseModel, UITestStepModel
from .schema import (
    UIProjectCreateSchema,
    UIProjectUpdateSchema,
    UIProjectOutSchema,
    UIElementGroupCreateSchema,
    UIElementGroupUpdateSchema,
    UIElementGroupOutSchema,
    UIElementCreateSchema,
    UIElementUpdateSchema,
    UIElementOutSchema,
    UIPageObjectCreateSchema,
    UIPageObjectUpdateSchema,
    UIPageObjectOutSchema,
    UIPageObjectElementCreateSchema,
    UIPageObjectElementOutSchema,
    UITestCaseCreateSchema,
    UITestCaseUpdateSchema,
    UITestCaseOutSchema,
    UITestStepCreateSchema,
    UITestStepUpdateSchema,
    UITestStepOutSchema,
    UITestSuiteCreateSchema,
    UITestSuiteUpdateSchema,
    UITestSuiteOutSchema,
    UIExecutionOutSchema
)


class UIProjectService:
    """UI项目服务"""
    
    @staticmethod
    async def create_ui_project(
        db: AsyncSession,
        data: UIProjectCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建UI项目"""
        ui_project_crud = UIProjectCRUD(db)
        # 创建UI项目
        ui_project = await ui_project_crud.create_crud(data=data.model_dump())
        
        return UIProjectOutSchema.model_validate(ui_project).model_dump()
    
    @staticmethod
    async def get_ui_project_list(
        db: AsyncSession,
        project_id: Optional[int] = None,
        name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取UI项目列表"""
        ui_project_crud = UIProjectCRUD(db)
        skip = (page - 1) * page_size
        
        # 构建查询条件
        filters = []
        if project_id:
            filters.append(UIProjectModel.project_id == project_id)
        if name:
            filters.append(UIProjectModel.name.like(f"%{name}%"))
        
        # 查询数据
        items, total = await ui_project_crud.get_multi_with_filters(
            db=db,
            filters=filters,
            skip=skip,
            limit=page_size
        )
        
        return {
            "items": [UIProjectOutSchema.model_validate(item).model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    async def get_ui_project(
        db: AsyncSession,
        ui_project_id: int
    ) -> Dict[str, Any]:
        """获取UI项目详情"""
        ui_project_crud = UIProjectCRUD(db)
        ui_project = await ui_project_crud.get_by_id_crud(ui_project_id)
        if not ui_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI项目不存在"
            )
        
        return UIProjectOutSchema.model_validate(ui_project).model_dump()
    
    @staticmethod
    async def update_ui_project(
        db: AsyncSession,
        ui_project_id: int,
        data: UIProjectUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新UI项目"""
        ui_project_crud = UIProjectCRUD(db)
        ui_project = await ui_project_crud.get_by_id_crud(ui_project_id)
        if not ui_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI项目不存在"
            )
        
        # 更新UI项目
        updated_project = await ui_project_crud.update_crud(ui_project.id, data.model_dump(exclude_unset=True))
        
        return UIProjectOutSchema.model_validate(updated_project).model_dump()
    
    @staticmethod
    async def delete_ui_project(
        db: AsyncSession,
        ui_project_id: int,
        user_id: int
    ):
        """删除UI项目"""
        ui_project_crud = UIProjectCRUD(db)
        ui_project = await ui_project_crud.get_by_id_crud(ui_project_id)
        if not ui_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI项目不存在"
            )
        
        await ui_project_crud.delete_crud(ids=[ui_project_id])


class UIElementGroupService:
    """UI元素分组服务"""
    
    @staticmethod
    async def create_element_group(
        db: AsyncSession,
        data: UIElementGroupCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建元素分组"""
        element_group_crud = UIElementGroupCRUD(db)
        group = await element_group_crud.create_crud(data=data.model_dump())
        
        return UIElementGroupOutSchema.model_validate(group).model_dump()
    
    @staticmethod
    async def get_element_group_tree(
        db: AsyncSession,
        ui_project_id: int
    ) -> List[Dict[str, Any]]:
        """获取元素分组树"""
        element_group_crud = UIElementGroupCRUD(db)
        
        # 获取所有分组
        groups = await element_group_crud.get_by_ui_project_id(
            db=db,
            ui_project_id=ui_project_id
        )
        
        # 构建树形结构
        group_dict = {}
        root_groups = []
        
        # 初始化分组字典
        for group in groups:
            group_data = UIElementGroupOutSchema.model_validate(group).model_dump()
            group_data['children'] = []
            group_dict[group.id] = group_data
        
        # 构建树形结构
        for group_data in group_dict.values():
            if group_data['parent_id'] is None:
                root_groups.append(group_data)
            else:
                parent = group_dict.get(group_data['parent_id'])
                if parent:
                    parent['children'].append(group_data)
        
        return root_groups
    
    @staticmethod
    async def update_element_group(
        db: AsyncSession,
        group_id: int,
        data: UIElementGroupUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新元素分组"""
        element_group_crud = UIElementGroupCRUD(db)
        group = await element_group_crud.get_by_id_crud(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="元素分组不存在"
            )
        
        updated_group = await element_group_crud.update_crud(group.id, data.model_dump(exclude_unset=True))
        
        return UIElementGroupOutSchema.model_validate(updated_group).model_dump()
    
    @staticmethod
    async def delete_element_group(
        db: AsyncSession,
        group_id: int,
        user_id: int
    ):
        """删除元素分组"""
        element_group_crud = UIElementGroupCRUD(db)
        group = await element_group_crud.get_by_id_crud(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="元素分组不存在"
            )
        
        await element_group_crud.delete_crud(ids=[group_id])


class UIElementService:
    """UI元素服务"""
    
    @staticmethod
    async def create_element(
        db: AsyncSession,
        data: UIElementCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建UI元素"""
        element_crud = UIElementCRUD(db)
        element = await element_crud.create_crud(data=data.model_dump())
        
        return UIElementOutSchema.model_validate(element).model_dump()
    
    @staticmethod
    async def get_element_list(
        db: AsyncSession,
        group_id: int,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """获取元素列表"""
        element_crud = UIElementCRUD(db)
        skip = (page - 1) * page_size
        items, total = await element_crud.get_by_group_id(
            db=db,
            group_id=group_id,
            skip=skip,
            limit=page_size
        )
        
        return {
            "items": [UIElementOutSchema.model_validate(item).model_dump() for item in items],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    async def get_element(
        db: AsyncSession,
        element_id: int
    ) -> Dict[str, Any]:
        """获取元素详情"""
        element_crud = UIElementCRUD(db)
        element = await element_crud.get_by_id_crud(element_id)
        if not element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI元素不存在"
            )
        
        return UIElementOutSchema.model_validate(element).model_dump()
    
    @staticmethod
    async def update_element(
        db: AsyncSession,
        element_id: int,
        data: UIElementUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新UI元素"""
        element_crud = UIElementCRUD(db)
        element = await element_crud.get_by_id_crud(element_id)
        if not element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI元素不存在"
            )
        
        updated_element = await element_crud.update_crud(element.id, data.model_dump(exclude_unset=True))
        
        return UIElementOutSchema.model_validate(updated_element).model_dump()
    
    @staticmethod
    async def delete_element(
        db: AsyncSession,
        element_id: int,
        user_id: int
    ):
        """删除UI元素"""
        element_crud = UIElementCRUD(db)
        element = await element_crud.get_by_id_crud(element_id)
        if not element:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI元素不存在"
            )
        
        await element_crud.delete_crud(ids=[element_id])


class UIPageObjectService:
    """UI页面对象服务"""
    
    @staticmethod
    async def create_page_object(
        db: AsyncSession,
        data: UIPageObjectCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建页面对象"""
        page_object_crud = UIPageObjectCRUD(db)
        page_object = await page_object_crud.create_crud(data=data.model_dump())
        
        return UIPageObjectOutSchema.model_validate(page_object).model_dump()
    
    @staticmethod
    async def get_page_object_list(
        db: AsyncSession,
        ui_project_id: int,
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """获取页面对象列表"""
        page_object_crud = UIPageObjectCRUD(db)
        page_object_element_crud = UIPageObjectElementCRUD(db)
        skip = (page - 1) * page_size
        items, total = await page_object_crud.get_by_ui_project_id(
            db=db,
            ui_project_id=ui_project_id,
            skip=skip,
            limit=page_size
        )
        
        # 获取每个页面对象的元素数量
        result_items = []
        for item in items:
            page_object_data = UIPageObjectOutSchema.model_validate(item).model_dump()
            # 获取关联的元素数量
            page_object_elements = await page_object_element_crud.get_by_page_object_id(
                db=db,
                page_object_id=item.id
            )
            page_object_data['element_count'] = len(page_object_elements)
            result_items.append(page_object_data)
        
        return {
            "items": result_items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    async def get_page_object(
        db: AsyncSession,
        page_object_id: int
    ) -> Dict[str, Any]:
        """获取页面对象详情"""
        page_object_crud = UIPageObjectCRUD(db)
        page_object_element_crud = UIPageObjectElementCRUD(db)
        element_crud = UIElementCRUD(db)
        
        page_object = await page_object_crud.get_by_id_crud(page_object_id)
        if not page_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="页面对象不存在"
            )
        
        # 获取关联的元素
        page_object_elements = await page_object_element_crud.get_by_page_object_id(
            db=db,
            page_object_id=page_object_id
        )
        
        # 获取元素详情
        elements = []
        for poe in page_object_elements:
            element = await element_crud.get_by_id_crud(poe.element_id)
            if element:
                element_data = UIElementOutSchema.model_validate(element).model_dump()
                element_data['method_name'] = poe.method_name
                element_data['is_property'] = poe.is_property
                element_data['order_num'] = poe.order_num
                element_data['page_object_element_id'] = poe.id
                elements.append(element_data)
        
        result = UIPageObjectOutSchema.model_validate(page_object).model_dump()
        result['elements'] = sorted(elements, key=lambda x: x['order_num'])
        result['element_count'] = len(elements)
        
        return result
    
    @staticmethod
    async def update_page_object(
        db: AsyncSession,
        page_object_id: int,
        data: UIPageObjectUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新页面对象"""
        page_object_crud = UIPageObjectCRUD(db)
        page_object_element_crud = UIPageObjectElementCRUD(db)
        
        page_object = await page_object_crud.get_by_id_crud(page_object_id)
        if not page_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="页面对象不存在"
            )
        
        # 更新页面对象基本信息
        elements_data = data.elements
        page_object_data = data.model_dump(exclude={'elements'}, exclude_unset=True)
        
        updated_page_object = await page_object_crud.update_crud(page_object.id, page_object_data)
        
        # 如果提供了元素列表，更新关联关系
        if elements_data is not None:
            # 删除旧的关联
            await page_object_element_crud.delete_by_page_object_id(
                db=db,
                page_object_id=page_object_id,
                user_id=user_id
            )
            
            # 创建新的关联
            for element_info in elements_data:
                poe_data = {
                    'page_object_id': page_object_id,
                    'element_id': element_info['element_id'],
                    'method_name': element_info.get('method_name', ''),
                    'is_property': element_info.get('is_property', False),
                    'order_num': element_info.get('order_num', 0),
                    'enabled_flag': 1
                }
                await page_object_element_crud.create_crud(data=poe_data)
        
        result = UIPageObjectOutSchema.model_validate(updated_page_object).model_dump()
        
        # 获取元素数量
        page_object_elements = await page_object_element_crud.get_by_page_object_id(
            db=db,
            page_object_id=page_object_id
        )
        result['element_count'] = len(page_object_elements)
        
        return result
    
    @staticmethod
    async def delete_page_object(
        db: AsyncSession,
        page_object_id: int,
        user_id: int
    ):
        """删除页面对象"""
        page_object_crud = UIPageObjectCRUD(db)
        page_object = await page_object_crud.get_by_id_crud(page_object_id)
        if not page_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="页面对象不存在"
            )
        
        await page_object_crud.delete_crud(ids=[page_object_id])


class UITestCaseService:
    """UI测试用例服务"""
    
    @staticmethod
    async def create_test_case(
        db: AsyncSession,
        data: UITestCaseCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建测试用例"""
        test_case_crud = UITestCaseCRUD(db)
        test_case = await test_case_crud.create_crud(data=data.model_dump())
        
        return UITestCaseOutSchema.model_validate(test_case).model_dump()
    
    @staticmethod
    async def get_test_case_list(
        db: AsyncSession,
        ui_project_id: int,
        page: int = 1,
        page_size: int = 100,
        name: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取测试用例列表"""
        test_case_crud = UITestCaseCRUD(db)
        skip = (page - 1) * page_size
        
        # 构建查询条件
        conditions = [
            UITestCaseModel.ui_project_id == ui_project_id,
            UITestCaseModel.enabled_flag == 1
        ]
        if name:
            conditions.append(UITestCaseModel.name.ilike(f'%{name}%'))
        if priority:
            conditions.append(UITestCaseModel.priority == priority)
        
        # 查询测试用例
        query = select(UITestCaseModel).where(and_(*conditions)).order_by(UITestCaseModel.id.desc()).offset(skip).limit(page_size)
        result = await db.execute(query)
        items = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count(UITestCaseModel.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 批量获取每个测试用例的步骤数量
        test_case_ids = [item.id for item in items]
        if test_case_ids:
            # 查询步骤数量
            steps_count_query = select(
                UITestStepModel.test_case_id,
                func.count(UITestStepModel.id).label('steps_count')
            ).where(
                UITestStepModel.test_case_id.in_(test_case_ids)
            ).group_by(UITestStepModel.test_case_id)
            
            steps_result = await db.execute(steps_count_query)
            steps_count_map = {row.test_case_id: row.steps_count for row in steps_result}
        else:
            steps_count_map = {}
        
        # 构建返回数据，添加步骤数量
        items_data = []
        for item in items:
            item_dict = UITestCaseOutSchema.model_validate(item).model_dump()
            item_dict['steps_count'] = steps_count_map.get(item.id, 0)
            items_data.append(item_dict)
        
        return {
            "items": items_data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    async def get_test_case(
        db: AsyncSession,
        test_case_id: int
    ) -> Dict[str, Any]:
        """获取测试用例详情"""
        test_case_crud = UITestCaseCRUD(db)
        test_step_crud = UITestStepCRUD(db)
        
        test_case = await test_case_crud.get_by_id_crud(test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 获取测试步骤
        steps = await test_step_crud.get_by_test_case_id(
            db=db,
            test_case_id=test_case_id
        )
        
        result = UITestCaseOutSchema.model_validate(test_case).model_dump()
        result['steps'] = [UITestStepOutSchema.model_validate(step).model_dump() for step in steps]
        
        return result
    
    @staticmethod
    async def update_test_case(
        db: AsyncSession,
        test_case_id: int,
        data: UITestCaseUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新测试用例"""
        test_case_crud = UITestCaseCRUD(db)
        test_case = await test_case_crud.get_by_id_crud(test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        updated_test_case = await test_case_crud.update_crud(test_case.id, data.model_dump(exclude_unset=True))
        
        return UITestCaseOutSchema.model_validate(updated_test_case).model_dump()
    
    @staticmethod
    async def delete_test_case(
        db: AsyncSession,
        test_case_id: int,
        user_id: int
    ):
        """删除测试用例"""
        test_case_crud = UITestCaseCRUD(db)
        test_case = await test_case_crud.get_by_id_crud(test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        await test_case_crud.delete_crud(ids=[test_case_id])


class UITestSuiteService:
    """UI测试套件服务"""
    
    @staticmethod
    async def create_test_suite(
        db: AsyncSession,
        data: UITestSuiteCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建测试套件"""
        test_suite_crud = UITestSuiteCRUD(db)
        suite_case_crud = UISuiteCaseCRUD(db)
        
        # 创建测试套件
        test_case_ids = data.test_case_ids or []
        suite_data = data.model_dump(exclude={'test_case_ids'})
        
        test_suite = await test_suite_crud.create_crud(data=suite_data)
        
        # 关联测试用例
        for idx, test_case_id in enumerate(test_case_ids):
            suite_case_data = {
                'suite_id': test_suite.id,
                'test_case_id': test_case_id,
                'order_num': idx + 1,
                'enabled_flag': 1  # 确保启用标志为1
            }
            await suite_case_crud.create_crud(data=suite_case_data)
        
        result = UITestSuiteOutSchema.model_validate(test_suite).model_dump()
        result['test_case_count'] = len(test_case_ids)
        
        return result
    
    @staticmethod
    async def get_test_suite_list(
        db: AsyncSession,
        ui_project_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取测试套件列表"""
        test_suite_crud = UITestSuiteCRUD(db)
        suite_case_crud = UISuiteCaseCRUD(db)
        skip = (page - 1) * page_size
        items, total = await test_suite_crud.get_by_ui_project_id(
            db=db,
            ui_project_id=ui_project_id,
            skip=skip,
            limit=page_size
        )
        
        # 获取每个套件的用例数量
        result_items = []
        for item in items:
            suite_data = UITestSuiteOutSchema.model_validate(item).model_dump()
            # 获取关联的用例数量
            suite_cases = await suite_case_crud.get_by_suite_id(
                db=db,
                suite_id=item.id
            )
            suite_data['test_case_count'] = len(suite_cases)
            result_items.append(suite_data)
        
        return {
            "items": result_items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    @staticmethod
    async def get_test_suite(
        db: AsyncSession,
        test_suite_id: int
    ) -> Dict[str, Any]:
        """获取测试套件详情"""
        test_suite_crud = UITestSuiteCRUD(db)
        suite_case_crud = UISuiteCaseCRUD(db)
        test_case_crud = UITestCaseCRUD(db)
        
        test_suite = await test_suite_crud.get_by_id_crud(test_suite_id)
        if not test_suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在"
            )
        
        # 获取关联的测试用例
        suite_cases = await suite_case_crud.get_by_suite_id(
            db=db,
            suite_id=test_suite_id
        )
        
        # 获取用例详情
        test_case_list = []
        for suite_case in suite_cases:
            test_case = await test_case_crud.get_by_id_crud(suite_case.test_case_id)
            if test_case:
                test_case_data = UITestCaseOutSchema.model_validate(test_case).model_dump()
                test_case_data['order_num'] = suite_case.order_num
                test_case_list.append(test_case_data)
        
        result = UITestSuiteOutSchema.model_validate(test_suite).model_dump()
        result['test_cases'] = sorted(test_case_list, key=lambda x: x['order_num'])
        result['test_case_count'] = len(test_case_list)
        
        return result
    
    @staticmethod
    async def update_test_suite(
        db: AsyncSession,
        test_suite_id: int,
        data: UITestSuiteUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新测试套件"""
        test_suite_crud = UITestSuiteCRUD(db)
        suite_case_crud = UISuiteCaseCRUD(db)
        
        test_suite = await test_suite_crud.get_by_id_crud(test_suite_id)
        if not test_suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在"
            )
        
        # 更新套件基本信息
        test_case_ids = data.test_case_ids
        suite_data = data.model_dump(exclude={'test_case_ids'}, exclude_unset=True)
        
        updated_suite = await test_suite_crud.update_crud(test_suite.id, suite_data)
        
        # 如果提供了test_case_ids，更新关联关系
        if test_case_ids is not None:
            # 去重：确保没有重复的用例ID
            unique_case_ids = list(dict.fromkeys(test_case_ids))  # 保持顺序的去重
            
            logger.info(f"更新套件用例关联: suite_id={test_suite_id}, 原始数量={len(test_case_ids)}, 去重后数量={len(unique_case_ids)}")
            
            # 删除旧的关联
            await suite_case_crud.delete_by_suite_id(
                db=db,
                suite_id=test_suite_id,
                user_id=user_id
            )
            
            # 创建新的关联
            for idx, test_case_id in enumerate(unique_case_ids):
                suite_case_data = {
                    'suite_id': test_suite_id,
                    'test_case_id': test_case_id,
                    'order_num': idx + 1,
                    'enabled_flag': 1  # 确保启用标志为1
                }
                await suite_case_crud.create_crud(data=suite_case_data)
        
        result = UITestSuiteOutSchema.model_validate(updated_suite).model_dump()
        
        # 获取用例数量
        suite_cases = await suite_case_crud.get_by_suite_id(
            db=db,
            suite_id=test_suite_id
        )
        result['test_case_count'] = len(suite_cases)
        
        return result
    
    @staticmethod
    async def delete_test_suite(
        db: AsyncSession,
        test_suite_id: int,
        user_id: int
    ):
        """删除测试套件"""
        test_suite_crud = UITestSuiteCRUD(db)
        suite_case_crud = UISuiteCaseCRUD(db)
        
        test_suite = await test_suite_crud.get_by_id_crud(test_suite_id)
        if not test_suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在"
            )
        
        # 删除关联的用例
        await suite_case_crud.delete_by_suite_id(
            db=db,
            suite_id=test_suite_id,
            user_id=user_id
        )
        
        # 删除套件
        await test_suite_crud.delete_crud(ids=[test_suite_id])



class UITestStepService:
    """UI测试步骤服务"""
    
    @staticmethod
    async def create_test_step(
        db: AsyncSession,
        data: UITestStepCreateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """创建测试步骤"""
        test_step_crud = UITestStepCRUD(db)
        test_step = await test_step_crud.create_crud(data=data.model_dump())
        
        return UITestStepOutSchema.model_validate(test_step).model_dump()
    
    @staticmethod
    async def batch_create_test_steps(
        db: AsyncSession,
        steps_data: List[UITestStepCreateSchema],
        user_id: int
    ) -> List[Dict[str, Any]]:
        """批量创建测试步骤"""
        test_step_crud = UITestStepCRUD(db)
        created_steps = []
        
        for step_data in steps_data:
            test_step = await test_step_crud.create_crud(data=step_data.model_dump())
            created_steps.append(UITestStepOutSchema.model_validate(test_step).model_dump())
        
        return created_steps
    
    @staticmethod
    async def update_test_step(
        db: AsyncSession,
        step_id: int,
        data: UITestStepUpdateSchema,
        user_id: int
    ) -> Dict[str, Any]:
        """更新测试步骤"""
        test_step_crud = UITestStepCRUD(db)
        test_step = await test_step_crud.get_by_id_crud(step_id)
        if not test_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试步骤不存在"
            )
        
        updated_step = await test_step_crud.update_crud(test_step.id, data.model_dump(exclude_unset=True))
        
        return UITestStepOutSchema.model_validate(updated_step).model_dump()
    
    @staticmethod
    async def delete_test_step(
        db: AsyncSession,
        step_id: int,
        user_id: int
    ):
        """删除测试步骤"""
        test_step_crud = UITestStepCRUD(db)
        test_step = await test_step_crud.get_by_id_crud(step_id)
        if not test_step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试步骤不存在"
            )
        
        await test_step_crud.delete_crud(ids=[step_id])
    
    @staticmethod
    async def reorder_test_steps(
        db: AsyncSession,
        test_case_id: int,
        step_orders: List,  # List of StepOrderSchema objects
        user_id: int
    ):
        """调整测试步骤顺序"""
        test_step_crud = UITestStepCRUD(db)
        
        # 更新每个步骤的序号
        for order_info in step_orders:
            # Handle both dict and StepOrderSchema objects
            if hasattr(order_info, 'id'):
                step_id = order_info.id
                step_number = order_info.step_number
            else:
                step_id = order_info.get('id')
                step_number = order_info.get('step_number')
            
            if step_id and step_number is not None:
                test_step = await test_step_crud.get_by_id_crud(step_id)
                if test_step and test_step.test_case_id == test_case_id:
                    await test_step_crud.update_crud(step_id, {'step_number': step_number})
    
    @staticmethod
    async def get_test_steps_by_case(
        db: AsyncSession,
        test_case_id: int
    ):
        """获取测试用例的所有步骤"""
        from sqlalchemy import select
        from .model import UITestStepModel
        
        # 查询该测试用例的所有步骤，按步骤序号排序
        query = select(UITestStepModel).where(
            UITestStepModel.test_case_id == test_case_id
        ).order_by(UITestStepModel.step_number)
        
        result = await db.execute(query)
        steps = result.scalars().all()
        
        return [
            {
                'id': step.id,
                'test_case_id': step.test_case_id,
                'step_number': step.step_number,
                'action_type': step.action_type,
                'element_id': step.element_id,
                'action_value': step.action_value,
                'description': step.description,
                'assertion_type': step.assertion_type,
                'assertion_value': step.assertion_value,
                'screenshot_on_failure': step.screenshot_on_failure,
                'continue_on_failure': step.continue_on_failure,
                'creation_date': step.creation_date
            }
            for step in steps
        ]



class UIExecutionService:
    """UI执行服务"""
    
    @staticmethod
    async def execute_test_suite(
        db: AsyncSession,
        test_suite_id: int,
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """执行测试套件"""
        from datetime import datetime
        
        test_suite_crud = UITestSuiteCRUD(db)
        execution_crud = UIExecutionCRUD(db)
        
        # 获取测试套件
        test_suite = await test_suite_crud.get_by_id_crud(test_suite_id)
        if not test_suite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试套件不存在"
            )
        
        # 创建执行记录
        execution_data = {
            'ui_project_id': test_suite.ui_project_id,
            'suite_id': test_suite_id,
            'test_case_id': None,
            'engine_type': config.get('engine_type', test_suite.engine_type),
            'browser_type': config.get('browser_type', test_suite.browser_type),
            'status': 'running',
            'start_time': datetime.now(),
            'total_steps': 0,
            'passed_steps': 0,
            'failed_steps': 0,
            'executed_by': user_id
        }
        
        execution = await execution_crud.create_crud(data=execution_data)
        await db.commit()
        
        # 根据引擎类型选择执行方式
        engine_type = config.get('engine_type', test_suite.engine_type)
        
        if engine_type == 'selenium':
            # Selenium 使用线程方式执行
            import threading
            
            def run_in_thread():
                """在独立线程中运行测试套件"""
                UIExecutionService._run_test_suite_sync(
                    execution.id, test_suite, config
                )
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
        else:
            # Playwright 使用异步方式执行
            asyncio.create_task(
                UIExecutionService._run_test_suite_async(
                    execution.id, test_suite, config
                )
            )
        
        return {
            'execution_id': execution.id,
            'status': 'running',
            'message': '测试套件开始执行'
        }
    
    @staticmethod
    async def _run_test_suite_async(
        execution_id: int,
        test_suite: Any,
        config: Dict[str, Any]
    ):
        """运行测试套件（Playwright异步方式）"""
        import time
        from datetime import datetime
        from app.db.sqlalchemy import async_session
        from .execution_engine import ExecutionManager
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建新的数据库会话（避免多协程共享同一个session）
        async with async_session() as db:
            try:
                suite_case_crud = UISuiteCaseCRUD(db)
                test_case_crud = UITestCaseCRUD(db)
                test_step_crud = UITestStepCRUD(db)
                execution_crud = UIExecutionCRUD(db)
                
                # 创建执行引擎
                engine = ExecutionManager.create_execution(execution_id, db)
                
                # 获取套件中的所有用例
                suite_cases = await suite_case_crud.get_by_suite_id(
                    db=db,
                    suite_id=test_suite.id
                )
                
                total_steps = 0
                passed_steps = 0
                failed_steps = 0
                all_logs = []
                total_duration = 0
                
                # 执行每个测试用例
                for suite_case in suite_cases:
                    test_case = await test_case_crud.get_by_id_crud(suite_case.test_case_id)
                    if not test_case:
                        continue
                    
                    # 获取测试步骤
                    steps = await test_step_crud.get_by_test_case_id(
                        db=db,
                        test_case_id=test_case.id
                    )
                    
                    # 执行测试用例
                    result = await engine.execute_test_case(test_case, steps, config)
                    
                    total_steps += result['total_steps']
                    passed_steps += result['passed_steps']
                    failed_steps += result['failed_steps']
                    total_duration += result.get('duration', 0)
                    all_logs.append(result['logs'])
                    
                    if engine.is_stopped:
                        break
                
                # 计算总执行时长（如果没有从result中累加，则使用总时间）
                if total_duration == 0:
                    total_duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录
                final_status = 'stopped' if engine.is_stopped else ('success' if failed_steps == 0 else 'failed')
                await execution_crud.update_crud(execution_id, {
                    'status': final_status,
                    'end_time': datetime.now(),
                    'total_steps': total_steps,
                    'passed_steps': passed_steps,
                    'failed_steps': failed_steps,
                    'duration': total_duration,
                    'logs': '\n\n'.join(all_logs)
                })
                
                # 提交事务
                await db.commit()
                
            except Exception as e:
                # 回滚事务
                await db.rollback()
                
                # 计算执行时长
                duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录为失败
                try:
                    await execution_crud.update_crud(execution_id, {
                        'status': 'failed',
                        'end_time': datetime.now(),
                        'duration': duration,
                        'error_message': str(e),
                        'logs': f"执行异常: {str(e)}"
                    })
                    await db.commit()
                except:
                    pass
            finally:
                # 清理执行实例
                ExecutionManager.remove_execution(execution_id)
    
    @staticmethod
    def _run_test_suite_sync(
        execution_id: int,
        test_suite: Any,
        config: Dict[str, Any]
    ):
        """运行测试套件（Selenium同步方式）"""
        import time
        from datetime import datetime
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import sessionmaker
        from config import Configs
        from .model import UIExecutionModel, UITestCaseModel, UITestStepModel, UIElementModel, UIProjectModel
        from .selenium_execution_wrapper import SeleniumExecutionEngine
        
        logger.info(f"线程启动: 执行ID={execution_id}, 测试套件={test_suite.name}")
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 创建同步数据库连接
            sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
            SyncSession = sessionmaker(bind=sync_engine)
            sync_db = SyncSession()
            
            try:
                # 获取套件中的所有用例
                from .model import UISuiteCaseModel
                suite_cases = sync_db.query(UISuiteCaseModel).filter(
                    UISuiteCaseModel.suite_id == test_suite.id
                ).order_by(UISuiteCaseModel.order_num).all()
                
                if not suite_cases:
                    # 没有用例，直接标记为成功
                    duration = int((time.time() - start_time) * 1000)
                    stmt = update(UIExecutionModel).where(
                        UIExecutionModel.id == execution_id
                    ).values(
                        status='success',
                        end_time=datetime.now(),
                        total_steps=0,
                        passed_steps=0,
                        failed_steps=0,
                        duration=duration,
                        logs='测试套件中没有用例'
                    )
                    sync_db.execute(stmt)
                    sync_db.commit()
                    return
                
                # 获取 UI 项目的 base_url
                ui_project = sync_db.query(UIProjectModel).filter(
                    UIProjectModel.id == test_suite.ui_project_id
                ).first()
                
                base_url = ui_project.base_url if ui_project else None
                
                # 创建 Selenium 执行引擎
                selenium_engine = SeleniumExecutionEngine(execution_id=execution_id)
                
                total_steps = 0
                passed_steps = 0
                failed_steps = 0
                all_logs = []
                
                # 执行每个测试用例
                for suite_case in suite_cases:
                    test_case = sync_db.query(UITestCaseModel).filter(
                        UITestCaseModel.id == suite_case.test_case_id
                    ).first()
                    
                    if not test_case:
                        continue
                    
                    # 获取测试步骤
                    steps = sync_db.query(UITestStepModel).filter(
                        UITestStepModel.test_case_id == test_case.id
                    ).order_by(UITestStepModel.step_number).all()
                    
                    # 准备测试用例数据
                    test_case_data = {
                        'id': test_case.id,
                        'name': test_case.name,
                        'ui_project_id': test_case.ui_project_id,
                        'base_url': base_url
                    }
                    
                    # 准备测试步骤数据
                    steps_data = []
                    for step in steps:
                        step_dict = {
                            'id': step.id,
                            'step_number': step.step_number,
                            'action_type': step.action_type,
                            'action_value': step.action_value,
                            'description': step.description,
                            'assertion_type': step.assertion_type,
                            'assertion_value': step.assertion_value,
                            'element': None
                        }
                        
                        # 如果有元素，获取元素数据
                        if step.element_id:
                            element = sync_db.query(UIElementModel).filter(
                                UIElementModel.id == step.element_id
                            ).first()
                            
                            if element:
                                step_dict['element'] = {
                                    'id': element.id,
                                    'name': element.name,
                                    'locator_strategy': element.locator_strategy,
                                    'locator_value': element.locator_value,
                                    'wait_timeout': getattr(element, 'wait_timeout', None) or 5.0,
                                    'force_action': getattr(element, 'force_action', False)
                                }
                        
                        steps_data.append(step_dict)
                    
                    # 执行测试用例
                    logger.info(f"开始执行测试用例: {test_case.name}")
                    result = selenium_engine.execute_test_case(test_case_data, steps_data, config)
                    logger.info(f"测试用例执行完成: status={result['status']}")
                    
                    total_steps += result['total_steps']
                    passed_steps += result['passed_steps']
                    failed_steps += result['failed_steps']
                    all_logs.append(f"\n{'='*80}\n测试用例: {test_case.name}\n{'='*80}\n{result['logs']}")
                
                # 计算总执行时长
                duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录
                final_status = 'success' if failed_steps == 0 else 'failed'
                stmt = update(UIExecutionModel).where(
                    UIExecutionModel.id == execution_id
                ).values(
                    status=final_status,
                    end_time=datetime.now(),
                    total_steps=total_steps,
                    passed_steps=passed_steps,
                    failed_steps=failed_steps,
                    duration=duration,
                    logs='\n\n'.join(all_logs)
                )
                
                sync_db.execute(stmt)
                sync_db.commit()
                logger.info(f"执行记录已更新: execution_id={execution_id}, duration={duration}ms")
                
            finally:
                sync_db.close()
                sync_engine.dispose()
                
        except Exception as e:
            logger.error(f"线程执行失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 计算执行时长
            duration = int((time.time() - start_time) * 1000)
            
            # 更新为失败状态
            try:
                sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
                SyncSession = sessionmaker(bind=sync_engine)
                sync_db = SyncSession()
                
                stmt = update(UIExecutionModel).where(
                    UIExecutionModel.id == execution_id
                ).values(
                    status='failed',
                    end_time=datetime.now(),
                    duration=duration,
                    error_message=str(e),
                    logs=f"执行异常: {str(e)}\n\n{traceback.format_exc()}"
                )
                sync_db.execute(stmt)
                sync_db.commit()
                sync_db.close()
                sync_engine.dispose()
            except Exception as db_error:
                logger.error(f"更新失败状态失败: {str(db_error)}")
    
    @staticmethod
    async def execute_test_case(
        db: AsyncSession,
        test_case_id: int,
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """执行单个测试用例（直接同步执行）"""
        from datetime import datetime
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import sessionmaker
        from config import config as app_config
        from .model import UIExecutionModel
        from .sync_execution_engine import SyncExecutionEngine
        
        test_case_crud = UITestCaseCRUD(db)
        test_step_crud = UITestStepCRUD(db)
        execution_crud = UIExecutionCRUD(db)
        ui_project_crud = UIProjectCRUD(db)
        
        # 获取测试用例
        test_case = await test_case_crud.get_by_id_crud(test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 获取 UI 项目（获取 base_url）
        ui_project = await ui_project_crud.get_by_id_crud(test_case.ui_project_id)
        if not ui_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UI项目不存在"
            )
        
        # 获取测试步骤
        steps = await test_step_crud.get_by_test_case_id(
            db=db,
            test_case_id=test_case_id
        )
        
        # 准备测试用例数据
        test_case_data = {
            'id': test_case.id,
            'name': test_case.name,
            'ui_project_id': test_case.ui_project_id,
            'base_url': ui_project.base_url
        }
        
        # 准备测试步骤数据
        steps_data = []
        for step in steps:
            step_dict = {
                'id': step.id,
                'step_number': step.step_number,
                'action_type': step.action_type,
                'action_value': step.action_value,
                'description': step.description,
                'assertion_type': step.assertion_type,
                'assertion_value': step.assertion_value,
                'element': None
            }
            
            # 如果有元素，获取元素数据
            if step.element_id:
                from .model import UIElementModel
                from sqlalchemy import select
                query = select(UIElementModel).where(UIElementModel.id == step.element_id)
                result = await db.execute(query)
                element = result.scalar_one_or_none()
                
                if element:
                    step_dict['element'] = {
                        'id': element.id,
                        'name': element.name,
                        'locator_strategy': element.locator_strategy,
                        'locator_value': element.locator_value,
                        'wait_timeout': getattr(element, 'wait_timeout', None) or getattr(element, 'wait_time', 5000) / 1000
                    }
            
            steps_data.append(step_dict)
        
        # 创建执行记录
        execution_data = {
            'ui_project_id': test_case.ui_project_id,
            'suite_id': None,
            'test_case_id': test_case_id,
            'engine_type': config.get('engine_type', 'playwright'),
            'browser_type': config.get('browser_type', 'chromium'),
            'status': 'running',
            'start_time': datetime.now(),
            'total_steps': len(steps_data),
            'passed_steps': 0,
            'failed_steps': 0,
            'executed_by': user_id
        }
        
        execution = await execution_crud.create_crud(data=execution_data)
        await db.commit()
        
        # 使用线程执行（完全脱离 asyncio，参考 testhub）
        import threading
        
        def run_in_thread():
            """在独立线程中运行测试引擎"""
            import time
            from datetime import datetime
            from sqlalchemy import create_engine, update
            from sqlalchemy.orm import sessionmaker
            from config import Configs
            from .model import UIExecutionModel
            
            logger.info(f"线程启动: 执行ID={execution.id}, 测试用例={test_case_data['name']}")
            
            try:
                # 根据引擎类型选择执行引擎
                engine_type = config.get('engine_type', 'playwright')
                
                if engine_type == 'playwright':
                    from .sync_execution_engine import SyncExecutionEngine
                    engine = SyncExecutionEngine()
                elif engine_type == 'selenium':
                    from .selenium_execution_wrapper import SeleniumExecutionEngine
                    engine = SeleniumExecutionEngine()
                else:
                    raise ValueError(f"不支持的执行引擎: {engine_type}")
                
                # 执行测试用例（同步，在独立线程中）
                logger.info(f"开始执行测试用例: {test_case_data['name']}, 引擎: {engine_type}")
                result = engine.execute_test_case(test_case_data, steps_data, config)
                logger.info(f"测试用例执行完成: status={result['status']}")
                
                # 更新执行记录（使用同步数据库）
                sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
                SyncSession = sessionmaker(bind=sync_engine)
                sync_db = SyncSession()
                
                try:
                    stmt = update(UIExecutionModel).where(
                        UIExecutionModel.id == execution.id
                    ).values(
                        status=result['status'],
                        end_time=datetime.now(),
                        total_steps=result['total_steps'],
                        passed_steps=result['passed_steps'],
                        failed_steps=result['failed_steps'],
                        duration=result['duration'],
                        logs=result['logs'],
                        screenshots=result.get('screenshots', []),  # 保存截图列表
                        error_message=result.get('error_message')
                    )
                    
                    sync_db.execute(stmt)
                    sync_db.commit()
                    logger.info(f"执行记录已更新: execution_id={execution.id}")
                finally:
                    sync_db.close()
                    sync_engine.dispose()
                    
            except Exception as e:
                logger.error(f"线程执行失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                
                # 更新为失败状态
                try:
                    sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
                    SyncSession = sessionmaker(bind=sync_engine)
                    sync_db = SyncSession()
                    
                    stmt = update(UIExecutionModel).where(
                        UIExecutionModel.id == execution.id
                    ).values(
                        status='failed',
                        end_time=datetime.now(),
                        error_message=str(e),
                        logs=f"执行异常: {str(e)}\n\n{traceback.format_exc()}"
                    )
                    sync_db.execute(stmt)
                    sync_db.commit()
                    sync_db.close()
                    sync_engine.dispose()
                except Exception as db_error:
                    logger.error(f"更新失败状态失败: {str(db_error)}")
        
        # 启动线程（daemon=True，参考 testhub）
        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        
        return {
            'execution_id': execution.id,
            'status': 'running',
            'message': '测试用例开始执行'
        }
    
    @staticmethod
    async def stop_execution(
        db: AsyncSession,
        execution_id: int,
        user_id: int
    ):
        """停止执行"""
        from .execution_engine import ExecutionManager
        
        execution_crud = UIExecutionCRUD(db)
        
        # 检查执行记录是否存在
        execution = await execution_crud.get_by_id_crud(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        # 停止执行
        success = ExecutionManager.stop_execution(execution_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="执行已结束或不存在"
            )
    
    @staticmethod
    async def get_execution_status(
        db: AsyncSession,
        execution_id: int
    ) -> Dict[str, Any]:
        """获取执行状态"""
        execution_crud = UIExecutionCRUD(db)
        
        execution = await execution_crud.get_by_id_crud(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        # 计算进度
        progress = 0
        if execution.total_steps > 0:
            completed = execution.passed_steps + execution.failed_steps
            progress = int((completed / execution.total_steps) * 100)
        
        return {
            'id': execution.id,
            'status': execution.status,
            'progress': progress,
            'current_step': None,  # 可以从执行引擎获取
            'start_time': execution.start_time,
            'end_time': execution.end_time,
            'total_steps': execution.total_steps,
            'completed_steps': execution.passed_steps + execution.failed_steps,
            'failed_steps': execution.failed_steps
        }
    
    @staticmethod
    async def get_execution_logs(
        db: AsyncSession,
        execution_id: int
    ) -> str:
        """获取执行日志"""
        execution_crud = UIExecutionCRUD(db)
        
        execution = await execution_crud.get_by_id_crud(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        return execution.logs or ""
    
    @staticmethod
    async def get_execution_list(
        db: AsyncSession,
        query: Dict[str, Any],
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取执行历史列表"""
        from sqlalchemy import select
        from .model import UIProjectModel, UITestSuiteModel
        
        execution_crud = UIExecutionCRUD(db)
        
        skip = (page - 1) * page_size
        
        # 从query中提取过滤条件
        ui_project_id = query.get('ui_project_id')
        suite_id = query.get('suite_id')
        test_case_id = query.get('test_case_id')
        status = query.get('status')
        start_date = query.get('start_date')
        end_date = query.get('end_date')
        
        # 查询执行记录
        items, total = await execution_crud.get_list_with_filters(
            db=db,
            ui_project_id=ui_project_id,
            suite_id=suite_id,
            test_case_id=test_case_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=page_size
        )
        
        # 转换为输出格式并添加关联信息
        items_data = []
        for item in items:
            item_dict = UIExecutionOutSchema.model_validate(item).model_dump()
            
            # 处理截图数据格式
            if item.screenshots and isinstance(item.screenshots, list):
                # 确保截图数据格式正确
                screenshots_data = []
                for screenshot in item.screenshots:
                    if isinstance(screenshot, dict):
                        screenshots_data.append(screenshot)
                    elif isinstance(screenshot, str):
                        # 如果是字符串，转换为对象格式
                        screenshots_data.append({
                            'step_number': 0,
                            'step_description': '截图',
                            'error_message': '',
                            'screenshot': screenshot,
                            'timestamp': item.creation_date.isoformat() if item.creation_date else ''
                        })
                item_dict['screenshots'] = screenshots_data
            else:
                item_dict['screenshots'] = []
            
            # 获取项目名称
            if item.ui_project_id:
                project_result = await db.execute(
                    select(UIProjectModel.name).where(UIProjectModel.id == item.ui_project_id)
                )
                project_name = project_result.scalar()
                item_dict['project_name'] = project_name
            else:
                item_dict['project_name'] = None
            
            # 获取套件名称
            if item.suite_id:
                suite_result = await db.execute(
                    select(UITestSuiteModel.name).where(UITestSuiteModel.id == item.suite_id)
                )
                suite_name = suite_result.scalar()
                item_dict['suite_name'] = suite_name
            else:
                item_dict['suite_name'] = None
            
            items_data.append(item_dict)
        
        return {
            'items': items_data,
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    async def get_execution_detail(
        db: AsyncSession,
        execution_id: int
    ) -> Dict[str, Any]:
        """获取执行详情"""
        from sqlalchemy import select
        from .model import UIProjectModel, UITestSuiteModel
        
        execution_crud = UIExecutionCRUD(db)
        
        execution = await execution_crud.get_by_id_crud(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        result = UIExecutionOutSchema.model_validate(execution).model_dump()
        
        # 处理截图数据格式
        if execution.screenshots and isinstance(execution.screenshots, list):
            # 确保截图数据格式正确
            screenshots_data = []
            for screenshot in execution.screenshots:
                if isinstance(screenshot, dict):
                    screenshots_data.append(screenshot)
                elif isinstance(screenshot, str):
                    # 如果是字符串，转换为对象格式
                    screenshots_data.append({
                        'step_number': 0,
                        'step_description': '截图',
                        'error_message': '',
                        'screenshot': screenshot,
                        'timestamp': execution.creation_date.isoformat() if execution.creation_date else ''
                    })
            result['screenshots'] = screenshots_data
        else:
            result['screenshots'] = []
        
        # 获取项目名称
        if execution.ui_project_id:
            project_result = await db.execute(
                select(UIProjectModel.name).where(UIProjectModel.id == execution.ui_project_id)
            )
            project_name = project_result.scalar()
            result['project_name'] = project_name
        else:
            result['project_name'] = None
        
        # 获取套件名称
        if execution.suite_id:
            suite_result = await db.execute(
                select(UITestSuiteModel.name).where(UITestSuiteModel.id == execution.suite_id)
            )
            suite_name = suite_result.scalar()
            result['suite_name'] = suite_name
        else:
            result['suite_name'] = None
        
        return result
    
    @staticmethod
    async def delete_execution(
        db: AsyncSession,
        execution_id: int,
        user_id: int
    ):
        """删除执行记录"""
        execution_crud = UIExecutionCRUD(db)
        
        execution = await execution_crud.get_by_id_crud(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        await execution_crud.delete_crud(ids=[execution_id])
    
    @staticmethod
    async def batch_execute_test_cases(
        db: AsyncSession,
        ui_project_id: int,
        test_case_ids: List[int],
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """批量执行测试用例"""
        from datetime import datetime
        import asyncio
        
        if not test_case_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试用例ID列表不能为空"
            )
        
        test_case_crud = UITestCaseCRUD(db)
        execution_crud = UIExecutionCRUD(db)
        
        # 验证所有测试用例是否存在
        test_cases = []
        for test_case_id in test_case_ids:
            test_case = await test_case_crud.get_by_id_crud(test_case_id)
            if not test_case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"测试用例 {test_case_id} 不存在"
                )
            test_cases.append(test_case)
        
        # 创建一个临时执行记录（用于批量执行）
        execution_data = {
            'ui_project_id': ui_project_id,
            'suite_id': None,
            'test_case_id': None,  # 批量执行不关联单个用例
            'engine_type': config.get('engine_type', 'playwright'),
            'browser_type': config.get('browser_type', 'chromium'),
            'status': 'running',
            'start_time': datetime.now(),
            'total_steps': 0,
            'passed_steps': 0,
            'failed_steps': 0,
            'executed_by': user_id
        }
        
        execution = await execution_crud.create_crud(data=execution_data)
        await db.commit()
        
        # 根据引擎类型选择执行方式
        engine_type = config.get('engine_type', 'playwright')
        
        if engine_type == 'selenium':
            # Selenium 使用线程方式执行
            import threading
            
            def run_in_thread():
                """在独立线程中运行批量测试用例"""
                UIExecutionService._run_batch_test_cases_sync(
                    execution.id, test_cases, config
                )
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
        else:
            # Playwright 使用异步方式执行
            asyncio.create_task(
                UIExecutionService._run_batch_test_cases_async(
                    execution.id, test_cases, config
                )
            )
        
        return {
            'execution_id': execution.id,
            'status': 'running',
            'message': f'开始批量执行 {len(test_case_ids)} 个测试用例'
        }
    
    @staticmethod
    async def _run_batch_test_cases_async(
        execution_id: int,
        test_cases: List[Any],
        config: Dict[str, Any]
    ):
        """运行批量测试用例（Playwright异步方式）"""
        import time
        from datetime import datetime
        from app.db.sqlalchemy import async_session
        from .execution_engine import ExecutionManager
        
        start_time = time.time()
        
        async with async_session() as db:
            try:
                test_step_crud = UITestStepCRUD(db)
                execution_crud = UIExecutionCRUD(db)
                
                # 创建执行引擎
                engine = ExecutionManager.create_execution(execution_id, db)
                
                total_steps = 0
                passed_steps = 0
                failed_steps = 0
                all_logs = []
                total_duration = 0
                
                # 执行每个测试用例
                for test_case in test_cases:
                    # 获取测试步骤
                    steps = await test_step_crud.get_by_test_case_id(
                        db=db,
                        test_case_id=test_case.id
                    )
                    
                    # 执行测试用例
                    result = await engine.execute_test_case(test_case, steps, config)
                    
                    total_steps += result['total_steps']
                    passed_steps += result['passed_steps']
                    failed_steps += result['failed_steps']
                    total_duration += result.get('duration', 0)
                    all_logs.append(result['logs'])
                    
                    if engine.is_stopped:
                        break
                
                # 计算总执行时长
                if total_duration == 0:
                    total_duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录
                final_status = 'stopped' if engine.is_stopped else ('success' if failed_steps == 0 else 'failed')
                await execution_crud.update_crud(execution_id, {
                    'status': final_status,
                    'end_time': datetime.now(),
                    'total_steps': total_steps,
                    'passed_steps': passed_steps,
                    'failed_steps': failed_steps,
                    'duration': total_duration,
                    'logs': '\n\n'.join(all_logs)
                })
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                duration = int((time.time() - start_time) * 1000)
                
                try:
                    await execution_crud.update_crud(execution_id, {
                        'status': 'failed',
                        'end_time': datetime.now(),
                        'duration': duration,
                        'error_message': str(e),
                        'logs': f"执行异常: {str(e)}"
                    })
                    await db.commit()
                except:
                    pass
            finally:
                ExecutionManager.remove_execution(execution_id)
    
    @staticmethod
    def _run_batch_test_cases_sync(
        execution_id: int,
        test_cases: List[Any],
        config: Dict[str, Any]
    ):
        """运行批量测试用例（Selenium同步方式）"""
        import time
        from datetime import datetime
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import sessionmaker
        from config import Configs
        from .model import UIExecutionModel, UITestStepModel, UIElementModel, UIProjectModel
        from .selenium_execution_wrapper import SeleniumExecutionEngine
        
        logger.info(f"线程启动: 批量执行ID={execution_id}, 用例数量={len(test_cases)}")
        
        start_time = time.time()
        
        try:
            sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
            SyncSession = sessionmaker(bind=sync_engine)
            sync_db = SyncSession()
            
            try:
                # 获取 UI 项目的 base_url
                ui_project = sync_db.query(UIProjectModel).filter(
                    UIProjectModel.id == test_cases[0].ui_project_id
                ).first()
                
                base_url = ui_project.base_url if ui_project else None
                
                # 创建 Selenium 执行引擎
                selenium_engine = SeleniumExecutionEngine()
                
                total_steps = 0
                passed_steps = 0
                failed_steps = 0
                all_logs = []
                
                # 执行每个测试用例
                for test_case in test_cases:
                    # 获取测试步骤
                    steps = sync_db.query(UITestStepModel).filter(
                        UITestStepModel.test_case_id == test_case.id
                    ).order_by(UITestStepModel.step_number).all()
                    
                    # 准备测试用例数据
                    test_case_data = {
                        'id': test_case.id,
                        'name': test_case.name,
                        'ui_project_id': test_case.ui_project_id,
                        'base_url': base_url
                    }
                    
                    # 准备测试步骤数据
                    steps_data = []
                    for step in steps:
                        step_dict = {
                            'id': step.id,
                            'step_number': step.step_number,
                            'action_type': step.action_type,
                            'action_value': step.action_value,
                            'description': step.description,
                            'assertion_type': step.assertion_type,
                            'assertion_value': step.assertion_value,
                            'element': None
                        }
                        
                        if step.element_id:
                            element = sync_db.query(UIElementModel).filter(
                                UIElementModel.id == step.element_id
                            ).first()
                            
                            if element:
                                step_dict['element'] = {
                                    'id': element.id,
                                    'name': element.name,
                                    'locator_strategy': element.locator_strategy,
                                    'locator_value': element.locator_value,
                                    'wait_timeout': getattr(element, 'wait_timeout', None) or 5.0,
                                    'force_action': getattr(element, 'force_action', False)
                                }
                        
                        steps_data.append(step_dict)
                    
                    # 执行测试用例
                    logger.info(f"开始执行测试用例: {test_case.name}")
                    result = selenium_engine.execute_test_case(test_case_data, steps_data, config)
                    logger.info(f"测试用例执行完成: status={result['status']}")
                    
                    total_steps += result['total_steps']
                    passed_steps += result['passed_steps']
                    failed_steps += result['failed_steps']
                    all_logs.append(f"\n{'='*80}\n测试用例: {test_case.name}\n{'='*80}\n{result['logs']}")
                
                # 计算总执行时长
                duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录
                final_status = 'success' if failed_steps == 0 else 'failed'
                stmt = update(UIExecutionModel).where(
                    UIExecutionModel.id == execution_id
                ).values(
                    status=final_status,
                    end_time=datetime.now(),
                    total_steps=total_steps,
                    passed_steps=passed_steps,
                    failed_steps=failed_steps,
                    duration=duration,
                    logs='\n\n'.join(all_logs)
                )
                
                sync_db.execute(stmt)
                sync_db.commit()
                logger.info(f"批量执行记录已更新: execution_id={execution_id}, duration={duration}ms")
                
            finally:
                sync_db.close()
                sync_engine.dispose()
                
        except Exception as e:
            logger.error(f"批量执行失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            duration = int((time.time() - start_time) * 1000)
            
            try:
                sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
                SyncSession = sessionmaker(bind=sync_engine)
                sync_db = SyncSession()
                
                stmt = update(UIExecutionModel).where(
                    UIExecutionModel.id == execution_id
                ).values(
                    status='failed',
                    end_time=datetime.now(),
                    duration=duration,
                    error_message=str(e),
                    logs=f"执行异常: {str(e)}\n\n{traceback.format_exc()}"
                )
                sync_db.execute(stmt)
                sync_db.commit()
                sync_db.close()
                sync_engine.dispose()
            except Exception as db_error:
                logger.error(f"更新失败状态失败: {str(db_error)}")
    
    @staticmethod
    async def batch_execute_test_suites(
        db: AsyncSession,
        suite_ids: List[int],
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """批量执行测试套件"""
        if not suite_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试套件ID列表不能为空"
            )
        
        test_suite_crud = UITestSuiteCRUD(db)
        
        # 验证所有测试套件是否存在
        for suite_id in suite_ids:
            test_suite = await test_suite_crud.get_by_id_crud(suite_id)
            if not test_suite:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"测试套件 {suite_id} 不存在"
                )
        
        # 为每个测试套件创建执行任务
        execution_ids = []
        for suite_id in suite_ids:
            result = await UIExecutionService.execute_test_suite(
                db, suite_id, config, user_id
            )
            execution_ids.append(result['execution_id'])
        
        return {
            'execution_ids': execution_ids,
            'status': 'running',
            'message': f'开始批量执行 {len(suite_ids)} 个测试套件'
        }




class UICodeGenerationService:
    """UI代码生成服务"""
    
    @staticmethod
    async def generate_page_object_code(
        db: AsyncSession,
        page_object_id: int,
        language: str = 'javascript',
        framework: str = 'playwright',
        include_comments: bool = True
    ) -> str:
        """生成页面对象代码"""
        from .code_generator import CodeGenerator
        
        page_object_crud = UIPageObjectCRUD(db)
        page_object_element_crud = UIPageObjectElementCRUD(db)
        element_crud = UIElementCRUD(db)
        
        # 获取页面对象
        page_object = await page_object_crud.get_by_id_crud(page_object_id)
        if not page_object:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="页面对象不存在"
            )
        
        # 获取关联的元素
        page_object_elements = await page_object_element_crud.get_by_page_object_id(
            db=db,
            page_object_id=page_object_id
        )
        
        elements = []
        for poe in page_object_elements:
            element = await element_crud.get_by_id_crud(poe.element_id)
            if element:
                elements.append(element)
        
        # 生成代码
        code = CodeGenerator.generate_code(
            page_object,
            elements,
            language,
            framework,
            include_comments
        )
        
        return code
    
    @staticmethod
    async def generate_project_code(
        db: AsyncSession,
        ui_project_id: int,
        language: str = 'javascript',
        framework: str = 'playwright',
        include_comments: bool = True
    ) -> List[Dict[str, str]]:
        """生成项目所有页面对象代码"""
        page_object_crud = UIPageObjectCRUD(db)
        
        # 获取项目下所有页面对象
        page_objects, _ = await page_object_crud.get_by_ui_project_id(
            db=db,
            ui_project_id=ui_project_id,
            skip=0,
            limit=1000
        )
        
        code_files = []
        for page_object in page_objects:
            code = await UICodeGenerationService.generate_page_object_code(
                db,
                page_object.id,
                language,
                framework,
                include_comments
            )
            
            # 确定文件扩展名
            ext = 'js' if language == 'javascript' else 'py'
            filename = f"{page_object.class_name or 'PageObject'}.{ext}"
            
            code_files.append({
                'filename': filename,
                'content': code
            })
        
        return code_files
    
    @staticmethod
    async def generate_test_case_code(
        db: AsyncSession,
        test_case_id: int,
        language: str = 'javascript',
        framework: str = 'playwright',
        include_comments: bool = True
    ) -> str:
        """生成测试用例代码"""
        from .code_generator import AdvancedCodeGenerator
        
        test_case_crud = UITestCaseCRUD(db)
        test_step_crud = UITestStepCRUD(db)
        element_crud = UIElementCRUD(db)
        
        # 获取测试用例
        test_case = await test_case_crud.get_by_id_crud(test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 获取测试步骤
        test_steps = await test_step_crud.get_by_test_case_id(
            db=db,
            test_case_id=test_case_id
        )
        
        # 获取步骤关联的元素，构建元素字典
        elements_dict = {}
        for step in test_steps:
            if step.element_id:
                element = await element_crud.get_by_id_crud(step.element_id)
                if element:
                    elements_dict[step.element_id] = element
        
        # 生成代码
        code = AdvancedCodeGenerator.generate_test_case_code(
            test_case,
            test_steps,
            elements_dict,
            language,
            framework
        )
        
        return code



class UIReportService:
    """UI执行报告服务"""
    
    @staticmethod
    async def get_execution_statistics(
        db: AsyncSession,
        ui_project_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取执行统计"""
        from sqlalchemy import func, and_, select
        from datetime import datetime, timedelta
        
        execution_crud = UIExecutionCRUD(db)
        
        # 构建查询条件
        conditions = []
        if ui_project_id:
            conditions.append(UIExecutionModel.ui_project_id == ui_project_id)
        if start_date:
            conditions.append(UIExecutionModel.start_time >= start_date)
        if end_date:
            conditions.append(UIExecutionModel.start_time <= end_date)
        
        # 查询总执行次数
        query = select(func.count(UIExecutionModel.id))
        if conditions:
            query = query.where(and_(*conditions))
        result = await db.execute(query)
        total_executions = result.scalar() or 0
        
        # 查询成功次数
        query = select(func.count(UIExecutionModel.id)).where(
            UIExecutionModel.status == 'success'
        )
        if conditions:
            query = query.where(and_(*conditions))
        result = await db.execute(query)
        success_count = result.scalar() or 0
        
        # 查询失败次数
        failed_count = total_executions - success_count
        
        # 计算成功率
        success_rate = (success_count / total_executions * 100) if total_executions > 0 else 0
        
        # 查询平均执行时长
        query = select(func.avg(UIExecutionModel.duration)).where(
            UIExecutionModel.duration.isnot(None)
        )
        if conditions:
            query = query.where(and_(*conditions))
        result = await db.execute(query)
        avg_duration = result.scalar() or 0
        
        # 生成趋势数据（最近7天）
        trend_data = []
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        
        for i in range(7):
            day = start_date + timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # 查询当天总执行次数
            query = select(func.count(UIExecutionModel.id)).where(
                and_(
                    UIExecutionModel.start_time >= day_start,
                    UIExecutionModel.start_time <= day_end
                )
            )
            if ui_project_id:
                query = query.where(UIExecutionModel.ui_project_id == ui_project_id)
            result = await db.execute(query)
            total_count = result.scalar() or 0
            
            # 查询当天成功次数
            query = select(func.count(UIExecutionModel.id)).where(
                and_(
                    UIExecutionModel.start_time >= day_start,
                    UIExecutionModel.start_time <= day_end,
                    UIExecutionModel.status == 'success'
                )
            )
            if ui_project_id:
                query = query.where(UIExecutionModel.ui_project_id == ui_project_id)
            result = await db.execute(query)
            success = result.scalar() or 0
            
            # 查询当天失败次数
            query = select(func.count(UIExecutionModel.id)).where(
                and_(
                    UIExecutionModel.start_time >= day_start,
                    UIExecutionModel.start_time <= day_end,
                    UIExecutionModel.status == 'failed'
                )
            )
            if ui_project_id:
                query = query.where(UIExecutionModel.ui_project_id == ui_project_id)
            result = await db.execute(query)
            failed = result.scalar() or 0
            
            trend_data.append({
                'date': day.strftime('%m-%d'),
                'total_count': total_count,
                'success_count': success,
                'failed_count': failed
            })
        
        return {
            'total_executions': total_executions,
            'success_count': success_count,
            'failed_count': failed_count,
            'success_rate': round(success_rate, 2),
            'avg_duration': round(avg_duration / 1000, 2) if avg_duration else 0,  # 转换为秒
            'trend_data': trend_data
        }
    
    @staticmethod
    async def export_execution_report(
        db: AsyncSession,
        execution_id: int,
        format: str = 'html'
    ) -> str:
        """导出执行报告"""
        execution_crud = UIExecutionCRUD(db)
        
        execution = await execution_crud.get_by_id_crud(execution_id)
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="执行记录不存在"
            )
        
        if format == 'html':
            return UIReportService._generate_html_report(execution)
        elif format == 'pdf':
            # PDF生成需要额外的库支持
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF导出功能暂未实现"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的导出格式"
            )
    
    @staticmethod
    def _generate_html_report(execution: Any) -> str:
        """生成HTML报告"""
        # 处理截图数据
        screenshots_html = ""
        if execution.screenshots and isinstance(execution.screenshots, list):
            screenshots_html = "<h2>失败截图</h2><div class='screenshots'>"
            for i, screenshot in enumerate(execution.screenshots):
                if isinstance(screenshot, dict):
                    # 格式化时间戳
                    timestamp = screenshot.get('timestamp', '')
                    formatted_timestamp = ''
                    if timestamp:
                        try:
                            from datetime import datetime
                            # 解析ISO格式时间戳
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except:
                            formatted_timestamp = timestamp
                    
                    screenshots_html += f"""
                    <div class="screenshot-item">
                        <h3>步骤 {screenshot.get('step_number', i+1)}: {screenshot.get('step_description', '未知步骤')}</h3>
                        <p class="error-message">{screenshot.get('error_message', '')}</p>
                        <img src="{screenshot.get('screenshot', '')}" alt="失败截图" style="max-width: 100%; border: 1px solid #ddd; margin: 10px 0;">
                        <p class="timestamp">时间: {formatted_timestamp}</p>
                    </div>
                    """
            screenshots_html += "</div>"
        
        # 格式化时间
        start_time = execution.start_time.strftime('%Y-%m-%d %H:%M:%S') if execution.start_time else 'N/A'
        end_time = execution.end_time.strftime('%Y-%m-%d %H:%M:%S') if execution.end_time else 'N/A'
        
        # 计算执行时长
        duration_text = 'N/A'
        if execution.duration:
            duration_seconds = execution.duration / 1000
            if duration_seconds >= 60:
                minutes = int(duration_seconds // 60)
                seconds = int(duration_seconds % 60)
                duration_text = f'{minutes}分{seconds}秒'
            else:
                duration_text = f'{int(duration_seconds)}秒'
        
        # 计算成功率
        success_rate = 0
        if execution.total_steps > 0:
            success_rate = round((execution.passed_steps / execution.total_steps) * 100, 2)
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UI自动化测试执行报告 - {execution.id}</title>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{ 
            background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%); 
            color: white; 
            padding: 25px; 
            text-align: center;
        }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
        .content {{ padding: 25px; }}
        .summary {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 15px; 
            margin-bottom: 25px; 
        }}
        .summary-card {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            border-left: 4px solid;
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        .summary-card h3 {{ margin: 0 0 8px 0; color: #333; font-size: 13px; font-weight: 500; }}
        .summary-card .value {{ font-size: 20px; font-weight: bold; margin-bottom: 5px; }}
        
        /* 状态相关的颜色 */
        .summary-card.status-success {{ border-left-color: #4CAF50; }}
        .summary-card.status-success .value {{ color: #4CAF50; }}
        
        .summary-card.status-failed {{ border-left-color: #f44336; }}
        .summary-card.status-failed .value {{ color: #f44336; }}
        
        .summary-card.status-running {{ border-left-color: #ff9800; }}
        .summary-card.status-running .value {{ color: #ff9800; }}
        
        .summary-card.status-stopped {{ border-left-color: #9e9e9e; }}
        .summary-card.status-stopped .value {{ color: #9e9e9e; }}
        
        /* 其他卡片类型的颜色 */
        .summary-card.engine {{ border-left-color: #2196F3; }}
        .summary-card.engine .value {{ color: #2196F3; }}
        
        .summary-card.browser {{ border-left-color: #9C27B0; }}
        .summary-card.browser .value {{ color: #9C27B0; }}
        
        .summary-card.duration {{ border-left-color: #607D8B; }}
        .summary-card.duration .value {{ color: #607D8B; }}
        
        .summary-card.steps-total {{ border-left-color: #795548; }}
        .summary-card.steps-total .value {{ color: #795548; }}
        
        .summary-card.steps-passed {{ border-left-color: #4CAF50; }}
        .summary-card.steps-passed .value {{ color: #4CAF50; }}
        
        .summary-card.steps-failed {{ border-left-color: #f44336; }}
        .summary-card.steps-failed .value {{ color: #f44336; }}
        
        .summary-card.success-rate {{ border-left-color: #00BCD4; }}
        .summary-card.success-rate .value {{ color: #00BCD4; }}
        
        /* 时间相关的颜色 */
        .summary-card.time-start {{ border-left-color: #FF5722; }}
        .summary-card.time-start .value {{ color: #FF5722; }}
        
        .summary-card.time-end {{ border-left-color: #E91E63; }}
        .summary-card.time-end .value {{ color: #E91E63; }}
        .status-success {{ color: #4CAF50; }}
        .status-failed {{ color: #f44336; }}
        .status-running {{ color: #ff9800; }}
        .status-stopped {{ color: #9e9e9e; }}
        .progress-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s ease;
        }}
        .logs {{ 
            background: #1e1e1e; 
            color: #d4d4d4; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            max-height: 500px;
            overflow-y: auto;
        }}
        .logs pre {{ margin: 0; white-space: pre-wrap; word-wrap: break-word; }}
        .screenshots {{ margin: 20px 0; }}
        .screenshot-item {{
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background: #fafafa;
        }}
        .screenshot-item h3 {{ color: #333; margin: 0 0 10px 0; }}
        .error-message {{ 
            color: #f44336; 
            background: #ffebee; 
            padding: 10px; 
            border-radius: 4px; 
            margin: 10px 0;
            border-left: 4px solid #f44336;
        }}
        .timestamp {{ color: #666; font-size: 12px; margin: 10px 0 0 0; }}
        .section {{ margin: 25px 0; }}
        .section h2 {{ 
            color: #333; 
            border-bottom: 2px solid #34495e; 
            padding-bottom: 8px; 
            margin-bottom: 15px;
            font-size: 18px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
            background: #f8f9fa;
        }}
        @media print {{
            body {{ background: white; }}
            .container {{ box-shadow: none; }}
            .logs {{ max-height: none; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>UI自动化测试执行报告</h1>
            <p>执行ID: {execution.id} | 生成时间: {start_time}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>执行摘要</h2>
                <div class="summary">
                    <div class="summary-card status-{execution.status}">
                        <h3>执行状态</h3>
                        <div class="value">
                            {'成功' if execution.status == 'success' else '失败' if execution.status == 'failed' else '执行中' if execution.status == 'running' else '已停止'}
                        </div>
                    </div>
                    <div class="summary-card engine">
                        <h3>执行引擎</h3>
                        <div class="value">{execution.engine_type}</div>
                    </div>
                    <div class="summary-card browser">
                        <h3>浏览器</h3>
                        <div class="value">{execution.browser_type}</div>
                    </div>
                    <div class="summary-card duration">
                        <h3>执行时长</h3>
                        <div class="value">{duration_text}</div>
                    </div>
                    <div class="summary-card steps-total">
                        <h3>总步骤数</h3>
                        <div class="value">{execution.total_steps}</div>
                    </div>
                    <div class="summary-card steps-passed">
                        <h3>通过步骤</h3>
                        <div class="value">{execution.passed_steps}</div>
                    </div>
                    <div class="summary-card steps-failed">
                        <h3>失败步骤</h3>
                        <div class="value">{execution.failed_steps}</div>
                    </div>
                    <div class="summary-card success-rate">
                        <h3>成功率</h3>
                        <div class="value">{success_rate}%</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: {success_rate}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>执行时间</h2>
                <div class="summary">
                    <div class="summary-card time-start">
                        <h3>开始时间</h3>
                        <div class="value">{start_time}</div>
                    </div>
                    <div class="summary-card time-end">
                        <h3>结束时间</h3>
                        <div class="value">{end_time}</div>
                    </div>
                </div>
            </div>
            
            {f'<div class="section"><h2>错误信息</h2><div class="error-message">{execution.error_message}</div></div>' if execution.error_message else ''}
            
            <div class="section">
                <h2>执行日志</h2>
                <div class="logs">
                    <pre>{execution.logs or '无执行日志'}</pre>
                </div>
            </div>
            
            {screenshots_html}
        </div>
        
        <div class="footer">
            <p>报告生成时间: {start_time} | UI自动化测试平台</p>
        </div>
    </div>
</body>
</html>
"""
        return html


class UIElementValidationService:
    """UI元素验证服务"""
    
    @staticmethod
    async def validate_locator(
        db: AsyncSession,
        url: str,
        locator_strategy: str,
        locator_value: str
    ) -> Dict[str, Any]:
        """验证元素定位器 - 使用Playwright真实验证"""
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        
        result = {
            'is_valid': False,
            'element_count': 0,
            'suggestions': [],
            'message': ''
        }
        
        try:
            async with async_playwright() as p:
                # 启动浏览器（无头模式）
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    # 访问页面
                    await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                    
                    # 根据定位策略构建选择器
                    selector = UIElementValidationService._build_selector(
                        locator_strategy, locator_value
                    )
                    
                    if not selector:
                        result['message'] = f'不支持的定位策略: {locator_strategy}'
                        return result
                    
                    # 查找元素
                    elements = await page.locator(selector).all()
                    element_count = len(elements)
                    
                    if element_count > 0:
                        result['is_valid'] = True
                        result['element_count'] = element_count
                        
                        if element_count == 1:
                            result['message'] = f'定位器验证成功，找到 1 个元素'
                        else:
                            result['message'] = f'定位器验证成功，找到 {element_count} 个元素'
                            result['suggestions'].append({
                                'type': 'warning',
                                'message': f'定位器匹配到 {element_count} 个元素，建议使用更精确的定位器'
                            })
                        
                        # 获取第一个元素的信息
                        first_element = elements[0]
                        try:
                            tag_name = await first_element.evaluate('el => el.tagName.toLowerCase()')
                            result['element_info'] = {
                                'tag_name': tag_name,
                                'is_visible': await first_element.is_visible(),
                                'is_enabled': await first_element.is_enabled()
                            }
                        except:
                            pass
                    else:
                        result['message'] = '定位器验证失败，未找到匹配的元素'
                        
                        # 提供建议
                        result['suggestions'].append({
                            'type': 'error',
                            'message': '请检查定位器是否正确，或页面是否已完全加载'
                        })
                    
                    # 添加定位策略相关的建议
                    if locator_strategy == 'xpath' and locator_value.startswith('//'):
                        result['suggestions'].append({
                            'type': 'info',
                            'message': '使用绝对XPath可能不稳定，建议使用相对XPath或其他定位策略'
                        })
                    
                except PlaywrightTimeoutError:
                    result['message'] = '页面加载超时，请检查URL是否正确'
                except Exception as e:
                    result['message'] = f'验证过程出错: {str(e)}'
                finally:
                    await browser.close()
                    
        except Exception as e:
            result['message'] = f'浏览器启动失败: {str(e)}'
        
        return result
    
    @staticmethod
    def _build_selector(locator_strategy: str, locator_value: str) -> str:
        """根据定位策略构建Playwright选择器"""
        strategy_map = {
            'id': f'#{locator_value}',
            'name': f'[name="{locator_value}"]',
            'class': f'.{locator_value}',
            'css': locator_value,
            'xpath': f'xpath={locator_value}',
            'link_text': f'text="{locator_value}"',
            'partial_link_text': f'text=/{locator_value}/',
            'tag_name': locator_value
        }
        
        return strategy_map.get(locator_strategy, None)
    
    @staticmethod
    async def suggest_locator(
        db: AsyncSession,
        url: str,
        element_html: str
    ) -> List[Dict[str, Any]]:
        """推荐定位策略"""
        # 这里是推荐逻辑的占位符
        # 实际实现需要解析HTML并生成多种定位策略
        
        suggestions = []
        
        # 模拟推荐结果
        # 1. ID定位（优先级最高）
        if 'id=' in element_html:
            suggestions.append({
                'strategy': 'id',
                'value': 'example-id',
                'priority': 1,
                'description': 'ID定位是最稳定的方式'
            })
        
        # 2. CSS选择器
        suggestions.append({
            'strategy': 'css',
            'value': '.example-class',
            'priority': 2,
            'description': 'CSS选择器简洁且性能好'
        })
        
        # 3. XPath
        suggestions.append({
            'strategy': 'xpath',
            'value': '//div[@class="example"]',
            'priority': 3,
            'description': 'XPath功能强大但可能不稳定'
        })
        
        # 4. 文本定位
        suggestions.append({
            'strategy': 'text',
            'value': '按钮文本',
            'priority': 4,
            'description': '文本定位直观但可能受国际化影响'
        })
        
        return suggestions


    
    @staticmethod
    async def generate_test_case_code(
        db: AsyncSession,
        test_case_id: int,
        language: str = 'javascript',
        framework: str = 'playwright'
    ) -> str:
        """生成测试用例代码"""
        from .code_generator import AdvancedCodeGenerator
        
        test_case_crud = UITestCaseCRUD(db)
        test_step_crud = UITestStepCRUD(db)
        element_crud = UIElementCRUD(db)
        
        # 获取测试用例
        test_case = await test_case_crud.get_by_id_crud(test_case_id)
        if not test_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 获取测试步骤
        steps = await test_step_crud.get_by_test_case_id(
            db=db,
            test_case_id=test_case_id
        )
        
        # 获取所有相关元素
        elements_dict = {}
        for step in steps:
            if step.element_id and step.element_id not in elements_dict:
                element = await element_crud.get_by_id_crud(step.element_id)
                if element:
                    elements_dict[step.element_id] = element
        
        # 生成代码
        code = AdvancedCodeGenerator.generate_test_case_code(
            test_case,
            steps,
            elements_dict,
            language,
            framework
        )
        
        return code


    @staticmethod
    async def batch_execute_test_cases(
        db: AsyncSession,
        ui_project_id: int,
        test_case_ids: List[int],
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """批量执行测试用例"""
        from datetime import datetime
        import asyncio
        
        if not test_case_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试用例ID列表不能为空"
            )
        
        test_case_crud = UITestCaseCRUD(db)
        execution_crud = UIExecutionCRUD(db)
        
        # 验证所有测试用例是否存在
        test_cases = []
        for test_case_id in test_case_ids:
            test_case = await test_case_crud.get_by_id_crud(test_case_id)
            if not test_case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"测试用例 {test_case_id} 不存在"
                )
            test_cases.append(test_case)
        
        # 创建一个临时执行记录（用于批量执行）
        execution_data = {
            'ui_project_id': ui_project_id,
            'suite_id': None,
            'test_case_id': None,  # 批量执行不关联单个用例
            'engine_type': config.get('engine_type', 'playwright'),
            'browser_type': config.get('browser_type', 'chromium'),
            'status': 'running',
            'start_time': datetime.now(),
            'total_steps': 0,
            'passed_steps': 0,
            'failed_steps': 0,
            'executed_by': user_id
        }
        
        execution = await execution_crud.create_crud(data=execution_data)
        await db.commit()
        
        # 根据引擎类型选择执行方式
        engine_type = config.get('engine_type', 'playwright')
        
        if engine_type == 'selenium':
            # Selenium 使用线程方式执行
            import threading
            
            def run_in_thread():
                """在独立线程中运行批量测试用例"""
                UIExecutionService._run_batch_test_cases_sync(
                    execution.id, test_cases, config
                )
            
            thread = threading.Thread(target=run_in_thread, daemon=True)
            thread.start()
        else:
            # Playwright 使用异步方式执行
            asyncio.create_task(
                UIExecutionService._run_batch_test_cases_async(
                    execution.id, test_cases, config
                )
            )
        
        return {
            'execution_id': execution.id,
            'status': 'running',
            'message': f'开始批量执行 {len(test_case_ids)} 个测试用例'
        }
    
    @staticmethod
    async def _run_batch_test_cases_async(
        execution_id: int,
        test_cases: List[Any],
        config: Dict[str, Any]
    ):
        """运行批量测试用例（Playwright异步方式）"""
        import time
        from datetime import datetime
        from app.db.sqlalchemy import async_session
        from .execution_engine import ExecutionManager
        
        start_time = time.time()
        
        async with async_session() as db:
            try:
                test_step_crud = UITestStepCRUD(db)
                execution_crud = UIExecutionCRUD(db)
                
                # 创建执行引擎
                engine = ExecutionManager.create_execution(execution_id, db)
                
                total_steps = 0
                passed_steps = 0
                failed_steps = 0
                all_logs = []
                total_duration = 0
                
                # 执行每个测试用例
                for test_case in test_cases:
                    # 获取测试步骤
                    steps = await test_step_crud.get_by_test_case_id(
                        db=db,
                        test_case_id=test_case.id
                    )
                    
                    # 执行测试用例
                    result = await engine.execute_test_case(test_case, steps, config)
                    
                    total_steps += result['total_steps']
                    passed_steps += result['passed_steps']
                    failed_steps += result['failed_steps']
                    total_duration += result.get('duration', 0)
                    all_logs.append(result['logs'])
                    
                    if engine.is_stopped:
                        break
                
                # 计算总执行时长
                if total_duration == 0:
                    total_duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录
                final_status = 'stopped' if engine.is_stopped else ('success' if failed_steps == 0 else 'failed')
                await execution_crud.update_crud(execution_id, {
                    'status': final_status,
                    'end_time': datetime.now(),
                    'total_steps': total_steps,
                    'passed_steps': passed_steps,
                    'failed_steps': failed_steps,
                    'duration': total_duration,
                    'logs': '\n\n'.join(all_logs)
                })
                
                await db.commit()
                
            except Exception as e:
                await db.rollback()
                duration = int((time.time() - start_time) * 1000)
                
                try:
                    await execution_crud.update_crud(execution_id, {
                        'status': 'failed',
                        'end_time': datetime.now(),
                        'duration': duration,
                        'error_message': str(e),
                        'logs': f"执行异常: {str(e)}"
                    })
                    await db.commit()
                except:
                    pass
            finally:
                ExecutionManager.remove_execution(execution_id)
    
    @staticmethod
    def _run_batch_test_cases_sync(
        execution_id: int,
        test_cases: List[Any],
        config: Dict[str, Any]
    ):
        """运行批量测试用例（Selenium同步方式）"""
        import time
        from datetime import datetime
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import sessionmaker
        from config import Configs
        from .model import UIExecutionModel, UITestStepModel, UIElementModel, UIProjectModel
        from .selenium_execution_wrapper import SeleniumExecutionEngine
        
        logger.info(f"线程启动: 批量执行ID={execution_id}, 用例数量={len(test_cases)}")
        
        start_time = time.time()
        
        try:
            sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
            SyncSession = sessionmaker(bind=sync_engine)
            sync_db = SyncSession()
            
            try:
                # 获取 UI 项目的 base_url
                ui_project = sync_db.query(UIProjectModel).filter(
                    UIProjectModel.id == test_cases[0].ui_project_id
                ).first()
                
                base_url = ui_project.base_url if ui_project else None
                
                # 创建 Selenium 执行引擎
                selenium_engine = SeleniumExecutionEngine()
                
                total_steps = 0
                passed_steps = 0
                failed_steps = 0
                all_logs = []
                
                # 执行每个测试用例
                for test_case in test_cases:
                    # 获取测试步骤
                    steps = sync_db.query(UITestStepModel).filter(
                        UITestStepModel.test_case_id == test_case.id
                    ).order_by(UITestStepModel.step_number).all()
                    
                    # 准备测试用例数据
                    test_case_data = {
                        'id': test_case.id,
                        'name': test_case.name,
                        'ui_project_id': test_case.ui_project_id,
                        'base_url': base_url
                    }
                    
                    # 准备测试步骤数据
                    steps_data = []
                    for step in steps:
                        step_dict = {
                            'id': step.id,
                            'step_number': step.step_number,
                            'action_type': step.action_type,
                            'action_value': step.action_value,
                            'description': step.description,
                            'assertion_type': step.assertion_type,
                            'assertion_value': step.assertion_value,
                            'element': None
                        }
                        
                        if step.element_id:
                            element = sync_db.query(UIElementModel).filter(
                                UIElementModel.id == step.element_id
                            ).first()
                            
                            if element:
                                step_dict['element'] = {
                                    'id': element.id,
                                    'name': element.name,
                                    'locator_strategy': element.locator_strategy,
                                    'locator_value': element.locator_value,
                                    'wait_timeout': getattr(element, 'wait_timeout', None) or 5.0,
                                    'force_action': getattr(element, 'force_action', False)
                                }
                        
                        steps_data.append(step_dict)
                    
                    # 执行测试用例
                    logger.info(f"开始执行测试用例: {test_case.name}")
                    result = selenium_engine.execute_test_case(test_case_data, steps_data, config)
                    logger.info(f"测试用例执行完成: status={result['status']}")
                    
                    total_steps += result['total_steps']
                    passed_steps += result['passed_steps']
                    failed_steps += result['failed_steps']
                    all_logs.append(f"\n{'='*80}\n测试用例: {test_case.name}\n{'='*80}\n{result['logs']}")
                
                # 计算总执行时长
                duration = int((time.time() - start_time) * 1000)
                
                # 更新执行记录
                final_status = 'success' if failed_steps == 0 else 'failed'
                stmt = update(UIExecutionModel).where(
                    UIExecutionModel.id == execution_id
                ).values(
                    status=final_status,
                    end_time=datetime.now(),
                    total_steps=total_steps,
                    passed_steps=passed_steps,
                    failed_steps=failed_steps,
                    duration=duration,
                    logs='\n\n'.join(all_logs)
                )
                
                sync_db.execute(stmt)
                sync_db.commit()
                logger.info(f"批量执行记录已更新: execution_id={execution_id}, duration={duration}ms")
                
            finally:
                sync_db.close()
                sync_engine.dispose()
                
        except Exception as e:
            logger.error(f"批量执行失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            duration = int((time.time() - start_time) * 1000)
            
            try:
                sync_engine = create_engine(Configs().DATABASE_URI_SYNC)
                SyncSession = sessionmaker(bind=sync_engine)
                sync_db = SyncSession()
                
                stmt = update(UIExecutionModel).where(
                    UIExecutionModel.id == execution_id
                ).values(
                    status='failed',
                    end_time=datetime.now(),
                    duration=duration,
                    error_message=str(e),
                    logs=f"执行异常: {str(e)}\n\n{traceback.format_exc()}"
                )
                sync_db.execute(stmt)
                sync_db.commit()
                sync_db.close()
                sync_engine.dispose()
            except Exception as db_error:
                logger.error(f"更新失败状态失败: {str(db_error)}")
    
    @staticmethod
    async def batch_execute_test_suites(
        db: AsyncSession,
        suite_ids: List[int],
        config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """批量执行测试套件"""
        if not suite_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="测试套件ID列表不能为空"
            )
        
        test_suite_crud = UITestSuiteCRUD(db)
        
        # 验证所有测试套件是否存在
        for suite_id in suite_ids:
            test_suite = await test_suite_crud.get_by_id_crud(suite_id)
            if not test_suite:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"测试套件 {suite_id} 不存在"
                )
        
        # 为每个测试套件创建执行任务
        execution_ids = []
        for suite_id in suite_ids:
            result = await UIExecutionService.execute_test_suite(
                db, suite_id, config, user_id
            )
            execution_ids.append(result['execution_id'])
        
        return {
            'execution_ids': execution_ids,
            'status': 'running',
            'message': f'开始批量执行 {len(suite_ids)} 个测试套件'
        }
