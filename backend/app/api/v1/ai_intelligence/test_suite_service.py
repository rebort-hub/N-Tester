"""
AI测试套件服务层
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete, update
from sqlalchemy.orm import selectinload

from .model import (
    AITestSuiteModel,
    AITestSuiteModuleModel,
    AITestSuiteExecutionModel,
    AITestSuiteModuleExecutionModel,
    AICaseModel,
    AIExecutionRecordModel
)
from .schema import (
    AITestSuiteCreateSchema,
    AITestSuiteUpdateSchema,
    AITestSuiteExecutionCreateSchema
)

logger = logging.getLogger(__name__)


class AITestSuiteService:
    """AI测试套件服务"""
    
    @staticmethod
    async def create_suite(
        db: AsyncSession,
        suite_data: AITestSuiteCreateSchema,
        user_id: int
    ) -> AITestSuiteModel:
        """创建测试套件"""
        try:
            # 创建套件
            suite = AITestSuiteModel(
                name=suite_data.name,
                description=suite_data.description,
                project_id=suite_data.project_id,
                status='active',
                created_by=user_id,
                enabled_flag=1
            )
            
            db.add(suite)
            await db.flush()
            
            # 创建模块关联
            for module_data in suite_data.modules:
                suite_module = AITestSuiteModuleModel(
                    suite_id=suite.id,
                    module_id=module_data.module_id,
                    module_name=module_data.module_name,
                    execution_order=module_data.execution_order,
                    created_by=user_id,
                    enabled_flag=1
                )
                db.add(suite_module)
            
            await db.commit()
            await db.refresh(suite)
            
            logger.info(f"创建测试套件成功: {suite.id} - {suite.name}")
            return suite
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建测试套件失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_suite_list(
        db: AsyncSession,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取测试套件列表"""
        try:
            # 构建查询条件
            conditions = [AITestSuiteModel.enabled_flag == 1]
            
            if project_id:
                conditions.append(AITestSuiteModel.project_id == project_id)
            
            if status:
                conditions.append(AITestSuiteModel.status == status)
            
            # 查询总数
            count_stmt = select(func.count(AITestSuiteModel.id)).where(and_(*conditions))
            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0
            
            # 查询数据
            offset = (page - 1) * page_size
            stmt = (
                select(AITestSuiteModel)
                .where(and_(*conditions))
                .order_by(AITestSuiteModel.creation_date.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await db.execute(stmt)
            suites = result.scalars().all()
            
            # 查询所有项目信息（用于显示项目名称）
            from ..projects.model import ProjectModel
            project_ids = list(set([suite.project_id for suite in suites if suite.project_id]))
            project_map = {}
            if project_ids:
                projects_stmt = select(ProjectModel).where(
                    and_(
                        ProjectModel.id.in_(project_ids),
                        ProjectModel.enabled_flag == 1
                    )
                )
                projects_result = await db.execute(projects_stmt)
                projects = projects_result.scalars().all()
                project_map = {p.id: p.name for p in projects}
            
            # 获取每个套件的模块数和用例数
            suite_list = []
            for suite in suites:
                # 查询模块数
                module_count_stmt = select(func.count(AITestSuiteModuleModel.id)).where(
                    and_(
                        AITestSuiteModuleModel.suite_id == suite.id,
                        AITestSuiteModuleModel.enabled_flag == 1
                    )
                )
                module_count_result = await db.execute(module_count_stmt)
                module_count = module_count_result.scalar() or 0
                
                # 查询用例数（所有关联模块下的用例总数）
                modules_stmt = select(AITestSuiteModuleModel.module_id).where(
                    and_(
                        AITestSuiteModuleModel.suite_id == suite.id,
                        AITestSuiteModuleModel.enabled_flag == 1
                    )
                )
                modules_result = await db.execute(modules_stmt)
                module_ids = [row[0] for row in modules_result.fetchall()]
                
                case_count = 0
                if module_ids:
                    case_count_stmt = select(func.count(AICaseModel.id)).where(
                        and_(
                            AICaseModel.source_module_id.in_(module_ids),
                            AICaseModel.enabled_flag == 1
                        )
                    )
                    case_count_result = await db.execute(case_count_stmt)
                    case_count = case_count_result.scalar() or 0
                
                suite_dict = {
                    'id': suite.id,
                    'name': suite.name,
                    'description': suite.description,
                    'project_id': suite.project_id,
                    'project_name': project_map.get(suite.project_id, f'项目{suite.project_id}'),
                    'status': suite.status,
                    'module_count': module_count,
                    'case_count': case_count,
                    'created_by': suite.created_by,
                    'creation_date': suite.creation_date.isoformat() if suite.creation_date else None,
                    'updated_by': suite.updated_by,
                    'updation_date': suite.updation_date.isoformat() if suite.updation_date else None
                }
                suite_list.append(suite_dict)
            
            return {
                'items': suite_list,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        except Exception as e:
            logger.error(f"获取测试套件列表失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_suite_detail(
        db: AsyncSession,
        suite_id: int
    ) -> Dict[str, Any]:
        """获取测试套件详情"""
        try:
            # 查询套件
            stmt = select(AITestSuiteModel).where(
                and_(
                    AITestSuiteModel.id == suite_id,
                    AITestSuiteModel.enabled_flag == 1
                )
            )
            result = await db.execute(stmt)
            suite = result.scalar_one_or_none()
            
            if not suite:
                raise ValueError(f"测试套件不存在: {suite_id}")
            
            # 查询关联的模块
            modules_stmt = (
                select(AITestSuiteModuleModel)
                .where(
                    and_(
                        AITestSuiteModuleModel.suite_id == suite_id,
                        AITestSuiteModuleModel.enabled_flag == 1
                    )
                )
                .order_by(AITestSuiteModuleModel.execution_order)
            )
            modules_result = await db.execute(modules_stmt)
            modules = modules_result.scalars().all()
            
            # 获取每个模块的用例数
            module_list = []
            total_cases = 0
            
            for module in modules:
                # 查询模块下的用例数
                case_count_stmt = select(func.count(AICaseModel.id)).where(
                    and_(
                        AICaseModel.source_module_id == module.module_id,
                        AICaseModel.enabled_flag == 1
                    )
                )
                case_count_result = await db.execute(case_count_stmt)
                case_count = case_count_result.scalar() or 0
                total_cases += case_count
                
                module_dict = {
                    'id': module.id,
                    'module_id': module.module_id,
                    'module_name': module.module_name,
                    'execution_order': module.execution_order,
                    'case_count': case_count
                }
                module_list.append(module_dict)
            
            suite_dict = {
                'id': suite.id,
                'name': suite.name,
                'description': suite.description,
                'project_id': suite.project_id,
                'status': suite.status,
                'module_count': len(module_list),
                'case_count': total_cases,
                'modules': module_list,
                'created_by': suite.created_by,
                'creation_date': suite.creation_date.isoformat() if suite.creation_date else None,
                'updated_by': suite.updated_by,
                'updation_date': suite.updation_date.isoformat() if suite.updation_date else None
            }
            
            return suite_dict
            
        except Exception as e:
            logger.error(f"获取测试套件详情失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def update_suite(
        db: AsyncSession,
        suite_id: int,
        suite_data: AITestSuiteUpdateSchema,
        user_id: int
    ) -> AITestSuiteModel:
        """更新测试套件"""
        try:
            # 查询套件
            stmt = select(AITestSuiteModel).where(
                and_(
                    AITestSuiteModel.id == suite_id,
                    AITestSuiteModel.enabled_flag == 1
                )
            )
            result = await db.execute(stmt)
            suite = result.scalar_one_or_none()
            
            if not suite:
                raise ValueError(f"测试套件不存在: {suite_id}")
            
            # 更新基本信息
            if suite_data.name is not None:
                suite.name = suite_data.name
            if suite_data.description is not None:
                suite.description = suite_data.description
            if suite_data.status is not None:
                suite.status = suite_data.status
            
            suite.updated_by = user_id
            
            # 更新模块关联
            if suite_data.modules is not None:
                # 删除旧的模块关联
                delete_stmt = delete(AITestSuiteModuleModel).where(
                    AITestSuiteModuleModel.suite_id == suite_id
                )
                await db.execute(delete_stmt)
                
                # 创建新的模块关联
                for module_data in suite_data.modules:
                    suite_module = AITestSuiteModuleModel(
                        suite_id=suite_id,
                        module_id=module_data.module_id,
                        module_name=module_data.module_name,
                        execution_order=module_data.execution_order,
                        created_by=user_id,
                        enabled_flag=1
                    )
                    db.add(suite_module)
            
            await db.commit()
            await db.refresh(suite)
            
            logger.info(f"更新测试套件成功: {suite_id}")
            return suite
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新测试套件失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def delete_suite(
        db: AsyncSession,
        suite_id: int
    ) -> None:
        """删除测试套件（软删除）"""
        try:
            # 软删除套件
            update_stmt = (
                update(AITestSuiteModel)
                .where(AITestSuiteModel.id == suite_id)
                .values(enabled_flag=0)
            )
            await db.execute(update_stmt)
            
            # 软删除模块关联
            update_modules_stmt = (
                update(AITestSuiteModuleModel)
                .where(AITestSuiteModuleModel.suite_id == suite_id)
                .values(enabled_flag=0)
            )
            await db.execute(update_modules_stmt)
            
            await db.commit()
            
            logger.info(f"删除测试套件成功: {suite_id}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"删除测试套件失败: {str(e)}", exc_info=True)
            raise



class AITestSuiteExecutionService:
    """AI测试套件执行服务"""
    
    @staticmethod
    async def execute_suite(
        db: AsyncSession,
        suite_id: int,
        execution_data: AITestSuiteExecutionCreateSchema,
        user_id: int
    ) -> AITestSuiteExecutionModel:
        """执行测试套件
        
        创建执行记录并返回，实际执行在后台进行
        """
        try:
            # 查询套件
            suite_stmt = select(AITestSuiteModel).where(
                and_(
                    AITestSuiteModel.id == suite_id,
                    AITestSuiteModel.enabled_flag == 1
                )
            )
            suite_result = await db.execute(suite_stmt)
            suite = suite_result.scalar_one_or_none()
            
            if not suite:
                raise ValueError(f"测试套件不存在: {suite_id}")
            
            # 查询套件关联的模块
            modules_stmt = (
                select(AITestSuiteModuleModel)
                .where(
                    and_(
                        AITestSuiteModuleModel.suite_id == suite_id,
                        AITestSuiteModuleModel.enabled_flag == 1
                    )
                )
                .order_by(AITestSuiteModuleModel.execution_order)
            )
            modules_result = await db.execute(modules_stmt)
            modules = modules_result.scalars().all()
            
            if not modules:
                raise ValueError(f"测试套件没有关联模块: {suite_id}")
            
            # 统计总用例数
            total_cases = 0
            for module in modules:
                case_count_stmt = select(func.count(AICaseModel.id)).where(
                    and_(
                        AICaseModel.source_module_id == module.module_id,
                        AICaseModel.enabled_flag == 1
                    )
                )
                case_count_result = await db.execute(case_count_stmt)
                case_count = case_count_result.scalar() or 0
                total_cases += case_count
            
            # 创建执行记录
            execution = AITestSuiteExecutionModel(
                suite_id=suite_id,
                suite_name=suite.name,
                execution_name=execution_data.execution_name or f"{suite.name}_执行_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                execution_mode=execution_data.execution_mode,
                status='running',
                start_time=datetime.now(),
                total_modules=len(modules),
                completed_modules=0,
                failed_modules=0,
                total_cases=total_cases,
                passed_cases=0,
                failed_cases=0,
                created_by=user_id,
                enabled_flag=1
            )
            
            db.add(execution)
            await db.flush()
            
            # 为每个模块创建执行记录
            for module in modules:
                # 查询模块下的用例数
                case_count_stmt = select(func.count(AICaseModel.id)).where(
                    and_(
                        AICaseModel.source_module_id == module.module_id,
                        AICaseModel.enabled_flag == 1
                    )
                )
                case_count_result = await db.execute(case_count_stmt)
                case_count = case_count_result.scalar() or 0
                
                module_execution = AITestSuiteModuleExecutionModel(
                    suite_execution_id=execution.id,
                    module_id=module.module_id,
                    module_name=module.module_name,
                    execution_order=module.execution_order,
                    status='pending',
                    total_cases=case_count,
                    passed_cases=0,
                    failed_cases=0,
                    created_by=user_id,
                    enabled_flag=1
                )
                db.add(module_execution)
            
            await db.commit()
            await db.refresh(execution)
            
            logger.info(f"创建测试套件执行记录成功: {execution.id}")
            return execution
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建测试套件执行记录失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def run_suite_execution(
        db: AsyncSession,
        execution_id: int
    ) -> None:
        """执行测试套件（后台任务）
        
        按模块顺序执行所有用例
        """
        try:
            # 查询执行记录
            execution_stmt = select(AITestSuiteExecutionModel).where(
                AITestSuiteExecutionModel.id == execution_id
            )
            execution_result = await db.execute(execution_stmt)
            execution = execution_result.scalar_one_or_none()
            
            if not execution:
                logger.error(f"执行记录不存在: {execution_id}")
                return
            
            logger.info(f"开始执行测试套件: {execution.suite_name} (ID: {execution_id})")
            
            # 查询模块执行记录（按顺序）
            module_executions_stmt = (
                select(AITestSuiteModuleExecutionModel)
                .where(
                    and_(
                        AITestSuiteModuleExecutionModel.suite_execution_id == execution_id,
                        AITestSuiteModuleExecutionModel.enabled_flag == 1
                    )
                )
                .order_by(AITestSuiteModuleExecutionModel.execution_order)
            )
            module_executions_result = await db.execute(module_executions_stmt)
            module_executions = module_executions_result.scalars().all()
            
            headless = execution.execution_mode == 'headless'
            completed_modules = 0
            failed_modules = 0
            total_passed = 0
            total_failed = 0
            
            # 按顺序执行每个模块
            for module_execution in module_executions:
                try:
                    logger.info(f"开始执行模块: {module_execution.module_name}")
                    
                    # 更新模块状态为执行中
                    module_execution.status = 'running'
                    module_execution.start_time = datetime.now()
                    await db.commit()
                    
                    # 查询模块下的所有用例
                    cases_stmt = select(AICaseModel).where(
                        and_(
                            AICaseModel.source_module_id == module_execution.module_id,
                            AICaseModel.enabled_flag == 1
                        )
                    )
                    cases_result = await db.execute(cases_stmt)
                    cases = cases_result.scalars().all()
                    
                    module_passed = 0
                    module_failed = 0
                    
                    # 执行模块下的每个用例
                    for case in cases:
                        try:
                            # 导入执行服务
                            from .service import AICaseService
                            
                            # 执行用例
                            await AICaseService.execute_ai_case(
                                db, case.id, execution.created_by, headless
                            )
                            
                            # 等待一小段时间，让执行记录创建
                            await asyncio.sleep(2)
                            
                            # 查询最新的执行记录
                            latest_record_stmt = (
                                select(AIExecutionRecordModel)
                                .where(
                                    and_(
                                        AIExecutionRecordModel.ai_case_id == case.id,
                                        AIExecutionRecordModel.enabled_flag == 1
                                    )
                                )
                                .order_by(AIExecutionRecordModel.start_time.desc())
                                .limit(1)
                            )
                            latest_record_result = await db.execute(latest_record_stmt)
                            latest_record = latest_record_result.scalar_one_or_none()
                            
                            # 等待执行完成（最多等待5分钟）
                            max_wait = 300  # 5分钟
                            waited = 0
                            while waited < max_wait:
                                if latest_record and latest_record.status in ['completed', 'failed', 'success']:
                                    break
                                await asyncio.sleep(5)
                                waited += 5
                                
                                # 刷新记录
                                await db.refresh(latest_record)
                            
                            # 统计结果
                            if latest_record and latest_record.status in ['completed', 'success']:
                                module_passed += 1
                            else:
                                module_failed += 1
                            
                            logger.info(f"用例执行完成: {case.name} - {latest_record.status if latest_record else 'unknown'}")
                            
                        except Exception as e:
                            logger.error(f"执行用例失败: {case.name}, 错误: {str(e)}")
                            module_failed += 1
                            continue
                    
                    # 更新模块执行记录
                    module_execution.status = 'completed' if module_failed == 0 else 'failed'
                    module_execution.end_time = datetime.now()
                    module_execution.duration = (module_execution.end_time - module_execution.start_time).total_seconds()
                    module_execution.passed_cases = module_passed
                    module_execution.failed_cases = module_failed
                    
                    if module_failed > 0:
                        failed_modules += 1
                    else:
                        completed_modules += 1
                    
                    total_passed += module_passed
                    total_failed += module_failed
                    
                    await db.commit()
                    
                    logger.info(f"模块执行完成: {module_execution.module_name}, 通过: {module_passed}, 失败: {module_failed}")
                    
                except Exception as e:
                    logger.error(f"执行模块失败: {module_execution.module_name}, 错误: {str(e)}")
                    
                    # 更新模块状态为失败
                    module_execution.status = 'failed'
                    module_execution.end_time = datetime.now()
                    if module_execution.start_time:
                        module_execution.duration = (module_execution.end_time - module_execution.start_time).total_seconds()
                    module_execution.error_message = str(e)
                    failed_modules += 1
                    
                    await db.commit()
                    continue
            
            # 更新套件执行记录
            execution.status = 'completed' if failed_modules == 0 else 'failed'
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.completed_modules = completed_modules
            execution.failed_modules = failed_modules
            execution.passed_cases = total_passed
            execution.failed_cases = total_failed
            
            await db.commit()
            
            logger.info(f"测试套件执行完成: {execution.suite_name}, 状态: {execution.status}")
            logger.info(f"模块统计 - 完成: {completed_modules}, 失败: {failed_modules}")
            logger.info(f"用例统计 - 通过: {total_passed}, 失败: {total_failed}")
            
        except Exception as e:
            logger.error(f"执行测试套件失败: {str(e)}", exc_info=True)
            
            # 更新执行记录为失败
            try:
                execution_stmt = select(AITestSuiteExecutionModel).where(
                    AITestSuiteExecutionModel.id == execution_id
                )
                execution_result = await db.execute(execution_stmt)
                execution = execution_result.scalar_one_or_none()
                
                if execution:
                    execution.status = 'failed'
                    execution.end_time = datetime.now()
                    if execution.start_time:
                        execution.duration = (execution.end_time - execution.start_time).total_seconds()
                    execution.error_message = str(e)
                    await db.commit()
            except Exception as update_error:
                logger.error(f"更新执行记录失败: {str(update_error)}")
    
    @staticmethod
    async def get_execution_list(
        db: AsyncSession,
        suite_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取执行记录列表"""
        try:
            # 构建查询条件
            conditions = [AITestSuiteExecutionModel.enabled_flag == 1]
            
            if suite_id:
                conditions.append(AITestSuiteExecutionModel.suite_id == suite_id)
            
            if status:
                conditions.append(AITestSuiteExecutionModel.status == status)
            
            # 查询总数
            count_stmt = select(func.count(AITestSuiteExecutionModel.id)).where(and_(*conditions))
            total_result = await db.execute(count_stmt)
            total = total_result.scalar() or 0
            
            # 查询数据
            offset = (page - 1) * page_size
            stmt = (
                select(AITestSuiteExecutionModel)
                .where(and_(*conditions))
                .order_by(AITestSuiteExecutionModel.start_time.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await db.execute(stmt)
            executions = result.scalars().all()
            
            execution_list = []
            for execution in executions:
                execution_dict = {
                    'id': execution.id,
                    'suite_id': execution.suite_id,
                    'suite_name': execution.suite_name,
                    'execution_name': execution.execution_name,
                    'execution_mode': execution.execution_mode,
                    'status': execution.status,
                    'start_time': execution.start_time.isoformat() if execution.start_time else None,
                    'end_time': execution.end_time.isoformat() if execution.end_time else None,
                    'duration': float(execution.duration) if execution.duration else None,
                    'total_modules': execution.total_modules,
                    'completed_modules': execution.completed_modules,
                    'failed_modules': execution.failed_modules,
                    'total_cases': execution.total_cases,
                    'passed_cases': execution.passed_cases,
                    'failed_cases': execution.failed_cases,
                    'error_message': execution.error_message,
                    'created_by': execution.created_by,
                    'creation_date': execution.creation_date.isoformat() if execution.creation_date else None
                }
                execution_list.append(execution_dict)
            
            return {
                'items': execution_list,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        except Exception as e:
            logger.error(f"获取执行记录列表失败: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_execution_detail(
        db: AsyncSession,
        execution_id: int
    ) -> Dict[str, Any]:
        """获取执行记录详情"""
        try:
            # 查询执行记录
            execution_stmt = select(AITestSuiteExecutionModel).where(
                and_(
                    AITestSuiteExecutionModel.id == execution_id,
                    AITestSuiteExecutionModel.enabled_flag == 1
                )
            )
            execution_result = await db.execute(execution_stmt)
            execution = execution_result.scalar_one_or_none()
            
            if not execution:
                raise ValueError(f"执行记录不存在: {execution_id}")
            
            # 查询模块执行记录
            module_executions_stmt = (
                select(AITestSuiteModuleExecutionModel)
                .where(
                    and_(
                        AITestSuiteModuleExecutionModel.suite_execution_id == execution_id,
                        AITestSuiteModuleExecutionModel.enabled_flag == 1
                    )
                )
                .order_by(AITestSuiteModuleExecutionModel.execution_order)
            )
            module_executions_result = await db.execute(module_executions_stmt)
            module_executions = module_executions_result.scalars().all()
            
            module_list = []
            for module_execution in module_executions:
                module_dict = {
                    'id': module_execution.id,
                    'module_id': module_execution.module_id,
                    'module_name': module_execution.module_name,
                    'execution_order': module_execution.execution_order,
                    'status': module_execution.status,
                    'start_time': module_execution.start_time.isoformat() if module_execution.start_time else None,
                    'end_time': module_execution.end_time.isoformat() if module_execution.end_time else None,
                    'duration': float(module_execution.duration) if module_execution.duration else None,
                    'total_cases': module_execution.total_cases,
                    'passed_cases': module_execution.passed_cases,
                    'failed_cases': module_execution.failed_cases,
                    'error_message': module_execution.error_message
                }
                module_list.append(module_dict)
            
            execution_dict = {
                'id': execution.id,
                'suite_id': execution.suite_id,
                'suite_name': execution.suite_name,
                'execution_name': execution.execution_name,
                'execution_mode': execution.execution_mode,
                'status': execution.status,
                'start_time': execution.start_time.isoformat() if execution.start_time else None,
                'end_time': execution.end_time.isoformat() if execution.end_time else None,
                'duration': float(execution.duration) if execution.duration else None,
                'total_modules': execution.total_modules,
                'completed_modules': execution.completed_modules,
                'failed_modules': execution.failed_modules,
                'total_cases': execution.total_cases,
                'passed_cases': execution.passed_cases,
                'failed_cases': execution.failed_cases,
                'error_message': execution.error_message,
                'modules': module_list,
                'created_by': execution.created_by,
                'creation_date': execution.creation_date.isoformat() if execution.creation_date else None
            }
            
            return execution_dict
            
        except Exception as e:
            logger.error(f"获取执行记录详情失败: {str(e)}", exc_info=True)
            raise
