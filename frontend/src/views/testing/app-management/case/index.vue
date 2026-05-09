<template>
  <div class="case-layout">

    <!-- 左侧脚本树 -->
    <div class="case-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">
          <el-icon class="sidebar-title-icon"><Files /></el-icon>
          用例管理
        </span>
        <div class="sidebar-actions">
          <el-tooltip content="刷新" placement="top">
            <el-button size="small" :icon="Refresh" circle @click="get_app_menu()" />
          </el-tooltip>
        </div>
      </div>
      <el-input
        v-model="filterText"
        clearable
        placeholder="过滤名称"
        size="small"
        class="sidebar-filter"
        :prefix-icon="Search"
      />
      <el-scrollbar class="sidebar-tree-wrap">
        <div v-if="loading" class="sidebar-skeleton">
          <el-skeleton :rows="6" animated />
        </div>
        <div v-else-if="!tree_data || tree_data.length === 0" class="sidebar-empty">
          <el-empty :image-size="60" description="暂无数据">
            <el-button type="primary" size="small" @click="create_root_menu">恢复根目录</el-button>
          </el-empty>
        </div>
        <el-tree
          v-else
          ref="treeRef"
          :data="tree_data"
          :props="defaultProps"
          default-expand-all
          :filter-node-method="filterNode"
          @node-click="app_menu_click"
          :allow-drop="on_menu_allowDrop"
          draggable
        >
          <template #default="{ node, data }">
            <span class="tree-node">
              <span class="tree-node-label">
                <el-icon v-if="data.type === 0" class="tree-ico root"><HomeFilled /></el-icon>
                <el-icon v-else-if="data.type === 1" class="tree-ico folder"><Folder /></el-icon>
                <el-icon v-else class="tree-ico leaf"><Iphone /></el-icon>
                <span class="tree-node-name">{{ node.label }}</span>
                <el-tag v-if="data.type === 0" size="small" type="info" class="root-tag">根</el-tag>
              </span>
              <span class="tree-node-ops" @click.stop>
                <el-dropdown trigger="click" placement="bottom-end" @command="(cmd: string) => onTreeCmd(cmd, data)">
                  <el-icon class="tree-more"><MoreFilled /></el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="data.type === 0 || data.type === 1" command="add" :icon="CirclePlus">新建子菜单</el-dropdown-item>
                      <el-dropdown-item v-if="data.type !== 0" command="rename" :icon="Edit">重命名</el-dropdown-item>
                      <el-dropdown-item v-if="data.type !== 0" command="delete" :icon="Remove" class="danger-item">删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </span>
            </span>
          </template>
        </el-tree>
      </el-scrollbar>
    </div>

    <!-- 右侧工作区 -->
    <div class="case-workspace">
      <div v-if="tab_list.length === 0" class="workspace-empty">
        <el-empty :image-size="80" description="点击左侧脚本或文件夹开始编辑" />
      </div>

      <el-tabs
        v-else
        v-model="tab_active"
        type="card"
        closable
        class="workspace-tabs"
        @tab-remove="removeTab"
        @tab-click="tab_click"
      >
        <el-tab-pane v-for="(item, index) in tab_list" :key="index" :label="item.title" :name="item.name">

          <!-- 文件夹列表视图 -->
          <div v-if="item.type == 1" class="folder-view">
            <div class="view-toolbar">
              <span class="view-toolbar-title">
                <el-icon><Folder /></el-icon>{{ item.title }}
              </span>
            </div>
            <el-table v-loading="loading" :data="table_list" stripe border empty-text="暂无脚本" @selection-change="handleSelectionChange">
              <el-table-column type="selection" width="44" align="center" />
              <el-table-column label="#" type="index" width="56" align="center" />
              <el-table-column label="脚本名称" prop="name" show-overflow-tooltip />
              <el-table-column label="类型" width="100" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.type == 1" type="warning" size="small">文件夹</el-tag>
                  <el-tag v-if="row.type == 2" type="success" size="small">脚本</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="顺序" width="130" align="center">
                <template #default="{ row }">
                  <el-input-number v-model="row.step" :min="1" :max="100" size="small" controls-position="right" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button type="danger" size="small" :icon="Delete" circle @click="Delete_row(row.name)" />
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 脚本编辑视图 -->
          <div v-if="item.type == 2" class="script-view">

            <!-- 顶部信息栏 -->
            <div class="script-infobar">
              <div class="infobar-meta">
                <el-tag type="primary" size="small" effect="plain">APP自动化</el-tag>
                <span class="infobar-name">{{ item.name }}</span>
                <span v-if="item.content.username" class="infobar-sub">
                  <el-icon><User /></el-icon>{{ item.content.username }}
                </span>
                <span v-if="item.content.update_time" class="infobar-sub">
                  <el-icon><Clock /></el-icon>{{ item.content.update_time }}
                </span>
              </div>
              <div class="infobar-actions">
                <el-button type="success" size="small" :icon="Check" @click="save_script(item.id)">保存</el-button>
                <el-button type="primary" size="small" :icon="VideoPlay" @click="openRunDebug(item.id)">立即调试</el-button>
                <el-dropdown @command="add_script">
                  <el-button type="warning" size="small">
                    <el-icon><CirclePlus /></el-icon>添加步骤<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :icon="Download"     :command="{ type: 0, name: '等待热更' }">等待热更</el-dropdown-item>
                      <el-dropdown-item :icon="SwitchButton" :command="{ type: 1, name: '启动App' }">启动App</el-dropdown-item>
                      <el-dropdown-item :icon="Pointer"      :command="{ type: 2, name: '点击事件' }">点击事件</el-dropdown-item>
                      <el-dropdown-item :icon="Edit"         :command="{ type: 3, name: '输入事件' }">输入事件</el-dropdown-item>
                      <el-dropdown-item :icon="Delete"       :command="{ type: 4, name: '清空输入' }">清空输入</el-dropdown-item>
                      <el-dropdown-item :icon="Iphone"       :command="{ type: 5, name: '手机验证码' }">手机验证码</el-dropdown-item>
                      <el-dropdown-item :icon="TurnOff"      :command="{ type: 6, name: '关闭app' }">关闭app</el-dropdown-item>
                      <el-dropdown-item :icon="Sort"         :command="{ type: 7, name: 'Tab键' }">Tab键</el-dropdown-item>
                      <el-dropdown-item :icon="Check"        :command="{ type: 8, name: '回车键' }">回车键</el-dropdown-item>
                      <el-dropdown-item :icon="Document"     :command="{ type: 9, name: '热更 push 文件' }">热更 push 文件</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>

            <!-- 步骤 + 配置双栏 -->
            <div class="script-body">

              <!-- 左：步骤列表 -->
              <div class="steps-panel">
                <div class="panel-header">
                  <el-icon class="panel-header-icon"><List /></el-icon>
                  脚本步骤
                  <el-tag size="small" type="info" class="step-count">{{ item.content.script?.length ?? 0 }}</el-tag>
                </div>
                <el-scrollbar class="steps-scroll">
                  <div v-if="!item.content.script || item.content.script.length === 0" class="steps-empty">
                    <el-empty :image-size="48" description="暂无步骤，点击「添加步骤」" />
                  </div>
                  <el-tree
                    v-else
                    ref="script_tree"
                    draggable
                    :data="item.content.script"
                    :props="defaultProps"
                    :highlight-current="true"
                    :expand-on-click-node="false"
                    @node-click="app_script_click"
                    :allow-drop="on_allowDrop"
                    @node-drop="(a: any, b: any, c: any) => onScriptNodeDrop(a, b, c, item)"
                    class="step-tree"
                  >
                    <template #default="{ node, data }">
                      <div class="step-row" :class="{ 'step-row--disabled': !data.status }">
                        <span class="step-row-icon" :style="{ background: getStepIconBg(data.type) }">
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
                        </span>
                        <span class="step-row-name">{{ node.label }}</span>
                        <div class="step-row-actions">
                          <el-switch v-model="data.status" size="small" inline-prompt
                            style="--el-switch-on-color:#409eff;--el-switch-off-color:#dcdfe6" @click.stop />
                          <el-button link type="danger" size="small" :icon="Remove" @click.stop="del_script_info(node)" />
                        </div>
                      </div>
                    </template>
                  </el-tree>
                </el-scrollbar>
              </div>

              <!-- 右：步骤配置 -->
              <div class="config-panel">
                <div class="panel-header">
                  <el-icon class="panel-header-icon"><Setting /></el-icon>
                  步骤配置
                </div>
                <el-scrollbar class="config-scroll">
                  <div v-if="script_info.type === '' || script_info.type === undefined" class="config-empty">
                    <el-empty :image-size="48" description="点击左侧步骤进行配置" />
                  </div>
                  <el-form v-else :model="script_info" label-width="90px" class="config-form" size="small">
                    <el-form-item label="事件名称">
                      <el-input v-model="script_info.name" placeholder="请输入事件名称" />
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 1 || script_info.type == 6" label="app包名">
                      <el-input v-model="script_info.package" placeholder="请输入app包名" />
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 3 || script_info.type == 7 || script_info.type == 8" label="输入值">
                      <el-input v-model="script_info.value" placeholder="请输入值" />
                    </el-form-item>
                    <el-form-item v-if="[0,2,3,4,5].includes(Number(script_info.type))" label="图像识别">
                      <el-cascader v-model="script_info.android.img" :options="img_select_list" filterable style="width:100%" :props="props1" clearable placeholder="请选择图像">
                        <template #default="{ node, data }">
                          <span style="float:left">{{ node.label }}</span>
                          <span v-if="data.file_path" style="float:right; margin-left:8px">
                            <el-image
                              style="width:32px;height:32px;border-radius:4px;vertical-align:middle;"
                              fit="cover"
                              :preview-teleported="true"
                              :preview-src-list="[data.file_path]"
                              :src="data.file_path"
                            ><template #error></template></el-image>
                          </span>
                        </template>
                      </el-cascader>
                    </el-form-item>
                    <el-form-item v-if="script_info.type == 2" label="图像断言">
                      <el-cascader v-model="script_info.android.assert" :options="img_select_list" filterable :props="props1" style="width:100%" clearable placeholder="请选择断言图像">
                        <template #default="{ node, data }">
                          <span style="float:left">{{ node.label }}</span>
                          <span v-if="data.file_path" style="float:right; margin-left:8px">
                            <el-image
                              style="width:32px;height:32px;border-radius:4px;vertical-align:middle;"
                              fit="cover"
                              :preview-teleported="true"
                              :preview-src-list="[data.file_path]"
                              :src="data.file_path"
                            >
                              <template #error><el-icon :size="16"><CircleCloseFilled /></el-icon></template>
                            </el-image>
                          </span>
                        </template>
                      </el-cascader>
                    </el-form-item>
                    <template v-if="script_info.android && [2,3,4].includes(Number(script_info.type))">
                      <el-divider content-position="left" class="config-divider">
                        <el-icon><Link /></el-icon> 页面元素（与「页面管理」联动）
                      </el-divider>
                      <el-form-item label="定位类型">
                        <el-input v-model="script_info.android.locate_type" clearable placeholder="id / xpath / accessibility_id / class_name" />
                      </el-form-item>
                      <el-form-item label="定位值">
                        <el-input v-model="script_info.android.locate_value" type="textarea" :rows="2" clearable placeholder="填写或与下方元素库同步" />
                      </el-form-item>
                      <el-form-item label="元素库">
                        <div class="element-lib-row">
                          <el-button size="small" type="primary" :icon="Search" @click="openElementPicker">从页面元素选择</el-button>
                          <el-tag v-if="script_info.element_id" size="small" type="success" class="element-linked-tag">已关联 #{{ script_info.element_id }}</el-tag>
                        </div>
                      </el-form-item>
                    </template>
                  </el-form>
                </el-scrollbar>
              </div>

            </div>
          </div>

        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 新增菜单 dialog -->
    <el-dialog v-model="dialogVisible" :title="title" width="400px" destroy-on-close>
      <el-form :model="add_menu_form" label-width="80px">
        <el-form-item label="菜单名称"><el-input v-model="add_menu_form.name" placeholder="请输入菜单名称" /></el-form-item>
        <el-form-item label="菜单类型">
          <el-select v-model="add_menu_form.type" placeholder="请选择类型" style="width:100%">
            <el-option label="文件夹" :value="1" /><el-option label="脚本" :value="2" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="add_menu_cancel">取消</el-button>
        <el-button type="primary" @click="add_menu_confirm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重命名 dialog -->
    <el-dialog v-model="renameDialogVisible" title="重命名" width="400px" destroy-on-close>
      <el-form :model="add_menu_form" label-width="80px">
        <el-form-item label="菜单名称"><el-input v-model="add_menu_form.name" placeholder="请输入菜单名称" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="edit_menu_cancel">取消</el-button>
        <el-button type="primary" @click="edit_menu_confirm">确定</el-button>
      </template>
    </el-dialog>

    <!-- 元素选择 dialog -->
    <el-dialog v-model="elementPickVisible" title="从页面元素库选择" width="520px" destroy-on-close append-to-body>
      <el-form label-width="60px">
        <el-form-item label="模块">
          <el-select v-model="pickModuleId" filterable clearable placeholder="选择页面管理中的模块" style="width:100%" :loading="pageModuleLoading" @change="onPickModuleChange">
            <el-option v-for="o in moduleMenuOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="页面">
          <el-select v-model="pickPageId" filterable clearable placeholder="先选模块" style="width:100%" :disabled="pickModuleId === null || pickModuleId === undefined" @change="onPickPageChange">
            <el-option v-for="o in pickPageOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="元素">
          <el-select v-model="pickElementId" filterable clearable placeholder="先选页面" style="width:100%" :disabled="pickPageId === null || pickPageId === undefined">
            <el-option v-for="o in pickElementOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="elementPickVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!pickElementId" @click="applyPickedElement">填入当前步骤</el-button>
      </template>
    </el-dialog>

    <!-- 执行调试 dialog -->
    <el-dialog v-model="runDebugVisible" title="执行调试" width="520px" destroy-on-close>
      <el-form :model="runForm" label-width="110px">
        <el-form-item label="Appium 服务器" required>
          <el-select v-model="runForm.server_id" filterable clearable placeholder="从设备中心选择" style="width:100%">
            <el-option v-for="o in serverOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="运行设备" required>
          <el-select v-model="runForm.phone_id" filterable clearable placeholder="从设备中心选择" style="width:100%">
            <el-option v-for="o in phoneOpts" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="包名" required>
          <el-input v-model="runForm.package" placeholder="Android applicationId" />
        </el-form-item>
        <el-form-item label="Activity">
          <el-input v-model="runForm.app_activity" placeholder="默认 .MainActivity" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="runDebugVisible = false">取消</el-button>
        <el-button type="primary" :loading="runSubmitting" @click="submitRunDebug">开始执行</el-button>
      </template>
    </el-dialog>

  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElTree, TabsPaneContext } from "element-plus";
import { useRoute } from "vue-router";
import { MsgBox, MsgError, MsgSuccess, NoticeError } from "@/utils/koi.ts";
import { appManagementDeviceApi } from "/@/api/v1/app_management_device";
import { useAppManagementApi } from "/@/api/v1/app_management";

const appMgmtApi = useAppManagementApi();
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
  Files,
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
  VideoPlay,
  User,
  Clock,
  List,
  Setting,
  Link,
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
    NoticeError("数据查询失败，请刷新重试");
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
      if (res?.data?.script && Array.isArray(res.data.script)) {
        normalizeScriptList(res.data.script);
      }
      await addTab(node, res.data);
      if (script_info.value.length > 0) {
        script_info.value = res.data.script[0];
      }
    }
  } catch {
    NoticeError("数据查询失败，请刷新重试");
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
  if (target?.script && Array.isArray(target.script)) {
    normalizeScriptList(target.script);
  }
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

/** 页面元素选择（与页面管理 app_ui_elements 联动） */
const elementPickVisible = ref(false);
const pickModuleId = ref<number | null>(null);
const pickPageId = ref<number | null>(null);
const pickElementId = ref<number | null>(null);
const pickPageOpts = ref<{ label: string; value: number }[]>([]);
const pickElementOpts = ref<{ label: string; value: number; raw: any }[]>([]);

// 页面管理的模块树（独立加载，与用例树无关）
const pageModuleTree = ref<any[]>([]);
const pageModuleLoading = ref(false);

async function loadPageModuleTree() {
	if (pageModuleTree.value.length > 0) return; // 已加载过则跳过
	pageModuleLoading.value = true;
	try {
		const res: any = await appMgmtApi.app_menu({});
		const raw = res?.data ?? res;
		pageModuleTree.value = Array.isArray(raw) ? raw : raw?.data ?? [];
	} catch {
		pageModuleTree.value = [];
	} finally {
		pageModuleLoading.value = false;
	}
}

const moduleMenuOptions = computed(() => {
	const out: { label: string; value: number }[] = [];
	const walk = (nodes: any[]) => {
		for (const n of nodes || []) {
			if (n.type === 0 || n.type === 1) {
				out.push({
					label: n.type === 0 ? `【根】${n.name}` : String(n.name),
					value: n.id,
				});
			}
			if (n.children?.length) walk(n.children);
		}
	};
	walk(pageModuleTree.value);
	return out;
});

function ensureStepAndroid(s: any) {
	if (!s || typeof s !== "object") return;
	if (!s.android || typeof s.android !== "object") s.android = {};
	const a = s.android;
	if (a.img === undefined) a.img = null;
	if (a.assert === undefined) a.assert = null;
	if (a.locate_type === undefined) a.locate_type = "";
	if (a.locate_value === undefined) a.locate_value = "";
	if (!s.ios || typeof s.ios !== "object") s.ios = { img: null, assert: null };
	if (s.element_id === undefined) s.element_id = null;
}

function normalizeScriptList(list: any[]) {
	if (!Array.isArray(list)) return;
	list.forEach((s) => ensureStepAndroid(s));
}

async function onPickModuleChange() {
	pickPageId.value = null;
	pickElementId.value = null;
	pickPageOpts.value = [];
	pickElementOpts.value = [];
	if (pickModuleId.value === null || pickModuleId.value === undefined) return;
	try {
		const res: any = await appMgmtApi.pageList({
			module_menu_id: pickModuleId.value,
			currentPage: 1,
			pageSize: 500,
		});
		// 兼容多种后端返回结构
		const payload = res?.data ?? res;
		const rows: any[] = payload?.data ?? payload?.list ?? (Array.isArray(payload) ? payload : []);
		pickPageOpts.value = rows.map((r: any) => ({ label: r.name, value: r.id }));
	} catch {
		pickPageOpts.value = [];
	}
}

async function onPickPageChange() {
	pickElementId.value = null;
	pickElementOpts.value = [];
	if (pickPageId.value === null || pickPageId.value === undefined) return;
	try {
		const res: any = await appMgmtApi.pageElementList({ page_id: pickPageId.value });
		const raw = res?.data ?? res;
		const list: any[] = Array.isArray(raw) ? raw : raw?.data ?? raw?.list ?? [];
		pickElementOpts.value = list.map((r: any) => ({
			label: `${r.name} (${r.locate_type})`,
			value: r.id,
			raw: r,
		}));
	} catch {
		pickElementOpts.value = [];
	}
}

function openElementPicker() {
	if (!script_info.value || script_info.value.type === undefined || script_info.value.type === "") {
		MsgError("请先点击选择一个步骤");
		return;
	}
	if (![2, 3, 4].includes(Number(script_info.value.type))) {
		MsgError("仅点击 / 输入 / 清空步骤支持元素库");
		return;
	}
	pickModuleId.value = null;
	pickPageId.value = null;
	pickElementId.value = null;
	pickPageOpts.value = [];
	pickElementOpts.value = [];
	loadPageModuleTree(); // 加载页面管理的模块树
	elementPickVisible.value = true;
}

function applyPickedElement() {
	const opt = pickElementOpts.value.find((x) => x.value === pickElementId.value);
	if (!opt?.raw) return;
	ensureStepAndroid(script_info.value);
	script_info.value.element_id = opt.raw.id;
	script_info.value.android.locate_type = opt.raw.locate_type || "id";
	script_info.value.android.locate_value = opt.raw.locate_value || "";
	elementPickVisible.value = false;
	MsgSuccess("已同步定位到当前步骤");
}

function onScriptNodeDrop(draggingNode: any, dropNode: any, dropType: string, item: any) {
	if (!item?.content?.script || !Array.isArray(item.content.script)) return;
	if (dropType === "inner") return;
	const list = item.content.script;
	const from = list.indexOf(draggingNode.data);
	if (from === -1) return;
	const [row] = list.splice(from, 1);
	let to = list.indexOf(dropNode.data);
	if (to === -1) {
		list.splice(from, 0, row);
		return;
	}
	if (dropType === "after") to += 1;
	list.splice(to, 0, row);
}

const runDebugVisible = ref(false);
const runSubmitting = ref(false);
const runTargetMenuId = ref<number | null>(null);
const runForm = ref({
  server_id: undefined as number | undefined,
  phone_id: undefined as number | undefined,
  package: "",
  app_activity: ".MainActivity",
});
const serverOpts = ref<{ label: string; value: number }[]>([]);
const phoneOpts = ref<{ label: string; value: number }[]>([]);

async function loadRunDeviceOptions() {
  const [sr, pr]: any[] = await Promise.all([
    appManagementDeviceApi.serverList({ currentPage: 1, pageSize: 200 }),
    appManagementDeviceApi.phoneList({ currentPage: 1, pageSize: 200 }),
  ]);
  const sdata = sr?.data ?? sr;
  const pdata = pr?.data ?? pr;
  serverOpts.value = (sdata?.data || []).map((x: any) => ({
    label: `${x.name} (${x.ip}:${x.port})`,
    value: x.id,
  }));
  phoneOpts.value = (pdata?.data || []).map((x: any) => ({
    label: `${x.name} (${x.device_id})`,
    value: x.id,
  }));
}

function openRunDebug(menuId: number) {
  runTargetMenuId.value = menuId;
  runForm.value = {
    server_id: undefined,
    phone_id: undefined,
    package: "",
    app_activity: ".MainActivity",
  };
  loadRunDeviceOptions();
  runDebugVisible.value = true;
}

async function submitRunDebug() {
  if (!runTargetMenuId.value) {
    MsgError("未选择脚本");
    return;
  }
  if (!runForm.value.server_id || !runForm.value.phone_id || !String(runForm.value.package || "").trim()) {
    MsgError("请填写 Appium 服务器、运行设备与包名");
    return;
  }
  runSubmitting.value = true;
  try {
    const res: any = await run_app_script({
      id: runTargetMenuId.value,
      task_name: "脚本调试",
      device_list: [
        {
          server_id: runForm.value.server_id,
          phone_id: runForm.value.phone_id,
          package: runForm.value.package.trim(),
          app_activity: runForm.value.app_activity || ".MainActivity",
        },
      ],
    });
    MsgSuccess(res?.message || "已启动");
    runDebugVisible.value = false;
  } catch {
    NoticeError("启动失败");
  } finally {
    runSubmitting.value = false;
  }
}

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
    NoticeError("保存失败，请重试");
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
    NoticeError("保存失败，请重试");
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
      element_id: null,
      android: { img: null, assert: null, locate_type: "", locate_value: "" },
      ios: { img: null, assert: null }
    });
  }
};

const app_script_click = async (node: any) => {
  ensureStepAndroid(node);
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
    NoticeError("保存失败，请重试");
  }
};
// Additional utility functions
const img_select_list = ref<any>([]);
const get_img_select = async () => {
  const res: any = await img_select({});
  img_select_list.value = res.data;
};

const del_script_info = async (node: any) => {
  // 获取当前激活的 tab
  const activeTab = tab_list.value.find((tab: any) => tab.name === tab_active.value);
  if (activeTab && activeTab.content && activeTab.content.script) {
    const list = activeTab.content.script;
    const index = list.findIndex((item: any) => item.name === node.label);
    if (index !== -1) {
      list.splice(index, 1);
      // 自动保存到后端
      try {
        await save_app_script(activeTab.id);
      } catch (error) {
        NoticeError("删除失败，请重试");
      }
    }
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
    0: '#409eff', 1: '#67c23a', 2: '#e6a23c', 3: '#f56c6c',
    4: '#909399', 5: '#409eff', 6: '#f56c6c', 7: '#e6a23c',
    8: '#67c23a', 9: '#909399'
  };
  return colors[type] || '#909399';
};

const getStepIconBg = (type: number) => getStepIconColor(type);

// 树节点统一命令处理（新 template 用）
function onTreeCmd(cmd: string, data: any) {
  if (cmd === 'add') add_menu(data);
  else if (cmd === 'rename') rename_menu(data);
  else if (cmd === 'delete') del_menu(data);
}

const route = useRoute();

onMounted(() => {
  get_app_menu();
  get_img_select();
});
</script>


<style scoped lang="scss">
/* ── 整体布局 ── */
.case-layout {
  display: flex;
  height: calc(100vh - 160px);
  min-height: 480px;
  background: var(--el-bg-color-page);
}

/* ── 左侧侧边栏 ── */
.case-sidebar {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-lighter);
  padding: 12px 10px 10px;
  gap: 8px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.sidebar-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.sidebar-title-icon {
  color: var(--el-color-primary);
  font-size: 16px;
}

.sidebar-actions { display: flex; gap: 4px; }

.sidebar-filter { flex-shrink: 0; }

.sidebar-tree-wrap { flex: 1; }

.sidebar-skeleton { padding: 12px; }

.sidebar-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px 0;
}

/* 树节点 */
.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  padding-right: 2px;
}

.tree-node-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
}

.tree-node-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}

.root-tag { flex-shrink: 0; margin-left: 2px; }

.tree-node-ops {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.el-tree-node:hover .tree-node-ops,
.el-tree-node.is-current .tree-node-ops {
  opacity: 1;
}

.tree-more {
  cursor: pointer;
  color: var(--el-text-color-secondary);
  font-size: 15px;
  padding: 2px;
  border-radius: 3px;
  &:hover { color: var(--el-color-primary); background: var(--el-fill-color); }
}

.tree-ico {
  font-size: 14px;
  flex-shrink: 0;
  &.root   { color: var(--el-color-primary); }
  &.folder { color: var(--el-color-warning); }
  &.leaf   { color: var(--el-color-success); }
}

:deep(.danger-item) { color: var(--el-color-danger) !important; }

/* ── 右侧工作区 ── */
.case-workspace {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.workspace-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.workspace-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.el-tabs__header) {
    margin: 0;
    padding: 0 12px;
    background: var(--el-bg-color);
    border-bottom: 1px solid var(--el-border-color-lighter);
    flex-shrink: 0;
  }

  :deep(.el-tabs__content) {
    flex: 1;
    overflow: hidden;
    padding: 0;
  }

  :deep(.el-tab-pane) {
    height: 100%;
    overflow: hidden;
  }
}

/* ── 文件夹视图 ── */
.folder-view {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.view-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.view-toolbar-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

/* ── 脚本编辑视图 ── */
.script-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部信息栏 */
.script-infobar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}

.infobar-meta {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex-wrap: wrap;
}

.infobar-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.infobar-sub {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.infobar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 步骤 + 配置双栏 */
.script-body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

/* 公共面板头 */
.panel-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  font-weight: 600;
  font-size: 13px;
  color: var(--el-text-color-primary);
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: var(--el-fill-color-light);
  flex-shrink: 0;
}

.panel-header-icon {
  color: var(--el-color-primary);
  font-size: 15px;
}

.step-count { margin-left: 4px; }

/* 左：步骤面板 */
.steps-panel {
  width: 42%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--el-border-color-lighter);
  overflow: hidden;
}

.steps-scroll {
  flex: 1;
  padding: 10px;
}

.steps-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 0;
}

/* 步骤行 */
.step-tree {
  background: transparent;

  :deep(.el-tree-node__content) {
    height: auto !important;
    padding: 0 !important;
    background: transparent !important;
    margin-bottom: 6px;
  }

  :deep(.el-tree-node__expand-icon) { display: none !important; }
  :deep(.el-tree-node__label) { display: none !important; }
  :deep(.el-tree-node > .el-tree-node__children) { padding-left: 0 !important; }
}

.step-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 8px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  width: 100%;
  box-sizing: border-box;

  &:hover {
    border-color: var(--el-color-primary-light-5);
    box-shadow: 0 1px 4px rgba(64,158,255,0.12);
  }

  &--disabled {
    opacity: 0.5;
  }
}

.step-row-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 13px;
  flex-shrink: 0;
}

.step-row-name {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-row-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* 右：配置面板 */
.config-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.config-scroll {
  flex: 1;
}

.config-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.config-form {
  padding: 16px 20px;
}

.config-divider {
  margin: 12px 0 !important;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.element-lib-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.element-linked-tag { flex-shrink: 0; }
</style>
