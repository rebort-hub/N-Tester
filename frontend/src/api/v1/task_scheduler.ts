import request from '/@/utils/request';

// 定时任务
export interface SchedulerTask {
  id: number;
  name: string;
  type: number; // 1-APP自动化, 2-Web UI自动化, 3-接口自动化
  status: number; // 0-停用, 1-启用
  script?: Record<string, any>;
  time?: Record<string, any>;
  notice?: Record<string, any>;
  description?: string;
  scheduler_job_id?: string | null;
  last_run_at?: string | null;
  next_run_at?: string | null;
  next_time?: string | null;
  latest_run_time?: string | null;
  total_run_count: number;
  creation_date: string;
  latest_status?: string;
}

// 通知配置
export interface SchedulerNotice {
  id: number;
  name: string;
  type: number;
  value: string;
  status: number;
  script?: Record<string, any>;
  description?: string;
  creation_date: string;
}

// 任务执行历史
export interface TaskExecutionHistory {
  id: number;
  task_id: number;
  execution_id: string;
  status: string;
  start_time: string;
  end_time?: string | null;
  duration?: number | null;
  result?: Record<string, any>;
  error_message?: string | null;
  trigger_type?: string | null;
}

interface ListResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

interface CommonResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

export function useTaskSchedulerApi() {
  return {
  getTaskList: (params: {
    page?: number;
    size?: number;
    name?: string;
    type?: number;
    status?: number;
  }) => {
    return request<ListResponse>({
      url: '/v1/task_scheduler/task_list',
      method: 'post',
      data: {
        page: params.page ?? 1,
        size: params.size ?? 10,
        name: params.name ?? null,
        type: params.type ?? null,
        status: params.status ?? null,
      },
    });
  },

  createTask: (data: {
    name: string;
    type: number;
    script: Record<string, any>;
    time: Record<string, any>;
    notice?: Record<string, any>;
    description?: string;
  }) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/add_task',
      method: 'post',
      data,
    });
  },

  updateTask: (data: {
    task_id: number;
    name?: string;
    type?: number;
    status?: number;
    script?: Record<string, any>;
    time?: Record<string, any>;
    notice?: Record<string, any>;
    description?: string;
  }) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/edit_task',
      method: 'post',
      data,
    });
  },

  deleteTask: (task_id: number) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/del_task',
      method: 'post',
      data: { task_id },
    });
  },

  getTaskHistory: (params: {
    task_id?: number;
    status?: string;
    page?: number;
    size?: number;
  }) => {
    return request<ListResponse>({
      url: '/v1/task_scheduler/task_history',
      method: 'post',
      data: {
        task_id: params.task_id ?? null,
        status: params.status ?? null,
        page: params.page ?? 1,
        size: params.size ?? 10,
      },
    });
  },

  getNoticeList: (params: {
    page?: number;
    size?: number;
    name?: string;
    type?: number;
    status?: number;
  }) => {
    return request<ListResponse>({
      url: '/v1/task_scheduler/notice_list',
      method: 'post',
      data: {
        page: params.page ?? 1,
        size: params.size ?? 10,
        name: params.name ?? null,
        type: params.type ?? null,
        status: params.status ?? null,
      },
    });
  },

  createNotice: (data: {
    name: string;
    type: number;
    value: string;
    script?: Record<string, any>;
    description?: string;
  }) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/add_notice',
      method: 'post',
      data,
    });
  },

  updateNotice: (data: {
    notice_id: number;
    name?: string;
    type?: number;
    value?: string;
    status?: number;
    script?: Record<string, any>;
    description?: string;
  }) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/edit_notice',
      method: 'post',
      data,
    });
  },

  deleteNotice: (notice_id: number) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/del_notice',
      method: 'post',
      data: { notice_id },
    });
  },

  getSchedulerStatus: () => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/scheduler/status',
      method: 'get',
    });
  },

  getSchedulerJobs: () => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/scheduler/jobs',
      method: 'get',
    });
  },

  reloadScheduler: () => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/scheduler/reload',
      method: 'post',
    });
  },

  pauseJob: (job_id: string | number) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/job/pause',
      method: 'post',
      data: { job_id },
    });
  },

  resumeJob: (job_id: string | number) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/job/resume',
      method: 'post',
      data: { job_id },
    });
  },

  runJobNow: (job_id: string | number) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/job/run_now',
      method: 'post',
      data: { job_id },
    });
  },

  removeJob: (job_id: string | number) => {
    return request<CommonResponse>({
      url: '/v1/task_scheduler/job/remove',
      method: 'post',
      data: { job_id },
    });
  },
  };
}

// 兼容旧用法：逐步迁移页面 import 后可移除
export const taskSchedulerApi = useTaskSchedulerApi();

