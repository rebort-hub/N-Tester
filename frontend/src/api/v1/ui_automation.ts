/**
 * UI自动化测试模块接口
 */
import request from '/@/utils/request'
import axios from 'axios'
import { getApiBaseUrl } from '/@/utils/config'
import { Session } from '/@/utils/storage'

export function useUiAutomationApi() {
  const uiProjectApi = {
    create: (data: any) => request.post('/v1/ui_automation/projects', data),
    list: (params: any) => request.get('/v1/ui_automation/projects', { params }),
    get: (id: number) => request.get(`/v1/ui_automation/projects/${id}`),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/projects/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/projects/${id}`),
    generateCode: (id: number, data: any) => request.post(`/v1/ui_automation/projects/${id}/generate-code`, data)
  }

  const uiElementGroupApi = {
    create: (data: any) => request.post('/v1/ui_automation/element-groups', data),
    tree: (uiProjectId: number) => request.get('/v1/ui_automation/element-groups/tree', { params: { ui_project_id: uiProjectId } }),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/element-groups/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/element-groups/${id}`)
  }

  const uiElementApi = {
    create: (data: any) => request.post('/v1/ui_automation/elements', data),
    list: (params: any) => request.get('/v1/ui_automation/elements', { params }),
    get: (id: number) => request.get(`/v1/ui_automation/elements/${id}`),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/elements/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/elements/${id}`),
    validateLocator: (data: any) => request.post('/v1/ui_automation/elements/validate-locator', data),
    suggestLocator: (data: any) => request.post('/v1/ui_automation/elements/suggest-locator', data)
  }

  const uiPageObjectApi = {
    create: (data: any) => request.post('/v1/ui_automation/page-objects', data),
    list: (params: any) => request.get('/v1/ui_automation/page-objects', { params }),
    get: (id: number) => request.get(`/v1/ui_automation/page-objects/${id}`),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/page-objects/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/page-objects/${id}`),
    generateCode: (id: number, data: any) => request.post(`/v1/ui_automation/page-objects/${id}/generate-code`, data),
    previewCode: (id: number, params: any) => request.get(`/v1/ui_automation/page-objects/${id}/preview-code`, { params })
  }

  const uiTestCaseApi = {
    create: (data: any) => request.post('/v1/ui_automation/test-cases', data),
    list: (params: any) => request.get('/v1/ui_automation/test-cases', { params }),
    get: (id: number) => request.get(`/v1/ui_automation/test-cases/${id}`),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/test-cases/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/test-cases/${id}`),
    execute: (id: number, data: any) => request.post(`/v1/ui_automation/test-cases/${id}/execute`, data),
    batchExecute: (data: any) => request.post('/v1/ui_automation/test-cases/batch-execute', data),
    generateCode: (id: number, data: any) => request.post(`/v1/ui_automation/test-cases/${id}/generate-code`, data)
  }

  const uiTestStepApi = {
    listByCase: (testCaseId: number) => request.get(`/v1/ui_automation/test-cases/${testCaseId}/steps`),
    create: (data: any) => request.post('/v1/ui_automation/test-steps', data),
    batchCreate: (data: any) => request.post('/v1/ui_automation/test-steps/batch', data),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/test-steps/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/test-steps/${id}`),
    reorder: (data: any) => request.put('/v1/ui_automation/test-steps/reorder', data)
  }

  const uiTestSuiteApi = {
    create: (data: any) => request.post('/v1/ui_automation/test-suites', data),
    list: (params: any) => request.get('/v1/ui_automation/test-suites', { params }),
    get: (id: number) => request.get(`/v1/ui_automation/test-suites/${id}`),
    update: (id: number, data: any) => request.put(`/v1/ui_automation/test-suites/${id}`, data),
    delete: (id: number) => request.delete(`/v1/ui_automation/test-suites/${id}`),
    execute: (id: number, data: any) => request.post(`/v1/ui_automation/test-suites/${id}/execute`, data),
    batchExecute: (data: any) => request.post('/v1/ui_automation/test-suites/batch-execute', data)
  }

  const uiExecutionApi = {
    list: (params: any) => request.get('/v1/ui_automation/executions', { params }),
    get: (id: number) => request.get(`/v1/ui_automation/executions/${id}`),
    getStatus: (id: number) => request.get(`/v1/ui_automation/executions/${id}/status`),
    getLogs: (id: number) => request.get(`/v1/ui_automation/executions/${id}/logs`),
    stop: (id: number) => request.post(`/v1/ui_automation/executions/${id}/stop`),
    delete: (id: number) => request.delete(`/v1/ui_automation/executions/${id}`),
    statistics: (params: any) => request.get('/v1/ui_automation/executions/statistics', { params }),
    export: async (id: number, params: any) => {
      const service = axios.create({
        baseURL: getApiBaseUrl(),
        timeout: 50000,
      })
      const token = Session.get('token')
      const headers: any = { Accept: 'text/html' }
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

  const uiBrowserApi = {
    check: (browserType: string) => request.get('/v1/ui_automation/browsers/check', { params: { browser_type: browserType } }),
    checkAll: () => request.get('/v1/ui_automation/browsers/check-all')
  }

  return {
    uiProjectApi,
    uiElementGroupApi,
    uiElementApi,
    uiPageObjectApi,
    uiTestCaseApi,
    uiTestStepApi,
    uiTestSuiteApi,
    uiExecutionApi,
    uiBrowserApi,
  }
}

export const uiAutomationApi = useUiAutomationApi()
export const {
  uiProjectApi,
  uiElementGroupApi,
  uiElementApi,
  uiPageObjectApi,
  uiTestCaseApi,
  uiTestStepApi,
  uiTestSuiteApi,
  uiExecutionApi,
  uiBrowserApi,
} = uiAutomationApi
