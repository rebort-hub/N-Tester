<template>
  <div class="import-request-operation-form">
    <el-form-item label="选择接口">
      <el-cascader
        v-model="selectedPath"
        :options="requestTree"
        :props="cascaderProps"
        placeholder="请选择要导入的接口"
        filterable
        clearable
        style="width: 100%"
        @change="handleRequestChange"
      />
      <div class="form-tip">
        <el-icon><ele-InfoFilled /></el-icon>
        <span>选择要导入的API请求，执行该接口并共享环境变量</span>
      </div>
    </el-form-item>

    <el-form-item label="使用环境">
      <el-select
        v-model="localValue.environment_id"
        placeholder="选择环境（可选）"
        clearable
        style="width: 100%"
        @change="emitChange"
      >
        <el-option
          v-for="env in environments"
          :key="env.id"
          :label="env.name"
          :value="env.id"
        />
      </el-select>
      <div class="form-tip">
        <el-icon><ele-InfoFilled /></el-icon>
        <span>可选，指定执行该接口时使用的环境</span>
      </div>
    </el-form-item>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useApiTestingApi } from '/@/api/v1/api_testing'

const { apiCollectionApi, apiEnvironmentApi } = useApiTestingApi()

const props = defineProps<{
  modelValue: any
  projectId?: number
  apiProjectId?: number
}>()

const emit = defineEmits(['update:modelValue'])

const localValue = ref({
  request_id: props.modelValue?.request_id || null,
  environment_id: props.modelValue?.environment_id || null
})

const selectedPath = ref<number[]>([])
const requestTree = ref<any[]>([])
const environments = ref<any[]>([])

const cascaderProps = {
  value: 'id',
  label: 'name',
  children: 'children',
  checkStrictly: false,
  emitPath: true,
  expandTrigger: 'hover' as const
}

// 加载接口树
const loadRequestTree = async () => {
  if (!props.apiProjectId) return
  
  try {
    const res = await apiCollectionApi.tree(props.apiProjectId)
    requestTree.value = buildCascaderTree(res.data || [])
    
    // 如果已有选中的请求ID，尝试恢复选中路径
    if (localValue.value.request_id) {
      const path = findRequestPath(requestTree.value, localValue.value.request_id)
      if (path) {
        selectedPath.value = path
      }
    }
  } catch (error) {
    console.error('加载接口树失败:', error)
  }
}

// 加载环境列表
const loadEnvironments = async () => {
  if (!props.projectId) return
  
  try {
    const res = await apiEnvironmentApi.list(props.projectId)
    environments.value = res.data || []
  } catch (error) {
    console.error('加载环境列表失败:', error)
  }
}

// 构建级联选择器树
const buildCascaderTree = (data: any[]): any[] => {
  return data.map(node => {
    const result: any = {
      id: node.type === 'request' ? `request_${node.id}` : node.id,
      name: node.name,
      type: node.type,
      realId: node.type === 'request' ? node.id : undefined,
      children: []
    }
    
    // 处理子集合
    if (node.children && node.children.length > 0) {
      const collections = node.children.filter((child: any) => child.type === 'collection')
      const requests = node.children.filter((child: any) => child.type === 'request')
      
      if (collections.length > 0) {
        result.children.push(...buildCascaderTree(collections))
      }
      
      if (requests.length > 0) {
        result.children.push(...requests.map((req: any) => ({
          id: `request_${req.id}`,
          name: req.name,
          type: 'request',
          realId: req.id,
          children: undefined // 请求节点没有子节点
        })))
      }
    }
    
    // 如果没有子节点，删除children属性
    if (result.children.length === 0) {
      delete result.children
    }
    
    return result
  })
}

// 查找请求在树中的路径
const findRequestPath = (tree: any[], requestId: number, path: number[] = []): number[] | null => {
  for (const node of tree) {
    const currentPath = [...path, node.id]
    
    if (node.type === 'request' && node.realId === requestId) {
      return currentPath
    }
    
    if (node.children) {
      const found = findRequestPath(node.children, requestId, currentPath)
      if (found) return found
    }
  }
  
  return null
}

// 处理接口选择变化
const handleRequestChange = (value: any[]) => {
  if (!value || value.length === 0) {
    localValue.value.request_id = null
    emitChange()
    return
  }
  
  // 获取最后一个节点（实际选中的节点）
  const lastId = value[value.length - 1]
  
  // 在树中查找该节点
  const findNode = (tree: any[], id: any): any => {
    for (const node of tree) {
      if (node.id === id) return node
      if (node.children) {
        const found = findNode(node.children, id)
        if (found) return found
      }
    }
    return null
  }
  
  const selectedNode = findNode(requestTree.value, lastId)
  
  if (selectedNode && selectedNode.type === 'request') {
    localValue.value.request_id = selectedNode.realId
    emitChange()
  }
}

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localValue.value = {
      request_id: newVal.request_id || null,
      environment_id: newVal.environment_id || null
    }
    
    // 更新选中路径
    if (newVal.request_id && requestTree.value.length > 0) {
      const path = findRequestPath(requestTree.value, newVal.request_id)
      if (path) {
        selectedPath.value = path
      }
    }
  }
}, { deep: true })

watch(() => props.apiProjectId, () => {
  loadRequestTree()
})

watch(() => props.projectId, () => {
  loadEnvironments()
})

const emitChange = () => {
  emit('update:modelValue', {
    ...props.modelValue,
    ...localValue.value
  })
}

onMounted(() => {
  loadRequestTree()
  loadEnvironments()
})
</script>

<style scoped lang="scss">
.import-request-operation-form {
  .form-tip {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-top: 8px;
    font-size: 12px;
    color: #909399;

    .el-icon {
      font-size: 14px;
    }
  }
}
</style>
