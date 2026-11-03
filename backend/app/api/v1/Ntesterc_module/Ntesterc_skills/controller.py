#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import Any, Dict, Optional

import asyncio
import json
from fastapi import APIRouter, Body, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user_id
from app.core.database import get_db
from app.api.v1.Ntesterc_module.Ntesterc_skills import service as S
from app.api.v1.Ntesterc_module.Ntesterc_skills.execution_model import SkillExecutionEventModel, SkillExecutionJobModel, SkillExecutionArtifactModel
from sqlalchemy import select

router = APIRouter(tags=["Skill管理"])


@router.get("/projects/{project_id}", summary="Skill 列表")
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


@router.post("/projects/{project_id}", summary="创建 Skill")
async def create_skill(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.create_skill(project_id, current_user_id, db, data)


@router.put("/projects/{project_id}/{skill_id}", summary="更新 Skill")
async def update_skill(
    project_id: int,
    skill_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.update_skill(project_id, current_user_id, skill_id, db, data)


@router.delete("/projects/{project_id}/{skill_id}", summary="删除 Skill")
async def delete_skill(
    project_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.delete_skill(project_id, current_user_id, skill_id, db)


@router.post("/projects/{project_id}/batch-delete", summary="批量删除 Skill（硬删+清理本地目录）")
async def batch_delete_skills(
    project_id: int,
    data: Dict[str, Any] = Body({}),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    skill_ids = data.get("skill_ids") if isinstance(data.get("skill_ids"), list) else None
    delete_all = bool(data.get("delete_all"))
    return await S.batch_delete_skills(
        project_id,
        current_user_id,
        db,
        skill_ids=skill_ids,
        delete_all=delete_all,
    )


@router.post("/projects/{project_id}/import/git", summary="从Git仓库导入 Skill")
async def import_skill_git(
    project_id: int,
    data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.import_skill_from_git(project_id, current_user_id, db, data)


@router.post("/projects/{project_id}/import/upload", summary="上传zip导入 Skill")
async def import_skill_upload(
    project_id: int,
    file: UploadFile = File(...),
    scenario_category: Optional[str] = Query(None, description="场景分类"),
    entry_command: Optional[str] = Query(None, description="执行命令"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.import_skill_from_upload(project_id, current_user_id, db, file, scenario_category, entry_command)


@router.get("/projects/{project_id}/{skill_id}/content", summary="读取 Skill 目录结构与文件内容")
async def get_skill_content(
    project_id: int,
    skill_id: int,
    file_path: Optional[str] = Query(None, description="相对技能目录的文件路径，默认 SKILL.md"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.get_skill_content(project_id, current_user_id, skill_id, db, file_path=file_path)


@router.get("/projects/{project_id}/{skill_id}/manifest", summary="读取 Skill 清单（工具/模板）")
async def get_skill_manifest(
    project_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.get_skill_manifest(project_id, current_user_id, skill_id, db)


@router.post("/projects/{project_id}/{skill_id}/execute", summary="执行 Skill")
async def execute_skill(
    project_id: int,
    skill_id: int,
    data: Dict[str, Any] = Body({}),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.execute_skill(project_id, current_user_id, skill_id, db, data)


@router.post("/projects/{project_id}/{skill_id}/actions/execute", summary="创建 Skill 执行任务（异步）")
async def execute_skill_action_async(
    project_id: int,
    skill_id: int,
    data: Dict[str, Any] = Body({}),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.create_skill_job(
        project_id,
        current_user_id,
        db,
        skill_id=skill_id,
        action_name=data.get("action_name"),
        arguments=data.get("arguments") if isinstance(data.get("arguments"), dict) else {},
        session_id=data.get("session_id"),
        runner_type=data.get("runner_type"),
    )


@router.get("/projects/{project_id}/jobs/{job_id}", summary="查询 Skill 执行任务")
async def get_skill_job(
    project_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.get_skill_job(project_id, current_user_id, db, job_id)


@router.get("/projects/{project_id}/jobs/{job_id}/artifacts", summary="查询 Skill 执行产物")
async def get_skill_job_artifacts(
    project_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    return await S.list_job_artifacts(project_id, current_user_id, db, job_id)


@router.get("/projects/{project_id}/jobs/{job_id}/stream", summary="Skill 执行流（SSE）")
async def stream_skill_job(
    project_id: int,
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    # Validate ownership
    stmt = select(SkillExecutionJobModel).where(
        SkillExecutionJobModel.id == job_id,
        SkillExecutionJobModel.project_id == project_id,
        SkillExecutionJobModel.user_id == current_user_id,
        SkillExecutionJobModel.enabled_flag == 1,
    )
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        return StreamingResponse(iter([b"event: error\ndata: {}\n\n"]), media_type="text/event-stream")

    async def gen():
        last_seq = 0
        # initial hello
        yield f"event: hello\ndata: {json.dumps({'job_id': job_id})}\n\n"
        while True:
            rows = (
                await db.execute(
                    select(SkillExecutionEventModel)
                    .where(
                        SkillExecutionEventModel.job_id == job_id,
                        SkillExecutionEventModel.seq > last_seq,
                        SkillExecutionEventModel.enabled_flag == 1,
                    )
                    .order_by(SkillExecutionEventModel.seq.asc())
                    .limit(200)
                )
            ).scalars().all()
            for r in rows:
                last_seq = int(r.seq)
                payload = {"seq": int(r.seq), "level": r.level, "message": r.message, "ts": r.ts.isoformat() if r.ts else None}
                yield f"event: log\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

            # refresh job status
            j = (await db.execute(select(SkillExecutionJobModel).where(SkillExecutionJobModel.id == job_id))).scalar_one()
            if j.status in ("succeeded", "failed", "cancelled"):
                done_payload = {"status": j.status, "return_code": j.return_code}
                yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
                break

            # keepalive
            yield "event: ping\ndata: {}\n\n"
            await asyncio.sleep(1.2)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/projects/{project_id}/artifacts/{artifact_id}/download", summary="下载 Skill 产物")
async def download_artifact(
    project_id: int,
    artifact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    # Find artifact and job
    a = (await db.execute(
        select(SkillExecutionArtifactModel).where(
            SkillExecutionArtifactModel.id == artifact_id,
            SkillExecutionArtifactModel.enabled_flag == 1,
        )
    )).scalar_one_or_none()
    if not a:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="artifact not found")
    job = (await db.execute(
        select(SkillExecutionJobModel).where(
            SkillExecutionJobModel.id == a.job_id,
            SkillExecutionJobModel.project_id == project_id,
            SkillExecutionJobModel.user_id == current_user_id,
            SkillExecutionJobModel.enabled_flag == 1,
        )
    )).scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="job not found")

    from app.api.v1.Ntesterc_module.Ntesterc_skills.service import SKILL_ROOT as _ROOT
    base = _ROOT / "runtime" / ("screenshots" if a.kind == "screenshots" else "artifacts") / str(project_id) / str(job.runtime_key)
    target = (base / str(a.relative_path)).resolve()
    if not str(target).startswith(str(base.resolve())):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="invalid path")
    if not target.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path=str(target), filename=a.name)

