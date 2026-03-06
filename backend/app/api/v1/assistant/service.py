# AI助手模块 - 业务逻辑层

import json
import httpx
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.orm import selectinload

from app.corelibs.logger import logger
from app.exceptions.exceptions import MyBaseException
from .model import AIAssistantConfig, AIConversation, AIMessage
from .schema import (
    AssistantConfigCreate, AssistantConfigUpdate,
    ConversationCreate, ConversationUpdate,
    MessageCreate, DifyChatRequest, DifyChatResponse,
    AssistantStatistics
)


class AssistantConfigService:
    """AI助手配置服务类"""
    
    @classmethod
    async def create_config(
        cls,
        db: AsyncSession,
        config_data: AssistantConfigCreate,
        creator_id: int
    ) -> AIAssistantConfig:
        """
        创建AI助手配置
        
        Args:
            db: 数据库会话
            config_data: 配置数据
            creator_id: 创建人ID
            
        Returns:
            创建的配置对象
        """
        try:
            config = AIAssistantConfig(
                name=config_data.name,
                dify_api_key=config_data.dify_api_key,
                dify_base_url=config_data.dify_base_url,
                assistant_type=config_data.assistant_type,
                created_by=creator_id,
                is_active=True
            )
            
            db.add(config)
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"[AI助手] 创建配置成功: {config.id}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[AI助手] 创建配置失败: {str(e)}")
            raise MyBaseException(f"创建配置失败: {str(e)}")
    
    @classmethod
    async def get_config_list(
        cls,
        db: AsyncSession,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AIAssistantConfig], int]:
        """
        获取AI助手配置列表
        
        Args:
            db: 数据库会话
            is_active: 是否启用筛选
            page: 页码
            page_size: 每页大小
            
        Returns:
            配置列表和总数
        """
        try:
            conditions = []
            
            if is_active is not None:
                conditions.append(AIAssistantConfig.is_active == is_active)
            
            # 获取总数
            count_query = select(func.count(AIAssistantConfig.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页查询
            query = select(AIAssistantConfig)
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(AIAssistantConfig.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            configs = result.scalars().all()
            
            return list(configs), total
            
        except Exception as e:
            logger.error(f"[AI助手] 获取配置列表失败: {str(e)}")
            raise MyBaseException(f"获取配置列表失败: {str(e)}")
    
    @classmethod
    async def get_config_by_id(
        cls,
        db: AsyncSession,
        config_id: int
    ) -> Optional[AIAssistantConfig]:
        """
        根据ID获取配置
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            
        Returns:
            配置对象
        """
        try:
            query = select(AIAssistantConfig).where(AIAssistantConfig.id == config_id)
            result = await db.execute(query)
            config = result.scalar_one_or_none()
            
            if not config:
                raise MyBaseException("配置不存在")
            
            return config
            
        except MyBaseException:
            raise
        except Exception as e:
            logger.error(f"[AI助手] 获取配置失败: {str(e)}")
            raise MyBaseException(f"获取配置失败: {str(e)}")
    
    @classmethod
    async def update_config(
        cls,
        db: AsyncSession,
        config_id: int,
        config_data: AssistantConfigUpdate
    ) -> AIAssistantConfig:
        """
        更新AI助手配置
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            config_data: 更新数据
            
        Returns:
            更新后的配置对象
        """
        try:
            config = await cls.get_config_by_id(db, config_id)
            
            # 更新字段
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
            
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"[AI助手] 更新配置成功: {config_id}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[AI助手] 更新配置失败: {str(e)}")
            raise MyBaseException(f"更新配置失败: {str(e)}")
    
    @classmethod
    async def delete_config(
        cls,
        db: AsyncSession,
        config_id: int
    ) -> bool:
        """
        删除AI助手配置
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            
        Returns:
            是否删除成功
        """
        try:
            config = await cls.get_config_by_id(db, config_id)
            
            # 检查是否有关联的对话
            from sqlalchemy import select, func
            conversation_count_query = select(func.count(AIConversation.id)).where(
                AIConversation.assistant_config_id == config_id
            )
            conversation_result = await db.execute(conversation_count_query)
            conversation_count = conversation_result.scalar() or 0
            
            if conversation_count > 0:
                raise MyBaseException(f"无法删除配置，该配置关联了 {conversation_count} 个对话")
            
            # 删除配置
            await db.delete(config)
            await db.commit()
            
            logger.info(f"[AI助手] 删除配置成功: {config_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[AI助手] 删除配置失败: {str(e)}")
            raise MyBaseException(f"删除配置失败: {str(e)}")


class ConversationService:
    """AI对话服务类"""
    
    @classmethod
    async def create_conversation(
        cls,
        db: AsyncSession,
        conversation_data: ConversationCreate,
        user_id: int
    ) -> AIConversation:
        """
        创建AI对话
        
        Args:
            db: 数据库会话
            conversation_data: 对话数据
            user_id: 用户ID
            
        Returns:
            创建的对话对象
        """
        try:
            conversation = AIConversation(
                user_id=user_id,
                assistant_config_id=conversation_data.assistant_config_id,
                title=conversation_data.title or "新对话",
                conversation_id=None  # 将在第一次聊天时由Dify生成
            )
            
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            
            logger.info(f"[AI助手] 创建对话成功: {conversation.id}")
            return conversation
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[AI助手] 创建对话失败: {str(e)}")
            raise MyBaseException(f"创建对话失败: {str(e)}")
    
    @classmethod
    async def get_user_conversations(
        cls,
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AIConversation], int]:
        """
        获取用户对话列表
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            对话列表和总数
        """
        try:
            # 获取总数
            count_query = select(func.count(AIConversation.id)).where(
                AIConversation.user_id == user_id
            )
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页查询
            query = select(AIConversation).where(AIConversation.user_id == user_id)
            query = query.order_by(desc(AIConversation.updated_at))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            conversations = result.scalars().all()
            
            return list(conversations), total
            
        except Exception as e:
            logger.error(f"[AI助手] 获取对话列表失败: {str(e)}")
            raise MyBaseException(f"获取对话列表失败: {str(e)}")
    
    @classmethod
    async def get_conversation_by_id(
        cls,
        db: AsyncSession,
        conversation_id: int,
        user_id: int
    ) -> Optional[AIConversation]:
        """
        根据ID获取对话
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            对话对象
        """
        try:
            query = select(AIConversation).where(
                and_(
                    AIConversation.id == conversation_id,
                    AIConversation.user_id == user_id
                )
            )
            result = await db.execute(query)
            conversation = result.scalar_one_or_none()
            
            if not conversation:
                raise MyBaseException("对话不存在")
            
            return conversation
            
        except MyBaseException:
            raise
        except Exception as e:
            logger.error(f"[AI助手] 获取对话失败: {str(e)}")
            raise MyBaseException(f"获取对话失败: {str(e)}")
    
    @classmethod
    async def delete_conversation(
        cls,
        db: AsyncSession,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """
        删除对话
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            # 验证对话权限
            conversation = await cls.get_conversation_by_id(db, conversation_id, user_id)
            
            # 删除关联的消息
            from sqlalchemy import delete
            delete_messages_query = delete(AIMessage).where(
                AIMessage.conversation_id == conversation_id
            )
            await db.execute(delete_messages_query)
            
            # 删除对话
            await db.delete(conversation)
            await db.commit()
            
            logger.info(f"[AI助手] 删除对话成功: {conversation_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[AI助手] 删除对话失败: {str(e)}")
            raise MyBaseException(f"删除对话失败: {str(e)}")


class MessageService:
    """AI消息服务类"""
    
    @classmethod
    async def get_conversation_messages(
        cls,
        db: AsyncSession,
        conversation_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[AIMessage], int]:
        """
        获取对话消息列表
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            page: 页码
            page_size: 每页大小
            
        Returns:
            消息列表和总数
        """
        try:
            # 获取总数
            count_query = select(func.count(AIMessage.id)).where(
                AIMessage.conversation_id == conversation_id
            )
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页查询
            query = select(AIMessage).where(AIMessage.conversation_id == conversation_id)
            query = query.order_by(asc(AIMessage.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            messages = result.scalars().all()
            
            return list(messages), total
            
        except Exception as e:
            logger.error(f"[AI助手] 获取消息列表失败: {str(e)}")
            raise MyBaseException(f"获取消息列表失败: {str(e)}")
    
    @classmethod
    async def add_message(
        cls,
        db: AsyncSession,
        conversation_id: int,
        role: str,
        content: str
    ) -> AIMessage:
        """
        添加消息
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            role: 角色
            content: 内容
            
        Returns:
            创建的消息对象
        """
        try:
            message = AIMessage(
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            
            db.add(message)
            await db.commit()
            await db.refresh(message)
            
            return message
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[AI助手] 添加消息失败: {str(e)}")
            raise MyBaseException(f"添加消息失败: {str(e)}")


class DifyService:
    """Dify集成服务类"""
    
    @classmethod
    async def chat_with_dify(
        cls,
        config: AIAssistantConfig,
        request: DifyChatRequest
    ) -> DifyChatResponse:
        """
        与Dify进行聊天
        
        Args:
            config: AI助手配置
            request: 聊天请求
            
        Returns:
            Dify响应
        """
        try:
            headers = {
                "Authorization": f"Bearer {config.dify_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": {},
                "query": request.query,
                "response_mode": "blocking",
                "user": request.user
            }
            
            if request.conversation_id:
                payload["conversation_id"] = request.conversation_id
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{config.dify_base_url}/v1/chat-messages",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"[AI助手] Dify API调用失败: {response.status_code} {response.text}")
                    raise MyBaseException(f"AI服务调用失败: {response.status_code}")
                
                result = response.json()
                
                return DifyChatResponse(
                    answer=result.get("answer", ""),
                    conversation_id=result.get("conversation_id", ""),
                    message_id=result.get("message_id", "")
                )
                
        except httpx.TimeoutException:
            logger.error("[AI助手] Dify API调用超时")
            raise MyBaseException("AI服务调用超时")
        except Exception as e:
            logger.error(f"[AI助手] Dify API调用失败: {str(e)}")
            raise MyBaseException(f"AI服务调用失败: {str(e)}")
    
    @classmethod
    async def chat(
        cls,
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        query: str
    ) -> Dict[str, Any]:
        """
        完整的聊天流程
        
        Args:
            db: 数据库会话
            conversation_id: 对话ID
            user_id: 用户ID
            query: 用户问题
            
        Returns:
            聊天结果
        """
        try:
            # 获取对话信息
            conversation = await ConversationService.get_conversation_by_id(
                db, conversation_id, user_id
            )
            
            # 获取助手配置
            config = await AssistantConfigService.get_config_by_id(
                db, conversation.assistant_config_id
            )
            
            if not config.is_active:
                raise MyBaseException("AI助手已禁用")
            
            # 保存用户消息
            user_message = await MessageService.add_message(
                db, conversation_id, "user", query
            )
            
            # 调用Dify API
            dify_request = DifyChatRequest(
                query=query,
                conversation_id=conversation.conversation_id,
                user=f"user_{user_id}"
            )
            
            dify_response = await cls.chat_with_dify(config, dify_request)
            
            # 更新对话的Dify会话ID
            if not conversation.conversation_id and dify_response.conversation_id:
                conversation.conversation_id = dify_response.conversation_id
                await db.commit()
            
            # 保存AI回复
            ai_message = await MessageService.add_message(
                db, conversation_id, "assistant", dify_response.answer
            )
            
            return {
                "user_message": {
                    "id": user_message.id,
                    "content": user_message.content,
                    "created_at": user_message.created_at
                },
                "ai_message": {
                    "id": ai_message.id,
                    "content": ai_message.content,
                    "created_at": ai_message.created_at
                },
                "conversation_id": conversation.conversation_id
            }
            
        except Exception as e:
            logger.error(f"[AI助手] 聊天失败: {str(e)}")
            raise MyBaseException(f"聊天失败: {str(e)}")


class StatisticsService:
    """统计服务类"""
    
    @classmethod
    async def get_statistics(
        cls,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取AI助手统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            统计信息
        """
        try:
            # 总配置数
            total_configs_result = await db.execute(
                select(func.count(AIAssistantConfig.id))
            )
            total_configs = total_configs_result.scalar() or 0
            
            # 活跃配置数
            active_configs_result = await db.execute(
                select(func.count(AIAssistantConfig.id)).where(
                    AIAssistantConfig.is_active == True
                )
            )
            active_configs = active_configs_result.scalar() or 0
            
            # 总对话数
            total_conversations_result = await db.execute(
                select(func.count(AIConversation.id))
            )
            total_conversations = total_conversations_result.scalar() or 0
            
            # 总消息数
            total_messages_result = await db.execute(
                select(func.count(AIMessage.id))
            )
            total_messages = total_messages_result.scalar() or 0
            
            # 时间统计
            now = datetime.now()
            today = now.date()
            week_start = today - timedelta(days=today.weekday())
            month_start = today.replace(day=1)
            
            # 今日统计
            today_conversations_result = await db.execute(
                select(func.count(AIConversation.id)).where(
                    func.date(AIConversation.created_at) == today
                )
            )
            today_conversations = today_conversations_result.scalar() or 0
            
            # 本周统计
            week_conversations_result = await db.execute(
                select(func.count(AIConversation.id)).where(
                    func.date(AIConversation.created_at) >= week_start
                )
            )
            week_conversations = week_conversations_result.scalar() or 0
            
            # 本月统计
            month_conversations_result = await db.execute(
                select(func.count(AIConversation.id)).where(
                    func.date(AIConversation.created_at) >= month_start
                )
            )
            month_conversations = month_conversations_result.scalar() or 0
            
            # 助手类型分布
            type_distribution_result = await db.execute(
                select(
                    AIAssistantConfig.assistant_type,
                    func.count(AIAssistantConfig.id)
                ).group_by(AIAssistantConfig.assistant_type)
            )
            type_distribution = {}
            for row in type_distribution_result:
                type_distribution[row[0]] = row[1]
            
            # 配置详细统计
            config_stats_query = select(
                AIAssistantConfig.id,
                AIAssistantConfig.name,
                AIAssistantConfig.assistant_type,
                AIAssistantConfig.is_active,
                func.count(AIConversation.id).label('conversation_count'),
                func.count(AIMessage.id).label('message_count'),
                func.max(AIConversation.updated_at).label('last_used')
            ).select_from(
                AIAssistantConfig
            ).outerjoin(
                AIConversation, AIAssistantConfig.id == AIConversation.assistant_config_id
            ).outerjoin(
                AIMessage, AIConversation.id == AIMessage.conversation_id
            ).group_by(
                AIAssistantConfig.id,
                AIAssistantConfig.name,
                AIAssistantConfig.assistant_type,
                AIAssistantConfig.is_active
            )
            
            config_stats_result = await db.execute(config_stats_query)
            config_stats_data = []
            
            for row in config_stats_result:
                avg_messages = 0
                if row.conversation_count > 0 and row.message_count > 0:
                    avg_messages = row.message_count / row.conversation_count
                
                config_stats_data.append({
                    "config_id": row.id,
                    "config_name": row.name,
                    "config_type": row.assistant_type,
                    "is_active": row.is_active,
                    "conversation_count": row.conversation_count or 0,
                    "message_count": row.message_count or 0,
                    "avg_messages_per_conversation": avg_messages,
                    "last_used": row.last_used.isoformat() if row.last_used else None
                })
            
            # 每日消息统计（最近7天）
            daily_stats = []
            
            # 先检查是否有任何消息数据
            total_messages_check = await db.execute(
                select(func.count(AIMessage.id))
            )
            total_msg_count = total_messages_check.scalar() or 0
            logger.info(f"[AI助手] 数据库中总消息数: {total_msg_count}")
            
            for i in range(7):
                date = today - timedelta(days=i)
                daily_count_result = await db.execute(
                    select(func.count(AIMessage.id)).where(
                        func.date(AIMessage.created_at) == date
                    )
                )
                daily_count = daily_count_result.scalar() or 0
                daily_stats.append({
                    "date": date.strftime("%m-%d"),
                    "count": daily_count
                })
                logger.info(f"[AI助手] 日期 {date} 消息数量: {daily_count}")
            
            # 反转列表，使日期从早到晚排列
            daily_stats.reverse()
            
            logger.info(f"[AI助手] 最终每日统计数据: {daily_stats}")
            
            # 最近对话（包含助手配置信息）
            recent_conversations_query = select(AIConversation, AIAssistantConfig).join(
                AIAssistantConfig, AIConversation.assistant_config_id == AIAssistantConfig.id
            ).order_by(desc(AIConversation.updated_at)).limit(10)
            
            recent_conversations_result = await db.execute(recent_conversations_query)
            recent_conversations_data = []
            
            for conversation, config in recent_conversations_result:
                # 获取消息数量
                message_count_result = await db.execute(
                    select(func.count(AIMessage.id)).where(
                        AIMessage.conversation_id == conversation.id
                    )
                )
                message_count = message_count_result.scalar() or 0
                
                recent_conversations_data.append({
                    "id": conversation.id,
                    "title": conversation.title,
                    "assistant_name": config.name,
                    "message_count": message_count,
                    "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                    "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
                })
            
            return {
                "total_configs": total_configs,
                "active_configs": active_configs,
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "usage_stats": {
                    "today": today_conversations,
                    "this_week": week_conversations,
                    "this_month": month_conversations
                },
                "type_distribution": type_distribution,
                "config_type_distribution": type_distribution,  # 为统计页面提供
                "daily_message_count": daily_stats,
                "config_stats": config_stats_data,
                "recent_conversations": recent_conversations_data
            }
            
        except Exception as e:
            logger.error(f"[AI助手] 获取统计信息失败: {str(e)}")
            raise MyBaseException(f"获取统计信息失败: {str(e)}")