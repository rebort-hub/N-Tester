"""
文件管理API控制器
"""

from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, Query, Request, Form
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.api.v1.system.file.service import FileService
from app.api.v1.system.file.schema import (
    FileQuerySchema,
    FileUpdateSchema,
    FileBatchDeleteSchema,
    FileUploadSchema
)
from app.common.response import success_response

router = APIRouter()


@router.post("/upload", summary="上传文件")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="上传的文件"),
    description: str = Form(None, description="文件描述"),
    tags: str = Form(None, description="文件标签"),
    is_public: int = Form(1, description="是否公开（0:私有 1:公开）"),
    store_in_database: bool = Form(True, description="是否存储在数据库中"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """上传文件"""
    request_base_url = str(request.base_url)
    result = await FileService.upload_file_service(
        file=file,
        current_user_id=current_user_id,
        description=description,
        tags=tags,
        is_public=is_public,
        request_base_url=request_base_url,
        store_in_database=store_in_database,
        db=db
    )
    return success_response(data=result.model_dump(), message="上传成功")


@router.post("/batch-upload", summary="批量上传文件")
async def batch_upload_files(
    request: Request,
    files: List[UploadFile] = File(..., description="上传的文件列表"),
    description: str = Form(None, description="文件描述"),
    tags: str = Form(None, description="文件标签"),
    is_public: int = Form(1, description="是否公开（0:私有 1:公开）"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量上传文件"""
    request_base_url = str(request.base_url)
    results = []
    
    for file in files:
        try:
            result = await FileService.upload_file_service(
                file=file,
                current_user_id=current_user_id,
                description=description,
                tags=tags,
                is_public=is_public,
                request_base_url=request_base_url,
                db=db
            )
            results.append({
                "success": True,
                "file": result.model_dump()
            })
        except Exception as e:
            results.append({
                "success": False,
                "filename": file.filename,
                "error": str(e)
            })
    
    return success_response(data=results, message="批量上传完成")


@router.get("", summary="获取文件列表")
async def get_file_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    file_name: str = Query(None, description="文件名"),
    original_name: str = Query(None, description="原始文件名"),
    file_type: str = Query(None, description="文件类型"),
    file_ext: str = Query(None, description="文件扩展名"),
    upload_type: str = Query(None, description="上传类型"),
    is_public: int = Query(None, ge=0, le=1, description="是否公开"),
    uploaded_by: int = Query(None, description="上传用户ID"),
    begin_time: str = Query(None, description="开始时间"),
    end_time: str = Query(None, description="结束时间"),
    tags: str = Query(None, description="标签"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取文件列表"""
    query = FileQuerySchema(
        page=page,
        page_size=page_size,
        file_name=file_name,
        original_name=original_name,
        file_type=file_type,
        file_ext=file_ext,
        upload_type=upload_type,
        is_public=is_public,
        uploaded_by=uploaded_by,
        begin_time=begin_time,
        end_time=end_time,
        tags=tags
    )
    return await FileService.get_file_list_service(query, current_user_id, db)


@router.get("/{file_id}", summary="获取文件详情")
async def get_file_detail(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取文件详情"""
    result = await FileService.get_file_detail_service(file_id, current_user_id, db)
    return success_response(data=result.model_dump())


@router.put("/{file_id}", summary="更新文件信息")
async def update_file(
    file_id: int,
    data: FileUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """更新文件信息"""
    result = await FileService.update_file_service(file_id, data, current_user_id, db)
    return success_response(data=result.model_dump(), message="更新成功")


@router.delete("/{file_id}", summary="删除文件")
async def delete_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """删除文件"""
    await FileService.delete_file_service(file_id, current_user_id, db)
    return success_response(message="删除成功")


@router.delete("/batch", summary="批量删除文件")
async def batch_delete_files(
    data: FileBatchDeleteSchema,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """批量删除文件"""
    await FileService.batch_delete_files_service(data, current_user_id, db)
    return success_response(message="批量删除成功")


@router.get("/{file_id}/url", summary="获取文件访问URL")
async def get_file_url(
    file_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取文件访问URL"""
    request_base_url = str(request.base_url)
    result = await FileService.get_file_url_service(file_id, current_user_id, request_base_url, db)
    return success_response(data=result.model_dump())


@router.get("/{file_id}/download", summary="下载文件")
async def download_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """下载文件"""
    from urllib.parse import quote
    
    file_path, original_name, file_content = await FileService.download_file_service(file_id, current_user_id, db)
    
    # 对文件名进行URL编码以支持中文文件名
    encoded_filename = quote(original_name.encode('utf-8'))
    
    if file_content is not None:
        # 数据库存储的文件，直接返回内容
        return Response(
            content=file_content,
            media_type='application/octet-stream',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    else:
        # 文件系统存储的文件，返回文件响应
        return FileResponse(
            path=file_path,
            filename=original_name,
            media_type='application/octet-stream'
        )


@router.get("/stats/summary", summary="获取文件统计信息")
async def get_file_stats(
    db: AsyncSession = Depends(get_db)
):
    """获取文件统计信息"""
    result = await FileService.get_file_stats_service(db)
    return success_response(data=result)

@router.get("/content/{file_name}", summary="获取数据库存储的文件内容")
async def get_file_content(
    file_name: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """获取存储在数据库中的文件内容"""
    file_content, file_type = await FileService.get_file_content_service(file_name, current_user_id, db)
    
    return Response(
        content=file_content,
        media_type=file_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f"inline; filename={file_name}"
        }
    )