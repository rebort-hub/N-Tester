<template>
	<div class="app-test-module">
		<!--
			单页聚合：一个菜单入口（testing/app-management/index）内用 Tab 切换子模块， 六块能力一一对应。
			刻意不拆成多条后端子菜单路由，保持「一个大页面」的交互；?tab= 用于深链与报告跳用例。
		-->
		<div class="app-test-module__header">
			<div class="header-left">
				<div class="page-icon app">
					<el-icon><Cellphone /></el-icon>
				</div>
				<div class="page-info">
					<h3 class="page-title">APP自动化</h3>
					<span class="page-subtitle">{{ menuSubtitle }}</span>
				</div>
				<el-tag type="primary" size="small" class="mode-tag">APP UI</el-tag>
			</div>
		</div>

		<el-tabs v-model="mainMenu" class="app-test-module__tabs" @tab-change="onTabChange">
			<el-tab-pane name="device">
				<template #label>
					<span class="tab-label"><el-icon><Monitor /></el-icon>设备管理</span>
				</template>
			</el-tab-pane>
			<el-tab-pane name="project">
				<template #label>
					<span class="tab-label"><el-icon><Box /></el-icon>APP管理</span>
				</template>
			</el-tab-pane>
			<el-tab-pane name="page">
				<template #label>
					<span class="tab-label"><el-icon><Reading /></el-icon>页面管理</span>
				</template>
			</el-tab-pane>
			<el-tab-pane name="case">
				<template #label>
					<span class="tab-label"><el-icon><Files /></el-icon>用例管理</span>
				</template>
			</el-tab-pane>
			<el-tab-pane name="task">
				<template #label>
					<span class="tab-label"><el-icon><Calendar /></el-icon>任务管理</span>
				</template>
			</el-tab-pane>
			<el-tab-pane name="report">
				<template #label>
					<span class="tab-label"><el-icon><Histogram /></el-icon>测试报告</span>
				</template>
			</el-tab-pane>
		</el-tabs>

		<div class="app-test-module__body">
			<DevicePage  v-if="mainMenu === 'device'"  :key="'device'"  />
			<ProjectPage v-else-if="mainMenu === 'project'" :key="'project'" />
			<PageManage  v-else-if="mainMenu === 'page'"    :key="'page'"    />
			<CaseSuite   v-else-if="mainMenu === 'case'"    :key="'case'"    />
			<TaskPage    v-else-if="mainMenu === 'task'"    :key="'task'"    />
			<ReportPage  v-else-if="mainMenu === 'report'"  :key="'report'"  />
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
	Monitor,
	Box,
	Reading,
	Files,
	Calendar,
	Histogram,
	Cellphone,
} from '@element-plus/icons-vue';
import DevicePage from './device/index.vue';
import ProjectPage from './project/index.vue';
import PageManage from './page/index.vue';
import CaseSuite from './case/index.vue';
import TaskPage from './task/index.vue';
import ReportPage from './report/index.vue';

type AppTestMenuKey = 'device' | 'project' | 'page' | 'case' | 'task' | 'report';

const MENU_KEYS: AppTestMenuKey[] = ['device', 'project', 'page', 'case', 'task', 'report'];

const route = useRoute();
const router = useRouter();
const mainMenu = ref<AppTestMenuKey>('device');

const menuSubtitle = computed(() => {
	const m: Record<AppTestMenuKey, string> = {
		device: 'Appium 执行服务器 / 运行终端',
		project: '图像素材库',
		page: '页面与元素',
		case: '脚本树与步骤编排',
		task: '调度任务',
		report: '执行记录与报告',
	};
	return m[mainMenu.value];
});

function isMenuKey(v: unknown): v is AppTestMenuKey {
	return typeof v === 'string' && (MENU_KEYS as string[]).includes(v);
}

function applyTabFromRoute() {
	const t = route.query.tab;
	if (isMenuKey(t)) {
		mainMenu.value = t;
		return;
	}
	mainMenu.value = 'device';
}

watch(
	() => route.query.tab,
	() => {
		applyTabFromRoute();
	},
	{ immediate: true },
);

onMounted(() => {
	if (!isMenuKey(route.query.tab)) {
		router.replace({ query: { ...route.query, tab: mainMenu.value } });
	}
});

function onTabChange(name: string | number) {
	const key = String(name);
	if (!isMenuKey(key)) return;
	router.replace({ query: { ...route.query, tab: key } });
}
</script>

<style scoped lang="scss">
.app-test-module {
	padding: 0 12px 16px;
	min-height: calc(100vh - 120px);
	box-sizing: border-box;
	background: var(--el-bg-color-page);
}

.app-test-module__header {
	padding: 14px 8px 10px;
	border-bottom: 1px solid var(--el-border-color-lighter);
	margin-bottom: 0;
	background: var(--el-bg-color);

	.header-left {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.page-icon {
		width: 40px;
		height: 40px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #fff;
		font-size: 20px;

		&.app {
			background: linear-gradient(135deg, #409eff, #67c23a);
		}
	}

	.page-info {
		flex: 1;

		.page-title {
			margin: 0 0 4px;
			font-size: 18px;
			font-weight: 600;
			color: var(--el-text-color-primary);
		}

		.page-subtitle {
			font-size: 13px;
			color: var(--el-text-color-secondary);
		}
	}

	.mode-tag {
		flex-shrink: 0;
	}
}

.app-test-module__tabs {
	margin-bottom: 0;

	:deep(.el-tabs__header) {
		margin: 0 0 8px;
		background: var(--el-fill-color-light);
		border-radius: 4px;
		padding: 0 8px;
	}

	:deep(.el-tabs__content) {
		display: none;
	}
}

.tab-label {
	display: inline-flex;
	align-items: center;
	gap: 6px;
}

.app-test-module__body {
	padding: 8px 0 0;
	min-height: 480px;
}
</style>
