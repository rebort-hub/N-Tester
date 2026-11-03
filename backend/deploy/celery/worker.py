#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
from __future__ import annotations

import asyncio
import os
import subprocess
import time
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Allow running via: python backend/deploy/celery/worker.py or cd backend/deploy/celery && python worker.py
_THIS_FILE = Path(__file__).resolve()
_BACKEND_ROOT = _THIS_FILE.parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))
# Make config.py resolve env_file=".env" from backend root.
# This keeps worker startup consistent with main.py (no extra env exports).
if Path.cwd().resolve() != _BACKEND_ROOT:
    os.chdir(_BACKEND_ROOT)

from loguru import logger
from sqlalchemy import select, update

from app.core.database import async_session_factory
from app.api.v1.Ntesterc_module.Ntesterc_skills.execution_model import (
    SkillExecutionArtifactModel,
    SkillExecutionEventModel,
    SkillExecutionJobModel,
)


SKILL_ROOT = Path(os.getenv("SKILL_UPLOAD_DIR", "uploads/skills"))


def _runtime_dirs(project_id: int, runtime_key: str) -> tuple[Path, Path]:
    screenshots = SKILL_ROOT / "runtime" / "screenshots" / str(project_id) / runtime_key
    artifacts = SKILL_ROOT / "runtime" / "artifacts" / str(project_id) / runtime_key
    screenshots.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    return screenshots, artifacts


@dataclass
class RunnerConfig:
    poll_interval: float = 1.0
    max_stdout: int = 12000
    max_stderr: int = 8000
    docker_image: str = os.getenv("SKILL_RUNNER_DOCKER_IMAGE", "skill-runner:latest")


async def _append_event(db, job_id: int, seq: int, level: str, message: str) -> None:
    db.add(SkillExecutionEventModel(job_id=job_id, seq=seq, level=level, message=message))
    await db.commit()


def _collect_files(base_dir: Path) -> list[dict]:
    if not base_dir.exists():
        return []
    items: list[dict] = []
    for p in base_dir.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(base_dir)).replace("\\", "/")
            items.append({"name": p.name, "relative_path": rel, "size": p.stat().st_size})
    return items


async def _index_artifacts(db, job_id: int, kind: str, base_dir: Path) -> None:
    for f in _collect_files(base_dir):
        db.add(
            SkillExecutionArtifactModel(
                job_id=job_id,
                kind=kind,
                name=f["name"],
                relative_path=f["relative_path"],
                size=f.get("size"),
            )
        )
    await db.commit()


def _run_local(command: str, cwd: str, env: dict, timeout: int = 240) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, env=env, shell=True, capture_output=True, text=False, timeout=timeout)


def _run_docker(image: str, command: str, skill_dir: Path, screenshots_dir: Path, artifacts_dir: Path, env: dict) -> subprocess.CompletedProcess:
    # Mount skill dir as /skill, runtime as /runtime; rewrite env paths
    docker_env = env.copy()
    docker_env["SCREENSHOT_DIR"] = "/runtime/screenshots"
    docker_env["SKILL_OUTPUT_DIR"] = "/runtime/artifacts"
    docker_env["ARTIFACT_DIR"] = "/runtime/artifacts"
    args = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{str(skill_dir)}:/skill",
        "-v",
        f"{str(screenshots_dir)}:/runtime/screenshots",
        "-v",
        f"{str(artifacts_dir)}:/runtime/artifacts",
        "-w",
        "/skill",
    ]
    for k in ("SCREENSHOT_DIR", "SKILL_OUTPUT_DIR", "ARTIFACT_DIR", "SKILL_ARGS_JSON", "SKILL_SESSION_ID", "PROJECT_ID", "USER_ID"):
        if k in docker_env:
            args += ["-e", f"{k}={docker_env[k]}"]
    args.append(image)
    args.append(command)
    return subprocess.run(args, capture_output=True, text=False, timeout=300)


def _split_shell_chain(command: str) -> list[str]:
    """
    Split a shell chain on ' && ' (outer only). Typical agent-browser / bash one-liners.
    Single command returns a one-element list.
    """
    s = (command or "").strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(" && ") if p.strip()]
    return parts if parts else [s]


def _smart_decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    # Windows often defaults to GBK, but many CLIs output UTF-8.
    for enc in ("utf-8", "gbk"):
        try:
            return data.decode(enc)
        except Exception:
            continue
    return data.decode("utf-8", errors="ignore")


async def _claim_one_job(db) -> Optional[SkillExecutionJobModel]:
    stmt = (
        select(SkillExecutionJobModel)
        .where(SkillExecutionJobModel.enabled_flag == 1, SkillExecutionJobModel.status == "pending")
        .order_by(SkillExecutionJobModel.id.asc())
        .limit(1)
    )
    job = (await db.execute(stmt)).scalars().first()
    if not job:
        return None
    # attempt claim by status update
    upd = (
        update(SkillExecutionJobModel)
        .where(SkillExecutionJobModel.id == job.id, SkillExecutionJobModel.status == "pending")
        .values(status="running", started_at=datetime.now(timezone.utc))
    )
    res = await db.execute(upd)
    await db.commit()
    if res.rowcount != 1:
        return None
    # reload fresh
    return (await db.execute(select(SkillExecutionJobModel).where(SkillExecutionJobModel.id == job.id))).scalars().first()


async def run_worker_forever(cfg: RunnerConfig) -> None:
    logger.info("Skill runner worker started")
    while True:
        async with async_session_factory() as db:
            try:
                job = await _claim_one_job(db)
                if not job:
                    await asyncio.sleep(cfg.poll_interval)
                    continue

                seq = 1
                await _append_event(db, job.id, seq, "info", f"job claimed: #{job.id} runner={job.runner_type}")
                seq += 1

                screenshots_dir, artifacts_dir = _runtime_dirs(int(job.project_id), str(job.runtime_key))

                env = os.environ.copy()
                env["SKILL_ARGS_JSON"] = __import__("json").dumps(job.input_args or {}, ensure_ascii=False)
                env["SKILL_SESSION_ID"] = job.session_id or ""
                env["PROJECT_ID"] = str(job.project_id)
                env["USER_ID"] = str(job.user_id)
                env["SCREENSHOT_DIR"] = str(screenshots_dir)
                env["SKILL_OUTPUT_DIR"] = str(artifacts_dir)
                env["ARTIFACT_DIR"] = str(artifacts_dir)

                skill_dir = Path((job.runner_meta or {}).get("skill_dir") or "").resolve()
                if not skill_dir.exists():
                    await _append_event(db, job.id, seq, "error", "skill_dir not found")
                    job.status = "failed"
                    job.error_message = "skill_dir not found"
                    await db.commit()
                    continue

                steps = _split_shell_chain(job.command or "")
                if not steps:
                    await _append_event(db, job.id, seq, "error", "empty command")
                    job.status = "failed"
                    job.error_message = "empty command"
                    job.finished_at = datetime.now(timezone.utc)
                    await db.commit()
                    continue
                await _append_event(db, job.id, seq, "info", f"execute: {job.command}")
                seq += 1
                await _append_event(
                    db,
                    job.id,
                    seq,
                    "info",
                    f"测试步骤规划: 共 {len(steps)} 步（按 && 拆分，任一步失败即终止，语义等同 shell 短路）",
                )
                seq += 1

                combined_out: list[str] = []
                combined_err: list[str] = []
                final_rc = 0
                per_step_timeout = max(45, min(240, 900 // max(1, len(steps))))

                try:
                    for idx, step in enumerate(steps, start=1):
                        preview = step if len(step) <= 260 else step[:260] + "..."
                        await _append_event(
                            db,
                            job.id,
                            seq,
                            "info",
                            f"[测试步骤 {idx}/{len(steps)}] 开始执行: {preview}",
                        )
                        seq += 1
                        if job.runner_type == "docker":
                            cp = _run_docker(
                                cfg.docker_image, step, skill_dir, screenshots_dir, artifacts_dir, env
                            )
                        else:
                            cp = _run_local(step, str(skill_dir), env, timeout=per_step_timeout)

                        out_text = _smart_decode(cp.stdout)
                        err_text = _smart_decode(cp.stderr)
                        final_rc = int(cp.returncode or 0)
                        combined_out.append(
                            f"======== 步骤 {idx}/{len(steps)} (returncode={final_rc}) ========\n{(out_text or '').strip()}"
                        )
                        if (err_text or "").strip():
                            combined_err.append(
                                f"======== 步骤 {idx}/{len(steps)} stderr ========\n{(err_text or '').strip()}"
                            )

                        await _append_event(
                            db,
                            job.id,
                            seq,
                            "info" if final_rc == 0 else "error",
                            f"[测试步骤 {idx}/{len(steps)}] 结束 returncode={final_rc}",
                        )
                        seq += 1
                        tail = (out_text or "")[-800:].replace("\r", "").strip()
                        if tail:
                            one_line = " ".join(tail.splitlines())[:700]
                            await _append_event(
                                db,
                                job.id,
                                seq,
                                "debug",
                                f"[测试步骤 {idx}/{len(steps)}] stdout摘要: {one_line}",
                            )
                            seq += 1
                        if final_rc != 0:
                            err_one = " ".join((err_text or "").splitlines())[:700]
                            if err_one.strip():
                                await _append_event(
                                    db,
                                    job.id,
                                    seq,
                                    "error",
                                    f"[测试步骤 {idx}/{len(steps)}] stderr摘要: {err_one}",
                                )
                                seq += 1
                            break
                except subprocess.TimeoutExpired:
                    job.status = "failed"
                    job.error_message = "timeout"
                    await _append_event(db, job.id, seq, "error", "timeout")
                    await db.commit()
                    continue
                except Exception as e:
                    job.status = "failed"
                    job.error_message = str(e)
                    await _append_event(db, job.id, seq, "error", f"exception: {e}")
                    await db.commit()
                    continue

                job.return_code = final_rc
                job.stdout = "\n\n".join(combined_out)[: cfg.max_stdout]
                job.stderr = "\n\n".join(combined_err)[: cfg.max_stderr] if combined_err else ""
                job.status = "succeeded" if final_rc == 0 else "failed"
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()

                await _append_event(db, job.id, seq, "info", f"done rc={final_rc}")
                seq += 1
                await _index_artifacts(db, job.id, "screenshots", screenshots_dir)
                await _index_artifacts(db, job.id, "artifacts", artifacts_dir)
            except Exception as e:
                logger.exception(f"worker loop error: {e}")
        await asyncio.sleep(0)


def main() -> None:
    cfg = RunnerConfig()
    asyncio.run(run_worker_forever(cfg))


if __name__ == "__main__":
    main()

