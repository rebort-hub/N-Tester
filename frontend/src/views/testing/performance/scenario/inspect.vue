<template>
	<el-drawer
		v-model="drawerVisible"
		direction="rtl"
		size="680px"
		class="scene-debug-drawer"
		:close-on-click-modal="false"
		destroy-on-close
		@open="onOpen"
		@closed="onClosed"
	>
		<!-- ── 标题栏 ── -->
		<template #header>
			<div class="dbg-header">
				<el-icon class="dbg-header-icon"><ele-Connection /></el-icon>
				<div class="dbg-header-info">
					<span class="dbg-scene-name">{{ scene?.name ?? '—' }}</span>
					<span class="dbg-jmx-name">
						<el-icon style="font-size:12px;margin-right:3px;vertical-align:-1px"><ele-Document /></el-icon>
						{{ scene?.script_name ?? '—' }}
						<span v-if="scene?.estimated_duration || scene?.known_times" class="dbg-duration">
							（预计压测耗时
							<template v-if="scene?.has_unknown_times">
								<el-tooltip content="存在循环次数控制的线程组，无法精确计算总耗时，实际时间可能超出预估" placement="top">
									<span class="dbg-duration-warn">
										<el-icon style="font-size:12px;vertical-align:-1px"><ele-WarningFilled /></el-icon>
										{{ (scene.known_times ?? scene.estimated_duration) > 0 ? formatDuration(scene.known_times ?? scene.estimated_duration) + '+' : '未知' }}
									</span>
								</el-tooltip>
							</template>
							<template v-else>{{ formatDuration(scene.estimated_duration) }}</template>
							）
						</span>
					</span>
				</div>
			</div>
		</template>

		<!-- ── 主体 ── -->
		<div class="dbg-flow">

			<!-- 进度条 -->
			<div class="dbg-progress-bar">
				<el-progress
					:percentage="progressPct"
					:status="progressPct === 100 ? 'success' : ''"
					:striped="isStreaming"
					:striped-flow="isStreaming"
					:duration="6"
					:stroke-width="8"
				/>
				<span class="dbg-progress-label">{{ doneCount }}/{{ PANEL_KEYS.length }}</span>
			</div>

			<!-- 初始加载中 -->
			<div v-if="isInitLoading" class="dbg-loading">
				<el-icon class="is-loading"><ele-Loading /></el-icon>
				<span>正在连接后端解析 JMX 场景…</span>
			</div>

			<!-- 全局错误 -->
			<el-alert v-else-if="globalError" :title="globalError" type="error" :closable="false" show-icon style="margin-top:12px" />

			<!-- 核查面板 -->
			<div v-else class="dbg-panels">

				<!-- ① 环境变量（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('used_vars')" @click="togglePanel('used_vars')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.used_vars" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('used_vars') !== false" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-fail"><ele-CircleCloseFilled /></el-icon>
							<span class="panel-num">1</span>
							<span class="panel-title">环境变量</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.used_vars" class="panel-wait">等待中…</span>
							<template v-else>
								<span class="panel-summary">{{ panelData.used_vars.total ? `脚本引用${panelData.used_vars.total} 个变量` : '无引用变量' }}</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.used_vars }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.used_vars" class="panel-content panel-content--no-pad" @click.stop>
							<div v-if="!panelData.used_vars?.total" class="empty-tip" style="padding:8px 14px">接口 URL 中未引用用户变量</div>
							<div v-else class="var-table">
								<div class="var-row var-header">
									<span class="var-name">变量名</span>
									<span class="var-value">变量值</span>
									<span class="var-desc">备注</span>
								</div>
								<div v-for="v in panelData.used_vars.vars" :key="v.name" class="var-row">
									<overflow-tip :content="v.name" class="var-name var-cell">{{ v.name }}</overflow-tip>
									<overflow-tip :content="v.value" class="var-value var-cell">{{ v.value }}</overflow-tip>
									<overflow-tip :content="v.desc" class="var-desc var-cell">{{ v.desc || '—' }}</overflow-tip>
								</div>
							</div>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ② 压测接口（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('api_interfaces')" @click="togglePanel('api_interfaces')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.api_interfaces" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('api_interfaces') !== false" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-fail"><ele-CircleCloseFilled /></el-icon>
							<span class="panel-num">2</span>
							<span class="panel-title">压测接口</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.api_interfaces" class="panel-wait">等待中…</span>
							<template v-else>
								<span class="panel-summary">{{ apiSummary }}</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.api_interfaces }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.api_interfaces" class="panel-content" @click.stop>
							<div v-if="!panelData.api_interfaces?.total" class="empty-tip">JMX 中未找到 HTTP 请求</div>
							<template v-else>
								<div v-for="g in panelData.api_interfaces?.groups" :key="g.thread_group_name" class="api-group">
									<div class="api-group-header">
										<el-tag size="small" :type="g.thread_group_enabled ? 'primary' : 'info'" effect="plain">{{ g.thread_group_type }}</el-tag>
										<span class="api-group-name">{{ g.thread_group_name }}</span>
										<span class="api-group-count">{{ g.samplers.length }} 个接口</span>
									</div>
									<div
										v-for="s in g.samplers"
										:key="s.testname"
										class="api-item"
									>
										<div class="api-left">
											<el-tag size="small" :type="methodTagType(s.method)" class="method-tag">{{ s.method }}</el-tag>
											<overflow-tip :content="s.url" class="api-url">{{ shortenUrl(s.url) }}</overflow-tip>
										</div>
										<div class="api-name">
											<el-tooltip :content="s.testname" placement="top" :show-after="400">
												<div class="api-name-inner">{{ s.testname }}</div>
											</el-tooltip>
										</div>
									</div>
								</div>
							</template>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ③ 线程配置（默认展开） -->
				<div class="dbg-panel" :class="panelClass('thread_config')" @click="togglePanel('thread_config')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.thread_config" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('thread_config') !== false" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-fail"><ele-CircleCloseFilled /></el-icon>
							<span class="panel-num">3</span>
							<span class="panel-title">线程配置</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.thread_config" class="panel-wait">等待中…</span>
							<template v-else>
								<span class="panel-summary">
									{{ (panelData.thread_config?.rows?.length ?? 0) }}个线程组，压力机<span :class="(panelData.thread_config?.workers ?? 1) > 1 ? 'mode-dist' : 'mode-single'">{{ (panelData.thread_config?.workers ?? 1) > 1 ? '分布式' : '单机' }}</span>{{ panelData.thread_config?.workers ?? 1 }}台
								</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.thread_config }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.thread_config" class="panel-content panel-content--no-pad" @click.stop>
							<div v-if="!panelData.thread_config?.rows?.length" class="empty-tip" style="padding:10px 14px">JMX 中未找到启用的线程组</div>
							<template v-else>
								<!-- 普通线程组 -->
								<el-table
									v-if="threadStandardRows.length"
									:data="threadStandardRows"
									size="small" border
									:header-cell-style="{ background: 'transparent', fontWeight: '500', fontSize: '13px', padding: '5px 0' }"
									:cell-style="{ padding: '4px 0', fontSize: '13px' }"
								>
									<el-table-column prop="name" label="线程组名称" show-overflow-tooltip width="110" />
									<el-table-column label="类型" width="68" align="center">
										<template #default="{ row }">
											<el-tag size="small" type="primary" effect="plain">{{ row.type_label }}</el-tag>
										</template>
									</el-table-column>
									<el-table-column label="总线程数" min-width="72" align="center">
										<template #default="{ row }"><span class="concur-num">{{ row.total_concurrent }}</span></template>
									</el-table-column>
									<el-table-column label="Ramp" min-width="65" align="center">
										<template #default="{ row }">{{ row.ramp_time != null ? row.ramp_time + 's' : '—' }}</template>
									</el-table-column>
									<el-table-column label="循环次数" min-width="62" align="center">
										<template #default="{ row }">{{ row.loop_forever ? '永远' : (row.loop_count ?? '—') }}</template>
									</el-table-column>
									<el-table-column label="持续" min-width="65" align="center">
										<template #default="{ row }">{{ row.loop_forever ? (row.duration != null ? row.duration + 's' : '—') : '—' }}</template>
									</el-table-column>
									<el-table-column label="延迟" min-width="60" align="center">
										<template #default="{ row }">{{ row.start_delay + 's' }}</template>
									</el-table-column>
								</el-table>

								<!-- 阶梯加压线程组 -->
								<el-table
									v-if="threadSteppingRows.length"
									:data="threadSteppingRows"
									size="small" border
									:header-cell-style="{ background: 'transparent', fontWeight: '500', fontSize: '13px', padding: '5px 0' }"
									:cell-style="{ padding: '4px 0', fontSize: '13px' }"
								>
									<el-table-column prop="name" label="线程组名称" show-overflow-tooltip width="110" />
									<el-table-column label="类型" width="85" align="center">
										<template #default="{ row }">
											<el-tag size="small" type="primary" effect="plain">{{ row.type_label }}</el-tag>
										</template>
									</el-table-column>
									<el-table-column label="目标线程" min-width="72" align="center">
										<template #default="{ row }"><span class="concur-num">{{ row.total_concurrent }}</span></template>
									</el-table-column>
									<el-table-column label="初始延迟" min-width="62" align="center">
										<template #default="{ row }">{{ row.start_delay + 's' }}</template>
									</el-table-column>
									<el-table-column label="初始线程" min-width="62" align="center">
										<template #default="{ row }">{{ row.initial_threads }}</template>
									</el-table-column>
									<el-table-column label="每步加压" prop="step_up" min-width="130" align="center" show-overflow-tooltip />
									<el-table-column label="持续" min-width="55" align="center">
										<template #default="{ row }">{{ row.flight_time + 's' }}</template>
									</el-table-column>
									<el-table-column label="每步减压" prop="step_down" min-width="72" align="center" />
								</el-table>

								<!-- 自定义阶段线程组（展平为行，第一列为线程组名称） -->
								<el-table
									v-if="threadUltimateFlat.length"
									:data="threadUltimateFlat"
									size="small" border
									:header-cell-style="{ background: 'transparent', fontWeight: '500', fontSize: '13px', padding: '5px 0' }"
									:cell-style="{ padding: '4px 0', fontSize: '13px' }"
								>
									<el-table-column prop="name" label="线程组名称" show-overflow-tooltip width="110" />
									<el-table-column label="类型" width="68" align="center">
										<template #default="{ row }">
											<el-tag size="small" type="primary" effect="plain">{{ row.type_label }}</el-tag>
										</template>
									</el-table-column>
									<el-table-column prop="phase" label="阶段" min-width="48" align="center" />
									<el-table-column label="线程数" min-width="60" align="center">
										<template #default="{ row }"><span class="concur-num">{{ row.start_threads }}</span></template>
									</el-table-column>
									<el-table-column label="初始延迟" min-width="60" align="center">
										<template #default="{ row }">{{ row.initial_delay + 's' }}</template>
									</el-table-column>
									<el-table-column label="爬坡时间" min-width="60" align="center">
										<template #default="{ row }">{{ row.startup_time + 's' }}</template>
									</el-table-column>
									<el-table-column label="持续时间" min-width="60" align="center">
										<template #default="{ row }">{{ row.hold_load_for + 's' }}</template>
									</el-table-column>
									<el-table-column label="停止时间" min-width="60" align="center">
										<template #default="{ row }">{{ row.shutdown_time + 's' }}</template>
									</el-table-column>
								</el-table>
							</template>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ④ 引用数据文件（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('data_files')" @click="togglePanel('data_files')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.data_files" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('data_files') !== false" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-fail"><ele-CircleCloseFilled /></el-icon>
							<span class="panel-num">4</span>
							<span class="panel-title">引用数据文件</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.data_files" class="panel-wait">等待中…</span>
							<template v-else>
								<span v-if="dataFilesWarnText" class="panel-warn-tag">{{ dataFilesWarnText }}</span>
								<span class="panel-summary">共 {{ panelData.data_files.total }} 个</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.data_files }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.data_files" class="panel-content" @click.stop>
							<div v-if="!panelData.data_files?.total" class="empty-tip">JMX 中未引用任何数据文件</div>
							<div v-else class="file-list">
								<div
									v-for="f in panelData.data_files.files"
									:key="f.expression ?? f.name"
									class="file-list-item"
								>
									<div :class="['file-col-name', { 'file-col-name--shrink': !!f.expression }]">
										<overflow-tip :content="f.name">{{ f.name }}</overflow-tip>
									</div>
									<div v-if="f.expression" class="file-col-expr">
										<overflow-tip :content="f.expression">{{ f.expression }}</overflow-tip>
									</div>
									<span class="file-status-tag" :class="`file-status-tag--${f.status_type || 'info'}`">{{ f.status }}</span>
								</div>
							</div>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ⑤ 后端监听器（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('backend_listeners')" @click="togglePanel('backend_listeners')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.backend_listeners" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('backend_listeners') !== false" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-fail"><ele-CircleCloseFilled /></el-icon>
							<span class="panel-num">5</span>
							<span class="panel-title">后端监听器</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.backend_listeners" class="panel-wait">等待中…</span>
							<template v-else>
								<span v-if="listenersFailCount > 0" class="panel-warn-tag">{{ listenersFailCount }} 个不可达</span>
								<span class="panel-summary">{{ listenerSummary }}</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.backend_listeners }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.backend_listeners" class="panel-content" @click.stop>
							<div v-if="!panelData.backend_listeners?.total" class="empty-tip">JMX 中未配置后端监听器</div>
							<div v-else class="listener-list">
								<div
									v-for="bl in panelData.backend_listeners?.listeners"
									:key="bl.testname"
									class="listener-item"
								>
									<div class="listener-row">
										<span class="listener-name">{{ bl.testname }}</span>
										<el-tag :type="bl.enabled ? 'success' : 'info'" size="small" effect="light">{{ bl.enabled ? '已启用' : '已禁用' }}</el-tag>
										<span v-if="bl.enabled && bl.connectivity === false" class="conn-unreachable-badge">不可达</span>
									</div>
									<div v-if="bl.influxdb_url" class="listener-url-row">
										<span class="url-label">InfluxdbURL:</span>
										<overflow-tip :content="bl.influxdb_url" class="url-text">{{ bl.influxdb_url }}</overflow-tip>
										<el-tag v-if="bl.connectivity === true" type="success" size="small" effect="light" class="conn-tag-right">连通</el-tag>
										<el-tag v-else-if="bl.connectivity === false" type="danger" size="small" effect="light" class="conn-tag-right">不可达</el-tag>
									</div>
								</div>
							</div>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ⑥ 调试组件（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('debug_components')" @click="togglePanel('debug_components')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.debug_components" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('debug_components')" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-warn"><ele-WarningFilled /></el-icon>
							<span class="panel-num">6</span>
							<span class="panel-title">调试组件</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.debug_components" class="panel-wait">等待中…</span>
							<template v-else>
								<span v-if="(panelData.debug_components?.open_count ?? 0) > 0" class="panel-warn-tag panel-warn-tag--warning">{{ panelData.debug_components.open_count }} 个未关闭</span>
								<span class="panel-summary">
									{{ panelData.debug_components?.total
										? `共 ${panelData.debug_components.total} 个，已关闭 ${panelData.debug_components.closed_count} 个`
										: '无调试组件' }}
								</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.debug_components }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.debug_components" class="panel-content" @click.stop>
							<div v-if="!panelData.debug_components?.total" class="empty-tip">JMX 中未检测到调试组件</div>
							<template v-else>
								<div class="dbg-comp-list">
									<div
										v-for="item in panelData.debug_components?.items"
										:key="item.type_label + '|' + item.testname"
										class="dbg-comp-item"
									>
										<el-icon class="dbg-comp-icon" :class="item.open_count > 0 ? 'chk-warn' : 'chk-pass'">
											<ele-WarningFilled v-if="item.open_count > 0" />
											<ele-CircleCheckFilled v-else />
										</el-icon>
										<span class="dbg-comp-type">{{ item.type_label }}</span>
										<el-tooltip :content="item.testname" placement="top" :show-after="400">
											<span class="dbg-comp-name">{{ item.testname }}</span>
										</el-tooltip>
										<span class="dbg-comp-count">{{ item.closed_count }}/{{ item.total }}</span>
										<template v-if="item.open_count > 0">
											<span class="dbg-status-open">{{ item.open_count }} 个未关闭</span>
											<span class="dbg-status-note">（压测启动会自动关闭）</span>
										</template>
										<el-tag v-else type="success" size="small" effect="light">全部已关闭</el-tag>
									</div>
								</div>
							</template>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ⑦ 压测前置准备（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('precheck')" @click="togglePanel('precheck')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.precheck" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<span class="panel-num">7</span>
							<span class="panel-title">压测前置准备</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.precheck" class="panel-wait">等待中…</span>
							<template v-else>
								<span class="panel-summary"><span :class="panelData.precheck.is_distributed ? 'mode-dist' : 'mode-single'">{{ panelData.precheck.is_distributed ? '分布式' : '单机' }}</span>模式</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.precheck }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.precheck" class="panel-content" @click.stop>
							<div v-for="item in panelData.precheck?.items" :key="item.key" class="precheck-row" :class="{ 'precheck-na': !item.applicable }">
								<el-icon class="precheck-icon" :class="!item.applicable ? 'chk-na' : item.enabled ? 'chk-pass' : 'chk-skip'">
									<ele-RemoveFilled v-if="!item.applicable" />
									<ele-CircleCheckFilled v-else-if="item.enabled" />
									<ele-RemoveFilled v-else />
								</el-icon>
								<span class="precheck-label">{{ item.label }}</span>
								<span class="precheck-script">{{ item.script }}</span>
								<span v-if="!item.applicable" class="precheck-na-tip">单机模式不适用</span>
							</div>
						</div>
					</el-collapse-transition>
				</div>

				<!-- ⑧ 服务连接状态检测（折叠展示） -->
				<div class="dbg-panel" :class="panelClass('service_check')" @click="togglePanel('service_check')">
					<div class="panel-header">
						<div class="panel-left">
							<el-icon v-if="!panelData.service_check" class="panel-icon is-loading"><ele-Loading /></el-icon>
							<el-icon v-else-if="isPanelPassed('service_check') !== false" class="panel-icon icon-done"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="panel-icon icon-fail"><ele-CircleCloseFilled /></el-icon>
							<span class="panel-num">8</span>
							<span class="panel-title">服务连接状态</span>
						</div>
						<div class="panel-right">
							<span v-if="!panelData.service_check" class="panel-wait">等待中…</span>
							<template v-else>
								<span v-if="svcCheckFailCount > 0" class="panel-warn-tag">{{ svcCheckFailCount }} 项异常</span>
								<span class="panel-summary">{{ serviceCheckSummary }}</span>
								<el-icon class="panel-arrow" :class="{ rotated: isExpanded.service_check }"><ele-ArrowDown /></el-icon>
							</template>
						</div>
					</div>
					<el-collapse-transition>
						<div v-if="isExpanded.service_check" class="panel-content" @click.stop>
							<div v-for="item in panelData.service_check?.items" :key="item.label" class="svc-row">
								<div class="svc-row-main">
									<el-icon class="svc-icon" :class="item.applicable === false ? 'chk-na' : item.ok === true ? 'chk-pass' : item.ok === false ? 'chk-fail' : 'chk-na'">
										<ele-CircleCheckFilled v-if="item.ok === true && item.applicable !== false" />
										<ele-CircleCloseFilled v-else-if="item.ok === false && item.applicable !== false" />
										<ele-RemoveFilled v-else />
									</el-icon>
									<span class="svc-label" :class="{ 'svc-label--na': item.applicable === false }">{{ item.label }}</span>
									<el-tooltip :content="item.detail" placement="top" :show-after="300" :disabled="item.applicable === false || !!item.sub?.length">
										<span class="svc-detail" :class="item.applicable === false ? 'svc-detail--na' : item.ok === false ? 'svc-detail--err' : ''">
											{{ item.applicable === false ? '--' : (item.sub?.length ? svcAggText(item) : item.detail) }}
										</span>
									</el-tooltip>
								</div>
								<!-- 多机时展示子结果 -->
								<div v-if="item.sub?.length" class="svc-sub-list">
									<div v-for="s in item.sub" :key="s.ip ?? s.role" class="svc-sub-item">
										<el-icon class="svc-sub-icon" :class="s.ok ? 'chk-pass' : 'chk-fail'">
											<ele-CircleCheckFilled v-if="s.ok" /><ele-CircleCloseFilled v-else />
										</el-icon>
										<el-tooltip
											:content="(s.role ? s.role + '  ' : '') + (s.ip ?? '') + (s.msg ? ' — ' + s.msg : '')"
											placement="top"
											:show-after="200"
										>
											<span class="svc-sub-line" :class="{ 'svc-sub-fail': !s.ok }">
												<span v-if="s.role" class="svc-sub-role">{{ s.role }}</span>
												{{ s.ip }}{{ s.msg ? ' — ' + s.msg : '' }}
											</span>
										</el-tooltip>
									</div>
								</div>
							</div>
						</div>
					</el-collapse-transition>
				</div>

			</div>
		</div>

		<!-- ── 页脚 ── -->
		<template #footer>
			<div class="dbg-footer">
				<div class="footer-notice">
					<el-icon><ele-InfoFilled /></el-icon>
					<span>{{ footerNotice }}</span>
				</div>
				<div class="footer-btns">
					<el-button @click="drawerVisible = false">{{ inspectConfirmed ? '关闭' : '取消' }}</el-button>
					<el-button
						v-if="!inspectConfirmed"
						type="primary"
						:disabled="!allDone"
						:loading="confirming"
						@click="handleConfirm"
					>
						<el-icon><ele-CircleCheck /></el-icon>确定（联调通过）
					</el-button>
					<el-button v-else type="success" @click="handleStartTest">
						<el-icon><ele-VideoPlay /></el-icon>启动压测
					</el-button>
				</div>
			</div>
		</template>
	</el-drawer>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import { usePerformanceApi } from '/@/api/v1/performance';
import OverflowTip from '../components/OverflowTip.vue';

const perfApi = usePerformanceApi();

// ── Props / Emits ──────────────────────────────────────────────────────────
const props = withDefaults(defineProps<{
	modelValue: boolean;
	scene?: any;
}>(), { modelValue: false, scene: null });

const emit = defineEmits<{
	(e: 'update:modelValue', val: boolean): void;
	(e: 'confirmed', scene: any): void;
	(e: 'start-test', scene: any): void;
}>();

const drawerVisible = computed({
	get: () => props.modelValue,
	set: (v) => emit('update:modelValue', v),
});

// ── 面板 key 列表 ──────────────────────────────────────────────────────────
const PANEL_KEYS = ['used_vars', 'api_interfaces', 'thread_config', 'data_files', 'backend_listeners', 'debug_components', 'precheck', 'service_check'] as const;
type PanelKey = typeof PANEL_KEYS[number];

// ── 状态 ──────────────────────────────────────────────────────────────────
const isInitLoading = ref(false);
const isStreaming    = ref(false);
const globalError    = ref('');
const panelData      = reactive<Partial<Record<PanelKey, any>>>({});
const isExpanded     = reactive<Record<string, boolean>>({
	api_interfaces: false, used_vars: false, thread_config: false,
	data_files: false, backend_listeners: false, debug_components: false,
	precheck: false, service_check: false,
});

// ── 计算属性 ────────────────────────────────────────────────────────────────
const doneCount   = computed(() => PANEL_KEYS.filter(k => !!panelData[k]).length);
const progressPct = computed(() => Math.round((doneCount.value / PANEL_KEYS.length) * 100));
const allDone     = computed(() => doneCount.value === PANEL_KEYS.length);

/** 各面板的通过判断 */
const isPanelPassed = (key: PanelKey): boolean | null => {
	const d = panelData[key];
	if (d === undefined) return null;
	switch (key) {
		case 'api_interfaces':    return (d.total ?? 0) > 0;
		case 'used_vars':         return true;
		case 'thread_config':     return (d.rows?.length ?? 0) > 0;
		case 'data_files': {
			if (!d.total) return true;
			const badStatuses = ['不存在', '未引用', '未分发'];
			return !(d.files ?? []).some((f: any) => badStatuses.includes(f.status));
		}
		case 'backend_listeners': {
			if (!d.total) return true;
			const enabled = (d.listeners ?? []).filter((l: any) => l.enabled);
			return !enabled.length || enabled.every((l: any) => l.connectivity === true);
		}
		case 'debug_components':
			return (d.open_count ?? 0) === 0;
		case 'precheck':     return true;
		case 'service_check': {
			if (!d.items?.length) return true;
			return !(d.items as any[]).some((i: any) => i.ok === false);
		}
		default: return null;
	}
};

const hasWarning = computed(() =>
	PANEL_KEYS.some(k => isPanelPassed(k) === false)
);

/** 面板标题行 class：通过=浅绿，失败=浅红 */
/** 调试组件：有未关闭项时为黄色警告（非红色错误） */
const isPanelWarning = (key: PanelKey): boolean => {
	if (key === 'debug_components') {
		const d = panelData[key];
		return !!d && (d.open_count ?? 0) > 0;
	}
	return false;
};

const panelClass = (key: PanelKey) => {
	const passed = isPanelPassed(key);
	const warn   = isPanelWarning(key);
	return {
		'panel-loaded': !!panelData[key],
		'panel-pass':   passed === true,
		'panel-warn':   warn,
		'panel-fail':   passed === false && !warn,
	};
};

// ── 摘要文本 ─────────────────────────────────────────────────────────────
const apiSummary = computed(() => {
	const d = panelData.api_interfaces;
	if (!d) return '';
	return `共 ${d.total ?? 0} 个接口，${d.groups?.length ?? 0} 个线程组`;
});

const listenerSummary = computed(() => {
	const d = panelData.backend_listeners;
	if (!d) return '';
	if (!d.total) return '无监听器';
	return `${d.total} 个监听器`;
});

// ── 异常统计（驱动标题行红色标签） ─────────────────────────────────────────
const BAD_FILE_STATUSES = ['不存在', '未引用', '未分发'];

// 按状态分组，生成如 "2个不存在" 或 "1个不存在 1个未分发" 的文本
const dataFilesWarnText = computed(() => {
	const d = panelData.data_files;
	if (!d?.files) return '';
	const groups: Record<string, number> = {};
	for (const f of d.files as any[]) {
		if (BAD_FILE_STATUSES.includes(f.status)) {
			groups[f.status] = (groups[f.status] || 0) + 1;
		}
	}
	return Object.entries(groups).map(([s, n]) => `${n}个${s}`).join('  ');
});

const listenersFailCount = computed(() => {
	const d = panelData.backend_listeners;
	if (!d?.listeners) return 0;
	return (d.listeners as any[]).filter((l: any) => l.enabled && l.connectivity === false).length;
});

const svcCheckFailCount = computed(() => {
	const d = panelData.service_check;
	if (!d?.items) return 0;
	return (d.items as any[]).filter((i: any) => i.ok === false).length;
});

const serviceCheckSummary = computed(() => {
	const d = panelData.service_check;
	if (!d) return '';
	const fail = (d.items ?? []).filter((i: any) => i.ok === false).length;
	return fail ? `${d.total} 项检测` : `${d.total} 项全部正常`;
});

/** 单条 service_check 项的聚合统计文案：N/M 通过 */
const svcAggText = (item: any): string => {
	const subs = (item.sub ?? []) as any[];
	if (!subs.length) return item.detail ?? '';
	const pass = subs.filter((s: any) => s.ok).length;
	return `${pass}/${subs.length} 通过`;
};

// ── 线程配置按类型分组（驱动不同列结构展示）────────────────────────────────
const threadStandardRows = computed(() =>
	(panelData.thread_config?.rows ?? []).filter((r: any) => r.tg_type === 'standard')
);
const threadSteppingRows = computed(() =>
	(panelData.thread_config?.rows ?? []).filter((r: any) => r.tg_type === 'stepping')
);
const threadUltimateRows = computed(() =>
	(panelData.thread_config?.rows ?? []).filter((r: any) => r.tg_type === 'ultimate')
);
// Ultimate 展平：每个阶段行携带所属线程组名称和类型标签，供单张表统一渲染
const threadUltimateFlat = computed(() =>
	threadUltimateRows.value.flatMap((utg: any) =>
		(utg.ultimate_rows ?? []).map((r: any) => ({ ...r, name: utg.name, type_label: utg.type_label }))
	)
);

// ── 页脚提示文案 ───────────────────────────────────────────────────────────
const footerNotice = computed(() => {
	if (!allDone.value)     return '核实中，请稍候…';
	if (hasWarning.value)   return '核查需关注项，请确认无误后再启动联调';
	return '8 项核查全部通过，可以启动压测';
});

// ── 耗时格式化 ────────────────────────────────────────────────────────────
const formatDuration = (seconds: number): string => {
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = seconds % 60;
	const parts: string[] = [];
	if (h) parts.push(`${h}小时`);
	if (m) parts.push(`${m}分钟`);
	if (s || !parts.length) parts.push(`${s}秒`);
	return parts.join('');
};

// ── HTTP 方法颜色 ─────────────────────────────────────────────────────────
const methodTagType = (method: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
	const m = (method ?? '').toUpperCase();
	if (m === 'GET')    return 'info';
	if (m === 'POST')   return 'success';
	if (m === 'PUT' || m === 'PATCH') return 'warning';
	if (m === 'DELETE') return 'danger';
	return '';
};

// 若 URL 域名部分是 JMeter 变量（${varName}），简化为 {varName}/path；否则保留完整地址
const shortenUrl = (url: string): string => {
	if (!url) return url;
	const m = url.match(/^(?:https?:\/\/)?\$\{([^}]+)\}(?::\d+)?(\/.*)?$/);
	if (m) return `{${m[1]}}${m[2] ?? ''}`;
	return url;
};

// ── 面板折叠切换（手风琴：展开一个时自动折叠其余）──────────────────────────
const togglePanel = (key: PanelKey) => {
	if (!panelData[key]) return;
	const willExpand = !isExpanded[key];
	PANEL_KEYS.forEach(k => { isExpanded[k] = false; });
	if (willExpand) isExpanded[key] = true;
};

// ── SSE 消费 ─────────────────────────────────────────────────────────────
const fetchInspectSSE = async (scenarioId: number) => {
	isInitLoading.value = true;
	globalError.value   = '';
	PANEL_KEYS.forEach(k => { delete panelData[k]; isExpanded[k] = false; });

	try {
		const resp = await perfApi.inspectScenarioStream(scenarioId);
		if (!resp.ok || !resp.body) {
			globalError.value = `请求失败（HTTP ${resp.status}）`;
			return;
		}
		isInitLoading.value = false;
		isStreaming.value   = true;

		const reader  = resp.body.getReader();
		const decoder = new TextDecoder();
		let buffer    = '';

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split('\n');
			buffer = lines.pop() ?? '';

			for (const line of lines) {
				if (!line.startsWith('data: ')) continue;
				try {
					const evt = JSON.parse(line.slice(6));
					if (evt.type === 'item' && (PANEL_KEYS as readonly string[]).includes(evt.key)) {
						panelData[evt.key as PanelKey] = evt.data;
						// 线程配置默认展开，同时折叠其他面板（手风琴）
						if (evt.key === 'thread_config') {
							PANEL_KEYS.forEach(k => { isExpanded[k] = false; });
							isExpanded.thread_config = true;
						}
					} else if (evt.type === 'error') {
						globalError.value = evt.message ?? '未知错误';
						return;
					}
				} catch { /* 忽略单行 JSON 解析异常 */ }
			}
		}
	} catch (e) {
		globalError.value = `请求异常：${e}`;
	} finally {
		isInitLoading.value = false;
		isStreaming.value   = false;
	}
};

// ── Drawer 生命周期 ──────────────────────────────────────────────────────
const onOpen = async () => {
	if (!props.scene?.id) return;
	await fetchInspectSSE(props.scene.id);
};

const onClosed = () => {
	isInitLoading.value = false;
	isStreaming.value   = false;
	globalError.value   = '';
	inspectConfirmed.value = false;
	PANEL_KEYS.forEach(k => { delete panelData[k]; isExpanded[k] = false; });
};

const confirming = ref(false);
const inspectConfirmed = ref(false);

const handleConfirm = async () => {
	if (!props.scene?.id) return;
	confirming.value = true;
	try {
		await perfApi.updateScenarioStatus({ scenario_id: props.scene.id, status: 1 });
		emit('confirmed', props.scene);
		inspectConfirmed.value = true;
	} catch (e: any) {
		ElMessage.error(e?.response?.data?.detail || '状态更新失败');
	} finally {
		confirming.value = false;
	}
};

const handleStartTest = () => {
	emit('start-test', props.scene);
	drawerVisible.value = false;
};
</script>

<style scoped lang="scss">
// ── 标题栏 ─────────────────────────────────────────────────────────────────
.dbg-header {
	display: flex;
	align-items: center;
	gap: 10px;

	.dbg-header-icon { font-size: 20px; color: var(--el-color-primary); flex-shrink: 0; }

	.dbg-header-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}

	.dbg-scene-name {
		font-size: 15px;
		font-weight: 600;
		color: var(--el-text-color-primary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.dbg-jmx-name {
		display: flex;
		align-items: center;
	}

	.dbg-duration {
		color: var(black);
		font-size: 13px;
		margin-left: 2px;

		.dbg-duration-warn {
			display: inline-flex;
			align-items: center;
			gap: 2px;
			color: var(--el-color-warning-dark-2);
			cursor: default;
		}
	}
}

// ── 进度条 ─────────────────────────────────────────────────────────────────
.dbg-progress-bar {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 14px;

	.el-progress { flex: 1; }

	.dbg-progress-label {
		font-size: 12px;
		color: var(--el-text-color-secondary);
		white-space: nowrap;
	}
}

// ── 加载状态 ───────────────────────────────────────────────────────────────
.dbg-loading {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	gap: 12px;
	padding: 60px 0;
	color: var(--el-text-color-secondary);
	font-size: 13px;

	.el-icon { font-size: 28px; color: var(--el-color-primary); }
}

// ── 面板列表 ───────────────────────────────────────────────────────────────
.dbg-panels {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

// 面板容器
.dbg-panel {
	border: 1px solid var(--el-border-color-lighter);
	border-radius: 6px;
	overflow: hidden;
	transition: border-color 0.2s;
	cursor: default;

	&.panel-loaded { border-color: var(--el-border-color); cursor: pointer; }
	// 通过/失败面板头：使用 element 主题色变量自动适配深色
	// panel-header 背景始终是浅色（success/danger light-9），所以标题用对应深色字保证对比度（无论深浅模式）
	&.panel-pass .panel-header {
		background: var(--el-color-success-light-9);
		.panel-title { color: var(--el-color-success); }
	}
	// 黄色警告（调试组件未关闭）
	&.panel-warn .panel-header {
		background: var(--el-color-warning-light-9);
		.panel-title { color: var(--el-color-warning-dark-2); }
	}
	&.panel-fail .panel-header {
		background: var(--el-color-danger-light-9);
		.panel-title { color: var(--el-color-danger); }
	}
}

// 面板标题行
.panel-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 9px 14px;
	background: var(--el-fill-color-light);
	user-select: none;
	transition: background 0.2s;
	gap: 8px;

	.panel-left {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}

	.panel-icon { font-size: 16px; flex-shrink: 0; }
	.panel-icon.is-loading { color: var(--el-color-primary); }
	.panel-icon.icon-done  { color: var(--el-color-success); }
	.panel-icon.icon-warn  { color: var(--el-color-warning); font-size: 17px; }
	.panel-icon.icon-fail  { color: var(--el-color-danger);  font-size: 17px; }

	// 序号徽章：使用 element 主色变量，自动适配深色
	.panel-num {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 18px;
		height: 18px;
		min-width: 18px;
		border-radius: 50%;
		background: var(--el-color-primary-light-9);
		color: var(--el-color-primary);
		border: 1px solid var(--el-color-primary-light-7);
		font-size: 11px;
		font-weight: 700;
		line-height: 1;
		flex-shrink: 0;
	}

	// 标题行异常标签（红色胶囊，用于错误）
	.panel-warn-tag {
		font-size: 12px;
		color: var(--el-color-danger);
		background: var(--el-color-danger-light-9);
		border: 1px solid var(--el-color-danger-light-7);
		border-radius: 3px;
		padding: 1px 6px;
		white-space: nowrap;
		flex-shrink: 0;
		font-weight: 500;
		// 黄色变体：用于调试组件未关闭警告
		&--warning {
			color: var(--el-color-warning-dark-2);
			background: var(--el-color-warning-light-9);
			border-color: var(--el-color-warning-light-5);
		}
	}

	.panel-title { font-size: 13.5px; font-weight: 500; color: var(--el-text-color-primary); white-space: nowrap; }

	.panel-right {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
	}

	.panel-wait   { font-size: 13px; color: var(--el-text-color-placeholder); }
	.panel-summary { font-size: 13px; color: var(--el-text-color-secondary); white-space: nowrap; }
	// 模式胶囊：使用 element success/primary 色变量自动适配深色
	.mode-single  { color: var(--el-color-success); font-weight: 600; background: var(--el-color-success-light-9); border-radius: 3px; padding: 0 4px; }
	.mode-dist    { color: var(--el-color-primary); font-weight: 600; background: var(--el-color-primary-light-9); border-radius: 3px; padding: 0 4px; }

	.panel-arrow {
		font-size: 13px;
		color: var(--el-text-color-secondary);
		transition: transform 0.2s;
		flex-shrink: 0;
		&.rotated { transform: rotate(180deg); }
	}
}

// ── ④ 引用数据文件 ────────────────────────────────────────────────────────
.file-list {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.file-list-item {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 4px 8px;
	background: var(--el-fill-color-lighter);
	border-radius: 4px;
	font-size: 13px;

	// 第一列：文件名（无表达式时占满剩余宽度，有表达式时固定宽度使两列间有明显间距）
	.file-col-name {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		color: var(--el-text-color-regular);

		&--shrink {
			flex: 0 0 200px;
			width: 200px;
		}
	}

	// 第二列：完整表达式/路径，浅灰色 monospace，占剩余空间
	.file-col-expr {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		color: var(--el-text-color-placeholder);
		font-family: 'Menlo', 'Consolas', monospace;
		font-size: 12px;
	}

	// 状态标签靠右
	.file-status-tag { margin-left: auto; flex-shrink: 0; }
}

// 文件状态标签：使用 element 主题色变量自动适配深色
.file-status-tag {
	font-size: 11px;
	padding: 1px 5px;
	border-radius: 3px;
	color: #fff;
	white-space: nowrap;
	flex-shrink: 0;
	&--primary { background: var(--el-color-primary); }
	&--success { background: var(--el-color-success); }
	&--danger  { background: var(--el-color-danger); }
	&--warning { background: var(--el-color-warning); }
	&--info    { background: var(--el-color-info); }
}

// 面板内容
.panel-content {
	padding: 10px 14px;
	border-top: 1px solid var(--el-border-color-lighter);
	font-size: 13px;
	color: var(--el-text-color-regular);

	&--no-pad {
		padding: 0;
		border-top: 1px solid var(--el-border-color-lighter);
		font-size: 13px;
		color: var(--el-text-color-regular);
	}
}

// ── ① 压测接口 ────────────────────────────────────────────────────────────
.api-group {
	margin-bottom: 10px;
	&:last-child { margin-bottom: 0; }
}

.api-group-header {
	display: flex;
	align-items: center;
	gap: 6px;
	margin-bottom: 4px;
	padding: 4px 8px;
	background: var(--el-fill-color);
	border-radius: 4px;

	.api-group-name {
		font-size: 13px;
		font-weight: 500;
		flex: 1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.api-group-count {
		font-size: 13px;
		color: var(--el-text-color-secondary);
		white-space: nowrap;
		flex-shrink: 0;
	}
}

.api-item {
	display: flex;
	align-items: center;
	gap: 0;
	padding: 3px 8px;
	border-radius: 3px;
	font-size: 13px;

	&:hover { background: var(--el-fill-color-lighter); }
	&.api-disabled { opacity: 0.4; }

	// 左列：方法标签 + URL，占 2/3
	.api-left {
		flex: 2;
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 6px;
	}

	.method-tag {
		flex-shrink: 0;
		min-width: 46px;
		text-align: center;
		font-weight: 600;
		font-size: 11px;
	}

	.api-url {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--el-text-color-regular);
		font-family: 'Menlo', 'Consolas', monospace;
		font-size: 13px;
	}

	// 右列：接口名称描述，占 1/3，右对齐
	.api-name {
		flex: 0 0 33.33%;
		min-width: 0;
		overflow: hidden;
		padding-left: 8px;
		border-left: 1px solid var(--el-border-color-lighter);

		.api-name-inner {
			overflow: hidden;
			text-overflow: ellipsis;
			white-space: nowrap;
			color: var(--el-text-color-secondary);
			font-size: 13px;
			text-align: right;
		}
	}
}

// ── ② 引用变量 ────────────────────────────────────────────────────────────
.var-table {
	display: flex;
	flex-direction: column;
	font-size: 13px;
}

.var-row {
	display: grid;
	grid-template-columns: 130px 1fr 200px;
	border-bottom: 1px solid var(--el-border-color-extra-light);

	&:last-child { border-bottom: none; }

	&.var-header {
		background: transparent;
		font-weight: 500;
		font-size: 13px;
		color: var(--el-text-color-secondary);

		span { padding: 4px 10px 4px 0; }
	}

	.var-cell {
		padding: 3px 10px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		line-height: 1.6;

		&.var-value { font-family: 'Menlo', 'Consolas', monospace; }
		&.var-desc  { color: var(--el-text-color-secondary); }
	}
}

// ── ③ 线程配置 ────────────────────────────────────────────────────────────
.concur-num {
	font-weight: 600;
	color: var(--el-color-primary);
	font-size: 13px;
}

// ── ⑤ 后端监听器 ─────────────────────────────────────────────────────────
.listener-list { display: flex; flex-direction: column; }

.listener-item {
	padding: 4px 8px;
	border-radius: 3px;
	&:hover { background: var(--el-fill-color-lighter); }
}

.listener-row {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 4px;

	.listener-name { font-size: 13px; font-weight: 500; }
}

// 不可达徽章（醒目红底白字）
.conn-unreachable-badge {
	font-size: 11px;
	color: #fff;
	background: var(--el-color-danger);
	border-radius: 3px;
	padding: 1px 5px;
	font-weight: 600;
	flex-shrink: 0;
}

.listener-url-row {
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: nowrap;
	min-width: 0;
	color: var(--el-text-color-secondary);

	.url-label { font-size: 13px; color: var(--el-text-color-regular); flex-shrink: 0; }

	.url-text {
		flex: 1;
		font-size: 13px;
		font-family: 'Menlo', 'Consolas', monospace;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		min-width: 0;
		cursor: pointer;
	}

	.conn-icon { font-size: 15px; flex-shrink: 0; &.conn-ok { color: var(--el-color-success); } &.conn-err { color: var(--el-color-danger); } }

	.conn-tag-right {
		margin-left: auto;
		flex-shrink: 0;
	}
}

// ── ⑥ 调试组件 ───────────────────────────────────────────────────────────
.dbg-comp-list { display: flex; flex-direction: column; gap: 4px; }

.dbg-comp-item {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 4px 6px;
	border-radius: 4px;
	font-size: 13px;
	&:hover { background: var(--el-fill-color-lighter); }

	.dbg-comp-icon { font-size: 15px; flex-shrink: 0; }
	.chk-warn { color: var(--el-color-warning); }

	.dbg-comp-type {
		flex: 0 0 auto;
		min-width: 80px;
		padding: 1px 7px;
		border-radius: 3px;
		background: var(--el-fill-color);
		color: var(--el-text-color-regular);
		font-size: 12px;
	}

	.dbg-comp-name {
		flex: 1;
		min-width: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 13px;
		color: var(--el-text-color-secondary);
	}

	.dbg-comp-count {
		flex: 0 0 auto;
		font-size: 12px;
		color: var(--el-text-color-placeholder);
	}
}

// 调试组件状态标签：未关闭用警告色，括号注释单独灰色
// 调试组件状态："未关闭"带警告背景，"（压测启动会自动关闭）"纯灰色文字无背景
.dbg-status-open {
	display: inline-flex;
	align-items: center;
	padding: 1px 7px;
	border-radius: 3px;
	font-size: 12px;
	line-height: 1.6;
	white-space: nowrap;
	flex-shrink: 0;
	color: var(--el-color-warning-dark-2);
	background: var(--el-color-warning-light-9);
	border: 1px solid var(--el-color-warning-light-5);
}

.dbg-status-note {
	font-size: 12px;
	color: var(--el-text-color-secondary);
	flex-shrink: 0;
	margin-left: 3px;
}

// ── 通用状态图标色 ─────────────────────────────────────────────────────────
.chk-pass { color: var(--el-color-success); }
.chk-fail { color: var(--el-color-danger);  }
.chk-na   { color: var(--el-text-color-placeholder); }
.chk-skip { color: var(--el-text-color-placeholder); }

// ── ⑥ 压测前置准备 ────────────────────────────────────────────────────────
.precheck-row {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 5px 0;
	border-bottom: 1px solid var(--el-border-color-extra-light);
	font-size: 13px;

	&:last-child { border-bottom: none; }
	&.precheck-na { opacity: 0.5; }

	.precheck-icon { font-size: 16px; flex-shrink: 0; }

	.precheck-label {
		flex: 0 0 auto;
		min-width: 110px;
		font-weight: 500;
	}

	.precheck-script {
		flex: 1;
		font-family: 'Menlo', 'Consolas', monospace;
		font-size: 12px;
		color: var(--el-text-color-secondary);
		background: var(--el-fill-color);
		padding: 1px 6px;
		border-radius: 3px;
	}

	.precheck-na-tip {
		font-size: 12px;
		color: var(--el-text-color-placeholder);
		flex-shrink: 0;
	}
}

// ── ⑦ 服务连接状态 ────────────────────────────────────────────────────────
.svc-row {
	padding: 6px 0;
	border-bottom: 1px solid var(--el-border-color-extra-light);

	&:last-child { border-bottom: none; }
}

.svc-row-main {
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 13px;

	.svc-icon { font-size: 16px; flex-shrink: 0; }

	.svc-label {
		flex: 0 0 auto;
		min-width: 130px;
		font-weight: 500;
		white-space: nowrap;
	}

	.svc-detail {
		flex: 1;
		color: var(--el-text-color-secondary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;

		&--err { color: var(--el-color-danger); }
		&--na  { color: var(--el-text-color-disabled); }
	}
}

.svc-label--na { color: var(--el-text-color-disabled); }

.svc-sub-list {
	margin-top: 4px;
	padding-left: 24px;
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.svc-sub-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	color: var(--el-text-color-secondary);

	.svc-sub-icon { font-size: 13px; flex-shrink: 0; }
	.svc-sub-role { color: var(--el-text-color-placeholder); flex-shrink: 0; margin-right: 2px; }
}

.svc-sub-line {
	flex: 1;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	font-family: 'Menlo', 'Consolas', monospace;
	cursor: default;

	&.svc-sub-fail { color: var(--el-color-danger); }
}

.empty-tip {
	font-size: 13px;
	color: var(--el-text-color-secondary);
	text-align: center;
	padding: 8px 0;
}

// ── 页脚 ───────────────────────────────────────────────────────────────────
.dbg-footer {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;

	.footer-notice {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		color: var(--el-color-primary);
		flex: 1;
		min-width: 0;

		.el-icon { font-size: 14px; flex-shrink: 0; }
		span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
	}

	.footer-btns {
		display: flex;
		gap: 8px;
		flex-shrink: 0;
	}
}
</style>

<!-- 全局修复 el-drawer -->
<style lang="scss">
// 深色模式下 panel-num 序号徽章：深色背景下用实色蓝底+白字，避免浅蓝底+蓝字在深背景上糊成一片
[data-theme='dark'] .scene-debug-drawer {
	.panel-num {
		background: var(--el-color-primary) !important;
		color: var(--next-color-white) !important;
		border-color: var(--el-color-primary) !important;
	}
}

.scene-debug-drawer {
	.el-drawer__header {
		margin-bottom: 0 !important;
		padding: 12px 20px 12px !important;
		border-bottom: 1px solid var(--el-border-color-lighter);
	}
	.el-drawer__body {
		padding: 14px 16px !important;
		overflow-y: auto;
	}
	.el-drawer__footer {
		padding: 10px 16px !important;
		border-top: 1px solid var(--el-border-color-lighter);
	}
}
</style>