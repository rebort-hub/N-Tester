<template>
  <el-dialog
    v-model="visible"
    :title="form.id ? '编辑API项目' : '新建API项目'"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="项目名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入项目名称" />
      </el-form-item>
      
      <el-form-item label="项目类型" prop="project_type">
        <el-select v-model="form.project_type" placeholder="请选择项目类型">
          <el-option label="HTTP" value="HTTP" />
          <el-option label="WebSocket" value="WEBSOCKET" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="基础URL" prop="base_url">
        <el-input v-model="form.base_url" placeholder="https://api.example.com" />
      </el-form-item>
      
      <el-form-item label="项目描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="4"
          placeholder="请输入项目描述"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useApiTestingApi } from '/@/api/v1/api_testing'

const { apiProjectApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: boolean
  projectId?: number
  apiProject?: any
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const loading = ref(false)
const formRef = ref()

const form = ref({
  id: undefined,
  name: '',
  project_type: 'HTTP',
  base_url: '',
  description: ''
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  project_type: [{ required: true, message: '请选择项目类型', trigger: 'change' }]
}

// 监听显示状态
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    if (props.apiProject) {
      form.value = { ...props.apiProject }
    } else {
      resetForm()
    }
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 重置表单
const resetForm = () => {
  form.value = {
    id: undefined,
    name: '',
    project_type: 'HTTP',
    base_url: '',
    description: ''
  }
  formRef.value?.clearValidate()
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    const data = {
      ...form.value,
      project_id: props.projectId
    }
    
    if (form.value.id) {
      await apiProjectApi.update(form.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await apiProjectApi.create(data)
      ElMessage.success('创建成功')
    }
    
    emit('success')
    handleClose()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    loading.value = false
  }
}
</script>
