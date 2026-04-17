<template>
	<div class="history-panel">
		<div class="history-toolbar">
			<el-button size="small" @click="load">刷新</el-button>
		</div>
		<div v-if="!list.length" class="history-empty">
			<el-icon style="font-size:36px;color:#dcdfe6"><Document /></el-icon>
			<p>暂无调试记录</p>
		</div>
		<div v-else class="history-list">
			<div v-for="(r,i) in list" :key="i" class="history-item">
				<div class="history-left">
					<el-tag size="small" :type="r.status_code>=200&&r.status_code<300?'success':r.status_code>=400?'danger':'warning'" effect="light">{{ r.status_code }}</el-tag>
					<span class="history-url">{{ r.req?.url || '-' }}</span>
				</div>
				<span class="history-time">{{ r.creation_date ? String(r.creation_date).replace('T',' ').slice(0,19) : '' }}</span>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { Document } from '@element-plus/icons-vue';
import { req_history } from '/@/api/v1/api_automation';

const list = ref<any[]>([]);
const load = async () => {
	try {
		const r: any = await req_history({});
		list.value = Array.isArray(r?.data) ? r.data : [];
	} catch { list.value = []; }
};
onMounted(load);
</script>

<style scoped>
.history-panel { height: 100%; display: flex; flex-direction: column; overflow: hidden; padding: 10px; }
.history-toolbar { margin-bottom: 10px; flex-shrink: 0; }
.history-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); gap: 8px; font-size: 13px; }
.history-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.history-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: var(--el-fill-color-light); border-radius: 6px; }
.history-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.history-url { font-size: 12px; color: var(--el-text-color-regular); font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.history-time { font-size: 11px; color: var(--el-text-color-placeholder); flex-shrink: 0; margin-left: 8px; }
</style>
