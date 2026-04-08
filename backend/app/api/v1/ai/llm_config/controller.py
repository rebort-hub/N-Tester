# -*- coding: utf-8 -*-
"""
LLM 配置 API 控制器
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.common.response import success_response, error_response
from app.api.v1.ai.llm_config.schema import (
    LLMConfigCreateSchema,
    LLMConfigUpdateSchema,
    LLMConfigOutSchema,
    LLMConfigTestSchema,
    LLMConfigTestResponseSchema
)
from app.api.v1.ai.llm_config.service import LLMConfigService

router = APIRouter()


@router.get("", summary="获取 LLM 配置列表")
async def get_llm_configs(
    provider: Optional[str] = Query(None, description="提供商筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: AsyncSession = Depends(get_db)
):
    """获取 LLM 配置列表"""
    configs = await LLMConfigService.get_list(db, provider, is_active)
    
    # 转换为输出格式（脱敏处理）
    result = []
    for config in configs:
        # 脱敏处理API密钥
        masked_api_key = ""
        if config.api_key:
            if len(config.api_key) > 12:
                masked_api_key = config.api_key[:8] + "****" + config.api_key[-4:]
            else:
                masked_api_key = "****" + config.api_key[-4:] if len(config.api_key) > 4 else "****"
        
        config_dict = {
            "id": config.id,
            "config_name": config.config_name,
            "name": config.name,
            "provider": config.provider,
            "model_name": config.model_name,
            "api_key": masked_api_key,  # 返回脱敏值
            "base_url": config.base_url,
            "system_prompt": config.system_prompt,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "supports_vision": config.supports_vision,
            "context_limit": config.context_limit,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "creation_date": config.creation_date.isoformat() if config.creation_date else None,
            "created_by": config.created_by,
            "updation_date": config.updation_date.isoformat() if config.updation_date else None,
            "updated_by": config.updated_by
        }
        result.append(config_dict)
    
    return success_response(data=result, message="查询成功")


@router.get("/default", summary="获取默认 LLM 配置")
async def get_default_config(db: AsyncSession = Depends(get_db)):
    """获取默认 LLM 配置"""
    config = await LLMConfigService.get_default(db)
    
    if not config:
        return error_response(message="未找到默认配置")
    
    # 脱敏处理API密钥
    masked_api_key = ""
    if config.api_key:
        if len(config.api_key) > 12:
            masked_api_key = config.api_key[:8] + "****" + config.api_key[-4:]
        else:
            masked_api_key = "****" + config.api_key[-4:] if len(config.api_key) > 4 else "****"
    
    config_dict = {
        "id": config.id,
        "config_name": config.config_name,
        "name": config.name,
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": masked_api_key,  # 返回脱敏值
        "base_url": config.base_url,
        "system_prompt": config.system_prompt,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "supports_vision": config.supports_vision,
        "context_limit": config.context_limit,
        "is_default": config.is_default,
        "is_active": config.is_active,
        "creation_date": config.creation_date.isoformat() if config.creation_date else None,
        "created_by": config.created_by,
        "updation_date": config.updation_date.isoformat() if config.updation_date else None,
        "updated_by": config.updated_by
    }
    
    return success_response(data=config_dict, message="查询成功")


@router.get("/{config_id}", summary="获取 LLM 配置详情")
async def get_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取 LLM 配置详情"""
    config = await LLMConfigService.get_by_id(db, config_id)
    
    if not config:
        return error_response(message="配置不存在")
    
    # 脱敏处理API密钥
    masked_api_key = ""
    if config.api_key:
        if len(config.api_key) > 12:
            masked_api_key = config.api_key[:8] + "****" + config.api_key[-4:]
        else:
            masked_api_key = "****" + config.api_key[-4:] if len(config.api_key) > 4 else "****"
    
    config_dict = {
        "id": config.id,
        "config_name": config.config_name,
        "name": config.name,
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": masked_api_key,  # 返回脱敏值
        "base_url": config.base_url,
        "system_prompt": config.system_prompt,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "supports_vision": config.supports_vision,
        "context_limit": config.context_limit,
        "is_default": config.is_default,
        "is_active": config.is_active,
        "creation_date": config.creation_date.isoformat() if config.creation_date else None,
        "created_by": config.created_by,
        "updation_date": config.updation_date.isoformat() if config.updation_date else None,
        "updated_by": config.updated_by
    }
    
    return success_response(data=config_dict, message="查询成功")


@router.post("", summary="创建 LLM 配置")
async def create_llm_config(
    data: LLMConfigCreateSchema,
    db: AsyncSession = Depends(get_db)
):
    """创建 LLM 配置"""
    config = await LLMConfigService.create(db, data, user_id=1)  # TODO: 从当前用户获取
    
    # 脱敏处理API密钥
    masked_api_key = ""
    if config.api_key:
        if len(config.api_key) > 12:
            masked_api_key = config.api_key[:8] + "****" + config.api_key[-4:]
        else:
            masked_api_key = "****" + config.api_key[-4:] if len(config.api_key) > 4 else "****"
    
    config_dict = {
        "id": config.id,
        "config_name": config.config_name,
        "name": config.name,
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": masked_api_key,  # 返回脱敏值
        "base_url": config.base_url,
        "system_prompt": config.system_prompt,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "supports_vision": config.supports_vision,
        "context_limit": config.context_limit,
        "is_default": config.is_default,
        "is_active": config.is_active,
        "creation_date": config.creation_date.isoformat() if config.creation_date else None,
        "created_by": config.created_by,
        "updation_date": config.updation_date.isoformat() if config.updation_date else None,
        "updated_by": config.updated_by
    }
    
    return success_response(data=config_dict, message="创建成功")


@router.put("/{config_id}", summary="更新 LLM 配置")
async def update_llm_config(
    config_id: int,
    data: LLMConfigUpdateSchema,
    db: AsyncSession = Depends(get_db)
):
    """更新 LLM 配置"""
    config = await LLMConfigService.update(db, config_id, data, user_id=1)  # TODO: 从当前用户获取
    
    # 脱敏处理API密钥
    masked_api_key = ""
    if config.api_key:
        if len(config.api_key) > 12:
            masked_api_key = config.api_key[:8] + "****" + config.api_key[-4:]
        else:
            masked_api_key = "****" + config.api_key[-4:] if len(config.api_key) > 4 else "****"
    
    config_dict = {
        "id": config.id,
        "config_name": config.config_name,
        "name": config.name,
        "provider": config.provider,
        "model_name": config.model_name,
        "api_key": masked_api_key,  # 返回脱敏值
        "base_url": config.base_url,
        "system_prompt": config.system_prompt,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "supports_vision": config.supports_vision,
        "context_limit": config.context_limit,
        "is_default": config.is_default,
        "is_active": config.is_active,
        "creation_date": config.creation_date.isoformat() if config.creation_date else None,
        "created_by": config.created_by,
        "updation_date": config.updation_date.isoformat() if config.updation_date else None,
        "updated_by": config.updated_by
    }
    
    return success_response(data=config_dict, message="更新成功")


@router.delete("/{config_id}", summary="删除 LLM 配置")
async def delete_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除 LLM 配置"""
    await LLMConfigService.delete(db, config_id)
    return success_response(message="删除成功")


@router.post("/{config_id}/set-default", summary="设置为默认配置")
async def set_default_config(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """设置为默认配置"""
    config = await LLMConfigService.set_default(db, config_id)
    
    config_dict = {
        "id": config.id,
        "config_name": config.config_name,
        "name": config.name,
        "provider": config.provider,
        "is_default": config.is_default
    }
    
    return success_response(data=config_dict, message="设置成功")


@router.post("/test", summary="测试 LLM 配置")
async def test_llm_config(
    data: LLMConfigTestSchema,
    db: AsyncSession = Depends(get_db)
):
    """测试 LLM 配置"""
    result = await LLMConfigService.test_config(db, data)
    
    if result["success"]:
        return success_response(data=result, message="测试成功")
    else:
        return error_response(data=result, message="测试失败")
