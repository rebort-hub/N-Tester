# 用例评审模块 - 业务逻辑层

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload, joinedload

from app.core.base_crud import BaseCRUD
from app.corelibs.logger import logger
from app.exceptions.exceptions import MyBaseException
from .model import (
    TestCaseReview, ReviewTestCase, ReviewAssignment, 
    ReviewComment, ReviewTemplate, TemplateProject, TemplateDefaultReviewer
)
from .schema import (
    ReviewCreate, ReviewUpdate, AssignmentCreate, AssignmentUpdate,
    CommentCreate, CommentUpdate, TemplateCreate, TemplateUpdate,
    ReviewStatistics
)


class ReviewService:
    """评审服务类"""
    
    @classmethod
    async def create_review(
        cls,
        db: AsyncSession,
        review_data: ReviewCreate,
        creator_id: int
    ) -> TestCaseReview:
        """
        创建评审
        
        Args:
            db: 数据库会话
            review_data: 评审数据
            creator_id: 创建人ID
            
        Returns:
            创建的评审对象
        """
        try:
            # 创建评审
            review = TestCaseReview(
                project_id=review_data.project_id,
                title=review_data.title,
                description=review_data.description,
                priority=review_data.priority,
                deadline=review_data.deadline,
                template_id=review_data.template_id,
                creator_id=creator_id,
                status='pending'
            )
            
            db.add(review)
            await db.flush()  # 获取ID
            
            # 收集所有需要关联的测试用例ID
            all_test_case_ids = set()
            
            # 如果指定了模块ID，获取模块下的所有测试用例
            if review_data.module_ids:
                from sqlalchemy import select, text
                
                # 查询指定模块下的所有测试用例
                query = text("""
                    SELECT id FROM test_cases 
                    WHERE module_id IN :module_ids 
                    AND project_id = :project_id 
                    AND enabled_flag = 1
                """)
                
                result = await db.execute(query, {
                    "module_ids": tuple(review_data.module_ids),
                    "project_id": review_data.project_id
                })
                
                module_test_cases = result.fetchall()
                for row in module_test_cases:
                    all_test_case_ids.add(row.id)
            
            # 添加直接指定的测试用例ID
            if review_data.test_case_ids:
                all_test_case_ids.update(review_data.test_case_ids)
            
            # 关联测试用例
            for test_case_id in all_test_case_ids:
                review_case = ReviewTestCase(
                    review_id=review.id,
                    test_case_id=test_case_id
                )
                db.add(review_case)
            
            # 分配评审人
            if review_data.reviewer_ids:
                for reviewer_id in review_data.reviewer_ids:
                    assignment = ReviewAssignment(
                        review_id=review.id,
                        reviewer_id=reviewer_id,
                        status='pending'
                    )
                    db.add(assignment)
            
            await db.commit()
            await db.refresh(review)
            
            logger.info(f"[评审管理] 创建评审成功: {review.id}")
            return review
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 创建评审失败: {str(e)}")
            raise MyBaseException(f"创建评审失败: {str(e)}")
    
    @classmethod
    async def get_review_list(
        cls,
        db: AsyncSession,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        creator_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TestCaseReview], int]:
        """
        获取评审列表
        
        Args:
            db: 数据库会话
            project_id: 项目ID（可选）
            status: 状态筛选
            priority: 优先级筛选
            creator_id: 创建人筛选
            reviewer_id: 评审人筛选
            page: 页码
            page_size: 每页大小
            
        Returns:
            评审列表和总数
        """
        try:
            # 构建查询条件
            conditions = []
            
            if project_id:
                conditions.append(TestCaseReview.project_id == project_id)
            if status:
                conditions.append(TestCaseReview.status == status)
            if priority:
                conditions.append(TestCaseReview.priority == priority)
            if creator_id:
                conditions.append(TestCaseReview.creator_id == creator_id)
            
            # 如果按评审人筛选，需要关联查询
            query = select(TestCaseReview)
            if conditions:
                query = query.where(and_(*conditions))
            
            if reviewer_id:
                query = query.join(ReviewAssignment).where(
                    ReviewAssignment.reviewer_id == reviewer_id
                )
            
            # 获取总数
            count_query = select(func.count(TestCaseReview.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))
            if reviewer_id:
                count_query = count_query.join(ReviewAssignment).where(
                    ReviewAssignment.reviewer_id == reviewer_id
                )
            
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页查询
            query = query.order_by(desc(TestCaseReview.creation_date))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            reviews = result.scalars().all()
            
            return list(reviews), total
            
        except Exception as e:
            logger.error(f"[评审管理] 获取评审列表失败: {str(e)}")
            raise MyBaseException(f"获取评审列表失败: {str(e)}")
    
    @classmethod
    async def get_review_detail(
        cls,
        db: AsyncSession,
        review_id: int,
        project_id: Optional[int] = None
    ) -> Optional[TestCaseReview]:
        """
        获取评审详情
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            project_id: 项目ID（可选）
            
        Returns:
            评审详情
        """
        try:
            conditions = [TestCaseReview.id == review_id]
            if project_id:
                conditions.append(TestCaseReview.project_id == project_id)
            
            query = select(TestCaseReview).where(and_(*conditions))
            
            result = await db.execute(query)
            review = result.scalar_one_or_none()
            
            if not review:
                raise MyBaseException("评审不存在")
            
            return review
            
        except MyBaseException:
            raise
        except Exception as e:
            logger.error(f"[评审管理] 获取评审详情失败: {str(e)}")
            raise MyBaseException(f"获取评审详情失败: {str(e)}")
    
    @classmethod
    async def update_review_status(
        cls,
        db: AsyncSession,
        review_id: int,
        project_id: int,
        status: str,
        user_id: int
    ) -> TestCaseReview:
        """
        更新评审状态
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            project_id: 项目ID
            status: 新状态
            user_id: 操作用户ID
            
        Returns:
            更新后的评审对象
        """
        try:
            review = await cls.get_review_detail(db, review_id, project_id)
            
            old_status = review.status
            review.status = status
            
            # 如果状态变为完成，记录完成时间
            if status == 'completed' and old_status != 'completed':
                review.completed_at = datetime.now()
            
            await db.commit()
            await db.refresh(review)
            
            logger.info(f"[评审管理] 更新评审状态: {review_id} {old_status} -> {status}")
            return review
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 更新评审状态失败: {str(e)}")
            raise MyBaseException(f"更新评审状态失败: {str(e)}")


class AssignmentService:
    """评审分配服务类"""
    
    @classmethod
    async def assign_reviewers(
        cls,
        db: AsyncSession,
        review_id: int,
        reviewer_ids: List[int],
        assigner_id: int
    ) -> List[ReviewAssignment]:
        """
        分配评审人
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            reviewer_ids: 评审人ID列表
            assigner_id: 分配人ID
            
        Returns:
            分配记录列表
        """
        try:
            assignments = []
            
            for reviewer_id in reviewer_ids:
                # 检查是否已经分配
                existing_query = select(ReviewAssignment).where(
                    and_(
                        ReviewAssignment.review_id == review_id,
                        ReviewAssignment.reviewer_id == reviewer_id
                    )
                )
                existing_result = await db.execute(existing_query)
                existing = existing_result.scalar_one_or_none()
                
                if not existing:
                    assignment = ReviewAssignment(
                        review_id=review_id,
                        reviewer_id=reviewer_id,
                        status='pending'
                    )
                    db.add(assignment)
                    assignments.append(assignment)
            
            await db.commit()
            
            logger.info(f"[评审管理] 分配评审人成功: 评审{review_id}, 新增{len(assignments)}人")
            return assignments
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 分配评审人失败: {str(e)}")
            raise MyBaseException(f"分配评审人失败: {str(e)}")
    
    @classmethod
    async def submit_review(
        cls,
        db: AsyncSession,
        review_id: int,
        reviewer_id: int,
        assignment_data: AssignmentUpdate
    ) -> ReviewAssignment:
        """
        提交评审结果
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            reviewer_id: 评审人ID
            assignment_data: 评审数据
            
        Returns:
            更新后的分配记录
        """
        try:
            # 查找分配记录
            query = select(ReviewAssignment).where(
                and_(
                    ReviewAssignment.review_id == review_id,
                    ReviewAssignment.reviewer_id == reviewer_id
                )
            )
            result = await db.execute(query)
            assignment = result.scalar_one_or_none()
            
            if not assignment:
                raise MyBaseException("评审分配不存在")
            
            # 更新评审结果
            if assignment_data.status:
                assignment.status = assignment_data.status
            if assignment_data.comment:
                assignment.comment = assignment_data.comment
            if assignment_data.checklist_results:
                assignment.checklist_results = assignment_data.checklist_results
            
            assignment.reviewed_at = datetime.now()
            
            await db.commit()
            await db.refresh(assignment)
            
            logger.info(f"[评审管理] 提交评审结果: 评审{review_id}, 评审人{reviewer_id}")
            return assignment
            
        except MyBaseException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 提交评审结果失败: {str(e)}")
            raise MyBaseException(f"提交评审结果失败: {str(e)}")


class CommentService:
    """评审意见服务类"""
    
    @classmethod
    async def add_comment(
        cls,
        db: AsyncSession,
        review_id: int,
        comment_data: CommentCreate,
        author_id: int
    ) -> ReviewComment:
        """
        添加评审意见
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            comment_data: 意见数据
            author_id: 评论者ID
            
        Returns:
            创建的意见对象
        """
        try:
            comment = ReviewComment(
                review_id=review_id,
                test_case_id=comment_data.test_case_id,
                author_id=author_id,
                comment_type=comment_data.comment_type,
                content=comment_data.content,
                step_number=comment_data.step_number,
                is_resolved=False
            )
            
            db.add(comment)
            await db.commit()
            await db.refresh(comment)
            
            logger.info(f"[评审管理] 添加评审意见: 评审{review_id}, 意见{comment.id}")
            return comment
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 添加评审意见失败: {str(e)}")
            raise MyBaseException(f"添加评审意见失败: {str(e)}")
    
    @classmethod
    async def get_review_comments(
        cls,
        db: AsyncSession,
        review_id: int,
        test_case_id: Optional[int] = None,
        is_resolved: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ReviewComment], int]:
        """
        获取评审意见列表
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            test_case_id: 测试用例ID筛选
            is_resolved: 是否已解决筛选
            page: 页码
            page_size: 每页大小
            
        Returns:
            意见列表和总数
        """
        try:
            conditions = [ReviewComment.review_id == review_id]
            
            if test_case_id:
                conditions.append(ReviewComment.test_case_id == test_case_id)
            if is_resolved is not None:
                conditions.append(ReviewComment.is_resolved == is_resolved)
            
            # 获取总数
            count_query = select(func.count(ReviewComment.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页查询
            query = select(ReviewComment).where(and_(*conditions))
            query = query.order_by(asc(ReviewComment.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            comments = result.scalars().all()
            
            return list(comments), total
            
        except Exception as e:
            logger.error(f"[评审管理] 获取评审意见失败: {str(e)}")
            raise MyBaseException(f"获取评审意见失败: {str(e)}")


class TemplateService:
    """评审模板服务类"""
    
    @classmethod
    async def create_template(
        cls,
        db: AsyncSession,
        template_data: TemplateCreate,
        creator_id: int
    ) -> ReviewTemplate:
        """
        创建评审模板
        
        Args:
            db: 数据库会话
            template_data: 模板数据
            creator_id: 创建人ID
            
        Returns:
            创建的模板对象
        """
        try:
            # 创建模板
            template = ReviewTemplate(
                name=template_data.name,
                description=template_data.description,
                checklist=template_data.checklist,
                creator_id=creator_id,
                is_active=True
            )
            
            db.add(template)
            await db.flush()  # 获取ID
            
            # 关联项目
            if template_data.project_ids:
                for project_id in template_data.project_ids:
                    template_project = TemplateProject(
                        template_id=template.id,
                        project_id=project_id
                    )
                    db.add(template_project)
            
            # 设置默认评审人
            if template_data.default_reviewer_ids:
                for reviewer_id in template_data.default_reviewer_ids:
                    default_reviewer = TemplateDefaultReviewer(
                        template_id=template.id,
                        user_id=reviewer_id
                    )
                    db.add(default_reviewer)
            
            await db.commit()
            await db.refresh(template)
            
            logger.info(f"[评审管理] 创建评审模板成功: {template.id}")
            return template
            
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 创建评审模板失败: {str(e)}")
            raise MyBaseException(f"创建评审模板失败: {str(e)}")
    
    @classmethod
    async def get_template_list(
        cls,
        db: AsyncSession,
        project_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ReviewTemplate], int]:
        """
        获取评审模板列表
        
        Args:
            db: 数据库会话
            project_id: 项目ID筛选
            is_active: 是否启用筛选
            page: 页码
            page_size: 每页大小
            
        Returns:
            模板列表和总数
        """
        try:
            conditions = []
            
            if is_active is not None:
                conditions.append(ReviewTemplate.is_active == is_active)
            
            # 构建基础查询
            query = select(ReviewTemplate)
            
            # 如果按项目筛选，需要关联查询
            if project_id:
                query = query.join(TemplateProject).where(
                    TemplateProject.project_id == project_id
                )
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # 获取总数
            count_query = select(func.count(ReviewTemplate.id))
            if project_id:
                count_query = count_query.select_from(
                    ReviewTemplate.__table__.join(TemplateProject.__table__)
                ).where(TemplateProject.project_id == project_id)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            total_result = await db.execute(count_query)
            total = total_result.scalar() or 0
            
            # 分页查询
            query = query.order_by(desc(ReviewTemplate.creation_date))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            result = await db.execute(query)
            templates = result.scalars().all()
            
            return list(templates), total
            
        except Exception as e:
            logger.error(f"[评审管理] 获取模板列表失败: {str(e)}")
            raise MyBaseException(f"获取模板列表失败: {str(e)}")
    
    @classmethod
    async def get_template_detail(
        cls,
        db: AsyncSession,
        template_id: int
    ) -> Optional[ReviewTemplate]:
        """
        获取模板详情
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            
        Returns:
            模板详情
        """
        try:
            query = select(ReviewTemplate).where(ReviewTemplate.id == template_id)
            result = await db.execute(query)
            template = result.scalar_one_or_none()
            
            return template
            
        except Exception as e:
            logger.error(f"[评审管理] 获取模板详情失败: {str(e)}")
            raise MyBaseException(f"获取模板详情失败: {str(e)}")
    
    @classmethod
    async def update_template(
        cls,
        db: AsyncSession,
        template_id: int,
        template_data: TemplateUpdate,
        user_id: int
    ) -> ReviewTemplate:
        """
        更新评审模板
        
        Args:
            db: 数据库会话
            template_id: 模板ID
            template_data: 更新数据
            user_id: 操作用户ID
            
        Returns:
            更新后的模板对象
        """
        try:
            template = await cls.get_template_detail(db, template_id)
            if not template:
                raise MyBaseException("模板不存在")
            
            # 更新基本信息
            update_data = template_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(template, field, value)
            
            await db.commit()
            await db.refresh(template)
            
            logger.info(f"[评审管理] 更新评审模板成功: {template.id}")
            return template
            
        except MyBaseException:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"[评审管理] 更新评审模板失败: {str(e)}")
            raise MyBaseException(f"更新评审模板失败: {str(e)}")
    
    @classmethod
    async def get_statistics(
        cls,
        db: AsyncSession,
        project_id: int
    ) -> ReviewStatistics:
        """
        获取评审统计信息
        
        Args:
            db: 数据库会话
            project_id: 项目ID
            
        Returns:
            统计信息
        """
        try:
            # 基础统计
            base_query = select(TestCaseReview).where(TestCaseReview.project_id == project_id)
            
            # 总评审数
            total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
            total_reviews = total_result.scalar() or 0
            
            # 各状态统计
            status_stats = {}
            for status in ['pending', 'in_progress', 'completed', 'cancelled']:
                status_query = select(func.count(TestCaseReview.id)).where(
                    and_(
                        TestCaseReview.project_id == project_id,
                        TestCaseReview.status == status
                    )
                )
                result = await db.execute(status_query)
                status_stats[status] = result.scalar() or 0
            
            # 逾期评审数
            now = datetime.now()
            overdue_query = select(func.count(TestCaseReview.id)).where(
                and_(
                    TestCaseReview.project_id == project_id,
                    TestCaseReview.deadline < now,
                    TestCaseReview.status.in_(['pending', 'in_progress'])
                )
            )
            overdue_result = await db.execute(overdue_query)
            overdue_reviews = overdue_result.scalar() or 0
            
            # 平均完成时间
            avg_time_query = select(
                func.avg(
                    func.timestampdiff(
                        'HOUR',
                        TestCaseReview.created_at,
                        TestCaseReview.completed_at
                    )
                )
            ).where(
                and_(
                    TestCaseReview.project_id == project_id,
                    TestCaseReview.status == 'completed',
                    TestCaseReview.completed_at.isnot(None)
                )
            )
            avg_time_result = await db.execute(avg_time_query)
            avg_completion_time = avg_time_result.scalar() or 0.0
            
            # 评论统计
            comment_query = select(func.count(ReviewComment.id)).select_from(
                ReviewComment.__table__.join(
                    TestCaseReview.__table__,
                    ReviewComment.review_id == TestCaseReview.id
                )
            ).where(TestCaseReview.project_id == project_id)
            comment_result = await db.execute(comment_query)
            total_comments = comment_result.scalar() or 0
            
            # 未解决评论数
            unresolved_query = select(func.count(ReviewComment.id)).select_from(
                ReviewComment.__table__.join(
                    TestCaseReview.__table__,
                    ReviewComment.review_id == TestCaseReview.id
                )
            ).where(
                and_(
                    TestCaseReview.project_id == project_id,
                    ReviewComment.is_resolved == False
                )
            )
            unresolved_result = await db.execute(unresolved_query)
            unresolved_comments = unresolved_result.scalar() or 0
            
            return ReviewStatistics(
                total_reviews=total_reviews,
                pending_reviews=status_stats['pending'],
                in_progress_reviews=status_stats['in_progress'],
                completed_reviews=status_stats['completed'],
                cancelled_reviews=status_stats['cancelled'],
                overdue_reviews=overdue_reviews,
                avg_completion_time=avg_completion_time,
                total_comments=total_comments,
                unresolved_comments=unresolved_comments
            )
            
        except Exception as e:
            logger.error(f"[评审管理] 获取统计信息失败: {str(e)}")
            raise MyBaseException(f"获取统计信息失败: {str(e)}")