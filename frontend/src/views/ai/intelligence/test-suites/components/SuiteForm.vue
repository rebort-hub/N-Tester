<template>
  <el-dialog
    v-model="visible"
    :title="suiteId ? '编辑测试套件' : '新增测试套件'"
    width="800px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      v-loading="loading"
    >
      <el-form-item label="套件名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入套件名称" />
      </el-form-item>

      <el-form-item label="套件描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入套件描述"
        />
      </el-form-item>

      <el-form-item label="选择项目" prop="project_id">
        <el-select
          v-model="formData.project_id"
          placeholder="请选择项目"
          style="width: 100%"
          @change="handleProjectChange"
        >
          <el-option
            v-for="project in projectList"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="选择模块" prop="modules">
        <div class="module-selector">
          <el-transfer
            v-model="selectedModuleIds"
            :data="moduleOptions"
            :titles="['可选模块', '已选模块']"
            :props="{
              key: 'id',
              label: 'name'
            }"
            @change="handleModuleChange"
          />
          
          <div v-if="formData.modules.length > 0" class="module-order">
            <div class="order-title">执行顺序（拖拽排序）：</div>
            <el-table :data="formData.modules" border>
              <el-table-column prop="execution_order" label="顺序" width="80" align="center" />
              <el-table-column prop="module_name" label="模块名称" />
              <el-table-column label="操作" width="120" align="center">
                <template #default="{ $index }">
                  <el-button
                    type="primary"
                    size="small"
                    :disabled="$index === 0"
                    @click="moveUp($index)"
                  >
                    上移
                  </el-button>
                  <el-button
                    type="primary"
                    size="small"
                    :disabled="$index === formData.modules.length - 1"
                    @click="moveDown($index)"
                  >
                    下移
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-form-item>

      <el-form-item>
        <el-alert
          v-if="formData.modules.length > 0"
          :title="`已选择 ${formData.modules.length} 个模块，共 ${totalCases} 个用例`"
          type="info"
          :closable="false"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { aiTestSuiteApi, aiCaseApi } from '/@/api/v1/ai_intelligence'
import { getProjectList } from '/@/api/v1/project'
import { getModuleList } from '/@/api/v1/modules'

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

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)

const formData = reactive({
  name: '',
  description: '',
  project_id: null,
  modules: []
})

const rules = {
  name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择项目', trigger: 'change' }],
  modules: [
    {
      validator: (rule, value, callback) => {
        if (!value || value.length === 0) {
          callback(new Error('请至少选择一个模块'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

const projectList = ref([])
const moduleList = ref([])
const selectedModuleIds = ref([])
const totalCases = ref(0)

// 模块选项
const moduleOptions = computed(() => {
  return moduleList.value.map(m => ({
    id: m.id,
    name: m.name,
    disabled: false
  }))
})

// 加载项目列表
const loadProjects = async () => {
  try {
    console.log('开始获取主项目列表...')
    // 使用主项目API而不是UI项目API
    const res = await getProjectList({ page: 1, page_size: 100 })
    console.log('主项目列表API响应:', res)
    if (res.code === 200) {
      projectList.value = res.data.list || res.data.items || res.data || []
      console.log('主项目列表:', projectList.value)
    }
  } catch (error) {
    console.error('获取主项目列表失败:', error)
  }
}

// 加载模块列表
const loadModules = async (projectId: number) => {
  if (!projectId) {
    moduleList.value = []
    return
  }
  try {
    const res = await getModuleList({ project_id: projectId, page: 1, page_size: 1000 })
    if (res.code === 200) {
      moduleList.value = res.data.list || res.data.items || []
    }
  } catch (error) {
    console.error('获取模块列表失败:', error)
  }
}

// 项目变化
const handleProjectChange = (projectId: number) => {
  formData.modules = []
  selectedModuleIds.value = []
  moduleList.value = []
  totalCases.value = 0
  
  if (projectId) {
    loadModules(projectId)
  }
}

// 模块变化
const handleModuleChange = async () => {
  const newModules = []
  
  for (let i = 0; i < selectedModuleIds.value.length; i++) {
    const moduleId = selectedModuleIds.value[i]
    const module = moduleList.value.find(m => m.id === moduleId)
    
    if (module) {
      // 查询模块下的用例数
      let caseCount = 0
      try {
        const res = await aiCaseApi.list({
          source_project_id: formData.project_id,
          source_module_id: moduleId,
          page: 1,
          page_size: 1
        })
        if (res.code === 200) {
          caseCount = res.data.total || 0
        }
      } catch (error) {
        console.error('查询用例数失败:', error)
      }
      
      newModules.push({
        module_id: moduleId,
        module_name: module.name,
        execution_order: i + 1,
        case_count: caseCount
      })
    }
  }
  
  formData.modules = newModules
  totalCases.value = newModules.reduce((sum, m) => sum + m.case_count, 0)
}

// 上移
const moveUp = (index: number) => {
  if (index > 0) {
    const temp = formData.modules[index]
    formData.modules[index] = formData.modules[index - 1]
    formData.modules[index - 1] = temp
    updateOrder()
  }
}

// 下移
const moveDown = (index: number) => {
  if (index < formData.modules.length - 1) {
    const temp = formData.modules[index]
    formData.modules[index] = formData.modules[index + 1]
    formData.modules[index + 1] = temp
    updateOrder()
  }
}

// 更新顺序
const updateOrder = () => {
  formData.modules.forEach((m, i) => {
    m.execution_order = i + 1
  })
}

// 加载套件详情
const loadSuiteDetail = async () => {
  if (!props.suiteId) return
  
  loading.value = true
  try {
    const res = await aiTestSuiteApi.get(props.suiteId)
    if (res.code === 200) {
      const suite = res.data
      formData.name = suite.name
      formData.description = suite.description
      formData.project_id = suite.project_id
      
      // 加载模块列表
      await loadModules(suite.project_id)
      
      // 设置已选模块
      if (suite.modules && suite.modules.length > 0) {
        formData.modules = suite.modules.map(m => ({
          module_id: m.module_id,
          module_name: m.module_name,
          execution_order: m.execution_order,
          case_count: 0
        }))
        selectedModuleIds.value = suite.modules.map(m => m.module_id)
        
        // 查询用例数
        await handleModuleChange()
      }
    }
  } catch (error) {
    ElMessage.error('加载套件详情失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 提交
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    submitting.value = true
    
    const data = {
      name: formData.name,
      description: formData.description,
      project_id: formData.project_id,
      modules: formData.modules.map(m => ({
        module_id: m.module_id,
        module_name: m.module_name,
        execution_order: m.execution_order
      }))
    }
    
    let res
    if (props.suiteId) {
      res = await aiTestSuiteApi.update(props.suiteId, data)
    } else {
      res = await aiTestSuiteApi.create(data)
    }
    
    if (res.code === 200) {
      ElMessage.success(props.suiteId ? '更新成功' : '创建成功')
      emit('success')
      handleClose()
    }
  } catch (error) {
    if (error !== false) {
      ElMessage.error(props.suiteId ? '更新失败' : '创建失败')
      console.error(error)
    }
  } finally {
    submitting.value = false
  }
}

// 关闭
const handleClose = () => {
  formRef.value?.resetFields()
  formData.name = ''
  formData.description = ''
  formData.project_id = null
  formData.modules = []
  selectedModuleIds.value = []
  moduleList.value = []
  totalCases.value = 0
  visible.value = false
}

// 监听对话框打开
watch(() => props.modelValue, (val) => {
  if (val) {
    loadProjects()
    if (props.suiteId) {
      loadSuiteDetail()
    }
  }
})
</script>

<style scoped lang="scss">
.module-selector {
  width: 100%;
}

.module-order {
  margin-top: 20px;
}

.order-title {
  margin-bottom: 10px;
  font-weight: bold;
}
</style>
