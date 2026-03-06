<template>
  <el-dialog
    v-model="visible"
    title="执行记录"
    width="1200px"
    @close="handleClose"
  >
    <div v-loading="loading">
      <!-- 筛选条件 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="执行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 执行记录列表 -->
      <el-table :data="tableData" border stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="execution_name" label="执行名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="execution_mode" label="执行模式" width="120">
          <template #default="{ row }">
            <el-tag size="small">
              {{ row.execution_mode === 'headless' ? '无头模式' : '有头模式' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="模块" width="120" align="center">
          <template #default="{ row }">
            {{ row.completed_modules }} / {{ row.total_modules }}
          </template>
        </el-table-column>
        <el-table-column label="用例" width="120" align="center">
          <template #default="{ row }">
            <span style="color: #67C23A">{{ row.passed_cases }}</span> /
            <span style="color: #F56C6C">{{ row.failed_cases }}</span> /
            {{ row.total_cases }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleViewDetail(row)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="handleQuery"
        @current-change="handleQuery"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>

    <!-- 执行详情对话框 -->
    <ExecutionMonitor
      v-model="detailVisible"
      :execution-id="currentExecutionId"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { aiTestSuiteApi } from '/@/api/v1/ai_intelligence'
import ExecutionMonitor from './ExecutionMonitor.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  suiteId: {
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
const tableData = ref([])

const queryForm = reactive({
  status: null
})

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

const detailVisible = ref(false)
const currentExecutionId = ref(null)

// 加载执行记录
const loadExecutions = async () => {
  if (!props.suiteId) return
  
  loading.value = true
  try {
    const params = {
      suite_id: props.suiteId,
      status: queryForm.status,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res = await aiTestSuiteApi.getExecutions(params)
    if (res.code === 200) {
      tableData.value = res.data.items || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('加载执行记录失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 查询
const handleQuery = () => {
  pagination.page = 1
  loadExecutions()
}

// 重置
const handleReset = () => {
  queryForm.status = null
  handleQuery()
}

// 查看详情
const handleViewDetail = (row: any) => {
  currentExecutionId.value = row.id
  detailVisible.value = true
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
  visible.value = false
}

// 监听对话框打开
watch(() => props.modelValue, (val) => {
  if (val && props.suiteId) {
    loadExecutions()
  }
})
</script>

<style scoped lang="scss">
.query-form {
  margin-bottom: 20px;
}
</style>
