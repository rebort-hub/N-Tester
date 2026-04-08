<template>
    <div>
        <el-card class="box-card">
            <div style="margin-bottom: 10px;">
                <el-radio-group v-model="device_type" @change="debouncedGetDeviceList">
                    <el-button type="primary" icon="Refresh" plain @click="getDeviceList" style="margin-right: 10px;">刷新状态</el-button>
                    <el-radio label="" disabled>手机品牌：</el-radio>
                    <el-radio label="">所有设备</el-radio>
                    <el-radio label="HUAWEI">华为</el-radio>
                    <el-radio label="XIAOMI">小米</el-radio>
                    <el-radio label="OPPO">OPPO</el-radio>
                    <el-radio label="HONOR">荣耀</el-radio>
                    <el-radio label="vivo">Vivo</el-radio>
                    <el-radio label="OnePlus">一加</el-radio>
                    <el-radio label="samsung">三星</el-radio>
                    <el-radio label="google">Google</el-radio>
                    <el-radio label="iOS">iPhone</el-radio>
                </el-radio-group>
            </div>
            <div style="margin-bottom: 10px;">
                <el-radio-group v-model="device_version" @change="debouncedGetDeviceList">
                    <el-button type="success" icon="Plus" plain @click="Add_device" style="margin-right: 10px;">添加设备</el-button>
                    <el-radio label="" disabled>系统版本：</el-radio>
                    <el-radio label="">所有版本</el-radio>
                    <el-radio label="16">16</el-radio>
                    <el-radio label="15">15</el-radio>
                    <el-radio label="14">14</el-radio>
                    <el-radio label="13">13</el-radio>
                    <el-radio label="12">12</el-radio>
                    <el-radio label="11">11</el-radio>
                    <el-radio label="10">10</el-radio>
                </el-radio-group>
            </div>
            <div>
                <el-radio-group v-model="device_status" @change="debouncedGetDeviceList">
                    <el-radio label="" disabled>设备状态：</el-radio>
                    <el-radio label="">所有状态</el-radio>
                    <el-radio :label="1">空闲</el-radio>
                    <el-radio :label="2">使用中</el-radio>
                    <el-radio :label="3">离线</el-radio>
                </el-radio-group>
            </div>
        </el-card>

        <el-card class="box-card mt-10px">
            <el-row :gutter="8">
                <el-col :span="3" v-for="(item, index) in device_list" :key="index" style="padding-bottom: 5px;">
                    <div class="device-card-wrapper">
                        <div class="device-image-container">
                            <el-badge v-if="item.device_status == 1" value="空闲" class="item" type="success" :offset="[-130, 5]">
                                <el-image :src="getDeviceImage(item)" style="width: 120px; height: 120px;" />
                            </el-badge>
                            <el-badge v-if="item.device_status == 2" value="使用中" class="item" type="danger" :offset="[-140, 5]">
                                <el-image :src="getDeviceImage(item)" style="width: 120px; height: 120px;" />
                            </el-badge>
                            <el-badge v-if="item.device_status == 3" value="离线" class="item" type="info" :offset="[-130, 5]">
                                <el-image :src="getDeviceImage(item)" style="width: 120px; height: 120px;" />
                            </el-badge>
                        </div>
                        <div class="device-info">
                            <div class="device-name">{{ item.device_name }}</div>
                            <div class="device-phone">{{ item.device_info?.phone }}</div>
                        </div>
                        <div class="device-actions">
                            <el-popover placement="top-start" :width="200" trigger="hover">
                                <template #default>
                                    <el-descriptions :title="item.device_name" column="1">
                                        <el-descriptions-item label="手机卡:">{{ item.device_info?.phone }}</el-descriptions-item>
                                        <el-descriptions-item label="系统版本:">{{ item.device_version }}</el-descriptions-item>
                                        <el-descriptions-item label="CPU:">{{ item.device_info?.cpu }}</el-descriptions-item>
                                        <el-descriptions-item label="内存:">{{ item.device_info?.memory }}</el-descriptions-item>
                                        <el-descriptions-item label="运行内存:">{{ item.device_info?.running_memory }}</el-descriptions-item>
                                        <el-descriptions-item label="电池:">{{ item.device_info?.battery }}</el-descriptions-item>
                                        <el-descriptions-item label="分辨率:">{{ item.device_info?.display }}</el-descriptions-item>
                                        <el-descriptions-item label="屏幕尺寸:">{{ item.device_info?.screen }}</el-descriptions-item>
                                    </el-descriptions>
                                </template>
                                <template #reference>
                                    <el-button type="text" size="small">
                                        <el-icon><View /></el-icon>
                                        设备信息
                                    </el-button>
                                </template>
                            </el-popover>
                            <el-button v-if="item.device_status == 1" type="text" size="small" @click="use_phone(item)">
                                <el-icon><Pointer /></el-icon>
                                立即使用
                            </el-button>
                            <el-button v-if="item.device_status != 1" disabled type="text" size="small">
                                <el-icon><Pointer /></el-icon>
                                立即使用
                            </el-button>
                        </div>
                        <!-- 添加引导小图标 - 进度条样式 -->
                        <div class="device-progress-bar">
                            <div class="progress-line"></div>
                        </div>
                    </div>
                </el-col>
            </el-row>
            <div class="h-5px"></div>
            <el-pagination 
                v-model:current-page="searchParams.currentPage" 
                v-model:page-size="searchParams.pageSize" 
                :total="total" 
                :page-sizes="[24, 50, 100]" 
                layout="total, sizes, prev, pager, next, jumper" 
                @size-change="handlePageChange" 
                @current-change="handlePageChange" 
            />
        </el-card>

        <el-dialog v-model="useDialogVisible" :title="title" width="94%" :before-close="useDialogBeforeClose" destroy-on-close>
            <div class="cloud-use-dialog-body">
                <div class="cloud-use-dialog-left">
                    <iframe :src="device_url" style="width: 97%; height: 730px" />
                </div>
                <div class="cloud-use-dialog-right">
                    <el-tabs v-model="use_active" type="card" @tab-click="tab_click">
                        <el-tab-pane label="安装APP" name="install">
                            <div>
                                <div class="flex justify-center" style="margin-bottom: 10px;">
                                    <KoiUploadFiles
                                        v-model="apk_path"
                                        :acceptType="'.apk,.aab'"
                                        :acceptTypes="'.apk, .aab'"
                                        :file-name="apk_path"
                                        @file-success="call_back"
                                    />
                                </div>
                                <el-table border :data="install_history" empty-text="暂时没有数据">
                                    <el-table-column label="序号" type="index" width="50"></el-table-column>
                                    <el-table-column label="设备名称" prop="device_name" width="120"></el-table-column>
                                    <el-table-column label="包体名称" prop="apk_name"></el-table-column>
                                    <el-table-column label="安装时间" prop="create_time" width="140"></el-table-column>
                                    <el-table-column label="操作" width="100">
                                        <template #default="{ row }">
                                            <el-button type="text" @click="install_app(row)">重新安装</el-button>
                                        </template>
                                    </el-table-column>
                                </el-table>
                            </div>
                        </el-tab-pane>
                        <el-tab-pane label="设备终端" name="first">
                            <iframe :src="shell_url" style="width: 98%; height: 650px" />
                        </el-tab-pane>

                        <el-tab-pane label="文件列表" name="second">
                            <iframe :src="file_url" style="width: 100%; height: 650px" />
                        </el-tab-pane>

                        <el-tab-pane label="设备抓包" name="third">
                            <div>
                                <el-table border :data="mitmproxy_log" empty-text="暂时没有数据哟🌻">
                                    <el-table-column label="" align="center" width="30px">
                                        <template #default="{ row }">
                                            <div v-if="row.status === 1" style="color: #0bbd87">
                                                <el-icon><CircleCheck /></el-icon>
                                            </div>
                                            <div v-else style="color: #d70e0e">
                                                <el-icon><CircleClose /></el-icon>
                                            </div>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="URL" prop="url" align="left" width="435px" :show-overflow-tooltip="true" />
                                    <el-table-column label="响应码" align="center" width="90px">
                                        <template #default="{ row }">
                                            <el-tag v-if="row.response_body?.code === 200" type="success">{{ row.response_body?.code }}</el-tag>
                                            <el-tag v-else type="danger">{{ row.response_body?.code }}</el-tag>
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="接口响应数据" align="left" width="220px" :show-overflow-tooltip="true">
                                        <template #default="{ row }">
                                            {{ row.response_body }}
                                        </template>
                                    </el-table-column>
                                    <el-table-column label="请求时间" prop="create_time" :show-overflow-tooltip="true" width="160px" />
                                    <el-table-column label="操作" align="center" width="90px">
                                        <template #default="{ row }">
                                            <el-button type="success" plain @click="mitmproxy_log_detail(row)">详情</el-button>
                                        </template>
                                    </el-table-column>
                                </el-table>
                                <div class="h-10px"></div>
                                <el-pagination
                                    background
                                    v-model:current-page="mitmproxy_log_searchParams.currentPage"
                                    v-model:page-size="mitmproxy_log_searchParams.pageSize"
                                    v-show="mitmproxy_log_total > 0"
                                    :page-sizes="[18]"
                                    layout="total, sizes, prev, pager, next, jumper"
                                    :total="mitmproxy_log_total"
                                    @size-change="mitmproxy_log_list"
                                    @current-change="mitmproxy_log_list"
                                />
                            </div>
                        </el-tab-pane>

                        <el-tab-pane label="设备性能" name="fourth">
                            <div id="chart" class="echarts" style="width: 100%; height: 600px"></div>
                        </el-tab-pane>

                        <el-tab-pane label="使用记录" name="sixth">
                            <el-table border :data="device_log" empty-text="暂时没有数据哟🌻">
                                <el-table-column label="序号" type="index"></el-table-column>
                                <el-table-column label="开始时间" prop="start_time"></el-table-column>
                                <el-table-column label="结束时间" prop="end_time"></el-table-column>
                            </el-table>
                        </el-tab-pane>
                    </el-tabs>
                </div>
            </div>
            <template #footer>
                <el-button @click="stop_phone">停止使用</el-button>
            </template>
        </el-dialog>

        <el-dialog
            v-model="mitmproxy_detail_visible"
            title="请求详情"
            width="1000px"
            :close-on-click-modal="false"
            destroy-on-close
        >
            <div style="color: rgb(18 31 205);">
                <div>URL：{{ mitmproxy_api_details.url }}</div>
                <div>
                    请求方法：{{ mitmproxy_api_details.method }} --- 响应时长：{{
                        mitmproxy_api_details.res_time + ' ms'
                    }}
                </div>
            </div>

            <el-tabs style="margin-top: 10px;">
                <el-tab-pane label="Request Headers">
                    <vue-json-pretty
                        v-model:data="mitmproxy_api_details.request_headers"
                        :height="250"
                        :showIcon="true"
                        :showLine="true"
                        :virtual="true"
                        :showSelectController="true"
                    />
                </el-tab-pane>
                <el-tab-pane label="Request Body">
                    <vue-json-pretty
                        v-model:data="mitmproxy_api_details.request_body"
                        :height="250"
                        :showIcon="true"
                        :showLine="true"
                        :virtual="true"
                        :showSelectController="true"
                    />
                </el-tab-pane>
                <el-tab-pane label="Response Headers">
                    <vue-json-pretty
                        v-model:data="mitmproxy_api_details.response_headers"
                        :height="250"
                        :showIcon="true"
                        :showLine="true"
                        :virtual="true"
                        :showSelectController="true"
                    />
                </el-tab-pane>
                <el-tab-pane label="Response Body">
                    <vue-json-pretty
                        v-model:data="mitmproxy_api_details.response_body"
                        :height="250"
                        :showIcon="true"
                        :showLine="true"
                        :virtual="true"
                        :showSelectController="true"
                    />
                </el-tab-pane>
            </el-tabs>
        </el-dialog>

        <el-dialog v-model="addDeviceDialogVisible" :title="title" width="700px" destroy-on-close>
            <el-form :model="add_device_form" label-width="100px">
                <el-form-item label="设备名称">
                    <el-input v-model="add_device_form.device_name" />
                </el-form-item>
                <el-form-item label="设备类型">
                    <el-input v-model="add_device_form.device_type" placeholder="如: Android, iOS" />
                </el-form-item>
                <el-form-item label="设备版本">
                    <el-input v-model="add_device_form.device_version" placeholder="如: 13.0" />
                </el-form-item>
                <el-form-item label="设备ID">
                    <el-input v-model="add_device_form.device_id" placeholder="设备唯一标识" />
                </el-form-item>
                <el-form-item label="设备图片">
                    <el-input v-model="add_device_form.file_path" placeholder="请输入图片路径" />
                </el-form-item>
                <el-form-item label="设备信息">
                    <el-input v-model="device_info_json" type="textarea" :rows="6" placeholder="请输入设备信息JSON" />
                </el-form-item>
                <el-form-item label="设备描述">
                    <el-input v-model="add_device_form.device_description" type="textarea" />
                </el-form-item>
            </el-form>
            <template #footer>
                <el-button @click="add_device_cancel">取消</el-button>
                <el-button type="primary" @click="add_device_confirm">确定</el-button>
            </template>
        </el-dialog>
    </div>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useCloudDeviceApi } from '/@/api/v1/cloud_device';
import { ElLoading, ElMessage, ElMessageBox, ElNotification } from 'element-plus';
import { CircleCheck, CircleClose, View, Pointer } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import KoiUploadFiles from '/@/components/koi/KoiUploadFiles.vue';
import devicePlaceholder from '/@/assets/device-placeholder.svg';
import VueJsonPretty from 'vue-json-pretty';
import 'vue-json-pretty/lib/styles.css';
import { mitmproxy_check, mitmproxy_close_agent, mitmproxy_run_log, mitmproxy_single_start, mitmproxy_stop } from '/@/api/v1/mitmproxy';

const {
  device_info_list,
  use_device,
  stop_device,
  get_device_log,
  get_history_list,
  device_install_app,
  direct_install_app,
  add_device,
  device_performance,
  sync_stf_devices,
} = useCloudDeviceApi();

// 搜索参数
const device_type = ref<any>('');
const device_version = ref<any>('');
const device_status = ref<any>('');
const device_list = ref<any>([]);
const total = ref<any>(0);
const searchParams = ref({
    search: {
        device_version: null,
        device_type: null,
        device_status: null
    },
    currentPage: 1,
    pageSize: 24
});

// APK 上传
const apk_path = ref<any>('');

const getDeviceImage = (item: any) => {
    return item?.file_path || devicePlaceholder;
};

// 获取设备列表
const getDeviceList = async () => {
    // 移除加载提示
    // 重置分页到第一页（当过滤条件改变时）
    searchParams.value.currentPage = 1;
    searchParams.value.search.device_version = device_version.value || null;
    searchParams.value.search.device_type = device_type.value || null;
    searchParams.value.search.device_status = device_status.value || null;
    
    try {
        const res = await device_info_list(searchParams.value);
        device_list.value = res.data.content;
        total.value = res.data.total;
    } catch (error) { 
        console.error('获取设备列表失败:', error); 
        ElMessage.error('获取设备列表失败');
    }
};

// 分页变化时的处理函数（不重置分页）
const handlePageChange = async () => {
    // 移除加载提示
    // 保持当前的搜索条件，不重置分页
    searchParams.value.search.device_version = device_version.value || null;
    searchParams.value.search.device_type = device_type.value || null;
    searchParams.value.search.device_status = device_status.value || null;
    
    try {
        const res = await device_info_list(searchParams.value);
        device_list.value = res.data.content;
        total.value = res.data.total;
    } catch (error) { 
        console.error('获取设备列表失败:', error); 
        ElMessage.error('获取设备列表失败');
    }
};

// 防抖函数
const debounce = (func: Function, wait: number) => {
    let timeout: any;
    return function executedFunction(...args: any[]) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// 防抖的获取设备列表函数
const debouncedGetDeviceList = debounce(getDeviceList, 300);

// 使用设备弹窗
const useDialogVisible = ref(false);
const title = ref('');
const use_active = ref('install');
const install_history = ref<any>([]);
const history_searchParams = ref({
    search: { device_id: '' },
    currentPage: 1,
    pageSize: 10
});
const log_searchParams = ref({
    search: { device_id: null },
    currentPage: 1,
    pageSize: 10
});
const device_log = ref<any>([]);
const device_url = ref('');
const shell_url = ref('');
const file_url = ref('');
const device_id = ref('');
const phone_id = ref<any>(null);
const wifi_ip = ref<any>('');
const log_id = ref<any>(null);
const log_total = ref(0);
const history_total = ref(0);
const loading = ref(false);

// mitmproxy 抓包相关
const result_id = ref<string>('');
const mitmproxy_port = 8088;
const mitmproxy_pid = ref<number>(0);
const mitmproxy_log = ref<any[]>([]);
const mitmproxy_log_total = ref<number>(0);
const mitmproxy_log_searchParams = ref<any>({
    search: {
        device_id: null, // app_devices.id
        result_id: ''
    },
    currentPage: 1,
    pageSize: 18
});
const mitmproxy_interval = ref<any>(null);
const mitmproxy_detail_visible = ref<boolean>(false);
const mitmproxy_api_details = ref<any>({});
const mitmproxy_cleanup_inflight = ref<boolean>(false);

// 性能监控
const performance = ref({
    cpu: [], memory: [], time: [], temperature: [], up_network: [], down_network: []
});
const performance_interval = ref<any>(null);
const start_status = ref(false);

// 添加设备弹窗
const addDeviceDialogVisible = ref(false);
const add_device_form = ref<any>({});
const device_info_json = ref('');

const buildShellUrlFromStream = (streamUrl: string, udid: string) => {
    if (!streamUrl) return '';
    const base = streamUrl.split('/#!action=')[0] || streamUrl.split('#!action=')[0];
    if (base) {
        return `${base}/#!action=shell&udid=${encodeURIComponent(udid)}`;
    }

    return streamUrl.replace(/#!action=stream/, '#!action=shell');
};

// 使用设备
const use_phone = async (phone: any) => {
    title.value = phone.device_name + '（系统版本：' + phone.device_version + '）';
    device_id.value = phone.device_id;
    phone_id.value = phone.id;
    wifi_ip.value = phone.wifi_ip || '';
    use_active.value = 'install';
    try {
        const res: any = await use_device({ device_id: device_id.value, id: phone_id.value });
        if (res.code !== 200) { ElMessage.error(res.message); return; }
        log_id.value = res.data.log_id;
        device_url.value = res.data.device_url;
        shell_url.value = buildShellUrlFromStream(res.data.device_url, device_id.value);
        file_url.value = res.data.file_url;
        await get_log_list();
        await get_history();
        // 进入弹窗时先清空抓包结果，避免显示上一次的记录
        mitmproxy_log.value = [];
        mitmproxy_log_total.value = 0;
        mitmproxy_log_searchParams.value.currentPage = 1;
        useDialogVisible.value = true;
    } catch (error) { console.error('使用设备失败:', error); }
};

const stop_saving = ref(false);

const stop_device_bg = async () => {
    // 避免重复停止：X 关闭和“停止使用”按钮可能同时触发
    if (stop_saving.value) return;
    const currentLogId = log_id.value;
    const currentPhoneId = phone_id.value;
    if (!currentLogId || !currentPhoneId) return;

    stop_saving.value = true;
    try {
        const res: any = await stop_device({ log_id: currentLogId, id: currentPhoneId });
        if (res?.code === 200) {
            await getDeviceList();
        }
    } catch (error) {
        console.error('停止设备失败:', error);
    } finally {
        device_url.value = '';
        file_url.value = '';
        stopPolling();
        mitmproxy_cleanup_bg();
        stop_saving.value = false;
    }
};

// =========================
// mitmproxy 抓包相关
// =========================
const mitmproxy_log_list = async () => {
    try {
        if (!phone_id.value || !result_id.value) return;
        mitmproxy_log_searchParams.value.search.device_id = phone_id.value;
        mitmproxy_log_searchParams.value.search.result_id = result_id.value;

        const res: any = await mitmproxy_run_log(mitmproxy_log_searchParams.value);
        mitmproxy_log.value = res?.data?.content || [];
        mitmproxy_log_total.value = res?.data?.total || 0;
    } catch (e) {
        console.error('抓包日志轮询失败:', e);
    }
};

const mitmproxy_log_polling = () => {
    if (mitmproxy_interval.value) return;
    mitmproxy_interval.value = setInterval(mitmproxy_log_list, 5000);
};

const mitmproxy_log_stoppolling = () => {
    if (mitmproxy_interval.value) {
        clearInterval(mitmproxy_interval.value);
        mitmproxy_interval.value = null;
    }
};

const mitmproxy_check_status = async () => {
    try {
        if (!device_id.value || !phone_id.value) return;
        const res: any = await mitmproxy_check({ deviceid: device_id.value });
        if (res?.data?.status === 'stop') {
            const startRes: any = await mitmproxy_single_start({
                deviceid: device_id.value,
                id: phone_id.value,
                port: mitmproxy_port,
                result_id: result_id.value,
                wifi_ip: wifi_ip.value
            });
            mitmproxy_pid.value = startRes?.data?.pid || 0;
        }
        mitmproxy_log_polling();
    } catch (e) {
        console.error('检查/启动抓包失败:', e);
    }
};

// 停止使用/关闭时的抓包清理（尽量不阻塞 UI）
const mitmproxy_cleanup_bg = () => {
    // 立即停止轮询（同步，保证关闭瞬间释放资源）
    mitmproxy_log_stoppolling();

    if (mitmproxy_cleanup_inflight.value) return;
    mitmproxy_cleanup_inflight.value = true;

    void (async () => {
        try {
            if (device_id.value) {
                await mitmproxy_close_agent({ deviceid: device_id.value });
                await mitmproxy_stop({
                    pid: mitmproxy_pid.value || 0,
                    port: mitmproxy_port,
                    device: [{ deviceid: device_id.value }]
                });
            }
        } catch (e) {
            // 清理失败不影响 UI 关闭
            console.error('mitmproxy 清理失败:', e);
        } finally {
            mitmproxy_pid.value = 0;
            mitmproxy_cleanup_inflight.value = false;
        }
    })();
};

const mitmproxy_log_detail = (row: any) => {
    mitmproxy_api_details.value = row;
    mitmproxy_detail_visible.value = true;
};

// 停止使用设备（点击按钮）
const stop_phone = async () => {
    try {
        await ElMessageBox.confirm('您确认停止使用：' + title.value, '温馨提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
        });

        // 立即关闭弹窗：停止请求放到后台执行，保证“实时/不阻塞”
        useDialogVisible.value = false;
        device_url.value = '';
        file_url.value = '';
        stopPolling();
        mitmproxy_cleanup_bg();
        stop_device_bg();
    } catch (error) {
        // 取消停止，不做任何事
    }
};

// 右上角 X 关闭（不弹确认框，保证立即关闭）
const useDialogBeforeClose = (done: () => void) => {
    useDialogVisible.value = false;
    device_url.value = '';
    file_url.value = '';
    stopPolling();
    mitmproxy_cleanup_bg();
    done();
    stop_device_bg();
};

// 获取安装历史
const get_history = async () => {
    history_searchParams.value.search.device_id = '';
    try {
        const res: any = await get_history_list(history_searchParams.value);
        install_history.value = res.data.content;
        history_total.value = res.data.total;
    } catch (error) { console.error('获取安装历史失败:', error); }
};

// 获取使用日志
const get_log_list = async () => {
    log_searchParams.value.search.device_id = phone_id.value;
    try {
        const res: any = await get_device_log(log_searchParams.value);
        device_log.value = res.data.content;
        log_total.value = res.data.total;
    } catch (error) { console.error('获取使用日志失败:', error); }
};

// 安装APP回调
const call_back = async (fileMap: any) => {
    ElMessage.success('上传文件成功');
    fileMap.device_id = device_id.value;
    fileMap.phone_id = phone_id.value;
    loading.value = true;
    try {
        const res: any = await device_install_app(fileMap);
        if (res.code === 200) {
            ElNotification.success({
                title: '温馨提示',
                message: fileMap.filename + '，安装成功',
                duration: 0
            });
            await get_history();
        } else {
            ElNotification.error({
                title: '温馨提示',
                message: fileMap.filename + '，安装失败，原因：' + res.message,
                duration: 0
            });
        }
    } catch (error) { console.error('安装APP失败:', error); }
    loading.value = false;
};

// 重新安装
const install_app = async (row: any) => {
    loading.value = true;
    try {
        const res: any = await direct_install_app({ device_id: device_id.value, id: row.id, filename: row.apk_name });
        if (res.code === 200) {
            ElNotification.success({
                title: '温馨提示',
                message: row.apk_name + '，安装成功',
                duration: 0
            });
        } else {
            ElNotification.error({
                title: '温馨提示',
                message: row.apk_name + '，安装失败，原因：' + res.message,
                duration: 0
            });
        }
    } catch (error) { console.error('重新安装失败:', error); }
    loading.value = false;
};

// 添加设备
const Add_device = () => {
    title.value = '添加设备';
    add_device_form.value = {
        device_name: '',
        device_info: {},
        device_type: '',
        device_version: '',
        device_status: '1',
        device_id: '',
        file_path: '', // 图片路径，可以为空
        device_description: ''
    };
    
    // 设置默认的设备信息JSON
    device_info_json.value = JSON.stringify({
        cpu: '',
        phone: '',
        memory: '',
        screen: '',
        battery: '',
        display: '',
        running_memory: ''
    }, null, 2);
    
    addDeviceDialogVisible.value = true;
};

const add_device_confirm = async () => {
    try {
        // 解析设备信息JSON
        if (device_info_json.value) {
            add_device_form.value.device_info = JSON.parse(device_info_json.value);
        }
        
        const res: any = await add_device(add_device_form.value);
        if (res.code === 200) {
            ElMessage.success(res.message);
            addDeviceDialogVisible.value = false;
            await getDeviceList();
        }
    } catch (error: any) {
        if (error.message.includes('JSON')) {
            ElMessage.error('设备信息格式错误，请输入有效的JSON格式');
        } else {
            console.error('添加设备失败:', error);
            ElMessage.error('添加设备失败');
        }
    }
};

const add_device_cancel = () => { 
    addDeviceDialogVisible.value = false; 
};

// Tab切换
const tab_click = (tab: any) => {
    const name = tab.props.name;
    if (name === 'fourth' && start_status.value === false) {
        startPolling();
    } else if (name === 'third') {
        mitmproxy_check_status();
    } else {
        stopPolling();
        mitmproxy_log_polling();
    }
};

// 获取设备性能
const get_device_performance = async () => {
    try {
        const res: any = await device_performance({ device_id: device_id.value, performance: performance.value });
        performance.value = res.data;
        await perform_result(res.data);
    } catch (error) { console.error('获取性能数据失败:', error); }
};

// 开始轮询
const startPolling = () => {
    if (performance_interval.value) return;
    start_status.value = true;
    performance_interval.value = setInterval(get_device_performance, 3000);
};

// 停止轮询
const stopPolling = () => {
    if (performance_interval.value) {
        start_status.value = false;
        clearInterval(performance_interval.value);
        performance_interval.value = null;
    }
};

// 性能图表数据
const per_time = ref<any>([]);
const cpu = ref<any>([]);
const memory = ref<any>([]);
const up_network = ref<any>([]);
const down_network = ref<any>([]);
const temperature = ref<any>([]);

// 处理性能数据并渲染图表
const perform_result = async (res: any) => {
    per_time.value = res.time;
    cpu.value = res.cpu;
    memory.value = res.memory;
    up_network.value = res.up_network;
    down_network.value = res.down_network;
    temperature.value = res.temperature;
    await getEcharts();
};

// 渲染ECharts图表
const getEcharts = async () => {
    const dom = document.getElementById('chart');
    if (!dom) return;
    let chartRefs = echarts.init(dom);
    let rq = per_time.value;
    let seriesArr: any = [];
    let list = [
        { name: 'CPU(%)', children: cpu.value },
        { name: '内存(%)', children: memory.value },
        { name: '温度(℃)', children: temperature.value },
        { name: '上传网速(KB/s)', children: up_network.value },
        { name: '下载网速(MB/s)', children: down_network.value }
    ];
    let colorArr = ['0, 62, 246', '0, 193, 142', '253, 148, 67', '211, 225, 96', '234, 66, 66'];
    list.forEach((val, index) => {
        seriesArr.push({
            name: val.name, type: 'line', symbolSize: 6, data: val.children,
            areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: `rgba(${colorArr[index]},.2)` },
                { offset: 1, color: 'rgba(255, 255, 255,0)' }
            ], false) } },
            itemStyle: { normal: { color: `rgb(${colorArr[index]})` } },
            lineStyle: { normal: { width: 2, shadowColor: `rgba(${colorArr[index]}, .2)`, shadowBlur: 4, shadowOffsetY: 25 } }
        });
    });
    let option = {
        backgroundColor: '#fff',
        tooltip: { trigger: 'axis', axisPointer: { lineStyle: { color: '#ddd' } }, backgroundColor: 'rgba(255,255,255,1)', padding: [5, 10], textStyle: { color: '#000' } },
        legend: { right: 'center', top: '6%', textStyle: { color: '#000', fontSize: 12, fontWeight: 600 }, data: list.map(val => val.name) },
        grid: { left: '2%', right: '5%', bottom: '6%', top: '18%', containLabel: true },
        xAxis: { type: 'category', data: rq, boundaryGap: false, splitLine: { show: true, interval: 'auto', lineStyle: { type: 'dashed', color: ['#cfcfcf'] } }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#cfcfcf' } }, axisLabel: { textStyle: { fontSize: 12, color: '#9e9d9f', fontWeight: 600 } } },
        yAxis: [{ name: '(%)', type: 'value', splitLine: { show: true, lineStyle: { type: 'dashed', color: ['#cfcfcf'] } }, axisTick: { show: false }, axisLine: { show: true, lineStyle: { fontSize: 12, color: '#cfcfcf' } }, axisLabel: { textStyle: { fontSize: 12, color: '#9e9d9f', fontWeight: 600 } }, max: 100 }],
        series: seriesArr
    };
    chartRefs.setOption(option);
};

onMounted(async () => {

    result_id.value = String(Date.now());
    try {
        // 进入页面先同步 STF 设备池，保证无需手工添加也能展示
        await sync_stf_devices();
    } catch (e) {
        // 忽略同步失败（未配置 STF 时不影响手动添加模式）
    }
    await getDeviceList();
});
</script>



<style scoped>
.box-card { 
    margin-bottom: 10px; 
}
.mt-10px { 
    margin-top: 10px; 
}
.mt-5px { 
    margin-top: 5px; 
}
.h-5px { 
    height: 5px; 
}
.h-10px {
    height: 10px;
}
.flex { 
    display: flex; 
}
.justify-center { 
    justify-content: center; 
}


.device-card-wrapper {
    background: #fff;
    border: 1px solid #ebeef5;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    padding: 5px;
    position: relative;
    overflow: visible; /* 确保没有滑动条 */
    transition: box-shadow 0.3s;
}

.device-card-wrapper:hover {
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.15);
}

.device-image-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px 0;
}

.device-info {
    text-align: center;
    margin: 5px 0;
}

.device-name {
    font-size: 14px;
    color: #303133;
    margin-bottom: 2px;
}

.device-phone {
    font-size: 14px;
    color: #606266;
}

.device-actions {
    display: flex;
    justify-content: space-between;
    padding: 0 10px;
    margin: 8px 0;
}

.device-actions .el-button {
    font-size: 12px;
    padding: 4px 8px;
    color: #409eff;
}

.device-actions .el-button:disabled {
    color: #c0c4cc !important;
}

.device-actions .el-button .el-icon {
    margin-right: 4px;
}

/* 引导小图标 - 进度条样式 */
.device-progress-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 4px;
    background-color: #f5f7fa;
    border-radius: 0 0 4px 4px;
}

.progress-line {
    height: 100%;
    width: 100%;
    background: linear-gradient(90deg, #e6e8eb 0%, #d3d4d6 50%, #e6e8eb 100%);
    border-radius: 0 0 4px 4px;
}


.cloud-use-dialog-body {
    display: flex;
    width: 100%;
    height: 730px;
}

.cloud-use-dialog-left {
    flex: 0 0 46%;
    min-width: 320px;
}

.cloud-use-dialog-right {
    flex: 1 1 auto;
    min-width: 0;
}

@media (max-width: 900px) {
    .cloud-use-dialog-body {
        flex-direction: column;
        height: auto;
    }
    .cloud-use-dialog-left {
        flex: 0 0 auto;
        min-width: 0;
    }
    .cloud-use-dialog-left iframe {
        height: 420px;
    }
}
</style>