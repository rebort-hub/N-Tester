<template>
	<div class="assistant-conversations-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><ChatLineRound /></el-icon>
						对话管理
					</h2>
					<p class="page-description">管理AI助手的对话记录，查看聊天历史和统计信息</p>
				</div>
				<div class="header-right">
					<el-button type="primary" @click="showCreateDialog">
						<el-icon><Plus /></el-icon>
						新建对话
					</el-button>
					<el-button @click="loadConversations">
						<el-icon><Refresh /></el-icon>
						刷新
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 筛选条件 -->
		<el-card shadow="hover" class="filter-card">
			<el-form :model="filters" inline>
				<el-form-item label="助手配置">
					<el-select v-model="filters.assistant_config_id" placeholder="全部配置" clearable @change="loadConversations" style="width: 180px">
						<el-option 
							v-for="config in assistantConfigs" 
							:key="config.id" 
							:label="config.name" 
							:value="config.id" 
						/>
					</el-select>
				</el-form-item>
				<el-form-item label="搜索">
					<el-input
						v-model="filters.keyword"
						placeholder="搜索对话标题"
						@keyup.enter="loadConversations"
						style="width: 200px"
					>
						<template #append>
							<el-button @click="loadConversations">
								<el-icon><Search /></el-icon>
							</el-button>
						</template>
					</el-input>
				</el-form-item>
			</el-form>
		</el-card>

		<!-- 对话列表 -->
		<el-card shadow="hover" class="table-card">
			<el-table
				v-loading="loading"
				:data="conversations"
				stripe
				style="width: 100%"
			>
				<el-table-column prop="title" label="对话标题" min-width="200" show-overflow-tooltip />
				<el-table-column prop="assistant_config_name" label="助手配置" width="120" show-overflow-tooltip />
				<el-table-column prop="message_count" label="消息数量" width="80" align="center">
					<template #default="{ row }">
						<el-tag type="info">{{ row.message_count || 0 }}</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="last_message_time" label="最后消息" width="140">
					<template #default="{ row }">
						{{ formatDateTime(row.last_message_time || row.updated_at) }}
					</template>
				</el-table-column>
				<el-table-column prop="created_at" label="创建时间" width="140">
					<template #default="{ row }">
						{{ formatDateTime(row.created_at) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="320" fixed="right">
					<template #default="{ row }">
						<div class="action-buttons">
							<el-button size="small" @click="viewMessages(row)">查看消息</el-button>
							<el-button size="small" type="primary" @click="continueChat(row)">继续对话</el-button>
							<el-button size="small" type="warning" @click="editConversation(row)">编辑</el-button>
							<el-button 
								size="small" 
								type="danger" 
								@click="deleteConversation(row)"
							>
								删除
							</el-button>
						</div>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<div class="pagination-container">
				<el-pagination
					v-model:current-page="pagination.page"
					v-model:page-size="pagination.pageSize"
					:total="pagination.total"
					:page-sizes="[10, 20, 50, 100]"
					layout="total, sizes, prev, pager, next, jumper"
					@size-change="loadConversations"
					@current-change="loadConversations"
				/>
			</div>
		</el-card>

		<!-- 创建/编辑对话对话框 -->
		<el-dialog
			v-model="dialogVisible"
			:title="dialogMode === 'create' ? '新建对话' : '编辑对话'"
			width="500px"
			@close="resetForm"
		>
			<el-form
				ref="formRef"
				:model="formData"
				:rules="formRules"
				label-width="100px"
			>
				<el-form-item label="对话标题" prop="title">
					<el-input v-model="formData.title" placeholder="请输入对话标题" />
				</el-form-item>
				<el-form-item label="助手配置" prop="assistant_config_id">
					<el-select v-model="formData.assistant_config_id" placeholder="请选择助手配置" style="width: 100%">
						<el-option 
							v-for="config in assistantConfigs" 
							:key="config.id" 
							:label="config.name" 
							:value="config.id" 
						/>
					</el-select>
				</el-form-item>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="dialogVisible = false">取消</el-button>
					<el-button type="primary" @click="submitForm">确定</el-button>
				</span>
			</template>
		</el-dialog>

		<!-- 消息查看对话框 -->
		<el-dialog
			v-model="messagesDialogVisible"
			:title="`对话消息 - ${currentConversation.title}`"
			width="800px"
			@close="resetMessages"
		>
			<div class="messages-container">
				<div v-if="messages.length === 0" class="no-messages">
					<el-empty description="暂无消息记录" />
				</div>
				<div v-else class="message-list">
					<div 
						v-for="message in messages" 
						:key="message.id" 
						:class="['message-item', message.role]"
					>
						<div class="message-avatar">
							<el-icon v-if="message.role === 'user'">
								<User />
							</el-icon>
							<el-icon v-else>
								<Avatar />
							</el-icon>
						</div>
						<div class="message-content">
							<div class="message-text">{{ message.content }}</div>
							<div class="message-time">{{ formatDateTime(message.created_at) }}</div>
						</div>
					</div>
				</div>
			</div>
			<div v-if="messagesLoading" class="messages-loading">
				<el-loading text="加载消息中..." />
			</div>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { ChatLineRound, Plus, Refresh, Search, User, Avatar } from '@element-plus/icons-vue';
import { 
	getConversationList, 
	createConversation, 
	updateConversation, 
	deleteConversation as deleteConversationApi,
	getConversationMessages,
	getConfigList,
	type Conversation,
	type AssistantConfig,
	type Message
} from '/@/api/v1/assistant';

// 响应式数据
const router = useRouter();
const loading = ref(false);
const messagesLoading = ref(false);
const conversations = ref<Conversation[]>([]);
const messages = ref<Message[]>([]);
const assistantConfigs = ref<AssistantConfig[]>([]);
const dialogVisible = ref(false);
const messagesDialogVisible = ref(false);
const dialogMode = ref<'create' | 'edit'>('create');

// 筛选条件
const filters = reactive({
	assistant_config_id: undefined as number | undefined,
	keyword: '',
});

// 分页数据
const pagination = reactive({
	page: 1,
	pageSize: 20,
	total: 0,
});

// 表单数据
const formRef = ref();
const formData = reactive({
	id: 0,
	title: '',
	assistant_config_id: undefined as number | undefined,
});

// 当前对话
const currentConversation = reactive({
	id: 0,
	title: '',
});

// 表单验证规则
const formRules = {
	title: [
		{ required: true, message: '请输入对话标题', trigger: 'blur' },
		{ min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur' }
	],
	assistant_config_id: [
		{ required: true, message: '请选择助手配置', trigger: 'change' }
	],
};

// 加载助手配置
const loadAssistantConfigs = async () => {
	try {
		const response = await getConfigList({
			page: 1,
			page_size: 100,
			is_active: true,
		});
		
		if (response.code === 200) {
			assistantConfigs.value = response.data.items || [];
		}
	} catch (error) {
		console.error('加载助手配置失败:', error);
	}
};

// 加载对话列表
const loadConversations = async () => {
	loading.value = true;
	try {
		const response = await getConversationList({
			page: pagination.page,
			page_size: pagination.pageSize,
		});
		
		if (response.code === 200) {
			conversations.value = response.data.items || [];
			pagination.total = response.data.total || 0;
			
			// 补充助手配置名称
			conversations.value.forEach(conv => {
				const config = assistantConfigs.value.find(c => c.id === conv.assistant_config_id);
				conv.assistant_config_name = config?.name || '未知配置';
			});
		} else {
			ElMessage.error(response.message || '加载对话列表失败');
		}
		
	} catch (error) {
		console.error('加载对话列表失败:', error);
		ElMessage.error('加载对话列表失败');
	} finally {
		loading.value = false;
	}
};

// 显示创建对话框
const showCreateDialog = () => {
	dialogMode.value = 'create';
	resetForm();
	dialogVisible.value = true;
};

// 编辑对话
const editConversation = (conversation: Conversation) => {
	dialogMode.value = 'edit';
	Object.assign(formData, {
		id: conversation.id,
		title: conversation.title,
		assistant_config_id: conversation.assistant_config_id,
	});
	dialogVisible.value = true;
};

// 查看消息
const viewMessages = async (conversation: Conversation) => {
	Object.assign(currentConversation, {
		id: conversation.id,
		title: conversation.title,
	});
	
	messagesDialogVisible.value = true;
	messagesLoading.value = true;
	
	try {
		const response = await getConversationMessages(conversation.id, {
			page: 1,
			page_size: 100,
		});
		
		if (response.code === 200) {
			messages.value = response.data.items || [];
		} else {
			ElMessage.error(response.message || '加载消息失败');
		}
	} catch (error) {
		console.error('加载消息失败:', error);
		ElMessage.error('加载消息失败');
	} finally {
		messagesLoading.value = false;
	}
};

// 继续对话
const continueChat = (conversation: Conversation) => {
	// 跳转到助手管理页面并开始对话
	router.push({
		path: '/assistant/index',
		query: { conversation_id: conversation.id }
	});
};

// 删除对话
const deleteConversation = async (conversation: Conversation) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除对话"${conversation.title}"吗？此操作将同时删除所有相关消息，且不可恢复。`,
			'确认删除',
			{
				confirmButtonText: '删除',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		
		const response = await deleteConversationApi(conversation.id);
		
		if (response.code === 200) {
			ElMessage.success('删除对话成功');
			loadConversations();
		} else {
			ElMessage.error(response.message || '删除对话失败');
		}
		
	} catch (error) {
		if (error !== 'cancel') {
			console.error('删除对话失败:', error);
			ElMessage.error('删除对话失败');
		}
	}
};

// 提交表单
const submitForm = async () => {
	try {
		await formRef.value.validate();
		
		const apiCall = dialogMode.value === 'create' ? createConversation : updateConversation;
		const params = dialogMode.value === 'create' ? formData : [formData.id, formData];
		
		const response = await apiCall(...(Array.isArray(params) ? params : [params]));
		
		if (response.code === 200) {
			ElMessage.success(`${dialogMode.value === 'create' ? '创建' : '更新'}对话成功`);
			dialogVisible.value = false;
			loadConversations();
		} else {
			ElMessage.error(response.message || `${dialogMode.value === 'create' ? '创建' : '更新'}对话失败`);
		}
		
	} catch (error) {
		console.error('提交表单失败:', error);
		ElMessage.error('提交表单失败');
	}
};

// 重置表单
const resetForm = () => {
	Object.assign(formData, {
		id: 0,
		title: '',
		assistant_config_id: undefined,
	});
	formRef.value?.resetFields();
};

// 重置消息
const resetMessages = () => {
	messages.value = [];
	Object.assign(currentConversation, {
		id: 0,
		title: '',
	});
};

// 格式化日期时间
const formatDateTime = (date: string) => {
	if (!date) return '-';
	const d = new Date(date);
	const year = d.getFullYear();
	const month = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	const hours = String(d.getHours()).padStart(2, '0');
	const minutes = String(d.getMinutes()).padStart(2, '0');
	const seconds = String(d.getSeconds()).padStart(2, '0');
	return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

// 组件挂载时加载数据
onMounted(async () => {
	await loadAssistantConfigs();
	await loadConversations();
});
</script>

<style scoped>
.assistant-conversations-container {
	padding: 20px;
}

.page-header-card {
	margin-bottom: 20px;
}

.page-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-left {
	flex: 1;
}

.page-title {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0 0 8px 0;
	font-size: 24px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.page-description {
	margin: 0;
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.filter-card {
	margin-bottom: 20px;
}

.table-card {
	margin-bottom: 20px;
}

.pagination-container {
	display: flex;
	justify-content: center;
	margin-top: 20px;
}

.messages-container {
	max-height: 500px;
	overflow-y: auto;
}

.no-messages {
	text-align: center;
	padding: 40px 0;
}

.message-list {
	padding: 10px 0;
}

.message-item {
	display: flex;
	margin-bottom: 20px;
	align-items: flex-start;
}

.message-item.user {
	flex-direction: row-reverse;
}

.message-item.user .message-content {
	margin-right: 12px;
	margin-left: 0;
}

.message-item.assistant .message-content {
	margin-left: 12px;
}

.message-avatar {
	width: 40px;
	height: 40px;
	border-radius: 50%;
	background: var(--el-color-primary-light-9);
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.message-item.user .message-avatar {
	background: var(--el-color-success-light-9);
}

.message-content {
	flex: 1;
	max-width: calc(100% - 60px);
}

.message-text {
	background: var(--el-bg-color-page);
	padding: 12px 16px;
	border-radius: 12px;
	word-wrap: break-word;
	white-space: pre-wrap;
	line-height: 1.5;
}

.message-item.user .message-text {
	background: var(--el-color-primary-light-9);
}

.message-time {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	margin-top: 4px;
	text-align: right;
}

.message-item.assistant .message-time {
	text-align: left;
}

.messages-loading {
	text-align: center;
	padding: 20px;
}

.action-buttons {
	display: flex;
	gap: 6px;
	flex-wrap: nowrap;
	align-items: center;
	min-width: 300px;
	justify-content: flex-start;
}

.action-buttons .el-button {
	flex-shrink: 0;
	white-space: nowrap;
	padding: 8px 12px; /* 稍微减少按钮内边距 */
}

.table-card {
	margin-bottom: 20px;
}

.table-card .el-table {
	min-width: 1060px; /* 调整最小宽度：200+120+80+140+140+320+60(边距) */
}
</style>