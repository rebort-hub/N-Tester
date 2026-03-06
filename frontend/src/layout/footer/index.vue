<template>
	<el-footer class="layout-footer pb15">
		<div class="layout-footer-warp">
			<div>N-Tester平台 ❤️</div>
			<div class="mt5">@2026 N-tester平台版权所有</div>
		</div>
	</el-footer>
</template>

<script setup lang="ts" name="layoutFooter">
// 此处需有内容（注释也得），否则缓存将失败
</script>

<style scoped lang="scss">
.layout-footer {
	width: 100%;
	display: flex;
	&-warp {
		margin: auto;
		color: var(--el-text-color-secondary);
		text-align: center;
		animation: error-num 0.3s ease;
	}
}
</style>
