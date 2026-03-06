<template>
  <div class="test-report-page">
    <!-- 顶部面包屑 -->
    <el-card shadow="hover" class="header-card">
      <div class="header-content">
        <div class="breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/testing/ui-automation' }">UI自动化</el-breadcrumb-item>
            <el-breadcrumb-item>测试报告</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="actions">
          <el-button :icon="Back" @click="handleBack">返回</el-button>
        </div>
      </div>
    </el-card>

    <!-- 筛选条件 -->
    <el-card shadow="hover" style="margin-top: 20px">
      <div class="filter-bar">
        <el-select v-model="filterForm.ui_project_id" placeholder="选择项目" clearable style="width: 200px" @change="loadReportList">
          <el-option
            v-for="project in projectList"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-select v-model="filterForm.status" placeholder="执行状态" clearable style="width: 150px" @change="loadReportList">
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
          <el-option label="执行中" value="running" />
          <el-option label="已停止" value="stopped" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 300px"
          @change="handleDateChange"
        />
        <el-button type="primary" :icon="Search" @click="loadReportList">查询</el-button>
        <el-button :icon="Refresh" @click="handleReset">重置</el-button>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.total_executions }}</div>
              <div class="stat-label">总执行次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.success_count }}</div>
              <div class="stat-label">成功次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon failed">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.failed_count }}</div>
              <div class="stat-label">失败次数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon rate">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ statistics.success_rate }}%</div>
              <div class="stat-label">成功率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 报告列表 -->
    <el-card shadow="hover" style="margin-top: 20px">
      <el-table :data="reportList" v-loading="loading" border stripe style="width: 100%">
        <el-table-column prop="id" label="报告ID" min-width="80" />
        <el-table-column prop="project_name" label="项目名称" min-width="120" show-overflow-tooltip />
        <el-table-column prop="suite_name" label="测试套件" min-width="120" show-overflow-tooltip />
        <el-table-column prop="status" label="执行状态" min-width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="步骤统计" min-width="220">
          <template #default="{ row }">
            <div class="steps-progress">
              <el-progress
                :percentage="getSuccessPercentage(row)"
                :color="getProgressColor(row)"
                :format="() => `${row.passed_steps}/${row.total_steps}`"
              />
              <div class="steps-detail">
                <span class="success-text">通过: {{ row.passed_steps }}</span>
                <span class="failed-text">失败: {{ row.failed_steps }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="执行时长" min-width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="engine_type" label="执行引擎" min-width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.engine_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewReport(row)">查看报告</el-button>
            <el-button type="success" size="small" @click="handleViewLogs(row)" style="margin-left: 8px;">查看日志</el-button>
            <el-button 
              v-if="row.status === 'failed' && hasScreenshots(row)" 
              type="danger" 
              size="small" 
              @click="handleViewScreenshots(row)"
              style="margin-left: 8px;"
            >
              失败截图
            </el-button>
            <el-dropdown @command="handleExportCommand" trigger="click" style="margin-left: 8px;">
              <el-button type="warning" size="small">
                导出<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="{action: 'preview', row}">预览报告</el-dropdown-item>
                  <el-dropdown-item :command="{action: 'download', row}">下载HTML</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadReportList"
        @current-change="loadReportList"
        style="margin-top: 15px; justify-content: flex-end"
      />
    </el-card>

    <!-- 报告详情对话框 -->
    <el-dialog
      v-model="reportDialogVisible"
      title="测试报告详情"
      width="1200px"
      :close-on-click-modal="false"
    >
      <div class="report-detail" v-if="currentReport">
        <!-- 报告头部 -->
        <el-descriptions :column="3" border>
          <el-descriptions-item label="报告ID">{{ currentReport.id }}</el-descriptions-item>
          <el-descriptions-item label="项目名称">{{ currentReport.project_name }}</el-descriptions-item>
          <el-descriptions-item label="测试套件">{{ currentReport.suite_name || '单个用例' }}</el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="getStatusTagType(currentReport.status)">
              {{ getStatusName(currentReport.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行引擎">{{ currentReport.engine_type }}</el-descriptions-item>
          <el-descriptions-item label="浏览器">{{ currentReport.browser_type }}</el-descriptions-item>
          <el-descriptions-item label="总步骤数">{{ currentReport.total_steps }}</el-descriptions-item>
          <el-descriptions-item label="通过步骤">
            <span style="color: #67c23a">{{ currentReport.passed_steps }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="失败步骤">
            <span style="color: #f56c6c">{{ currentReport.failed_steps }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="执行时长">{{ formatDuration(currentReport.duration) }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(currentReport.start_time) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ formatDateTime(currentReport.end_time) }}</el-descriptions-item>
        </el-descriptions>

        <!-- 执行日志 -->
        <el-divider content-position="left">执行日志</el-divider>
        <div class="log-container">
          <pre>{{ currentReport.logs || '暂无日志' }}</pre>
        </div>

        <!-- 错误信息 -->
        <el-divider content-position="left" v-if="currentReport.error_message">错误信息</el-divider>
        <el-alert
          v-if="currentReport.error_message"
          type="error"
          :title="currentReport.error_message"
          :closable="false"
        />
      </div>
    </el-dialog>

    <!-- 日志对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="执行日志"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="logs-actions">
        <el-button type="primary" size="small" :icon="CopyDocument" @click="handleCopyLogs">复制日志</el-button>
        <el-button type="success" size="small" :icon="Download" @click="handleDownloadLogs">下载日志</el-button>
      </div>
      <div class="log-container">
        <pre>{{ currentLogs }}</pre>
      </div>
    </el-dialog>

    <!-- 失败截图对话框 -->
    <el-dialog
      v-model="screenshotsDialogVisible"
      title="失败截图"
      width="1000px"
      :close-on-click-modal="false"
    >
      <div v-if="currentScreenshots && currentScreenshots.length > 0">
        <el-timeline>
          <el-timeline-item
            v-for="(screenshot, index) in currentScreenshots"
            :key="index"
            :timestamp="formatDateTime(screenshot.timestamp)"
            placement="top"
          >
            <el-card>
              <template #header>
                <div class="screenshot-header">
                  <span class="screenshot-title">
                    步骤 {{ screenshot.step_number }}: {{ screenshot.step_description }}
                  </span>
                  <el-button
                    type="primary"
                    size="small"
                    :icon="Download"
                    @click="handleDownloadScreenshot(screenshot, index)"
                  >
                    下载截图
                  </el-button>
                </div>
              </template>
              <el-alert
                v-if="screenshot.error_message"
                :title="screenshot.error_message"
                type="error"
                :closable="false"
                style="margin-bottom: 15px"
              />
              <div class="screenshot-container">
                <el-image
                  :src="screenshot.screenshot"
                  :preview-src-list="[screenshot.screenshot]"
                  fit="contain"
                  style="width: 100%; max-height: 500px"
                >
                  <template #error>
                    <div class="image-error">
                      <el-icon><Picture /></el-icon>
                      <span>截图加载失败</span>
                    </div>
                  </template>
                </el-image>
              </div>
            </el-card>
          </el-timeline-item>
        </el-timeline>
      </div>
      <el-empty v-else description="暂无失败截图" />
    </el-dialog>

    <!-- 报告预览对话框 -->
    <el-dialog
      v-model="reportPreviewDialogVisible"
      title="报告预览"
      width="90%"
      :close-on-click-modal="false"
      top="5vh"
    >
      <div class="report-preview-container">
        <div class="preview-toolbar">
          <el-button type="primary" size="small" @click="handleDownloadCurrentReport">
            <el-icon><Download /></el-icon>
            下载HTML
          </el-button>
          <el-button size="small" @click="handleOpenInNewWindow">
            <el-icon><CopyDocument /></el-icon>
            新窗口打开
          </el-button>
        </div>
        <div class="preview-content">
          <div 
            ref="previewContainer"
            class="preview-html-container"
            v-html="currentReportHtml"
          ></div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Back,
  Search,
  Refresh,
  Document,
  CircleCheck,
  CircleClose,
  TrendCharts,
  CopyDocument,
  Download,
  Picture,
  ArrowDown
} from '@element-plus/icons-vue'
import { uiExecutionApi, uiProjectApi } from '/@/api/v1/ui_automation'
import { formatDateTime } from '/@/utils/formatTime'

const router = useRouter()
const route = useRoute()

// 项目列表
const projectList = ref([])

// 筛选条件
const filterForm = reactive({
  ui_project_id: null,
  status: null,
  start_date: null,
  end_date: null
})

const dateRange = ref([])

// 统计数据
const statistics = reactive({
  total_executions: 0,
  success_count: 0,
  failed_count: 0,
  success_rate: 0
})

// 报告列表
const reportList = ref([])
const loading = ref(false)

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 报告详情
const reportDialogVisible = ref(false)
const currentReport = ref<any>(null)

// 日志对话框
const logsDialogVisible = ref(false)
const currentLogs = ref('')

// 截图对话框
const screenshotsDialogVisible = ref(false)
const currentScreenshots = ref<any[]>([])

// 报告预览对话框
const reportPreviewDialogVisible = ref(false)
const currentReportHtml = ref('')
const currentReportRow = ref<any>(null)
const previewContainer = ref<HTMLDivElement>()

// 判断是否有截图
const hasScreenshots = (row: any) => {
  return row.screenshots && Array.isArray(row.screenshots) && row.screenshots.length > 0
}

// 加载项目列表
const loadProjectList = async () => {
  try {
    const res = await uiProjectApi.list({ page: 1, page_size: 1000 })
    projectList.value = res.data.items || []
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    const params: any = {}
    if (filterForm.ui_project_id) {
      params.ui_project_id = filterForm.ui_project_id
    }
    if (filterForm.start_date) {
      params.start_date = filterForm.start_date
    }
    if (filterForm.end_date) {
      params.end_date = filterForm.end_date
    }
    
    const res = await uiExecutionApi.statistics(params)
    Object.assign(statistics, res.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载报告列表
const loadReportList = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    
    if (filterForm.ui_project_id) {
      params.ui_project_id = filterForm.ui_project_id
    }
    if (filterForm.status) {
      params.status = filterForm.status
    }
    if (filterForm.start_date) {
      params.start_date = filterForm.start_date
    }
    if (filterForm.end_date) {
      params.end_date = filterForm.end_date
    }
    
    const res = await uiExecutionApi.list(params)
    reportList.value = res.data.items || []
    pagination.total = res.data.total || 0
    
    // 加载统计数据
    await loadStatistics()
  } catch (error) {
    ElMessage.error('加载报告列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 日期范围变化
const handleDateChange = (dates: any) => {
  if (dates && dates.length === 2) {
    // 格式化日期为 YYYY-MM-DD 格式
    const startDate = new Date(dates[0])
    const endDate = new Date(dates[1])
    
    filterForm.start_date = startDate.toISOString().split('T')[0]
    filterForm.end_date = endDate.toISOString().split('T')[0]
  } else {
    filterForm.start_date = null
    filterForm.end_date = null
  }
  loadReportList()
}

// 重置筛选
const handleReset = () => {
  filterForm.ui_project_id = null
  filterForm.status = null
  filterForm.start_date = null
  filterForm.end_date = null
  dateRange.value = []
  pagination.page = 1
  loadReportList()
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const types: any = {
    running: '',
    success: 'success',
    failed: 'danger',
    stopped: 'warning'
  }
  return types[status] || 'info'
}

// 获取状态名称
const getStatusName = (status: string) => {
  const names: any = {
    running: '执行中',
    success: '成功',
    failed: '失败',
    stopped: '已停止'
  }
  return names[status] || status
}

// 获取成功百分比
const getSuccessPercentage = (row: any) => {
  if (row.total_steps === 0) return 0
  return Math.round((row.passed_steps / row.total_steps) * 100)
}

// 获取进度条颜色
const getProgressColor = (row: any) => {
  const percentage = getSuccessPercentage(row)
  if (percentage === 100) return '#67c23a'
  if (percentage >= 80) return '#e6a23c'
  return '#f56c6c'
}

// 格式化时长
const formatDuration = (duration: number) => {
  if (!duration) return '-'
  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`
  }
  return `${remainingSeconds}秒`
}

// 查看报告
const handleViewReport = async (row: any) => {
  try {
    const res = await uiExecutionApi.get(row.id)
    currentReport.value = res.data
    reportDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载报告详情失败')
    console.error(error)
  }
}

// 查看日志
const handleViewLogs = async (row: any) => {
  try {
    const res = await uiExecutionApi.getLogs(row.id)
    currentLogs.value = res.data.logs || '暂无日志'
    logsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载日志失败')
    console.error(error)
  }
}

// 复制日志
const handleCopyLogs = async () => {
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(currentLogs.value)
      ElMessage.success('日志已复制到剪贴板')
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = currentLogs.value
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          ElMessage.success('日志已复制到剪贴板')
        } else {
          ElMessage.error('复制失败，请手动复制')
        }
      } catch (err) {
        console.error('复制失败:', err)
        ElMessage.error('复制失败，请手动复制')
      } finally {
        document.body.removeChild(textArea)
      }
    }
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 下载日志
const handleDownloadLogs = () => {
  const blob = new Blob([currentLogs.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `execution_logs_${Date.now()}.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('日志已下载')
}

// 查看失败截图
const handleViewScreenshots = async (row: any) => {
  try {
    const res = await uiExecutionApi.get(row.id)
    currentScreenshots.value = res.data.screenshots || []
    screenshotsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载截图失败')
    console.error(error)
  }
}

// 下载单个截图
const handleDownloadScreenshot = (screenshot: any, index: number) => {
  try {
    // 从 base64 数据中提取图片数据
    const base64Data = screenshot.screenshot.replace(/^data:image\/\w+;base64,/, '')
    const binaryData = atob(base64Data)
    const arrayBuffer = new ArrayBuffer(binaryData.length)
    const uint8Array = new Uint8Array(arrayBuffer)
    
    for (let i = 0; i < binaryData.length; i++) {
      uint8Array[i] = binaryData.charCodeAt(i)
    }
    
    const blob = new Blob([uint8Array], { type: 'image/png' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `screenshot_step${screenshot.step_number}_${Date.now()}.png`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('截图已下载')
  } catch (error) {
    console.error('下载截图失败:', error)
    ElMessage.error('下载截图失败')
  }
}

// 导出命令处理
const handleExportCommand = async (command: any) => {
  const { action, row } = command
  
  if (action === 'preview') {
    // 预览报告
    try {
      ElMessage.info('正在生成报告预览...')
      const res = await uiExecutionApi.export(row.id, { format: 'html' })
      
      // 直接使用返回的HTML内容
      currentReportHtml.value = res.data
      currentReportRow.value = row
      reportPreviewDialogVisible.value = true
      
      ElMessage.success('报告预览已生成')
    } catch (error) {
      ElMessage.error('生成报告预览失败')
      console.error('预览错误:', error)
    }
  } else if (action === 'download') {
    // 下载报告
    await handleExport(row)
  }
}

// 下载当前预览的报告
const handleDownloadCurrentReport = () => {
  if (currentReportHtml.value && currentReportRow.value) {
    const blob = new Blob([currentReportHtml.value], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `execution_report_${currentReportRow.value.id}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.html`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('报告已下载')
  }
}

// 在新窗口打开当前报告
const handleOpenInNewWindow = () => {
  if (currentReportHtml.value) {
    const newWindow = window.open('', '_blank')
    if (newWindow) {
      newWindow.document.write(currentReportHtml.value)
      newWindow.document.close()
      ElMessage.success('报告已在新窗口打开')
    } else {
      ElMessage.error('无法打开新窗口，请检查浏览器设置')
    }
  }
}

// 导出报告
const handleExport = async (row: any) => {
  try {
    ElMessage.info('正在生成报告...')
    const res = await uiExecutionApi.export(row.id, { format: 'html' })
    
    // 创建Blob并下载
    const blob = new Blob([res.data], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `execution_report_${row.id}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.html`
    a.click()
    URL.revokeObjectURL(url)
    
    ElMessage.success('报告已导出')
  } catch (error) {
    ElMessage.error('导出报告失败')
    console.error(error)
  }
}

// 返回
const handleBack = () => {
  router.push('/testing/ui-automation')
}

// 初始化
onMounted(() => {
  loadProjectList()
  loadReportList()
  
  // 检查是否有 execution_id 参数，如果有则自动打开该报告详情
  const executionId = route.query.execution_id
  if (executionId) {
    handleViewReport({ id: Number(executionId) })
  }
})
</script>

<style scoped lang="scss">
.test-report-page {
  padding: 20px;

  .header-card {
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .breadcrumb {
        font-size: 16px;
      }
    }
  }

  .filter-bar {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 20px;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        color: white;

        &.total {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        &.success {
          background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
        }

        &.failed {
          background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
        }

        &.rate {
          background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
        }
      }

      .stat-info {
        flex: 1;

        .stat-value {
          font-size: 28px;
          font-weight: bold;
          color: #303133;
        }

        .stat-label {
          font-size: 14px;
          color: #909399;
          margin-top: 5px;
        }
      }
    }
  }

  .steps-progress {
    .steps-detail {
      display: flex;
      gap: 15px;
      margin-top: 5px;
      font-size: 12px;

      .success-text {
        color: #67c23a;
      }

      .failed-text {
        color: #f56c6c;
      }
    }
  }

  .report-detail {
    .log-container {
      max-height: 400px;
      overflow-y: auto;
      background-color: #f5f5f5;
      padding: 15px;
      border-radius: 4px;

      pre {
        margin: 0;
        font-family: 'Courier New', Courier, monospace;
        font-size: 13px;
        line-height: 1.5;
        color: #333;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
    }
  }

  .logs-actions {
    margin-bottom: 15px;
    display: flex;
    gap: 10px;
  }

  .log-container {
    max-height: 500px;
    overflow-y: auto;
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 4px;

    pre {
      margin: 0;
      font-family: 'Courier New', Courier, monospace;
      font-size: 13px;
      line-height: 1.5;
      color: #333;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }

  .screenshot-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .screenshot-title {
      font-weight: bold;
      font-size: 14px;
    }
  }

  .screenshot-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
    background-color: #f5f5f5;
    border-radius: 4px;
    padding: 10px;

    .image-error {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      color: #909399;
      font-size: 14px;

      .el-icon {
        font-size: 48px;
      }
    }
  }

  .report-preview-container {
    .preview-toolbar {
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
      padding: 10px;
      background: #f5f5f5;
      border-radius: 4px;
    }
    
    .preview-content {
      border-radius: 4px;
      overflow: hidden;
      
      .preview-html-container {
        width: 100%;
        height: 70vh;
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow-y: auto;
        background: white;
        
        // 重置预览内容的样式，避免与父页面样式冲突
        :deep(*) {
          box-sizing: border-box;
        }
        
        // 确保预览内容的字体和样式正确显示
        :deep(body) {
          margin: 0;
          padding: 0;
        }
      }
    }
  }
}
</style>
