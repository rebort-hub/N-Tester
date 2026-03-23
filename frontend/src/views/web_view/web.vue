<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'
import { ElTree, ElMessage, ElMessageBox } from 'element-plus'
import {
  DocumentCopy,
  Delete,
  HomeFilled,
  Folder,
  ChromeFilled,
  ArrowDown,
  MoreFilled,
  CirclePlus,
  Edit,
  Upload,
  Remove,
} from '@element-plus/icons-vue'
import KoiDialog from '/@/components/koi/KoiDialog.vue'
import KoiUploadFiles from '/@/components/koi/KoiUploadFiles.vue'
import {
  web_menu,
  get_web_script,
  menu_script_list,
  run_web_script,
  get_web_result,
  get_web_result_log,
  add_web_menu,
  del_web_menu,
  rename_web_menu,
  save_web_script,
  input_element,
  get_element_select,
} from '/@/api/v1/web_management'

// 数据表格加载页面动画
const loading = ref(false)
const filterText = ref<any>('')
const treeRef = ref<InstanceType<typeof ElTree>>()
const tree_data = ref<any>()
const defaultProps = {
  children: 'children',
  label: 'name',
}
// 当前页面的脚本数据 — 始终指向当前激活 tab 的 script 数组
const script_list = computed<any[]>(() => {
  const active = tab_list.value.find((t: any) => t.name === tab_active.value)
  return active?.content?.script ?? []
})
const script_info = ref<any>({
  name: '',
  type: 0,
  status: true,
  children: [],
  action: {
    type: 1,
    locator: 1,
    locator_select: 1,
    target_locator: 1,
    target_locator_select: 1,
    target_type: 1,
    up_type: 1,
    sway_type: 1,
    before_wait: 1,
    after_wait: 1,
    timeout: 15,
    input: '',
    element: '',
    target: '',
    assert: [],
    cookies: [],
    localstorage: [],
    role: 'button',
    element_id: null,
    target_id: '',
  },
})
const table_list = ref<any>([])
const tab_active = ref('')
const tab_list = ref<any>([])
const add_menu_form = ref<any>({})
const icon_style = ref<any>('padding-right: 5px; padding-left: 5px; padding-top: 4px;')
const locator_list = ref<any>([
  { name: '定位器', value: 1 },
  { name: '选择器', value: 2 },
])
const locator_selects = ref<any>([
  { label: 'id', value: 1 },
  { label: 'text', value: 2 },
  { label: 'label', value: 3 },
  { label: 'title', value: 4 },
  { label: 'placeholder', value: 5 },
  { label: 'alt', value: 6 },
  { label: 'role', value: 7 },
])
const role_list = ref<any>([
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
const browser_list = ref<any>([
  { name: 'Chrome', value: 1 },
  { name: 'Firefox', value: 2 },
  { name: 'Edge', value: 3 },
  { name: 'Safari', value: 4 },
])

// web目录过滤
watch(filterText, (val) => {
  treeRef.value?.filter(val)
})

const filterNode = (value: string, data: any): boolean => {
  if (!value) return true
  return data.name.includes(value)
}

const element_select_change = (selection: any) => {
  console.log(selection)
}

const get_web_menu = async () => {
  try {
    loading.value = true
    const res: any = await web_menu({})
    tree_data.value = res.data
  } catch {
    ElMessage.error('数据查询失败，请刷新重试')
  } finally {
    loading.value = false
  }
}

const web_menu_click = async (node: any) => {
  try {
    if (node.type === 1) {
      const res: any = await menu_script_list({ id: node.id })
      table_list.value = res.data
      await addTab(node, res.data)
    } else if (node.type === 2) {
      const res: any = await get_web_script({ id: node.id })
      script_info.value = res.data.script[0]
      await addTab(node, res.data)
    }
  } catch {
    ElMessage.error('数据查询失败，请刷新重试')
  }
}

const addTab = async (node: any, target: any) => {
  const newTabName = node.name
  const index = tab_list.value.findIndex((item: any) => item.title === newTabName)
  if (index === -1) {
    tab_list.value.push({
      title: newTabName,
      name: newTabName,
      content: target,
      id: node.id,
      type: node.type,
    })
  }
  tab_active.value = node.name
}

const removeTab = (targetName: string) => {
  const tabs = tab_list.value
  let activeName = tab_active.value
  if (activeName === targetName) {
    tab_list.value.forEach((tab: any, index: any) => {
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

const select_list = ref<any>([])
const handleSelectionChange = (selection: any) => {
  select_list.value = selection.sort((a: any, b: any) => a.step - b.step)
}

const menu_form = ref<any>({
  name: '',
  id: null,
})
const title = ref<string>('')
const add_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const rename_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)

const add_menu = (data: any) => {
  title.value = '新增子菜单'
  add_koiDialogRef.value?.koiOpen()
  menu_form.value = data
}

const check_children = (data: any, menu: any) => {
  if ('children' in data) {
    data.children.push(menu)
  } else {
    data.children = []
    data.children.push(menu)
  }
}

const add_menu_confirm = async () => {
  try {
    add_menu_form.value.pid = menu_form.value.id
    const res: any = await add_web_menu(add_menu_form.value)
    await check_children(menu_form.value, res.data)
    add_koiDialogRef.value?.koiQuickClose(res.message)
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    add_menu_form.value = {}
  }
}

const add_menu_cancel = () => {
  add_koiDialogRef.value?.koiClose()
}

const rename_menu = (data: any) => {
  title.value = '重命名'
  rename_koiDialogRef.value?.koiOpen()
  menu_form.value = data
}

const edit_menu_confirm = async () => {
  try {
    add_menu_form.value.id = menu_form.value.id
    const res: any = await rename_web_menu(add_menu_form.value)
    rename_koiDialogRef.value?.koiQuickClose(res.message)
    menu_form.value.name = add_menu_form.value.name
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    add_menu_form.value = {}
  }
}

const edit_menu_cancel = () => {
  rename_koiDialogRef.value?.koiClose()
}

const on_menu_allowDrop = (moveNode: any, inNode: any, type: any) => {
  console.log(moveNode)
  if (inNode.data.type === 2) {
    return type !== 'inner'
  }
  return type
}

const del_menu = (data: any) => {
  ElMessageBox.confirm('您确认需要删除该目录么？', '提示', {
    type: 'warning',
  })
    .then(async () => {
      const res: any = await del_web_menu({ id: data.id, type: data.type })
      ElMessage.success(res.message || '删除成功')
      await get_web_menu()
    })
    .catch(() => {})
}

const step_style = (type: any) => {
  if (type === 0) {
    return 'border: 1px solid #3e7be5; border-radius: 5px; width: 93%; color: #3e7be5'
  } else if (type === 1 || type === 2 || type === 3 || type === 4) {
    return 'border: 1px solid #400ae6; border-radius: 5px; width: 93%; color: #400ae6'
  } else if (type === 5 || type === 6 || type === 7) {
    return 'border: 1px solid #ee4866; border-radius: 5px; width: 93%; color: #ee4866'
  } else if (type === 8 || type === 9) {
    return 'border: 1px solid #e99516; border-radius: 5px; width: 93%; color: #e99516'
  } else if (type === 10 || type === 11) {
    return 'border: 1px solid #ea035f; border-radius: 5px; width: 93%; color: #ea035f'
  } else if (type === 12) {
    return 'border: 1px solid #20a162; border-radius: 5px; width: 93%; color: #20a162'
  }
  return 'border: 1px solid #3e7be5; border-radius: 5px; width: 93%; color: #3e7be5'
}

const random_string = (data_length: any) => {
  return Array.from(crypto.getRandomValues(new Uint8Array(data_length)))
    .map((n) => n.toString(36))
    .join('')
}

// 自动化脚本：新增步骤
const add_script = (command: any) => {
  const active = tab_list.value.find((t: any) => t.name === tab_active.value)
  if (!active?.content?.script) return
  const new_string = random_string(2)
  active.content.script.push({
    name: `${command.name}-${new_string}`,
    type: command.type,
    status: true,
    children: [],
    action: {
      type: 1,
      locator: 1,
      locator_select: 1,
      target_locator: 1,
      target_locator_select: 1,
      input: '',
      element: '',
      element_id: null,
      target: '',
      target_id: '',
      target_type: 1,
      assert: [],
      up_type: 1,
      sway_type: 1,
      wait_time: 1,
      before_wait: 1,
      after_wait: 1,
      role: 'button',
      cookies: [],
      localstorage: [],
      timeout: 15,
    },
  })
}

const config_active = ref('first')
const assert_list = ref<any>([
  { name: '元素存在', value: 1 },
  { name: '元素不存在', value: 2 },
  { name: '文本存在', value: 3 },
  { name: '文本不存在', value: 4 },
  { name: '页面属性', value: 5 },
  { name: '自定义断言', value: 6 },
  { name: 'AI 断言', value: 7 },
])
const browser_assert = ref<any>([
  { name: '网页地址', value: 1 },
  { name: '网页标题', value: 2 },
])

const add_assert = (data: any) => {
  data.push({
    type: 1,
    locator: 1,
    locator_select: 1,
    page_type: 1,
    element: '',
    role: 'button',
  })
}

const add_cookie = (data: any) => {
  data.push({
    name: '',
    value: '',
  })
}

const del_cookie = (data: any, index: any) => {
  data.splice(index, 1)
}

const add_localstorage = (data: any) => {
  data.push({
    name: '',
    value: '',
  })
}

const del_localstorage = (data: any, index: any) => {
  data.splice(index, 1)
}

const del_assert = (data: any, index: any) => {
  data.splice(index, 1)
}

const web_script_click = (node: any) => {
  // 重要：这里必须保持对步骤节点对象的引用（不能 clone），否则右侧表单改动不会写回树数据，
  // 保存后再次切换回来就会像“没记忆”一样被清空。
  if (!node.action) node.action = {}
  const action = node.action

  action.type ??= 1
  action.locator ??= 1
  action.locator_select ??= 1
  action.target_locator ??= 1
  action.target_locator_select ??= 1
  action.target_type ??= 1
  action.up_type ??= 1
  action.sway_type ??= 1
  action.before_wait ??= 1
  action.after_wait ??= 1
  action.timeout ??= 15
  action.input ??= ''
  action.element ??= ''
  action.target ??= ''
  action.role ??= 'button'
  action.element_id ??= null
  action.target_id ??= ''

  if (!Array.isArray(action.assert)) action.assert = []
  if (!Array.isArray(action.cookies)) action.cookies = []
  if (!Array.isArray(action.localstorage)) action.localstorage = []

  script_info.value = node
}

// 顶部“AI脚本录入”按钮：先按旧架构的交互提供入口（后续可接真正的AI生成/录入流程）
const ai_script_input = () => {
  // 默认新增一个 AI 步骤并选中它
  add_script({ type: 19, name: 'AI 步骤' })
  const last = script_list.value?.[script_list.value.length - 1]
  if (last) web_script_click(last)
  ElMessage.success('已添加 AI 步骤，请在右侧填写脚本内容')
}

const save_web_script_handler = async (id: any) => {
  const res: any = await save_web_script({
    id,
    script: script_list.value,
  })
  if (res.code === 200) {
    ElMessage.success(res.message || '保存成功')
  } else {
    ElMessage.error(res.message || '保存失败，请重试')
  }
}

const Delete_row = (list: any, data: any) => {
  list.forEach((item: any, index: any) => {
    if (item.name === data.name) {
      list.splice(index, 1)
    } else if (item.children.length > 0) {
      Delete_row(item.children, data)
    }
  })
  return false
}

const copy_row = (list: any, data: any) => {
  const new_string = 'copy'
  const new_data = {
    name: `${data.name}-${new_string}`,
    type: data.type,
    status: true,
    children: [],
    action: data.action,
  }
  list.push(new_data)
}

const element_select_list = ref<any>([])
const element_select = async () => {
  const res: any = await get_element_select({})
  element_select_list.value = res.data
}

const file_name = ref<any>(null)
const file_url = ref<any>(null)
const upload_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)

const call_back = (fileMap: any) => {
  ElMessage.success('上传文件成功（占位实现）')
  file_url.value = fileMap.file_url
  file_name.value = fileMap.filename
}

const file_script_path = ref<any>('')
const call_back_1 = (fileMap: any) => {
  file_script_path.value = `${fileMap.file_url}/${fileMap.filename}`
}

const add_file = (action: any) => {
  action.input = file_script_path.value
}

const pid = ref<any>(null)
const upload_file = (data: any) => {
  pid.value = data.id
  upload_koiDialogRef.value?.koiOpen()
  title.value = '上传文件'
}

const upload_file_confirm = async () => {
  const res: any = await input_element({
    file_url: file_url.value,
    file_name: file_name.value,
    pid: pid.value,
  })
  if (res.code === 200) {
    upload_koiDialogRef.value?.koiQuickClose(res.message || '上传成功')
    await get_web_menu()
  } else {
    ElMessage.error('上传失败，请重试')
  }
}

const upload_file_cancel = () => {
  upload_koiDialogRef.value?.koiQuickClose('取消上传')
}

const run_script_form = ref<any>({
  task_name: '',
  browser: [],
  script: [],
  width: 1920,
  height: 1080,
  browser_type: 1,
})
const run_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)
const result_id = ref<any>('')

const run_script = (item: any) => {
  run_script_form.value.script = []
  run_koiDialogRef.value?.koiOpen()
  title.value = '请配置调试信息'
  const script = {
    id: item.id,
    name: item.name,
    type: item.type,
  }
  run_script_form.value.script.push(script)
}

const run_browsers = ref<any>([])
const run_browser_active = ref<any>('')
const res_koiDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null)

const run_script_confirm = async () => {
  if (run_script_form.value.script.length === 0) {
    ElMessage.error('请选择脚本')
    return
  }
  if (!run_script_form.value.task_name) {
    ElMessage.error('请输入任务名称')
    return
  }
  if (run_script_form.value.browser.length === 0) {
    ElMessage.error('请选择浏览器')
    return
  }
  if (run_script_form.value.browser.length > 1) {
    ElMessage.error('抱歉，由于资源有限，单次仅支持一个浏览器执行')
    return
  }

  run_browsers.value = []
  result_id.value = String(Date.now())
  run_script_form.value.result_id = result_id.value
  await run_browser_show()
  run_browser_active.value = run_script_form.value.browser[0]
  title.value = `正在执行：${run_script_form.value.task_name}`
  res_koiDialogRef.value?.koiOpen()
  await startPolling()
  const res: any = await run_web_script(run_script_form.value)
  if (res.code === 10001) {
    ElMessage.error(res.message || '执行失败')
    res_koiDialogRef.value?.koiQuickClose(res.message)
    stopPolling()
  }
}

const run_browser_show = () => {
  run_browsers.value = []
  run_script_form.value.browser.forEach((item: any) => {
    browser_list.value.forEach((browser: any) => {
      if (browser.value === item) {
        run_browsers.value.push({
          name: browser.name,
          value: browser.value,
        })
      }
    })
  })
}

const interval = ref<any>(null)

const startPolling = async () => {
  if (interval.value) return
  interval.value = setInterval(get_run_result, 2000)
}

const stopPolling = () => {
  if (interval.value) {
    clearInterval(interval.value)
    interval.value = null
  }
}

const change_browser = async () => {
  loading.value = true
  await startPolling()
  loading.value = false
}

const get_run_result = async () => {
  run_type.value = '正在执行'
  await get_result()
  await get_result_log()
}

const web_result = ref<any>([])
const web_result_log = ref<any>([])
const run_type = ref<any>('')
const run_count = ref<any>(0)
const run_fail = ref<any>(0)
const start_time = ref<any>('')
const end_time = ref<any>('')
const pre_video = ref<any>('')
const img_show = ref<any>(false)
const pre_img = ref<any>('')
const trace = ref<any>('')

const formatTime = (t: string) => t ? t.replace('T', ' ').slice(0, 19) : '-'

const get_result = async () => {
  const res: any = await get_web_result({
    result_id: result_id.value,
    browser: run_browser_active.value,
  })
  web_result.value = res.data
  run_count.value = web_result.value.length
  if (web_result.value.length > 0) {
    start_time.value = formatTime(web_result.value[web_result.value.length - 1].create_time)
  }
  let fail = 0
  web_result.value.forEach((item: any) => {
    if (item.status === 0) {
      fail += 1
    }
    if (item.name === '执行结束') {
      stopPolling()
      run_count.value -= 1
      run_type.value = '执行结束'
      end_time.value = formatTime(item.create_time)
      pre_video.value = item.video
      trace.value = item.trace
    }
  })
  run_fail.value = fail
}

const get_result_log = async () => {
  const res: any = await get_web_result_log({
    result_id: result_id.value,
    browser: run_browser_active.value,
  })
  web_result_log.value = res.data
}

const getIcon = (status: any) => (status === 1 ? 'Check' : 'Close')
const colors = (status: any) => (status === 1 ? '#0bbd87' : '#d70e0e')
const get_colors = (status: any) => (status === 1 ? 'color: #0bbd87' : 'color: #d70e0e')
const get_log_style = (data: any) => {
  if (data.includes('失败')) {
    return 'color: #d70e0e'
  }
  if (data.includes('补救')) {
    return 'color: #1605ef'
  }
  return ''
}

const pre_view = (img: any) => {
  pre_img.value = [img]
  img_show.value = true
}

const close_img = () => {
  img_show.value = false
}

const view_video = () => {
  if (pre_video.value) window.open(pre_video.value)
}

const run_script_cancel = () => {
  run_koiDialogRef.value?.koiQuickClose('取消调试')
}

const batch_run_script = () => {
  run_script_form.value.script = []
  run_koiDialogRef.value?.koiOpen()
  title.value = '请配置调试信息'
  run_script_form.value.script = select_list.value
}

const download_report = () => {
  if (trace.value) window.open(trace.value)
  view_trace()
}

const view_trace = () => {
  window.open('https://trace.playwright.dev/')
}

onMounted(() => {
  get_web_menu()
  element_select()
})
</script>

<template>
  <div>
    <div style="width: 100%; display: flex; gap: 8px; align-items: flex-start">
      <el-card shadow="hover" style="width: 220px; flex-shrink: 0; height: 800px; overflow-y: auto">
        <div style="width: 100%">
          <div>
            <el-input
              v-model="filterText"
              style="margin-bottom: 5px; width: 90%; padding-right: 10px"
              placeholder="请输入节点名称"
            />
            <el-button type="text" style="padding-left: 5px" icon="Refresh" @click="get_web_menu" />
          </div>
          <el-tree
            ref="treeRef"
            class="filter-tree"
            :data="tree_data"
            :props="defaultProps"
            default-expand-all
            :filter-node-method="filterNode"
            @node-click="web_menu_click"
            :allow-drop="on_menu_allowDrop"
            draggable
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <span v-if="data.type === 0">
                  <el-icon style="padding-right: 3px">
                    <HomeFilled />
                  </el-icon>
                  {{ node.label }}
                </span>
                <span v-else-if="data.type === 1">
                  <el-icon style="padding-right: 3px">
                    <Folder />
                  </el-icon>
                  {{ node.label }}
                </span>
                <span v-else-if="data.type === 2">
                  <el-icon style="padding-right: 3px">
                    <ChromeFilled />
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
                        <el-dropdown-item :icon="CirclePlus" @click="add_menu(data)">
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
                        <el-dropdown-item :icon="CirclePlus" @click="add_menu(data)">
                          新建子菜单
                        </el-dropdown-item>
                        <el-dropdown-item :icon="Upload" @click="upload_file(data)">上传</el-dropdown-item>
                        <el-dropdown-item :icon="Edit" @click="rename_menu(data)">重命名</el-dropdown-item>
                        <el-dropdown-item :icon="Delete" @click="del_menu(data)">删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </span>
                <span v-else-if="data.type === 2" class="right" style="padding-right: 10px">
                  <el-dropdown placement="bottom">
                    <el-icon>
                      <MoreFilled />
                    </el-icon>
                    <span class="el-dropdown-link" style="font-size: 20px" />
                    <template #dropdown>
                      <el-dropdown-menu class="header-new-drop">
                        <el-dropdown-item :icon="Edit" @click="rename_menu(data)">重命名</el-dropdown-item>
                        <el-dropdown-item :icon="Delete" @click="del_menu(data)">删除</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </span>
              </span>
            </template>
          </el-tree>
        </div>
      </el-card>

      <!-- 右侧脚本编辑区域 -->
      <el-card shadow="hover" style="flex: 1; min-width: 0; height: 800px; overflow: hidden">
        <div>
          <el-tabs v-model="tab_active" type="card" closable class="demo-tabs" @tab-remove="removeTab">
            <el-tab-pane
              v-for="(item, index) in tab_list"
              :key="index"
              :label="item.title"
              :name="item.name"
              v-loading="loading"
            >
              <template #label>
                <span v-if="item.type === 1">
                  <el-icon style="padding-right: 5px">
                    <Folder />
                  </el-icon>
                  {{ item.name }}
                </span>
                <span v-else-if="item.type === 2">
                  <el-icon style="padding-right: 5px">
                    <ChromeFilled />
                  </el-icon>
                  {{ item.name }}
                </span>
              </template>

              <!-- 脚本集 tab -->
              <div v-if="item.type === 1">
                <el-card shadow="never" style="height: 700px">
                  <div>
                    <div
                      style="float: right; padding-left: 10px; padding-right: 10px; padding-block-end: 10px"
                    >
                      <el-button type="primary" @click="batch_run_script">立即调试</el-button>
                    </div>
                    <el-table
                      v-loading="loading"
                      border
                      :data="table_list"
                      empty-text="暂时没有数据哟🌻"
                      @selection-change="handleSelectionChange"
                    >
                      <el-table-column type="selection" align="center" />
                      <el-table-column label="序号" prop="id" align="center" type="index" />
                      <el-table-column
                        label="脚本名称"
                        prop="name"
                        align="center"
                        :show-overflow-tooltip="true"
                      />
                      <el-table-column label="类型" align="center">
                        <template #default="{ row }">
                          <el-tag v-if="row.type === 1">文件夹</el-tag>
                          <el-tag v-else-if="row.type === 2">脚本</el-tag>
                        </template>
                      </el-table-column>
                      <el-table-column label="顺序" align="center">
                        <template #default="{ row }">
                          <el-input-number v-model="row.step" :min="1" :max="100" />
                        </template>
                      </el-table-column>
                    </el-table>
                  </div>
                </el-card>
              </div>

              <!-- 单脚本 tab -->
              <div v-else-if="item.type === 2" style="padding: 5px; height: 100%; display: flex; flex-direction: column; min-height: 0">
                <div style="flex-shrink: 0; padding-block-end: 5px">
                  <el-card shadow="never" class="script-info-card">
                    <el-descriptions title="脚本信息" :column="4" size="small" border>
                      <el-descriptions-item label="类型">Web自动化</el-descriptions-item>
                      <el-descriptions-item label="脚本名称">{{ item.name }}</el-descriptions-item>
                      <el-descriptions-item label="最后更新人">
                        {{ item.content?.username ?? '-' }}
                      </el-descriptions-item>
                      <el-descriptions-item label="最后更新时间">
                        {{ item.content?.update_time ?? '-' }}
                      </el-descriptions-item>
                    </el-descriptions>
                  </el-card>
                </div>

                <div style="flex: 1; min-height: 0; display: flex; flex-direction: column">
                  <el-card shadow="never" style="flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden">
                    <!-- 顶部工具栏 -->
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding-bottom: 8px; flex-shrink: 0">
                      <el-dropdown @command="add_script">
                        <el-button type="info">浏览器操作<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item divided :command="{ type: 0, name: '首次打开网页' }">首次打开网页</el-dropdown-item>
                            <el-dropdown-item divided :command="{ type: 13, name: '打开新窗口' }">打开新窗口</el-dropdown-item>
                            <el-dropdown-item divided :command="{ type: 14, name: '切换上一个窗口' }">切换上一个窗口</el-dropdown-item>
                            <el-dropdown-item divided :command="{ type: 15, name: '切换下一个窗口' }">切换下一个窗口</el-dropdown-item>
                            <el-dropdown-item divided :command="{ type: 20, name: '刷新当前页' }">刷新当前页</el-dropdown-item>
                            <el-dropdown-item divided :command="{ type: 21, name: '关闭标签页' }">关闭标签页</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <el-dropdown @command="add_script">
                        <el-button type="primary">AI + 自定义<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ type: 19, name: 'AI 步骤' }">AI 步骤</el-dropdown-item>
                            <el-dropdown-item divided :command="{ type: 17, name: '自定义步骤' }">自定义步骤</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <el-dropdown @command="add_script">
                        <el-button type="primary">鼠标操作<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ type: 1, name: '左键点击' }">左键点击</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 16, name: '右键点击' }">右键点击</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 2, name: '双击事件' }">双击事件</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 3, name: '长按事件' }">长按事件</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 4, name: '拖拽事件' }">拖拽事件</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <el-dropdown @command="add_script">
                        <el-button type="success">输入操作<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ type: 5, name: '直接输入' }">直接输入</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 6, name: '补充输入' }">补充输入</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 7, name: '清空文本' }">清空文本</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <el-dropdown @command="add_script">
                        <el-button type="warning">滑动操作<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ type: 8, name: '上下滑动' }">上下滑动</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <el-dropdown @command="add_script">
                        <el-button type="info">文件操作<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ type: 18, name: '上传文件' }">上传文件</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <el-dropdown @command="add_script">
                        <el-button type="danger">逻辑事件<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item :command="{ type: 10, name: 'if 事件' }">if 事件</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 11, name: 'for 循环' }">for 循环</el-dropdown-item>
                            <el-dropdown-item :command="{ type: 12, name: '等待事件' }">等待事件</el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                      <div style="margin-left: auto; display: flex; gap: 8px">
                        <el-button type="primary" plain @click="ai_script_input()">AI脚本录入</el-button>
                        <el-button type="primary" @click="run_script(item)">立即调试</el-button>
                        <el-button type="success" @click="save_web_script_handler(item.id)">保存</el-button>
                      </div>
                    </div>

                    <!-- 脚本树 + 配置表单 -->
                    <div style="flex: 1; min-height: 0; display: flex; width: 100%">
                      <div class="step-tree-wrap">
                        <div class="step-tree-inner">
                          <el-tree
                            ref="step_treeRef"
                            :data="item.content.script"
                            :props="defaultProps"
                            default-expand-all
                            :allow-drop="on_menu_allowDrop"
                            @node-click="web_script_click"
                            draggable
                            class="step-tree"
                          >
                            <template #default="{ data }">
                              <el-card class="step-card" shadow="never" :body-style="{ padding: '4px 8px' }">
                                <div class="card-header">
                                  <span class="card-left">
                                    <span class="step-icon" :style="{ color: 'rgb(97, 100, 159)' }">1</span>
                                    <span class="method-tag">{{ data.name }}</span>
                                  </span>
                                  <div class="card-actions">
                                    <el-switch
                                      v-model="data.status"
                                      inline-prompt
                                      size="small"
                                      style="--el-switch-on-color: #53a8ff; --el-switch-off-color: #f56c6c"
                                    />
                                    <el-button
                                      :icon="DocumentCopy"
                                      link
                                      type="primary"
                                      size="small"
                                      circle
                                      class="action-button"
                                      title="复制"
                                      @click.stop="copy_row(item.content.script, data)"
                                    />
                                    <el-button
                                      :icon="Delete"
                                      link
                                      type="danger"
                                      size="small"
                                      circle
                                      class="action-button"
                                      title="删除"
                                      @click.stop="Delete_row(item.content.script, data)"
                                    />
                                  </div>
                                </div>
                              </el-card>
                            </template>
                          </el-tree>
                        </div>
                      </div>

                      <!-- 右侧配置表单 -->
                      <div class="step-config-wrap">
                          <el-form>
                            <el-form-item v-if="script_info.type !== 19" label="名称：">
                              <el-input v-model="script_info.name" />
                            </el-form-item>
                            <el-form-item
                              v-if="
                                script_info.type === 0 ||
                                script_info.type === 1 ||
                                script_info.type === 2 ||
                                script_info.type === 3 ||
                                script_info.type === 5 ||
                                script_info.type === 6 ||
                                script_info.type === 7 ||
                                script_info.type === 13 ||
                                script_info.type === 16 ||
                                script_info.type === 17
                              "
                              label="定位："
                            >
                              <el-radio-group v-model="script_info.action.type">
                                <el-radio :value="1">自定义</el-radio>
                                <el-radio :value="2">元素库</el-radio>
                              </el-radio-group>
                            </el-form-item>
                            <el-form-item
                              v-if="
                                script_info.action.type !== 2 &&
                                script_info.type !== 0 &&
                                script_info.type !== 4 &&
                                script_info.type !== 8 &&
                                script_info.type !== 9 &&
                                script_info.type !== 10 &&
                                script_info.type !== 11 &&
                                script_info.type !== 12 &&
                                script_info.type !== 13 &&
                                script_info.type !== 14 &&
                                script_info.type !== 15 &&
                                script_info.type !== 19 &&
                                script_info.type !== 20 &&
                                script_info.type !== 21 &&
                                script_info.type !== 17
                              "
                              label="选择器："
                            >
                              <el-select v-model="script_info.action.locator" style="width: 22%" filterable>
                                <el-option
                                  v-for="item in locator_list"
                                  :key="item.value"
                                  :label="item.name"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.locator === 2"
                                v-model="script_info.action.locator_select"
                                style="width: 22%; padding-left: 15px"
                                filterable
                              >
                                <el-option
                                  v-for="item in locator_selects"
                                  :key="item.value"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.locator_select === 7 && script_info.action.locator === 2"
                                v-model="script_info.action.role"
                                style="width: 22%; padding-left: 15px"
                                filterable
                              >
                                <el-option
                                  v-for="(item, index) in role_list"
                                  :key="index"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                            </el-form-item>
                            <el-form-item
                              v-if="
                                script_info.action.type !== 2 &&
                                (script_info.type === 0 || script_info.type === 13)
                              "
                              label="网址："
                            >
                              <el-input v-model="script_info.action.element" placeholder="请输入网址" />
                            </el-form-item>
                            <el-form-item
                              v-if="
                                script_info.type !== 0 &&
                                script_info.type !== 4 &&
                                script_info.type !== 8 &&
                                script_info.type !== 9 &&
                                script_info.type !== 10 &&
                                script_info.type !== 11 &&
                                script_info.type !== 12 &&
                                script_info.type !== 13 &&
                                script_info.type !== 14 &&
                                script_info.type !== 15 &&
                                script_info.type !== 20 &&
                                script_info.type !== 19 &&
                                script_info.type !== 21 &&
                                script_info.action.type === 1
                              "
                              label="元素值："
                            >
                              <textarea
                                v-if="
                                  (script_info.type !== 19 && script_info.action.locator === 1) ||
                                  script_info.type === 17
                                "
                                v-model="script_info.action.element"
                                style="
                                  padding: 5px;
                                  border: 1px solid var(--el-border-color);
                                  width: 98%;
                                  height: 80px;
                                "
                                placeholder="请输入元素值，多个元素地址用英文逗号“,”隔开"
                              />
                              <el-input
                                v-if="script_info.action.locator === 2"
                                v-model="script_info.action.element"
                                placeholder="请输入元素值"
                              />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 19" label="脚本内容：">
                              <textarea
                                v-model="script_info.action.element"
                                style="
                                  padding: 5px;
                                  border: 1px solid var(--el-border-color);
                                  width: 98%;
                                  height: 80px;
                                "
                                placeholder="例如：用户名输入框输入'admin'"
                              />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 4" label="起始定位：">
                              <el-radio-group v-model="script_info.action.type">
                                <el-radio :value="1">自定义</el-radio>
                                <el-radio :value="2">元素库</el-radio>
                              </el-radio-group>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.action.type === 1 && script_info.type === 4"
                              label="选择器："
                            >
                              <el-select v-model="script_info.action.locator" style="width: 22%" filterable>
                                <el-option
                                  v-for="item in locator_list"
                                  :key="item.value"
                                  :label="item.name"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.locator === 2"
                                v-model="script_info.action.locator_select"
                                style="width: 22%; padding-left: 15px"
                                filterable
                              >
                                <el-option
                                  v-for="item in locator_selects"
                                  :key="item.value"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.locator_select === 7 && script_info.action.locator === 2"
                                v-model="script_info.action.role"
                                style="width: 22%; padding-left: 15px"
                                filterable
                              >
                                <el-option
                                  v-for="(item, index) in role_list"
                                  :key="index"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.action.type === 2 && script_info.type === 4"
                              label="选择元素："
                            >
                              <el-cascader
                                v-model="script_info.action.element_id"
                                placeholder="请选择元素"
                                style="width: 350px"
                                :options="element_select_list"
                                filterable
                                :props="{ value: 'element_id', label: 'name', children: 'children' }"
                                @change="element_select_change"
                              >
                                <template #default="{ node, data }">
                                  <el-icon v-if="data.type === 0" style="padding-right: 5px">
                                    <HomeFilled />
                                  </el-icon>
                                  <el-icon v-if="data.type === 1" style="padding-right: 5px">
                                    <Folder />
                                  </el-icon>
                                  <el-icon v-if="data.type === 2" style="padding-right: 5px">
                                    <ElementPlus />
                                  </el-icon>
                                  <span>{{ data.name }}</span>
                                  <span v-if="!node.isLeaf">({{ data.children?.length ?? 0 }})</span>
                                </template>
                              </el-cascader>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.type === 4 && script_info.action.type === 1"
                              label="起始地址："
                            >
                              <el-input v-model="script_info.action.element" />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 4" label="目标定位：">
                              <el-radio-group v-model="script_info.action.target_type">
                                <el-radio :value="1">自定义</el-radio>
                                <el-radio :value="2">元素库</el-radio>
                              </el-radio-group>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.action.target_type === 1 && script_info.type === 4"
                              label="选择器："
                            >
                              <el-select v-model="script_info.action.target_locator" style="width: 22%" filterable>
                                <el-option
                                  v-for="item in locator_list"
                                  :key="item.value"
                                  :label="item.name"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.target_locator === 2"
                                v-model="script_info.action.target_locator_select"
                                style="width: 22%; padding-left: 15px"
                                filterable
                              >
                                <el-option
                                  v-for="item in locator_selects"
                                  :key="item.value"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.target_locator_select === 7"
                                v-model="script_info.action.role"
                                style="width: 22%; padding-left: 15px"
                                filterable
                              >
                                <el-option
                                  v-for="(item, index) in role_list"
                                  :key="index"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.action.target_type === 2 && script_info.type === 4"
                              label="选择元素："
                            >
                              <el-cascader
                                v-model="script_info.action.target_id"
                                placeholder="请选择元素"
                                style="width: 350px"
                                :options="element_select_list"
                                filterable
                                :props="{ value: 'element_id', label: 'name', children: 'children' }"
                                @change="element_select_change"
                              >
                                <template #default="{ node, data }">
                                  <el-icon v-if="data.type === 0" style="padding-right: 5px">
                                    <HomeFilled />
                                  </el-icon>
                                  <el-icon v-if="data.type === 1" style="padding-right: 5px">
                                    <Folder />
                                  </el-icon>
                                  <el-icon v-if="data.type === 2" style="padding-right: 5px">
                                    <ElementPlus />
                                  </el-icon>
                                  <span>{{ data.name }}</span>
                                  <span v-if="!node.isLeaf">({{ data.children?.length ?? 0 }})</span>
                                </template>
                              </el-cascader>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.type === 4 && script_info.action.target_type === 1"
                              label="目标地址："
                            >
                              <el-input v-model="script_info.action.target" />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 8" label="滑动方向：">
                              <el-radio-group v-model="script_info.action.up_type">
                                <el-radio :value="1">向上</el-radio>
                                <el-radio :value="2">向下</el-radio>
                              </el-radio-group>
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 9" label="滑动方向：">
                              <el-radio-group v-model="script_info.action.sway_type">
                                <el-radio :value="1">向左</el-radio>
                                <el-radio :value="2">向右</el-radio>
                              </el-radio-group>
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 8 || script_info.type === 9" label="像素：">
                              <el-input v-model="script_info.action.element" />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 10">
                              <el-select
                                v-model="script_info.action.type"
                                style="width: 17%; padding-block-end: 5px"
                                filterable
                              >
                                <el-option
                                  v-for="item in assert_list"
                                  :key="item.value"
                                  :label="item.name"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.type === 1 || script_info.action.type === 2"
                                v-model="script_info.action.locator"
                                style="width: 15%; padding-block-end: 5px; padding-left: 5px"
                                filterable
                              >
                                <el-option
                                  v-for="item in locator_list"
                                  :key="item.value"
                                  :label="item.name"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="script_info.action.type === 5"
                                v-model="script_info.action.target_type"
                                style="width: 20%; padding-block-end: 5px; padding-left: 5px"
                                filterable
                              >
                                <el-option
                                  v-for="item in browser_assert"
                                  :key="item.value"
                                  :label="item.name"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="
                                  script_info.action.locator === 2 &&
                                  (script_info.action.type === 1 || script_info.action.type === 2)
                                "
                                v-model="script_info.action.locator_select"
                                style="width: 15%; padding-block-end: 5px; padding-left: 5px"
                                filterable
                              >
                                <el-option
                                  v-for="item in locator_selects"
                                  :key="item.value"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-select
                                v-if="
                                  script_info.action.locator_select === 7 && script_info.action.locator === 2
                                "
                                v-model="script_info.action.input"
                                style="width: 18%; padding-left: 5px; padding-block-end: 5px"
                              >
                                <el-option
                                  v-for="(item, index) in role_list"
                                  :key="index"
                                  :label="item.label"
                                  :value="item.value"
                                />
                              </el-select>
                              <el-input
                                v-model="script_info.action.element"
                                style="width: 30%; padding-left: 5px; padding-block-end: 5px"
                                placeholder="请输入断言内容"
                              />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 12" label="等待时长：">
                              <el-input-number v-model="script_info.action.element" />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 11" label="循环次数：">
                              <el-input-number v-model="script_info.action.element" />
                            </el-form-item>
                            <el-form-item
                              v-if="
                                script_info.action.type === 2 &&
                                script_info.type !== 4 &&
                                script_info.type !== 10
                              "
                              label="选择元素："
                            >
                              <el-cascader
                                v-model="script_info.action.element_id"
                                placeholder="请选择元素"
                                style="width: 350px"
                                :options="element_select_list"
                                filterable
                                :props="{ value: 'element_id', label: 'name', children: 'children' }"
                                @change="element_select_change"
                              >
                                <template #default="{ node, data }">
                                  <el-icon v-if="data.type === 0" style="padding-right: 5px">
                                    <HomeFilled />
                                  </el-icon>
                                  <el-icon v-if="data.type === 1" style="padding-right: 5px">
                                    <Folder />
                                  </el-icon>
                                  <el-icon v-if="data.type === 2" style="padding-right: 5px">
                                    <ElementPlus />
                                  </el-icon>
                                  <span>{{ data.name }}</span>
                                  <span v-if="!node.isLeaf">({{ data.children?.length ?? 0 }})</span>
                                </template>
                              </el-cascader>
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 5 || script_info.type === 6" label="输入值：">
                              <el-input v-model="script_info.action.input" />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 0 || script_info.type === 13">
                              <div style="width: 100%">
                                <el-button
                                  type="primary"
                                  link
                                  :icon="CirclePlus"
                                  @click="add_cookie(script_info.action.cookies || [])"
                                >
                                  添加 cookies 配置项
                                </el-button>
                                <el-form>
                                  <el-form-item
                                    v-for="(ck, index) in (script_info.action.cookies || [])"
                                    :key="index"
                                  >
                                    <el-input
                                      v-model="ck.name"
                                      placeholder="请输入 key"
                                      style="width: 30%; padding-block-end: 5px"
                                    />
                                    <el-input
                                      v-model="ck.value"
                                      placeholder="请输入 value"
                                      style="width: 63%; padding-block-end: 5px; padding-left: 5px"
                                    />
                                    <el-button
                                      type="danger"
                                      link
                                      style="padding-left: 5px; padding-block-end: 10px"
                                      :icon="Remove"
                                      circle
                                      @click="del_cookie(script_info.action.cookies, index)"
                                    />
                                  </el-form-item>
                                </el-form>
                              </div>
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 0 || script_info.type === 13">
                              <div style="width: 100%">
                                <el-button
                                  type="primary"
                                  link
                                  :icon="CirclePlus"
                                  @click="add_localstorage(script_info.action.localstorage || [])"
                                >
                                  添加 localstorage 配置项
                                </el-button>
                                <el-form>
                                  <el-form-item
                                    v-for="(local, index) in (script_info.action.localstorage || [])"
                                    :key="index"
                                  >
                                    <el-input
                                      v-model="local.name"
                                      placeholder="请输入 key"
                                      style="width: 30%; padding-block-end: 5px"
                                    />
                                    <el-input
                                      v-model="local.value"
                                      placeholder="请输入 value"
                                      style="width: 63%; padding-block-end: 5px; padding-left: 5px"
                                    />
                                    <el-button
                                      type="danger"
                                      link
                                      style="padding-left: 5px; padding-block-end: 10px"
                                      :icon="Remove"
                                      circle
                                      @click="del_localstorage(script_info.action.localstorage, index)"
                                    />
                                  </el-form-item>
                                </el-form>
                              </div>
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 21" label="请选择：">
                              <el-radio-group v-model="script_info.action.target">
                                <el-radio value="now">当前标签页</el-radio>
                                <el-radio value="previous">关闭上一个标签页</el-radio>
                                <el-radio value="next">关闭下一个标签页</el-radio>
                                <el-radio value="customize">自定义</el-radio>
                              </el-radio-group>
                            </el-form-item>
                            <el-form-item
                              v-if="script_info.type === 21 && script_info.action.target === 'customize'"
                              label="请选择第几个标签页："
                            >
                              <el-input-number v-model="script_info.action.element" :min="0" :max="10" />
                            </el-form-item>
                            <el-form-item v-if="script_info.type === 18" label="上传文件：">
                              <span v-if="script_info.action.input">
                                （已上传成功：{{ script_info.action.input }}）
                              </span>
                              <div style="width: 100%; display: flex; justify-content: center; height: 220px">
                                <KoiUploadFiles
                                  v-model="script_info.action.input"
                                  :file-name="script_info.action.input"
                                  @file-success="call_back_1"
                                />
                                <el-button plain type="primary" @click="add_file(script_info.action)">
                                  确认上传
                                </el-button>
                              </div>
                            </el-form-item>
                            <div style="margin-top: 4px">
                              <div style="width: 100%">
                                <el-tabs v-model="config_active" class="demo-tabs">
                                  <el-tab-pane label="配置项" name="first">
                                    <el-form label-width="120px" label-position="right" style="margin-top: 8px">
                                      <el-form-item label="执行前等待(秒)">
                                        <el-input-number
                                          v-model="script_info.action.before_wait"
                                          :min="0"
                                          :max="15"
                                          controls-position="right"
                                        />
                                      </el-form-item>
                                      <el-form-item label="执行后等待(秒)">
                                        <el-input-number
                                          v-model="script_info.action.after_wait"
                                          :min="0"
                                          :max="15"
                                          controls-position="right"
                                        />
                                      </el-form-item>
                                      <el-form-item label="超时时长(秒)">
                                        <el-input-number
                                          v-model="script_info.action.timeout"
                                          :min="0"
                                          :max="60"
                                          controls-position="right"
                                        />
                                      </el-form-item>
                                    </el-form>
                                  </el-tab-pane>
                                  <el-tab-pane label="断言" name="second">
                                    <el-button
                                      type="primary"
                                      link
                                      :icon="CirclePlus"
                                      @click="add_assert(script_info.action.assert || [])"
                                    >
                                      添加断言
                                    </el-button>
                                    <el-form>
                                      <el-form-item
                                        v-for="(as, index) in (script_info.action.assert || [])"
                                        :key="index"
                                      >
                                        <el-select
                                          v-model="as.type"
                                          style="width: 17%; padding-block-end: 5px"
                                          filterable
                                        >
                                          <el-option
                                            v-for="item in assert_list"
                                            :key="item.value"
                                            :label="item.name"
                                            :value="item.value"
                                          />
                                        </el-select>
                                        <el-select
                                          v-if="as.type === 1 || as.type === 2"
                                          v-model="as.locator"
                                          style="width: 15%; padding-block-end: 5px; padding-left: 5px"
                                          filterable
                                        >
                                          <el-option
                                            v-for="item in locator_list"
                                            :key="item.value"
                                            :label="item.name"
                                            :value="item.value"
                                          />
                                        </el-select>
                                        <el-select
                                          v-if="as.type === 5"
                                          v-model="as.page_type"
                                          style="width: 20%; padding-block-end: 5px; padding-left: 5px"
                                          filterable
                                        >
                                          <el-option
                                            v-for="item in browser_assert"
                                            :key="item.value"
                                            :label="item.name"
                                            :value="item.value"
                                          />
                                        </el-select>
                                        <el-select
                                          v-if="as.locator === 2 && (as.type === 1 || as.type === 2)"
                                          v-model="as.locator_select"
                                          style="width: 15%; padding-block-end: 5px; padding-left: 5px"
                                          filterable
                                        >
                                          <el-option
                                            v-for="item in locator_selects"
                                            :key="item.value"
                                            :label="item.label"
                                            :value="item.value"
                                          />
                                        </el-select>
                                        <el-select
                                          v-if="as.locator_select === 7 && as.locator === 2"
                                          v-model="as.role"
                                          style="width: 18%; padding-left: 5px; padding-block-end: 5px"
                                        >
                                          <el-option
                                            v-for="(item, index) in role_list"
                                            :key="index"
                                            :label="item.label"
                                            :value="item.value"
                                          />
                                        </el-select>
                                        <el-input
                                          v-if="as.type !== 6 && as.type !== 7"
                                          v-model="as.element"
                                          style="width: 28%; padding-left: 5px; padding-block-end: 5px"
                                          placeholder="请输入断言内容"
                                        />
                                        <el-input
                                          v-if="as.type === 6"
                                          v-model="as.element"
                                          style="width: 75%; padding-left: 5px; padding-block-end: 5px"
                                          placeholder="例如：expect(page.get_by_role('xxx', name='xxx')).to_have_value(xxx)"
                                        />
                                        <el-input
                                          v-if="as.type === 7"
                                          v-model="as.element"
                                          style="width: 75%; padding-left: 5px; padding-block-end: 5px"
                                          placeholder="例如：断言xxx存在当前页面"
                                        />
                                        <el-button
                                          type="danger"
                                          link
                                          style="padding-left: 5px; padding-block-end: 10px"
                                          :icon="Remove"
                                          circle
                                          @click="del_assert(script_info.action.assert, index)"
                                        />
                                      </el-form-item>
                                    </el-form>
                                  </el-tab-pane>
                                </el-tabs>
                              </div>
                            </div>
                          </el-form>
                        </div>
                      </div>
                  </el-card>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 各种对话框：新增/重命名/上传/运行结果等 -->
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
              <el-form-item label="类型：">
                <el-radio-group v-model="add_menu_form.type">
                  <el-radio :value="1">文件夹</el-radio>
                  <el-radio :value="2">脚本</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </template>
        </KoiDialog>

        <KoiDialog
          ref="rename_koiDialogRef"
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

        <KoiDialog
          ref="upload_koiDialogRef"
          :title="title"
          :height="250"
          @koi-confirm="upload_file_confirm"
          @koi-cancel="upload_file_cancel"
        >
          <template #content>
            <div style="width: 100%; display: flex; justify-content: center">
              <KoiUploadFiles
                v-model="file_name"
                :accept-type="'.json'"
                :accept-types="'.json'"
                :file-name="file_name"
                @file-success="call_back"
              />
            </div>
          </template>
        </KoiDialog>

        <KoiDialog
          ref="run_koiDialogRef"
          :title="title"
          :height="200"
          @koi-confirm="run_script_confirm"
          @koi-cancel="run_script_cancel"
        >
          <template #content>
            <el-form>
              <el-form-item label="名称：">
                <el-input v-model="run_script_form.task_name" placeholder="请输入名称" clearable />
              </el-form-item>
              <el-form-item label="执行模式：">
                <el-radio-group v-model="run_script_form.browser_type">
                  <el-radio :value="1">有界面</el-radio>
                  <el-radio :value="2">无界面</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="分辨率(高*宽)：">
                <div>
                  <el-input-number
                    v-model="run_script_form.height"
                    controls-position="right"
                    :min="800"
                    label="高度"
                  />
                  <el-input-number
                    v-model="run_script_form.width"
                    style="padding-left: 10px"
                    controls-position="right"
                    :min="800"
                    label="宽度"
                  />
                </div>
              </el-form-item>
              <el-form-item label="选择浏览器：">
                <el-select v-model="run_script_form.browser" multiple style="width: 60%">
                  <el-option
                    v-for="item in browser_list"
                    :key="item.value"
                    :label="item.name"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </template>
        </KoiDialog>

        <KoiDialog
          ref="res_koiDialogRef"
          :title="title"
          :height="680"
          :width="1600"
          :footer-hidden="true"
        >
          <template #content>
            <div v-loading="loading" style="width: 100%">
              <el-tabs
                tab-position="left"
                v-model="run_browser_active"
                class="demo-tabs"
                @tab-click="change_browser"
              >
                <el-tab-pane v-for="(item, index) in run_browsers" :key="index" :name="item.value">
                  <template #label>
                    <span>{{ item.name }}</span>
                  </template>
                  <div style="width: 100%">
                    <div style="width: 100%; padding-block-end: 10px">
                      <el-card shadow="never" :body-style="{ padding: '8px 12px' }">
                        <el-descriptions :column="5">
                          <el-descriptions-item label="执行状态：">
                            <el-tag type="success" v-if="run_type === '正在执行'">{{ run_type }}</el-tag>
                            <el-tag type="danger" v-else-if="run_type === '执行结束'">{{ run_type }}</el-tag>
                          </el-descriptions-item>
                          <el-descriptions-item label="浏览器：">{{ item.name }}</el-descriptions-item>
                          <el-descriptions-item label="开始时间：">{{ start_time }}</el-descriptions-item>
                          <el-descriptions-item label="结束时间：">{{ end_time }}</el-descriptions-item>
                          <el-descriptions-item label="已执行：">{{ run_count }}</el-descriptions-item>
                          <el-descriptions-item label="通过：">
                            {{ run_count - run_fail }}
                          </el-descriptions-item>
                          <el-descriptions-item label="失败：">{{ run_fail }}</el-descriptions-item>
                        </el-descriptions>
                      </el-card>
                    </div>
                    <div style="width: 100%; display: flex; gap: 8px">
                      <el-card shadow="never" style="width: 30%; height: 560px; overflow-y: auto">
                        <el-timeline style="width: 80%">
                          <el-timeline-item
                            v-for="(res, index) in web_result"
                            :key="index"
                            center
                            :icon="getIcon(res.status)"
                            type="primary"
                            :color="colors(res.status)"
                            size="large"
                            :timestamp="'执行时间：' + formatTime(res.create_time)"
                            placement="top"
                          >
                            <el-card shadow="never" :body-style="{ padding: '6px 10px' }" :style="get_colors(res.status)">
                              <span>{{ res.name }}</span>
                              <span>{{ '结果：' + res.log }}</span>
                            </el-card>
                          </el-timeline-item>
                        </el-timeline>
                      </el-card>
                      <el-card shadow="never" style="flex: 1; height: 560px; overflow-y: auto">
                        <ul>
                          <li
                            v-if="run_type !== '执行结束'"
                            style="margin-bottom: 7px; color: #0bbd87"
                          >
                            执行日志获取中...
                          </li>
                          <li
                            v-for="(log, index) in web_result_log"
                            :key="index"
                            :style="get_log_style(log)"
                          >
                            {{ log }}
                          </li>
                        </ul>
                      </el-card>
                    </div>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </template>
        </KoiDialog>
      </el-card>
    </div>
  </div>
</template>

<style lang="scss" scoped>
/* 脚本信息区域 */
.script-info-card {
  min-height: 72px;
}

/* 步骤树 + 右侧配置：左右分栏，可滚动不重叠 */
.step-tree-wrap {
  width: 50%;
  flex-shrink: 0;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  margin-right: 8px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.step-tree-inner {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: auto;
  padding: 8px;
}
.step-config-wrap {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--el-border-color);
  border-radius: 5px;
  padding: 10px;
  overflow-y: auto;
  overflow-x: auto;
}

/* 步骤树：每行高度紧凑 */
.step-tree :deep(.el-tree-node__content) {
  height: auto;
  margin-bottom: 4px;
  padding: 0;
  min-height: 0;
}
.step-tree :deep(.el-tree-node) {
  margin-bottom: 2px;
}

/* 步骤小卡片：单行紧凑，不叠加重叠 */
.step-card {
  border-radius: 6px;
  margin-bottom: 4px;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  width: 100%;
  position: relative;
  overflow: visible;
  border: 1px solid var(--el-border-color-lighter);
}
.step-card :deep(.el-card__body) {
  padding: 4px 8px;
  line-height: 1.4;
}
.card-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-height: 28px;
}
.card-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
  overflow: hidden;
}
.method-tag {
  font-size: 13px;
  color: #49cc90;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.step-icon {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 20px;
  height: 20px;
  font-size: 11px;
  font-weight: bold;
  border-radius: 50%;
  background: #f0f2f5;
  border: 1px solid #dcdfe6;
  flex-shrink: 0;
}
.card-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.action-button {
  padding: 4px;
  transition: all 0.2s;
}
.action-button:hover {
  transform: scale(1.1);
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
</style>

