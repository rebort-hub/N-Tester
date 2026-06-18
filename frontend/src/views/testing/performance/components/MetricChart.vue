<template>
	<div
		class="metric-chart-panel"
		:class="{ 'is-dark': darkMode }"
		@mousemove="onMouseMove"
		@mouseleave="onMouseLeave"
	>
		<div class="panel-title-handle" />
		<el-tooltip v-if="expandable" content="放大" placement="top" :show-after="400">
			<el-button class="panel-expand-btn" size="small" text circle @click="handleExpand">
				<el-icon><ele-FullScreen /></el-icon>
			</el-button>
		</el-tooltip>
		<div ref="chartRef" class="panel-chart" :style="{ height: chartHeight + 'px' }" />

		<!-- 自定义 Y 轴横向十字线：吸附到最近数据点（ECharts trigger:axis 模式下 Y 轴无法原生吸附） -->
		<div v-if="yCrossVisible" class="y-snap-line" :style="{ top: yCrossTop + 'px' }" />
		<div v-if="yCrossVisible" class="y-snap-label" :style="{ top: (yCrossTop - 10) + 'px', right: yCrossRight + 'px' }">
			{{ yCrossVal }}
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';

export interface SeriesItem {
	name: string;
	data: number[];
}

const props = withDefaults(defineProps<{
	title: string;
	unit: string;
	series: SeriesItem[];
	timeLabels: string[];
	darkMode?: boolean;
	expandable?: boolean;
	chartHeight?: number;
}>(), {
	darkMode: false,
	expandable: true,
	chartHeight: 180,
});

const emit = defineEmits<{
	(e: 'expand', cfg: { title: string; unit: string; series: SeriesItem[]; timeLabels: string[] }): void;
}>();

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// Grafana 配色方案
const DARK_COLORS  = ['#7EB26D', '#EAB839', '#6ED0E0', '#EF843C', '#E24D42', '#1F78C1', '#BA43A9'];
const LIGHT_COLORS = ['#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE', '#3BA272', '#FC8452'];

// hex → rgba，用于悬停外环半透明色
const hexToRgba = (hex: string, alpha: number) => {
	const r = parseInt(hex.slice(1, 3), 16);
	const g = parseInt(hex.slice(3, 5), 16);
	const b = parseInt(hex.slice(5, 7), 16);
	return `rgba(${r},${g},${b},${alpha})`;
};

const buildOption = (dark: boolean): echarts.EChartsOption => {
	const colors = dark ? DARK_COLORS : LIGHT_COLORS;
	const gridColor  = dark ? 'rgba(255,255,255,0.08)' : '#f0f0f0';
	const axisColor  = dark ? '#32333a' : '#e0e0e0';
	const labelColor = dark ? '#9fa7b3' : '#909399';
	const titleColor = dark ? '#d8d9da' : '#303133';
	const tooltipBg  = dark ? '#1c2128' : '#fff';
	const tooltipBorder = dark ? '#454c53' : '#ddd';
	const fontFamily = 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

	return {
		backgroundColor: dark ? '#181b1f' : 'transparent',
		color: colors,
		title: {
			text: props.title,
			textStyle: { color: titleColor, fontSize: 13, fontWeight: 'bold', fontFamily },
			top: 6,
			left: 'center',
		},
		tooltip: {
			trigger: 'axis',
			backgroundColor: tooltipBg,
			borderColor: tooltipBorder,
			textStyle: { color: dark ? '#d8d9da' : '#303133', fontSize: 12, fontFamily },
			axisPointer: {
				type: 'cross',
				// Y 轴横线隐藏（由自定义 DOM 吸附替代）
				crossStyle: { width: 0, color: 'transparent' },
				lineStyle: {
					color: dark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.12)',
					width: 1,
					type: 'dashed',
				},
				label: {
					show: true,
					fontSize: 12,
					padding: [3, 6],
					backgroundColor: dark ? 'rgba(44,50,53,0.85)' : 'rgba(220,222,226,0.8)',
					color: dark ? '#c2cad6' : '#666',
					fontFamily,
					borderWidth: 0,
				},
			},
			formatter: (params: any) => {
				if (!Array.isArray(params) || !params.length) return '';
				const now = new Date();
				const yyyy = now.getFullYear();
				const mm   = String(now.getMonth() + 1).padStart(2, '0');
				const dd   = String(now.getDate()).padStart(2, '0');
				const time = `${params[0].axisValue}:00`;
				const dateTime = `${yyyy}-${mm}-${dd} ${time}`;
				let html = `<div style="margin-bottom:4px;font-weight:600;">${dateTime}</div>`;
				params.forEach((p: any) => {
					html += `<div style="display:flex;align-items:center;gap:8px;line-height:1.8;">
						<span style="display:inline-block;width:12px;height:2px;background:${p.color};border-radius:1px;"></span>
						<span style="flex:1">${p.seriesName}</span>
						<span style="font-weight:600;">${p.value}</span>
					</div>`;
				});
				return html;
			},
		},
		legend: {
			data: props.series.map(s => s.name),
			bottom: 2,
			left: 'center',
			textStyle: { color: labelColor, fontSize: 12, fontWeight: 500, fontFamily },
			itemWidth: 16,
			itemHeight: 2,
			icon: 'rect',
		},
		grid: {
			left: 8,
			right: 18,
			top: 44,
			bottom: 34,
			containLabel: true,
		},
		xAxis: {
			type: 'category',
			data: props.timeLabels,
			boundaryGap: false,
			axisLine: { lineStyle: { color: axisColor } },
			axisTick: { show: false },
			axisLabel: { color: labelColor, fontSize: 12, fontWeight: 400, fontFamily },
			splitLine: { show: true, lineStyle: { color: gridColor } },
		},
		yAxis: {
			type: 'value',
			name: props.unit,
			nameLocation: 'end',
			nameTextStyle: { color: labelColor, fontSize: 12, fontWeight: 400, align: 'right', verticalAlign: 'bottom', padding: [0, 0, 2, 0], fontFamily },
			axisLine: { show: false },
			axisTick: { show: false },
			axisLabel: { color: labelColor, fontSize: 12, fontWeight: 400, fontFamily },
			splitLine: { show: true, lineStyle: { color: gridColor } },
			// 隐藏 ECharts Y 轴 cross 标注（由自定义 DOM 替代）
			axisPointer: { show: false },
		},
		series: props.series.map((s, i) => ({
			name: s.name,
			type: 'line',
			data: s.data,
			smooth: false,
			symbol: 'circle',
			symbolSize: 5,
			showSymbol: true,
			lineStyle: { width: 1.5, color: colors[i % colors.length] },
			itemStyle: { color: colors[i % colors.length] },
			emphasis: {
				scale: false,
				itemStyle: {
					color: colors[i % colors.length],
					borderColor: hexToRgba(colors[i % colors.length], 0.35),
					borderWidth: 6,
				},
			},
		})),
	};
};

const initChart = () => {
	if (!chartRef.value) return;
	chartInstance?.dispose();
	chartInstance = echarts.init(chartRef.value);
	chartInstance.setOption(buildOption(!!props.darkMode));
};

watch(() => props.darkMode, () => {
	if (!chartRef.value) return;
	chartInstance?.dispose();
	chartInstance = echarts.init(chartRef.value);
	chartInstance.setOption(buildOption(!!props.darkMode));
});

watch(() => [props.series, props.timeLabels], () => {
	chartInstance?.setOption(buildOption(!!props.darkMode));
}, { deep: true });

const ro = typeof ResizeObserver !== 'undefined'
	? new ResizeObserver(() => chartInstance?.resize())
	: null;

onMounted(() => {
	initChart();
	if (chartRef.value && ro) ro.observe(chartRef.value);
});

onBeforeUnmount(() => {
	ro?.disconnect();
	chartInstance?.dispose();
	chartInstance = null;
});

const handleExpand = () => {
	emit('expand', { title: props.title, unit: props.unit, series: props.series, timeLabels: props.timeLabels });
};

// ── 自定义 Y 轴吸附十字线 ─────────────────────────────────────
const yCrossVisible = ref(false);
const yCrossTop = ref(0);
const yCrossVal = ref('');
const yCrossRight = ref(0); // 距容器右边距，使标注紧贴 Y 轴

const onMouseMove = (e: MouseEvent) => {
	if (!chartInstance || !chartRef.value) return;
	const rect = chartRef.value.getBoundingClientRect();
	const px = e.clientX - rect.left;
	const py = e.clientY - rect.top;

	// 仅在图表网格区域内响应
	if (!chartInstance.containPixel('grid', [px, py])) {
		yCrossVisible.value = false;
		return;
	}

	const [xF, yF] = chartInstance.convertFromPixel({ gridIndex: 0 }, [px, py]) as [number, number];
	const xI = Math.max(0, Math.min(Math.round(xF), props.timeLabels.length - 1));

	// 在当前 X 位置，找与鼠标 Y 值最近的系列数据点
	let bestY = yF;
	let minDiff = Infinity;
	props.series.forEach(s => {
		const v = s.data[xI];
		if (v != null) {
			const diff = Math.abs(Number(v) - yF);
			if (diff < minDiff) { minDiff = diff; bestY = Number(v); }
		}
	});

	// 将吸附后的数据坐标转回像素坐标
	// 用第一个时间标签作为 X 参考（category 轴需传字符串，不能传数字索引）
	const refX = props.timeLabels[0] ?? 0;
	const [yAxisPx, snappedPy] = chartInstance.convertToPixel({ gridIndex: 0 }, [refX, bestY]) as [number, number];

	yCrossTop.value = snappedPy;
	// 保留有效小数：整数直接显示，小数去掉尾部零（最多保留 2 位）
	yCrossVal.value = parseFloat(bestY.toFixed(2)).toString();
	// 标注右对齐到 Y 轴位置（距容器右边 = 容器宽 - Y轴像素X + 4）
	yCrossRight.value = chartRef.value.offsetWidth - yAxisPx + 4;
	yCrossVisible.value = true;
};

const onMouseLeave = () => {
	yCrossVisible.value = false;
};
</script>

<style scoped lang="scss">
.metric-chart-panel {
	position: relative;
	border: 1px solid var(--el-border-color);
	border-radius: 6px;
	overflow: hidden;
	background: var(--el-fill-color-blank);

	&.is-dark {
		border-color: #32333a;
		background: #181b1f;

		.panel-expand-btn {
			color: #9e9e9e !important;

			&:hover {
				color: #d9d9d9 !important;
				background: rgba(255, 255, 255, 0.1) !important;
			}
		}

		.y-snap-line {
			border-top-color: rgba(255, 255, 255, 0.28);
		}

		.y-snap-label {
			background: rgba(44, 50, 53, 0.92);
			color: #c2cad6;
		}
	}

	.panel-title-handle {
		position: absolute;
		top: 0;
		left: 0;
		right: 0;
		height: 40px;
		z-index: 5;
		cursor: move;
	}

	.panel-expand-btn {
		position: absolute;
		top: 4px;
		right: 4px;
		z-index: 10;
		color: var(--el-text-color-secondary);
		opacity: 0;
		transition: opacity 0.15s;
	}

	&:hover .panel-expand-btn {
		opacity: 1;
	}

	.panel-chart {
		width: 100%;
	}

	// 自定义 Y 轴横向吸附十字线
	.y-snap-line {
		position: absolute;
		left: 0;
		right: 0;
		height: 0;
		border-top: 1px dashed rgba(0, 0, 0, 0.25);
		pointer-events: none;
		z-index: 6;
	}

	// 自定义 Y 轴标注（紧贴 Y 轴，右对齐）
	.y-snap-label {
		position: absolute;
		height: 20px;
		line-height: 20px;
		padding: 0 5px;
		font-size: 12px;
		border-radius: 2px;
		background: rgba(220, 222, 226, 0.92);
		color: #555;
		pointer-events: none;
		z-index: 7;
		white-space: nowrap;
	}
}
</style>
