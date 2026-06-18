<template>
	<div class="system-dict-data-dialog-container">
		<el-dialog 
			:title="`字典数据管理 - ${state.dictType.dict_name}`" 
			v-model="state.isShowDialog" 
			width="1000px"
			:close-on-click-modal="false"
		>
			<div class="mb15">
				<el-button 
					v-auth="'system:dict:data:add'"
					type="primary" 
					@click="onOpenAddData"
				>
					<el-icon><ele-Plus /></el-icon>
					新增数据
				</el-button>
			</div>
			
			<el-table :data="state.tableData" v-loading="state.loading" style="width: 100%">
				<el-table-column type="index" label="序号" width="60" />
				<el-table-column prop="dict_label" label="字典标签" show-overflow-tooltip width="150" />
				<el-table-column prop="dict_value" label="字典键值" show-overflow-tooltip width="150" />
				<el-table-column prop="dict_sort" label="排序" width="80" align="center" />
				<el-table-column prop="status" label="状态" width="80" align="center">
					<template #default="scope">
						<el-tag type="success" v-if="scope.row.status === 1">启用</el-tag>
						<el-tag type="info" v-else>禁用</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="remark" label="备注" show-overflow-tooltip />
				<el-table-column prop="created_at" label="创建时间" show-overflow-tooltip width="160" align="center">
					<template #default="scope">
						{{ formatDateTime(scope.row.created_at) }}
					</template>
				</el-table-column>
				<el-table-column label="操作" width="150" fixed="right" align="center">
					<template #default="scope">
						<el-button 
							v-auth="'system:dict:data:edit'"
							size="small" 
							type="primary"
							@click="onOpenEditData(scope.row)"
						>
							修改
						</el-button>
						<el-button 
							v-auth="'system:dict:data:delete'"
							size="small" 
							type="danger"
							@click="onDeleteData(scope.row)"
						>
							删除
						</el-button>
					</template>
				</el-table-column>
			</el-table>
			
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="closeDialog">关 闭</el-button>
				</span>
			</template>
		</el-dialog>
		
		<!-- 字典数据编辑对话框 -->
		<el-dialog 
			:title="state.dataDialog.title" 
			v-model="state.dataDialog.isShow" 
			width="600px"
			:close-on-click-modal="false"
		>
			<el-form 
				ref="dataFormRef" 
				:model="state.dataForm" 
				:rules="state.dataRules" 
				size="default" 
				label-width="90px"
			>
				<el-row :gutter="35">
					<el-col :xs="24" :sm="12" :md="12" :lg="12" :xl="12" class="mb20">
						<el-form-item label="字典标签" prop="dict_label">
							<el-input v-model="state.dataForm.dict_label" placeholder="请输入字典标签" clearable />
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="12" :md="12" :lg="12" :xl="12" class="mb20">
						<el-form-item label="字典键值" prop="dict_value">
							<el-input v-model="state.dataForm.dict_value" placeholder="请输入字典键值" clearable />
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="12" :md="12" :lg="12" :xl="12" class="mb20">
						<el-form-item label="排序">
							<el-input-number v-model="state.dataForm.dict_sort" :min="0" :max="9999" class="w100" />
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="12" :md="12" :lg="12" :xl="12" class="mb20">
						<el-form-item label="状态">
							<el-switch 
								v-model="state.dataForm.status" 
								:active-value="1"
								:inactive-value="0"
								inline-prompt 
								active-text="启" 
								inactive-text="禁"
							/>
						</el-form-item>
					</el-col>
					<el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24" class="mb20">
						<el-form-item label="备注">
							<el-input 
								v-model="state.dataForm.remark" 
								type="textarea" 
								placeholder="请输入备注" 
								maxlength="500"
								:rows="3"
							/>
						</el-form-item>
					</el-col>
				</el-row>
			</el-form>
			<template #footer>
				<span class="dialog-footer">
					<el-button @click="state.dataDialog.isShow = false">取 消</el-button>
					<el-button type="primary" @click="onSubmitData">确 定</el-button>
				</span>
			</template>
		</el-dialog>
	</div>
</template>

<script setup lang="ts" name="systemDictDataDialog">
import { reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useDictDataApi } from '/@/api/v1/system/dict';
import { formatDateTime } from '/@/utils/formatTime';

// 定义变量内容
const dataFormRef = ref();
const state = reactive({
	isShowDialog: false,
	loading: false,
	dictType: {
		id: null as number | null,
		dict_name: '',
		dict_type: '',
	},
	tableData: [] as any[],
	dataDialog: {
		isShow: false,
		title: '',
		type: '',
	},
	dataForm: {
		id: null as number | null,
		dict_label: '',
		dict_value: '',
		dict_type: '',
		dict_sort: 0,
		status: 1,
		remark: '',
	},
	dataRules: {
		dict_label: [
			{ required: true, message: '请输入字典标签', trigger: 'blur' }
		],
		dict_value: [
			{ required: true, message: '请输入字典键值', trigger: 'blur' }
		],
	},
});

// 打开对话框
const openDialog = (dictType: any) => {
	state.dictType = {
		id: dictType.id,
		dict_name: dictType.dict_name,
		dict_type: dictType.dict_type,
	};
	state.isShowDialog = true;
	getDataList();
};

// 获取字典数据列表（含禁用数据，管理页面需看到全部）
const getDataList = () => {
	state.loading = true;
	useDictDataApi().getList({ dict_type: state.dictType.dict_type, page_size: 1000 })
		.then(res => {
			state.tableData = res.data?.items || [];
		})
		.catch(error => {
			ElMessage.error(error.message || '获取字典数据失败');
		})
		.finally(() => {
			state.loading = false;
		});
};

// 打开新增数据对话框
const onOpenAddData = () => {
	state.dataDialog.type = 'add';
	state.dataDialog.title = '新增字典数据';
	state.dataForm = {
		id: null,
		dict_label: '',
		dict_value: '',
		dict_type: state.dictType.dict_type,
		dict_sort: 0,
		status: 1,
		remark: '',
	};
	state.dataDialog.isShow = true;
};

// 打开编辑数据对话框
const onOpenEditData = (row: any) => {
	state.dataDialog.type = 'edit';
	state.dataDialog.title = '修改字典数据';
	state.dataForm = {
		id: row.id,
		dict_label: row.dict_label,
		dict_value: row.dict_value,
		dict_type: row.dict_type,
		dict_sort: row.dict_sort,
		status: row.status,
		remark: row.remark || '',
	};
	state.dataDialog.isShow = true;
};

// 提交数据
const onSubmitData = () => {
	dataFormRef.value.validate((valid: boolean) => {
		if (!valid) return;
		
		const formData = { ...state.dataForm };
		
		useDictDataApi().saveOrUpdate(formData)
			.then(() => {
				ElMessage.success('操作成功');
				state.dataDialog.isShow = false;
				getDataList();
			})
			.catch(error => {
				ElMessage.error(error.message || '操作失败');
			});
	});
};

// 删除数据
const onDeleteData = (row: any) => {
	ElMessageBox.confirm(`确定要删除字典数据"${row.dict_label}"吗？`, '提示', {
		confirmButtonText: '确认',
		cancelButtonText: '取消',
		type: 'warning',
	})
		.then(() => {
			useDictDataApi().delete(row.id)
				.then(() => {
					ElMessage.success('删除成功');
					getDataList();
				})
				.catch(error => {
					ElMessage.error(error.message || '删除失败');
				});
		})
		.catch(() => {});
};

// 关闭对话框
const closeDialog = () => {
	state.isShowDialog = false;
};

// 暴露方法
defineExpose({
	openDialog,
});
</script>

<style scoped>
.w100 {
	width: 100%;
}
</style>
