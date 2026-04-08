<template>
  <div class="api-testing-container">
    <!-- 顶部工具栏 -->
    <el-card shadow="hover" class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <span class="toolbar-label">项目来源：</span>
          <el-select
            v-model="currentProjectId"
            placeholder="选择项目"
            @change="handleProjectChange"
            style="width: 200px"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
          
          <span class="toolbar-label" style="margin-left: 15px">API项目来源：</span>
          <el-select
            v-model="currentApiProjectId"
            placeholder="选择API项目"
            @change="handleApiProjectChange"
            style="width: 200px"
            :key="`api-project-${apiProjectList.length}`"
          >
            <el-option
              v-for="apiProject in apiProjectList"
              :key="apiProject.id"
              :label="apiProject.name"
              :value="apiProject.id"
            />
          </el-select>
          <el-button
            type="danger"
            :icon="'ele-Delete'"
            circle
            size="small"
            :disabled="!currentApiProjectId"
            @click="handleDeleteApiProject"
            title="删除当前API项目"
            style="margin-left: 5px"
          />
          
          <span class="toolbar-label" style="margin-left: 15px">运行环境：</span>
          <el-select
            v-model="currentEnvironmentId"
            placeholder="选择环境"
            style="width: 150px"
          >
            <el-option
              v-for="env in environmentList"
              :key="env.id"
              :label="env.name"
              :value="env.id"
            />
          </el-select>
        </div>
        
        <div class="toolbar-right">
          <el-button type="primary" @click="showApiProjectDialog = true">
            <el-icon><ele-Plus /></el-icon>
            新建API项目
          </el-button>
          <el-dropdown @command="handleImportExport" style="margin-left: 10px">
            <el-button type="primary">
              <el-icon><ele-Download /></el-icon>
              导入/导出
              <el-icon class="el-icon--right"><ele-ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="exportProject" :disabled="!currentApiProjectId">
                  导出API项目
                </el-dropdown-item>
                <el-dropdown-item command="importProject" :disabled="!currentProjectId">
                  导入API项目
                </el-dropdown-item>
                <el-dropdown-item divided command="exportEnvironments" :disabled="!currentProjectId">
                  导出环境变量
                </el-dropdown-item>
                <el-dropdown-item command="importEnvironments" :disabled="!currentProjectId">
                  导入环境变量
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button type="primary" @click="showEnvironmentDialog = true">
            <el-icon><ele-Setting /></el-icon>
            环境管理
          </el-button>
          <el-button type="primary" @click="showTestSuiteDialog = true">
            <el-icon><ele-List /></el-icon>
            测试套件
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：集合和请求树 -->
      <el-card shadow="hover" class="sidebar-card">
        <template #header>
          <div class="card-header">
            <span>API集合</span>
            <el-button
              type="primary"
              size="small"
              @click="handleAddCollection"
              :disabled="!currentApiProjectId"
            >
              <el-icon><ele-Plus /></el-icon>
            </el-button>
          </div>
        </template>
        
        <el-tree
          :data="collectionTree"
          :props="treeProps"
          node-key="id"
          :expand-on-click-node="false"
          @node-click="handleNodeClick"
          :default-expand-all="true"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <span class="node-label">
                <el-icon v-if="data.type === 'collection'"><ele-Folder /></el-icon>
                <el-icon v-else :style="{ color: getMethodColor(data.method) }">
                  <ele-Document />
                </el-icon>
                <span class="method-tag" v-if="data.type === 'request'" :style="{ color: getMethodColor(data.method) }">
                  {{ data.method }}
                </span>
                {{ node.label }}
              </span>
              <span class="node-actions">
                <el-button
                  v-if="data.type === 'collection'"
                  type="primary"
                  size="small"
                  text
                  @click.stop="handleAddSubCollection(data)"
                  title="添加子集合"
                >
                  <el-icon><ele-FolderAdd /></el-icon>
                </el-button>
                <el-button
                  v-if="data.type === 'collection'"
                  type="primary"
                  size="small"
                  text
                  @click.stop="handleAddRequest(data)"
                  title="添加请求"
                >
                  <el-icon><ele-Plus /></el-icon>
                </el-button>
                <el-button
                  type="warning"
                  size="small"
                  text
                  @click.stop="handleEditNode(data)"
                  title="编辑"
                >
                  <el-icon><ele-Edit /></el-icon>
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click.stop="handleDeleteNode(data)"
                  title="删除"
                >
                  <el-icon><ele-Delete /></el-icon>
                </el-button>
              </span>
            </div>
          </template>
        </el-tree>
      </el-card>

      <!-- 右侧：请求编辑器 -->
      <el-card shadow="hover" class="editor-card" v-if="currentRequest">
        <template #header>
          <div class="card-header">
            <span>{{ currentRequest.name || '新建请求' }}</span>
            <div>
              <el-button type="primary" @click="handleSaveRequest">
                <el-icon><ele-Check /></el-icon>
                保存
              </el-button>
              <el-button type="success" @click="handleExecuteRequest" :loading="executing">
                <el-icon><ele-VideoPlay /></el-icon>
                发送
              </el-button>
            </div>
          </div>
        </template>
        
        <!-- 请求编辑器组件 -->
        <RequestEditor
          v-model="currentRequest"
          :environment-id="currentEnvironmentId"
          :project-id="currentProjectId"
          :api-project-id="currentApiProjectId"
          :response="currentResponse"
          :executing="executing"
          @execute="handleExecuteRequest"
        />
      </el-card>
      
      <!-- 空状态 -->
      <el-card shadow="hover" class="editor-card" v-else>
        <el-empty description="请选择或创建一个API请求" />
      </el-card>
    </div>

    <!-- API项目对话框 -->
    <ApiProjectDialog
      v-model="showApiProjectDialog"
      :project-id="currentProjectId"
      @success="loadApiProjects"
    />

    <!-- 集合对话框 -->
    <CollectionDialog
      v-model="showCollectionDialog"
      :api-project-id="currentApiProjectId"
      :parent-id="currentParentId"
      :collection="editingCollection"
      @success="loadCollectionTree"
    />

    <!-- 请求对话框 -->
    <RequestDialog
      v-model="showRequestDialog"
      :collection-id="currentCollectionId"
      :request="editingRequest"
      @success="loadCollectionTree"
    />

    <!-- 环境管理对话框 -->
    <EnvironmentDialog
      v-model="showEnvironmentDialog"
      :project-id="currentProjectId"
      @success="loadEnvironments"
    />

    <!-- 测试套件对话框 -->
    <TestSuiteDialog
      v-model="showTestSuiteDialog"
      :api-project-id="currentApiProjectId"
      :project-id="currentProjectId"
      @success="handleTestSuiteSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useApiTestingApi } from '/@/api/v1/api_testing'
import { useProjectApi } from '/@/api/v1/projects/project'
import RequestEditor from './components/RequestEditor.vue'
import ApiProjectDialog from './components/ApiProjectDialog.vue'
import CollectionDialog from './components/CollectionDialog.vue'
import RequestDialog from './components/RequestDialog.vue'
import EnvironmentDialog from './components/EnvironmentDialog.vue'
import TestSuiteDialog from './components/TestSuiteDialog.vue'

const projectApi = useProjectApi()
const { apiProjectApi, apiCollectionApi, apiRequestApi, apiEnvironmentApi } = useApiTestingApi()

// 项目列表
const projectList = ref<any[]>([])
const currentProjectId = ref<number>()

// API项目列表
const apiProjectList = ref<any[]>([])
const currentApiProjectId = ref<number>()

// 环境列表
const environmentList = ref<any[]>([])
const currentEnvironmentId = ref<number>()

// 集合树
const collectionTree = ref<any[]>([])
const treeProps = {
  children: 'children',
  label: 'name'
}

// 当前请求
const currentRequest = ref<any>(null)
const currentResponse = ref<any>(null)
const executing = ref(false)

// 对话框显示状态
const showApiProjectDialog = ref(false)
const showCollectionDialog = ref(false)
const showRequestDialog = ref(false)
const showEnvironmentDialog = ref(false)
const showTestSuiteDialog = ref(false)

// 编辑状态
const editingCollection = ref<any>(null)
const editingRequest = ref<any>(null)
const currentParentId = ref<number>()
const currentCollectionId = ref<number>()

// 加载项目列表
const loadProjects = async () => {
  try {
    const res = await projectApi.getList({ page: 1, page_size: 100 })
    projectList.value = res.data.items || res.data.rows || []
    if (projectList.value.length > 0) {
      currentProjectId.value = projectList.value[0].id
      await loadApiProjects()
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  }
}

// 加载API项目列表
const loadApiProjects = async () => {
  if (!currentProjectId.value) return
  
  try {
    const res = await apiProjectApi.list({ project_id: currentProjectId.value })
    console.log('API项目列表响应:', res)
    apiProjectList.value = res.data.items || []
    console.log('API项目列表:', apiProjectList.value)
    
    // 使用 nextTick 确保 DOM 更新
    await nextTick()
    
    // 如果当前选中的API项目不在列表中，或者没有选中，则选择第一个
    if (apiProjectList.value.length > 0) {
      const currentExists = apiProjectList.value.some((p: any) => p.id === currentApiProjectId.value)
      if (!currentExists || !currentApiProjectId.value) {
        currentApiProjectId.value = apiProjectList.value[0].id
      }
      await loadCollectionTree()
      await loadEnvironments()
    } else {
      // 如果没有API项目，清空当前选择
      currentApiProjectId.value = undefined
      collectionTree.value = []
    }
  } catch (error) {
    console.error('加载API项目列表失败:', error)
  }
}

// 加载集合树
const loadCollectionTree = async () => {
  if (!currentApiProjectId.value) return
  
  try {
    const res = await apiCollectionApi.tree(currentApiProjectId.value)
    collectionTree.value = buildTree(res.data || [])
  } catch (error) {
    console.error('加载集合树失败:', error)
  }
}

// 构建树形结构
const buildTree = (data: any[]) => {
  const processNode = (node: any): any => {
    const result: any = {
      ...node,
      type: 'collection',
      children: []
    }
    
    // 处理子集合
    if (node.children && node.children.length > 0) {
      result.children = node.children.map(processNode)
    }
    
    // 添加请求到children
    if (node.requests && node.requests.length > 0) {
      const requests = node.requests.map((req: any) => ({
        ...req,
        type: 'request',
        realId: req.id, // 保存真实ID
        // 使用带前缀的ID作为树节点的key，避免与集合id冲突
        id: `request_${req.id}`
      }))
      result.children = [...result.children, ...requests]
    }
    
    return result
  }
  
  return data.map(processNode)
}

// 加载环境列表
const loadEnvironments = async () => {
  if (!currentProjectId.value) return
  
  try {
    const res = await apiEnvironmentApi.list(currentProjectId.value)
    environmentList.value = res.data || []
    if (environmentList.value.length > 0 && !currentEnvironmentId.value) {
      const activeEnv = environmentList.value.find((env: any) => env.is_active)
      currentEnvironmentId.value = activeEnv?.id || environmentList.value[0].id
    }
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

// 项目切换
const handleProjectChange = async () => {
  currentApiProjectId.value = undefined
  apiProjectList.value = []
  collectionTree.value = []
  currentRequest.value = null
  await loadApiProjects()
}

// API项目切换
const handleApiProjectChange = async () => {
  collectionTree.value = []
  currentRequest.value = null
  await loadCollectionTree()
  await loadEnvironments()
}

// 删除API项目
const handleDeleteApiProject = async () => {
  if (!currentApiProjectId.value) return
  
  try {
    const currentProject = apiProjectList.value.find((p: any) => p.id === currentApiProjectId.value)
    const projectName = currentProject?.name || 'API项目'
    
    await ElMessageBox.confirm(
      `确定要删除API项目"${projectName}"吗？删除后将无法恢复，包括其下的所有集合和请求。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await apiProjectApi.delete(currentApiProjectId.value)
    ElMessage.success('删除成功')
    
    // 重新加载API项目列表
    await loadApiProjects()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除API项目失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 树节点点击
const handleNodeClick = async (data: any) => {
  if (data.type === 'request') {
    try {
      // 使用realId（真实ID）而不是带前缀的id
      const requestId = data.realId || data.id
      const res = await apiRequestApi.get(requestId)
      currentRequest.value = res.data
      currentResponse.value = null
    } catch (error) {
      ElMessage.error('加载请求详情失败')
    }
  }
}

// 添加集合
const handleAddCollection = () => {
  editingCollection.value = null
  currentParentId.value = undefined
  showCollectionDialog.value = true
}

// 添加子集合
const handleAddSubCollection = (collection: any) => {
  editingCollection.value = null
  currentParentId.value = collection.id
  showCollectionDialog.value = true
}

// 编辑节点
const handleEditNode = (data: any) => {
  if (data.type === 'collection') {
    editingCollection.value = data
    currentParentId.value = data.parent_id
    showCollectionDialog.value = true
  } else {
    // 编辑请求
    editingRequest.value = data
    currentCollectionId.value = data.collection_id
    showRequestDialog.value = true
  }
}

// 添加请求
const handleAddRequest = (collection: any) => {
  editingRequest.value = null
  currentCollectionId.value = collection.id
  showRequestDialog.value = true
}

// 删除节点
const handleDeleteNode = async (data: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除${data.type === 'collection' ? '集合' : '请求'} "${data.name}" 吗？`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (data.type === 'collection') {
      await apiCollectionApi.delete(data.id)
    } else {
      // 使用realId（真实ID）而不是带前缀的id
      const requestId = data.realId || data.id
      await apiRequestApi.delete(requestId)
    }
    
    ElMessage.success('删除成功')
    await loadCollectionTree()
    
    // 检查当前请求是否被删除
    const currentRequestId = currentRequest.value?.id
    const deletedRequestId = data.type === 'request' ? (data.realId || data.id) : null
    if (currentRequestId === deletedRequestId) {
      currentRequest.value = null
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 保存请求
const handleSaveRequest = async () => {
  if (!currentRequest.value) return
  
  try {
    if (currentRequest.value.id) {
      await apiRequestApi.update(currentRequest.value.id, currentRequest.value)
      ElMessage.success('保存成功')
    } else {
      const res = await apiRequestApi.create(currentRequest.value)
      currentRequest.value.id = res.data.id
      ElMessage.success('创建成功')
    }
    await loadCollectionTree()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

// 执行请求
const handleExecuteRequest = async () => {
  if (!currentRequest.value?.id) {
    ElMessage.warning('请先保存请求')
    return
  }
  
  executing.value = true
  try {
    const res = await apiRequestApi.execute(currentRequest.value.id, {
      environment_id: currentEnvironmentId.value
    })
    currentResponse.value = res.data
    ElMessage.success('执行成功')
  } catch (error) {
    ElMessage.error('执行失败')
  } finally {
    executing.value = false
  }
}

// 测试套件成功回调
const handleTestSuiteSuccess = () => {
  ElMessage.success('操作成功')
}

// 导入导出处理
const handleImportExport = async (command: string) => {
  switch (command) {
    case 'exportProject':
      await exportApiProject()
      break
    case 'importProject':
      await importApiProject()
      break
    case 'exportEnvironments':
      await exportEnvironments()
      break
    case 'importEnvironments':
      await importEnvironments()
      break
  }
}

// 导出API项目
const exportApiProject = async () => {
  if (!currentApiProjectId.value) return
  
  try {
    const res = await apiProjectApi.export(currentApiProjectId.value)
    const data = res.data
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = data.filename || 'api_project_export.json'
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 导入API项目
const importApiProject = async () => {
  if (!currentProjectId.value) return
  
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e: any) => {
    const file = e.target.files[0]
    if (!file) return
    
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      
      await apiProjectApi.import(currentProjectId.value!, data)
      ElMessage.success('导入成功')
      await loadApiProjects()
    } catch (error) {
      ElMessage.error('导入失败，请检查文件格式')
    }
  }
  input.click()
}

// 导出环境变量
const exportEnvironments = async () => {
  if (!currentProjectId.value) return
  
  try {
    const res = await apiEnvironmentApi.export(currentProjectId.value)
    const data = res.data
    
    // 创建下载链接
    const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = data.filename || 'environments_export.json'
    link.click()
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

// 导入环境变量
const importEnvironments = async () => {
  if (!currentProjectId.value) return
  
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = async (e: any) => {
    const file = e.target.files[0]
    if (!file) return
    
    try {
      const text = await file.text()
      const data = JSON.parse(text)
      
      await apiEnvironmentApi.import(currentProjectId.value!, data)
      ElMessage.success('导入成功')
      await loadEnvironments()
    } catch (error) {
      ElMessage.error('导入失败，请检查文件格式')
    }
  }
  input.click()
}

// 获取HTTP方法颜色
const getMethodColor = (method: string) => {
  const colors: any = {
    GET: '#61affe',
    POST: '#49cc90',
    PUT: '#fca130',
    DELETE: '#f93e3e',
    PATCH: '#50e3c2',
    HEAD: '#9012fe',
    OPTIONS: '#0d5aa7'
  }
  return colors[method] || '#999'
}

onMounted(() => {
  loadProjects()
})
</script>

<style scoped lang="scss">
.api-testing-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  
  .toolbar-card {
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .toolbar-left,
      .toolbar-right {
        display: flex;
        align-items: center;
        gap: 10px;
      }
      
      .toolbar-label {
        font-size: 14px;
        color: #606266;
        font-weight: 500;
        white-space: nowrap;
      }
    }
  }
  
  .main-content {
    flex: 1;
    display: flex;
    gap: 10px;
    overflow: hidden;
    
    .sidebar-card {
      width: 300px;
      display: flex;
      flex-direction: column;
      
      :deep(.el-card__body) {
        flex: 1;
        overflow-y: auto;
      }
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .tree-node {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-right: 10px;
        
        .node-label {
          display: flex;
          align-items: center;
          gap: 5px;
          
          .method-tag {
            font-size: 12px;
            font-weight: bold;
            margin-right: 5px;
          }
        }
        
        .node-actions {
          display: none;
        }
        
        &:hover .node-actions {
          display: flex;
          gap: 5px;
        }
      }
    }
    
    .editor-card {
      flex: 1;
      display: flex;
      flex-direction: column;
      
      :deep(.el-card__body) {
        flex: 1;
        overflow-y: auto;
      }
      
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    }
  }
}
</style>
