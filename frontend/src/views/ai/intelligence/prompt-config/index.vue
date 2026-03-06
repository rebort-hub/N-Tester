<template>
  <div class="prompt-config-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>提示词配置</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增提示词
          </el-button>
        </div>
      </template>

      <!-- 筛选区域 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="提示词类型">
          <el-select 
            v-model="queryForm.prompt_type" 
            placeholder="请选择" 
            clearable
            style="width: 200px"
            :popper-options="{ strategy: 'fixed' }"
          >
            <el-option label="Writer (编写)" value="writer" />
            <el-option label="Reviewer (评审)" value="reviewer" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe>
        <el-table-column prop="name" label="配置名称" min-width="150" />
        <el-table-column prop="prompt_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.prompt_type === 'writer' ? 'primary' : 'success'">
              {{ row.prompt_type === 'writer' ? 'Writer' : 'Reviewer' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="提示词内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creation_date" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="提示词类型" prop="prompt_type">
          <el-select v-model="formData.prompt_type" placeholder="请选择类型" style="width: 100%">
            <el-option label="Writer (编写)" value="writer" />
            <el-option label="Reviewer (评审)" value="reviewer" />
          </el-select>
        </el-form-item>
        <el-form-item label="提示词内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="12"
            placeholder="请输入提示词内容"
          />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { promptConfigApi } from '/@/api/v1/ai_intelligence'
import type { PromptConfig, PromptConfigForm } from '/@/types/ai_intelligence'

// 查询表单
const queryForm = reactive({
  prompt_type: ''
})

// 表格数据
const tableData = ref<PromptConfig[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增提示词')
const formRef = ref<FormInstance>()
const submitLoading = ref(false)

// 表单数据
const formData = reactive<PromptConfigForm>({
  name: '',
  prompt_type: '',
  content: '',
  is_active: true
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  prompt_type: [{ required: true, message: '请选择提示词类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入提示词内容', trigger: 'blur' }]
}

// 当前编辑的ID
let currentEditId: number | null = null

// 格式化时间
const formatDateTime = (dateStr: string | null | undefined): string => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (queryForm.prompt_type) params.prompt_type = queryForm.prompt_type
    
    const res = await promptConfigApi.list(params)
    tableData.value = res.data || []
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 查询
const handleQuery = () => {
  getList()
}

// 重置
const handleReset = () => {
  queryForm.prompt_type = ''
  getList()
}

// 新增
const handleAdd = () => {
  currentEditId = null
  dialogTitle.value = '新增提示词'
  resetForm()
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: PromptConfig) => {
  currentEditId = row.id!
  dialogTitle.value = '编辑提示词'
  Object.assign(formData, {
    name: row.name,
    prompt_type: row.prompt_type,
    content: row.content,
    is_active: row.is_active !== false
  })
  dialogVisible.value = true
}

// 删除
const handleDelete = (row: PromptConfig) => {
  ElMessageBox.confirm('确定要删除该提示词吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await promptConfigApi.delete(row.id!)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      if (currentEditId) {
        await promptConfigApi.update(currentEditId, formData)
        ElMessage.success('更新成功')
      } else {
        await promptConfigApi.create(formData)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      getList()
    } catch (error) {
      ElMessage.error(currentEditId ? '更新失败' : '创建失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  Object.assign(formData, {
    name: '',
    prompt_type: '',
    content: '',
    is_active: true
  })
  formRef.value?.clearValidate()
}

onMounted(() => {
  getList()
})
</script>

<style scoped lang="scss">
.prompt-config-container {
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
</style>
