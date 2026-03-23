<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';

const emit = defineEmits(['update:value']);
const props = defineProps<{
	value?: string;
	height?: string;
	width?: string;
}>();

const inner = ref(props.value ?? '');
const isFull = ref(false);

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
		<div class="toolbar">
			<el-button size="small" @click="pretty">格式化</el-button>
			<el-button size="small" @click="compact">去空格</el-button>
			<el-button size="small" @click="isFull = true">全屏</el-button>
		</div>
		<el-input
			:model-value="inner"
			type="textarea"
			:autosize="{ minRows: 8, maxRows: 30 }"
			placeholder="请输入 JSON"
			@update:model-value="(v:any) => update(v)"
		/>
		<el-dialog v-model="isFull" title="JSON 编辑器" width="90%" top="5vh" destroy-on-close>
			<el-input
				:model-value="inner"
				type="textarea"
				:autosize="{ minRows: 25, maxRows: 45 }"
				placeholder="请输入 JSON"
				@update:model-value="(v:any) => update(v)"
			/>
			<template #footer>
				<el-button @click="isFull = false">关闭</el-button>
			</template>
		</el-dialog>
	</div>
</template>

<style scoped>
.toolbar {
	display: flex;
	gap: 8px;
	margin-bottom: 8px;
}
</style>

