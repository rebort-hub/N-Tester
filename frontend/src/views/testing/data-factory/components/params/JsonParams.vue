<template>
	<div class="json-params">
		<!-- JSON字符串输入 -->
		<el-form-item v-if="needsJsonInput" label="JSON字符串" required>
			<el-input
				v-model="localData.json_str"
				type="textarea"
				:autosize="{ minRows: 4, maxRows: 8 }"
				placeholder="请输入JSON字符串"
			/>
			<div class="param-tip">
				<el-button size="small" text @click="insertSampleJson">
					插入示例JSON
				</el-button>
			</div>
		</el-form-item>

		<!-- 第二个JSON字符串（用于对比） -->
		<el-form-item v-if="needsSecondJson" label="对比JSON字符串" required>
			<el-input
				v-model="localData.json_str2"
				type="textarea"
				:autosize="{ minRows: 4, maxRows: 8 }"
				placeholder="请输入要对比的JSON字符串"
			/>
		</el-form-item>

		<!-- JSONPath表达式 -->
		<el-form-item v-if="needsJsonPath" label="JSONPath表达式" required>
			<el-input
				v-model="localData.jsonpath"
				placeholder="例如: $.users[*].name"
			/>
			<div class="param-tip">
				<span>支持的语法: $.key, $.array[*], $.array[0], $.key.subkey</span>
			</div>
		</el-form-item>

		<!-- XML字符串输入 -->
		<el-form-item v-if="needsXmlInput" label="XML字符串" required>
			<el-input
				v-model="localData.xml_str"
				type="textarea"
				:autosize="{ minRows: 4, maxRows: 8 }"
				placeholder="请输入XML字符串"
			/>
			<div class="param-tip">
				<el-button size="small" text @click="insertSampleXml">
					插入示例XML
				</el-button>
			</div>
		</el-form-item>

		<!-- YAML字符串输入 -->
		<el-form-item v-if="needsYamlInput" label="YAML字符串" required>
			<el-input
				v-model="localData.yaml_str"
				type="textarea"
				:autosize="{ minRows: 4, maxRows: 8 }"
				placeholder="请输入YAML字符串"
			/>
			<div class="param-tip">
				<el-button size="small" text @click="insertSampleYaml">
					插入示例YAML
				</el-button>
			</div>
		</el-form-item>

		<!-- 格式化选项 -->
		<template v-if="needsFormatOptions">
			<el-form-item label="缩进空格数">
				<el-input-number
					v-model="localData.indent"
					:min="0"
					:max="8"
					placeholder="缩进空格数"
				/>
			</el-form-item>
			<el-form-item label="排序键">
				<el-switch v-model="localData.sort_keys" />
			</el-form-item>
			<el-form-item label="压缩模式">
				<el-switch v-model="localData.compress" />
			</el-form-item>
		</template>

		<!-- 扁平化选项 -->
		<el-form-item v-if="needsFlattenOptions" label="分隔符">
			<el-input
				v-model="localData.separator"
				placeholder="例如: . 或 _"
			/>
		</el-form-item>

		<!-- XML转换选项 -->
		<el-form-item v-if="needsXmlOptions" label="根标签名">
			<el-input
				v-model="localData.root_tag"
				placeholder="例如: root"
			/>
		</el-form-item>

		<!-- 对比选项 -->
		<el-form-item v-if="needsDiffOptions" label="忽略空白字符">
			<el-switch v-model="localData.ignore_whitespace" />
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
	json_str: '',
	json_str1: '',
	json_str2: '',
	jsonpath: '',
	xml_str: '',
	yaml_str: '',
	indent: 2,
	sort_keys: false,
	compress: false,
	separator: '.',
	root_tag: 'root',
	ignore_whitespace: true,
});

// 计算属性 - 根据工具类型显示不同参数
const needsJsonInput = computed(() => {
	return [
		'format_json',
		'validate_json',
		'json_diff_enhanced',
		'jsonpath_query',
		'json_flatten',
		'json_path_list',
		'json_to_xml',
		'json_to_yaml'
	].includes(props.tool.name);
});

const needsSecondJson = computed(() => {
	return props.tool.name === 'json_diff_enhanced';
});

const needsJsonPath = computed(() => {
	return props.tool.name === 'jsonpath_query';
});

const needsXmlInput = computed(() => {
	return props.tool.name === 'xml_to_json';
});

const needsYamlInput = computed(() => {
	return props.tool.name === 'yaml_to_json';
});

const needsFormatOptions = computed(() => {
	return props.tool.name === 'format_json';
});

const needsFlattenOptions = computed(() => {
	return props.tool.name === 'json_flatten';
});

const needsXmlOptions = computed(() => {
	return props.tool.name === 'json_to_xml';
});

const needsDiffOptions = computed(() => {
	return props.tool.name === 'json_diff_enhanced';
});

// 插入示例数据
const insertSampleJson = () => {
	const sampleJson = {
		users: [
			{ name: 'Alice', age: 25, email: 'alice@example.com' },
			{ name: 'Bob', age: 30, email: 'bob@example.com' }
		],
		total: 2,
		page: 1
	};
	localData.json_str = JSON.stringify(sampleJson, null, 2);
};

const insertSampleXml = () => {
	const sampleXml = `<?xml version="1.0" encoding="UTF-8"?>
<users>
	<user>
		<name>Alice</name>
		<age>25</age>
		<email>alice@example.com</email>
	</user>
	<user>
		<name>Bob</name>
		<age>30</age>
		<email>bob@example.com</email>
	</user>
</users>`;
	localData.xml_str = sampleXml;
};

const insertSampleYaml = () => {
	const sampleYaml = `users:
  - name: Alice
    age: 25
    email: alice@example.com
  - name: Bob
    age: 30
    email: bob@example.com
total: 2
page: 1`;
	localData.yaml_str = sampleYaml;
};

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsJsonInput.value) filteredData.json_str = newValue.json_str;
		if (needsSecondJson.value) {
			filteredData.json_str1 = newValue.json_str;
			filteredData.json_str2 = newValue.json_str2;
		}
		if (needsJsonPath.value) filteredData.jsonpath = newValue.jsonpath;
		if (needsXmlInput.value) filteredData.xml_str = newValue.xml_str;
		if (needsYamlInput.value) filteredData.yaml_str = newValue.yaml_str;
		
		if (needsFormatOptions.value) {
			filteredData.indent = newValue.indent;
			filteredData.sort_keys = newValue.sort_keys;
			filteredData.compress = newValue.compress;
		}
		
		if (needsFlattenOptions.value) filteredData.separator = newValue.separator;
		if (needsXmlOptions.value) filteredData.root_tag = newValue.root_tag;
		if (needsDiffOptions.value) filteredData.ignore_whitespace = newValue.ignore_whitespace;
		
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
.json-params {
	.param-tip {
		margin-top: 4px;
		font-size: 12px;
		color: var(--el-text-color-placeholder);
		
		.el-button {
			padding: 0;
			font-size: 12px;
		}
	}
}
</style>