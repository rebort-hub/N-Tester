#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort


from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_id
from app.core.database import get_db
from app.api.v1.Ntesterc_module.Ntesterc_project import project_platform_service as S

router = APIRouter()


# ---------- MCP ----------


class MCPCallBody(BaseModel):
    name: str = Field(..., description="工具名称")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MCPImportBody(BaseModel):
    path: Optional[str] = Field(None, description="可选绝对路径；默认按 .n-tester/mcp.json → .mcp.json → .cursor/mcp.json 探测")
    scope: Optional[str] = Field("project", description="导入作用域 local/project/user")


class MCPExportBody(BaseModel):
    format: str = Field("claude", description="导出格式：n-tester / claude / cursor")
    scope: Optional[str] = Field(None, description="可选：仅导出指定作用域")
    write: bool = Field(True, description="是否写入目标文件；false 仅返回预览")


@router.get("/{project_id}/mcp-configs", summary="MCP 配置列表")
async def list_mcp(
    project_id: int,
    search: str = Query("", description="名称搜索"),
    is_enabled: Optional[bool] = Query(None),
    scope: Optional[str] = Query(None, description="作用域 local/project/user"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.list_mcp_configs(
        project_id, current_user_id, db, search, is_enabled, scope, page, page_size
    )


@router.post("/{project_id}/mcp-configs", summary="创建 MCP 配置")
async def create_mcp(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.create_mcp_config(project_id, current_user_id, db, data)


@router.post("/{project_id}/mcp-configs/import", summary="从平台/兼容文件导入")
async def mcp_import(
    project_id: int,
    body: MCPImportBody = Body(default=MCPImportBody()),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.import_mcp_from_file(
        project_id, current_user_id, db, body.model_dump(exclude_none=True)
    )


@router.post("/{project_id}/mcp-configs/sync-files", summary="同步到 N-Tester 平台文件")
async def mcp_sync_files(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.sync_mcp_files(project_id, current_user_id, db)


@router.post("/{project_id}/mcp-configs/export", summary="按需导出为 Claude/Cursor/平台格式")
async def mcp_export(
    project_id: int,
    body: MCPExportBody = Body(default=MCPExportBody()),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.export_mcp_configs(
        project_id, current_user_id, db, body.model_dump(exclude_none=True)
    )


@router.put("/{project_id}/mcp-configs/{config_id}", summary="更新 MCP 配置")
async def update_mcp(
    project_id: int,
    config_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.update_mcp_config(project_id, current_user_id, config_id, db, data)


@router.delete("/{project_id}/mcp-configs/{config_id}", summary="删除 MCP 配置")
async def delete_mcp(
    project_id: int,
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.delete_mcp_config(project_id, current_user_id, config_id, db)


@router.post("/{project_id}/mcp-configs/{config_id}/test", summary="测试 MCP 连接")
async def test_mcp(
    project_id: int,
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.test_mcp_config(project_id, current_user_id, config_id, db)


@router.get("/{project_id}/mcp-configs/{config_id}/tools", summary="列出 MCP 工具")
async def mcp_tools(
    project_id: int,
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.mcp_list_tools(project_id, current_user_id, config_id, db)


@router.post("/{project_id}/mcp-configs/{config_id}/call", summary="调用 MCP 工具")
async def mcp_call(
    project_id: int,
    config_id: int,
    body: MCPCallBody = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.mcp_call_tool(
        project_id, current_user_id, config_id, db, body.name, body.arguments or {}
    )


# ---------- Skill ----------


@router.get("/{project_id}/skills", summary="Skill 列表")
async def list_skills(
    project_id: int,
    search: str = Query("", description="名称搜索"),
    scenario_category: str = Query("", description="场景分类"),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.list_skills(project_id, current_user_id, db, search, scenario_category, is_active, page, page_size)


@router.post("/{project_id}/skills", summary="创建 Skill")
async def create_skill(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.create_skill(project_id, current_user_id, db, data)


@router.put("/{project_id}/skills/{skill_id}", summary="更新 Skill")
async def update_skill(
    project_id: int,
    skill_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.update_skill(project_id, current_user_id, skill_id, db, data)


@router.delete("/{project_id}/skills/{skill_id}", summary="删除 Skill")
async def delete_skill(
    project_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.delete_skill(project_id, current_user_id, skill_id, db)


@router.post("/{project_id}/skills/import/git", summary="从Git仓库导入 Skill")
async def import_skill_git(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.import_skill_from_git(project_id, current_user_id, db, data)


@router.post("/{project_id}/skills/import/upload", summary="上传zip导入 Skill")
async def import_skill_upload(
    project_id: int,
    file: UploadFile = File(...),
    scenario_category: Optional[str] = Query(None, description="场景分类"),
    entry_command: Optional[str] = Query(None, description="执行命令"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.import_skill_from_upload(
        project_id=project_id,
        user_id=current_user_id,
        db=db,
        file=file,
        scenario_category=scenario_category,
        entry_command=entry_command,
    )


@router.get("/{project_id}/skills/{skill_id}/content", summary="读取 Skill 内容")
async def get_skill_content(
    project_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.get_skill_content(project_id, current_user_id, skill_id, db)


@router.post("/{project_id}/skills/{skill_id}/execute", summary="执行 Skill")
async def execute_skill(
    project_id: int,
    skill_id: int,
    data: Dict[str, Any] = Body({}),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.execute_skill(project_id, current_user_id, skill_id, db, data)


# ---------- API 密钥 ----------


@router.get("/{project_id}/api-keys", summary="API 密钥列表")
async def list_keys(
    project_id: int,
    search: str = Query("", description="名称搜索"),
    service_type: str = Query("", description="服务类型"),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.list_api_keys(project_id, current_user_id, db, search, service_type, is_active, page, page_size)


@router.post("/{project_id}/api-keys", summary="创建 API 密钥")
async def create_key(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.create_api_key(project_id, current_user_id, db, data)


@router.put("/{project_id}/api-keys/{key_id}", summary="更新 API 密钥")
async def update_key(
    project_id: int,
    key_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.update_api_key(project_id, current_user_id, key_id, db, data)


@router.delete("/{project_id}/api-keys/{key_id}", summary="删除 API 密钥")
async def delete_key(
    project_id: int,
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.delete_api_key(project_id, current_user_id, key_id, db)


@router.post("/{project_id}/api-keys/{key_id}/test", summary="测试 API 密钥")
async def test_key(
    project_id: int,
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.test_api_key(project_id, current_user_id, key_id, db)


@router.post("/{project_id}/api-keys/{key_id}/regenerate", summary="重新生成 API 密钥")
async def regen_key(
    project_id: int,
    key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.regenerate_api_key(project_id, current_user_id, key_id, db)


# ---------- 知识库 ----------


@router.get("/{project_id}/knowledge/global-config", summary="知识库全局配置")
async def get_kgc(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.get_knowledge_global_config(project_id, current_user_id, db)


@router.put("/{project_id}/knowledge/global-config", summary="保存知识库全局配置")
async def put_kgc(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.update_knowledge_global_config(project_id, current_user_id, db, data)


class EmbeddingTestBody(BaseModel):
    api_base_url: Optional[str] = None
    api_key: str = ""
    model_name: Optional[str] = None


@router.post("/{project_id}/knowledge/test-embedding", summary="测试嵌入服务连接")
async def test_emb(
    project_id: int,
    data: EmbeddingTestBody = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.test_embedding_connection(project_id, current_user_id, db, data.model_dump())


@router.get("/{project_id}/knowledge/system-status", summary="知识库系统状态")
async def kb_sys(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.system_status(project_id, current_user_id, db)


@router.get("/{project_id}/knowledge-bases", summary="知识库列表")
async def list_kb(
    project_id: int,
    search: str = Query("", description="搜索"),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.list_knowledge_bases(project_id, current_user_id, db, search, is_active, page, page_size)


@router.post("/{project_id}/knowledge-bases", summary="创建知识库")
async def create_kb(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.create_knowledge_base(project_id, current_user_id, db, data)


@router.put("/{project_id}/knowledge-bases/{kb_id}", summary="更新知识库")
async def update_kb(
    project_id: int,
    kb_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.update_knowledge_base(project_id, current_user_id, kb_id, db, data)


@router.delete("/{project_id}/knowledge-bases/{kb_id}", summary="删除知识库")
async def delete_kb(
    project_id: int,
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.delete_knowledge_base(project_id, current_user_id, kb_id, db)


@router.get("/{project_id}/knowledge-bases/{kb_id}/statistics", summary="知识库统计")
async def kb_stats(
    project_id: int,
    kb_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.kb_statistics(project_id, current_user_id, kb_id, db)


@router.get("/{project_id}/knowledge-bases/{kb_id}/documents", summary="文档列表")
async def list_docs(
    project_id: int,
    kb_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.list_documents(project_id, current_user_id, kb_id, db, page, page_size)


@router.post("/{project_id}/knowledge-bases/{kb_id}/documents", summary="上传文档")
async def up_doc(
    project_id: int,
    kb_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.upload_document(project_id, current_user_id, kb_id, db, file)


@router.delete("/{project_id}/knowledge-bases/{kb_id}/documents/{doc_id}", summary="删除文档")
async def del_doc(
    project_id: int,
    kb_id: int,
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.delete_document(project_id, current_user_id, kb_id, doc_id, db)


class KbQueryBody(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=50)


@router.post("/{project_id}/knowledge-bases/{kb_id}/query", summary="知识库查询（关键词）")
async def q_kb(
    project_id: int,
    kb_id: int,
    body: KbQueryBody = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.query_knowledge_base(project_id, current_user_id, kb_id, db, body.query, body.top_k)
