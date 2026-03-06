<template>
	<div class="random-params">
		<!-- 通用数量参数 -->
		<el-form-item v-if="needsCount" label="生成数量">
			<el-input-number
				v-model="localData.count"
				:min="1"
				:max="100"
				placeholder="请输入生成数量"
			/>
		</el-form-item>

		<!-- 整数范围参数 -->
		<template v-if="needsIntRange">
			<el-form-item label="最小值">
				<el-input-number
					v-model="localData.min_val"
					placeholder="最小值"
					style="width: 100%"
				/>
			</el-form-item>
			<el-form-item label="最大值">
				<el-input-number
					v-model="localData.max_val"
					placeholder="最大值"
					style="width: 100%"
				/>
			</el-form-item>
		</template>

		<!-- 浮点数范围参数 -->
		<template v-if="needsFloatRange">
			<el-form-item label="最小值">
				<el-input-number
					v-model="localData.min_val"
					:precision="6"
					placeholder="最小值"
					style="width: 100%"
				/>
			</el-form-item>
			<el-form-item label="最大值">
				<el-input-number
					v-model="localData.max_val"
					:precision="6"
					placeholder="最大值"
					style="width: 100%"
				/>
			</el-form-item>
			<el-form-item label="小数位数">
				<el-input-number
					v-model="localData.precision"
					:min="0"
					:max="10"
					placeholder="小数位数"
				/>
			</el-form-item>
		</template>

		<!-- 字符串长度参数 -->
		<el-form-item v-if="needsStringLength" label="字符串长度">
			<el-input-number
				v-model="localData.length"
				:min="1"
				:max="1000"
				placeholder="字符串长度"
			/>
		</el-form-item>

		<!-- 字符类型选择 -->
		<el-form-item v-if="needsCharType" label="字符类型">
			<el-checkbox-group v-model="charTypeArray">
				<el-checkbox label="letters">字母</el-checkbox>
				<el-checkbox label="numbers">数字</el-checkbox>
				<el-checkbox label="symbols">符号</el-checkbox>
			</el-checkbox-group>
		</el-form-item>

		<!-- UUID版本 -->
		<el-form-item v-if="needsUUIDVersion" label="UUID版本">
			<el-select v-model="localData.version" placeholder="请选择UUID版本">
				<el-option label="UUID1 (基于时间)" value="1" />
				<el-option label="UUID4 (随机)" value="4" />
			</el-select>
		</el-form-item>

		<!-- 布尔值概率 -->
		<el-form-item v-if="needsBooleanProb" label="True概率">
			<el-slider
				v-model="localData.true_probability"
				:min="0"
				:max="1"
				:step="0.1"
				:format-tooltip="formatProbability"
				show-input
			/>
		</el-form-item>

		<!-- MAC地址格式 -->
		<el-form-item v-if="needsMacFormat" label="MAC地址格式">
			<el-select v-model="localData.format_type" placeholder="请选择MAC地址格式">
				<el-option label="冒号分隔 (:)" value="colon" />
				<el-option label="短横线分隔 (-)" value="dash" />
				<el-option label="无分隔符" value="none" />
			</el-select>
		</el-form-item>

		<!-- IP地址类型 -->
		<el-form-item v-if="needsIPType" label="IP地址类型">
			<el-select v-model="localData.ip_type" placeholder="请选择IP地址类型">
				<el-option label="IPv4" value="ipv4" />
				<el-option label="IPv6" value="ipv6" />
			</el-select>
		</el-form-item>

		<!-- 日期范围参数 -->
		<template v-if="needsDateRange">
			<el-form-item label="开始日期">
				<el-date-picker
					v-model="startDate"
					type="date"
					placeholder="选择开始日期"
					format="YYYY-MM-DD"
					value-format="YYYY-MM-DD"
					style="width: 100%"
				/>
			</el-form-item>
			<el-form-item label="结束日期">
				<el-date-picker
					v-model="endDate"
					type="date"
					placeholder="选择结束日期"
					format="YYYY-MM-DD"
					value-format="YYYY-MM-DD"
					style="width: 100%"
				/>
			</el-form-item>
			<el-form-item label="日期格式">
				<el-select v-model="localData.format_str" placeholder="请选择日期格式">
					<el-option label="YYYY-MM-DD" value="%Y-%m-%d" />
					<el-option label="YYYY/MM/DD" value="%Y/%m/%d" />
					<el-option label="DD-MM-YYYY" value="%d-%m-%Y" />
					<el-option label="MM/DD/YYYY" value="%m/%d/%Y" />
					<el-option label="YYYY-MM-DD HH:mm:ss" value="%Y-%m-%d %H:%M:%S" />
				</el-select>
			</el-form-item>
		</template>

		<!-- 密码参数 -->
		<template v-if="needsPasswordParams">
			<el-form-item label="密码长度">
				<el-input-number
					v-model="localData.length"
					:min="4"
					:max="128"
					placeholder="密码长度"
				/>
			</el-form-item>
			<el-form-item label="包含字符类型">
				<el-checkbox-group v-model="passwordCharTypes">
					<el-checkbox label="uppercase">大写字母</el-checkbox>
					<el-checkbox label="lowercase">小写字母</el-checkbox>
					<el-checkbox label="numbers">数字</el-checkbox>
					<el-checkbox label="symbols">特殊符号</el-checkbox>
				</el-checkbox-group>
			</el-form-item>
		</template>

		<!-- 颜色格式 -->
		<el-form-item v-if="needsColorFormat" label="颜色格式">
			<el-select v-model="localData.format_type" placeholder="请选择颜色格式">
				<el-option label="HEX (#RRGGBB)" value="hex" />
				<el-option label="RGB (r,g,b)" value="rgb" />
				<el-option label="HSL (h,s,l)" value="hsl" />
				<el-option label="HSV (h,s,v)" value="hsv" />
			</el-select>
		</el-form-item>

		<!-- 序列参数 -->
		<template v-if="needsSequenceParams">
			<el-form-item label="序列类型">
				<el-select v-model="localData.sequence_type" placeholder="请选择序列类型">
					<el-option label="数字列表" value="list" />
					<el-option label="数字范围" value="range" />
				</el-select>
			</el-form-item>
			<el-form-item v-if="localData.sequence_type === 'list'" label="序列长度">
				<el-input-number
					v-model="localData.length"
					:min="1"
					:max="1000"
					placeholder="序列长度"
				/>
			</el-form-item>
			<template v-if="localData.sequence_type === 'range'">
				<el-form-item label="最小值">
					<el-input-number
						v-model="localData.min_val"
						placeholder="最小值"
						style="width: 100%"
					/>
				</el-form-item>
				<el-form-item label="最大值">
					<el-input-number
						v-model="localData.max_val"
						placeholder="最大值"
						style="width: 100%"
					/>
				</el-form-item>
			</template>
			<el-form-item label="唯一值">
				<el-switch v-model="localData.unique" />
				<div class="param-tip">
					<span>开启后确保生成的值不重复</span>
				</div>
			</el-form-item>
		</template>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, watch, ref, defineProps, defineEmits } from 'vue';
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
	count: 1,
	min_val: 0,
	max_val: 100,
	precision: 2,
	length: 10,
	version: 4,
	true_probability: 0.5,
	format_type: 'hex',
	ip_type: 'ipv4',
	start_date: '2020-01-01',
	end_date: '2030-12-31',
	format_str: '%Y-%m-%d',
	sequence_type: 'list',
	unique: false,
});

// 日期相关
const startDate = ref('2020-01-01');
const endDate = ref('2030-12-31');

// 字符类型数组
const charTypeArray = reactive<string[]>(['letters', 'numbers']);
const passwordCharTypes = reactive<string[]>(['uppercase', 'lowercase', 'numbers', 'symbols']);

// 计算属性 - 根据工具类型显示不同参数
const needsCount = computed(() => {
	return [
		'random_int',
		'random_float',
		'random_string',
		'random_uuid',
		'random_boolean',
		'random_mac_address',
		'random_ip_address',
		'random_date',
		'random_password',
		'random_color',
		'random_sequence'
	].includes(props.tool.name);
});

const needsIntRange = computed(() => {
	return props.tool.name === 'random_int';
});

const needsFloatRange = computed(() => {
	return props.tool.name === 'random_float';
});

const needsStringLength = computed(() => {
	return ['random_string', 'random_password'].includes(props.tool.name);
});

const needsCharType = computed(() => {
	return props.tool.name === 'random_string';
});

const needsUUIDVersion = computed(() => {
	return props.tool.name === 'random_uuid';
});

const needsBooleanProb = computed(() => {
	return props.tool.name === 'random_boolean';
});

const needsMacFormat = computed(() => {
	return props.tool.name === 'random_mac_address';
});

const needsIPType = computed(() => {
	return props.tool.name === 'random_ip_address';
});

const needsDateRange = computed(() => {
	return props.tool.name === 'random_date';
});

const needsPasswordParams = computed(() => {
	return props.tool.name === 'random_password';
});

const needsColorFormat = computed(() => {
	return props.tool.name === 'random_color';
});

const needsSequenceParams = computed(() => {
	return props.tool.name === 'random_sequence';
});

// 格式化概率显示
const formatProbability = (value: number) => {
	return `${(value * 100).toFixed(0)}%`;
};

// 监听日期变化
watch([startDate, endDate], ([start, end]) => {
	localData.start_date = start;
	localData.end_date = end;
});

// 监听字符类型数组变化
watch(
	charTypeArray,
	(newTypes) => {
		localData.include_letters = newTypes.includes('letters');
		localData.include_numbers = newTypes.includes('numbers');
		localData.include_symbols = newTypes.includes('symbols');
	},
	{ deep: true }
);

// 监听密码字符类型数组变化
watch(
	passwordCharTypes,
	(newTypes) => {
		localData.include_uppercase = newTypes.includes('uppercase');
		localData.include_lowercase = newTypes.includes('lowercase');
		localData.include_numbers = newTypes.includes('numbers');
		localData.include_symbols = newTypes.includes('symbols');
	},
	{ deep: true }
);

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsCount.value) filteredData.count = newValue.count;
		
		if (needsIntRange.value || needsFloatRange.value) {
			filteredData.min_val = newValue.min_val;
			filteredData.max_val = newValue.max_val;
		}
		
		if (needsFloatRange.value) filteredData.precision = newValue.precision;
		if (needsStringLength.value) filteredData.length = newValue.length;
		
		if (needsCharType.value) {
			filteredData.include_letters = newValue.include_letters;
			filteredData.include_numbers = newValue.include_numbers;
			filteredData.include_symbols = newValue.include_symbols;
		}
		
		if (needsUUIDVersion.value) filteredData.version = newValue.version;
		if (needsBooleanProb.value) filteredData.true_probability = newValue.true_probability;
		if (needsMacFormat.value) filteredData.format_type = newValue.format_type;
		if (needsIPType.value) filteredData.ip_type = newValue.ip_type;
		
		if (needsDateRange.value) {
			filteredData.start_date = newValue.start_date;
			filteredData.end_date = newValue.end_date;
			filteredData.format_str = newValue.format_str;
		}
		
		if (needsPasswordParams.value) {
			filteredData.length = newValue.length;
			filteredData.include_uppercase = newValue.include_uppercase;
			filteredData.include_lowercase = newValue.include_lowercase;
			filteredData.include_numbers = newValue.include_numbers;
			filteredData.include_symbols = newValue.include_symbols;
		}
		
		if (needsColorFormat.value) filteredData.format_type = newValue.format_type;
		
		if (needsSequenceParams.value) {
			filteredData.sequence_type = newValue.sequence_type;
			filteredData.length = newValue.length;
			filteredData.min_val = newValue.min_val;
			filteredData.max_val = newValue.max_val;
			filteredData.unique = newValue.unique;
		}
		
		emit('update:modelValue', filteredData);
	},
	{ deep: true, immediate: true }
);

// 监听外部数据变化
watch(
	() => props.modelValue,
	(newValue) => {
		Object.assign(localData, newValue);
		
		// 更新日期
		if (newValue.start_date) startDate.value = newValue.start_date;
		if (newValue.end_date) endDate.value = newValue.end_date;
		
		// 更新字符类型数组
		charTypeArray.splice(0, charTypeArray.length);
		if (newValue.include_letters) charTypeArray.push('letters');
		if (newValue.include_numbers) charTypeArray.push('numbers');
		if (newValue.include_symbols) charTypeArray.push('symbols');
		
		// 更新密码字符类型数组
		passwordCharTypes.splice(0, passwordCharTypes.length);
		if (newValue.include_uppercase) passwordCharTypes.push('uppercase');
		if (newValue.include_lowercase) passwordCharTypes.push('lowercase');
		if (newValue.include_numbers) passwordCharTypes.push('numbers');
		if (newValue.include_symbols) passwordCharTypes.push('symbols');
	},
	{ deep: true }
);
</script>

<style scoped lang="scss">
.random-params {
	.param-tip {
		margin-top: 4px;
		font-size: 12px;
		color: var(--el-text-color-placeholder);
	}
}
</style>