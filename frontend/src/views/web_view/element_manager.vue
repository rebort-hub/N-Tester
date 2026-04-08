<template>
  <div class="element-manager-container">
    <div style="display: flex; gap: 8px; align-items: flex-start">
        <!-- 左侧元素菜单树 -->
        <div style="width: 250px; flex-shrink: 0">
          <el-card shadow="hover" style="height: 780px; overflow-y: auto">
            <div>
              <div>
                <el-input
                  v-model="filterText"
                  style="margin-bottom: 5px; width: 90%; padding-right: 10px"
                  placeholder="请输入节点名称"
                />
                <el-button type="text" style="padding-left: 5px" icon="Refresh" @click="get_tree" />
              </div>
              <el-tree
                :data="treeData"
                :props="defaultProps"
                default-expand-all
                :filter-node-method="filterNode"
                @node-click="get_element"
              >
                <template #default="{ node, data }">
                  <span class="custom-tree-node">
                    <span v-if="data.type === 0">
                      <el-icon class="tree-folder-icon" style="padding-right: 3px">
                        <HomeFilled />
                      </el-icon>
                      {{ node.label }}
                    </span>
                    <span v-else-if="data.type === 1">
                      <el-icon class="tree-folder-icon" style="padding-right: 3px">
                        <Folder />
                      </el-icon>
                      {{ node.label }}
                    </span>
                    <span v-if="data.type === 0" class="right" style="padding-right: 10px">
                      <el-dropdown placement="bottom">
                        <el-icon>
                          <MoreFilled />
                        </el-icon>
                        <span class="el-dropdown-link" style="font-size: 20px" />
                        <template #dropdown>
                          <el-dropdown-menu class="header-new-drop">
                            <el-dropdown-item :icon="CirclePlus" @click="Add_menu(data)">
                              新建子菜单
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </span>
                    <span v-else-if="data.type === 1" class="right" style="padding-right: 10px">
                      <el-dropdown placement="bottom">
                        <el-icon>
                          <MoreFilled />
                        </el-icon>
                        <span class="el-dropdown-link" style="font-size: 20px" />
                        <template #dropdown>
                          <el-dropdown-menu class="header-new-drop">
                            <el-dropdown-item :icon="CirclePlus" @click="Add_menu(data)">
                              新建子菜单
                            </el-dropdown-item>
                            <el-dropdown-item :icon="Edit" @click="Edit_menu(data)">重命名</el-dropdown-item>
                            <el-dropdown-item :icon="Delete" @click="Del_menu(data)">删除</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </span>
                  </span>
                </template>
              </el-tree>
            </div>
          </el-card>
        </div>
        <div style="flex: 1; min-width: 0">
          <el-tabs
            v-model="tab_active"
            type="card"
            closable
            class="demo-tabs"
            @tab-remove="removeTab"
            @tab-click="tab_click"
          >
            <el-tab-pane
              v-for="(item, index) in tab_list"
              :key="index"
              :label="item.title"
              :name="item.name"
            >
              <template #label>
                <el-icon style="padding-right: 5px"><Folder /></el-icon>
                {{ item.title }}
              </template>

              <!-- 搜索栏 -->
              <el-card shadow="hover" :body-style="{ paddingBottom: '0' }" style="margin-bottom: 8px">
                <el-form :inline="true">
                  <el-form-item label="元素名称">
                    <el-input
                      v-model="item.searchParams.search.name__icontains"
                      placeholder="请输入元素名称"
                      clearable
                      style="width: 220px"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" icon="Search" @click="element_list">搜索</el-button>
                    <el-button type="success" icon="Plus" @click="Add_element(item, item.id)">新增元素</el-button>
                  </el-form-item>
                </el-form>
              </el-card>

              <!-- 表格 -->
              <el-card shadow="hover">
                <el-table border stripe :data="item.content.content" style="width: 100%" empty-text="暂无数据">
                  <el-table-column type="index" label="序号" width="60" align="center" />
                  <el-table-column prop="name" label="元素名称" min-width="120" show-overflow-tooltip />
                  <el-table-column label="元素类型" width="90" align="center">
                    <template #default="{ row }">
                      <el-tag v-if="row.element.type === 1" type="success">网页</el-tag>
                      <el-tag v-else-if="row.element.type === 2" type="warning">元素</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="定位类型" width="90" align="center">
                    <template #default="{ row }">
                      <el-tag v-if="row.element.locator_type === 1 && row.element.type === 1">标题</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 2 && row.element.type === 1">网址</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 3 && row.element.type === 2">定位器</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2">选择器</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 5 && row.element.type === 2">自定义</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="定位方式" width="110" align="center">
                    <template #default="{ row }">
                      <el-tag v-if="row.element.type === 1">-</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 5">-</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 3 && row.element.type === 2">-</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 1">id</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 2">text</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 3">label</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 4">title</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 5">placeholder</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 6">alt</el-tag>
                      <el-tag v-else-if="row.element.locator_type === 4 && row.element.type === 2 && row.element.locator_select_type === 7">role</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="目标值" min-width="120" show-overflow-tooltip>
                    <template #default="{ row }">{{ row.element.value }}</template>
                  </el-table-column>
                  <el-table-column prop="username" label="更新人" width="80" align="center" />
                  <el-table-column label="操作" width="170" align="center" fixed="right">
                    <template #default="{ row }">
                      <span style="white-space: nowrap">
                        <el-button type="primary" size="small" icon="Edit" @click="Edit_element(item, row)">编辑</el-button>
                        <el-button type="danger" size="small" icon="Delete" @click="Del_element(item, row)">删除</el-button>
                      </span>
                    </template>
                  </el-table-column>
                </el-table>
                <div style="margin-top: 12px">
                  <el-pagination
                    v-show="refresh_tab.content?.total > 0"
                    background
                    v-model:current-page="refresh_tab.searchParams.currentPage"
                    v-model:page-size="refresh_tab.searchParams.pageSize"
                    :total="refresh_tab.content.total"
                    :page-sizes="[10, 20, 50, 100]"
                    layout="total, sizes, prev, pager, next, jumper"
                    @size-change="element_list"
                    @current-change="element_list"
                  />
                </div>
              </el-card>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

    <!-- 菜单新增 / 编辑弹窗 -->
      <KoiDialog
        ref="add_koiDialogRef"
        :title="title"
        :height="100"
        @koi-confirm="add_menu_confirm"
        @koi-cancel="add_menu_cancel"
      >
        <template #content>
          <el-form :model="add_menu_form" label-width="80px">
            <el-form-item label="名称：">
              <el-input v-model="add_menu_form.name" placeholder="请输入名称" clearable />
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>

      <KoiDialog
        ref="edit_koiDialogRef"
        :title="title"
        :height="100"
        @koi-confirm="edit_menu_confirm"
        @koi-cancel="edit_menu_cancel"
      >
        <template #content>
          <el-form :model="add_menu_form" label-width="80px">
            <el-form-item label="名称：">
              <el-input v-model="add_menu_form.name" placeholder="请输入名称" clearable />
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>

      <!-- 元素新增 / 编辑弹窗 -->
      <KoiDialog
        ref="add_element_dialogRef"
        :title="title"
        :height="350"
        width="35%"
        @koi-confirm="add_element_confirm"
        @koi-cancel="add_element_cancel"
      >
        <template #content>
          <el-form :model="add_element_form" label-width="100px">
            <el-form-item label="元素名称：">
              <el-input v-model="add_element_form.name" />
            </el-form-item>
            <el-form-item label="元素类型：">
              <el-select v-model="add_element_form.element.type" placeholder="请选择元素类型">
                <el-option
                  v-for="item in element_type_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="add_element_form.element.type === 1" label="浏览器：">
              <el-select
                v-model="add_element_form.element.locator_type"
                placeholder="请选择浏览器"
              >
                <el-option
                  v-for="item in browser_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="add_element_form.element.type === 2" label="定位类型：">
              <el-select
                v-model="add_element_form.element.locator_type"
                placeholder="请选择定位类型"
              >
                <el-option
                  v-for="item in locator_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              v-if="
                add_element_form.element.locator_type === 4 &&
                add_element_form.element.type === 2
              "
              label="定位方式："
            >
              <el-select
                v-model="add_element_form.element.locator_select_type"
                placeholder="请选择定位方式"
              >
                <el-option
                  v-for="item in locator_selects"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              v-if="
                add_element_form.element.locator_select_type === 7 &&
                add_element_form.element.type === 2
              "
              label="role对象："
            >
              <el-select
                v-model="add_element_form.element.locator_role_type"
                style="padding-left: 5px; padding-block-end: 5px"
              >
                <el-option
                  v-for="(item, index) in role_list"
                  :key="index"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="目标值：">
              <el-input v-model="add_element_form.element.value" />
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>

      <KoiDialog
        ref="edit_element_dialogRef"
        :title="title"
        :height="350"
        width="35%"
        @koi-confirm="edit_element_confirm"
        @koi-cancel="edit_element_cancel"
      >
        <template #content>
          <el-form :model="add_element_form" label-width="100px">
            <el-form-item label="元素名称：">
              <el-input v-model="add_element_form.name" />
            </el-form-item>
            <el-form-item label="元素类型：">
              <el-select v-model="add_element_form.element.type" placeholder="请选择元素类型">
                <el-option
                  v-for="item in element_type_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="add_element_form.element.type === 1" label="浏览器：">
              <el-select
                v-model="add_element_form.element.locator_type"
                placeholder="请选择浏览器"
              >
                <el-option
                  v-for="item in browser_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item v-if="add_element_form.element.type === 2" label="定位类型：">
              <el-select
                v-model="add_element_form.element.locator_type"
                placeholder="请选择定位类型"
              >
                <el-option
                  v-for="item in locator_list"
                  :key="item.value"
                  :label="item.name"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              v-if="
                add_element_form.element.locator_type === 4 &&
                add_element_form.element.type === 2
              "
              label="定位方式："
            >
              <el-select
                v-model="add_element_form.element.locator_select_type"
                placeholder="请选择定位方式"
              >
                <el-option
                  v-for="item in locator_selects"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item
              v-if="
                add_element_form.element.locator_select_type === 7 &&
                add_element_form.element.type === 2
              "
              label="role对象："
            >
              <el-select
                v-model="add_element_form.element.locator_role_type"
                style="padding-left: 5px; padding-block-end: 5px"
              >
                <el-option
                  v-for="(item, index) in role_list"
                  :key="index"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="目标值：">
              <el-input v-model="add_element_form.element.value" />
            </el-form-item>
          </el-form>
        </template>
      </KoiDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { HomeFilled, Folder, MoreFilled, CirclePlus, Edit, Delete } from '@element-plus/icons-vue'
import KoiCard from '/@/components/koi/KoiCard.vue'
import KoiDialog from '/@/components/koi/KoiDialog.vue'
import { useWebManagementApi } from '/@/api/v1/web_management'

const {
  element_tree,
  add_element_menu,
  edit_element_menu,
  del_element_menu,
  get_element_list,
  add_element,
  edit_element,
  del_element,
} = useWebManagementApi()

const treeData = ref<any[]>([])
const defaultProps = {
  children: 'children',
  label: 'name',
}
const filterText = ref('')
const title = ref('')
const add_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const edit_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const add_menu_form = ref<any>({})

const get_tree = async () => {
  const res: any = await element_tree({})
  treeData.value = res.data || []
}

const filterNode = (value: string, data: any): boolean => {
  if (!value) return true
  return data.name.includes(value)
}

const Add_menu = (data: any) => {
  add_menu_form.value = {
    pid: data.id,
    name: '',
    type: 1,
  }
  title.value = '新建菜单'
  add_koiDialogRef.value?.koiOpen()
}

const add_menu_confirm = async () => {
  const res: any = await add_element_menu(add_menu_form.value)
  add_koiDialogRef.value?.koiQuickClose(res.message)
  await get_tree()
}

const add_menu_cancel = () => {
  add_koiDialogRef.value?.koiClose()
}

const Edit_menu = (data: any) => {
  add_menu_form.value = {
    id: data.id,
    name: data.name,
  }
  title.value = '重命名'
  edit_koiDialogRef.value?.koiOpen()
}

const edit_menu_confirm = async () => {
  const res: any = await edit_element_menu(add_menu_form.value)
  edit_koiDialogRef.value?.koiQuickClose(res.message)
  await get_tree()
}

const edit_menu_cancel = () => {
  edit_koiDialogRef.value?.koiClose()
}

const Del_menu = (data: any) => {
  ElMessageBox.confirm(`确认删除菜单「${data.name}」吗？`, '提示', {
    type: 'warning',
  })
    .then(async () => {
      const res: any = await del_element_menu({ id: data.id })
      ElMessage.success(res.message || '删除成功')
      await get_tree()
    })
    .catch(() => {})
}

const searchParams = ref<any>({
  currentPage: 1,
  pageSize: 10,
  search: {
    menu_id: null,
    name__icontains: '',
  },
})

const tab_list = ref<any[]>([])
const tab_active = ref('')
const refresh_tab = ref<any>({})

const get_element = async (data: any) => {
  if (data.type === 1) {
    searchParams.value.search.menu_id = data.id
    const res: any = await get_element_list({
      page: searchParams.value.currentPage,
      pageSize: searchParams.value.pageSize,
      menu_id: data.id,
      name__icontains: searchParams.value.search.name__icontains,
    })
    const pageData = {
      content: res.data.content || [],
      total: res.data.totalElements ?? res.data.total ?? 0,
    }
    await addTab(data, searchParams.value, pageData)
  }
}

const addTab = async (node: any, searchParamsValue: any, element: any) => {
  const tabKey = String(node.id)
  const index = tab_list.value.findIndex((item: any) => item.name === tabKey)
  const tab = {
    title: node.name,   // 显示用
    name: tabKey,       // 唯一 key，用 id
    content: element,
    id: node.id,
    type: node.type,
    searchParams: searchParamsValue,
  }
  if (index === -1) {
    tab_list.value.push(tab)
  } else {
    tab_list.value[index].content = element
    tab_list.value[index].title = node.name
    tab_list.value[index].searchParams = searchParamsValue
  }
  refresh_tab.value = index === -1 ? tab : tab_list.value[index]
  tab_active.value = tabKey
}

const tab_click = async (target: any) => {
  const tabName = target.props.name
  tab_list.value.forEach((tab: any) => {
    if (tab.name === tabName) {
      refresh_tab.value = tab
      refresh_tab.value.searchParams.search.menu_id = tab.id
    }
  })
  await element_list()
}

const removeTab = (targetName: string) => {
  const tabs = tab_list.value
  let activeName = tab_active.value
  if (activeName === targetName) {
    tabs.forEach((tab: any, index: number) => {
      if (tab.name === targetName) {
        const nextTab = tabs[index + 1] || tabs[index - 1]
        if (nextTab) {
          activeName = nextTab.name
        }
      }
    })
  }
  tab_active.value = activeName
  tab_list.value = tabs.filter((tab: any) => tab.name !== targetName)
}

const element_list = async () => {
  if (!refresh_tab.value.id) return
  const res: any = await get_element_list({
    page: refresh_tab.value.searchParams.currentPage,
    pageSize: refresh_tab.value.searchParams.pageSize,
    menu_id: refresh_tab.value.id,
    name__icontains: refresh_tab.value.searchParams.search.name__icontains,
  })
  refresh_tab.value.content = {
    content: res.data.content || [],
    total: res.data.totalElements ?? res.data.total ?? 0,
  }
}

const add_element_dialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const edit_element_dialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const add_element_form = ref<any>({})

const element_type_list = ref([
  { name: '网页', value: 1 },
  { name: '元素', value: 2 },
])
const browser_list = ref([
  { name: '标题', value: 1 },
  { name: '网址', value: 2 },
])
const locator_list = ref([
  { name: '定位器', value: 3 },
  { name: '选择器', value: 4 },
  { name: '自定义', value: 5 },
])
const locator_selects = ref([
  { label: 'id', value: 1 },
  { label: 'text', value: 2 },
  { label: 'label', value: 3 },
  { label: 'title', value: 4 },
  { label: 'placeholder', value: 5 },
  { label: 'alt', value: 6 },
  { label: 'role', value: 7 },
])
const role_list = ref([
  { label: 'button', value: 'button' },
  { label: 'link', value: 'link' },
  { label: 'tab', value: 'tab' },
  { label: 'tabpanel', value: 'tabpanel' },
  { label: 'textbox', value: 'textbox' },
  { label: 'checkbox', value: 'checkbox' },
  { label: 'radio', value: 'radio' },
  { label: 'combobox', value: 'combobox' },
  { label: 'listbox', value: 'listbox' },
  { label: 'menu', value: 'menu' },
  { label: 'menuitem', value: 'menuitem' },
  { label: 'alert', value: 'alert' },
  { label: 'status', value: 'status' },
  { label: 'progressbar', value: 'progressbar' },
  { label: 'spinbutton', value: 'spinbutton' },
  { label: 'heading', value: 'heading' },
  { label: 'tree', value: 'tree' },
  { label: 'treeitem', value: 'treeitem' },
])

const Add_element = (tab: any, menu_id: any) => {
  refresh_tab.value = tab
  add_element_form.value = {
    menu_id,
    name: '',
    element: {
      type: 1,
      browser: 1,
      locator_type: 1,
      locator_select_type: 1,
      value: '',
      locator_role_type: 1,
    },
  }
  title.value = '新建元素'
  add_element_dialogRef.value?.koiOpen()
}

const Edit_element = (tab: any, data: any) => {
  refresh_tab.value = tab
  add_element_form.value = data
  title.value = `编辑元素：${data.name}`
  edit_element_dialogRef.value?.koiOpen()
}

const add_element_confirm = async () => {
  const res: any = await add_element(add_element_form.value)
  add_element_dialogRef.value?.koiQuickClose(res.message)
  await element_list()
}

const edit_element_confirm = async () => {
  const res: any = await edit_element(add_element_form.value)
  edit_element_dialogRef.value?.koiQuickClose(res.message)
  await element_list()
}

const add_element_cancel = () => {
  add_element_dialogRef.value?.koiClose()
}

const edit_element_cancel = () => {
  edit_element_dialogRef.value?.koiClose()
}

const Del_element = (tab: any, data: any) => {
  refresh_tab.value = tab
  ElMessageBox.confirm(`确认删除元素「${data.name}」吗？`, '提示', {
    type: 'warning',
  })
    .then(async () => {
      const res: any = await del_element({ id: data.id })
      ElMessage.success(res.message || '删除成功')
      await element_list()
    })
    .catch(() => {})
}

onMounted(() => {
  get_tree()
})
</script>

<style lang="scss" scoped>
.element-manager-container {
  padding: 10px;
}

.el-table .el-button + .el-button {
  margin-left: 6px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 2px;
}

.el-tree-node__content {
  margin-bottom: 5px;
  height: 28px;
}

.tree-folder-icon,
.custom-tree-node .el-icon {
  display: inline-flex;
  vertical-align: middle;
}
</style>

