# -*- coding: utf-8 -*-
"""
用例评审AI服务
"""
import json
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api.v1.ai_intelligence.model import AIModelConfigModel, PromptConfigModel
from app.api.v1.ai_intelligence.service import AIModelService

logger = logging.getLogger(__name__)


class ReviewAIService:
    """用例评审AI服务 - 复用现有AI评审角色和提示词"""
    
    @classmethod
    async def get_active_reviewer_config(cls, db: AsyncSession) -> Optional[AIModelConfigModel]:
        """获取激活的评审AI模型配置"""
        query = select(AIModelConfigModel).where(
            and_(
                AIModelConfigModel.role == 'reviewer',
                AIModelConfigModel.is_active == True,
                AIModelConfigModel.enabled_flag == 1
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_active_reviewer_prompt(cls, db: AsyncSession) -> Optional[PromptConfigModel]:
        """获取激活的评审提示词配置"""
        query = select(PromptConfigModel).where(
            and_(
                PromptConfigModel.prompt_type == 'reviewer',
                PromptConfigModel.is_active == True,
                PromptConfigModel.enabled_flag == 1
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def ai_review_test_case(
        cls,
        db: AsyncSession,
        test_case: Dict[str, Any],
        review_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """AI评审单个测试用例
        
        Args:
            db: 数据库会话
            test_case: 测试用例数据
            review_context: 评审上下文信息（可选）
            
        Returns:
            AI评审结果
        """
        try:
            # 获取AI配置
            reviewer_config = await cls.get_active_reviewer_config(db)
            if not reviewer_config:
                return {
                    "success": False,
                    "error": "未找到可用的AI评审模型配置",
                    "suggestions": []
                }
            
            reviewer_prompt_config = await cls.get_active_reviewer_prompt(db)
            if not reviewer_prompt_config:
                return {
                    "success": False,
                    "error": "未找到可用的AI评审提示词配置",
                    "suggestions": []
                }
            
            # 构建评审内容
            review_content = cls._build_review_content(test_case, review_context)
            
            # 构建消息
            messages = [
                {"role": "system", "content": reviewer_prompt_config.content},
                {"role": "user", "content": review_content}
            ]
            
            logger.info(f"开始AI评审测试用例: {test_case.get('title', 'Unknown')}")
            
            # 调用AI服务
            response = await AIModelService.call_openai_compatible_api(
                reviewer_config, messages
            )
            
            # 解析AI响应
            ai_content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 解析评审结果
            review_result = cls._parse_review_response(ai_content)
            review_result["success"] = True
            review_result["ai_model"] = reviewer_config.name
            review_result["raw_response"] = ai_content
            
            logger.info(f"AI评审完成: {test_case.get('title', 'Unknown')}")
            return review_result
            
        except Exception as e:
            logger.error(f"AI评审失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"AI评审失败: {str(e)}",
                "suggestions": []
            }
    
    @classmethod
    async def batch_ai_review(
        cls,
        db: AsyncSession,
        test_cases: List[Dict[str, Any]],
        review_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """批量AI评审测试用例
        
        Args:
            db: 数据库会话
            test_cases: 测试用例列表
            review_context: 评审上下文信息
            
        Returns:
            批量评审结果
        """
        results = []
        success_count = 0
        failed_count = 0
        
        for i, test_case in enumerate(test_cases):
            try:
                result = await cls.ai_review_test_case(db, test_case, review_context)
                results.append({
                    "test_case_id": test_case.get("id"),
                    "test_case_title": test_case.get("title"),
                    "result": result
                })
                
                if result.get("success"):
                    success_count += 1
                else:
                    failed_count += 1
                    
                logger.info(f"批量评审进度: {i+1}/{len(test_cases)}")
                
            except Exception as e:
                failed_count += 1
                results.append({
                    "test_case_id": test_case.get("id"),
                    "test_case_title": test_case.get("title"),
                    "result": {
                        "success": False,
                        "error": str(e),
                        "suggestions": []
                    }
                })
                logger.error(f"批量评审单个用例失败: {test_case.get('title')}, error: {str(e)}")
        
        return {
            "total_cases": len(test_cases),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results
        }
    
    @classmethod
    def _build_review_content(
        cls, 
        test_case: Dict[str, Any], 
        review_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建评审内容"""
        
        # 基本测试用例信息
        content_parts = []
        
        content_parts.append("请评审以下测试用例：\n")
        
        # 测试用例基本信息
        if test_case.get("title"):
            content_parts.append(f"**用例标题**: {test_case['title']}")
        
        if test_case.get("description"):
            content_parts.append(f"**用例描述**: {test_case['description']}")
        
        if test_case.get("preconditions"):
            content_parts.append(f"**前置条件**: {test_case['preconditions']}")
        
        # 测试步骤
        steps = test_case.get("steps", [])
        if steps:
            content_parts.append("**测试步骤**:")
            for i, step in enumerate(steps, 1):
                if isinstance(step, dict):
                    step_desc = step.get("description", "")
                    step_expected = step.get("expected_result", "")
                    content_parts.append(f"{i}. {step_desc}")
                    if step_expected:
                        content_parts.append(f"   预期: {step_expected}")
                else:
                    content_parts.append(f"{i}. {step}")
        
        if test_case.get("expected_result"):
            content_parts.append(f"**预期结果**: {test_case['expected_result']}")
        
        # 添加评审上下文
        if review_context:
            if review_context.get("project_name"):
                content_parts.append(f"**项目名称**: {review_context['project_name']}")
            
            if review_context.get("module_name"):
                content_parts.append(f"**所属模块**: {review_context['module_name']}")
            
            if review_context.get("review_focus"):
                content_parts.append(f"**评审重点**: {review_context['review_focus']}")
        
        # 评审要求
        content_parts.append("\n**评审要求**:")
        content_parts.append("请从以下维度进行评审并提供具体的改进建议：")
        content_parts.append("1. 完整性：是否包含所有必要信息")
        content_parts.append("2. 清晰性：描述是否清晰易懂")
        content_parts.append("3. 可执行性：步骤是否可以准确执行")
        content_parts.append("4. 覆盖性：是否覆盖了关键场景")
        content_parts.append("5. 边界条件：是否考虑了异常情况")
        
        return "\n".join(content_parts)
    
    @classmethod
    def _parse_review_response(cls, ai_response: str) -> Dict[str, Any]:
        """解析AI评审响应"""
        try:
            # 尝试解析JSON格式的响应
            if ai_response.strip().startswith('{') and ai_response.strip().endswith('}'):
                return json.loads(ai_response)
            
            # 如果不是JSON，则解析文本格式
            suggestions = []
            issues = []
            strengths = []
            
            lines = ai_response.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 识别不同的评审部分
                if any(keyword in line.lower() for keyword in ['建议', 'suggestion', '改进']):
                    current_section = 'suggestions'
                elif any(keyword in line.lower() for keyword in ['问题', 'issue', '缺陷']):
                    current_section = 'issues'
                elif any(keyword in line.lower() for keyword in ['优点', 'strength', '良好']):
                    current_section = 'strengths'
                elif line.startswith(('-', '•', '*', '1.', '2.', '3.', '4.', '5.')):
                    # 这是一个列表项
                    item_text = line.lstrip('-•*0123456789. ')
                    if current_section == 'suggestions':
                        suggestions.append({
                            "type": "improvement",
                            "description": item_text,
                            "priority": "medium"
                        })
                    elif current_section == 'issues':
                        issues.append({
                            "type": "issue",
                            "description": item_text,
                            "severity": "medium"
                        })
                    elif current_section == 'strengths':
                        strengths.append(item_text)
            
            # 如果没有找到结构化内容，将整个响应作为一般建议
            if not suggestions and not issues and not strengths:
                suggestions.append({
                    "type": "general",
                    "description": ai_response,
                    "priority": "medium"
                })
            
            return {
                "suggestions": suggestions,
                "issues": issues,
                "strengths": strengths,
                "summary": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
            }
            
        except Exception as e:
            logger.error(f"解析AI评审响应失败: {str(e)}")
            return {
                "suggestions": [{
                    "type": "general",
                    "description": ai_response,
                    "priority": "medium"
                }],
                "issues": [],
                "strengths": [],
                "summary": "AI评审完成，请查看详细建议",
                "parse_error": str(e)
            }
    
    @classmethod
    async def check_ai_review_availability(cls, db: AsyncSession) -> Dict[str, Any]:
        """检查AI评审功能可用性"""
        try:
            # 检查是否有可用的评审AI模型配置
            reviewer_config = await cls.get_active_reviewer_config(db)
            reviewer_prompt = await cls.get_active_reviewer_prompt(db)
            
            availability = {
                "available": bool(reviewer_config and reviewer_prompt),
                "model_config_available": bool(reviewer_config),
                "prompt_config_available": bool(reviewer_prompt),
                "model_name": reviewer_config.name if reviewer_config else None,
                "prompt_name": reviewer_prompt.name if reviewer_prompt else None
            }
            
            if not reviewer_config:
                availability["error"] = "未找到可用的AI评审模型配置，请在AI智能化模块中配置评审角色的AI模型"
            elif not reviewer_prompt:
                availability["error"] = "未找到可用的AI评审提示词配置，请在AI智能化模块中配置评审类型的提示词"
            
            return availability
            
        except Exception as e:
            logger.error(f"检查AI评审可用性失败: {str(e)}")
            return {
                "available": False,
                "model_config_available": False,
                "prompt_config_available": False,
                "error": f"检查AI评审可用性失败: {str(e)}"
            }

    @classmethod
    async def ai_pre_review_all_cases(
        cls,
        db: AsyncSession,
        review_id: int,
        reviewer_id: int
    ) -> Dict[str, Any]:
        """AI预评审所有测试用例
        
        Args:
            db: 数据库会话
            review_id: 评审ID
            reviewer_id: 评审人ID
            
        Returns:
            预评审结果
        """
        try:
            # 获取评审关联的所有测试用例
            from sqlalchemy import text
            query = text("""
                SELECT 
                    tc.id, 
                    tc.title, 
                    tc.description, 
                    tc.preconditions,
                    tc.expected_result,
                    tc.priority, 
                    tc.module_id,
                    p.name as project_name
                FROM test_cases tc
                INNER JOIN review_test_cases rtc ON tc.id = rtc.test_case_id
                INNER JOIN projects p ON tc.project_id = p.id
                WHERE rtc.review_id = :review_id
                AND tc.enabled_flag = 1
                ORDER BY tc.id
            """)
            
            result = await db.execute(query, {"review_id": review_id})
            test_cases = result.fetchall()
            
            if not test_cases:
                return {
                    "success": False,
                    "error": "未找到关联的测试用例",
                    "total_cases": 0,
                    "processed_cases": 0
                }
            
            # 转换为字典格式并获取测试步骤
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
                    "project_name": tc.project_name,
                    "steps": steps
                })
            
            # 构建评审上下文
            review_context = {
                "review_id": review_id,
                "reviewer_id": reviewer_id,
                "mode": "pre_review"
            }
            
            # 批量AI评审
            batch_result = await cls.batch_ai_review(db, test_case_list, review_context)
            
            # 如果AI评审成功，自动保存为初步评审结果
            if batch_result["success_count"] > 0:
                await cls._save_ai_pre_review_results(
                    db, review_id, reviewer_id, batch_result["results"]
                )
                
                # 更新评审任务状态为人工审核
                await cls._update_review_assignment_to_human_review(
                    db, review_id, reviewer_id
                )
            
            return {
                "success": True,
                "total_cases": len(test_case_list),
                "processed_cases": batch_result["success_count"],
                "failed_cases": batch_result["failed_count"],
                "ai_results": batch_result["results"]
            }
            
        except Exception as e:
            logger.error(f"AI预评审失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"AI预评审失败: {str(e)}",
                "total_cases": 0,
                "processed_cases": 0
            }
    
    @classmethod
    async def _save_ai_pre_review_results(
        cls,
        db: AsyncSession,
        review_id: int,
        reviewer_id: int,
        ai_results: List[Dict[str, Any]]
    ):
        """保存AI预评审结果到数据库"""
        from sqlalchemy import text, delete
        
        # 删除已存在的AI预评审结果
        delete_query = text("""
            DELETE FROM review_results 
            WHERE review_id = :review_id 
            AND reviewer_id = :reviewer_id 
            AND comment LIKE 'AI预评审:%'
        """)
        await db.execute(delete_query, {
            "review_id": review_id,
            "reviewer_id": reviewer_id
        })
        
        # 保存新的AI预评审结果
        for ai_result in ai_results:
            if not ai_result.get("result", {}).get("success"):
                continue
                
            test_case_id = ai_result.get("test_case_id")
            ai_data = ai_result.get("result", {})
            
            # 构建AI评审意见
            ai_comment_parts = ["AI预评审:"]
            
            # 添加建议
            suggestions = ai_data.get("suggestions", [])
            if suggestions:
                ai_comment_parts.append("\n【AI建议】:")
                for i, suggestion in enumerate(suggestions[:3], 1):  # 最多显示3条建议
                    ai_comment_parts.append(f"{i}. {suggestion.get('description', '')}")
            
            # 添加问题
            issues = ai_data.get("issues", [])
            if issues:
                ai_comment_parts.append("\n【发现问题】:")
                for i, issue in enumerate(issues[:2], 1):  # 最多显示2个问题
                    ai_comment_parts.append(f"{i}. {issue.get('description', '')}")
            
            # 添加优点
            strengths = ai_data.get("strengths", [])
            if strengths:
                ai_comment_parts.append("\n【用例优点】:")
                for i, strength in enumerate(strengths[:2], 1):  # 最多显示2个优点
                    ai_comment_parts.append(f"{i}. {strength}")
            
            ai_comment = "\n".join(ai_comment_parts)
            
            # 根据AI建议确定初步评审结果
            ai_result_status = "pass"  # 默认通过
            if issues:
                ai_result_status = "fail"  # 有问题则不通过
            elif suggestions:
                ai_result_status = "modify"  # 有建议则需修改
            
            # 插入评审结果
            insert_query = text("""
                INSERT INTO review_results 
                (review_id, test_case_id, reviewer_id, result, comment, created_by, updated_by)
                VALUES (:review_id, :test_case_id, :reviewer_id, :result, :comment, :created_by, :updated_by)
            """)
            
            await db.execute(insert_query, {
                "review_id": review_id,
                "test_case_id": test_case_id,
                "reviewer_id": reviewer_id,
                "result": ai_result_status,
                "comment": ai_comment,
                "created_by": reviewer_id,
                "updated_by": reviewer_id
            })
        
        await db.commit()
    
    @classmethod
    async def _update_review_assignment_to_human_review(
        cls,
        db: AsyncSession,
        review_id: int,
        reviewer_id: int
    ):
        """更新评审任务状态为人工审核"""
        from sqlalchemy import text
        
        # 更新评审分配状态为人工审核
        update_query = text("""
            UPDATE review_assignments 
            SET status = 'human_review',
                ai_pre_reviewed = 1,
                ai_pre_review_at = NOW(),
                updated_by = :reviewer_id,
                updation_date = NOW()
            WHERE review_id = :review_id 
            AND reviewer_id = :reviewer_id
        """)
        
        await db.execute(update_query, {
            "review_id": review_id,
            "reviewer_id": reviewer_id
        })
        
        await db.commit()
    
    @classmethod
    async def get_ai_pre_review_summary(
        cls,
        db: AsyncSession,
        review_id: int,
        reviewer_id: int
    ) -> Dict[str, Any]:
        """获取AI预评审摘要"""
        try:
            from sqlalchemy import text
            
            # 统计AI预评审结果
            summary_query = text("""
                SELECT 
                    result,
                    COUNT(*) as count
                FROM review_results 
                WHERE review_id = :review_id 
                AND reviewer_id = :reviewer_id 
                AND comment LIKE 'AI预评审:%'
                GROUP BY result
            """)
            
            result = await db.execute(summary_query, {
                "review_id": review_id,
                "reviewer_id": reviewer_id
            })
            
            summary_data = result.fetchall()
            
            # 构建摘要
            summary = {
                "total_cases": 0,
                "pass_count": 0,
                "modify_count": 0,
                "fail_count": 0,
                "distribution": {}
            }
            
            for row in summary_data:
                count = row.count
                summary["total_cases"] += count
                summary["distribution"][row.result] = count
                
                if row.result == "pass":
                    summary["pass_count"] = count
                elif row.result == "modify":
                    summary["modify_count"] = count
                elif row.result == "fail":
                    summary["fail_count"] = count
            
            return summary
            
        except Exception as e:
            logger.error(f"获取AI预评审摘要失败: {str(e)}")
            return {
                "total_cases": 0,
                "pass_count": 0,
                "modify_count": 0,
                "fail_count": 0,
                "distribution": {}
            }