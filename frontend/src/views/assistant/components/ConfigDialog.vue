<template>
	<el-dialog
		v-model="visible"
		:title="isEdit ? '编辑助手配置' : '创建助手配置'"
		width="600px"
		:before-close="handleClose"
	>
		<el-form
			ref="formRef"
			:model="form"
			:rules="rules"
			label-width="120px"
		>
			<el-form-item label="助手名称" prop="name">
				<el-input v-model="form.name" placeholder="请输入助手名称" />
			</el-form-item>

			<el-form-item label="助手类型" prop="assistant_type">
				<el-select v-model="form.assistant_type" placeholder="选择助手类型" style="width: 100%">
					<el-option label="聊天机器人" value="chatbot" />
					<el-option label="工作流" value="workflow" />
					<el-option label="智能代理" value="agent" />
				</el-select>
			</el-form-item>

			<el-form-item label="Dify API Key" prop="dify_api_key">
				<el-input
					v-model="form.dify_api_key"
					type="password"
					placeholder="请输入Dify API Key"
					show-password
				/>
			</el-form-item>

			<el-form-item label="Dify Base URL" prop="dify_base_url">
				<el-input v-model="form.dify_base_url" placeholder="请输入Dify Base URL" />
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
import { createConfig, updateConfig, type AssistantConfig } from '/@/api/v1/assistant';

// Props
interface Props {
	modelValue: boolean;
	config?: AssistantConfig | null;
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

// 计算属性
const isEdit = computed(() => !!props.config);

// 表单数据
const form = reactive({
	name: '',
	assistant_type: 'chatbot',
	dify_api_key: '',
	dify_base_url: 'https://api.dify.ai',
	is_active: true,
});

// 表单验证规则
const rules: FormRules = {
	name: [
		{ required: true, message: '请输入助手名称', trigger: 'blur' },
		{ min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
	],
	assistant_type: [
		{ required: true, message: '请选择助手类型', trigger: 'change' }
	],
	dify_api_key: [
		{ required: true, message: '请输入Dify API Key', trigger: 'blur' }
	],
	dify_base_url: [
		{ required: true, message: '请输入Dify Base URL', trigger: 'blur' },
		{ type: 'url', message: '请输入有效的URL', trigger: 'blur' }
	],
};

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	(val) => {
		visible.value = val;
		if (val) {
			resetForm();
			if (props.config) {
				loadConfigData();
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
	form.assistant_type = 'chatbot';
	form.dify_api_key = '';
	form.dify_base_url = 'https://api.dify.ai';
	form.is_active = true;
	formRef.value?.clearValidate();
};

// 加载配置数据
const loadConfigData = () => {
	if (props.config) {
		form.name = props.config.name;
		form.assistant_type = props.config.assistant_type;
		form.dify_api_key = props.config.dify_api_key;
		form.dify_base_url = props.config.dify_base_url;
		form.is_active = props.config.is_active;
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
		
		let response;
		if (isEdit.value && props.config) {
			response = await updateConfig(props.config.id, form);
		} else {
			response = await createConfig(form);
		}
		
		if (response.code === 200) {
			ElMessage.success(isEdit.value ? '更新助手配置成功' : '创建助手配置成功');
			emit('success');
			handleClose();
		}
	} catch (error) {
		console.error('保存助手配置失败:', error);
		ElMessage.error('保存助手配置失败');
	} finally {
		loading.value = false;
	}
};

// 组件挂载时初始化
onMounted(() => {
	if (props.modelValue) {
		visible.value = true;
		if (props.config) {
			loadConfigData();
		}
	}
});
</script>

<style scoped>
.dialog-footer {
	text-align: right;
}
</style>