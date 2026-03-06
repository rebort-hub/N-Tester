<template>
	<el-dialog
		:model-value="modelValue"
		:title="versionId ? '编辑版本' : '新增版本'"
		width="600px"
		:close-on-click-modal="false"
		@close="handleClose"
	>
		<el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
			<el-form-item label="版本名称" prop="name">
				<el-input v-model="form.name" placeholder="请输入版本名称，如：v1.0.0" maxlength="100" show-word-limit />
			</el-form-item>

			<el-form-item label="版本描述">
				<el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入版本描述" />
			</el-form-item>

			<el-form-item label="主干版本">
				<el-switch v-model="form.is_baseline" active-text="是" inactive-text="否" />
				<div style="color: #909399; font-size: 12px; margin-top: 5px">主干版本用于标记重要的版本里程碑</div>
			</el-form-item>

			<el-form-item label="关联项目" v-if="!versionId">
				<el-select v-model="form.project_ids" multiple placeholder="请选择要关联的项目" style="width: 100%">
					<el-option v-for="project in projectList" :key="project.id" :label="project.name" :value="project.id" />
				</el-select>
			</el-form-item>
		</el-form>

		<template #footer>
			<el-button @click="handleClose">取消</el-button>
			<el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { createVersion, updateVersion, getVersionDetail } from '/@/api/v1/testcases';
import { getProjectList } from '/@/api/v1/project';

const props = defineProps({
	modelValue: {
		type: Boolean,
		default: false,
	},
	versionId: {
		type: Number,
		default: null,
	},
});

const emit = defineEmits(['update:modelValue', 'success']);

const formRef = ref();
const loading = ref(false);
const projectList = ref<any[]>([]);

const form = reactive({
	name: '',
	description: '',
	is_baseline: false,
	project_ids: [] as number[],
});

const rules = {
	name: [{ required: true, message: '请输入版本名称', trigger: 'blur' }],
};

// 获取项目列表
const getProjects = async () => {
	try {
		const res = await getProjectList({ page: 1, page_size: 100 });
		if (res.code === 200) {
			projectList.value = res.data.items || [];
		}
	} catch (error) {
		console.error('获取项目列表失败:', error);
	}
};

// 获取详情
const getDetail = async () => {
	if (!props.versionId) return;

	loading.value = true;
	try {
		const res = await getVersionDetail(props.versionId);
		if (res.code === 200) {
			Object.assign(form, {
				name: res.data.name,
				description: res.data.description || '',
				is_baseline: res.data.is_baseline,
			});
		}
	} catch (error) {
		console.error('获取详情失败:', error);
		ElMessage.error('获取详情失败');
	} finally {
		loading.value = false;
	}
};

// 提交
const handleSubmit = async () => {
	await formRef.value.validate();

	loading.value = true;
	try {
		const data = { ...form };
		let res;

		if (props.versionId) {
			// 编辑时不需要project_ids
			delete (data as any).project_ids;
			res = await updateVersion(props.versionId, data);
		} else {
			res = await createVersion(data);
		}

		if (res.code === 200) {
			ElMessage.success(props.versionId ? '更新成功' : '创建成功');
			emit('success');
			handleClose();
		}
	} catch (error) {
		console.error('提交失败:', error);
		ElMessage.error('提交失败');
	} finally {
		loading.value = false;
	}
};

// 关闭
const handleClose = () => {
	emit('update:modelValue', false);
};

// 监听对话框打开
watch(
	() => props.modelValue,
	(val) => {
		if (val) {
			if (props.versionId) {
				getDetail();
			} else {
				// 重置表单
				Object.assign(form, {
					name: '',
					description: '',
					is_baseline: false,
					project_ids: [],
				});
			}
		}
	}
);

onMounted(() => {
	getProjects();
});
</script>
