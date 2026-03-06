<template>
	<el-dialog
		v-model="visible"
		:title="isEdit ? '编辑评审模板' : '创建评审模板'"
		width="700px"
		:before-close="handleClose"
	>
		<el-form
			ref="formRef"
			:model="form"
			:rules="rules"
			label-width="120px"
		>
			<el-form-item label="模板名称" prop="name">
				<el-input v-model="form.name" placeholder="请输入模板名称" />
			</el-form-item>

			<el-form-item label="模板描述">
				<el-input
					v-model="form.description"
					type="textarea"
					:rows="3"
					placeholder="请输入模板描述"
				/>
			</el-form-item>

			<el-form-item label="检查清单" prop="checklist">
				<div class="checklist-container">
					<div
						v-for="(item, index) in checklistItems"
						:key="index"
						class="checklist-item"
					>
						<el-input
							v-model="item.title"
							placeholder="检查项标题"
							style="margin-bottom: 8px"
						/>
						<el-input
							v-model="item.description"
							type="textarea"
							:rows="2"
							placeholder="检查项描述"
							style="margin-bottom: 8px"
						/>
						<div class="checklist-actions">
							<el-button size="small" type="danger" @click="removeChecklistItem(index)">
								删除
							</el-button>
						</div>
					</div>
					<el-button type="primary" plain @click="addChecklistItem">
						<el-icon><Plus /></el-icon>
						添加检查项
					</el-button>
				</div>
			</el-form-item>

			<el-form-item label="关联项目">
				<el-select
					v-model="form.project_ids"
					multiple
					placeholder="选择关联项目（可选）"
					style="width: 100%"
				>
					<el-option
						v-for="project in projects"
						:key="project.id"
						:label="project.name"
						:value="project.id"
					/>
				</el-select>
			</el-form-item>

			<el-form-item label="默认评审人">
				<el-select
					v-model="form.default_reviewer_ids"
					multiple
					placeholder="选择默认评审人（可选）"
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

			<el-form-item label="启用状态" v-if="isEdit">
				<el-switch v-model="form.is_active" />
			</el-form-item>
		</el-form>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="handleClose">取消</el-button>
				<el-button type="primary" :loading="loading" @click="handleSubmit">
					{{ isEdit ? '更新' : '创建' }}
				</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { createTemplate, updateTemplate, getTemplateDetail, type ReviewTemplate } from '/@/api/v1/reviews';
import { getProjectList } from '/@/api/v1/project';
import { useUserApi } from '/@/api/v1/system/user';

// Props
interface Props {
	modelValue: boolean;
	template?: ReviewTemplate | null;
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
const users = ref<any[]>([]);

// 计算属性
const isEdit = computed(() => !!props.template);

// 检查清单项
interface ChecklistItem {
	title: string;
	description: string;
}

const checklistItems = ref<ChecklistItem[]>([
	{ title: '', description: '' }
]);

// 表单数据
const form = reactive({
	name: '',
	description: '',
	checklist: {},
	project_ids: [] as number[],
	default_reviewer_ids: [] as number[],
	is_active: true,
});

// 表单验证规则
const rules: FormRules = {
	name: [
		{ required: true, message: '请输入模板名称', trigger: 'blur' },
		{ min: 2, max: 100, message: '名称长度在 2 到 100 个字符', trigger: 'blur' }
	],
};

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	async (val) => {
		visible.value = val;
		if (val) {
			resetForm();
			loadData();
			if (props.template) {
				await loadTemplateData();
			}
		}
	}
);

// 监听 visible 变化
watch(visible, (val) => {
	emit('update:modelValue', val);
});

// 重置表单
const resetForm = () => {
	form.name = '';
	form.description = '';
	form.checklist = {};
	form.project_ids = [];
	form.default_reviewer_ids = [];
	form.is_active = true;
	checklistItems.value = [{ title: '', description: '' }];
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
	} catch (error) {
		console.error('加载数据失败:', error);
		ElMessage.error('加载数据失败');
	}
};

// 加载模板数据
const loadTemplateData = async () => {
	if (props.template) {
		try {
			// 获取完整的模板详情，包括关联的项目和评审人
			const response = await getTemplateDetail(props.template.id);
			if (response.code === 200) {
				const templateData = response.data;
				
				form.name = templateData.name;
				form.description = templateData.description || '';
				form.is_active = templateData.is_active;
				form.project_ids = templateData.project_ids || [];
				form.default_reviewer_ids = templateData.default_reviewer_ids || [];
				
				// 解析检查清单
				if (templateData.checklist && typeof templateData.checklist === 'object') {
					const checklist = templateData.checklist as any;
					if (checklist.items && Array.isArray(checklist.items)) {
						checklistItems.value = checklist.items.map((item: any) => ({
							title: item.title || '',
							description: item.description || '',
						}));
					} else {
						checklistItems.value = [{ title: '', description: '' }];
					}
				} else {
					checklistItems.value = [{ title: '', description: '' }];
				}
			}
		} catch (error) {
			console.error('加载模板详情失败:', error);
			ElMessage.error('加载模板详情失败');
			
			// 如果加载失败，使用传入的基本数据
			form.name = props.template.name;
			form.description = props.template.description || '';
			form.is_active = props.template.is_active;
			
			// 解析检查清单
			if (props.template.checklist && typeof props.template.checklist === 'object') {
				const checklist = props.template.checklist as any;
				if (checklist.items && Array.isArray(checklist.items)) {
					checklistItems.value = checklist.items.map((item: any) => ({
						title: item.title || '',
						description: item.description || '',
					}));
				}
			}
		}
	}
};

// 添加检查项
const addChecklistItem = () => {
	checklistItems.value.push({ title: '', description: '' });
};

// 删除检查项
const removeChecklistItem = (index: number) => {
	if (checklistItems.value.length > 1) {
		checklistItems.value.splice(index, 1);
	}
};

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
		
		// 构建检查清单
		const checklist = {
			items: checklistItems.value.filter(item => item.title.trim())
		};
		
		const data = {
			...form,
			checklist,
		};
		
		let response;
		if (isEdit.value && props.template) {
			response = await updateTemplate(props.template.id, data);
		} else {
			response = await createTemplate(data);
		}
		
		if (response.code === 200) {
			ElMessage.success(isEdit.value ? '更新模板成功' : '创建模板成功');
			emit('success');
			handleClose();
		}
	} catch (error) {
		console.error('保存模板失败:', error);
		ElMessage.error('保存模板失败');
	} finally {
		loading.value = false;
	}
};

// 组件挂载时初始化
onMounted(async () => {
	if (props.modelValue) {
		visible.value = true;
		loadData();
		if (props.template) {
			await loadTemplateData();
		}
	}
});
</script>

<style scoped>
.checklist-container {
	border: 1px solid var(--el-border-color-light);
	border-radius: 4px;
	padding: 15px;
	background: var(--el-bg-color-page);
}

.checklist-item {
	margin-bottom: 15px;
	padding: 10px;
	border: 1px solid var(--el-border-color-light);
	border-radius: 4px;
	background: var(--el-bg-color);
}

.checklist-actions {
	text-align: right;
}

.dialog-footer {
	text-align: right;
}

/* 深色主题适配 */
html.dark .checklist-container {
	background: #1d1e1f;
	border-color: #414243;
}

html.dark .checklist-item {
	background: #262727;
	border-color: #414243;
}

[data-theme="dark"] .checklist-container {
	background: #1d1e1f;
	border-color: #414243;
}

[data-theme="dark"] .checklist-item {
	background: #262727;
	border-color: #414243;
}
</style>