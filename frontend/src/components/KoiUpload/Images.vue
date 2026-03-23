<template>
  <KoiUploadImages v-bind="$attrs" v-model:file-list="proxy">
    <template v-for="(_, name) in $slots" #[name]="slotProps"><slot :name="name" v-bind="slotProps" /></template>
  </KoiUploadImages>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import KoiUploadImages from '/@/components/koi/KoiUploadImages.vue';
import type { UploadUserFile } from 'element-plus';

const props = defineProps<{ fileList: UploadUserFile[] }>();
const emit = defineEmits<{ 'update:fileList': [value: UploadUserFile[]] }>();

const proxy = computed({
  get: () => props.fileList,
  set: (v) => emit('update:fileList', v),
});
</script>

