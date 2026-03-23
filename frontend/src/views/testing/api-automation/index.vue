<script setup lang="ts">
import { ref } from 'vue';
import ApiProject from './api_project.vue';
import ApiScript from './api_script.vue';
import ApiResultList from './api_result_list.vue';

const active = ref<'manage' | 'scene' | 'result'>('manage');
</script>

<template>
	<div class="api-automation-tabs">
		<el-tabs v-model="active" type="border-card">
			<el-tab-pane label="接口管理" name="manage">
				<ApiProject />
			</el-tab-pane>
			<el-tab-pane label="场景管理" name="scene">
				<ApiScript />
			</el-tab-pane>
			<el-tab-pane label="执行结果" name="result">
				<ApiResultList />
			</el-tab-pane>
		</el-tabs>
	</div>
</template>

<style scoped>
.api-automation-tabs {
	padding: 10px;
}
</style>
