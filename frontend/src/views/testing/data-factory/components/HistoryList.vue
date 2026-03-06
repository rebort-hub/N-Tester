<template>
	<div class="history-list-container">
		<!-- 搜索和筛选 -->
		<div class="filter-bar">
			<el-row :gutter="16" align="middle">
				<el-col :span="6">
					<el-input
						v-model="searchKeyword"
						placeholder="搜索工具名称..."
						clearable
						@input="handleSearch"
					>
						<template #prefix>
							<el-icon><Search /></el-icon>
						</template>
					</el-input>
				</el-col>
				<el-col :span="4">
					<el-select
						v-model="filterCategory"
						placeholder="选择分类"
						clearable
						@change="handleFilter"
					>
						<el-option label="全部分类" value="" />
						<el-option label="测试数据" value="test_data" />
						<el-option label="JSON工具" value="json" />
						<el-option label="字符工具" value="string" />
						<el-option label="编码工具" value="encoding" />
						<el-option label="随机工具" value="random" />
						<el-option label="加密工具" value="encryption" />
						<el-option label="Crontab工具" value="crontab" />
					</el-select>
				</el-col>
				<el-col :span="4">
					<el-select
						v-model="selectedTags"
						placeholder="选择标签"
						multiple
						clearable
						@change="handleFilter"
					>
						<el-option
							v-for="tag in availableTags"
							:key="tag"
							:label="tag"
							:value="tag"
						/>
					</el-select>
				</el-col>
				<el-col :span="3">
					<el-button @click="clearFilters">清空筛选</el-button>
				</el-col>
				<el-col :span="7">
					<div class="batch-actions-inline" :class="{ 'has-selection': selectedRecords.length > 0 }">
						<span class="selection-info">
							<span 
								class="selection-text" 
								:class="{ 'has-selection': selectedRecords.length > 0 }"
							>
								<span v-if="selectedRecords.length > 0">
									已选择 {{ selectedRecords.length }} 条
								</span>
								<span v-else>
									共 {{ total }} 条记录
								</span>
							</span>
						</span>
						<div class="batch-buttons">
							<el-button
								size="small"
								type="danger"
								:disabled="selectedRecords.length === 0"
								@click="batchDelete"
							>
								<el-icon><Delete /></el-icon>
								批量删除
							</el-button>
							<el-button size="small" @click="clearSelection">
								清空选择
							</el-button>
						</div>
					</div>
				</el-col>
			</el-row>
		</div>

		<!-- 记录列表 -->
		<div class="records-list">
			<el-table
				v-loading="loading"
				:data="records"
				stripe
				style="width: 100%"
				@selection-change="handleSelectionChange"
			>
				<el-table-column type="selection" width="55" />
				<el-table-column label="工具名称" min-width="180">
					<template #default="{ row }">
						<div class="tool-info">
							<div class="tool-name">{{ getToolDisplayName(row.tool_name) }}</div>
							<el-tag size="small" type="info">{{ getCategoryDisplayName(row.tool_category) }}</el-tag>
						</div>
					</template>
				</el-table-column>
				<el-table-column label="输入参数" min-width="200" show-overflow-tooltip>
					<template #default="{ row }">
						<div class="input-preview">
							{{ getInputPreview(row.input_data) }}
						</div>
					</template>
				</el-table-column>
				<el-table-column label="执行结果" min-width="200" show-overflow-tooltip>
					<template #default="{ row }">
						<div class="result-preview">
							{{ getResultPreview(row.output_data) }}
						</div>
					</template>
				</el-table-column>
				<el-table-column label="标签" width="120">
					<template #default="{ row }">
						<div class="tags-container">
							<el-tag
								v-for="tag in (row.tags || []).slice(0, 2)"
								:key="tag"
								size="small"
								class="tag-item"
							>
								{{ tag }}
							</el-tag>
							<el-tag v-if="row.tags && row.tags.length > 2" size="small" type="info">
								+{{ row.tags.length - 2 }}
							</el-tag>
						</div>
					</template>
				</el-table-column>
				<el-table-column label="创建时间" width="160">
					<template #default="{ row }">
						<div class="time-info">
							{{ formatDateTime(row.creation_date) }}
						</div>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="200" fixed="right">
					<template #default="{ row }">
						<div class="action-buttons">
							<el-button size="small" type="primary" @click="executeAgain(row)">
								重新执行
							</el-button>
							<el-button size="small" @click="viewDetail(row)">
								详情
							</el-button>
							<el-button size="small" type="danger" @click="deleteRecord(row)">
								删除
							</el-button>
						</div>
					</template>
				</el-table-column>
			</el-table>
		</div>

		<!-- 分页 -->
		<div class="pagination-container">
			<el-pagination
				v-model:current-page="currentPage"
				v-model:page-size="pageSize"
				:total="total"
				:page-sizes="[10, 20, 50, 100]"
				layout="total, sizes, prev, pager, next, jumper"
				@size-change="handleSizeChange"
				@current-change="handleCurrentChange"
			/>
		</div>


		<!-- 详情对话框 -->
		<el-dialog
			v-model="detailDialogVisible"
			title="记录详情"
			width="900px"
			:close-on-click-modal="false"
		>
			<div v-if="selectedRecord" class="record-detail">
				<el-descriptions :column="2" border>
					<el-descriptions-item label="工具名称">
						{{ getToolDisplayName(selectedRecord.tool_name) }}
					</el-descriptions-item>
					<el-descriptions-item label="工具分类">
						{{ getCategoryDisplayName(selectedRecord.tool_category) }}
					</el-descriptions-item>
					<el-descriptions-item label="创建时间">
						{{ formatDateTime(selectedRecord.creation_date) }}
					</el-descriptions-item>
					<el-descriptions-item label="记录ID">
						{{ selectedRecord.id }}
					</el-descriptions-item>
				</el-descriptions>

				<div class="detail-section">
					<h4>输入参数</h4>
					<el-input
						:value="formatInputData(selectedRecord.input_data)"
						type="textarea"
						:autosize="{ minRows: 3, maxRows: 8 }"
						readonly
					/>
				</div>

				<div class="detail-section">
					<h4>执行结果</h4>
					<el-input
						:value="formatOutputData(selectedRecord.output_data)"
						type="textarea"
						:autosize="{ minRows: 3, maxRows: 8 }"
						readonly
					/>
				</div>

				<div v-if="selectedRecord.tags && selectedRecord.tags.length > 0" class="detail-section">
					<h4>标签</h4>
					<div class="tags-container">
						<el-tag
							v-for="tag in selectedRecord.tags"
							:key="tag"
							class="tag-item"
						>
							{{ tag }}
						</el-tag>
					</div>
				</div>
			</div>
			
			<template #footer>
				<div class="dialog-footer">
					<el-button @click="detailDialogVisible = false">关闭</el-button>
					<el-button type="primary" @click="executeAgain(selectedRecord!)">
						重新执行
					</el-button>
				</div>
			</template>
		</el-dialog>

		<!-- 工具执行弹窗 -->
		<el-dialog
			v-model="executeDialogVisible"
			:title="`重新执行 - ${executeTool?.display_name || ''}`"
			width="800px"
			:close-on-click-modal="false"
			@close="closeExecuteDialog"
		>
			<ToolExecutor
				v-if="executeTool && executeCategory"
				:tool="executeTool"
				:category="executeCategory"
				:initial-data="executeRecord?.input_data"
				@execute="handleToolExecute"
				@batch-generate="handleBatchGenerate"
				@close="closeExecuteDialog"
			/>
		</el-dialog>
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, defineEmits } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Delete } from '@element-plus/icons-vue';
import { getRecordList, deleteRecord as deleteRecordAPI, batchDeleteRecords, getTagList, getToolCategories, type ToolRecord, type Tool, type ToolCategory } from '/@/api/v1/data_factory';
import ToolExecutor from './ToolExecutor.vue';

// Emits
const emit = defineEmits<{
	executeAgain: [record: ToolRecord];
}>();

// 响应式数据
const loading = ref(false);
const records = ref<ToolRecord[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

// 筛选条件
const searchKeyword = ref('');
const filterCategory = ref('');
const selectedTags = ref<string[]>([]);
const availableTags = ref<string[]>([]);

// 选择的记录
const selectedRecords = ref<ToolRecord[]>([]);

// 详情对话框
const detailDialogVisible = ref(false);
const selectedRecord = ref<ToolRecord | null>(null);

// 执行弹窗
const executeDialogVisible = ref(false);
const executeRecord = ref<ToolRecord | null>(null);
const executeTool = ref<Tool | null>(null);
const executeCategory = ref<ToolCategory | null>(null);
const toolCategories = ref<ToolCategory[]>([]);

// 分类显示名称映射
const categoryDisplayMap: Record<string, string> = {
	test_data: '测试数据',
	json: 'JSON工具',
	string: '字符工具',
	encoding: '编码工具',
	random: '随机工具',
	encryption: '加密工具',
	crontab: 'Crontab工具'
};

// 工具显示名称映射（完整版）
const toolDisplayMap: Record<string, string> = {
	// 测试数据工具
	generate_chinese_name: '生成中文姓名',
	generate_chinese_phone: '生成手机号',
	generate_chinese_email: '生成邮箱',
	generate_chinese_address: '生成中文地址',
	generate_id_card: '生成身份证号',
	generate_company_name: '生成公司名称',
	generate_bank_card: '生成银行卡号',
	generate_hk_id_card: '生成香港身份证',
	generate_business_license: '生成营业执照号',
	generate_coordinates: '生成经纬度',
	generate_user_profile: '生成用户档案',
	
	// JSON工具
	format_json: 'JSON格式化',
	validate_json: 'JSON校验',
	json_diff_enhanced: 'JSON对比',
	jsonpath_query: 'JSONPath查询',
	json_flatten: 'JSON扁平化',
	json_path_list: 'JSON路径列表',
	json_to_xml: 'JSON转XML',
	xml_to_json: 'XML转JSON',
	json_to_yaml: 'JSON转YAML',
	yaml_to_json: 'YAML转JSON',
	
	// 字符工具
	text_diff: '文本对比',
	regex_test: '正则测试',
	remove_whitespace: '去除空格换行',
	replace_string: '字符串替换',
	escape_string: '字符串转义',
	unescape_string: '字符串反转义',
	word_count: '字数统计',
	case_convert: '大小写转换',
	string_format: '字符串格式化',
	
	// 编码工具
	generate_barcode: '生成条形码',
	generate_qrcode: '生成二维码',
	decode_qrcode: '二维码解析',
	timestamp_convert: '时间戳转换',
	base_convert: '进制转换',
	unicode_convert: 'Unicode转换',
	ascii_convert: 'ASCII转换',
	color_convert: '颜色值转换',
	url_encode: 'URL编码',
	url_decode: 'URL解码',
	jwt_decode: 'JWT解码',
	image_to_base64: '图片转Base64',
	base64_to_image: 'Base64转图片',
	base64_encode: 'Base64编码',
	base64_decode: 'Base64解码',
	
	// 随机工具
	random_int: '随机整数',
	random_float: '随机浮点数',
	random_string: '随机字符串',
	random_uuid: '随机UUID',
	random_boolean: '随机布尔值',
	random_mac_address: '随机MAC地址',
	random_ip_address: '随机IP地址',
	random_date: '随机日期',
	random_password: '随机密码',
	random_color: '随机颜色',
	random_sequence: '随机序列数据',
	
	// 加密工具
	md5_hash: 'MD5加密',
	sha1_hash: 'SHA1加密',
	sha256_hash: 'SHA256加密',
	sha512_hash: 'SHA512加密',
	hash_comparison: '哈希值比对',
	aes_encrypt: 'AES加密',
	aes_decrypt: 'AES解密',
	password_strength: '密码强度分析',
	generate_salt: '随机盐值',
	
	// Crontab工具
	generate_expression: '生成Crontab表达式',
	parse_expression: '解析Crontab表达式',
	get_next_runs: '获取下次执行时间',
	validate_expression: '验证Crontab表达式',
};

// 获取工具显示名称
const getToolDisplayName = (toolName: string): string => {
	return toolDisplayMap[toolName] || toolName;
};

// 获取分类显示名称
const getCategoryDisplayName = (category: string): string => {
	return categoryDisplayMap[category] || category;
};

// 获取输入参数预览
const getInputPreview = (inputData: any): string => {
	if (!inputData) return '无参数';
	
	const str = JSON.stringify(inputData);
	return str.length > 50 ? str.substring(0, 50) + '...' : str;
};

// 获取结果预览
const getResultPreview = (outputData: any): string => {
	if (!outputData) return '无结果';
	
	// 如果有result字段，优先显示
	if (outputData.result !== undefined) {
		const result = String(outputData.result);
		return result.length > 50 ? result.substring(0, 50) + '...' : result;
	}
	
	const str = JSON.stringify(outputData);
	return str.length > 50 ? str.substring(0, 50) + '...' : str;
};

// 格式化输入数据
const formatInputData = (inputData: any): string => {
	if (!inputData) return '无参数';
	return JSON.stringify(inputData, null, 2);
};

// 格式化输出数据
const formatOutputData = (outputData: any): string => {
	if (!outputData) return '无结果';
	return JSON.stringify(outputData, null, 2);
};

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
	if (!dateTime) return '';
	return new Date(dateTime).toLocaleString('zh-CN');
};

// 加载记录列表
const loadRecords = async () => {
	try {
		loading.value = true;
		const params = {
			page: currentPage.value,
			page_size: pageSize.value,
			tool_category: filterCategory.value || undefined,
			tool_name: searchKeyword.value || undefined,
			tags: selectedTags.value.length > 0 ? selectedTags.value.join(',') : undefined,
		};
		
		const response = await getRecordList(params);
		if (response.data) {
			records.value = response.data.items || [];
			total.value = response.data.total || 0;
		}
	} catch (error) {
		console.error('加载记录列表失败:', error);
		ElMessage.error('加载记录列表失败');
	} finally {
		loading.value = false;
	}
};

// 加载标签列表
const loadTags = async () => {
	try {
		const response = await getTagList();
		availableTags.value = response.data?.tags || [];
	} catch (error) {
		console.error('加载标签失败:', error);
	}
};

// 加载工具分类
const loadToolCategories = async () => {
	try {
		const response = await getToolCategories();
		if (response.data) {
			toolCategories.value = response.data.categories || [];
		}
	} catch (error) {
		console.error('加载工具分类失败:', error);
	}
};

// 搜索处理
const handleSearch = () => {
	currentPage.value = 1;
	loadRecords();
};

// 筛选处理
const handleFilter = () => {
	currentPage.value = 1;
	loadRecords();
};

// 清空筛选
const clearFilters = () => {
	searchKeyword.value = '';
	filterCategory.value = '';
	selectedTags.value = [];
	currentPage.value = 1;
	loadRecords();
};

// 分页处理
const handleSizeChange = (size: number) => {
	pageSize.value = size;
	currentPage.value = 1;
	loadRecords();
};

const handleCurrentChange = (page: number) => {
	currentPage.value = page;
	loadRecords();
};

// 选择变化处理
const handleSelectionChange = (selection: ToolRecord[]) => {
	selectedRecords.value = selection;
};

// 重新执行
const executeAgain = async (record: ToolRecord) => {
	try {
		// 查找对应的工具分类和工具信息
		const category = toolCategories.value.find(c => c.category === record.tool_category);
		if (!category) {
			ElMessage.error('找不到对应的工具分类');
			return;
		}

		const tool = category.tools.find(t => t.name === record.tool_name);
		if (!tool) {
			ElMessage.error('找不到对应的工具');
			return;
		}

		// 设置执行相关数据
		executeRecord.value = record;
		executeTool.value = tool;
		executeCategory.value = category;
		executeDialogVisible.value = true;
	} catch (error) {
		console.error('准备重新执行失败:', error);
		ElMessage.error('准备重新执行失败');
	}
};

// 查看详情
const viewDetail = (record: ToolRecord) => {
	selectedRecord.value = record;
	detailDialogVisible.value = true;
};

// 删除记录
const deleteRecord = async (record: ToolRecord) => {
	try {
		await ElMessageBox.confirm(
			'确定要删除这条记录吗？',
			'确认删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		
		await deleteRecordAPI(record.id);
		ElMessage.success('删除成功');
		loadRecords();
	} catch (error: any) {
		if (error !== 'cancel') {
			console.error('删除记录失败:', error);
			ElMessage.error('删除记录失败');
		}
	}
};

// 清空选择
const clearSelection = () => {
	selectedRecords.value = [];
};

// 批量删除
const batchDelete = async () => {
	try {
		await ElMessageBox.confirm(
			`确定要删除选中的 ${selectedRecords.value.length} 条记录吗？`,
			'确认批量删除',
			{
				confirmButtonText: '确定',
				cancelButtonText: '取消',
				type: 'warning',
			}
		);
		
		const ids = selectedRecords.value.map(record => record.id);
		await batchDeleteRecords(ids);
		ElMessage.success('批量删除成功');
		selectedRecords.value = [];
		loadRecords();
	} catch (error: any) {
		if (error !== 'cancel') {
			console.error('批量删除失败:', error);
			ElMessage.error('批量删除失败');
		}
	}
};

// 处理工具执行
const handleToolExecute = (result: any) => {
	console.log('工具执行结果:', result);
	if (result && result.error) {
		ElMessage.error(`执行失败: ${result.error}`);
	} else {
		ElMessage.success(`${result.tool_name || '工具'}执行成功`);
		// 刷新记录列表
		loadRecords();
	}
};

// 处理批量生成
const handleBatchGenerate = (result: any) => {
	console.log('批量生成结果:', result);
	if (result && result.error) {
		ElMessage.error(`批量生成失败: ${result.error}`);
	} else {
		let count = 0;
		if (result?.results?.length) {
			count = result.results.length;
		} else if (result?.count) {
			count = result.count;
		} else if (result?.success_count !== undefined) {
			count = result.success_count;
		} else if (Array.isArray(result)) {
			count = result.length;
		} else {
			count = 1;
		}
		
		ElMessage.success(`${result.tool_name || '工具'}批量生成成功，共生成 ${count} 条数据`);
		// 刷新记录列表
		loadRecords();
	}
};

// 关闭执行弹窗
const closeExecuteDialog = () => {
	executeDialogVisible.value = false;
	executeRecord.value = null;
	executeTool.value = null;
	executeCategory.value = null;
};

// 组件挂载时加载数据
onMounted(() => {
	loadRecords();
	loadTags();
	loadToolCategories();
});
</script>

<style scoped lang="scss">
.history-list-container {
	.filter-bar {
		margin-bottom: 20px;
		padding: 16px;
		background: var(--el-fill-color-lighter);
		border-radius: var(--el-border-radius-base);
		border: 1px solid var(--el-border-color-light);

		.batch-actions-inline {
			display: flex;
			align-items: center;
			justify-content: space-between;
			height: 32px;
			padding: 0 8px;
			border-radius: var(--el-border-radius-small);
			transition: all var(--el-transition-duration);

			&.has-selection {
				background: var(--el-color-primary-light-9);
				border: 1px solid var(--el-color-primary-light-7);
			}

			.selection-info {
				.selection-text {
					font-size: 13px;
					color: var(--el-text-color-regular);

					&.has-selection {
						color: var(--el-color-primary);
						font-weight: 600;
					}
				}
			}

			.batch-buttons {
				display: flex;
				gap: 8px;
			}
		}
	}

	.records-list {
		// 添加左右间距，避免表格铺满
		padding: 0 16px;
		margin-bottom: 20px;

		:deep(.el-table) {
			.el-table__row {
				height: 60px;
			}

			.el-table__cell {
				padding: 8px 0;
				vertical-align: middle;
			}

			.el-table__header {
				.el-table__cell {
					background-color: var(--el-fill-color-light);
					font-weight: 600;
					color: var(--el-text-color-primary);
				}
			}
		}

		.tool-info {
			.tool-name {
				font-weight: 600;
				margin-bottom: 4px;
				font-size: 14px;
			}
		}

		.input-preview,
		.result-preview {
			font-family: 'Courier New', monospace;
			font-size: 12px;
			color: var(--el-text-color-regular);
			line-height: 1.4;
			word-break: break-all;
		}

		.tags-container {
			display: flex;
			flex-wrap: wrap;
			gap: 4px;

			.tag-item {
				margin: 0;
			}
		}

		.time-info {
			font-size: 12px;
			color: var(--el-text-color-regular);
			line-height: 1.4;
		}

		.action-buttons {
			display: flex;
			gap: 4px;
			flex-wrap: wrap;

			.el-button {
				padding: 4px 8px;
				font-size: 12px;
			}
		}
	}

	.pagination-container {
		padding: 20px 16px;
		display: flex;
		justify-content: center;
		background: var(--el-bg-color);
		border-top: 1px solid var(--el-border-color-light);
	}

	.record-detail {
		.detail-section {
			margin-top: 20px;

			h4 {
				margin: 0 0 12px 0;
				font-size: 14px;
				color: var(--el-text-color-primary);
			}
		}

		.tags-container {
			display: flex;
			flex-wrap: wrap;
			gap: 8px;

			.tag-item {
				margin: 0;
			}
		}
	}
}

// 响应式设计
@media (max-width: 768px) {
	.history-list-container {
		.filter-bar {
			padding: 12px;

			.el-row {
				flex-direction: column;
				gap: 12px;
			}

			.batch-actions-inline {
				flex-direction: column;
				align-items: flex-start;
				height: auto;
				gap: 8px;

				.batch-buttons {
					width: 100%;
					justify-content: flex-start;

					.el-button {
						flex: 1;
					}
				}
			}
		}

		.records-list {
			padding: 0 8px;
			
			:deep(.el-table) {
				.el-table__row {
					height: 50px;
				}
			}

			.action-buttons {
				flex-direction: column;

				.el-button {
					width: 100%;
					font-size: 11px;
				}
			}
		}

		.pagination-container {
			padding: 16px 8px;
		}
	}
}
</style>