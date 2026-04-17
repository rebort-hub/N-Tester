<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['update:value']);
const props = defineProps<{
	value?: string;
	height?: string;
	width?: string;
}>();

const inner = ref(props.value ?? '');
const isFull = ref(false);

watch(() => props.value, (v) => { if (v !== inner.value) inner.value = v ?? ''; });

const style = computed(() => ({
	height: props.height ?? '320px',
	width: props.width ?? '100%',
}));

const update = (v: string) => {
	inner.value = v;
	emit('update:value', v);
};

const pretty = () => {
	try {
		update(JSON.stringify(JSON.parse(inner.value || '{}'), null, 2));
	} catch (e: any) {
		ElMessage.error(e?.message || 'JSON 格式错误');
	}
};
const compact = () => {
	update((inner.value || '').replace(/\s+/g, ''));
};
</script>

<template>
	<div class="json-editor" :style="style">
		<div class="je-toolbar">
			<button class="je-btn" title="格式化" @click="pretty">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><line x1="3" y1="18" x2="18" y2="18"/>
				</svg>
				<span>格式化</span>
			</button>
			<button class="je-btn" title="压缩" @click="compact">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/>
					<line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/>
				</svg>
				<span>压缩</span>
			</button>
			<button class="je-btn" title="全屏" @click="isFull = true">
				<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/>
					<line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/>
				</svg>
				<span>全屏</span>
			</button>
		</div>
		<textarea
			class="je-textarea"
			:value="inner"
			placeholder="请输入 JSON"
			spellcheck="false"
			@input="(e:any) => update(e.target.value)"
		/>
		<el-dialog v-model="isFull" title="" width="80%" top="4vh" destroy-on-close class="je-dialog">
			<template #header>
				<div class="je-dialog-header">
					<span class="je-dialog-title">JSON 编辑器</span>
					<div style="display:flex;gap:6px">
						<button class="je-btn" @click="pretty">
							<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="15" y2="12"/><line x1="3" y1="18" x2="18" y2="18"/></svg>
							<span>格式化</span>
						</button>
						<button class="je-btn" @click="compact">
							<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
							<span>压缩</span>
						</button>
					</div>
				</div>
			</template>
			<textarea
				class="je-textarea je-textarea--full"
				:value="inner"
				placeholder="请输入 JSON"
				spellcheck="false"
				@input="(e:any) => update(e.target.value)"
			/>
			<template #footer>
				<button class="je-btn je-btn--close" @click="isFull = false">关闭</button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.json-editor { display: flex; flex-direction: column; background: #1e1e1e; overflow: hidden; }
.je-toolbar { display: flex; gap: 4px; padding: 5px 10px; background: #252526; border-bottom: 1px solid #3c3c3c; flex-shrink: 0; }
.je-btn { display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; background: transparent; border: 1px solid #4a4a4a; border-radius: 3px; color: #aaa; font-size: 11px; cursor: pointer; transition: all .15s; white-space: nowrap; }
.je-btn:hover { background: #3c3c3c; color: #e0e0e0; border-color: #666; }
.je-btn svg { flex-shrink: 0; }
.je-textarea { flex: 1; width: 100%; background: #1e1e1e; color: #d4d4d4; border: none; outline: none; resize: none; padding: 12px 14px; font-family: 'Consolas','Monaco','Courier New',monospace; font-size: 13px; line-height: 1.65; tab-size: 2; box-sizing: border-box; min-height: 0; }
.je-textarea::placeholder { color: #555; }
.je-textarea--full { min-height: 60vh; resize: vertical; }
.je-dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 0 4px; }
.je-dialog-title { font-size: 14px; font-weight: 600; color: #d4d4d4; }
.je-btn--close { padding: 5px 16px; font-size: 12px; }
</style>

<style>
.je-dialog .el-dialog { background: #1e1e1e !important; border: 1px solid #3c3c3c; }
.je-dialog .el-dialog__header { background: #252526; border-bottom: 1px solid #3c3c3c; padding: 10px 16px; }
.je-dialog .el-dialog__body { padding: 0; background: #1e1e1e; }
.je-dialog .el-dialog__footer { background: #252526; border-top: 1px solid #3c3c3c; padding: 8px 16px; }
</style>
