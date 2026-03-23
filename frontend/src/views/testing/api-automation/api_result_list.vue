<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { get_api_script_result_list } from '/@/api/v1/api_automation';

const table_data = ref<any>([]);
const searchParams = ref({
	currentPage: 1,
	pageSize: 10,
	search: {
		name: '',
	},
});
const customColors = ref<any>([
	{ color: '#ea2e2e', percentage: 99.99 },
	{ color: '#81d36f', percentage: 100 },
]);
const total = ref(0);

const get_script_result_list = async () => {
	const res: any = await get_api_script_result_list(searchParams.value as any);
	const raw = res?.data;
	const list = Array.isArray(raw?.content) ? raw.content : (Array.isArray(raw) ? raw : []);
	table_data.value = list;
	total.value = typeof raw?.total === 'number' ? raw.total : list.length;
};

const reset_search = () => {
	searchParams.value.currentPage = 1;
	searchParams.value.pageSize = 10;
	searchParams.value.search.name = '';
	get_script_result_list();
};

const view_report = async (result_id: any) => {
	// 新架构：使用站内路由页（后续会迁移完整 report UI）
	window.open(`/api-automation/report?result_id=${result_id}`, '_blank');
};

onMounted(() => {
	get_script_result_list();
});
</script>

<template>
	<div>
		<el-card class="box-card">
			<div class="result-topbar">
				<div class="result-topbar-left">
					<span class="result-title">接口自动化 - 执行结果</span>
				</div>
				<div class="result-topbar-right">
					<el-input 
						v-model="searchParams.search.name" 
						placeholder="请输入任务名称" 
						clearable 
						style="width: 300px; margin-right: 10px;"
						@keyup.enter="get_script_result_list"
					>
						<template #append>
							<el-button @click="get_script_result_list">搜索</el-button>
						</template>
					</el-input>
					<el-button type="danger" @click="reset_search">重置</el-button>
				</div>
			</div>
		</el-card>

		<el-card class="box-card mt-10px">
			<el-table :data="table_data" stripe>
				<el-table-column prop="id" label="ID" width="80" />
				<el-table-column prop="name" label="任务名称" />
				<el-table-column prop="result.pass" label="用例详情" width="120">
					<template #default="{ row }">
						<el-popover placement="top" :width="350" trigger="hover">
							<div>
								<el-steps direction="vertical" :active="99">
									<el-step v-for="step in row.script" :key="step.id">
										<template #title>
											<span>{{ step.name }}</span>
											<span style="float: right">{{ '(通过数：' + step.pass + ' 失败数：' + step.fail + ')' }}</span>
										</template>
									</el-step>
								</el-steps>
							</div>
							<template #reference>
								<el-button type="text">用例详情</el-button>
							</template>
						</el-popover>
					</template>
				</el-table-column>
				<el-table-column label="通过率" width="200">
					<template #default="{ row }">
						<el-progress :percentage="row.result.percent" :color="customColors" />
					</template>
				</el-table-column>
				<el-table-column prop="username" label="执行人" width="120" />
				<el-table-column label="开始时间" width="200">
					<template #default="{ row }">
						{{ row.start_time ? String(row.start_time).replace('T', ' ') : '-' }}
					</template>
				</el-table-column>
				<el-table-column label="结束时间" width="200">
					<template #default="{ row }">
						{{ row.end_time ? String(row.end_time).replace('T', ' ') : '-' }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="150">
					<template #default="{ row }">
						<el-button type="primary" size="small" @click="view_report(row.result_id)">查看测试报告</el-button>
					</template>
				</el-table-column>
			</el-table>
			
			<div class="pagination-wrapper">
				<el-pagination
					v-model:current-page="searchParams.currentPage"
					v-model:page-size="searchParams.pageSize"
					:page-sizes="[10, 25, 50, 100]"
					:background="true"
					layout="total, sizes, prev, pager, next, jumper"
					:total="total"
					@size-change="get_script_result_list"
					@current-change="get_script_result_list"
				/>
			</div>
		</el-card>
	</div>
</template>

<style scoped>
/* 通用样式 */
.box-card {
	margin-bottom: 10px;
}

.mt-10px {
	margin-top: 10px;
}

/* 结果页面样式 */
.result-topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.result-topbar-left {
	display: flex;
	align-items: center;
	gap: 10px;
}

.result-topbar-right {
	display: flex;
	align-items: center;
	gap: 10px;
}

.result-title {
	font-size: 16px;
	font-weight: bold;
	color: var(--el-text-color-primary);
}

.pagination-wrapper {
	margin-top: 20px;
	display: flex;
	justify-content: center;
}
</style>

