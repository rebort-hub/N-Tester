"""
项目管理业务逻辑层
"""

from typing import List
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.api.v1.projects.crud import ProjectCRUD, ProjectMemberCRUD, ProjectEnvironmentCRUD
from app.api.v1.projects.schema import (
    ProjectCreateSchema, ProjectUpdateSchema, ProjectOutSchema, ProjectQuerySchema,
    ProjectMemberCreateSchema, ProjectMemberUpdateSchema, ProjectMemberOutSchema,
    ProjectEnvironmentCreateSchema, ProjectEnvironmentUpdateSchema, ProjectEnvironmentOutSchema
)
from app.api.v1.projects.model import ProjectModel, ProjectMemberModel, ProjectEnvironmentModel
from app.common.response import page_response


class ProjectService:
    """项目服务"""
    
    @classmethod
    async def create_project_service(
        cls,
        data: ProjectCreateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectOutSchema:
        """创建项目"""
        crud = ProjectCRUD(db)
        
        # 检查项目名称是否已存在
        existing = await crud.get_by_name_crud(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="项目名称已存在"
            )
        
        # 创建项目
        project_data = data.model_dump()
        project_data["owner_id"] = current_user_id
        project_data["created_by"] = current_user_id
        project = await crud.create_crud(project_data)
        
        # 自动添加创建者为项目成员（owner角色）
        member_crud = ProjectMemberCRUD(db)
        await member_crud.create_crud({
            "project_id": project.id,
            "user_id": current_user_id,
            "role": "owner",
            "created_by": current_user_id
        })
        
        # 重新获取项目（包含关联数据）
        project = await crud.get_with_relations_crud(project.id)
        
        # 构建输出
        project_out = ProjectOutSchema.model_validate(project)
        project_out.member_count = len(project.members)
        project_out.environment_count = len(project.environments)
        
        return project_out
    
    @classmethod
    async def get_project_list_service(
        cls,
        query: ProjectQuerySchema,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """获取项目列表"""
        crud = ProjectCRUD(db)
        
        # 构建查询条件
        conditions = []
        if query.name:
            conditions.append(ProjectModel.name.like(f"%{query.name}%"))
        if query.status:
            conditions.append(ProjectModel.status == query.status)
        
        # 查询用户参与的项目
        skip = (query.page - 1) * query.page_size
        projects, total = await crud.get_user_projects_crud(
            current_user_id,
            conditions,
            skip,
            query.page_size
        )
        
        # 构建输出
        items = []
        for project in projects:
            project_out = ProjectOutSchema.model_validate(project)
            project_out.member_count = len(project.members)
            project_out.environment_count = len(project.environments)
            items.append(project_out.model_dump())
        
        return page_response(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
    
    @classmethod
    async def get_project_detail_service(
        cls,
        project_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectOutSchema:
        """获取项目详情"""
        # 检查权限
        await cls._check_project_member(project_id, current_user_id, db)
        
        crud = ProjectCRUD(db)
        project = await crud.get_with_relations_crud(project_id)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 构建输出
        project_out = ProjectOutSchema.model_validate(project)
        project_out.member_count = len(project.members)
        project_out.environment_count = len(project.environments)
        
        # 获取项目负责人姓名
        if project.owner:
            project_out.owner_name = project.owner.nickname or project.owner.username
        
        return project_out
    
    @classmethod
    async def update_project_service(
        cls,
        project_id: int,
        data: ProjectUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectOutSchema:
        """更新项目"""
        # 检查权限（只有owner和admin可以更新）
        await cls._check_project_permission(project_id, current_user_id, ["owner", "admin"], db)
        
        crud = ProjectCRUD(db)
        
        # 更新项目
        update_data = data.model_dump(exclude_unset=True)
        update_data["id"] = project_id
        update_data["updated_by"] = current_user_id
        project = await crud.update_crud(project_id, update_data)
        
        # 重新获取项目（包含关联数据）
        project = await crud.get_with_relations_crud(project.id)
        
        # 构建输出
        project_out = ProjectOutSchema.model_validate(project)
        project_out.member_count = len(project.members) if project.members else 0
        project_out.environment_count = len(project.environments) if project.environments else 0
        
        return project_out
    
    @classmethod
    async def delete_project_service(
        cls,
        project_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """删除项目"""
        # 检查权限（只有owner可以删除）
        await cls._check_project_permission(project_id, current_user_id, ["owner"], db)
        
        # 获取项目信息
        crud = ProjectCRUD(db)
        project = await crud.get_by_id_crud(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )
        
        # 检查项目成员
        from .crud import ProjectMemberCRUD
        member_crud = ProjectMemberCRUD(db)
        from .model import ProjectMemberModel
        
        # 获取所有项目成员
        stmt = select(ProjectMemberModel).where(
            ProjectMemberModel.project_id == project_id,
            ProjectMemberModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        members = result.scalars().all()
        
        # 如果有成员，检查是否只有项目负责人一个成员
        if members:
            if len(members) > 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"项目还有 {len(members)} 个成员，请先移除其他成员后再删除项目"
                )
            elif len(members) == 1:
                # 检查唯一的成员是否是项目负责人
                only_member = members[0]
                if only_member.user_id != project.owner_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="项目还有其他成员，请先移除后再删除项目"
                    )
        
        # 检查项目是否有环境
        from .crud import ProjectEnvironmentCRUD
        env_crud = ProjectEnvironmentCRUD(db)
        from .model import ProjectEnvironmentModel
        
        # 统计项目环境数量
        stmt = select(func.count(ProjectEnvironmentModel.id)).where(
            ProjectEnvironmentModel.project_id == project_id,
            ProjectEnvironmentModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        env_count = result.scalar()
        
        if env_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"项目还有 {env_count} 个环境，请先删除所有环境后再删除项目"
            )
        
        # 如果只有项目负责人一个成员，先删除成员记录
        if members and len(members) == 1 and members[0].user_id == project.owner_id:
            await member_crud.delete_crud([members[0].id])
        
        await crud.delete_crud([project_id])
    
    # ========== 项目成员管理 ==========
    
    @classmethod
    async def add_project_member_service(
        cls,
        project_id: int,
        data: ProjectMemberCreateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectMemberOutSchema:
        """添加项目成员"""
        # 检查权限
        await cls._check_project_permission(project_id, current_user_id, ["owner", "admin"], db)
        
        member_crud = ProjectMemberCRUD(db)
        
        # 检查是否已是成员
        existing = await member_crud.get_by_project_user_crud(project_id, data.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已是项目成员"
            )
        
        # 添加成员
        member_data = data.model_dump()
        member_data["project_id"] = project_id
        member_data["created_by"] = current_user_id
        member = await member_crud.create_crud(member_data)
        
        # 重新获取成员（包含用户信息）
        member = await member_crud.get_by_id_with_user_crud(member.id)
        
        # 构建输出
        member_out = ProjectMemberOutSchema.model_validate(member)
        if member.user:
            member_out.username = member.user.username
            member_out.email = member.user.email
            member_out.nickname = member.user.nickname
        
        return member_out
    
    @classmethod
    async def get_project_members_service(
        cls,
        project_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> List[ProjectMemberOutSchema]:
        """获取项目成员列表"""
        # 检查权限
        await cls._check_project_member(project_id, current_user_id, db)
        
        member_crud = ProjectMemberCRUD(db)
        members = await member_crud.get_project_members_crud(project_id)
        
        # 构建输出
        items = []
        for member in members:
            member_out = ProjectMemberOutSchema.model_validate(member)
            if member.user:
                member_out.username = member.user.username
                member_out.email = member.user.email
                member_out.nickname = member.user.nickname
            items.append(member_out)
        
        return items
    
    @classmethod
    async def update_project_member_service(
        cls,
        member_id: int,
        data: ProjectMemberUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectMemberOutSchema:
        """更新项目成员角色"""
        member_crud = ProjectMemberCRUD(db)
        
        # 获取成员（包含用户信息）
        member = await member_crud.get_by_id_with_user_crud(member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 检查权限
        await cls._check_project_permission(member.project_id, current_user_id, ["owner", "admin"], db)
        
        # 不能修改owner的角色
        if member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能修改项目负责人的角色"
            )
        
        # 更新角色
        update_data = data.model_dump()
        update_data["updated_by"] = current_user_id
        member = await member_crud.update_crud(member_id, update_data)
        
        # 重新获取成员（包含用户信息）
        member = await member_crud.get_by_id_with_user_crud(member.id)
        
        # 构建输出
        member_out = ProjectMemberOutSchema.model_validate(member)
        if member.user:
            member_out.username = member.user.username
            member_out.email = member.user.email
            member_out.nickname = member.user.nickname
        
        return member_out
    
    @classmethod
    async def remove_project_member_service(
        cls,
        member_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """移除项目成员"""
        member_crud = ProjectMemberCRUD(db)
        
        # 获取成员（不需要用户信息，只需要基本信息）
        member = await member_crud.get_by_id_crud(member_id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="成员不存在"
            )
        
        # 检查权限
        await cls._check_project_permission(member.project_id, current_user_id, ["owner", "admin"], db)
        
        # 不能移除owner
        if member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能移除项目负责人"
            )
        
        # 删除成员
        await member_crud.delete_crud([member_id])
    
    # ========== 项目环境管理 ==========
    
    @classmethod
    async def create_project_environment_service(
        cls,
        project_id: int,
        data: ProjectEnvironmentCreateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectEnvironmentOutSchema:
        """创建项目环境"""
        # 检查权限
        await cls._check_project_permission(project_id, current_user_id, ["owner", "admin", "developer"], db)
        
        env_crud = ProjectEnvironmentCRUD(db)
        
        # 检查环境名称是否已存在
        existing = await env_crud.get_by_project_name_crud(project_id, data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="环境名称已存在"
            )
        
        # 如果设置为默认，取消其他环境的默认状态
        if data.is_default:
            await env_crud.clear_default_environments_crud(project_id)
        
        # 创建环境
        env_data = data.model_dump()
        env_data["project_id"] = project_id
        env_data["created_by"] = current_user_id
        environment = await env_crud.create_crud(env_data)
        
        return ProjectEnvironmentOutSchema.model_validate(environment)
    
    @classmethod
    async def get_project_environments_service(
        cls,
        project_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> List[ProjectEnvironmentOutSchema]:
        """获取项目环境列表"""
        # 检查权限
        await cls._check_project_member(project_id, current_user_id, db)
        
        env_crud = ProjectEnvironmentCRUD(db)
        environments = await env_crud.get_project_environments_crud(project_id)
        
        return [ProjectEnvironmentOutSchema.model_validate(env) for env in environments]
    
    @classmethod
    async def update_project_environment_service(
        cls,
        env_id: int,
        data: ProjectEnvironmentUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> ProjectEnvironmentOutSchema:
        """更新项目环境"""
        env_crud = ProjectEnvironmentCRUD(db)
        
        # 获取环境
        environment = await env_crud.get_by_id_crud(env_id)
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="环境不存在"
            )
        
        # 检查权限
        await cls._check_project_permission(environment.project_id, current_user_id, ["owner", "admin", "developer"], db)
        
        # 如果设置为默认，取消其他环境的默认状态
        if data.is_default:
            await env_crud.clear_default_environments_crud(environment.project_id, env_id)
        
        # 更新环境
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = current_user_id
        environment = await env_crud.update_crud(env_id, update_data)
        
        return ProjectEnvironmentOutSchema.model_validate(environment)
    
    @classmethod
    async def delete_project_environment_service(
        cls,
        env_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """删除项目环境"""
        env_crud = ProjectEnvironmentCRUD(db)
        
        # 获取环境
        environment = await env_crud.get_by_id_crud(env_id)
        if not environment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="环境不存在"
            )
        
        # 检查权限
        await cls._check_project_permission(environment.project_id, current_user_id, ["owner", "admin", "developer"], db)
        
        # 删除环境
        await env_crud.delete_crud([env_id])
    
    # ========== 权限检查辅助方法 ==========
    
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
    
    @classmethod
    async def _check_project_permission(
        cls,
        project_id: int,
        user_id: int,
        required_roles: List[str],
        db: AsyncSession
    ) -> None:
        """检查用户项目权限"""
        member_crud = ProjectMemberCRUD(db)
        role = await member_crud.get_user_role_in_project_crud(project_id, user_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您不是该项目成员，无权操作"
            )
        
        if role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下角色之一: {', '.join(required_roles)}"
            )
