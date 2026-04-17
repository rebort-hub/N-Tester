<template>
	<div class="mock-panel">
		<div class="mock-section">
			<div class="mock-section-title">Mock 地址</div>
			<div class="mock-addr-bar">
				<code class="mock-url">{{ mockUrl }}</code>
				<el-button size="small" plain @click="copy">复制</el-button>
			</div>
		</div>
		<div class="mock-section" style="margin-top:20px">
			<div class="mock-section-header">
				<span class="mock-section-title">Mock 期望</span>
				<el-button size="small" type="primary" plain @click="openAdd">+ 新建期望</el-button>
			</div>
			<el-table :data="expects" size="small" style="margin-top:8px" empty-text="暂无期望">
				<el-table-column prop="name" label="名称" />
				<el-table-column prop="condition" label="条件" />
				<el-table-column label="操作" width="80">
					<template #default="{$index}">
						<el-button type="danger" link size="small" @click="expects.splice($index,1)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
		</div>
		<el-dialog v-model="dialogVisible" title="新建 Mock 期望" width="460px" destroy-on-close>
			<el-form :model="form" label-width="80px">
				<el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
				<el-form-item label="条件"><el-input v-model="form.condition" placeholder="可选" /></el-form-item>
				<el-form-item label="响应体">
					<textarea v-model="form.body" class="mock-textarea" placeholder='{"code":200,"data":{}}'></textarea>
				</el-form-item>
				<el-form-item label="状态码"><el-input-number v-model="form.status" :min="100" :max="599" /></el-form-item>
			</el-form>
			<template #footer>
				<el-button @click="dialogVisible=false">取消</el-button>
				<el-button type="primary" @click="confirm">确定</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

const props = defineProps<{ serviceId: number; apiData: any }>();
const info = computed(() => props.apiData?.api_info || props.apiData || {});
const mockUrl = computed(() => `${window.location.origin}/mock${info.value.url || '/api/path'}`);
const expects = ref<any[]>([]);
const dialogVisible = ref(false);
const form = ref({ name: '', condition: '', body: '{"code":200,"data":{}}', status: 200 });

const copy = () => navigator.clipboard?.writeText(mockUrl.value).then(() => ElMessage.success('已复制'));
const openAdd = () => { form.value = { name: '', condition: '', body: '{"code":200,"data":{}}', status: 200 }; dialogVisible.value = true; };
const confirm = () => {
	if (!form.value.name) { ElMessage.warning('请填写名称'); return; }
	expects.value.push({ ...form.value });
	dialogVisible.value = false;
};
</script>

<style scoped>
.mock-panel { height: 100%; overflow-y: auto; padding: 16px; }
.mock-section-title { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 10px; }
.mock-section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.mock-addr-bar { display: flex; align-items: center; gap: 10px; background: var(--el-fill-color-light); border-radius: 6px; padding: 8px 12px; }
.mock-url { font-family: monospace; font-size: 12px; color: #409eff; flex: 1; word-break: break-all; }
.mock-textarea { width: 100%; min-height: 80px; background: var(--el-bg-color); border: 1px solid var(--el-border-color); border-radius: 4px; padding: 8px; font-family: monospace; font-size: 12px; color: var(--el-text-color-primary); resize: vertical; outline: none; box-sizing: border-box; }
</style>
