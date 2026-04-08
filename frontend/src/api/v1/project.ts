import request from '/@/utils/request';

/**
 * 项目管理API
 */

// 获取项目列表
export function getProjectList(params?: {
  page?: number;
  page_size?: number;
  name?: string;
  status?: string;
}) {
  return request({
    url: '/v1/projects/',
    method: 'GET',
    params,
  });
}

// 获取项目详情
export function getProjectDetail(id: number) {
  return request({
    url: `/v1/projects/${id}`,
    method: 'GET',
  });
}

// 创建项目
export function createProject(data: {
  name: string;
  description?: string;
  status?: string;
}) {
  return request({
    url: '/v1/projects/',
    method: 'POST',
    data,
  });
}

// 更新项目
export function updateProject(id: number, data: {
  name?: string;
  description?: string;
  status?: string;
}) {
  return request({
    url: `/v1/projects/${id}`,
    method: 'PUT',
    data,
  });
}

// 删除项目
export function deleteProject(id: number) {
  return request({
    url: `/v1/projects/${id}`,
    method: 'DELETE',
  });
}
