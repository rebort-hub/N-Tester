<template>
  <el-dialog
    v-model="visible"
    :title="form.id ? '编辑集合' : '新建集合'"
    width="500px"
    @close="handleClose"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
      <el-form-item label="集合名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入集合名称" />
      </el-form-item>
      
      <el-form-item label="集合描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入集合描述"
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

const { apiCollectionApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: boolean
  apiProjectId?: number
  parentId?: number
  collection?: any
}>()

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const loading = ref(false)
const formRef = ref()

const form = ref({
  id: undefined,
  name: '',
  description: '',
  order_num: 0
})

const rules = {
  name: [{ required: true, message: '请输入集合名称', trigger: 'blur' }]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    if (props.collection) {
      form.value = { ...props.collection }
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
      api_project_id: props.apiProjectId,
      parent_id: props.parentId
    }
    
    if (form.value.id) {
      await apiCollectionApi.update(form.value.id, data)
      ElMessage.success('更新成功')
    } else {
      await apiCollectionApi.create(data)
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
