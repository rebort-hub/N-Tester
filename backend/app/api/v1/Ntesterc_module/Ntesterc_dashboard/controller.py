#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from app.core.database import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.core.logger import logger

router = APIRouter(tags=["首页看板"])


@router.get("/overview", summary="获取首页统计总览")
async def get_dashboard_overview(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取首页核心统计数据
    """
    try:
        # 项目统计
        project_total_query = text("SELECT COUNT(*) FROM projects WHERE enabled_flag = 1")
        project_total_result = await db.execute(project_total_query)
        project_total = project_total_result.scalar() or 0
        
        project_active_query = text("SELECT COUNT(*) FROM projects WHERE enabled_flag = 1 AND status = 'active'")
        project_active_result = await db.execute(project_active_query)
        project_active = project_active_result.scalar() or 0
        
        # 本月新增项目
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        project_monthly_query = text("SELECT COUNT(*) FROM projects WHERE enabled_flag = 1 AND creation_date >= :month_start")
        project_monthly_result = await db.execute(project_monthly_query, {"month_start": month_start})
        project_monthly = project_monthly_result.scalar() or 0
        
        # 测试用例统计
        testcase_total_query = text("SELECT COUNT(*) FROM test_cases WHERE enabled_flag = 1")
        testcase_total_result = await db.execute(testcase_total_query)
        testcase_total = testcase_total_result.scalar() or 0
        
        # 本周新增用例
        week_start = datetime.now() - timedelta(days=7)
        testcase_weekly_query = text("SELECT COUNT(*) FROM test_cases WHERE enabled_flag = 1 AND creation_date >= :week_start")
        testcase_weekly_result = await db.execute(testcase_weekly_query, {"week_start": week_start})
        testcase_weekly = testcase_weekly_result.scalar() or 0
        
        # 用例通过率
        api_pass = api_total = 0
        web_pass = web_total = 0
        try:
            api_rate_query = text("""
                SELECT
                    COALESCE(SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(result, '$.pass')) AS SIGNED)), 0) AS pass_count,
                    COALESCE(SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(result, '$.total')) AS SIGNED)), 0) AS total_count
                FROM api_automation_script_result_lists
                WHERE enabled_flag = 1
                  AND end_time IS NOT NULL
                  AND result IS NOT NULL
            """)
            api_rate_result = await db.execute(api_rate_query)
            api_rate_row = api_rate_result.fetchone()
            if api_rate_row:
                api_pass = int(api_rate_row.pass_count or 0)
                api_total = int(api_rate_row.total_count or 0)
        except Exception as api_rate_err:
            logger.warning(f"[首页看板] 汇总 API 通过率失败: {api_rate_err}")

        try:
            import json as _json
            web_rate_query = text("""
                SELECT result
                FROM web_management_result_lists
                WHERE enabled_flag = 1
                  AND end_time IS NOT NULL
                  AND result IS NOT NULL
            """)
            web_rate_result = await db.execute(web_rate_query)
            for row in web_rate_result.fetchall():
                items = row.result
                if isinstance(items, str):
                    try:
                        items = _json.loads(items)
                    except Exception:
                        continue
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    total_num = int(item.get("total") or 0)
                    fail_num = int(item.get("run_false") or 0)
                    if total_num <= 0:
                        continue
                    web_total += total_num
                    web_pass += max(total_num - fail_num, 0)
        except Exception as web_rate_err:
            logger.warning(f"[首页看板] 汇总 Web 通过率失败: {web_rate_err}")

        exec_pass = api_pass + web_pass
        exec_total = api_total + web_total
        testcase_pass_rate = round(exec_pass / exec_total * 100, 1) if exec_total > 0 else 0
        
        # AI执行统计
        ai_total_query = text("""
            SELECT COUNT(*) FROM (
                SELECT id FROM testcase_generation_tasks WHERE enabled_flag = 1
                UNION ALL
                SELECT id FROM ai_execution_records WHERE enabled_flag = 1
            ) as ai_executions
        """)
        ai_total_result = await db.execute(ai_total_query)
        ai_total = ai_total_result.scalar() or 0
        
        # 本月AI生成用例数
        ai_monthly_query = text("SELECT COUNT(*) FROM testcase_generation_tasks WHERE enabled_flag = 1 AND creation_date >= :month_start")
        ai_monthly_result = await db.execute(ai_monthly_query, {"month_start": month_start})
        ai_monthly = ai_monthly_result.scalar() or 0
        
        # AI 执行成功率（与 browser-use 统计页一致：completed/success）
        ai_rate_query = text("""
            SELECT
                COUNT(*) AS total_count,
                SUM(CASE WHEN status IN ('completed', 'success') THEN 1 ELSE 0 END) AS success_count
            FROM ai_execution_records
            WHERE enabled_flag = 1
        """)
        ai_rate_result = await db.execute(ai_rate_query)
        ai_rate_row = ai_rate_result.fetchone()
        ai_exec_total = int(ai_rate_row.total_count or 0) if ai_rate_row else 0
        ai_exec_success = int(ai_rate_row.success_count or 0) if ai_rate_row else 0
        ai_success_rate = round(ai_exec_success / ai_exec_total * 100, 1) if ai_exec_total > 0 else 0
        
        # 用户统计
        user_total_query = text("SELECT COUNT(*) FROM sys_user WHERE enabled_flag = 1")
        user_total_result = await db.execute(user_total_query)
        user_total = user_total_result.scalar() or 0
        
        # 在线用户：
        try:
            from app.api.v1.monitor.online.service import OnlineUserService
            online_stats = await OnlineUserService.get_online_stats()
            user_online = int(getattr(online_stats, "total_online", 0) or 0)
        except Exception as online_err:
            logger.warning(f"[首页看板] 获取在线用户失败: {online_err}")
            user_online = 0
        
        # 本月活跃用户
        user_monthly_query = text("""
            SELECT COUNT(*) FROM sys_user
            WHERE enabled_flag = 1 AND updation_date >= :month_start
        """)
        user_monthly_result = await db.execute(user_monthly_query, {"month_start": month_start})
        user_monthly_active = user_monthly_result.scalar() or 0
        
        overview_data = {
            "projects": {
                "total": project_total,
                "active": project_active,
                "monthly_new": project_monthly
            },
            "test_cases": {
                "total": testcase_total,
                "weekly_new": testcase_weekly,
                "pass_rate": testcase_pass_rate
            },
            "ai_executions": {
                "total": ai_total,
                "monthly_generated": ai_monthly,
                "success_rate": ai_success_rate
            },
            "users": {
                "total": user_total,
                "online": user_online,
                "monthly_active": user_monthly_active
            }
        }
        
        return success_response(data=overview_data, message="获取统计总览成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取统计总览失败: {str(e)}")
        return error_response(message=f"获取统计总览失败: {str(e)}")


@router.get("/execution-trends", summary="获取测试执行趋势")
async def get_execution_trends(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取API和UI测试执行趋势
    """
    try:
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # API测试执行趋势
        api_trends = []
        ui_trends = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            
            # 接口自动化调试统计
            api_query = text("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status_code >= 200 AND status_code < 400
                              AND (error_message IS NULL OR error_message = '')
                         THEN 1 ELSE 0 END) as success_count
                FROM api_automation_results 
                WHERE enabled_flag = 1
                  AND DATE(creation_date) = :current_date
            """)
            try:
                api_result = await db.execute(api_query, {"current_date": current_date})
                api_data = api_result.fetchone()
            except Exception:
                api_data = None
            
            api_count = api_data.total_count if api_data else 0
            api_success = api_data.success_count if api_data else 0
            api_success_rate = round((api_success / api_count * 100), 1) if api_count > 0 else 0
            
            api_trends.append({
                "date": current_date.strftime("%m-%d"),
                "count": api_count,
                "success_rate": api_success_rate
            })
            
            # UI测试统计
            ui_query = text("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count
                FROM ui_executions 
                WHERE DATE(creation_date) = :current_date
            """)
            ui_result = await db.execute(ui_query, {"current_date": current_date})
            ui_data = ui_result.fetchone()
            
            ui_count = ui_data.total_count if ui_data else 0
            ui_success = ui_data.success_count if ui_data else 0
            ui_success_rate = round((ui_success / ui_count * 100), 1) if ui_count > 0 else 0
            
            ui_trends.append({
                "date": current_date.strftime("%m-%d"),
                "count": ui_count,
                "success_rate": ui_success_rate
            })
        
        trends_data = {
            "api_tests": api_trends,
            "ui_tests": ui_trends
        }
        
        return success_response(data=trends_data, message="获取执行趋势成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取执行趋势失败: {str(e)}")
        return error_response(message=f"获取执行趋势失败: {str(e)}")


@router.get("/data-factory-stats", summary="获取数据工厂统计")
async def get_data_factory_stats(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取数据工厂使用统计
    """
    try:
        # 工具名称中文映射
        tool_name_mapping = {
            # 测试数据类
            'random_name': '随机姓名',
            'random_phone': '随机手机号',
            'random_email': '随机邮箱',
            'random_address': '随机地址',
            'random_id_card': '随机身份证',
            'random_company': '随机公司名',
            'random_date': '随机日期',
            'random_number': '随机数字',
            'random_text': '随机文本',
            'random_password': '随机密码',
            'generate_company_name': '生成公司名称',
            'generate_bank_card': '生成银行卡号',
            'generate_barcode': '生成条形码',
            'generate_chinese_address': '生成中文地址',
            'generate_chinese_phone': '生成中文手机号',
            'generate_expression': '生成表达式',
            'generate_qrcode': '生成二维码',
            'generate_chinese_name': '生成中文姓名',
            'generate_id_card': '生成身份证号',
            'generate_email': '生成邮箱地址',
            
            # JSON工具类
            'json_format': 'JSON格式化',
            'json_compress': 'JSON压缩',
            'json_validate': 'JSON验证',
            'validate_json': 'JSON验证',
            'json_to_xml': 'JSON转XML',
            'xml_to_json': 'XML转JSON',
            'json_to_yaml': 'JSON转YAML',
            'yaml_to_json': 'YAML转JSON',
            'format_json': 'JSON格式化',
            'minify_json': 'JSON压缩',
            
            # 字符串工具类
            'string_encode': '字符串编码',
            'string_decode': '字符串解码',
            'string_hash': '字符串哈希',
            'string_encrypt': '字符串加密',
            'string_decrypt': '字符串解密',
            'string_format': '字符串格式化',
            'string_replace': '字符串替换',
            'string_split': '字符串分割',
            'escape_string': '字符串转义',
            'unescape_string': '字符串反转义',
            'trim_string': '字符串去空格',
            'reverse_string': '字符串反转',
            'uppercase_string': '字符串大写',
            'lowercase_string': '字符串小写',
            
            # 编码工具类
            'base64_encode': 'Base64编码',
            'base64_decode': 'Base64解码',
            'url_encode': 'URL编码',
            'url_decode': 'URL解码',
            'html_encode': 'HTML编码',
            'html_decode': 'HTML解码',
            'unicode_encode': 'Unicode编码',
            'unicode_decode': 'Unicode解码',
            'hex_encode': '十六进制编码',
            'hex_decode': '十六进制解码',
            
            # 加密工具类
            'md5_hash': 'MD5哈希',
            'sha1_hash': 'SHA1哈希',
            'sha256_hash': 'SHA256哈希',
            'aes_encrypt': 'AES加密',
            'aes_decrypt': 'AES解密',
            'rsa_encrypt': 'RSA加密',
            'rsa_decrypt': 'RSA解密',
            'des_encrypt': 'DES加密',
            'des_decrypt': 'DES解密',
            
            # 时间工具类
            'timestamp_convert': '时间戳转换',
            'date_format': '日期格式化',
            'date_calculate': '日期计算',
            'cron_parse': 'Cron表达式解析',
            'cron_generate': 'Cron表达式生成',
            'format_timestamp': '格式化时间戳',
            'parse_date': '解析日期',
            
            # 其他工具
            'generate_uuid': '生成UUID',
            'color_convert': '颜色转换',
            'qr_code_generate': '生成二维码',
            'barcode_generate': '生成条形码',
            'password_generate': '生成密码',
            'regex_test': '正则表达式测试',
            'sql_format': 'SQL格式化',
            'xml_format': 'XML格式化',
            'css_format': 'CSS格式化',
            'html_format': 'HTML格式化'
        }
        
        # 分类中文映射
        category_mapping = {
            'test_data': '测试数据',
            'json': 'JSON工具',
            'string': '字符串工具',
            'encoding': '编码工具',
            'random': '随机生成',
            'encryption': '加密工具',
            'crontab': '定时任务',
            'time': '时间工具',
            'format': '格式化工具',
            'convert': '转换工具'
        }
        
        # 工具使用排行（TOP 10）
        top_tools_query = text("""
            SELECT 
                tool_name,
                COUNT(*) as usage_count
            FROM data_factory_records 
            WHERE enabled_flag = 1
            GROUP BY tool_name
            ORDER BY usage_count DESC
            LIMIT 10
        """)
        top_tools_result = await db.execute(top_tools_query)
        top_tools = [
            {
                "name": tool_name_mapping.get(row.tool_name, row.tool_name),
                "count": row.usage_count
            }
            for row in top_tools_result.fetchall()
        ]
        
        # 分类使用分布
        category_query = text("""
            SELECT 
                tool_category,
                COUNT(*) as usage_count
            FROM data_factory_records 
            WHERE enabled_flag = 1
            GROUP BY tool_category
            ORDER BY usage_count DESC
        """)
        category_result = await db.execute(category_query)
        category_data = category_result.fetchall()
        
        total_usage = sum(row.usage_count for row in category_data)
        category_distribution = [
            {
                "category": category_mapping.get(row.tool_category, row.tool_category),
                "count": row.usage_count,
                "percentage": round((row.usage_count / total_usage * 100), 1) if total_usage > 0 else 0
            }
            for row in category_data
        ]
        
        stats_data = {
            "top_tools": top_tools,
            "category_distribution": category_distribution
        }
        
        return success_response(data=stats_data, message="获取数据工厂统计成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取数据工厂统计失败: {str(e)}")
        return error_response(message=f"获取数据工厂统计失败: {str(e)}")


@router.get("/review-stats", summary="获取评审统计")
async def get_review_stats(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取用例评审统计
    """
    try:
        # 评审状态分布
        status_query = text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM test_case_reviews 
            WHERE enabled_flag = 1
            GROUP BY status
        """)
        status_result = await db.execute(status_query)
        status_data = {row.status: row.count for row in status_result.fetchall()}
        
        status_distribution = {
            "pending": status_data.get("pending", 0),
            "in_progress": status_data.get("in_progress", 0),
            "completed": status_data.get("completed", 0),
            "cancelled": status_data.get("cancelled", 0)
        }
        
        # 最近30天完成率趋势
        completion_trends = []
        for i in range(30):
            current_date = datetime.now().date() - timedelta(days=29-i)
            
            # 当天完成的评审数
            completed_query = text("""
                SELECT COUNT(*) 
                FROM test_case_reviews 
                WHERE DATE(completed_at) = :current_date
                AND status = 'completed'
                AND enabled_flag = 1
            """)
            completed_result = await db.execute(completed_query, {"current_date": current_date})
            completed_count = completed_result.scalar() or 0
            
            # 当天总评审数（包括之前创建的）
            total_query = text("""
                SELECT COUNT(*) 
                FROM test_case_reviews 
                WHERE DATE(creation_date) <= :current_date
                AND enabled_flag = 1
            """)
            total_result = await db.execute(total_query, {"current_date": current_date})
            total_count = total_result.scalar() or 0
            
            completion_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0
            
            completion_trends.append({
                "date": current_date.strftime("%m-%d"),
                "completion_rate": completion_rate
            })
        
        stats_data = {
            "status_distribution": status_distribution,
            "completion_trend": completion_trends
        }
        
        return success_response(data=stats_data, message="获取评审统计成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取评审统计失败: {str(e)}")
        return error_response(message=f"获取评审统计失败: {str(e)}")


@router.get("/project-activity", summary="获取项目活跃度")
async def get_project_activity(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取项目活跃度统计
    """
    try:
        # 活跃项目排行（按最近活动时间，不计算虚构活跃度百分比）
        active_projects_query = text("""
            SELECT 
                p.id,
                p.name,
                p.updation_date as last_activity
            FROM projects p
            WHERE p.enabled_flag = 1
            AND p.status = 'active'
            ORDER BY p.updation_date DESC
            LIMIT 10
        """)
        active_projects_result = await db.execute(active_projects_query)
        active_projects = [
            {
                "id": row.id,
                "name": row.name,
                "last_activity": row.last_activity.isoformat() if row.last_activity else None,
            }
            for row in active_projects_result.fetchall()
        ]
        
        # 模块使用热力图统计
        module_usage = {
            "test_cases": 0,
            "api_testing": 0,
            "automation_ui": 0,
            "ai_intelligence": 0,
            "data_factory": 0,
            "reviews": 0
        }
        
        # 测试用例模块
        testcase_query = text("SELECT COUNT(*) FROM test_cases WHERE enabled_flag = 1")
        testcase_result = await db.execute(testcase_query)
        module_usage["test_cases"] = testcase_result.scalar() or 0
        
        # API / 接口自动化模块（统计调试与脚本执行结果）
        api_query = text(
            "SELECT COUNT(*) FROM api_automation_results WHERE enabled_flag = 1"
        )
        try:
            api_result = await db.execute(api_query)
            module_usage["api_testing"] = api_result.scalar() or 0
        except Exception:
            # 兼容：若表结构差异则回退脚本执行汇总
            try:
                api_query2 = text(
                    "SELECT COUNT(*) FROM api_automation_script_result_lists"
                )
                api_result2 = await db.execute(api_query2)
                module_usage["api_testing"] = api_result2.scalar() or 0
            except Exception:
                module_usage["api_testing"] = 0
        
        # UI自动化模块 
        ui_query = text("SELECT COUNT(*) FROM ui_executions")
        ui_result = await db.execute(ui_query)
        module_usage["automation_ui"] = ui_result.scalar() or 0
        
        # AI智能化模块
        ai_query = text("SELECT COUNT(*) FROM testcase_generation_tasks WHERE enabled_flag = 1")
        ai_result = await db.execute(ai_query)
        module_usage["ai_intelligence"] = ai_result.scalar() or 0
        
        # 数据工厂模块
        df_query = text("SELECT COUNT(*) FROM data_factory_records WHERE enabled_flag = 1")
        df_result = await db.execute(df_query)
        module_usage["data_factory"] = df_result.scalar() or 0
        
        # 评审模块
        review_query = text("SELECT COUNT(*) FROM test_case_reviews WHERE enabled_flag = 1")
        review_result = await db.execute(review_query)
        module_usage["reviews"] = review_result.scalar() or 0
        
        activity_data = {
            "active_projects": active_projects,
            "module_usage": module_usage
        }
        
        return success_response(data=activity_data, message="获取项目活跃度成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取项目活跃度失败: {str(e)}")
        return error_response(message=f"获取项目活跃度失败: {str(e)}")


@router.get("/recent-notifications", summary="获取最近通知")
async def get_recent_notifications(
    limit: int = Query(5, ge=1, le=20, description="获取数量"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    获取最近的通知消息
    """
    try:
        notifications_query = text("""
            SELECT 
                title,
                status,
                creation_date
            FROM notification_histories 
            WHERE enabled_flag = 1
            ORDER BY creation_date DESC
            LIMIT :limit
        """)
        notifications_result = await db.execute(notifications_query, {"limit": limit})
        
        notifications = [
            {
                "title": row.title,
                "status": row.status,
                "created_at": row.creation_date.isoformat() if row.creation_date else None
            }
            for row in notifications_result.fetchall()
        ]
        
        # 未读通知数量
        unread_query = text("""
            SELECT COUNT(*) 
            FROM notification_histories 
            WHERE enabled_flag = 1
            AND status = 'pending'
        """)
        unread_result = await db.execute(unread_query)
        unread_count = unread_result.scalar() or 0
        
        notification_data = {
            "notifications": notifications,
            "unread_count": unread_count
        }
        
        return success_response(data=notification_data, message="获取最近通知成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取最近通知失败: {str(e)}")
        return error_response(message=f"获取最近通知失败: {str(e)}")


@router.get("/api-interface-stats", summary="获取API接口统计")
async def get_api_interface_stats(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    按 HTTP 请求方法统计接口数量
    """
    try:
        METHOD_MAP = {1: "GET", 2: "POST", 3: "PUT", 4: "DELETE", 5: "PATCH", 6: "OPTIONS"}

        query = text("""
            SELECT
                JSON_UNQUOTE(JSON_EXTRACT(req, '$.method')) AS method_int,
                COUNT(*) AS cnt
            FROM api_automation_apis
            WHERE enabled_flag = 1
            GROUP BY method_int
        """)
        result = await db.execute(query)
        rows = result.fetchall()

        method_counts: dict = {name: 0 for name in METHOD_MAP.values()}
        total = 0
        for row in rows:
            try:
                m = int(row.method_int) if row.method_int is not None else 2
            except (ValueError, TypeError):
                m = 2
            name = METHOD_MAP.get(m, "OTHER")
            method_counts[name] = method_counts.get(name, 0) + int(row.cnt)
            total += int(row.cnt)

        stats = [
            {"method": k, "count": v}
            for k, v in method_counts.items()
            if v > 0
        ]
        # 按数量降序
        stats.sort(key=lambda x: x["count"], reverse=True)

        return success_response(
            data={"method_stats": stats, "total": total},
            message="获取API接口统计成功"
        )

    except Exception as e:
        logger.error(f"[首页看板] 获取API接口统计失败: {str(e)}")
        return error_response(message=f"获取API接口统计失败: {str(e)}")

@router.get("/llm-usage", summary="获取 LLM 用量统计")
async def get_llm_usage_stats(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    tab: str = Query("overview", description="overview|daily|category|model"),
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """LLM token / 缓存命中 / 请求统计（数据来自 llm_usage_logs，改造上线后开始累积）"""
    try:
        from app.api.v1.Ntesterc_module.Ntesterc_ai.usage.service import UsageLogService
        await UsageLogService.ensure_table()

        start_date = datetime.now() - timedelta(days=days - 1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        overview_q = text("""
            SELECT
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(cached_tokens), 0) AS cached_tokens,
                COALESCE(SUM(prompt_tokens), 0) AS prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) AS completion_tokens,
                COUNT(*) AS request_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count
            FROM llm_usage_logs
            WHERE enabled_flag = 1
              AND creation_date >= :start_date
        """)
        overview_row = (await db.execute(overview_q, {"start_date": start_date})).fetchone()
        total_tokens = int(overview_row.total_tokens or 0) if overview_row else 0
        cached_tokens = int(overview_row.cached_tokens or 0) if overview_row else 0
        prompt_tokens = int(overview_row.prompt_tokens or 0) if overview_row else 0
        completion_tokens = int(overview_row.completion_tokens or 0) if overview_row else 0
        request_count = int(overview_row.request_count or 0) if overview_row else 0
        error_count = int(overview_row.error_count or 0) if overview_row else 0

        base_for_hit = prompt_tokens if prompt_tokens > 0 else total_tokens
        uncached_tokens = max(base_for_hit - cached_tokens, 0)
        cache_hit_rate = round(cached_tokens / base_for_hit * 100, 1) if base_for_hit > 0 else 0.0

        by_model_q = text("""
            SELECT
                COALESCE(NULLIF(model_name, ''), 'unknown') AS model_name,
                COALESCE(provider, '') AS provider,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(cached_tokens), 0) AS cached_tokens,
                COUNT(*) AS request_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count
            FROM llm_usage_logs
            WHERE enabled_flag = 1
              AND creation_date >= :start_date
            GROUP BY COALESCE(NULLIF(model_name, ''), 'unknown'), COALESCE(provider, '')
            ORDER BY total_tokens DESC
            LIMIT 20
        """)
        by_model = [
            {
                "model_name": row.model_name,
                "provider": row.provider,
                "total_tokens": int(row.total_tokens or 0),
                "cached_tokens": int(row.cached_tokens or 0),
                "request_count": int(row.request_count or 0),
                "error_count": int(row.error_count or 0),
            }
            for row in (await db.execute(by_model_q, {"start_date": start_date})).fetchall()
        ]

        by_date_q = text("""
            SELECT
                DATE(creation_date) AS day,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COALESCE(SUM(cached_tokens), 0) AS cached_tokens,
                COUNT(*) AS request_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count
            FROM llm_usage_logs
            WHERE enabled_flag = 1
              AND creation_date >= :start_date
            GROUP BY DATE(creation_date)
            ORDER BY day ASC
        """)
        by_date = [
            {
                "date": row.day.strftime("%m-%d") if hasattr(row.day, "strftime") else str(row.day)[5:10],
                "total_tokens": int(row.total_tokens or 0),
                "cached_tokens": int(row.cached_tokens or 0),
                "request_count": int(row.request_count or 0),
                "error_count": int(row.error_count or 0),
            }
            for row in (await db.execute(by_date_q, {"start_date": start_date})).fetchall()
        ]

        by_category_q = text("""
            SELECT
                COALESCE(NULLIF(source, ''), 'unknown') AS category,
                COALESCE(SUM(total_tokens), 0) AS total_tokens,
                COUNT(*) AS request_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count
            FROM llm_usage_logs
            WHERE enabled_flag = 1
              AND creation_date >= :start_date
            GROUP BY COALESCE(NULLIF(source, ''), 'unknown')
            ORDER BY total_tokens DESC
        """)
        category_label = {
            "chat": "AI 聊天",
            "browser_use": "Browser-Use",
            "unknown": "其他",
        }
        by_category = [
            {
                "category": category_label.get(row.category, row.category),
                "source": row.category,
                "total_tokens": int(row.total_tokens or 0),
                "request_count": int(row.request_count or 0),
                "error_count": int(row.error_count or 0),
            }
            for row in (await db.execute(by_category_q, {"start_date": start_date})).fetchall()
        ]

        recent_q = text("""
            SELECT
                id,
                creation_date,
                model_name,
                provider,
                source,
                total_tokens,
                cached_tokens,
                status,
                error_message,
                latency_ms
            FROM llm_usage_logs
            WHERE enabled_flag = 1
              AND creation_date >= :start_date
            ORDER BY creation_date DESC
            LIMIT 30
        """)
        recent_requests = [
            {
                "id": row.id,
                "created_at": row.creation_date.isoformat() if row.creation_date else None,
                "model_name": row.model_name or "unknown",
                "provider": row.provider or "",
                "source": row.source or "chat",
                "source_label": category_label.get(row.source or "chat", row.source or "chat"),
                "total_tokens": int(row.total_tokens or 0),
                "cached_tokens": int(row.cached_tokens or 0),
                "status": row.status or "success",
                "error_message": row.error_message,
                "latency_ms": row.latency_ms,
            }
            for row in (await db.execute(recent_q, {"start_date": start_date})).fetchall()
        ]

        data = {
            "tab": tab,
            "days": days,
            "overview": {
                "total_tokens": total_tokens,
                "cached_tokens": cached_tokens,
                "uncached_tokens": uncached_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "cache_hit_rate": cache_hit_rate,
                "request_count": request_count,
                "error_count": error_count,
            },
            "by_model": by_model,
            "by_date": by_date,
            "by_category": by_category,
            "recent_requests": recent_requests,
        }
        return success_response(data=data, message="获取 LLM 用量统计成功")

    except Exception as e:
        logger.error(f"[首页看板] 获取 LLM 用量统计失败: {str(e)}")
        return error_response(message=f"获取 LLM 用量统计失败: {str(e)}")

