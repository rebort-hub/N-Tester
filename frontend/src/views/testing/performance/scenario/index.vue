<template>
	<div class="perf-scene-container">
		<el-card shadow="never">
			<el-tabs v-model="activeTab" class="scene-tabs">

				<!-- Tab 1: 压测场景列表 -->
				<el-tab-pane label="压测场景列表" name="list">
					<!-- 工具栏 -->
					<div class="toolbar">
						<!-- 搜索框区（仅输入控件） -->
						<div class="toolbar-filters">
							<el-input
								v-model="query.name"
								placeholder="搜索场景名称"
								clearable
								style="width: 300px"
								@keyup.enter="handleQuery"
								@clear="handleQuery"
							>
								<template #prefix><el-icon><ele-Search /></el-icon></template>
							</el-input>
							<el-input
								v-model="query.code"
								placeholder="场景编号"
								clearable
								style="width: 160px"
								@keyup.enter="handleQuery"
								@clear="handleQuery"
							>
								<template #prefix><el-icon><ele-Search /></el-icon></template>
							</el-input>
							<el-select v-model="query.script_name" placeholder="查询脚本" clearable style="width: 160px" @change="(v: any) => v != null && handleQuery()" @clear="handleQuery">
								<el-option v-for="s in queryScriptOptions" :key="s.id" :label="s.name" :value="s.name" />
							</el-select>
							<el-select v-model="query.status" placeholder="执行状态" clearable style="width: 130px" @change="handleQuery" @clear="handleQuery">
								<el-option label="待联调" value="debug" />
								<el-option label="待开始" value="pending" />
								<el-option label="进行中" value="running" />
								<el-option label="已完成" value="completed" />
								<el-option label="已取消" value="cancelled" />
								<el-option label="失败" value="failed" />
							</el-select>
							<el-select v-model="query.test_type" placeholder="测试类型" clearable style="width: 130px" @change="handleQuery" @clear="handleQuery">
								<el-option v-for="t in TEST_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value" />
							</el-select>
							<el-input
								v-model="query.created_by"
								placeholder="创建人"
								clearable
								style="width: 160px"
								@keyup.enter="handleQuery"
								@clear="handleQuery"
							/>
						</div>
						<!-- 查询/重置（宽屏：紧跟搜索框；窄屏：换行后靠左） -->
						<div class="toolbar-query-btns">
							<el-button type="primary" @click="handleQuery">
								<el-icon><ele-Search /></el-icon>查询
							</el-button>
							<el-button @click="resetQuery">
								<el-icon><ele-RefreshRight /></el-icon>重置
							</el-button>
						</div>
						<!-- 操作按钮（始终靠右） -->
						<div class="toolbar-right">
							<el-button type="primary" @click="addUpdateRef?.open('add')">
								<el-icon><ele-Plus /></el-icon>新增压测场景
							</el-button>
							<el-button class="btn-debug" :disabled="selectedRows.length !== 1 || selectedRows[0]?.status === 'running'" @click="handleDebug">
								<el-icon><ele-Connection /></el-icon>场景联调
							</el-button>
							<el-button
								type="success"
								:disabled="selectedRows.length !== 1 || selectedRows[0]?.status !== 'pending'"
								@click="handleStartSelected"
							>
								<el-icon><ele-VideoPlay /></el-icon>启动压测
							</el-button>
							<el-button :loading="statusRefreshing" @click="handleRefreshStatus">
								<el-icon><ele-Refresh /></el-icon>刷新状态
							</el-button>
						</div>
					</div>

					<!-- 列表 -->
					<el-table
						ref="tableRef"
						v-loading="loading"
						:data="sceneList"
						border
						stripe
						style="width: 100%"
						row-key="id"
						@selection-change="handleSelectionChange"
						@expand-change="handleExpandChange"
					>
						<!-- 左固定：多选 + 展开 + 任务名称 -->
						<el-table-column type="selection" width="45" align="center" fixed="left" :selectable="(row: any) => row.status !== 'running'">
							<template #header></template>
						</el-table-column>
						<el-table-column type="expand" width="40" fixed="left">
							<template #default="{ row }">
								<div class="expand-detail">
									<!-- 无配置时占位（标准列布局）-->
									<template v-if="row.configs.length === 0">
										<table class="expand-table">
											<thead>
												<tr>
											<th style="width:60px;min-width:60px">状态</th>
											<th class="col-name" style="width:230px;min-width:230px">线程组名称</th>
											<th style="width:170px;min-width:170px">线程组类型</th>
											<th style="width:100px;min-width:100px">是否分布式</th>
                      <th style="width:100px;min-width:100px">节点线程数<el-tooltip content="ThreadGroup.num_threads：单节点同时运行的虚拟线程数（并发用户数）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></th>
                      <th><span class="th-label-flex"><span>Ramp-up 时间</span><el-tooltip content="ThreadGroup.ramp_time：所有线程启动完毕所需的时间（秒），0=同时启动" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                      <th><span class="th-label-flex"><span>循环次数</span><el-tooltip content="LoopController.loops：每个线程执行测试计划的循环次数；勾选永远循环时不限次数" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                      <th><span class="th-label-flex"><span>持续时间</span><el-tooltip content="ThreadGroup.duration：压测持续运行的时间（秒），勾选永远循环时必须大于 0" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                      <th><span class="th-label-flex"><span>启动延迟</span><el-tooltip content="ThreadGroup.delay：压测任务启动前的延迟等待时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
											<th style="width:260px;min-width:260px">操作</th>
												</tr>
											</thead>
											<tbody>
												<tr>
												<td><el-switch :model-value="true" disabled /></td>
												<td>--</td><td>--</td><td>--</td>
												<td>--</td><td>--</td><td>--</td><td>--</td><td>--</td>
												<td>
													<el-button type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-add', { row })">
														<el-icon><ele-CopyDocument /></el-icon>复制
													</el-button>
												</td>
												</tr>
											</tbody>
										</table>
									</template>

									<template v-else>
										<!-- 标准线程组（SetUp/ThreadGroup，type 0/1）-->
										<template v-if="row.configs.filter((c: any) => ['0','1'].includes(c.thread_type)).length > 0">
											<table class="expand-table">
												<thead>
													<tr>
                            <th style="width:60px;min-width:60px">状态</th>
                            <th class="col-name" style="width:230px;min-width:230px">线程组名称</th>
                            <th style="width:170px;min-width:170px">线程组类型</th>
                            <th style="width:100px;min-width:100px">预计耗时</th>
                            <th style="width:100px;min-width:100px">节点线程数<el-tooltip content="ThreadGroup.num_threads：单节点同时运行的虚拟线程数（并发用户数）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></th>
                            <th><span class="th-label-flex"><span>Ramp-up 时间</span><el-tooltip content="ThreadGroup.ramp_time：所有线程启动完毕所需的时间（秒），0=同时启动" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                            <th><span class="th-label-flex"><span>循环次数</span><el-tooltip content="LoopController.loops：每个线程执行测试计划的循环次数；勾选永远循环时不限次数" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                            <th><span class="th-label-flex"><span>持续时间</span><el-tooltip content="ThreadGroup.duration：压测持续运行的时间（秒），勾选永远循环时必须大于 0" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                            <th><span class="th-label-flex"><span>启动延迟</span><el-tooltip content="ThreadGroup.delay：压测任务启动前的延迟等待时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
                            <th style="width:260px;min-width:260px">操作</th>
													</tr>
												</thead>
												<tbody>
													<tr v-for="cfg in row.configs.filter((c: any) => ['0','1'].includes(c.thread_type))" :key="cfg.id">
												<td>
													<el-switch v-model="cfg.active" :disabled="cfg.thread_type === '0' || row.status === 'running' || row.status === 'completed'" @change="handleConfigActiveChange(row, cfg)" />
												</td>
												<td>
													<el-tooltip :content="cfg.tg_name || '--'" placement="top" :show-after="400">
														<span class="expand-text-clip">{{ cfg.tg_name || '--' }}</span>
													</el-tooltip>
												</td>
												<td>
													<span class="tg-type-tag" :class="cfg.thread_type ? `tg-type-tag--${cfg.thread_type}` : ''">
														{{ getThreadTypeLabel(cfg.thread_type) || '--' }}
													</span>
												</td>
																								<td>
													
														<span v-if="cfg.has_unknown_times" style="cursor:default;display:inline-flex;align-items:center;gap:3px">
															<el-icon :size="13" color="var(--el-color-warning)"><ele-WarningFilled /></el-icon>
															<span style="color:var(--el-color-warning)">{{ cfg.known_times > 0 ? formatDuration(cfg.known_times) : '?' }}</span>
														</span>
													<span v-else>{{ cfg.known_times > 0 ? formatDuration(cfg.known_times) : '--' }}</span>
												</td>
													<td>{{ cfg.threads ?? '--' }}</td>
													<td>{{ cfg.ramp_up != null ? `${cfg.ramp_up}s` : '--' }}</td>
													<td>{{ cfg.forever ? '永远' : (cfg.loop_count ?? '--') }}</td>
													<td>{{ cfg.forever && cfg.duration ? `${cfg.duration}s` : '--' }}</td>
													<td>{{ cfg.start_delay ? `${cfg.start_delay}s` : '0s' }}</td>
												<td>
													<template v-if="row.status === 'running'">
														<template v-if="cfg.active">
															<el-button type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
																<el-icon><ele-CopyDocument /></el-icon>复制
															</el-button>
														</template>
														<template v-else>
															<el-button type="primary" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-edit', { row, cfg })">
																<el-icon><ele-Edit /></el-icon>修改
															</el-button>
															<el-button v-if="cfg.thread_type !== '0'" type="danger" size="small" text style="font-weight:600" :disabled="['1','2','3'].includes(cfg.thread_type) && row.configs.filter((c: any) => c.thread_type === cfg.thread_type).length === 1" @click="handleDeleteConfig(row, cfg)">
																<el-icon><ele-Delete /></el-icon>删除
															</el-button>
														</template>
													</template>
													<template v-else-if="row.status === 'completed'">
														<el-button v-if="cfg.thread_type !== '0'" type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
															<el-icon><ele-CopyDocument /></el-icon>复制
														</el-button>
													</template>
													<template v-else>
														<el-button type="primary" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-edit', { row, cfg })">
															<el-icon><ele-Edit /></el-icon>修改
														</el-button>
														<el-button v-if="cfg.thread_type !== '0'" type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
															<el-icon><ele-CopyDocument /></el-icon>复制
														</el-button>
														<el-button v-if="cfg.thread_type !== '0'" type="danger" size="small" text style="font-weight:600" :disabled="cfg.active || (['1','2','3'].includes(cfg.thread_type) && row.configs.filter((c: any) => c.thread_type === cfg.thread_type).length === 1)" @click="handleDeleteConfig(row, cfg)">
															<el-icon><ele-Delete /></el-icon>删除
														</el-button>
													</template>
												</td>
													</tr>
												</tbody>
											</table>
										</template>

										<!-- 阶梯加压（Stepping，type 2）-->
										<template v-if="row.configs.filter((c: any) => c.thread_type === '2').length > 0">
											<table class="expand-table">
												<thead>
													<tr>
														<th style="width:60px;min-width:60px">状态</th>
														<th class="col-name" style="width:230px;min-width:230px">线程组名称</th>
														<th style="width:170px;min-width:170px">线程组类型</th>
														<th style="width:100px;min-width:100px">预计耗时</th>
														<th style="width:100px;min-width:100px"><span class="th-label-flex"><span>目标线程数</span><el-tooltip content="num_threads：SteppingThreadGroup 最终目标线程数" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>初始延迟(s)</span><el-tooltip content="initial_delay：延迟 X 秒后开始启动第一批线程" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>初始线程数</span><el-tooltip content="start_users_burst：第一个阶梯启动的线程数（初始爆发数）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>每步间隔(s)</span><el-tooltip content="start_users_period：每个步骤的时间间隔（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>爬坡时间(s)</span><el-tooltip content="ramp_up：步骤内的爬坡时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>每步新增</span><el-tooltip content="start_users_count：每步新增的线程数" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>满载持续(s)</span><el-tooltip content="flight_time：达到最大线程数后保持满载的时间（秒），0=不持续" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>每步减压</span><el-tooltip content="stop_users_count / stop_users_period：每多少秒停止多少个线程" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th style="width:260px;min-width:260px">操作</th>
													</tr>
												</thead>
												<tbody>
													<tr v-for="cfg in row.configs.filter((c: any) => c.thread_type === '2')" :key="cfg.id">
												<td>
													<el-switch v-model="cfg.active" :disabled="cfg.thread_type === '0' || row.status === 'running' || row.status === 'completed'" @change="handleConfigActiveChange(row, cfg)" />
												</td>
												<td>
													<el-tooltip :content="cfg.tg_name || '--'" placement="top" :show-after="400">
														<span class="expand-text-clip">{{ cfg.tg_name || '--' }}</span>
													</el-tooltip>
												</td>
												<td>
													<span class="tg-type-tag" :class="cfg.thread_type ? `tg-type-tag--${cfg.thread_type}` : ''">
														{{ getThreadTypeLabel(cfg.thread_type) || '--' }}
													</span>
												</td>
												<td>
														<span v-if="cfg.has_unknown_times" style="cursor:default;display:inline-flex;align-items:center;gap:3px">
															<el-icon :size="13" color="var(--el-color-warning)"><ele-WarningFilled /></el-icon>
															<span style="color:var(--el-color-warning)">{{ cfg.known_times > 0 ? formatDuration(cfg.known_times) : '?' }}</span>
														</span>
													<span v-else>{{ cfg.known_times > 0 ? formatDuration(cfg.known_times) : '--' }}</span>
												</td>
													<td>{{ cfg.threads ?? '--' }}</td>
													<td>{{ cfg.step_initial_delay != null ? `${cfg.step_initial_delay}s` : '--' }}</td>
													<td>{{ cfg.step_start_users_burst ?? '--' }}</td>
													<td>{{ cfg.step_start_users_period ?? '--' }}</td>
													<td>{{ cfg.step_ramp_up ?? '--' }}</td>
													<td>{{ cfg.step_start_users_count ?? '--' }}</td>
													<td>{{ cfg.step_flight_time ?? '--' }}</td>
													<td>{{ cfg.step_stop_users_period != null && cfg.step_stop_users_count != null ? `${cfg.step_stop_users_count}个/${cfg.step_stop_users_period}s` : '--' }}</td>
												<td>
													<template v-if="row.status === 'running'">
														<template v-if="cfg.active">
															<el-button type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
																<el-icon><ele-CopyDocument /></el-icon>复制
															</el-button>
														</template>
														<template v-else>
															<el-button type="primary" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-edit', { row, cfg })">
																<el-icon><ele-Edit /></el-icon>修改
															</el-button>
															<el-button type="danger" size="small" text style="font-weight:600" :disabled="row.configs.filter((c: any) => c.thread_type === cfg.thread_type).length === 1" @click="handleDeleteConfig(row, cfg)">
																<el-icon><ele-Delete /></el-icon>删除
															</el-button>
														</template>
													</template>
													<template v-else-if="row.status === 'completed'">
														<el-button v-if="cfg.thread_type !== '0'" type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
															<el-icon><ele-CopyDocument /></el-icon>复制
														</el-button>
													</template>
													<template v-else>
														<el-button type="primary" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-edit', { row, cfg })">
															<el-icon><ele-Edit /></el-icon>修改
														</el-button>
														<el-button v-if="cfg.thread_type !== '0'" type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
															<el-icon><ele-CopyDocument /></el-icon>复制
														</el-button>
														<el-button v-if="cfg.thread_type !== '0'" type="danger" size="small" text style="font-weight:600" :disabled="cfg.active || (['1','2','3'].includes(cfg.thread_type) && row.configs.filter((c: any) => c.thread_type === cfg.thread_type).length === 1)" @click="handleDeleteConfig(row, cfg)">
															<el-icon><ele-Delete /></el-icon>删除
														</el-button>
													</template>
												</td>
													</tr>
												</tbody>
											</table>
										</template>

										<!-- 自定义阶段（UltimateThreadGroup，type 3）-->
										<template v-if="row.configs.filter((c: any) => c.thread_type === '3').length > 0">
											<table class="expand-table">
												<thead>
													<tr>
                            <th style="width:60px;min-width:60px">状态</th>
                            <th class="col-name" style="width:230px;min-width:230px">线程组名称</th>
                            <th style="width:170px;min-width:170px">线程组类型</th>
                            <th style="width:100px;min-width:100px"><span class="th-label-flex"><span>阶段耗时</span><el-tooltip content="各阶段自身耗时 = 初始延迟 + 爬坡时间 + 持续时间 + 停止时间" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th style="width:100px;min-width:100px"><span class="th-label-flex"><span>阶段</span><el-tooltip content="UltimateThreadGroup 自定义阶段编号" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>线程数</span><el-tooltip content="start_threads：该阶段同时运行的线程数" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>初始延迟(s)</span><el-tooltip content="initial_delay：该阶段开始前等待的延迟时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>爬坡时间(s)</span><el-tooltip content="startup_time：阶段启动到达目标线程数所用的时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>持续时间(s)</span><el-tooltip content="hold_load_for：达到目标线程后保持满载运行的时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
														<th><span class="th-label-flex"><span>停止时间(s)</span><el-tooltip content="shutdown_time：阶段结束后线程逐渐停止的时间（秒）" placement="top"><el-icon class="th-tip-icon"><ele-QuestionFilled /></el-icon></el-tooltip></span></th>
											<th style="width:260px;min-width:260px">操作</th>
													</tr>
												</thead>
												<tbody>
														<!-- 每行独立完整：cfg 级字段每行重复显示，stage 字段每行不同 -->
														<!-- 注意：所有行的开关都绑同一个 cfg.active（后端 stage 无独立 active 字段），切换会同步 -->
														<template v-for="cfg in row.configs.filter((c: any) => c.thread_type === '3')">
															<tr
																v-for="(stage, sIdx) in (cfg.ultimate_rows?.length ? cfg.ultimate_rows : [{}])"
																:key="`${cfg.id}-${sIdx}`"
															>
																<td>
																	<el-switch v-model="cfg.active" :disabled="cfg.thread_type === '0' || row.status === 'running' || row.status === 'completed'" @change="handleConfigActiveChange(row, cfg)" />
																</td>
																<td>
																	<el-tooltip :content="cfg.tg_name || '--'" placement="top" :show-after="400">
																		<span class="expand-text-clip">{{ cfg.tg_name || '--' }}</span>
																	</el-tooltip>
																</td>
																<td>
																	<span class="tg-type-tag" :class="cfg.thread_type ? `tg-type-tag--${cfg.thread_type}` : ''">
																		{{ getThreadTypeLabel(cfg.thread_type) || '--' }}
																	</span>
																</td>
										<td>
											{{ formatDuration((stage.initial_delay || 0) + (stage.startup_time || 0) + (stage.hold_load_for || 0) + (stage.shutdown_time || 0)) || '--' }}
										</td>
																<!-- stage 字段：每行不同 -->
																<td>{{ cfg.ultimate_rows?.length ? `阶段${sIdx + 1}` : '--' }}</td>
																<td>{{ stage.start_threads ?? '--' }}</td>
																<td>{{ stage.initial_delay ?? '--' }}</td>
																<td>{{ stage.startup_time ?? '--' }}</td>
																<td>{{ stage.hold_load_for ?? '--' }}</td>
																<td>{{ stage.shutdown_time ?? '--' }}</td>
																<td>
																	<template v-if="row.status === 'running'">
																		<template v-if="cfg.active">
																			<el-button type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
																				<el-icon><ele-CopyDocument /></el-icon>复制
																			</el-button>
																		</template>
																		<template v-else>
																			<el-button type="primary" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-edit', { row, cfg })">
																				<el-icon><ele-Edit /></el-icon>修改
																			</el-button>
																			<el-button type="danger" size="small" text style="font-weight:600" :disabled="(cfg.ultimate_rows?.length || 0) <= 1" @click="handleDeleteUltimateStage(row, cfg, sIdx)">
																				<el-icon><ele-Delete /></el-icon>删除
																			</el-button>
																		</template>
																	</template>
																	<template v-else-if="row.status === 'completed'">
																	</template>
																	<template v-else>
																		<el-button type="primary" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-edit', { row, cfg })">
																			<el-icon><ele-Edit /></el-icon>修改
																		</el-button>
																		<el-button v-if="cfg.thread_type !== '0' && cfg.thread_type !== '3'" type="success" size="small" text style="font-weight:600" @click="addUpdateRef?.open('config-copy', { row, cfg })">
																			<el-icon><ele-CopyDocument /></el-icon>复制
																		</el-button>
																		<el-button type="danger" size="small" text style="font-weight:600" :disabled="(cfg.ultimate_rows?.length || 0) <= 1" @click="handleDeleteUltimateStage(row, cfg, sIdx)">
																			<el-icon><ele-Delete /></el-icon>删除
																		</el-button>
																	</template>
																</td>
															</tr>
														</template>
													</tbody>
											</table>
										</template>
									</template>
								</div>
							</template>
						</el-table-column>
						<el-table-column prop="name" label="场景名称" min-width="150" show-overflow-tooltip fixed="left" header-align="center" />

						<!-- 中间可滚动列 -->
						<el-table-column prop="scene_no" label="场景编号" width="100" align="center" show-overflow-tooltip />
						<el-table-column label="场景脚本" min-width="170" show-overflow-tooltip header-align="center">
							<template #default="{ row }">
								<span class="script-link" @click="handleGotoFiles(row)">{{ row.script_name }}</span>
							</template>
						</el-table-column>
						<el-table-column label="测试类型" width="100" align="center">
							<template #default="{ row }">
								<el-tag v-if="row.test_type" :type="testTypeTagType(row.test_type)" size="small" effect="light">
									{{ testTypeLabel(row.test_type) }}
								</el-tag>
								<span v-else class="text-placeholder">--</span>
							</template>
						</el-table-column>
						<el-table-column label="是否分布式" width="85" align="center">
						<template #default="{ row }">
							<el-tag :type="row.is_distributed ? 'primary' : 'info'" size="small" effect="light">
								{{ row.is_distributed ? '是' : '否' }}
							</el-tag>
						</template>
					</el-table-column>
					<el-table-column label="节点数量" width="75" align="center">
						<template #default="{ row }">
							{{ row.is_distributed ? row.node_count : 1 }}
						</template>
					</el-table-column>
					<el-table-column label="并发数" width="80" align="center">
							<template #header>
								<span>并发数</span>
								<el-tooltip content="启用的 Stepping / Ultimate 子配置 线程数 × Worker 数（非分布式 Worker=1），多个累加" placement="top">
									<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
							<template #default="{ row }">
								{{ displayConcurrentCount(row) }}
							</template>
						</el-table-column>
						<el-table-column label="状态" width="80" align="center">
							<template #default="{ row }">
								<el-tag :type="statusTagType(row.status)" size="small" :effect="row.status === 'running' ? 'dark' : 'light'">
									{{ statusLabel(row.status) }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column label="压测进度" width="170" align="center">
							<template #default="{ row }">
								<div class="progress-cell">
									<el-progress
										:percentage="liveProgress(row)"
										:color="progressColor(row.status)"
										:show-text="false"
										:stroke-width="8"
										class="progress-bar"
									/>
									<span class="progress-suffix" :style="{ color: progressColor(row.status) }">
										<template v-if="row.status === 'completed'">
											<el-icon style="font-size:15px;font-weight:700"><ele-CircleCheck /></el-icon>
										</template>
										<template v-else-if="row.status === 'failed'">
											<el-icon style="font-size:15px;font-weight:700"><ele-CircleClose /></el-icon>
										</template>
										<template v-else>{{ liveProgress(row) }}%</template>
									</span>
								</div>
							</template>
						</el-table-column>
						<el-table-column align="center" width="120">
							<template #header>
								<span>预计总耗时</span>
								<el-tooltip content="总耗时 = 各启用子配置预计耗时之和；使用循环次数控制时 ramp-up + 延迟为已知部分，循环次数耗时无法自动解析，以 ！标识。" placement="top">
									<el-icon style="margin-left:3px;cursor:pointer"><ele-QuestionFilled /></el-icon>
								</el-tooltip>
							</template>
							<template #default="{ row }">
								<span v-if="row.has_unknown_times" style="cursor:default;display:inline-flex;align-items:center;gap:4px">
									<el-icon :size="15" color="var(--el-color-danger)"><ele-WarningFilled /></el-icon>
									<span style="color:var(--el-color-danger)">
										<template v-if="row.known_times != null && row.known_times > 0">{{ formatDuration(row.known_times) }}</template>
										<template v-else>?</template>
									</span>
								</span>
								<span v-else>{{ formatDuration(row.known_times ?? row.estimated_duration) || '--' }}</span>
							</template>
						</el-table-column>
            <el-table-column label="运行环境" width="90" align="center">
							<template #default="{ row }">
								<el-tag :type="envTagType(row.env)" size="small" effect="light">{{ envLabel(row.env) }}</el-tag>
							</template>
						</el-table-column>
						<el-table-column prop="created_at" label="创建时间" width="160" align="center">
							<template #default="{ row }"><span style="white-space: nowrap">{{ formatDateTime(row.created_at) }}</span></template>
						</el-table-column>
						<el-table-column label="执行时间" width="160" align="center">
							<template #default="{ row }">
								<span v-if="row.started_at" style="white-space: nowrap">{{ formatDateTime(row.started_at) }}</span>
								<span v-else class="text-placeholder">--</span>
							</template>
						</el-table-column>
						<el-table-column label="错误信息" min-width="150" show-overflow-tooltip header-align="center">
							<template #default="{ row }">
								<span v-if="row.error_msg" class="error-text">{{ row.error_msg }}</span>
								<span v-else class="text-placeholder">--</span>
							</template>
						</el-table-column>
						<el-table-column label="备注" min-width="120" show-overflow-tooltip header-align="center">
						<template #default="{ row }">
							<span v-if="row.remark">{{ row.remark }}</span>
							<span v-else class="text-placeholder">--</span>
						</template>
					</el-table-column>
					<el-table-column prop="created_by" label="创建人" width="80" align="center" />

						<!-- 右固定：操作 -->
						<el-table-column label="操作" width="260" fixed="right" align="center" class-name="operation-col">
							<template #default="{ row }">
								<div class="action-btns">
									<!-- 进行中：立即停止 + 复制 -->
									<template v-if="row.status === 'running'">
										<el-button type="danger" size="small" text @click="handleStopTask(row)">
											<el-icon><ele-VideoPause /></el-icon>立即停止
										</el-button>
										<el-button type="info" size="small" text @click="addUpdateRef?.open('copy', { row })">
											<el-icon><ele-CopyDocument /></el-icon>复制
										</el-button>
									</template>

										<!-- 失败 / 已取消：恢复 + 复制 + 修改 + 删除 -->
									<template v-else-if="row.status === 'failed' || row.status === 'cancelled'">
										<el-button type="warning" size="small" text @click="handleRecover(row)">
											<el-icon><ele-RefreshRight /></el-icon>恢复
										</el-button>
										<el-button type="info" size="small" text @click="addUpdateRef?.open('copy', { row })">
											<el-icon><ele-CopyDocument /></el-icon>复制
										</el-button>
										<el-button type="primary" size="small" text @click="addUpdateRef?.open('edit', { row })">
											<el-icon><ele-Edit /></el-icon>修改
										</el-button>
										<el-button type="danger" size="small" text @click="handleDelete(row)">
											<el-icon><ele-Delete /></el-icon>删除
										</el-button>
									</template>

									<!-- 已完成：查看报告 + 复制 -->
									<template v-else-if="row.status === 'completed'">
										<el-button type="info" size="small" text @click="addUpdateRef?.open('copy', { row })">
											<el-icon><ele-CopyDocument /></el-icon>复制
										</el-button>
                    <el-button type="success" size="small" text @click="handleViewReport(row)">
											<el-icon><ele-DataLine /></el-icon>查看报告
										</el-button>
									</template>

									<!-- 待开始 / 其他状态（待联调等）：复制 + 修改 + 删除 -->
									<template v-else>
										<el-button type="info" size="small" text @click="addUpdateRef?.open('copy', { row })">
											<el-icon><ele-CopyDocument /></el-icon>复制
										</el-button>
										<el-button type="primary" size="small" text @click="addUpdateRef?.open('edit', { row })">
											<el-icon><ele-Edit /></el-icon>修改
										</el-button>
										<el-button type="danger" size="small" text @click="handleDelete(row)">
											<el-icon><ele-Delete /></el-icon>删除
										</el-button>
									</template>
								</div>
							</template>
						</el-table-column>
					</el-table>

					<!-- 分页 -->
					<el-pagination
						v-show="total > 0"
						v-model:current-page="query.page"
						v-model:page-size="query.page_size"
						:page-sizes="[10, 20, 50]"
						:total="total"
						layout="total, sizes, prev, pager, next, jumper"
						class="pagination"
						@size-change="handleQuery"
						@current-change="handleQuery"
					/>
				</el-tab-pane>

				<!-- Tab 2: 压测实时监控 -->
				<el-tab-pane label="压测实时监控" name="console">
					<SceneMonitor
						ref="monitorRef"
						:scene="monitorScene"
						:exec-state="execState"
						@exec-done="execState = null"
						@force-stop="handleForceStop"
					/>
				</el-tab-pane>

			</el-tabs>
		</el-card>

		<!-- 脚本联调抽屉 -->
		<SceneDebug
			v-model="debugDrawerVisible"
			:scene="debugScene"
			@confirmed="handleDebugConfirm"
			@start-test="handleStartFromDebug"
		/>

		<AddUpdate ref="addUpdateRef" @success="handleAddUpdateSuccess" />
	</div>
</template>

<script setup lang="ts" name="PerformanceScenario">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import SceneDebug from './inspect.vue';
import SceneMonitor from './monitor.vue';
import AddUpdate from './addUpdate.vue';
import { normalizeConfig } from './utils';
import { usePerformanceApi } from '/@/api/v1/performance';
import { useDictCache } from '/@/utils/dictCache';

const perfApi = usePerformanceApi();
const { getDictOptions } = useDictCache();
const router = useRouter();
const route = useRoute();
const addUpdateRef = ref<InstanceType<typeof AddUpdate>>();

const handleGotoFiles = (row: any) => {
	router.push({ path: '/performance/files', query: { name: row.script_name } });
};

// ======================== 线程组类型标签 ========================
const THREAD_TYPE_LABELS: Record<string, string> = {
	'0': 'SetUp',
	'1': 'Standard',
	'2': 'Stepping',
	'3': 'Ultimate',
};
// 线程组类型字典（从 perf_thread_group_type 动态加载，用于 panel 标题展示）
const THREAD_TYPE_OPTIONS = ref<{ value: string; label: string }[]>([]);
const getThreadTypeLabel = (type: string) =>
	THREAD_TYPE_OPTIONS.value.find(o => o.value === type)?.label ?? THREAD_TYPE_LABELS[type] ?? type;

// ======================== 常量 ========================
// 运行环境和测试类型在 onMounted 中从字典表动态加载
const ENV_OPTIONS = ref<{ value: string; label: string }[]>([]);

const TEST_TYPE_OPTIONS = ref<{ value: string; label: string; tagType: string; desc: string }[]>([]);

// 状态整数 ↔ 字符串（后端 0-5 ↔ 前端 string）
const STATUS_INT_TO_STR: Record<number, string> = { 0: 'debug', 1: 'pending', 2: 'running', 3: 'completed', 4: 'cancelled', 5: 'failed' };
const STATUS_STR_TO_INT: Record<string, number> = { debug: 0, pending: 1, running: 2, completed: 3, cancelled: 4, failed: 5 };

const testTypeLabel = (v: string) => TEST_TYPE_OPTIONS.value.find(t => t.value === v)?.label ?? '--';

// 按选项顺序循环分配颜色；字典配置了 list_class 时优先使用
const TAG_COLOR_CYCLE = ['', 'success', 'warning', 'danger', 'info'] as const;
const testTypeTagType = (v: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
	const opt = TEST_TYPE_OPTIONS.value.find(t => t.value === v);
	if (opt?.tagType) return opt.tagType as any;
	const idx = TEST_TYPE_OPTIONS.value.findIndex(t => t.value === v);
	return TAG_COLOR_CYCLE[idx % TAG_COLOR_CYCLE.length];
};

// ======================== 工具函数 ========================
const formatDateTime = (val: string) => {
	if (!val) return '--';
	return val.replace('T', ' ').substring(0, 19);
};

const formatDuration = (seconds: number) => {
	if (!seconds) return '--';
	if (seconds < 60) return `${seconds}s`;
	if (seconds < 3600) {
		const m = Math.floor(seconds / 60);
		const s = seconds % 60;
		return s > 0 ? `${m}m ${s}s` : `${m}m`;
	}
	if (seconds < 86400) {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		return m > 0 ? `${h}h ${m}m` : `${h}h`;
	}
	const d = Math.floor(seconds / 86400);
	const h = Math.floor((seconds % 86400) / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	let result = `${d}天`;
	if (h > 0) result += ` ${h}h`;
	if (m > 0) result += ` ${m}m`;
	return result;
};

const envLabel = (env: string) => ENV_OPTIONS.value.find(o => o.value === env)?.label ?? env;

const envTagType = (env: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
	const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
		dev: '', test: 'warning', perf: 'danger', staging: 'info', prod: 'success',
	};
	return map[env] ?? '';
};

const statusLabel = (status: string) => {
	const map: Record<string, string> = {
		debug: '待联调', pending: '待开始', running: '进行中', completed: '已完成', cancelled: '已取消', failed: '失败',
	};
	return map[status] ?? status;
};

const statusTagType = (status: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
	const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
		debug: '', pending: 'warning', running: '', completed: 'success', cancelled: 'info', failed: 'danger',
	};
	return map[status] ?? '';
};

const progressColor = (status: string) => {
	const map: Record<string, string> = {
		running: '#409eff', completed: '#67c23a', failed: '#f56c6c', cancelled: '#909399',
	};
	return map[status] ?? '#409eff';
};

// 秒级时钟：每秒更新，驱动 running 行实时计算进度，与监控界面保持一致
const nowMs = ref(Date.now());
let _nowTimer: ReturnType<typeof setInterval> | null = null;

// running 时：当前监控场景直接用 SSE 已写入的 row.progress（与监控界面完全同步）；
// 其他 running 行（理论上不存在，兜底）才用客户端时钟估算
const liveProgress = (row: any): number => {
	// Stage 1/2 执行期间（execState 存在且 monitorScene 是当前行）：直接用 execState.progress 显示阶段进度
	if (execState.value && monitorScene.value?.id === row.id) {
		return execState.value.progress ?? 0;
	}
	if (row.status !== 'running') return row.progress ?? 0;
	// monitor SSE 通过 props.scene.progress = evt.value 实时回写到 row（共享对象引用），直接使用
	if (monitorScene.value?.id === row.id) return row.progress ?? 0;
	if (!row.estimated_duration || !row.started_at) return row.progress ?? 0;
	const elapsed = (nowMs.value - new Date(row.started_at).getTime()) / 1000;
	return Math.min(99, Math.floor(elapsed / row.estimated_duration * 100));
};

// ======================== 数据归一化 ========================

// 后端场景字段 → 前端字段
function normalizeScenario(raw: any): any {
	return {
		id: raw.id,
		scene_no: raw.code,
		name: raw.name,
		script_id: raw.script_id,
		script_name: raw.script_name,
		test_type: raw.test_type,
		// 并发数：后端 list 接口实时聚合返回（启用的 Stepping/Ultimate 子配置 thread_count × workers 累加）
		concurrent_count: raw.concurrent_count ?? 0,
		is_distributed: raw.is_distributed === 1,
		node_count: raw.node_count ?? 1,
		env: raw.run_env,
		status: STATUS_INT_TO_STR[raw.status as number] ?? 'pending',
		progress: raw.progress ?? 0,
		estimated_duration: raw.estimated_duration,
		has_unknown_times: raw.has_unknown_times ?? false,
		known_times: (raw.known_times ?? null) as number | null,
		started_at: raw.executed_at,
		error_msg: raw.error_info,
		remark: raw.remark,
		created_at: raw.creation_date,
		created_by: raw.operator_name ?? String(raw.created_by ?? ''),
		configs: [] as any[],
		_configsLoaded: false,
	};
}


// 互斥类型（标准/Stepping/Ultimate）必须至少有 1 条启用：若全部 inactive 则前端自动置首条为 active
// 用于 normalizeConfig 后兜底（应对数据库存在多条 status=0 的互斥配置场景）
function ensureExclusiveActive(): void {
	// '1'/'2'/'3' 类型均可多个同时启用，无需互斥处理
	// '0'(SetUp/TearDown) 开关禁用，不经此函数处理
}
// 查询栏下拉数据源：从已加载的场景列表提取去重脚本名，只列出当前已在用的脚本
const queryScriptOptions = computed<{ id: number; name: string }[]>(() => {
	const seen = new Set<number>();
	const result: { id: number; name: string }[] = [];
	for (const s of sceneList.value) {
		if (s.script_id && !seen.has(s.script_id)) {
			seen.add(s.script_id);
			result.push({ id: s.script_id, name: s.script_name });
		}
	}
	return result;
});

// ======================== 列表 ========================
const activeTab = ref('list');
const loading = ref(false);
const tableRef = ref();
const sceneList = ref<any[]>([]);
const total = ref(0);
const selectedRows = ref<any[]>([]);

const query = reactive({
	name: '',
	code: '',
	script_name: undefined as string | undefined,
	status: undefined as string | undefined,
	test_type: undefined as string | undefined,
	created_by: '',
	page: 1,
	page_size: 20,
});

const hasRunningTask = computed(() => sceneList.value.some(r => r.status === 'running'));

const handleQuery = async () => {
	loading.value = true;
	try {
		const params: any = { page: query.page, page_size: query.page_size };
		if (query.name)        params.name        = query.name;
		if (query.code)        params.code        = query.code;
		if (query.script_name) params.script_name = query.script_name;
		if (query.status)      params.status      = STATUS_STR_TO_INT[query.status];
		if (query.test_type)   params.test_type   = query.test_type;
		if (query.created_by)  params.created_by  = query.created_by;

		const res: any = await perfApi.getScenarioList(params);
		if (res.code === 200) {
			total.value = res.data.total;
			sceneList.value = (res.data.items ?? []).map(normalizeScenario);
			// 重新绑定 monitorScene 引用，防止列表刷新后引用断裂导致进度条不同步
			if (monitorScene.value) {
				const fresh = sceneList.value.find((r: any) => r.id === monitorScene.value.id);
				if (fresh) {
					// DB 仍在进行中：保留 SSE 实时进度，防止列表刷新覆盖
					// DB 已是终态（完成/取消/失败）：以 DB 值为准，不用旧 SSE 状态覆盖
					if (fresh.status === 'running') {
						fresh.progress = monitorScene.value.progress;
						fresh.status   = monitorScene.value.status;
					}
					monitorScene.value = fresh;
				}
			}
		}
	} catch (_) {
		ElMessage.error('获取场景列表失败');
	} finally {
		loading.value = false;
	}
};

const resetQuery = () => {
	query.name        = '';
	query.code        = '';
	query.script_name = undefined;
	query.status      = undefined;
	query.test_type   = undefined;
	query.created_by  = '';
	query.page        = 1;
	handleQuery();
};

const handleSelectionChange = (rows: any[]) => {
	if (rows.length > 1) {
		const latest = rows[rows.length - 1];
		rows.slice(0, -1).forEach(r => tableRef.value?.toggleRowSelection(r, false));
		selectedRows.value = [latest];
	} else {
		selectedRows.value = rows;
	}
};

// ======================== 展开行懒加载子配置 ========================
// 手风琴模式：记录当前已展开的行 id，展开新行时自动折叠旧行
const expandedRowId = ref<any>(null);

const handleExpandChange = async (row: any, expandedRows: any[]) => {
	// element-plus 的 expand-change 事件第二个参数是当前所有展开行数组（非 boolean）
	// 通过查 expandedRows 是否含本 row 判断当前是展开还是折叠
	const expanded = Array.isArray(expandedRows) && expandedRows.some((r: any) => r.id === row.id);

	// 手风琴：折叠上一个展开行
	if (expanded && expandedRowId.value !== null && expandedRowId.value !== row.id) {
		const prevRow = sceneList.value.find((r: any) => r.id === expandedRowId.value);
		if (prevRow) tableRef.value?.toggleRowExpansion(prevRow, false);
	}
	expandedRowId.value = expanded ? row.id : null;

	// 折叠时不调接口；展开时总是重新拉取最新子配置（不依赖 _configsLoaded 缓存）
	if (!expanded) return;
	try {
		const res: any = await perfApi.getScenarioConfigList(row.id);
		if (res.code === 200) {
			row.configs = (res.data ?? []).map(normalizeConfig);
			ensureExclusiveActive();
			row._configsLoaded = true;
			// 展开后实时计算总并发数（场景级别分布式 × 各启用子配置线程数之和）
			const workers = row.is_distributed ? (row.node_count ?? 1) : 1;
			const activeCfgs = row.configs.filter((c: any) => c.active && ['1', '2', '3'].includes(c.thread_type));
			row.concurrent_count = activeCfgs.reduce((sum: number, c: any) => {
				const t = c.thread_type === '3'
					? (c.ultimate_rows ?? []).reduce((s: number, r: any) => s + (r.start_threads ?? 0), 0)
					: (c.threads ?? 0);
				return sum + t * workers;
			}, 0);
		}
	} catch (_) {
		ElMessage.error('加载子配置失败');
	}
};

// ======================== 刷新状态 ========================
const statusRefreshing = ref(false);

const handleRefreshStatus = async () => {
	statusRefreshing.value = true;
	try {
		const prevExpandedId = expandedRowId.value;
		await handleQuery();
		// 刷新后补回展开行子配置（el-table 凭 row-key 保留展开状态，但新行对象没有 configs）
		if (prevExpandedId !== null) {
			const expandedRow = sceneList.value.find((r: any) => r.id === prevExpandedId);
			if (expandedRow) {
				try {
					const res: any = await perfApi.getScenarioConfigList(prevExpandedId);
					if (res.code === 200) {
						expandedRow.configs = (res.data ?? []).map(normalizeConfig);
						expandedRow._configsLoaded = true;
					}
				} catch (_) { /* ignore */ }
			}
		}
		ElMessage.success('执行状态已刷新');
	} finally {
		statusRefreshing.value = false;
	}
};

// ======================== 脚本联调 ========================
const debugDrawerVisible = ref(false);
const debugScene = ref<any>(null);

const handleDebug = () => {
	const row = selectedRows.value[0];
	if (!row) return;
	debugScene.value = row;
	debugDrawerVisible.value = true;
};

const handleDebugConfirm = (scene: any) => {
	const row = sceneList.value.find((r: any) => r.id === scene.id);
	if (row) row.status = 'pending';
};

const handleStartFromDebug = (scene: any) => {
	handleStartRow(scene);
};

// ======================== 启动 / 停止 ========================
const handleStartSelected = () => {
	if (selectedRows.value.length !== 1) return;
	handleStartRow(selectedRows.value[0]);
};

const handleStartRow = (row: any) => {
	if (hasRunningTask.value) {
		ElMessage.warning('当前已有压测任务正在运行，请等待完成或停止后再启动');
		return;
	}
	if (row.has_unknown_times) {
		ElMessage.warning('当前场景含有循环次数控制的线程组，无法精确预估压测总耗时，请先在子配置中设置自定义压测时间');
		return;
	}
	_runExecSSE(row, 'execute');
};

// 通用 SSE 执行流程：联调（action=inspect）和正式执行（action=execute）均在监控 Tab 内显示进度
const INSPECT_STAGE_LABELS = ['注入参数', '上传脚本', '执行联调'];
const EXECUTE_STAGE_LABELS = ['注入参数', '上传脚本', '启动进程'];
const RECOVER_STAGE_LABELS = ['恢复启动进程'];

const _runExecSSE = async (row: any, action: 'inspect' | 'execute' | 'recover') => {
	// execute/recover 点击即时更新状态为运行中，让列表 badge 立即响应，出错时回滚
	const originalStatus = row.status;
	if (action === 'execute' || action === 'recover') {
		row.status = 'running';
	}

	const stageLabels = action === 'inspect' ? INSPECT_STAGE_LABELS
	                  : action === 'recover'  ? RECOVER_STAGE_LABELS
	                  : EXECUTE_STAGE_LABELS;
	execState.value = {
		stages: stageLabels.map((label, i) => ({ label, done: false, active: i === 0 })),
		progress: 0,
	};
	monitorScene.value = row;
	// 切换到监控 Tab 前清空历史日志，避免新旧日志混合
	monitorRef.value?.clearLogs();
	activeTab.value = 'console';

	let actionDone = false;
	let actionError = '';

	try {
		const resp = await perfApi.executeScenarioStream(row.id, { action });
		if (!resp.ok || !resp.body) {
			const msg = `请求失败（HTTP ${resp.status}）`;
			monitorRef.value?.addExternalLog(msg, 'error');
			execState.value = null;
			return;
		}
		const reader = resp.body.getReader();
		const decoder = new TextDecoder();
		let buffer = '';

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
					if (evt.type === 'stage_start') {
						// 后端 stage 字段为 1-indexed，转换为 0-indexed 数组下标
						const stageIdx = (evt.stage ?? 1) - 1;
						const stages = execState.value!.stages;
						stages.forEach((s, i) => {
							s.done   = i < stageIdx;
							s.active = i === stageIdx;
						});
						// 前置阶段（非最后）各占 3%；最后阶段由 Monitor SSE 填充，此处保持在 preWeight
						const preWeight = Math.max(0, (stages.length - 1) * 3);
						execState.value!.progress = Math.min(stageIdx * 3, preWeight);
						if (evt.message) monitorRef.value?.addExternalLog(evt.message);
					} else if (evt.type === 'stage_done') {
						const stageIdx = (evt.stage ?? 1) - 1;
						const stages = execState.value!.stages;
						const isLastStage = stageIdx === stages.length - 1;
						if (isLastStage && (action === 'execute' || action === 'recover')) {
							// JMeter 已后台启动：标记当前阶段 active，进度由 Monitor SSE 持续更新
							stages.forEach((s, i) => { s.done = i < stageIdx; s.active = i === stageIdx; });
							// 进程启动完成，立即开放强制停止按钮
							row.status = 'running';
						} else {
							stages.forEach((s, i) => {
								s.done   = i <= stageIdx;
								s.active = i === stageIdx + 1 && stageIdx + 1 < stages.length;
							});
							// 非最后阶段：3% 递增；inspect 最后阶段：100%
							execState.value!.progress = isLastStage ? 100 : (stageIdx + 1) * 3;
						}
						if (evt.message) monitorRef.value?.addExternalLog(evt.message);
					} else if (evt.type === 'log') {
						monitorRef.value?.addExternalLog(evt.message ?? '');
					} else if (evt.type === 'done') {
						actionDone = true;
						if (action === 'inspect') {
							// 联调完成：全部阶段打勾，进度 100%
							execState.value!.stages.forEach(s => { s.done = true; s.active = false; });
							execState.value!.progress = 100;
						}
						// execute/recover：execState 保持 Stage 3 active，由 Monitor SSE 继续更新
						monitorRef.value?.addExternalLog(
							evt.message || (action === 'inspect' ? '联调完成' : '压测已启动'), 'success');
					} else if (evt.type === 'error') {
						actionError = evt.message ?? (action === 'inspect' ? '联调失败' : '执行失败');
						monitorRef.value?.addExternalLog(actionError, 'error');
					}
				} catch { /* 忽略单行 JSON 解析异常 */ }
			}
		}
	} catch (e: any) {
		actionError = String(e?.message ?? e ?? (action === 'inspect' ? '联调失败' : '执行失败'));
		monitorRef.value?.addExternalLog(actionError, 'error');
	}

	if (actionDone && !actionError) {
		if (action === 'inspect') {
			row.status = 'pending';
			ElMessage.success('联调完成！场景已就绪，可以启动正式压测');
			setTimeout(() => { execState.value = null; }, 3000);
		} else {
			// execute / recover 均进入运行中状态，启动实时监控
			// consoleLogs 不会被清空，继续追加 execute SSE 阶段写入的启动命令、PID 等日志
			row.status = 'running';
			monitorScene.value = row;
			monitorRef.value?.startMonitor(row.id, 0);
			// execState 保持显示（Stage 最后阶段 active），由 monitor @exec-done 清除
		}
	} else if (actionError) {
		// 出错时回滚 status 并延迟清除 execState
		if (action === 'execute' || action === 'recover') row.status = originalStatus;
		setTimeout(() => { execState.value = null; }, 5000);
	}
	if (actionError && action === 'inspect') {
		ElMessage.error(actionError);
	}
};

const handleStopTask = (row: any) => {
	const sceneId = row.id;
	const sceneName = row.name;
	ElMessageBox.confirm(
		`确认立即停止「${sceneName}」的压测任务？停止后场景状态将变为【已取消】。`,
		'立即停止',
		{ type: 'warning', confirmButtonText: '立即停止', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
	).then(async () => {
		try {
			await perfApi.stopScenario(sceneId);
			// API 等待期间列表可能已刷新，重新按 ID 查找避免更新到旧引用
			const freshRow = sceneList.value.find((r: any) => r.id === sceneId);
			if (freshRow) freshRow.status = 'cancelled';
			if (monitorScene.value?.id === sceneId) monitorScene.value.status = 'cancelled';
			ElMessage.success('压测任务已停止');
		} catch (e: any) {
			ElMessage.error(e?.response?.data?.detail || '停止失败');
		}
	}).catch(() => {});
};

const handleForceStop = async (sceneId: number) => {
	try {
		await perfApi.stopScenario(sceneId);
		// API 等待期间列表可能已刷新，直接同时更新 sceneList 和 monitorScene 避免竞态
		const freshRow = sceneList.value.find((r: any) => r.id === sceneId);
		if (freshRow) freshRow.status = 'cancelled';
		if (monitorScene.value?.id === sceneId) monitorScene.value.status = 'cancelled';
		ElMessage.success('压测任务已停止');
	} catch (e: any) {
		ElMessage.error(e?.response?.data?.detail || '停止失败');
	}
};

// ======================== 查看报告 ========================
const handleViewReport = (row?: any) => {
	if (row) {
		router.push({ path: '/performance/report', query: { scene_no: row.scene_no } });
	} else {
		router.push({ path: '/performance/report' });
	}
};

// ======================== 恢复执行 ========================
const handleRecover = (row: any) => {
	if (hasRunningTask.value) {
		ElMessage.warning('当前已有压测任务正在运行，无法恢复执行');
		return;
	}
	_runExecSSE(row, 'recover');
};

// ======================== 删除 ========================
const handleDelete = (row: any) => {
	if (row.status === 'running') {
		ElMessage.warning('压测任务进行中，不支持删除');
		return;
	}
	ElMessageBox.confirm(
		`确认删除压测场景「${row.name}」？`,
		'删除确认',
		{ type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
	).then(async () => {
		try {
			await perfApi.deleteScenario(row.id);
			ElMessage.success('删除成功');
			handleQuery();
		} catch (e: any) {
			ElMessage.error(e?.response?.data?.detail || '删除失败');
		}
	}).catch(() => {});
};

// ======================== 监控 Tab ========================
const monitorScene = ref<any>(null);
const monitorRef = ref<any>(null);

// 联调阶段进度条状态（inspect action 使用，替代弹窗）
const execState = ref<{
	stages: { label: string; done: boolean; active: boolean }[];
	progress: number;
} | null>(null);

// 新增/修改/复制场景或子配置成功后的回调：full 模式刷新父列表，config 模式局部刷新对应行
const handleAddUpdateSuccess = async ({ mode, row }: any) => {
	if (['add', 'edit', 'copy'].includes(mode)) {
		// 记录刷新前已展开的行 id，刷新后补回子配置数据（el-table 凭 row-key 保留展开状态，但新行对象没有 configs）
		const prevExpandedId = expandedRowId.value;
		await handleQuery();
		if (prevExpandedId !== null) {
			const expandedRow = sceneList.value.find((r: any) => r.id === prevExpandedId);
			if (expandedRow) {
				try {
					const res: any = await perfApi.getScenarioConfigList(prevExpandedId);
					if (res.code === 200) {
						expandedRow.configs = (res.data ?? []).map(normalizeConfig);
						expandedRow._configsLoaded = true;
					}
				} catch (_) { /* ignore */ }
			}
		}
	} else if (row) {
		const res: any = await perfApi.getScenarioConfigList(row.id);
		if (res.code === 200) {
			row.configs = (res.data ?? []).map(normalizeConfig);
			await refreshRowEstimatedDuration(row);
		}
	}
};

// 子列表"删除"：仅禁用状态的配置可删除，确保始终至少有一条启用配置
const handleDeleteConfig = async (row: any, cfg: any) => {
	ElMessageBox.confirm(
		'确认删除该压测配置？',
		'删除确认',
		{ type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
	).then(async () => {
		try {
			await perfApi.deleteScenarioConfig(row.id, cfg.id);
			row.configs = row.configs.filter((c: any) => c.id !== cfg.id);
			ElMessage.success('配置已删除');
		} catch (_) {
			ElMessage.error('删除失败');
		}
	}).catch(() => {});
};

// 子列表 Ultimate 类型行的"删除"：仅删除该行对应的 stage（不是整个 cfg），调用 updateScenarioConfig 同步
// 至少保留 1 条 stage（按钮在 ultimate_rows.length<=1 时已 disabled）
const handleDeleteUltimateStage = async (row: any, cfg: any, sIdx: number) => {
	if (!cfg?.ultimate_rows || cfg.ultimate_rows.length <= 1) {
		ElMessage.warning('至少保留一条阶段配置');
		return;
	}
	ElMessageBox.confirm(
		`确认删除该配置的「阶段${sIdx + 1}」？`,
		'删除确认',
		{ type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消', confirmButtonClass: 'el-button--danger' }
	).then(async () => {
		const newRows = cfg.ultimate_rows.filter((_: any, i: number) => i !== sIdx);
		try {
			// 调 updateScenarioConfig 把新的 ultimate_rows 提交后端
			await perfApi.updateScenarioConfig(row.id, cfg.id, {
				thread_type: cfg.thread_type,
				ultimate_rows: newRows,
			});
			// 拉取最新配置同步到 row.configs
			const cfgRes: any = await perfApi.getScenarioConfigList(row.id);
			if (cfgRes.code === 200) {
				row.configs = (cfgRes.data ?? []).map(normalizeConfig);
				ensureExclusiveActive();
				row._configsLoaded = true;
			}
			ElMessage.success('阶段已删除');
		} catch (_) {
			ElMessage.error('删除失败');
		}
	}).catch(() => {});
};

// 主表"并发数"列实时计算：仅累加启用的 Stepping(type=2)/Ultimate(type=3) 子配置的 线程数 × Worker 数（非分布式 Worker=1）
// configs 未加载时（行未展开过）回退到数据库 row.concurrent_count 兜底显示
const displayConcurrentCount = (row: any): string | number => {
	if (!row?._configsLoaded || !row.configs?.length) {
		return row?.concurrent_count || '--';
	}
	// 累加启用(status=1)的 ThreadGroup('1')/Stepping('2')/Ultimate('3') 子配置；SetUp/TearDown('0') 不计入
	const active = row.configs.filter((c: any) => c.active && ['1', '2', '3'].includes(c.thread_type));
	if (!active.length) return '--';
	const workers = row.is_distributed ? (row.node_count ?? 1) : 1;
	const total = active.reduce((sum: number, c: any) => {
		const cfgThreads = c.thread_type === '3'
			? (c.ultimate_rows ?? []).reduce((s: number, r: any) => s + (r.start_threads ?? 0), 0)
			: (c.threads ?? 0);
		return sum + cfgThreads * workers;
	}, 0);
	return total || '--';
};

// 状态开关：通过 sync_stats 接口一次完成「状态更新 + 互斥处理 + 并发数 + 预计耗时」同步
const handleConfigActiveChange = async (row: any, activated: any) => {
	// SetUp/TearDown('0') 开关在模板层已禁用，此处作为安全兜底
	if (activated.thread_type === '0') return;

	// 至少保留一条启用（前端保护）
	if (!activated.active && !row.configs.some((c: any) => c !== activated && c.active)) {
		ElMessage.warning('子列表必须保留至少一条开启状态的配置');
		activated.active = true;
		return;
	}

	const prevActive = activated.active;
	try {
		const res: any = await perfApi.syncScenarioStats({
			scenario_id: row.id,
			config_id: activated.id,
			status: activated.active ? 1 : 0,
			thread_type: activated.thread_type ?? '1',
		});
		if (res.code === 200) {
			// 后端只返回启用配置，在本地 configs 上同步 active 状态（不整体替换，保留禁用行）
			const activeIds = new Set((res.data.configs ?? []).map((c: any) => c.id));
			row.configs.forEach((c: any) => { c.active = activeIds.has(c.id); });
			row._configsLoaded = true;
			row.concurrent_count  = res.data.concurrent_count ?? 0;
			row.has_unknown_times = res.data.has_unknown_times ?? false;
			row.known_times       = res.data.known_times ?? null;
			if (res.data.known_times != null) {
				row.estimated_duration = res.data.known_times;
			}
		}
	} catch (_) {
		ElMessage.error('更新配置状态失败');
		activated.active = prevActive;
	}
};


// 从场景的已启用子配置汇总预计耗时，并同步更新主列表行数据和后端记录
const refreshRowEstimatedDuration = async (row: any) => {
	const activeCfgs = (row.configs ?? []).filter((c: any) => c.active);
	const total = activeCfgs.reduce((sum: number, c: any) => sum + (c.known_times ?? 0), 0);
	const hasUnknown = activeCfgs.some((c: any) => c.has_unknown_times);

	row.has_unknown_times = hasUnknown;
	row.known_times       = total > 0 ? total : null;
	if (total > 0) {
		row.estimated_duration = total;
		try { await perfApi.updateScenario(row.id, { estimated_duration: total }); } catch (_) { /* ignore */ }
	}
};

// ======================== 初始化 ========================
onMounted(async () => {
	if (route.query.scene_no) {
		query.code = route.query.scene_no as string;
	}

	// 并行加载测试类型字典、运行环境字典、线程组类型字典
	const [testTypeOpts, envOpts, tgTypeOpts] = await Promise.all([
		getDictOptions('perf_test_category').catch(() => []),
		getDictOptions('sys_env').catch(() => []),
		getDictOptions('perf_thread_group_type').catch(() => []),
	]);
	// 测试类型：desc 取字典备注（remark），tagType 取 list_class
	TEST_TYPE_OPTIONS.value = (testTypeOpts as any[]).map((o) => ({
		value: String(o.value),
		label: o.label,
		tagType: (o.raw?.list_class ?? '') as string,
		desc: o.raw?.remark ?? '',
	}));

	// 运行环境：直接取 label/value
	ENV_OPTIONS.value = (envOpts as any[]).map((o) => ({ value: String(o.value), label: o.label }));

	// 线程组类型：用于 panel 标题标签动态显示
	THREAD_TYPE_OPTIONS.value = (tgTypeOpts as any[]).map((o) => ({ value: String(o.value), label: o.label }));

	handleQuery();
	_nowTimer = setInterval(() => { nowMs.value = Date.now(); }, 1000);
});

onUnmounted(() => {
	if (_nowTimer) clearInterval(_nowTimer);
});
</script>

<style scoped lang="scss">
.perf-scene-container {
	// 外间距：上/左/右缩减一半，下保留
	padding: 10px 10px 20px 10px;

	// 卡片内间距：上/左/右缩减一半，下保留
	:deep(.el-card__body) {
		padding: 10px 10px 20px 10px;
	}

	.scene-tabs {
		:deep(.el-tabs__header) {
			margin-top: -8px;
		}
	}

	// 隐藏列表表头的全选复选框，不支持多选
	:deep(.el-table__header th.el-table-column--selection .cell) {
		display: none;
	}

	:deep(.el-button > span) {
		display: inline-flex !important;
		align-items: center !important;
		line-height: 1 !important;
	}

	:deep(.el-input__inner),
	:deep(.el-textarea__inner) {
		font-size: 13.5px;
	}

	:deep(.el-select__placeholder),
	:deep(.el-select__selected-item) {
		font-size: 13.5px;
	}

	:deep(.el-tag) {
		font-size: 13px;
		padding: 0 8px;
	}

	:deep(.el-table) {
		font-size: 13.5px;

		// 表头背景：使用 element 填充色变量，自动适配深色/浅色
		.el-table__header th {
			font-size: 13.5px;
			background-color: var(--el-fill-color-light);
		}

		// 带 ? 图标的表头：禁止折行，文字与图标水平对齐
		.el-table__header th .cell {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			white-space: nowrap;
		}

		.el-table__cell {
			padding: 11px 0;
		}

		// 操作列背景：使用 element fill-color-light 变量，浅色 #f5f7fa 明显灰，深色由 dark.scss 强制为 #303030
		td.operation-col {
			background-color: var(--el-fill-color-light) !important;
		}
	}

	.tip-icon {
		margin-left: 4px;
		color: var(--el-text-color-secondary);
		cursor: help;
		vertical-align: -2px;
		font-size: 13.5px;

		&:hover {
			color: var(--el-color-primary);
		}
	}

	// 展开行背景 — el-table__expanded-cell 自带白色 padding，需清除
	:deep(.el-table__expanded-cell) {
		padding: 0 !important;
		background-color: var(--el-fill-color-light) !important;
	}

	// 展开行详情
	.expand-detail {
		// 选择列45px，与展开列左侧对齐
		padding: 8px 0 8px 45px;
		// 父背景使用 fill-color-lighter（浅 #fafafa / 深 #252525），
		// 形成三档色阶：父表行 #fff/#191919 → .expand-detail #fafafa/#252525 → sticky 末列 #f5f7fa/#303030
		// 既能区分子列表区域，又让 sticky 末列在父背上明显突出
		background: var(--el-fill-color-lighter);
		// 注意：这里不加 overflow-x: auto。若加，会让 .expand-detail 成为新的滚动容器，
		// 导致 sticky 末列只相对 .expand-detail 固定，与父表的横向滚动失去对齐。
		// 横向滚动由外层 el-table 接管，sticky 列自然与父表操作列对齐。

		.expand-table {
			// width:100% + table-layout:fixed：
			//   - 有 inline width 的列（前 5 列、操作列）严格按设定宽度
			//   - 没设 width 的中间列吸收多余空间（均分剩余）
			//   - sum(列 widths) 超过父宽时由外层 el-table 横向滚动
			// 这样不同嵌套表的"前 5 列 + 操作列"宽度严格一致，且 sticky 末列贴父容器右
			width: 100%;
			min-width: max-content;
			table-layout: fixed;
			border-collapse: collapse;
			font-size: 13px;

			th, td {
				border: 1px solid var(--el-border-color-lighter);
				padding: 0 8px;
				height: 40px;
				box-sizing: border-box;
				vertical-align: middle;
				text-align: center;
				white-space: nowrap;
				overflow: hidden;
				text-overflow: ellipsis;
			}

			// 列宽规范（所有嵌套表的前 5 列结构相同）：通过 :nth-child 强制 width + min-width
			// 避免 table-layout: fixed 下因父容器空间不足而被压缩
			// 状态列
			th:nth-child(1),
			td:nth-child(1) { width: 52px; min-width: 52px; }
			// 线程组名称：thead 居中（继承通用 text-align: center），tbody 内容左对齐
			th:nth-child(2),
			td:nth-child(2) { width: 220px; min-width: 220px; }
			td:nth-child(2) { text-align: left; }
			// 线程组类型
			th:nth-child(3),
			td:nth-child(3) { width: 100px; min-width: 100px; }
			// 是否分布式
			th:nth-child(4),
			td:nth-child(4) { width: 80px; min-width: 80px; }
			// 节点数量
			th:nth-child(5),
			td:nth-child(5) { width: 80px; min-width: 80px; }
			// 中间动态列（第 6 列起到倒数第 2 列）：默认 min-width 100px
			th:nth-child(n+6):not(:last-child),
			td:nth-child(n+6):not(:last-child) { min-width: 100px; }

			// 名称列加宽（仅设 min-width，让 thead 继承通用居中、tbody 由 td:nth-child(2) 控左对齐）
			th.col-name { min-width: 200px; }

			// 线程组名称列：超长截断，tooltip 显示完整
			.expand-text-clip {
				display: block;
				overflow: hidden;
				text-overflow: ellipsis;
				white-space: nowrap;
				max-width: 240px;
			}

			thead th {
				color: var(--el-table-header-text-color, var(--el-text-color-secondary));
				font-weight: 600;
				font-size: 13px;
			}

			// 表头带 ? tooltip 的列：文字与 ? 图标水平居中
			.th-label-flex {
				display: inline-flex;
				align-items: center;
				gap: 4px;
				justify-content: center;
				vertical-align: middle;
			}

			.th-tip-icon {
				color: var(--el-text-color-secondary);
				cursor: help;
				font-size: 13px;

				&:hover {
					color: var(--el-color-primary);
				}
			}

			// 数据行单元格：使用 element 背景与文字色变量自动适配深色
			tbody td {
				background: var(--el-fill-color-blank);
				color: var(--el-text-color-primary);
			}

			// 相邻表格去除重复上边框
			.expand-table + .expand-table {
				thead tr:first-child th,
				thead tr:first-child td {
					border-top: none;
				}
			}

			// 最后一列（操作）锁定右侧，与父表操作列对齐
			th:last-child,
			td:last-child {
				position: sticky;
				right: 0;
				z-index: 2;
				width: 260px;
				min-width: 260px;
			}

			// sticky 末列：使用 fill-color-light 与父表操作列严格同色
			// 浅 #f5f7fa / 深 #303030（dark.scss 重写）
			// 注意：必须是 fill-color-light，不能是 fill-color-lighter（lighter 浅色 #fafafa/深色 #252525 与父表不一致）
			th:last-child {
				background: var(--el-fill-color-light);
				box-shadow: -2px 0 6px -1px rgba(0, 21, 41, 0.1);
			}

			td:last-child {
				background: var(--el-fill-color-light) !important;
				box-shadow: -2px 0 6px -1px rgba(0, 21, 41, 0.1);
			}
		}
	}

	.toolbar {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 10px;
		margin-bottom: 16px;

		// 搜索框区：内部允许换行，宽度随父级伸缩
		.toolbar-filters {
			display: flex;
			align-items: center;
			gap: 10px;
			flex-wrap: wrap;
			flex: 1 1 auto;
			min-width: 0;
		}

		// 查询/重置：宽屏时紧跟搜索框，窄屏换行后靠左
		.toolbar-query-btns {
			display: flex;
			align-items: center;
			gap: 10px;
			flex-shrink: 0;
		}

		// 操作按钮：始终靠右（margin-left:auto 在任何行上都把它推到最右）
		.toolbar-right {
			display: flex;
			align-items: center;
			gap: 10px;
			margin-left: auto;

			// 脚本联调按钮：黄褐色背景标识
			.btn-debug {
				background-color: #c07828;
				border-color: #c07828;
				color: #fff;

				&:hover, &:focus {
					background-color: #d08a35;
					border-color: #d08a35;
					color: #fff;
				}

				&.is-disabled {
					background-color: #ddb87a;
					border-color: #ddb87a;
					color: #fff;
				}
			}
		}
	}

	.progress-cell {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 0 6px;

		.progress-bar {
			flex: 1;
			min-width: 0;
		}

		.progress-suffix {
			font-size: 13px;
			font-weight: 700;
			flex-shrink: 0;
			line-height: 1;
		}
	}

	.script-link {
		color: var(--el-color-primary);
		cursor: pointer;
		font-size: 13.5px;

		&:hover {
			text-decoration: underline;
		}
	}

	.error-text {
		color: var(--el-color-danger);
		font-size: 13px;
	}

	// 占位文字（"--"）：使用 element 占位文本色变量
	.text-placeholder {
		color: var(--el-text-color-placeholder);
	}

	.action-btns {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-wrap: nowrap;

		:deep(.el-button) {
			padding: 0 4px;
			font-weight: 600;
			white-space: nowrap;

			.el-icon {
				margin-right: 2px;
			}
		}
	}

	.pagination {
		margin-top: 16px;
		display: flex;
		justify-content: flex-end;
	}

}

// 线程组类型标签（panel 标题 + 子列表共用）
// 浅色模式下保留四色品牌底，深色模式下通过 [data-theme='dark'] 覆盖为半透明背景以保证可读性
.tg-type-tag {
	display: inline-block;
	padding: 1px 8px;
	border-radius: 4px;
	font-size: 12px;
	white-space: nowrap;
	border: 1px solid transparent;
	&--0 { color: #722ed1; background: #f9f0ff; border-color: #d3adf7; }
	&--1 { color: #1677ff; background: #e6f4ff; border-color: #91caff; }
	&--2 { color: #d46b08; background: #fff7e6; border-color: #ffd591; }
	&--3 { color: #389e0d; background: #f6ffed; border-color: #b7eb8f; }
}

// 深色模式：四色徽章保持品牌识别度，但底色降透明、文字提亮
[data-theme='dark'] .tg-type-tag {
	&--0 { color: #b37feb; background: rgba(114, 46, 209, 0.18); border-color: rgba(114, 46, 209, 0.45); }
	&--1 { color: #69b1ff; background: rgba(22, 119, 255, 0.18); border-color: rgba(22, 119, 255, 0.45); }
	&--2 { color: #ffa940; background: rgba(212, 107, 8, 0.18); border-color: rgba(212, 107, 8, 0.45); }
	&--3 { color: #95de64; background: rgba(56, 158, 13, 0.18); border-color: rgba(56, 158, 13, 0.45); }
}
</style>

<style lang="scss">
/* 按钮内 slot wrapper span 设为 flex，使图标与文字垂直居中 */
.perf-scene-container .el-button > span {
	display: inline-flex !important;
	align-items: center !important;
	line-height: 1 !important;
}
</style>
