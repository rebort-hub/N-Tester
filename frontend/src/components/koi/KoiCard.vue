<template>
	<div class="koi-card">
		<div class="p-b-5px">
			<slot name="header"></slot>
		</div>
		<slot></slot>
		<div class="p-t-7px">
			<slot name="footer"></slot>
		</div>
	</div>
</template>

<script setup lang="ts"></script>

<style scoped>
.koi-card {
	border-radius: 6px;
	border: 1px solid #e4e7ed;
	background-color: #fff;
	overflow: hidden;
	color: #303133;
	@apply p-x-10px p-t-10px p-b-0px dark:bg-#1d1e1f dark:c-#cfd3dc dark:b-#414243 flex flex-col flex-1 transition-ease-in-out transition-300;
}
</style>

