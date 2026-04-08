"""
统一响应格式
"""

from typing import Any, Optional
from app.common.enums import ResponseCode
from app.core.base_schema import PageSchema


def success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = ResponseCode.SUCCESS
) -> dict:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 响应状态码
        
    Returns:
        响应字典
    """
    return {
        "code": int(code),
        "message": message,
        "data": data
    }


def error_response(
    message: str = "操作失败",
    code: int = ResponseCode.ERROR,
    data: Any = None
) -> dict:
    """
    错误响应
    
    Args:
        message: 错误消息
        code: 错误状态码
        data: 额外数据
        
    Returns:
        响应字典
    """
    return {
        "code": int(code),
        "message": message,
        "data": data
    }


def page_response(
    items: list,
    total: int,
    page: int,
    page_size: int,
    message: str = "查询成功"
) -> dict:
    """
    分页响应
    
    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页数量
        message: 响应消息
        
    Returns:
        响应字典
    """
    return success_response(
        data={
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        },
        message=message
    )
