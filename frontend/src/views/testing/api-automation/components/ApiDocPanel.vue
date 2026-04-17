<template>
	<div class="doc-panel-wrap">
		<template v-if="docInfo">
			<div class="doc-header">
				<span class="doc-method-badge" :style="{background: methodColor}">{{ methodName }}</span>
				<span class="doc-path">{{ docInfo.url }}</span>
				<el-tag size="small" effect="plain" type="info" style="margin-left:8px">{{ docInfo.name }}</el-tag>
			</div>
			<div v-if="docInfo.description" class="doc-desc-block">{{ docInfo.description }}</div>
			<div v-if="docInfo.parameters?.length" class="doc-section">
				<div class="doc-section-title">请求参数</div>
				<table class="doc-table">
					<thead><tr><th>参数名</th><th>位置</th><th>类型</th><th>必填</th><th>说明</th></tr></thead>
					<tbody>
						<tr v-for="p in docInfo.parameters" :key="p.name">
							<td class="doc-param-name">{{ p.name }}</td>
							<td><span class="doc-in-badge" :class="'in-'+p.in">{{ p.in }}</span></td>
							<td class="doc-type">{{ p.schema?.type || p.type || '-' }}</td>
							<td><el-tag v-if="p.required" size="small" type="danger" effect="plain">必填</el-tag><span v-else style="color:var(--el-text-color-placeholder);font-size:12px">可选</span></td>
							<td style="color:var(--el-text-color-regular)">{{ p.description || '-' }}</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-if="docInfo.responses?.length" class="doc-section">
				<div class="doc-section-title">返回响应</div>
				<div v-for="resp in docInfo.responses" :key="resp.code" style="margin-bottom:12px">
					<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
						<el-tag size="small" :type="resp.code>=200&&resp.code<300?'success':resp.code>=400?'danger':'warning'" effect="light">{{ resp.code }}</el-tag>
						<span style="font-size:13px;color:var(--el-text-color-regular)">{{ resp.description }}</span>
					</div>
					<table v-if="resp.fields?.length" class="doc-table">
						<thead><tr><th>字段名</th><th>类型</th><th>说明</th></tr></thead>
						<tbody>
							<tr v-for="f in resp.fields" :key="f.name">
								<td class="doc-param-name">{{ f.name }}</td>
								<td class="doc-type">{{ f.type || '-' }}</td>
								<td style="color:var(--el-text-color-regular)">{{ f.description || '-' }}</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</template>
		<div v-else class="doc-empty">
			<el-icon style="font-size:36px;color:#dcdfe6"><Document /></el-icon>
			<p>暂无接口文档，请先拉取 Swagger / Apifox 文档</p>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Document } from '@element-plus/icons-vue';

const props = defineProps<{ apiData: any }>();

const METHOD_MAP: Record<number, { label: string; color: string }> = {
	1: { label: 'GET', color: '#67C23A' }, 2: { label: 'POST', color: '#409EFF' },
	3: { label: 'PUT', color: '#E6A23C' }, 4: { label: 'DELETE', color: '#F56C6C' },
	5: { label: 'PATCH', color: '#8E44AD' },
};

const docInfo = computed(() => {
	const info = props.apiData?.api_info || props.apiData || {};
	const doc = info.document;
	if (!doc) return null;
	const m = info.req?.method ?? 2;
	const parameters: any[] = Array.isArray(doc.parameters) ? doc.parameters : [];
	const responses: any[] = [];
	if (doc.responses) {
		for (const [code, resp] of Object.entries(doc.responses as Record<string, any>)) {
			const content = resp.content || {};
			const ct = Object.keys(content)[0] || '';
			const schema = ct ? (content[ct]?.schema || {}) : {};
			let fields: any[] = [];
			if (schema.properties) fields = Object.entries(schema.properties).map(([k, v]: any) => ({ name: k, type: v.type || '-', description: v.description || '' }));
			responses.push({ code: Number(code), description: resp.description || '', fields });
		}
	}
	return { name: info.name || '', url: info.url || '', method: m, description: doc.description || doc.summary || '', parameters, responses };
});

const methodName = computed(() => METHOD_MAP[docInfo.value?.method ?? 2]?.label || 'GET');
const methodColor = computed(() => METHOD_MAP[docInfo.value?.method ?? 2]?.color || '#409EFF');
</script>

<style scoped>
.doc-panel-wrap { height: 100%; overflow-y: auto; padding: 0; }
.doc-header { display: flex; align-items: center; padding: 12px 20px; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color); }
.doc-method-badge { padding: 3px 10px; border-radius: 4px; color: #fff; font-size: 12px; font-weight: 700; margin-right: 10px; flex-shrink: 0; }
.doc-path { font-family: monospace; font-size: 14px; color: var(--el-text-color-primary); }
.doc-desc-block { padding: 10px 20px; font-size: 13px; color: var(--el-text-color-regular); background: var(--el-color-warning-light-9); border-bottom: 1px solid var(--el-color-warning-light-5); }
.doc-section { padding: 14px 20px; border-bottom: 1px solid var(--el-border-color-lighter); }
.doc-section-title { font-size: 13px; font-weight: 600; color: var(--el-text-color-primary); margin-bottom: 10px; padding-left: 8px; border-left: 3px solid #409eff; }
.doc-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.doc-table th { background: var(--el-fill-color-light); color: var(--el-text-color-placeholder); font-weight: 500; padding: 7px 12px; text-align: left; border-bottom: 1px solid var(--el-border-color); }
.doc-table td { padding: 7px 12px; border-bottom: 1px solid var(--el-border-color-lighter); vertical-align: top; }
.doc-table tr:hover td { background: var(--el-fill-color-lighter); }
.doc-param-name { font-family: monospace; font-size: 12px; color: #e6a23c; font-weight: 600; }
.doc-type { font-family: monospace; font-size: 12px; color: #67c23a; }
.doc-in-badge { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 11px; font-weight: 500; }
.in-query { background: var(--el-color-primary-light-9); color: #409eff; }
.in-path { background: var(--el-color-warning-light-9); color: #e6a23c; }
.in-header { background: var(--el-color-success-light-9); color: #67c23a; }
.doc-empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--el-text-color-placeholder); gap: 8px; font-size: 13px; }
</style>
