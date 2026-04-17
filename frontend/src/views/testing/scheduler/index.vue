<template>
  <div class="scheduler-page">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>任务调度管理</span>
          <el-button 
            type="primary" 
            @click="handleAdd"
            v-auth="'scheduler:task:add'"
          >
            <el-icon><Plus /></el-icon>
            新增任务
          </el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="queryParams" ref="queryRef" :inline="true" class="search-form">
        <el-form-item label="任务名称" prop="name">
          <el-input
            v-model="queryParams.name"
            placeholder="请输入任务名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item label="任务类型" prop="type">
          <el-select
            v-model="queryParams.type"
            placeholder="请选择任务类型"
            clearable
            style="width: 160px"
          >
            <el-option :value="1" label="APP自动化" />
            <el-option :value="2" label="WEB自动化" />
            <el-option :value="3" label="API自动化" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select
            v-model="queryParams.status"
            placeholder="请选择状态"
            clearable
            style="width: 140px"
          >
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetQuery">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="taskList"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="任务名称" min-width="160" />
        <el-table-column label="任务类型" width="120" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.type === 1" type="success" size="small">APP自动化</el-tag>
            <el-tag v-else-if="scope.row.type === 2" type="warning" size="small">WEB自动化</el-tag>
            <el-tag v-else-if="scope.row.type === 3" type="info" size="small">API自动化</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="1"
              :inactive-value="0"
              @change="handleStatusChange(scope.row)"
              v-auth="'scheduler:task:edit'"
            />
          </template>
        </el-table-column>
        <el-table-column label="执行类型" width="120" align="center">
          <template #default="scope">
            <el-tag size="small" type="info">
              {{ getTimeTypeLabel(scope.row.time?.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行状态" width="120" align="center">
          <template #default="scope">
            <el-tag :type="getExecuteStatusType(scope.row.latest_status)" size="small">
              {{ getExecuteStatusLabel(scope.row.latest_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="next_run_at"
          label="下一次执行时间"
          min-width="180"
          align="center"
        >
          <template #default="scope">
            <el-tag v-if="scope.row.next_time || scope.row.next_run_at" type="primary" size="small">
              {{ scope.row.next_time || scope.row.next_run_at }}
            </el-tag>
            <el-tag v-else type="info" size="small">-</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="total_run_count"
          label="执行次数"
          width="100"
          align="center"
        />
        <el-table-column
          prop="latest_run_time"
          label="最近执行时间"
          min-width="170"
          align="center"
        >
          <template #default="scope">
            <span>{{ scope.row.latest_run_time || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          prop="creation_date"
          label="创建时间"
          min-width="160"
          align="center"
        >
          <template #default="scope">
            <span>{{ formatDateTime(scope.row.creation_date) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="140" class-name="small-padding fixed-width">
          <template #default="scope">
            <div class="button-group">
              <el-button
                type="primary"
                size="small"
                @click="handleEdit(scope.row)"
                v-auth="'scheduler:task:edit'"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleDelete(scope.row)"
                v-auth="'scheduler:task:delete'"
              >
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-show="total > 0"
        :total="total"
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.size"
        @size-change="getList"
        @current-change="getList"
        layout="total, sizes, prev, pager, next, jumper"
        :page-sizes="[10, 20, 50, 100]"
      />
    </el-card>

      <!-- 新增/编辑任务对话框 -->
      <el-dialog
        :title="dialogTitle"
        v-model="dialogVisible"
        width="50%"
        append-to-body
        destroy-on-close
        class="scheduler-task-dialog"
      >
        <el-form
          ref="taskFormRef"
          :model="form"
          :rules="rules"
          label-width="100px"
          class="scheduler-form"
        >
              <el-form-item label="任务名称">
                <el-input
                  v-model="form.name"
                  placeholder="请输入任务名称"
                  style="width: 80%"
                />
              </el-form-item>
              <el-form-item label="任务类型">
                <el-radio-group v-model="form.type">
                  <el-radio :label="1">APP自动化</el-radio>
                  <el-radio :label="2">WEB自动化</el-radio>
                  <el-radio :label="3">API自动化</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="任务状态">
                <el-switch
                  v-model="form.status"
                  :active-value="1"
                  :inactive-value="0"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>
              <el-form-item label="任务描述">
                <el-input
                  v-model="form.description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入任务描述"
                  style="width: 80%"
                />
              </el-form-item>

              <!-- 脚本配置：根据任务类型切换不同的字段（设备/浏览器/用例等） -->
              <el-divider content-position="left">脚本配置</el-divider>
              <el-form-item v-if="form.type === 1" label="设备列表">
                <el-select
                  v-model="form.script.device"
                  multiple
                  filterable
                  placeholder="请选择设备"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in deviceList"
                    :key="item.deviceid"
                    :label="item.name"
                    :value="item.deviceid"
                  />
                </el-select>
              </el-form-item>

              <el-form-item v-if="form.type === 2" label="浏览器列表">
                <el-select
                  v-model="form.script.browser"
                  multiple
                  placeholder="请选择浏览器"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in browserList"
                    :key="item.value"
                    :label="item.name"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item v-if="form.type === 2" label="分辨率(高×宽)">
                <div>
                  <el-input-number
                    v-model="form.script.height"
                    controls-position="right"
                    :min="800"
                    label="高度"
                  />
                  <el-input-number
                    v-model="form.script.width"
                    style="margin-left: 10px"
                    controls-position="right"
                    :min="800"
                    label="宽度"
                  />
                </div>
              </el-form-item>

              <el-form-item v-if="form.type === 1" label="测试用例">
                <el-select
                  v-model="form.script.app_script_list"
                  multiple
                  filterable
                  placeholder="请选择测试用例"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in appScriptList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item v-if="form.type === 2" label="测试场景">
                <el-select
                  v-model="form.script.web_group_list"
                  multiple
                  filterable
                  placeholder="请选择测试场景"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in webScriptList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item v-if="form.type === 3" label="选择服务">
                <el-select
                  v-model="form.script.api_service_id"
                  placeholder="请选择服务"
                  style="width: 80%"
                  clearable
                  filterable
                  @change="onSchedulerServiceChange"
                >
                  <el-option
                    v-for="item in apiServiceList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item v-if="form.type === 3" label="用例集">
                <el-select
                  v-model="form.script.api_suite_list"
                  multiple
                  filterable
                  placeholder="请选择用例集（可多选）"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in schedulerSuiteOptions"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>

              <el-form-item v-if="form.type === 3" label="执行环境">
                <el-select
                  v-model="form.script.env_id"
                  placeholder="请选择环境"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in envList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>

              <!-- 时间配置 -->
              <el-divider content-position="left">时间配置</el-divider>
              <el-form-item label="执行类型">
                <el-radio-group v-model="form.time.type">
                  <el-radio :label="1">执行一次</el-radio>
                  <el-radio :label="2">间隔执行</el-radio>
                  <el-radio :label="3">每天执行</el-radio>
                  <el-radio :label="4">每周执行</el-radio>
                </el-radio-group>
              </el-form-item>

              <el-form-item v-if="form.time.type === 1" label="执行时间">
                <el-date-picker
                  v-model="form.time.run_time"
                  type="datetime"
                  format="YYYY-MM-DD HH:mm:ss"
                  value-format="YYYY-MM-DD HH:mm:ss"
                  placeholder="请选择执行时间"
                  style="width: 100%"
                  teleported
                  popper-class="scheduler-datetime-popper"
                />
              </el-form-item>

              <el-form-item v-if="form.time.type === 2" label="间隔(分钟)">
                <el-input-number
                  v-model="form.time.interval"
                  :min="1"
                  :max="3600"
                />
              </el-form-item>

              <el-form-item v-if="form.time.type === 3" label="执行时间">
                <el-time-select
                  v-model="form.time.week_run_time"
                  style="width: 240px"
                  start="00:00"
                  step="00:15"
                  end="23:45"
                  placeholder="请选择执行时间"
                />
              </el-form-item>

              <el-form-item v-if="form.time.type === 4" label="执行时间">
                <el-select
                  v-model="form.time.week_date"
                  multiple
                  collapse-tags
                  style="width: 30%; margin-right: 10px"
                  placeholder="请选择星期"
                >
                  <el-option
                    v-for="item in weekList"
                    :key="item.value"
                    :label="item.name"
                    :value="item.value"
                  />
                </el-select>
                <el-time-select
                  v-model="form.time.week_run_time"
                  style="width: 240px"
                  start="00:00"
                  step="00:15"
                  end="23:45"
                  placeholder="请选择执行时间"
                />
              </el-form-item>

              <!-- 结果通知 -->
              <el-divider content-position="left">结果通知</el-divider>
              <el-form-item label="是否通知">
                <el-switch
                  v-model="form.notice.status"
                  :active-value="1"
                  :inactive-value="0"
                  active-text="开启"
                  inactive-text="关闭"
                />
              </el-form-item>
              <el-form-item v-if="form.notice.status === 1" label="通知配置">
                <el-select
                  v-model="form.notice.notice_id"
                  placeholder="请选择通知配置"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in noticeList"
                    :key="item.id"
                    :label="item.name"
                    :value="item.id"
                  />
                </el-select>
              </el-form-item>
            </el-form>
        <template #footer>
          <div class="dialog-footer">
            <el-button type="primary" @click="submitForm">确 定</el-button>
            <el-button @click="cancelForm">取 消</el-button>
          </div>
        </template>
      </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Search, Refresh, Edit, Delete } from '@element-plus/icons-vue';
import type { FormInstance } from 'element-plus';
import { useTaskSchedulerApi, type SchedulerTask } from '/@/api/v1/task_scheduler';
import { useNotificationConfigApi } from '/@/api/v1/notifications';
import { useCloudDeviceApi } from '/@/api/v1/cloud_device';
import { useApiAutomationApi } from '/@/api/v1/api_automation';
import { useWebManagementApi } from '/@/api/v1/web_management';

const taskSchedulerApi = useTaskSchedulerApi();
const notificationConfigApi = useNotificationConfigApi();
const { device_list } = useCloudDeviceApi();
const { get_api_script_list, api_env, params_select, api_service, api_suite_list } = useApiAutomationApi();
const { web_group_select } = useWebManagementApi();
import { formatDateTime } from '/@/utils/formatTime';

const loading = ref(false);
const taskList = ref<SchedulerTask[]>([]);
const total = ref(0);
const dialogVisible = ref(false);
const ids = ref<number[]>([]);
const single = ref(true);
const multiple = ref(true);

const queryParams = reactive({
  page: 1,
  size: 10,
  name: '',
  type: undefined as number | undefined,
  status: undefined as number | undefined,
});

const taskFormRef = ref<FormInstance>();
const dialogTitle = ref('新增定时任务');

const form = reactive<{
  id?: number;
  name: string;
  type: number;
  status: number;
  description?: string;
  script: {
    width: number;
    height: number;
    device: any[];
    app_script_list: number[];
    web_group_list: number[];
    api_script_list: number[];
    browser: number[];
    env_id: number | null;
    params_id: number | null;
    [key: string]: any;
  };
  time: {
    type: number;
    run_time: string;
    interval: number;
    week_date: string[];
    week_run_time: string;
    [key: string]: any;
  };
  notice: { status: number; notice_id?: number | null };
}>({
  name: '',
  type: 1,
  status: 1,
  description: '',
  script: {
    width: 1920,
    height: 1080,
    device: [],
    app_script_list: [],
    web_group_list: [],
    api_script_list: [],
    api_suite_list: [],
    api_service_id: null,
    browser: [],
    env_id: null,
    params_id: null,
  },
  time: {
    type: 1,
    run_time: '',
    interval: 1,
    week_date: [],
    week_run_time: '',
  },
  notice: {
    status: 0,
    notice_id: null,
  },
});

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '任务名称不能为空', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '任务类型不能为空', trigger: 'change' }
  ]
};

// 下拉选项数据
const deviceList = ref<any[]>([]);
const appScriptList = ref<any[]>([]);
const webScriptList = ref<any[]>([]);
const apiScriptList = ref<any[]>([]);
const apiServiceList = ref<any[]>([]);
const schedulerSuiteOptions = ref<any[]>([]);
const envList = ref<any[]>([]);
const paramsList = ref<any[]>([]);
const noticeList = ref<any[]>([]);
const weekList = ref<any[]>([
  { name: '周一', value: 'mon' },
  { name: '周二', value: 'tue' },
  { name: '周三', value: 'wed' },
  { name: '周四', value: 'thu' },
  { name: '周五', value: 'fri' },
  { name: '周六', value: 'sat' },
  { name: '周日', value: 'sun' },
]);
const browserList = ref<any[]>([
  { name: 'Chrome', value: 1 },
  { name: 'Firefox', value: 2 },
  { name: 'Edge', value: 3 },
  { name: 'Safari', value: 4 },
]);

const loadDevices = async () => {
  try {
    const res = await device_list({});
    deviceList.value = (res.data && (res.data.items || res.data)) || [];
  } catch {
    deviceList.value = [];
  }
};

const loadApiScripts = async () => {
  try {
    const res = await get_api_script_list({});
    apiScriptList.value = res.data || [];
  } catch {
    apiScriptList.value = [];
  }
};

const loadApiServices = async () => {
  try {
    const res: any = await api_service({ page: 1, pageSize: 200, search: {} });
    const raw = res?.data;
    apiServiceList.value = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
  } catch { apiServiceList.value = []; }
};

const onSchedulerServiceChange = async (serviceId: number | null) => {
  schedulerSuiteOptions.value = [];
  form.script.api_suite_list = [];
  if (!serviceId) return;
  try {
    const r: any = await api_suite_list({ api_service_id: serviceId });
    const flatten = (nodes: any[]): any[] => {
      const result: any[] = [];
      for (const n of nodes) { result.push(n); if (n.children?.length) result.push(...flatten(n.children)); }
      return result;
    };
    schedulerSuiteOptions.value = flatten(Array.isArray(r?.data) ? r.data : []);
  } catch { schedulerSuiteOptions.value = []; }
};

const loadApiEnv = async () => {
  try {
    const res = await api_env({});
    envList.value = res.data || [];
  } catch {
    envList.value = [];
  }
};

const loadApiParams = async () => {
  try {
    const res = await params_select({});
    paramsList.value = res.data || [];
  } catch {
    paramsList.value = [];
  }
};

const loadNotices = async () => {
  try {
    const res = await notificationConfigApi.getConfigs({
      is_active: true,
      skip: 0,
      limit: 200,
    });
    const data = res.data as any;
    noticeList.value =
      data.content || data.items || data.records || data.list || [];
  } catch {
    noticeList.value = [];
  }
};

const getTimeTypeLabel = (timeType?: number) => {
  if (timeType === 1) return '执行一次';
  if (timeType === 2) return '间隔执行';
  if (timeType === 3) return '每天执行';
  if (timeType === 4) return '每周执行';
  return '-';
};

const getExecuteStatusLabel = (status?: string) => {
  if (status === 'running') return '执行中';
  if (status === 'success') return '执行成功';
  if (status === 'failed') return '执行失败';
  if (status === 'timeout') return '执行超时';
  return '未执行';
};

const getExecuteStatusType = (status?: string) => {
  if (status === 'running') return 'warning';
  if (status === 'success') return 'success';
  if (status === 'failed') return 'danger';
  if (status === 'timeout') return 'info';
  return 'info';
};

// APP 脚本列表后续按业务接口补齐
const loadAppScripts = async () => {
  appScriptList.value = [];
};

const loadWebScripts = async () => {
  try {
    const res = await web_group_select({});
    const data = res.data as any[];
    webScriptList.value = Array.isArray(data) ? data : [];
  } catch {
    webScriptList.value = [];
  }
};

const getList = async () => {
  loading.value = true;
  try {
    const res = await taskSchedulerApi.getTaskList({
      page: queryParams.page,
      size: queryParams.size,
      name: queryParams.name || undefined,
      type: queryParams.type,
      status: queryParams.status,
    });
    const data = res.data as any;
    taskList.value = data.content || data.items || data.records || data.list || [];
    total.value = data.total || 0;
  } catch (error) {
    console.error(error);
    ElMessage.error('获取定时任务列表失败');
  } finally {
    loading.value = false;
  }
};

const handleQuery = () => {
  queryParams.page = 1;
  getList();
};

const resetQuery = () => {
  queryParams.page = 1;
  queryParams.size = 10;
  queryParams.name = '';
  queryParams.type = undefined;
  queryParams.status = undefined;
  getList();
};

const resetForm = () => {
  form.id = undefined;
  form.name = '';
  form.type = 1;
  form.status = 1;
  form.description = '';
  form.script = {
    width: 1920,
    height: 1080,
    device: [],
    app_script_list: [],
    web_group_list: [],
    api_script_list: [],
    api_suite_list: [],
    api_service_id: null,
    browser: [],
    env_id: null,
    params_id: null,
  };
  form.time = {
    type: 1,
    run_time: '',
    interval: 1,
    week_date: [],
    week_run_time: '',
  };
  form.notice = {
    status: 0,
    notice_id: null,
  };
  if (taskFormRef.value) {
    taskFormRef.value.clearValidate();
  }
};

// 多选框选中数据
const handleSelectionChange = (selection: SchedulerTask[]) => {
  ids.value = selection.map(item => item.id);
  single.value = selection.length !== 1;
  multiple.value = !selection.length;
};

// 状态修改
const handleStatusChange = async (row: SchedulerTask) => {
  const text = row.status ? '启用' : '停用';
  try {
    await ElMessageBox.confirm(`确认要${text}该任务吗？`);
    await taskSchedulerApi.updateTask({
      task_id: row.id,
      status: row.status,
    });
    ElMessage.success(`${text}成功`);
  } catch (error: any) {
    row.status = row.status ? 0 : 1;
    console.error(`${text}任务失败:`, error);
    if (error?.message) {
      ElMessage.error(error.message);
    } else {
      ElMessage.error(`${text}失败`);
    }
  }
};

const handleAdd = () => {
  resetForm();
  dialogTitle.value = '新增定时任务';
  Promise.all([
    loadDevices(),
    loadAppScripts(),
    loadWebScripts(),
    loadApiServices(),
    loadApiEnv(),
    loadNotices(),
  ]);
  dialogVisible.value = true;
};

const handleEdit = (row: SchedulerTask) => {
  resetForm();
  dialogTitle.value = '编辑定时任务';
  form.id = row.id;
  form.name = row.name;
  form.type = row.type;
  form.status = row.status;
  form.description = row.description || '';
  form.script = (row.script as any) || {};
  // 兼容历史数据：旧字段 web_script_list 迁移为 web_group_list（场景）
  if (
    form.type === 2 &&
    !Array.isArray(form.script.web_group_list) &&
    Array.isArray((form.script as any).web_script_list)
  ) {
    form.script.web_group_list = (form.script as any).web_script_list;
  }
  form.time = (row.time as any) || {};
  form.notice = (row.notice as any) || { status: 0, notice_id: null };
  Promise.all([
    loadDevices(),
    loadAppScripts(),
    loadWebScripts(),
    loadApiServices(),
    loadApiEnv(),
    loadNotices(),
  ]);
  // 编辑时如果有 api_service_id，加载对应用例集
  if (form.type === 3 && form.script.api_service_id) {
    onSchedulerServiceChange(form.script.api_service_id);
  }
  dialogVisible.value = true;
};

const handleDelete = async (row: SchedulerTask) => {
  try {
    await ElMessageBox.confirm(`确认删除任务「${row.name}」吗？`, '提示', {
      type: 'warning',
    });
    await taskSchedulerApi.deleteTask(row.id);
    ElMessage.success('删除成功');
    getList();
  } catch {
    // 用户取消或请求失败时不再抛出
  }
};

const submitForm = async () => {
  if (!taskFormRef.value) return;
  
  try {
    // 先进行表单验证
    await taskFormRef.value.validate();
    
    if (!form.name) {
      ElMessage.error('请填写任务名称');
      return;
    }
    if (!form.type) {
      ElMessage.error('请选择任务类型');
      return;
    }
    if (form.time.type === 1 && !String(form.time.run_time || '').trim()) {
      ElMessage.error('请选择执行时间');
      return;
    }

    const payload: any = {
      name: form.name,
      type: form.type,
      status: form.status,
      description: form.description,
      script: form.script,
      time: form.time,
      notice: form.notice,
    };
    // WEB 场景模式：仅选择场景；为兼容旧后端字段，同时回填 web_script_list
    if (form.type === 2 && Array.isArray(form.script.web_group_list)) {
      payload.script.web_script_list = [...form.script.web_group_list];
    }

    if (Array.isArray(form.script.device) && deviceList.value.length) {
      const deviceDetail = form.script.device
        .map((id) => deviceList.value.find((d) => d.deviceid === id))
        .filter((d) => d);
      payload.script.device_list = deviceDetail;
    }

    if (form.id) {
      await taskSchedulerApi.updateTask({
        task_id: form.id,
        ...payload,
      });
      ElMessage.success('编辑成功');
    } else {
      await taskSchedulerApi.createTask(payload);
      ElMessage.success('新增成功');
    }

    dialogVisible.value = false;
    getList();
  } catch (error) {
    console.error(error);
    ElMessage.error('保存失败');
  }
};

const cancelForm = () => {
  dialogVisible.value = false;
  resetForm();
};

onMounted(() => {
  getList();
});
</script>

<style scoped>
.scheduler-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 16px;
}

.dialog-footer {
  text-align: right;
}

.button-group {
  display: flex;
  gap: 4px;
  justify-content: center;
  align-items: center;
  white-space: nowrap;
}

.button-group .el-button {
  margin: 0;
}

/* 修复表单验证样式 */
:deep(.el-form-item.is-required .el-form-item__label:before) {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
  position: static;
  display: inline;
  font-weight: normal;
}

:deep(.el-form-item__label) {
  position: relative;
  display: inline-block;
}

:deep(.el-form-item__error) {
  position: absolute;
  top: 100%;
  left: 0;
  font-size: 12px;
  color: #f56c6c;
  line-height: 1;
  padding-top: 4px;
  z-index: 1;
}

/* 确保表单项有足够的底部间距来显示错误信息 */
:deep(.el-form-item) {
  margin-bottom: 22px;
}

/* 弹窗内日期选择器：避免被遮挡、保证可点选 */
.scheduler-task-dialog :deep(.el-dialog__body) {
  overflow: visible;
}
</style>

<style>
.scheduler-datetime-popper {
  z-index: 4000 !important;
}
</style>

