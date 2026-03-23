<template>
  <div class="scheduler-page">
    <KoiCard>
      <!-- 搜索区域 -->
      <el-form :inline="true" :model="queryParams" class="scheduler-search">
        <el-form-item label="任务名称">
          <el-input
            v-model="queryParams.name"
            placeholder="请输入任务名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="任务类型">
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
        <el-form-item label="状态">
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
            搜索
          </el-button>
          <el-button @click="resetQuery">
            重置
          </el-button>
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="handleAdd" v-auth="'scheduler:task:add'">
            新增任务
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 任务表格 -->
      <el-table
        v-loading="loading"
        :data="taskList"
        border
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" align="center" />
        <el-table-column prop="name" label="任务名称" min-width="160" />
        <el-table-column label="任务类型" width="120" align="center">
          <template #default="scope">
            <el-tag v-if="scope.row.type === 1" type="success">APP自动化</el-tag>
            <el-tag v-else-if="scope.row.type === 2" type="warning">WEB自动化</el-tag>
            <el-tag v-else-if="scope.row.type === 3" type="info">API自动化</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              :active-value="1"
              :inactive-value="0"
              active-text="启用"
              inactive-text="停用"
              disabled
            />
          </template>
        </el-table-column>
        <el-table-column
          prop="next_run_at"
          label="下一次执行时间"
          min-width="180"
          align="center"
        >
          <template #default="scope">
            <el-tag v-if="scope.row.next_run_at" type="primary">
              {{ scope.row.next_run_at }}
            </el-tag>
            <el-tag v-else type="info">-</el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="total_run_count"
          label="执行次数"
          width="100"
          align="center"
        />
        <el-table-column
          prop="creation_date"
          label="创建时间"
          min-width="160"
          align="center"
        />
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              plain
              @click="handleEdit(scope.row)"
              v-auth="'scheduler:task:edit'"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              plain
              @click="handleDelete(scope.row)"
              v-auth="'scheduler:task:delete'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="scheduler-pagination">
        <el-pagination
          v-show="total > 0"
          background
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.size"
          :page-sizes="[10, 20, 50]"
          @size-change="getList"
          @current-change="getList"
        />
      </div>

      <!-- 新增/编辑任务对话框（表单骨架，后续继续细化字段） -->
      <KoiDialog
        ref="taskDialogRef"
        :title="dialogTitle"
        :height="520"
        width="50%"
        @koi-confirm="submitForm"
        @koi-cancel="cancelForm"
      >
        <template #content>
          <div>
            <el-form
              ref="taskFormRef"
              :model="form"
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

              <el-form-item v-if="form.type === 2" label="测试用例">
                <el-select
                  v-model="form.script.web_script_list"
                  multiple
                  filterable
                  placeholder="请选择测试用例"
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

              <el-form-item v-if="form.type === 3" label="测试用例">
                <el-select
                  v-model="form.script.api_script_list"
                  multiple
                  filterable
                  placeholder="请选择测试用例"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in apiScriptList"
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

              <el-form-item v-if="form.type === 3" label="参数配置">
                <el-select
                  v-model="form.script.params_id"
                  placeholder="请选择参数配置"
                  style="width: 80%"
                >
                  <el-option
                    v-for="item in paramsList"
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
                  value-format="yyyy-MM-dd HH:mm:ss"
                  placeholder="请选择执行时间"
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
          </div>
        </template>
      </KoiDialog>
    </KoiCard>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import KoiCard from '/@/components/koi/KoiCard.vue';
import KoiDialog from '/@/components/koi/KoiDialog.vue';
import type { FormInstance } from 'element-plus';
import { taskSchedulerApi, type SchedulerTask } from '/@/api/v1/task_scheduler';
import { device_list } from '/@/api/v1/cloud_device';
import { get_api_script_list, api_env, params_select } from '/@/api/v1/api_automation';

const loading = ref(false);
const taskList = ref<SchedulerTask[]>([]);
const total = ref(0);

const queryParams = reactive({
  page: 1,
  size: 10,
  name: '',
  type: undefined as number | undefined,
  status: undefined as number | undefined,
});

const taskDialogRef = ref<InstanceType<typeof KoiDialog> | null>(null);
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
    web_script_list: number[];
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
    web_script_list: [],
    api_script_list: [],
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

// 下拉选项数据
const deviceList = ref<any[]>([]);
const appScriptList = ref<any[]>([]);
const webScriptList = ref<any[]>([]);
const apiScriptList = ref<any[]>([]);
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
    const res = await taskSchedulerApi.getNoticeList({
      page: 1,
      size: 100,
      status: 1,
    });
    const data = res.data as any;
    noticeList.value = data.items || data.records || data.list || data.content || [];
  } catch {
    noticeList.value = [];
  }
};

// 目前新架构未直接暴露 app/web 脚本列表接口，这里先占位，后续按需要补充
const loadAppScripts = async () => {
  appScriptList.value = [];
};

const loadWebScripts = async () => {
  webScriptList.value = [];
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
    taskList.value = data.items || data.records || data.list || [];
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
    web_script_list: [],
    api_script_list: [],
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

const handleAdd = () => {
  resetForm();
  dialogTitle.value = '新增定时任务';
  Promise.all([
    loadDevices(),
    loadAppScripts(),
    loadWebScripts(),
    loadApiScripts(),
    loadApiEnv(),
    loadApiParams(),
    loadNotices(),
  ]);
  taskDialogRef.value?.koiOpen();
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
  form.time = (row.time as any) || {};
  form.notice = (row.notice as any) || { status: 0, notice_id: null };
  Promise.all([
    loadDevices(),
    loadAppScripts(),
    loadWebScripts(),
    loadApiScripts(),
    loadApiEnv(),
    loadApiParams(),
    loadNotices(),
  ]);
  taskDialogRef.value?.koiOpen();
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
  try {
    if (!form.name) {
      ElMessage.error('请填写任务名称');
      return;
    }
    if (!form.type) {
      ElMessage.error('请选择任务类型');
      return;
    }

    // 兼容旧后端：设备需要转换为 device_list 结构
    const payload: any = {
      name: form.name,
      type: form.type,
      status: form.status,
      description: form.description,
      script: form.script,
      time: form.time,
      notice: form.notice,
    };

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

    taskDialogRef.value?.koiQuickClose('操作成功');
    getList();
  } catch (error) {
    console.error(error);
    ElMessage.error('保存失败');
  }
};

const cancelForm = () => {
  taskDialogRef.value?.koiQuickClose('已取消');
};

onMounted(() => {
  getList();
});
</script>

<style scoped>
.scheduler-page {
  padding: 16px;
}

.scheduler-search {
  margin-bottom: 16px;
}

.scheduler-pagination {
  margin-top: 16px;
  text-align: right;
}
</style>

