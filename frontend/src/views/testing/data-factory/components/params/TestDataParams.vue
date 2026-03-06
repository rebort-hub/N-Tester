<template>
	<div class="test-data-params">
		<!-- 通用数量参数 -->
		<el-form-item v-if="needsCount" label="生成数量">
			<el-input-number
				v-model="localData.count"
				:min="1"
				:max="100"
				placeholder="请输入生成数量"
			/>
		</el-form-item>

		<!-- 地区参数（用于地址生成） -->
		<el-form-item v-if="needsRegion" label="地区">
			<el-select v-model="localData.region" placeholder="请选择地区">
				<el-option label="全国" value="all" />
				<el-option label="北京" value="beijing" />
				<el-option label="上海" value="shanghai" />
				<el-option label="广东" value="guangdong" />
				<el-option label="江苏" value="jiangsu" />
				<el-option label="浙江" value="zhejiang" />
			</el-select>
		</el-form-item>

		<!-- 性别参数（用于姓名生成） -->
		<el-form-item v-if="needsGender" label="性别">
			<el-radio-group v-model="localData.gender">
				<el-radio label="all">不限</el-radio>
				<el-radio label="male">男性</el-radio>
				<el-radio label="female">女性</el-radio>
			</el-radio-group>
		</el-form-item>

		<!-- 邮箱域名参数 -->
		<el-form-item v-if="needsEmailDomain" label="邮箱域名">
			<el-select v-model="localData.domain" placeholder="请选择邮箱域名">
				<el-option label="随机" value="random" />
				<el-option label="qq.com" value="qq.com" />
				<el-option label="163.com" value="163.com" />
				<el-option label="gmail.com" value="gmail.com" />
				<el-option label="sina.com" value="sina.com" />
				<el-option label="foxmail.com" value="foxmail.com" />
			</el-select>
		</el-form-item>

		<!-- 银行类型参数 -->
		<el-form-item v-if="needsBankType" label="银行类型">
			<el-select v-model="localData.bank_type" placeholder="请选择银行类型">
				<el-option label="随机" value="random" />
				<el-option label="工商银行" value="icbc" />
				<el-option label="建设银行" value="ccb" />
				<el-option label="农业银行" value="abc" />
				<el-option label="中国银行" value="boc" />
				<el-option label="招商银行" value="cmb" />
			</el-select>
		</el-form-item>

		<!-- 公司类型参数 -->
		<el-form-item v-if="needsCompanyType" label="公司类型">
			<el-select v-model="localData.company_type" placeholder="请选择公司类型">
				<el-option label="随机" value="random" />
				<el-option label="科技公司" value="tech" />
				<el-option label="贸易公司" value="trade" />
				<el-option label="实业公司" value="industry" />
				<el-option label="投资公司" value="investment" />
			</el-select>
		</el-form-item>

		<!-- 坐标范围参数 -->
		<template v-if="needsCoordinateRange">
			<el-form-item label="经度范围">
				<el-col :span="11">
					<el-input-number
						v-model="localData.min_longitude"
						:precision="6"
						:min="-180"
						:max="180"
						placeholder="最小经度"
					/>
				</el-col>
				<el-col :span="2" class="text-center">
					<span>-</span>
				</el-col>
				<el-col :span="11">
					<el-input-number
						v-model="localData.max_longitude"
						:precision="6"
						:min="-180"
						:max="180"
						placeholder="最大经度"
					/>
				</el-col>
			</el-form-item>
			<el-form-item label="纬度范围">
				<el-col :span="11">
					<el-input-number
						v-model="localData.min_latitude"
						:precision="6"
						:min="-90"
						:max="90"
						placeholder="最小纬度"
					/>
				</el-col>
				<el-col :span="2" class="text-center">
					<span>-</span>
				</el-col>
				<el-col :span="11">
					<el-input-number
						v-model="localData.max_latitude"
						:precision="6"
						:min="-90"
						:max="90"
						placeholder="最大纬度"
					/>
				</el-col>
			</el-form-item>
		</template>

		<!-- 年龄范围参数（用于用户档案） -->
		<template v-if="needsAgeRange">
			<el-form-item label="年龄范围">
				<el-col :span="11">
					<el-input-number
						v-model="localData.min_age"
						:min="1"
						:max="100"
						placeholder="最小年龄"
					/>
				</el-col>
				<el-col :span="2" class="text-center">
					<span>-</span>
				</el-col>
				<el-col :span="11">
					<el-input-number
						v-model="localData.max_age"
						:min="1"
						:max="100"
						placeholder="最大年龄"
					/>
				</el-col>
			</el-form-item>
		</template>
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
	count: 1,
	gender: 'all',
	region: 'all',
	domain: 'random',
	bank_type: 'random',
	company_type: 'random',
	min_longitude: 73.0,
	max_longitude: 135.0,
	min_latitude: 18.0,
	max_latitude: 54.0,
	min_age: 18,
	max_age: 65,
});

// 计算属性 - 根据工具类型显示不同参数
const needsCount = computed(() => {
	return [
		'generate_chinese_name',
		'generate_chinese_phone',
		'generate_chinese_email',
		'generate_chinese_address',
		'generate_id_card',
		'generate_company_name',
		'generate_bank_card',
		'generate_hk_id_card',
		'generate_business_license',
		'generate_coordinates',
		'generate_user_profile'
	].includes(props.tool.name);
});

const needsGender = computed(() => {
	return ['generate_chinese_name', 'generate_user_profile'].includes(props.tool.name);
});

const needsRegion = computed(() => {
	return ['generate_chinese_address', 'generate_id_card'].includes(props.tool.name);
});

const needsEmailDomain = computed(() => {
	return props.tool.name === 'generate_chinese_email';
});

const needsBankType = computed(() => {
	return props.tool.name === 'generate_bank_card';
});

const needsCompanyType = computed(() => {
	return props.tool.name === 'generate_company_name';
});

const needsCoordinateRange = computed(() => {
	return props.tool.name === 'generate_coordinates';
});

const needsAgeRange = computed(() => {
	return props.tool.name === 'generate_user_profile';
});

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsCount.value) filteredData.count = newValue.count;
		if (needsGender.value) filteredData.gender = newValue.gender;
		if (needsRegion.value) filteredData.region = newValue.region;
		if (needsEmailDomain.value) filteredData.domain = newValue.domain;
		if (needsBankType.value) filteredData.bank_type = newValue.bank_type;
		if (needsCompanyType.value) filteredData.company_type = newValue.company_type;
		
		if (needsCoordinateRange.value) {
			filteredData.min_longitude = newValue.min_longitude;
			filteredData.max_longitude = newValue.max_longitude;
			filteredData.min_latitude = newValue.min_latitude;
			filteredData.max_latitude = newValue.max_latitude;
		}
		
		if (needsAgeRange.value) {
			filteredData.min_age = newValue.min_age;
			filteredData.max_age = newValue.max_age;
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
.test-data-params {
	.text-center {
		text-align: center;
		line-height: 32px;
	}
}
</style>