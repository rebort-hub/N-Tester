/**
 * UI自动化测试模块接口
 */
import request from '/@/utils/request'
import axios from 'axios'
import { getApiBaseUrl } from '/@/utils/config'
import { Session } from '/@/utils/storage'

// ==================== UI项目管理 ====================
export const uiProjectApi = {
  // 创建UI项目
  create: (data: any) => request.post('/v1/ui_automation/projects', data),
  
  // 获取UI项目列表
  list: (params: any) => request.get('/v1/ui_automation/projects', { params }),
  
  // 获取UI项目详情
  get: (id: number) => request.get(`/v1/ui_automation/projects/${id}`),
  
  // 更新UI项目
  update: (id: number, data: any) => request.put(`/v1/ui_automation/projects/${id}`, data),
  
  // 删除UI项目
  delete: (id: number) => request.delete(`/v1/ui_automation/projects/${id}`),
  
  // 生成项目代码
  generateCode: (id: number, data: any) => request.post(`/v1/ui_automation/projects/${id}/generate-code`, data)
}

// ==================== 元素分组管理 ====================
export const uiElementGroupApi = {
  // 创建元素分组
  create: (data: any) => request.post('/v1/ui_automation/element-groups', data),
  
  // 获取元素分组树
  tree: (uiProjectId: number) => request.get('/v1/ui_automation/element-groups/tree', { params: { ui_project_id: uiProjectId } }),
  
  // 更新元素分组
  update: (id: number, data: any) => request.put(`/v1/ui_automation/element-groups/${id}`, data),
  
  // 删除元素分组
  delete: (id: number) => request.delete(`/v1/ui_automation/element-groups/${id}`)
}

// ==================== UI元素管理 ====================
export const uiElementApi = {
  // 创建UI元素
  create: (data: any) => request.post('/v1/ui_automation/elements', data),
  
  // 获取UI元素列表
  list: (params: any) => request.get('/v1/ui_automation/elements', { params }),
  
  // 获取UI元素详情
  get: (id: number) => request.get(`/v1/ui_automation/elements/${id}`),
  
  // 更新UI元素
  update: (id: number, data: any) => request.put(`/v1/ui_automation/elements/${id}`, data),
  
  // 删除UI元素
  delete: (id: number) => request.delete(`/v1/ui_automation/elements/${id}`),
  
  // 验证元素定位器
  validateLocator: (data: any) => request.post('/v1/ui_automation/elements/validate-locator', data),
  
  // 推荐定位策略
  suggestLocator: (data: any) => request.post('/v1/ui_automation/elements/suggest-locator', data)
}

// ==================== 页面对象管理 ====================
export const uiPageObjectApi = {
  // 创建页面对象
  create: (data: any) => request.post('/v1/ui_automation/page-objects', data),
  
  // 获取页面对象列表
  list: (params: any) => request.get('/v1/ui_automation/page-objects', { params }),
  
  // 获取页面对象详情
  get: (id: number) => request.get(`/v1/ui_automation/page-objects/${id}`),
  
  // 更新页面对象
  update: (id: number, data: any) => request.put(`/v1/ui_automation/page-objects/${id}`, data),
  
  // 删除页面对象
  delete: (id: number) => request.delete(`/v1/ui_automation/page-objects/${id}`),
  
  // 生成页面对象代码
  generateCode: (id: number, data: any) => request.post(`/v1/ui_automation/page-objects/${id}/generate-code`, data),
  
  // 预览页面对象代码
  previewCode: (id: number, params: any) => request.get(`/v1/ui_automation/page-objects/${id}/preview-code`, { params })
}

// ==================== 测试用例管理 ====================
export const uiTestCaseApi = {
  // 创建测试用例
  create: (data: any) => request.post('/v1/ui_automation/test-cases', data),
  
  // 获取测试用例列表
  list: (params: any) => request.get('/v1/ui_automation/test-cases', { params }),
  
  // 获取测试用例详情
  get: (id: number) => request.get(`/v1/ui_automation/test-cases/${id}`),
  
  // 更新测试用例
  update: (id: number, data: any) => request.put(`/v1/ui_automation/test-cases/${id}`, data),
  
  // 删除测试用例
  delete: (id: number) => request.delete(`/v1/ui_automation/test-cases/${id}`),
  
  // 执行测试用例
  execute: (id: number, data: any) => request.post(`/v1/ui_automation/test-cases/${id}/execute`, data),
  
  // 批量执行测试用例
  batchExecute: (data: any) => request.post('/v1/ui_automation/test-cases/batch-execute', data),
  
  // 生成测试用例代码
  generateCode: (id: number, data: any) => request.post(`/v1/ui_automation/test-cases/${id}/generate-code`, data)
}

// ==================== 测试步骤管理 ====================
export const uiTestStepApi = {
  // 获取测试用例的步骤列表
  listByCase: (testCaseId: number) => request.get(`/v1/ui_automation/test-cases/${testCaseId}/steps`),
  
  // 创建测试步骤
  create: (data: any) => request.post('/v1/ui_automation/test-steps', data),
  
  // 批量创建测试步骤
  batchCreate: (data: any) => request.post('/v1/ui_automation/test-steps/batch', data),
  
  // 更新测试步骤
  update: (id: number, data: any) => request.put(`/v1/ui_automation/test-steps/${id}`, data),
  
  // 删除测试步骤
  delete: (id: number) => request.delete(`/v1/ui_automation/test-steps/${id}`),
  
  // 调整步骤顺序
  reorder: (data: any) => request.put('/v1/ui_automation/test-steps/reorder', data)
}

// ==================== 测试套件管理 ====================
export const uiTestSuiteApi = {
  // 创建测试套件
  create: (data: any) => request.post('/v1/ui_automation/test-suites', data),
  
  // 获取测试套件列表
  list: (params: any) => request.get('/v1/ui_automation/test-suites', { params }),
  
  // 获取测试套件详情
  get: (id: number) => request.get(`/v1/ui_automation/test-suites/${id}`),
  
  // 更新测试套件
  update: (id: number, data: any) => request.put(`/v1/ui_automation/test-suites/${id}`, data),
  
  // 删除测试套件
  delete: (id: number) => request.delete(`/v1/ui_automation/test-suites/${id}`),
  
  // 执行测试套件
  execute: (id: number, data: any) => request.post(`/v1/ui_automation/test-suites/${id}/execute`, data),
  
  // 批量执行测试套件
  batchExecute: (data: any) => request.post('/v1/ui_automation/test-suites/batch-execute', data)
}

// ==================== 执行记录管理 ====================
export const uiExecutionApi = {
  // 获取执行历史列表
  list: (params: any) => request.get('/v1/ui_automation/executions', { params }),
  
  // 获取执行详情
  get: (id: number) => request.get(`/v1/ui_automation/executions/${id}`),
  
  // 获取执行状态
  getStatus: (id: number) => request.get(`/v1/ui_automation/executions/${id}/status`),
  
  // 获取执行日志
  getLogs: (id: number) => request.get(`/v1/ui_automation/executions/${id}/logs`),
  
  // 停止执行
  stop: (id: number) => request.post(`/v1/ui_automation/executions/${id}/stop`),
  
  // 删除执行记录
  delete: (id: number) => request.delete(`/v1/ui_automation/executions/${id}`),
  
  // 获取执行统计
  statistics: (params: any) => request.get('/v1/ui_automation/executions/statistics', { params }),
  
  // 导出执行报告
  export: async (id: number, params: any) => {
    // 直接使用axios实例，绕过request工具的响应拦截器
    const service = axios.create({
      baseURL: getApiBaseUrl(),
      timeout: 50000,
    })
    
    // 添加认证头
    const token = Session.get('token')
    const headers: any = {
      'Accept': 'text/html'
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
      headers['token'] = token
    }
    
    const response = await service.get(`/v1/ui_automation/executions/${id}/export`, {
      params,
      responseType: 'text',
      headers
    })
    
    return { data: response.data }
  }
}

// ==================== 浏览器管理 ====================
export const uiBrowserApi = {
  // 检查单个浏览器可用性
  check: (browserType: string) => request.get('/v1/ui_automation/browsers/check', { params: { browser_type: browserType } }),
  
  // 检查所有浏览器可用性
  checkAll: () => request.get('/v1/ui_automation/browsers/check-all')
}
