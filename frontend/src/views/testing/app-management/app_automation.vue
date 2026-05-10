<template>
  <div class="app-automation-wrapper">
    <div class="app-automation-page">
    <!-- 顶部标题栏 -->
    <el-card class="box-card">
      <div class="automation-topbar">
        <div class="automation-topbar-left">
          <span class="automation-title">APP自动化管理</span>
        </div>
        <div class="automation-actions">
          <el-button type="primary" class="action-button primary-button" @click="get_app_menu()">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <div class="main-layout">
      <!-- 左侧树形菜单 -->
      <div class="tree-sidebar">
        <div class="tree-search">
          <el-input 
            v-model="filterText" 
            placeholder="请输入节点名称" 
            clearable
            style="flex: 1"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="5" animated />
        </div>
        
        <!-- 空状态提示 -->
        <div v-else-if="!tree_data || tree_data.length === 0" class="empty-tree-state">
          <el-empty description="暂无菜单数据">
            <el-button type="primary" @click="create_root_menu">
              <el-icon><CirclePlus /></el-icon>
              恢复根目录
            </el-button>
          </el-empty>
        </div>
        
        <el-tree 
          v-else
          ref="treeRef" 
          class="filter-tree" 
          :data="tree_data" 
          :props="defaultProps"
          default-expand-all 
          :filter-node-method="filterNode" 
          @node-click="app_menu_click"
          :allow-drop="on_menu_allowDrop" 
          draggable
        >
          <template #default="{ node, data }">
            <span class="custom-tree-node">
              <span v-if="data.type === 0">
                <el-icon style="padding-right: 3px; color: #409eff;">
                  <HomeFilled />
                </el-icon>
                <span style="font-weight: 600; color: #409eff;">{{ node.label }}</span>
                <el-tag size="small" type="info" style="margin-left: 8px;">根目录</el-tag>
              </span>
              <span v-if="data.type === 1">
                <el-icon style="padding-right: 3px; color: #e6a23c;">
                  <Folder />
                </el-icon>
                {{ node.label }}
              </span>
              <span v-if="data.type === 2">
                <el-icon style="padding-right: 3px; color: #67c23a;">
                  <Iphone />
                </el-icon>
                {{ node.label }}
              </span>
              <span v-if="data.type === 0" class="right" style="padding-right: 10px">
                <el-dropdown placement="bottom">
                  <el-icon style="cursor: pointer; color: #909399;">
                    <MoreFilled />
                  </el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :icon="CirclePlus" @click="add_menu(data)">新建子菜单</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </span>
              <span v-if="data.type === 1" class="right" style="padding-right: 10px">
                <el-dropdown placement="bottom">
                  <el-icon style="cursor: pointer; color: #909399;">
                    <MoreFilled />
                  </el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :icon="CirclePlus" @click="add_menu(data)">新建子菜单</el-dropdown-item>
                      <el-dropdown-item :icon="Edit" @click="rename_menu(data)">重命名</el-dropdown-item>
                      <el-dropdown-item :icon="Remove" @click="del_menu(data)">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </span>
              <span v-if="data.type === 2" class="right" style="padding-right: 10px">
                <el-dropdown placement="bottom">
                  <el-icon style="cursor: pointer; color: #909399;">
                    <MoreFilled />
                  </el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :icon="Edit" @click="rename_menu(data)">重命名</el-dropdown-item>
                      <el-dropdown-item :icon="Remove" @click="del_menu(data)">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </span>
            </span>
          </template>
        </el-tree>
      </div>
      <!-- 右侧内容区域 -->
      <div class="content-area">
        <el-tabs v-model="tab_active" type="card" closable class="demo-tabs" @tab-remove="removeTab" @tab-click="tab_click">
          <el-tab-pane v-for="(item, index) in tab_list" :key="index" :label="item.title" :name="item.name">
            <!-- 脚本列表页面 -->
            <div v-if="item.type == 1" class="script-list-container">
              <div class="script-actions">
                <el-button type="primary" class="action-button primary-button">
                  <el-icon><VideoPlay /></el-icon>
                  立即调试
                </el-button>
              </div>
              <el-table 
                v-loading="loading" 
                :data="table_list" 
                class="script-table"
                empty-text="暂时没有数据"
                @selection-change="handleSelectionChange"
              >
                <el-table-column type="selection" align="center" />
                <el-table-column label="序号" prop="id" align="center" type="index" width="80" />
                <el-table-column label="脚本名称" prop="name" align="center" :show-overflow-tooltip="true" />
                <el-table-column label="类型" align="center" width="120">
                  <template #default="{ row }">
                    <el-tag v-if="row.type == 1" type="warning">文件夹</el-tag>
                    <el-tag v-if="row.type == 2" type="success">脚本</el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="顺序" align="center" width="120">
                  <template #default="{ row }">
                    <el-input-number :min="1" :max="100" v-model="row.step" size="small" />
                  </template>
                </el-table-column>
                <el-table-column label="操作" align="center" fixed="right" width="120">
                  <template #default="{ row }">
                    <el-tooltip content="删除" placement="top">
                      <el-button type="danger" :icon="Delete" circle plain size="small" @click="Delete_row(row.name)" />
                    </el-tooltip>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 脚本编辑页面 -->
            <div v-if="item.type == 2" class="script-edit-container">
              <!-- 脚本信息卡片 -->
              <el-card class="script-info-card">
                <el-descriptions title="脚本信息" :column="4" size="small">
                  <el-descriptions-item label="类型">APP自动化</el-descriptions-item>
                  <el-descriptions-item label="脚本名称">{{ item.name }}</el-descriptions-item>
                  <el-descriptions-item label="最后更新人">{{ item.content.username }}</el-descriptions-item>
                  <el-descriptions-item label="最后更新时间">{{ item.content.update_time }}</el-descriptions-item>
                </el-descriptions>
              </el-card>

              <!-- 操作按钮 -->
              <div class="script-actions">
                <el-button type="success" class="action-button success-button" @click="save_script(item.id)">
                  <el-icon><Check /></el-icon>
                  保存
                </el-button>
                <el-button type="primary" class="action-button primary-button">
                  <el-icon><VideoPlay /></el-icon>
                  立即调试
                </el-button>
                <el-dropdown @command="add_script">
                  <el-button type="warning" class="action-button warning-button">
                    <el-icon><CirclePlus /></el-icon>
                    添加步骤
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :icon="Download" :command="{ type: 0, name: '等待热更' }">等待热更</el-dropdown-item>
                      <el-dropdown-item :icon="SwitchButton" :command="{ type: 1, name: '启动App' }">启动App</el-dropdown-item>
                      <el-dropdown-item :icon="Pointer" :command="{ type: 2, name: '点击事件' }">点击事件</el-dropdown-item>
                      <el-dropdown-item :icon="Edit" :command="{ type: 3, name: '输入事件' }">输入事件</el-dropdown-item>
                      <el-dropdown-item :icon="Delete" :command="{ type: 4, name: '清空输入' }">清空输入</el-dropdown-item>
                      <el-dropdown-item :icon="Iphone" :command="{ type: 5, name: '手机验证码' }">手机验证码</el-dropdown-item>
                      <el-dropdown-item :icon="TurnOff" :command="{ type: 6, name: '关闭app' }">关闭app</el-dropdown-item>
                      <el-dropdown-item :icon="Sort" :command="{ type: 7, name: 'Tab键' }">Tab键</el-dropdown-item>
                      <el-dropdown-item :icon="Check" :command="{ type: 8, name: '回车键' }">回车键</el-dropdown-item>
                      <el-dropdown-item :icon="Document" :command="{ type: 9, name: '热更 push 文件' }">热更 push 文件</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>

              <!-- 脚本编辑区域 -->
              <div class="script-editor">
                <div class="script-tree-panel">
                  <h4 style="margin-bottom: 16px; color: var(--el-text-color-primary);">脚本步骤</h4>
                  <el-tree 
                    ref="script_tree" 
                    draggable 
                    :data="item.content.script" 
                    :props="defaultProps"
                    :highlight-current="true" 
                    :default-expanded-keys="[1, 10]" 
                    :expand-on-click-node="false"
                    @node-click="app_script_click" 
                    :allow-drop="on_allowDrop"
                    class="step-tree"
                  >
                    <template #default="{ node, data }">
                      <el-card class="step-card" shadow="never" :body-style="{ padding: '4px 8px' }">
                        <div class="card-header">
                          <span class="card-left">
                            <span class="step-icon" :style="{ color: getStepIconColor(data.type) }">
                              <el-icon v-if="data.type === 0"><Download /></el-icon>
                              <el-icon v-else-if="data.type === 1"><SwitchButton /></el-icon>
                              <el-icon v-else-if="data.type === 2"><Pointer /></el-icon>
                              <el-icon v-else-if="data.type === 3"><Edit /></el-icon>
                              <el-icon v-else-if="data.type === 4"><Delete /></el-icon>
                              <el-icon v-else-if="data.type === 5"><Iphone /></el-icon>
                              <el-icon v-else-if="data.type === 6"><TurnOff /></el-icon>
                              <el-icon v-else-if="data.type === 7"><Sort /></el-icon>
                              <el-icon v-else-if="data.type === 8"><Check /></el-icon>
                              <el-icon v-else-if="data.type === 9"><Document /></el-icon>
                              <span v-else>{{ data.type }}</span>
                            </span>
                            <span class="method-tag">{{ node.label }}</span>
                          </span>
                          <div class="card-actions">
                            <el-switch 
                              v-model="data.status" 
                              size="small" 
                              inline-prompt
                              style="--el-switch-on-color: #53a8ff; --el-switch-off-color: #f56c6c"
                            />
                            <el-button 
                              :icon="Remove" 
                              link 
                              type="danger" 
                              size="small" 
                              circle 
                              class="action-button"
                              title="删除"
                              @click.stop="del_script_info(node)" 
                            />
                          </div>
                        </div>
                      </el-card>
                    </template>
                  </el-tree>
                </div>
                <div class="script-form-panel">
                  <h4 style="margin-bottom: 16px; color: var(--el-text-color-primary);">步骤配置</h4>
                  <el-form :model="script_info" label-width="100px">
                    <el-form-item v-if="script_info.type !== ''" label="事件名称">
                      <el-input v-model="script_info.name" placeholder="请输入事件名称" />
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 1 || script_info.type == 6" label="app包名">
                      <el-input v-model="script_info.package" placeholder="请输入app包名" />
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 3 || script_info.type == 7 || script_info.type == 8" label="输入值">
                      <el-input v-model="script_info.value" placeholder="请输入值" />
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 0 || script_info.type == 2 || script_info.type == 3 || script_info.type == 4 || script_info.type == 5" label="图像识别">
                      <el-cascader 
                        v-model="script_info.android.img" 
                        :options="img_select_list" 
                        filterable
                        style="width: 100%;" 
                        :props="props1" 
                        clearable
                        placeholder="请选择图像"
                      >
                        <template #default="{ node, data }">
                          <span style="float: left">{{ node.label }}</span>
                          <span v-if="data.file_path != null && data.file_path != ''" style="float: right;">
                            <el-image 
                              class="w-200px h-30px" 
                              :preview-teleported="true"
                              :preview-src-list="[data.file_path]" 
                              :src="data.file_path"
                            >
                              <template #error></template>
                            </el-image>
                          </span>
                        </template>
                      </el-cascader>
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 2" label="图像断言">
                      <el-cascader 
                        v-model="script_info.android.assert" 
                        :options="img_select_list" 
                        filterable
                        :props="props1" 
                        style="width: 100%" 
                        clearable
                        placeholder="请选择断言图像"
                      >
                        <template #default="{ node, data }">
                          <span style="float: left">{{ node.label }}</span>
                          <span v-if="data.file_path != null && data.file_path != ''" style="float: right;">
                            <el-image 
                              class="w-200px h-36px" 
                              :preview-teleported="true"
                              :preview-src-list="[data.file_path]" 
                              :src="data.file_path"
                            >
                              <template #error>
                                <el-icon class="c-[--el-color-primary]" :size="36">
                                  <CircleCloseFilled />
                                </el-icon>
                              </template>
                            </el-image>
                          </span>
                        </template>
                      </el-cascader>
                    </el-form-item>
                  </el-form>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
    </div>

      <!-- 新增菜单对话框 -->
      <el-dialog v-model="dialogVisible" :title="title" width="400px" ref="add_koiDialogRef">
        <el-form :model="add_menu_form" label-width="80px">
          <el-form-item label="菜单名称">
            <el-input v-model="add_menu_form.name" placeholder="请输入菜单名称" />
          </el-form-item>
          <el-form-item label="菜单类型">
            <el-select v-model="add_menu_form.type" placeholder="请选择类型">
              <el-option label="文件夹" :value="1" />
              <el-option label="脚本" :value="2" />
            </el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="add_menu_cancel">取消</el-button>
          <el-button type="primary" @click="add_menu_confirm">确定</el-button>
        </template>
      </el-dialog>

      <!-- 重命名对话框 -->
      <el-dialog v-model="renameDialogVisible" title="重命名" width="400px" ref="rename_koiDialogRef">
        <el-form :model="add_menu_form" label-width="80px">
          <el-form-item label="菜单名称">
            <el-input v-model="add_menu_form.name" placeholder="请输入菜单名称" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="edit_menu_cancel">取消</el-button>
          <el-button type="primary" @click="edit_menu_confirm">确定</el-button>
        </template>
      </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElTree, TabsPaneContext } from "element-plus";
import { useRoute } from "vue-router";
import { MsgBox, MsgError, MsgSuccess, NoticeError } from "@/utils/koi.ts";
import { formatRequestError } from "/@/utils";
import {
  add_app_menu,
  app_menu,
  del_app_menu,
  get_script,
  rename_app_menu,
  run_app_script,
  save_app_script,
  app_result,
  pid_status,
  stop_process,
  get_script_list,
  app_result_detail,
  run_scripts,
  view_script_list,
  app_correction,
  recover_root_menu
} from "@/api/api_app/app.ts";
import { file_list } from "@/api/api_file/file.ts";
import * as echarts from "echarts";
import { img_select } from "@/api/api_app/img.ts";
import { ElLoading } from "element-plus";
import { LocalStorage } from "@/utils/storage.ts";
import {
  ArrowDown,
  Check,
  Close,
  Delete,
  Document,
  Download,
  Edit,
  Folder,
  HomeFilled,
  Iphone,
  MoreFilled,
  Pointer,
  Refresh,
  Remove,
  Sort,
  SwitchButton,
  TurnOff,
  CircleCloseFilled,
  CirclePlus,
  Picture,
  Search,
  View,
  VideoPlay
} from "@element-plus/icons-vue";

const loading = ref(false);
const filterText = ref<any>("");
const treeRef = ref<InstanceType<typeof ElTree>>();
const tree_data = ref<any>();
const defaultProps = {
  children: "children",
  label: "name"
};

const script_list = ref<any>([]);
const script_info = ref<any>({});
watch(filterText, (val) => {
  treeRef.value!.filter(val);
});

const filterNode = (value: string, data: any) => {
  if (!value) return true;
  return data.name.includes(value);
};

const get_app_menu = async () => {
  try {
    loading.value = true;
    const res: any = await app_menu({});
    console.log("API 返回的数据:", res); // 调试日志
    
    if (res && res.data) {
      tree_data.value = res.data;
      console.log("设置的树数据:", tree_data.value); // 调试日志
      
      // 如果数据为空，可能是软删除问题
      if (res.data.length === 0) {
        console.log("检测到空数据，可能是软删除问题");
      }
    } else {
      tree_data.value = [];
      console.log("API 返回数据为空"); // 调试日志
    }
  } catch (error) {
    console.error("获取菜单失败:", error);
    NoticeError("数据查询失败，请刷新重试🌻");
    tree_data.value = [];
  } finally {
    loading.value = false;
  }
};

const table_list = ref<any>([]);
const app_menu_click = async (node: any) => {
  try {
    if (node.type == 1) {
      loading.value = true;
      const res: any = await get_script_list({ id: node.id });
      table_list.value = res.data;
      table_list.value.forEach((item: any, index: number) => {
        item.step = index + 1;
      });
      await addTab(node, res.data);
    } else if (node.type == 2) {
      loading.value = true;
      const res: any = await get_script({ id: node.id });
      await addTab(node, res.data);
      if (script_info.value.length > 0) {
        script_info.value = res.data.script[0];
      }
    }
  } catch {
    NoticeError("数据查询失败，请刷新重试🌻");
  } finally {
    loading.value = false;
  }
};

const select_list = ref<any>([]);
const handleSelectionChange = (selection: any) => {
  select_list.value = selection.sort((a: any, b: any) => a.step - b.step);
};

const Delete_row = async (name: any) => {
  table_list.value.forEach((item: any, index: any) => {
    if (item.name === name) {
      table_list.value.splice(index, 1);
    }
  });
};
const showPrefix = ref<any>(true);
const props1 = computed(() => ({
  showPrefix: showPrefix.value,
  checkOnClickNode: true
}));

const tab_active = ref("");
const tab_list = ref<any>([]);

const addTab = async (node: any, target: any) => {
  const newTabName = node.name;
  const index = tab_list.value.findIndex((item: any) => item.title === newTabName);
  script_list.value = target.script;
  if (index === -1) {
    tab_list.value.push({
      title: newTabName,
      name: newTabName,
      content: target,
      id: node.id,
      type: node.type
    });
  }
  tab_active.value = node.name;
};

const removeTab = async (targetName: string) => {
  const tabs = tab_list.value;
  let activeName = tab_active.value;
  if (activeName === targetName) {
    tab_list.value.forEach((tab: any, index: any) => {
      if (tab.name === targetName) {
        const nextTab = tabs[index + 1] || tabs[index - 1];
        if (nextTab) {
          activeName = nextTab.name;
          tabs.splice(1, index);
        }
      }
    });
  }
  tab_active.value = activeName;
  tab_list.value = tabs.filter((tab: any) => tab.name !== targetName);
};

const tab_click = async (pane: TabsPaneContext, ev: Event) => {
  console.log(pane);
  console.log(ev);
};

// Additional functions for menu management, script execution, etc.
const add_menu_form = ref<any>({});
const run_form = ref<any>({
  version: "",
  run_type: 1,
  channel_id: "",
  app_list: [
    {
      path: "",
      config: [
        {
          deviceid: "",
          package: ""
        }
      ]
    }
  ]
});
const device_list = ref<any>([]);
const run_device_list = ref<any>([]);
const device_active = ref<any>("");
const title = ref<string>("");
const device = ref<string>("");
const dialogVisible = ref(false);
const renameDialogVisible = ref(false);
const add_koiDialogRef = ref();
const rename_koiDialogRef = ref();
const device_koiDialogRef = ref();
const run_koiDialogRef = ref();
const user = JSON.parse(LocalStorage.get("user"));
const script_id = ref<number>();
const menu_form = ref<any>({
  name: "",
  id: null
});
const pid_list = ref<any>([]);
const run_pid = ref<any>(null);
// Menu management functions
const add_menu = async (data: any) => {
  title.value = "新增子菜单";
  dialogVisible.value = true;
  menu_form.value = data;
  add_menu_form.value = { name: "", type: 1 };
};

const check_children = async (data: any, menu: any) => {
  if ("children" in data) {
    data.children.push(menu);
  } else {
    data.children = [];
    data.children.push(menu);
  }
};

const add_menu_confirm = async () => {
  try {
    add_menu_form.value.pid = menu_form.value.id;
    const res: any = await add_app_menu(add_menu_form.value);
    await check_children(menu_form.value, res.data);
    dialogVisible.value = false;
    MsgSuccess(res.message);
  } catch {
    NoticeError("保存失败，请重试🌻");
  }
};

const add_menu_cancel = async () => {
  dialogVisible.value = false;
};

const rename_menu = async (data: any) => {
  title.value = "重命名";
  renameDialogVisible.value = true;
  menu_form.value = data;
  add_menu_form.value = { name: data.name };
};

const edit_menu_confirm = async () => {
  try {
    add_menu_form.value.id = menu_form.value.id;
    const res: any = await rename_app_menu(add_menu_form.value);
    renameDialogVisible.value = false;
    MsgSuccess(res.message);
    menu_form.value.name = add_menu_form.value.name;
  } catch {
    NoticeError("保存失败，请重试🌻");
  } finally {
    add_menu_form.value = {};
  }
};

const edit_menu_cancel = async () => {
  renameDialogVisible.value = false;
};

const create_root_menu = async () => {
  try {
    const res: any = await recover_root_menu({});
    MsgSuccess("恢复成功");
    await get_app_menu();
  } catch (error: any) {
    NoticeError("恢复失败");
  }
};

const del_menu = async (data: any) => {
  // 防止删除根目录
  if (data.type === 0) {
    NoticeError("根目录不能删除");
    return;
  }
  
  MsgBox("您确认需要删除该目录么？").then(async () => {
    try {
      const res: any = await del_app_menu({ id: data.id, type: data.type });
      console.log("删除响应:", res); // 调试日志
      
      // 刷新数据
      await get_app_menu();
      
      // 根据后端返回判断是否真正删除成功
      if (res && res.code === 200) {
        MsgSuccess("删除成功");
      } else if (res && res.message) {
        NoticeError(res.message);
      } else {
        NoticeError("删除失败");
      }
    } catch (error: any) {
      console.error("删除错误:", error);
      
      // 刷新数据
      await get_app_menu();
      
      if (error?.response?.data?.message) {
        NoticeError(error.response.data.message);
      } else {
        NoticeError("删除失败，请重试");
      }
    }
  });
};

const add_script = (command: any) => {
  // 获取当前激活的 tab
  const activeTab = tab_list.value.find((tab: any) => tab.name === tab_active.value);
  if (activeTab && activeTab.content && activeTab.content.script) {
    activeTab.content.script.push({
      name: command.name,
      address: "",
      type: command.type,
      status: true,
      android: { img: null, assert: null },
      ios: { img: null, assert: null }
    });
  }
};

const app_script_click = async (node: any) => {
  script_info.value = node;
};

const save_script = async (id: number) => {
  try {
    // 获取当前激活的 tab 的脚本列表
    const activeTab = tab_list.value.find((tab: any) => tab.name === tab_active.value);
    const scriptList = activeTab?.content?.script || [];
    
    const res: any = await save_app_script({
      script: scriptList,
      id: id
    });
    MsgSuccess(res.message);
  } catch {
    NoticeError("保存失败，请重试🌻");
  }
};
// Additional utility functions
const img_select_list = ref<any>([]);
const get_img_select = async () => {
  const res: any = await img_select({});
  img_select_list.value = res.data;
};

const del_script_info = async (node: any) => {
  const activeTab = tab_list.value.find((tab: any) => tab.name === tab_active.value);
  if (!activeTab?.content?.script) return;
  const list = activeTab.content.script;
  const index = list.findIndex((item: any) => item.name === node.label);
  if (index === -1) return;
  const removed = list.splice(index, 1)[0];
  try {
    await save_app_script({ script: list, id: activeTab.id });
  } catch (error: unknown) {
    list.splice(index, 0, removed);
    NoticeError(formatRequestError(error, "删除失败，请重试"));
  }
};

const on_allowDrop = (moveNode: any, inNode: any, type: any) => {
  console.log(moveNode, inNode);
  return type !== "inner";
};

const on_menu_allowDrop = (moveNode: any, inNode: any, type: any) => {
  console.log(moveNode, inNode);
  
  // 防止根目录被拖拽
  if (moveNode.data.type === 0) {
    return false;
  }
  
  // 防止拖拽到根目录内部（根目录只能有子菜单）
  if (inNode.data.type === 0 && type === "inner") {
    return true;
  }
  
  if (inNode.data.type == 2) {
    return type !== "inner";
  } else {
    return type;
  }
};

const getStepIconColor = (type: number) => {
  const colors: { [key: number]: string } = {
    0: '#409eff',
    1: '#67c23a', 
    2: '#e6a23c',
    3: '#f56c6c',
    4: '#909399',
    5: '#409eff',
    6: '#f56c6c',
    7: '#e6a23c',
    8: '#67c23a',
    9: '#909399'
  };
  return colors[type] || '#909399';
};

const route = useRoute();

onMounted(() => {
  get_app_menu();
  get_img_select();
});
</script>

<style scoped>
/* 包裹容器 */
.app-automation-wrapper {
  width: 100%;
  height: 100%;
}

/* 通用样式 */
.app-automation-page {
  padding: 10px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.box-card {
  margin-bottom: 10px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 顶部标题栏样式 */
.automation-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.automation-topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.automation-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.automation-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 主布局样式 */
.main-layout {
  display: flex;
  gap: 15px;
  min-height: 600px;
}

/* 左侧树形菜单样式 */
.tree-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.tree-search {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.filter-tree {
  flex: 1;
  overflow: auto;
}

.empty-tree-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.loading-state {
  padding: 20px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
}

/* 右侧内容区域样式 */
.content-area {
  flex: 1;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  min-height: 600px;
}

.demo-tabs {
  min-height: 500px;
}

.demo-tabs .el-tabs__content {
  min-height: 460px;
  overflow: auto;
  padding: 16px;
}

/* 脚本列表容器样式 */
.script-list-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.script-actions {
  margin-bottom: 20px;
  padding: 0 4px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.script-table {
  flex: 1;
  border-radius: 6px;
  overflow: hidden;
}

/* 脚本编辑容器样式 */
.script-edit-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 4px;
}

.script-info-card {
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.script-editor {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.script-tree-panel {
  width: 50%;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-lighter);
  height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
}

.script-tree-panel::-webkit-scrollbar {
  width: 6px;
}

.script-tree-panel::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 3px;
}

.script-tree-panel::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.script-tree-panel::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

.script-form-panel {
  width: 50%;
  background: var(--el-fill-color-light);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--el-border-color-lighter);
  height: 500px;
  overflow-y: auto;
  overflow-x: hidden;
}

.script-form-panel::-webkit-scrollbar {
  width: 6px;
}

.script-form-panel::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 3px;
}

.script-form-panel::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.script-form-panel::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}

.script-tree-panel .step-tree {
  background: transparent;
  height: 100%;
}

.script-tree-panel .step-tree .el-tree-node {
  position: relative;
  margin-bottom: 8px;
}

.script-tree-panel .step-tree .el-tree-node:not(:last-child) {
  margin-bottom: 12px;
}

/* 步骤小卡片：参考 web_view 的实现 */
.step-card {
  border-radius: 6px;
  margin-bottom: 8px !important;
  transition: all 0.2s;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  width: 100%;
  position: relative;
  overflow: visible;
  border: 1px solid var(--el-border-color-lighter);
  display: block !important;
}

.step-card:not(:last-child) {
  margin-bottom: 12px !important;
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

.step-tree :deep(.el-tree-node__content) {
  margin-bottom: 8px !important;
  height: auto !important;
  padding: 0 !important;
  background: transparent !important;
  border: none !important;
}

.step-tree :deep(.el-tree-node__expand-icon) {
  display: none !important;
}

.step-tree :deep(.el-tree-node) {
  white-space: normal !important;
  margin-bottom: 8px !important;
  position: relative !important;
}

.step-tree :deep(.el-tree-node > .el-tree-node__children) {
  padding-left: 0 !important;
}

.step-tree :deep(.el-tree-node__label) {
  display: none !important;
}

.step-tree :deep(.el-tree-node:not(:last-child)) {
  margin-bottom: 12px !important;
}

/* 按钮样式 */
.action-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.primary-button {
  background: linear-gradient(135deg, #409eff, #1890ff);
  border: none;
  color: white;
}

.primary-button:hover {
  background: linear-gradient(135deg, #66b1ff, #40a9ff);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.success-button {
  background: linear-gradient(135deg, #67c23a, #52c41a);
  border: none;
  color: white;
}

.success-button:hover {
  background: linear-gradient(135deg, #85ce61, #73d13d);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.4);
}

.warning-button {
  background: linear-gradient(135deg, #e6a23c, #fa8c16);
  border: none;
  color: white;
}

.warning-button:hover {
  background: linear-gradient(135deg, #ebb563, #ffa940);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.4);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-layout {
    flex-direction: column;
    height: auto;
  }
  
  .tree-sidebar {
    width: 100%;
    height: 300px;
  }
  
  .script-editor {
    flex-direction: column;
  }
  
  .script-tree-panel,
  .script-form-panel {
    width: 100%;
  }
}

/* 深色模式适配 */
@media (prefers-color-scheme: dark) {
  .automation-title {
    background: linear-gradient(135deg, #a8b8ff 0%, #c4a8ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}
</style>