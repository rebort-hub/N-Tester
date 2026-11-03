# -*- coding: utf-8 -*-
"""Skill 异步任务执行器：将 pending 任务在本机拉起子进程并写入事件流与产物索引。"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.Ntesterc_module.Ntesterc_skills.execution_model import SkillExecutionArtifactModel, SkillExecutionEventModel, SkillExecutionJobModel
from app.api.v1.Ntesterc_module.Ntesterc_skills.model import ProjectSkillModel
from app.core import database as db_sa


async def _next_event_seq(db: AsyncSession, job_id: int) -> int:
    r = (await db.execute(select(func.max(SkillExecutionEventModel.seq)).where(SkillExecutionEventModel.job_id == job_id))).scalar()
    return int(r or 0) + 1


async def _append_event(db: AsyncSession, job_id: int, level: str, message: str, user_id: int) -> None:
    seq = await _next_event_seq(db, job_id)
    db.add(
        SkillExecutionEventModel(
            job_id=job_id,
            seq=seq,
            level=level,
            message=message[:65000],
            created_by=user_id,
            updated_by=user_id,
        )
    )
    await db.commit()


async def run_skill_job_worker(job_id: int) -> None:
    """
    独立 DB 会话中执行单个 job（勿在请求会话内 await，避免阻塞）。
    """
    from app.api.v1.Ntesterc_module.Ntesterc_skills.service import (
        _build_skill_runtime_dirs,
        _collect_files,
        _ingest_saved_outputs,
        _inject_agent_browser_session,
        _smart_decode,
    )

    timeout_s = int(os.getenv("SKILL_JOB_TIMEOUT_SEC", "600"))

    async with db_sa.async_session_factory() as db:
        try:
            job = (
                await db.execute(
                    select(SkillExecutionJobModel).where(
                        SkillExecutionJobModel.id == job_id,
                        SkillExecutionJobModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            if not job or job.status != "pending":
                return

            skill = (
                await db.execute(
                    select(ProjectSkillModel).where(
                        ProjectSkillModel.id == job.skill_id,
                        ProjectSkillModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            if not skill:
                await db.execute(
                    update(SkillExecutionJobModel)
                    .where(SkillExecutionJobModel.id == job_id)
                    .values(status="failed", finished_at=datetime.now(), error_message="技能不存在或已删除", updated_by=job.user_id)
                )
                await db.commit()
                return

            skill_dir = Path(skill.skill_path or "")
            if not skill_dir.exists():
                await db.execute(
                    update(SkillExecutionJobModel)
                    .where(SkillExecutionJobModel.id == job_id)
                    .values(status="failed", finished_at=datetime.now(), error_message="技能目录不存在，请重新上传/导入", updated_by=job.user_id)
                )
                await db.commit()
                return

            cmd = (job.command or "").strip()
            cmd = _inject_agent_browser_session(cmd, job.session_id)
            if not cmd:
                await db.execute(
                    update(SkillExecutionJobModel)
                    .where(SkillExecutionJobModel.id == job_id)
                    .values(status="failed", finished_at=datetime.now(), error_message="任务命令为空", updated_by=job.user_id)
                )
                await db.commit()
                return

            rt = (job.runner_type or "local").strip().lower()
            if rt == "docker":
                await _append_event(db, job_id, "warn", "docker runner 未接入，已回退为 local 执行", job.user_id)

            await db.execute(
                update(SkillExecutionJobModel)
                .where(SkillExecutionJobModel.id == job_id, SkillExecutionJobModel.status == "pending")
                .values(status="running", started_at=datetime.now(), updated_by=job.user_id)
            )
            await db.commit()
            await _append_event(db, job_id, "info", f"开始执行: {cmd[:2000]}", job.user_id)

            screenshots_dir, artifacts_dir = _build_skill_runtime_dirs(int(job.project_id), str(job.runtime_key))
            env = os.environ.copy()
            env["SCREENSHOT_DIR"] = str(screenshots_dir)
            env["SKILL_OUTPUT_DIR"] = str(artifacts_dir)
            env["ARTIFACT_DIR"] = str(artifacts_dir)
            env["SKILL_ARGS_JSON"] = json.dumps(job.input_args or {}, ensure_ascii=False)
            env["SKILL_SESSION_ID"] = str(job.runtime_key)
            env["PROJECT_ID"] = str(job.project_id)
            env["USER_ID"] = str(job.user_id)

            extra = skill.extra_config or {}
            workdir = (extra.get("workdir") or "").strip()
            cwd = skill_dir
            if workdir:
                wd = Path(workdir)
                if not wd.is_absolute():
                    pack_root = Path(str(extra.get("pack_root") or "")).resolve() if extra.get("pack_root") else None
                    base = pack_root if pack_root and pack_root.exists() else skill_dir
                    wd = (base / workdir).resolve()
                if wd.exists():
                    cwd = wd

            def _run() -> subprocess.CompletedProcess:
                return subprocess.run(
                    cmd,
                    cwd=str(cwd),
                    env=env,
                    shell=True,
                    capture_output=True,
                    text=False,
                    timeout=timeout_s,
                )

            try:
                cp = await asyncio.to_thread(_run)
            except subprocess.TimeoutExpired:
                await db.execute(
                    update(SkillExecutionJobModel)
                    .where(SkillExecutionJobModel.id == job_id)
                    .values(
                        status="failed",
                        finished_at=datetime.now(),
                        return_code=-1,
                        error_message=f"执行超时（>{timeout_s}s）",
                        updated_by=job.user_id,
                    )
                )
                await db.commit()
                await _append_event(db, job_id, "error", f"超时 >{timeout_s}s", job.user_id)
                return
            except Exception as e:
                logger.exception("skill job subprocess error job_id={}", job_id)
                await db.execute(
                    update(SkillExecutionJobModel)
                    .where(SkillExecutionJobModel.id == job_id)
                    .values(status="failed", finished_at=datetime.now(), error_message=str(e)[:2000], updated_by=job.user_id)
                )
                await db.commit()
                await _append_event(db, job_id, "error", str(e)[:4000], job.user_id)
                return

            out_text = _smart_decode(cp.stdout).strip()[:24000]
            err_text = _smart_decode(cp.stderr).strip()[:12000]
            ok = cp.returncode == 0
            final_status = "succeeded" if ok else "failed"

            await db.execute(
                update(SkillExecutionJobModel)
                .where(SkillExecutionJobModel.id == job_id)
                .values(
                    status=final_status,
                    finished_at=datetime.now(),
                    return_code=cp.returncode,
                    stdout=out_text,
                    stderr=err_text,
                    updated_by=job.user_id,
                )
            )
            await db.commit()

            tail_lines = [ln.strip() for ln in (out_text or "").splitlines() if ln.strip()][-80:]
            if tail_lines:
                blob = "\n".join(tail_lines)[:12000]
                await _append_event(db, job_id, "info", f"[stdout 摘要]\n{blob}", job.user_id)
            if err_text:
                await _append_event(db, job_id, "error", err_text[:8000], job.user_id)

            _ingest_saved_outputs(out_text, err_text, cwd, screenshots_dir)

            # 产物索引（与下载接口路径一致）
            for kind, base in (("screenshots", screenshots_dir), ("artifacts", artifacts_dir)):
                for it in _collect_files(base):
                    db.add(
                        SkillExecutionArtifactModel(
                            job_id=job_id,
                            kind=kind,
                            name=it["name"],
                            relative_path=it["relative_path"],
                            size=it.get("size"),
                            created_by=job.user_id,
                            updated_by=job.user_id,
                        )
                    )
            await db.commit()
            await _append_event(db, job_id, "info", f"任务结束: {final_status} rc={cp.returncode}", job.user_id)
        except Exception as e:
            logger.exception("run_skill_job_worker fatal job_id={}", job_id)
            try:
                await db.execute(
                    update(SkillExecutionJobModel)
                    .where(SkillExecutionJobModel.id == job_id)
                    .values(status="failed", finished_at=datetime.now(), error_message=str(e)[:2000], updated_by=1)
                )
                await db.commit()
            except Exception:
                await db.rollback()


def schedule_skill_job(job_id: int) -> None:
    """在事件循环中调度异步 worker（非阻塞）。"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(run_skill_job_worker(job_id))
        return

    def _done(t: asyncio.Task) -> None:
        try:
            t.result()
        except Exception as e:
            logger.warning("skill job task exception: {}", e)

    task = loop.create_task(run_skill_job_worker(job_id))
    task.add_done_callback(_done)
