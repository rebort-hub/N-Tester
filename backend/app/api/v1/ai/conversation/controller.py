"""
对话管理控制器
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json
import asyncio
from app.db.sqlalchemy import get_db
from app.api.v1.system.auth.dependencies import get_current_user
from app.common.response import success_response, error_response
from .schema import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
    ConversationData,
    ConversationListResponse,
    SendMessageRequest,
    SendMessageResponse,
    MessageData,
    MessageListResponse
)
from .service import ConversationService, MessageService


router = APIRouter(prefix="/conversation", tags=["AI对话管理"])


# ==================== 对话管理 ====================

@router.post("", summary="创建对话")
async def create_conversation(
    data: ConversationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建新对话"""
    try:
        conversation = await ConversationService.create_conversation(
            db, current_user.id, data
        )
        
        return success_response(data=ConversationData.model_validate(conversation))
    except Exception as e:
        return error_response(message=f"创建对话失败: {str(e)}")


@router.get("", summary="获取对话列表")
async def get_conversation_list(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取当前用户的对话列表"""
    try:
        conversations, total = await ConversationService.get_conversation_list(
            db, current_user.id, skip, limit
        )
        
        # 获取每个对话的消息数量
        conversation_list = []
        for conv in conversations:
            conv_data = ConversationData.model_validate(conv)
            conv_data.message_count = await ConversationService.get_message_count(db, conv.id)
            conversation_list.append(conv_data)
        
        return success_response(data=ConversationListResponse(
            conversations=conversation_list,
            total=total
        ))
    except Exception as e:
        return error_response(message=f"获取对话列表失败: {str(e)}")


@router.get("/{conversation_id}", summary="获取对话详情")
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取对话详情"""
    try:
        conversation = await ConversationService.get_conversation(
            db, conversation_id, current_user.id
        )
        
        if not conversation:
            return error_response(message="对话不存在")
        
        conv_data = ConversationData.model_validate(conversation)
        conv_data.message_count = await ConversationService.get_message_count(db, conversation.id)
        
        return success_response(data=conv_data)
    except Exception as e:
        return error_response(message=f"获取对话详情失败: {str(e)}")


@router.put("/{conversation_id}", summary="更新对话")
async def update_conversation(
    conversation_id: int,
    data: ConversationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """更新对话信息"""
    try:
        conversation = await ConversationService.update_conversation(
            db, conversation_id, current_user.id, data
        )
        
        if not conversation:
            return error_response(message="对话不存在")
        
        return success_response(data=ConversationData.model_validate(conversation))
    except Exception as e:
        return error_response(message=f"更新对话失败: {str(e)}")


@router.delete("/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除对话"""
    try:
        success_flag = await ConversationService.delete_conversation(
            db, conversation_id, current_user.id
        )
        
        if not success_flag:
            return error_response(message="对话不存在")
        
        return success_response(message="删除成功")
    except Exception as e:
        return error_response(message=f"删除对话失败: {str(e)}")


# ==================== 消息管理 ====================

@router.get("/{conversation_id}/messages", summary="获取消息列表")
async def get_message_list(
    conversation_id: int,
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=500, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取对话的消息列表"""
    try:
        messages, total = await MessageService.get_message_list(
            db, conversation_id, current_user.id, skip, limit
        )
        
        return success_response(data=MessageListResponse(
            messages=[MessageData.model_validate(msg) for msg in messages],
            total=total
        ))
    except Exception as e:
        return error_response(message=f"获取消息列表失败: {str(e)}")


@router.post("/{conversation_id}/messages", summary="发送消息")
async def send_message(
    conversation_id: int,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """发送消息并获取AI响应"""
    try:
        user_message, assistant_message, total_tokens = await MessageService.send_message(
            db, conversation_id, current_user.id, data
        )
        
        return success_response(data=SendMessageResponse(
            user_message=MessageData.model_validate(user_message),
            assistant_message=MessageData.model_validate(assistant_message),
            total_tokens=total_tokens
        ))
    except ValueError as e:
        return error_response(message=str(e))
    except Exception as e:
        return error_response(message=f"发送消息失败: {str(e)}")


@router.post("/{conversation_id}/messages/stream", summary="发送消息（流式响应）")
async def send_message_stream(
    conversation_id: int,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """发送消息并获取AI流式响应（SSE）"""
    
    async def event_generator():
        """SSE 事件生成器"""
        try:
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'message': '开始生成回复'}, ensure_ascii=False)}\n\n"
            
            # 调用流式消息服务
            async for event in MessageService.send_message_stream(
                db, conversation_id, current_user.id, data
            ):
                # 发送事件数据
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                # 添加小延迟，确保客户端能够接收
                await asyncio.sleep(0.01)
            
            # 发送完成事件
            yield f"data: {json.dumps({'type': 'done', 'message': '生成完成'}, ensure_ascii=False)}\n\n"
            
        except ValueError as e:
            # 发送错误事件
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 发送错误事件
            yield f"data: {json.dumps({'type': 'error', 'message': f'发送消息失败: {str(e)}'}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@router.get("/{conversation_id}/mcp-records", summary="获取MCP执行记录")
async def get_mcp_records(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        records = await MessageService.get_mcp_execution_records(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            limit=limit,
        )
        return success_response(data={"records": records, "total": len(records)})
    except Exception as e:
        return error_response(message=f"获取MCP执行记录失败: {str(e)}")

