<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { app_result, app_result_detail, get_result_list } from "@/api/api_app/app.ts";
import { TabsPaneContext } from "element-plus";
import { MsgError, MsgSuccess } from "@/utils/koi";
import * as echarts from "echarts";
import { app_view_device } from "@/api/api_app/device";
import { ElLoading } from 'element-plus';

const route = useRoute();
const router = useRouter();

const table_list = ref<any>([]);
const loading = ref<any>(false);
const customColors = ref<any>([
  { color: "#ea2e2e", percentage: 99.99 },
  { color: "#81d36f", percentage: 100 }
]);
// 搜索区域展示
const showSearch = ref<boolean>(true);
// 查询参数
const searchParams = ref({
  currentPage: 1, // 第几页
  pageSize: 10, // 每页显示多少条
  search: {
    task_name__icontaints: ""
  }
});
//总数
const total = ref<number>(0);

const result_list = async () => {
  loading.value = true;
  const res: any = await get_result_list(searchParams.value);
  table_list.value = res.data.content;
  total.value = res.data.total;
  loading.value = false;
};

const reset_search = async () => {
  searchParams.value = {
    currentPage: 1,
    pageSize: 10,
    search: { task_name__icontaints: "" }
  };
  await result_list();
};

// 旧版实时页/图表相关变量（后续继续完整迁移）
const run_koiDialogRef = ref();
const run_device_list = ref<any>([]);
const device_active = ref<any>("");
const title = ref<any>("");
const run_pid = ref<any>(null);
const device = ref<any>("");
const result_id = ref<any>(null);
const per_time = ref<any>([]);
const cpu = ref<any>([]);
const memory = ref<any>([]);
const up_network = ref<any>([]);
const down_network = ref<any>([]);
const temperature = ref<any>([]);

const open_report = (row: any) => {
  window.open(`/app_report?result_id=${row.result_id}`, "_blank");
};

const view_result = async (data: any) => {
  // 迁移修复：本页不承担实时监控判断，直接跳转到 automation 页面，
  // 由 pid_status/实时轮询决定“正在执行/执行结束”以及是否能拉起实时流程。
  const basePath = route.path.replace(/\/results\/?$/, "/automation");
  router.push({ path: basePath, query: { result_id: data.result_id } });
};

onMounted(() => {
  result_list();
});
</script>

<template>
  <div style="padding: 10px">
    <KoiCard>
      <el-form v-show="showSearch" :inline="true">
        <el-form-item label="任务名称">
          <el-input placeholder="请输入任务名称" v-model="searchParams.search.task_name__icontaints" clearable style="width: 240px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="search" plain v-debounce="result_list">搜索</el-button>
          <el-button type="danger" icon="refresh" plain v-throttle="reset_search">重置</el-button>
        </el-form-item>
      </el-form>
      <div class="h-10px"></div>
      <el-table v-loading="loading" border :data="table_list" empty-text="暂时没有数据哟🌻">
        <el-table-column label="序号" prop="id" width="80px" align="center" type="index" />
        <el-table-column label="任务名称" prop="task_name" align="center" />
        <el-table-column label="执行人" prop="username" width="120px" align="center" />
        <el-table-column label="开始时间" prop="start_time" width="180px" align="center" />
        <el-table-column label="结束时间" prop="end_time" width="180px" align="center" />
        <el-table-column label="操作" align="center" width="160px" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="view_result(row)">查看</el-button>
            <el-button type="warning" size="small" @click="open_report(row)">报告</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="h-10px"></div>
      <el-pagination
        background
        v-model:current-page="searchParams.currentPage"
        v-model:page-size="searchParams.pageSize"
        v-show="total > 0"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="total"
        @size-change="result_list"
        @current-change="result_list"
      />
    </KoiCard>
  </div>
</template>

