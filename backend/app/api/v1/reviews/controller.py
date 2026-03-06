# 用例评审模块 - 控制器层

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.corelibs.logger import logger

from .service import ReviewService, AssignmentService, CommentService, TemplateService
from .ai_review_service import ReviewAIService
from .model import (
    ReviewComment, ReviewAssignment, ReviewTestCase, TestCaseReview,
    ReviewTemplate, TemplateProject, TemplateDefaultReviewer
)
from .schema import (
    ReviewCreate, ReviewUpdate, ReviewResponse,
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    CommentCreate, CommentUpdate, CommentResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    ReviewStatistics
)

router = APIRouter(prefix="/reviews", tags=["用例评审"])


# 评审管理接口
@router.post("", summary="创建评审")
async def create_review(
    review_data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    创建评审
    
    - **title**: 评审标题
    - **description**: 评审描述
    - **priority**: 优先级 (low/medium/high/urgent)
    - **deadline**: 截止日期
    - **template_id**: 使用的模板ID
    - **test_case_ids**: 关联的测试用例ID列表
    - **reviewer_ids**: 评审人ID列表
    """
    try:
        review = await ReviewService.create_review(
            db=db,
            review_data=review_data,
            creator_id=current_user_id
        )
        
        # 构建响应数据
        response_data = ReviewResponse(
            id=review.id,
            project_id=review.project_id,
            title=review.title,
            description=review.description,
            status=review.status,
            priority=review.priority,
            deadline=review.deadline,
            template_id=review.template_id,
            creator_id=review.creator_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
            completed_at=review.completed_at,
            test_case_count=len(review_data.test_case_ids),
            reviewer_count=len(review_data.reviewer_ids),
            comment_count=0,
            progress=0.0
        )
        
        return success_response(data=response_data, message="创建评审成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 创建评审失败: {str(e)}")
        return error_response(message=f"创建评审失败: {str(e)}")


@router.get("", summary="获取评审列表")
async def get_review_list(
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    creator_id: Optional[int] = Query(None, description="创建人筛选"),
    reviewer_id: Optional[int] = Query(None, description="评审人筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取评审列表
    
    支持按状态、优先级、创建人、评审人筛选
    """
    try:
        reviews, total = await ReviewService.get_review_list(
            db=db,
            project_id=project_id,
            status=status,
            priority=priority,
            creator_id=creator_id,
            reviewer_id=reviewer_id,
            page=page,
            page_size=page_size
        )
        
        # 构建响应数据
        review_list = []
        
        # 获取所有创建人ID
        creator_ids = list(set([review.creator_id for review in reviews if review.creator_id]))
        
        # 查询创建人信息
        creator_map = {}
        if creator_ids:
            from sqlalchemy import text
            creator_query = text("SELECT id, nickname, username FROM sys_user WHERE id IN :creator_ids")
            creator_result = await db.execute(creator_query, {"creator_ids": tuple(creator_ids)})
            creators = creator_result.fetchall()
            creator_map = {creator.id: creator.nickname or creator.username for creator in creators}
        
        for review in reviews:
            # TODO: 获取关联数据统计
            review_data = {
                "id": review.id,
                "project_id": review.project_id,
                "title": review.title,
                "description": review.description,
                "status": review.status,
                "priority": review.priority,
                "deadline": review.deadline.isoformat() if review.deadline else None,
                "template_id": review.template_id,
                "creator_id": review.creator_id,
                "creator_name": creator_map.get(review.creator_id, "未知用户"),  # 添加创建人姓名
                "creation_date": review.creation_date.isoformat() if review.creation_date else None,
                "updation_date": review.updation_date.isoformat() if review.updation_date else None,
                "completed_at": review.completed_at.isoformat() if review.completed_at else None,
                "test_case_count": 0,  # TODO: 实际统计
                "reviewer_count": 0,   # TODO: 实际统计
                "comment_count": 0,    # TODO: 实际统计
                "progress": 0.0        # TODO: 实际计算
            }
            review_list.append(review_data)
        
        paginated_data = {
            "rows": review_list,
            "rowTotal": total,
            "page": page,
            "pageSize": page_size,
            "pageTotal": (total + page_size - 1) // page_size
        }
        
        return success_response(data=paginated_data, message="获取评审列表成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审列表失败: {str(e)}")
        return error_response(message=f"获取评审列表失败: {str(e)}")


# 评审模板接口 - 移到这里，在 /{review_id} 之前
@router.post("/templates", summary="创建评审模板")
async def create_template(
    template_data: TemplateCreate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建评审模板"""
    try:
        template = await TemplateService.create_template(
            db=db,
            template_data=template_data,
            creator_id=current_user_id
        )
        
        return success_response(data=None, message="创建评审模板成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 创建评审模板失败: {str(e)}")
        return error_response(message=f"创建评审模板失败: {str(e)}")


@router.get("/templates", summary="获取评审模板列表")
async def get_template_list(
    project_id: Optional[int] = Query(None, description="项目ID"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取评审模板列表"""
    try:
        templates, total = await TemplateService.get_template_list(
            db=db,
            project_id=project_id,
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        
        # 获取所有创建人ID
        creator_ids = list(set([template.creator_id for template in templates if template.creator_id]))
        
        # 查询创建人信息
        creator_map = {}
        if creator_ids:
            from sqlalchemy import text
            creator_query = text("SELECT id, nickname, username FROM sys_user WHERE id IN :creator_ids")
            creator_result = await db.execute(creator_query, {"creator_ids": tuple(creator_ids)})
            creators = creator_result.fetchall()
            creator_map = {creator.id: creator.nickname or creator.username for creator in creators}
        
        # 构建响应数据
        template_list = []
        for template in templates:
            template_data = {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "checklist": template.checklist,
                "is_active": template.is_active,
                "creator_id": template.creator_id,
                "creator_name": creator_map.get(template.creator_id, "未知用户"),  # 添加创建人姓名
                "creation_date": template.creation_date.isoformat() if template.creation_date else None,
                "updation_date": template.updation_date.isoformat() if template.updation_date else None,
            }
            template_list.append(template_data)
        
        result = {
            "rows": template_list,
            "rowTotal": total,
            "page": page,
            "pageSize": page_size,
            "pageTotal": (total + page_size - 1) // page_size
        }
        
        return success_response(data=result, message="获取评审模板列表成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审模板列表失败: {str(e)}")
        return error_response(message=f"获取评审模板列表失败: {str(e)}")


@router.get("/templates/{template_id}", summary="获取评审模板详情")
async def get_template_detail(
    template_id: int = Path(..., description="模板ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取评审模板详情"""
    try:
        template = await TemplateService.get_template_detail(
            db=db,
            template_id=template_id
        )
        
        if not template:
            return error_response(message="模板不存在")
        
        # 获取关联的项目
        from sqlalchemy import text
        project_query = text("""
            SELECT p.id, p.name
            FROM template_projects tp
            INNER JOIN projects p ON tp.project_id = p.id
            WHERE tp.template_id = :template_id
            AND p.enabled_flag = 1
        """)
        project_result = await db.execute(project_query, {"template_id": template_id})
        projects = project_result.fetchall()
        project_ids = [p.id for p in projects]
        
        # 获取默认评审人
        reviewer_query = text("""
            SELECT tdr.user_id, u.username, u.nickname
            FROM template_default_reviewers tdr
            INNER JOIN sys_user u ON tdr.user_id = u.id
            WHERE tdr.template_id = :template_id
            AND u.enabled_flag = 1
        """)
        reviewer_result = await db.execute(reviewer_query, {"template_id": template_id})
        reviewers = reviewer_result.fetchall()
        reviewer_ids = [r.user_id for r in reviewers]
        
        template_data = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "checklist": template.checklist,
            "is_active": template.is_active,
            "creator_id": template.creator_id,
            "creation_date": template.creation_date.isoformat() if template.creation_date else None,
            "updation_date": template.updation_date.isoformat() if template.updation_date else None,
            "project_ids": project_ids,
            "default_reviewer_ids": reviewer_ids,
        }
        
        return success_response(data=template_data, message="获取模板详情成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取模板详情失败: {str(e)}")
        return error_response(message=f"获取模板详情失败: {str(e)}")


@router.put("/templates/{template_id}", summary="更新评审模板")
async def update_template(
    template_id: int = Path(..., description="模板ID"),
    template_data: TemplateUpdate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新评审模板"""
    try:
        template = await TemplateService.update_template(
            db=db,
            template_id=template_id,
            template_data=template_data,
            user_id=current_user_id
        )
        
        template_data = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "checklist": template.checklist,
            "is_active": template.is_active,
            "creator_id": template.creator_id,
            "creation_date": template.creation_date.isoformat() if template.creation_date else None,
            "updation_date": template.updation_date.isoformat() if template.updation_date else None,
        }
        
        return success_response(data=template_data, message="更新模板成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 更新模板失败: {str(e)}")
        return error_response(message=f"更新模板失败: {str(e)}")


@router.delete("/templates/{template_id}", summary="删除评审模板")
async def delete_template(
    template_id: int = Path(..., description="模板ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除评审模板"""
    try:
        # 获取模板详情
        template = await TemplateService.get_template_detail(
            db=db,
            template_id=template_id
        )
        
        if not template:
            return error_response(message="模板不存在")
        
        # 检查权限（只有创建人或管理员可以删除）
        # TODO: 添加管理员权限检查
        if template.creator_id != current_user_id:
            return error_response(message="无权限删除此模板")
        
        # 检查是否有评审在使用此模板
        from sqlalchemy import select, func, text
        
        # 查询使用此模板的评审详情
        usage_query = text("""
            SELECT tcr.id, tcr.title, tcr.status, tcr.creation_date
            FROM test_case_reviews tcr
            WHERE tcr.template_id = :template_id
            ORDER BY tcr.creation_date DESC
            LIMIT 5
        """)
        usage_result = await db.execute(usage_query, {"template_id": template_id})
        using_reviews = usage_result.fetchall()
        
        if using_reviews:
            # 统计总数
            count_query = select(func.count(TestCaseReview.id)).where(
                TestCaseReview.template_id == template_id
            )
            count_result = await db.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # 构建详细的错误信息
            review_list = []
            for review in using_reviews:
                status_text = {
                    'pending': '待开始',
                    'in_progress': '进行中', 
                    'completed': '已完成',
                    'cancelled': '已取消'
                }.get(review.status, review.status)
                
                creation_date = review.creation_date.strftime('%Y-%m-%d %H:%M:%S') if review.creation_date else '未知时间'
                review_list.append(f"• {review.title} ({status_text}) - {creation_date}")
            
            error_msg = f"无法删除模板\"{template.name}\"，该模板正在被 {total_count} 个评审使用。\n\n"
            error_msg += "使用此模板的评审包括：\n"
            error_msg += "\n".join(review_list)
            
            if total_count > 5:
                error_msg += f"\n... 还有 {total_count - 5} 个评审"
            
            error_msg += "\n\n请先删除或修改这些评审的模板设置后再删除此模板。"
            
            return error_response(message=error_msg)
        
        # 硬删除模板及相关数据
        from sqlalchemy import delete
        
        # 删除模板项目关联
        await db.execute(delete(TemplateProject).where(TemplateProject.template_id == template_id))
        
        # 删除模板默认评审人关联
        await db.execute(delete(TemplateDefaultReviewer).where(TemplateDefaultReviewer.template_id == template_id))
        
        # 删除模板记录
        await db.execute(delete(ReviewTemplate).where(ReviewTemplate.id == template_id))
        
        await db.commit()
        
        return success_response(data=None, message=f"模板\"{template.name}\"删除成功")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[评审管理] 删除模板失败: {str(e)}")
        return error_response(message=f"删除模板失败: {str(e)}")


# 统计接口 - 必须在 /{review_id} 之前定义
@router.get("/statistics", summary="获取评审统计")
async def get_review_statistics(
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取评审统计信息"""
    try:
        # 如果没有指定项目ID，获取全局统计
        if project_id is None:
            # 全局统计
            # 总评审数
            total_result = await db.execute(select(func.count(TestCaseReview.id)))
            total_reviews = total_result.scalar() or 0
            
            # 各状态统计
            status_stats = {}
            for status in ['pending', 'in_progress', 'completed', 'cancelled']:
                status_query = select(func.count(TestCaseReview.id)).where(
                    TestCaseReview.status == status
                )
                result = await db.execute(status_query)
                status_stats[status] = result.scalar() or 0
            
            # 优先级统计
            priority_stats = {}
            for priority in ['low', 'medium', 'high', 'urgent']:
                priority_query = select(func.count(TestCaseReview.id)).where(
                    TestCaseReview.priority == priority
                )
                result = await db.execute(priority_query)
                priority_stats[priority] = result.scalar() or 0
            
            # 逾期评审数
            from datetime import datetime
            now = datetime.now()
            overdue_query = select(func.count(TestCaseReview.id)).where(
                and_(
                    TestCaseReview.deadline < now,
                    TestCaseReview.status.in_(['pending', 'in_progress'])
                )
            )
            overdue_result = await db.execute(overdue_query)
            overdue_reviews = overdue_result.scalar() or 0
            
            # 最近评审（最近10条）
            recent_query = select(TestCaseReview).order_by(desc(TestCaseReview.creation_date)).limit(10)
            recent_result = await db.execute(recent_query)
            recent_reviews = recent_result.scalars().all()
            
            # 构建统计数据
            statistics = {
                "total_reviews": total_reviews,
                "pending_reviews": status_stats['pending'],
                "in_progress_reviews": status_stats['in_progress'],
                "completed_reviews": status_stats['completed'],
                "cancelled_reviews": status_stats['cancelled'],
                "overdue_reviews": overdue_reviews,
                "avg_completion_time": 0.0,  # TODO: 计算平均完成时间
                "total_comments": 0,  # TODO: 统计评论数
                "unresolved_comments": 0,  # TODO: 统计未解决评论数
                "status_distribution": status_stats,
                "priority_distribution": priority_stats,
                "recent_reviews": [
                    {
                        "id": review.id,
                        "title": review.title,
                        "status": review.status,
                        "priority": review.priority,
                        "creation_date": review.creation_date.isoformat() if review.creation_date else None
                    }
                    for review in recent_reviews
                ]
            }
        else:
            # 项目级统计
            statistics = await TemplateService.get_statistics(
                db=db,
                project_id=project_id
            )
        
        return success_response(data=statistics, message="获取评审统计成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审统计失败: {str(e)}")
        return error_response(message=f"获取评审统计失败: {str(e)}")


# 我的评审任务接口 - 必须在 /{review_id} 之前定义
@router.get("/my-tasks", summary="获取我的评审任务")
async def get_my_review_tasks(
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的评审任务列表"""
    try:
        from sqlalchemy import text
        
        # 构建查询条件
        where_conditions = ["ra.reviewer_id = :user_id", "ra.enabled_flag = 1", "tcr.enabled_flag = 1"]
        params = {"user_id": current_user_id}
        
        if status:
            where_conditions.append("ra.status = :status")
            params["status"] = status
            
        if priority:
            where_conditions.append("tcr.priority = :priority")
            params["priority"] = priority
            
        if keyword:
            where_conditions.append("tcr.title LIKE :keyword")
            params["keyword"] = f"%{keyword}%"
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询任务列表
        query = text(f"""
            SELECT 
                tcr.id,
                tcr.title,
                tcr.priority,
                tcr.deadline,
                ra.status as my_status,
                ra.assigned_at,
                ra.reviewed_at,
                COUNT(rtc.test_case_id) as test_case_count,
                COUNT(CASE WHEN rr.result IS NOT NULL THEN 1 END) as reviewed_count
            FROM review_assignments ra
            INNER JOIN test_case_reviews tcr ON ra.review_id = tcr.id
            LEFT JOIN review_test_cases rtc ON tcr.id = rtc.review_id
            LEFT JOIN review_results rr ON rtc.test_case_id = rr.test_case_id 
                AND rr.review_id = tcr.id 
                AND rr.reviewer_id = ra.reviewer_id
            WHERE {where_clause}
            GROUP BY tcr.id, ra.id
            ORDER BY 
                CASE ra.status 
                    WHEN 'pending' THEN 1 
                    WHEN 'in_progress' THEN 2 
                    ELSE 3 
                END,
                tcr.deadline ASC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": page_size,
            "offset": (page - 1) * page_size
        })
        
        result = await db.execute(query, params)
        tasks = result.fetchall()
        
        # 查询总数
        count_query = text(f"""
            SELECT COUNT(DISTINCT tcr.id)
            FROM review_assignments ra
            INNER JOIN test_case_reviews tcr ON ra.review_id = tcr.id
            WHERE {where_clause}
        """)
        
        count_result = await db.execute(count_query, {k: v for k, v in params.items() if k not in ['limit', 'offset']})
        total = count_result.scalar() or 0
        
        # 构建响应数据
        task_list = []
        for task in tasks:
            my_progress = 0
            if task.test_case_count > 0:
                my_progress = round((task.reviewed_count / task.test_case_count) * 100, 1)
            
            task_data = {
                "id": task.id,
                "title": task.title,
                "priority": task.priority,
                "my_status": task.my_status,
                "my_progress": my_progress,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                "assigned_at": task.assigned_at.isoformat() if task.assigned_at else None,
                "reviewed_at": task.reviewed_at.isoformat() if task.reviewed_at else None,
                "test_case_count": task.test_case_count,
                "reviewed_count": task.reviewed_count,
            }
            task_list.append(task_data)
        
        result_data = {
            "rows": task_list,
            "rowTotal": total,
            "page": page,
            "pageSize": page_size,
            "pageTotal": (total + page_size - 1) // page_size
        }
        
        return success_response(data=result_data, message="获取我的评审任务成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取我的评审任务失败: {str(e)}")
        return error_response(message=f"获取我的评审任务失败: {str(e)}")


@router.get("/{review_id}", summary="获取评审详情")
async def get_review_detail(
    review_id: int = Path(..., description="评审ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取评审详情"""
    try:
        review = await ReviewService.get_review_detail(
            db=db,
            review_id=review_id,
            project_id=project_id
        )
        
        if not review:
            return error_response(message="评审不存在")
        
        # 获取创建人信息
        creator_name = "未知用户"
        if review.creator_id:
            from sqlalchemy import text
            creator_query = text("SELECT nickname, username FROM sys_user WHERE id = :creator_id")
            creator_result = await db.execute(creator_query, {"creator_id": review.creator_id})
            creator = creator_result.fetchone()
            if creator:
                creator_name = creator.nickname or creator.username
        
        # 获取关联数据统计
        # 统计测试用例数量
        test_case_count_query = select(func.count(ReviewTestCase.test_case_id)).where(
            ReviewTestCase.review_id == review_id
        )
        test_case_result = await db.execute(test_case_count_query)
        test_case_count = test_case_result.scalar() or 0
        
        # 统计评审人数量
        reviewer_count_query = select(func.count(ReviewAssignment.reviewer_id)).where(
            ReviewAssignment.review_id == review_id
        )
        reviewer_result = await db.execute(reviewer_count_query)
        reviewer_count = reviewer_result.scalar() or 0
        
        # 统计评论数量（来自评审结果中的评论）
        comment_count_query = text("""
            SELECT COUNT(*) 
            FROM review_results 
            WHERE review_id = :review_id 
            AND comment IS NOT NULL 
            AND comment != ''
        """)
        comment_result = await db.execute(comment_count_query, {"review_id": review_id})
        comment_count = comment_result.scalar() or 0
        
        # 计算完成进度（已完成的评审人数 / 总评审人数）
        completed_reviewer_query = select(func.count(ReviewAssignment.reviewer_id)).where(
            and_(
                ReviewAssignment.review_id == review_id,
                ReviewAssignment.status == 'completed'
            )
        )
        completed_result = await db.execute(completed_reviewer_query)
        completed_count = completed_result.scalar() or 0
        progress = (completed_count / reviewer_count * 100) if reviewer_count > 0 else 0.0

        response_data = ReviewResponse(
            id=review.id,
            project_id=review.project_id,
            title=review.title,
            description=review.description,
            status=review.status,
            priority=review.priority,
            deadline=review.deadline,
            template_id=review.template_id,
            creator_id=review.creator_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
            completed_at=review.completed_at,
            test_case_count=test_case_count,
            reviewer_count=reviewer_count,
            comment_count=comment_count,
            progress=round(progress, 1)
        )
        
        # 添加创建人姓名到响应数据
        response_dict = response_data.dict()
        response_dict["creator_name"] = creator_name
        response_dict["creation_date"] = review.creation_date.isoformat() if review.creation_date else None
        response_dict["updation_date"] = review.updation_date.isoformat() if review.updation_date else None
        
        return success_response(data=response_dict, message="获取评审详情成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审详情失败: {str(e)}")
        return error_response(message=f"获取评审详情失败: {str(e)}")


@router.delete("/{review_id}", summary="删除评审")
async def delete_review(
    review_id: int = Path(..., description="评审ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除评审"""
    try:
        # 获取评审详情
        review = await ReviewService.get_review_detail(
            db=db,
            review_id=review_id,
            project_id=project_id
        )
        
        if not review:
            return error_response(message="评审不存在")
        
        # 检查权限（只有创建人或管理员可以删除）
        # TODO: 添加管理员权限检查
        if review.creator_id != current_user_id:
            return error_response(message="无权限删除此评审")
        
        # 硬删除评审及相关数据
        from sqlalchemy import delete
        
        # 删除评审意见
        await db.execute(delete(ReviewComment).where(ReviewComment.review_id == review_id))
        
        # 删除评审分配
        await db.execute(delete(ReviewAssignment).where(ReviewAssignment.review_id == review_id))
        
        # 删除评审用例关联
        await db.execute(delete(ReviewTestCase).where(ReviewTestCase.review_id == review_id))
        
        # 删除评审记录
        await db.execute(delete(TestCaseReview).where(TestCaseReview.id == review_id))
        
        await db.commit()
        
        return success_response(data=None, message="删除评审成功")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[评审管理] 删除评审失败: {str(e)}")
        return error_response(message=f"删除评审失败: {str(e)}")


@router.put("/{review_id}", summary="更新评审")
async def update_review(
    review_id: int = Path(..., description="评审ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    review_data: ReviewUpdate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新评审信息"""
    try:
        # 获取现有评审
        review = await ReviewService.get_review_detail(
            db=db,
            review_id=review_id,
            project_id=project_id
        )
        
        if not review:
            return error_response(message="评审不存在")
        
        # 更新评审信息
        update_data = review_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
        await db.commit()
        await db.refresh(review)
        
        # 构建响应数据
        response_data = ReviewResponse(
            id=review.id,
            project_id=review.project_id,
            title=review.title,
            description=review.description,
            status=review.status,
            priority=review.priority,
            deadline=review.deadline,
            template_id=review.template_id,
            creator_id=review.creator_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
            completed_at=review.completed_at,
            test_case_count=0,  # TODO: 实际统计
            reviewer_count=0,   # TODO: 实际统计
            comment_count=0,    # TODO: 实际统计
            progress=0.0        # TODO: 实际计算
        )
        
        return success_response(data=response_data, message="更新评审成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 更新评审失败: {str(e)}")
        return error_response(message=f"更新评审失败: {str(e)}")


@router.put("/{review_id}/status", summary="更新评审状态")
async def update_review_status(
    review_id: int = Path(..., description="评审ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: str = Body(..., embed=True, description="新状态"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新评审状态"""
    try:
        review = await ReviewService.update_review_status(
            db=db,
            review_id=review_id,
            project_id=project_id,
            status=status,
            user_id=current_user_id
        )
        
        # 构建响应数据
        response_data = ReviewResponse(
            id=review.id,
            project_id=review.project_id,
            title=review.title,
            description=review.description,
            status=review.status,
            priority=review.priority,
            deadline=review.deadline,
            template_id=review.template_id,
            creator_id=review.creator_id,
            created_at=review.created_at,
            updated_at=review.updated_at,
            completed_at=review.completed_at,
            test_case_count=0,  # TODO: 实际统计
            reviewer_count=0,   # TODO: 实际统计
            comment_count=0,    # TODO: 实际统计
            progress=0.0        # TODO: 实际计算
        )
        
        return success_response(data=response_data, message="更新评审状态成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 更新评审状态失败: {str(e)}")
        return error_response(message=f"更新评审状态失败: {str(e)}")


# 评审分配接口
@router.post("/{review_id}/assignments", summary="分配评审人")
async def assign_reviewers(
    review_id: int = Path(..., description="评审ID"),
    reviewer_ids: List[int] = Body(..., embed=True, description="评审人ID列表"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """分配评审人"""
    try:
        assignments = await AssignmentService.assign_reviewers(
            db=db,
            review_id=review_id,
            reviewer_ids=reviewer_ids,
            assigner_id=current_user_id
        )
        
        # TODO: 构建响应数据，包含评审人信息
        return success_response(data=[], message="分配评审人成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 分配评审人失败: {str(e)}")
        return error_response(message=f"分配评审人失败: {str(e)}")


@router.put("/{review_id}/assignments/{reviewer_id}", summary="提交评审结果")
async def submit_review(
    review_id: int = Path(..., description="评审ID"),
    reviewer_id: int = Path(..., description="评审人ID"),
    assignment_data: AssignmentUpdate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """提交评审结果"""
    try:
        # 验证当前用户是否为指定的评审人
        if current_user_id != reviewer_id:
            return error_response(message="只能提交自己的评审结果")
        
        assignment = await AssignmentService.submit_review(
            db=db,
            review_id=review_id,
            reviewer_id=reviewer_id,
            assignment_data=assignment_data
        )
        
        return success_response(data=None, message="提交评审结果成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 提交评审结果失败: {str(e)}")
        return error_response(message=f"提交评审结果失败: {str(e)}")


# 评审意见接口
@router.post("/{review_id}/comments", summary="添加评审意见")
async def add_comment(
    review_id: int = Path(..., description="评审ID"),
    comment_data: CommentCreate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """添加评审意见"""
    try:
        comment = await CommentService.add_comment(
            db=db,
            review_id=review_id,
            comment_data=comment_data,
            author_id=current_user_id
        )
        
        return success_response(data=None, message="添加评审意见成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 添加评审意见失败: {str(e)}")
        return error_response(message=f"添加评审意见失败: {str(e)}")


@router.put("/comments/{comment_id}", summary="更新评审意见")
async def update_comment(
    comment_id: int = Path(..., description="意见ID"),
    comment_data: CommentUpdate = Body(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新评审意见"""
    try:
        # TODO: 验证权限，只有作者或管理员可以更新
        comment = await CommentService.update(
            db=db,
            id=comment_id,
            obj_in=comment_data
        )
        
        return success_response(data=None, message="更新评审意见成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 更新评审意见失败: {str(e)}")
        return error_response(message=f"更新评审意见失败: {str(e)}")
        return success_response(data=None, message="更新评审意见成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 更新评审意见失败: {str(e)}")
        return error_response(message=f"更新评审意见失败: {str(e)}")


# 评审相关数据接口将在/{review_id}路由之前定义


@router.post("/{review_id}/start", summary="开始评审任务")
async def start_review_task(
    review_id: int = Path(..., description="评审ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """评审人开始评审任务"""
    try:
        # 检查评审分配是否存在
        assignment_query = select(ReviewAssignment).where(
            and_(
                ReviewAssignment.review_id == review_id,
                ReviewAssignment.reviewer_id == current_user_id,
                ReviewAssignment.enabled_flag == 1
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()
        
        if not assignment:
            return error_response(message="未找到评审分配记录")
        
        if assignment.status != 'pending':
            return error_response(message="评审任务已经开始或已完成")
        
        # 更新分配状态为进行中
        assignment.status = 'in_progress'
        assignment.started_at = func.now()
        
        # 检查主评审记录状态，如果还是pending，更新为in_progress
        review_query = select(TestCaseReview).where(TestCaseReview.id == review_id)
        review_result = await db.execute(review_query)
        review = review_result.scalar_one_or_none()
        
        if review and review.status == 'pending':
            review.status = 'in_progress'
            review.updation_date = func.now()
        
        await db.commit()
        
        return success_response(data=None, message="开始评审任务成功")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[评审管理] 开始评审任务失败: {str(e)}")
        return error_response(message=f"开始评审任务失败: {str(e)}")


@router.get("/{review_id}/test-cases", summary="获取评审关联的测试用例")
async def get_review_test_cases(
    review_id: int = Path(..., description="评审ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取评审关联的测试用例列表"""
    try:
        from sqlalchemy import text
        
        # 查询评审关联的测试用例，包含完整信息和项目信息
        query = text("""
            SELECT 
                tc.id, 
                tc.title, 
                tc.description, 
                tc.preconditions,
                tc.expected_result,
                tc.priority, 
                tc.module_id,
                tc.test_type,
                tc.status,
                p.name as project_name
            FROM test_cases tc
            INNER JOIN review_test_cases rtc ON tc.id = rtc.test_case_id
            INNER JOIN projects p ON tc.project_id = p.id
            WHERE rtc.review_id = :review_id
            AND tc.enabled_flag = 1
            ORDER BY tc.id
        """)
        
        result = await db.execute(query, {"review_id": review_id})
        rows = result.fetchall()
        
        # 构建测试用例数据，使用真实的测试步骤
        test_case_list = []
        for row in rows:
            # 查询真实的测试步骤
            steps_query = text("""
                SELECT 
                    id,
                    step_number,
                    action as description,
                    expected
                FROM test_case_steps
                WHERE test_case_id = :test_case_id
                AND enabled_flag = 1
                ORDER BY step_number
            """)
            
            steps_result = await db.execute(steps_query, {"test_case_id": row.id})
            steps_rows = steps_result.fetchall()
            
            # 构建步骤数据
            steps = []
            for step_row in steps_rows:
                steps.append({
                    "id": step_row.id,
                    "step_number": step_row.step_number,
                    "description": step_row.description,
                    "expected_result": step_row.expected
                })
            
            # 如果没有具体步骤，使用基本信息构建一个简单步骤
            if not steps and row.description:
                steps = [
                    {
                        "id": row.id * 1000 + 1,
                        "step_number": 1,
                        "description": row.description,
                        "expected_result": row.expected_result or "测试通过"
                    }
                ]
            
            test_case_data = {
                "id": row.id,
                "title": row.title,
                "description": row.description or f"测试{row.title}的功能",
                "preconditions": row.preconditions,
                "expected_result": row.expected_result,
                "priority": row.priority,
                "module_id": row.module_id,
                "test_type": row.test_type,
                "status": row.status,
                "project_name": row.project_name,  # 添加项目名称
                "steps": steps
            }
            test_case_list.append(test_case_data)
        
        return success_response(data=test_case_list, message="获取测试用例成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取测试用例失败: {str(e)}")
        return error_response(message=f"获取测试用例失败: {str(e)}")


@router.get("/{review_id}/reviewers", summary="获取评审人员")
async def get_review_reviewers(
    review_id: int = Path(..., description="评审ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取评审人员列表"""
    try:
        from sqlalchemy import text
        
        # 查询评审人员信息
        query = text("""
            SELECT ra.reviewer_id, ra.status, ra.comment, ra.reviewed_at,
                   u.username, u.nickname
            FROM review_assignments ra
            INNER JOIN sys_user u ON ra.reviewer_id = u.id
            WHERE ra.review_id = :review_id
            AND ra.enabled_flag = 1
            ORDER BY ra.id
        """)
        
        result = await db.execute(query, {"review_id": review_id})
        reviewers = result.fetchall()
        
        reviewer_list = []
        for reviewer in reviewers:
            reviewer_list.append({
                "id": reviewer.reviewer_id,
                "username": reviewer.username,
                "nickname": reviewer.nickname,
                "name": reviewer.nickname or reviewer.username,
                "status": reviewer.status,
                "comment": reviewer.comment,
                "reviewed_at": reviewer.reviewed_at.isoformat() if reviewer.reviewed_at else None
            })
        
        return success_response(data=reviewer_list, message="获取评审人员成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审人员失败: {str(e)}")
        return error_response(message=f"获取评审人员失败: {str(e)}")


@router.get("/{review_id}/comments", summary="获取评审意见列表")
async def get_review_comments(
    review_id: int = Path(..., description="评审ID"),
    test_case_id: Optional[int] = Query(None, description="测试用例ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db)
):
    """获取评审意见列表（来自评审结果）"""
    try:
        from sqlalchemy import text
        
        # 构建查询条件
        where_conditions = ["rr.review_id = :review_id", "rr.comment IS NOT NULL", "rr.comment != ''"]
        params = {"review_id": review_id}
        
        if test_case_id:
            where_conditions.append("rr.test_case_id = :test_case_id")
            params["test_case_id"] = test_case_id
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询评审意见
        query = text(f"""
            SELECT 
                rr.id,
                rr.test_case_id,
                rr.reviewer_id,
                rr.result,
                rr.comment,
                rr.creation_date,
                tc.title as test_case_title,
                u.nickname,
                u.username
            FROM review_results rr
            INNER JOIN test_cases tc ON rr.test_case_id = tc.id
            INNER JOIN sys_user u ON rr.reviewer_id = u.id
            WHERE {where_clause}
            ORDER BY rr.creation_date DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": page_size,
            "offset": (page - 1) * page_size
        })
        
        result = await db.execute(query, params)
        comments = result.fetchall()
        
        # 查询总数
        count_query = text(f"""
            SELECT COUNT(*)
            FROM review_results rr
            INNER JOIN test_cases tc ON rr.test_case_id = tc.id
            WHERE {where_clause}
        """)
        
        count_result = await db.execute(count_query, {k: v for k, v in params.items() if k not in ['limit', 'offset']})
        total = count_result.scalar() or 0
        
        # 构建响应数据
        comment_list = []
        for comment in comments:
            comment_data = {
                "id": comment.id,
                "review_id": review_id,
                "test_case_id": comment.test_case_id,
                "test_case_title": comment.test_case_title,
                "author_id": comment.reviewer_id,
                "author_name": comment.nickname or comment.username,
                "comment_type": "review_result",  # 标识这是评审结果中的意见
                "content": comment.comment,
                "result": comment.result,  # 添加评审结果
                "is_resolved": True,  # 评审结果默认为已解决
                "created_at": comment.creation_date.isoformat() if comment.creation_date else None
            }
            comment_list.append(comment_data)
        
        paginated_data = {
            "rows": comment_list,
            "rowTotal": total,
            "page": page,
            "pageSize": page_size,
            "pageTotal": (total + page_size - 1) // page_size
        }
        
        return success_response(data=paginated_data, message="获取评审意见列表成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审意见列表失败: {str(e)}")
        return error_response(message=f"获取评审意见列表失败: {str(e)}")


@router.post("/{review_id}/testcases/{testcase_id}/review", summary="保存测试用例评审结果")
async def save_testcase_review_result(
    review_id: int = Path(..., description="评审ID"),
    testcase_id: int = Path(..., description="测试用例ID"),
    result_data: dict = Body(..., description="评审结果数据"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """保存单个测试用例的评审结果"""
    try:
        from sqlalchemy import select, delete
        from .model import ReviewResult
        
        # 验证评审分配是否存在
        assignment_query = select(ReviewAssignment).where(
            and_(
                ReviewAssignment.review_id == review_id,
                ReviewAssignment.reviewer_id == current_user_id,
                ReviewAssignment.enabled_flag == 1
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()
        
        if not assignment:
            return error_response(message="未找到评审分配记录")
        
        # 删除已存在的评审结果
        await db.execute(
            delete(ReviewResult).where(
                and_(
                    ReviewResult.review_id == review_id,
                    ReviewResult.test_case_id == testcase_id,
                    ReviewResult.reviewer_id == current_user_id
                )
            )
        )
        
        # 创建新的评审结果
        review_result = ReviewResult(
            review_id=review_id,
            test_case_id=testcase_id,
            reviewer_id=current_user_id,
            result=result_data.get('result'),
            comment=result_data.get('comment'),
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        db.add(review_result)
        await db.commit()
        
        return success_response(data=None, message="保存评审结果成功")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[评审管理] 保存评审结果失败: {str(e)}")
        return error_response(message=f"保存评审结果失败: {str(e)}")


@router.post("/{review_id}/complete", summary="完成评审")
async def complete_review_task(
    review_id: int = Path(..., description="评审ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """完成评审任务"""
    try:
        # 检查评审分配是否存在
        assignment_query = select(ReviewAssignment).where(
            and_(
                ReviewAssignment.review_id == review_id,
                ReviewAssignment.reviewer_id == current_user_id,
                ReviewAssignment.enabled_flag == 1
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()
        
        if not assignment:
            return error_response(message="未找到评审分配记录")
        
        if assignment.status == 'completed':
            return error_response(message="评审任务已完成")
        
        # 更新评审分配状态
        assignment.status = 'completed'
        assignment.reviewed_at = func.now()
        
        # 检查是否所有评审人都已完成
        all_assignments_query = select(ReviewAssignment).where(
            and_(
                ReviewAssignment.review_id == review_id,
                ReviewAssignment.enabled_flag == 1
            )
        )
        all_assignments_result = await db.execute(all_assignments_query)
        all_assignments = all_assignments_result.scalars().all()
        
        # 统计完成状态
        completed_count = sum(1 for a in all_assignments if a.status == 'completed')
        total_count = len(all_assignments)
        
        # 如果所有评审人都完成了，更新主评审状态
        if completed_count == total_count:
            review_query = select(TestCaseReview).where(TestCaseReview.id == review_id)
            review_result = await db.execute(review_query)
            review = review_result.scalar_one_or_none()
            
            if review:
                review.status = 'completed'
                review.completed_at = func.now()
                review.updation_date = func.now()
        
        await db.commit()
        
        return success_response(data=None, message="完成评审任务成功")
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[评审管理] 完成评审任务失败: {str(e)}")
        return error_response(message=f"完成评审任务失败: {str(e)}")


@router.get("/{review_id}/my-results", summary="获取我的评审结果")
async def get_my_review_results(
    review_id: int = Path(..., description="评审ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户对该评审的所有评审结果"""
    try:
        from sqlalchemy import text
        
        # 查询当前用户对该评审的所有评审结果
        query = text("""
            SELECT 
                rr.test_case_id,
                rr.result,
                rr.comment,
                rr.reviewed_at,
                tc.title as test_case_title
            FROM review_results rr
            INNER JOIN test_cases tc ON rr.test_case_id = tc.id
            WHERE rr.review_id = :review_id
            AND rr.reviewer_id = :reviewer_id
            ORDER BY rr.reviewed_at ASC
        """)
        
        result = await db.execute(query, {
            "review_id": review_id,
            "reviewer_id": current_user_id
        })
        results = result.fetchall()
        
        # 构建结果字典
        review_results = {}
        for row in results:
            review_results[row.test_case_id] = {
                "result": row.result,
                "comment": row.comment,
                "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
                "test_case_title": row.test_case_title
            }
        
        return success_response(data=review_results, message="获取评审结果成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审结果失败: {str(e)}")
        return error_response(message=f"获取评审结果失败: {str(e)}")


@router.get("/{review_id}/results", summary="获取评审结果列表")
async def get_review_results(
    review_id: int = Path(..., description="评审ID"),
    result: Optional[str] = Query(None, description="结果筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取评审结果列表"""
    try:
        from sqlalchemy import text
        
        # 构建查询条件
        where_conditions = ["rr.review_id = :review_id", "rr.reviewer_id = :reviewer_id"]
        params = {"review_id": review_id, "reviewer_id": current_user_id}
        
        if result:
            where_conditions.append("rr.result = :result")
            params["result"] = result
            
        if keyword:
            where_conditions.append("tc.title LIKE :keyword")
            params["keyword"] = f"%{keyword}%"
        
        where_clause = " AND ".join(where_conditions)
        
        # 查询评审结果
        query = text(f"""
            SELECT 
                rr.id,
                rr.test_case_id,
                tc.title as test_case_title,
                tc.description,
                rr.result,
                rr.comment,
                rr.reviewed_at
            FROM review_results rr
            INNER JOIN test_cases tc ON rr.test_case_id = tc.id
            WHERE {where_clause}
            ORDER BY rr.reviewed_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        params.update({
            "limit": page_size,
            "offset": (page - 1) * page_size
        })
        
        result_data = await db.execute(query, params)
        results = result_data.fetchall()
        
        # 查询总数
        count_query = text(f"""
            SELECT COUNT(*)
            FROM review_results rr
            INNER JOIN test_cases tc ON rr.test_case_id = tc.id
            WHERE {where_clause}
        """)
        
        count_result = await db.execute(count_query, {k: v for k, v in params.items() if k not in ['limit', 'offset']})
        total = count_result.scalar() or 0
        
        # 构建响应数据
        result_list = []
        for result_row in results:
            result_item = {
                "id": result_row.id,
                "testCaseId": result_row.test_case_id,
                "testCaseTitle": result_row.test_case_title,
                "description": result_row.description,
                "result": result_row.result,
                "comment": result_row.comment,
                "reviewedAt": result_row.reviewed_at.isoformat() if result_row.reviewed_at else None,
            }
            result_list.append(result_item)
        
        paginated_data = {
            "rows": result_list,
            "rowTotal": total,
            "page": page,
            "pageSize": page_size,
            "pageTotal": (total + page_size - 1) // page_size
        }
        
        return success_response(data=paginated_data, message="获取评审结果成功")
        
    except Exception as e:
        logger.error(f"[评审管理] 获取评审结果失败: {str(e)}")
        return error_response(message=f"获取评审结果失败: {str(e)}")


# AI评审相关接口
@router.get("/{review_id}/ai-review/availability", summary="检查AI评审功能可用性")
async def check_ai_review_availability(
    review_id: int = Path(..., description="评审ID"),
    db: AsyncSession = Depends(get_db)
):
    """检查AI评审功能是否可用"""
    try:
        availability = await ReviewAIService.check_ai_review_availability(db)
        return success_response(data=availability, message="检查AI评审可用性成功")
        
    except Exception as e:
        logger.error(f"[AI评审] 检查可用性失败: {str(e)}")
        return error_response(message=f"检查AI评审可用性失败: {str(e)}")


@router.post("/{review_id}/ai-review/single", summary="AI评审单个测试用例")
async def ai_review_single_test_case(
    review_id: int = Path(..., description="评审ID"),
    test_case_data: dict = Body(..., description="测试用例数据"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """AI评审单个测试用例"""
    try:
        # 构建评审上下文
        review_context = {
            "review_id": review_id,
            "reviewer_id": current_user_id
        }
        
        # 调用AI评审服务
        result = await ReviewAIService.ai_review_test_case(
            db, test_case_data, review_context
        )
        
        return success_response(data=result, message="AI评审完成")
        
    except Exception as e:
        logger.error(f"[AI评审] 单个用例评审失败: {str(e)}")
        return error_response(message=f"AI评审失败: {str(e)}")


@router.post("/{review_id}/ai-review/batch", summary="批量AI评审测试用例")
async def ai_review_batch_test_cases(
    review_id: int = Path(..., description="评审ID"),
    request_data: dict = Body(..., description="批量评审请求数据"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """批量AI评审测试用例"""
    try:
        test_case_ids = request_data.get("test_case_ids", [])
        if not test_case_ids:
            return error_response(message="请选择要评审的测试用例")
        
        # 获取测试用例数据
        from sqlalchemy import text
        query = text("""
            SELECT 
                tc.id, 
                tc.title, 
                tc.description, 
                tc.preconditions,
                tc.expected_result,
                tc.priority, 
                tc.module_id
            FROM test_cases tc
            INNER JOIN review_test_cases rtc ON tc.id = rtc.test_case_id
            WHERE rtc.review_id = :review_id
            AND tc.id IN :test_case_ids
            AND tc.enabled_flag = 1
            ORDER BY tc.id
        """)
        
        result = await db.execute(query, {
            "review_id": review_id,
            "test_case_ids": tuple(test_case_ids)
        })
        test_cases = result.fetchall()
        
        if not test_cases:
            return error_response(message="未找到指定的测试用例")
        
        # 转换为字典格式
        test_case_list = []
        for tc in test_cases:
            # 获取测试步骤
            steps_query = text("""
                SELECT 
                    step_number,
                    action as description,
                    expected
                FROM test_case_steps
                WHERE test_case_id = :test_case_id
                AND enabled_flag = 1
                ORDER BY step_number
            """)
            
            steps_result = await db.execute(steps_query, {"test_case_id": tc.id})
            steps_rows = steps_result.fetchall()
            
            steps = []
            for step_row in steps_rows:
                steps.append({
                    "step_number": step_row.step_number,
                    "description": step_row.description,
                    "expected_result": step_row.expected
                })
            
            test_case_list.append({
                "id": tc.id,
                "title": tc.title,
                "description": tc.description,
                "preconditions": tc.preconditions,
                "expected_result": tc.expected_result,
                "priority": tc.priority,
                "module_id": tc.module_id,
                "steps": steps
            })
        
        # 构建评审上下文
        review_context = {
            "review_id": review_id,
            "reviewer_id": current_user_id,
            "batch_mode": True
        }
        
        # 调用批量AI评审服务
        result = await ReviewAIService.batch_ai_review(
            db, test_case_list, review_context
        )
        
        return success_response(data=result, message="批量AI评审完成")
        
    except Exception as e:
        logger.error(f"[AI评审] 批量评审失败: {str(e)}")
        return error_response(message=f"批量AI评审失败: {str(e)}")


@router.post("/my-tasks/{review_id}/ai-pre-review", summary="AI预评审所有测试用例")
async def ai_pre_review_all_cases(
    review_id: int = Path(..., description="评审ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """AI预评审所有测试用例，完成后状态变为人工审核"""
    try:
        # 检查AI评审功能可用性
        availability = await ReviewAIService.check_ai_review_availability(db)
        if not availability.get("available"):
            return error_response(message=availability.get("error", "AI评审功能不可用"))
        
        # 检查评审任务是否存在且属于当前用户
        from sqlalchemy import text, select
        assignment_query = select(text("1")).select_from(text("review_assignments")).where(
            text("review_id = :review_id AND reviewer_id = :reviewer_id AND enabled_flag = 1")
        )
        assignment_result = await db.execute(assignment_query, {
            "review_id": review_id,
            "reviewer_id": current_user_id
        })
        
        if not assignment_result.fetchone():
            return error_response(message="评审任务不存在或无权限")
        
        # 执行AI预评审
        result = await ReviewAIService.ai_pre_review_all_cases(
            db=db,
            review_id=review_id,
            reviewer_id=current_user_id
        )
        
        if result.get("success"):
            return success_response(data=result, message="AI预评审完成，任务状态已更新为人工审核")
        else:
            return error_response(message=result.get("error", "AI预评审失败"))
        
    except Exception as e:
        logger.error(f"[AI评审] AI预评审失败: {str(e)}")
        return error_response(message=f"AI预评审失败: {str(e)}")


@router.get("/my-tasks/{review_id}/ai-pre-review/summary", summary="获取AI预评审摘要")
async def get_ai_pre_review_summary(
    review_id: int = Path(..., description="评审ID"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取AI预评审摘要统计"""
    try:
        summary = await ReviewAIService.get_ai_pre_review_summary(
            db=db,
            review_id=review_id,
            reviewer_id=current_user_id
        )
        
        return success_response(data=summary, message="获取AI预评审摘要成功")
        
    except Exception as e:
        logger.error(f"[AI评审] 获取AI预评审摘要失败: {str(e)}")
        return error_response(message=f"获取AI预评审摘要失败: {str(e)}")