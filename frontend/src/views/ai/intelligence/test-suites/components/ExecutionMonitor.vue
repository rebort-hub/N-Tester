<template>
  <el-dialog
    v-model="visible"
    title="测试套件执行监控"
    width="900px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div v-loading="loading" class="monitor-container">
      <!-- 执行信息 -->
      <el-descriptions :column="2" border>
        <el-descriptions-item label="套件名称">
          {{ executionData.suite_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="执行名称">
          {{ executionData.execution_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="执行模式">
          <el-tag size="small">
            {{ executionData.execution_mode === 'headless' ? '无头模式' : '有头模式' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行状态">
          <el-tag :type="getStatusType(executionData.status)" size="small">
            {{ getStatusLabel(executionData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatDateTime(executionData.start_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="执行时长">
          {{ formatDuration(executionData.duration) }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 整体进度 -->
      <div class="progress-section">
        <div class="section-title">整体进度</div>
        <el-progress
          :percentage="overallProgress"
          :status="getProgressStatus(executionData.status)"
          :stroke-width="20"
        >
          <span class="progress-text">
            {{ executionData.completed_modules || 0 }} / {{ executionData.total_modules || 0 }} 模块
          </span>
        </el-progress>
      </div>

      <!-- 统计信息 -->
      <div class="stats-section">
        <div class="section-title">统计信息</div>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总模块数" :value="executionData.total_modules || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="已完成" :value="executionData.completed_modules || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="总用例数" :value="executionData.total_cases || 0" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="通过率" :value="passRate" suffix="%" :precision="1" />
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="8">
            <el-statistic title="通过用例" :value="executionData.passed_cases || 0">
              <template #suffix>
                <el-icon color="#67C23A"><CircleCheck /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="8">
            <el-statistic title="失败用例" :value="executionData.failed_cases || 0">
              <template #suffix>
                <el-icon color="#F56C6C"><CircleClose /></el-icon>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="8">
            <el-statistic title="失败模块" :value="executionData.failed_modules || 0">
              <template #suffix>
                <el-icon color="#E6A23C"><Warning /></el-icon>
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </div>

      <!-- 模块执行状态 -->
      <div class="modules-section">
        <div class="section-title">模块执行状态</div>
        <el-table :data="executionData.modules || []" border stripe max-height="400">
          <el-table-column prop="execution_order" label="顺序" width="80" align="center" />
          <el-table-column prop="module_name" label="模块名称" min-width="150" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getModuleStatusType(row.status)" size="small">
                {{ getModuleStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_cases" label="总用例" width="100" align="center" />
          <el-table-column prop="passed_cases" label="通过" width="100" align="center">
            <template #default="{ row }">
              <span style="color: #67C23A">{{ row.passed_cases || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failed_cases" label="失败" width="100" align="center">
            <template #default="{ row }">
              <span style="color: #F56C6C">{{ row.failed_cases || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时" width="100" align="center">
            <template #default="{ row }">
              {{ formatDuration(row.duration) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 错误信息 -->
      <div v-if="executionData.error_message" class="error-section">
        <el-alert
          title="执行错误"
          type="error"
          :description="executionData.error_message"
          :closable="false"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button
        v-if="executionData.status === 'running'"
        type="primary"
        @click="loadExecutionDetail"
      >
        刷新
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, CircleClose, Warning } from '@element-plus/icons-vue'
import { aiTestSuiteApi } from '/@/api/v1/ai_intelligence'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  executionId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const loading = ref(false)
const executionData = ref<any>({})
const pollingTimer = ref(null)

// 整体进度
const overallProgress = computed(() => {
  const total = executionData.value.total_modules || 0
  const completed = executionData.value.completed_modules || 0
  return total > 0 ? Math.round((completed / total) * 100) : 0
})

// 通过率
const passRate = computed(() => {
  const total = executionData.value.total_cases || 0
  const passed = executionData.value.passed_cases || 0
  return total > 0 ? (passed / total) * 100 : 0
})

// 加载执行详情
const loadExecutionDetail = async () => {
  if (!props.executionId) return
  
  loading.value = true
  try {
    const res = await aiTestSuiteApi.getExecutionDetail(props.executionId)
    if (res.code === 200) {
      executionData.value = res.data
      
      // 如果还在执行中，继续轮询
      if (res.data.status === 'running') {
        startPolling()
      } else {
        stopPolling()
      }
    }
  } catch (error) {
    ElMessage.error('加载执行详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 开始轮询
const startPolling = () => {
  stopPolling()
  pollingTimer.value = setInterval(() => {
    loadExecutionDetail()
  }, 2000)
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}

// 获取状态类型
const getStatusType = (status: string) => {
  const map = {
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const map = {
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

// 获取进度状态
const getProgressStatus = (status: string) => {
  const map = {
    running: undefined,
    completed: 'success',
    failed: 'exception'
  }
  return map[status]
}

// 获取模块状态类型
const getModuleStatusType = (status: string) => {
  const map = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

// 获取模块状态标签
const getModuleStatusLabel = (status: string) => {
  const map = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    failed: '失败'
  }
  return map[status] || status
}

// 格式化时长
const formatDuration = (seconds: number) => {
  if (!seconds) return '-'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}时${minutes}分${secs}秒`
  } else if (minutes > 0) {
    return `${minutes}分${secs}秒`
  } else {
    return `${secs}秒`
  }
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).replace(/\//g, '-')
  } catch (e) {
    return dateStr
  }
}

// 关闭
const handleClose = () => {
  stopPolling()
  visible.value = false
}

// 监听对话框打开
watch(() => props.modelValue, (val) => {
  if (val && props.executionId) {
    loadExecutionDetail()
  } else {
    stopPolling()
  }
})

// 组件卸载时停止轮询
watch(() => visible.value, (val) => {
  if (!val) {
    stopPolling()
  }
})
</script>

<style scoped lang="scss">
.monitor-container {
  padding: 10px 0;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  margin: 20px 0 10px;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.progress-section {
  margin-top: 20px;
}

.progress-text {
  font-size: 14px;
  margin-left: 10px;
}

.stats-section {
  margin-top: 20px;
}

.modules-section {
  margin-top: 20px;
}

.error-section {
  margin-top: 20px;
}
</style>
