<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { app_result, get_app_result_detail, get_result_log } from "@/api/api_app/app.ts";
import * as echarts from "echarts";
import {
  Check,
  Close,
  CircleCheck,
  CircleClose,
  Picture,
  Search,
  VideoPlay
} from "@element-plus/icons-vue";
import { formatDateTime } from "@/utils/formatTime";

const device_active = ref<any>("all");
const log_active = ref<any>("first");
const device_list = ref<any>([]);
const loading = ref(false);
const selectedIndex = ref<any>(null);

const handleTabClick = (tab: any) => {
  if (tab.props.name === "all") {
    device_list.value = res_form.value.device_list;
  } else if (tab.props.name === "pass") {
    device_list.value = res_form.value.device_list.filter((item: any) => item.status === 1);
  } else if (tab.props.name === "fail") {
    device_list.value = res_form.value.device_list.filter((item: any) => item.status === 0);
  }
};

const device_form = ref<any>({});
const res_form = ref<any>({});
const result_id = ref<any>("");

const get_app_result = async () => {
  const route = useRoute();
  result_id.value = route.query.result_id;
  const res: any = await get_app_result_detail({ result_id: result_id.value });
  res_form.value = res.data;
  device_list.value = res.data.device_list;
  await device_click(res.data.device_list[0], 0);
  loading.value = false;
};

const device_id = ref<any>("");
const result_form = ref<any>({});
const device_click = async (device: any, index: any) => {
  device_form.value = device;
  device_id.value = device.deviceid;
  selectedIndex.value = index;
  res_form.value.script_status.forEach((item: any) => {
    if (item.device === device_id.value) {
      result_form.value = item;
    }
  });
  await get_result();
};

const handle_script = async (tab: any) => {
  if (tab.props.label !== "结果总览") {
    const res: any = await get_result_log({
      device: device_id.value,
      menu_id: tab.props.name,
      result_id: result_id.value
    });
    run_result.value = res.data;
  } else {
    await get_result();
  }
};

const run_result = ref<any>([]);
const pre_video = ref<any>("");
const get_result = async () => {
  const res = await app_result({
    result_id: result_id.value,
    device: device_id.value
  });
  await perform_result(res.data);
  run_result.value = res.data;
  res.data.forEach((item: any) => {
    if (item.name == "执行结束") {
      pre_video.value = item.video;
    }
  });
  await getEcharts();
};

const per_time = ref<any>([]);
const cpu = ref<any>([]);
const memory = ref<any>([]);
const up_network = ref<any>([]);
const down_network = ref<any>([]);
const temperature = ref<any>([]);
const perform_result = async (result: any) => {
  if (result.length > 0) {
    const res: any = result[0];
    per_time.value = res.performance.time;
    cpu.value = res.performance.cpu;
    memory.value = res.performance.memory;
    up_network.value = res.performance.up_network;
    down_network.value = res.performance.down_network;
    temperature.value = res.performance.temperature;
  }
};

const getEcharts = async () => {
  const dom = document.getElementById("chart");
  if (!dom) return;
  const chartRefs = echarts.init(dom);
  const rq = per_time.value;
  const seriesArr: any = [];
  const list = [
    { name: "CPU(%)", children: cpu.value },
    { name: "内存(%)", children: memory.value },
    { name: "温度(℃)", children: temperature.value },
    { name: "上传网速(KB/s)", children: up_network.value },
    { name: "下载网速(KB/s)", children: down_network.value }
  ];
  const colorArr = ["0, 62, 246", "0, 193, 142", "253, 148, 67", "211, 225, 96", "234, 66, 66"];
  list.forEach((val, index) => {
    seriesArr.push({
      name: val.name,
      type: "line",
      symbolSize: 6,
      data: val.children,
      areaStyle: {
        normal: {
          color: new echarts.graphic.LinearGradient(
            0,
            0,
            0,
            1,
            [
              { offset: 0, color: `rgba(${colorArr[index]},.2)` },
              { offset: 1, color: "rgba(255, 255, 255,0)" }
            ],
            false
          )
        }
      },
      itemStyle: {
        normal: {
          color: `rgb(${colorArr[index]})`
        }
      },
      lineStyle: {
        normal: {
          width: 2,
          shadowColor: `rgba(${colorArr[index]}, .2)`,
          shadowBlur: 4,
          shadowOffsetY: 25
        }
      }
    });
  });
  const option = {
    backgroundColor: "#fff",
    tooltip: {
      trigger: "axis",
      axisPointer: {
        lineStyle: {
          color: "#ddd"
        }
      },
      backgroundColor: "rgba(255,255,255,1)",
      padding: [5, 10],
      textStyle: {
        color: "#000"
      }
    },
    legend: {
      right: "center",
      top: "6%",
      textStyle: {
        color: "#000",
        fontSize: 12,
        fontWeight: 600
      },
      data: list.map((val) => val.name)
    },
    grid: {
      left: "2%",
      right: "5%",
      bottom: "6%",
      top: "18%",
      containLabel: true
    },
    xAxis: {
      type: "category",
      data: rq,
      boundaryGap: false,
      splitLine: {
        show: true,
        interval: "auto",
        lineStyle: {
          type: "dashed",
          color: ["#cfcfcf"]
        }
      },
      axisTick: {
        show: false
      },
      axisLine: {
        lineStyle: {
          color: "#cfcfcf"
        }
      },
      axisLabel: {
        textStyle: {
          fontSize: 12,
          color: "#9e9d9f",
          fontWeight: 600
        }
      }
    },
    yAxis: [
      {
        name: "(%)",
        type: "value",
        splitLine: {
          show: true,
          lineStyle: {
            type: "dashed",
            color: ["#cfcfcf"]
          }
        },
        axisTick: {
          show: false
        },
        axisLine: {
          show: true,
          lineStyle: {
            fontSize: 12,
            color: "#cfcfcf"
          }
        },
        axisLabel: {
          textStyle: {
            fontSize: 12,
            color: "#9e9d9f",
            fontWeight: 600
          }
        },
        max: 100
      }
    ],
    series: seriesArr
  };
  chartRefs.setOption(option);
};

const getIcon = (status: any) => {
  if (status === 1 || status === 2) {
    return Check;
  } else {
    return Close;
  }
};
const colors = (status: any) => {
  if (status === 1 || status === 2) {
    return "#0bbd87";
  } else {
    return "#d70e0e";
  }
};

const get_card_style = (type: any) => {
  if (type === 0) {
    return "border-radius: 10px; border-color: #f3050d; text-align: left;";
  } else {
    return "border-radius: 10px; border-color: #67c23ae0; text-align: left";
  }
};

const img_show = ref<any>(false);
const pre_img = ref<any>("");
const pre_view = async (img: any) => {
  pre_img.value = [img];
  img_show.value = true;
};
const close_img = async () => {
  img_show.value = false;
};
const pre_view_video = async () => {
  if (pre_video.value) window.open(pre_video.value);
};

const get_colors = (status: any) => {
  if (status === 1 || status === 2) {
    return "color: #0bbd87";
  } else {
    return "color: #d70e0e";
  }
};

onMounted(() => {
  loading.value = true;
  get_app_result();
});
</script>

<template>
  <div style="padding: 10px; padding-left: 50px; padding-right: 50px" :loading="loading">
    <koiCard>
      <div style="height: 890px">
        <div style="padding-block-end: 10px">
          <div style="height: 190px">
            <div style="width: 100%">
              <div>
                <koiCard style="width: 33%; float: left; height: 190px">
                  <el-descriptions border :column="1" size="mini">
                    <el-descriptions-item label="任务名称">{{ res_form.task_name }}</el-descriptions-item>
                    <el-descriptions-item label="执行人">{{ res_form.username }}</el-descriptions-item>
                    <el-descriptions-item label="开始时间">{{ formatDateTime(res_form.start_time) }}</el-descriptions-item>
                    <el-descriptions-item label="结束时间">{{ formatDateTime(res_form.end_time) }}</el-descriptions-item>
                  </el-descriptions>
                </koiCard>
              </div>
              <div class="width-10px"></div>
              <div style="padding-right: 10px">
                <koiCard style="width: 33%; float: left; height: 190px">
                  <div style="display: flex; justify-content: center">
                    <el-card style="width: 270px" shadow="never">
                      脚本总数：
                      <span style="font-size: 26px">{{ res_form.total }}</span>
                    </el-card>
                    <el-card style="width: 270px" shadow="never">
                      未执行：
                      <span style="font-size: 26px">{{ res_form.un_run }}</span>
                    </el-card>
                  </div>
                  <div style="display: flex; justify-content: center; padding-top: 10px">
                    <el-card style="width: 270px" shadow="never">
                      通过数：
                      <span style="font-size: 26px">{{ res_form.passed }}</span>
                    </el-card>
                    <el-card style="width: 270px" shadow="never">
                      失败数：
                      <span style="font-size: 26px">{{ res_form.fail }}</span>
                    </el-card>
                  </div>
                </koiCard>
              </div>
              <div>
                <koiCard style="width: 30%; float: left; padding-right: 10px; height: 190px">
                  <div style="justify-content: center; padding-left: 34%">
                    <el-progress type="dashboard" :percentage="res_form.percent" status="success">
                      <template #default="{ percentage }">
                        <span class="percentage-value">{{ percentage }}%</span>
                        <span class="percentage-label">通过率</span>
                      </template>
                    </el-progress>
                  </div>
                </koiCard>
              </div>
            </div>
          </div>
        </div>
        <div>
          <koiCard style="height: 680px">
            <div style="width: 100%">
              <koiCard style="width: 15%; float: left">
                <div>
                  <el-tabs v-model="device_active" @tab-click="handleTabClick">
                    <el-tab-pane label="全部" name="all">
                      <div>
                        <div v-for="(device, index) in device_list" :key="index" style="padding-block-end: 10px">
                          <div :style="get_card_style(device.status)" :class="{ highlight: selectedIndex === index }"
                            style="border: 1px solid #e5e5e5">
                            <el-button v-if="device.status === 0"
                              style="padding: 0 !important; color: #f3050d; width: 60%" type="text"
                              :icon="CircleClose" circle @click="device_click(device, index)">
                              {{ device.name }}
                            </el-button>
                            <el-button v-if="device.status === 1"
                              style="padding: 0 !important; color: #0bbd87; width: 60%" type="text"
                              :icon="CircleCheck" circle @click="device_click(device, index)">
                              {{ device.name }}
                            </el-button>
                          </div>
                        </div>
                      </div>
                    </el-tab-pane>
                    <el-tab-pane label="通过" name="pass">
                      <div>
                        <div v-for="(device, index) in device_list" :key="index" style="padding-block-end: 10px">
                          <div :style="get_card_style(device.status)" :class="{ highlight: selectedIndex === index }"
                            style="border: 1px solid #e5e5e5">
                            <el-button v-if="device.status === 1"
                              style="padding: 0 !important; color: #0bbd87; width: 60%" type="text"
                              :icon="CircleCheck" circle @click="device_click(device, index)">
                              {{ device.name }}
                            </el-button>
                          </div>
                        </div>
                      </div>
                    </el-tab-pane>
                    <el-tab-pane label="失败" name="fail">
                      <div>
                        <div v-for="(device, index) in device_list" :key="index" style="padding-block-end: 10px">
                          <div :style="get_card_style(device.status)" :class="{ highlight: selectedIndex === index }"
                            style="border: 1px solid #e5e5e5">
                            <el-button v-if="device.status === 0"
                              style="padding: 0 !important; color: #f3050d; width: 60%" type="text"
                              :icon="CircleClose" circle @click="device_click(device, index)">
                              {{ device.name }}
                            </el-button>
                          </div>
                        </div>
                      </div>
                    </el-tab-pane>
                  </el-tabs>
                </div>
              </koiCard>
              <koiCard style="width: 82%; float: right">
                <div>
                  <div style="width: 66%; float: left">
                    <el-tabs v-model="log_active" @tab-click="handle_script">
                      <el-tab-pane label="结果总览" name="first">
                        <div>
                          <KoiCard>
                            <div>
                              <el-descriptions column="4">
                                <el-descriptions-item label="设备：">{{ device_form.name }}</el-descriptions-item>
                                <el-descriptions-item label="操作系统：">{{ device_form.os_type }}</el-descriptions-item>
                                <el-descriptions-item label="系统版本： ">{{ device_form.version }}</el-descriptions-item>
                                <el-descriptions-item label="进程id： ">{{ device_form.pid }}</el-descriptions-item>
                              </el-descriptions>
                            </div>
                          </KoiCard>
                        </div>
                        <div style="padding-top: 5px">
                          <KoiCard style="height: 510px">
                            <div style="width: 100%">
                              <div>
                                <KoiCard style="width: 45%; float: left; height: 487px; overflow: auto">
                                  <el-timeline style="width: 90%">
                                    <el-timeline-item center v-for="(res, index) in run_result" :key="index"
                                      :icon="getIcon(res.status)" type="primary" :color="colors(res.status)"
                                      size="large" :timestamp="'执行时间：' + formatDateTime(res.create_time)" placement="top">
                                      <KoiCard :style="get_colors(res.status)">
                                        <span>{{ "步骤：" + res.name }}</span>
                                        <span>{{ res.log }}</span>
                                        <span>
                                          <el-popover placement="right" :width="200" trigger="click">
                                            <template #reference>
                                              <el-button v-if="Object.keys(res.assert_value).length !== 0" :icon="Search"
                                                type="text" style="float: right">
                                                断言详情
                                              </el-button>
                                            </template>
                                            <div>
                                              <span>{{ "断言结果：" + res.assert_value.result }}</span>
                                              <el-button :icon="Picture" type="text" style="float: right"
                                                @click="pre_view(res.assert_value.img)">
                                                查看详情
                                              </el-button>
                                            </div>
                                          </el-popover>
                                          <el-button :icon="Picture" type="text" @click="pre_view(res.before_img)">
                                            执行前
                                          </el-button>
                                          <el-button :icon="Picture" type="text" @click="pre_view(res.after_img)">
                                            执行后
                                          </el-button>
                                        </span>
                                        <div class="img-viewer-box">
                                          <el-image-viewer v-if="img_show" :url-list="pre_img" @close="close_img" />
                                        </div>
                                      </KoiCard>
                                    </el-timeline-item>
                                  </el-timeline>
                                </KoiCard>
                              </div>
                              <div>
                                <KoiCard style="width: 50%; float: left; height: 487px; overflow: auto">
                                  <div style="padding-left: 35%">
                                    <el-progress type="dashboard" :percentage="result_form.percent" status="success">
                                      <template #default="{ percentage }">
                                        <span class="percentage-value">{{ percentage }}%</span>
                                        <span class="percentage-label">通过率</span>
                                      </template>
                                    </el-progress>
                                  </div>
                                  <div>
                                    <el-descriptions column="2">
                                      <el-descriptions-item label="脚本总数：">{{ result_form.total }}个</el-descriptions-item>
                                      <el-descriptions-item label="未执行：">{{ result_form.un_run }}个</el-descriptions-item>
                                    </el-descriptions>
                                    <el-descriptions column="2">
                                      <el-descriptions-item label="执行通过：">
                                        <el-tag type="success"> {{ result_form.passed }} 个 </el-tag>
                                      </el-descriptions-item>
                                      <el-descriptions-item label="执行失败：">
                                        <el-tag type="danger"> {{ result_form.fail }} 个 </el-tag>
                                      </el-descriptions-item>
                                    </el-descriptions>
                                    <el-descriptions column="1">
                                      <el-descriptions-item v-if="pre_video !== ''" label="视频详情：">
                                        <el-button :icon="VideoPlay" type="text" @click="pre_view_video">查看视频详情</el-button>
                                      </el-descriptions-item>
                                    </el-descriptions>
                                  </div>
                                </KoiCard>
                              </div>
                            </div>
                          </KoiCard>
                        </div>
                      </el-tab-pane>
                    </el-tabs>
                  </div>
                  <div style="width: 33%; float: left; padding-left: 5px">
                    <KoiCard style="width: 100%; float: left; height: 660px; overflow: auto">
                      <p>{{ device_form.name }}：性能情况：</p>
                      <div id="chart" class="echarts" style="width: 100%; height: 600px"></div>
                    </KoiCard>
                  </div>
                </div>
              </koiCard>
            </div>
          </koiCard>
        </div>
      </div>
    </koiCard>
  </div>
</template>

