<template>
  <div class="images-page">
    <!-- 顶部标题栏 -->
    <el-card class="box-card">
      <div class="images-topbar">
        <div class="images-topbar-left">
          <span class="images-title">图像库管理</span>
        </div>
        <div class="images-actions">
          <el-button type="primary" class="action-button primary-button" @click="Add()">
            <el-icon><Plus /></el-icon>
            新增图像
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 搜索区域 -->
    <el-card class="search-card">
      <el-form :inline="true" class="search-form">
        <el-form-item label="项目">
          <el-select
            v-model="searchParams.search.menu_id"
            placeholder="请选择项目"
            class="search-select"
            @change="onMenuChange"
          >
            <el-option v-for="item in app_menu_list" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="图像名称">
          <el-input 
            v-model="searchParams.search.file_name__icontains" 
            placeholder="请输入图像名称" 
            clearable
            class="search-input"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" class="action-button primary-button" @click="get_img_list">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button class="action-button" @click="resetsearch">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table 
        v-loading="loading" 
        :data="tableList" 
        stripe
        empty-text="暂无图像数据"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="序号" type="index" width="80" align="center" />
        <el-table-column label="图像名称" prop="file_name" min-width="200" :show-overflow-tooltip="true" />
        <el-table-column label="预览" width="120" align="center">
          <template #default="{ row }">
            <div class="image-preview">
              <el-image
                class="preview-image"
                fit="cover"
                :preview-teleported="true"
                :preview-src-list="[row.file_path]"
                :src="row.file_path || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"
              >
                <template #error>
                  <div class="image-error">
                    <el-icon><CircleCloseFilled /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="create_time" width="180" align="center">
          <template #default="{ row }">
            <span class="time-text">{{ formatDateTime(row.create_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button type="primary" size="small" @click="Edit(row)">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button type="danger" size="small" @click="Delete(row)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="searchParams.currentPage"
          v-model:page-size="searchParams.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="get_img_list"
          @current-change="get_img_list"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <KoiDialog
      ref="koiDialogRef"
      title="图像库上传"
      :destroy-on-close="true"
      :before-close-check="false"
      :loading="confirmLoading"
      :visible="dialogVisible"
      @koi-confirm="add_Confirm"
      @koi-cancel="add_Cancel"
    >
      <template #content>
        <el-form ref="formRef" :model="add_form" label-width="100px" status-icon>
          <el-form-item label="归属项目">
            <el-alert
              title="已固定为打开窗口时的项目，与列表「项目」筛选一致"
              type="info"
              :closable="false"
              show-icon
            />
          </el-form-item>
          <el-form-item label="图像文件" prop="avatar">
            <KoiUploadImages
              :key="drawerUploadKey"
              v-model:file-list="add_form.file_list"
              :app_menu_id="drawerMenuId"
              :defer-commit="true"
            >
              <template #content>
                <el-icon><Avatar /></el-icon>
                <span>选择图片</span>
              </template>
              <template #tip>选择后仅预览，点下方「确定」后统一上传并写入当前项目；单张不超过 30M，最多 9 张。</template>
            </KoiUploadImages>
          </el-form-item>
        </el-form>
      </template>
    </KoiDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MsgBox, MsgSuccess, NoticeError } from "@/utils/koi.ts";
import { formatDateTime } from "@/utils/formatTime";
import { Edit, Delete, CircleCloseFilled, Avatar, Search, Refresh, Plus } from "@element-plus/icons-vue";
import request from "/@/utils/request";
import { useAppManagementApi } from "/@/api/v1/app_management";

const { app_menu_select } = useAppManagementApi();

// 图像相关 API（直接用 request，与新版保持一致）
const img_list_api = (data: any) => request({ url: '/v1/app_management/img_list', method: 'post', data });
const delete_img_api = (data: any) => request({ url: '/v1/app_management/delete_img', method: 'post', data });

// 搜索区域展示
const showSearch = ref<boolean>(true);

//总数
const total = ref<number>(0);

// 查询参数
const searchParams = ref({
  currentPage: 1, // 第几页
  pageSize: 10, // 每页显示多少条
  search: {
    file_name__icontains: "",
    menu_id: ""
  }
});
// 添加 / 编辑表单（file_list 与 el-upload 同步）
const add_form = ref<{ file_list: any[]; type: string; id?: number; file_name?: string; file_path?: string; menu_id?: number; create_time?: string }>({
  file_list: [],
  type: ""
});

/** 添加 / 编辑弹窗 */
const koiDialogRef = ref();
/** 弹窗显隐状态，由代码显式控制，防止组件挂载时自动打开 */
const dialogVisible = ref(false);

/** 上传归属的项目 ID：打开抽屉时从当前筛选快照，避免与列表「项目」下拉联动导致重复/错项目写入 */
const drawerMenuId = ref<number | string | "">("");
/** 每次打开抽屉换新 key，重置 el-upload 内部状态，防止切项目后残留文件链路上传 */
const drawerUploadKey = ref(0);

// 数据表格加载页面动画
const loading = ref(false);
// 防止 get_img_list 被重复触发造成“持续请求/循环刷新”
const imgListInFlight = ref(false);
// 表数据
const tableList = ref<any>([]);

const app_menu_list = ref<any>([]);
const get_app_select = async () => {
  const res: any = await app_menu_select({});
  app_menu_list.value = res.data;
  // 检查数组是否为空，避免访问undefined
  if (app_menu_list.value && app_menu_list.value.length > 0) {
    searchParams.value.search.menu_id = app_menu_list.value[0].id;
    await get_img_list();
  } else {
    console.warn('APP菜单列表为空');
  }
};


const get_img_list = async () => {
  if (imgListInFlight.value) return;
  imgListInFlight.value = true;
  try {
    loading.value = true;
    tableList.value = []; // 重置表格数据
    const res: any = await img_list_api(searchParams.value);
    tableList.value = res.data.content;
    total.value = res.data.total;
  } catch {
    NoticeError("数据查询失败，请刷新重试");
  } finally {
    loading.value = false;
    imgListInFlight.value = false;
  }
};
const resetsearch = async () => {
  const firstId = app_menu_list.value[0]?.id ?? "";
  searchParams.value = {
    currentPage: 1, // 第几页
    pageSize: 10, // 每页显示多少条
    search: {
      file_name__icontains: "",
     
      menu_id: firstId
    }
  };
  await get_img_list();
};

const onMenuChange = async () => {
  // 切项目时强制回到第一页，避免分页组件内部回填触发多次 current-change
  searchParams.value.currentPage = 1;
  await get_img_list();
};

/** 释放延迟上传产生的 blob 预览地址 */
const revokeBlobUrls = (list: any[]) => {
  (list || []).forEach((f: any) => {
    const u = f?.url;
    if (typeof u === "string" && u.startsWith("blob:")) {
      try {
        URL.revokeObjectURL(u);
      } catch {
        /* ignore */
      }
    }
  });
};

/** 添加 */
const Add = () => {
  drawerMenuId.value = searchParams.value.search.menu_id ?? "";
  drawerUploadKey.value += 1;
  resetForm();
  add_form.value.type = "add";
  dialogVisible.value = true;
  koiDialogRef.value?.koiOpen();
};

/** 清空表单数据 */
const resetForm = () => {
  add_form.value = {
    file_list: [],
    type: ""
  };
};

// 确定按钮是否显示loading
const confirmLoading = ref(false);

const add_Confirm = async () => {
  const mid = drawerMenuId.value;
  let committed = false;
  // 不依赖列表刷新结果：任何异常都要保证抽屉能关、上传实例能重置
  try {
    if (mid === "" || mid == null) {
      NoticeError("未选择所属项目，无法上传");
      return;
    }

    const list = add_form.value.file_list || [];
    const pending = list.filter((f: any) => f.raw);

    if (add_form.value.type === "add" && pending.length === 0) {
      NoticeError("请先选择要上传的图片，再点确定");
      return;
    }

    // 防止确认后仍保留文件导致后续列表操作触发重复上传
    const pendingToCommit = pending.map((f: any) => f.raw as File);
    add_form.value.file_list = [];

    confirmLoading.value = true;
    for (const raw of pendingToCommit) {
      const form = new FormData();
      form.append("file", raw);
      form.append("menu_id", String(mid));
      await request({
        url: "/v1/app_management/add_img",
        method: "POST",
        data: form,
        headers: { "Content-Type": "multipart/form-data" }
      });
    }

    revokeBlobUrls(list);
    committed = true;
    await get_img_list();
  } catch {
    NoticeError("上传失败，请重试");
  } finally {
    confirmLoading.value = false;
    resetForm();
    drawerUploadKey.value += 1;
    koiDialogRef.value?.koiQuickClose(committed ? "上传成功" : undefined);
    dialogVisible.value = false;
  }
};

/** 取消 */
const add_Cancel = () => {
  revokeBlobUrls(add_form.value.file_list || []);
  resetForm();
  drawerUploadKey.value += 1;
  dialogVisible.value = false;
  koiDialogRef.value?.koiQuickClose(undefined);
};

// 编辑用户（仅展示当前图，新增替换走 defer 提交）
const Edit = async (row: any) => {
  drawerMenuId.value = row.menu_id ?? searchParams.value.search.menu_id ?? "";
  drawerUploadKey.value += 1;
  add_form.value = {
    type: "edit",
    id: row.id,
    file_name: row.file_name,
    file_path: row.file_path,
    menu_id: row.menu_id,
    create_time: row.create_time,
    file_list: row.file_path
      ? [{ name: row.file_name, url: row.file_path, status: "success" as const }]
      : []
  };
  dialogVisible.value = true;
  koiDialogRef.value?.koiOpen();
};

const handleSelectionChange = (selection: any) => {
  console.log(selection);
};

const Delete = async (row: any) => {
  MsgBox("您确认需要删除用户名称[" + row.file_name + "]么？").then(async () => {
    const res: any = await delete_img_api({ id: row.id });
    MsgSuccess(res.message);
    await get_img_list();
  });
};

onMounted(() => {
  get_app_select();
});
</script>


<style scoped lang="scss">
/* 通用样式 */
.images-page {
  padding: 10px;
  min-height: 100vh;
}

.box-card {
  margin-bottom: 10px;
  border-radius: 8px;
}

/* 顶部标题栏样式 */
.images-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.images-topbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.images-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.images-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 搜索区域样式 */
.search-card {
  margin-bottom: 10px;
  border-radius: 8px;
}

.search-form {
  margin: 0;
}

.search-select {
  width: 200px;
}

.search-input {
  width: 200px;
}

/* 表格样式 */
.table-card {
  border-radius: 8px;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

/* 图像预览样式 */
.image-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 0;
}

.preview-image {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid var(--el-border-color-lighter);
  transition: all 0.3s ease;
}

.preview-image:hover {
  border-color: var(--el-color-primary);
  transform: scale(1.05);
}

.preview-image :deep(.el-image__inner),
.preview-image :deep(.el-image__wrapper) {
  width: 60px !important;
  height: 60px !important;
}

.image-error {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  color: var(--el-color-primary);
  background: var(--el-fill-color-light);
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 6px;
  justify-content: center;
  flex-wrap: wrap;
}

.action-button {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.primary-button {
  background: linear-gradient(135deg, #409eff, #1890ff);
  border: none;
  color: white;
}

.primary-button:hover {
  background: linear-gradient(135deg, #66b1ff, #40a9ff);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

/* 时间文本样式 */
.time-text {
  color: var(--el-text-color-regular);
  font-size: 13px;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  border-top: 1px solid var(--el-border-color-lighter);
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .images-topbar {
    flex-direction: column;
    gap: 10px;
    align-items: stretch;
  }
  
  .search-form {
    flex-direction: column;
  }
  
  .search-select,
  .search-input {
    width: 100%;
  }
}
</style>

