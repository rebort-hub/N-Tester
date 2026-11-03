#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""公开 Mock 入口：/mock/{path}，无需登录。"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

from .mock_service import ApiMockRuntime

router = APIRouter(prefix="/mock", tags=["Mock服务"])


async def _handle(path: str, request: Request, db: AsyncSession) -> Response:
    result = await ApiMockRuntime.resolve(db, request, path or "")
    delay = int(result.get("delay") or 0)
    if delay > 0:
        await asyncio.sleep(min(delay, 60000) / 1000.0)

    status = int(result.get("status") or 200)
    headers = {str(k): str(v) for k, v in (result.get("headers") or {}).items()}
    body: Any = result.get("body")

    # 已有 Content-Type 则尊重；否则 JSON 默认
    if isinstance(body, (dict, list)):
        headers.setdefault("Content-Type", "application/json; charset=utf-8")
        return JSONResponse(content=body, status_code=status, headers=headers)
    if body is None:
        headers.setdefault("Content-Type", "application/json; charset=utf-8")
        return JSONResponse(content={}, status_code=status, headers=headers)

    text = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    headers.setdefault("Content-Type", "text/plain; charset=utf-8")
    return Response(content=text, status_code=status, headers=headers, media_type=headers.get("Content-Type"))


@router.api_route("", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
@router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def mock_root(request: Request, db: AsyncSession = Depends(get_db)):
    return await _handle("", request, db)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def mock_path(path: str, request: Request, db: AsyncSession = Depends(get_db)):
    return await _handle(path, request, db)
