<template>
  <div class="execution-monitor">
    <!-- 执行状态卡片 -->
    <el-card shadow="hover" class="status-card">
      <div class="status-header">
        <div class="status-info">
          <el-tag :type="getStatusTagType(executionStatus.status)" size="large">
            {{ getStatusName(executionStatus.status) }}
          </el-tag>
          <span class="execution-id">执行ID: {{ executionId }}</span>
        </div>
        <div class="status-actions">
          <el-button
            v-if="executionStatus.status === 'running'"
            type="danger"
            :icon="VideoPause"
            @click="handleStop"
            :loading="stopLoading"
          >
            停止执行
          </el-button>
          <el-button :icon="Refresh" @click="loadExecutionStatus">刷新</el-button>
          <el-button :icon="Close" @click="handleClose">关闭</el-button>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <el-progress
          :percentage="executionStatus.progress"
          :status="getProgressStatus(executionStatus.status)"
          :stroke-width="20"
        >
          <template #default="{ percentage }">
            <span class="progress-text">{{ percentage }}%</span>
          </template>
        </el-progress>
        <div class="progress-info">
          <span>当前步骤: {{ executionStatus.current_step || '准备中...' }}</span>
        </div>
      </div>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="statistics">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">总步骤数</div>
            <div class="stat-value">{{ executionStatus.total_steps }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">已完成</div>
            <div class="stat-value success">{{ executionStatus.completed_steps }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">失败</div>
            <div class="stat-value danger">{{ executionStatus.failed_steps }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-label">执行时长</div>
            <div class="stat-value">{{ formatDuration(executionStatus.start_time, executionStatus.end_time) }}</div>
          </div>
        </el-col>
      </el-row>

      <!-- 时间信息 -->
      <div class="time-info">
        <div class="time-item">
          <span class="time-label">开始时间:</span>
          <span class="time-value">{{ formatTime(executionStatus.start_time) }}</span>
        </div>
        <div class="time-item" v-if="executionStatus.end_time">
          <span class="time-label">结束时间:</span>
          <span class="time-value">{{ formatTime(executionStatus.end_time) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 执行日志 -->
    <el-card shadow="hover" class="logs-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>执行日志</span>
          <div class="header-actions">
            <el-switch v-model="autoScroll" active-text="自动滚动" />
            <el-button size="small" :icon="Download" @click="handleDownloadLogs">下载日志</el-button>
            <el-button size="small" :icon="Refresh" @click="loadExecutionLogs">刷新</el-button>
          </div>
        </div>
      </template>
      <div class="logs-container" ref="logsContainerRef">
        <pre class="logs-content">{{ executionLogs }}</pre>
      </div>
    </el-card>

    <!-- 执行详情 -->
    <el-card shadow="hover" class="details-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>执行详情</span>
          <el-button size="small" :icon="Document" @click="handleViewReport">查看报告</el-button>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="执行ID">{{ executionId }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTagType(executionStatus.status)">
            {{ getStatusName(executionStatus.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行引擎">{{ executionDetails.engine_type }}</el-descriptions-item>
        <el-descriptions-item label="浏览器类型">{{ executionDetails.browser_type }}</el-descriptions-item>
        <el-descriptions-item label="总步骤数">{{ executionStatus.total_steps }}</el-descriptions-item>
        <el-descriptions-item label="通过步骤数">{{ executionStatus.completed_steps }}</el-descriptions-item>
        <el-descriptions-item label="失败步骤数">{{ executionStatus.failed_steps }}</el-descriptions-item>
        <el-descriptions-item label="执行时长">
          {{ formatDuration(executionStatus.start_time, executionStatus.end_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="executionDetails.error_message">
          <el-alert type="error" :closable="false">
            {{ executionDetails.error_message }}
          </el-alert>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPause, Refresh, Close, Download, Document } from '@element-plus/icons-vue'
import { useUiAutomationApi } from '/@/api/v1/ui_automation'
import dayjs from 'dayjs'
import duration from 'dayjs/plugin/duration'

dayjs.extend(duration)
const { uiExecutionApi } = useUiAutomationApi()

const props = defineProps<{
  executionId: number
}>()

const emit = defineEmits(['close'])

// 初始化 router
const router = useRouter()

// 执行状态
const executionStatus = reactive({
  id: props.executionId,
  status: 'running',
  progress: 0,
  current_step: '',
  start_time: null,
  end_time: null,
  total_steps: 0,
  completed_steps: 0,
  failed_steps: 0
})

// 执行详情
const executionDetails = reactive({
  engine_type: '',
  browser_type: '',
  error_message: ''
})

// 执行日志
const executionLogs = ref('')
const logsContainerRef = ref()
const autoScroll = ref(true)

// 停止加载
const stopLoading = ref(false)

// 轮询定时器
let statusTimer: any = null
let logsTimer: any = null

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

// 获取进度条状态
const getProgressStatus = (status: string) => {
  if (status === 'success') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

// 格式化时间
const formatTime = (time: any) => {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 格式化时长
const formatDuration = (startTime: any, endTime: any) => {
  if (!startTime) return '-'
  const end = endTime ? dayjs(endTime) : dayjs()
  const start = dayjs(startTime)
  const diff = end.diff(start)
  const dur = dayjs.duration(diff)
  
  const hours = Math.floor(dur.asHours())
  const minutes = dur.minutes()
  const seconds = dur.seconds()
  
  if (hours > 0) {
    return `${hours}小时${minutes}分${seconds}秒`
  } else if (minutes > 0) {
    return `${minutes}分${seconds}秒`
  } else {
    return `${seconds}秒`
  }
}

// 加载执行状态
const loadExecutionStatus = async () => {
  try {
    const res = await uiExecutionApi.getStatus(props.executionId)
    Object.assign(executionStatus, res.data)
    
    // 如果执行完成，停止轮询
    if (executionStatus.status !== 'running') {
      stopPolling()
      loadExecutionDetails()
    }
  } catch (error) {
    console.error('加载执行状态失败:', error)
  }
}

// 加载执行详情
const loadExecutionDetails = async () => {
  try {
    const res = await uiExecutionApi.get(props.executionId)
    Object.assign(executionDetails, res.data)
  } catch (error) {
    console.error('加载执行详情失败:', error)
  }
}

// 加载执行日志
const loadExecutionLogs = async () => {
  try {
    const res = await uiExecutionApi.getLogs(props.executionId)
    executionLogs.value = res.data.logs || ''
    
    // 自动滚动到底部
    if (autoScroll.value) {
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('加载执行日志失败:', error)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (logsContainerRef.value) {
    logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
  }
}

// 开始轮询
const startPolling = () => {
  // 轮询状态（每2秒）
  statusTimer = setInterval(() => {
    loadExecutionStatus()
  }, 2000)
  
  // 轮询日志（每3秒）
  logsTimer = setInterval(() => {
    loadExecutionLogs()
  }, 3000)
}

// 停止轮询
const stopPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  if (logsTimer) {
    clearInterval(logsTimer)
    logsTimer = null
  }
}

// 停止执行
const handleStop = async () => {
  stopLoading.value = true
  try {
    await uiExecutionApi.stop(props.executionId)
    ElMessage.success('停止执行成功')
    loadExecutionStatus()
  } catch (error) {
    ElMessage.error('停止执行失败')
    console.error(error)
  } finally {
    stopLoading.value = false
  }
}

// 下载日志
const handleDownloadLogs = () => {
  const blob = new Blob([executionLogs.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `execution_${props.executionId}_logs.txt`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('日志已下载')
}

// 查看报告
const handleViewReport = () => {
  // 关闭当前对话框
  emit('close')
  
  // 跳转到测试报告页面
  router.push({
    path: '/testing/ui-automation/report',
    query: {
      execution_id: props.executionId
    }
  })
}

// 关闭
const handleClose = () => {
  emit('close')
}

// 监听自动滚动变化
watch(autoScroll, (newVal) => {
  if (newVal) {
    scrollToBottom()
  }
})

// 初始化
onMounted(() => {
  loadExecutionStatus()
  loadExecutionDetails()
  loadExecutionLogs()
  startPolling()
})

// 清理
onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="scss">
.execution-monitor {
  .status-card {
    .status-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;

      .status-info {
        display: flex;
        align-items: center;
        gap: 15px;

        .execution-id {
          color: #909399;
          font-size: 14px;
        }
      }

      .status-actions {
        display: flex;
        gap: 10px;
      }
    }

    .progress-section {
      margin-bottom: 20px;

      .progress-text {
        font-size: 14px;
        font-weight: bold;
      }

      .progress-info {
        margin-top: 10px;
        text-align: center;
        color: #606266;
        font-size: 14px;
      }
    }

    .statistics {
      margin-bottom: 20px;

      .stat-item {
        text-align: center;
        padding: 15px;
        background-color: #f5f7fa;
        border-radius: 4px;

        .stat-label {
          font-size: 12px;
          color: #909399;
          margin-bottom: 8px;
        }

        .stat-value {
          font-size: 24px;
          font-weight: bold;
          color: #303133;

          &.success {
            color: #67c23a;
          }

          &.danger {
            color: #f56c6c;
          }
        }
      }
    }

    .time-info {
      display: flex;
      gap: 30px;
      padding-top: 15px;
      border-top: 1px solid #ebeef5;

      .time-item {
        .time-label {
          color: #909399;
          font-size: 13px;
          margin-right: 8px;
        }

        .time-value {
          color: #606266;
          font-size: 13px;
        }
      }
    }
  }

  .logs-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        gap: 10px;
        align-items: center;
      }
    }

    .logs-container {
      max-height: 400px;
      overflow-y: auto;
      background-color: #1e1e1e;
      border-radius: 4px;
      padding: 15px;

      .logs-content {
        color: #d4d4d4;
        font-family: 'Courier New', Courier, monospace;
        font-size: 12px;
        line-height: 1.6;
        margin: 0;
        white-space: pre-wrap;
        word-wrap: break-word;
      }
    }
  }

  .details-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  }
}
</style>
