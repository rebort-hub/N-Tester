"""
UI自动化模块 - 控制器
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from .schema import (
    UIProjectCreateSchema,
    UIProjectUpdateSchema,
    UIElementGroupCreateSchema,
    UIElementGroupUpdateSchema,
    UIElementCreateSchema,
    UIElementUpdateSchema,
    UIPageObjectCreateSchema,
    UIPageObjectUpdateSchema,
    UITestCaseCreateSchema,
    UITestCaseUpdateSchema,
    UITestSuiteCreateSchema,
    UITestSuiteUpdateSchema,
    UITestStepCreateSchema,
    UITestStepUpdateSchema,
    TestStepReorderSchema,
    ExecutionRequestSchema,
    CodeGenerationSchema
)
from .service import (
    UIProjectService,
    UIElementGroupService,
    UIElementService,
    UIPageObjectService,
    UITestCaseService,
    UITestSuiteService,
    UITestStepService,
    UIExecutionService,
    UICodeGenerationService,
    UIReportService,
    UIElementValidationService
)

router = APIRouter()


# ==================== UI项目管理 ====================
@router.post("/projects", summary="创建UI项目")
async def create_ui_project(
    data: UIProjectCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建UI项目"""
    result = await UIProjectService.create_ui_project(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.get("/projects", summary="获取UI项目列表")
async def get_ui_project_list(
    project_id: Optional[int] = Query(None, description="项目ID"),
    name: Optional[str] = Query(None, description="项目名称"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取UI项目列表"""
    result = await UIProjectService.get_ui_project_list(db, project_id, name, page, page_size)
    return success_response(data=result)


@router.get("/projects/{ui_project_id}", summary="获取UI项目详情")
async def get_ui_project(
    ui_project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取UI项目详情"""
    result = await UIProjectService.get_ui_project(db, ui_project_id)
    return success_response(data=result)


@router.put("/projects/{ui_project_id}", summary="更新UI项目")
async def update_ui_project(
    ui_project_id: int,
    data: UIProjectUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新UI项目"""
    result = await UIProjectService.update_ui_project(db, ui_project_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/projects/{ui_project_id}", summary="删除UI项目")
async def delete_ui_project(
    ui_project_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除UI项目"""
    await UIProjectService.delete_ui_project(db, ui_project_id, user_id)
    return success_response(message="删除成功")


# ==================== UI元素分组管理 ====================
@router.post("/element-groups", summary="创建元素分组")
async def create_element_group(
    data: UIElementGroupCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建元素分组"""
    result = await UIElementGroupService.create_element_group(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.get("/element-groups/tree", summary="获取元素分组树")
async def get_element_group_tree(
    ui_project_id: int = Query(..., description="UI项目ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取元素分组树"""
    result = await UIElementGroupService.get_element_group_tree(db, ui_project_id)
    return success_response(data=result)


@router.put("/element-groups/{group_id}", summary="更新元素分组")
async def update_element_group(
    group_id: int,
    data: UIElementGroupUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新元素分组"""
    result = await UIElementGroupService.update_element_group(db, group_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/element-groups/{group_id}", summary="删除元素分组")
async def delete_element_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除元素分组"""
    await UIElementGroupService.delete_element_group(db, group_id, user_id)
    return success_response(message="删除成功")


# ==================== UI元素管理 ====================
@router.post("/elements", summary="创建UI元素")
async def create_element(
    data: UIElementCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建UI元素"""
    result = await UIElementService.create_element(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.get("/elements", summary="获取UI元素列表")
async def get_element_list(
    group_id: int = Query(..., description="分组ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取UI元素列表"""
    result = await UIElementService.get_element_list(db, group_id, page, page_size)
    return success_response(data=result)


@router.get("/elements/{element_id}", summary="获取UI元素详情")
async def get_element(
    element_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取UI元素详情"""
    result = await UIElementService.get_element(db, element_id)
    return success_response(data=result)


@router.put("/elements/{element_id}", summary="更新UI元素")
async def update_element(
    element_id: int,
    data: UIElementUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新UI元素"""
    result = await UIElementService.update_element(db, element_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/elements/{element_id}", summary="删除UI元素")
async def delete_element(
    element_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除UI元素"""
    await UIElementService.delete_element(db, element_id, user_id)
    return success_response(message="删除成功")


# ==================== UI页面对象管理 ====================
@router.post("/page-objects", summary="创建页面对象")
async def create_page_object(
    data: UIPageObjectCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建页面对象"""
    result = await UIPageObjectService.create_page_object(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.get("/page-objects", summary="获取页面对象列表")
async def get_page_object_list(
    ui_project_id: int = Query(..., description="UI项目ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取页面对象列表"""
    result = await UIPageObjectService.get_page_object_list(db, ui_project_id, page, page_size)
    return success_response(data=result)


@router.get("/page-objects/{page_object_id}", summary="获取页面对象详情")
async def get_page_object(
    page_object_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取页面对象详情"""
    result = await UIPageObjectService.get_page_object(db, page_object_id)
    return success_response(data=result)


@router.put("/page-objects/{page_object_id}", summary="更新页面对象")
async def update_page_object(
    page_object_id: int,
    data: UIPageObjectUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新页面对象"""
    result = await UIPageObjectService.update_page_object(db, page_object_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/page-objects/{page_object_id}", summary="删除页面对象")
async def delete_page_object(
    page_object_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除页面对象"""
    await UIPageObjectService.delete_page_object(db, page_object_id, user_id)
    return success_response(message="删除成功")


# ==================== UI测试用例管理 ====================
@router.post("/test-cases", summary="创建测试用例")
async def create_test_case(
    data: UITestCaseCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建测试用例"""
    result = await UITestCaseService.create_test_case(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.get("/test-cases", summary="获取测试用例列表")
async def get_test_case_list(
    ui_project_id: int = Query(..., description="UI项目ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页数量"),
    name: Optional[str] = Query(None, description="用例名称搜索"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例列表"""
    result = await UITestCaseService.get_test_case_list(
        db, ui_project_id, page, page_size, name, priority
    )
    return success_response(data=result)


@router.get("/test-cases/{test_case_id}", summary="获取测试用例详情")
async def get_test_case(
    test_case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例详情"""
    result = await UITestCaseService.get_test_case(db, test_case_id)
    return success_response(data=result)


@router.put("/test-cases/{test_case_id}", summary="更新测试用例")
async def update_test_case(
    test_case_id: int,
    data: UITestCaseUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新测试用例"""
    result = await UITestCaseService.update_test_case(db, test_case_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/test-cases/{test_case_id}", summary="删除测试用例")
async def delete_test_case(
    test_case_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除测试用例"""
    await UITestCaseService.delete_test_case(db, test_case_id, user_id)
    return success_response(message="删除成功")


# ==================== UI测试套件管理 ====================
@router.post("/test-suites", summary="创建测试套件")
async def create_test_suite(
    data: UITestSuiteCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建测试套件"""
    result = await UITestSuiteService.create_test_suite(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.get("/test-suites", summary="获取测试套件列表")
async def get_test_suite_list(
    ui_project_id: int = Query(..., description="UI项目ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=1000, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取测试套件列表"""
    result = await UITestSuiteService.get_test_suite_list(db, ui_project_id, page, page_size)
    return success_response(data=result)


@router.get("/test-suites/{test_suite_id}", summary="获取测试套件详情")
async def get_test_suite(
    test_suite_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试套件详情"""
    result = await UITestSuiteService.get_test_suite(db, test_suite_id)
    return success_response(data=result)


@router.put("/test-suites/{test_suite_id}", summary="更新测试套件")
async def update_test_suite(
    test_suite_id: int,
    data: UITestSuiteUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新测试套件"""
    result = await UITestSuiteService.update_test_suite(db, test_suite_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/test-suites/{test_suite_id}", summary="删除测试套件")
async def delete_test_suite(
    test_suite_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除测试套件"""
    await UITestSuiteService.delete_test_suite(db, test_suite_id, user_id)
    return success_response(message="删除成功")



# ==================== UI测试步骤管理 ====================
@router.get("/test-cases/{test_case_id}/steps", summary="获取测试用例的步骤列表")
async def get_test_case_steps(
    test_case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取测试用例的所有步骤"""
    result = await UITestStepService.get_test_steps_by_case(db, test_case_id)
    return success_response(data=result)


@router.post("/test-steps", summary="创建测试步骤")
async def create_test_step(
    data: UITestStepCreateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """创建测试步骤"""
    result = await UITestStepService.create_test_step(db, data, user_id)
    return success_response(data=result, message="创建成功")


@router.post("/test-steps/batch", summary="批量创建测试步骤")
async def batch_create_test_steps(
    steps_data: List[UITestStepCreateSchema],
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """批量创建测试步骤"""
    result = await UITestStepService.batch_create_test_steps(db, steps_data, user_id)
    return success_response(data=result, message=f"成功创建{len(result)}个步骤")


@router.put("/test-steps/reorder", summary="调整步骤顺序")
async def reorder_test_steps(
    data: TestStepReorderSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """调整测试步骤顺序"""
    await UITestStepService.reorder_test_steps(
        db, 
        data.test_case_id, 
        data.step_orders, 
        user_id
    )
    return success_response(message="步骤顺序调整成功")


@router.put("/test-steps/{step_id}", summary="更新测试步骤")
async def update_test_step(
    step_id: int,
    data: UITestStepUpdateSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新测试步骤"""
    result = await UITestStepService.update_test_step(db, step_id, data, user_id)
    return success_response(data=result, message="更新成功")


@router.delete("/test-steps/{step_id}", summary="删除测试步骤")
async def delete_test_step(
    step_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除测试步骤"""
    await UITestStepService.delete_test_step(db, step_id, user_id)
    return success_response(message="删除成功")



# ==================== UI测试执行 ====================
@router.get("/browsers/check", summary="检查浏览器可用性")
async def check_browser_availability(
    browser_type: str = Query('chrome', description="浏览器类型: chrome, firefox, edge, safari")
):
    """检查指定浏览器是否可用"""
    from .selenium_engine import SeleniumTestEngine
    
    is_available, error_msg = SeleniumTestEngine.check_browser_available(browser_type)
    
    return success_response(data={
        'browser_type': browser_type,
        'is_available': is_available,
        'message': error_msg if not is_available else '浏览器可用',
        'install_tips': {
            'chrome': {
                'macos': 'brew install --cask google-chrome',
                'windows': '访问 https://www.google.com/chrome/ 下载安装',
                'linux': 'sudo apt-get install google-chrome-stable'
            },
            'firefox': {
                'macos': 'brew install --cask firefox',
                'windows': '访问 https://www.mozilla.org/firefox/ 下载安装',
                'linux': 'sudo apt-get install firefox'
            },
            'edge': {
                'macos': 'brew install --cask microsoft-edge',
                'windows': 'Windows 10+ 自带 Edge 浏览器',
                'linux': '访问 https://www.microsoft.com/edge 下载安装'
            },
            'safari': {
                'macos': 'macOS 自带 Safari，需执行: sudo safaridriver --enable',
                'windows': 'Safari 不支持 Windows',
                'linux': 'Safari 不支持 Linux'
            }
        }.get(browser_type, {})
    })


@router.get("/browsers/check-all", summary="检查所有浏览器可用性")
async def check_all_browsers():
    """检查所有支持的浏览器可用性"""
    from .selenium_engine import SeleniumTestEngine
    
    browsers = ['chrome', 'firefox', 'edge', 'safari']
    results = []
    
    for browser in browsers:
        is_available, error_msg = SeleniumTestEngine.check_browser_available(browser)
        results.append({
            'browser_type': browser,
            'is_available': is_available,
            'message': error_msg if not is_available else '浏览器可用'
        })
    
    return success_response(data={
        'browsers': results,
        'available_count': sum(1 for r in results if r['is_available']),
        'total_count': len(results)
    })


@router.post("/test-suites/{test_suite_id}/execute", summary="执行测试套件")
async def execute_test_suite(
    test_suite_id: int,
    config: ExecutionRequestSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """执行测试套件"""
    result = await UIExecutionService.execute_test_suite(
        db, test_suite_id, config.model_dump(), user_id
    )
    return success_response(data=result, message="测试套件开始执行")


@router.post("/test-cases/{test_case_id}/execute", summary="执行测试用例")
async def execute_test_case(
    test_case_id: int,
    config: ExecutionRequestSchema,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """执行测试用例"""
    result = await UIExecutionService.execute_test_case(
        db, test_case_id, config.model_dump(), user_id
    )
    return success_response(data=result, message="测试用例开始执行")


@router.post("/test-cases/batch-execute", summary="批量执行测试用例")
async def batch_execute_test_cases(
    request: dict,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """批量执行测试用例"""
    test_case_ids = request.get('test_case_ids', [])
    ui_project_id = request.get('ui_project_id')
    config = {
        'engine_type': request.get('engine_type', 'playwright'),
        'browser_type': request.get('browser_type', 'chromium'),
        'channel': request.get('channel'),
        'headless': request.get('headless', True),
        'parallel': request.get('parallel', False),
        'max_workers': request.get('max_workers', 1),
        'timeout': request.get('timeout', 30000)
    }
    
    result = await UIExecutionService.batch_execute_test_cases(
        db, ui_project_id, test_case_ids, config, user_id
    )
    return success_response(data=result, message=f"开始批量执行 {len(test_case_ids)} 个测试用例")


@router.post("/test-suites/batch-execute", summary="批量执行测试套件")
async def batch_execute_test_suites(
    request: dict,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """批量执行测试套件"""
    suite_ids = request.get('suite_ids', [])
    config = {
        'engine_type': request.get('engine_type', 'playwright'),
        'browser_type': request.get('browser_type', 'chromium'),
        'channel': request.get('channel'),
        'headless': request.get('headless', True),
        'parallel': request.get('parallel', False),
        'max_workers': request.get('max_workers', 1),
        'timeout': request.get('timeout', 30000)
    }
    
    result = await UIExecutionService.batch_execute_test_suites(
        db, suite_ids, config, user_id
    )
    return success_response(data=result, message=f"开始批量执行 {len(suite_ids)} 个测试套件")


@router.post("/executions/{execution_id}/stop", summary="停止执行")
async def stop_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """停止执行"""
    await UIExecutionService.stop_execution(db, execution_id, user_id)
    return success_response(message="执行已停止")


@router.get("/executions/{execution_id}/status", summary="获取执行状态")
async def get_execution_status(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取执行状态"""
    result = await UIExecutionService.get_execution_status(db, execution_id)
    return success_response(data=result)


@router.get("/executions/{execution_id}/logs", summary="获取执行日志")
async def get_execution_logs(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取执行日志"""
    logs = await UIExecutionService.get_execution_logs(db, execution_id)
    return success_response(data={'logs': logs})


# ==================== UI执行记录管理 ====================
@router.get("/executions", summary="获取执行历史列表")
async def get_execution_list(
    ui_project_id: Optional[int] = Query(None, description="UI项目ID"),
    suite_id: Optional[int] = Query(None, description="测试套件ID"),
    test_case_id: Optional[int] = Query(None, description="测试用例ID"),
    status: Optional[str] = Query(None, description="执行状态"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """获取执行历史列表"""
    query = {
        'ui_project_id': ui_project_id,
        'suite_id': suite_id,
        'test_case_id': test_case_id,
        'status': status,
        'start_date': start_date,
        'end_date': end_date
    }
    result = await UIExecutionService.get_execution_list(db, query, page, page_size)
    return success_response(data=result)


@router.get("/executions/statistics", summary="获取执行统计")
async def get_execution_statistics(
    ui_project_id: Optional[int] = Query(None, description="UI项目ID"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db)
):
    """获取执行统计数据"""
    from datetime import datetime
    
    # 解析日期
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    result = await UIReportService.get_execution_statistics(
        db, ui_project_id, start, end
    )
    return success_response(data=result)


@router.get("/executions/{execution_id}/export", summary="导出执行报告")
async def export_execution_report(
    execution_id: int,
    format: str = Query('html', description="导出格式: html/pdf"),
    db: AsyncSession = Depends(get_db)
):
    """导出执行报告"""
    report = await UIReportService.export_execution_report(db, execution_id, format)
    
    from fastapi.responses import HTMLResponse
    if format == 'html':
        return HTMLResponse(content=report)
    else:
        return success_response(data={'report': report})


@router.get("/executions/{execution_id}", summary="获取执行详情")
async def get_execution_detail(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取执行详情"""
    result = await UIExecutionService.get_execution_detail(db, execution_id)
    return success_response(data=result)


@router.get("/executions/{execution_id}/logs", summary="获取执行日志")
async def get_execution_logs(
    execution_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取执行日志"""
    result = await UIExecutionService.get_execution_detail(db, execution_id)
    return success_response(data={'logs': result.get('logs', '')})


@router.delete("/executions/{execution_id}", summary="删除执行记录")
async def delete_execution(
    execution_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """删除执行记录"""
    await UIExecutionService.delete_execution(db, execution_id, user_id)
    return success_response(message="删除成功")



# ==================== 代码生成 ====================
@router.post("/page-objects/{page_object_id}/generate-code", summary="生成页面对象代码")
async def generate_page_object_code(
    page_object_id: int,
    config: CodeGenerationSchema,
    db: AsyncSession = Depends(get_db)
):
    """生成页面对象代码"""
    code = await UICodeGenerationService.generate_page_object_code(
        db,
        page_object_id,
        config.language,
        config.framework,
        config.include_comments
    )
    return success_response(data={'code': code}, message="代码生成成功")


@router.get("/page-objects/{page_object_id}/preview-code", summary="预览页面对象代码")
async def preview_page_object_code(
    page_object_id: int,
    language: str = Query('javascript', description="编程语言"),
    framework: str = Query('playwright', description="框架"),
    include_comments: bool = Query(True, description="是否包含注释"),
    db: AsyncSession = Depends(get_db)
):
    """预览页面对象代码"""
    code = await UICodeGenerationService.generate_page_object_code(
        db,
        page_object_id,
        language,
        framework,
        include_comments
    )
    return success_response(data={'code': code})


@router.post("/projects/{ui_project_id}/generate-code", summary="生成项目代码")
async def generate_project_code(
    ui_project_id: int,
    config: CodeGenerationSchema,
    db: AsyncSession = Depends(get_db)
):
    """生成项目所有页面对象代码"""
    code_files = await UICodeGenerationService.generate_project_code(
        db,
        ui_project_id,
        config.language,
        config.framework,
        config.include_comments
    )
    return success_response(data={'files': code_files}, message=f"成功生成{len(code_files)}个文件")



# ==================== 元素智能定位 ====================
@router.post("/elements/validate-locator", summary="验证元素定位器")
async def validate_locator(
    data: Dict[str, str],
    db: AsyncSession = Depends(get_db)
):
    """验证元素定位器是否有效"""
    url = data.get('url')
    locator_strategy = data.get('locator_strategy')
    locator_value = data.get('locator_value')
    
    if not all([url, locator_strategy, locator_value]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必要参数"
        )
    
    result = await UIElementValidationService.validate_locator(
        db, url, locator_strategy, locator_value
    )
    return success_response(data=result)


@router.post("/elements/suggest-locator", summary="推荐定位策略")
async def suggest_locator(
    data: Dict[str, str],
    db: AsyncSession = Depends(get_db)
):
    """根据元素HTML推荐最佳定位策略"""
    url = data.get('url')
    element_html = data.get('element_html')
    
    if not all([url, element_html]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必要参数"
        )
    
    suggestions = await UIElementValidationService.suggest_locator(
        db, url, element_html
    )
    return success_response(data={'suggestions': suggestions})



@router.post("/test-cases/{test_case_id}/generate-code", summary="生成测试用例代码")
async def generate_test_case_code(
    test_case_id: int,
    config: CodeGenerationSchema,
    db: AsyncSession = Depends(get_db)
):
    """生成测试用例代码"""
    code = await UICodeGenerationService.generate_test_case_code(
        db,
        test_case_id,
        config.language,
        config.framework
    )
    return success_response(data={'code': code}, message="测试用例代码生成成功")
