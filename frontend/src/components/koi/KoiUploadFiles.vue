<template>
  <div class="koi-upload-files">
    <el-upload
      class="upload-area"
      :show-file-list="false"
      :before-upload="handleBeforeUpload"
    >
      <el-button type="primary" plain>选择文件</el-button>
      <span v-if="fileName" class="file-name">当前：{{ fileName }}</span>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useFileApi } from '/@/api/v1/common/file'

const props = defineProps<{
  modelValue?: string | null
  fileName?: string | null
  acceptType?: string
  acceptTypes?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: string | null): void
  (e: 'file-success', payload: { file_url: string; filename: string }): void
}>()

const fileName = computed(() => props.fileName || props.modelValue || '')
const fileApi = useFileApi()

const handleBeforeUpload = async (file: File) => {
  // 通过系统文件上传接口上传，返回可访问的 file_url
  try {
    const form = new FormData()
    form.append('file', file)
    form.append('is_public', '1')
    // 让上层先看到文件名
    emit('update:modelValue', file.name)

    const res: any = await fileApi.upload(form)
    const fileUrl = res?.data?.file_url
    if (!fileUrl) {
      ElMessage.error('上传失败：未返回文件地址')
      return false
    }
    emit('file-success', { file_url: fileUrl, filename: file.name })
    ElMessage.success('上传成功：' + file.name)
  } catch (e: any) {
    ElMessage.error('上传失败：' + (e?.message || '未知错误'))
  }
  // 阻止 el-upload 自行上传（我们已手动上传）
  return false
}
</script>

<style scoped>
.koi-upload-files {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.file-name {
  font-size: 12px;
  color: var(--el-text-color-regular);
}
</style>

