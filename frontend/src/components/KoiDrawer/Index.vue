<template>
  <KoiDrawer v-bind="$attrs" ref="inner">
    <template v-for="(_, name) in $slots" #[name]="slotProps"><slot :name="name" v-bind="slotProps" /></template>
  </KoiDrawer>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import KoiDrawer from '/@/components/koi/KoiDrawer.vue';

const inner = ref<any>(null);
defineExpose({
  koiOpen: (...args: any[]) => inner.value?.koiOpen?.(...args),
  koiClose: (...args: any[]) => inner.value?.koiClose?.(...args),
  koiQuickClose: (...args: any[]) => inner.value?.koiQuickClose?.(...args),
});
</script>

