<template>
  <el-dialog
    v-model="visible"
    :title="form.id ? '编辑请求' : '新建请求'"
    width="600px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-form-item label="请求名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入请求名称" />
      </el-form-item>
      
      <el-form-item label="请求方法" prop="method">
        <el-select v-model="form.method" placeholder="请选择请求方法">
          <el-option label="GET" value="GET" />
          <el-option label="POST" value="POST" />
          <el-option label="PUT" value="PUT" />
          <el-option label="DELETE" value="DELETE" />
          <el-option label="PATCH" value="PATCH" />
          <el-option label="HEAD" value="HEAD" />
          <el-option label="OPTIONS" value="OPTIONS" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="请求URL" prop="url">
        <el-input v-model="form.url" placeholder="/api/users" />
      </el-form-item>
      
      <el-form-item label="请求描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入请求描述"
        />
      </el-form-item>
      
      <el-form-item label="排序" prop="order_num">
        <el-input-number v-model="form.order_num" :min="0" />
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

const { apiRequestApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: boolean
  collectionId?: number
  request?: any
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const loading = ref(false)
const formRef = ref()

const form = ref({
  id: undefined,
  name: '',
  method: 'GET',
  url: '',
  description: '',
  order_num: 0
})

const rules = {
  name: [{ required: true, message: '请输入请求名称', trigger: 'blur' }],
  method: [{ required: true, message: '请选择请求方法', trigger: 'change' }],
  url: [{ required: true, message: '请输入请求URL', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    if (props.request) {
      form.value = { ...props.request }
    } else {
      resetForm()
    }
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const resetForm = () => {
  form.value = {
    id: undefined,
    name: '',
    method: 'GET',
    url: '',
    description: '',
    order_num: 0
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  visible.value = false
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    loading.value = true
    const data = {
      ...form.value,
      collection_id: props.collectionId
    }
    
    if (form.value.id) {
      await apiRequestApi.update(form.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await apiRequestApi.create(data)
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
