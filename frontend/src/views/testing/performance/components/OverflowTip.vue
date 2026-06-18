<template>
	<el-tooltip :content="content" :placement="placement" :show-after="showAfter" :disabled="!overflow">
		<span ref="el" class="ovf-tip-text" @mouseenter="check"><slot /></span>
	</el-tooltip>
</template>

<script setup lang="ts">
import { ref } from 'vue';
withDefaults(defineProps<{
	content?:   string;
	placement?: string;
	showAfter?: number;
}>(), { placement: 'top', showAfter: 400 });

const el       = ref<HTMLElement>();
const overflow = ref(false);
const check    = () => {
	if (el.value) overflow.value = el.value.scrollWidth > el.value.clientWidth;
};
</script>

<style scoped>
.ovf-tip-text {
	display: block;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	min-width: 0;
}
</style>
