"""
项目管理API控制器
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.projects.service import ProjectService
from app.api.v1.projects.schema import (
    ProjectCreateSchema,
    ProjectUpdateSchema,
    ProjectQuerySchema,
    ProjectMemberCreateSchema,
    ProjectMemberUpdateSchema,
    ProjectEnvironmentCreateSchema,
    ProjectEnvironmentUpdateSchema
)
from app.common.response import success_response

router = APIRouter()


# ========== 项目管理 ==========

@router.post("/", summary="创建项目")
async def create_project(
    data: ProjectCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建项目"""
    result = await ProjectService.create_project_service(data, current_user_id, db)
    return success_response(data=result.model_dump(), message="项目创建成功")


@router.get("/", summary="获取项目列表")
async def get_project_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="项目名称"),
    status: Optional[str] = Query(None, description="项目状态"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取项目列表"""
    query = ProjectQuerySchema(
        page=page,
        page_size=page_size,
        name=name if name and name.strip() else None,
        status=status if status and status.strip() else None
    )
    return await ProjectService.get_project_list_service(query, current_user_id, db)


@router.get("/{project_id}", summary="获取项目详情")
async def get_project_detail(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取项目详情"""
    result = await ProjectService.get_project_detail_service(project_id, current_user_id, db)
    return success_response(data=result.model_dump())


@router.put("/{project_id}", summary="更新项目")
async def update_project(
    project_id: int,
    data: ProjectUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新项目"""
    result = await ProjectService.update_project_service(project_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="项目更新成功")


@router.delete("/{project_id}", summary="删除项目")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除项目"""
    await ProjectService.delete_project_service(project_id, current_user_id, db)
    return success_response(message="项目删除成功")


# ========== 项目成员管理 ==========

@router.post("/{project_id}/members", summary="添加项目成员")
async def add_project_member(
    project_id: int,
    data: ProjectMemberCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """添加项目成员"""
    result = await ProjectService.add_project_member_service(project_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="成员添加成功")


@router.get("/{project_id}/members", summary="获取项目成员列表")
async def get_project_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取项目成员列表"""
    result = await ProjectService.get_project_members_service(project_id, current_user_id, db)
    return success_response(data=[item.model_dump() for item in result])


@router.put("/{project_id}/members/{member_id}", summary="更新项目成员角色")
async def update_project_member(
    project_id: int,
    member_id: int,
    data: ProjectMemberUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新项目成员角色"""
    result = await ProjectService.update_project_member_service(member_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="成员角色更新成功")


@router.delete("/{project_id}/members/{member_id}", summary="移除项目成员")
async def remove_project_member(
    project_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """移除项目成员"""
    await ProjectService.remove_project_member_service(member_id, current_user_id, db)
    return success_response(message="成员移除成功")


# ========== 项目环境管理 ==========

@router.post("/{project_id}/environments", summary="创建项目环境")
async def create_project_environment(
    project_id: int,
    data: ProjectEnvironmentCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建项目环境"""
    result = await ProjectService.create_project_environment_service(project_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="环境创建成功")


@router.get("/{project_id}/environments", summary="获取项目环境列表")
async def get_project_environments(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取项目环境列表"""
    result = await ProjectService.get_project_environments_service(project_id, current_user_id, db)
    return success_response(data=[item.model_dump() for item in result])


@router.put("/{project_id}/environments/{env_id}", summary="更新项目环境")
async def update_project_environment(
    project_id: int,
    env_id: int,
    data: ProjectEnvironmentUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新项目环境"""
    result = await ProjectService.update_project_environment_service(env_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="环境更新成功")


@router.delete("/{project_id}/environments/{env_id}", summary="删除项目环境")
async def delete_project_environment(
    project_id: int,
    env_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除项目环境"""
    await ProjectService.delete_project_environment_service(env_id, current_user_id, db)
    return success_response(message="环境删除成功")
