<template>
	<el-dialog
		v-model="visible"
		title="创建评审"
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
					<el-form-item label="项目" prop="project_id">
						<el-select v-model="form.project_id" placeholder="选择项目" style="width: 100%">
							<el-option
								v-for="project in projects"
								:key="project.id"
								:label="project.name"
								:value="project.id"
							/>
						</el-select>
					</el-form-item>
				</el-col>
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

			<el-row :gutter="20">
				<el-col :span="12">
					<el-form-item label="截止日期">
						<el-date-picker
							v-model="form.deadline"
							type="datetime"
							placeholder="选择截止日期"
							style="width: 100%"
						/>
					</el-form-item>
				</el-col>
				<el-col :span="12">
					<el-form-item label="评审模板">
						<el-select v-model="form.template_id" placeholder="选择模板（可选）" clearable style="width: 100%">
							<el-option
								v-for="template in templates"
								:key="template.id"
								:label="template.name"
								:value="template.id"
							/>
						</el-select>
					</el-form-item>
				</el-col>
			</el-row>

			<el-form-item label="选择模块">
				<el-select
					v-model="form.module_ids"
					multiple
					placeholder="请先选择项目，然后选择要评审的模块"
					style="width: 100%"
					:disabled="!form.project_id"
					filterable
				>
					<el-option
						v-for="module in modules"
						:key="module.id"
						:label="`${module.name} (${module.testcase_count || 0}个用例)`"
						:value="module.id"
					/>
				</el-select>
				<div v-if="!form.project_id" class="form-tip">
					请先选择项目以加载模块列表
				</div>
				<div v-else-if="!modules.length" class="form-tip">
					该项目暂无模块
				</div>
				<div v-else class="form-tip">
					选择模块后，系统将自动包含模块下的所有测试用例进行评审
				</div>
			</el-form-item>

			<el-form-item label="评审人员">
				<el-select
					v-model="form.reviewer_ids"
					multiple
					placeholder="选择评审人员"
					style="width: 100%"
				>
					<el-option
						v-for="user in users"
						:key="user.id"
						:label="user.nickname || user.username"
						:value="user.id"
					/>
				</el-select>
			</el-form-item>
		</el-form>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="handleClose">取消</el-button>
				<el-button type="primary" :loading="loading" @click="handleSubmit">
					创建
				</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { createReview, getTemplateList } from '/@/api/v1/reviews';
import { getProjectList } from '/@/api/v1/project';
import { getTestCaseList } from '/@/api/v1/testcases';
import { getModuleList } from '/@/api/v1/modules';
import { useUserApi } from '/@/api/v1/system/user';

// Props
interface Props {
	modelValue: boolean;
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
const projects = ref<any[]>([]);
const templates = ref<any[]>([]);
const modules = ref<any[]>([]);
const users = ref<any[]>([]);

// 表单数据
const form = reactive({
	project_id: undefined,
	title: '',
	description: '',
	priority: 'medium',
	deadline: '',
	template_id: undefined,
	module_ids: [] as number[], // 改为选择模块ID列表
	reviewer_ids: [] as number[],
});

// 表单验证规则
const rules: FormRules = {
	project_id: [
		{ required: true, message: '请选择项目', trigger: 'change' }
	],
	title: [
		{ required: true, message: '请输入评审标题', trigger: 'blur' },
		{ min: 2, max: 100, message: '标题长度在 2 到 100 个字符', trigger: 'blur' }
	],
	priority: [
		{ required: true, message: '请选择优先级', trigger: 'change' }
	],
};

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	(val) => {
		visible.value = val;
		if (val) {
			resetForm();
			loadData();
		}
	}
);

// 监听 visible 变化
watch(visible, (val) => {
	emit('update:modelValue', val);
});

// 重置表单
const resetForm = () => {
	form.project_id = undefined;
	form.title = '';
	form.description = '';
	form.priority = 'medium';
	form.deadline = '';
	form.template_id = undefined;
	form.module_ids = [];
	form.reviewer_ids = [];
	formRef.value?.clearValidate();
};

// 加载数据
const loadData = async () => {
	try {
		// 加载项目列表
		const projectResponse = await getProjectList({ page: 1, page_size: 100 });
		if (projectResponse.code === 200) {
			projects.value = projectResponse.data.rows || [];
		}
		
		// 加载用户列表
		const userApi = useUserApi();
		const userResponse = await userApi.getList({ page: 1, page_size: 100 });
		if (userResponse.code === 200) {
			users.value = userResponse.data.rows || [];
		}
		
		// 加载评审模板列表
		const templateResponse = await getTemplateList({ page: 1, page_size: 100 });
		if (templateResponse.code === 200) {
			templates.value = templateResponse.data.rows || [];
		}
	} catch (error) {
		console.error('加载数据失败:', error);
	}
};

// 当项目改变时，只加载模块列表
const loadModules = async (projectId: number) => {
	if (!projectId) {
		modules.value = [];
		return;
	}
	
	try {
		// 只加载模块列表，不加载测试用例
		const moduleResponse = await getModuleList({ 
			project_id: projectId, 
			page: 1, 
			page_size: 1000 
		});
		
		if (moduleResponse.code === 200) {
			modules.value = moduleResponse.data.items || [];
		}
	} catch (error) {
		console.error('加载模块失败:', error);
		modules.value = [];
	}
};

// 根据模块ID获取模块名称
const getModuleName = (moduleId: number) => {
	const module = modules.value.find(m => m.id === moduleId);
	return module ? module.name : '未分配模块';
};

// 监听项目选择变化
watch(() => form.project_id, (newProjectId) => {
	if (newProjectId) {
		loadModules(newProjectId);
		// 清空已选择的模块
		form.module_ids = [];
	} else {
		modules.value = [];
		form.module_ids = [];
	}
});

// 处理关闭
const handleClose = () => {
	visible.value = false;
};

// 处理提交
const handleSubmit = async () => {
	if (!formRef.value) return;
	
	try {
		await formRef.value.validate();
		
		loading.value = true;
		
		const data = {
			...form,
			deadline: form.deadline ? new Date(form.deadline).toISOString() : undefined,
		};
		
		const response = await createReview(data);
		if (response.code === 200) {
			ElMessage.success('创建评审成功');
			emit('success');
			handleClose();
		}
	} catch (error) {
		console.error('创建评审失败:', error);
		ElMessage.error('创建评审失败');
	} finally {
		loading.value = false;
	}
};

// 组件挂载时初始化
onMounted(() => {
	if (props.modelValue) {
		visible.value = true;
		loadData();
	}
});
</script>

<style scoped>
.dialog-footer {
	text-align: right;
}

.form-tip {
	font-size: 12px;
	color: #909399;
	margin-top: 5px;
}

/* 增加表单项之间的间距 */
.el-form-item {
	margin-bottom: 38px; /* 调整到38px */
}

/* 调整行间距 - 增加行与行之间的间距 */
.el-row {
	margin-bottom: 18px; /* 增加行间距 */
}

/* 行内的表单项间距 */
.el-row .el-col .el-form-item {
	margin-bottom: 38px;
}

/* 最后一个表单项不需要额外间距 */
.el-form-item:last-child {
	margin-bottom: 0;
}

/* 确保错误提示有足够空间显示 */
.el-form-item .el-form-item__error {
	position: static;
	margin-top: 6px;
	line-height: 1.5;
	word-wrap: break-word;
	white-space: normal;
}

/* 调整弹窗高度以适应内容 */
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