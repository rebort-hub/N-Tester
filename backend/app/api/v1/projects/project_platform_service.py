# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import os
import re
import secrets
import uuid
from pathlib import Path
from typing import Any, List, Optional, Tuple
import httpx
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.projects.model import (
    KnowledgeBaseModel,
    KnowledgeDocumentModel,
    KnowledgeGlobalConfigModel,
    ProjectApiKeyModel,
    ProjectMCPConfigModel,
    ProjectModel,
)
from app.api.v1.projects.service import ProjectService
from app.api.v1.ai.knowledge_config.service import KnowledgeConfigService
from app.common.response import page_response, success_response, error_response


UPLOAD_ROOT = Path(os.getenv("KNOWLEDGE_UPLOAD_DIR", "uploads/knowledge"))


async def _check_member(project_id: int, user_id: int, db: AsyncSession) -> None:
    await ProjectService._check_project_member(project_id, user_id, db)  # noqa: SLF001


async def _check_role(project_id: int, user_id: int, roles: List[str], db: AsyncSession) -> None:
    await ProjectService._check_project_permission(project_id, user_id, roles, db)  # noqa: SLF001


def _iso(dt) -> Optional[str]:
    if not dt:
        return None
    return dt.isoformat() if hasattr(dt, "isoformat") else str(dt)


async def _get_project(project_id: int, db: AsyncSession) -> ProjectModel:
    stmt = select(ProjectModel).where(ProjectModel.id == project_id, ProjectModel.enabled_flag == 1)
    r = await db.execute(stmt)
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")
    return p


# ---------- MCP 配置 ----------


async def list_mcp_configs(
    project_id: int,
    user_id: int,
    db: AsyncSession,
    search: str = "",
    is_enabled: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    await _check_member(project_id, user_id, db)
    q = select(ProjectMCPConfigModel).where(
        ProjectMCPConfigModel.user_id == user_id,
        ProjectMCPConfigModel.enabled_flag == 1,
    )
    if search:
        q = q.where(ProjectMCPConfigModel.name.contains(search))
    if is_enabled is not None:
        q = q.where(ProjectMCPConfigModel.is_enabled == is_enabled)

    count_stmt = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    q = q.order_by(ProjectMCPConfigModel.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = []
    for c in rows:
        items.append(
            {
                "id": c.id,
                "name": c.name,
                "url": c.url,
                "transport": c.transport,
                "headers": c.headers or {},
                "is_enabled": c.is_enabled,
                "created_at": _iso(c.creation_date),
            }
        )
    return page_response(items, total, page, page_size, "查询成功")


async def create_mcp_config(project_id: int, user_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="配置名称不能为空")
    exists = await db.execute(
        select(ProjectMCPConfigModel.id).where(
            ProjectMCPConfigModel.user_id == user_id,
            ProjectMCPConfigModel.name == name,
            ProjectMCPConfigModel.enabled_flag == 1,
        )
    )
    if exists.scalar():
        raise HTTPException(status_code=400, detail="MCP 配置名称已存在")

    m = ProjectMCPConfigModel(
        user_id=user_id,
        name=name,
        url=data.get("url", "").strip(),
        transport=data.get("transport") or "streamable-http",
        headers=data.get("headers") or {},
        is_enabled=data.get("is_enabled", True),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return success_response(
        data={
            "id": m.id,
            "name": m.name,
            "url": m.url,
            "transport": m.transport,
            "headers": m.headers or {},
            "is_enabled": m.is_enabled,
            "created_at": _iso(m.creation_date),
        },
        message="创建成功",
    )


async def update_mcp_config(project_id: int, user_id: int, config_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    stmt = select(ProjectMCPConfigModel).where(
        ProjectMCPConfigModel.id == config_id,
        ProjectMCPConfigModel.user_id == user_id,
        ProjectMCPConfigModel.enabled_flag == 1,
    )
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")

    if data.get("name"):
        dup = await db.execute(
            select(ProjectMCPConfigModel.id).where(
                ProjectMCPConfigModel.user_id == user_id,
                ProjectMCPConfigModel.name == data["name"],
                ProjectMCPConfigModel.id != config_id,
                ProjectMCPConfigModel.enabled_flag == 1,
            )
        )
        if dup.scalar():
            raise HTTPException(status_code=400, detail="MCP 配置名称已存在")
        c.name = data["name"]
    if data.get("url") is not None:
        c.url = data["url"]
    if data.get("transport") is not None:
        c.transport = data["transport"]
    if data.get("headers") is not None:
        c.headers = data["headers"]
    if data.get("is_enabled") is not None:
        c.is_enabled = data["is_enabled"]
    c.updated_by = user_id
    await db.commit()
    await db.refresh(c)
    return success_response(
        data={
            "id": c.id,
            "name": c.name,
            "url": c.url,
            "transport": c.transport,
            "headers": c.headers or {},
            "is_enabled": c.is_enabled,
            "created_at": _iso(c.creation_date),
        },
        message="更新成功",
    )


async def delete_mcp_config(project_id: int, user_id: int, config_id: int, db: AsyncSession) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    stmt = select(ProjectMCPConfigModel).where(
        ProjectMCPConfigModel.id == config_id,
        ProjectMCPConfigModel.user_id == user_id,
        ProjectMCPConfigModel.enabled_flag == 1,
    )
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    c.enabled_flag = 0
    c.updated_by = user_id
    await db.commit()
    return success_response(message="删除成功")


async def test_mcp_config(project_id: int, user_id: int, config_id: int, db: AsyncSession) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(ProjectMCPConfigModel).where(
        ProjectMCPConfigModel.id == config_id,
        ProjectMCPConfigModel.user_id == user_id,
        ProjectMCPConfigModel.enabled_flag == 1,
    )
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    try:
        tools = await mcp_list_tools(project_id, user_id, config_id, db)
        if tools.get("code") == 200:
            return success_response(
                data={"ok": True, "tools_count": len((tools.get("data") or {}).get("tools") or [])},
                message="连接成功",
            )
        return tools
    except Exception as e:
        return error_response(message=f"连接失败: {e}")


async def _get_mcp_config(project_id: int, user_id: int, config_id: int, db: AsyncSession) -> ProjectMCPConfigModel:
    await _check_member(project_id, user_id, db)
    stmt = select(ProjectMCPConfigModel).where(
        ProjectMCPConfigModel.id == config_id,
        ProjectMCPConfigModel.user_id == user_id,
        ProjectMCPConfigModel.enabled_flag == 1,
    )
    c = (await db.execute(stmt)).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="MCP 配置不存在")
    return c


def _build_server_config(c: ProjectMCPConfigModel) -> dict:
    name = c.name or f"mcp-{c.id}"
    transport = (c.transport or "streamable-http").strip()
    
    if transport.lower() == "streamable-http":
        transport = "streamable_http"
    cfg = {
        name: {
            "transport": transport,
            "url": c.url,
        }
    }
    if c.headers and isinstance(c.headers, dict):
        cfg[name]["headers"] = c.headers
    return cfg, name


async def mcp_list_tools(project_id: int, user_id: int, config_id: int, db: AsyncSession) -> dict:
    c = await _get_mcp_config(project_id, user_id, config_id, db)
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except Exception as e:
        return error_response(message=f"缺少依赖 langchain-mcp-adapters: {e}")

    server_config, server_name = _build_server_config(c)
    try:
        client = MultiServerMCPClient(server_config)
        async with client.session(server_name) as session:
            tools_resp = await session.list_tools()
            remote_tools = tools_resp.tools if hasattr(tools_resp, "tools") else []
        items = []
        for t in remote_tools or []:
            items.append(
                {
                    "name": getattr(t, "name", ""),
                    "description": getattr(t, "description", "") or "",
                    "input_schema": getattr(t, "inputSchema", {}) or {},
                }
            )
        return success_response(data={"tools": items}, message="查询成功")
    except Exception as e:
        return error_response(message=f"获取工具列表失败: {e}")


async def mcp_call_tool(project_id: int, user_id: int, config_id: int, db: AsyncSession, tool_name: str, arguments: dict) -> dict:
    c = await _get_mcp_config(project_id, user_id, config_id, db)
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langchain_mcp_adapters.tools import load_mcp_tools
    except Exception as e:
        return error_response(message=f"缺少依赖 langchain-mcp-adapters: {e}")

    server_config, server_name = _build_server_config(c)
    try:
        client = MultiServerMCPClient(server_config)
        async with client.session(server_name) as session:
            tools = await load_mcp_tools(session)
            target = None
            for tool in tools:
                if getattr(tool, "name", None) == tool_name:
                    target = tool
                    break
            if not target:
                return error_response(message=f"工具不存在: {tool_name}")
            # langchain tools: invoke/ainvoke
            if hasattr(target, "ainvoke"):
                result = await target.ainvoke(arguments or {})
            else:
                result = target.invoke(arguments or {})
        return success_response(data={"result": result}, message="调用成功")
    except Exception as e:
        return error_response(message=f"调用失败: {e}")
    except Exception as e:
        return success_response(data={"ok": False, "reachable": False, "error": str(e)}, message="连接失败")


# ---------- API 密钥 ----------


async def list_api_keys(
    project_id: int,
    user_id: int,
    db: AsyncSession,
    search: str = "",
    service_type: str = "",
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    await _check_member(project_id, user_id, db)
    q = select(ProjectApiKeyModel).where(
        ProjectApiKeyModel.user_id == user_id,
        ProjectApiKeyModel.enabled_flag == 1,
    )
    if search:
        q = q.where(ProjectApiKeyModel.name.contains(search))
    if service_type:
        q = q.where(ProjectApiKeyModel.service_type == service_type)
    if is_active is not None:
        q = q.where(ProjectApiKeyModel.is_active == is_active)

    count_stmt = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    q = q.order_by(ProjectApiKeyModel.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = []
    for k in rows:
        items.append(
            {
                "id": k.id,
                "name": k.name,
                "service_type": k.service_type,
                "api_key": k.key_value,
                "description": k.description,
                "is_active": k.is_active,
                "created_at": _iso(k.creation_date),
            }
        )
    return page_response(items, total, page, page_size, "查询成功")


async def create_api_key(project_id: int, user_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="密钥名称不能为空")
    exists = await db.execute(
        select(ProjectApiKeyModel.id).where(
            ProjectApiKeyModel.user_id == user_id,
            ProjectApiKeyModel.name == name,
            ProjectApiKeyModel.enabled_flag == 1,
        )
    )
    if exists.scalar():
        raise HTTPException(status_code=400, detail="API 密钥名称已存在")

    k = ProjectApiKeyModel(
        user_id=user_id,
        name=name,
        service_type=data.get("service_type") or "openai",
        key_value=data.get("api_key") or "",
        description=data.get("description"),
        is_active=data.get("is_active", True),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(k)
    await db.commit()
    await db.refresh(k)
    return success_response(
        data={
            "id": k.id,
            "name": k.name,
            "service_type": k.service_type,
            "api_key": k.key_value,
            "description": k.description,
            "is_active": k.is_active,
            "created_at": _iso(k.creation_date),
        },
        message="创建成功",
    )


async def update_api_key(project_id: int, user_id: int, key_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    stmt = select(ProjectApiKeyModel).where(
        ProjectApiKeyModel.id == key_id,
        ProjectApiKeyModel.user_id == user_id,
        ProjectApiKeyModel.enabled_flag == 1,
    )
    k = (await db.execute(stmt)).scalar_one_or_none()
    if not k:
        raise HTTPException(status_code=404, detail="API 密钥不存在")

    if data.get("name"):
        dup = await db.execute(
            select(ProjectApiKeyModel.id).where(
                ProjectApiKeyModel.user_id == user_id,
                ProjectApiKeyModel.name == data["name"],
                ProjectApiKeyModel.id != key_id,
                ProjectApiKeyModel.enabled_flag == 1,
            )
        )
        if dup.scalar():
            raise HTTPException(status_code=400, detail="API 密钥名称已存在")
        k.name = data["name"]
    if data.get("service_type") is not None:
        k.service_type = data["service_type"]
    if data.get("api_key") is not None:
        k.key_value = data["api_key"]
    if data.get("description") is not None:
        k.description = data["description"]
    if data.get("is_active") is not None:
        k.is_active = data["is_active"]
    k.updated_by = user_id
    await db.commit()
    await db.refresh(k)
    return success_response(
        data={
            "id": k.id,
            "name": k.name,
            "service_type": k.service_type,
            "api_key": k.key_value,
            "description": k.description,
            "is_active": k.is_active,
            "created_at": _iso(k.creation_date),
        },
        message="更新成功",
    )


async def delete_api_key(project_id: int, user_id: int, key_id: int, db: AsyncSession) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    stmt = select(ProjectApiKeyModel).where(
        ProjectApiKeyModel.id == key_id,
        ProjectApiKeyModel.user_id == user_id,
        ProjectApiKeyModel.enabled_flag == 1,
    )
    k = (await db.execute(stmt)).scalar_one_or_none()
    if not k:
        raise HTTPException(status_code=404, detail="API 密钥不存在")
    k.enabled_flag = 0
    k.updated_by = user_id
    await db.commit()
    return success_response(message="删除成功")


async def test_api_key(project_id: int, user_id: int, key_id: int, db: AsyncSession) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(ProjectApiKeyModel).where(
        ProjectApiKeyModel.id == key_id,
        ProjectApiKeyModel.user_id == user_id,
        ProjectApiKeyModel.enabled_flag == 1,
    )
    k = (await db.execute(stmt)).scalar_one_or_none()
    if not k:
        raise HTTPException(status_code=404, detail="API 密钥不存在")

    st = (k.service_type or "").lower()
    api_key_val = k.key_value or ""
    try:
        if st in ("openai", "qwen", "gemini"):
            base = "https://api.openai.com/v1"
            if st == "qwen":
                base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
            elif st == "gemini":
                base = "https://generativelanguage.googleapis.com/v1beta"
            headers = {"Authorization": f"Bearer {api_key_val}"}
            url = f"{base}/models" if st != "gemini" else f"{base}/models?key={api_key_val}"
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(url, headers=headers if st != "gemini" else {})
            ok = r.status_code < 400
            return success_response(
                data={"ok": ok, "status_code": r.status_code},
                message="测试成功" if ok else "测试失败",
            )
        if st == "claude":
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key_val,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={"model": "claude-3-haiku-20240307", "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]},
                )
            ok = r.status_code < 400
            return success_response(data={"ok": ok, "status_code": r.status_code}, message="测试完成")
        # 其他：仅校验非空
        ok = bool(api_key_val)
        return success_response(data={"ok": ok, "note": "未内置该服务类型的在线探测，仅校验密钥非空"}, message="测试完成")
    except Exception as e:
        return success_response(data={"ok": False, "error": str(e)}, message="测试失败")


async def regenerate_api_key(project_id: int, user_id: int, key_id: int, db: AsyncSession) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    stmt = select(ProjectApiKeyModel).where(
        ProjectApiKeyModel.id == key_id,
        ProjectApiKeyModel.user_id == user_id,
        ProjectApiKeyModel.enabled_flag == 1,
    )
    k = (await db.execute(stmt)).scalar_one_or_none()
    if not k:
        raise HTTPException(status_code=404, detail="API 密钥不存在")
    prefix = {
        "openai": "sk-",
        "claude": "sk-ant-",
        "gemini": "AIza",
        "qwen": "sk-",
        "github": "ghp_",
    }.get(k.service_type.lower(), "key-")
    k.key_value = prefix + secrets.token_hex(16)
    k.updated_by = user_id
    await db.commit()
    await db.refresh(k)
    return success_response(
        data={
            "id": k.id,
            "api_key": k.key_value,
        },
        message="已重新生成",
    )


# ---------- 知识库 ----------


async def get_knowledge_global_config(project_id: int, user_id: int, db: AsyncSession) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(KnowledgeGlobalConfigModel).where(
        KnowledgeGlobalConfigModel.user_id == user_id,
        KnowledgeGlobalConfigModel.enabled_flag == 1,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        return success_response(
            data={
                "embedding_service": "openai",
                "api_base_url": "",
                "api_key": "",
                "model_name": "text-embedding-3-small",
                "chunk_size": 1000,
                "chunk_overlap": 200,
            },
            message="查询成功",
        )
    return success_response(
        data={
            "id": row.id,
            "embedding_service": row.embedding_service,
            "api_base_url": row.api_base_url or "",
            "api_key": row.api_key or "",
            "model_name": row.model_name,
            "chunk_size": row.chunk_size,
            "chunk_overlap": row.chunk_overlap,
            "updated_at": _iso(row.updation_date),
        },
        message="查询成功",
    )


async def update_knowledge_global_config(project_id: int, user_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin", "developer"], db)
    stmt = select(KnowledgeGlobalConfigModel).where(
        KnowledgeGlobalConfigModel.user_id == user_id,
        KnowledgeGlobalConfigModel.enabled_flag == 1,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if not row:
        row = KnowledgeGlobalConfigModel(
            user_id=user_id,
            embedding_service=data.get("embedding_service") or "openai",
            api_base_url=data.get("api_base_url"),
            api_key=data.get("api_key"),
            model_name=data.get("model_name") or "text-embedding-3-small",
            chunk_size=int(data.get("chunk_size") or 1000),
            chunk_overlap=int(data.get("chunk_overlap") or 200),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(row)
    else:
        if data.get("embedding_service") is not None:
            row.embedding_service = data["embedding_service"]
        if data.get("api_base_url") is not None:
            row.api_base_url = data["api_base_url"]
        if data.get("api_key") is not None:
            row.api_key = data["api_key"]
        if data.get("model_name") is not None:
            row.model_name = data["model_name"]
        if data.get("chunk_size") is not None:
            row.chunk_size = int(data["chunk_size"])
        if data.get("chunk_overlap") is not None:
            row.chunk_overlap = int(data["chunk_overlap"])
        row.updated_by = user_id
    await db.commit()
    await db.refresh(row)
    return success_response(data={"id": row.id}, message="保存成功")


async def test_embedding_connection(project_id: int, user_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_member(project_id, user_id, db)
    base = (data.get("api_base_url") or "").strip().rstrip("/")
    key = (data.get("api_key") or "").strip()
    model = (data.get("model_name") or "text-embedding-3-small").strip()
    if not key:
        raise HTTPException(status_code=400, detail="请填写 API Key")
    url = f"{base}/embeddings" if base else "https://api.openai.com/v1/embeddings"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": model, "input": "ping"},
            )
        ok = r.status_code < 400
        return success_response(
            data={"ok": ok, "status_code": r.status_code},
            message="连接成功" if ok else "连接失败",
        )
    except Exception as e:
        return success_response(data={"ok": False, "error": str(e)}, message="连接失败")


async def list_knowledge_bases(
    project_id: int,
    user_id: int,
    db: AsyncSession,
    search: str = "",
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    await _get_project(project_id, db)
    await _check_member(project_id, user_id, db)

    q = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    if search:
        q = q.where(
            or_(
                KnowledgeBaseModel.name.contains(search),
                KnowledgeBaseModel.description.contains(search),
            )
        )
    if is_active is not None:
        q = q.where(KnowledgeBaseModel.is_active == is_active)

    count_stmt = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    q = q.order_by(KnowledgeBaseModel.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()

    items = []
    for kb in rows:
        doc_cnt = (
            await db.execute(
                select(func.count())
                .select_from(KnowledgeDocumentModel)
                .where(
                    KnowledgeDocumentModel.knowledge_base_id == kb.id,
                    KnowledgeDocumentModel.enabled_flag == 1,
                )
            )
        ).scalar() or 0
        completed = (
            await db.execute(
                select(func.count())
                .select_from(KnowledgeDocumentModel)
                .where(
                    KnowledgeDocumentModel.knowledge_base_id == kb.id,
                    KnowledgeDocumentModel.enabled_flag == 1,
                    KnowledgeDocumentModel.status == "completed",
                )
            )
        ).scalar() or 0
        items.append(
            {
                "id": str(kb.id),
                "name": kb.name,
                "description": kb.description,
                "project_id": project_id,
                "is_active": kb.is_active,
                "chunk_size": kb.chunk_size,
                "chunk_overlap": kb.chunk_overlap,
                "document_count": doc_cnt,
                "processed_count": completed,
                "chunk_count": 0,
                "created_at": _iso(kb.creation_date),
                "updated_at": _iso(kb.updation_date),
                "creator_name": "",
            }
        )
    return page_response(items, total, page, page_size, "查询成功")


async def create_knowledge_base(project_id: int, user_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin", "developer"], db)
    name = (data.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="知识库名称不能为空")
    dup = await db.execute(
        select(KnowledgeBaseModel.id).where(
            KnowledgeBaseModel.project_id == project_id,
            KnowledgeBaseModel.name == name,
            KnowledgeBaseModel.enabled_flag == 1,
        )
    )
    if dup.scalar():
        raise HTTPException(status_code=400, detail="该项目下已存在同名知识库")

    kb = KnowledgeBaseModel(
        project_id=project_id,
        name=name,
        description=data.get("description"),
        chunk_size=int(data.get("chunk_size") or 1000),
        chunk_overlap=int(data.get("chunk_overlap") or 200),
        is_active=data.get("is_active", True),
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    return success_response(
        data={
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
            "is_active": kb.is_active,
            "created_at": _iso(kb.creation_date),
        },
        message="创建成功",
    )


async def update_knowledge_base(project_id: int, user_id: int, kb_id: int, db: AsyncSession, data: dict) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin", "developer"], db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    kb = (await db.execute(stmt)).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    if data.get("name"):
        dup = await db.execute(
            select(KnowledgeBaseModel.id).where(
                KnowledgeBaseModel.project_id == project_id,
                KnowledgeBaseModel.name == data["name"],
                KnowledgeBaseModel.id != kb_id,
                KnowledgeBaseModel.enabled_flag == 1,
            )
        )
        if dup.scalar():
            raise HTTPException(status_code=400, detail="该项目下已存在同名知识库")
        kb.name = data["name"]
    if data.get("description") is not None:
        kb.description = data["description"]
    if data.get("chunk_size") is not None:
        kb.chunk_size = int(data["chunk_size"])
    if data.get("chunk_overlap") is not None:
        kb.chunk_overlap = int(data["chunk_overlap"])
    if data.get("is_active") is not None:
        kb.is_active = data["is_active"]
    kb.updated_by = user_id
    await db.commit()
    await db.refresh(kb)
    return success_response(data={"id": str(kb.id)}, message="更新成功")


async def delete_knowledge_base(project_id: int, user_id: int, kb_id: int, db: AsyncSession) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin"], db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    kb = (await db.execute(stmt)).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    await db.execute(
        delete(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.knowledge_base_id == kb_id,
        )
    )
    kb.enabled_flag = 0
    kb.updated_by = user_id
    await db.commit()
    return success_response(message="删除成功")


async def kb_statistics(project_id: int, user_id: int, kb_id: int, db: AsyncSession) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    kb = (await db.execute(stmt)).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    doc_cnt = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeDocumentModel)
            .where(
                KnowledgeDocumentModel.knowledge_base_id == kb_id,
                KnowledgeDocumentModel.enabled_flag == 1,
            )
        )
    ).scalar() or 0
    return success_response(
        data={
            "knowledge_base_id": str(kb_id),
            "document_count": doc_cnt,
            "chunk_count": 0,
            "name": kb.name,
        },
        message="查询成功",
    )


async def kb_vector_status(project_id: int, user_id: int, kb_id: int, db: AsyncSession) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    kb = (await db.execute(stmt)).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    cfg = await KnowledgeConfigService.get_config(db, user_id)
    enabled = bool(cfg.get("vector_enabled")) and (cfg.get("vector_provider") or "").lower() == "qdrant"
    if not enabled:
        return success_response(
            data={
                "vector_enabled": bool(cfg.get("vector_enabled")),
                "vector_provider": cfg.get("vector_provider"),
                "vector_url": cfg.get("vector_url"),
                "vector_collection": cfg.get("vector_collection"),
                "vector_count": 0,
                "message": "未启用Qdrant向量写入",
            },
            message="查询成功",
        )

    url = (cfg.get("vector_url") or "").rstrip("/")
    collection = cfg.get("vector_collection") or "knowledge_default"
    headers = {"Content-Type": "application/json"}
    if cfg.get("vector_api_key"):
        headers["api-key"] = cfg["vector_api_key"]
    vector_count = 0
    detail = ""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{url}/collections/{collection}/points/count",
                headers=headers,
                json={
                    "exact": True,
                    "filter": {
                        "must": [
                            {"key": "project_id", "match": {"value": str(project_id)}},
                            {"key": "kb_id", "match": {"value": str(kb_id)}},
                        ]
                    },
                },
            )
        if resp.status_code < 400:
            vector_count = int(((resp.json() or {}).get("result") or {}).get("count") or 0)
        else:
            detail = f"Qdrant count失败: HTTP {resp.status_code}"
    except Exception as e:
        detail = f"Qdrant count异常: {e}"

    return success_response(
        data={
            "vector_enabled": True,
            "vector_provider": cfg.get("vector_provider"),
            "vector_url": cfg.get("vector_url"),
            "vector_collection": collection,
            "vector_count": vector_count,
            "message": detail or "向量状态正常",
        },
        message="查询成功",
    )


async def list_documents(
    project_id: int,
    user_id: int,
    kb_id: int,
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    if not (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    q = select(KnowledgeDocumentModel).where(
        KnowledgeDocumentModel.knowledge_base_id == kb_id,
        KnowledgeDocumentModel.enabled_flag == 1,
    )
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0
    q = q.order_by(KnowledgeDocumentModel.id.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(q)).scalars().all()
    items = []
    for d in rows:
        items.append(
            {
                "id": str(d.id),
                "title": d.title,
                "document_type": d.document_type,
                "status": d.status,
                "file_size": d.file_size,
                "word_count": d.word_count,
                "chunk_count": 0,
                "error_message": d.error_message,
                "uploaded_at": _iso(d.creation_date),
                "processed_at": _iso(d.updation_date) if d.status == "completed" else None,
            }
        )
    return page_response(items, total, page, page_size, "查询成功")


async def get_document_chunks(
    project_id: int,
    user_id: int,
    kb_id: int,
    doc_id: int,
    db: AsyncSession,
) -> dict:
    await _check_member(project_id, user_id, db)
    kb_stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    kb = (await db.execute(kb_stmt)).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    doc_stmt = select(KnowledgeDocumentModel).where(
        KnowledgeDocumentModel.id == doc_id,
        KnowledgeDocumentModel.knowledge_base_id == kb_id,
        KnowledgeDocumentModel.enabled_flag == 1,
    )
    doc = (await db.execute(doc_stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not (doc.content or "").strip():
        return success_response(
            data={
                "document_id": str(doc.id),
                "document_title": doc.title,
                "chunk_size": kb.chunk_size,
                "chunk_overlap": kb.chunk_overlap,
                "total_chunks": 0,
                "chunks": [],
            },
            message="文档暂无可分块内容",
        )

    chunks = _split_text(doc.content or "", int(kb.chunk_size or 1000), int(kb.chunk_overlap or 200))
    chunk_items = [{"index": i + 1, "content": c} for i, c in enumerate(chunks)]
    return success_response(
        data={
            "document_id": str(doc.id),
            "document_title": doc.title,
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap,
            "total_chunks": len(chunk_items),
            "chunks": chunk_items,
        },
        message="查询成功",
    )


def _extract_text_from_file(path: Path, doc_type: str) -> Tuple[str, Optional[int]]:
    """返回 (text, word_count)"""
    doc_type = doc_type.lower()
    if doc_type in ("txt", "md", "html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        words = len(text.split())
        return text, words
    if doc_type == "pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            parts = []
            for p in reader.pages:
                parts.append(p.extract_text() or "")
            text = "\n".join(parts)
            words = len(text.split())
            return text, words
        except Exception:
            return "", None
    if doc_type == "docx":
        try:
            import docx

            d = docx.Document(str(path))
            text = "\n".join([para.text for para in d.paragraphs])
            words = len(text.split())
            return text, words
        except Exception:
            return "", None
    return "", None


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if not text:
        return []
    step = max(1, chunk_size - max(0, chunk_overlap))
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        chunk = text[i : i + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        i += step
    return chunks


async def _embed_texts(chunks: List[str], cfg: dict) -> List[List[float]]:
    if not chunks:
        return []
    api_key = cfg.get("embedding_api_key") or ""
    if not api_key:
        return []
    base = (cfg.get("embedding_base_url") or "https://api.openai.com/v1").rstrip("/")
    model = cfg.get("embedding_model") or "text-embedding-3-small"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{base}/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "input": chunks},
        )
        if resp.status_code >= 400:
            return []
        data = resp.json().get("data", [])
    return [item.get("embedding", []) for item in data if item.get("embedding")]


async def _qdrant_ensure_collection(cfg: dict):
    url = (cfg.get("vector_url") or "").rstrip("/")
    collection = cfg.get("vector_collection") or "knowledge_default"
    dim = int(cfg.get("vector_dimension") or 1536)
    metric = (cfg.get("distance_metric") or "Cosine").capitalize()
    headers = {"Content-Type": "application/json"}
    if cfg.get("vector_api_key"):
        headers["api-key"] = cfg["vector_api_key"]
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(f"{url}/collections/{collection}", headers=headers)
        if r.status_code == 200:
            return
        await client.put(
            f"{url}/collections/{collection}",
            headers=headers,
            json={"vectors": {"size": dim, "distance": metric}},
        )


async def _qdrant_upsert_chunks(cfg: dict, doc_id: int, kb_id: int, project_id: int, title: str, chunks: List[str], vectors: List[List[float]]):
    if not chunks or not vectors:
        return 0
    url = (cfg.get("vector_url") or "").rstrip("/")
    collection = cfg.get("vector_collection") or "knowledge_default"
    headers = {"Content-Type": "application/json"}
    if cfg.get("vector_api_key"):
        headers["api-key"] = cfg["vector_api_key"]
    points = []
    for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
        h = hashlib.md5(f"{doc_id}-{idx}-{chunk[:30]}".encode("utf-8")).hexdigest()[:16]
        pid = uuid.UUID(h + h)
        points.append(
            {
                "id": str(pid),
                "vector": vec,
                "payload": {
                    "doc_id": str(doc_id),
                    "kb_id": str(kb_id),
                    "project_id": str(project_id),
                    "chunk_index": idx,
                    "title": title,
                    "content": chunk,
                },
            }
        )
    async with httpx.AsyncClient(timeout=60.0) as client:
        await client.put(f"{url}/collections/{collection}/points", headers=headers, json={"points": points})
    return len(points)


async def _qdrant_delete_doc(cfg: dict, doc_id: int):
    url = (cfg.get("vector_url") or "").rstrip("/")
    collection = cfg.get("vector_collection") or "knowledge_default"
    headers = {"Content-Type": "application/json"}
    if cfg.get("vector_api_key"):
        headers["api-key"] = cfg["vector_api_key"]
    async with httpx.AsyncClient(timeout=20.0) as client:
        await client.post(
            f"{url}/collections/{collection}/points/delete",
            headers=headers,
            json={"filter": {"must": [{"key": "doc_id", "match": {"value": str(doc_id)}}]}},
        )


async def upload_document(
    project_id: int,
    user_id: int,
    kb_id: int,
    db: AsyncSession,
    file: UploadFile,
) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin", "developer"], db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    kb = (await db.execute(stmt)).scalar_one_or_none()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    filename = file.filename or "upload.bin"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    if ext not in ("pdf", "docx", "txt", "md", "html"):
        ext = "txt"

    dir_path = UPLOAD_ROOT / str(project_id) / str(kb_id)
    dir_path.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", filename)[:180]
    dest = dir_path / f"{secrets.token_hex(8)}_{safe_name}"

    content_bytes = await file.read()
    dest.write_bytes(content_bytes)
    text, wc = _extract_text_from_file(dest, ext)
    st = "completed" if text else ("failed" if ext in ("pdf", "docx") else "completed")
    err = None if st == "completed" else "文档解析失败或内容为空"

    chunk_count = 0
    cfg = await KnowledgeConfigService.get_config(db, user_id)

    doc = KnowledgeDocumentModel(
        knowledge_base_id=kb_id,
        title=filename,
        document_type=ext,
        file_path=str(dest),
        content=text,
        status=st,
        error_message=err,
        file_size=len(content_bytes),
        word_count=wc,
        created_by=user_id,
        updated_by=user_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # 文档ID生成后再做一次向量化，确保 payload 里有 doc_id
    if text and cfg.get("vector_enabled") and (cfg.get("vector_provider") or "").lower() == "qdrant":
        try:
            await _qdrant_ensure_collection(cfg)
            chunks = _split_text(text, int(cfg.get("chunk_size") or kb.chunk_size), int(cfg.get("chunk_overlap") or kb.chunk_overlap))
            vectors = await _embed_texts(chunks, cfg)
            if vectors:
                chunk_count = await _qdrant_upsert_chunks(cfg, doc.id, kb_id, project_id, filename, chunks, vectors)
        except Exception:
            chunk_count = 0

    return success_response(
        data={
            "id": str(doc.id),
            "title": doc.title,
            "status": doc.status,
            "chunk_count": chunk_count,
        },
        message="上传成功",
    )


async def delete_document(project_id: int, user_id: int, kb_id: int, doc_id: int, db: AsyncSession) -> dict:
    await _check_role(project_id, user_id, ["owner", "admin", "developer"], db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    if not (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    stmt = select(KnowledgeDocumentModel).where(
        KnowledgeDocumentModel.id == doc_id,
        KnowledgeDocumentModel.knowledge_base_id == kb_id,
        KnowledgeDocumentModel.enabled_flag == 1,
    )
    d = (await db.execute(stmt)).scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="文档不存在")

    if d.file_path:
        try:
            p = Path(d.file_path)
            if p.exists():
                p.unlink()
        except Exception:
            pass
    cfg = await KnowledgeConfigService.get_config(db, user_id)
    if cfg.get("vector_enabled") and (cfg.get("vector_provider") or "").lower() == "qdrant":
        try:
            await _qdrant_delete_doc(cfg, doc_id)
        except Exception:
            pass
    d.enabled_flag = 0
    d.updated_by = user_id
    await db.commit()
    return success_response(message="删除成功")


async def query_knowledge_base(
    project_id: int,
    user_id: int,
    kb_id: int,
    db: AsyncSession,
    query: str,
    top_k: int = 5,
) -> dict:
    await _check_member(project_id, user_id, db)
    stmt = select(KnowledgeBaseModel).where(
        KnowledgeBaseModel.id == kb_id,
        KnowledgeBaseModel.project_id == project_id,
        KnowledgeBaseModel.enabled_flag == 1,
    )
    if not (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="知识库不存在")

    q = query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="query 不能为空")

    cfg = await KnowledgeConfigService.get_config(db, user_id)
    results = []
    mode = "keyword"

    # 启用向量检索（Qdrant）
    if cfg.get("vector_enabled") and (cfg.get("vector_provider") or "").lower() == "qdrant":
        try:
            query_vec = await _embed_texts([q], cfg)
            if query_vec:
                url = (cfg.get("vector_url") or "").rstrip("/")
                collection = cfg.get("vector_collection") or "knowledge_default"
                headers = {"Content-Type": "application/json"}
                if cfg.get("vector_api_key"):
                    headers["api-key"] = cfg["vector_api_key"]
                async with httpx.AsyncClient(timeout=20.0) as client:
                    r = await client.post(
                        f"{url}/collections/{collection}/points/search",
                        headers=headers,
                        json={
                            "vector": query_vec[0],
                            "limit": top_k,
                            "with_payload": True,
                            "filter": {
                                "must": [
                                    {"key": "project_id", "match": {"value": str(project_id)}},
                                    {"key": "kb_id", "match": {"value": str(kb_id)}},
                                ]
                            },
                        },
                    )
                if r.status_code < 400:
                    for item in r.json().get("result", []):
                        payload = item.get("payload") or {}
                        results.append(
                            {
                                "content": (payload.get("content") or "")[:2000],
                                "metadata": {
                                    "document_title": payload.get("title") or "",
                                    "chunk_index": payload.get("chunk_index") or 0,
                                    "score": item.get("score") or 0,
                                },
                            }
                        )
                    mode = "vector"
        except Exception:
            results = []

    # 回退关键词检索
    if not results:
        stmt = (
            select(KnowledgeDocumentModel)
            .where(
                KnowledgeDocumentModel.knowledge_base_id == kb_id,
                KnowledgeDocumentModel.enabled_flag == 1,
                KnowledgeDocumentModel.content.isnot(None),
                KnowledgeDocumentModel.content.like(f"%{q}%"),
            )
            .limit(top_k)
        )
        rows = (await db.execute(stmt)).scalars().all()
        for d in rows:
            results.append(
                {
                    "content": (d.content or "")[:2000],
                    "metadata": {
                        "document_title": d.title,
                        "chunk_index": 0,
                        "score": 1.0,
                    },
                }
            )
        mode = "keyword"

    return success_response(
        data={
            "query": q,
            "results": results,
            "retrieval_time": 0.0,
            "total_results": len(results),
            "mode": mode,
        },
        message="查询成功",
    )


async def system_status(project_id: int, user_id: int, db: AsyncSession) -> dict:
    await _check_member(project_id, user_id, db)
    kb_cnt = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeBaseModel)
            .where(KnowledgeBaseModel.project_id == project_id, KnowledgeBaseModel.enabled_flag == 1)
        )
    ).scalar() or 0
    doc_cnt = (
        await db.execute(
            select(func.count())
            .select_from(KnowledgeDocumentModel)
            .join(
                KnowledgeBaseModel,
                KnowledgeDocumentModel.knowledge_base_id == KnowledgeBaseModel.id,
            )
            .where(
                KnowledgeBaseModel.project_id == project_id,
                KnowledgeDocumentModel.enabled_flag == 1,
                KnowledgeBaseModel.enabled_flag == 1,
            )
        )
    ).scalar() or 0
    return success_response(
        data={
            "total_knowledge_bases": kb_cnt,
            "total_documents": doc_cnt,
            "processing_documents": 0,
            "total_chunks": 0,
            "system_status": "healthy",
            "status_message": "已支持全局配置的向量检索（Qdrant），未启用时自动回退关键词检索",
        },
        message="查询成功",
    )
