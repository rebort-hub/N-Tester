<template>
  <div class="template-management-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>测试用例模板管理</span>
          <div>
            <el-button type="primary" size="small" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建模板
            </el-button>
            <el-button type="success" size="small" @click="handleImport">
              <el-icon><Upload /></el-icon>
              导入模板
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选栏 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="模板类型">
          <el-select v-model="searchForm.template_type" placeholder="全部" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="主项目" value="main" />
            <el-option label="UI自动化" value="ui" />
            <el-option label="API测试" value="api" />
            <el-option label="性能测试" value="performance" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshLeft /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table
        :data="tableData"
        v-loading="loading"
        border
        stripe
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="模板名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="template_type" label="模板类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getTemplateTypeTag(row.template_type)">
              {{ getTemplateTypeLabel(row.template_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="is_default" label="默认模板" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">是</el-tag>
            <el-tag v-else type="info" size="small">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_active" type="success" size="small">启用</el-tag>
            <el-tag v-else type="danger" size="small">禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creation_date" label="创建时间" width="160" align="center">
          <template #default="{ row }">
            {{ formatTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handlePreview(row)">
              <el-icon><View /></el-icon>
              预览
            </el-button>
            <el-button type="success" size="small" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="warning" size="small" @click="handleExport(row)">
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="handleDelete(row)"
              :disabled="row.is_default"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑模板对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板类型" prop="template_type">
          <el-select v-model="form.template_type" placeholder="请选择模板类型" style="width: 100%">
            <el-option label="主项目" value="main" />
            <el-option label="UI自动化" value="ui" />
            <el-option label="API测试" value="api" />
            <el-option label="性能测试" value="performance" />
          </el-select>
        </el-form-item>
        <el-form-item label="模板描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模板描述"
          />
        </el-form-item>
        <el-form-item label="字段映射" prop="field_mapping">
          <div style="width: 100%">
            <el-button type="primary" size="small" @click="handleAddColumn" style="margin-bottom: 10px">
              <el-icon><Plus /></el-icon>
              添加字段
            </el-button>
            <div class="field-mapping-table-wrapper">
              <el-table :data="form.field_mapping.columns" border style="width: 100%">
                <el-table-column label="源字段" min-width="140">
                  <template #default="{ row, $index }">
                    <el-input v-model="row.source" placeholder="源字段名" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="目标字段" min-width="140">
                  <template #default="{ row, $index }">
                    <el-input v-model="row.target" placeholder="目标字段名" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="字段类型" min-width="110">
                  <template #default="{ row, $index }">
                    <el-select v-model="row.type" size="small" style="width: 100%">
                      <el-option label="文本" value="text" />
                      <el-option label="枚举" value="enum" />
                      <el-option label="数字" value="number" />
                    </el-select>
                  </template>
                </el-table-column>
                <el-table-column label="默认值" min-width="110">
                  <template #default="{ row, $index }">
                    <el-input v-model="row.default" placeholder="默认值" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80" align="center">
                  <template #default="{ row, $index }">
                    <el-button
                      type="danger"
                      size="small"
                      @click="handleRemoveColumn($index)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="设为默认" prop="is_default">
          <el-switch v-model="form.is_default" />
          <span style="color: #909399; font-size: 12px; margin-left: 10px;">
            默认模板将在保存时自动使用
          </span>
        </el-form-item>
        <el-form-item label="启用状态" prop="is_active">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="模板预览"
      width="900px"
      destroy-on-close
    >
      <div v-if="previewTemplate">
        <el-descriptions :column="2" border style="margin-bottom: 20px">
          <el-descriptions-item label="模板名称">
            {{ previewTemplate.name }}
          </el-descriptions-item>
          <el-descriptions-item label="模板类型">
            <el-tag :type="getTemplateTypeTag(previewTemplate.template_type)">
              {{ getTemplateTypeLabel(previewTemplate.template_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ previewTemplate.description || '无' }}
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">字段映射配置</el-divider>
        <el-table :data="previewTemplate.field_mapping.columns" border style="width: 100%">
          <el-table-column prop="source" label="源字段" min-width="150" />
          <el-table-column prop="target" label="目标字段" min-width="150" />
          <el-table-column prop="type" label="字段类型" min-width="100" />
          <el-table-column prop="default" label="默认值" min-width="120" />
        </el-table>

        <el-divider content-position="left">示例数据预览</el-divider>
        <el-form :inline="true" style="margin-bottom: 15px">
          <el-form-item label="示例数据">
            <el-input
              v-model="sampleInput"
              type="textarea"
              :rows="3"
              placeholder='输入JSON格式的示例数据，例如：{"用例名称": "测试登录", "优先级": "高"}'
              style="width: 600px"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleTestMapping">
              测试映射
            </el-button>
          </el-form-item>
        </el-form>

        <div v-if="mappingResult">
          <el-alert
            title="映射结果"
            type="success"
            :closable="false"
            style="margin-bottom: 10px"
          />
          <pre style="background: #f5f7fa; padding: 15px; border-radius: 4px; overflow: auto;">{{ JSON.stringify(mappingResult, null, 2) }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- 导入文件选择 -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".json"
      style="display: none"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Search, RefreshLeft, Upload, Download, Edit, Delete, View } from '@element-plus/icons-vue'
import { testcaseTemplateApi } from '/@/api/v1/ai_intelligence'

// 搜索表单
const searchForm = reactive({
  template_type: ''
})

// 表格数据
const tableData = ref<any[]>([])
const loading = ref(false)

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建模板')
const formRef = ref<FormInstance>()
const submitLoading = ref(false)
const isEdit = ref(false)
const editId = ref(0)

// 表单数据
const form = reactive({
  name: '',
  description: '',
  template_type: 'ui',
  field_mapping: {
    columns: [] as any[]
  },
  is_default: false,
  is_active: true
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入模板名称', trigger: 'blur' }],
  template_type: [{ required: true, message: '请选择模板类型', trigger: 'change' }],
  field_mapping: [
    {
      validator: (rule: any, value: any, callback: any) => {
        if (!value.columns || value.columns.length === 0) {
          callback(new Error('请至少添加一个字段映射'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

// 预览对话框
const previewDialogVisible = ref(false)
const previewTemplate = ref<any>(null)
const sampleInput = ref('')
const mappingResult = ref<any>(null)

// 文件输入
const fileInputRef = ref<HTMLInputElement>()

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (searchForm.template_type) {
      params.template_type = searchForm.template_type
    }
    
    const res = await testcaseTemplateApi.list(params)
    tableData.value = res.data || []
  } catch (error) {
    console.error('获取模板列表失败', error)
    ElMessage.error('获取模板列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  getList()
}

// 重置
const handleReset = () => {
  searchForm.template_type = ''
  getList()
}

// 新建模板
const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = '新建模板'
  resetForm()
  dialogVisible.value = true
}

// 编辑模板
const handleEdit = async (row: any) => {
  isEdit.value = true
  editId.value = row.id
  dialogTitle.value = '编辑模板'
  
  try {
    const res = await testcaseTemplateApi.get(row.id)
    const template = res.data
    
    form.name = template.name
    form.description = template.description || ''
    form.template_type = template.template_type
    form.field_mapping = template.field_mapping || { columns: [] }
    form.is_default = template.is_default
    form.is_active = template.is_active
    
    dialogVisible.value = true
  } catch (error) {
    console.error('获取模板详情失败', error)
    ElMessage.error('获取模板详情失败')
  }
}

// 删除模板
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模板"${row.name}"吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await testcaseTemplateApi.delete(row.id)
    ElMessage.success('删除成功')
    getList()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
      ElMessage.error('删除失败')
    }
  }
}

// 导出模板
const handleExport = async (row: any) => {
  try {
    const res = await testcaseTemplateApi.export(row.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `template_${row.id}_${row.name}.json`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败', error)
    ElMessage.error('导出失败')
  }
}

// 导入模板
const handleImport = () => {
  fileInputRef.value?.click()
}

// 文件选择变化
const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  try {
    await testcaseTemplateApi.import(file)
    ElMessage.success('导入成功')
    getList()
  } catch (error: any) {
    console.error('导入失败', error)
    ElMessage.error(error.message || '导入失败')
  } finally {
    // 清空文件输入
    target.value = ''
  }
}

// 预览模板
const handlePreview = async (row: any) => {
  try {
    const res = await testcaseTemplateApi.get(row.id)
    previewTemplate.value = res.data
    sampleInput.value = ''
    mappingResult.value = null
    previewDialogVisible.value = true
  } catch (error) {
    console.error('获取模板详情失败', error)
    ElMessage.error('获取模板详情失败')
  }
}

// 测试映射
const handleTestMapping = async () => {
  if (!sampleInput.value) {
    ElMessage.warning('请输入示例数据')
    return
  }
  
  try {
    const sampleData = JSON.parse(sampleInput.value)
    const res = await testcaseTemplateApi.preview(previewTemplate.value.id, sampleData)
    mappingResult.value = res.data.mapped_output
  } catch (error: any) {
    if (error instanceof SyntaxError) {
      ElMessage.error('示例数据格式错误，请输入有效的JSON')
    } else {
      console.error('测试映射失败', error)
      ElMessage.error('测试映射失败')
    }
  }
}

// 添加字段
const handleAddColumn = () => {
  form.field_mapping.columns.push({
    source: '',
    target: '',
    type: 'text',
    default: ''
  })
}

// 删除字段
const handleRemoveColumn = (index: number) => {
  form.field_mapping.columns.splice(index, 1)
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      if (isEdit.value) {
        await testcaseTemplateApi.update(editId.value, form)
        ElMessage.success('更新成功')
      } else {
        await testcaseTemplateApi.create(form)
        ElMessage.success('创建成功')
      }
      
      dialogVisible.value = false
      getList()
    } catch (error: any) {
      console.error('提交失败', error)
      ElMessage.error(error.message || '提交失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 重置表单
const resetForm = () => {
  form.name = ''
  form.description = ''
  form.template_type = 'ui'
  form.field_mapping = { columns: [] }
  form.is_default = false
  form.is_active = true
}

// 辅助函数
const getTemplateTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    main: '主项目',
    ui: 'UI自动化',
    api: 'API测试',
    performance: '性能测试'
  }
  return map[type] || type
}

const getTemplateTypeTag = (type: string) => {
  const map: Record<string, string> = {
    main: 'primary',
    ui: 'success',
    api: 'warning',
    performance: 'danger'
  }
  return map[type] || ''
}

const formatTime = (time?: string) => {
  if (!time) return ''
  return time.substring(0, 16).replace('T', ' ')
}

onMounted(() => {
  getList()
})
</script>

<style scoped lang="scss">
.template-management-container {
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

// 字段映射表格容器样式
.field-mapping-table-wrapper {
  max-height: 350px; // 约7行的高度（每行约50px）
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  
  // 自定义滚动条样式
  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #c1c1c1;
    border-radius: 4px;
    
    &:hover {
      background: #a8a8a8;
    }
  }
  
  // 确保表格在容器内正常显示
  :deep(.el-table) {
    margin-bottom: 0;
    
    // 固定表头
    .el-table__header-wrapper {
      position: sticky;
      top: 0;
      z-index: 2;
      background: #fff;
    }
  }
}
</style>
