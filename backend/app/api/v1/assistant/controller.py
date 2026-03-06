# AI助手模块 - 控制器层

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.corelibs.logger import logger

from .service import AssistantConfigService, ConversationService, MessageService, DifyService, StatisticsService
from .schema import (
    AssistantConfigCreate, AssistantConfigUpdate, AssistantConfigResponse,
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse, DifyChatRequest,
    AssistantStatistics, PaginatedResponse
)

router = APIRouter(prefix="/assistant", tags=["AI助手"])


# AI助手配置接口
@router.post("/configs", summary="创建AI助手配置")
async def create_config(
    config_data: AssistantConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    创建AI助手配置
    
    - **name**: 助手名称
    - **dify_api_key**: Dify API Key
    - **dify_base_url**: Dify Base URL
    - **assistant_type**: 助手类型 (chatbot/workflow/agent)
    """
    try:
        config = await AssistantConfigService.create_config(
            db=db,
            config_data=config_data,
            creator_id=current_user_id
        )
        
        response_data = AssistantConfigResponse(
            id=config.id,
            name=config.name,
            dify_api_key=config.dify_api_key,
            dify_base_url=config.dify_base_url,
            assistant_type=config.assistant_type,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
        return success_response(data=response_data, message="创建AI助手配置成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 创建配置失败: {str(e)}")
        return error_response(message=f"创建配置失败: {str(e)}")


@router.get("/configs", summary="获取AI助手配置列表")
async def get_config_list(
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """获取AI助手配置列表"""
    try:
        configs, total = await AssistantConfigService.get_config_list(
            db=db,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        
        config_list = []
        for config in configs:
            config_data = AssistantConfigResponse(
                id=config.id,
                name=config.name,
                dify_api_key=config.dify_api_key,
                dify_base_url=config.dify_base_url,
                assistant_type=config.assistant_type,
                is_active=config.is_active,
                created_by=config.created_by,
                created_at=config.created_at,
                updated_at=config.updated_at
            )
            config_list.append(config_data)
        
        paginated_data = PaginatedResponse(
            items=config_list,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
        
        return success_response(data=paginated_data, message="获取配置列表成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 获取配置列表失败: {str(e)}")
        return error_response(message=f"获取配置列表失败: {str(e)}")


@router.get("/configs/{config_id}", summary="获取AI助手配置详情")
async def get_config_detail(
    config_id: int = Path(..., description="配置ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取AI助手配置详情"""
    try:
        config = await AssistantConfigService.get_config_by_id(db, config_id)
        
        response_data = AssistantConfigResponse(
            id=config.id,
            name=config.name,
            dify_api_key=config.dify_api_key,
            dify_base_url=config.dify_base_url,
            assistant_type=config.assistant_type,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
        return success_response(data=response_data, message="获取配置详情成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 获取配置详情失败: {str(e)}")
        return error_response(message=f"获取配置详情失败: {str(e)}")


@router.put("/configs/{config_id}", summary="更新AI助手配置")
async def update_config(
    config_id: int = Path(..., description="配置ID"),
    config_data: AssistantConfigUpdate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    """更新AI助手配置"""
    try:
        config = await AssistantConfigService.update_config(
            db=db,
            config_id=config_id,
            config_data=config_data
        )
        
        response_data = AssistantConfigResponse(
            id=config.id,
            name=config.name,
            dify_api_key=config.dify_api_key,
            dify_base_url=config.dify_base_url,
            assistant_type=config.assistant_type,
            is_active=config.is_active,
            created_by=config.created_by,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        
        return success_response(data=response_data, message="更新配置成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 更新配置失败: {str(e)}")
        return error_response(message=f"更新配置失败: {str(e)}")


@router.delete("/configs/{config_id}", summary="删除AI助手配置")
async def delete_config(
    config_id: int = Path(..., description="配置ID"),
    db: AsyncSession = Depends(get_db)
):
    """删除AI助手配置"""
    try:
        await AssistantConfigService.delete_config(
            db=db,
            config_id=config_id
        )
        
        return success_response(data=None, message="删除配置成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 删除配置失败: {str(e)}")
        return error_response(message=f"删除配置失败: {str(e)}")


# AI对话接口
@router.post("/conversations", summary="创建AI对话")
async def create_conversation(
    conversation_data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """创建AI对话"""
    try:
        conversation = await ConversationService.create_conversation(
            db=db,
            conversation_data=conversation_data,
            user_id=current_user_id
        )
        
        response_data = ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            assistant_config_id=conversation.assistant_config_id,
            conversation_id=conversation.conversation_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,
            last_message_time=None
        )
        
        return success_response(data=response_data, message="创建对话成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 创建对话失败: {str(e)}")
        return error_response(message=f"创建对话失败: {str(e)}")


@router.get("/conversations", summary="获取用户对话列表")
async def get_conversation_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取用户对话列表"""
    try:
        conversations, total = await ConversationService.get_user_conversations(
            db=db,
            user_id=current_user_id,
            page=page,
            page_size=page_size
        )
        
        conversation_list = []
        for conversation in conversations:
            # TODO: 获取消息统计
            conversation_data = ConversationResponse(
                id=conversation.id,
                user_id=conversation.user_id,
                assistant_config_id=conversation.assistant_config_id,
                conversation_id=conversation.conversation_id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                message_count=0,  # TODO: 实际统计
                last_message_time=None  # TODO: 实际查询
            )
            conversation_list.append(conversation_data)
        
        paginated_data = PaginatedResponse(
            items=conversation_list,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
        
        return success_response(data=paginated_data, message="获取对话列表成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 获取对话列表失败: {str(e)}")
        return error_response(message=f"获取对话列表失败: {str(e)}")


@router.get("/conversations/{conversation_id}", summary="获取对话详情")
async def get_conversation_detail(
    conversation_id: int = Path(..., description="对话ID"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取对话详情"""
    try:
        conversation = await ConversationService.get_conversation_by_id(
            db, conversation_id, current_user_id
        )
        
        response_data = ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            assistant_config_id=conversation.assistant_config_id,
            conversation_id=conversation.conversation_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=0,  # TODO: 实际统计
            last_message_time=None  # TODO: 实际查询
        )
        
        return success_response(data=response_data, message="获取对话详情成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 获取对话详情失败: {str(e)}")
        return error_response(message=f"获取对话详情失败: {str(e)}")


@router.delete("/conversations/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: int = Path(..., description="对话ID"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除对话"""
    try:
        await ConversationService.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user_id
        )
        
        return success_response(data=None, message="删除对话成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 删除对话失败: {str(e)}")
        return error_response(message=f"删除对话失败: {str(e)}")


# AI消息接口
@router.get("/conversations/{conversation_id}/messages", summary="获取对话消息列表")
async def get_conversation_messages(
    conversation_id: int = Path(..., description="对话ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取对话消息列表"""
    try:
        # 验证对话权限
        await ConversationService.get_conversation_by_id(
            db, conversation_id, current_user_id
        )
        
        messages, total = await MessageService.get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
            page=page,
            page_size=page_size
        )
        
        message_list = []
        for message in messages:
            message_data = MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at
            )
            message_list.append(message_data)
        
        paginated_data = PaginatedResponse(
            items=message_list,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
        
        return success_response(data=paginated_data, message="获取消息列表成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 获取消息列表失败: {str(e)}")
        return error_response(message=f"获取消息列表失败: {str(e)}")


@router.post("/conversations/{conversation_id}/chat", summary="发送聊天消息")
async def chat_with_assistant(
    conversation_id: int = Path(..., description="对话ID"),
    query: str = Body(..., embed=True, description="用户问题"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """发送聊天消息"""
    try:
        result = await DifyService.chat(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user_id,
            query=query
        )
        
        return success_response(data=result, message="聊天成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 聊天失败: {str(e)}")
        return error_response(message=f"聊天失败: {str(e)}")


# 统计接口
@router.get("/statistics", summary="获取AI助手统计")
async def get_assistant_statistics(
    db: AsyncSession = Depends(get_db)
):
    """获取AI助手统计信息"""
    try:
        statistics = await StatisticsService.get_statistics(db=db)
        
        return success_response(data=statistics, message="获取统计信息成功")
        
    except Exception as e:
        logger.error(f"[AI助手] 获取统计信息失败: {str(e)}")
        return error_response(message=f"获取统计信息失败: {str(e)}")