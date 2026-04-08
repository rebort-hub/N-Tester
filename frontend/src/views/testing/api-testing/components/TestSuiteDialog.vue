<template>
  <el-dialog
    v-model="visible"
    title="测试套件管理"
    width="900px"
    @close="handleClose"
  >
    <div class="test-suite-manager">
      <div class="toolbar">
        <el-button type="primary" @click="handleAdd">
          <el-icon><ele-Plus /></el-icon>
          新建套件
        </el-button>
      </div>
      
      <el-table :data="testSuites" style="width: 100%; margin-top: 15px">
        <el-table-column prop="name" label="套件名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column label="请求数量" width="100">
          <template #default="{ row }">
            {{ row.request_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="success" size="small" @click="handleExecute(row)" :loading="row.executing">
              执行
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 编辑套件对话框 -->
    <el-dialog
      v-model="showEditDialog"
      :title="editForm.id ? '编辑测试套件' : '新建测试套件'"
      width="900px"
      append-to-body
    >
      <el-form :model="editForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="套件名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入套件名称" />
        </el-form-item>
        
        <el-form-item label="套件描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入套件描述"
          />
        </el-form-item>
        
        <el-form-item label="执行环境" prop="environment_id">
          <el-select v-model="editForm.environment_id" placeholder="请选择执行环境">
            <el-option
              v-for="env in environments"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择请求" class="transfer-form-item">
          <el-transfer
            v-model="selectedRequests"
            :data="availableRequests"
            :titles="['可用请求', '已选请求']"
            :props="{
              key: 'id',
              label: 'name'
            }"
            filterable
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          确定
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="执行结果"
      width="800px"
      append-to-body
    >
      <div class="execution-result" v-if="executionResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="总请求数">
            {{ executionResult.total_requests }}
          </el-descriptions-item>
          <el-descriptions-item label="通过数">
            <el-tag type="success">{{ executionResult.passed_requests }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="失败数">
            <el-tag type="danger">{{ executionResult.failed_requests }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="executionResult.status === 'SUCCESS' ? 'success' : 'danger'">
              {{ executionResult.status }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider>详细结果</el-divider>
        
        <el-table :data="executionResult.results" style="width: 100%">
          <el-table-column prop="request_name" label="请求名称" min-width="200" />
          <el-table-column prop="status_code" label="状态码" width="100" />
          <el-table-column prop="response_time" label="响应时间(ms)" width="120">
            <template #default="{ row }">
              {{ row.response_time?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="passed" label="结果" width="100">
            <template #default="{ row }">
              <el-tag :type="row.passed ? 'success' : 'danger'">
                {{ row.passed ? '通过' : '失败' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApiTestingApi } from '/@/api/v1/api_testing'

const { apiTestSuiteApi, apiEnvironmentApi, apiCollectionApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: boolean
  apiProjectId?: number
  projectId?: number
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const showEditDialog = ref(false)
const showResultDialog = ref(false)
const loading = ref(false)
const formRef = ref()

const testSuites = ref<any[]>([])
const environments = ref<any[]>([])
const availableRequests = ref<any[]>([])
const selectedRequests = ref<number[]>([])
const executionResult = ref<any>(null)

const editForm = ref({
  id: undefined,
  name: '',
  description: '',
  environment_id: undefined
})

const rules = {
  name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadTestSuites()
    loadEnvironments()
    loadAvailableRequests()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 加载测试套件列表
const loadTestSuites = async () => {
  if (!props.apiProjectId) return
  
  try {
    const res = await apiTestSuiteApi.list({ api_project_id: props.apiProjectId })
    testSuites.value = res.data.items || []
  } catch (error) {
    console.error('加载测试套件列表失败:', error)
  }
}

// 加载环境列表
const loadEnvironments = async () => {
  if (!props.projectId) return
  
  try {
    const res = await apiEnvironmentApi.list(props.projectId)
    environments.value = res.data || []
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

// 加载可用请求
const loadAvailableRequests = async () => {
  if (!props.apiProjectId) return
  
  try {
    const res = await apiCollectionApi.tree(props.apiProjectId)
    const requests: any[] = []
    
    // 递归提取所有请求
    const extractRequests = (items: any[]) => {
      items.forEach(item => {
        if (item.requests && item.requests.length > 0) {
          requests.push(...item.requests.map((req: any) => ({
            id: req.id,
            name: `${item.name} / ${req.name}`
          })))
        }
        if (item.children && item.children.length > 0) {
          extractRequests(item.children)
        }
      })
    }
    
    extractRequests(res.data || [])
    availableRequests.value = requests
  } catch (error) {
    console.error('加载可用请求失败:', error)
  }
}

// 新建套件
const handleAdd = () => {
  editForm.value = {
    id: undefined,
    name: '',
    description: '',
    environment_id: undefined
  }
  selectedRequests.value = []
  showEditDialog.value = true
}

// 编辑套件
const handleEdit = async (row: any) => {
  try {
    const res = await apiTestSuiteApi.get(row.id)
    editForm.value = { ...res.data }
    selectedRequests.value = res.data.request_ids || []
    showEditDialog.value = true
  } catch (error) {
    ElMessage.error('加载套件详情失败')
  }
}

// 执行套件
const handleExecute = async (row: any) => {
  try {
    row.executing = true
    const res = await apiTestSuiteApi.execute(row.id)
    executionResult.value = res.data
    showResultDialog.value = true
    ElMessage.success('执行完成')
  } catch (error) {
    ElMessage.error('执行失败')
  } finally {
    row.executing = false
  }
}

// 删除套件
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除测试套件 "${row.name}" 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await apiTestSuiteApi.delete(row.id)
    await loadTestSuites()
    emit('success')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    const data = {
      ...editForm.value,
      api_project_id: props.apiProjectId,
      request_ids: selectedRequests.value
    }
    
    if (editForm.value.id) {
      await apiTestSuiteApi.update(editForm.value.id, data)
    } else {
      await apiTestSuiteApi.create(data)
    }
    
    showEditDialog.value = false
    await loadTestSuites()
    emit('success')
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error('提交失败')
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped lang="scss">
.test-suite-manager {
  .toolbar {
    display: flex;
    justify-content: flex-end;
  }
}

.execution-result {
  .el-descriptions {
    margin-bottom: 20px;
  }
}

// 修复el-transfer布局
.transfer-form-item {
  :deep(.el-form-item__content) {
    display: flex;
    justify-content: center;
  }
}

:deep(.el-transfer) {
  display: flex !important;
  flex-direction: row !important;
  align-items: flex-start;
  justify-content: center;
  text-align: left;
  
  .el-transfer-panel {
    width: 280px;
    height: 400px;
    flex-shrink: 0;
    
    .el-transfer-panel__body {
      height: 340px;
    }
    
    .el-transfer-panel__list {
      height: 300px;
      overflow-y: auto;
    }
  }
  
  .el-transfer__buttons {
    display: flex !important;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0 20px;
    margin: 0 10px;
    flex-shrink: 0;
    
    .el-button {
      margin: 5px 0;
    }
  }
}
</style>
