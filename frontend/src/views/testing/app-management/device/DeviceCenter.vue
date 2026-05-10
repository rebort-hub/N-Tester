<template>
	<div class="ntest-device-layout">
		<div class="page-header">
			<div class="header-left">
				<div class="page-icon" :class="activeName">
					<el-icon v-if="activeName === 'server'"><Monitor /></el-icon>
					<el-icon v-else><Iphone /></el-icon>
				</div>
				<div class="page-info">
					<h3 class="page-title">APP自动化测试</h3>
					<span class="page-subtitle">
						{{ activeName === 'server' ? 'Appium服务器管理' : '手机设备管理' }}
					</span>
				</div>
				<div class="status-indicator">
					<el-tag :type="activeName === 'server' ? 'primary' : 'success'" size="small">
						{{ activeName === 'server' ? '服务器模式' : '设备模式' }}
					</el-tag>
				</div>
				<el-button type="primary" :icon="Plus" size="small" class="add-button" @click="showAddDrawer">
					添加{{ activeName === 'server' ? 'Appium服务器' : '手机设备' }}
				</el-button>
			</div>
		</div>

		<nav class="ntest-device-nav" role="tablist" aria-label="设备中心">
			<button
				type="button"
				class="ntest-device-nav-item"
				role="tab"
				:aria-selected="activeName === 'server'"
				:class="{ 'is-active': activeName === 'server' }"
				@click="setActiveSub('server')"
			>
				appium执行服务器
			</button>
			<button
				type="button"
				class="ntest-device-nav-item"
				role="tab"
				:aria-selected="activeName === 'phone'"
				:class="{ 'is-active': activeName === 'phone' }"
				@click="setActiveSub('phone')"
			>
				手机设备管理
			</button>
		</nav>
		<div class="ntest-device-panels">
			<AppiumServerPanel v-if="activeName === 'server'" ref="serverPanelRef" :key="'device-server'" />
			<RunPhonePanel v-if="activeName === 'phone'" ref="phonePanelRef" :key="'device-phone'" />
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { Plus, Monitor, Iphone } from '@element-plus/icons-vue';
import AppiumServerPanel from './AppiumServerPanel.vue';
import RunPhonePanel from './RunPhonePanel.vue';

const activeName = ref<'server' | 'phone'>('server');
const serverPanelRef = ref<InstanceType<typeof AppiumServerPanel> | null>(null);
const phonePanelRef = ref<InstanceType<typeof RunPhonePanel> | null>(null);

function setActiveSub(k: 'server' | 'phone') {
	activeName.value = k;
}

function showAddDrawer() {
	if (activeName.value === 'server') {
		serverPanelRef.value?.openAdd();
	} else {
		phonePanelRef.value?.openAdd();
	}
}
</script>

<style scoped lang="scss">

.ntest-device-layout {
	.page-header {
		padding: 16px 20px;
		background: var(--el-bg-color);
		border-bottom: 1px solid var(--el-border-color-lighter);
		margin-bottom: 0;

		.header-left {
			display: flex;
			align-items: center;
			gap: 12px;

			.page-icon {
				width: 40px;
				height: 40px;
				border-radius: 8px;
				display: flex;
				align-items: center;
				justify-content: center;
				color: white;
				font-size: 20px;
				transition: all 0.3s ease;

				&.server {
					background: linear-gradient(135deg, #409eff, #67c23a);
				}

				&.phone {
					background: linear-gradient(135deg, #f093fb, #f5576c);
				}
			}

			.page-info {
				flex: 1;

				.page-title {
					margin: 0 0 4px 0;
					font-size: 18px;
					font-weight: 600;
					color: var(--el-text-color-primary);
				}

				.page-subtitle {
					font-size: 14px;
					color: var(--el-text-color-secondary);
					transition: all 0.3s ease;
				}
			}

			.status-indicator {
				margin-right: 12px;
			}

			.add-button {
				margin-left: auto;
			}
		}
	}

	.ntest-device-nav {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin: 10px;
		padding: 6px 8px;
		background: var(--el-fill-color-light);
		border-radius: 4px;
		box-sizing: border-box;
	}

	.ntest-device-nav-item {
		margin: 0;
		padding: 8px 16px;
		border: none;
		border-radius: 4px;
		background: transparent;
		cursor: pointer;
		font: inherit;
		font-size: 14px;
		color: var(--el-text-color-regular);
		transition: color 0.2s, background 0.2s;

		&:hover {
			color: #409eff;
		}

		&.is-active {
			color: #409eff;
			font-weight: 600;
			background: var(--el-bg-color);
			box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
		}
	}

	.ntest-device-panels {
		margin: 0 10px 10px;
	}

	:deep(.el-table) {
		border-radius: 4px;
		overflow: hidden;

		.el-table__header-wrapper th {
			background: #f5f7fa;
		}

		.el-table__body-wrapper tr:hover > td {
			background-color: #f5f7fa !important;
		}
	}
}
</style>
