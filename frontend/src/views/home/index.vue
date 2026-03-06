<template>
  <div class="dashboard-container app-container">
    <!-- 顶部固定欢迎区域 -->
    <el-card class="welcome-card" shadow="never">
      <div class="welcome-content">
        <div class="welcome-left">
          <h2 class="welcome-title">
            <el-avatar 
              :size="32" 
              :src="userInfo.avatar || undefined" 
              class="welcome-avatar"
            >
              <el-icon><User /></el-icon>
            </el-avatar>
            你好，{{ userInfo.nickname || '管理员' }}
          </h2>
          <p class="welcome-desc">{{ greetingText }}，欢迎回到N-Tester2.0平台！</p>
        </div>
        <div class="welcome-right">
          <div class="time-info">
            <div class="current-date">
              <el-icon><Calendar /></el-icon>
              {{ currentDate }}
            </div>
            <div class="server-time">
              <el-icon><Clock /></el-icon>
              {{ currentTime }} (服务器时间)
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 核心业务统计卡片 -->
    <el-row :gutter="16" class="core-stats-row">
      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card" @click="goToPage('/projects/list')">
          <div class="stat-content">
            <div class="stat-icon project-icon">
              <el-icon :size="32"><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ coreStats.projects?.total || 0 }}</div>
              <div class="stat-label">项目总数</div>
              <div class="stat-sub">活跃: {{ coreStats.projects?.active || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card" @click="goToPage('/testing/testcases')">
          <div class="stat-content">
            <div class="stat-icon testcase-icon">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ coreStats.test_cases?.total || 0 }}</div>
              <div class="stat-label">测试用例</div>
              <div class="stat-sub">通过率: {{ coreStats.test_cases?.pass_rate || 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card" @click="goToPage('/ai/intelligence/browser-use/cases')">
          <div class="stat-content">
            <div class="stat-icon ai-icon">
              <el-icon :size="32"><MagicStick /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ coreStats.ai_executions?.total || 0 }}</div>
              <div class="stat-label">AI执行</div>
              <div class="stat-sub">成功率: {{ coreStats.ai_executions?.success_rate || 0 }}%</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card shadow="hover" class="stat-card" @click="goToPage('/system/user')">
          <div class="stat-content">
            <div class="stat-icon user-icon">
              <el-icon :size="32"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ coreStats.users?.total || 0 }}</div>
              <div class="stat-label">用户总数</div>
              <div class="stat-sub">在线: {{ coreStats.users?.online || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细统计区域 -->
    <el-row :gutter="16" class="detail-stats-row">
      <!-- 测试执行统计 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><TrendCharts /></el-icon>
              <span>测试执行趋势</span>
              <el-button text size="small" @click="refreshExecutionTrends">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-container" ref="executionTrendChart" v-loading="executionTrendLoading"></div>
        </el-card>
      </el-col>

      <!-- 数据工厂使用统计 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>数据工厂统计</span>
              <el-button text size="small" @click="goToPage('/data-factory/tools')">
                <el-icon><View /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-container" ref="dataFactoryChart" v-loading="dataFactoryLoading"></div>
        </el-card>
      </el-col>

      <!-- 用例评审进度 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <el-icon><CircleCheck /></el-icon>
              <span>评审进度统计</span>
              <el-button text size="small" @click="goToPage('/reviews/statistics')">
                <el-icon><View /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-container" ref="reviewStatsChart" v-loading="reviewStatsLoading"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部信息区域 -->
    <el-row :gutter="16" class="bottom-row">
      <!-- 通知中心 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <el-icon><Bell /></el-icon>
              <span>通知中心</span>
              <el-badge :value="unreadNotifications" class="notification-badge">
                <el-button text size="small" @click="goToPage('/notifications/histories')">
                  <el-icon><View /></el-icon>
                </el-button>
              </el-badge>
            </div>
          </template>
          <div class="notification-list">
            <el-empty v-if="recentNotifications.length === 0" description="暂无通知" :image-size="60" />
            <div v-else>
              <div v-for="(notification, index) in recentNotifications" :key="index" class="notification-item">
                <div class="notification-content">
                  <div class="notification-title">{{ notification.title }}</div>
                  <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
                </div>
                <el-tag :type="getNotificationTypeTag(notification.status)" size="small">
                  {{ getNotificationStatusText(notification.status) }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 项目活跃度 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <el-icon><Histogram /></el-icon>
              <span>项目活跃度</span>
              <el-button text size="small" @click="refreshProjectActivity">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="activity-list" v-loading="activityLoading">
            <el-empty v-if="activeProjects.length === 0" description="暂无活跃项目" :image-size="60" />
            <div v-else>
              <div v-for="(project, index) in activeProjects" :key="project.id" class="activity-item">
                <div class="activity-rank">{{ index + 1 }}</div>
                <div class="activity-content">
                  <div class="activity-name">{{ project.name }}</div>
                  <div class="activity-time">{{ formatTime(project.last_activity) }}</div>
                </div>
                <div class="activity-score">
                  <el-progress 
                    :percentage="project.activity_score" 
                    :show-text="false" 
                    :stroke-width="6"
                    :color="getActivityColor(project.activity_score)"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- API接口统计 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="8" :xl="8">
        <el-card shadow="never" class="info-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataLine /></el-icon>
              <span>API接口统计</span>
              <el-button text size="small" @click="refreshApiInterfaceStats">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="chart-container" ref="apiInterfaceChart" v-loading="apiInterfaceLoading"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts" name="home">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { useUserStore } from '/@/stores/user';
import { useThemeConfig } from '/@/stores/themeConfig';
import { ElMessage } from 'element-plus';
import * as echarts from 'echarts';
import { dashboardApi, type CoreStats, type ExecutionTrends, type DataFactoryStats, type ReviewStats, type ProjectActivity, type NotificationData, type ApiInterfaceStatsData } from '/@/api/v1/dashboard';
import { 
  User, 
  UserFilled,
  Calendar,
  Clock, 
  Folder,
  Document,
  MagicStick,
  TrendCharts,
  DataAnalysis,
  CircleCheck,
  Bell,
  Histogram,
  Operation,
  Plus,
  Tools,
  View,
  Refresh,
  DataLine
} from '@element-plus/icons-vue';

const router = useRouter();
const userStore = useUserStore();
const themeConfigStore = useThemeConfig();
const { userInfos: userInfo } = storeToRefs(userStore);
const { themeConfig } = storeToRefs(themeConfigStore);

// 核心统计数据
const coreStats = ref({
  projects: {
    total: 0,
    active: 0,
    monthly_new: 0
  },
  test_cases: {
    total: 0,
    weekly_new: 0,
    pass_rate: 0
  },
  ai_executions: {
    total: 0,
    monthly_generated: 0,
    success_rate: 0
  },
  users: {
    total: 0,
    online: 0,
    monthly_active: 0
  }
});

// 时间相关
const currentTime = ref('');
const currentDate = ref('');

// 图表相关
const executionTrendChart = ref();
const dataFactoryChart = ref();
const reviewStatsChart = ref();
const apiInterfaceChart = ref();
const executionTrendLoading = ref(false);
const dataFactoryLoading = ref(false);
const reviewStatsLoading = ref(false);
const apiInterfaceLoading = ref(false);

// 通知相关
const recentNotifications = ref([]);
const unreadNotifications = ref(0);

// 项目活跃度
const activeProjects = ref([]);
const activityLoading = ref(false);

// 问候语
const greetingText = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return '凌晨好';
  if (hour < 9) return '早上好';
  if (hour < 12) return '上午好';
  if (hour < 14) return '中午好';
  if (hour < 17) return '下午好';
  if (hour < 19) return '傍晚好';
  if (hour < 22) return '晚上好';
  return '夜深了';
});

// 更新时间
const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
  
  currentDate.value = now.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  });
};

// 定时器
let timer: any = null;

// 跳转页面
const goToPage = (path: string) => {
  router.push(path);
};

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return '';
  const date = new Date(timeStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  return date.toLocaleDateString('zh-CN');
};

// 获取通知状态标签类型
const getNotificationTypeTag = (status: string) => {
  const typeMap: Record<string, string> = {
    success: 'success',
    failed: 'danger',
    pending: 'warning'
  };
  return typeMap[status] || 'info';
};

// 获取通知状态文本
const getNotificationStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    success: '成功',
    failed: '失败',
    pending: '待处理'
  };
  return textMap[status] || '未知';
};

// 获取活跃度颜色
const getActivityColor = (score: number) => {
  if (score >= 80) return '#67c23a';
  if (score >= 60) return '#e6a23c';
  if (score >= 40) return '#f56c6c';
  return '#909399';
};

// 加载核心统计数据
const loadCoreStats = async () => {
  try {
    const response = await dashboardApi.getOverview();
    if (response.code === 200 && response.data) {
      coreStats.value = response.data;
    } else {
      console.warn('获取统计数据失败，使用默认数据:', response.message);
      // 使用默认数据
      coreStats.value = {
        projects: { total: 0, active: 0, monthly_new: 0 },
        test_cases: { total: 0, weekly_new: 0, pass_rate: 0 },
        ai_executions: { total: 0, monthly_generated: 0, success_rate: 0 },
        users: { total: 0, online: 0, monthly_active: 0 }
      };
    }
  } catch (error) {
    console.error('加载核心统计数据失败:', error);
    // 使用默认数据，不显示错误提示
    coreStats.value = {
      projects: { total: 0, active: 0, monthly_new: 0 },
      test_cases: { total: 0, weekly_new: 0, pass_rate: 0 },
      ai_executions: { total: 0, monthly_generated: 0, success_rate: 0 },
      users: { total: 0, online: 0, monthly_active: 0 }
    };
  }
};

// 初始化测试执行趋势图表
const initExecutionTrendChart = async () => {
  if (!executionTrendChart.value) return;
  
  executionTrendLoading.value = true;
  try {
    const response = await dashboardApi.getExecutionTrends({ days: 7 });
    if (response.code === 200 && response.data) {
      const { api_tests, ui_tests } = response.data;
      
      if (api_tests && ui_tests) {
        const dates = api_tests.map(item => item.date);
        const apiData = api_tests.map(item => item.count);
        const uiData = ui_tests.map(item => item.count);
        
        const chart = echarts.init(executionTrendChart.value);
        const option = {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'cross'
            }
          },
          legend: {
            data: ['API测试', 'UI测试']
          },
          xAxis: {
            type: 'category',
            data: dates
          },
          yAxis: {
            type: 'value'
          },
          series: [
            {
              name: 'API测试',
              type: 'line',
              data: apiData,
              smooth: true,
              itemStyle: {
                color: '#409EFF'
              }
            },
            {
              name: 'UI测试',
              type: 'line',
              data: uiData,
              smooth: true,
              itemStyle: {
                color: '#67C23A'
              }
            }
          ]
        };
        chart.setOption(option);
        
        // 响应式
        window.addEventListener('resize', () => chart.resize());
      } else {
        showDefaultExecutionChart();
      }
    } else {
      console.warn('获取执行趋势失败，显示默认图表:', response.message);
      showDefaultExecutionChart();
    }
  } catch (error) {
    console.error('初始化执行趋势图表失败:', error);
    showDefaultExecutionChart();
  } finally {
    executionTrendLoading.value = false;
  }
};

// 显示默认执行趋势图表
const showDefaultExecutionChart = () => {
  if (!executionTrendChart.value) return;
  
  const dates = ['03-01', '03-02', '03-03', '03-04', '03-05', '03-06', '03-07'];
  const apiData = [0, 0, 0, 0, 0, 0, 0];
  const uiData = [0, 0, 0, 0, 0, 0, 0];
  
  const chart = echarts.init(executionTrendChart.value);
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['API测试', 'UI测试']
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: 'API测试',
        type: 'line',
        data: apiData,
        smooth: true,
        itemStyle: {
          color: '#409EFF'
        }
      },
      {
        name: 'UI测试',
        type: 'line',
        data: uiData,
        smooth: true,
        itemStyle: {
          color: '#67C23A'
        }
      }
    ]
  };
  chart.setOption(option);
  
  // 响应式
  window.addEventListener('resize', () => chart.resize());
};

// 初始化数据工厂图表
const initDataFactoryChart = async () => {
  if (!dataFactoryChart.value) return;
  
  dataFactoryLoading.value = true;
  try {
    const response = await dashboardApi.getDataFactoryStats();
    if (response.code === 200 && response.data) {
      const { category_distribution } = response.data;
      
      if (category_distribution && category_distribution.length > 0) {
        const data = category_distribution.map(item => ({
          name: item.category,
          value: item.percentage
        }));
        
        const chart = echarts.init(dataFactoryChart.value);
        const option = {
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c}% ({d}%)'
          },
          series: [
            {
              name: '工具使用',
              type: 'pie',
              radius: ['40%', '70%'],
              avoidLabelOverlap: false,
              itemStyle: {
                borderRadius: 10,
                borderColor: '#fff',
                borderWidth: 2
              },
              label: {
                show: false,
                position: 'center'
              },
              emphasis: {
                label: {
                  show: true,
                  fontSize: '16',
                  fontWeight: 'bold'
                }
              },
              labelLine: {
                show: false
              },
              data: data
            }
          ]
        };
        chart.setOption(option);
        
        // 响应式
        window.addEventListener('resize', () => chart.resize());
      } else {
        showDefaultDataFactoryChart();
      }
    } else {
      console.warn('获取数据工厂统计失败，显示默认图表:', response.message);
      showDefaultDataFactoryChart();
    }
  } catch (error) {
    console.error('初始化数据工厂图表失败:', error);
    showDefaultDataFactoryChart();
  } finally {
    dataFactoryLoading.value = false;
  }
};

// 显示默认数据工厂图表
const showDefaultDataFactoryChart = () => {
  if (!dataFactoryChart.value) return;
  
  const data = [
    { name: '暂无数据', value: 100 }
  ];
  
  const chart = echarts.init(dataFactoryChart.value);
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c}%'
    },
    series: [
      {
        name: '工具使用',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
          color: '#E4E7ED'
        },
        label: {
          show: true,
          position: 'center',
          formatter: '暂无数据',
          fontSize: 14,
          color: '#909399'
        },
        labelLine: {
          show: false
        },
        data: data
      }
    ]
  };
  chart.setOption(option);
  
  // 响应式
  window.addEventListener('resize', () => chart.resize());
};

// 初始化评审统计图表
const initReviewStatsChart = async () => {
  if (!reviewStatsChart.value) return;
  
  reviewStatsLoading.value = true;
  try {
    const response = await dashboardApi.getReviewStats();
    if (response.code === 200 && response.data) {
      const { status_distribution } = response.data;
      
      if (status_distribution) {
        const data = [
          { value: status_distribution.pending, name: '待开始', itemStyle: { color: '#E6A23C' } },
          { value: status_distribution.in_progress, name: '进行中', itemStyle: { color: '#409EFF' } },
          { value: status_distribution.completed, name: '已完成', itemStyle: { color: '#67C23A' } },
          { value: status_distribution.cancelled, name: '已取消', itemStyle: { color: '#F56C6C' } }
        ];
        
        const chart = echarts.init(reviewStatsChart.value);
        const option = {
          tooltip: {
            trigger: 'item',
            formatter: '{a} <br/>{b}: {c} ({d}%)'
          },
          series: [
            {
              name: '评审状态',
              type: 'pie',
              radius: '70%',
              data: data,
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        };
        chart.setOption(option);
        
        // 响应式
        window.addEventListener('resize', () => chart.resize());
      } else {
        console.warn('评审统计数据格式错误');
      }
    } else {
      console.warn('获取评审统计失败:', response.message);
    }
  } catch (error) {
    console.error('初始化评审统计图表失败:', error);
  } finally {
    reviewStatsLoading.value = false;
  }
};

// 加载通知数据
const loadNotifications = async () => {
  try {
    const response = await dashboardApi.getRecentNotifications({ limit: 5 });
    if (response.code === 200) {
      recentNotifications.value = response.data.notifications;
      unreadNotifications.value = response.data.unread_count;
    } else {
      console.warn('获取通知数据失败，使用默认数据:', response.message);
      recentNotifications.value = [];
      unreadNotifications.value = 0;
    }
  } catch (error) {
    console.error('加载通知数据失败:', error);
    recentNotifications.value = [];
    unreadNotifications.value = 0;
  }
};

// 加载项目活跃度
const loadProjectActivity = async () => {
  activityLoading.value = true;
  try {
    const response = await dashboardApi.getProjectActivity();
    if (response.code === 200) {
      activeProjects.value = response.data.active_projects;
    } else {
      console.warn('获取项目活跃度失败，使用默认数据:', response.message);
      activeProjects.value = [];
    }
  } catch (error) {
    console.error('加载项目活跃度失败:', error);
    activeProjects.value = [];
  } finally {
    activityLoading.value = false;
  }
};

// 重置所有loading状态
const resetAllLoadingStates = () => {
  executionTrendLoading.value = false;
  dataFactoryLoading.value = false;
  reviewStatsLoading.value = false;
  apiInterfaceLoading.value = false;
  activityLoading.value = false;
};

// 刷新方法
const refreshExecutionTrends = () => {
  initExecutionTrendChart();
};

const refreshProjectActivity = () => {
  loadProjectActivity();
};

const refreshApiInterfaceStats = () => {
  initApiInterfaceChart();
};

// 初始化API接口统计图表
const initApiInterfaceChart = async () => {
  if (!apiInterfaceChart.value) return;
  
  // 等待DOM元素完全渲染
  await nextTick();
  
  // 强制初始化，不再检查高度
  apiInterfaceLoading.value = true;
  try {
    const response = await dashboardApi.getApiInterfaceStats();
    
    if (response.code === 200 && response.data) {
      const { interface_stats } = response.data;
      
      if (interface_stats && interface_stats.length > 0) {
        const projectNames = interface_stats.map(item => item.project_name);
        const totalInterfaces = interface_stats.map(item => item.total_interfaces);
        const successCounts = interface_stats.map(item => item.success_count);
        const failedCounts = interface_stats.map(item => item.failed_count);
        
        const chart = echarts.init(apiInterfaceChart.value);
        const option = {
          tooltip: {
            trigger: 'axis',
            axisPointer: {
              type: 'shadow'
            }
          },
          legend: {
            data: ['总接口数', '成功次数', '失败次数']
          },
          xAxis: {
            type: 'category',
            data: projectNames,
            axisLabel: {
              rotate: 30,
              interval: 0,
              fontSize: 12
            }
          },
          yAxis: {
            type: 'value',
            name: '数量'
          },
          series: [
            {
              name: '总接口数',
              type: 'bar',
              data: totalInterfaces,
              itemStyle: {
                color: '#409EFF'
              },
              barWidth: '20%'
            },
            {
              name: '成功次数',
              type: 'bar',
              data: successCounts,
              itemStyle: {
                color: '#67C23A'
              },
              barWidth: '20%'
            },
            {
              name: '失败次数',
              type: 'bar',
              data: failedCounts,
              itemStyle: {
                color: '#F56C6C'
              },
              barWidth: '20%'
            }
          ]
        };
        
        chart.setOption(option);
        
        // 响应式
        window.addEventListener('resize', () => chart.resize());
      } else {
        showDefaultApiInterfaceChart();
      }
    } else {
      console.warn('获取API接口统计失败，显示默认图表:', response.message);
      showDefaultApiInterfaceChart();
    }
  } catch (error) {
    console.error('初始化API接口统计图表失败:', error);
    showDefaultApiInterfaceChart();
  } finally {
    apiInterfaceLoading.value = false;
  }
};

// 显示默认API接口统计图表
const showDefaultApiInterfaceChart = async () => {
  if (!apiInterfaceChart.value) return;
  
  // 等待DOM元素完全渲染
  await nextTick();
  
  const projectNames = ['项目A', '项目B', '项目C'];
  const totalInterfaces = [10, 8, 6];
  const successCounts = [8, 6, 4];
  const failedCounts = [2, 2, 2];
  
  try {
    const chart = echarts.init(apiInterfaceChart.value);
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      legend: {
        data: ['总接口数', '成功次数', '失败次数']
      },
      xAxis: {
        type: 'category',
        data: projectNames
      },
      yAxis: {
        type: 'value',
        name: '数量'
      },
      series: [
        {
          name: '总接口数',
          type: 'bar',
          data: totalInterfaces,
          itemStyle: {
            color: '#409EFF'
          }
        },
        {
          name: '成功次数',
          type: 'bar',
          data: successCounts,
          itemStyle: {
            color: '#67C23A'
          }
        },
        {
          name: '失败次数',
          type: 'bar',
          data: failedCounts,
          itemStyle: {
            color: '#F56C6C'
          }
        }
      ]
    };
    
    chart.setOption(option);
    
    // 响应式
    window.addEventListener('resize', () => chart.resize());
  } catch (error) {
    console.error('初始化默认图表失败:', error);
  }
};

onMounted(async () => {
  // 确保锁屏被禁用
  if (themeConfig.value.isLockScreen) {
    themeConfig.value.isLockScreen = false;
    themeConfig.value.lockScreenTime = 0;
  }
  
  updateTime();
  // 每秒更新时间
  timer = setInterval(updateTime, 1000);
  
  try {
    // 加载数据
    await loadCoreStats();
    await loadNotifications();
    await loadProjectActivity();
    
    // 等待DOM更新后初始化图表，分批初始化避免冲突
    await nextTick();
    
    // 第一批图表
    setTimeout(() => {
      initExecutionTrendChart();
      initDataFactoryChart();
    }, 100);
    
    // 第二批图表
    setTimeout(() => {
      initReviewStatsChart();
    }, 300);
    
    // API接口统计图表单独初始化，给更多时间
    setTimeout(() => {
      initApiInterfaceChart();
    }, 500);
    
    // 确保所有loading状态都被重置
    setTimeout(() => {
      resetAllLoadingStates();
    }, 2000);
    
  } catch (error) {
    console.error('首页初始化失败:', error);
    // 确保loading状态被重置
    resetAllLoadingStates();
  }
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<style scoped lang="scss">
.dashboard-container {
  min-height: 100vh;

  // 顶部欢迎卡片
  .welcome-card {
    margin-bottom: 16px;
    border-radius: 8px;
    background: transparent;
    border: 1px solid var(--el-border-color);
    color: var(--el-text-color-primary);

    :deep(.el-card__body) {
      padding: 16px;
    }

    .welcome-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .welcome-left {
        .welcome-title {
          margin: 0 0 6px 0;
          font-size: 24px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 10px;

          .welcome-avatar {
            border: 2px solid #409EFF;
          }
        }

        .welcome-desc {
          margin: 0;
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }

      .welcome-right {
        .time-info {
          text-align: right;

          .current-date {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 6px;
            color: #409EFF;
          }

          .server-time {
            font-size: 13px;
            color: var(--el-text-color-secondary);
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 6px;
          }
        }
      }
    }
  }

  // 核心统计卡片行
  .core-stats-row {
    margin-bottom: 16px;

    .stat-card {
      margin-bottom: 12px;
      border-radius: 8px;
      transition: all 0.3s ease;
      cursor: pointer;

      &:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
      }

      :deep(.el-card__body) {
        padding: 16px;
      }

      .stat-content {
        display: flex;
        align-items: center;

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-right: 14px;
          color: white;

          &.project-icon {
            background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
          }

          &.testcase-icon {
            background: linear-gradient(135deg, #E6A23C 0%, #F56C6C 100%);
          }

          &.ai-icon {
            background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
          }

          &.user-icon {
            background: linear-gradient(135deg, #67C23A 0%, #409EFF 100%);
          }
        }

        .stat-info {
          flex: 1;

          .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--el-text-color-primary);
            line-height: 1;
            margin-bottom: 4px;
          }

          .stat-label {
            font-size: 13px;
            color: var(--el-text-color-regular);
            margin-bottom: 2px;
          }

          .stat-sub {
            font-size: 11px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }

  // 详细统计区域
  .detail-stats-row {
    margin-bottom: 20px;

    .chart-card {
      margin-bottom: 16px;
      border-radius: 12px;

      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        font-size: 16px;

        > div:first-child {
          display: flex;
          align-items: center;
          gap: 8px;
        }
      }

      .chart-container {
        height: 280px;
        width: 100%;
      }
    }
  }

  // 底部信息区域
  .bottom-row {
    .info-card {
      margin-bottom: 16px;
      border-radius: 12px;

      .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-weight: 600;
        font-size: 16px;

        > div:first-child {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .notification-badge {
          :deep(.el-badge__content) {
            top: 8px;
            right: 8px;
          }
        }
      }

      // 为info-card中的图表容器也设置高度
      .chart-container {
        height: 280px;
        width: 100%;
      }

      // 通知列表
      .notification-list {
        max-height: 300px;
        overflow-y: auto;

        .notification-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);

          &:last-child {
            border-bottom: none;
          }

          .notification-content {
            flex: 1;

            .notification-title {
              font-size: 14px;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }

            .notification-time {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }
        }
      }

      // 活跃度列表
      .activity-list {
        max-height: 300px;
        overflow-y: auto;

        .activity-item {
          display: flex;
          align-items: center;
          padding: 12px 0;
          border-bottom: 1px solid var(--el-border-color-lighter);

          &:last-child {
            border-bottom: none;
          }

          .activity-rank {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #409eff;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            margin-right: 12px;
          }

          .activity-content {
            flex: 1;
            margin-right: 12px;

            .activity-name {
              font-size: 14px;
              color: var(--el-text-color-primary);
              margin-bottom: 4px;
            }

            .activity-time {
              font-size: 12px;
              color: var(--el-text-color-secondary);
            }
          }

          .activity-score {
            width: 80px;
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .dashboard-container {
    padding: 12px;

    .welcome-card {
      .welcome-content {
        flex-direction: column;
        align-items: flex-start;
        gap: 16px;

        .welcome-right {
          .time-info {
            text-align: left;
          }
        }
      }
    }

    .core-stats-row {
      .stat-card {
        .stat-content {
          .stat-icon {
            width: 48px;
            height: 48px;
            margin-right: 16px;

            .el-icon {
              font-size: 24px !important;
            }
          }

          .stat-info {
            .stat-value {
              font-size: 24px;
            }

            .stat-label {
              font-size: 14px;
            }
          }
        }
      }
    }

    .detail-stats-row,
    .bottom-row {
      .chart-container {
        height: 240px;
      }
    }
  }
}
</style>
