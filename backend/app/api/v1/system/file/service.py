"""
文件管理业务逻辑层
"""

import os
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.system.file.crud import FileCRUD
from app.api.v1.system.file.model import FileModel
from app.api.v1.system.file.schema import (
    FileOutSchema,
    FileQuerySchema,
    FileUpdateSchema,
    FileUploadResponseSchema,
    FileUrlSchema,
    FileBatchDeleteSchema
)
from app.common.response import page_response
from app.utils.common import format_file_size


class FileService:
    """文件服务"""
    
    # 文件上传配置
    UPLOAD_DIR = "static/upload"
    ALLOWED_EXTENSIONS = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',  # 图片
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # 文档
        '.txt', '.md', '.csv',  # 文本
        '.zip', '.rar', '.7z', '.tar', '.gz',  # 压缩包
        '.mp4', '.avi', '.mov', '.wmv', '.flv',  # 视频
        '.mp3', '.wav', '.flac', '.aac'  # 音频
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_DATABASE_FILE_SIZE = 10 * 1024 * 1024  # 10MB - 超过此大小的文件存储到文件系统
    
    @classmethod
    def _format_file_size(cls, size_bytes: int) -> str:
        """格式化文件大小"""
        return format_file_size(size_bytes)
    
    @classmethod
    def _get_file_ext(cls, filename: str) -> str:
        """获取文件扩展名"""
        return os.path.splitext(filename)[1].lower()
    
    @classmethod
    def _generate_unique_filename(cls, original_filename: str) -> str:
        """生成唯一文件名"""
        file_ext = cls._get_file_ext(original_filename)
        return f"{uuid.uuid4().hex}{file_ext}"
    
    @classmethod
    def _create_upload_dir(cls, upload_type: str = "local") -> str:
        """创建上传目录"""
        today = datetime.now().strftime("%Y%m%d")
        upload_path = os.path.join(cls.UPLOAD_DIR, today)
        os.makedirs(upload_path, exist_ok=True)
        return upload_path
    
    @classmethod
    def _get_file_url(cls, file_path: str, request_base_url: str) -> str:
        """生成文件访问URL"""
        # 将文件路径转换为URL路径
        url_path = file_path.replace("\\", "/")
        if not url_path.startswith("/"):
            url_path = "/" + url_path
        return f"{request_base_url.rstrip('/')}{url_path}"
    
    @classmethod
    async def upload_file_service(
        cls,
        file: UploadFile,
        current_user_id: int,
        description: Optional[str] = None,
        tags: Optional[str] = None,
        is_public: int = 1,
        request_base_url: str = "",
        store_in_database: bool = True,  # 新增参数：是否存储在数据库中
        db: AsyncSession = None
    ) -> FileUploadResponseSchema:
        """
        上传文件
        
        Args:
            file: 上传的文件
            current_user_id: 当前用户ID
            description: 文件描述
            tags: 文件标签
            is_public: 是否公开
            request_base_url: 请求基础URL
            store_in_database: 是否将文件内容存储在数据库中
            db: 数据库会话
            
        Returns:
            上传响应
        """
        # 检查文件是否为空
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择要上传的文件"
            )
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 检查文件大小
        if file_size > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件大小超过限制（最大{cls._format_file_size(cls.MAX_FILE_SIZE)}）"
            )
        
        # 检查文件类型
        file_ext = cls._get_file_ext(file.filename)
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型，允许的类型：{', '.join(cls.ALLOWED_EXTENSIONS)}"
            )
        
        # 生成唯一文件名
        unique_filename = cls._generate_unique_filename(file.filename)
        
        # 根据存储方式处理文件
        if store_in_database and file_size <= cls.MAX_DATABASE_FILE_SIZE:
            # 小文件存储在数据库中
            upload_type = "database"
            file_path = f"database://{unique_filename}"
            # 生成完整的访问URL - 确保包含完整的协议和域名
            if request_base_url and request_base_url.startswith('http'):
                # 如果有完整的base URL，使用它
                base_url = request_base_url.rstrip('/')
                file_url = f"{base_url}/api/v1/system/file/content/{unique_filename}"
            else:
                # 否则使用相对路径，前端会自动处理
                file_url = f"http://127.0.0.1:8100/api/v1/system/file/content/{unique_filename}"
            file_content = content
        else:
            # 大文件或指定存储在文件系统中
            upload_type = "local"
            upload_path = cls._create_upload_dir()
            file_path = os.path.join(upload_path, unique_filename)
            
            try:
                with open(file_path, "wb") as f:
                    f.write(content)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文件保存失败：{str(e)}"
                )
            
            file_url = cls._get_file_url(file_path, request_base_url)
            file_content = None
            
            # 如果原本想存储在数据库但文件太大，给出提示
            if store_in_database and file_size > cls.MAX_DATABASE_FILE_SIZE:
                print(f"文件 {file.filename} 大小 {cls._format_file_size(file_size)} 超过数据库存储限制 {cls._format_file_size(cls.MAX_DATABASE_FILE_SIZE)}，已自动存储到文件系统")
        
        # 保存到数据库
        crud = FileCRUD(db)
        file_data = {
            "file_name": unique_filename,
            "original_name": file.filename,
            "file_path": file_path,
            "file_url": file_url,
            "file_size": file_size,
            "file_type": file.content_type,
            "file_ext": file_ext,
            "upload_type": upload_type,
            "storage_path": upload_path if not store_in_database else None,
            "file_content": file_content,
            "description": description,
            "tags": tags,
            "is_public": is_public,
            "uploaded_by": current_user_id,
            "uploaded_at": datetime.now()
        }
        
        file_obj = await crud.create_crud(file_data)
        
        return FileUploadResponseSchema(
            id=file_obj.id,
            file_name=file_obj.file_name,
            original_name=file_obj.original_name,
            file_path=file_obj.file_path,
            file_url=file_obj.file_url,
            file_size=file_obj.file_size,
            file_type=file_obj.file_type,
            upload_type=file_obj.upload_type,
            uploaded_at=file_obj.uploaded_at
        )
    
    @classmethod
    async def get_file_list_service(
        cls,
        query: FileQuerySchema,
        current_user_id: int,
        db: AsyncSession
    ) -> dict:
        """
        获取文件列表
        
        Args:
            query: 查询参数
            current_user_id: 当前用户ID
            db: 数据库会话
            
        Returns:
            分页数据
        """
        crud = FileCRUD(db)
        
        # 构建查询条件
        conditions = []
        if query.file_name:
            conditions.append(FileModel.file_name.like(f"%{query.file_name}%"))
        if query.original_name:
            conditions.append(FileModel.original_name.like(f"%{query.original_name}%"))
        if query.file_type:
            conditions.append(FileModel.file_type.like(f"%{query.file_type}%"))
        if query.file_ext:
            conditions.append(FileModel.file_ext == query.file_ext)
        if query.upload_type:
            conditions.append(FileModel.upload_type == query.upload_type)
        if query.is_public is not None:
            conditions.append(FileModel.is_public == query.is_public)
        if query.uploaded_by:
            conditions.append(FileModel.uploaded_by == query.uploaded_by)
        if query.begin_time:
            conditions.append(FileModel.creation_date >= query.begin_time)
        if query.end_time:
            conditions.append(FileModel.creation_date <= query.end_time)
        if query.tags:
            conditions.append(FileModel.tags.like(f"%{query.tags}%"))
        
        # 添加权限过滤：公开文件或当前用户上传的文件
        from sqlalchemy import or_
        privacy_condition = or_(
            FileModel.is_public == 1,  # 公开文件
            FileModel.uploaded_by == current_user_id  # 当前用户上传的文件
        )
        conditions.append(privacy_condition)
        
        # 排序
        order_by = [FileModel.creation_date.desc()]
        
        # 查询数据
        items, total = await crud.get_list_crud(
            conditions=conditions,
            order_by=order_by,
            skip=query.skip,
            limit=query.limit
        )
        
        # 转换为输出格式
        file_list = []
        for file_obj in items:
            # 创建字典并添加字段映射
            file_dict = {
                **{c.name: getattr(file_obj, c.name) for c in file_obj.__table__.columns},
                'created_at': file_obj.creation_date,  # 映射字段
                'updated_at': file_obj.updation_date   # 映射字段
            }
            
            file_data = FileOutSchema.model_validate(file_dict)
            file_data.formatted_size = cls._format_file_size(file_obj.file_size)
            file_list.append(file_data.model_dump())
        
        return page_response(
            items=file_list,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
    
    @classmethod
    async def get_file_detail_service(
        cls,
        file_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> FileOutSchema:
        """
        获取文件详情
        
        Args:
            file_id: 文件ID
            current_user_id: 当前用户ID
            db: 数据库会话
            
        Returns:
            文件详情
        """
        crud = FileCRUD(db)
        file_obj = await crud.get_by_id_crud(file_id)
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限：公开文件或当前用户上传的文件
        if file_obj.is_public == 0 and file_obj.uploaded_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文件"
            )
        
        # 创建字典并添加字段映射
        file_dict = {
            **{c.name: getattr(file_obj, c.name) for c in file_obj.__table__.columns},
            'created_at': file_obj.creation_date,  # 映射字段
            'updated_at': file_obj.updation_date   # 映射字段
        }
        
        file_data = FileOutSchema.model_validate(file_dict)
        file_data.formatted_size = cls._format_file_size(file_obj.file_size)
        
        return file_data
    
    @classmethod
    async def update_file_service(
        cls,
        file_id: int,
        data: FileUpdateSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> FileOutSchema:
        """
        更新文件信息
        
        Args:
            file_id: 文件ID
            data: 更新数据
            current_user_id: 当前用户ID
            db: 数据库会话
            
        Returns:
            更新后的文件信息
        """
        crud = FileCRUD(db)
        
        # 检查文件是否存在
        file_obj = await crud.get_by_id_crud(file_id)
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限（只有上传者可以修改）
        if file_obj.uploaded_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限修改此文件"
            )
        
        # 准备更新数据
        update_data = data.model_dump(exclude_unset=True)
        update_data['updated_by'] = current_user_id
        
        # 更新文件信息
        await crud.update_crud(file_id, update_data)
        
        return await cls.get_file_detail_service(file_id, current_user_id, db)
    
    @classmethod
    async def delete_file_service(
        cls,
        file_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            current_user_id: 当前用户ID
            db: 数据库会话
        """
        crud = FileCRUD(db)
        
        # 检查文件是否存在
        file_obj = await crud.get_by_id_crud(file_id)
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限（只有上传者可以删除）
        if file_obj.uploaded_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限删除此文件"
            )
        
        # 删除物理文件（仅对文件系统存储的文件）
        if file_obj.upload_type != "database":
            try:
                if os.path.exists(file_obj.file_path):
                    os.remove(file_obj.file_path)
            except Exception as e:
                # 记录日志但不阻止删除数据库记录
                print(f"删除物理文件失败：{str(e)}")
        
        # 删除数据库记录
        await crud.delete_crud([file_id])
    
    @classmethod
    async def batch_delete_files_service(
        cls,
        data: FileBatchDeleteSchema,
        current_user_id: int,
        db: AsyncSession
    ) -> None:
        """
        批量删除文件
        
        Args:
            data: 批量删除数据
            current_user_id: 当前用户ID
            db: 数据库会话
        """
        crud = FileCRUD(db)
        
        # 检查所有文件是否存在且有权限删除
        for file_id in data.ids:
            file_obj = await crud.get_by_id_crud(file_id)
            if not file_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"文件ID {file_id} 不存在"
                )
            
            if file_obj.uploaded_by != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"无权限删除文件：{file_obj.original_name}"
                )
        
        # 删除物理文件（仅对文件系统存储的文件）
        for file_id in data.ids:
            file_obj = await crud.get_by_id_crud(file_id)
            if file_obj.upload_type != "database":
                try:
                    if os.path.exists(file_obj.file_path):
                        os.remove(file_obj.file_path)
                except Exception as e:
                    print(f"删除物理文件失败：{str(e)}")
        
        # 批量删除数据库记录
        await crud.delete_crud(data.ids)
    
    @classmethod
    async def get_file_url_service(
        cls,
        file_id: int,
        current_user_id: int,
        request_base_url: str,
        db: AsyncSession
    ) -> FileUrlSchema:
        """
        获取文件访问URL
        
        Args:
            file_id: 文件ID
            current_user_id: 当前用户ID
            request_base_url: 请求基础URL
            db: 数据库会话
            
        Returns:
            文件URL信息
        """
        crud = FileCRUD(db)
        file_obj = await crud.get_by_id_crud(file_id)
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限：公开文件或当前用户上传的文件
        if file_obj.is_public == 0 and file_obj.uploaded_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问此文件"
            )
        
        # 生成访问URL和下载URL
        file_url = cls._get_file_url(file_obj.file_path, request_base_url)
        download_url = f"{request_base_url.rstrip('/')}/api/v1/system/file/{file_id}/download"
        
        return FileUrlSchema(
            file_url=file_url,
            download_url=download_url
        )
    
    @classmethod
    async def download_file_service(
        cls,
        file_id: int,
        current_user_id: int,
        db: AsyncSession
    ) -> tuple[str, str, bytes]:
        """
        下载文件
        
        Args:
            file_id: 文件ID
            current_user_id: 当前用户ID
            db: 数据库会话
            
        Returns:
            (文件路径, 原始文件名, 文件内容) - 如果是数据库存储，文件路径为None，文件内容为bytes
        """
        crud = FileCRUD(db)
        file_obj = await crud.get_by_id_crud(file_id)
        
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限：公开文件或当前用户上传的文件
        if file_obj.is_public == 0 and file_obj.uploaded_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限下载此文件"
            )
        
        # 根据存储类型处理文件
        if file_obj.upload_type == "database":
            # 数据库存储的文件
            if not file_obj.file_content:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件内容不存在"
                )
            
            # 增加下载次数
            await crud.increment_download_count_crud(file_id)
            
            return None, file_obj.original_name, file_obj.file_content
        else:
            # 文件系统存储的文件
            if not os.path.exists(file_obj.file_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件已被删除或移动"
                )
            
            # 增加下载次数
            await crud.increment_download_count_crud(file_id)
            
            return file_obj.file_path, file_obj.original_name, None
    
    @classmethod
    async def get_file_stats_service(
        cls,
        db: AsyncSession
    ) -> dict:
        """
        获取文件统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            统计信息
        """
        crud = FileCRUD(db)
        stats = await crud.get_files_stats_crud()
        
        # 格式化文件大小
        stats['formatted_total_size'] = cls._format_file_size(stats['total_size'])
        
        return stats
    @classmethod
    async def get_file_content_service(
        cls,
        file_name: str,
        current_user_id: int,
        db: AsyncSession
    ) -> tuple[bytes, str]:
        """
        获取存储在数据库中的文件内容
        
        Args:
            file_name: 文件名
            current_user_id: 当前用户ID
            db: 数据库会话
            
        Returns:
            文件内容和MIME类型的元组
        """
        crud = FileCRUD(db)
        
        # 根据文件名查找文件
        file_obj = await crud.get_by_file_name_crud(file_name)
        if not file_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 检查权限：公开文件或当前用户上传的文件
        if file_obj.is_public == 0 and file_obj.uploaded_by != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该文件"
            )
        
        # 检查文件是否存储在数据库中
        if file_obj.upload_type != "database" or not file_obj.file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该文件未存储在数据库中"
            )
        
        return file_obj.file_content, file_obj.file_type or "application/octet-stream"

    @classmethod
    async def read_file_bytes_for_user(
        cls,
        file_name: str,
        current_user_id: int,
        db: AsyncSession,
    ) -> Optional[bytes]:
        """
        按存储文件名读取字节（database / local），供对话注入附件等内部逻辑使用。
        无权限或文件不存在返回 None。
        """
        crud = FileCRUD(db)
        file_obj = await crud.get_by_file_name_crud(file_name)
        if not file_obj:
            return None
        if file_obj.is_public == 0 and file_obj.uploaded_by != current_user_id:
            return None
        if file_obj.upload_type == "database" and file_obj.file_content:
            return file_obj.file_content
        if file_obj.upload_type == "local" and file_obj.file_path:
            try:
                if os.path.exists(file_obj.file_path):
                    with open(file_obj.file_path, "rb") as f:
                        return f.read()
            except OSError:
                return None
        return None