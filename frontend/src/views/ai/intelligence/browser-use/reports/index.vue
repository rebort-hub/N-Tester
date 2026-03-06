<template>
  <div class="ai-browser-reports-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI测试报告</span>
          <el-button type="primary" @click="handleGenerateReport">
            <el-icon><Document /></el-icon>
            生成报告
          </el-button>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
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
        
        <el-form-item label="状态">
          <el-select 
            v-model="queryForm.status" 
            placeholder="请选择状态" 
            clearable
            style="width: 150px"
          >
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
            <el-option label="部分成功" value="partial" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 报告列表 -->
      <el-table :data="reportList" v-loading="loading" border stripe>
        <el-table-column prop="report_id" label="报告ID" width="180" />
        <el-table-column prop="report_name" label="报告名称" min-width="200">
          <template #default="{ row }">
            {{ row.report_name }}
            <el-tag v-if="row.is_temp" type="info" size="small" style="margin-left: 8px;">实时</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="project_name" label="项目" width="150" />
        <el-table-column label="统计信息" width="200">
          <template #default="{ row }">
            <div style="font-size: 12px;">
              <div>总用例: {{ row.total_cases }}</div>
              <div>执行次数: {{ row.total_executions }}</div>
              <div>成功率: <span :style="{ color: getSuccessRateColor(row.success_rate) }">
                {{ row.success_rate }}%
              </span></div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="date_range" label="时间范围" width="200" />
        <el-table-column prop="created_time" label="生成时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewReport(row)" style="margin-right: 8px;">查看</el-button>
            <el-dropdown @command="(command) => handleExport(row, command)" style="margin-right: 8px;">
              <el-button type="success" size="small">
                导出<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="pdf">导出PDF</el-dropdown-item>
                  <el-dropdown-item command="html">导出HTML</el-dropdown-item>
                  <el-dropdown-item command="excel">导出Excel</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryForm.page"
        v-model:page-size="queryForm.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="getList"
        @current-change="getList"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 生成报告对话框 -->
    <el-dialog 
      v-model="generateDialogVisible" 
      title="生成测试报告"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="generateForm" :rules="generateRules" ref="generateFormRef" label-width="120px">
        <el-form-item label="报告名称" prop="report_name">
          <el-input v-model="generateForm.report_name" placeholder="请输入报告名称" />
        </el-form-item>
        
        <el-form-item label="项目" prop="project_id">
          <el-select 
            v-model="generateForm.project_id" 
            placeholder="请选择项目"
            style="width: 100%"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="日期范围" prop="date_range">
          <el-date-picker
            v-model="generateForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="执行状态">
          <el-checkbox-group v-model="generateForm.status_filter">
            <el-checkbox label="success">成功</el-checkbox>
            <el-checkbox label="failed">失败</el-checkbox>
            <el-checkbox label="stopped">停止</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="包含内容">
          <el-checkbox-group v-model="generateForm.include_sections">
            <el-checkbox label="overview">执行概览</el-checkbox>
            <el-checkbox label="case_details">用例详情</el-checkbox>
            <el-checkbox label="trend_analysis">趋势分析</el-checkbox>
            <el-checkbox label="failure_analysis">失败分析</el-checkbox>
            <el-checkbox label="ai_usage">AI使用统计</el-checkbox>
            <el-checkbox label="recommendations">改进建议</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitGenerate" :loading="generateLoading">
          生成报告
        </el-button>
      </template>
    </el-dialog>

    <!-- 报告详情对话框 -->
    <el-dialog 
      v-model="reportDialogVisible" 
      title="测试报告详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="currentReport" class="report-content">
        <!-- 报告头部 -->
        <div class="report-header">
          <h1>{{ currentReport.report_name }}</h1>
          <div class="report-meta">
            <span>项目: {{ currentReport.project_name }}</span>
            <span>时间范围: {{ currentReport.date_range }}</span>
            <span>生成时间: {{ formatDateTime(currentReport.created_time) }}</span>
          </div>
        </div>

        <!-- 执行概览 -->
        <el-card class="report-section" v-if="currentReport.overview">
          <template #header>
            <h3>执行概览</h3>
          </template>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">总用例数</div>
                <div class="overview-value">{{ currentReport.overview.total_cases }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">总执行次数</div>
                <div class="overview-value">{{ currentReport.overview.total_executions }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">成功次数</div>
                <div class="overview-value success">{{ currentReport.overview.success_count }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">失败次数</div>
                <div class="overview-value failed">{{ currentReport.overview.failed_count }}</div>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 20px;">
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">成功率</div>
                <div class="overview-value" :style="{ color: getSuccessRateColor(currentReport.overview.success_rate) }">
                  {{ currentReport.overview.success_rate }}%
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">总执行时长</div>
                <div class="overview-value">{{ formatDuration(currentReport.overview.total_duration) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">平均时长</div>
                <div class="overview-value">{{ formatDuration(currentReport.overview.avg_duration) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="overview-item">
                <div class="overview-label">Token使用量</div>
                <div class="overview-value">{{ formatNumber(currentReport.overview.total_tokens) }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 用例详情 -->
        <el-card class="report-section" v-if="currentReport.case_details">
          <template #header>
            <h3>用例详情</h3>
          </template>
          <el-table :data="currentReport.case_details" border stripe>
            <el-table-column prop="case_id" label="用例编号" width="120" />
            <el-table-column prop="title" label="用例标题" min-width="200" />
            <el-table-column prop="priority" label="优先级" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="getPriorityType(row.priority)" size="small">
                  {{ row.priority }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="execution_count" label="执行次数" width="100" align="center" />
            <el-table-column prop="success_count" label="成功次数" width="100" align="center">
              <template #default="{ row }">
                <span style="color: #67c23a;">{{ row.success_count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="failed_count" label="失败次数" width="100" align="center">
              <template #default="{ row }">
                <span style="color: #f56c6c;">{{ row.failed_count }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="success_rate" label="成功率" width="100" align="center">
              <template #default="{ row }">
                <span :style="{ color: getSuccessRateColor(row.success_rate) }">
                  {{ row.success_rate }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="avg_duration" label="平均时长" width="100" align="center">
              <template #default="{ row }">
                {{ row.avg_duration }}s
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 执行趋势 -->
        <el-card class="report-section" v-if="currentReport.execution_trend">
          <template #header>
            <h3>执行趋势分析</h3>
          </template>
          <div ref="reportTrendChart" style="width: 100%; height: 400px;"></div>
        </el-card>

        <!-- 失败分析 -->
        <el-card class="report-section" v-if="currentReport.failure_analysis">
          <template #header>
            <h3>失败用例分析</h3>
          </template>
          <el-table :data="currentReport.failure_analysis" border stripe>
            <el-table-column prop="case_id" label="用例编号" width="120" />
            <el-table-column prop="title" label="用例标题" min-width="200" />
            <el-table-column prop="failed_count" label="失败次数" width="100" align="center" />
            <el-table-column prop="error_message" label="错误信息" min-width="300" show-overflow-tooltip />
            <el-table-column prop="last_failed_time" label="最后失败时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.last_failed_time) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- AI使用统计 -->
        <el-card class="report-section" v-if="currentReport.ai_usage">
          <template #header>
            <h3>AI使用统计</h3>
          </template>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="ai-usage-item">
                <div class="ai-usage-label">总API调用次数</div>
                <div class="ai-usage-value">{{ currentReport.ai_usage.total_api_calls }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="ai-usage-item">
                <div class="ai-usage-label">总Token使用量</div>
                <div class="ai-usage-value">{{ formatNumber(currentReport.ai_usage.total_tokens) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="ai-usage-item">
                <div class="ai-usage-label">平均每次Token</div>
                <div class="ai-usage-value">{{ currentReport.ai_usage.avg_tokens_per_execution }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 改进建议 -->
        <el-card class="report-section" v-if="currentReport.recommendations">
          <template #header>
            <h3>改进建议</h3>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(recommendation, index) in currentReport.recommendations"
              :key="index"
              :timestamp="recommendation.category"
              placement="top"
            >
              <el-card>
                <h4>{{ recommendation.title }}</h4>
                <p>{{ recommendation.description }}</p>
                <el-tag v-if="recommendation.priority" :type="getPriorityType(recommendation.priority)" size="small">
                  {{ recommendation.priority }}
                </el-tag>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </div>
      
      <template #footer>
        <el-button @click="reportDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleExport(currentReport, 'pdf')">导出PDF</el-button>
        <el-button type="success" @click="handleExport(currentReport, 'html')">导出HTML</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document, ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getProjectList } from '/@/api/v1/project'
// 导入AI智能浏览器API
import { aiExecutionRecordApi, aiTestReportApi } from '/@/api/v1/ai_intelligence'

const loading = ref(false)
const reportList = ref([])
const total = ref(0)
const projectList = ref([])
const dateRange = ref([])

const queryForm = reactive({
  start_date: null,
  end_date: null,
  project_id: null,
  status: null,
  page: 1,
  page_size: 20
})

// 生成报告对话框
const generateDialogVisible = ref(false)
const generateLoading = ref(false)
const generateFormRef = ref()
const generateForm = reactive({
  report_name: '',
  project_id: null,
  date_range: [],
  status_filter: ['success', 'failed'],
  include_sections: ['overview', 'case_details', 'trend_analysis', 'failure_analysis', 'ai_usage', 'recommendations']
})

const generateRules = {
  report_name: [{ required: true, message: '请输入报告名称', trigger: 'blur' }],
  date_range: [{ required: true, message: '请选择日期范围', trigger: 'change' }]
}

// 报告详情对话框
const reportDialogVisible = ref(false)
const currentReport = ref<any>(null)
const reportTrendChart = ref()
let reportTrendChartInstance: any = null

// 获取报告列表
const getList = async () => {
  loading.value = true
  try {
    // 同时获取已保存的报告和实时生成的报告
    const params: any = {
      page: 1,
      page_size: 100  // 后端限制最大100
    }
    if (queryForm.project_id) params.project_id = queryForm.project_id
    if (queryForm.start_date) params.start_date = queryForm.start_date
    if (queryForm.end_date) params.end_date = queryForm.end_date
    
    // 1. 获取已保存的报告（可能需要多次请求获取所有数据）
    const savedReports: any[] = []
    try {
      let currentPage = 1
      let hasMore = true
      
      while (hasMore) {
        const savedRes = await aiTestReportApi.list({ ...params, page: currentPage })
        if (savedRes.code === 200) {
          const items = savedRes.data.items || []
          savedReports.push(...items)
          
          // 检查是否还有更多数据
          const total = savedRes.data.total || 0
          hasMore = savedReports.length < total
          currentPage++
        } else {
          hasMore = false
        }
      }
    } catch (error) {
      console.error('获取已保存报告失败:', error)
    }
    
    // 2. 基于执行记录实时生成报告
    const execParams: any = {}
    if (queryForm.project_id) execParams.ui_project_id = queryForm.project_id
    if (queryForm.start_date) execParams.start_date = queryForm.start_date
    if (queryForm.end_date) execParams.end_date = queryForm.end_date
    if (queryForm.status) execParams.status = queryForm.status
    
    const execRes = await aiExecutionRecordApi.list(execParams)
    const dynamicReports: any[] = []
    
    if (execRes.code === 200) {
      const records = execRes.data?.items || execRes.data?.list || execRes.data || []
      
      // 按项目分组统计
      const projectStats: any = {}
      records.forEach((record: any) => {
        const projectId = record.ui_project_id || 0
        if (!projectStats[projectId]) {
          projectStats[projectId] = {
            project_id: projectId,
            total_executions: 0,
            success_count: 0,
            failed_count: 0,
            total_cases: new Set(),
            start_time: null,
            end_time: null
          }
        }
        
        projectStats[projectId].total_executions++
        if (record.status === 'completed' || record.status === 'success') {
          projectStats[projectId].success_count++
        } else if (record.status === 'failed') {
          projectStats[projectId].failed_count++
        }
        if (record.ai_case_id) {
          projectStats[projectId].total_cases.add(record.ai_case_id)
        }
        
        // 记录时间范围
        if (record.start_time) {
          const recordTime = new Date(record.start_time)
          if (!projectStats[projectId].start_time || recordTime < projectStats[projectId].start_time) {
            projectStats[projectId].start_time = recordTime
          }
          if (!projectStats[projectId].end_time || recordTime > projectStats[projectId].end_time) {
            projectStats[projectId].end_time = recordTime
          }
        }
      })
      
      // 获取项目名称映射
      const projectMap: any = {}
      projectList.value.forEach((p: any) => {
        projectMap[p.id] = p.name
      })
      
      // 转换为报告列表（实时生成的报告）
      Object.values(projectStats).forEach((stat: any) => {
        const projectName = projectMap[stat.project_id] || `项目${stat.project_id}`
        const startDate = stat.start_time ? formatDate(stat.start_time) : (queryForm.start_date || '-')
        const endDate = stat.end_time ? formatDate(stat.end_time) : (queryForm.end_date || '-')
        
        // 检查是否已经有保存的报告（避免重复）
        const hasSaved = savedReports.some(r => r.project_id === stat.project_id)
        if (!hasSaved) {
          dynamicReports.push({
            report_id: `TEMP_${stat.project_id}_${Date.now()}`,
            report_name: `${projectName}测试报告（实时）`,
            project_id: stat.project_id,
            project_name: projectName,
            total_cases: stat.total_cases.size,
            total_executions: stat.total_executions,
            success_rate: stat.total_executions > 0 
              ? ((stat.success_count / stat.total_executions) * 100).toFixed(2) 
              : 0,
            date_range: `${startDate} 至 ${endDate}`,
            created_time: new Date().toISOString(),
            status: 'generated',
            is_temp: true,  // 标记为临时报告
            // 添加详情数据
            overview: {
              total_cases: stat.total_cases.size,
              total_executions: stat.total_executions,
              success_count: stat.success_count,
              failed_count: stat.failed_count,
              success_rate: stat.total_executions > 0 
                ? ((stat.success_count / stat.total_executions) * 100).toFixed(2) 
                : 0,
              total_duration: 0,
              avg_duration: 0,
              total_tokens: 0
            }
          })
        }
      })
    }
    
    // 3. 合并已保存的报告和实时生成的报告
    reportList.value = [...savedReports, ...dynamicReports]
    
    // 4. 分页处理
    total.value = reportList.value.length
    const start = (queryForm.page - 1) * queryForm.page_size
    const end = start + queryForm.page_size
    reportList.value = reportList.value.slice(start, end)
    
    console.log('报告列表加载成功:', reportList.value.length, '(已保存:', savedReports.length, ', 实时:', dynamicReports.length, ')')
  } catch (error) {
    console.error('获取报告列表失败:', error)
    ElMessage.error('获取报告列表失败')
  } finally {
    loading.value = false
  }
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

// 查询
const handleQuery = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    queryForm.start_date = dateRange.value[0]
    queryForm.end_date = dateRange.value[1]
  }
  queryForm.page = 1
  getList()
}

// 重置
const handleReset = () => {
  Object.assign(queryForm, {
    start_date: null,
    end_date: null,
    project_id: null,
    status: null,
    page: 1,
    page_size: 20
  })
  dateRange.value = []
  getList()
}

// 生成报告
const handleGenerateReport = () => {
  generateForm.report_name = `测试报告_${new Date().toLocaleDateString()}`
  generateDialogVisible.value = true
}

// 提交生成
const submitGenerate = async () => {
  if (!generateFormRef.value) return
  
  await generateFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    generateLoading.value = true
    try {
      // 基于执行记录生成报告数据
      const params: any = {}
      if (generateForm.project_id) params.ui_project_id = generateForm.project_id
      if (generateForm.date_range && generateForm.date_range.length === 2) {
        params.start_date = formatDate(generateForm.date_range[0])
        params.end_date = formatDate(generateForm.date_range[1])
      }
      
      const res = await aiExecutionRecordApi.list(params)
      if (res.code === 200) {
        const records = res.data?.items || res.data?.list || res.data || []
        
        // 统计数据
        let totalCases = new Set()
        let totalExecutions = records.length
        let successCount = 0
        let failedCount = 0
        
        records.forEach((record: any) => {
          if (record.ai_case_id) {
            totalCases.add(record.ai_case_id)
          }
          if (record.status === 'completed' || record.status === 'success') {
            successCount++
          } else if (record.status === 'failed') {
            failedCount++
          }
        })
        
        // 获取项目名称
        const project = projectList.value.find((p: any) => p.id === generateForm.project_id)
        const projectName = project ? project.name : `项目${generateForm.project_id}`
        
        // 创建报告
        const reportData = {
          report_name: generateForm.report_name,
          project_id: generateForm.project_id,
          project_name: projectName,
          start_date: params.start_date || null,
          end_date: params.end_date || null,
          date_range: `${params.start_date || '-'} 至 ${params.end_date || '-'}`,
          total_cases: totalCases.size,
          total_executions: totalExecutions,
          success_count: successCount,
          failed_count: failedCount,
          success_rate: totalExecutions > 0 ? ((successCount / totalExecutions) * 100).toFixed(2) : 0,
          total_duration: 0,
          avg_duration: 0,
          total_tokens: 0,
          report_data: {
            overview: {
              total_cases: totalCases.size,
              total_executions: totalExecutions,
              success_count: successCount,
              failed_count: failedCount,
              success_rate: totalExecutions > 0 ? ((successCount / totalExecutions) * 100).toFixed(2) : 0,
              total_duration: 0,
              avg_duration: 0,
              total_tokens: 0
            }
          }
        }
        
        const createRes = await aiTestReportApi.create(reportData)
        if (createRes.code === 200) {
          ElMessage.success('报告已生成并保存')
          generateDialogVisible.value = false
          getList()
        }
      }
    } catch (error) {
      ElMessage.error('生成报告失败')
      console.error(error)
    } finally {
      generateLoading.value = false
    }
  })
}
// 查看报告
const handleViewReport = (row: any) => {
  currentReport.value = row
  reportDialogVisible.value = true
  
  // 初始化图表
  nextTick(() => {
    if (reportTrendChart.value && row.execution_trend) {
      reportTrendChartInstance = echarts.init(reportTrendChart.value)
      reportTrendChartInstance.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['执行次数', '成功率'] },
        xAxis: {
          type: 'category',
          data: row.execution_trend.dates
        },
        yAxis: [
          { type: 'value', name: '执行次数' },
          { type: 'value', name: '成功率(%)', max: 100 }
        ],
        series: [
          {
            name: '执行次数',
            type: 'bar',
            data: row.execution_trend.executions
          },
          {
            name: '成功率',
            type: 'line',
            yAxisIndex: 1,
            data: row.execution_trend.success_rates
          }
        ]
      })
    }
  })
}

// 导出报告
const handleExport = async (row: any, format: string) => {
  try {
    // 导出功能待实现
    ElMessage.info(`导出${format.toUpperCase()}格式报告功能开发中`)
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 删除报告
const handleDelete = (row: any) => {
  // 临时报告不能删除
  if (row.is_temp) {
    ElMessage.warning('实时生成的报告无法删除，只能删除已保存的报告')
    return
  }
  
  ElMessageBox.confirm(
    '确定要完全删除该报告吗？此操作不可恢复！', 
    '警告', 
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger'
    }
  ).then(async () => {
    try {
      // 调用后端API硬删除
      const res = await aiTestReportApi.delete(row.report_id)
      if (res.code === 200) {
        ElMessage.success('报告已完全删除')
        getList()
      }
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }).catch(() => {
    // 用户取消删除
  })
}

// 工具函数
const getPriorityType = (priority: string) => {
  const map: any = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return map[priority] || ''
}

const getSuccessRateColor = (rate: number) => {
  if (rate >= 80) return '#67c23a'
  if (rate >= 60) return '#e6a23c'
  return '#f56c6c'
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const formatDate = (date: Date | string) => {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

const formatDuration = (seconds?: number) => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}分${secs}秒`
}

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(2) + 'M'
  if (num >= 1000) return (num / 1000).toFixed(2) + 'K'
  return num.toString()
}

onMounted(() => {
  getProjects()
  getList()
})
</script>

<style scoped lang="scss">
.ai-browser-reports-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-form {
  margin-bottom: 20px;
}

.report-content {
  .report-header {
    text-align: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 2px solid #e4e7ed;
    
    h1 {
      margin: 0 0 10px 0;
      color: #303133;
    }
    
    .report-meta {
      display: flex;
      justify-content: center;
      gap: 30px;
      color: #909399;
      font-size: 14px;
    }
  }
  
  .report-section {
    margin-bottom: 20px;
    
    h3 {
      margin: 0;
      color: #303133;
    }
  }
  
  .overview-item {
    text-align: center;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
    
    .overview-label {
      font-size: 14px;
      color: #909399;
      margin-bottom: 8px;
    }
    
    .overview-value {
      font-size: 28px;
      font-weight: bold;
      color: #303133;
      
      &.success {
        color: #67c23a;
      }
      
      &.failed {
        color: #f56c6c;
      }
    }
  }
  
  .ai-usage-item {
    text-align: center;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 4px;
    
    .ai-usage-label {
      font-size: 14px;
      color: #909399;
      margin-bottom: 8px;
    }
    
    .ai-usage-value {
      font-size: 24px;
      font-weight: bold;
      color: #409eff;
    }
  }
}
</style>
