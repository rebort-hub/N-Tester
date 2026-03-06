<template>
	<el-dialog
		v-model="visible"
		:title="`与 ${config?.name} 对话`"
		width="800px"
		:before-close="handleClose"
		class="chat-dialog"
	>
		<div class="chat-container">
			<!-- 消息列表 -->
			<div ref="messagesRef" class="messages-container">
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
						<div class="message-time">{{ formatTime(message.created_at) }}</div>
					</div>
				</div>
				
				<!-- 加载中提示 -->
				<div v-if="sending" class="message-item assistant">
					<div class="message-avatar">
						<el-icon><Avatar /></el-icon>
					</div>
					<div class="message-content">
						<div class="message-text typing">
							<span></span>
							<span></span>
							<span></span>
						</div>
					</div>
				</div>
			</div>

			<!-- 输入区域 -->
			<div class="input-container">
				<el-input
					v-model="inputMessage"
					type="textarea"
					:rows="3"
					placeholder="输入您的问题..."
					:disabled="sending"
					@keydown.ctrl.enter="sendMessage"
				/>
				<div class="input-actions">
					<span class="input-tip">Ctrl + Enter 发送</span>
					<el-button
						type="primary"
						:loading="sending"
						:disabled="!inputMessage.trim()"
						@click="sendMessage"
					>
						发送
					</el-button>
				</div>
			</div>
		</div>

		<template #footer>
			<div class="dialog-footer">
				<el-button @click="clearMessages">清空对话</el-button>
				<el-button @click="handleClose">关闭</el-button>
			</div>
		</template>
	</el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { User, Avatar } from '@element-plus/icons-vue';
import { 
	chatWithDify, 
	createConversation,
	getConversationMessages,
	type AssistantConfig, 
	type Message 
} from '/@/api/v1/assistant';

// Props
interface Props {
	modelValue: boolean;
	config?: AssistantConfig | null;
	conversationId?: number; // 新增：现有对话ID
}

// Emits
interface Emits {
	(e: 'update:modelValue', value: boolean): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 响应式数据
const visible = ref(false);
const sending = ref(false);
const inputMessage = ref('');
const messages = ref<Message[]>([]);
const messagesRef = ref<HTMLDivElement>();
const currentConversationId = ref<number>();

// 监听 modelValue 变化
watch(
	() => props.modelValue,
	(val) => {
		visible.value = val;
		if (val && props.config) {
			initChat();
		}
	}
);

// 监听 visible 变化
watch(visible, (val) => {
	emit('update:modelValue', val);
});

// 初始化聊天
const initChat = async () => {
	messages.value = [];
	
	// 如果有现有对话ID，加载对话消息
	if (props.conversationId) {
		currentConversationId.value = props.conversationId;
		await loadConversationMessages();
	} else {
		// 创建新对话
		currentConversationId.value = undefined;
		if (props.config) {
			try {
				const response = await createConversation({
					assistant_config_id: props.config.id,
					title: `与${props.config.name}的对话`,
				});
				if (response.code === 200) {
					currentConversationId.value = response.data.id;
				}
			} catch (error) {
				console.error('创建对话失败:', error);
			}
		}
	}
};

// 加载对话消息
const loadConversationMessages = async () => {
	if (!currentConversationId.value) return;
	
	try {
		const response = await getConversationMessages(currentConversationId.value, {
			page: 1,
			page_size: 100,
		});
		
		if (response.code === 200) {
			messages.value = response.data.items || [];
			// 滚动到底部
			await nextTick();
			scrollToBottom();
		}
	} catch (error) {
		console.error('加载对话消息失败:', error);
		ElMessage.error('加载对话消息失败');
	}
};

// 发送消息
const sendMessage = async () => {
	if (!inputMessage.value.trim() || !props.config) return;
	
	const userMessage = inputMessage.value.trim();
	inputMessage.value = '';
	
	// 添加用户消息到列表
	const userMsg: Message = {
		id: Date.now(),
		conversation_id: currentConversationId.value || 0,
		role: 'user',
		content: userMessage,
		created_at: new Date().toISOString(),
	};
	messages.value.push(userMsg);
	
	// 滚动到底部
	await nextTick();
	scrollToBottom();
	
	// 发送到AI
	sending.value = true;
	try {
		const response = await chatWithDify({
			assistant_config_id: props.config.id,
			conversation_id: currentConversationId.value,
			message: userMessage,
		});
		
		if (response.code === 200) {
			// 添加AI回复到列表
			const aiMsg: Message = {
				id: Date.now() + 1,
				conversation_id: currentConversationId.value || 0,
				role: 'assistant',
				content: response.data.message,
				created_at: new Date().toISOString(),
			};
			messages.value.push(aiMsg);
			
			// 更新对话ID
			if (response.data.conversation_id) {
				currentConversationId.value = parseInt(response.data.conversation_id);
			}
		} else {
			ElMessage.error('发送消息失败');
		}
	} catch (error) {
		console.error('发送消息失败:', error);
		ElMessage.error('发送消息失败');
	} finally {
		sending.value = false;
		await nextTick();
		scrollToBottom();
	}
};

// 清空对话
const clearMessages = () => {
	messages.value = [];
	initChat();
};

// 滚动到底部
const scrollToBottom = () => {
	if (messagesRef.value) {
		messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
	}
};

// 格式化时间
const formatTime = (date: string) => {
	return new Date(date).toLocaleTimeString();
};

// 处理关闭
const handleClose = () => {
	visible.value = false;
};

// 组件挂载时初始化
onMounted(() => {
	if (props.modelValue && props.config) {
		visible.value = true;
		initChat();
	}
});
</script>

<style scoped>
.chat-dialog :deep(.el-dialog__body) {
	padding: 0;
}

.chat-container {
	height: 600px;
	display: flex;
	flex-direction: column;
}

.messages-container {
	flex: 1;
	overflow-y: auto;
	padding: 20px;
	background: #f5f7fa;
}

.message-item {
	display: flex;
	margin-bottom: 20px;
}

.message-item.user {
	flex-direction: row-reverse;
}

.message-item.user .message-content {
	background: #409eff;
	color: white;
	margin-right: 10px;
}

.message-item.assistant .message-content {
	background: white;
	color: #303133;
	margin-left: 10px;
}

.message-avatar {
	width: 40px;
	height: 40px;
	border-radius: 50%;
	background: #e4e7ed;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.message-content {
	max-width: 70%;
	padding: 12px 16px;
	border-radius: 12px;
	box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.message-text {
	line-height: 1.5;
	word-wrap: break-word;
}

.message-time {
	font-size: 12px;
	opacity: 0.7;
	margin-top: 5px;
}

.message-item.user .message-time {
	text-align: right;
}

/* 打字动画 */
.typing {
	display: flex;
	align-items: center;
	gap: 4px;
}

.typing span {
	width: 8px;
	height: 8px;
	border-radius: 50%;
	background: #909399;
	animation: typing 1.4s infinite ease-in-out;
}

.typing span:nth-child(1) {
	animation-delay: -0.32s;
}

.typing span:nth-child(2) {
	animation-delay: -0.16s;
}

@keyframes typing {
	0%, 80%, 100% {
		transform: scale(0);
		opacity: 0.5;
	}
	40% {
		transform: scale(1);
		opacity: 1;
	}
}

.input-container {
	padding: 20px;
	border-top: 1px solid #e4e7ed;
	background: white;
}

.input-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-top: 10px;
}

.input-tip {
	font-size: 12px;
	color: #909399;
}

.dialog-footer {
	text-align: right;
}
</style>