<template>
	<el-dialog
		:model-value="modelValue"
		:title="testcaseId ? '编辑测试用例' : '新增测试用例'"
		width="900px"
		:close-on-click-modal="false"
		@close="handleClose"
	>
		<el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="testcase-form">
			<el-row :gutter="20">
				<!-- 显示所属项目 -->
				<el-col :span="24" v-if="projectName">
					<div class="project-info">
						<span class="project-label">所属项目：</span>
						<span class="project-name">{{ projectName }}</span>
					</div>
				</el-col>

				<el-col :span="24">
					<el-form-item label="用例标题" prop="title">
						<el-input v-model="form.title" placeholder="请输入用例标题" maxlength="500" show-word-limit />
					</el-form-item>
				</el-col>

				<el-col :span="12">
					<el-form-item label="优先级" prop="priority">
						<el-select v-model="form.priority" placeholder="请选择优先级" style="width: 100%">
							<el-option label="低" value="low" />
							<el-option label="中" value="medium" />
							<el-option label="高" value="high" />
							<el-option label="紧急" value="critical" />
						</el-select>
					</el-form-item>
				</el-col>

				<el-col :span="12">
					<el-form-item label="状态" prop="status">
						<el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
							<el-option label="草稿" value="draft" />
							<el-option label="激活" value="active" />
							<el-option label="已废弃" value="deprecated" />
						</el-select>
					</el-form-item>
				</el-col>

				<el-col :span="12">
					<el-form-item label="测试类型" prop="test_type">
						<el-select v-model="form.test_type" placeholder="请选择测试类型" style="width: 100%">
							<el-option label="功能测试" value="functional" />
							<el-option label="集成测试" value="integration" />
							<el-option label="API测试" value="api" />
							<el-option label="UI测试" value="ui" />
							<el-option label="性能测试" value="performance" />
							<el-option label="安全测试" value="security" />
						</el-select>
					</el-form-item>
				</el-col>

				<el-col :span="12">
					<el-form-item label="所属模块">
						<el-select v-model="form.module_id" placeholder="请选择模块" clearable style="width: 100%">
							<el-option v-for="module in moduleList" :key="module.id" :label="module.name" :value="module.id" />
						</el-select>
					</el-form-item>
				</el-col>

				<el-col :span="24">
					<el-form-item label="标签">
						<el-select v-model="form.tags" multiple placeholder="请选择或输入标签" allow-create filterable style="width: 100%">
							<el-option label="功能测试" value="功能测试" />
							<el-option label="冒烟测试" value="冒烟测试" />
							<el-option label="回归测试" value="回归测试" />
						</el-select>
					</el-form-item>
				</el-col>

				<el-col :span="24">
					<el-form-item label="用例描述">
						<el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入用例描述" />
					</el-form-item>
				</el-col>

				<el-col :span="24">
					<el-form-item label="前置条件">
						<el-input v-model="form.preconditions" type="textarea" :rows="2" placeholder="请输入前置条件" />
					</el-form-item>
				</el-col>

				<el-col :span="24">
					<el-form-item label="预期结果">
						<el-input v-model="form.expected_result" type="textarea" :rows="2" placeholder="请输入预期结果" />
					</el-form-item>
				</el-col>

				<el-col :span="24">
					<el-form-item label="测试步骤" class="step-form-item">
						<StepManager v-model="form.steps" />
					</el-form-item>
				</el-col>
			</el-row>
		</el-form>

		<template #footer>
			<el-button @click="handleClose">取消</el-button>
			<el-button type="primary" @click="handleSubmit" :loading="loading">确定</el-button>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { createTestCase, updateTestCase, getTestCaseDetail } from '/@/api/v1/testcases';
import { getModuleList } from '/@/api/v1/modules';
import StepManager from './StepManager.vue';

const props = defineProps({
	modelValue: {
		type: Boolean,
		default: false,
	},
	projectId: {
		type: Number,
		required: true,
	},
	projectName: {
		type: String,
		default: '',
	},
	testcaseId: {
		type: Number,
		default: null,
	},
});

const emit = defineEmits(['update:modelValue', 'success']);

const formRef = ref();
const loading = ref(false);
const moduleList = ref<any[]>([]);

const form = reactive({
	title: '',
	description: '',
	preconditions: '',
	expected_result: '',
	priority: 'medium',
	status: 'draft',
	test_type: 'functional',
	tags: [] as string[],
	steps: [] as any[],
	module_id: null as number | null,
});

const rules = {
	title: [{ required: true, message: '请输入用例标题', trigger: 'blur' }],
	priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
	status: [{ required: true, message: '请选择状态', trigger: 'change' }],
	test_type: [{ required: true, message: '请选择测试类型', trigger: 'change' }],
};

// 获取模块列表
const getModules = async () => {
	if (!props.projectId) return;
	
	try {
		const res = await getModuleList({ project_id: props.projectId, page: 1, page_size: 100 });
		if (res.code === 200) {
			moduleList.value = res.data.items || [];
		}
	} catch (error) {
		console.error('获取模块列表失败:', error);
	}
};

// 获取详情
const getDetail = async () => {
	if (!props.testcaseId) return;

	loading.value = true;
	try {
		const res = await getTestCaseDetail(props.testcaseId);
		
		if (res.code === 200) {
			const detailData = res.data;
			
			// 分别赋值，避免响应式问题
			form.title = detailData.title;
			form.description = detailData.description || '';
			form.preconditions = detailData.preconditions || '';
			form.expected_result = detailData.expected_result || '';
			form.priority = detailData.priority;
			form.status = detailData.status;
			form.test_type = detailData.test_type;
			form.tags = detailData.tags || [];
			form.module_id = detailData.module_id || null;
			// 使用扩展运算符复制数组
			form.steps = detailData.steps ? [...detailData.steps] : [];
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
		
		// 过滤掉空步骤（action和expected都为空的步骤）
		if (data.steps && data.steps.length > 0) {
			data.steps = data.steps.filter((step: any) => step.action.trim() || step.expected.trim());
		}
		
		let res;

		if (props.testcaseId) {
			res = await updateTestCase(props.testcaseId, data);
		} else {
			res = await createTestCase(props.projectId, data);
		}

		if (res.code === 200) {
			ElMessage.success(props.testcaseId ? '更新成功' : '创建成功');
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
			// 获取模块列表
			getModules();
			
			if (props.testcaseId) {
				getDetail();
			} else {
				// 重置表单
				form.title = '';
				form.description = '';
				form.preconditions = '';
				form.expected_result = '';
				form.priority = 'medium';
				form.status = 'draft';
				form.test_type = 'functional';
				form.tags = [];
				form.steps = [];
				form.module_id = null;
			}
		}
	},
	{ immediate: true }
);
</script>

<style scoped lang="scss">
.testcase-form {
	:deep(.el-form-item) {
		margin-bottom: 18px;
	}
	
	:deep(.el-row) {
		row-gap: 8px;
	}
	
	:deep(.step-form-item) {
		margin-top: 10px;
		
		.el-form-item__content {
			line-height: normal;
		}
	}
}

.project-info {
	padding: 12px 16px;
	margin-bottom: 20px;
	background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
	border-radius: 8px;
	box-shadow: 0 2px 8px rgba(79, 172, 254, 0.15);
	
	.project-label {
		font-size: 14px;
		color: rgba(255, 255, 255, 0.9);
		font-weight: 500;
	}
	
	.project-name {
		font-size: 15px;
		color: #ffffff;
		font-weight: 600;
		margin-left: 4px;
	}
}
</style>
