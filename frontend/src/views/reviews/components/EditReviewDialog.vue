<template>
	<el-dialog
		v-model="visible"
		title="编辑评审"
		width="800px"
		:before-close="handleClose"
	>
		<el-form
			ref="formRef"
			:model="form"
			:rules="rules"
			label-width="100px"
		>
			<el-row :gutter="20">
				<el-col :span="12">
					<el-form-item label="优先级" prop="priority">
						<el-select v-model="form.priority" placeholder="选择优先级" style="width: 100%">
							<el-option label="低" value="low" />
							<el-option label="中" value="medium" />
							<el-option label="高" value="high" />
							<el-option label="紧急" value="urgent" />
						</el-select>
					</el-form-item>
				</el-col>
				<el-col :span="12">
					<el-form-item label="状态" prop="status">
						<el-select v-model="form.status" placeholder="选择状态" style="width: 100%">
							<el-option label="待开始" value="pending" />
							<el-option label="进行中" value="in_progress" />
							<el-option label="已完成" value="completed" />
							<el-option label="已取消" value="cancelled" />
						</el-select>
					</el-form-item>
				</el-col>
			</el-row>

			<el-form-item label="评审标题" prop="title">
				<el-input v-model="form.title" placeholder="请输入评审标题" />
			</el-form-item>

			<el-form-item label="评审描述">
				<el-input
					v-model="form.description"
					type="textarea"
					:rows="3"
					placeholder="请输入评审描述"
				/>
			</el-form-item>

			<el-form-item label="截止日期">
				<el-date-picker
					v-model="form.deadline"
					type="datetime"
					placeholder="选择截止日期"
					style="width: 100%"
				/>
			</el-form-item>
		</el-form>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="handleClose">取消</el-button>
				<el-button type="primary" :loading="loading" @click="handleSubmit">
					更新
				</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { updateReview, type Review } from '/@/api/v1/reviews';

// Props
interface Props {
	modelValue: boolean;
	review?: Review | null;
}

// Emits
interface Emits {
	(e: 'update:modelValue', value: boolean): void;
	(e: 'success'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式数据
const visible = ref(false);
const loading = ref(false);
const formRef = ref<FormInstance>();

// 表单数据
const form = reactive({
	title: '',
	description: '',
	priority: 'medium',
	status: 'pending',
	deadline: '',
});

// 表单验证规则
const rules: FormRules = {
	title: [
		{ required: true, message: '请输入评审标题', trigger: 'blur' },
		{ min: 2, max: 100, message: '标题长度在 2 到 100 个字符', trigger: 'blur' }
	],
	priority: [
		{ required: true, message: '请选择优先级', trigger: 'change' }
	],
	status: [
		{ required: true, message: '请选择状态', trigger: 'change' }
	],
};

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	(val) => {
		visible.value = val;
		if (val && props.review) {
			loadReviewData();
		}
	}
);

// 监听 visible 变化
watch(visible, (val) => {
	emit('update:modelValue', val);
});

// 加载评审数据
const loadReviewData = () => {
	if (props.review) {
		form.title = props.review.title;
		form.description = props.review.description || '';
		form.priority = props.review.priority;
		form.status = props.review.status;
		form.deadline = props.review.deadline || '';
	}
};

// 重置表单
const resetForm = () => {
	form.title = '';
	form.description = '';
	form.priority = 'medium';
	form.status = 'pending';
	form.deadline = '';
	formRef.value?.clearValidate();
};

// 处理关闭
const handleClose = () => {
	visible.value = false;
	resetForm();
};

// 处理提交
const handleSubmit = async () => {
	if (!formRef.value || !props.review) return;
	
	try {
		await formRef.value.validate();
		
		loading.value = true;
		
		const data = {
			title: form.title,
			description: form.description,
			priority: form.priority,
			status: form.status,
			deadline: form.deadline ? new Date(form.deadline).toISOString() : undefined,
		};
		
		const response = await updateReview(props.review.id, data);
		if (response.code === 200) {
			ElMessage.success('更新评审成功');
			emit('success');
			handleClose();
		}
	} catch (error) {
		console.error('更新评审失败:', error);
		ElMessage.error('更新评审失败');
	} finally {
		loading.value = false;
	}
};
</script>

<style scoped>
.dialog-footer {
	text-align: right;
}

.el-form-item {
	margin-bottom: 38px;
}

.el-row {
	margin-bottom: 18px;
}

.el-row .el-col .el-form-item {
	margin-bottom: 38px;
}

.el-form-item:last-child {
	margin-bottom: 0;
}

.el-form-item .el-form-item__error {
	position: static;
	margin-top: 6px;
	line-height: 1.5;
	word-wrap: break-word;
	white-space: normal;
}

:deep(.el-dialog) {
	max-height: 95vh;
	overflow-y: auto;
}

:deep(.el-dialog__body) {
	max-height: calc(95vh - 140px);
	overflow-y: auto;
	padding: 20px 20px 0 20px;
}
</style>