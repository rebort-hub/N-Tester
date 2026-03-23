<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import VueJsonPretty from "vue-json-pretty";
import JsonEditor from "/@/components/code-editor/JsonEditor.vue";
import "vue-json-pretty/lib/styles.css";
import { 
	Operation, 
	Clock, 
	EditPen, 
	CircleCheck, 
	Coin, 
	InfoFilled,
	Connection,
	ArrowDown,
	View,
	Document,
	Delete
} from '@element-plus/icons-vue';
import { api_send, save_api, save_api_case, req_history, edit_history, api_params } from '/@/api/v1/api_automation';
import { useFileApi } from '/@/api/v1/common/file';
import { ElMessage, ElMessageBox } from 'element-plus';

const props = defineProps({
	apiData: { type: Object, default: () => ({}) },
	envId: { type: [Number, String], default: null },
	env_list: { type: Array, default: () => [] },
	tree_list: { type: Array, default: () => [] },
	redis_example_list: { type: Array, default: () => ["common"] },
	local_db_list: { type: Array, default: () => [] },
	params_list: { type: Array, default: () => [{ name: "", id: null }] }
});

const emit = defineEmits(['caseSaved', 'apiSaved']);

const fileApi = useFileApi();

// vue-json-pretty 的 height 参数需要 number（旧架构传 260），传字符串会导致高度不生效
const viewportH = ref(typeof window !== 'undefined' ? window.innerHeight : 900);
const onResize = () => { viewportH.value = window.innerHeight; };
onMounted(() => window.addEventListener('resize', onResize));
onBeforeUnmount(() => window.removeEventListener('resize', onResize));

const resJsonHeight = computed(() => {
	// 经验值：尽量接近旧版“响应区大面板”，同时限制上下界避免过大/过小
	const h = Math.floor(viewportH.value * 0.38);
	return Math.max(260, Math.min(780, h));
});

const val_type_list = ref([
	{ name: "环境变量", value: 1 },
	{ name: "全局变量", value: 2 }
]);

const res_type_list = ref([
	{ name: "响应结果-JSON", value: 1 },
	{ name: "请求头-Headers", value: 2 },
	{ name: "请求头-Body", value: 3 },
	{ name: "Headers-响应结果", value: 4 },
	{ name: "自定义目标值", value: 5 }
]);

const tips = ref<any>(
	'路径示例，结果={"code": 200, "info": {"username": "admin"}, "list": [{"id": 1},{"id": 2}]}\n' +
	"例子：code：$.code, username：$.info.username，数组：$.list[0].id / $.list[1].id分别等于1 / 2"
);

const method_list = ref([
	{ name: "GET", value: 1, color: "#67C23A" },
	{ name: "POST", value: 2, color: "#409EFF" },
	{ name: "PUT", value: 3, color: "#E6A23C" },
	{ name: "DELETE", value: 4, color: "#F56C6C" },
	{ name: "PATCH", value: 5, color: "#8E44AD" },
	{ name: "OPTIONS", value: 6, color: "#909399" }
]);

const req_active = ref<any>("body");
const res_active = ref<any>("res");

// 对话框状态
const toolboxDialogVisible = ref(false);
const paramsDepDialogVisible = ref(false);
const directDbDialogVisible = ref(false);
const publicFuncDialogVisible = ref(false);
const errorCodeDialogVisible = ref(false);
const envManageDialogVisible = ref(false);
const editRecordDialogVisible = ref(false);
const debugRecordDialogVisible = ref(false);
const apiDocDialogVisible = ref(false);

// 对话框数据
const paramsDepList = ref<any[]>([]);
const directDbList = ref<any[]>([]);
const publicFuncList = ref<any[]>([]);
const errorCodeList = ref<any[]>([]);
const envList = ref<any[]>([]);
const editRecordList = ref<any[]>([]);
const debugRecordList = ref<any[]>([]);
const apiDocInfo = ref<any>({});

// 接口请求数据结构
const req = ref({
	method: 1,
	url: '',
	params: [],
	header: [],
	body: '',
	body_type: 2,
	form_data: [],
	form_urlencoded: [],
	file_path: [],
	params_id: null,
	before: [],
	after: [],
	assert: [],
	config: {
		retry: 0,
		req_timeout: 30,
		res_timeout: 30
	}
});

// 接口响应数据结构
const res = ref({
	body: {},
	header: {},
	before: [],
	after: [],
	assert: [],
	code: 0,
	size: 0,
	res_time: 0
});

// 当前接口 ID（保存/发送/记录用）：树节点 api_id 为接口ID，后端 get_api_info 不返回 id
const apiId = computed(() => {
	const d = props.apiData;
	return d?.api_id ?? d?.api_info?.id ?? d?.id ?? null;
});

// 仅在“切换到另一个接口”时初始化一次，避免编辑过程中被 deep watch 重置（导致 body_type 跳回 JSON）
const lastApiId = ref<number | string | null>(null);
watch(
	() => apiId.value,
	() => {
		const newId = apiId.value;
		if (newId == null) return;
		if (lastApiId.value === newId) return;
		lastApiId.value = newId;

		const newData = props.apiData;
		if (!newData) return;
		const apiInfo = newData.api_info || newData;
		const reqSrc = apiInfo.req || apiInfo;
		const resSrc = apiInfo.response || apiInfo.res || {};

		req.value = {
			method: reqSrc.method ?? 1,
			url: reqSrc.url ?? apiInfo.url ?? '',
			params: Array.isArray(reqSrc.params) ? reqSrc.params : [],
			header: Array.isArray(reqSrc.header) ? reqSrc.header : [],
			body: typeof reqSrc.body === 'string' ? reqSrc.body : JSON.stringify(reqSrc.body != null ? reqSrc.body : {}, null, 2),
			body_type: reqSrc.body_type ?? 2,
			form_data: Array.isArray(reqSrc.form_data) ? reqSrc.form_data : [],
			form_urlencoded: Array.isArray(reqSrc.form_urlencoded) ? reqSrc.form_urlencoded : [],
			file_path: Array.isArray(reqSrc.file_path) ? reqSrc.file_path : [],
			params_id: reqSrc.params_id ?? apiInfo.params_id ?? null,
			before: Array.isArray(reqSrc.before) ? reqSrc.before : [],
			after: Array.isArray(reqSrc.after) ? reqSrc.after : [],
			assert: Array.isArray(reqSrc.assert) ? reqSrc.assert : [],
			config: {
				retry: reqSrc.config?.retry ?? 0,
				req_timeout: reqSrc.config?.req_timeout ?? 30,
				res_timeout: reqSrc.config?.res_timeout ?? 30,
			},
		};

		res.value = {
			body: resSrc.body ?? {},
			header: resSrc.header ?? {},
			before: Array.isArray(resSrc.before) ? resSrc.before : [],
			after: Array.isArray(resSrc.after) ? resSrc.after : [],
			assert: Array.isArray(resSrc.assert) ? resSrc.assert : [],
			code: resSrc.code ?? 0,
			size: resSrc.size ?? 0,
			res_time: resSrc.res_time ?? 0,
		};
	},
	{ immediate: true }
);
// 添加参数行
const addParam = () => {
	req.value.params.push({ key: '', value: '', status: true });
};

// 删除参数行
const removeParam = (index: number) => {
	req.value.params.splice(index, 1);
};

// 添加Header行
const addHeader = () => {
	req.value.header.push({ key: '', value: '', status: true });
};

// 删除Header行
const removeHeader = (index: number) => {
	req.value.header.splice(index, 1);
};

// 添加form-data行
const addFormData = () => {
	req.value.form_data.push({ key: '', value: '', status: true });
};

// 删除form-data行
const removeFormData = (index: number) => {
	req.value.form_data.splice(index, 1);
};

// 添加form-urlencoded行
const addFormUrlencoded = () => {
	req.value.form_urlencoded.push({ key: '', value: '', status: true });
};

// 删除form-urlencoded行
const removeFormUrlencoded = (index: number) => {
	req.value.form_urlencoded.splice(index, 1);
};

// 添加前置操作
const addBefore = (type: number) => {
	const beforeItem: any = { type };
	
	switch (type) {
		case 1: // 预请求接口
			beforeItem.title = '';
			beforeItem.env_id = null;
			beforeItem.api_id = [];
			break;
		case 2: // 预设变量
			beforeItem.name = '';
			beforeItem.value = '';
			beforeItem.env_type = 1;
			break;
		case 3: // 等待时长
			beforeItem.wait_time = 1;
			break;
		case 4: // 自定义脚本
			beforeItem.title = '';
			beforeItem.code = '';
			break;
	}
	
	req.value.before.push(beforeItem);
};

// 删除前置操作
const removeBefore = (index: number) => {
	req.value.before.splice(index, 1);
};

// 添加后置操作
const addAfter = (type: number) => {
	const afterItem: any = { type };
	
	switch (type) {
		case 1: // 提取变量
			afterItem.name = '';
			afterItem.value = '';
			afterItem.res_type = 1;
			afterItem.env_type = 1;
			break;
		case 2: // 等待时长
			afterItem.wait_time = 1;
			break;
	}
	
	req.value.after.push(afterItem);
};

// 删除后置操作
const removeAfter = (index: number) => {
	req.value.after.splice(index, 1);
};
// 添加断言
const addAssert = (type: number) => {
	const assertItem: any = { type };
	
	switch (type) {
		case 1: // 响应断言
			assertItem.name = '';
			assertItem.value = '';
			assertItem.res_type = 1;
			break;
		case 2: // ops-数据库断言
			assertItem.ops_db = null;
			assertItem.ops_db_table = '';
			assertItem.ops_db_where = '';
			assertItem.ops_db_assert = [];
			break;
		case 3: // ops-redis断言
			assertItem.ops_redis = null;
			assertItem.ops_redis_key = '';
			assertItem.ops_redis_assert = [];
			break;
		case 4: // 直连-数据库断言
			assertItem.local_db = null;
			assertItem.local_db_table = '';
			assertItem.local_db_where = '';
			assertItem.local_db_assert = [];
			break;
	}
	
	req.value.assert.push(assertItem);
};

// 删除断言
const removeAssert = (index: number) => {
	req.value.assert.splice(index, 1);
};

// 添加数据库断言配置
const addDbAssertConfig = (dbAssertList: any[]) => {
	dbAssertList.push({
		name: '',
		type: 1,
		value: ''
	});
};

// 删除数据库断言配置
const removeDbAssertConfig = (dbAssertList: any[], index: number) => {
	dbAssertList.splice(index, 1);
};

// 添加ops-数据库断言配置
const addOpsDbAssertConfig = (opsDbAssertList: any[]) => {
	opsDbAssertList.push({
		name: '',
		type: 1,
		value: ''
	});
};

// 删除ops-数据库断言配置
const removeOpsDbAssertConfig = (opsDbAssertList: any[], index: number) => {
	opsDbAssertList.splice(index, 1);
};

// 添加ops-redis断言配置
const addOpsRedisAssertConfig = (opsRedisAssertList: any[]) => {
	opsRedisAssertList.push({
		name: '',
		type: 1,
		value: ''
	});
};

// 删除ops-redis断言配置
const removeOpsRedisAssertConfig = (opsRedisAssertList: any[], index: number) => {
	opsRedisAssertList.splice(index, 1);
};

const formatTime = (value: any) => {
	if (!value) return '-';
	const d = new Date(value);
	if (!isNaN(d.getTime())) {
		return d.toLocaleString();
	}
	return String(value);
};

const getMethodColor = (methodVal: number | undefined) => {
	const v = Number(methodVal);
	switch (v) {
		case 1: return '#67C23A'; // GET
		case 2: return '#409EFF'; // POST
		case 3: return '#E6A23C'; // PUT
		case 4: return '#F56C6C'; // DELETE
		case 5: return '#8E44AD'; // PATCH
		case 6: return '#909399'; // OPTIONS
		default: return '#409EFF';
	}
};

const currentMethodColor = computed(() => getMethodColor(req.value?.method));

const uploadBinaryFile = async (options: any) => {
	try {
		const form = new FormData();
		form.append('file', options.file);
		// 需要落盘，后端 api_automation 以文件路径 open()
		form.append('store_in_database', 'false');
		const res: any = await fileApi.upload(form);
		const filePath = res?.data?.file_path;
		if (!filePath) throw new Error('未获取到文件路径');
		req.value.file_path = Array.isArray(req.value.file_path) ? req.value.file_path : [];
		req.value.file_path.push(filePath);
		ElMessage.success('上传成功');
		options?.onSuccess?.(res);
	} catch (e: any) {
		console.error('上传失败:', e);
		ElMessage.error(e?.message || '上传失败');
		options?.onError?.(e);
	}
};

// 发送请求
const sendRequest = async () => {
	const id = apiId.value;
	if (id == null) {
		ElMessage.warning('无法获取接口ID');
		return;
	}
	try {
		const requestData = {
			id: Number(id),
			env_id: props.envId,
			req: req.value
		};
		const response: any = await api_send(requestData);
		if (response.code === 200) {
			const data = response.data;
			// 兼容后端返回 data 或 data.res
			res.value = data?.res ? { ...res.value, ...data.res } : (data || res.value);
			ElMessage.success('请求发送成功');
		}
	} catch (error) {
		console.error('发送请求失败:', error);
		ElMessage.error('请求发送失败');
	}
};

// 保存接口
const saveApiData = async () => {
	const id = apiId.value;
	if (id == null) {
		ElMessage.warning('无法获取接口ID');
		return;
	}
	try {
		const saveData = {
			id: Number(id),
			url: req.value.url || props.apiData?.api_info?.url || props.apiData?.url || '/',
			req: req.value
		};
		const response: any = await save_api(saveData);
		if (response.code === 200) {
			ElMessage.success('保存成功');
			emit('apiSaved');
		}
	} catch (error) {
		console.error('保存失败:', error);
		ElMessage.error('保存失败');
	}
};

// 保存项下拉命令
const handleSaveCommand = (command: string) => {
	if (command === 'save') saveApiData();
	else if (command === 'saveAsCase') saveAsCase();
};

// 保存为用例
const saveAsCase = async () => {
	const id = apiId.value;
	if (id == null) {
		ElMessage.warning('无法获取接口ID');
		return;
	}
	try {
		const defaultName = `${props.apiData?.name || props.apiData?.api_info?.name || '接口'}_用例_${Date.now()}`;
		const { value, action } = await ElMessageBox.prompt('请输入用例名称', '保存为用例', {
			inputValue: defaultName,
			confirmButtonText: '确定',
			cancelButtonText: '取消'
		});
		if (action === 'cancel') return;
		const caseName = (value || '').trim() || defaultName;
		const caseData: Record<string, any> = {
			id: Number(id),
			name: caseName,
			req: req.value,
			url: req.value.url
		};
		const apiServiceId = props.apiData?.api_info?.api_service_id ?? props.apiData?.api_service_id;
		if (apiServiceId != null) caseData.api_service_id = Number(apiServiceId);
		const response: any = await save_api_case(caseData);
		if (response.code === 200) {
			ElMessage.success('保存为用例成功');
			emit('caseSaved');
		}
	} catch (error) {
		console.error('保存为用例失败:', error);
		ElMessage.error('保存为用例失败');
	}
};

// 显示编辑记录
const showEditRecord = () => {
	editRecordDialogVisible.value = true;
	loadEditRecords();
};

// 显示调试记录
const showDebugRecord = () => {
	debugRecordDialogVisible.value = true;
	loadDebugRecords();
};

// 显示接口文档
const showApiDoc = () => {
	apiDocDialogVisible.value = true;
	loadApiDoc();
};

// 加载编辑记录（对接 edit_history 接口）
const loadEditRecords = async () => {
	const id = apiId.value;
	if (id == null) {
		editRecordList.value = [];
		return;
	}
	try {
		const response: any = await edit_history({ api_id: Number(id) });
		const data = response?.data;
		let raw: any[] = [];
		if (Array.isArray(data)) raw = data;
		else if (data?.content && Array.isArray(data.content)) raw = data.content;
		else if (data?.list && Array.isArray(data.list)) raw = data.list;
		editRecordList.value = raw.map((row: any) => {
			const editSummary = row.edit != null
				? (Array.isArray(row.edit) ? row.edit.map((e: any) => `${e.field || ''} ${e.type || ''}`).filter(Boolean).join('; ') : JSON.stringify(row.edit))
				: (row.details ?? row.content ?? row.description ?? '-');
			return {
				id: row.id,
				operation: row.operation ?? row.operation_type ?? '接口编辑',
				user: row.user ?? row.username ?? row.created_by ?? '-',
				time: formatTime(row.time ?? row.create_time ?? row.creation_date ?? row.created_at ?? '-'),
				details: row.details ?? editSummary
			};
		});
	} catch (e) {
		console.error('加载编辑记录失败:', e);
		editRecordList.value = [];
	}
};

// 加载调试记录（对接 req_history 接口）
const loadDebugRecords = async () => {
	const id = apiId.value;
	if (id == null) {
		debugRecordList.value = [];
		return;
	}
	try {
		const response: any = await req_history({ api_id: Number(id) });
		const data = response?.data;
		let list: any[] = [];
		if (Array.isArray(data)) {
			list = data;
		} else if (data?.content && Array.isArray(data.content)) {
			list = data.content;
		} else if (data?.list && Array.isArray(data.list)) {
			list = data.list;
		} else if (data?.items && Array.isArray(data.items)) {
			list = data.items;
		}
		const curId = apiId.value != null ? Number(apiId.value) : null;
		const filtered = curId != null ? list.filter((row: any) => (row.api_id != null ? Number(row.api_id) : null) === curId) : list;
		// 映射为弹窗表格字段：id, status, statusCode, responseTime, time, size
		debugRecordList.value = filtered.map((row: any) => ({
			id: row.id,
			status: row.status ?? (row.code === 200 || row.status_code === 200 ? '成功' : '失败'),
			statusCode: row.code ?? row.status_code ?? row.statusCode ?? 0,
			responseTime: row.res_time != null ? `${row.res_time}ms` : (row.response_time != null ? `${row.response_time}ms` : (row.responseTime ?? '-')),
			time: formatTime(row.create_time ?? row.created_at ?? row.creation_date ?? row.time ?? '-'),
			size: row.size != null ? `${row.size} B` : row.size_str ?? row.size ?? '-',
			details: row.details ?? row.res ?? row.body
		}));
	} catch (e) {
		console.error('加载调试记录失败:', e);
		debugRecordList.value = [];
	}
};

const debugRecordDetailDialogVisible = ref(false);
const currentDebugRecord = ref<any | null>(null);

const showDebugRecordDetail = (row: any) => {
	currentDebugRecord.value = row;
	debugRecordDetailDialogVisible.value = true;
};

// 加载接口文档
const loadApiDoc = () => {
	apiDocInfo.value = {
		name: props.apiData.name || '接口名称',
		url: req.value.url || '/api/example',
		method: getMethodName(req.value.method),
		description: '接口描述信息',
		requestParams: req.value.params || [],
		requestHeaders: req.value.header || [],
		requestBody: req.value.body || '',
		responseExample: res.value.body || {}
	};
};

// 获取方法名称
const getMethodName = (methodValue: number) => {
	const method = method_list.value.find(m => m.value === methodValue);
	return method ? method.name : 'GET';
};

// 处理工具箱命令
const handleToolboxCommand = (command: string) => {
	switch (command) {
		case 'params_dependency':
			openParamsDependency();
			break;
		case 'direct_db':
			openDirectDatabase();
			break;
		case 'public_functions':
			openPublicFunctions();
			break;
		case 'error_code':
			openErrorCodeManagement();
			break;
		case 'env_management':
			openEnvironmentManagement();
			break;
	}
};
// 打开参数依赖管理
const openParamsDependency = () => {
	paramsDepDialogVisible.value = true;
	// 加载参数依赖数据
	loadParamsDependency();
};

// 打开直连数据库管理
const openDirectDatabase = () => {
	directDbDialogVisible.value = true;
	// 加载数据库连接数据
	loadDirectDatabase();
};

// 打开公共函数管理
const openPublicFunctions = () => {
	publicFuncDialogVisible.value = true;
	// 加载公共函数数据
	loadPublicFunctions();
};

// 打开错误码管理
const openErrorCodeManagement = () => {
	errorCodeDialogVisible.value = true;
	// 加载错误码数据
	loadErrorCodes();
};

// 打开环境管理
const openEnvironmentManagement = () => {
	envManageDialogVisible.value = true;
	// 加载环境数据
	loadEnvironments();
};

// 加载数据的函数
const loadParamsDependency = async () => {
	try {
		const res: any = await api_params({ currentPage: 1, pageSize: 100, search: {} });
		const data = res?.data;
		const list: any[] = Array.isArray(data?.content) ? data.content : (Array.isArray(data) ? data : []);
		paramsDepList.value = list.map((row: any) => ({
			id: row.id,
			name: row.name,
			description: row.description ?? '',
			// 以字符串形式展示，避免 [object Object]
			value: typeof row.value === 'string' ? row.value : JSON.stringify(row.value ?? {}, null, 2)
		}));
	} catch (e) {
		console.error('加载参数依赖失败:', e);
		paramsDepList.value = [];
	}
};

const loadDirectDatabase = () => {
	// 数据源统一由父组件传入的 local_db_list，在弹窗中仅做展示
	directDbList.value = Array.isArray(local_db_list) ? local_db_list : [];
};

const loadPublicFunctions = () => {
	// 模拟公共函数数据
	publicFuncList.value = [
		{ id: 1, name: '${randomUuid()}', description: '生成随机UUID', example: 'uuid: 550e8400-e29b-41d4-a716-446655440000' },
		{ id: 2, name: '${timestamp()}', description: '获取当前时间戳', example: 'timestamp: 1640995200000' },
		{ id: 3, name: '${randomString(num)}', description: '生成指定长度随机字符串', example: 'randomString(8): AbC12345' }
	];
};

const loadErrorCodes = () => {
	// 模拟错误码数据
	errorCodeList.value = [
		{ id: 1, code: 200, message: '请求成功', description: '操作成功完成' },
		{ id: 2, code: 400, message: '请求参数错误', description: '请求参数格式不正确' },
		{ id: 3, code: 401, message: '未授权访问', description: '用户未登录或token无效' },
		{ id: 4, code: 500, message: '服务器内部错误', description: '服务器处理请求时发生错误' }
	];
};

const loadEnvironments = () => {
	// 模拟环境数据
	envList.value = [
		{ id: 1, name: '开发环境', host: 'http://dev.api.com', description: '开发测试环境' },
		{ id: 2, name: '测试环境', host: 'http://test.api.com', description: '功能测试环境' },
		{ id: 3, name: '生产环境', host: 'http://api.com', description: '正式生产环境' }
	];
};
</script>
<template>
	<div class="api-detail-container">
		<el-card class="api-detail-card">
			<div class="api-detail-content">
				<div class="api-detail-header">
					<div style="border: 1px solid #e4e7ed; width: 100%; padding: 5px; border-radius: 5px">
						<div style="display: flex; justify-content: space-between; align-items: center;">
							<div style="display: flex; align-items: center;">
								<el-select v-model="req.method" class="method-select" placeholder="选择请求方法" style="width: 120px" :style="{ '--method-color': currentMethodColor }">
									<el-option
										v-for="(method, index) in method_list"
										:key="index"
										:label="method.name"
										:value="method.value"
									>
										<span :style="{ color: method.color, 'font-weight': 600 }">{{ method.name }}</span>
									</el-option>
								</el-select>
								<el-input v-model="req.url" placeholder="请输入请求地址" clearable style="width: 400px; margin-left: 10px; margin-right: 10px">
								</el-input>
								<el-button type="primary" @click="sendRequest" style="margin-right: 8px">发送请求</el-button>
								<el-dropdown @command="handleSaveCommand" style="margin-right: 8px">
									<el-button type="success">
										保存项 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
									</el-button>
									<template #dropdown>
										<el-dropdown-menu>
											<el-dropdown-item command="save">直接保存</el-dropdown-item>
											<el-dropdown-item command="saveAsCase">保存为用例</el-dropdown-item>
										</el-dropdown-menu>
									</template>
								</el-dropdown>
								<el-button type="primary" plain @click="showApiDoc" style="margin-right: 4px">接口文档</el-button>
								<el-button type="success" plain @click="showDebugRecord" style="margin-right: 4px">调试记录</el-button>
								<el-button type="warning" plain @click="showEditRecord">编辑记录</el-button>
								<el-dropdown @command="handleToolboxCommand" style="margin-left: 8px">
									<el-button type="info" size="small">
										工具箱 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
									</el-button>
									<template #dropdown>
										<el-dropdown-menu>
											<el-dropdown-item command="env_management">
												<el-tag type="primary" effect="dark" size="small">环境</el-tag>&nbsp;环境管理
											</el-dropdown-item>
											<el-dropdown-item command="error_code">
												<el-tag type="warning" effect="dark" size="small">码</el-tag>&nbsp;错误码管理
											</el-dropdown-item>
											<el-dropdown-item command="public_functions">
												<el-tag type="success" effect="dark" size="small">函</el-tag>&nbsp;公共函数
											</el-dropdown-item>
											<el-dropdown-item command="direct_db">
												<el-tag type="info" effect="dark" size="small">DB</el-tag>&nbsp;直连数据库
											</el-dropdown-item>
											<el-dropdown-item command="params_dependency">
												<el-tag type="danger" effect="dark" size="small">参</el-tag>&nbsp;参数依赖
											</el-dropdown-item>
										</el-dropdown-menu>
									</template>
								</el-dropdown>
							</div>
						</div>
					</div>
				</div>

				<div class="api-detail-body">
					<div class="request-section">
						<div style="border: 1px solid #e4e7ed; border-radius: 5px; width: 100%; padding-left: 10px; height: 100%">
							<el-tabs v-model="req_active" class="demo-tabs" style="height: 100%">
								<el-tab-pane label="Params" name="params">
									<template #label>
										<el-badge :show-zero="false" :value="req.params.length" :offset="[13, 2]" type="primary"> Params </el-badge>
									</template>
									<div style="width: 100%; overflow: auto; height: calc(100% - 20px)">
										<div v-for="(params, index) in req.params" :key="index" style="padding-block-end: 5px">
											<el-checkbox v-model="params.status" />
											<el-input v-model="params.key" placeholder="请输入参数key" style="width: 40%; padding-left: 10px">
											</el-input>
											<el-input v-model="params.value" placeholder="请输入参数value" style="width: 40%; padding-left: 10px; padding-right: 10px">
											</el-input>
											<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeParam(index)">删除</el-button>
										</div>
										<el-button type="text" @click="addParam">添加参数</el-button>
									</div>
								</el-tab-pane>
								<el-tab-pane label="Header" name="header">
									<template #label>
										<el-badge :show-zero="false" :value="req.header.length" :offset="[13, 2]" type="primary"> Header </el-badge>
									</template>
									<div style="width: 100%; overflow: auto; height: calc(100% - 20px)">
										<div v-for="(header, index) in req.header" :key="index" style="padding-block-end: 5px">
											<el-checkbox v-model="header.status" />
											<el-input v-model="header.key" placeholder="请输入参数key" style="width: 40%; padding-left: 10px">
											</el-input>
											<el-input v-model="header.value" placeholder="请输入参数value" style="width: 40%; padding-left: 10px; padding-right: 10px">
											</el-input>
											<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeHeader(index)">删除</el-button>
										</div>
										<el-button type="text" @click="addHeader">添加Header</el-button>
									</div>
								</el-tab-pane>
								<el-tab-pane label="Body" name="body">
									<div style="width: 100%; height: calc(100% - 20px)">
										<div style="width: 10%; float: right; padding-right: 40px; padding-left: 10px">
											<el-select style="width: 120%; padding-block-end: 30px" v-model="req.params_id" clearable placeholder="非必选：选择参数依赖">
												<el-option v-for="(params, index) in params_list" :key="index" :label="params.name" :value="params.id">
												</el-option>
											</el-select>
											<el-radio-group v-model="req.body_type">
												<el-radio :label="1" size="small">None</el-radio>
												<el-radio :label="2" size="small">JSON</el-radio>
												<el-radio :label="3" size="small">form-data</el-radio>
												<el-radio :label="4" size="small">form-urlencoded</el-radio>
												<el-radio :label="5" size="small">binary</el-radio>
											</el-radio-group>
										</div>
										<div v-if="req.body_type === 2" style="width: 85%; float: left">
											<JsonEditor v-model:value="req.body" height="calc(100% - 20px)" />
										</div>
										<div v-if="req.body_type === 3" style="width: 85%; float: left">
											<div v-for="(form, index) in req.form_data" :key="index" style="padding-block-end: 5px">
												<el-checkbox v-model="form.status" />
												<el-input v-model="form.key" placeholder="请输入参数key" style="width: 40%; padding-left: 10px">
												</el-input>
												<el-input v-model="form.value" placeholder="请输入参数value" style="width: 40%; padding-left: 10px; padding-right: 10px">
												</el-input>
												<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeFormData(index)">删除</el-button>
											</div>
											<el-button type="text" @click="addFormData">添加form-data</el-button>
										</div>
										<div v-if="req.body_type === 4" style="width: 85%; float: left">
											<div v-for="(form, index) in req.form_urlencoded" :key="index" style="padding-block-end: 5px">
												<el-checkbox v-model="form.status" />
												<el-input v-model="form.key" placeholder="请输入参数key" style="width: 40%; padding-left: 10px">
												</el-input>
												<el-input v-model="form.value" placeholder="请输入参数value" style="width: 40%; padding-left: 10px; padding-right: 10px">
												</el-input>
												<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeFormUrlencoded(index)">删除</el-button>
											</div>
											<el-button type="text" @click="addFormUrlencoded">添加form-urlencoded</el-button>
										</div>
										<div v-if="req.body_type === 5" style="height: calc(100% - 20px); overflow: auto; width: 84%">
											<div style="width: 100%; padding-right: 10px;">
												<el-upload
													:show-file-list="false"
													:limit="1"
													:http-request="uploadBinaryFile"
												>
													<el-button type="primary" plain size="small">选择文件并上传</el-button>
												</el-upload>
												<div class="h-10px"></div>
											</div>
											<div style="width: 60%; float: left">
												<el-tag
													v-for="(file, index) in req.file_path"
													:key="file + index"
													type="success"
													closable
													style="margin-right: 8px; margin-bottom: 6px;"
													@close="req.file_path.splice(index, 1)"
												>
													{{ file }}
												</el-tag>
											</div>
										</div>
									</div>
								</el-tab-pane>
								<el-tab-pane name="before">
									<template #label>
										<el-badge :show-zero="false" :value="req.before.length" :offset="[10, 2]" type="primary"> 前置操作 </el-badge>
									</template>
									<div class="op-pane">
										<div class="op-scroll">
											<el-collapse accordion>
												<el-collapse-item v-for="(pre, index) in req.before" :key="index">
													<template #title>
														<span style="display: flex; align-items: center;">
															<el-button type="text" size="small" style="color: rgb(219, 97, 120); margin-right: 8px;" @click.stop="removeBefore(index)">
																<el-icon><Delete /></el-icon>
															</el-button>
															<span v-if="pre.type === 1">
																<el-icon style="padding-right: 5px" width="14" height="14">
																	<Connection />
																</el-icon>
																<span>{{ index + 1 + ". 预请求接口：" + pre.title }}</span>
															</span>
															<span v-if="pre.type === 2">
																<el-icon class="header-icon">
																	<Operation />
																</el-icon>
																{{ index + 1 + ". 预设变量：" + pre.name + " 赋值等于 " + pre.value }}
															</span>
															<span v-if="pre.type === 3">
																<el-icon class="header-icon" style="">
																	<Clock />
																</el-icon>
																{{ index + 1 + ". 设置等待时长：" + pre.wait_time + "秒" }}
															</span>
															<span v-if="pre.type === 4">
																<el-icon class="header-icon">
																	<EditPen />
																</el-icon>
																{{ index + 1 + ". 自定义脚本" + pre.title }}
															</span>
														</span>
													</template>
													<div v-if="pre.type === 1">
														<div>
															<el-form inline>
																<el-form-item label="操作名称：">
																	<el-input style="width: 300px" v-model="pre.title" placeholder="请输入前置名称"></el-input>
																</el-form-item>
																<el-form-item label="选择环境：">
																	<el-select placeholder="请选择环境地址" v-model="pre.env_id" style="width: 300px">
																		<el-option v-for="(env, index) in env_list" :key="index" :label="env.name" :value="env.id"></el-option>
																	</el-select>
																</el-form-item>
																<el-form-item label="选择接口：">
																	<!-- 前置-预请求接口：后端需要菜单(type=3)的 id 路径（不是 api_id） -->
																	<el-cascader :options="tree_list" v-model="pre.api_id" :props="{ value: 'id', label: 'name', children: 'children' }" style="width: 705px"></el-cascader>
																</el-form-item>
															</el-form>
														</div>
													</div>
													<div v-if="pre.type === 2">
														<el-form inline>
															<el-form-item label="变量名：">
																<el-input style="width: 200px" v-model="pre.name" placeholder="请输入变量名"></el-input>
															</el-form-item>
															<el-form-item label="变量类型：">
																<el-select placeholder="请选择变量类型" v-model="pre.env_type" style="width: 200px">
																	<el-option v-for="(type, index) in val_type_list" :key="index" :label="type.name" :value="type.value"></el-option>
																</el-select>
															</el-form-item>
															<el-form-item label="预期值：">
																<el-input style="width: 200px" v-model="pre.value" placeholder="请输入预期值"></el-input>
															</el-form-item>
														</el-form>
													</div>
													<div v-if="pre.type === 3">
														<div>
															<el-form inline>
																<el-form-item label="等待时间(秒)：">
																	<el-input-number style="width: 200px" :min="0" :max="60" v-model="pre.wait_time" placeholder="请输入等待时间"></el-input-number>
																</el-form-item>
															</el-form>
														</div>
													</div>
													<div v-if="pre.type === 4">
														<div>
															<div>
																<el-input v-model="pre.code" type="textarea" :rows="6" placeholder="请输入Python代码" />
															</div>
														</div>
													</div>
												</el-collapse-item>
											</el-collapse>
										</div>
										<div class="op-footer">
											<el-dropdown>
												<el-button type="primary" size="small">
													添加前置操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
												</el-button>
												<template #dropdown>
													<el-dropdown-menu>
														<el-dropdown-item @click="addBefore(1)">预请求接口</el-dropdown-item>
														<el-dropdown-item @click="addBefore(2)">预设变量</el-dropdown-item>
														<el-dropdown-item @click="addBefore(3)">等待时长</el-dropdown-item>
														<el-dropdown-item @click="addBefore(4)">自定义脚本</el-dropdown-item>
													</el-dropdown-menu>
												</template>
											</el-dropdown>
										</div>
									</div>
								</el-tab-pane>
								<el-tab-pane name="after">
									<template #label>
										<el-badge :show-zero="false" :value="req.after.length" :offset="[10, 2]" type="primary"> 后置操作 </el-badge>
									</template>
									<div class="op-pane">
										<div class="op-scroll">
											<el-collapse accordion>
												<el-collapse-item v-for="(after, index) in req.after" :key="index">
													<template #title>
														<span style="display: flex; align-items: center;">
															<el-button type="text" size="small" style="color: rgb(219, 97, 120); margin-right: 8px;" @click.stop="removeAfter(index)">
																<el-icon><Delete /></el-icon>
															</el-button>
															<span v-if="after.type === 1">
																<el-icon class="header-icon">
																	<Operation />
																</el-icon>
																{{ index + 1 + ". 提取变量：提取 ' " + after.name + " ' 赋值给 ' " + after.value + " '" }}
															</span>
															<span v-if="after.type === 2">
																<el-icon class="header-icon" style="">
																	<Clock />
																</el-icon>
																{{ index + 1 + ". 设置等待时长：" + after.wait_time + "秒" }}
															</span>
														</span>
													</template>
													<div v-if="after.type === 1">
														<el-form inline>
															<el-form-item>
																<template #label>
																	<el-tooltip :content="tips" raw-content>
																		<el-button type="text" style="color: #000" :icon="InfoFilled"></el-button>
																	</el-tooltip>
																	路径:
																</template>
																<el-input style="width: 300px" v-model="after.name" placeholder="请输入路径"></el-input>
															</el-form-item>
															<el-form-item label="提取目标:">
																<el-select placeholder="请选择提取目标" v-model="after.res_type" style="width: 300px">
																	<el-option v-for="(res, index) in res_type_list" :key="index" :label="res.name" :value="res.value"></el-option>
																</el-select>
															</el-form-item>
															<el-form-item label="变量类型:">
																<el-select placeholder="请选择变量类型" v-model="after.env_type" style="width: 300px">
																	<el-option v-for="(type, index) in val_type_list" :key="index" :label="type.name" :value="type.value"></el-option>
																</el-select>
															</el-form-item>
															<el-form-item label="变量名:">
																<el-input style="width: 300px" v-model="after.value" placeholder="请输入变量名"></el-input>
															</el-form-item>
														</el-form>
													</div>
													<div v-if="after.type === 2">
														<div>
															<el-form inline>
																<el-form-item label="等待时间(秒)：">
																	<el-input-number style="width: 200px" :min="0" :max="60" v-model="after.wait_time" placeholder="请输入等待时间"></el-input-number>
																</el-form-item>
															</el-form>
														</div>
													</div>
												</el-collapse-item>
											</el-collapse>
										</div>
										<div class="op-footer">
											<el-dropdown>
												<el-button type="primary" size="small">
													添加后置操作 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
												</el-button>
												<template #dropdown>
													<el-dropdown-menu>
														<el-dropdown-item @click="addAfter(1)">提取变量</el-dropdown-item>
														<el-dropdown-item @click="addAfter(2)">等待时长</el-dropdown-item>
													</el-dropdown-menu>
												</template>
											</el-dropdown>
										</div>
									</div>
								</el-tab-pane>
								<el-tab-pane name="assert">
									<template #label>
										<el-badge :show-zero="false" :value="req.assert.length" :offset="[10, 2]" type="primary"> 断言 </el-badge>
									</template>
									<div class="op-pane">
										<div class="op-scroll">
											<el-collapse accordion>
												<el-collapse-item v-for="(assert, index) in req.assert" :key="index">
													<template #title>
														<span style="display: flex; align-items: center;">
															<el-button type="text" size="small" style="color: rgb(219, 97, 120); margin-right: 8px;" @click.stop="removeAssert(index)">
																<el-icon><Delete /></el-icon>
															</el-button>
															<span v-if="assert.type === 1">
																<el-icon class="header-icon">
																	<CircleCheck />
																</el-icon>
																{{ index + 1 + ". 响应断言：断言 ' " + assert.name + " ' 等于 ' " + assert.value + " '" }}
															</span>
															<span v-if="assert.type === 2">
																<el-icon class="header-icon">
																	<Coin />
																</el-icon>
																{{ index + 1 + ". ops-数据库断言：查询表 ' " + assert.ops_db_table + " ' 条件： " + "' " + assert.ops_db_where + " '" }}
															</span>
															<span v-if="assert.type === 3">
																<el-icon class="header-icon">
																	<Coin />
																</el-icon>
																{{ index + 1 + ". ops-redis断言：查询key ' " + assert.ops_redis_key + " '" }}
															</span>
															<span v-if="assert.type === 4">
																<el-icon class="header-icon">
																	<Coin />
																</el-icon>
																{{ index + 1 + ". 直连-数据库断言：查询表 ' " + assert.local_db_table + " ' 条件： " + "' " + assert.local_db_where + " '" }}
															</span>
														</span>
													</template>
													<div v-if="assert.type === 1">
														<el-form inline>
															<el-form-item>
																<template #label>
																	<el-tooltip :content="tips" raw-content>
																		<el-button type="text" style="color: #000" :icon="InfoFilled"></el-button>
																	</el-tooltip>
																	路径:
																</template>
																<el-input style="width: 220px" v-model="assert.name" placeholder="请输入路径"></el-input>
															</el-form-item>
															<el-form-item label="断言对象:">
																<el-select placeholder="请选择断言对象" v-model="assert.res_type" style="width: 220px">
																	<el-option v-for="(res, index) in res_type_list" :key="index" :label="res.name" :value="res.value"></el-option>
																</el-select>
															</el-form-item>
															<el-form-item label="预期值:">
																<el-input style="width: 220px" v-model="assert.value" placeholder="请输入预期值"></el-input>
															</el-form-item>
														</el-form>
													</div>
													<div v-if="assert.type === 2">
														<div style="width: 100%">
															<div style="width: 40%; float: left; padding-right: 50px">
																<el-form>
																	<el-form-item label="添加ops-数据库断言配置:">
																		<el-button type="primary" plain size="small" @click="addOpsDbAssertConfig(assert.ops_db_assert)">
																			添加ops-数据库断言配置
																		</el-button>
																	</el-form-item>
																	<el-form-item label="选择数据库:">
																		<el-select v-model="assert.ops_db">
																			<el-option v-for="(db, index) in local_db_list" :key="index" :label="db.name" :value="db.id"></el-option>
																		</el-select>
																	</el-form-item>
																	<el-form-item label="数据库表:">
																		<el-input v-model="assert.ops_db_table" placeholder="请输入数据库表名"></el-input>
																	</el-form-item>
																	<el-form-item label="条件(where):">
																		<el-input v-model="assert.ops_db_where" placeholder="请输入筛选条件，与where条件一致，例：game_id=50001 and xxx=xxx"></el-input>
																	</el-form-item>
																</el-form>
															</div>
															<div style="width: 50%; float: left; border: 1px solid #e4e7ed; padding: 5px; height: 150px; overflow-y: auto; border-radius: 5px;">
																<div v-for="(form, index) in assert.ops_db_assert" :key="index" style="padding-block-end: 5px">
																	<el-input v-model="form.name" placeholder="请输入表字段名" style="width: 30%; padding-left: 10px">
																	</el-input>
																	<el-select placeholder="请断言目标" v-model="form.type" style="width: 25%; padding-left: 10px">
																		<el-option v-for="(res, index) in res_type_list" :key="index" :label="res.name" :value="res.value"></el-option>
																	</el-select>
																	<el-input v-model="form.value" placeholder="请输入预期值" style="width: 30%; padding-left: 10px; padding-right: 10px">
																	</el-input>
																	<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeOpsDbAssertConfig(assert.ops_db_assert, index)">删除</el-button>
																</div>
															</div>
														</div>
													</div>
													<div v-if="assert.type === 3">
														<div style="width: 100%">
															<div style="width: 40%; float: left; padding-right: 50px">
																<el-form>
																	<el-form-item label="添加ops-redis断言配置:">
																		<el-button type="primary" plain size="small" @click="addOpsRedisAssertConfig(assert.ops_redis_assert)">
																			添加ops-redis断言配置
																		</el-button>
																	</el-form-item>
																	<el-form-item label="选择Redis:">
																		<el-select v-model="assert.ops_redis">
																			<el-option v-for="(redis, index) in redis_example_list" :key="index" :label="redis" :value="redis"></el-option>
																		</el-select>
																	</el-form-item>
																	<el-form-item label="Redis Key:">
																		<el-input v-model="assert.ops_redis_key" placeholder="请输入Redis Key"></el-input>
																	</el-form-item>
																</el-form>
															</div>
															<div style="width: 50%; float: left; border: 1px solid #e4e7ed; padding: 5px; height: 150px; overflow-y: auto; border-radius: 5px;">
																<div v-for="(form, index) in assert.ops_redis_assert" :key="index" style="padding-block-end: 5px">
																	<el-input v-model="form.name" placeholder="请输入字段名" style="width: 30%; padding-left: 10px">
																	</el-input>
																	<el-select placeholder="请断言目标" v-model="form.type" style="width: 25%; padding-left: 10px">
																		<el-option v-for="(res, index) in res_type_list" :key="index" :label="res.name" :value="res.value"></el-option>
																	</el-select>
																	<el-input v-model="form.value" placeholder="请输入预期值" style="width: 30%; padding-left: 10px; padding-right: 10px">
																	</el-input>
																	<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeOpsRedisAssertConfig(assert.ops_redis_assert, index)">删除</el-button>
																</div>
															</div>
														</div>
													</div>
													<div v-if="assert.type == 4">
														<div style="width: 100%">
															<div style="width: 40%; float: left; padding-right: 50px">
																<el-form>
																	<el-form-item label="添加直连-数据库断言配置:">
																		<el-button type="primary" plain size="small" @click="addDbAssertConfig(assert.local_db_assert)">
																			添加直连-数据库断言配置
																		</el-button>
																	</el-form-item>
																	<el-form-item label="选择数据库:">
																		<el-select v-model="assert.local_db">
																			<el-option v-for="(db, index) in local_db_list" :key="index" :label="db.name" :value="db.id"></el-option>
																		</el-select>
																	</el-form-item>
																	<el-form-item label="数据库表:">
																		<el-input v-model="assert.local_db_table" placeholder="请输入数据库表名"></el-input>
																	</el-form-item>
																	<el-form-item label="条件(where):">
																		<el-input v-model="assert.local_db_where" placeholder="请输入筛选条件，与where条件一致，例：game_id=50001 and xxx=xxx"></el-input>
																	</el-form-item>
																</el-form>
															</div>
															<div style="width: 50%; float: left; border: 1px solid #e4e7ed; padding: 5px; height: 150px; overflow-y: auto; border-radius: 5px;">
																<div v-for="(form, index) in assert.local_db_assert" :key="index" style="padding-block-end: 5px">
																	<el-input v-model="form.name" placeholder="请输入表字段名" style="width: 30%; padding-left: 10px">
																	</el-input>
																	<el-select placeholder="请断言目标" v-model="form.type" style="width: 25%; padding-left: 10px">
																		<el-option v-for="(res, index) in res_type_list" :key="index" :label="res.name" :value="res.value"></el-option>
																	</el-select>
																	<el-input v-model="form.value" placeholder="请输入预期值" style="width: 30%; padding-left: 10px; padding-right: 10px">
																	</el-input>
																	<el-button type="text" size="small" style="color: rgb(219, 97, 120)" @click="removeDbAssertConfig(assert.local_db_assert, index)">删除</el-button>
																</div>
															</div>
														</div>
													</div>
												</el-collapse-item>
											</el-collapse>
										</div>
										<div class="op-footer">
											<el-dropdown>
												<el-button type="primary" size="small">
													添加断言 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
												</el-button>
												<template #dropdown>
													<el-dropdown-menu>
														<el-dropdown-item @click="addAssert(1)">
															<el-icon><CircleCheck /></el-icon>响应结果断言
														</el-dropdown-item>
														<el-dropdown-item @click="addAssert(2)">
															<el-icon><Coin /></el-icon>ops-数据库断言
														</el-dropdown-item>
														<el-dropdown-item @click="addAssert(3)">
															<el-icon><Coin /></el-icon>ops-redis断言
														</el-dropdown-item>
														<el-dropdown-item @click="addAssert(4)">
															<el-icon><Coin /></el-icon>直连-数据库断言
														</el-dropdown-item>
													</el-dropdown-menu>
												</template>
											</el-dropdown>
										</div>
									</div>
								</el-tab-pane>
								<el-tab-pane label="配置" name="config">
									<div>
										<el-form v-model="req.config" label-position="right">
											<el-form-item label="重试次数(次)：">
												<el-input-number v-model="req.config.retry"></el-input-number>
											</el-form-item>
											<el-form-item label="接口连接超时(秒)：">
												<el-input-number v-model="req.config.req_timeout"></el-input-number>
											</el-form-item>
											<el-form-item label="结果读取超时(秒)：">
												<el-input-number v-model="req.config.res_timeout"></el-input-number>
											</el-form-item>
										</el-form>
									</div>
								</el-tab-pane>
							</el-tabs>
						</div>
					</div>
					<div class="response-section">
						<div style="border: 1px solid #e4e7ed; border-radius: 5px; width: 100%; padding-left: 10px; height: 100%">
							<el-tabs v-model="res_active" class="demo-tabs" style="height: 100%">
								<el-tab-pane label="响应-结果" name="res">
									<div class="json-panel">
										<vue-json-pretty v-model:data="res.body" :height="resJsonHeight" :showIcon="true" :showLine="true" :virtual="true" :showSelectController="true" />
									</div>
								</el-tab-pane>
								<el-tab-pane label="响应-Header" name="res_log">
									<div class="json-panel">
										<vue-json-pretty v-model:data="res.header" :height="resJsonHeight" :showIcon="true" :showLine="true" :virtual="true" :showSelectController="true" />
									</div>
								</el-tab-pane>
								<el-tab-pane name="before_res">
									<template #label>
										<el-badge :show-zero="false" :value="res.before.length" :offset="[10, 2]" type="danger">前置操作结果</el-badge>
									</template>
									<div style="padding-left: 10px; height: calc(100% - 20px); overflow-y: auto">
										<el-collapse>
											<el-collapse-item v-for="(before, index) in res.before" :key="index">
												<template #title>
													<span v-if="before.status === 0" style="color: rgb(219, 97, 120)">{{ index + 1 + ". " + before.message }}</span>
													<span v-if="before.status === 1" style="color: rgb(46, 134, 234)">{{ index + 1 + ". " + before.message }}</span>
												</template>
												<div v-if="before.type === 1">
													<vue-json-pretty v-model:data="before.content.body" :height="160" :showIcon="true" :showLine="true" :virtual="true" :showSelectController="true" />
												</div>
											</el-collapse-item>
										</el-collapse>
									</div>
								</el-tab-pane>
								<el-tab-pane name="after_res">
									<template #label>
										<el-badge :show-zero="false" :value="res.after.length" :offset="[10, 2]" type="danger">后置操作结果</el-badge>
									</template>
									<div style="padding-left: 10px; height: calc(100% - 20px); overflow-y: auto">
										<el-collapse>
											<el-collapse-item v-for="(after, index) in res.after" :key="index">
												<template #title>
													<span v-if="after.status === 0" style="color: rgb(219, 97, 120)">{{ index + 1 + ". " + after.message }}</span>
													<span v-if="after.status === 1" style="color: rgb(46, 134, 234)">{{ index + 1 + ". " + after.message }}</span>
												</template>
											</el-collapse-item>
										</el-collapse>
									</div>
								</el-tab-pane>
								<el-tab-pane label="断言结果" name="assert_res">
									<template #label>
										<el-badge :show-zero="false" :value="res.assert.length" :offset="[10, 2]" type="danger">断言结果</el-badge>
									</template>
									<div style="padding-left: 10px; height: calc(100% - 20px); overflow-y: auto">
										<el-collapse>
											<el-collapse-item v-for="(assert, index) in res.assert" :key="index">
												<template #title>
													<span v-if="assert.status === 0" style="color: rgb(219, 97, 120)">{{ index + 1 + ". " + assert.message }}</span>
													<span v-if="assert.status === 1" style="color: rgb(46, 134, 234)">{{ index + 1 + ". " + assert.message }}</span>
												</template>
											</el-collapse-item>
										</el-collapse>
									</div>
								</el-tab-pane>
								<el-tab-pane disabled style="float: right">
									<template #label>
										<div class="tab-info">
											<el-icon style="font-size: 16px"><View /></el-icon>
											<span slot="code" class="code">状态码：{{ res.code }}</span>
										</div>
									</template>
								</el-tab-pane>
								<el-tab-pane disabled>
									<template #label>
										<div class="tab-info">
											<el-icon style="font-size: 16px"><Document /></el-icon>
											<span slot="size" class="size">资源大小：{{ res.size }} B</span>
										</div>
									</template>
								</el-tab-pane>
								<el-tab-pane disabled>
									<template #label>
										<div class="tab-info">
											<el-icon style="font-size: 16px"><Clock /></el-icon>
											<span slot="size" class="size">响应时间：{{ res.res_time }} ms</span>
										</div>
									</template>
								</el-tab-pane>
							</el-tabs>
						</div>
					</div>
				</div>
			</div>
		</el-card>
	</div>
	<!-- 参数依赖管理对话框 -->
	<el-dialog v-model="paramsDepDialogVisible" title="参数依赖管理" width="800px" destroy-on-close>
		<el-table :data="paramsDepList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="name" label="参数名称" width="150" />
			<el-table-column prop="description" label="描述" />
			<el-table-column prop="type" label="类型" width="100" />
			<el-table-column label="值" min-width="280" show-overflow-tooltip>
				<template #default="{ row }">
					<el-input :model-value="row.value" type="textarea" :rows="3" readonly />
				</template>
			</el-table-column>
			<el-table-column label="操作" width="120">
				<template #default="{ row }">
					<el-button type="primary" size="small">编辑</el-button>
					<el-button type="danger" size="small">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<template #footer>
			<el-button type="primary">添加参数依赖</el-button>
			<el-button @click="paramsDepDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 直连数据库管理对话框 -->
	<el-dialog v-model="directDbDialogVisible" title="直连数据库管理" width="900px" destroy-on-close>
		<el-table :data="directDbList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="name" label="连接名称" width="120" />
			<el-table-column prop="host" label="主机地址" width="150" />
			<el-table-column prop="port" label="端口" width="80" />
			<el-table-column prop="database" label="数据库" width="120" />
			<el-table-column prop="username" label="用户名" width="100" />
			<el-table-column prop="status" label="状态" width="100">
				<template #default="{ row }">
					<el-tag :type="row.status === '已连接' ? 'success' : 'danger'">{{ row.status }}</el-tag>
				</template>
			</el-table-column>
			<el-table-column label="操作" width="180">
				<template #default="{ row }">
					<el-button type="success" size="small">测试连接</el-button>
					<el-button type="primary" size="small">编辑</el-button>
					<el-button type="danger" size="small">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<template #footer>
			<el-button type="primary">添加数据库连接</el-button>
			<el-button @click="directDbDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 公共函数管理对话框 -->
	<el-dialog v-model="publicFuncDialogVisible" title="公共函数管理" width="800px" destroy-on-close>
		<el-table :data="publicFuncList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="name" label="函数名称" width="200" />
			<el-table-column prop="description" label="描述" />
			<el-table-column prop="example" label="示例" width="250" />
			<el-table-column label="操作" width="120">
				<template #default="{ row }">
					<el-button type="primary" size="small">编辑</el-button>
					<el-button type="danger" size="small">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<template #footer>
			<el-button type="primary">添加公共函数</el-button>
			<el-button @click="publicFuncDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 错误码管理对话框 -->
	<el-dialog v-model="errorCodeDialogVisible" title="错误码管理" width="800px" destroy-on-close>
		<el-table :data="errorCodeList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="code" label="错误码" width="100" />
			<el-table-column prop="message" label="错误信息" width="200" />
			<el-table-column prop="description" label="描述" />
			<el-table-column label="操作" width="120">
				<template #default="{ row }">
					<el-button type="primary" size="small">编辑</el-button>
					<el-button type="danger" size="small">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<template #footer>
			<el-button type="primary">添加错误码</el-button>
			<el-button @click="errorCodeDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 环境管理对话框 -->
	<el-dialog v-model="envManageDialogVisible" title="环境管理" width="700px" destroy-on-close>
		<el-table :data="envList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="name" label="环境名称" width="150" />
			<el-table-column prop="host" label="主机地址" />
			<el-table-column prop="description" label="描述" width="200" />
			<el-table-column label="操作" width="120">
				<template #default="{ row }">
					<el-button type="primary" size="small">编辑</el-button>
					<el-button type="danger" size="small">删除</el-button>
				</template>
			</el-table-column>
		</el-table>
		<template #footer>
			<el-button type="primary">添加环境</el-button>
			<el-button @click="envManageDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>
	<!-- 编辑记录对话框 -->
	<el-dialog v-model="editRecordDialogVisible" title="编辑记录" width="800px" destroy-on-close>
		<el-table :data="editRecordList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="operation" label="操作类型" width="150" />
			<el-table-column prop="user" label="操作人" width="100" />
			<el-table-column prop="time" label="操作时间" width="180" />
			<el-table-column prop="details" label="操作详情" />
		</el-table>
		<template #footer>
			<el-button @click="editRecordDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 调试记录对话框 -->
	<el-dialog v-model="debugRecordDialogVisible" title="调试记录" width="800px" destroy-on-close>
			<el-table :data="debugRecordList" stripe>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="status" label="状态" width="100">
				<template #default="{ row }">
					<el-tag :type="row.status === '成功' ? 'success' : 'danger'">{{ row.status }}</el-tag>
				</template>
			</el-table-column>
			<el-table-column prop="statusCode" label="状态码" width="100" />
			<el-table-column prop="responseTime" label="响应时间" width="120" />
			<el-table-column prop="size" label="响应大小" width="120" />
			<el-table-column prop="time" label="调试时间" width="180" />
			<el-table-column label="操作" width="100">
				<template #default="{ row }">
					<el-button type="primary" size="small" @click="showDebugRecordDetail(row)">查看详情</el-button>
				</template>
			</el-table-column>
		</el-table>
		<template #footer>
			<el-button @click="debugRecordDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 调试记录详情 -->
	<el-dialog v-model="debugRecordDetailDialogVisible" title="调试详情" width="800px" destroy-on-close>
		<div v-if="currentDebugRecord">
			<p style="margin-bottom: 8px;">状态：{{ currentDebugRecord.status }} / 状态码：{{ currentDebugRecord.statusCode }}</p>
			<p style="margin-bottom: 8px;">时间：{{ currentDebugRecord.time }} / 大小：{{ currentDebugRecord.size }}</p>
			<vue-json-pretty v-model:data="currentDebugRecord.details" :height="400" :showIcon="true" :showLine="true" :virtual="true" :showSelectController="true" />
		</div>
		<template #footer>
			<el-button @click="debugRecordDetailDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>

	<!-- 接口文档对话框 -->
	<el-dialog v-model="apiDocDialogVisible" title="接口文档" width="900px" destroy-on-close>
		<div class="api-doc-content">
			<el-descriptions title="基本信息" :column="2" border>
				<el-descriptions-item label="接口名称">{{ apiDocInfo.name }}</el-descriptions-item>
				<el-descriptions-item label="请求方法">{{ apiDocInfo.method }}</el-descriptions-item>
				<el-descriptions-item label="请求地址" :span="2">{{ apiDocInfo.url }}</el-descriptions-item>
				<el-descriptions-item label="接口描述" :span="2">{{ apiDocInfo.description }}</el-descriptions-item>
			</el-descriptions>

			<el-divider content-position="left">请求参数</el-divider>
			<el-table :data="apiDocInfo.requestParams" stripe size="small">
				<el-table-column prop="key" label="参数名" />
				<el-table-column prop="value" label="示例值" />
				<el-table-column prop="status" label="是否必填" width="100">
					<template #default="{ row }">
						<el-tag :type="row.status ? 'success' : 'info'">{{ row.status ? '必填' : '可选' }}</el-tag>
					</template>
				</el-table-column>
			</el-table>

			<el-divider content-position="left">请求头</el-divider>
			<el-table :data="apiDocInfo.requestHeaders" stripe size="small">
				<el-table-column prop="key" label="Header名" />
				<el-table-column prop="value" label="示例值" />
				<el-table-column prop="status" label="是否必填" width="100">
					<template #default="{ row }">
						<el-tag :type="row.status ? 'success' : 'info'">{{ row.status ? '必填' : '可选' }}</el-tag>
					</template>
				</el-table-column>
			</el-table>

			<el-divider content-position="left">请求体</el-divider>
			<el-input v-model="apiDocInfo.requestBody" type="textarea" :rows="4" readonly />

			<el-divider content-position="left">响应示例</el-divider>
			<vue-json-pretty :data="apiDocInfo.responseExample" :showIcon="true" :showLine="true" />
		</div>
		<template #footer>
			<el-button type="primary">导出文档</el-button>
			<el-button @click="apiDocDialogVisible = false">关闭</el-button>
		</template>
	</el-dialog>
</template>
<style lang="scss" scoped>
.api-detail-container {
	height: calc(100vh - 100px);
	display: flex;
	flex-direction: column;
	padding: 0;
	margin: 0;
	overflow: hidden;
}

.api-detail-card {
	height: 100%;
	display: flex;
	flex-direction: column;
	margin: 0;
}

.api-detail-card :deep(.el-card__body) {
	height: 100%;
	display: flex;
	flex-direction: column;
	padding: 16px;
}

.api-detail-content {
	height: 100%;
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.api-detail-header {
	flex: 0 0 auto;
	margin-bottom: 10px;
}

.api-detail-body {
	flex: 1 1 auto;
	display: flex;
	flex-direction: column;
	gap: 10px;
	min-height: 0;
	height: 100%;
}

.request-section {
	flex: 0 0 40%;
	min-height: 280px;
}

.response-section {
	flex: 1 1 60%;
	min-height: 360px;
}

.demo-tabs {
	height: 100%;
}

.method-select :deep(.el-input__inner) {
	color: var(--method-color);
	font-weight: 700;
}

.demo-tabs :deep(.el-tabs__content) {
	height: calc(100% - 40px);
	overflow-y: auto;
	padding: 10px;
}

.demo-tabs :deep(.el-tab-pane) {
	height: 100%;
	display: flex;
	flex-direction: column;
	min-height: 0;
}

.op-pane {
	height: 100%;
	display: flex;
	flex-direction: column;
	min-height: 0;
	padding: 0 5px;
}

.op-scroll {
	flex: 1 1 auto;
	min-height: 0;
	overflow-y: auto;
	padding: 5px 0;
}

.op-footer {
	flex: 0 0 auto;
	padding-top: 8px;
	background: var(--el-bg-color);
	position: sticky;
	bottom: 0;
}

.json-panel {
	flex: 1 1 auto;
	min-height: 0;
	height: 100%;
	overflow: auto;
}

.el-collapse-item__content {
	padding-bottom: 5px !important;
}

.el-collapse-item__header {
	height: 35px !important;
}

.code,
.size {
	font-size: 14px;
	color: rgb(45, 23, 241);
	margin-left: 5px;
}

.api-doc-content {
	max-height: 600px;
	overflow-y: auto;
}

.api-doc-content .el-divider {
	margin: 20px 0 10px 0;
}

.tab-info {
	display: flex;
	align-items: center;
	gap: 5px;
}
</style>