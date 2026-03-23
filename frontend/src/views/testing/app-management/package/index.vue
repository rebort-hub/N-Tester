<script setup lang="ts">
import { onMounted, ref } from "vue";
import { get_device_list, devices_install, devices_uninstall } from "@/api/api_app/device.ts";
import { MsgSuccess } from "@/utils/koi";
import { file_list } from "@/api/api_file/file";

const device_list = ref<any>([]);
const package_type = ref<number>();
const app_list = ref<any>([
  {
    path: "",
    config: [
      {
        deviceid: "",
        package: ""
      }
    ]
  }
]);

const uninstall_form = ref<any>({});

const package_list = ref<any>([]);

const getDeviceList = async () => {
  const res: any = await get_device_list({});
  device_list.value = res.data;
};

const add_app_list = async () => {
  app_list.value.push({
    path: "",
    config: [
      {
        deviceid: "",
        package: ""
      }
    ]
  });
};

const add_config = async (config: any) => {
  config.push({
    deviceid: "",
    package: ""
  });
};

const search_package = async (path: any) => {
  const res: any = await file_list({
    folder_path: path
  });
  package_list.value = res.data;
};
const del_app_list = async (index: any) => {
  app_list.value.splice(index, 1);
};

const del_config = async (index: any, data: any) => {
  if (data.length == 1) {
    return;
  }
  data.splice(index, 1);
};

const install_app = async () => {
  MsgSuccess("包体正在安装中，请稍后...");
  const res: any = await devices_install({
    config: app_list.value
  });
  console.log(res);
};

const uninstall_app = async () => {
  MsgSuccess("包体正在卸载中，请稍后...");
  const res: any = await devices_uninstall(uninstall_form.value);
  console.log(res);
};

onMounted(() => {
  getDeviceList();
  package_type.value = 1
  uninstall_form.value = {
    device_list: [],
    package: ""
  }
  app_list.value = [
    {
      path: "",
      config: [{
        deviceid: "",
        package: ""
      }]
    }
  ];
});
</script>

<template>
  <div style="padding: 10px">
    <koiCard>
      <div>
        <el-radio-group v-model="package_type">
          <el-radio :value="1" size="large">一键装包</el-radio>
          <el-radio :value="2" size="large">一键卸载</el-radio>
        </el-radio-group>
      </div>
      <div v-if="package_type == 1">
        <koiCard style="height: 730px; overflow: auto;">
          <div>
            <el-form :model="app_list">
              <el-form-item label="添加配置：">
                <el-button @click="add_app_list" type="primary">添加安装配置</el-button>
              </el-form-item>
              <el-form-item v-for="(app, index) in app_list" :key="index" :label="'安装配置' + index + '：'">
                <el-button @click="del_app_list(index)" type="text" icon="Delete"></el-button>
                <KoiCard>
                  <div>
                    <el-input v-model="app.path" style="width: 700px; padding-right: 10px;" placeholder="请输入路径" />
                    <el-button @click="search_package(app.path)" type="primary">搜索</el-button>
                  </div>
                  <div class="h-2"></div>
                  <div style="padding-top: 5px;" v-for="(config, config_index) in app.config" :key="config_index">请选择：
                    <el-select v-model="config.package" filterable style="width: 700px; padding-right: 10px" clearable
                      placeholder="请选择包体">
                      <el-option v-for="device in package_list" :key="device.id" :label="device.file_name"
                        :value="device.file_name"></el-option>
                    </el-select>
                    <el-select v-model="config.deviceid" filterable style="width: 400px; padding-right: 10px" clearable
                      placeholder="请选择设备">
                      <el-option v-for="device in device_list" :key="device.deviceid" :label="device.name"
                        :value="device.deviceid"></el-option>
                    </el-select>
                    <el-button @click="add_config(app.config)" type="primary">添加</el-button>
                    <el-button @click="del_config(config_index, app.config)" type="text" icon="Delete"></el-button>
                  </div>
                </KoiCard>
              </el-form-item>
            </el-form>
            <div v-if="app_list.length > 0" style="justify-content: center; display: flex;">
              <el-button @click="install_app" type="warning">立即安装包体</el-button>
            </div>
          </div>
        </koiCard>
      </div>
      <div v-if="package_type == 2">
        <koiCard style="height: 730px; overflow: auto;">
          <div>
            <el-select v-model="uninstall_form.device_list" style="width: 400px; padding-right: 10px" multiple clearable
              placeholder="请选择设备">
              <el-option v-for="device in device_list" :key="device.deviceid" :label="device.name"
                :value="device.deviceid"></el-option>
            </el-select>
            <el-input v-model="uninstall_form.package" style="width: 400px; padding-right: 10px"
              placeholder="请输入包体名称" />
            <el-button @click="uninstall_app" type="warning">立即卸载包体</el-button>
          </div>
        </koiCard>
      </div>
    </koiCard>
  </div>
</template>

<style scoped lang="scss"></style>

