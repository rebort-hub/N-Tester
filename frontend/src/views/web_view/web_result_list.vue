<template>
  <div class="result-list-container">
    <!-- 搜索栏 -->
    <el-card shadow="hover" :body-style="{ paddingBottom: '0' }">
      <el-form :inline="true" :model="searchParams.search">
        <el-form-item label="任务名称">
          <el-input
            v-model="searchParams.search.task_name__icontains"
            placeholder="请输入任务名称"
            clearable
            style="width: 220px"
            @keyup.enter="result_list"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="result_list">搜索</el-button>
          <el-button icon="Refresh" @click="reset_search">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格 -->
    <el-card shadow="hover" style="margin-top: 8px">
      <el-table v-loading="loading" :data="table_list" border stripe empty-text="暂无数据">
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column label="任务名称" prop="task_name" min-width="120" show-overflow-tooltip />

        <el-table-column label="测试用例" width="100" align="center">
          <template #default="{ row }">
            <el-popover placement="top" :width="280" trigger="hover">
              <el-steps direction="vertical" :active="99" style="max-height: 300px; overflow-y: auto">
                <el-step v-for="step in row.script_list" :key="step.id" :title="step.name" />
              </el-steps>
              <template #reference>
                <el-button type="primary" size="small" plain>用例详情</el-button>
              </template>
            </el-popover>
          </template>
        </el-table-column>

        <el-table-column label="执行浏览器" width="110" align="center">
          <template #default="{ row }">
            <el-popover placement="top" trigger="hover" :width="180">
              <div v-for="(browser, index) in row.browser_list" :key="index" style="padding-bottom: 4px">
                <el-tag v-if="browser === 1" size="small" type="danger">Chrome</el-tag>
                <el-tag v-else-if="browser === 2" size="small" type="warning">Firefox</el-tag>
                <el-tag v-else-if="browser === 3" size="small" type="primary">Edge</el-tag>
                <el-tag v-else-if="browser === 4" size="small" type="success">Safari</el-tag>
              </div>
              <template #reference>
                <el-button type="info" size="small" plain>浏览器</el-button>
              </template>
            </el-popover>
          </template>
        </el-table-column>

        <el-table-column label="任务状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 1" type="success">执行完成</el-tag>
            <el-tag v-else type="warning">执行中</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="通过率" width="160" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.percent ?? 0" :color="customColors" :stroke-width="10" />
          </template>
        </el-table-column>

        <el-table-column label="执行人" prop="username" width="90" align="center" show-overflow-tooltip />

        <el-table-column label="开始时间" width="160" align="center">
          <template #default="{ row }">{{ formatTime(row.start_time) }}</template>
        </el-table-column>

        <el-table-column label="结束时间" width="160" align="center">
          <template #default="{ row }">{{ formatTime(row.end_time) }}</template>
        </el-table-column>

        <el-table-column label="操作" width="130" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 1"
              type="primary"
              size="small"
              icon="Document"
              @click="view_report(row.result_id)"
            >查看报告</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 12px">
        <el-pagination
          v-show="total > 0"
          background
          v-model:current-page="searchParams.currentPage"
          v-model:page-size="searchParams.pageSize"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="result_list"
          @current-change="result_list"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { get_web_result_list } from '/@/api/v1/web_management'

const table_list = ref<any[]>([])
const loading = ref(false)

const customColors = [
  { color: '#ea2e2e', percentage: 99.99 },
  { color: '#67c23a', percentage: 100 },
]

const searchParams = ref({
  currentPage: 1,
  pageSize: 10,
  search: { task_name__icontains: '' },
})

const total = ref(0)

// 格式化时间：2026-03-15T13:20:05 → 2026-03-15 13:20:05
const formatTime = (t: string) => t ? t.replace('T', ' ') : '-'

const result_list = async () => {
  loading.value = true
  try {
    const res: any = await get_web_result_list({
      page: searchParams.value.currentPage,
      pageSize: searchParams.value.pageSize,
      search: searchParams.value.search,
    })
    table_list.value = res.data.content
    total.value = res.data.totalElements ?? res.data.total ?? 0
  } finally {
    loading.value = false
  }
}

const reset_search = async () => {
  searchParams.value = { currentPage: 1, pageSize: 10, search: { task_name__icontains: '' } }
  await result_list()
}

const view_report = (result_id: string) => {
  window.open(`${window.location.origin}/web/report?result_id=${encodeURIComponent(result_id)}`)
}

onMounted(() => { result_list() })
</script>

<style scoped lang="scss">
.result-list-container {
  padding: 10px;
}
</style>
