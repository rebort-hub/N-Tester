<template>
	<div class="string-params">
		<!-- 文本输入 -->
		<el-form-item v-if="needsTextInput" label="文本内容" required>
			<el-input
				v-model="localData.text"
				type="textarea"
				:autosize="{ minRows: 3, maxRows: 6 }"
				placeholder="请输入文本内容"
			/>
		</el-form-item>

		<!-- 第二个文本输入（用于对比） -->
		<el-form-item v-if="needsSecondText" label="对比文本" required>
			<el-input
				v-model="localData.text2"
				type="textarea"
				:autosize="{ minRows: 3, maxRows: 6 }"
				placeholder="请输入要对比的文本内容"
			/>
		</el-form-item>

		<!-- 正则表达式 -->
		<el-form-item v-if="needsPattern" label="正则表达式" required>
			<el-input
				v-model="localData.pattern"
				placeholder="例如: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
			/>
			<div class="param-tip">
				<span>支持标准正则表达式语法</span>
			</div>
		</el-form-item>

		<!-- 正则标志 -->
		<el-form-item v-if="needsFlags" label="正则标志">
			<el-checkbox-group v-model="flagsArray">
				<el-checkbox label="i">忽略大小写</el-checkbox>
				<el-checkbox label="m">多行模式</el-checkbox>
				<el-checkbox label="s">单行模式</el-checkbox>
				<el-checkbox label="g">全局匹配</el-checkbox>
			</el-checkbox-group>
		</el-form-item>

		<!-- 字符串替换参数 -->
		<template v-if="needsReplaceParams">
			<el-form-item label="查找字符串" required>
				<el-input
					v-model="localData.old_str"
					placeholder="要替换的字符串"
				/>
			</el-form-item>
			<el-form-item label="替换字符串" required>
				<el-input
					v-model="localData.new_str"
					placeholder="替换为的字符串"
				/>
			</el-form-item>
			<el-form-item label="使用正则表达式">
				<el-switch v-model="localData.is_regex" />
			</el-form-item>
		</template>

		<!-- 转义类型 -->
		<el-form-item v-if="needsEscapeType" label="转义类型">
			<el-select v-model="localData.escape_type" placeholder="请选择转义类型">
				<el-option label="JSON转义" value="json" />
				<el-option label="HTML转义" value="html" />
				<el-option label="URL转义" value="url" />
				<el-option label="SQL转义" value="sql" />
				<el-option label="正则转义" value="regex" />
			</el-select>
		</el-form-item>

		<!-- 反转义类型 -->
		<el-form-item v-if="needsUnescapeType" label="反转义类型">
			<el-select v-model="localData.unescape_type" placeholder="请选择反转义类型">
				<el-option label="JSON反转义" value="json" />
				<el-option label="HTML反转义" value="html" />
				<el-option label="URL反转义" value="url" />
				<el-option label="SQL反转义" value="sql" />
				<el-option label="正则反转义" value="regex" />
			</el-select>
		</el-form-item>

		<!-- 大小写转换类型 -->
		<el-form-item v-if="needsCaseType" label="转换类型">
			<el-select v-model="localData.case_type" placeholder="请选择转换类型">
				<el-option label="转为大写" value="upper" />
				<el-option label="转为小写" value="lower" />
				<el-option label="首字母大写" value="title" />
				<el-option label="驼峰命名" value="camel" />
				<el-option label="下划线命名" value="snake" />
				<el-option label="短横线命名" value="kebab" />
			</el-select>
		</el-form-item>

		<!-- 格式化类型 -->
		<el-form-item v-if="needsFormatType" label="格式化类型">
			<el-select v-model="localData.format_type" placeholder="请选择格式化类型">
				<el-option label="去除首尾空格" value="trim" />
				<el-option label="去除所有空格" value="remove_spaces" />
				<el-option label="标准化空格" value="normalize_spaces" />
				<el-option label="去除换行符" value="remove_newlines" />
				<el-option label="标准化换行符" value="normalize_newlines" />
			</el-select>
		</el-form-item>
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
	text1: '',
	text2: '',
	pattern: '',
	flags: '',
	old_str: '',
	new_str: '',
	is_regex: false,
	escape_type: 'json',
	unescape_type: 'json',
	case_type: 'upper',
	format_type: 'trim',
});

// 正则标志数组
const flagsArray = reactive<string[]>([]);

// 计算属性 - 根据工具类型显示不同参数
const needsTextInput = computed(() => {
	return [
		'text_diff',
		'regex_test',
		'remove_whitespace',
		'replace_string',
		'escape_string',
		'unescape_string',
		'word_count',
		'case_convert',
		'string_format'
	].includes(props.tool.name);
});

const needsSecondText = computed(() => {
	return props.tool.name === 'text_diff';
});

const needsPattern = computed(() => {
	return props.tool.name === 'regex_test';
});

const needsFlags = computed(() => {
	return props.tool.name === 'regex_test';
});

const needsReplaceParams = computed(() => {
	return props.tool.name === 'replace_string';
});

const needsEscapeType = computed(() => {
	return props.tool.name === 'escape_string';
});

const needsUnescapeType = computed(() => {
	return props.tool.name === 'unescape_string';
});

const needsCaseType = computed(() => {
	return props.tool.name === 'case_convert';
});

const needsFormatType = computed(() => {
	return props.tool.name === 'string_format';
});

// 监听标志数组变化
watch(
	flagsArray,
	(newFlags) => {
		localData.flags = newFlags.join('');
	},
	{ deep: true }
);

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsTextInput.value) filteredData.text = newValue.text;
		if (needsSecondText.value) {
			filteredData.text1 = newValue.text;
			filteredData.text2 = newValue.text2;
		}
		if (needsPattern.value) filteredData.pattern = newValue.pattern;
		if (needsFlags.value) filteredData.flags = newValue.flags;
		
		if (needsReplaceParams.value) {
			filteredData.old_str = newValue.old_str;
			filteredData.new_str = newValue.new_str;
			filteredData.is_regex = newValue.is_regex;
		}
		
		if (needsEscapeType.value) filteredData.escape_type = newValue.escape_type;
		if (needsUnescapeType.value) filteredData.unescape_type = newValue.unescape_type;
		if (needsCaseType.value) filteredData.case_type = newValue.case_type;
		if (needsFormatType.value) filteredData.format_type = newValue.format_type;
		
		emit('update:modelValue', filteredData);
	},
	{ deep: true, immediate: true }
);

// 监听外部数据变化
watch(
	() => props.modelValue,
	(newValue) => {
		Object.assign(localData, newValue);
		// 更新标志数组
		if (newValue.flags) {
			flagsArray.splice(0, flagsArray.length, ...newValue.flags.split(''));
		}
	},
	{ deep: true }
);
</script>

<style scoped lang="scss">
.string-params {
	.param-tip {
		margin-top: 4px;
		font-size: 12px;
		color: var(--el-text-color-placeholder);
	}
}
</style>