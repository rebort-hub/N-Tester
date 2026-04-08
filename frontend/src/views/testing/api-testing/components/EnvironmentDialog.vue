<template>
  <el-dialog
    v-model="visible"
    title="环境管理"
    width="800px"
    @close="handleClose"
  >
    <div class="environment-manager">
      <div class="toolbar">
        <el-button type="primary" @click="handleAdd">
          <el-icon><ele-Plus /></el-icon>
          新建环境
        </el-button>
      </div>
      
      <el-table :data="environments" style="width: 100%; margin-top: 15px">
        <el-table-column prop="name" label="环境名称" min-width="120" />
        <el-table-column prop="scope" label="作用域" width="100">
          <template #default="{ row }">
            <el-tag :type="row.scope === 'GLOBAL' ? 'success' : 'info'">
              {{ row.scope === 'GLOBAL' ? '全局' : '本地' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变量数量" width="100">
          <template #default="{ row }">
            {{ Object.keys(row.variables || {}).length }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="240">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="handleActivate(row)"
              :disabled="row.is_active"
            >
              激活
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 编辑环境对话框 -->
    <el-dialog
      v-model="showEditDialog"
      :title="editForm.id ? '编辑环境' : '新建环境'"
      width="600px"
      append-to-body
    >
      <el-form :model="editForm" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="环境名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入环境名称" />
        </el-form-item>
        
        <el-form-item label="作用域" prop="scope">
          <el-radio-group v-model="editForm.scope">
            <el-radio label="LOCAL">本地</el-radio>
            <el-radio label="GLOBAL">全局</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="环境变量">
          <div class="variables-editor">
            <div class="variables-container">
              <div class="variable-item" v-for="(row, index) in variablesList" :key="index">
                <span class="variable-label">变量名</span>
                <el-input 
                  v-model="row.key" 
                  placeholder="请输入变量名" 
                  size="small"
                  class="variable-key-input"
                />
                <span class="variable-label">变量值</span>
                <el-input 
                  v-model="row.value" 
                  placeholder="请输入变量值" 
                  size="small"
                  class="variable-value-input"
                />
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDeleteVariable(index)"
                  class="delete-btn"
                >
                  删除
                </el-button>
              </div>
            </div>
            <el-button
              type="primary"
              size="small"
              @click="handleAddVariable"
              style="margin-top: 10px"
            >
              <el-icon><ele-Plus /></el-icon>
              添加变量
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApiTestingApi } from '/@/api/v1/api_testing'

const { apiEnvironmentApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: boolean
  projectId?: number
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const showEditDialog = ref(false)
const loading = ref(false)
const formRef = ref()

const environments = ref<any[]>([])
const variablesList = ref<any[]>([])

const editForm = ref({
  id: undefined,
  name: '',
  scope: 'LOCAL',
  variables: {}
})

const rules = {
  name: [{ required: true, message: '请输入环境名称', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadEnvironments()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

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

// 新建环境
const handleAdd = () => {
  editForm.value = {
    id: undefined,
    name: '',
    scope: 'LOCAL',
    variables: {}
  }
  variablesList.value = []
  showEditDialog.value = true
}

// 编辑环境
const handleEdit = (row: any) => {
  editForm.value = { ...row }
  variablesList.value = Object.entries(row.variables || {}).map(([key, value]) => ({
    key,
    value
  }))
  showEditDialog.value = true
}

// 激活环境
const handleActivate = async (row: any) => {
  try {
    await apiEnvironmentApi.activate(row.id)
    ElMessage.success('激活成功')
    await loadEnvironments()
    emit('success')
  } catch (error) {
    ElMessage.error('激活失败')
  }
}

// 删除环境
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确定要删除环境 "${row.name}" 吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await apiEnvironmentApi.delete(row.id)
    ElMessage.success('删除成功')
    await loadEnvironments()
    emit('success')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 添加变量
const handleAddVariable = () => {
  variablesList.value.push({ key: '', value: '' })
}

// 删除变量
const handleDeleteVariable = (index: number) => {
  variablesList.value.splice(index, 1)
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    // 转换变量列表为对象
    const variables: any = {}
    variablesList.value.forEach(item => {
      if (item.key) {
        variables[item.key] = item.value
      }
    })
    
    const data = {
      ...editForm.value,
      project_id: props.projectId,
      variables
    }
    
    if (editForm.value.id) {
      await apiEnvironmentApi.update(editForm.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await apiEnvironmentApi.create(data)
      ElMessage.success('创建成功')
    }
    
    showEditDialog.value = false
    await loadEnvironments()
    emit('success')
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped lang="scss">
.environment-manager {
  .toolbar {
    display: flex;
    justify-content: flex-end;
  }
  
  .variables-editor {
    width: 100%;
    
    .variables-container {
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      padding: 10px;
      background-color: #fafafa;
      
      &::-webkit-scrollbar {
        width: 6px;
      }
      
      &::-webkit-scrollbar-thumb {
        background-color: #dcdfe6;
        border-radius: 3px;
        
        &:hover {
          background-color: #c0c4cc;
        }
      }
    }
    
    .variable-item {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
      gap: 8px;
      height: 32px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      .variable-label {
        font-size: 13px;
        color: #606266;
        white-space: nowrap;
        min-width: 45px;
        flex-shrink: 0;
      }
      
      .variable-key-input {
        width: 120px;
        flex-shrink: 0;
      }
      
      .variable-value-input {
        flex: 1;
        min-width: 150px;
      }
      
      .delete-btn {
        flex-shrink: 0;
        width: 60px;
      }
    }
  }
}
</style>
