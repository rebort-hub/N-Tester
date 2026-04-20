<template>
  <div class="dashboard-container app-container">

    <!-- 公告滚动条 -->
    <div class="notice-bar">
      <el-icon class="notice-icon"><Bell /></el-icon>
      <div class="notice-track-wrap">
        <div class="notice-track">
          <span class="notice-text">N-Tester AI全栈测试平台，提供接口自动化，双引擎UI自动化，APP自动化，支持MCP，知识库，自定义管理Skill，一站式解决方案！持续优化中</span>
          <span class="notice-text">N-Tester AI全栈测试平台，提供接口自动化，双引擎UI自动化，APP自动化，支持MCP，知识库，自定义管理Skill，一站式解决方案！持续优化中</span>
        </div>
      </div>
    </div>

    <!-- 欢迎 Hero 区域 -->
    <div class="hero-section">
      <div class="hero-bg"></div>
      <div class="hero-content">
        <div class="hero-left">
          <div class="hero-greeting">{{ greetingText }}，{{ userInfo.nickname || '管理员' }}</div>
          <div class="hero-sub">欢迎回到 N-Tester 全栈测试平台</div>
          <div class="hero-meta">
            <span class="hero-date"><el-icon class="meta-icon"><Calendar /></el-icon>{{ currentDate }}</span>
            <span class="hero-time"><el-icon class="meta-icon"><Clock /></el-icon>{{ currentTime }}</span>
          </div>
        </div>
        <div class="hero-right">
          <div class="hero-avatar-wrap">
            <el-avatar :size="72" :src="userInfo.avatar || undefined" class="hero-avatar">
              <el-icon :size="36"><User /></el-icon>
            </el-avatar>
            <div class="hero-avatar-ring"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 核心统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="(card, i) in statCards" :key="i">
        <div class="stat-card" :style="{'--card-color': card.color}" @click="goToPage(card.path)">
          <div class="stat-card-bg"></div>
          <el-icon class="stat-card-icon" :size="30"><component :is="card.icon" /></el-icon>
          <div class="stat-card-body">
            <div class="stat-card-val">{{ card.value }}</div>
            <div class="stat-card-label">{{ card.label }}</div>
            <div class="stat-card-sub">{{ card.sub }}</div>
          </div>
          <el-icon class="stat-card-arrow"><ArrowRight /></el-icon>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="16">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title"><el-icon class="title-icon"><TrendCharts /></el-icon>测试执行趋势</span>
            <el-button text size="small" @click="refreshExecutionTrends"><el-icon><Refresh /></el-icon></el-button>
          </div>
          <div class="chart-box" ref="executionTrendChart" v-loading="executionTrendLoading"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title"><el-icon class="title-icon"><PieChart /></el-icon>评审进度</span>
            <el-button text size="small" @click="goToPage('/reviews/statistics')"><el-icon><View /></el-icon></el-button>
          </div>
          <div class="chart-box" ref="reviewStatsChart" v-loading="reviewStatsLoading"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="12">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title"><el-icon class="title-icon"><DataAnalysis /></el-icon>数据工厂统计</span>
            <el-button text size="small" @click="goToPage('/data-factory/tools')"><el-icon><View /></el-icon></el-button>
          </div>
          <div class="chart-box" ref="dataFactoryChart" v-loading="dataFactoryLoading"></div>
        </div>
      </el-col>
      <el-col :xs="24" :md="12">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title"><el-icon class="title-icon"><Connection /></el-icon>API接口统计</span>
            <el-button text size="small" @click="refreshApiInterfaceStats"><el-icon><Refresh /></el-icon></el-button>
          </div>
          <div class="chart-box" ref="apiInterfaceChart" v-loading="apiInterfaceLoading"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部信息区 -->
    <el-row :gutter="16" class="bottom-row">
      <!-- 通知中心 -->
      <el-col :xs="24" :md="12">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title"><el-icon class="title-icon"><Bell /></el-icon>通知中心</span>
            <el-badge :value="unreadNotifications" :hidden="!unreadNotifications">
              <el-button text size="small" @click="goToPage('/notifications/histories')"><el-icon><View /></el-icon></el-button>
            </el-badge>
          </div>
          <div class="list-body">
            <el-empty v-if="!recentNotifications.length" description="暂无通知" :image-size="50" />
            <div v-for="(n, i) in recentNotifications" :key="i" class="list-item">
              <div class="list-item-dot" :class="'dot-' + n.status"></div>
              <div class="list-item-content">
                <div class="list-item-title">{{ n.title }}</div>
                <div class="list-item-time">{{ formatTime(n.created_at) }}</div>
              </div>
              <el-tag :type="getNotificationTypeTag(n.status)" size="small" effect="plain">{{ getNotificationStatusText(n.status) }}</el-tag>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 项目活跃度 -->
      <el-col :xs="24" :md="12">
        <div class="panel">
          <div class="panel-header">
            <span class="panel-title"><el-icon class="title-icon"><Trophy /></el-icon>项目活跃度</span>
            <el-button text size="small" @click="refreshProjectActivity"><el-icon><Refresh /></el-icon></el-button>
          </div>
          <div class="list-body" v-loading="activityLoading">
            <el-empty v-if="!activeProjects.length" description="暂无活跃项目" :image-size="50" />
            <div v-for="(p, i) in activeProjects" :key="p.id" class="list-item">
              <div class="rank-badge" :class="i < 3 ? 'rank-top' : ''">{{ i + 1 }}</div>
              <div class="list-item-content">
                <div class="list-item-title">{{ p.name }}</div>
                <el-progress :percentage="p.activity_score" :show-text="false" :stroke-width="5" :color="getActivityColor(p.activity_score)" style="margin-top:4px" />
              </div>
              <span class="activity-score-text" :style="{color: getActivityColor(p.activity_score)}">{{ p.activity_score }}%</span>
            </div>
          </div>
        </div>
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
import * as echarts from 'echarts';
import { useDashboardApi } from '/@/api/v1/dashboard';
import { User, Refresh, View, Bell, Calendar, Clock, Folder, Document, MagicStick, UserFilled, TrendCharts, DataAnalysis, Connection, ArrowRight, Trophy, PieChart } from '@element-plus/icons-vue';
import { useApiAutomationApi } from '/@/api/v1/api_automation';
import { useWebManagementApi } from '/@/api/v1/web_management';

const dashboardApi = useDashboardApi();
const { api_service, get_api_script_result_list } = useApiAutomationApi();
const { get_web_result_list } = useWebManagementApi();
const router = useRouter();
const userStore = useUserStore();
const themeConfigStore = useThemeConfig();
const { userInfos: userInfo } = storeToRefs(userStore);
const { themeConfig } = storeToRefs(themeConfigStore);

const currentTime = ref('');
const currentDate = ref('');
const coreStats = ref({ projects: { total: 0, active: 0 }, test_cases: { total: 0, pass_rate: 0 }, ai_executions: { total: 0, success_rate: 0 }, users: { total: 0, online: 0 } });
const recentNotifications = ref<any[]>([]);
const unreadNotifications = ref(0);
const activeProjects = ref<any[]>([]);
const activityLoading = ref(false);
const executionTrendChart = ref();
const dataFactoryChart = ref();
const reviewStatsChart = ref();
const apiInterfaceChart = ref();
const executionTrendLoading = ref(false);
const dataFactoryLoading = ref(false);
const reviewStatsLoading = ref(false);
const apiInterfaceLoading = ref(false);

const greetingText = computed(() => {
  const h = new Date().getHours();
  if (h < 6) return '凌晨好'; if (h < 9) return '早上好'; if (h < 12) return '上午好';
  if (h < 14) return '中午好'; if (h < 17) return '下午好'; if (h < 19) return '傍晚好';
  if (h < 22) return '晚上好'; return '夜深了';
});

const statCards = computed(() => [
  { icon: Folder, label: '项目总数', value: coreStats.value.projects?.total || 0, sub: `活跃 ${coreStats.value.projects?.active || 0}`, color: '#6366f1', path: '/projects/list' },
  { icon: Document, label: '测试用例', value: coreStats.value.test_cases?.total || 0, sub: `通过率 ${coreStats.value.test_cases?.pass_rate || 0}%`, color: '#0ea5e9', path: '/testing/testcases' },
  { icon: MagicStick, label: 'AI执行', value: coreStats.value.ai_executions?.total || 0, sub: `成功率 ${coreStats.value.ai_executions?.success_rate || 0}%`, color: '#10b981', path: '/ai/intelligence/browser-use/cases' },
  { icon: UserFilled, label: '用户总数', value: coreStats.value.users?.total || 0, sub: `在线 ${coreStats.value.users?.online || 0}`, color: '#f59e0b', path: '/system/user' },
]);

let timer: any = null;
const updateTime = () => {
  const now = new Date();
  currentTime.value = now.toLocaleTimeString('zh-CN', { hour12: false });
  currentDate.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
};

const goToPage = (path: string) => router.push(path);
const formatTime = (t: string) => {
  if (!t) return '';
  const d = new Date(t), now = new Date(), diff = now.getTime() - d.getTime();
  if (diff < 60000) return '刚刚'; if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`; return d.toLocaleDateString('zh-CN');
};
const getNotificationTypeTag = (s: string) => ({ success: 'success', failed: 'danger', pending: 'warning' }[s] || 'info');
const getNotificationStatusText = (s: string) => ({ success: '成功', failed: '失败', pending: '待处理' }[s] || '未知');
const getActivityColor = (s: number) => s >= 80 ? '#10b981' : s >= 60 ? '#f59e0b' : s >= 40 ? '#ef4444' : '#909399';

const loadCoreStats = async () => {
  try { const r = await dashboardApi.getOverview(); if (r.code === 200 && r.data) coreStats.value = r.data; } catch {}
};
const loadNotifications = async () => {
  try { const r = await dashboardApi.getRecentNotifications({ limit: 5 }); if (r.code === 200) { recentNotifications.value = r.data.notifications; unreadNotifications.value = r.data.unread_count; } } catch {}
};
const loadProjectActivity = async () => {
  activityLoading.value = true;
  try { const r = await dashboardApi.getProjectActivity(); if (r.code === 200) activeProjects.value = r.data.active_projects; } catch {} finally { activityLoading.value = false; }
};

const initChart = (el: any, option: any) => {
  if (!el) return; const c = echarts.init(el); c.setOption(option); window.addEventListener('resize', () => c.resize());
};

const initExecutionTrendChart = async () => {
  executionTrendLoading.value = true;
  try {
    // 并行获取 API 执行结果和 Web 执行结果
    const [apiRes, webRes] = await Promise.allSettled([
      get_api_script_result_list({ page: 1, pageSize: 200 }),
      get_web_result_list({ page: 1, pageSize: 200, search: {} }),
    ]);

    const apiList: any[] = apiRes.status === 'fulfilled' ? (apiRes.value?.data?.content || []) : [];
    const webList: any[] = webRes.status === 'fulfilled' ? (webRes.value?.data?.content || []) : [];

    // 生成最近 7 天日期
    const days: string[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i);
      days.push(`${d.getMonth()+1}-${String(d.getDate()).padStart(2,'0')}`);
    }

    const countByDay = (list: any[], dateField = 'start_time') => {
      const map: Record<string, number> = {};
      days.forEach(d => { map[d] = 0; });
      list.forEach((item: any) => {
        const t = item[dateField] || item.creation_date || '';
        if (!t) return;
        const d = new Date(t);
        const key = `${d.getMonth()+1}-${String(d.getDate()).padStart(2,'0')}`;
        if (map[key] !== undefined) map[key]++;
      });
      return days.map(d => map[d]);
    };

    const apiData = countByDay(apiList, 'start_time');
    const webData = countByDay(webList, 'start_time');

    initChart(executionTrendChart.value, {
      tooltip: { trigger: 'axis' },
      legend: { data: ['API执行', 'Web执行'], bottom: 0 },
      grid: { top: 20, bottom: 40, left: 40, right: 20 },
      xAxis: { type: 'category', data: days, axisLine: { lineStyle: { color: '#d1d5db' } }, axisLabel: { color: '#6b7280', fontSize: 12 } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f3f4f6' } }, minInterval: 1, axisLabel: { color: '#6b7280' } },
      series: [
        { name: 'API执行', type: 'line', data: apiData, smooth: true, areaStyle: { opacity: .12 }, itemStyle: { color: '#6366f1' }, lineStyle: { width: 2 } },
        { name: 'Web执行', type: 'line', data: webData, smooth: true, areaStyle: { opacity: .12 }, itemStyle: { color: '#10b981' }, lineStyle: { width: 2 } },
      ],
    });
  } catch (e) { console.error(e); } finally { executionTrendLoading.value = false; }
};

const initDataFactoryChart = async () => {
  dataFactoryLoading.value = true;
  try {
    const r = await dashboardApi.getDataFactoryStats();
    const dist = r.data?.category_distribution || [];
    initChart(dataFactoryChart.value, {
      tooltip: { trigger: 'item' },
      series: [{ name: '工具使用', type: 'pie', radius: ['45%', '72%'], data: dist.length ? dist.map((i: any) => ({ name: i.category, value: i.percentage })) : [{ name: '暂无数据', value: 1, itemStyle: { color: '#e5e7eb' } }], itemStyle: { borderRadius: 6, borderWidth: 2, borderColor: '#fff' }, label: { show: dist.length === 0, position: 'center', formatter: '暂无数据', color: '#9ca3af' } }]
    });
  } catch {} finally { dataFactoryLoading.value = false; }
};

const initReviewStatsChart = async () => {
  reviewStatsLoading.value = true;
  try {
    const r = await dashboardApi.getReviewStats();
    const d = r.data?.status_distribution || {};
    initChart(reviewStatsChart.value, {
      tooltip: { trigger: 'item' },
      series: [{ name: '评审状态', type: 'pie', radius: '72%', data: [
        { value: d.pending || 0, name: '待开始', itemStyle: { color: '#f59e0b' } },
        { value: d.in_progress || 0, name: '进行中', itemStyle: { color: '#6366f1' } },
        { value: d.completed || 0, name: '已完成', itemStyle: { color: '#10b981' } },
        { value: d.cancelled || 0, name: '已取消', itemStyle: { color: '#ef4444' } },
      ], emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,.2)' } } }]
    });
  } catch {} finally { reviewStatsLoading.value = false; }
};

const initApiInterfaceChart = async () => {
  apiInterfaceLoading.value = true;
  try {
    // 获取所有服务列表
    const r: any = await api_service({ page: 1, pageSize: 200, search: {} });
    const raw = r?.data;
    const list: any[] = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);

    // 按文档类型分组统计
    const typeMap: Record<string, number> = { swagger: 0, apifox: 0, '未配置': 0 };
    // 按拉取状态统计
    const statusMap: Record<string, number> = { '未拉取': 0, '拉取成功': 0, '拉取失败': 0 };

    list.forEach((s: any) => {
      const t = s.source_type || '未配置';
      typeMap[t] = (typeMap[t] || 0) + 1;
      const st = s.last_pull_status;
      if (st === 1) statusMap['拉取成功']++;
      else if (st === 2) statusMap['拉取失败']++;
      else statusMap['未拉取']++;
    });

    // 拉取状态数据用于 tooltip 展示
    const statusLabels = ['未拉取', '拉取成功', '拉取失败'];
    const statusValues = [statusMap['未拉取'], statusMap['拉取成功'], statusMap['拉取失败']];
    const statusColors = ['#94a3b8', '#10b981', '#ef4444'];

    initChart(apiInterfaceChart.value, {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const p = params[0];
          const name = p.name;
          const val = p.value;
          const idx = Object.keys(typeMap).indexOf(name);
          return `${name}<br/>服务数：<b>${val}</b>`;
        },
      },
      grid: { top: 16, bottom: 60, left: 50, right: 20 },
      xAxis: { type: 'category', data: Object.keys(typeMap), axisLabel: { color: '#6b7280', fontSize: 12 } },
      yAxis: { type: 'value', name: '服务数', minInterval: 1, axisLabel: { color: '#6b7280' } },
      series: [
        {
          name: '文档类型分布',
          type: 'bar',
          data: Object.values(typeMap),
          itemStyle: { color: (p: any) => ['#6366f1','#0ea5e9','#94a3b8'][p.dataIndex] || '#94a3b8', borderRadius: [6,6,0,0] },
          barMaxWidth: 50,
          label: { show: true, position: 'top', fontSize: 12, color: '#374151' },
        },
      ],
    });

    // 在图表下方单独展示拉取状态（不用 graphic 避免遮挡）
    // 通过 legend 附加说明
    const statusEl = (apiInterfaceChart.value as HTMLElement)?.parentElement?.querySelector('.status-legend');
    if (!statusEl) {
      const div = document.createElement('div');
      div.className = 'status-legend';
      div.style.cssText = 'display:flex;gap:12px;justify-content:center;padding:4px 0 8px;font-size:11px;';
      statusLabels.forEach((l, i) => {
        const span = document.createElement('span');
        span.style.cssText = `color:${statusColors[i]};display:flex;align-items:center;gap:3px;`;
        span.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:${statusColors[i]};display:inline-block"></span>${l} ${statusValues[i]}`;
        div.appendChild(span);
      });
      (apiInterfaceChart.value as HTMLElement)?.parentElement?.appendChild(div);
    }
  } catch (e) { console.error(e); } finally { apiInterfaceLoading.value = false; }
};

const refreshExecutionTrends = () => initExecutionTrendChart();
const refreshProjectActivity = () => loadProjectActivity();
const refreshApiInterfaceStats = () => initApiInterfaceChart();

onMounted(async () => {
  if (themeConfig.value.isLockScreen) { themeConfig.value.isLockScreen = false; themeConfig.value.lockScreenTime = 0; }
  updateTime(); timer = setInterval(updateTime, 1000);
  await loadCoreStats(); await loadNotifications(); await loadProjectActivity();
  await nextTick();
  setTimeout(() => { initExecutionTrendChart(); initDataFactoryChart(); }, 100);
  setTimeout(() => { initReviewStatsChart(); initApiInterfaceChart(); }, 300);
});
onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped lang="scss">
.dashboard-container { padding: 0 0 24px; background: var(--el-bg-color-page); min-height: 100vh; }

/* 公告滚动条 */
.notice-bar { display: flex; align-items: center; background: #eef2ff; border-bottom: 1px solid #c7d2fe; color: #0bc5a4; padding: 0 16px; height: 36px; overflow: hidden; }
.notice-icon { font-size: 16px; margin-right: 10px; flex-shrink: 0; color: #0bc5a4; }
.notice-track-wrap { flex: 1; overflow: hidden; }
.notice-track { display: flex; width: max-content; animation: marquee 22s linear infinite; }
.notice-text { font-size: 13px; letter-spacing: .3px; color: #0bc5a4; padding-right: 80px; white-space: nowrap; }
@keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }

/* Hero 区域 */
.hero-section { position: relative; margin: 16px 16px 0; border-radius: 16px; overflow: hidden; padding: 28px 28px; background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 50%, #dbeafe 100%); border: 1px solid #c7d2fe; }
.hero-bg { position: absolute; inset: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); }
.hero-content { position: relative; display: flex; align-items: center; justify-content: space-between; }
.hero-greeting { font-size: 26px; font-weight: 700; color: #1e1b4b; margin-bottom: 6px; }
.hero-sub { font-size: 14px; color: #4338ca; margin-bottom: 14px; }
.hero-meta { display: flex; gap: 16px; }
.hero-date, .hero-time { font-size: 13px; color: #6366f1; display: flex; align-items: center; gap: 4px; }
.meta-icon { font-size: 13px; }
.hero-avatar-wrap { position: relative; }
.hero-avatar { border: 3px solid #a5b4fc; box-shadow: 0 0 0 6px rgba(99,102,241,.1); }
.hero-avatar-ring { position: absolute; inset: -8px; border-radius: 50%; border: 2px dashed #a5b4fc; animation: spin 12s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* 统计卡片 */
.stats-row { padding: 16px 16px 0; }
.stat-card { position: relative; border-radius: 14px; padding: 20px 18px; cursor: pointer; overflow: hidden; background: var(--el-bg-color); border: 1px solid var(--el-border-color-lighter); transition: all .25s; margin-bottom: 16px; display: flex; align-items: center; gap: 14px; }
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,.1); border-color: var(--card-color); }
.stat-card-bg { position: absolute; right: -20px; top: -20px; width: 80px; height: 80px; border-radius: 50%; background: var(--card-color); opacity: .08; }
.stat-card-icon { font-size: 30px; flex-shrink: 0; color: var(--card-color); }
.stat-card-body { flex: 1; min-width: 0; }
.stat-card-val { font-size: 28px; font-weight: 700; color: var(--card-color); line-height: 1; margin-bottom: 4px; }
.stat-card-label { font-size: 13px; color: var(--el-text-color-regular); font-weight: 500; }
.stat-card-sub { font-size: 11px; color: var(--el-text-color-placeholder); margin-top: 2px; }
.stat-card-arrow { font-size: 16px; color: var(--card-color); opacity: .4; flex-shrink: 0; }

/* 面板 */
.chart-row, .bottom-row { padding: 0 16px; margin-top: 16px !important; }
.panel { background: var(--el-bg-color); border: 1px solid var(--el-border-color-lighter); border-radius: 14px; overflow: hidden; height: 100%; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid var(--el-border-color-lighter); }
.panel-title { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); display: flex; align-items: center; gap: 6px; }
.title-icon { color: #6366f1; font-size: 15px; }
.meta-icon { font-size: 13px; vertical-align: middle; }
.chart-box { height: 240px; padding: 8px; }

/* 列表 */
.list-body { padding: 8px 0; min-height: 200px; }
.list-item { display: flex; align-items: center; gap: 10px; padding: 10px 18px; transition: background .15s; }
.list-item:hover { background: var(--el-fill-color-lighter); }
.list-item-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-success { background: #10b981; } .dot-failed { background: #ef4444; } .dot-pending { background: #f59e0b; }
.list-item-content { flex: 1; min-width: 0; }
.list-item-title { font-size: 13px; color: var(--el-text-color-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.list-item-time { font-size: 11px; color: var(--el-text-color-placeholder); margin-top: 2px; }
.rank-badge { width: 22px; height: 22px; border-radius: 50%; background: var(--el-fill-color); color: var(--el-text-color-regular); font-size: 11px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rank-badge.rank-top { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #fff; }
.activity-score-text { font-size: 12px; font-weight: 600; flex-shrink: 0; }
</style>
