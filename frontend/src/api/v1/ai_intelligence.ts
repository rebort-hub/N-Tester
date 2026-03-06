/**
 * AI智能化模块接口
 */
import request from '/@/utils/request'

// ==================== 需求文档管理 ====================
export const requirementDocumentApi = {
  // 获取需求文档列表
  list: (params?: any) => request.get('/v1/ai_intelligence/requirement-documents', { params }),
  
  // 上传需求文档
  upload: (data: FormData) => request.post('/v1/ai_intelligence/requirement-documents', data, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  // 获取需求文档详情
  get: (id: number) => request.get(`/v1/ai_intelligence/requirement-documents/${id}`),
  
  // 更新需求文档
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/requirement-documents/${id}`, data),
  
  // 删除需求文档
  delete: (id: number) => request.delete(`/v1/ai_intelligence/requirement-documents/${id}`),
  
  // 分析需求文档
  analyze: (id: number) => request.post(`/v1/ai_intelligence/requirement-documents/${id}/analyze`),
  
  // 获取分析结果
  getAnalysis: (id: number) => request.get(`/v1/ai_intelligence/requirement-documents/${id}/analysis`)
}

// ==================== AI模型配置 ====================
export const aiModelConfigApi = {
  // 获取AI模型配置列表
  list: (params?: any) => request.get('/v1/ai_intelligence/ai-model-configs', { params }),
  
  // 创建AI模型配置
  create: (data: any) => request.post('/v1/ai_intelligence/ai-model-configs', data),
  
  // 获取AI模型配置详情
  get: (id: number) => request.get(`/v1/ai_intelligence/ai-model-configs/${id}`),
  
  // 更新AI模型配置
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/ai-model-configs/${id}`, data),
  
  // 删除AI模型配置
  delete: (id: number) => request.delete(`/v1/ai_intelligence/ai-model-configs/${id}`)
}

// ==================== 提示词配置 ====================
export const promptConfigApi = {
  // 获取提示词配置列表
  list: (params?: any) => request.get('/v1/ai_intelligence/prompt-configs', { params }),
  
  // 创建提示词配置
  create: (data: any) => request.post('/v1/ai_intelligence/prompt-configs', data),
  
  // 获取提示词配置详情
  get: (id: number) => request.get(`/v1/ai_intelligence/prompt-configs/${id}`),
  
  // 更新提示词配置
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/prompt-configs/${id}`, data),
  
  // 删除提示词配置
  delete: (id: number) => request.delete(`/v1/ai_intelligence/prompt-configs/${id}`)
}

// ==================== 测试用例生成任务 ====================
export const generationTaskApi = {
  // 获取生成任务列表
  list: (params?: any) => request.get('/v1/ai_intelligence/generation-tasks', { params }),
  
  // 创建生成任务
  create: (data: any) => request.post('/v1/ai_intelligence/generation-tasks', data),
  
  // 获取生成任务详情
  get: (taskId: string) => request.get(`/v1/ai_intelligence/generation-tasks/${taskId}`),
  
  // 流式获取生成任务输出
  stream: (taskId: string) => `/v1/ai_intelligence/generation-tasks/${taskId}/stream`,
  
  // 保存到测试用例管理
  saveToTestcases: (taskId: string, data: any) => request.post(`/v1/ai_intelligence/generation-tasks/${taskId}/save-to-testcases`, data),
  
  // 删除生成任务
  delete: (taskId: string) => request.delete(`/v1/ai_intelligence/generation-tasks/${taskId}`),
  
  // 批量删除生成任务
  batchDelete: (taskIds: string[]) => request.post('/v1/ai_intelligence/generation-tasks/batch-delete', taskIds)
}

// ==================== 项目管理 ====================
export const projectApi = {
  // 获取主项目下的子项目
  getSubProjects: (projectId: number, params?: any) => request.get(`/v1/ai_intelligence/projects/${projectId}/sub-projects`, { params })
}

// ==================== 测试用例模板 ====================
export const testcaseTemplateApi = {
  // 获取模板列表
  list: (params?: any) => request.get('/v1/ai_intelligence/testcase-templates', { params }),
  
  // 获取模板详情
  get: (id: number) => request.get(`/v1/ai_intelligence/testcase-templates/${id}`),
  
  // 创建模板
  create: (data: any) => request.post('/v1/ai_intelligence/testcase-templates', data),
  
  // 更新模板
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/testcase-templates/${id}`, data),
  
  // 删除模板
  delete: (id: number) => request.delete(`/v1/ai_intelligence/testcase-templates/${id}`),
  
  // 导出模板
  export: (id: number) => request.get(`/v1/ai_intelligence/testcase-templates/${id}/export`, {
    responseType: 'blob'
  }),
  
  // 导入模板
  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/v1/ai_intelligence/testcase-templates/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 预览模板
  preview: (id: number, sampleData: any) => request.post(`/v1/ai_intelligence/testcase-templates/${id}/preview`, sampleData)
}

// ==================== AI智能浏览器用例 ====================
export const aiCaseApi = {
  // 获取AI用例列表
  list: (params?: any) => request.get('/v1/ai_intelligence/ai-cases', { params }),
  
  // 创建AI用例
  create: (data: any) => request.post('/v1/ai_intelligence/ai-cases', data),
  
  // 获取AI用例详情
  get: (id: number) => request.get(`/v1/ai_intelligence/ai-cases/${id}`),
  
  // 更新AI用例
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/ai-cases/${id}`, data),
  
  // 删除AI用例（硬删除）
  delete: (id: number) => request.delete(`/v1/ai_intelligence/ai-cases/${id}`),
  
  // 批量删除AI用例（硬删除）
  batchDelete: (case_ids: number[]) => request.post('/v1/ai_intelligence/ai-cases/batch-delete', { case_ids }),
  
  // 执行AI用例
  execute: (id: number, headless: boolean = false) => request.post(`/v1/ai_intelligence/ai-cases/${id}/execute`, null, {
    params: { headless }
  }),
  
  // 批量执行AI用例
  batchExecute: (data: { task_name: string, execution_mode: string, parallel_count: number, case_ids: number[] }) => 
    request.post('/v1/ai_intelligence/ai-cases/batch-execute', data),
  
  // 从测试用例模块批量导入
  importFromModules: (data: { project_id: number, module_ids: number[] }) => 
    request.post('/v1/ai_intelligence/ai-cases/import-from-modules', data),
  
  // 从Excel导入AI用例
  importFromExcel: (file: File, project_id?: number, module_id?: number) => {
    const formData = new FormData()
    formData.append('file', file)
    if (project_id) {
      formData.append('project_id', project_id.toString())
    }
    if (module_id) {
      formData.append('module_id', module_id.toString())
    }
    return request.post('/v1/ai_intelligence/ai-cases/import-from-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

// ==================== AI执行记录 ====================
export const aiExecutionRecordApi = {
  // 获取AI执行记录列表
  list: (params?: any) => request.get('/v1/ai_intelligence/ai-execution-records', { params }),
  
  // 创建AI执行记录
  create: (data: any) => request.post('/v1/ai_intelligence/ai-execution-records', data),
  
  // 获取AI执行记录详情
  get: (id: number) => request.get(`/v1/ai_intelligence/ai-execution-records/${id}`),
  
  // 删除AI执行记录（硬删除）
  delete: (id: number) => request.delete(`/v1/ai_intelligence/ai-execution-records/${id}`),
  
  // 获取执行状态（用于轮询）
  getStatus: (id: number) => request.get(`/v1/ai_intelligence/ai-execution-records/${id}/status`)
}

// ==================== Figma配置管理 ====================
export const figmaConfigApi = {
  // 获取Figma配置列表
  list: (params?: any) => request.get('/v1/ai_intelligence/figma-configs', { params }),
  
  // 创建Figma配置
  create: (data: any) => request.post('/v1/ai_intelligence/figma-configs', data),
  
  // 获取Figma配置详情
  get: (id: number) => request.get(`/v1/ai_intelligence/figma-configs/${id}`),
  
  // 更新Figma配置
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/figma-configs/${id}`, data),
  
  // 删除Figma配置
  delete: (id: number) => request.delete(`/v1/ai_intelligence/figma-configs/${id}`),
  
  // 提取需求（旧版，保留兼容）
  extract: (id: number) => request.post(`/v1/ai_intelligence/figma-configs/${id}/extract`),
  
  // 带模式的提取
  extractWithMode: (configId: number, mode: 'simple' | 'complete', forceRefresh: boolean = false) => 
    request.post(`/v1/ai_intelligence/figma-configs/${configId}/extract-with-mode?extraction_mode=${mode}&force_refresh=${forceRefresh}`),
  
  // 查询任务状态
  getTaskStatus: (taskId: string) => 
    request.get(`/v1/ai_intelligence/figma-extraction-tasks/${taskId}`),
  
  // 获取最新任务
  getLatestTask: (configId: number) => 
    request.get(`/v1/ai_intelligence/figma-configs/${configId}/latest-task`),
  
  // 预览
  preview: (configId: number) => 
    request.get(`/v1/ai_intelligence/figma-configs/${configId}/preview`),
  
  // ==================== 高级功能 ====================
  
  // 获取速率限制状态
  getRateLimitStatus: (configId: number) => 
    request.get(`/v1/ai_intelligence/figma-configs/${configId}/rate-limit-status`),
  
  // 获取缓存信息
  getCacheInfo: (configId: number) => 
    request.get(`/v1/ai_intelligence/figma-configs/${configId}/cache-info`),
  
  // 离线查看缓存数据
  getCachedData: (configId: number) => 
    request.get(`/v1/ai_intelligence/figma-configs/${configId}/cached-data`),
  
  // 清除缓存
  clearCache: (configId: number) => 
    request.delete(`/v1/ai_intelligence/figma-configs/${configId}/cache`),
  
  // 检查更新
  checkUpdates: (configId: number) => 
    request.get(`/v1/ai_intelligence/figma-configs/${configId}/check-updates`)
}

// ==================== AI测试套件管理 ====================
export const aiTestSuiteApi = {
  // 获取测试套件列表
  list: (params?: any) => request.get('/v1/ai_intelligence/ai-test-suites', { params }),
  
  // 创建测试套件
  create: (data: any) => request.post('/v1/ai_intelligence/ai-test-suites', data),
  
  // 获取测试套件详情
  get: (id: number) => request.get(`/v1/ai_intelligence/ai-test-suites/${id}`),
  
  // 更新测试套件
  update: (id: number, data: any) => request.put(`/v1/ai_intelligence/ai-test-suites/${id}`, data),
  
  // 删除测试套件
  delete: (id: number) => request.delete(`/v1/ai_intelligence/ai-test-suites/${id}`),
  
  // 执行测试套件
  execute: (id: number, data: { execution_name?: string, execution_mode: string }) => 
    request.post(`/v1/ai_intelligence/ai-test-suites/${id}/execute`, data),
  
  // 获取套件执行记录列表
  getExecutions: (params?: any) => request.get('/v1/ai_intelligence/ai-test-suite-executions', { params }),
  
  // 获取套件执行记录详情
  getExecutionDetail: (id: number) => request.get(`/v1/ai_intelligence/ai-test-suite-executions/${id}`)
}


// ==================== AI测试报告管理 ====================
export const aiTestReportApi = {
  // 获取测试报告列表
  list: (params?: any) => request.get('/v1/ai_intelligence/ai-test-reports', { params }),
  
  // 创建测试报告
  create: (data: any) => request.post('/v1/ai_intelligence/ai-test-reports', data),
  
  // 删除测试报告（硬删除）
  delete: (reportId: string) => request.delete(`/v1/ai_intelligence/ai-test-reports/${reportId}`)
}
