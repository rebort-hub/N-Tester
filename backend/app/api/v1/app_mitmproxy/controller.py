"""
APP 抓包
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.utils.common import body_to_json
from .service import MitmproxyService

router = APIRouter()


@router.post("/mitmproxy_start")
async def mitmproxy_start(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        ok, msg = await MitmproxyService.mitmproxy_start(body or {})
        if ok:
            return success_response({}, message=msg)
        return error_response(msg)
    except Exception as e:
        return error_response(str(e))


@router.post("/mitmproxy_single_start")
async def mitmproxy_single_start(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        ok, data = await MitmproxyService.mitmproxy_single_start(body or {})
        if ok:
            return success_response(data)
        return error_response(data.get("message") or "启动失败")
    except Exception as e:
        return error_response(str(e))


@router.post("/mitmproxy_check")
async def mitmproxy_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        data = await MitmproxyService.mitmproxy_check(str((body or {}).get("deviceid") or ""))
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@router.post("/mitmproxy_stop")
async def mitmproxy_stop(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        ok, msg = await MitmproxyService.mitmproxy_stop(
            pid=int((body or {}).get("pid") or 0),
            port=int((body or {}).get("port") or 0),
            device_list=(body or {}).get("device") or [],
        )
        if ok:
            return success_response({})
        return error_response(msg)
    except Exception as e:
        return error_response(str(e))


@router.post("/mitmproxy_write_api")
async def mitmproxy_write_api(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        await MitmproxyService.mitmproxy_write_api(
            db=db,
            request_list=(body or {}).get("request_list") or [],
            current_user_id=current_user_id,
        )
        await db.commit()
        return success_response({})
    except Exception as e:
        await db.rollback()
        return error_response(str(e))


@router.post("/single_write")
async def single_write(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        await MitmproxyService.single_write(
            db=db,
            device_id=int((body or {}).get("device_id") or 0),
            request_list=(body or {}).get("request_list") or [],
            current_user_id=current_user_id,
        )
        await db.commit()
        return success_response({})
    except Exception as e:
        await db.rollback()
        return error_response(str(e))


@router.post("/mitmproxy_close_agent")
async def mitmproxy_close_agent(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        ok = await MitmproxyService.mitmproxy_close_agent(str((body or {}).get("deviceid") or ""))
        if ok:
            return success_response({})
        return error_response("关闭代理失败")
    except Exception as e:
        return error_response(str(e))


@router.post("/mitmproxy_run_log")
async def mitmproxy_run_log(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        body = await body_to_json(request)
        search = (body or {}).get("search") or {}
        page = int((body or {}).get("currentPage") or 1)
        page_size = int((body or {}).get("pageSize") or 18)
        data = await MitmproxyService.run_log_paged(db, current_user_id, search, page, page_size)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))

