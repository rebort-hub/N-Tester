<template>
  <div class="notification-histories">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>通知历史</span>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="queryParams" ref="queryRef" :inline="true" class="search-form">
        <el-form-item label="通知配置" prop="config_id">
          <el-select
            v-model="queryParams.config_id"
            placeholder="请选择通知配置"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="config in configOptions"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="发送状态" prop="status">
          <el-select
            v-model="queryParams.status"
            placeholder="请选择发送状态"
            clearable
            style="width: 120px"
          >
            <el-option label="待发送" value="pending" />
            <el-option label="发送成功" value="success" />
            <el-option label="发送失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围" prop="days">
          <el-select
            v-model="queryParams.days"
            placeholder="请选择时间范围"
            clearable
            style="width: 120px"
          >
            <el-option label="今天" :value="1" />
            <el-option label="最近3天" :value="3" />
            <el-option label="最近7天" :value="7" />
            <el-option label="最近30天" :value="30" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetQuery">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 批量操作按钮 -->
      <div class="table-header" style="margin-bottom: 16px;">
        <el-button 
          type="danger" 
          :disabled="multiple"
          @click="handleBatchDelete"
          v-auth="'notifications:history:remove'"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="historyList"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="通知标题" prop="title" min-width="150" />
        <el-table-column label="通知内容" prop="content" min-width="200">
          <template #default="scope">
            <div class="content-cell">
              {{ scope.row.content }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="接收者" prop="recipient" width="120" />
        <el-table-column label="发送状态" prop="status" width="100" align="center">
          <template #default="scope">
            <el-tag
              :type="getStatusTagType(scope.row.status)"
              size="small"
            >
              {{ getStatusLabel(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="发送时间" prop="sent_at" width="160" align="center">
          <template #default="scope">
            <span>{{ scope.row.sent_at ? formatDateTime(new Date(scope.row.sent_at * 1000)) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="creation_date" width="160" align="center">
          <template #default="scope">
            <span>{{ formatDateTime(scope.row.creation_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="240" class-name="small-padding fixed-width">
          <template #default="scope">
            <div class="button-group">
              <el-button
                type="primary"
                size="small"
                @click="handleDetail(scope.row)"
                v-auth="'notifications:history:detail'"
              >
                查看详情
              </el-button>
              <el-button
                type="warning"
                size="small"
                @click="handleResend(scope.row)"
                v-auth="'notifications:history:resend'"
                v-if="scope.row.status === 'failed'"
              >
                重新发送
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
                v-auth="'notifications:history:remove'"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-show="total > 0"
        :total="total"
        v-model:current-page="queryParams.pageNum"
        v-model:page-size="queryParams.pageSize"
        @size-change="getList"
        @current-change="getList"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
      />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog title="通知详情" v-model="detailOpen" width="800px" append-to-body>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="通知标题">
          {{ detailData.title }}
        </el-descriptions-item>
        <el-descriptions-item label="发送状态">
          <el-tag :type="getStatusTagType(detailData.status)" size="small">
            {{ getStatusLabel(detailData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="接收者">
          {{ detailData.recipient || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="发送时间">
          {{ detailData.sent_at ? formatDateTime(new Date(detailData.sent_at * 1000)) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">
          {{ formatDateTime(detailData.creation_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="通知内容" :span="2">
          <div class="content-detail">
            {{ detailData.content }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="错误信息" :span="2" v-if="detailData.error_message">
          <div class="error-message">
            {{ detailData.error_message }}
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="响应数据" :span="2" v-if="detailData.response_data">
          <el-input
            type="textarea"
            :rows="6"
            :value="JSON.stringify(detailData.response_data, null, 2)"
            readonly
          />
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailOpen = false">关 闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, View, Delete } from '@element-plus/icons-vue'
import { 
  notificationHistoryApi, 
  notificationConfigApi,
  notificationSendApi,
  type NotificationHistory,
  type NotificationConfig 
} from '/@/api/v1/notifications'
import { formatDateTime } from '/@/utils/formatTime'

// 响应式数据
const loading = ref(true)
const total = ref(0)
const historyList = ref<NotificationHistory[]>([])
const configOptions = ref<NotificationConfig[]>([])
const detailOpen = ref(false)
const detailData = ref<NotificationHistory>({} as NotificationHistory)
const ids = ref<number[]>([])
const single = ref(true)
const multiple = ref(true)

// 查询参数
const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  config_id: undefined as number | undefined,
  status: '',
  days: undefined as number | undefined
})

// 获取历史列表
const getList = async () => {
  loading.value = true
  try {
    const params = {
      ...queryParams,
      skip: (queryParams.pageNum - 1) * queryParams.pageSize,
      limit: queryParams.pageSize
    }
    const response = await notificationHistoryApi.getHistories(params)
    historyList.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('获取通知历史失败:', error)
    ElMessage.error('获取通知历史失败')
  } finally {
    loading.value = false
  }
}

// 获取配置选项
const getConfigOptions = async () => {
  try {
    const response = await notificationConfigApi.getConfigs({ is_active: true })
    configOptions.value = response.data.items || []
  } catch (error) {
    console.error('获取配置选项失败:', error)
  }
}

// 搜索
const handleQuery = () => {
  queryParams.pageNum = 1
  getList()
}

// 重置搜索
const resetQuery = () => {
  queryParams.pageNum = 1
  queryParams.pageSize = 10
  queryParams.config_id = undefined
  queryParams.status = ''
  queryParams.days = undefined
  getList()
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    success: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

// 获取状态标签文本
const getStatusLabel = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待发送',
    success: '发送成功',
    failed: '发送失败'
  }
  return statusMap[status] || status
}

// 查看详情
const handleDetail = (row: NotificationHistory) => {
  detailData.value = { ...row }
  detailOpen.value = true
}

// 重新发送
const handleResend = async (row: NotificationHistory) => {
  try {
    await ElMessageBox.confirm('确认要重新发送这条通知吗？')
    await notificationSendApi.sendNotification({
      config_id: row.config_id,
      title: row.title,
      content: row.content,
      recipient: row.recipient
    })
    ElMessage.success('重新发送成功')
    await getList()
  } catch (error) {
    console.error('重新发送失败:', error)
    ElMessage.error('重新发送失败')
  }
}

// 多选框选中数据
const handleSelectionChange = (selection: NotificationHistory[]) => {
  ids.value = selection.map(item => item.id!)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

// 删除按钮操作
const handleDelete = async (row: NotificationHistory) => {
  try {
    await ElMessageBox.confirm(`是否确认删除这条通知历史记录？`)
    
    try {
      await notificationHistoryApi.deleteHistory(row.id!)
      ElMessage.success('删除成功')
      await getList()
    } catch (error: any) {
      console.error('删除历史记录失败:', error)
      if (error?.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('删除失败')
      }
    }
  } catch (error) {
    // 用户取消确认对话框，不显示错误信息
    console.log('用户取消删除操作')
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (ids.value.length === 0) {
    ElMessage.warning('请选择要删除的历史记录')
    return
  }
  
  try {
    await ElMessageBox.confirm(`是否确认删除选中的 ${ids.value.length} 条历史记录？`)
    
    try {
      await notificationHistoryApi.batchDeleteHistories(ids.value)
      ElMessage.success(`成功删除 ${ids.value.length} 条历史记录`)
      await getList()
    } catch (error: any) {
      console.error('批量删除失败:', error)
      if (error?.message) {
        ElMessage.error(error.message)
      } else {
        ElMessage.error('批量删除失败')
      }
    }
  } catch (error) {
    // 用户取消确认对话框，不显示错误信息
    console.log('用户取消删除操作')
  }
}

// 初始化
onMounted(() => {
  getConfigOptions()
  getList()
})
</script>

<style scoped>
.notification-histories {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.content-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-detail {
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

.error-message {
  color: #f56c6c;
  white-space: pre-wrap;
  word-break: break-all;
}

.dialog-footer {
  text-align: right;
}
</style>
<style scoped>
.button-group {
  display: flex;
  gap: 4px;
  justify-content: center;
  align-items: center;
  white-space: nowrap;
}

.button-group .el-button {
  margin: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 16px;
}
</style>