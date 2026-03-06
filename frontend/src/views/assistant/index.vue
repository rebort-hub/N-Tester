<template>
	<div class="assistant-container">
		<!-- 页面头部 -->
		<el-card shadow="hover" class="page-header-card">
			<div class="page-header">
				<div class="header-left">
					<h2 class="page-title">
						<el-icon><ChatDotRound /></el-icon>
						AI助手
					</h2>
					<p class="page-description">智能AI助手，提供测试相关的智能对话服务</p>
				</div>
				<div class="header-right">
					<el-button type="primary" @click="showConfigDialog = true">
						<el-icon><Plus /></el-icon>
						新建助手
					</el-button>
					<el-button @click="showStatistics = true">
						<el-icon><DataAnalysis /></el-icon>
						统计信息
					</el-button>
					<el-button @click="$router.push('/assistant/configs')">
						<el-icon><Setting /></el-icon>
						配置管理
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 助手配置列表 -->
		<el-row :gutter="20" class="configs-grid">
			<el-col
				v-for="config in configs"
				:key="config.id"
				:span="8"
				class="config-col"
			>
				<el-card shadow="hover" class="config-card" @click="startChat(config)">
					<div class="config-content">
						<div class="config-header">
							<div class="config-icon">
								<el-icon :size="32">
									<component :is="getTypeIcon(config.assistant_type)" />
								</el-icon>
							</div>
							<div class="config-info">
								<h3 class="config-name">{{ config.name }}</h3>
								<p class="config-type">{{ getTypeText(config.assistant_type) }}</p>
							</div>
							<div class="config-status">
								<el-tag :type="config.is_active ? 'success' : 'info'" size="small">
									{{ config.is_active ? '启用' : '禁用' }}
								</el-tag>
							</div>
						</div>
						<div class="config-actions">
							<el-button size="small" type="primary" @click.stop="startChat(config)">
								<el-icon><ChatDotRound /></el-icon>
								开始对话
							</el-button>
							<el-button size="small" @click.stop="editConfig(config)">
								<el-icon><Edit /></el-icon>
								编辑
							</el-button>
							<el-button size="small" type="danger" @click.stop="deleteConfig(config)">
								<el-icon><Delete /></el-icon>
								删除
							</el-button>
						</div>
					</div>
				</el-card>
			</el-col>
		</el-row>

		<!-- 最近对话 -->
		<el-card shadow="hover" class="conversations-card">
			<template #header>
				<div class="card-header">
					<span>最近对话</span>
					<el-button size="small" @click="$router.push('/assistant/conversations')">
						查看全部
					</el-button>
				</div>
			</template>
			<el-table :data="recentConversations" style="width: 100%">
				<el-table-column prop="title" label="对话标题" min-width="200">
					<template #default="{ row }">
						<el-link type="primary" @click="openConversation(row.id)">
							{{ row.title || '未命名对话' }}
						</el-link>
					</template>
				</el-table-column>
				<el-table-column prop="assistant_config.name" label="助手" width="150" />
				<el-table-column prop="message_count" label="消息数" width="100" />
				<el-table-column prop="last_message_time" label="最后活动" width="160">
					<template #default="{ row }">
						{{ formatDateTime(row.last_message_time || row.updated_at) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="150">
					<template #default="{ row }">
						<el-button size="small" @click="openConversation(row.id)">继续对话</el-button>
						<el-button size="small" type="danger" @click="deleteConversation(row)">删除</el-button>
					</template>
				</el-table-column>
			</el-table>
		</el-card>

		<!-- 配置对话框 -->
		<ConfigDialog
			v-model="showConfigDialog"
			:config="currentConfig"
			@success="loadConfigs"
		/>

		<!-- 统计信息对话框 -->
		<StatisticsDialog
			v-model="showStatistics"
		/>

		<!-- 聊天对话框 -->
		<ChatDialog
			v-model="showChatDialog"
			:config="selectedConfig"
			:conversation-id="selectedConversationId"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
	ChatDotRound, 
	Plus, 
	DataAnalysis, 
	Setting, 
	Edit, 
	Delete,
	Avatar,
	Connection,
	User
} from '@element-plus/icons-vue';
import { 
	getConfigList, 
	deleteConfig as deleteConfigApi, 
	getConversationList,
	deleteConversation as deleteConversationApi,
	type AssistantConfig,
	type Conversation 
} from '/@/api/v1/assistant';
import ConfigDialog from './components/ConfigDialog.vue';
import StatisticsDialog from './components/StatisticsDialog.vue';
import ChatDialog from './components/ChatDialog.vue';

// 响应式数据
const route = useRoute();
const loading = ref(false);
const configs = ref<AssistantConfig[]>([]);
const recentConversations = ref<Conversation[]>([]);
const showConfigDialog = ref(false);
const showStatistics = ref(false);
const showChatDialog = ref(false);
const currentConfig = ref<AssistantConfig | null>(null);
const selectedConfig = ref<AssistantConfig | null>(null);
const selectedConversationId = ref<number | undefined>(undefined);

// 加载助手配置列表
const loadConfigs = async () => {
	loading.value = true;
	try {
		const response = await getConfigList({ page: 1, page_size: 50 });
		if (response.code === 200) {
			configs.value = response.data.items || [];
		}
	} catch (error) {
		console.error('加载助手配置失败:', error);
		ElMessage.error('加载助手配置失败');
	} finally {
		loading.value = false;
	}
};

// 加载最近对话
const loadRecentConversations = async () => {
	try {
		const response = await getConversationList({ page: 1, page_size: 10 });
		if (response.code === 200) {
			recentConversations.value = response.data.items || [];
		}
	} catch (error) {
		console.error('加载最近对话失败:', error);
	}
};

// 开始聊天
const startChat = (config: AssistantConfig) => {
	if (!config.is_active) {
		ElMessage.warning('该助手已禁用，无法开始对话');
		return;
	}
	selectedConfig.value = config;
	selectedConversationId.value = undefined; // 新对话
	showChatDialog.value = true;
};

// 编辑配置
const editConfig = (config: AssistantConfig) => {
	currentConfig.value = config;
	showConfigDialog.value = true;
};

// 删除配置
const deleteConfig = async (config: AssistantConfig) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除助手"${config.name}"吗？`,
			'确认删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);

		const response = await deleteConfigApi(config.id);
		if (response.code === 200) {
			ElMessage.success('删除成功');
			loadConfigs();
		}
	} catch (error) {
		if (error !== 'cancel') {
			console.error('删除助手配置失败:', error);
			ElMessage.error('删除助手配置失败');
		}
	}
};

// 打开对话
const openConversation = (conversationId: number) => {
	// 找到对应的助手配置
	const conversation = recentConversations.value.find(c => c.id === conversationId);
	if (conversation) {
		const config = configs.value.find(c => c.id === conversation.assistant_config_id);
		if (config) {
			selectedConfig.value = config;
			selectedConversationId.value = conversationId; // 现有对话
			showChatDialog.value = true;
		}
	}
};

// 删除对话
const deleteConversation = async (conversation: Conversation) => {
	try {
		await ElMessageBox.confirm(
			`确定要删除对话"${conversation.title || '未命名对话'}"吗？`,
			'确认删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);

		const response = await deleteConversationApi(conversation.id);
		if (response.code === 200) {
			ElMessage.success('删除成功');
			loadRecentConversations();
		}
	} catch (error) {
		if (error !== 'cancel') {
			console.error('删除对话失败:', error);
			ElMessage.error('删除对话失败');
		}
	}
};

// 获取类型图标
const getTypeIcon = (type: string) => {
	const icons: Record<string, any> = {
		chatbot: ChatDotRound,
		workflow: Connection,
		agent: Avatar,
	};
	return icons[type] || ChatDotRound;
};

// 获取类型文本
const getTypeText = (type: string) => {
	const texts: Record<string, string> = {
		chatbot: '聊天机器人',
		workflow: '工作流',
		agent: '智能代理',
	};
	return texts[type] || type;
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
	await loadConfigs();
	await loadRecentConversations();
	
	// 检查是否有conversation_id参数，如果有则自动打开对话
	const conversationId = route.query.conversation_id;
	if (conversationId) {
		const id = parseInt(conversationId as string);
		if (!isNaN(id)) {
			openConversation(id);
		}
	}
});
</script>

<style scoped>
.assistant-container {
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
	color: #303133;
}

.page-description {
	margin: 0;
	color: #909399;
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.configs-grid {
	margin-bottom: 30px;
}

.config-col {
	margin-bottom: 20px;
}

.config-card {
	height: 180px;
	cursor: pointer;
	transition: all 0.3s ease;
}

.config-card:hover {
	transform: translateY(-2px);
	box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.config-content {
	height: 100%;
	display: flex;
	flex-direction: column;
	justify-content: space-between;
}

.config-header {
	display: flex;
	align-items: flex-start;
	gap: 12px;
}

.config-icon {
	width: 50px;
	height: 50px;
	border-radius: 50%;
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	display: flex;
	align-items: center;
	justify-content: center;
	color: white;
	flex-shrink: 0;
}

.config-info {
	flex: 1;
}

.config-name {
	margin: 0 0 5px 0;
	font-size: 16px;
	font-weight: 600;
	color: #303133;
}

.config-type {
	margin: 0;
	font-size: 14px;
	color: #909399;
}

.config-status {
	flex-shrink: 0;
}

.config-actions {
	display: flex;
	gap: 8px;
	margin-top: 15px;
}

.conversations-card {
	margin-bottom: 20px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-weight: 600;
	color: #303133;
}
</style>