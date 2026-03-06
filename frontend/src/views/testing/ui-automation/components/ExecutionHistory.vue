<template>
  <div class="execution-history">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-select v-model="searchStatus" placeholder="执行状态" clearable style="width: 150px" @change="handleSearch">
        <el-option label="执行中" value="running" />
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failed" />
        <el-option label="已停止" value="stopped" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="width: 300px"
        @change="handleSearch"
      />
      <el-button type="primary" :icon="Histogram" @click="handleViewStatistics">查看统计</el-button>
      <el-button type="danger" :icon="Delete" @click="handleBatchDelete" :disabled="selectedExecutions.length === 0">批量删除</el-button>
      <el-button :icon="Refresh" @click="loadExecutionList">刷新</el-button>
    </div>

    <!-- 执行记录列表 -->
    <el-table :data="executionList" v-loading="loading" border stripe style="margin-top: 15px" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="执行ID" width="100" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)">
            {{ getStatusName(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="engine_type" label="执行引擎" width="120">
        <template #default="{ row }">
          <el-tag>{{ row.engine_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="browser_type" label="浏览器" width="100">
        <template #default="{ row }">
          <el-tag type="success">{{ row.browser_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="步骤统计" width="200">
        <template #default="{ row }">
          <div class="steps-stats">
            <span class="stat-item">总数: {{ row.total_steps }}</span>
            <span class="stat-item success">通过: {{ row.passed_steps }}</span>
            <span class="stat-item danger">失败: {{ row.failed_steps }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="执行时长" width="120">
        <template #default="{ row }">
          {{ formatDuration(row.duration) }}
        </template>
      </el-table-column>
      <el-table-column label="开始时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.start_time) }}
        </template>
      </el-table-column>
      <el-table-column label="结束时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.end_time) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="450" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleViewDetails(row)">查看详情</el-button>
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
              导出报告<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="{action: 'preview', row}">预览报告</el-dropdown-item>
                <el-dropdown-item :command="{action: 'download', row}">下载HTML</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="danger" size="small" @click="handleDelete(row)" style="margin-left: 8px;">删除</el-button>
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
      @size-change="loadExecutionList"
      @current-change="loadExecutionList"
      style="margin-top: 15px; justify-content: flex-end"
    />

    <!-- 执行详情对话框 -->
    <el-dialog
      v-model="detailsDialogVisible"
      title="执行详情"
      width="900px"
      :close-on-click-modal="false"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">{{ currentExecution.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTagType(currentExecution.status)">
            {{ getStatusName(currentExecution.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行引擎">{{ currentExecution.engine_type }}</el-descriptions-item>
        <el-descriptions-item label="浏览器类型">{{ currentExecution.browser_type }}</el-descriptions-item>
        <el-descriptions-item label="总步骤数">{{ currentExecution.total_steps }}</el-descriptions-item>
        <el-descriptions-item label="通过步骤数">{{ currentExecution.passed_steps }}</el-descriptions-item>
        <el-descriptions-item label="失败步骤数">{{ currentExecution.failed_steps }}</el-descriptions-item>
        <el-descriptions-item label="执行时长">{{ formatDuration(currentExecution.duration) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ formatDateTime(currentExecution.start_time) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ formatDateTime(currentExecution.end_time) }}</el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="currentExecution.error_message">
          <el-alert type="error" :closable="false">
            {{ currentExecution.error_message }}
          </el-alert>
        </el-descriptions-item>
        <el-descriptions-item label="截图" :span="2" v-if="currentExecution.screenshots && currentExecution.screenshots.length > 0">
          <div class="screenshots-container">
            <div 
              v-for="(screenshot, index) in currentExecution.screenshots"
              :key="index"
              class="screenshot-item"
            >
              <el-image
                :src="screenshot.screenshot"
                :preview-src-list="currentExecution.screenshots.map(s => s.screenshot)"
                :initial-index="index"
                fit="cover"
                style="width: 100px; height: 100px; cursor: pointer"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><Picture /></el-icon>
                    <span>加载失败</span>
                  </div>
                </template>
              </el-image>
              <div class="screenshot-info">
                <div class="step-info">步骤 {{ screenshot.step_number }}</div>
                <div class="step-desc">{{ screenshot.step_description }}</div>
              </div>
            </div>
          </div>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 日志查看对话框 -->
    <el-dialog
      v-model="logsDialogVisible"
      title="执行日志"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="logs-container">
        <div class="logs-actions">
          <el-button type="primary" size="small" :icon="Download" @click="handleDownloadLogs">下载日志</el-button>
          <el-button size="small" :icon="CopyDocument" @click="handleCopyLogs">复制日志</el-button>
        </div>
        <pre class="logs-content">{{ currentLogs }}</pre>
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

    <!-- 统计图表对话框 -->
    <el-dialog
      v-model="statisticsDialogVisible"
      title="执行统计"
      width="1000px"
      :close-on-click-modal="false"
    >
      <div class="statistics-container">
        <!-- 统计卡片 -->
        <el-row :gutter="20" style="margin-bottom: 20px">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card-wrapper total">
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label">总执行次数</div>
                  <div class="stat-value">{{ statistics.total_executions }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card-wrapper success">
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon><CircleCheck /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label">成功次数</div>
                  <div class="stat-value">{{ statistics.success_count }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card-wrapper danger">
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon><CircleClose /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label">失败次数</div>
                  <div class="stat-value">{{ statistics.failed_count }}</div>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card-wrapper rate">
              <div class="stat-card">
                <div class="stat-icon">
                  <el-icon><TrendCharts /></el-icon>
                </div>
                <div class="stat-content">
                  <div class="stat-label">成功率</div>
                  <div class="stat-value">{{ statistics.success_rate }}%</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 图表 -->
        <el-card shadow="hover">
          <div ref="chartRef" style="width: 100%; height: 400px"></div>
        </el-card>
      </div>
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Histogram, Refresh, Download, CopyDocument, Document, CircleCheck, CircleClose, TrendCharts, Picture, ArrowDown, Delete } from '@element-plus/icons-vue'
import { uiExecutionApi } from '/@/api/v1/ui_automation'
import { formatDateTime } from '/@/utils/formatTime'
import * as echarts from 'echarts'

const props = defineProps<{
  uiProjectId: number
}>()

// 搜索
const searchStatus = ref('')
const dateRange = ref([])

// 表格数据
const executionList = ref([])
const loading = ref(false)
const selectedExecutions = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 详情对话框
const detailsDialogVisible = ref(false)
const currentExecution = ref<any>({})

// 日志对话框
const logsDialogVisible = ref(false)
const currentLogs = ref('')

// 截图对话框
const screenshotsDialogVisible = ref(false)
const currentScreenshots = ref<any[]>([])

// 判断是否有截图
const hasScreenshots = (row: any) => {
  return row.screenshots && Array.isArray(row.screenshots) && row.screenshots.length > 0
}

// 统计对话框
const statisticsDialogVisible = ref(false)
const statistics = reactive({
  total_executions: 0,
  success_count: 0,
  failed_count: 0,
  success_rate: 0,
  avg_duration: 0,
  trend_data: []
})
const chartRef = ref()
let chartInstance: any = null

// 报告预览对话框
const reportPreviewDialogVisible = ref(false)
const currentReportHtml = ref('')
const currentReportRow = ref<any>(null)
const previewContainer = ref<HTMLDivElement>()

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const types: any = {
    running: 'warning',
    success: 'success',
    failed: 'danger',
    stopped: 'info'
  }
  return types[status] || ''
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

// 格式化时长
const formatDuration = (duration: number) => {
  if (!duration) return '-'
  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}小时${minutes % 60}分${seconds % 60}秒`
  } else if (minutes > 0) {
    return `${minutes}分${seconds % 60}秒`
  } else {
    return `${seconds}秒`
  }
}

// 加载执行列表
const loadExecutionList = async () => {
  loading.value = true
  try {
    const params: any = {
      ui_project_id: props.uiProjectId,
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchStatus.value) {
      params.status = searchStatus.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      // 格式化日期为 YYYY-MM-DD 格式
      const startDate = new Date(dateRange.value[0])
      const endDate = new Date(dateRange.value[1])
      
      params.start_date = startDate.toISOString().split('T')[0]
      params.end_date = endDate.toISOString().split('T')[0]
    }
    const res = await uiExecutionApi.list(params)
    executionList.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载执行列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadExecutionList()
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedExecutions.value = selection
}

// 查看详情
const handleViewDetails = async (row: any) => {
  try {
    const res = await uiExecutionApi.get(row.id)
    currentExecution.value = res.data
    detailsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载执行详情失败')
    console.error(error)
  }
}

// 查看日志
const handleViewLogs = async (row: any) => {
  try {
    const res = await uiExecutionApi.getLogs(row.id)
    currentLogs.value = res.data.logs || ''
    logsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载执行日志失败')
    console.error(error)
  }
}

// 下载日志
const handleDownloadLogs = () => {
  const blob = new Blob([currentLogs.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `execution_logs.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('日志已下载')
}

// 复制日志
const handleCopyLogs = async () => {
  try {
    // 优先使用现代 Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(currentLogs.value)
      ElMessage.success('日志已复制到剪贴板')
    } else {
      // 降级方案：使用传统的 document.execCommand
      const textarea = document.createElement('textarea')
      textarea.value = currentLogs.value
      textarea.style.position = 'fixed'
      textarea.style.opacity = '0'
      document.body.appendChild(textarea)
      textarea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          ElMessage.success('日志已复制到剪贴板')
        } else {
          ElMessage.error('复制失败')
        }
      } catch (err) {
        ElMessage.error('复制失败')
      } finally {
        document.body.removeChild(textarea)
      }
    }
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
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
    await handleExportReport(row)
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
const handleExportReport = async (row: any) => {
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

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该执行记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiExecutionApi.delete(row.id)
      ElMessage.success('删除成功')
      loadExecutionList()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedExecutions.value.length === 0) {
    ElMessage.warning('请先选择要删除的执行记录')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedExecutions.value.length} 个执行记录吗？此操作不可恢复。`,
    '批量删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      dangerouslyUseHTMLString: true
    }
  ).then(async () => {
    const loading = ElLoading.service({
      lock: true,
      text: `正在删除 ${selectedExecutions.value.length} 个执行记录...`,
      background: 'rgba(0, 0, 0, 0.7)'
    })
    
    try {
      let successCount = 0
      let failCount = 0
      const errors: string[] = []
      
      // 逐个删除
      for (const execution of selectedExecutions.value) {
        try {
          await uiExecutionApi.delete(execution.id)
          successCount++
        } catch (error: any) {
          failCount++
          errors.push(`执行ID ${execution.id}: ${error?.response?.data?.detail || '删除失败'}`)
        }
      }
      
      loading.close()
      
      if (failCount === 0) {
        ElMessage.success(`成功删除 ${successCount} 个执行记录`)
      } else {
        const errorMsg = errors.length > 0 ? `\n失败详情：\n${errors.join('\n')}` : ''
        ElMessageBox.alert(
          `删除完成：成功 ${successCount} 个，失败 ${failCount} 个${errorMsg}`,
          '批量删除结果',
          {
            confirmButtonText: '确定',
            type: failCount > 0 ? 'warning' : 'success'
          }
        )
      }
      
      // 刷新列表
      loadExecutionList()
      // 清空选择
      selectedExecutions.value = []
    } catch (error) {
      loading.close()
      ElMessage.error('批量删除失败')
      console.error(error)
    }
  })
}

// 查看统计
const handleViewStatistics = async () => {
  try {
    const res = await uiExecutionApi.statistics({
      ui_project_id: props.uiProjectId
    })
    Object.assign(statistics, res.data)
    statisticsDialogVisible.value = true
    
    // 等待DOM更新后初始化图表
    await nextTick()
    initChart()
  } catch (error) {
    ElMessage.error('加载统计数据失败')
    console.error(error)
  }
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(chartRef.value)
  
  // 确保有趋势数据
  const trendData = statistics.trend_data || []
  
  const option = {
    title: {
      text: '执行趋势'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['成功', '失败']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendData.map((item: any) => item.date)
    },
    yAxis: {
      type: 'value',
      minInterval: 1
    },
    series: [
      {
        name: '成功',
        type: 'line',
        data: trendData.map((item: any) => item.success_count || 0),
        smooth: true,
        itemStyle: {
          color: '#67c23a'
        },
        areaStyle: {
          color: 'rgba(103, 194, 58, 0.2)'
        }
      },
      {
        name: '失败',
        type: 'line',
        data: trendData.map((item: any) => item.failed_count || 0),
        smooth: true,
        itemStyle: {
          color: '#f56c6c'
        },
        areaStyle: {
          color: 'rgba(245, 108, 108, 0.2)'
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
}

// 初始化
onMounted(() => {
  loadExecutionList()
})
</script>

<style scoped lang="scss">
.execution-history {
  .toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .steps-stats {
    display: flex;
    gap: 10px;
    font-size: 12px;

    .stat-item {
      &.success {
        color: #67c23a;
      }

      &.danger {
        color: #f56c6c;
      }
    }
  }

  .screenshots-container {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    
    .screenshot-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      
      .screenshot-info {
        text-align: center;
        font-size: 12px;
        
        .step-info {
          font-weight: bold;
          color: #409eff;
        }
        
        .step-desc {
          color: #666;
          max-width: 100px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
      
      .image-error {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100px;
        height: 100px;
        background: #f5f5f5;
        border: 1px dashed #ddd;
        border-radius: 4px;
        color: #999;
        font-size: 12px;
        
        .el-icon {
          font-size: 24px;
          margin-bottom: 4px;
        }
      }
    }
  }

  .logs-container {
    .logs-actions {
      margin-bottom: 15px;
      display: flex;
      gap: 10px;
    }

    .logs-content {
      background-color: #1e1e1e;
      color: #d4d4d4;
      padding: 15px;
      border-radius: 4px;
      max-height: 500px;
      overflow-y: auto;
      font-family: 'Courier New', Courier, monospace;
      font-size: 12px;
      line-height: 1.6;
      margin: 0;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
  }

  .statistics-container {
    .stat-card-wrapper {
      border: none;
      border-radius: 12px;
      overflow: hidden;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
      }

      &.total {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        
        :deep(.el-card__body) {
          padding: 0;
        }
      }

      &.success {
        background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
        
        :deep(.el-card__body) {
          padding: 0;
        }
      }

      &.danger {
        background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
        
        :deep(.el-card__body) {
          padding: 0;
        }
      }

      &.rate {
        background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
        
        :deep(.el-card__body) {
          padding: 0;
        }
      }
    }

    .stat-card {
      display: flex;
      align-items: center;
      padding: 25px 20px;
      gap: 20px;

      .stat-icon {
        width: 60px;
        height: 60px;
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 30px;
        color: white;
        flex-shrink: 0;
      }

      .stat-content {
        flex: 1;
        color: white;
      }

      .stat-label {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 8px;
      }

      .stat-value {
        font-size: 32px;
        font-weight: bold;
      }
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

