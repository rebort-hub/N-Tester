/**
 * 首页看板API接口
 */
import request from '/@/utils/request'

// 核心统计数据接口
export interface CoreStats {
  projects: {
    total: number
    active: number
    monthly_new: number
  }
  test_cases: {
    total: number
    weekly_new: number
    pass_rate: number
  }
  ai_executions: {
    total: number
    monthly_generated: number
    success_rate: number
  }
  users: {
    total: number
    online: number
    monthly_active: number
  }
}

// 执行趋势数据接口
export interface ExecutionTrend {
  date: string
  count: number
  success_rate: number
}

export interface ExecutionTrends {
  api_tests: ExecutionTrend[]
  ui_tests: ExecutionTrend[]
}

// 数据工厂统计接口
export interface ToolUsage {
  name: string
  count: number
}

export interface CategoryDistribution {
  category: string
  count: number
  percentage: number
}

export interface DataFactoryStats {
  top_tools: ToolUsage[]
  category_distribution: CategoryDistribution[]
}

// 评审统计接口
export interface ReviewStats {
  status_distribution: {
    pending: number
    in_progress: number
    completed: number
    cancelled: number
  }
  completion_trend: Array<{
    date: string
    completion_rate: number
  }>
}

// 项目活跃度接口
export interface ActiveProject {
  id: number
  name: string
  last_activity: string
  activity_score: number
}

export interface ProjectActivity {
  active_projects: ActiveProject[]
  module_usage: {
    test_cases: number
    api_testing: number
    ui_automation: number
    ai_intelligence: number
    data_factory: number
    reviews: number
  }
}

// 通知接口
export interface RecentNotification {
  title: string
  status: string
  created_at: string
}

export interface NotificationData {
  notifications: RecentNotification[]
  unread_count: number
}

// API接口统计接口
export interface ApiInterfaceStats {
  project_name: string
  total_interfaces: number
  success_count: number
  failed_count: number
  success_rate: number
}

export interface ApiInterfaceStatsData {
  interface_stats: ApiInterfaceStats[]
  total_stats: {
    total_projects: number
    total_interfaces: number
    total_success: number
    total_failed: number
    overall_success_rate: number
  }
}

// 首页看板API
export const dashboardApi = {
  // 获取核心统计数据
  getOverview: () => {
    return request({
      url: '/v1/dashboard/overview',
      method: 'get'
    })
  },

  // 获取测试执行趋势
  getExecutionTrends: (params?: { days?: number }) => {
    return request({
      url: '/v1/dashboard/execution-trends',
      method: 'get',
      params
    })
  },

  // 获取数据工厂统计
  getDataFactoryStats: () => {
    return request({
      url: '/v1/dashboard/data-factory-stats',
      method: 'get'
    })
  },

  // 获取评审统计
  getReviewStats: () => {
    return request({
      url: '/v1/dashboard/review-stats',
      method: 'get'
    })
  },

  // 获取项目活跃度
  getProjectActivity: () => {
    return request({
      url: '/v1/dashboard/project-activity',
      method: 'get'
    })
  },

  // 获取最近通知
  getRecentNotifications: (params?: { limit?: number }) => {
    return request({
      url: '/v1/dashboard/recent-notifications',
      method: 'get',
      params
    })
  },

  // 获取API接口统计
  getApiInterfaceStats: () => {
    return request({
      url: '/v1/dashboard/api-interface-stats',
      method: 'get'
    })
  }
}