<template>
	<div class="encoding-params">
		<!-- 文本输入 -->
		<el-form-item v-if="needsTextInput" label="文本内容" required>
			<el-input
				v-model="localData.text"
				type="textarea"
				:autosize="{ minRows: 2, maxRows: 4 }"
				placeholder="请输入文本内容"
			/>
		</el-form-item>

		<!-- 编码文本输入 -->
		<el-form-item v-if="needsEncodedText" label="编码文本" required>
			<el-input
				v-model="localData.encoded_text"
				type="textarea"
				:autosize="{ minRows: 2, maxRows: 4 }"
				placeholder="请输入编码后的文本"
			/>
		</el-form-item>

		<!-- Base64字符串输入 -->
		<el-form-item v-if="needsBase64Input" label="Base64字符串" required>
			<el-input
				v-model="localData.base64_str"
				type="textarea"
				:autosize="{ minRows: 2, maxRows: 4 }"
				placeholder="请输入Base64编码字符串"
			/>
		</el-form-item>

		<!-- JWT Token输入 -->
		<el-form-item v-if="needsTokenInput" label="JWT Token" required>
			<el-input
				v-model="localData.token"
				type="textarea"
				:autosize="{ minRows: 2, maxRows: 4 }"
				placeholder="请输入JWT Token"
			/>
		</el-form-item>

		<!-- 图片路径输入 -->
		<el-form-item v-if="needsImagePath" label="图片路径">
			<el-input
				v-model="localData.image_path"
				placeholder="请输入图片路径或上传图片"
			/>
			<div class="param-tip">
				<span>支持本地路径或URL</span>
			</div>
		</el-form-item>

		<!-- 条形码类型 -->
		<el-form-item v-if="needsBarcodeType" label="条形码类型">
			<el-select v-model="localData.barcode_type" placeholder="请选择条形码类型">
				<el-option label="Code128" value="code128" />
				<el-option label="Code39" value="code39" />
				<el-option label="EAN13" value="ean13" />
				<el-option label="EAN8" value="ean8" />
				<el-option label="UPC-A" value="upca" />
			</el-select>
		</el-form-item>

		<!-- 二维码大小 -->
		<el-form-item v-if="needsQRSize" label="二维码大小">
			<el-input-number
				v-model="localData.size"
				:min="100"
				:max="1000"
				:step="50"
				placeholder="二维码大小"
			/>
			<div class="param-tip">
				<span>像素大小，建议100-500</span>
			</div>
		</el-form-item>

		<!-- 二维码边框 -->
		<el-form-item v-if="needsQRBorder" label="边框大小">
			<el-input-number
				v-model="localData.border"
				:min="1"
				:max="10"
				placeholder="边框大小"
			/>
		</el-form-item>

		<!-- 时间戳 -->
		<el-form-item v-if="needsTimestamp" label="时间戳" required>
			<el-input-number
				v-model="localData.timestamp"
				:precision="0"
				placeholder="请输入时间戳"
				style="width: 100%"
			/>
			<div class="param-tip">
				<el-button size="small" text @click="useCurrentTimestamp">
					使用当前时间戳
				</el-button>
			</div>
		</el-form-item>

		<!-- 时间戳格式类型 -->
		<el-form-item v-if="needsTimestampFormat" label="转换类型">
			<el-select v-model="localData.format_type" placeholder="请选择转换类型">
				<el-option label="转为日期时间" value="to_datetime" />
				<el-option label="转为时间戳" value="to_timestamp" />
			</el-select>
		</el-form-item>

		<!-- 时间戳单位 -->
		<el-form-item v-if="needsTimestampUnit" label="时间戳单位">
			<el-select v-model="localData.timestamp_unit" placeholder="请选择时间戳单位">
				<el-option label="自动检测" value="auto" />
				<el-option label="秒" value="seconds" />
				<el-option label="毫秒" value="milliseconds" />
			</el-select>
		</el-form-item>

		<!-- 进制转换参数 -->
		<template v-if="needsBaseConvert">
			<el-form-item label="数字字符串" required>
				<el-input
					v-model="localData.num_str"
					placeholder="请输入数字"
				/>
			</el-form-item>
			<el-form-item label="源进制">
				<el-input-number
					v-model="localData.from_base"
					:min="2"
					:max="36"
					placeholder="源进制"
				/>
			</el-form-item>
			<el-form-item label="目标进制">
				<el-input-number
					v-model="localData.to_base"
					:min="2"
					:max="36"
					placeholder="目标进制"
				/>
			</el-form-item>
		</template>

		<!-- Unicode转换类型 -->
		<el-form-item v-if="needsUnicodeType" label="转换类型">
			<el-select v-model="localData.convert_type" placeholder="请选择转换类型">
				<el-option label="转为Unicode" value="to_unicode" />
				<el-option label="从Unicode转换" value="from_unicode" />
			</el-select>
		</el-form-item>

		<!-- ASCII转换类型 -->
		<el-form-item v-if="needsAsciiType" label="转换类型">
			<el-select v-model="localData.convert_type" placeholder="请选择转换类型">
				<el-option label="转为ASCII码" value="to_ascii" />
				<el-option label="从ASCII码转换" value="from_ascii" />
			</el-select>
		</el-form-item>

		<!-- 颜色值转换参数 -->
		<template v-if="needsColorConvert">
			<el-form-item label="颜色值" required>
				<el-input
					v-model="localData.color_value"
					placeholder="例如: #FF0000 或 rgb(255,0,0)"
				/>
			</el-form-item>
			<el-form-item label="源格式">
				<el-select v-model="localData.from_format" placeholder="请选择源格式">
					<el-option label="HEX" value="hex" />
					<el-option label="RGB" value="rgb" />
					<el-option label="HSL" value="hsl" />
					<el-option label="HSV" value="hsv" />
				</el-select>
			</el-form-item>
			<el-form-item label="目标格式">
				<el-select v-model="localData.to_format" placeholder="请选择目标格式">
					<el-option label="HEX" value="hex" />
					<el-option label="RGB" value="rgb" />
					<el-option label="HSL" value="hsl" />
					<el-option label="HSV" value="hsv" />
				</el-select>
			</el-form-item>
		</template>

		<!-- 编码格式 -->
		<el-form-item v-if="needsEncoding" label="编码格式">
			<el-select v-model="localData.encoding" placeholder="请选择编码格式">
				<el-option label="UTF-8" value="utf-8" />
				<el-option label="GBK" value="gbk" />
				<el-option label="ASCII" value="ascii" />
				<el-option label="ISO-8859-1" value="iso-8859-1" />
			</el-select>
		</el-form-item>

		<!-- JWT验证选项 -->
		<el-form-item v-if="needsJWTVerify" label="验证签名">
			<el-switch v-model="localData.verify" />
			<div class="param-tip">
				<span>开启后需要提供密钥进行签名验证</span>
			</div>
		</el-form-item>

		<!-- 图片格式 -->
		<el-form-item v-if="needsImageFormat" label="图片格式">
			<el-select v-model="localData.image_format" placeholder="请选择图片格式">
				<el-option label="PNG" value="png" />
				<el-option label="JPEG" value="jpeg" />
				<el-option label="GIF" value="gif" />
				<el-option label="BMP" value="bmp" />
			</el-select>
		</el-form-item>

		<!-- 输出格式 -->
		<el-form-item v-if="needsOutputFormat" label="输出格式">
			<el-select v-model="localData.output_format" placeholder="请选择输出格式">
				<el-option label="PNG" value="png" />
				<el-option label="JPEG" value="jpeg" />
				<el-option label="GIF" value="gif" />
				<el-option label="BMP" value="bmp" />
			</el-select>
		</el-form-item>

		<!-- 保存到静态目录 -->
		<el-form-item v-if="needsSaveToStatic" label="保存到静态目录">
			<el-switch v-model="localData.save_to_static" />
			<div class="param-tip">
				<span>开启后将保存生成的图片到服务器静态目录</span>
			</div>
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
	encoded_text: '',
	base64_str: '',
	token: '',
	image_path: '',
	barcode_type: 'code128',
	size: 300,
	border: 4,
	timestamp: Math.floor(Date.now() / 1000),
	format_type: 'to_datetime',
	timestamp_unit: 'auto',
	num_str: '',
	from_base: 10,
	to_base: 16,
	convert_type: 'to_unicode',
	color_value: '',
	from_format: 'hex',
	to_format: 'rgb',
	encoding: 'utf-8',
	verify: false,
	image_format: 'png',
	output_format: 'png',
	save_to_static: true,
});

// 计算属性 - 根据工具类型显示不同参数
const needsTextInput = computed(() => {
	return [
		'generate_barcode',
		'generate_qrcode',
		'unicode_convert',
		'ascii_convert',
		'url_encode',
		'base64_encode'
	].includes(props.tool.name);
});

const needsEncodedText = computed(() => {
	return ['url_decode', 'base64_decode'].includes(props.tool.name);
});

const needsBase64Input = computed(() => {
	return props.tool.name === 'base64_to_image';
});

const needsTokenInput = computed(() => {
	return props.tool.name === 'jwt_decode';
});

const needsImagePath = computed(() => {
	return ['decode_qrcode', 'image_to_base64'].includes(props.tool.name);
});

const needsBarcodeType = computed(() => {
	return props.tool.name === 'generate_barcode';
});

const needsQRSize = computed(() => {
	return props.tool.name === 'generate_qrcode';
});

const needsQRBorder = computed(() => {
	return props.tool.name === 'generate_qrcode';
});

const needsTimestamp = computed(() => {
	return props.tool.name === 'timestamp_convert';
});

const needsTimestampFormat = computed(() => {
	return props.tool.name === 'timestamp_convert';
});

const needsTimestampUnit = computed(() => {
	return props.tool.name === 'timestamp_convert';
});

const needsBaseConvert = computed(() => {
	return props.tool.name === 'base_convert';
});

const needsUnicodeType = computed(() => {
	return props.tool.name === 'unicode_convert';
});

const needsAsciiType = computed(() => {
	return props.tool.name === 'ascii_convert';
});

const needsColorConvert = computed(() => {
	return props.tool.name === 'color_convert';
});

const needsEncoding = computed(() => {
	return ['url_encode', 'url_decode', 'base64_encode', 'base64_decode'].includes(props.tool.name);
});

const needsJWTVerify = computed(() => {
	return props.tool.name === 'jwt_decode';
});

const needsImageFormat = computed(() => {
	return ['decode_qrcode', 'image_to_base64'].includes(props.tool.name);
});

const needsOutputFormat = computed(() => {
	return props.tool.name === 'base64_to_image';
});

const needsSaveToStatic = computed(() => {
	return ['generate_barcode', 'generate_qrcode'].includes(props.tool.name);
});

// 使用当前时间戳
const useCurrentTimestamp = () => {
	localData.timestamp = Math.floor(Date.now() / 1000);
};

// 监听本地数据变化
watch(
	localData,
	(newValue) => {
		// 只传递当前工具需要的参数
		const filteredData: Record<string, any> = {};
		
		if (needsTextInput.value) filteredData.text = newValue.text;
		if (needsEncodedText.value) filteredData.encoded_text = newValue.encoded_text;
		if (needsBase64Input.value) filteredData.base64_str = newValue.base64_str;
		if (needsTokenInput.value) filteredData.token = newValue.token;
		if (needsImagePath.value) filteredData.image_path = newValue.image_path;
		
		if (needsBarcodeType.value) filteredData.barcode_type = newValue.barcode_type;
		if (needsQRSize.value) filteredData.size = newValue.size;
		if (needsQRBorder.value) filteredData.border = newValue.border;
		
		if (needsTimestamp.value) filteredData.timestamp = newValue.timestamp;
		if (needsTimestampFormat.value) filteredData.format_type = newValue.format_type;
		if (needsTimestampUnit.value) filteredData.timestamp_unit = newValue.timestamp_unit;
		
		if (needsBaseConvert.value) {
			filteredData.num_str = newValue.num_str;
			filteredData.from_base = newValue.from_base;
			filteredData.to_base = newValue.to_base;
		}
		
		if (needsUnicodeType.value || needsAsciiType.value) {
			filteredData.convert_type = newValue.convert_type;
		}
		
		if (needsColorConvert.value) {
			filteredData.color_value = newValue.color_value;
			filteredData.from_format = newValue.from_format;
			filteredData.to_format = newValue.to_format;
		}
		
		if (needsEncoding.value) filteredData.encoding = newValue.encoding;
		if (needsJWTVerify.value) filteredData.verify = newValue.verify;
		if (needsImageFormat.value) filteredData.image_format = newValue.image_format;
		if (needsOutputFormat.value) filteredData.output_format = newValue.output_format;
		if (needsSaveToStatic.value) filteredData.save_to_static = newValue.save_to_static;
		
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
.encoding-params {
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