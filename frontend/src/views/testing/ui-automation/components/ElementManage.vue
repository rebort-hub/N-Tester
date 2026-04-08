<template>
  <div class="element-manage">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建元素</el-button>
      <el-button type="success" :icon="Check" @click="handleValidateLocator">验证定位器</el-button>
      <el-button type="danger" :icon="Delete" @click="handleBatchDelete" :disabled="selectedElements.length === 0">批量删除</el-button>
      <el-button :icon="Refresh" @click="loadElementList">刷新</el-button>
    </div>

    <!-- 元素列表 -->
    <el-table ref="tableRef" :data="elementList" v-loading="loading" border stripe style="margin-top: 15px" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="元素名称" min-width="150" />
      <el-table-column prop="element_type" label="元素类型" width="100">
        <template #default="{ row }">
          <el-tag>{{ getElementTypeName(row.element_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="locator_strategy" label="定位策略" width="100">
        <template #default="{ row }">
          <el-tag type="success">{{ row.locator_strategy }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="locator_value" label="定位器值" min-width="200" show-overflow-tooltip />
      <el-table-column prop="wait_time" label="等待时间(ms)" width="120" />
      <el-table-column prop="is_dynamic" label="动态元素" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_dynamic ? 'warning' : 'info'">
            {{ row.is_dynamic ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="success" size="small" @click="handleValidate(row)">验证</el-button>
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
      @size-change="loadElementList"
      @current-change="loadElementList"
      style="margin-top: 15px; justify-content: flex-end"
    />

    <!-- 元素对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="元素名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入元素名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="2" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="元素类型" prop="element_type">
          <el-select v-model="formData.element_type" placeholder="请选择元素类型" style="width: 100%">
            <el-option label="按钮" value="button" />
            <el-option label="输入框" value="input" />
            <el-option label="链接" value="link" />
            <el-option label="文本" value="text" />
            <el-option label="图片" value="image" />
            <el-option label="下拉框" value="select" />
            <el-option label="复选框" value="checkbox" />
            <el-option label="单选框" value="radio" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="定位策略" prop="locator_strategy">
          <el-select v-model="formData.locator_strategy" placeholder="请选择定位策略" style="width: 100%">
            <el-option-group label="通用策略（Selenium + Playwright）">
              <el-option label="CSS选择器 (css)" value="css">
                <span style="float: left">CSS选择器</span>
                <span style="float: right; color: #67c23a; font-size: 13px">✓ 推荐</span>
              </el-option>
              <el-option label="XPath" value="xpath">
                <span style="float: left">XPath</span>
                <span style="float: right; color: #409eff; font-size: 13px">✓ 强大</span>
              </el-option>
              <el-option label="ID" value="id">
                <span style="float: left">ID</span>
                <span style="float: right; color: #e6a23c; font-size: 13px">✓ 最快</span>
              </el-option>
              <el-option label="Name" value="name" />
              <el-option label="Text (文本内容)" value="text" />
            </el-option-group>
            
            <el-option-group label="Selenium 专用">
              <el-option label="Class Name" value="class" />
              <el-option label="Tag Name" value="tag" />
              <el-option label="Link Text (完全匹配)" value="link text" />
              <el-option label="Partial Link Text (部分匹配)" value="partial link text" />
            </el-option-group>
            
            <el-option-group label="Playwright 专用">
              <el-option label="Placeholder (占位符)" value="placeholder" />
              <el-option label="Role (角色)" value="role" />
              <el-option label="Label (标签)" value="label" />
              <el-option label="Title (标题)" value="title" />
              <el-option label="Test ID (测试ID)" value="test-id" />
            </el-option-group>
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            <div v-if="formData.locator_strategy === 'css'">
              <strong>CSS选择器示例：</strong><br/>
              • #username - ID选择器<br/>
              • .btn-primary - Class选择器<br/>
              • input[name="email"] - 属性选择器<br/>
              • div > button:first-child - 组合选择器
            </div>
            <div v-else-if="formData.locator_strategy === 'xpath'">
              <strong>XPath示例：</strong><br/>
              • //input[@id='username'] - 通过ID<br/>
              • //button[contains(text(),'登录')] - 包含文本<br/>
              • //div[@class='form']//input[1] - 层级定位<br/>
              • //a[starts-with(@href,'http')] - 属性匹配
            </div>
            <div v-else-if="formData.locator_strategy === 'id'">
              <strong>ID示例：</strong> username, submit-btn, login-form<br/>
              <span style="color: #67c23a;">✓ 最快速的定位方式</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'name'">
              <strong>Name示例：</strong> email, password, phone<br/>
              <span style="color: #409eff;">适用于表单元素</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'class'">
              <strong>Class Name示例：</strong> btn-primary, form-control, alert-danger<br/>
              <span style="color: #e6a23c;">⚠ Selenium专用</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'tag'">
              <strong>Tag Name示例：</strong> button, input, div, span<br/>
              <span style="color: #e6a23c;">⚠ Selenium专用，不够精确</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'link text'">
              <strong>Link Text示例：</strong> 登录, 注册, 返回首页<br/>
              <span style="color: #e6a23c;">⚠ Selenium专用，完全匹配链接文本</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'partial link text'">
              <strong>Partial Link Text示例：</strong> 登, 注, 首页<br/>
              <span style="color: #e6a23c;">⚠ Selenium专用，部分匹配链接文本</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'text'">
              <strong>Text示例：</strong> 登录, 提交, 确认<br/>
              <span style="color: #409eff;">• Selenium: 自动转换为 XPath</span><br/>
              <span style="color: #409eff;">• Playwright: 使用 text= 语法</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'placeholder'">
              <strong>Placeholder示例：</strong> 请输入用户名, Enter email<br/>
              <span style="color: #67c23a;">✓ Playwright专用，适用于输入框</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'role'">
              <strong>Role示例：</strong> button, textbox, link, heading<br/>
              <span style="color: #67c23a;">✓ Playwright专用，基于ARIA角色</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'label'">
              <strong>Label示例：</strong> 用户名, 密码, 邮箱<br/>
              <span style="color: #67c23a;">✓ Playwright专用，通过标签文本定位</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'title'">
              <strong>Title示例：</strong> 点击登录, 返回上一页<br/>
              <span style="color: #67c23a;">✓ Playwright专用，通过title属性</span>
            </div>
            <div v-else-if="formData.locator_strategy === 'test-id'">
              <strong>Test ID示例：</strong> login-btn, user-input, submit-form<br/>
              <span style="color: #67c23a;">✓ Playwright专用，使用data-testid属性</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="定位器值" prop="locator_value">
          <el-input v-model="formData.locator_value" placeholder="例如: #username" />
        </el-form-item>
        <el-form-item label="等待时间(ms)" prop="wait_time">
          <el-input-number v-model="formData.wait_time" :min="0" :max="60000" :step="1000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="动态元素">
          <el-switch v-model="formData.is_dynamic" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            动态元素需要等待加载完成
          </span>
        </el-form-item>
        <el-form-item label="备用定位器">
          <el-button size="small" @click="handleAddBackupLocator">添加备用定位器</el-button>
          <div v-for="(locator, index) in formData.backup_locators" :key="index" style="margin-top: 10px">
            <el-row :gutter="10">
              <el-col :span="8">
                <el-select v-model="locator.strategy" placeholder="策略" size="small">
                  <el-option-group label="通用策略">
                    <el-option label="CSS" value="css" />
                    <el-option label="XPath" value="xpath" />
                    <el-option label="ID" value="id" />
                    <el-option label="Name" value="name" />
                    <el-option label="Text" value="text" />
                  </el-option-group>
                  <el-option-group label="Selenium">
                    <el-option label="Class" value="class" />
                    <el-option label="Tag" value="tag" />
                    <el-option label="Link Text" value="link text" />
                    <el-option label="Partial Link" value="partial link text" />
                  </el-option-group>
                  <el-option-group label="Playwright">
                    <el-option label="Placeholder" value="placeholder" />
                    <el-option label="Role" value="role" />
                    <el-option label="Label" value="label" />
                    <el-option label="Title" value="title" />
                    <el-option label="Test ID" value="test-id" />
                  </el-option-group>
                </el-select>
              </el-col>
              <el-col :span="14">
                <el-input v-model="locator.value" placeholder="定位器值" size="small" />
              </el-col>
              <el-col :span="2">
                <el-button size="small" type="danger" :icon="Delete" @click="handleRemoveBackupLocator(index)" />
              </el-col>
            </el-row>
          </div>
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
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Plus, Check, Refresh, Delete } from '@element-plus/icons-vue'
import { useUiAutomationApi } from '/@/api/v1/ui_automation'

const { uiElementApi } = useUiAutomationApi()

const props = defineProps<{
  uiProjectId: number
  groupId: number | null
}>()

const emit = defineEmits(['refresh'])

// 表格数据
const tableRef = ref()
const elementList = ref([])
const loading = ref(false)
const selectedElements = ref([])

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新建元素')
const formRef = ref()
const submitLoading = ref(false)

// 表单数据
const formData = reactive({
  id: null,
  group_id: props.groupId,
  name: '',
  description: '',
  element_type: 'button',
  locator_strategy: 'css',
  locator_value: '',
  backup_locators: [],
  wait_time: 5000,
  is_dynamic: false,
  screenshot: ''
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入元素名称', trigger: 'blur' }],
  element_type: [{ required: true, message: '请选择元素类型', trigger: 'change' }],
  locator_strategy: [{ required: true, message: '请选择定位策略', trigger: 'change' }],
  locator_value: [{ required: true, message: '请输入定位器值', trigger: 'blur' }],
  wait_time: [{ required: true, message: '请输入等待时间', trigger: 'blur' }]
}

// 元素类型映射
const getElementTypeName = (type: string) => {
  const types: any = {
    button: '按钮',
    input: '输入框',
    link: '链接',
    text: '文本',
    image: '图片',
    select: '下拉框',
    checkbox: '复选框',
    radio: '单选框',
    other: '其他'
  }
  return types[type] || type
}

// 加载元素列表
const loadElementList = async () => {
  if (!props.groupId) {
    elementList.value = []
    return
  }
  
  loading.value = true
  try {
    const res = await uiElementApi.list({
      group_id: props.groupId,
      page: pagination.page,
      page_size: pagination.page_size
    })
    elementList.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (error) {
    ElMessage.error('加载元素列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 监听分组变化
watch(() => props.groupId, () => {
  pagination.page = 1
  loadElementList()
})

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedElements.value = selection
}

// 新建
const handleCreate = () => {
  if (!props.groupId) {
    ElMessage.warning('请先选择元素分组')
    return
  }
  
  dialogTitle.value = '新建元素'
  Object.assign(formData, {
    id: null,
    group_id: props.groupId,
    name: '',
    description: '',
    element_type: 'button',
    locator_strategy: 'css',
    locator_value: '',
    backup_locators: [],
    wait_time: 5000,
    is_dynamic: false,
    screenshot: ''
  })
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑元素'
  Object.assign(formData, {
    ...row,
    backup_locators: row.backup_locators || []
  })
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  await formRef.value.validate()
  submitLoading.value = true
  try {
    if (formData.id) {
      await uiElementApi.update(formData.id, formData)
      ElMessage.success('更新成功')
    } else {
      await uiElementApi.create(formData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadElementList()
    emit('refresh')
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    submitLoading.value = false
  }
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm('确定要删除该元素吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiElementApi.delete(row.id)
      ElMessage.success('删除成功')
      loadElementList()
      emit('refresh')
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 验证单个元素定位器
const handleValidate = async (row: any) => {
  // 弹出对话框让用户输入URL
  ElMessageBox.prompt('请输入要验证的页面URL', '验证元素定位器', {
    confirmButtonText: '验证',
    cancelButtonText: '取消',
    inputPlaceholder: '例如: https://example.com',
    inputValidator: (value) => {
      if (!value) {
        return '请输入URL'
      }
      if (!value.startsWith('http://') && !value.startsWith('https://')) {
        return 'URL必须以http://或https://开头'
      }
      return true
    }
  }).then(async ({ value }) => {
    try {
      const res = await uiElementApi.validateLocator({
        url: value,
        locator_strategy: row.locator_strategy,
        locator_value: row.locator_value
      })
      // 后端返回的字段是 is_valid，不是 valid
      if (res.data.is_valid) {
        ElMessage.success(res.data.message || '定位器验证通过')
      } else {
        ElMessage.warning(res.data.message || '定位器验证失败')
      }
    } catch (error: any) {
      const errorMsg = error?.response?.data?.detail || error?.message || '验证失败'
      ElMessage.error(errorMsg)
      console.error(error)
    }
  }).catch(() => {
    // 用户取消
  })
}

// 批量验证定位器
const handleValidateLocator = async () => {
  // 获取选中的元素
  const selectedRows = tableRef.value?.getSelectionRows() || []
  
  if (selectedRows.length === 0) {
    ElMessage.warning('请先选择要验证的元素')
    return
  }
  
  // 弹出对话框让用户输入URL
  ElMessageBox.prompt('请输入要验证的页面URL', '批量验证定位器', {
    confirmButtonText: '开始验证',
    cancelButtonText: '取消',
    inputPlaceholder: '例如: https://example.com',
    inputValidator: (value) => {
      if (!value) {
        return '请输入URL'
      }
      if (!value.startsWith('http://') && !value.startsWith('https://')) {
        return 'URL必须以http://或https://开头'
      }
      return true
    }
  }).then(async ({ value: url }) => {
    const loading = ElLoading.service({
      lock: true,
      text: `正在验证 ${selectedRows.length} 个元素...`,
      background: 'rgba(0, 0, 0, 0.7)'
    })
    
    try {
      let successCount = 0
      let failCount = 0
      const results: any[] = []
      
      // 逐个验证
      for (const row of selectedRows) {
        try {
          const res = await uiElementApi.validateLocator({
            url,
            locator_strategy: row.locator_strategy,
            locator_value: row.locator_value
          })
          
          if (res.data.is_valid) {
            successCount++
            results.push({
              name: row.name,
              status: 'success',
              message: res.data.message
            })
          } else {
            failCount++
            results.push({
              name: row.name,
              status: 'fail',
              message: res.data.message
            })
          }
        } catch (error: any) {
          failCount++
          results.push({
            name: row.name,
            status: 'error',
            message: error?.response?.data?.detail || '验证失败'
          })
        }
      }
      
      loading.close()
      
      // 显示验证结果
      const resultHtml = results.map(r => {
        const icon = r.status === 'success' ? '✅' : '❌'
        return `<div style="text-align: left; margin: 5px 0;">${icon} ${r.name}: ${r.message}</div>`
      }).join('')
      
      ElMessageBox.alert(
        `<div style="max-height: 400px; overflow-y: auto;">
          <p><strong>验证完成：</strong></p>
          <p>成功: ${successCount} 个，失败: ${failCount} 个</p>
          <hr/>
          ${resultHtml}
        </div>`,
        '批量验证结果',
        {
          dangerouslyUseHTMLString: true,
          confirmButtonText: '确定'
        }
      )
    } catch (error) {
      loading.close()
      ElMessage.error('批量验证失败')
      console.error(error)
    }
  }).catch(() => {
    // 用户取消
  })
}

// 添加备用定位器
const handleAddBackupLocator = () => {
  formData.backup_locators.push({
    strategy: 'css',
    value: ''
  })
}

// 删除备用定位器
const handleRemoveBackupLocator = (index: number) => {
  formData.backup_locators.splice(index, 1)
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedElements.value.length === 0) {
    ElMessage.warning('请先选择要删除的元素')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedElements.value.length} 个元素吗？此操作不可恢复。`,
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
      text: `正在删除 ${selectedElements.value.length} 个元素...`,
      background: 'rgba(0, 0, 0, 0.7)'
    })
    
    try {
      let successCount = 0
      let failCount = 0
      const errors: string[] = []
      
      // 逐个删除
      for (const element of selectedElements.value) {
        try {
          await uiElementApi.delete(element.id)
          successCount++
        } catch (error: any) {
          failCount++
          errors.push(`${element.name}: ${error?.response?.data?.detail || '删除失败'}`)
        }
      }
      
      loading.close()
      
      if (failCount === 0) {
        ElMessage.success(`成功删除 ${successCount} 个元素`)
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
      loadElementList()
      emit('refresh')
      // 清空选择
      selectedElements.value = []
    } catch (error) {
      loading.close()
      ElMessage.error('批量删除失败')
      console.error(error)
    }
  })
}

// 初始化
onMounted(() => {
  if (props.groupId) {
    loadElementList()
  }
})
</script>

<style scoped lang="scss">
.element-manage {
  .toolbar {
    display: flex;
    gap: 10px;
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
