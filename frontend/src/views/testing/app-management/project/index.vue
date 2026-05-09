<template>
	<div class="app-test-project layout-container autotest-module-shell">
		<div class="page-toolbar">
			<span class="page-toolbar__title">APP管理</span>
			<span class="page-toolbar__hint">图像资源库</span>
		</div>
		<AppImages />
	</div>
</template>

<script setup lang="ts">
import AppImages from '../app_images.vue';
</script>

<style scoped lang="scss">
.layout-container.autotest-module-shell {
	min-height: 400px;
}

.page-toolbar {
	display: flex;
	align-items: baseline;
	gap: 12px;
	margin-bottom: 12px;
	padding-bottom: 12px;
	border-bottom: 1px solid var(--el-border-color-lighter);
}

.page-toolbar__title {
	font-size: 16px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.page-toolbar__hint {
	font-size: 13px;
	color: var(--el-text-color-secondary);
}
</style>
