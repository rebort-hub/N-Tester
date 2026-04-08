<template>
  <div class="task-notification-settings">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>任务通知设置</span>
          <el-button 
            type="primary" 
            @click="handleAdd"
            v-auth="'notifications:task:add'"
          >
            <el-icon><Plus /></el-icon>
            新增设置
          </el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="queryParams" ref="queryRef" :inline="true" class="search-form">
        <el-form-item label="任务ID" prop="task_id">
          <el-input
            v-model.number="queryParams.task_id"
            placeholder="请输入任务ID"
            clearable
            style="width: 150px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select
            v-model="queryParams.task_type"
            placeholder="请选择任务类型"
            clearable
            style="width: 120px"
          >
            <el-option label="API测试" value="API" />
            <el-option label="UI测试" value="UI" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知配置" prop="notification_config_id">
          <el-select
            v-model="queryParams.notification_config_id"
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
          v-auth="'notifications:task:remove'"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="settingList"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="任务ID" prop="task_id" width="100" align="center" />
        <el-table-column label="任务类型" prop="task_type" width="100" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.task_type === 'API' ? 'primary' : 'success'"
              size="small"
            >
              {{ scope.row.task_type === 'API' ? 'API测试' : 'UI测试' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="通知配置" prop="notification_config_name" min-width="150">
          <template #default="scope">
            {{ getConfigName(scope.row.notification_config_id) }}
          </template>
        </el-table-column>
        <el-table-column label="启用状态" prop="is_enabled" width="100" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_enabled"
              @change="handleStatusChange(scope.row)"
              v-auth="'notifications:task:edit'"
            />
          </template>
        </el-table-column>
        <el-table-column label="成功通知" prop="notify_on_success" width="100" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.notify_on_success ? 'success' : 'info'"
              size="small"
            >
              {{ scope.row.notify_on_success ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="失败通知" prop="notify_on_failure" width="100" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.notify_on_failure ? 'danger' : 'info'"
              size="small"
            >
              {{ scope.row.notify_on_failure ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="creation_date" width="160" align="center">
          <template #default="scope">
            <span>{{ formatDateTime(scope.row.creation_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="140" class-name="small-padding fixed-width">
          <template #default="scope">
            <div class="button-group">
              <el-button
                type="primary"
                size="small"
                @click="handleUpdate(scope.row)"
                v-auth="'notifications:task:edit'"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
                v-auth="'notifications:task:remove'"
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

    <!-- 添加或修改设置对话框 -->
    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="settingRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="任务ID" prop="task_id">
          <el-input-number
            v-model="form.task_id"
            placeholder="请输入任务ID"
            :min="1"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select
            v-model="form.task_type"
            placeholder="请选择任务类型"
            style="width: 100%"
          >
            <el-option label="API测试" value="API" />
            <el-option label="UI测试" value="UI" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知配置" prop="notification_config_id">
          <el-select
            v-model="form.notification_config_id"
            placeholder="请选择通知配置"
            style="width: 100%"
          >
            <el-option
              v-for="config in configOptions"
              :key="config.id"
              :label="config.name"
              :value="config.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="通知设置">
          <el-checkbox v-model="form.notify_on_success">成功时通知</el-checkbox>
          <el-checkbox v-model="form.notify_on_failure">失败时通知</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.is_enabled">启用设置</el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { Plus, Search, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import { 
  useTaskNotificationApi, 
  useNotificationConfigApi,
  type TaskNotificationSetting,
  type TaskNotificationSettingCreate,
  type NotificationConfig 
} from '/@/api/v1/notifications'
import { formatDateTime } from '/@/utils/formatTime'

const taskNotificationApi = useTaskNotificationApi()
const notificationConfigApi = useNotificationConfigApi()

// 响应式数据
const loading = ref(true)
const ids = ref<number[]>([])
const single = ref(true)
const multiple = ref(true)
const total = ref(0)
const settingList = ref<TaskNotificationSetting[]>([])
const configOptions = ref<NotificationConfig[]>([])
const title = ref('')
const open = ref(false)
const settingRef = ref<FormInstance>()

// 查询参数
const queryParams = reactive({
  pageNum: 1,
  pageSize: 10,
  task_id: undefined as number | undefined,
  task_type: '',
  notification_config_id: undefined as number | undefined
})

// 表单数据
const form = ref<TaskNotificationSettingCreate & { id?: number }>({
  task_id: 1,
  task_type: 'API',
  notification_config_id: undefined as any,
  is_enabled: true,
  notify_on_success: false,
  notify_on_failure: true
})

// 表单验证规则
const rules = {
  task_id: [
    { required: true, message: '任务ID不能为空', trigger: 'blur' }
  ],
  task_type: [
    { required: true, message: '任务类型不能为空', trigger: 'change' }
  ],
  notification_config_id: [
    { required: true, message: '通知配置不能为空', trigger: 'change' }
  ]
}

// 获取设置列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {
      skip: (queryParams.pageNum - 1) * queryParams.pageSize,
      limit: queryParams.pageSize
    }
    
    // 只有当参数有值时才添加到请求中
    if (queryParams.task_id !== undefined) {
      params.task_id = queryParams.task_id
    }
    if (queryParams.task_type) {
      params.task_type = queryParams.task_type
    }
    if (queryParams.notification_config_id !== undefined) {
      params.notification_config_id = queryParams.notification_config_id
    }
    
    console.log('请求参数:', params)
    const response = await taskNotificationApi.getTaskSettings(params)
    console.log('API响应:', response)
    
    settingList.value = response.data.items || []
    total.value = response.data.total || 0
  } catch (error) {
    console.error('获取任务通知设置失败:', error)
    ElMessage.error('获取任务通知设置失败')
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
  queryParams.task_id = undefined
  queryParams.task_type = ''
  queryParams.notification_config_id = undefined
  getList()
}

// 多选框选中数据
const handleSelectionChange = (selection: TaskNotificationSetting[]) => {
  ids.value = selection.map(item => item.id!)
  single.value = selection.length !== 1
  multiple.value = !selection.length
}

// 获取配置名称
const getConfigName = (configId: number) => {
  const config = configOptions.value.find(c => c.id === configId)
  return config ? config.name : `配置ID: ${configId}`
}

// 状态修改
const handleStatusChange = async (row: TaskNotificationSetting) => {
  const text = row.is_enabled ? '启用' : '停用'
  try {
    await ElMessageBox.confirm(`确认要${text}该任务通知设置吗？`)
    await taskNotificationApi.updateTaskSetting(row.id!, { is_enabled: row.is_enabled })
    ElMessage.success(`${text}成功`)
  } catch (error: any) {
    row.is_enabled = !row.is_enabled
    console.error(`${text}设置失败:`, error)
    if (error?.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error(`${text}失败`)
    }
  }
}

// 新增按钮操作
const handleAdd = () => {
  reset()
  open.value = true
  title.value = '添加任务通知设置'
}

// 修改按钮操作
const handleUpdate = (row: TaskNotificationSetting) => {
  reset()
  form.value = { ...row }
  open.value = true
  title.value = '修改任务通知设置'
}

// 删除按钮操作
const handleDelete = async (row: TaskNotificationSetting) => {
  try {
    await ElMessageBox.confirm(`是否确认删除任务${row.task_id}的通知设置？`)
    
    try {
      await taskNotificationApi.deleteTaskSetting(row.id!)
      ElMessage.success('删除成功')
      await getList()
    } catch (error: any) {
      console.error('删除设置失败:', error)
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
    ElMessage.warning('请选择要删除的设置')
    return
  }
  
  try {
    await ElMessageBox.confirm(`是否确认删除选中的 ${ids.value.length} 个设置？`)
    
    try {
      await taskNotificationApi.batchDeleteTaskSettings(ids.value)
      ElMessage.success(`成功删除 ${ids.value.length} 个设置`)
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

// 提交表单
const submitForm = async () => {
  if (!settingRef.value) return
  
  try {
    // 先进行表单验证
    await settingRef.value.validate()
    
    if (form.value.id) {
      await taskNotificationApi.updateTaskSetting(form.value.id, form.value)
      ElMessage.success('修改成功')
    } else {
      await taskNotificationApi.createTaskSetting(form.value)
      ElMessage.success('新增成功')
    }
    open.value = false
    await getList()
  } catch (error: any) {
    console.error('提交表单失败:', error)
    if (error?.message) {
      ElMessage.error(error.message)
    } else {
      ElMessage.error('操作失败')
    }
  }
}

// 取消按钮
const cancel = () => {
  open.value = false
  reset()
}

// 表单重置
const reset = () => {
  form.value = {
    task_id: 1,
    task_type: 'API',
    notification_config_id: undefined as any,
    is_enabled: true,
    notify_on_success: false,
    notify_on_failure: true
  }
  
  // 清除表单验证状态
  if (settingRef.value) {
    settingRef.value.clearValidate()
  }
}

// 初始化
onMounted(() => {
  getConfigOptions()
  getList()
})
</script>

<style scoped>
.task-notification-settings {
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

.dialog-footer {
  text-align: right;
}

/* 修复表单验证样式 */
:deep(.el-form-item.is-required .el-form-item__label:before) {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
  position: static;
  display: inline;
  font-weight: normal;
}

:deep(.el-form-item__label) {
  position: relative;
  display: inline-block;
}

:deep(.el-form-item__error) {
  position: absolute;
  top: 100%;
  left: 0;
  font-size: 12px;
  color: #f56c6c;
  line-height: 1;
  padding-top: 4px;
  z-index: 1;
}

/* 确保表单项有足够的底部间距来显示错误信息 */
:deep(.el-form-item) {
  margin-bottom: 22px;
}
</style>