"""
WebSocket 流式对话控制器
"""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.api.v1.system.auth.service import AuthService
from app.api.v1.system.user.crud import UserCRUD
from .service import ConversationService, MessageService
from .schema import SendMessageRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversation", tags=["AI对话WebSocket"])


async def get_current_user_ws(token: str, db: AsyncSession):
    """
    WebSocket 认证
    """
    try:
        # 验证 token
        payload = AuthService.verify_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
        
        # 获取用户信息
        user_crud = UserCRUD(db)
        user = await user_crud.get_by_id_crud(int(user_id))
        return user
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        return None


@router.websocket("/{conversation_id}/ws")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: int,
    token: str = Query(None, description="认证 token")
):
    """
    WebSocket 聊天端点
    
    消息格式:
    客户端 -> 服务器:
    {
        "type": "message",
        "content": "用户消息内容"
    }
    
    服务器 -> 客户端:
    {
        "type": "start",
        "message": "开始生成回复"
    }
    {
        "type": "user_message",
        "data": { ... }
    }
    {
        "type": "content",
        "data": { "content": "内容块" }
    }
    {
        "type": "assistant_message",
        "data": { ... }
    }
    {
        "type": "done",
        "message": "生成完成"
    }
    {
        "type": "error",
        "message": "错误信息"
    }
    """
    # 先接受连接
    await websocket.accept()
    
    try:
        # 验证 token
        if not token:
            await websocket.close(code=1008, reason="Token is required")
            return
        
        # 获取数据库会话
        async for db in get_db():
            try:
                # 认证
                current_user = await get_current_user_ws(token, db)
                if not current_user:
                    await websocket.close(code=1008, reason="Authentication failed")
                    return
                
                # 验证对话权限
                conversation = await ConversationService.get_conversation(db, conversation_id, current_user.id)
                if not conversation:
                    await websocket.close(code=1008, reason="Conversation not found")
                    return
                
                logger.info(f"WebSocket connected: user={current_user.id}, conversation={conversation_id}")
                
                # 发送连接成功消息
                await websocket.send_json({
                    "type": "connected",
                    "message": "WebSocket 连接成功",
                    "conversation_id": conversation_id
                })
                
                # 消息循环
                while True:
                    # 接收客户端消息
                    data = await websocket.receive_json()
                    
                    if data.get("type") == "message":
                        content = data.get("content", "").strip()
                        
                        if not content:
                            await websocket.send_json({
                                "type": "error",
                                "message": "消息内容不能为空"
                            })
                            continue
                        
                        # 发送开始事件
                        await websocket.send_json({
                            "type": "start",
                            "message": "开始生成回复"
                        })
                        
                        try:
                            # 创建请求对象
                            request = SendMessageRequest(
                                content=content,
                                stream=True,
                                attachments=data.get("attachments"),
                                project_id=data.get("project_id"),
                                use_knowledge_base=bool(data.get("use_knowledge_base", False)),
                                knowledge_base_id=data.get("knowledge_base_id"),
                                use_mcp=bool(data.get("use_mcp", False)),
                                mcp_config_id=data.get("mcp_config_id"),
                            )
                            
                            # 调用流式消息服务
                            async for event in MessageService.send_message_stream(
                                db, conversation_id, current_user.id, request
                            ):
                                # 发送事件到客户端
                                await websocket.send_json(event)
                            
                            # 发送完成事件
                            await websocket.send_json({
                                "type": "done",
                                "message": "生成完成"
                            })
                            
                        except ValueError as e:
                            await websocket.send_json({
                                "type": "error",
                                "message": str(e)
                            })
                        except Exception as e:
                            logger.error(f"Message processing error: {e}", exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "message": f"处理消息失败: {str(e)}"
                            })
                    
                    elif data.get("type") == "ping":
                        # 心跳响应
                        await websocket.send_json({
                            "type": "pong"
                        })
                    
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"未知的消息类型: {data.get('type')}"
                        })
            
            finally:
                # 确保数据库会话被关闭
                pass
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: conversation={conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"连接错误: {str(e)}"
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
