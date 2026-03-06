<template>
	<div class="encryption-params">
		<!-- 文本输入 -->
		<el-form-item v-if="needsTextInput" label="文本内容" required>
			<el-input
				v-model="localData.text"
				type="textarea"
				:autosize="{ minRows: 3, maxRows: 6 }"
				placeholder="请输入要加密的文本"
			/>
		</el-form-item>

		<!-- 密码输入 -->
		<el-form-item v-if="needsPasswordInput" label="密码" required>
			<el-input
				v-model="localData.password"
				type="password"
				placeholder="请输入密码"
				show-password
			/>
		</el-form-item>

		<!-- 加密文本输入 -->
		<el-form-item v-if="needsEncryptedText" label="加密文本" required>
			<el-input
				v-model="localData.encrypted_text"
				type="textarea"
				:autosize="{ minRows: 3, maxRows: 6 }"
				placeholder="请输入要解密的文本"
			/>
		</el-form-item>

		<!-- 密钥输入 -->
		<el-form-item v-if="needsKeyInput" label="密钥" required>
			<el-input
				v-model="localData.key"
				type="password"
				placeholder="请输入AES密钥（16/24/32字节）"
				show-password
			/>
			<div class="param-tip">
				<span>AES密钥长度必须是16、24或32字节</span>
			</div>
		</el-form-item>

		<!-- AES加密模式 -->
		<el-form-item v-if="needsAESMode" label="加密模式">
			<el-select v-model="localData.mode" placeholder="请选择加密模式">
				<el-option label="CBC模式" value="CBC" />
				<el-option label="ECB模式" value="ECB" />
				<el-option label="CFB模式" value="CFB" />
				<el-option label="OFB模式" value="OFB" />
			</el-select>
		</el-form-item>

		<!-- 哈希值输入（用于比对） -->
		<el-form-item v-if="needsHashInput" label="哈希值" required>
			<el-input
				v-model="localData.hash1"
				placeholder="请输入要比对的哈希值"
			/>
		</el-form-item>

		<!-- 第二个哈希值输入 -->
		<el-form-item v-if="needsSecondHash" label="第二个哈希值">
			<el-input
				v-model="localData.hash2"
				placeholder="请输入第二个哈希值（可选）"
			/>
		</el-form-item>

		<!-- 哈希算法类型 -->
		<el-form-item v-if="needsHashType" label="哈希算法">
			<el-select v-model="localData.hash_type" placeholder="请选择哈希算法">
				<el-option label="自动检测" value="auto" />
				<el-option label="MD5" value="md5" />
				<el-option label="SHA1" value="sha1" />
				<el-option label="SHA256" value="sha256" />
				<el-option label="SHA512" value="sha512" />
			</el-select>
		</el-form-item>

		<!-- 盐值长度 -->
		<el-form-item v-if="needsSaltLength" label="盐值长度">
			<el-input-number
				v-model="localData.length"
				:min="8"
				:max="64"
				placeholder="盐值长度"
			/>
		</el-form-item>

		<!-- 盐值编码格式 -->
		<el-form-item v-if="needsSaltEncoding" label="编码格式">
			<el-select v-model="localData.encoding" placeholder="请选择编码格式">
				<el-option label="十六进制" value="hex" />
				<el-option label="Base64" value="base64" />
				<el-option label="原始字节" value="bytes" />
			</el-select>
		</el-form-item>

		<!-- 密码强度分析输入 -->
		<el-form-item v-if="needsPasswordAnalysis" label="密码" required>
			<el-input
				v-model="localData.password"
				type="password"
				placeholder="请输入要分析的密码"
				show-password
			/>
			<div class="param-tip">
				<span>将分析密码的强度、复杂度和安全性</span>
			</div>
		</el-form-item>

		<!-- 输出格式选择 -->
		<el-form-item v-if="needsOutputFormat" label="输出格式">
			<el-select v-model="localData.output_format" placeholder="请选择输出格式">
				<el-option label="十六进制" value="hex" />
				<el-option label="Base64" value="base64" />
				<el-option label="原始字符串" value="raw" />
			</el-select>
		</el-form-item>

		<!-- 编码格式 -->
		<el-form-item v-if="needsEncoding" label="字符编码">
			<el-select v-model="localData.encoding" placeholder="请选择字符编码">
				<el-option label="UTF-8" value="utf-8" />
				<el-option label="GBK" value="gbk" />
				<el-option label="ASCII" value="ascii" />
				<el-option label="ISO-8859-1" value="iso-8859-1" />
			</el-select>
		</el-form-item>

		<!-- 快速操作按钮 -->
		<div v-if="needsQuickActions" class="quick-actions">
			<el-button size="small" @click="generateRandomKey">
				生成随机密钥
			</el-button>
			<el-button size="small" @click="insertSampleText">
				插入示例文本
			</el-button>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, defineProps, defineEmits } from 'vue';
import type { Tool } from '/@/api/v1/data_factory';

// Props
const props = defineProps<{
	modelValue: Record<string, any>;
	tool: Tool;
}>();

// Emits
const emit = defineEmits<{
	'update:modelValue': [value: Record<string, any>];
}>();

// 本地数据
const localData = reactive<Record<string, any>>({
	text: '',
	password: '',
	encrypted_text: '',
	key: '',
	mode: 'CBC',
	hash1: '',
	hash2: '',
	hash_type: 'auto',
	length: 16,
	encoding: 'hex',
	output_format: 'hex',
});

// 计算属性 - 根据工具类型显示不同参数
const needsTextInput = computed(() => {
	return [
		'md5_hash',
		'sha1_hash',
		'sha256_hash',
		'sha512_hash',
		'hash_comparison',
		'aes_encrypt'
	].includes(props.tool.name);
});

const needsPasswordInput = computed(() => {
	return props.tool.name === 'password_strength';
});

const needsEncryptedText = computed(() => {
	return props.tool.name === 'aes_decrypt';
});

const needsKeyInput = computed(() => {
	return ['aes_encrypt', 'aes_decrypt'].includes(props.tool.name);
});

const needsAESMode = computed(() => {
	return ['aes_encrypt', 'aes_decrypt'].includes(props.tool.name);
});

const needsHashInput = computed(() => {
	return props.tool.name === 'hash_comparison';
});

const needsSecondHash = computed(() => {
	return props.tool.name === 'hash_comparison';
});

const needsHashType = computed(() => {
	return props.tool.name === 'hash_comparison';
});

const needsSaltLength = computed(() => {
	return props.tool.name === 'generate_salt';
});

const needsSaltEncoding = computed(() => {
	return props.tool.name === 'generate_salt';
});

const needsPasswordAnalysis = computed(() => {
	return props.tool.name === 'password_strength';
});

const needsOutputFormat = computed(() => {
	return [
		'md5_hash',
		'sha1_hash',
		'sha256_hash',
		'sha512_hash',
		'aes_encrypt'
	].includes(props.tool.name);
});

const needsEncoding = computed(() => {
	return [
		'md5_hash',
		'sha1_hash',
		'sha256_hash',
		'sha512_hash'
	].includes(props.tool.name);
});

const needsQuickActions = computed(() => {
	return ['aes_encrypt', 'aes_decrypt'].includes(props.tool.name);
});

// 生成随机密钥
const generateRandomKey = () => {
	const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
	let result = '';
	for (let i = 0; i < 16; i++) {
		result += chars.charAt(Math.floor(Math.random() * chars.length));
	}
	localData.key = result;
};

// 插入示例文本
const insertSampleText = () => {
	const sampleTexts = [
		'Hello World! This is a test message.',
		'数据工厂加密测试文本',
		'The quick brown fox jumps over the lazy dog.',
		'测试中文加密功能是否正常工作'
	];
	const randomIndex = Math.floor(Math.random() * sampleTexts.length);
	localData.text = sampleTexts[randomIndex];
};

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsTextInput.value) filteredData.text = newValue.text;
		if (needsPasswordInput.value || needsPasswordAnalysis.value) filteredData.password = newValue.password;
		if (needsEncryptedText.value) filteredData.encrypted_text = newValue.encrypted_text;
		if (needsKeyInput.value) filteredData.key = newValue.key;
		if (needsAESMode.value) filteredData.mode = newValue.mode;
		
		if (needsHashInput.value) filteredData.hash1 = newValue.hash1;
		if (needsSecondHash.value) filteredData.hash2 = newValue.hash2;
		if (needsHashType.value) filteredData.hash_type = newValue.hash_type;
		
		if (needsSaltLength.value) filteredData.length = newValue.length;
		if (needsSaltEncoding.value) filteredData.encoding = newValue.encoding;
		if (needsOutputFormat.value) filteredData.output_format = newValue.output_format;
		if (needsEncoding.value) filteredData.encoding = newValue.encoding;
		
		emit('update:modelValue', filteredData);
	},
	{ deep: true, immediate: true }
);

// 监听外部数据变化
watch(
	() => props.modelValue,
	(newValue) => {
		Object.assign(localData, newValue);
	},
	{ deep: true }
);
</script>

<style scoped lang="scss">
.encryption-params {
	.param-tip {
		margin-top: 4px;
		font-size: 12px;
		color: var(--el-text-color-placeholder);
	}

	.quick-actions {
		margin-top: 16px;
		padding-top: 16px;
		border-top: 1px solid var(--el-border-color-light);
		display: flex;
		gap: 8px;
	}
}
</style>