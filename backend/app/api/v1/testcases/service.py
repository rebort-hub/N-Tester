"""
测试用例管理业务逻辑层
"""

from typing import List
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.testcases.crud import (
    TestCaseCRUD, TestCaseStepCRUD, VersionCRUD,
    ProjectVersionCRUD, TestCaseVersionCRUD, ModuleInfoCRUD
)
from app.api.v1.testcases.schema import (
    TestCaseCreateSchema, TestCaseUpdateSchema, TestCaseOutSchema, TestCaseQuerySchema,
    TestCaseStepOutSchema, VersionCreateSchema, VersionUpdateSchema, VersionOutSchema,
    VersionQuerySchema, VersionAssociationSchema,
    ModuleInfoCreateSchema, ModuleInfoUpdateSchema, ModuleInfoOutSchema, ModuleInfoQuerySchema
)
from app.api.v1.testcases.model import TestCaseModel, VersionModel, ModuleInfoModel
from app.api.v1.projects.crud import ProjectMemberCRUD
from app.common.response import page_response


class TestCaseService:
    """测试用例服务"""
    
    @classmethod
    async def create_testcase_service(
        cls,
        project_id: int,
        data: TestCaseCreateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> TestCaseOutSchema:
        """创建测试用例"""
        # 检查项目权限
        await cls._check_project_member(project_id, current_user_id, db)
        
        crud = TestCaseCRUD(db)
        
        # 创建测试用例
        testcase_data = data.model_dump(exclude={"steps"})
        testcase_data["project_id"] = project_id
        testcase_data["author_id"] = current_user_id
        testcase_data["created_by"] = current_user_id
        testcase = await crud.create_crud(testcase_data)
        
        # 创建测试步骤
        if data.steps:
            print(f"[DEBUG] 创建步骤，数量: {len(data.steps)}")
            step_crud = TestCaseStepCRUD(db)
            for i, step_data in enumerate(data.steps):
                step_dict = step_data.model_dump()
                print(f"[DEBUG] 步骤{i+1}: {step_dict}")
                step_dict["test_case_id"] = testcase.id
                step_dict["created_by"] = current_user_id
                created_step = await step_crud.create_crud(step_dict)
                print(f"[DEBUG] 创建成功，步骤ID: {created_step.id}")
        else:
            print("[DEBUG] 没有步骤数据")
        
        # 重新获取测试用例（包含关联数据）
        testcase = await crud.get_with_relations_crud(testcase.id)
        
        return cls._build_testcase_out(testcase)
    
    @classmethod
    async def get_testcase_list_service(
        cls,
        query: TestCaseQuerySchema,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """获取测试用例列表"""
        # 检查项目权限
        await cls._check_project_member(query.project_id, current_user_id, db)
        
        crud = TestCaseCRUD(db)
        
        # 构建查询条件
        conditions = []
        if query.title:
            conditions.append(TestCaseModel.title.like(f"%{query.title}%"))
        if query.status:
            conditions.append(TestCaseModel.status == query.status)
        if query.priority:
            conditions.append(TestCaseModel.priority == query.priority)
        if query.test_type:
            conditions.append(TestCaseModel.test_type == query.test_type)
        if query.author_id:
            conditions.append(TestCaseModel.author_id == query.author_id)
        if query.module_id:
            conditions.append(TestCaseModel.module_id == query.module_id)
        
        # 如果指定了版本，需要关联查询
        if query.version_id:
            # TODO: 实现版本过滤
            pass
        
        # 查询测试用例
        skip = (query.page - 1) * query.page_size
        testcases, total = await crud.get_project_testcases_crud(
            query.project_id,
            conditions,
            skip,
            query.page_size
        )
        
        # 构建输出
        items = [cls._build_testcase_out(tc).model_dump() for tc in testcases]
        
        # 直接返回数据字典，不使用page_response
        return {
            "items": items,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size
        }
    
    @classmethod
    async def get_testcase_detail_service(
        cls,
        testcase_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> TestCaseOutSchema:
        """获取测试用例详情"""
        crud = TestCaseCRUD(db)
        testcase = await crud.get_with_relations_crud(testcase_id)
        
        if not testcase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 检查项目权限
        await cls._check_project_member(testcase.project_id, current_user_id, db)
        
        return cls._build_testcase_out(testcase)
    
    @classmethod
    async def update_testcase_service(
        cls,
        testcase_id: int,
        data: TestCaseUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> TestCaseOutSchema:
        """更新测试用例"""
        crud = TestCaseCRUD(db)
        testcase = await crud.get_by_id_crud(testcase_id)
        
        if not testcase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 检查项目权限
        await cls._check_project_member(testcase.project_id, current_user_id, db)
        
        # 更新测试用例
        update_data = data.model_dump(exclude_unset=True, exclude={"steps"})
        update_data["updated_by"] = current_user_id
        testcase = await crud.update_crud(testcase_id, update_data)
        
        # 更新测试步骤
        if data.steps is not None:
            step_crud = TestCaseStepCRUD(db)
            # 删除旧步骤
            await step_crud.delete_testcase_steps_crud(testcase_id)
            # 创建新步骤
            for step_data in data.steps:
                step_dict = step_data.model_dump()
                step_dict["test_case_id"] = testcase_id
                step_dict["created_by"] = current_user_id
                await step_crud.create_crud(step_dict)
        
        # 重新获取测试用例（包含关联数据）
        testcase = await crud.get_with_relations_crud(testcase.id)
        
        return cls._build_testcase_out(testcase)
    
    @classmethod
    async def delete_testcase_service(
        cls,
        testcase_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """删除测试用例"""
        crud = TestCaseCRUD(db)
        testcase = await crud.get_by_id_crud(testcase_id)
        
        if not testcase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="测试用例不存在"
            )
        
        # 检查项目权限
        await cls._check_project_member(testcase.project_id, current_user_id, db)
        
        await crud.delete_crud([testcase_id])
    
    @classmethod
    def _build_testcase_out(cls, testcase: TestCaseModel) -> TestCaseOutSchema:
        """构建测试用例输出"""
        print(f"[DEBUG] _build_testcase_out - testcase.id: {testcase.id}")
        print(f"[DEBUG] testcase.steps 类型: {type(testcase.steps)}")
        print(f"[DEBUG] testcase.steps 长度: {len(testcase.steps) if testcase.steps else 0}")
        if testcase.steps:
            print(f"[DEBUG] testcase.steps 内容: {testcase.steps}")
        
        # 处理空标题的情况
        if not testcase.title or testcase.title.strip() == '':
            testcase.title = '未命名用例'
        
        testcase_out = TestCaseOutSchema.model_validate(testcase)
        
        print(f"[DEBUG] testcase_out.steps 长度: {len(testcase_out.steps) if testcase_out.steps else 0}")
        
        # 设置作者和指派人姓名
        if testcase.author:
            testcase_out.author_name = testcase.author.nickname or testcase.author.username
        if testcase.assignee:
            testcase_out.assignee_name = testcase.assignee.nickname or testcase.assignee.username
        
        # 设置模块名称
        if testcase.module:
            testcase_out.module_name = testcase.module.name
        
        # 设置步骤
        if testcase.steps:
            print(f"[DEBUG] 手动设置 steps，数量: {len(testcase.steps)}")
            testcase_out.steps = [TestCaseStepOutSchema.model_validate(step) for step in testcase.steps]
            print(f"[DEBUG] 设置后 testcase_out.steps 长度: {len(testcase_out.steps)}")
        
        # 设置版本ID列表
        if testcase.versions:
            testcase_out.version_ids = [v.version_id for v in testcase.versions]
        
        print(f"[DEBUG] 最终返回的 testcase_out.steps: {testcase_out.steps}")
        return testcase_out
    
    @classmethod
    async def _check_project_member(
        cls,
        project_id: int,
        user_id: int,
        db: AsyncSession
    ) -> None:
        """检查用户是否是项目成员"""
        member_crud = ProjectMemberCRUD(db)
        is_member = await member_crud.check_user_in_project_crud(project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您不是该项目成员，无权访问"
            )


class VersionService:
    """版本服务"""
    
    @classmethod
    async def create_version_service(
        cls,
        data: VersionCreateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> VersionOutSchema:
        """创建版本"""
        crud = VersionCRUD(db)
        
        # 检查版本名称是否已存在
        existing = await crud.get_by_name_crud(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="版本名称已存在"
            )
        
        # 创建版本
        version_data = data.model_dump(exclude={"project_ids"})
        version_data["created_by"] = current_user_id
        version = await crud.create_crud(version_data)
        
        # 关联项目
        if data.project_ids:
            pv_crud = ProjectVersionCRUD(db)
            for project_id in data.project_ids:
                await pv_crud.create_crud({
                    "project_id": project_id,
                    "version_id": version.id,
                    "created_by": current_user_id
                })
        
        # 重新获取版本（包含关联数据）
        version = await crud.get_with_relations_crud(version.id)
        
        return cls._build_version_out(version)
    
    @classmethod
    async def get_version_list_service(
        cls,
        query: VersionQuerySchema,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """获取版本列表"""
        crud = VersionCRUD(db)
        
        # 构建查询条件
        conditions = []
        if query.name:
            conditions.append(VersionModel.name.like(f"%{query.name}%"))
        if query.is_baseline is not None:
            conditions.append(VersionModel.is_baseline == query.is_baseline)
        
        # TODO: 如果指定了项目，需要关联查询
        
        # 查询版本
        skip = (query.page - 1) * query.page_size
        versions, total = await crud.get_versions_crud(
            conditions,
            skip,
            query.page_size
        )
        
        # 构建输出
        items = [cls._build_version_out(v).model_dump() for v in versions]
        
        # 直接返回数据字典，不使用page_response
        return {
            "items": items,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size
        }
    
    @classmethod
    async def get_version_detail_service(
        cls,
        version_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> VersionOutSchema:
        """获取版本详情"""
        crud = VersionCRUD(db)
        version = await crud.get_with_relations_crud(version_id)
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="版本不存在"
            )
        
        return cls._build_version_out(version)
    
    @classmethod
    async def update_version_service(
        cls,
        version_id: int,
        data: VersionUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> VersionOutSchema:
        """更新版本"""
        crud = VersionCRUD(db)
        version = await crud.get_by_id_crud(version_id)
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="版本不存在"
            )
        
        # 更新版本
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = current_user_id
        version = await crud.update_crud(version_id, update_data)
        
        # 重新获取版本（包含关联数据）
        version = await crud.get_with_relations_crud(version.id)
        
        return cls._build_version_out(version)
    
    @classmethod
    async def delete_version_service(
        cls,
        version_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """删除版本"""
        crud = VersionCRUD(db)
        await crud.delete_crud([version_id])
    
    @classmethod
    async def associate_testcases_service(
        cls,
        data: VersionAssociationSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """关联测试用例到版本"""
        # 检查版本是否存在
        version_crud = VersionCRUD(db)
        version = await version_crud.get_by_id_crud(data.version_id)
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="版本不存在"
            )
        
        # 删除旧关联
        tcv_crud = TestCaseVersionCRUD(db)
        await tcv_crud.delete_version_testcases_crud(data.version_id)
        
        # 创建新关联
        for testcase_id in data.testcase_ids:
            await tcv_crud.create_crud({
                "test_case_id": testcase_id,
                "version_id": data.version_id,
                "created_by": current_user_id
            })
    
    @classmethod
    def _build_version_out(cls, version: VersionModel) -> VersionOutSchema:
        """构建版本输出"""
        version_out = VersionOutSchema.model_validate(version)
        
        # 设置项目数量和用例数量
        if version.projects:
            version_out.project_count = len(version.projects)
        if version.test_cases:
            version_out.testcase_count = len(version.test_cases)
        
        return version_out



class ModuleInfoService:
    """模块管理服务"""
    
    @classmethod
    async def create_module_service(
        cls,
        data: ModuleInfoCreateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ModuleInfoOutSchema:
        """创建模块"""
        # 检查项目权限
        await TestCaseService._check_project_member(data.project_id, current_user_id, db)
        
        crud = ModuleInfoCRUD(db)
        
        # 检查模块名称是否已存在
        existing = await crud.get_by_name_crud(data.project_id, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="模块名称已存在"
            )
        
        # 创建模块
        module_data = data.model_dump()
        module_data["created_by"] = current_user_id
        module_data["enabled_flag"] = 1
        module = await crud.create_crud(module_data)
        
        # 刷新对象以确保与会话绑定
        await db.refresh(module)
        
        return cls._build_module_out(module)
    
    @classmethod
    async def get_module_list_service(
        cls,
        query: ModuleInfoQuerySchema,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """获取模块列表"""
        # 检查项目权限
        await TestCaseService._check_project_member(query.project_id, current_user_id, db)
        
        crud = ModuleInfoCRUD(db)
        
        # 获取模块列表（包含用例数量）
        modules = await crud.get_with_testcase_count_crud(query.project_id)
        
        # 如果有名称过滤
        if query.name:
            modules = [m for m in modules if query.name in m['name']]
        
        # 分页
        total = len(modules)
        skip = (query.page - 1) * query.page_size
        items = modules[skip:skip + query.page_size]
        
        # 构建输出
        module_list = [ModuleInfoOutSchema(**m) for m in items]
        
        return {
            "items": [m.model_dump() for m in module_list],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size
        }
    
    @classmethod
    async def get_module_detail_service(
        cls,
        module_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> ModuleInfoOutSchema:
        """获取模块详情"""
        crud = ModuleInfoCRUD(db)
        module = await crud.get_by_id_crud(module_id)
        
        if not module or module.enabled_flag != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模块不存在"
            )
        
        # 检查项目权限
        await TestCaseService._check_project_member(module.project_id, current_user_id, db)
        
        return cls._build_module_out(module)
    
    @classmethod
    @classmethod
    async def update_module_service(
        cls,
        module_id: int,
        data: ModuleInfoUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ModuleInfoOutSchema:
        """更新模块"""
        crud = ModuleInfoCRUD(db)
        module = await crud.get_by_id_crud(module_id)
        
        if not module or module.enabled_flag != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模块不存在"
            )
        
        # 检查项目权限
        await TestCaseService._check_project_member(module.project_id, current_user_id, db)
        
        # 如果更新名称，检查是否重复
        if data.name and data.name != module.name:
            existing = await crud.get_by_name_crud(module.project_id, data.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="模块名称已存在"
                )
        
        # 更新模块
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = current_user_id
        module = await crud.update_crud(module_id, update_data)
        
        # 刷新对象以确保与会话绑定
        await db.refresh(module)
        
        return cls._build_module_out(module)
    
    @classmethod
    async def delete_module_service(
        cls,
        module_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """删除模块（软删除）"""
        crud = ModuleInfoCRUD(db)
        module = await crud.get_by_id_crud(module_id)
        
        if not module or module.enabled_flag != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模块不存在"
            )
        
        # 检查项目权限
        await TestCaseService._check_project_member(module.project_id, current_user_id, db)
        
        # 检查是否有关联的测试用例
        from sqlalchemy import select, func
        stmt = select(func.count()).select_from(TestCaseModel).where(
            TestCaseModel.module_id == module_id,
            TestCaseModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        count = result.scalar()
        
        if count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该模块下还有 {count} 个测试用例，无法删除"
            )
        
        # 软删除
        await crud.soft_delete_crud([module_id])
    
    @classmethod
    def _build_module_out(cls, module: ModuleInfoModel, testcase_count: int = 0) -> ModuleInfoOutSchema:
        """构建模块输出"""
        # 手动构建输出，避免触发延迟加载
        module_dict = {
            'id': module.id,
            'name': module.name,
            'project_id': module.project_id,
            'parent_id': module.parent_id,
            'description': module.description,
            'sort_order': module.sort_order,
            'testcase_count': testcase_count,
            'creation_date': module.creation_date,
            'created_by': module.created_by,
            'updation_date': module.updation_date,
            'updated_by': module.updated_by,
            'enabled_flag': module.enabled_flag,
        }
        return ModuleInfoOutSchema(**module_dict)
    
    @classmethod
    async def get_module_tree_service(
        cls,
        project_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> List[dict]:
        """获取模块树形结构"""
        # 检查项目权限
        await TestCaseService._check_project_member(project_id, current_user_id, db)
        
        crud = ModuleInfoCRUD(db)
        
        # 获取所有模块（包含用例数量）
        modules = await crud.get_with_testcase_count_crud(project_id)
        
        # 构建树形结构
        return cls._build_tree(modules)
    
    @classmethod
    def _build_tree(cls, modules: List[dict], parent_id: int = None, level: int = 0) -> List[dict]:
        """递归构建树形结构"""
        tree = []
        for module in modules:
            if module.get('parent_id') == parent_id:
                node = {
                    'id': module['id'],
                    'name': module['name'],
                    'project_id': module['project_id'],
                    'parent_id': module.get('parent_id'),
                    'description': module.get('description'),
                    'sort_order': module.get('sort_order', 0),
                    'testcase_count': module.get('testcase_count', 0),
                    'level': level,
                    'children': cls._build_tree(modules, module['id'], level + 1)
                }
                tree.append(node)
        
        # 按sort_order排序
        tree.sort(key=lambda x: x['sort_order'])
        return tree
    
    @classmethod
    async def move_module_service(
        cls,
        module_id: int,
        target_parent_id: int | None,
        current_user_id: int,
        db: AsyncSession
    ) -> ModuleInfoOutSchema:
        """移动模块到新的父模块下"""
        crud = ModuleInfoCRUD(db)
        module = await crud.get_by_id_crud(module_id)
        
        if not module or module.enabled_flag != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="模块不存在"
            )
        
        # 检查项目权限
        await TestCaseService._check_project_member(module.project_id, current_user_id, db)
        
        # 检查目标父模块是否存在且属于同一项目
        if target_parent_id:
            target_parent = await crud.get_by_id_crud(target_parent_id)
            if not target_parent or target_parent.enabled_flag != 1:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="目标父模块不存在"
                )
            if target_parent.project_id != module.project_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能移动到其他项目的模块下"
                )
            
            # 检查是否会形成循环引用
            if await cls._would_create_cycle(module_id, target_parent_id, crud):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="不能移动到自己的子模块下"
                )
        
        # 更新父模块
        update_data = {
            "parent_id": target_parent_id,
            "updated_by": current_user_id
        }
        module = await crud.update_crud(module_id, update_data)
        
        return cls._build_module_out(module)
    
    @classmethod
    async def _would_create_cycle(cls, module_id: int, target_parent_id: int, crud: ModuleInfoCRUD) -> bool:
        """检查是否会形成循环引用"""
        current_id = target_parent_id
        while current_id:
            if current_id == module_id:
                return True
            parent = await crud.get_by_id_crud(current_id)
            if not parent:
                break
            current_id = parent.parent_id
        return False
    
    @classmethod
    async def export_modules_service(
        cls,
        project_id: int,
        module_ids: List[int] | None,
        include_testcases: bool,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """导出模块"""
        # 检查项目权限
        await TestCaseService._check_project_member(project_id, current_user_id, db)
        
        crud = ModuleInfoCRUD(db)
        
        # 获取要导出的模块
        if module_ids:
            modules = []
            for module_id in module_ids:
                module = await crud.get_by_id_crud(module_id)
                if module and module.enabled_flag == 1 and module.project_id == project_id:
                    modules.append(module)
        else:
            # 导出所有模块 - 直接使用 ORM 查询而不是字典
            modules = await crud.get_by_project_crud(project_id)
        
        # 构建导出数据
        export_data = {
            "version": "1.0",
            "project_id": project_id,
            "export_time": datetime.now().isoformat(),
            "modules": []
        }
        
        for module in modules:
            module_data = {
                "name": module.name,
                "description": module.description,
                "parent_id": module.parent_id,
                "sort_order": module.sort_order,
            }
            
            # 如果包含测试用例
            if include_testcases:
                from sqlalchemy import select
                stmt = select(TestCaseModel).where(
                    TestCaseModel.module_id == module.id,
                    TestCaseModel.enabled_flag == 1
                )
                result = await db.execute(stmt)
                testcases = result.scalars().all()
                
                module_data["testcases"] = [
                    {
                        "title": tc.title,
                        "description": tc.description,
                        "preconditions": tc.preconditions,
                        "expected_result": tc.expected_result,
                        "priority": tc.priority,
                        "test_type": tc.test_type,
                        "tags": tc.tags
                    }
                    for tc in testcases
                ]
            
            export_data["modules"].append(module_data)
        
        return export_data
    
    @classmethod
    async def import_modules_service(
        cls,
        project_id: int,
        modules_data: List[dict],
        override: bool,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """导入模块"""
        # 检查项目权限
        await TestCaseService._check_project_member(project_id, current_user_id, db)
        
        crud = ModuleInfoCRUD(db)
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        errors = []
        
        # ID映射表（用于处理父子关系）
        id_mapping = {}
        
        for module_data in modules_data:
            try:
                module_name = module_data.get("name")
                if not module_name:
                    error_count += 1
                    errors.append("模块名称不能为空")
                    continue
                
                # 检查是否已存在
                existing = await crud.get_by_name_crud(project_id, module_name)
                
                if existing and not override:
                    skipped_count += 1
                    continue
                
                # 处理父模块ID映射
                old_parent_id = module_data.get("parent_id")
                new_parent_id = id_mapping.get(old_parent_id) if old_parent_id else None
                
                # 准备数据
                create_data = {
                    "name": module_name,
                    "description": module_data.get("description"),
                    "project_id": project_id,
                    "parent_id": new_parent_id,
                    "sort_order": module_data.get("sort_order", 0),
                    "created_by": current_user_id,
                    "enabled_flag": 1
                }
                
                if existing and override:
                    # 更新现有模块
                    update_data = {k: v for k, v in create_data.items() if k not in ["project_id", "created_by"]}
                    update_data["updated_by"] = current_user_id
                    module = await crud.update_crud(existing.id, update_data)
                    id_mapping[old_parent_id] = module.id if old_parent_id else None
                else:
                    # 创建新模块
                    module = await crud.create_crud(create_data)
                    id_mapping[module_data.get("id")] = module.id
                
                # 如果包含测试用例数据
                if "testcases" in module_data:
                    testcase_crud = TestCaseCRUD(db)
                    for tc_data in module_data["testcases"]:
                        tc_create_data = {
                            **tc_data,
                            "project_id": project_id,
                            "module_id": module.id,
                            "author_id": current_user_id,
                            "created_by": current_user_id,
                            "enabled_flag": 1
                        }
                        await testcase_crud.create_crud(tc_create_data)
                
                imported_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"导入模块 '{module_data.get('name', 'unknown')}' 失败: {str(e)}")
        
        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "error_count": error_count,
            "errors": errors
        }
