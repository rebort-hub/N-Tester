<template>
	<el-dialog
		:model-value="visible"
		:title="title"
		:width="width"
		:center="center"
		:close-on-click-modal="false"
		append-to-body
		draggable
		:destroy-on-close="destroyOnClose"
		:before-close="koiClose"
		:fullscreen="fullscreen"
	>
		<slot name="header"></slot>
		<!-- 关闭时不挂载插槽内容，避免首屏挂载 Upload/Form 与外层 KeepAlive 卸载叠在同一帧触发 Vue patch 告警 -->
		<div v-if="visible" class="container" :style="{ height: height + 'px' }">
			<slot name="content"></slot>
		</div>
		<template #footer v-if="!footerHidden">
			<span class="dialog-footer">
				<el-button type="primary" :loading="confirmLoading" @click="koiConfirm">{{ confirmText }}</el-button>
				<el-button type="danger" @click="koiCancel">{{ cancelText }}</el-button>
			</span>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, toRefs, watch } from 'vue';
import { MsgWarning, MsgBox, MsgSuccess } from '/@/utils/koi';

interface IDialogProps {
	title?: string;
	visible?: boolean;
	width?: number | string;
	center?: boolean;
	height?: number;
	confirmText?: string;
	cancelText?: string;
	destroyOnClose?: boolean;
	fullscreen?: boolean;
	loading?: boolean;
	footerHidden?: boolean;
	beforeCloseCheck?: boolean;
	/**
	 * el-dialog 关闭时执行的回调（主要用于 X 关闭时清理副作用）。
	 * 注意：不会参与 Element Plus 的 done 回调链。
	 */
	beforeClose?: (() => void | Promise<void>) | null;
}

const props = withDefaults(defineProps<IDialogProps>(), {
	title: 'Dialog',
	height: 300,
	width: 650,
	center: true,
	visible: false,
	confirmText: '确定',
	cancelText: '取消',
	destroyOnClose: false,
	fullscreen: false,
	loading: false,
	footerHidden: false,
	beforeCloseCheck: true,
	beforeClose: null,
});

const visible = ref(false);
watch(
	() => props.visible,
	(v) => {
		visible.value = !!v;
	},
	{ immediate: true }
);

const { loading } = toRefs(props);
const confirmLoading = ref(loading);

const koiOpen = () => {
	visible.value = true;
};

const koiClose = () => {
	const runBeforeClose = () => {
		try {
			props.beforeClose?.();
		} catch (e) {
			// 回调失败不影响关闭
		}
	};

	if (props.beforeCloseCheck) {
		MsgBox('您确认进行关闭么？')
			.then(() => {
				runBeforeClose();
				visible.value = false;
			})
			.catch(() => {
				MsgWarning('已取消');
			});
	} else {
		runBeforeClose();
		visible.value = false;
	}
};

const koiQuickClose = (data: any) => {
	visible.value = false;
	if (data !== undefined && data !== null && data !== '') MsgSuccess(data);
};

const emits = defineEmits(['koiConfirm', 'koiCancel']);
const koiConfirm = () => emits('koiConfirm');
const koiCancel = () => emits('koiCancel');

defineExpose({
	koiOpen,
	koiClose,
	koiQuickClose,
});
</script>

<style lang="scss" scoped>
.container {
	overflow-x: initial;
	overflow-y: auto;
}
</style>

