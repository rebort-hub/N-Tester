"""
对话管理服务
"""
import uuid
import json
import time
from typing import List, Optional, Dict, Any, Union
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.models.ai.conversation import ConversationModel
from app.models.ai.message import MessageModel
from app.models.ai.mcp_execution_record import MCPExecutionRecordModel
from app.services.ai.llm_service_langchain import get_llm_service, get_llm_service_by_id, LLMMessage
from app.api.v1.system.file.service import FileService
from app.api.v1.projects.project_platform_service import query_knowledge_base, mcp_list_tools, mcp_call_tool
from .schema import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
    SendMessageRequest
)


class ConversationService:
    """对话服务"""
    
    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: int,
        data: ConversationCreateRequest
    ) -> ConversationModel:
        """创建对话"""
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        # 创建对话
        conversation = ConversationModel(
            session_id=session_id,
            title=data.title or "新对话",
            llm_config_id=data.llm_config_id,
            user_id=user_id,
            is_active=1,
            created_by=user_id,
            updated_by=user_id
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    async def get_conversation_list(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[ConversationModel], int]:
        """获取对话列表"""
        # 查询总数
        count_stmt = select(func.count(ConversationModel.id)).where(
            ConversationModel.user_id == user_id,
            ConversationModel.enabled_flag == 1
        )
        result = await db.execute(count_stmt)
        total = result.scalar()
        
        # 查询列表
        stmt = select(ConversationModel).where(
            ConversationModel.user_id == user_id,
            ConversationModel.enabled_flag == 1
        ).order_by(desc(ConversationModel.updation_date)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        conversations = result.scalars().all()
        
        return conversations, total
    
    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int
    ) -> Optional[ConversationModel]:
        """获取对话详情"""
        stmt = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id,
            ConversationModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        data: ConversationUpdateRequest
    ) -> Optional[ConversationModel]:
        """更新对话"""
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return None
        
        # 更新字段
        if data.title is not None:
            conversation.title = data.title
        if data.llm_config_id is not None:
            conversation.llm_config_id = data.llm_config_id
        if data.is_active is not None:
            conversation.is_active = 1 if data.is_active else 0
        
        conversation.updated_by = user_id
        
        await db.commit()
        await db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        conversation_id: int,
        user_id: int
    ) -> bool:
        """删除对话（软删除）"""
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        
        conversation.enabled_flag = 0
        conversation.updated_by = user_id
        
        await db.commit()
        return True
    
    @staticmethod
    async def get_message_count(
        db: AsyncSession,
        conversation_id: int
    ) -> int:
        """获取对话消息数量"""
        stmt = select(func.count(MessageModel.id)).where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.enabled_flag == 1
        )
        result = await db.execute(stmt)
        return result.scalar()


class MessageService:
    """消息服务"""
    
    @staticmethod
    def _estimate_tokens(content: Union[str, List[Dict[str, Any]], Any]) -> int:
        """粗略 token 估算（约 1 token ≈ 4 chars）。"""
        if not content:
            return 0
        if isinstance(content, str):
            return max(1, len(content) // 4)
        if isinstance(content, list):
            merged_text = []
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") == "text":
                    merged_text.append(str(part.get("text") or ""))
                elif part.get("type") == "image_url":
                    merged_text.append(str((part.get("image_url") or {}).get("url") or ""))
            text = "\n".join(merged_text)
            return max(1, len(text) // 4) if text else 0
        text = str(content)
        return max(1, len(text) // 4) if text else 0

    @staticmethod
    def _build_multimodal_user_content(text: str, attachments: Optional[List[Dict[str, Any]]]) -> Union[str, List[Dict[str, Any]]]:
        if not MessageService._has_image_attachment(attachments):
            return text
        parts: List[Dict[str, Any]] = [{"type": "text", "text": text or ""}]
        for item in attachments or []:
            if not isinstance(item, dict):
                continue
            mime = str(item.get("mime_type") or item.get("content_type") or item.get("type") or "").lower()
            url = str(item.get("url") or item.get("file_url") or "").strip()
            if not url:
                continue
            if "image" in mime or url.lower().startswith("data:image/") or url.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")):
                parts.append({"type": "image_url", "image_url": {"url": url}})
        return parts if len(parts) > 1 else text

    @staticmethod
    def _has_image_attachment(attachments: Optional[List[Dict[str, Any]]]) -> bool:
        if not attachments:
            return False
        image_exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
        for item in attachments:
            if not isinstance(item, dict):
                continue
            mime = str(item.get("mime_type") or item.get("content_type") or "").lower()
            name = str(item.get("name") or item.get("filename") or "").lower()
            url = str(item.get("url") or item.get("file_url") or "").lower()
            typ = str(item.get("type") or "").lower()
            if "image" in mime or typ == "image":
                return True
            if name.endswith(image_exts) or url.endswith(image_exts):
                return True
            if url.startswith("data:image/"):
                return True
        return False

    @staticmethod
    def _apply_context_limit(
        llm_messages: List[LLMMessage],
        context_limit: int,
        max_tokens: int,
    ) -> List[LLMMessage]:
        if context_limit <= 0:
            return llm_messages
        # 预留输出预算，至少保留 512
        budget = max(512, context_limit - max(0, max_tokens))
        if budget <= 0:
            return llm_messages[-6:] if len(llm_messages) > 6 else llm_messages

        system_msgs = [m for m in llm_messages if m.role == "system"]
        non_system = [m for m in llm_messages if m.role != "system"]

        kept_rev: List[LLMMessage] = []
        used = 0
        for m in reversed(non_system):
            t = MessageService._estimate_tokens(m.content)
            if used + t > budget and kept_rev:
                break
            if used + t > budget and not kept_rev:
                # 至少保留最后一条用户消息
                kept_rev.append(m)
                break
            kept_rev.append(m)
            used += t

        kept_non_system = list(reversed(kept_rev))
        return [*system_msgs, *kept_non_system]

    @staticmethod
    def _apply_llm_runtime_controls(
        llm_messages: List[LLMMessage],
        llm_service: Any,
        data: SendMessageRequest,
    ) -> List[LLMMessage]:
        cfg = getattr(llm_service, "config", {}) or {}
        system_prompt = str(cfg.get("system_prompt") or "").strip()
        supports_vision = bool(cfg.get("supports_vision", False))
        context_limit = int(cfg.get("context_limit") or 0)
        max_tokens = int(cfg.get("max_tokens") or 2000)

        
        if MessageService._has_image_attachment(data.attachments) and not supports_vision:
            raise ValueError("当前 LLM 配置未开启多模态支持，无法处理图片附件")

        new_msgs = list(llm_messages)
        # 系统提示词注入（最高优先级）
        if system_prompt:
            new_msgs = [LLMMessage(role="system", content=system_prompt), *new_msgs]

        
        if supports_vision and MessageService._has_image_attachment(data.attachments):
            for idx in range(len(new_msgs) - 1, -1, -1):
                if new_msgs[idx].role == "user":
                    text = new_msgs[idx].content if isinstance(new_msgs[idx].content, str) else str(new_msgs[idx].content or "")
                    new_msgs[idx] = LLMMessage(
                        role="user",
                        content=MessageService._build_multimodal_user_content(text, data.attachments)
                    )
                    break

        
        new_msgs = MessageService._apply_context_limit(new_msgs, context_limit, max_tokens)
        return new_msgs

    @staticmethod
    def _kb_explicitly_enabled(data: SendMessageRequest) -> bool:
        return bool(
            data.use_knowledge_base
            and data.project_id
            and data.knowledge_base_id
        )

    @staticmethod
    def _attachment_storage_file_name(att: Dict[str, Any]) -> Optional[str]:
        url = str(att.get("url") or att.get("file_url") or "").strip()
        if not url:
            return None
        if url.startswith("database://"):
            return url.replace("database://", "", 1).split("?", 1)[0] or None
        if "/api/v1/system/file/content/" in url:
            return url.split("/api/v1/system/file/content/")[-1].split("?", 1)[0] or None
        if "/" not in url and "\\" not in url and ".." not in url:
            return url
        return None

    @staticmethod
    def _is_text_like_attachment(att: Dict[str, Any]) -> bool:
        typ = str(att.get("type") or "").lower()
        name = str(att.get("name") or "").lower()
        if typ.startswith("text/") or typ in ("application/json", "application/xml"):
            return True
        return name.endswith((".txt", ".md", ".csv", ".json", ".xml", ".log", ".yaml", ".yml"))

    @staticmethod
    async def _build_text_attachment_prompt(
        db: AsyncSession,
        user_id: int,
        attachments: Optional[List[Dict[str, Any]]],
    ) -> Optional[str]:
        if not attachments:
            return None
        chunks: List[str] = []
        max_each = 48 * 1024
        for att in attachments:
            if not isinstance(att, dict) or not MessageService._is_text_like_attachment(att):
                continue
            fname = MessageService._attachment_storage_file_name(att)
            if not fname:
                continue
            raw = await FileService.read_file_bytes_for_user(fname, user_id, db)
            if not raw:
                continue
            if len(raw) > max_each:
                raw = raw[:max_each]
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("utf-8", errors="replace")
            label = str(att.get("name") or fname)
            chunks.append(f"### 附件《{label}》全文\n{text}")
        if not chunks:
            return None
        return (
            "用户上传了以下文本类附件，请基于这些内容回答（若与问题无关可简要说明）。\n"
            + "\n\n".join(chunks)
        )
    
    @staticmethod
    async def get_message_list(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[MessageModel], int]:
        """获取消息列表"""
        # 验证对话权限
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return [], 0
        
        # 查询总数
        count_stmt = select(func.count(MessageModel.id)).where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.enabled_flag == 1
        )
        result = await db.execute(count_stmt)
        total = result.scalar()
        
        # 查询列表
        stmt = select(MessageModel).where(
            MessageModel.conversation_id == conversation_id,
            MessageModel.enabled_flag == 1
        ).order_by(MessageModel.creation_date).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        return messages, total
    
    @staticmethod
    async def create_message(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        role: str,
        content: str,
        message_type: str = "text",
        meta_data: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None
    ) -> MessageModel:
        """创建消息"""
        message = MessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            meta_data=meta_data,
            tokens_used=tokens_used,
            created_by=user_id,
            updated_by=user_id
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        return message
    
    @staticmethod
    async def _record_mcp_execution(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        data: SendMessageRequest,
        *,
        phase: str,
        status: str,
        tool_name: Optional[str] = None,
        tool_arguments: Optional[Dict[str, Any]] = None,
        output_summary: Optional[str] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> None:
        try:
            rec = MCPExecutionRecordModel(
                conversation_id=conversation_id,
                user_id=user_id,
                project_id=data.project_id,
                knowledge_base_id=data.knowledge_base_id,
                mcp_config_id=data.mcp_config_id,
                phase=phase,
                tool_name=tool_name,
                tool_arguments=tool_arguments,
                status=status,
                duration_ms=duration_ms,
                output_summary=output_summary,
                error_message=error_message,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(rec)
            await db.commit()
        except Exception:
            await db.rollback()

    @staticmethod
    async def _build_rag_system_prompt(
        db: AsyncSession,
        user_id: int,
        data: SendMessageRequest,
    ) -> tuple[Optional[str], str]:
        if not MessageService._kb_explicitly_enabled(data):
            return None, "知识库未开启"
        try:
            rag = await query_knowledge_base(
                project_id=int(data.project_id),
                user_id=user_id,
                kb_id=int(data.knowledge_base_id),
                db=db,
                query=data.content,
                top_k=5,
            )
            results = ((rag or {}).get("data") or {}).get("results") or []
            if not results:
                return (
                    "当前已启用知识库检索，但未检索到相关片段。请明确告诉用户“本次未命中知识库内容”，不要虚构来源。",
                    "知识库已检索但无命中",
                )
            refs = []
            for idx, item in enumerate(results[:5], start=1):
                title = ((item.get("metadata") or {}).get("document_title") or "").strip() or f"片段{idx}"
                content = (item.get("content") or "").strip()
                if content:
                    refs.append(f"[{idx}] {title}\n{content}")
            if not refs:
                return (
                    "当前已启用知识库检索，但未检索到可用片段。请明确告知用户本次未命中知识库内容。",
                    "知识库结果为空",
                )
            return (
                "你可以参考以下知识库检索片段回答用户问题。若片段不足以支持结论，请明确说明。\n\n"
                + "\n\n".join(refs)
            ), f"知识库命中 {len(refs)} 条片段"
        except Exception as e:
            return (
                "当前已启用知识库检索，但检索过程出现异常。请明确告诉用户“知识库检索失败，已退回基础回答”。",
                f"知识库检索异常: {e}",
            )

    @staticmethod
    async def _run_mcp_chain(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        data: SendMessageRequest,
        llm_messages: List[LLMMessage],
    ) -> tuple[Optional[str], str]:
        if not (data.use_mcp and data.project_id and data.mcp_config_id):
            return None, "MCP未开启"
        start_ms = int(time.time() * 1000)
        try:
            tools_res = await mcp_list_tools(
                project_id=int(data.project_id),
                user_id=user_id,
                config_id=int(data.mcp_config_id),
                db=db,
            )
            tools = ((tools_res or {}).get("data") or {}).get("tools") or []
            if not tools:
                await MessageService._record_mcp_execution(
                    db,
                    conversation_id,
                    user_id,
                    data,
                    phase="tool_list",
                    status="failed",
                    error_message=f"MCP工具列表为空: {(tools_res or {}).get('message') or '未知原因'}",
                    duration_ms=int(time.time() * 1000) - start_ms,
                )
                return None, f"MCP工具列表为空: {(tools_res or {}).get('message') or '未知原因'}"

            tool_descriptions = []
            for t in tools[:20]:
                tool_descriptions.append(f"- {t.get('name')}: {t.get('description') or ''}")
            planner_prompt = (
                "你是工具路由器。基于用户问题与工具列表，判断是否需要调用工具。"
                "仅输出 JSON，不要输出其他文本。\n"
                "格式: {\"use_tool\": true|false, \"tool_name\": \"...\", \"arguments\": {...}}\n"
                "若不需要工具，输出 {\"use_tool\": false, \"tool_name\": \"\", \"arguments\": {}}\n\n"
                f"工具列表:\n{chr(10).join(tool_descriptions)}\n\n"
                f"用户问题:\n{data.content}"
            )

            if llm_messages and llm_messages[-1].role == "user":
                llm_messages[-1] = LLMMessage(role="user", content=planner_prompt)
            else:
                llm_messages.append(LLMMessage(role="user", content=planner_prompt))

            llm_service = await get_llm_service()
            plan_resp = await llm_service.chat_completion(messages=llm_messages, stream=False)
            raw = (plan_resp.content or "").strip()
            if raw.startswith("```"):
                raw = raw.strip("`")
                raw = raw.replace("json", "", 1).strip()

            try:
                plan = json.loads(raw)
            except Exception:
                l = raw.find("{")
                r = raw.rfind("}")
                if l >= 0 and r > l:
                    plan = json.loads(raw[l : r + 1])
                else:
                    await MessageService._record_mcp_execution(
                        db,
                        conversation_id,
                        user_id,
                        data,
                        phase="auto_plan",
                        status="failed",
                        error_message=f"MCP规划结果无法解析: {raw[:300]}",
                        duration_ms=int(time.time() * 1000) - start_ms,
                    )
                    return None, f"MCP规划结果无法解析: {raw[:160]}"
            if not plan.get("use_tool"):
                await MessageService._record_mcp_execution(
                    db,
                    conversation_id,
                    user_id,
                    data,
                    phase="auto_plan",
                    status="skipped",
                    output_summary="模型判定无需调用工具",
                    duration_ms=int(time.time() * 1000) - start_ms,
                )
                return None, "MCP规划判定无需调用工具"

            tool_name = (plan.get("tool_name") or "").strip()
            args = plan.get("arguments") or {}
            if not tool_name:
                await MessageService._record_mcp_execution(
                    db,
                    conversation_id,
                    user_id,
                    data,
                    phase="auto_plan",
                    status="failed",
                    error_message="规划未返回工具名",
                    duration_ms=int(time.time() * 1000) - start_ms,
                )
                return None, "MCP规划未返回工具名"

            call_res = await mcp_call_tool(
                project_id=int(data.project_id),
                user_id=user_id,
                config_id=int(data.mcp_config_id),
                db=db,
                tool_name=tool_name,
                arguments=args if isinstance(args, dict) else {},
            )
            if (call_res or {}).get("code") != 200:
                await MessageService._record_mcp_execution(
                    db,
                    conversation_id,
                    user_id,
                    data,
                    phase="tool_call",
                    status="failed",
                    tool_name=tool_name,
                    tool_arguments=args if isinstance(args, dict) else {},
                    error_message=(call_res or {}).get("message") or "未知错误",
                    duration_ms=int(time.time() * 1000) - start_ms,
                )
                return None, f"MCP工具调用失败: {(call_res or {}).get('message') or '未知错误'}"
            result = ((call_res or {}).get("data") or {}).get("result")
            await MessageService._record_mcp_execution(
                db,
                conversation_id,
                user_id,
                data,
                phase="tool_call",
                status="success",
                tool_name=tool_name,
                tool_arguments=args if isinstance(args, dict) else {},
                output_summary=str(result)[:2000],
                duration_ms=int(time.time() * 1000) - start_ms,
            )
            return f"已调用 MCP 工具 `{tool_name}`，返回结果:\n{result}", f"MCP已调用工具: {tool_name}"
        except Exception as e:
            await MessageService._record_mcp_execution(
                db,
                conversation_id,
                user_id,
                data,
                phase="tool_call",
                status="failed",
                error_message=str(e),
                duration_ms=int(time.time() * 1000) - start_ms,
            )
            return None, f"MCP链路异常: {e}"

    @staticmethod
    async def send_message(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        data: SendMessageRequest
    ) -> tuple[MessageModel, MessageModel, Optional[int]]:
        """发送消息并获取AI响应"""
        # 验证对话权限
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")
        
        # 1. 保存用户消息
        user_message = await MessageService.create_message(
            db,
            conversation_id,
            user_id,
            "user",
            data.content,
            meta_data={"attachments": data.attachments} if data.attachments else None,
        )
        
        # 2. 获取对话历史
        messages, _ = await MessageService.get_message_list(db, conversation_id, user_id, limit=50)
        
        # 3. 构建LLM消息列表
        llm_messages = []
        if not MessageService._kb_explicitly_enabled(data):
            llm_messages.append(
                LLMMessage(
                    role="system",
                    content="未启用知识库检索。请仅根据用户消息与下方附件内容回答，不要提及知识库命中、未命中、检索失败或知识库状态。",
                )
            )
        text_att = await MessageService._build_text_attachment_prompt(db, user_id, data.attachments)
        if text_att:
            llm_messages.append(LLMMessage(role="system", content=text_att))
        rag_prompt, rag_status = await MessageService._build_rag_system_prompt(db, user_id, data)
        if rag_prompt:
            llm_messages.append(LLMMessage(role="system", content=rag_prompt))
        if MessageService._kb_explicitly_enabled(data):
            llm_messages.append(LLMMessage(role="system", content=f"[知识库状态]{rag_status}"))
        for msg in messages:
            llm_messages.append(LLMMessage(role=msg.role, content=msg.content))

        mcp_result, mcp_status = await MessageService._run_mcp_chain(db, conversation_id, user_id, data, llm_messages.copy())
        if mcp_result:
            llm_messages.append(LLMMessage(role="system", content=mcp_result))
        if data.use_mcp:
            llm_messages.append(LLMMessage(role="system", content=f"[MCP状态]{mcp_status}"))
        
        # 4. 调用LLM服务
        if conversation.llm_config_id:
            llm_service = await get_llm_service_by_id(conversation.llm_config_id)
        else:
            llm_service = await get_llm_service()
        llm_messages = MessageService._apply_llm_runtime_controls(llm_messages, llm_service, data)
        
        response = await llm_service.chat_completion(
            messages=llm_messages,
            stream=False
        )
        
        # 5. 保存AI响应
        assistant_message = await MessageService.create_message(
            db,
            conversation_id,
            user_id,
            "assistant",
            response.content,
            tokens_used=response.total_tokens
        )
        
        # 6. 更新对话标题（如果是第一条消息）
        if not conversation.title or conversation.title == "新对话":
            # 使用用户第一条消息的前30个字符作为标题
            conversation.title = data.content[:30] + ("..." if len(data.content) > 30 else "")
            conversation.updated_by = user_id
            await db.commit()
        
        return user_message, assistant_message, response.total_tokens
    
    @staticmethod
    async def send_message_stream(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        data: SendMessageRequest
    ):
        """发送消息并获取AI流式响应（生成器）"""
        # 验证对话权限
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")
        
        # 1. 保存用户消息
        user_message = await MessageService.create_message(
            db,
            conversation_id,
            user_id,
            "user",
            data.content,
            meta_data={"attachments": data.attachments} if data.attachments else None,
        )
        
        # 发送用户消息事件
        yield {
            "type": "user_message",
            "data": {
                "id": user_message.id,
                "role": "user",
                "content": user_message.content,
                "creation_date": user_message.creation_date.isoformat()
            }
        }
        
        # 2. 获取对话历史
        messages, _ = await MessageService.get_message_list(db, conversation_id, user_id, limit=50)
        
        # 3. 构建LLM消息列表
        llm_messages = []
        if not MessageService._kb_explicitly_enabled(data):
            llm_messages.append(
                LLMMessage(
                    role="system",
                    content="未启用知识库检索。请仅根据用户消息与下方附件内容回答，不要提及知识库命中、未命中、检索失败或知识库状态。",
                )
            )
        text_att = await MessageService._build_text_attachment_prompt(db, user_id, data.attachments)
        if text_att:
            llm_messages.append(LLMMessage(role="system", content=text_att))
        rag_prompt, rag_status = await MessageService._build_rag_system_prompt(db, user_id, data)
        if rag_prompt:
            llm_messages.append(LLMMessage(role="system", content=rag_prompt))
        if MessageService._kb_explicitly_enabled(data):
            llm_messages.append(LLMMessage(role="system", content=f"[知识库状态]{rag_status}"))
        for msg in messages:
            llm_messages.append(LLMMessage(role=msg.role, content=msg.content))

        mcp_result, mcp_status = await MessageService._run_mcp_chain(db, conversation_id, user_id, data, llm_messages.copy())
        if mcp_result:
            llm_messages.append(LLMMessage(role="system", content=mcp_result))
        if data.use_mcp:
            llm_messages.append(LLMMessage(role="system", content=f"[MCP状态]{mcp_status}"))
        
        # 4. 调用LLM服务（流式）
        if conversation.llm_config_id:
            llm_service = await get_llm_service_by_id(conversation.llm_config_id)
        else:
            llm_service = await get_llm_service()
        llm_messages = MessageService._apply_llm_runtime_controls(llm_messages, llm_service, data)
        
        # 收集完整的响应内容
        full_content = ""
        
        # 流式获取响应；若模型未返回 chunk（部分兼容模型常见），自动降级到非流式
        got_chunk = False
        try:
            stream = await llm_service.chat_completion(
                messages=llm_messages,
                stream=True
            )
            async for chunk in stream:
                if not chunk:
                    continue
                got_chunk = True
                full_content += chunk
                # 发送内容块事件
                yield {
                    "type": "content",
                    "data": {
                        "content": chunk
                    }
                }
        except Exception:
            got_chunk = False

        if not got_chunk:
            fallback_resp = await llm_service.chat_completion(
                messages=llm_messages,
                stream=False
            )
            full_content = (fallback_resp.content or "").strip()
            if full_content:
                yield {
                    "type": "content",
                    "data": {
                        "content": full_content
                    }
                }

        # 5. 保存AI响应
        assistant_message = await MessageService.create_message(
            db,
            conversation_id,
            user_id,
            "assistant",
            full_content,
            tokens_used=len(full_content)  # 简单估算，实际应该从LLM响应中获取
        )
        
        # 发送完成事件
        yield {
            "type": "assistant_message",
            "data": {
                "id": assistant_message.id,
                "role": "assistant",
                "content": assistant_message.content,
                "tokens_used": assistant_message.tokens_used,
                "creation_date": assistant_message.creation_date.isoformat()
            }
        }
        
        # 6. 更新对话标题（如果是第一条消息）
        if not conversation.title or conversation.title == "新对话":
            conversation.title = data.content[:30] + ("..." if len(data.content) > 30 else "")
            conversation.updated_by = user_id
            await db.commit()

    @staticmethod
    async def get_mcp_execution_records(
        db: AsyncSession,
        conversation_id: int,
        user_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        conversation = await ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return []
        stmt = (
            select(MCPExecutionRecordModel)
            .where(
                MCPExecutionRecordModel.conversation_id == conversation_id,
                MCPExecutionRecordModel.user_id == user_id,
                MCPExecutionRecordModel.enabled_flag == 1,
            )
            .order_by(desc(MCPExecutionRecordModel.creation_date))
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [
            {
                "id": r.id,
                "phase": r.phase,
                "status": r.status,
                "tool_name": r.tool_name,
                "tool_arguments": r.tool_arguments,
                "output_summary": r.output_summary,
                "error_message": r.error_message,
                "duration_ms": r.duration_ms,
                "creation_date": r.creation_date,
            }
            for r in rows
        ]

