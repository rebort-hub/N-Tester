<template>
	<div class="app-test-module">
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

		<!--
			不用 el-tabs：空 pane + 隐藏 content 时在 EP 2.7 + Vue 3.5 下点击会走 removeFocus，
			与 v-if 切换子页叠加易触发 unmountComponent / subTree 空引用。
		-->
		<nav class="app-test-module__nav" role="tablist" aria-label="APP 自动化模块">
			<button
				v-for="item in MAIN_MENU"
				:key="item.name"
				type="button"
				class="app-test-nav-item"
				role="tab"
				:aria-selected="mainMenu === item.name"
				:class="{ 'is-active': mainMenu === item.name }"
				@click="onSelectMainMenu(item.name)"
			>
				<span class="tab-label">
					<el-icon><component :is="item.icon" /></el-icon>
					{{ item.label }}
				</span>
			</button>
		</nav>

		<!--
			单一动态组件 + key：避免长 v-if/v-else-if 链在同一次 patch 里卸载多块子树，
			在 Vue 3.5 + 重型子页（表格/弹层）下易触发 getNextHostNode(subTree null)。
		-->
		<div class="app-test-module__body">
			<component :is="PAGE_MAP[mainMenu]" :key="mainMenu" />
		</div>
	</div>
</template>

<script setup lang="ts">
import type { Component } from 'vue';
import { computed, markRaw, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
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

const MAIN_MENU: { name: AppTestMenuKey; label: string; icon: Component }[] = [
	{ name: 'device', label: '设备管理', icon: Monitor },
	{ name: 'project', label: 'APP管理', icon: Box },
	{ name: 'page', label: '页面管理', icon: Reading },
	{ name: 'case', label: '用例管理', icon: Files },
	{ name: 'task', label: '任务管理', icon: Calendar },
	{ name: 'report', label: '测试报告', icon: Histogram },
];

const PAGE_MAP: Record<AppTestMenuKey, Component> = {
	device: markRaw(DevicePage),
	project: markRaw(ProjectPage),
	page: markRaw(PageManage),
	case: markRaw(CaseSuite),
	task: markRaw(TaskPage),
	report: markRaw(ReportPage),
};

const route = useRoute();

/**
 * 子模块切换用本地 ref 立即更新 DOM，避免 router.replace 改 fullPath → parent.vue 里 transition+keep-alive
 * 与内部 <component> 换页抢同一轮 patch（subTree / emitsOptions 空引用）。
 * 地址栏用 history.replaceState 静默同步；浏览器前进后退用 popstate 读回。
 * 外部 router.push（如报告带 ?tab=）仍通过 watch(route.fullPath) 对齐。
 */
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

/** Vue Router 的 query 可能为 string | string[]，统一成单值再校验 */
function queryParamSingle(v: unknown): string | undefined {
	if (v === undefined || v === null) return undefined;
	if (Array.isArray(v)) return v.length ? String(v[0]) : undefined;
	return String(v);
}

/** 只改地址栏，不触发 vue-router finalizeNavigation，避免 parent.vue 对 fullPath 的 watch 搅动外层 transition */
function silentSetTabQuery(key: AppTestMenuKey) {
	try {
		const u = new URL(window.location.href);
		u.searchParams.set('tab', key);
		window.history.replaceState(window.history.state, '', `${u.pathname}${u.search}${u.hash}`);
	} catch {
		void 0;
	}
}

function onPopState() {
	try {
		const u = new URL(window.location.href);
		const t = u.searchParams.get('tab');
		const next = isMenuKey(t) ? t : 'device';
		if (mainMenu.value !== next) mainMenu.value = next;
	} catch {
		void 0;
	}
}

watch(
	() => route.fullPath,
	() => {
		const t = queryParamSingle(route.query.tab);
		if (!isMenuKey(t)) {
			mainMenu.value = 'device';
			silentSetTabQuery('device');
			return;
		}
		if (mainMenu.value !== t) mainMenu.value = t;
	},
	{ immediate: true, flush: 'post' },
);

onMounted(() => {
	window.addEventListener('popstate', onPopState);
	if (!isMenuKey(queryParamSingle(route.query.tab))) {
		silentSetTabQuery('device');
	}
});

onBeforeUnmount(() => {
	window.removeEventListener('popstate', onPopState);
});

function onSelectMainMenu(key: AppTestMenuKey) {
	if (mainMenu.value === key) return;
	silentSetTabQuery(key);
	/** 与外层 layout transition+keep-alive 错开两帧再换子页，减轻 unmount/mount 与异步 flush 竞态 */
	const swap = () => {
		mainMenu.value = key;
	};
	if (typeof requestAnimationFrame === 'function') {
		requestAnimationFrame(() => requestAnimationFrame(swap));
	} else {
		setTimeout(swap, 32);
	}
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

.app-test-module__nav {
	display: flex;
	flex-wrap: wrap;
	gap: 4px;
	margin: 0 0 8px;
	padding: 6px 8px;
	background: var(--el-fill-color-light);
	border-radius: 4px;
	box-sizing: border-box;
}

.app-test-nav-item {
	margin: 0;
	padding: 8px 14px;
	border: none;
	border-radius: 4px;
	background: transparent;
	cursor: pointer;
	font: inherit;
	color: var(--el-text-color-regular);
	transition: color 0.2s, background 0.2s;

	&:hover {
		color: var(--el-color-primary);
	}

	&.is-active {
		color: var(--el-color-primary);
		font-weight: 600;
		background: var(--el-bg-color);
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
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
