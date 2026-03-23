"""
API v1版本
"""

from fastapi import APIRouter
from app.api.v1.system import router as system_router
from app.api.v1.monitor import router as monitor_router
from app.api.v1.common.health.controller import router as health_router
from app.api.v1.oauth.controller import router as oauth_router
from app.api.v1.ai import router as ai_router
from app.api.v1.ai_intelligence.controller import router as ai_intelligence_router
from app.api.v1.projects import router as projects_router
from app.api.v1.testcases.controller import router as testcases_router
from app.api.v1.api_testing.controller import router as api_testing_router
from app.api.v1.ui_automation.controller import router as ui_automation_router
from app.api.v1.data_factory.controller import router as data_factory_router
from app.api.v1.reviews.controller import router as reviews_router
from app.api.v1.assistant.controller import router as assistant_router
from app.api.v1.notifications.controller import router as notifications_router
from app.api.v1.dashboard.controller import router as dashboard_router
# L-Tester 迁移模块
from app.api.v1.cloud_device.controller import router as cloud_device_router
from app.api.v1.api_automation.controller import router as api_automation_router
from app.api.v1.web_management.controller import router as web_management_router
from app.api.v1.app_management.controller import router as app_management_router
from app.api.v1.task_scheduler.controller import router as task_scheduler_router
from app.api.v1.app_mitmproxy.controller import router as app_mitmproxy_router

# 创建v1路由
router = APIRouter(prefix="/v1")

# 注册子路由
router.include_router(system_router, prefix="/system", tags=["系统管理"])
router.include_router(monitor_router, prefix="/monitor", tags=["系统监控"])
router.include_router(health_router, prefix="/common/health", tags=["健康检查"])
router.include_router(oauth_router)  # OAuth router 已经在 controller 中定义了 prefix="/oauth"
router.include_router(ai_router, prefix="/ai", tags=["AI管理"])
router.include_router(ai_intelligence_router, prefix="/ai_intelligence", tags=["AI智能化"])
router.include_router(projects_router, prefix="/projects", tags=["项目管理"])
router.include_router(testcases_router, tags=["测试用例管理"])
router.include_router(api_testing_router, tags=["API测试"])
router.include_router(ui_automation_router, prefix="/ui_automation", tags=["UI自动化"])
router.include_router(data_factory_router, tags=["数据工厂"])
router.include_router(reviews_router, tags=["用例评审"])
router.include_router(assistant_router, tags=["AI助手"])
router.include_router(notifications_router, tags=["统一通知系统"])
router.include_router(dashboard_router, tags=["首页看板"])

# L-Tester 迁移模块路由
router.include_router(cloud_device_router, prefix="/cloud_device", tags=["云真机管理"])
router.include_router(api_automation_router, prefix="/api_automation", tags=["接口自动化"])
router.include_router(web_management_router, prefix="/web_management", tags=["Web管理模块"])
router.include_router(app_management_router, prefix="/app_management", tags=["APP管理"])
router.include_router(task_scheduler_router, prefix="/task_scheduler", tags=["定时任务调度"])
router.include_router(app_mitmproxy_router, prefix="/mitmproxy", tags=["APP抓包( mitmproxy )"])

__all__ = ["router"]
