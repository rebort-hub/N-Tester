<template>
  <div class="project-container">
    <el-card shadow="hover" :body-style="{ paddingBottom: '0' }">
      <!-- 搜索栏 -->
      <el-form :model="queryForm" :inline="true">
        <el-form-item label="项目名称">
          <el-input
            v-model="queryForm.name"
            placeholder="请输入项目名称"
            clearable
            @keyup.enter="handleQuery"
          />
        </el-form-item>
        <el-form-item label="项目状态">
          <el-select v-model="queryForm.status" placeholder="请选择状态" clearable style="width: 150px">
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="paused" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuery" v-auth="'projects:list:query'">
            <el-icon><ele-Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><ele-Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover" style="margin-top: 8px">
      <!-- 工具栏 -->
      <el-row :gutter="10" style="margin-bottom: 8px">
        <el-col :span="1.5">
          <el-button
            type="primary"
            plain
            @click="handleAdd"
            v-auth="'projects:list:add'"
          >
            <el-icon><ele-Plus /></el-icon>
            新增
          </el-button>
        </el-col>
      </el-row>

      <!-- 表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="name" label="项目名称" min-width="150" show-overflow-tooltip />
        <el-table-column prop="description" label="项目描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="member_count" label="成员数" width="100" align="center" />
        <el-table-column prop="environment_count" label="环境数" width="100" align="center" />
        <el-table-column prop="creation_date" label="创建时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.creation_date) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="380" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click="handleEdit(row)"
              v-auth="'projects:list:edit'"
            >
              <el-icon><ele-Edit /></el-icon>
              编辑
            </el-button>
            <el-button
              size="small"
              type="success"
              @click="handleMembers(row)"
              v-auth="'projects:member:manage'"
            >
              <el-icon><ele-User /></el-icon>
              成员
            </el-button>
            <el-button
              size="small"
              type="warning"
              @click="handleEnvironments(row)"
              v-auth="'projects:environment:manage'"
            >
              <el-icon><ele-Setting /></el-icon>
              环境
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              v-auth="'projects:list:delete'"
            >
              <el-icon><ele-Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryForm.page"
        v-model:page-size="queryForm.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleQuery"
        @current-change="handleQuery"
        style="margin-top: 16px"
      />
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="项目状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态">
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="paused" />
            <el-option label="已完成" value="completed" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 成员管理对话框 -->
    <MemberManage
      v-model="memberDialogVisible"
      :project-id="currentProjectId"
      :project-name="currentProjectName"
    />

    <!-- 环境管理对话框 -->
    <EnvironmentManage
      v-model="envDialogVisible"
      :project-id="currentProjectId"
      :project-name="currentProjectName"
    />
  </div>
</template>

<script setup lang="ts" name="projectsList">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { useProjectApi } from '/@/api/v1/projects/project';
import MemberManage from '../components/MemberManage.vue';
import EnvironmentManage from '../components/EnvironmentManage.vue';

const router = useRouter();
const projectApi = useProjectApi();

// 查询表单
const queryForm = reactive({
  page: 1,
  page_size: 20,
  name: '',
  status: '',
});

// 表格数据
const loading = ref(false);
const tableData = ref([]);
const total = ref(0);

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref('');
const formRef = ref<FormInstance>();
const formData = reactive({
  id: undefined,
  name: '',
  description: '',
  status: 'active',
});
const submitLoading = ref(false);

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 1, max: 200, message: '长度在 1 到 200 个字符', trigger: 'blur' },
  ],
};

// 获取状态类型
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    active: 'success',
    paused: 'warning',
    completed: 'info',
    archived: 'info',
  };
  return typeMap[status] || '';
};

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    active: '活跃',
    paused: '暂停',
    completed: '已完成',
    archived: '已归档',
  };
  return textMap[status] || status;
};

// 查询列表
const handleQuery = async () => {
  loading.value = true;
  try {
    const res = await projectApi.getList(queryForm);
    if (res.code === 200) {
      tableData.value = res.data.items;
      total.value = res.data.total;
    }
  } catch (error) {
    console.error('查询失败:', error);
  } finally {
    loading.value = false;
  }
};

// 重置查询
const handleReset = () => {
  queryForm.page = 1;
  queryForm.name = '';
  queryForm.status = '';
  handleQuery();
};

// 新增
const handleAdd = () => {
  dialogTitle.value = '新增项目';
  formData.id = undefined;
  formData.name = '';
  formData.description = '';
  formData.status = 'active';
  dialogVisible.value = true;
};

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑项目';
  formData.id = row.id;
  formData.name = row.name;
  formData.description = row.description;
  formData.status = row.status;
  dialogVisible.value = true;
};

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    submitLoading.value = true;
    try {
      const data = {
        name: formData.name,
        description: formData.description,
        status: formData.status,
      };
      
      if (formData.id) {
        await projectApi.update(formData.id, data);
        ElMessage.success('更新成功');
      } else {
        await projectApi.create(data);
        ElMessage.success('创建成功');
      }
      
      dialogVisible.value = false;
      handleQuery();
    } catch (error: any) {
      console.error('提交失败:', error);
      // 显示后端返回的错误信息
      const errorMsg = error?.response?.data?.message || error?.message || '操作失败';
      ElMessage.error(errorMsg);
    } finally {
      submitLoading.value = false;
    }
  });
};

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm(`确定要删除项目"${row.name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await projectApi.delete(row.id);
      ElMessage.success('删除成功');
      handleQuery();
    } catch (error) {
      console.error('删除失败:', error);
    }
  });
};

// 成员管理对话框
const memberDialogVisible = ref(false);
const currentProjectId = ref<number>();
const currentProjectName = ref('');

// 环境管理对话框
const envDialogVisible = ref(false);

// 管理成员
const handleMembers = (row: any) => {
  currentProjectId.value = row.id;
  currentProjectName.value = row.name;
  memberDialogVisible.value = true;
};

// 管理环境
const handleEnvironments = (row: any) => {
  currentProjectId.value = row.id;
  currentProjectName.value = row.name;
  envDialogVisible.value = true;
};

// 初始化
onMounted(() => {
  handleQuery();
});
</script>

<style scoped lang="scss">
.project-container {
  padding: 15px;
}
</style>
