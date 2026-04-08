/**
 * API测试模块接口
 */
import request from '/@/utils/request'

export function useApiTestingApi() {
  const apiProjectApi = {
    create: (data: any) => request.post('/v1/api_testing/projects', data),
    list: (params: any) => request.get('/v1/api_testing/projects', { params }),
    get: (id: number) => request.get(`/v1/api_testing/projects/${id}`),
    update: (id: number, data: any) => request.put(`/v1/api_testing/projects/${id}`, data),
    delete: (id: number) => request.delete(`/v1/api_testing/projects/${id}`),
    export: (id: number) => request.get(`/v1/api_testing/projects/${id}/export`),
    import: (projectId: number, data: any) => request.post(`/v1/api_testing/projects/import?project_id=${projectId}`, { data })
  }

  const apiCollectionApi = {
    create: (data: any) => request.post('/v1/api_testing/collections', data),
    tree: (apiProjectId: number) => request.get('/v1/api_testing/collections/tree', { params: { api_project_id: apiProjectId } }),
    get: (id: number) => request.get(`/v1/api_testing/collections/${id}`),
    update: (id: number, data: any) => request.put(`/v1/api_testing/collections/${id}`, data),
    delete: (id: number) => request.delete(`/v1/api_testing/collections/${id}`),
    export: (id: number) => request.get(`/v1/api_testing/collections/${id}/export`),
    import: (apiProjectId: number, data: any, parentId?: number) =>
      request.post(`/v1/api_testing/collections/import?api_project_id=${apiProjectId}${parentId ? `&parent_id=${parentId}` : ''}`, { data })
  }

  const apiRequestApi = {
    create: (data: any) => request.post('/v1/api_testing/requests', data),
    list: (params: any) => request.get('/v1/api_testing/requests', { params }),
    get: (id: number) => request.get(`/v1/api_testing/requests/${id}`),
    update: (id: number, data: any) => request.put(`/v1/api_testing/requests/${id}`, data),
    delete: (id: number) => request.delete(`/v1/api_testing/requests/${id}`),
    execute: (id: number, data: any) => request.post(`/v1/api_testing/requests/${id}/execute`, data),
    history: (id: number, params: any) => request.get(`/v1/api_testing/requests/${id}/history`, { params })
  }

  const apiEnvironmentApi = {
    create: (data: any) => request.post('/v1/api_testing/environments', data),
    list: (projectId: number) => request.get('/v1/api_testing/environments', { params: { project_id: projectId } }),
    get: (id: number) => request.get(`/v1/api_testing/environments/${id}`),
    update: (id: number, data: any) => request.put(`/v1/api_testing/environments/${id}`, data),
    delete: (id: number) => request.delete(`/v1/api_testing/environments/${id}`),
    activate: (id: number) => request.post(`/v1/api_testing/environments/${id}/activate`),
    export: (projectId: number) => request.get('/v1/api_testing/environments/export', { params: { project_id: projectId } }),
    import: (projectId: number, data: any) => request.post(`/v1/api_testing/environments/import?project_id=${projectId}`, { data })
  }

  const apiTestSuiteApi = {
    create: (data: any) => request.post('/v1/api_testing/test_suites', data),
    list: (params: any) => request.get('/v1/api_testing/test_suites', { params }),
    get: (id: number) => request.get(`/v1/api_testing/test_suites/${id}`),
    update: (id: number, data: any) => request.put(`/v1/api_testing/test_suites/${id}`, data),
    delete: (id: number) => request.delete(`/v1/api_testing/test_suites/${id}`),
    execute: (id: number) => request.post(`/v1/api_testing/test_suites/${id}/execute`),
    executions: (id: number, params: any) => request.get(`/v1/api_testing/test_suites/${id}/executions`, { params })
  }

  return {
    apiProjectApi,
    apiCollectionApi,
    apiRequestApi,
    apiEnvironmentApi,
    apiTestSuiteApi,
  }
}

export const apiTestingApi = useApiTestingApi()
export const { apiProjectApi, apiCollectionApi, apiRequestApi, apiEnvironmentApi, apiTestSuiteApi } = apiTestingApi
