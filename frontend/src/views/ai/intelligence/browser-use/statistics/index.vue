<template>
  <div class="ai-browser-statistics-container">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="statistics-cards">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon :size="32"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overviewData.total_executions }}</div>
              <div class="stat-label">总执行次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon :size="32"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overviewData.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon :size="32"><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overviewData.avg_duration }}s</div>
              <div class="stat-label">平均时长</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon :size="32"><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ formatNumber(overviewData.total_tokens) }}</div>
              <div class="stat-label">Token使用量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和操作 -->
    <el-card shadow="hover" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>AI执行统计</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleRefresh">
              <el-icon><Refresh /></el-icon>
              刷新统计
            </el-button>
            <el-button type="success" @click="handleExport">
              <el-icon><Download /></el-icon>
              导出统计
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="统计类型">
          <el-select v-model="queryForm.stat_type" placeholder="请选择统计类型" style="width: 150px">
            <el-option label="每日统计" value="daily" />
            <el-option label="每周统计" value="weekly" />
            <el-option label="每月统计" value="monthly" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 300px"
          />
        </el-form-item>
        
        <el-form-item label="项目">
          <el-select 
            v-model="queryForm.project_id" 
            placeholder="请选择项目" 
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 图表区域 -->
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <div class="chart-container">
            <h4>执行趋势</h4>
            <div ref="executionTrendChart" style="width: 100%; height: 300px;"></div>
          </div>
        </el-col>
        
        <el-col :span="12">
          <div class="chart-container">
            <h4>成功率趋势</h4>
            <div ref="successRateChart" style="width: 100%; height: 300px;"></div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <div class="chart-container">
            <h4>执行状态分布</h4>
            <div ref="statusDistributionChart" style="width: 100%; height: 300px;"></div>
          </div>
        </el-col>
        
        <el-col :span="12">
          <div class="chart-container">
            <h4>平均执行时长趋势</h4>
            <div ref="durationTrendChart" style="width: 100%; height: 300px;"></div>
          </div>
        </el-col>
      </el-row>

      <!-- 统计表格 -->
      <el-divider />
      <h4>详细统计数据</h4>
      <el-table 
        :data="statisticsData" 
        border 
        stripe 
        v-loading="loading"
        style="width: 100%"
        :fit="true"
      >
        <el-table-column prop="stat_date" label="统计日期" min-width="120">
          <template #default="{ row }">
            {{ formatDate(row.stat_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="stat_type" label="统计类型" min-width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ getStatTypeLabel(row.stat_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_executions" label="总执行次数" min-width="100" align="center" />
        <el-table-column prop="success_executions" label="成功次数" min-width="90" align="center">
          <template #default="{ row }">
            <span style="color: #67c23a;">{{ row.success_executions }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="failed_executions" label="失败次数" min-width="90" align="center">
          <template #default="{ row }">
            <span style="color: #f56c6c;">{{ row.failed_executions }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="success_rate" label="成功率" min-width="120" align="center">
          <template #default="{ row }">
            <el-progress 
              :percentage="row.success_rate" 
              :stroke-width="12"
              :status="row.success_rate >= 80 ? 'success' : row.success_rate >= 60 ? 'warning' : 'exception'"
            />
          </template>
        </el-table-column>
        <el-table-column prop="avg_duration" label="平均时长(秒)" min-width="110" align="center">
          <template #default="{ row }">
            {{ row.avg_duration.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_cases" label="总用例数" min-width="90" align="center" />
        <el-table-column prop="active_cases" label="激活用例数" min-width="100" align="center" />
        <el-table-column prop="total_api_calls" label="API调用" min-width="90" align="center" />
        <el-table-column prop="total_tokens" label="Token使用" min-width="100" align="center">
          <template #default="{ row }">
            {{ formatNumber(row.total_tokens) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  DataAnalysis, 
  SuccessFilled, 
  Timer, 
  Coin, 
  Refresh, 
  Download 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getProjectList } from '/@/api/v1/project'
// 导入旧的AI智能浏览器API（用于查询执行记录）
import { aiExecutionRecordApi } from '/@/api/v1/ai_intelligence'

const loading = ref(false)
const statisticsData = ref([])
const projectList = ref([])
const dateRange = ref([])

// 概览数据
const overviewData = reactive({
  total_executions: 0,
  success_rate: 0,
  avg_duration: 0,
  total_tokens: 0
})

// 查询表单
const queryForm = reactive({
  stat_type: 'daily',
  start_date: null,
  end_date: null,
  project_id: null
})

// 图表引用
const executionTrendChart = ref()
const successRateChart = ref()
const statusDistributionChart = ref()
const durationTrendChart = ref()

// 图表实例
let executionTrendChartInstance: any = null
let successRateChartInstance: any = null
let statusDistributionChartInstance: any = null
let durationTrendChartInstance: any = null

// 获取统计数据
const getStatistics = async () => {
  loading.value = true
  try {
    console.log('开始获取统计数据...', queryForm)
    
    // 直接从执行记录计算统计数据
    const params: any = {}
    if (queryForm.project_id) {
      params.ui_project_id = queryForm.project_id
    }
    
    const res = await aiExecutionRecordApi.list(params)
    console.log('执行记录API响应:', res)
    
    const records = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.items || [])
    console.log('执行记录数量:', records.length)
    
    if (records.length === 0) {
      ElMessage.info('暂无执行记录')
      statisticsData.value = []
      overviewData.total_executions = 0
      overviewData.success_rate = 0
      overviewData.avg_duration = 0
      overviewData.total_tokens = 0
      return
    }
    
    // 过滤日期范围
    let filteredRecords = records
    if (queryForm.start_date && queryForm.end_date) {
      const startDate = new Date(queryForm.start_date)
      const endDate = new Date(queryForm.end_date)
      endDate.setHours(23, 59, 59, 999) // 包含结束日期的全天
      
      filteredRecords = records.filter((record: any) => {
        if (!record.start_time) return false
        const recordDate = new Date(record.start_time)
        return recordDate >= startDate && recordDate <= endDate
      })
      
      console.log(`日期过滤: ${records.length} -> ${filteredRecords.length}`)
    }
    
    // 按统计类型分组
    const statsByKey: any = {}
    let totalExecutions = 0
    let successExecutions = 0
    let failedExecutions = 0
    let totalDuration = 0
    let durationCount = 0
    let totalTokens = 0
    let totalApiCalls = 0
    
    filteredRecords.forEach((record: any) => {
      totalExecutions++
      
      // 统计成功/失败
      if (record.status === 'completed' || record.status === 'success') {
        successExecutions++
      } else if (record.status === 'failed') {
        failedExecutions++
      }
      
      // 统计时长
      if (record.duration) {
        totalDuration += record.duration
        durationCount++
      }
      
      // 统计Token
      if (record.total_tokens) {
        totalTokens += record.total_tokens
      }
      
      // 统计API调用
      if (record.api_calls) {
        totalApiCalls += record.api_calls
      }
      
      // 按统计类型分组
      const groupKey = getGroupKey(record.start_time, queryForm.stat_type)
      if (!statsByKey[groupKey]) {
        statsByKey[groupKey] = {
          stat_date: groupKey,
          stat_type: queryForm.stat_type,
          total_executions: 0,
          success_executions: 0,
          failed_executions: 0,
          stopped_executions: 0,
          success_rate: 0,
          avg_duration: 0,
          total_cases: 0,
          active_cases: 0,
          total_api_calls: 0,
          total_tokens: 0,
          durations: [],
          tokens: [],
          api_calls: []
        }
      }
      
      statsByKey[groupKey].total_executions++
      if (record.status === 'completed' || record.status === 'success') {
        statsByKey[groupKey].success_executions++
      } else if (record.status === 'failed') {
        statsByKey[groupKey].failed_executions++
      } else if (record.status === 'stopped') {
        statsByKey[groupKey].stopped_executions++
      }
      
      if (record.duration) {
        statsByKey[groupKey].durations.push(record.duration)
      }
      
      if (record.total_tokens) {
        statsByKey[groupKey].tokens.push(record.total_tokens)
        statsByKey[groupKey].total_tokens += record.total_tokens
      }
      
      if (record.api_calls) {
        statsByKey[groupKey].api_calls.push(record.api_calls)
        statsByKey[groupKey].total_api_calls += record.api_calls
      }
    })
    
    // 计算每组的成功率和平均时长
    const statsArray = Object.values(statsByKey).map((stat: any) => {
      stat.success_rate = stat.total_executions > 0 
        ? Math.round((stat.success_executions / stat.total_executions) * 100) 
        : 0
      
      stat.avg_duration = stat.durations.length > 0
        ? stat.durations.reduce((a: number, b: number) => a + b, 0) / stat.durations.length
        : 0
      
      delete stat.durations // 删除临时数组
      delete stat.tokens
      delete stat.api_calls
      return stat
    })
    
    // 按日期倒序排序
    statsArray.sort((a: any, b: any) => b.stat_date.localeCompare(a.stat_date))
    
    statisticsData.value = statsArray
    
    // 更新概览数据
    overviewData.total_executions = totalExecutions
    overviewData.success_rate = totalExecutions > 0 
      ? ((successExecutions / totalExecutions) * 100).toFixed(2) 
      : '0'
    overviewData.avg_duration = durationCount > 0 
      ? (totalDuration / durationCount).toFixed(2) 
      : '0'
    overviewData.total_tokens = totalTokens
    
    console.log('统计数据计算完成:', {
      total: totalExecutions,
      success: successExecutions,
      failed: failedExecutions,
      successRate: overviewData.success_rate,
      avgDuration: overviewData.avg_duration,
      totalTokens: totalTokens,
      totalApiCalls: totalApiCalls
    })
    
    // 更新图表
    await nextTick()
    updateCharts()
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  } finally {
    loading.value = false
  }
}

// 根据统计类型获取分组键
const getGroupKey = (dateStr: string, statType: string) => {
  if (!dateStr) return new Date().toISOString().split('T')[0]
  
  const date = new Date(dateStr)
  
  if (statType === 'daily') {
    // 每日：YYYY-MM-DD
    return date.toISOString().split('T')[0]
  } else if (statType === 'weekly') {
    // 每周：YYYY-WW（年-周数）
    const year = date.getFullYear()
    const weekNum = getWeekNumber(date)
    return `${year}-W${String(weekNum).padStart(2, '0')}`
  } else if (statType === 'monthly') {
    // 每月：YYYY-MM
    const year = date.getFullYear()
    const month = date.getMonth() + 1
    return `${year}-${String(month).padStart(2, '0')}`
  }
  
  return date.toISOString().split('T')[0]
}

// 获取周数（ISO 8601标准）
const getWeekNumber = (date: Date) => {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNum = d.getUTCDay() || 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
}

// 获取项目列表
const getProjects = async () => {
  try {
    console.log('开始获取主项目列表...')
    const res = await getProjectList({ page: 1, page_size: 100 })
    console.log('主项目列表API响应:', res)
    if (res.code === 200) {
      projectList.value = res.data.list || res.data.items || res.data || []
      console.log('主项目列表:', projectList.value)
    }
  } catch (error) {
    console.error('获取主项目列表失败:', error)
  }
}

// 获取趋势数据
const getTrendData = async () => {
  try {
    console.log('开始计算趋势数据...')
    
    // 从执行记录计算趋势数据
    const params: any = {}
    if (queryForm.project_id) {
      params.ui_project_id = queryForm.project_id
    }
    
    const res = await aiExecutionRecordApi.list(params)
    let records = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.items || [])
    
    // 过滤日期范围
    if (queryForm.start_date && queryForm.end_date) {
      const startDate = new Date(queryForm.start_date)
      const endDate = new Date(queryForm.end_date)
      endDate.setHours(23, 59, 59, 999)
      
      records = records.filter((record: any) => {
        if (!record.start_time) return false
        const recordDate = new Date(record.start_time)
        return recordDate >= startDate && recordDate <= endDate
      })
    }
    
    if (records.length === 0) {
      return {
        dates: [],
        total_executions: [],
        success_rate: [],
        avg_duration: [],
        total_tokens: []
      }
    }
    
    // 按统计类型分组
    const statsByKey: any = {}
    
    records.forEach((record: any) => {
      const groupKey = getGroupKey(record.start_time, queryForm.stat_type)
      if (!statsByKey[groupKey]) {
        statsByKey[groupKey] = {
          total: 0,
          success: 0,
          durations: [],
          tokens: []
        }
      }
      
      statsByKey[groupKey].total++
      if (record.status === 'completed' || record.status === 'success') {
        statsByKey[groupKey].success++
      }
      if (record.duration) {
        statsByKey[groupKey].durations.push(record.duration)
      }
      if (record.total_tokens) {
        statsByKey[groupKey].tokens.push(record.total_tokens)
      }
    })
    
    // 转换为数组并排序
    const keys = Object.keys(statsByKey).sort()
    const total_executions = keys.map(key => statsByKey[key].total)
    const success_rate = keys.map(key => {
      const stat = statsByKey[key]
      return stat.total > 0 ? Math.round((stat.success / stat.total) * 100) : 0
    })
    const avg_duration = keys.map(key => {
      const durations = statsByKey[key].durations
      return durations.length > 0 
        ? durations.reduce((a: number, b: number) => a + b, 0) / durations.length 
        : 0
    })
    const total_tokens = keys.map(key => {
      const tokens = statsByKey[key].tokens
      return tokens.length > 0 
        ? tokens.reduce((a: number, b: number) => a + b, 0) 
        : 0
    })
    
    // 格式化日期标签
    const formattedDates = keys.map(key => formatGroupKey(key, queryForm.stat_type))
    
    console.log('趋势数据计算完成:', {
      dates: formattedDates.length,
      total_executions,
      success_rate,
      avg_duration,
      total_tokens
    })
    
    return {
      dates: formattedDates,
      total_executions,
      success_rate,
      avg_duration,
      total_tokens
    }
  } catch (error) {
    console.error('获取趋势数据失败', error)
    return {
      dates: [],
      total_executions: [],
      success_rate: [],
      avg_duration: [],
      total_tokens: []
    }
  }
}

// 格式化分组键为显示标签
const formatGroupKey = (key: string, statType: string) => {
  if (statType === 'daily') {
    // YYYY-MM-DD -> MM-DD
    const parts = key.split('-')
    return `${parts[1]}-${parts[2]}`
  } else if (statType === 'weekly') {
    // YYYY-WNN -> 第NN周
    const weekNum = key.split('-W')[1]
    return `第${weekNum}周`
  } else if (statType === 'monthly') {
    // YYYY-MM -> MM月
    const month = key.split('-')[1]
    return `${parseInt(month)}月`
  }
  return key
}

// 初始化图表
const initCharts = () => {
  if (executionTrendChart.value) {
    executionTrendChartInstance = echarts.init(executionTrendChart.value)
  }
  if (successRateChart.value) {
    successRateChartInstance = echarts.init(successRateChart.value)
  }
  if (statusDistributionChart.value) {
    statusDistributionChartInstance = echarts.init(statusDistributionChart.value)
  }
  if (durationTrendChart.value) {
    durationTrendChartInstance = echarts.init(durationTrendChart.value)
  }
}

// 更新图表
const updateCharts = async () => {
  const trendData = await getTrendData()
  
  if (!trendData || trendData.dates.length === 0) {
    console.log('无趋势数据，跳过图表更新')
    return
  }
  
  console.log('开始更新图表...')
  
  // 执行趋势图
  if (executionTrendChartInstance) {
    executionTrendChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trendData.dates
      },
      yAxis: { type: 'value' },
      series: [{
        name: '执行次数',
        type: 'line',
        data: trendData.total_executions,
        smooth: true,
        areaStyle: {}
      }]
    })
    console.log('执行趋势图更新完成')
  }
  
  // 成功率趋势图
  if (successRateChartInstance) {
    successRateChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trendData.dates
      },
      yAxis: { 
        type: 'value',
        max: 100,
        axisLabel: { formatter: '{value}%' }
      },
      series: [{
        name: '成功率',
        type: 'line',
        data: trendData.success_rate,
        smooth: true,
        itemStyle: { color: '#67c23a' }
      }]
    })
    console.log('成功率趋势图更新完成')
  }
  
  // 状态分布饼图
  if (statusDistributionChartInstance && statisticsData.value.length > 0) {
    // 计算总体状态分布
    let totalSuccess = 0
    let totalFailed = 0
    let totalStopped = 0
    
    statisticsData.value.forEach((stat: any) => {
      totalSuccess += stat.success_executions
      totalFailed += stat.failed_executions
      totalStopped += stat.stopped_executions
    })
    
    statusDistributionChartInstance.setOption({
      tooltip: { trigger: 'item' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: '执行状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: totalSuccess, name: '成功', itemStyle: { color: '#67c23a' } },
          { value: totalFailed, name: '失败', itemStyle: { color: '#f56c6c' } },
          { value: totalStopped, name: '停止', itemStyle: { color: '#909399' } }
        ]
      }]
    })
    console.log('状态分布饼图更新完成')
  }
  
  // 平均时长趋势图
  if (durationTrendChartInstance) {
    durationTrendChartInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: trendData.dates
      },
      yAxis: { 
        type: 'value',
        axisLabel: { formatter: '{value}s' }
      },
      series: [{
        name: '平均时长',
        type: 'bar',
        data: trendData.avg_duration,
        itemStyle: { color: '#e6a23c' }
      }]
    })
    console.log('平均时长趋势图更新完成')
  }
  
  console.log('所有图表更新完成')
}

// 查询
const handleQuery = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    queryForm.start_date = dateRange.value[0]
    queryForm.end_date = dateRange.value[1]
  } else {
    queryForm.start_date = null
    queryForm.end_date = null
  }
  console.log('查询参数:', queryForm)
  getStatistics()
}

// 重置
const handleReset = () => {
  Object.assign(queryForm, {
    stat_type: 'daily',
    start_date: null,
    end_date: null,
    project_id: null
  })
  dateRange.value = []
  console.log('重置查询参数')
  getStatistics()
}

// 刷新统计
const handleRefresh = async () => {
  try {
    ElMessage.success('正在刷新统计数据...')
    await getStatistics()
    ElMessage.success('统计数据已刷新')
  } catch (error) {
    ElMessage.error('刷新统计失败')
  }
}

// 导出统计
const handleExport = () => {
  ElMessage.info('导出功能开发中')
}

// 工具函数
const getStatTypeLabel = (type: string) => {
  const map: any = { daily: '每日', weekly: '每周', monthly: '每月' }
  return map[type] || type
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  
  // 检查是否是周格式 (YYYY-WNN)
  if (dateStr.includes('-W')) {
    const [year, week] = dateStr.split('-W')
    return `${year}年第${week}周`
  }
  
  // 检查是否是月格式 (YYYY-MM)
  if (dateStr.match(/^\d{4}-\d{2}$/)) {
    const [year, month] = dateStr.split('-')
    return `${year}年${parseInt(month)}月`
  }
  
  // 日期格式 (YYYY-MM-DD)
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(2) + 'K'
  return num.toString()
}

// 初始化
onMounted(async () => {
  await getProjects()
  await getStatistics()
  await nextTick()
  initCharts()
  updateCharts()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    executionTrendChartInstance?.resize()
    successRateChartInstance?.resize()
    statusDistributionChartInstance?.resize()
    durationTrendChartInstance?.resize()
  })
})
</script>

<style scoped lang="scss">
.ai-browser-statistics-container {
  padding: 20px;
}

.statistics-cards {
  margin-bottom: 20px;
}

.stat-card {
  .stat-content {
    display: flex;
    align-items: center;
    
    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      margin-right: 16px;
    }
    
    .stat-info {
      flex: 1;
      
      .stat-value {
        font-size: 28px;
        font-weight: bold;
        color: #303133;
        margin-bottom: 4px;
      }
      
      .stat-label {
        font-size: 14px;
        color: #909399;
      }
    }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.query-form {
  margin-bottom: 20px;
}

.chart-container {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
  
  h4 {
    margin: 0 0 16px 0;
    color: #303133;
  }
}
</style>
