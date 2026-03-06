"""
数据工厂Controller层
提供API接口
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.corelibs.logger import logger

from .service import DataFactoryService
from .schema import (
    ToolExecuteRequest,
    ToolExecuteResponse,
    BatchGenerateRequest,
    BatchGenerateResponse,
    DataFactoryRecordOut,
    DataFactoryRecordListResponse,
    ToolCategoriesResponse,
    StatisticsResponse,
    TagsResponse
)

router = APIRouter(prefix="/data-factory", tags=["数据工厂"])


@router.get("/categories", summary="获取工具分类")
async def get_categories():
    """
    获取所有工具分类和工具列表
    
    Returns:
        工具分类和工具列表
    """
    try:
        result = await DataFactoryService.get_categories_with_tools()
        return success_response(data=result)
    except Exception as e:
        logger.error(f"[数据工厂] 获取工具分类失败: {str(e)}")
        return error_response(message=f"获取工具分类失败: {str(e)}")


@router.post("/execute", summary="执行工具")
async def execute_tool(
    request: ToolExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    执行数据工厂工具
    
    Args:
        request: 工具执行请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        工具执行结果
    """
    try:
        # 执行工具
        result = await DataFactoryService.execute_tool(
            tool_name=request.tool_name,
            tool_category=request.tool_category,
            input_data=request.input_data or {}
        )
        
        # 检查是否有错误
        if 'error' in result:
            return error_response(message=result['error'])
        
        # 保存记录
        record_id = None
        created_at = None
        if request.is_saved:
            record = await DataFactoryService.save_record(
                db=db,
                user_id=user_id,
                tool_name=request.tool_name,
                tool_category=request.tool_category,
                tool_scenario=request.tool_scenario,
                input_data=request.input_data,
                output_data=result,
                is_saved=request.is_saved,
                tags=request.tags
            )
            record_id = record.id
            created_at = record.creation_date
        
        return success_response(data={
            'result': result,
            'record_id': record_id,
            'created_at': created_at
        })
        
    except Exception as e:
        logger.error(f"[数据工厂] 执行工具失败: {str(e)}")
        return error_response(message=f"执行工具失败: {str(e)}")


@router.post("/batch-generate", summary="批量生成数据")
async def batch_generate(
    request: BatchGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    批量生成数据
    
    Args:
        request: 批量生成请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        批量生成结果
    """
    try:
        results = []
        
        # 批量执行工具
        for i in range(request.count):
            result = await DataFactoryService.execute_tool(
                tool_name=request.tool_name,
                tool_category=request.tool_category,
                input_data=request.input_data or {}
            )
            
            if 'error' not in result:
                results.append(result)
        
        # 保存记录
        if request.is_saved and results:
            await DataFactoryService.save_record(
                db=db,
                user_id=user_id,
                tool_name=request.tool_name,
                tool_category=request.tool_category,
                tool_scenario=request.tool_scenario,
                input_data=request.input_data,
                output_data={'results': results, 'count': len(results)},
                is_saved=request.is_saved
            )
        
        return success_response(data={
            'results': results,
            'count': len(results),
            'total_requested': request.count
        })
        
    except Exception as e:
        logger.error(f"[数据工厂] 批量生成失败: {str(e)}")
        return error_response(message=f"批量生成失败: {str(e)}")


@router.get("/records", summary="获取使用记录")
async def get_records(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    tool_category: Optional[str] = Query(None, description="工具分类过滤"),
    tool_name: Optional[str] = Query(None, description="工具名称过滤"),
    tags: Optional[str] = Query(None, description="标签过滤，多个标签用逗号分隔"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取用户的工具使用记录
    
    Args:
        page: 页码
        page_size: 每页数量
        tool_category: 工具分类过滤
        tool_name: 工具名称过滤
        tags: 标签过滤，多个标签用逗号分隔
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        记录列表
    """
    try:
        # 处理标签参数
        tag_list = None
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        
        records, total = await DataFactoryService.get_records(
            db=db,
            user_id=user_id,
            page=page,
            page_size=page_size,
            tool_category=tool_category,
            tool_name=tool_name,
            tags=tag_list
        )
        
        # 转换为输出格式
        items = [DataFactoryRecordOut.model_validate(record) for record in records]
        
        return success_response(data={
            'items': items,
            'total': total,
            'page': page,
            'page_size': page_size
        })
        
    except Exception as e:
        logger.error(f"[数据工厂] 获取记录列表失败: {str(e)}")
        return error_response(message=f"获取记录列表失败: {str(e)}")


@router.delete("/records/{record_id}", summary="删除记录")
async def delete_record(
    record_id: int = Path(..., description="记录ID"),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    删除工具使用记录（硬删除）
    
    Args:
        record_id: 记录ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        success = await DataFactoryService.hard_delete_record(
            db=db,
            record_id=record_id,
            user_id=user_id
        )
        
        if not success:
            return error_response(message="记录不存在或无权限删除")
        
        return success_response(message="删除成功")
        
    except Exception as e:
        logger.error(f"[数据工厂] 删除记录失败: {str(e)}")
        return error_response(message=f"删除记录失败: {str(e)}")


@router.post("/records/batch-delete", summary="批量删除记录")
async def batch_delete_records(
    request: dict,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    批量删除工具使用记录（硬删除）
    
    Args:
        request: 包含ids列表的请求体
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        删除结果
    """
    try:
        ids = request.get('ids', [])
        if not ids:
            return error_response(message="请选择要删除的记录")
        
        success_count = await DataFactoryService.batch_hard_delete_records(
            db=db,
            record_ids=ids,
            user_id=user_id
        )
        
        return success_response(
            message=f"成功删除 {success_count} 条记录",
            data={'deleted_count': success_count}
        )
        
    except Exception as e:
        logger.error(f"[数据工厂] 批量删除记录失败: {str(e)}")
        return error_response(message=f"批量删除记录失败: {str(e)}")


@router.get("/statistics", summary="获取使用统计")
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取用户的工具使用统计
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        统计信息
    """
    try:
        stats = await DataFactoryService.get_statistics(
            db=db,
            user_id=user_id
        )
        
        return success_response(data=stats)
        
    except Exception as e:
        logger.error(f"[数据工厂] 获取统计信息失败: {str(e)}")
        return error_response(message=f"获取统计信息失败: {str(e)}")


@router.get("/tags", summary="获取标签列表")
async def get_tags(
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    获取用户的所有标签
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        标签列表
    """
    try:
        tags = await DataFactoryService.get_tags(
            db=db,
            user_id=user_id
        )
        
        return success_response(data={
            'tags': tags,
            'count': len(tags)
        })
        
    except Exception as e:
        logger.error(f"[数据工厂] 获取标签列表失败: {str(e)}")
        return error_response(message=f"获取标签列表失败: {str(e)}")
