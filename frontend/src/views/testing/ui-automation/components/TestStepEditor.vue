<template>
  <div class="test-step-editor">
    <!-- 工具栏 -->
    <div class="toolbar">
      <el-button type="primary" :icon="Plus" @click="handleAddStep">添加步骤</el-button>
      <el-button type="success" :icon="DocumentCopy" @click="handleBatchAdd">批量添加</el-button>
      <el-button type="warning" :icon="Sort" @click="handleAutoSort">自动排序</el-button>
      <el-button :icon="Refresh" @click="loadTestSteps">刷新</el-button>
      <el-divider direction="vertical" />
      <span style="color: #909399">拖拽步骤可调整顺序</span>
    </div>

    <!-- 步骤列表（可拖拽） -->
    <div class="steps-container" v-loading="loading">
      <draggable
        v-model="stepsList"
        item-key="id"
        handle=".drag-handle"
        @end="handleDragEnd"
        animation="300"
      >
        <template #item="{ element, index }">
          <div class="step-item" :class="{ 'step-error': element.hasError }">
            <!-- 拖拽手柄 -->
            <div class="drag-handle">
              <el-icon><DCaret /></el-icon>
            </div>

            <!-- 步骤序号 -->
            <div class="step-number">
              <el-tag type="info" size="large">{{ index + 1 }}</el-tag>
            </div>

            <!-- 步骤内容 -->
            <div class="step-content">
              <el-row :gutter="10">
                <el-col :span="4">
                  <el-select v-model="element.action_type" placeholder="操作类型" size="small">
                    <el-option label="导航" value="navigate" />
                    <el-option label="点击" value="click" />
                    <el-option label="输入" value="fill" />
                    <el-option label="等待" value="wait" />
                    <el-option label="滚动" value="scroll" />
                    <el-option label="悬停" value="hover" />
                    <el-option label="选择" value="select" />
                    <el-option label="勾选" value="check" />
                    <el-option label="取消勾选" value="uncheck" />
                    <el-option label="断言检查" value="assert" />
                    <el-option label="截图" value="screenshot" />
                    <el-option label="执行脚本" value="execute_script" />
                  </el-select>
                </el-col>
                <el-col :span="5">
                  <el-select
                    v-model="element.element_id"
                    placeholder="选择元素"
                    size="small"
                    filterable
                    clearable
                    :disabled="!needsElement(element.action_type)"
                  >
                    <el-option
                      v-for="elem in availableElements"
                      :key="elem.id"
                      :label="elem.name"
                      :value="elem.id"
                    >
                      <span>{{ elem.name }}</span>
                      <span style="float: right; color: #8492a6; font-size: 12px">
                        {{ elem.locator_value }}
                      </span>
                    </el-option>
                  </el-select>
                </el-col>
                <el-col :span="5">
                  <el-input
                    v-model="element.action_value"
                    placeholder="操作值"
                    size="small"
                    :disabled="!needsActionValue(element.action_type)"
                  />
                </el-col>
                <el-col :span="10">
                  <el-input
                    v-model="element.description"
                    placeholder="步骤描述"
                    size="small"
                  />
                </el-col>
              </el-row>

              <!-- 断言配置（仅在操作类型为"断言检查"时显示） -->
              <el-row :gutter="10" style="margin-top: 8px" v-if="element.action_type === 'assert'">
                <el-col :span="4">
                  <el-select v-model="element.assertion_type" placeholder="断言类型" size="small" clearable>
                    <el-option label="文本相等" value="textEquals" />
                    <el-option label="文本包含" value="textContains" />
                    <el-option label="元素可见" value="isVisible" />
                    <el-option label="元素存在" value="exists" />
                  </el-select>
                </el-col>
                <el-col :span="5">
                  <el-input
                    v-model="element.assertion_value"
                    placeholder="断言值"
                    size="small"
                    :disabled="!element.assertion_type || !needsAssertionValue(element.assertion_type)"
                  />
                </el-col>
                <el-col :span="5">
                  <el-checkbox v-model="element.screenshot_on_failure" size="small">失败时截图</el-checkbox>
                </el-col>
                <el-col :span="5">
                  <el-checkbox v-model="element.continue_on_failure" size="small">失败时继续</el-checkbox>
                </el-col>
                <el-col :span="5">
                  <div class="step-actions">
                    <el-button link type="primary" size="small" @click="handleInsertStep(index)">插入</el-button>
                    <el-button link type="success" size="small" @click="handleCopyStep(index)">复制</el-button>
                    <el-button link type="danger" size="small" @click="handleDeleteStep(index)">删除</el-button>
                  </div>
                </el-col>
              </el-row>
              
              <!-- 其他操作类型的操作按钮行 -->
              <el-row :gutter="10" style="margin-top: 8px" v-else>
                <el-col :span="24">
                  <div class="step-actions" style="justify-content: flex-end">
                    <el-button link type="primary" size="small" @click="handleInsertStep(index)">插入</el-button>
                    <el-button link type="success" size="small" @click="handleCopyStep(index)">复制</el-button>
                    <el-button link type="danger" size="small" @click="handleDeleteStep(index)">删除</el-button>
                  </div>
                </el-col>
              </el-row>
            </div>
          </div>
        </template>
      </draggable>

      <!-- 空状态 -->
      <el-empty v-if="stepsList.length === 0" description="暂无测试步骤，点击上方按钮添加" />
    </div>

    <!-- 底部操作栏 -->
    <div class="footer-actions">
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saveLoading">保存</el-button>
      <el-button type="success" @click="handleSaveAndClose" :loading="saveLoading">保存并关闭</el-button>
    </div>

    <!-- 批量添加对话框 -->
    <el-dialog
      v-model="batchDialogVisible"
      title="批量添加步骤"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-alert
        title="批量添加说明"
        type="info"
        :closable="false"
        style="margin-bottom: 15px"
      >
        <p>每行一个步骤，格式：操作类型|元素名称|操作值|描述</p>
        <p>示例：</p>
        <p>navigate||https://example.com|打开网站</p>
        <p>fill|用户名输入框|admin|输入用户名</p>
        <p>click|登录按钮||点击登录</p>
      </el-alert>
      <el-input
        v-model="batchStepsText"
        type="textarea"
        :rows="10"
        placeholder="请输入步骤，每行一个"
      />
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchAddSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, DocumentCopy, Sort, Refresh, DCaret } from '@element-plus/icons-vue'
import draggable from 'vuedraggable'
import { useUiAutomationApi } from '/@/api/v1/ui_automation'

const { uiTestStepApi, uiElementApi, uiElementGroupApi } = useUiAutomationApi()

const props = defineProps<{
  testCaseId: number
  uiProjectId: number
}>()

const emit = defineEmits(['close'])

// 步骤列表
const stepsList = ref<any[]>([])
const originalStepIds = ref<number[]>([]) // 跟踪原始步骤ID
const loading = ref(false)
const saveLoading = ref(false)

// 可用元素列表
const availableElements = ref([])

// 批量添加
const batchDialogVisible = ref(false)
const batchStepsText = ref('')

// 判断操作类型是否需要元素
const needsElement = (actionType: string) => {
  const needsElementTypes = ['click', 'fill', 'hover', 'select', 'check', 'uncheck', 'assert']
  return needsElementTypes.includes(actionType)
}

// 判断操作类型是否需要操作值
const needsActionValue = (actionType: string) => {
  const needsValueTypes = ['navigate', 'fill', 'wait', 'select', 'execute_script']
  return needsValueTypes.includes(actionType)
}

// 判断断言类型是否需要断言值
const needsAssertionValue = (assertionType: string) => {
  // textEquals 和 textContains 需要断言值
  // isVisible 和 exists 不需要断言值
  const needsValueTypes = ['textEquals', 'textContains']
  return needsValueTypes.includes(assertionType)
}

// 加载可用元素
const loadAvailableElements = async () => {
  try {
    // 加载所有元素分组
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
      availableElements.value = []
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
    
    availableElements.value = allElements
  } catch (error) {
    ElMessage.error('加载元素列表失败')
    console.error(error)
  }
}

// 加载测试步骤
const loadTestSteps = async () => {
  loading.value = true
  try {
    const res = await uiTestStepApi.listByCase(props.testCaseId)
    stepsList.value = (res.data || []).map((step: any) => ({
      ...step,
      hasError: false
    }))
    // 保存原始步骤ID列表
    originalStepIds.value = stepsList.value.map(step => step.id).filter(id => id)
  } catch (error) {
    ElMessage.error('加载测试步骤失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 添加步骤
const handleAddStep = () => {
  stepsList.value.push({
    id: null,
    test_case_id: props.testCaseId,
    step_number: stepsList.value.length + 1,
    action_type: 'navigate',
    element_id: null,
    action_value: '',
    description: '',
    assertion_type: null,
    assertion_value: '',
    screenshot_on_failure: true,
    continue_on_failure: false,
    hasError: false
  })
}

// 插入步骤
const handleInsertStep = (index: number) => {
  stepsList.value.splice(index + 1, 0, {
    id: null,
    test_case_id: props.testCaseId,
    step_number: index + 2,
    action_type: 'navigate',
    element_id: null,
    action_value: '',
    description: '',
    assertion_type: null,
    assertion_value: '',
    screenshot_on_failure: true,
    continue_on_failure: false,
    hasError: false
  })
  updateStepNumbers()
}

// 复制步骤
const handleCopyStep = (index: number) => {
  const step = { ...stepsList.value[index] }
  step.id = null
  step.step_number = index + 2
  stepsList.value.splice(index + 1, 0, step)
  updateStepNumbers()
}

// 删除步骤
const handleDeleteStep = (index: number) => {
  ElMessageBox.confirm('确定要删除该步骤吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    stepsList.value.splice(index, 1)
    updateStepNumbers()
    ElMessage.success('删除成功')
  })
}

// 拖拽结束
const handleDragEnd = () => {
  updateStepNumbers()
}

// 更新步骤序号
const updateStepNumbers = () => {
  stepsList.value.forEach((step, index) => {
    step.step_number = index + 1
  })
}

// 自动排序
const handleAutoSort = () => {
  updateStepNumbers()
  ElMessage.success('排序完成')
}

// 批量添加
const handleBatchAdd = () => {
  batchDialogVisible.value = true
  batchStepsText.value = ''
}

// 批量添加提交
const handleBatchAddSubmit = () => {
  const lines = batchStepsText.value.split('\n').filter(line => line.trim())
  if (lines.length === 0) {
    ElMessage.warning('请输入步骤内容')
    return
  }

  const newSteps: any[] = []
  lines.forEach((line, index) => {
    const parts = line.split('|')
    if (parts.length >= 3) {
      const actionType = parts[0].trim()
      const elementName = parts[1].trim()
      const actionValue = parts[2].trim()
      const description = parts[3] ? parts[3].trim() : ''

      // 查找元素ID
      let elementId = null
      if (elementName) {
        const element = availableElements.value.find((e: any) => e.name === elementName)
        if (element) {
          elementId = element.id
        }
      }

      newSteps.push({
        id: null,
        test_case_id: props.testCaseId,
        step_number: stepsList.value.length + index + 1,
        action_type: actionType,
        element_id: elementId,
        action_value: actionValue,
        description: description,
        assertion_type: null,
        assertion_value: '',
        screenshot_on_failure: true,
        continue_on_failure: false,
        hasError: false
      })
    }
  })

  stepsList.value.push(...newSteps)
  batchDialogVisible.value = false
  ElMessage.success(`成功添加 ${newSteps.length} 个步骤`)
}

// 验证步骤
const validateSteps = () => {
  let hasError = false
  stepsList.value.forEach(step => {
    step.hasError = false
    if (!step.action_type) {
      step.hasError = true
      hasError = true
    }
    if (needsElement(step.action_type) && !step.element_id) {
      step.hasError = true
      hasError = true
    }
    if (needsActionValue(step.action_type) && !step.action_value) {
      step.hasError = true
      hasError = true
    }
  })
  return !hasError
}

// 保存
const handleSave = async () => {
  if (!validateSteps()) {
    ElMessage.error('请完善步骤信息，红色标记的步骤有错误')
    return
  }

  saveLoading.value = true
  try {
    // 1. 找出被删除的步骤
    const currentStepIds = stepsList.value.map(step => step.id).filter(id => id)
    const deletedStepIds = originalStepIds.value.filter(id => !currentStepIds.includes(id))
    
    // 删除已移除的步骤
    for (const stepId of deletedStepIds) {
      await uiTestStepApi.delete(stepId)
    }

    // 2. 分离新建和更新的步骤
    const newSteps = stepsList.value.filter(step => !step.id)
    const updateSteps = stepsList.value.filter(step => step.id)

    // 3. 批量创建新步骤
    if (newSteps.length > 0) {
      await uiTestStepApi.batchCreate(newSteps)
    }

    // 4. 更新现有步骤
    for (const step of updateSteps) {
      await uiTestStepApi.update(step.id, step)
    }

    // 5. 调整步骤顺序（只针对已有ID的步骤）
    const stepOrders = stepsList.value.map(step => ({
      id: step.id,
      step_number: step.step_number
    })).filter(item => item.id)

    if (stepOrders.length > 0) {
      await uiTestStepApi.reorder({
        test_case_id: props.testCaseId,
        step_orders: stepOrders
      })
    }

    ElMessage.success('保存成功')
    // 重新加载步骤列表，更新originalStepIds
    await loadTestSteps()
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  } finally {
    saveLoading.value = false
  }
}

// 保存并关闭
const handleSaveAndClose = async () => {
  await handleSave()
  emit('close')
}

// 关闭
const handleClose = () => {
  emit('close')
}

// 初始化
onMounted(() => {
  loadAvailableElements()
  loadTestSteps()
})
</script>

<style scoped lang="scss">
.test-step-editor {
  .toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid var(--el-border-color);
  }

  .steps-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 10px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;

    .step-item {
      display: flex;
      gap: 10px;
      padding: 15px;
      margin-bottom: 10px;
      background-color: var(--el-bg-color);
      border: 1px solid var(--el-border-color);
      border-radius: 4px;
      transition: all 0.3s;

      &:hover {
        box-shadow: 0 2px 12px 0 var(--el-box-shadow-light);
        border-color: var(--el-border-color-hover);
      }

      &.step-error {
        border-color: var(--el-color-danger);
        background-color: var(--el-color-danger-light-9);
      }

      .drag-handle {
        display: flex;
        align-items: center;
        cursor: move;
        color: var(--el-text-color-secondary);
        font-size: 20px;

        &:hover {
          color: var(--el-color-primary);
        }
      }

      .step-number {
        display: flex;
        align-items: center;
      }

      .step-content {
        flex: 1;

        .step-actions {
          display: flex;
          gap: 5px;
          justify-content: flex-end;
        }
      }
    }
  }

  .footer-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid var(--el-border-color);
  }
}
</style>
