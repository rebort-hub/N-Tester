<template>
  <div class="ui-automation-manage" v-if="projectId && !isNaN(projectId)">
    <!-- 顶部面包屑和操作栏 -->
    <el-card shadow="hover" class="header-card">
      <div class="header-content">
        <div class="breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/testing/ui-automation/index' }">UI自动化</el-breadcrumb-item>
            <el-breadcrumb-item>{{ projectInfo.name || '项目管理' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="actions">
          <el-button type="primary" :icon="VideoPlay" @click="handleExecute">执行测试</el-button>
          <el-button type="success" :icon="Document" @click="handleViewReport">查看报告</el-button>
          <el-button :icon="Back" @click="handleBack">返回</el-button>
        </div>
      </div>
    </el-card>

    <!-- 主内容区 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 左侧：元素分组树 -->
      <el-col :span="6">
        <el-card shadow="hover" class="tree-card">
          <template #header>
            <div class="card-header">
              <span>元素分组</span>
              <el-button type="primary" size="small" :icon="Plus" @click="handleAddGroup">新建分组</el-button>
            </div>
          </template>
          <el-tree
            :data="elementGroupTree"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            :expand-on-click-node="false"
            @node-click="handleGroupClick"
          >
            <template #default="{ node, data }">
              <div class="tree-node">
                <span class="tree-node-label">
                  <el-icon class="folder-icon"><Folder /></el-icon>
                  <span>{{ node.label }}</span>
                </span>
                <span class="tree-node-actions">
                  <el-button link type="primary" size="small" @click.stop="handleEditGroup(data)">编辑</el-button>
                  <el-button link type="danger" size="small" @click.stop="handleDeleteGroup(data)">删除</el-button>
                </span>
              </div>
            </template>
          </el-tree>
        </el-card>
      </el-col>

      <!-- 右侧：Tab页 -->
      <el-col :span="18">
        <el-card shadow="hover">
          <el-tabs v-model="activeTab" @tab-change="handleTabChange">
            <!-- 元素管理 -->
            <el-tab-pane label="元素管理" name="elements">
              <ElementManage :ui-project-id="projectId" :group-id="selectedGroupId" @refresh="loadElementGroupTree" />
            </el-tab-pane>

            <!-- 页面对象 -->
            <el-tab-pane label="页面对象" name="pageObjects">
              <PageObjectManage :ui-project-id="projectId" />
            </el-tab-pane>

            <!-- 测试用例 -->
            <el-tab-pane label="测试用例" name="testCases">
              <TestCaseManage :ui-project-id="projectId" />
            </el-tab-pane>

            <!-- 测试套件 -->
            <el-tab-pane label="测试套件" name="testSuites">
              <TestSuiteManage ref="testSuiteManageRef" :ui-project-id="projectId" />
            </el-tab-pane>

            <!-- 执行历史 -->
            <el-tab-pane label="执行历史" name="executions">
              <ExecutionHistory :ui-project-id="projectId" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分组对话框 -->
    <el-dialog
      v-model="groupDialogVisible"
      :title="groupDialogTitle"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="groupForm" :rules="groupRules" ref="groupFormRef" label-width="100px">
        <el-form-item label="分组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="请输入分组名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="groupForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="父分组">
          <el-tree-select
            v-model="groupForm.parent_id"
            :data="filteredGroupTree"
            :props="{ label: 'name', children: 'children', value: 'id' }"
            node-key="id"
            check-strictly
            clearable
            placeholder="请选择父分组（可选，支持多级分组）"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="groupForm.order_num" :min="0" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="groupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleGroupSubmit" :loading="groupSubmitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
  <div v-else class="error-container">
    <el-result icon="error" title="无效的项目ID" sub-title="请从UI自动化列表页面进入">
      <template #extra>
        <el-button type="primary" @click="router.push('/testing/ui-automation/index')">返回列表</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, VideoPlay, Document, Back, Folder } from '@element-plus/icons-vue'
import { useUiAutomationApi } from '/@/api/v1/ui_automation'
import ElementManage from './components/ElementManage.vue'
import PageObjectManage from './components/PageObjectManage.vue'
import TestCaseManage from './components/TestCaseManage.vue'
import TestSuiteManage from './components/TestSuiteManage.vue'
import ExecutionHistory from './components/ExecutionHistory.vue'

const { uiProjectApi, uiElementGroupApi } = useUiAutomationApi()

const route = useRoute()
const router = useRouter()

// 从路由参数获取UI项目ID
const projectId = ref(Number(route.query.id))

// 验证projectId是否有效
if (!projectId.value || isNaN(projectId.value)) {
  ElMessage.error('无效的项目ID')
  router.push({ path: '/testing/ui-automation/index' })
}

const projectInfo = ref<any>({})
const activeTab = ref('elements')
const selectedGroupId = ref<number | null>(null)
const testSuiteManageRef = ref()

// 元素分组树
const elementGroupTree = ref([])

// 过滤后的分组树（编辑时排除当前分组及其子分组）
const filteredGroupTree = computed(() => {
  if (!groupForm.id) {
    return elementGroupTree.value
  }
  
  // 递归过滤函数
  const filterTree = (nodes: any[]): any[] => {
    return nodes
      .filter(node => node.id !== groupForm.id)
      .map(node => ({
        ...node,
        children: node.children ? filterTree(node.children) : []
      }))
  }
  
  return filterTree(elementGroupTree.value)
})

// 分组对话框
const groupDialogVisible = ref(false)
const groupDialogTitle = ref('新建分组')
const groupFormRef = ref()
const groupSubmitLoading = ref(false)

const groupForm = reactive({
  id: null,
  ui_project_id: projectId.value,
  name: '',
  description: '',
  parent_id: null,
  order_num: 0
})

const groupRules = {
  name: [{ required: true, message: '请输入分组名称', trigger: 'blur' }]
}

// 加载项目信息
const loadProjectInfo = async () => {
  if (!projectId.value || isNaN(projectId.value)) {
    return
  }
  try {
    const res = await uiProjectApi.get(projectId.value)
    projectInfo.value = res.data
  } catch (error) {
    ElMessage.error('加载项目信息失败')
    console.error(error)
  }
}

// 加载元素分组树
const loadElementGroupTree = async () => {
  if (!projectId.value || isNaN(projectId.value)) {
    return
  }
  try {
    const res = await uiElementGroupApi.tree(projectId.value)
    elementGroupTree.value = res.data || []
  } catch (error) {
    ElMessage.error('加载元素分组失败')
    console.error(error)
  }
}

// 分组点击
const handleGroupClick = (data: any) => {
  selectedGroupId.value = data.id
}

// Tab切换
const handleTabChange = (name: string) => {
  console.log('切换到:', name)
}

// 新建分组
const handleAddGroup = () => {
  groupDialogTitle.value = '新建分组'
  Object.assign(groupForm, {
    id: null,
    ui_project_id: projectId.value,
    name: '',
    description: '',
    parent_id: null,
    order_num: 0
  })
  groupDialogVisible.value = true
}

// 编辑分组
const handleEditGroup = (data: any) => {
  groupDialogTitle.value = '编辑分组'
  Object.assign(groupForm, data)
  groupDialogVisible.value = true
}

// 删除分组
const handleDeleteGroup = (data: any) => {
  // 检查是否有子分组
  if (data.children && data.children.length > 0) {
    ElMessage.warning('该分组下存在子分组，请先删除子分组')
    return
  }
  
  ElMessageBox.confirm('确定要删除该分组吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await uiElementGroupApi.delete(data.id)
      ElMessage.success('删除成功')
      loadElementGroupTree()
    } catch (error) {
      ElMessage.error('删除失败')
      console.error(error)
    }
  })
}

// 提交分组表单
const handleGroupSubmit = async () => {
  await groupFormRef.value.validate()
  groupSubmitLoading.value = true
  try {
    if (groupForm.id) {
      await uiElementGroupApi.update(groupForm.id, groupForm)
      ElMessage.success('更新成功')
    } else {
      await uiElementGroupApi.create(groupForm)
      ElMessage.success('创建成功')
    }
    groupDialogVisible.value = false
    loadElementGroupTree()
  } catch (error) {
    ElMessage.error('操作失败')
    console.error(error)
  } finally {
    groupSubmitLoading.value = false
  }
}

// 执行测试
const handleExecute = () => {
  // 切换到测试套件标签页
  activeTab.value = 'testSuites'
  
  // 等待组件渲染完成后调用批量执行
  nextTick(() => {
    if (testSuiteManageRef.value && testSuiteManageRef.value.handleBatchExecute) {
      testSuiteManageRef.value.handleBatchExecute()
    } else {
      ElMessage.info('请在测试套件中选择要执行的套件')
    }
  })
}

// 查看报告
const handleViewReport = () => {
  router.push('/testing/ui-automation/report')
}

// 返回
const handleBack = () => {
  router.push({ path: '/testing/ui-automation/index' })
}

// 初始化
onMounted(() => {
  loadProjectInfo()
  loadElementGroupTree()
})
</script>

<style scoped lang="scss">
.ui-automation-manage {
  padding: 20px;

  .header-card {
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .breadcrumb {
        font-size: 16px;
      }
    }
  }

  .tree-card {
    height: calc(100vh - 200px);
    overflow-y: auto;

    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .tree-node {
      flex: 1;
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-right: 10px;

      .tree-node-label {
        display: flex;
        align-items: center;
        gap: 6px;

        .folder-icon {
          color: #409eff;
          font-size: 16px;
        }
      }

      .tree-node-actions {
        display: none;
      }

      &:hover .tree-node-actions {
        display: inline-block;
      }
    }
  }
}

.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 20px;
}
</style>
