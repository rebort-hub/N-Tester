<script setup lang="ts">
import { ref, onMounted } from "vue";
import { MsgBox, MsgSuccess, NoticeError } from "@/utils/koi.ts";
import { delete_img, img_list } from "@/api/api_app/img.ts";
import { app_menu_select } from "@/api/api_app/app";
import { formatDateTime } from "@/utils/formatTime";
import { Edit, Delete, CircleCloseFilled, Avatar } from "@element-plus/icons-vue";
import request from "@/utils/request";

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
  searchParams.value.search.menu_id = app_menu_list.value[0].id;
  await get_img_list();
};


const get_img_list = async () => {
  if (imgListInFlight.value) return;
  imgListInFlight.value = true;
  try {
    loading.value = true;
    tableList.value = []; // 重置表格数据
    const res: any = await img_list(searchParams.value);
    tableList.value = res.data.content;
    total.value = res.data.total;
  } catch {
    NoticeError("数据查询失败，请刷新重试🌻");
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
      // 与旧架构一致：图像库按「脚本/项目菜单」隔离，重置回到第一个项目，避免 menu_id 为空时混入全部项目
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
  koiDialogRef.value.koiOpen();
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
    koiDialogRef.value.koiQuickClose(committed ? "上传成功" : undefined);
  }
};

/** 取消 */
const add_Cancel = () => {
  revokeBlobUrls(add_form.value.file_list || []);
  resetForm();
  drawerUploadKey.value += 1;
  koiDialogRef.value.koiQuickClose(undefined);
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
  koiDialogRef.value.koiOpen();
};

const handleSelectionChange = (selection: any) => {
  console.log(selection);
};

const Delete = async (row: any) => {
  MsgBox("您确认需要删除用户名称[" + row.file_name + "]么？").then(async () => {
    const res: any = await delete_img({ id: row.id });
    MsgSuccess(res.message);
    await get_img_list();
  });
};

onMounted(() => {
  get_app_select();
});
</script>

<template>
  <div>
    <KoiCard>
      <!-- 搜索条件 -->
      <el-form v-show="showSearch" :inline="true">
        <el-form-item label="项目：">
          <el-select
            v-model="searchParams.search.menu_id"
            placeholder="请选择项目（按项目隔离）"
            style="width: 200px"
            @change="onMenuChange"
          >
            <el-option v-for="item in app_menu_list" :key="item.id" :label="item.name" :value="item.id">
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="图像名称" prop="userName">
          <el-input placeholder="请输入图像名称" v-model="searchParams.search.file_name__icontains" clearable
            style="width: 200px"></el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="search" plain v-debounce="get_img_list">搜索</el-button>
          <el-button type="danger" icon="refresh" plain v-throttle="resetsearch">重置</el-button>
          <el-button type="primary" icon="plus" plain @click="Add()">新增</el-button>
        </el-form-item>
      </el-form>
      <div class="h-10px"></div>
      <!-- 数据表格 -->
      <el-table v-loading="loading" border :data="tableList" empty-text="暂时没有数据哟🌻"
        @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" align="center" />
        <el-table-column label="序号" prop="id" width="80px" align="center" type="index"></el-table-column>
        <el-table-column label="名称" prop="file_name" width="300px" align="center"
          :show-overflow-tooltip="true"></el-table-column>
        <el-table-column label="预览" prop="avatar" width="100" align="center">
          <template #default="scope">
            <div class="preview-cell">
              <el-image
                class="list-thumb-image"
                fit="cover"
                :preview-teleported="true"
                :preview-src-list="[scope.row.file_path]"
                :src="
                  scope.row.file_path != null && scope.row.file_path !== ''
                    ? scope.row.file_path
                    : 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
                "
              >
                <template #error>
                  <el-icon class="thumb-error-icon" :size="22">
                    <CircleCloseFilled />
                  </el-icon>
                </template>
              </el-image>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" prop="create_time" width="180px" align="center">
          <template #default="scope">
            {{ formatDateTime(scope.row.create_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" align="center" width="160" fixed="right">
          <template #default="{ row }">
            <el-tooltip content="修改" placement="top">
              <el-button type="primary" :icon="Edit" circle size="small" @click="Edit(row)" />
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-button type="danger" :icon="Delete" circle size="small" class="ml-6px" @click="Delete(row)" />
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>
      <div class="h-10px"></div>
      <el-pagination background v-model:current-page="searchParams.currentPage"
        v-model:page-size="searchParams.pageSize" v-show="total > 0" :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper" :total="total" @size-change="get_img_list"
        @current-change="get_img_list" />

      <KoiDialog
        ref="koiDialogRef"
        title="图像库上传"
        :destroy-on-close="true"
        :before-close-check="false"
        :loading="confirmLoading"
        @koi-confirm="add_Confirm"
        @koi-cancel="add_Cancel"
      >
        <template #content>
          <el-form ref="formRef" :model="add_form" label-width="100px" status-icon>
            <el-form-item label="归属项目">
              <span class="text-14px c-[var(--el-text-color-secondary)]">
                已固定为打开窗口时的项目，与列表「项目」筛选一致；切换列表项目不会改动此处。
              </span>
            </el-form-item>
            <el-row>
              <el-col :xs="{ span: 24 }" :sm="{ span: 24 }">
                <el-form-item label="图像文件" prop="avatar">
                  <KoiUploadImages
                    :key="drawerUploadKey"
                    v-model:file-list="add_form.file_list"
                    :app_menu_id="drawerMenuId"
                    :defer-commit="true"
                  >
                    <template #content>
                      <el-icon>
                        <Avatar />
                      </el-icon>
                      <span>选择图片</span>
                    </template>
                    <template #tip>选择后仅预览，点下方「确定」后统一上传并写入当前项目；单张不超过 30M，最多 9 张。</template>
                  </KoiUploadImages>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </template>
      </KoiDialog>
    </KoiCard>
  </div>
</template>

<style scoped lang="scss">
::deep(.el-transfer-panel__body) {
  height: 400px;
}

/* 列表缩略图：固定尺寸，避免大图撑开行高 */
.preview-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 0;
}

.list-thumb-image {
  width: 56px;
  height: 56px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.list-thumb-image :deep(.el-image__inner),
.list-thumb-image :deep(.el-image__wrapper) {
  width: 56px !important;
  height: 56px !important;
}

.thumb-error-icon {
  color: var(--el-color-primary);
}

.ml-6px {
  margin-left: 6px;
}
</style>

