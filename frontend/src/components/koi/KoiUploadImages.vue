<template>
	<div class="upload-box">
		<el-upload
			v-model:file-list="_fileList"
			action="#"
			list-type="picture-card"
			:class="['upload', imageDisabled ? 'disabled' : '', drag ? 'no-border' : '']"
			:multiple="true"
			:disabled="imageDisabled"
			:limit="limit"
			:http-request="handleHttpUpload"
			:before-upload="beforeUpload"
			:on-exceed="handleExceed"
			:on-success="uploadSuccess"
			:on-error="uploadError"
			:drag="drag"
			:accept="fileType.join(',')"
		>
			<div class="upload-content">
				<slot name="content">
					<el-icon><Plus /></el-icon>
				</slot>
			</div>
			<template #file="{ file }">
				<img :src="file.url" class="upload-image" />
				<div class="upload-operator" @click.stop>
					<div class="upload-icon" @click="handlePictureCardPreview(file)">
						<el-icon><ZoomIn /></el-icon>
						<span>查看</span>
					</div>
					<div v-if="!imageDisabled" class="upload-icon" @click="handleRemove(file)">
						<el-icon><Delete /></el-icon>
						<span>删除</span>
					</div>
				</div>
			</template>
		</el-upload>
		<div class="el-upload-tip">
			<slot name="tip"></slot>
		</div>
		<el-image-viewer v-if="imgViewVisible" :url-list="[viewImageUrl]" @close="imgViewVisible = false" />
	</div>
</template>

<script setup lang="ts">
import { computed, inject, ref, watch } from 'vue';
import { ElLoading } from 'element-plus';
import type { UploadProps, UploadFile, UploadUserFile, UploadRequestOptions } from 'element-plus';
import { formContextKey, formItemContextKey } from 'element-plus';
import { NoticeError, NoticeSuccess, koiNoticeWarning } from '/@/utils/koi';
import { useFileApi } from '/@/api/v1/common/file';
import request from '/@/utils/request';

interface IUploadImagesProps {
	fileList: UploadUserFile[];
	drag?: boolean;
	disabled?: boolean;
	limit?: number;
	fileSize?: number;
	fileType?: any;
	height?: string;
	width?: string;
	borderRadius?: string;
	// 兼容旧版：把图片归属到某个 app_menu_id
	app_menu_id?: any;
	/** 为 true 时不在选文件时请求后端，仅本地预览；由父组件在「确定」时统一上传（对齐旧架构，避免列表刷新等误触发上传） */
	deferCommit?: boolean;
}

const props = withDefaults(defineProps<IUploadImagesProps>(), {
	fileList: () => [],
	drag: true,
	disabled: false,
	limit: 9,
	fileSize: 30,
	fileType: ['image/webp', 'image/jpg', 'image/jpeg', 'image/png', 'image/gif'],
	height: '120px',
	width: '120px',
	borderRadius: '6px',
	app_menu_id: '',
	deferCommit: false,
});

const formContext = inject(formContextKey, void 0);
const formItemContext = inject(formItemContextKey, void 0);

const imageDisabled = computed(() => props.disabled || formContext?.disabled);

const _fileList = ref<UploadUserFile[]>(props.fileList);
watch(
	() => props.fileList,
	(n) => (_fileList.value = n || []),
	{ immediate: true }
);

const beforeUpload: UploadProps['beforeUpload'] = (rawFile) => {
	const okSize = rawFile.size / 1024 / 1024 < props.fileSize;
	const okType = props.fileType.includes(rawFile.type);
	if (!okType) koiNoticeWarning('上传图片不符合所需的格式');
	if (!okSize) koiNoticeWarning(`上传图片大小不能超过 ${props.fileSize}M！`);
	return okType && okSize;
};

/** 是否走 APP 图像库专用接口（避免仅依赖 truthy：0、空串、切换筛选项时误判） */
const isAppImageLibraryUpload = (): boolean => {
	const id = props.app_menu_id;
	return id !== undefined && id !== null && String(id) !== '';
};

const handleHttpUpload = async (options: UploadRequestOptions) => {
	// 延迟提交：只生成本地预览，真正上传由父级在确定时调用 add_img
	// 这里不依赖 app_menu_id，确保只要 deferCommit=true，就绝对不会发任何后端请求。
	if (props.deferCommit) {
		const raw = options.file as File;
		const blobUrl = URL.createObjectURL(raw);
		options.onSuccess({ code: 200, data: { file_path: blobUrl } });
		return;
	}

	const loadingInstance = ElLoading.service({ text: '正在上传', background: 'rgba(0,0,0,.2)' });
	try {
		let res;
		// APP 图像库场景：走专用上传接口，直接写入 app_airtest_images（menu_id 由父组件传入快照，勿绑列表筛选项）
		if (isAppImageLibraryUpload()) {
			const form = new FormData();
			form.append('file', options.file as any);
			form.append('menu_id', String(props.app_menu_id));
			res = await request({
				url: '/v1/app_management/add_img',
				method: 'POST',
				data: form,
				headers: {
					'Content-Type': 'multipart/form-data',
				},
			});
		} else {
			// 其他场景仍然走通用文件上传
			res = await useFileApi().upload({ file: options.file as any });
		}
		// 把完整响应传给 onSuccess，方便在 uploadSuccess 里解析
		options.onSuccess(res);
	} catch (e: any) {
		options.onError(e);
	} finally {
		loadingInstance.close();
	}
};

const emit = defineEmits<{
	'update:fileList': [value: UploadUserFile[]];
}>();

const uploadSuccess = (response: any, uploadFile: UploadFile) => {
	if (!response) return;
	const data = response?.data || response;
	// 兼容多种返回结构：{ data: { file_url } } | { file_url } | 直接是 url 字符串
	const url =
		data?.file_url ||
		data?.file_path ||
		response?.file_url ||
		(typeof response === 'string' ? response : '');
	if (!url) return;

	uploadFile.url = url;
	emit('update:fileList', _fileList.value);
	formItemContext?.prop && formContext?.validateField([formItemContext.prop as string]);
	if (!props.deferCommit) {
		NoticeSuccess('图片上传成功');
	}
};

const handleRemove = (file: UploadFile) => {
	if (file.url?.startsWith('blob:')) {
		try {
			URL.revokeObjectURL(file.url);
		} catch {
			/* ignore */
		}
	}
	_fileList.value = _fileList.value.filter((item) => item.url !== file.url || item.name !== file.name);
	emit('update:fileList', _fileList.value);
};

const uploadError = () => NoticeError('图片上传失败，请您重新上传');
const handleExceed = () => koiNoticeWarning(`当前最多只能上传 ${props.limit} 张图片，请移除后上传！`);

const viewImageUrl = ref('');
const imgViewVisible = ref(false);
const handlePictureCardPreview: UploadProps['onPreview'] = (file) => {
	viewImageUrl.value = file.url!;
	imgViewVisible.value = true;
};
</script>

<style scoped lang="scss">
.upload-box {
	.no-border {
		:deep(.el-upload--picture-card) {
			border: none !important;
		}
	}
	:deep(.upload) {
		.el-upload-dragger {
			display: flex;
			align-items: center;
			justify-content: center;
			width: 100%;
			height: 100%;
			padding: 0;
			overflow: hidden;
			border: 2px dashed var(--el-color-primary);
			border-radius: v-bind(borderRadius);
		}
		.el-upload-list__item,
		.el-upload--picture-card {
			width: v-bind(width);
			height: v-bind(height);
			background-color: transparent;
			border: 2px dashed var(--el-color-primary);
			border-radius: v-bind(borderRadius);
		}
	}
}
</style>

