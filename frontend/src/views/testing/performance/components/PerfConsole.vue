<template>
	<div class="perf-console">
		<div class="perf-console__toolbar">
			<span class="perf-console__label">
				<el-icon><ele-Monitor /></el-icon>{{ title }}
			</span>
			<div class="perf-console__actions">
				<slot name="actions" />
			</div>
		</div>
		<div ref="bodyRef" class="perf-console__body">
			<template v-if="logs.length">
				<div
					v-for="(line, idx) in logs"
					:key="idx"
					class="console-line"
					:class="`log-${line.level}`"
				>
					<span class="log-time">{{ line.time }}</span>
					<span class="log-text">{{ line.text }}</span>
				</div>
			</template>
			<div v-else class="console-empty">{{ emptyText }}</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';

export interface LogLine {
	time: string;
	level: string;
	text: string;
}

const props = withDefaults(defineProps<{
	logs: LogLine[];
	title?: string;
	emptyText?: string;
	autoScroll?: boolean;
}>(), {
	title: '控制台输出',
	emptyText: '暂无输出，启动压测后将在此显示实时日志...',
	autoScroll: true,
});

defineEmits<{ (e: 'clear'): void }>();

const bodyRef = ref<HTMLElement | null>(null);

watch(
	() => props.logs.length,
	() => {
		if (!props.autoScroll) return;
		nextTick(() => {
			if (bodyRef.value) bodyRef.value.scrollTop = bodyRef.value.scrollHeight;
		});
	},
);
</script>

<style scoped lang="scss">
.perf-console {
	display: flex;
	flex-direction: column;
	flex: 1;
	min-height: 0;
	border: 1px solid #2a2a3a;
	border-radius: 6px;
	overflow: hidden;

	&__toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 8px 14px;
		background: #1a1a2e;
		color: #7ec8e3;
		font-size: 13.5px;
		flex-shrink: 0;
	}

	&__label {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	&__actions {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	&__body {
		flex: 1;
		min-height: 0;
		background: #0d0d1a;
		overflow-x: auto;
		overflow-y: auto;
		padding: 8px 12px 28px;
		font-family: 'Ubuntu Mono', 'DejaVu Sans Mono', 'Liberation Mono',
			'WenQuanYi Micro Hei Mono', 'Noto Sans Mono CJK SC',
			'Courier New', monospace;
		font-size: 12px;
		line-height: 1.45;
		letter-spacing: 0;

		// 滚动条轨道与内容背景一致，不露白
		scrollbar-color: rgba(255, 255, 255, 0.18) #0d0d1a; // Firefox
		scrollbar-width: thin;
	}
}

.console-line {
	display: flex;
	gap: 8px;
	white-space: nowrap;

	.log-time {
		color: #5f6b7c;
		flex-shrink: 0;
		user-select: none;
	}

	.log-text {
		white-space: pre; /* 保留 \n 换行（多行命令），配合外层 overflow-x: auto 横向滚动 */
	}

	&.log-info    .log-text { color: #c8d0e0; }
	&.log-success .log-text { color: #67c23a; }
	&.log-warn    .log-text { color: #e6a23c; }
	&.log-error   .log-text { color: #f56c6c; }
}

.console-empty {
	color: #5f6b7c;
	text-align: center;
	padding: 40px 0;
}
</style>

<style>
/* webkit 滚动条：scoped 样式对伪元素选择器不可靠，此处用全局覆盖 */
.perf-console__body::-webkit-scrollbar {
	width: 6px;
	height: 6px;
}
.perf-console__body::-webkit-scrollbar-track {
	background: #0d0d1a;
}
.perf-console__body::-webkit-scrollbar-thumb {
	background: rgba(255, 255, 255, 0.18);
	border-radius: 3px;
}
.perf-console__body::-webkit-scrollbar-thumb:hover {
	background: rgba(255, 255, 255, 0.32);
}
</style>
