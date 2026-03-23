<template>
  <KoiCard><slot /><template v-for="(_, name) in $slots" #[name]="slotProps"><slot :name="name" v-bind="slotProps" /></template></KoiCard>
</template>

<script setup lang="ts">
import KoiCard from '/@/components/koi/KoiCard.vue';
</script>

