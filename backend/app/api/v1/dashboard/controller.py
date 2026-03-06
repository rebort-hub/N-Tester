"""
首页看板控制器
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text

from app.db.sqlalchemy import get_db
from app.core.dependencies import get_current_user_id
from app.common.response import success_response, error_response
from app.corelibs.logger import logger

router = APIRouter(prefix="/dashboard", tags=["首页看板"])


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
        
        # 用例通过率（模拟计算）
        testcase_pass_rate = 87  # TODO: 根据实际执行结果计算
        
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
        
        # AI成功率（模拟计算）
        ai_success_rate = 92  # TODO: 根据实际执行结果计算
        
        # 用户统计
        user_total_query = text("SELECT COUNT(*) FROM sys_user WHERE enabled_flag = 1")
        user_total_result = await db.execute(user_total_query)
        user_total = user_total_result.scalar() or 0
        
        # 在线用户（模拟数据）
        user_online = 12  # TODO: 实现在线用户统计
        
        # 本月活跃用户（模拟数据）
        user_monthly_active = int(user_total * 0.75)  # TODO: 根据实际活动记录计算
        
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
            
            # API测试统计
            api_query = text("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count
                FROM api_test_executions 
                WHERE DATE(creation_date) = :current_date
            """)
            api_result = await db.execute(api_query, {"current_date": current_date})
            api_data = api_result.fetchone()
            
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
        # 活跃项目排行（按最近活动时间）
        active_projects_query = text("""
            SELECT 
                p.id,
                p.name,
                p.updation_date as last_activity,
                CASE 
                    WHEN p.updation_date >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 95
                    WHEN p.updation_date >= DATE_SUB(NOW(), INTERVAL 3 DAY) THEN 85
                    WHEN p.updation_date >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 70
                    WHEN p.updation_date >= DATE_SUB(NOW(), INTERVAL 14 DAY) THEN 50
                    ELSE 30
                END as activity_score
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
                "activity_score": row.activity_score
            }
            for row in active_projects_result.fetchall()
        ]
        
        # 模块使用热力图统计
        module_usage = {
            "test_cases": 0,
            "api_testing": 0,
            "ui_automation": 0,
            "ai_intelligence": 0,
            "data_factory": 0,
            "reviews": 0
        }
        
        # 测试用例模块
        testcase_query = text("SELECT COUNT(*) FROM test_cases WHERE enabled_flag = 1")
        testcase_result = await db.execute(testcase_query)
        module_usage["test_cases"] = testcase_result.scalar() or 0
        
        # API测试模块
        api_query = text("SELECT COUNT(*) FROM api_test_executions")
        api_result = await db.execute(api_query)
        module_usage["api_testing"] = api_result.scalar() or 0
        
        # UI自动化模块 - 使用正确的表名
        ui_query = text("SELECT COUNT(*) FROM ui_executions")
        ui_result = await db.execute(ui_query)
        module_usage["ui_automation"] = ui_result.scalar() or 0
        
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
    获取API测试接口树统计
    """
    try:
        # 获取API项目及其接口统计
        api_projects_query = text("""
            SELECT 
                p.name as project_name,
                COUNT(DISTINCT r.id) as interface_count,
                COUNT(DISTINCT CASE WHEN h.status_code >= 200 AND h.status_code < 300 THEN h.id END) as success_count,
                COUNT(DISTINCT CASE WHEN h.status_code >= 400 OR h.error_message IS NOT NULL THEN h.id END) as failed_count
            FROM api_projects p
            LEFT JOIN api_collections c ON p.id = c.api_project_id AND c.enabled_flag = 1
            LEFT JOIN api_requests r ON c.id = r.collection_id AND r.enabled_flag = 1
            LEFT JOIN api_request_histories h ON r.id = h.request_id
            WHERE p.enabled_flag = 1
            GROUP BY p.id, p.name
            HAVING interface_count > 0
            ORDER BY interface_count DESC
            LIMIT 10
        """)
        api_projects_result = await db.execute(api_projects_query)
        api_projects_data = api_projects_result.fetchall()
        
        # 构建统计数据
        interface_stats = []
        for row in api_projects_data:
            total_interfaces = row.interface_count or 0
            success_count = row.success_count or 0
            failed_count = row.failed_count or 0
            
            interface_stats.append({
                "project_name": row.project_name,
                "total_interfaces": total_interfaces,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": round((success_count / (success_count + failed_count) * 100), 1) if (success_count + failed_count) > 0 else 0
            })
        
        # 获取总体统计
        total_stats_query = text("""
            SELECT 
                COUNT(DISTINCT p.id) as total_projects,
                COUNT(DISTINCT r.id) as total_interfaces,
                COUNT(DISTINCT CASE WHEN h.status_code >= 200 AND h.status_code < 300 THEN h.id END) as total_success,
                COUNT(DISTINCT CASE WHEN h.status_code >= 400 OR h.error_message IS NOT NULL THEN h.id END) as total_failed
            FROM api_projects p
            LEFT JOIN api_collections c ON p.id = c.api_project_id AND c.enabled_flag = 1
            LEFT JOIN api_requests r ON c.id = r.collection_id AND r.enabled_flag = 1
            LEFT JOIN api_request_histories h ON r.id = h.request_id
            WHERE p.enabled_flag = 1
        """)
        total_stats_result = await db.execute(total_stats_query)
        total_stats_data = total_stats_result.fetchone()
        
        total_interfaces = total_stats_data.total_interfaces or 0
        total_success = total_stats_data.total_success or 0
        total_failed = total_stats_data.total_failed or 0
        
        stats_data = {
            "interface_stats": interface_stats,
            "total_stats": {
                "total_projects": total_stats_data.total_projects or 0,
                "total_interfaces": total_interfaces,
                "total_success": total_success,
                "total_failed": total_failed,
                "overall_success_rate": round((total_success / (total_success + total_failed) * 100), 1) if (total_success + total_failed) > 0 else 0
            }
        }
        
        return success_response(data=stats_data, message="获取API接口统计成功")
        
    except Exception as e:
        logger.error(f"[首页看板] 获取API接口统计失败: {str(e)}")
        return error_response(message=f"获取API接口统计失败: {str(e)}")