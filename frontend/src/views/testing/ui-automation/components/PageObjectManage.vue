<template>
  <div class="page-object-manage">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建页面对象</el-button>
      <el-button type="success" :icon="Document" @click="handleBatchGenerateCode">批量生成代码</el-button>
      <el-button type="danger" :icon="Delete" @click="handleBatchDelete" :disabled="selectedPageObjects.length === 0">批量删除</el-button>
      <el-button :icon="Refresh" @click="loadPageObjectList">刷新</el-button>
    </div>

    <!-- 页面对象列表 -->
    <el-table :data="pageObjectList" v-loading="loading" border stripe style="margin-top: 15px" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="页面对象名称" min-width="150" />
      <el-table-column prop="class_name" label="类名" min-width="150" />
      <el-table-column prop="element_count" label="元素数量" width="100">
        <template #default="{ row }">
          <el-tag type="primary">{{ row.element_count || 0 }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDateTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="350" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleManageElements(row)">管理元素</el-button>
          <el-button type="success" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="warning" size="small" @click="handleGenerateCode(row)">生成代码</el-button>
          <el-button type="info" size="small" @click="handlePreviewCode(row)">预览代码</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.page_size"
      :total="pagination.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      @size-change="loadPageObjectList"
      @current-change="loadPageObjectList"
      style="margin-top: 15px; justify-content: flex-end"
    />

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="页面对象名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入页面对象名称" />
        </el-form-item>
        <el-form-item label="类名" prop="class_name">
          <el-input v-model="formData.class_name" placeholder="例如: LoginPage" />
          <span style="color: #909399; font-size: 12px">用于代码生成的类名</span>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="URL模式">
          <el-input v-model="formData.url_pattern" placeholder="例如: /login" />
          <span style="color: #909399; font-size: 12px">页面的URL路径模式</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 管理元素对话框 -->
    <el-dialog
      v-model="elementsDialogVisible"
      :title="`管理页面对象元素 - ${currentPageObjectName}`"
      width="1200px"
      :close-on-click-modal="false"
    >
      <div class="elements-manage-container">
        <!-- 左侧：可用元素列表 -->
        <div class="available-elements">
          <div class="section-header">
            <span>可用元素</span>
            <el-input
              v-model="elementSearchKeyword"
              placeholder="搜索元素"
              size="small"
              style="width: 200px"
              clearable
            />
          </div>
          <el-table
            :data="filteredAvailableElements"
            height="450"
            @selection-change="handleAvailableElementsSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="元素名称" min-width="120" />
            <el-table-column prop="element_type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag size="small">{{ row.element_type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="locator_value" label="定位器" min-width="150" show-overflow-tooltip />
            <template #empty>
              <div class="empty-state">
                <el-icon size="48" color="var(--el-text-color-placeholder)">
                  <Search />
                </el-icon>
                <p>暂无可用的元素</p>
                <p class="empty-tip">请先创建元素分组并添加元素</p>
              </div>
            </template>
          </el-table>
          <div class="button-area">
            <el-button type="primary" :icon="Right" @click="handleAddElements" :disabled="selectedAvailableElements.length === 0">
              添加选中元素
            </el-button>
          </div>
        </div>

        <!-- 右侧：已关联元素列表 -->
        <div class="linked-elements">
          <div class="section-header">
            <span>已关联元素</span>
            <el-button type="danger" size="small" :icon="Delete" @click="handleRemoveSelectedElements" :disabled="selectedLinkedElements.length === 0">
              移除选中
            </el-button>
          </div>
          <el-table
            :data="linkedElementsList"
            height="450"
            @selection-change="handleLinkedElementsSelectionChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column prop="element_name" label="元素名称" width="150" show-overflow-tooltip />
            <el-table-column prop="method_name" label="方法名" width="150">
              <template #default="{ row }">
                <el-input v-model="row.method_name" size="small" placeholder="方法名" />
              </template>
            </el-table-column>
            <el-table-column prop="is_property" label="属性" width="70" align="center">
              <template #default="{ row }">
                <el-switch v-model="row.is_property" size="small" />
              </template>
            </el-table-column>
            <el-table-column prop="order_num" label="排序" width="90">
              <template #default="{ row }">
                <el-input-number v-model="row.order_num" size="small" :min="0" :controls="false" class="compact-input-number" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row, $index }">
                <el-button link type="danger" size="small" @click="handleRemoveElement($index)">移除</el-button>
              </template>
            </el-table-column>
            <template #empty>
              <div class="empty-state">
                <el-icon size="48" color="var(--el-text-color-placeholder)">
                  <Box />
                </el-icon>
                <p>暂无关联的元素</p>
                <p class="empty-tip">请从左侧选择元素进行添加</p>
              </div>
            </template>
          </el-table>
        </div>
      </div>
      <template #footer>
        <el-button @click="elementsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveElements" :loading="elementsSubmitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 代码生成对话框 -->
    <el-dialog
      v-model="codeDialogVisible"
      title="生成页面对象代码"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="codeForm" label-width="120px">
        <el-form-item label="编程语言">
          <el-radio-group v-model="codeForm.language">
            <el-radio label="javascript">JavaScript</el-radio>
            <el-radio label="python">Python</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="测试框架">
          <el-radio-group v-model="codeForm.framework">
            <el-radio label="playwright">Playwright</el-radio>
            <el-radio label="selenium">Selenium</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="包含注释">
          <el-switch v-model="codeForm.include_comments" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="codeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGenerateCodeSubmit" :loading="codeLoading">生成代码</el-button>
      </template>
    </el-dialog>

    <!-- 代码预览对话框 -->
    <el-dialog
      v-model="codePreviewVisible"
      :title="`代码预览 - ${currentPageObjectName}`"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="code-preview-container">
        <div class="code-actions">
          <el-button type="primary" size="small" :icon="CopyDocument" @click="handleCopyCode">复制代码</el-button>
          <el-button type="success" size="small" :icon="Download" @click="handleDownloadCode">下载代码</el-button>
        </div>
        <div class="code-content">
          <pre><code>{{ generatedCode }}</code></pre>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Plus, Document, Refresh, Delete, Right, CopyDocument, Download, Search, Box } from '@element-plus/icons-vue'
import { uiPageObjectApi, uiElementApi, uiElementGroupApi } from '/@/api/v1/ui_automation'
import { formatDateTime } from '/@/utils/formatTime'

const props = defineProps<{
  uiProjectId: number
}>()

// 表格数据
const pageObjectList = ref([])
const loading = ref(false)
const selectedPageObjects = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建页面对象')
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  id: null,
  ui_project_id: props.uiProjectId,
  name: '',
  class_name: '',
  description: '',
  url_pattern: ''
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入页面对象名称', trigger: 'blur' }],
  class_name: [{ required: true, message: '请输入类名', trigger: 'blur' }]
}

// 元素管理对话框
const elementsDialogVisible = ref(false)
const currentPageObjectId = ref<number | null>(null)
const currentPageObjectName = ref('')
const availableElementsList = ref([])
const linkedElementsList = ref([])
const elementSearchKeyword = ref('')
const selectedAvailableElements = ref([])
const selectedLinkedElements = ref([])
const elementsSubmitLoading = ref(false)

// 过滤后的可用元素
const filteredAvailableElements = computed(() => {
  if (!elementSearchKeyword.value) {
    return availableElementsList.value
  }
  return availableElementsList.value.filter((item: any) =>
    item.name.toLowerCase().includes(elementSearchKeyword.value.toLowerCase())
  )
})

// 代码生成
const codeDialogVisible = ref(false)
const codeLoading = ref(false)
const currentCodePageObjectId = ref<number | null>(null)
const codeForm = reactive({
  language: 'javascript',
  framework: 'playwright',
  include_comments: true
})

// 代码预览
const codePreviewVisible = ref(false)
const generatedCode = ref('')

// 加载页面对象列表
const loadPageObjectList = async () => {
  loading.value = true
  try {
    const res = await uiPageObjectApi.list({
      ui_project_id: props.uiProjectId,
      page: pagination.page,
      page_size: pagination.page_size
    })
    pageObjectList.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载页面对象列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedPageObjects.value = selection
}

// 新建
const handleCreate = () => {
  dialogTitle.value = '新建页面对象'
  Object.assign(formData, {
    id: null,
    ui_project_id: props.uiProjectId,
    name: '',
    class_name: '',
    description: '',
    url_pattern: ''
  })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑页面对象'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (formData.id) {
      await uiPageObjectApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await uiPageObjectApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadPageObjectList()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该页面对象吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiPageObjectApi.delete(row.id)
      ElMessage.success('删除成功')
      loadPageObjectList()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 管理元素
const handleManageElements = async (row: any) => {
  currentPageObjectId.value = row.id
  currentPageObjectName.value = row.name
  elementsDialogVisible.value = true
  
  // 加载所有元素分组
  try {
    const groupRes = await uiElementGroupApi.tree(props.uiProjectId)
    const groups = groupRes.data || []
    
    // 递归获取所有分组ID（包括子分组）
    const getAllGroupIds = (nodes: any[]): number[] => {
      let ids: number[] = []
      nodes.forEach(node => {
        ids.push(node.id)
        if (node.children && node.children.length > 0) {
          ids = ids.concat(getAllGroupIds(node.children))
        }
      })
      return ids
    }
    
    const groupIds = getAllGroupIds(groups)
    
    // 如果没有分组，显示提示
    if (groupIds.length === 0) {
      ElMessage.warning('请先创建元素分组并添加元素')
      availableElementsList.value = []
      linkedElementsList.value = []
      return
    }
    
    // 加载所有分组的元素
    const allElements: any[] = []
    for (const groupId of groupIds) {
      try {
        const res = await uiElementApi.list({
          group_id: groupId,
          page: 1,
          page_size: 100
        })
        if (res.data.items && res.data.items.length > 0) {
          allElements.push(...res.data.items)
        }
      } catch (error) {
        console.error(`加载分组${groupId}的元素失败:`, error)
      }
    }
    
    availableElementsList.value = allElements
  } catch (error) {
    ElMessage.error('加载元素列表失败')
    console.error(error)
  }
  
  // 加载已关联元素列表（从详情API获取）
  try {
    const detailRes = await uiPageObjectApi.get(row.id)
    const elements = detailRes.data.elements || []
    linkedElementsList.value = elements.map((el: any) => ({
      element_id: el.id,
      element_name: el.name,
      method_name: el.method_name || el.name.replace(/\s+/g, '_').toLowerCase(),
      is_property: el.is_property || false,
      order_num: el.order_num || 0
    }))
  } catch (error) {
    ElMessage.error('加载已关联元素失败')
    console.error(error)
    linkedElementsList.value = []
  }
}

// 可用元素选择变化
const handleAvailableElementsSelectionChange = (selection: any[]) => {
  selectedAvailableElements.value = selection
}

// 已关联元素选择变化
const handleLinkedElementsSelectionChange = (selection: any[]) => {
  selectedLinkedElements.value = selection
}

// 添加元素
const handleAddElements = () => {
  selectedAvailableElements.value.forEach((element: any) => {
    // 检查是否已存在
    const exists = linkedElementsList.value.some((item: any) => item.element_id === element.id)
    if (!exists) {
      linkedElementsList.value.push({
        element_id: element.id,
        element_name: element.name,
        method_name: element.name.replace(/\s+/g, '_').toLowerCase(),
        is_property: false,
        order_num: linkedElementsList.value.length
      })
    }
  })
  selectedAvailableElements.value = []
}

// 移除单个元素
const handleRemoveElement = (index: number) => {
  linkedElementsList.value.splice(index, 1)
}

// 移除选中元素
const handleRemoveSelectedElements = () => {
  const selectedIds = selectedLinkedElements.value.map((item: any) => item.element_id)
  linkedElementsList.value = linkedElementsList.value.filter(
    (item: any) => !selectedIds.includes(item.element_id)
  )
  selectedLinkedElements.value = []
}

// 保存元素关联
const handleSaveElements = async () => {
  elementsSubmitLoading.value = true
  try {
    // 构建元素数据
    const elements = linkedElementsList.value.map((item: any) => ({
      element_id: item.element_id,
      method_name: item.method_name || '',
      is_property: item.is_property || false,
      order_num: item.order_num || 0
    }))
    
    console.log('保存元素关联:', {
      page_object_id: currentPageObjectId.value,
      elements: elements,
      count: elements.length
    })
    
    await uiPageObjectApi.update(currentPageObjectId.value, { elements })
    ElMessage.success('保存成功')
    elementsDialogVisible.value = false
    loadPageObjectList()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    elementsSubmitLoading.value = false
  }
}

// 生成代码
const handleGenerateCode = (row: any) => {
  currentCodePageObjectId.value = row.id
  currentPageObjectName.value = row.name
  codeDialogVisible.value = true
}

// 提交代码生成
const handleGenerateCodeSubmit = async () => {
  codeLoading.value = true
  try {
    const res = await uiPageObjectApi.generateCode(currentCodePageObjectId.value, codeForm)
    generatedCode.value = res.data.code || ''
    codeDialogVisible.value = false
    codePreviewVisible.value = true
    ElMessage.success('代码生成成功')
  } catch (error) {
    ElMessage.error('代码生成失败')
    console.error(error)
  } finally {
    codeLoading.value = false
  }
}

// 预览代码
const handlePreviewCode = async (row: any) => {
  currentPageObjectName.value = row.name
  try {
    const res = await uiPageObjectApi.previewCode(row.id, {
      language: 'javascript',
      framework: 'playwright',
      include_comments: true
    })
    generatedCode.value = res.data.code || ''
    codePreviewVisible.value = true
  } catch (error) {
    ElMessage.error('预览代码失败')
    console.error(error)
  }
}

// 复制代码
const handleCopyCode = async () => {
  try {
    // 尝试使用现代 Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(generatedCode.value)
      ElMessage.success('代码已复制到剪贴板')
    } else {
      // 降级方案：使用 execCommand
      const textArea = document.createElement('textarea')
      textArea.value = generatedCode.value
      textArea.style.position = 'fixed'
      textArea.style.left = '-999999px'
      textArea.style.top = '-999999px'
      document.body.appendChild(textArea)
      textArea.focus()
      textArea.select()
      
      try {
        const successful = document.execCommand('copy')
        if (successful) {
          ElMessage.success('代码已复制到剪贴板')
        } else {
          ElMessage.error('复制失败，请手动复制')
        }
      } catch (err) {
        console.error('复制失败:', err)
        ElMessage.error('复制失败，请手动复制')
      } finally {
        document.body.removeChild(textArea)
      }
    }
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 下载代码
const handleDownloadCode = () => {
  const blob = new Blob([generatedCode.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentPageObjectName.value}.js`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('代码已下载')
}

// 批量生成代码
const handleBatchGenerateCode = () => {
  ElMessage.info('批量生成代码功能开发中...')
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedPageObjects.value.length === 0) {
    ElMessage.warning('请先选择要删除的页面对象')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedPageObjects.value.length} 个页面对象吗？此操作不可恢复。`,
    '批量删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      dangerouslyUseHTMLString: true
    }
  ).then(async () => {
    const loading = ElLoading.service({
      lock: true,
      text: `正在删除 ${selectedPageObjects.value.length} 个页面对象...`,
      background: 'rgba(0, 0, 0, 0.7)'
    })
    
    try {
      let successCount = 0
      let failCount = 0
      const errors: string[] = []
      
      // 逐个删除
      for (const pageObject of selectedPageObjects.value) {
        try {
          await uiPageObjectApi.delete(pageObject.id)
          successCount++
        } catch (error: any) {
          failCount++
          errors.push(`${pageObject.name}: ${error?.response?.data?.detail || '删除失败'}`)
        }
      }
      
      loading.close()
      
      if (failCount === 0) {
        ElMessage.success(`成功删除 ${successCount} 个页面对象`)
      } else {
        const errorMsg = errors.length > 0 ? `\n失败详情：\n${errors.join('\n')}` : ''
        ElMessageBox.alert(
          `删除完成：成功 ${successCount} 个，失败 ${failCount} 个${errorMsg}`,
          '批量删除结果',
          {
            confirmButtonText: '确定',
            type: failCount > 0 ? 'warning' : 'success'
          }
        )
      }
      
      // 刷新列表
      loadPageObjectList()
      // 清空选择
      selectedPageObjects.value = []
    } catch (error) {
      loading.close()
      ElMessage.error('批量删除失败')
      console.error(error)
    }
  })
}

// 初始化
onMounted(() => {
  loadPageObjectList()
})
</script>

<style scoped lang="scss">
.page-object-manage {
  .toolbar {
    display: flex;
    gap: 10px;
  }

  .elements-manage-container {
    display: flex;
    gap: 20px;
    height: 500px;
    overflow: hidden;

    .available-elements,
    .linked-elements {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        font-weight: 600;
        font-size: 14px;
        flex-shrink: 0;
        color: var(--el-text-color-primary);
        padding-bottom: 8px;
        border-bottom: 1px solid var(--el-border-color-light);
      }
      
      // 表格容器样式
      :deep(.el-table) {
        flex: 1;
        min-height: 0;
        
        // 当表格为空时的样式
        .el-table__empty-block {
          min-height: 100px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .el-table__empty-text {
          color: var(--el-text-color-placeholder);
          font-size: 14px;
        }
      }
      
      // 按钮区域样式
      .button-area {
        margin-top: 15px;
        text-align: center;
        flex-shrink: 0;
        padding-top: 12px;
        border-top: 1px solid var(--el-border-color-lighter);
      }
    }

    // 左侧可用元素区域特殊样式
    .available-elements {
      .button-area {
        .el-button {
          width: 140px;
        }
      }
    }

    // 右侧已关联元素区域特殊样式
    .linked-elements {
      .section-header {
        .el-button {
          margin-left: 10px;
        }
      }
    }
  }

  .code-preview-container {
    .code-actions {
      margin-bottom: 15px;
      display: flex;
      gap: 10px;
    }

    .code-content {
      pre {
        background-color: var(--el-fill-color-light);
        padding: 15px;
        border-radius: var(--el-border-radius-base);
        overflow-x: auto;
        max-height: 500px;
        margin: 0;
        border: 1px solid var(--el-border-color-light);

        code {
          font-family: 'Courier New', Courier, monospace;
          font-size: 13px;
          line-height: 1.5;
          color: var(--el-text-color-primary);
        }
      }
    }
  }

  // 紧凑型输入数字组件
  :deep(.compact-input-number) {
    width: 70px;
    
    .el-input__inner {
      padding: 0 8px;
      text-align: center;
    }
  }

  // 空状态样式
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: var(--el-text-color-placeholder);

    p {
      margin: 10px 0 5px 0;
      font-size: 14px;
      color: var(--el-text-color-regular);
      
      &.empty-tip {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
      }
    }
  }
}
</style>
