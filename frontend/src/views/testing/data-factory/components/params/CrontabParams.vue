<template>
	<div class="crontab-params">
		<!-- Crontab表达式输入 -->
		<el-form-item v-if="needsExpressionInput" label="Crontab表达式" required>
			<el-input
				v-model="localData.expression"
				placeholder="例如: 0 9 * * 1-5"
			/>
			<div class="param-tip">
				<span>格式: 分钟 小时 日 月 星期</span>
				<el-button size="small" text @click="insertSampleExpression">
					插入示例
				</el-button>
			</div>
		</el-form-item>

		<!-- 手动构建Crontab表达式 -->
		<template v-if="needsManualBuild">
			<el-form-item label="分钟 (0-59)">
				<el-input
					v-model="localData.minute"
					placeholder="例如: 0, 15, 30, 45 或 *"
				/>
				<div class="param-tip">
					<span>* 表示每分钟，0-59 表示具体分钟，*/5 表示每5分钟</span>
				</div>
			</el-form-item>

			<el-form-item label="小时 (0-23)">
				<el-input
					v-model="localData.hour"
					placeholder="例如: 9, 14, 18 或 *"
				/>
				<div class="param-tip">
					<span>* 表示每小时，0-23 表示具体小时，9-17 表示9点到17点</span>
				</div>
			</el-form-item>

			<el-form-item label="日 (1-31)">
				<el-input
					v-model="localData.day"
					placeholder="例如: 1, 15, 30 或 *"
				/>
				<div class="param-tip">
					<span>* 表示每天，1-31 表示具体日期，*/2 表示每2天</span>
				</div>
			</el-form-item>

			<el-form-item label="月 (1-12)">
				<el-input
					v-model="localData.month"
					placeholder="例如: 1, 6, 12 或 *"
				/>
				<div class="param-tip">
					<span>* 表示每月，1-12 表示具体月份，1,3,5 表示1、3、5月</span>
				</div>
			</el-form-item>

			<el-form-item label="星期 (0-7)">
				<el-input
					v-model="localData.weekday"
					placeholder="例如: 1-5, 0,6 或 *"
				/>
				<div class="param-tip">
					<span>0和7都表示周日，1-6表示周一到周六，1-5表示工作日</span>
				</div>
			</el-form-item>

			<!-- 快速选择按钮 -->
			<div class="quick-select">
				<el-button size="small" @click="setQuickExpression('every_minute')">
					每分钟
				</el-button>
				<el-button size="small" @click="setQuickExpression('every_hour')">
					每小时
				</el-button>
				<el-button size="small" @click="setQuickExpression('every_day')">
					每天
				</el-button>
				<el-button size="small" @click="setQuickExpression('workday_9am')">
					工作日9点
				</el-button>
				<el-button size="small" @click="setQuickExpression('weekly_monday')">
					每周一
				</el-button>
				<el-button size="small" @click="setQuickExpression('monthly_1st')">
					每月1号
				</el-button>
			</div>
		</template>

		<!-- 获取执行时间数量 -->
		<el-form-item v-if="needsNextRunsCount" label="获取执行次数">
			<el-input-number
				v-model="localData.count"
				:min="1"
				:max="20"
				placeholder="获取未来执行时间的次数"
			/>
			<div class="param-tip">
				<span>获取未来多少次执行时间</span>
			</div>
		</el-form-item>

		<!-- 时区选择 -->
		<el-form-item v-if="needsTimezone" label="时区">
			<el-select v-model="localData.timezone" placeholder="请选择时区">
				<el-option label="北京时间 (UTC+8)" value="Asia/Shanghai" />
				<el-option label="UTC时间" value="UTC" />
				<el-option label="纽约时间 (UTC-5)" value="America/New_York" />
				<el-option label="伦敦时间 (UTC+0)" value="Europe/London" />
				<el-option label="东京时间 (UTC+9)" value="Asia/Tokyo" />
			</el-select>
		</el-form-item>

		<!-- 表达式预览 -->
		<div v-if="needsManualBuild" class="expression-preview">
			<el-form-item label="生成的表达式">
				<el-input
					:value="generatedExpression"
					readonly
					placeholder="将根据上述设置自动生成"
				/>
			</el-form-item>
		</div>

		<!-- 常用表达式示例 -->
		<div class="expression-examples">
			<h5>常用表达式示例:</h5>
			<div class="examples-grid">
				<div class="example-item" @click="useExample('0 0 * * *')">
					<code>0 0 * * *</code>
					<span>每天午夜</span>
				</div>
				<div class="example-item" @click="useExample('0 9 * * 1-5')">
					<code>0 9 * * 1-5</code>
					<span>工作日9点</span>
				</div>
				<div class="example-item" @click="useExample('*/15 * * * *')">
					<code>*/15 * * * *</code>
					<span>每15分钟</span>
				</div>
				<div class="example-item" @click="useExample('0 0 1 * *')">
					<code>0 0 1 * *</code>
					<span>每月1号</span>
				</div>
				<div class="example-item" @click="useExample('0 0 * * 0')">
					<code>0 0 * * 0</code>
					<span>每周日</span>
				</div>
				<div class="example-item" @click="useExample('0 */2 * * *')">
					<code>0 */2 * * *</code>
					<span>每2小时</span>
				</div>
			</div>
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
	expression: '',
	minute: '*',
	hour: '*',
	day: '*',
	month: '*',
	weekday: '*',
	count: 5,
	timezone: 'Asia/Shanghai',
});

// 计算属性 - 根据工具类型显示不同参数
const needsExpressionInput = computed(() => {
	return [
		'parse_expression',
		'get_next_runs',
		'validate_expression'
	].includes(props.tool.name);
});

const needsManualBuild = computed(() => {
	return props.tool.name === 'generate_expression';
});

const needsNextRunsCount = computed(() => {
	return props.tool.name === 'get_next_runs';
});

const needsTimezone = computed(() => {
	return ['get_next_runs', 'parse_expression'].includes(props.tool.name);
});

// 生成的表达式
const generatedExpression = computed(() => {
	if (!needsManualBuild.value) return '';
	return `${localData.minute} ${localData.hour} ${localData.day} ${localData.month} ${localData.weekday}`;
});

// 插入示例表达式
const insertSampleExpression = () => {
	const examples = [
		'0 9 * * 1-5',  // 工作日9点
		'*/15 * * * *', // 每15分钟
		'0 0 1 * *',    // 每月1号
		'0 */2 * * *',  // 每2小时
		'30 14 * * 0',  // 每周日14:30
	];
	const randomIndex = Math.floor(Math.random() * examples.length);
	localData.expression = examples[randomIndex];
};

// 设置快速表达式
const setQuickExpression = (type: string) => {
	const expressions = {
		every_minute: { minute: '*', hour: '*', day: '*', month: '*', weekday: '*' },
		every_hour: { minute: '0', hour: '*', day: '*', month: '*', weekday: '*' },
		every_day: { minute: '0', hour: '0', day: '*', month: '*', weekday: '*' },
		workday_9am: { minute: '0', hour: '9', day: '*', month: '*', weekday: '1-5' },
		weekly_monday: { minute: '0', hour: '0', day: '*', month: '*', weekday: '1' },
		monthly_1st: { minute: '0', hour: '0', day: '1', month: '*', weekday: '*' },
	};

	const expr = expressions[type as keyof typeof expressions];
	if (expr) {
		Object.assign(localData, expr);
	}
};

// 使用示例表达式
const useExample = (expression: string) => {
	if (needsExpressionInput.value) {
		localData.expression = expression;
	} else if (needsManualBuild.value) {
		// 解析表达式到各个字段
		const parts = expression.split(' ');
		if (parts.length === 5) {
			localData.minute = parts[0];
			localData.hour = parts[1];
			localData.day = parts[2];
			localData.month = parts[3];
			localData.weekday = parts[4];
		}
	}
};

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsExpressionInput.value) {
			filteredData.expression = newValue.expression;
		}
		
		if (needsManualBuild.value) {
			filteredData.minute = newValue.minute;
			filteredData.hour = newValue.hour;
			filteredData.day = newValue.day;
			filteredData.month = newValue.month;
			filteredData.weekday = newValue.weekday;
		}
		
		if (needsNextRunsCount.value) {
			filteredData.count = newValue.count;
		}
		
		if (needsTimezone.value) {
			filteredData.timezone = newValue.timezone;
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
	},
	{ deep: true }
);
</script>

<style scoped lang="scss">
.crontab-params {
	.param-tip {
		margin-top: 4px;
		font-size: 12px;
		color: var(--el-text-color-placeholder);
		display: flex;
		justify-content: space-between;
		align-items: center;
		
		.el-button {
			padding: 0;
			font-size: 12px;
		}
	}

	.quick-select {
		margin: 16px 0;
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.expression-preview {
		margin: 16px 0;
		padding: 12px;
		background: var(--el-color-primary-light-9);
		border-radius: var(--el-border-radius-small);
		border: 1px solid var(--el-color-primary-light-7);
	}

	.expression-examples {
		margin-top: 24px;
		padding-top: 16px;
		border-top: 1px solid var(--el-border-color-light);

		h5 {
			margin: 0 0 12px 0;
			font-size: 14px;
			color: var(--el-text-color-regular);
		}

		.examples-grid {
			display: grid;
			grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
			gap: 8px;
		}

		.example-item {
			display: flex;
			flex-direction: column;
			padding: 8px 12px;
			background: var(--el-fill-color-lighter);
			border-radius: var(--el-border-radius-small);
			cursor: pointer;
			transition: all var(--el-transition-duration);
			border: 1px solid var(--el-border-color-light);

			&:hover {
				background: var(--el-color-primary-light-9);
				border-color: var(--el-color-primary);
			}

			code {
				font-family: 'Courier New', monospace;
				font-size: 13px;
				color: var(--el-color-warning);
				font-weight: 600;
				margin-bottom: 2px;
			}

			span {
				font-size: 12px;
				color: var(--el-text-color-placeholder);
			}
		}
	}
}
</style>