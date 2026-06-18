<template>
	<el-drawer
		v-model="drawerVisible"
		:title="drawerTitle"
		direction="rtl"
		:size="drawerSize"
		:close-on-click-modal="false"
		class="perf-scene-drawer"
		@close="resetForm"
	>
		<el-form
			ref="formRef"
			:model="form"
			:rules="formRules"
			size="default"
			label-width="130px"
			hide-required-asterisk
			class="scene-form"
		>
			<!-- JMX脚本 -->
			<el-form-item v-if="drawerMode === 'full'" prop="script_id">
				<template #label>
					<span class="label-txt"><span class="label-star">*</span>场景脚本</span>
					<el-tooltip content="选择已上传的JMX压测脚本" placement="top">
						<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
					</el-tooltip>
				</template>
				<div class="input-with-unit">
					<el-select
						v-model="form.script_id"
						placeholder="请选择JMX脚本（支持ID或名称搜索）"
						filterable
						:filter-method="filterJmx"
						style="width: 100%"
						@change="handleScriptChange"
					>
						<el-option
							v-for="s in filteredJmxScripts"
							:key="s.id"
							:label="`${s.id}：${s.name}`"
							:value="s.id"
						/>
					</el-select>
					<span class="unit-placeholder" />
				</div>
			</el-form-item>

			<!-- 任务名称 -->
			<el-form-item v-if="drawerMode === 'full'" prop="name">
				<template #label>
					<span class="label-txt"><span class="label-star">*</span>任务名称</span>
					<span class="label-tip-placeholder" />
				</template>
				<div class="input-with-unit">
					<el-input v-model="form.name" placeholder="请输入任务名称" maxlength="100" show-word-limit style="width: 100%" />
					<span class="unit-placeholder" />
				</div>
			</el-form-item>


			<!-- 测试类型 -->
			<el-form-item v-if="drawerMode === 'full'" prop="test_type">
				<template #label>
					<span class="label-txt">测试类型</span>
					<el-tooltip content="用于标识本次压测的场景类型" placement="top">
						<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
					</el-tooltip>
				</template>
				<div class="input-with-unit">
					<el-select
						v-model="form.test_type"
						placeholder="请选择测试类型"
						clearable
						style="width: 100%"
						popper-class="test-type-select-dropdown"
						placement="bottom-start"
						:popper-options="{ modifiers: [{ name: 'flip', options: { fallbackPlacements: [] } }, { name: 'preventOverflow', options: { altAxis: false } }] }"
					>
						<el-option v-for="t in TEST_TYPE_OPTIONS" :key="t.value" :label="t.label" :value="t.value">
							<div class="test-type-option">
								<span class="test-type-name">{{ t.label }}</span>
								<span class="test-type-desc">{{ t.desc }}</span>
							</div>
						</el-option>
					</el-select>
					<span class="unit-placeholder" />
				</div>
			</el-form-item>

			<!-- 是否分布式（仅主场景表单） -->
			<el-form-item v-if="drawerMode === 'full'" prop="distributed">
				<template #label>
					<span class="label-txt">是否分布式</span>
					<el-tooltip content="开启后将使用多个Worker节点并发执行压测" placement="top">
						<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
					</el-tooltip>
				</template>
				<el-switch v-model="form.distributed" active-text="是" inactive-text="否" inline-prompt />
			</el-form-item>

			<!-- Worker数量（仅主场景表单 + 分布式时显示） -->
			<el-form-item v-if="drawerMode === 'full' && form.distributed" prop="worker_count">
				<template #label>
					<span class="label-txt"><span class="label-star">*</span>Worker数量</span>
					<el-tooltip content="分布式压测时使用的Slave节点数量" placement="top">
						<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
					</el-tooltip>
				</template>
				<div class="input-with-unit">
					<el-input-number
						v-model="form.worker_count"
						:min="1"
						:max="20"
						placeholder="请输入Worker节点数"
						style="width: 100%"
						controls-position="right"
					/>
					<span class="unit-placeholder" />
				</div>
			</el-form-item>

			<!-- 运行环境 -->
			<el-form-item v-if="drawerMode === 'full'" prop="env">
				<template #label>
					<span class="label-txt"><span class="label-star">*</span>运行环境</span>
					<span class="label-tip-placeholder" />
				</template>
				<div class="input-with-unit">
					<el-select v-model="form.env" placeholder="请选择运行环境" style="width: 100%">
						<el-option v-for="opt in ENV_OPTIONS" :key="opt.value" :label="opt.label" :value="opt.value" />
					</el-select>
					<span class="unit-placeholder" />
				</div>
			</el-form-item>

			<!-- 备注 -->
			<el-form-item v-if="drawerMode === 'full'" prop="remark">
				<template #label>
					<span class="label-txt">备注</span>
					<span class="label-tip-placeholder" />
				</template>
				<div class="input-with-unit">
					<el-input v-model="form.remark" placeholder="选填，最多200个字符" maxlength="200" show-word-limit style="width: 100%" />
					<span class="unit-placeholder" />
				</div>
			</el-form-item>

			<!-- 高级设置分割线（仅新增/复制模式显示，修改时隐藏：修改仅维护基本信息） -->
			<el-divider v-if="drawerMode === 'full' && _openMode !== 'edit'">
				<span class="divider-advanced">
					高级设置
					<el-switch v-model="form.advanced" style="margin-left: 8px; vertical-align: middle" />
				</span>
			</el-divider>

			<!-- 子配置预计耗时（config 模式，在高级设置前显示） -->
			<el-form-item v-if="drawerMode === 'config'">
				<template #label>
					<span class="label-txt">预计耗时</span>
					<el-tooltip :content="configDurationTooltip" placement="top" raw-content>
						<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
					</el-tooltip>
				</template>
				<div class="input-with-unit duration-input" :class="{ 'duration-unparsed': !!configDurationNote }">
					<el-input-number
						v-model="configEstimatedDuration"
						:min="0"
						:precision="0"
						:placeholder="configDurationNote || '选填'"
						style="width:100%"
						controls-position="right"
					/>
					<span class="unit-label">秒</span>
				</div>
			</el-form-item>

			<!-- 高级设置备注 -->
			<div v-if="drawerMode === 'config' || (form.advanced && _openMode !== 'edit')" class="advanced-remark">
				<el-icon class="advanced-remark__icon"><ele-WarningFilled /></el-icon>
				<span>高级设置：默认解析 JMX 脚本中的配置。修改线程参数配置后会覆盖 JMX 脚本原有参数配置。</span>
			</div>

			<template v-if="drawerMode === 'config' || (form.advanced && _openMode !== 'edit')">

				<!-- ① 有解析到的线程组：按 panel 展示，每个 panel 对应一个线程组 -->
				<template v-if="tabConfigs.length > 0">
					<div class="tg-panels">
						<div v-for="(tab, idx) in tabConfigs" :key="idx" class="tg-panel">
							<!-- panel 标题栏 -->
							<div class="tg-panel-header" @click.stop="toggleTgPanel(idx)">
								<div class="tg-panel-left">
									<span class="tg-type-tag" :class="`tg-type-tag--${tab.thread_type}`">
										{{ getThreadTypeLabel(tab.thread_type) }}
									</span>
									<el-tooltip :content="tab.tg_name || `线程组${idx + 1}`" placement="top" :show-after="400">
										<span class="tg-panel-name">{{ tab.tg_name || `线程组${idx + 1}` }}</span>
									</el-tooltip>
								</div>
								<div class="tg-panel-right">
									<span class="tg-panel-summary">{{ getTgSummary(tab) }}</span>
									<el-icon class="tg-panel-arrow" :class="{ rotated: panelExpanded[idx] }">
										<ele-ArrowDown />
									</el-icon>
								</div>
							</div>
							<!-- panel 展开内容 -->
							<el-collapse-transition>
								<div v-show="panelExpanded[idx]" class="tg-panel-content">

									<!-- 标准线程组 / SetUp 线程组 -->
									<template v-if="tab.thread_type === '0' || tab.thread_type === '1'">
										<el-form-item>
											<template #label>
												<span class="label-txt"><span class="label-star">*</span>线程数</span>
												<el-tooltip content="并发用户数，即单节点同时运行的虚拟线程数量" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.threads" :min="1" :max="10000" :precision="0" placeholder="如100" style="width:100%" controls-position="right" />
												<span class="unit-placeholder" />
											</div>
										</el-form-item>
										<el-form-item>
											<template #label>
												<span class="label-txt"><span class="label-star">*</span>Ramp-up 时间</span>
												<el-tooltip content="所有线程全部启动完毕所需的时间（秒），0表示同时启动" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.ramp_up" :min="0" placeholder="如60" style="width:100%" controls-position="right" />
												<span class="unit-label">秒</span>
											</div>
										</el-form-item>
										<el-form-item>
											<template #label>
												<span class="label-txt">循环次数</span>
												<el-tooltip content="每个线程执行测试计划的循环次数；若勾选永远循环，则必须设置持续时间" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.loop_count" :min="1" :precision="0" :disabled="tab.forever" placeholder="如10" style="width:100%" controls-position="right" />
												<el-checkbox v-model="tab.forever" class="unit-checkbox">永远</el-checkbox>
											</div>
										</el-form-item>
										<el-form-item v-if="tab.forever">
											<template #label>
												<span class="label-txt"><span class="label-star">*</span>持续时间</span>
												<el-tooltip content="压测持续运行的时间（秒），勾选永远循环时必须大于 0" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.duration" :min="1" placeholder="如 3600" style="width:100%" controls-position="right" />
												<span class="unit-label">秒</span>
											</div>
										</el-form-item>
										<el-form-item>
											<template #label>
												<span class="label-txt">启动延迟</span>
												<el-tooltip content="压测任务启动前的延迟等待时间（秒）" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.start_delay" :min="0" placeholder="如0" style="width:100%" controls-position="right" />
												<span class="unit-label">秒</span>
											</div>
										</el-form-item>
									</template>

									<!-- 阶梯加压 SteppingThreadGroup -->
									<template v-else-if="tab.thread_type === '2'">
										<el-form-item>
											<template #label>
												<span class="label-txt"><span class="label-star">*</span>目标线程数</span>
												<el-tooltip content="SteppingThreadGroup 最终目标线程数（num_threads）" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.threads" :min="1" :max="10000" :precision="0" placeholder="如100" style="width:100%" controls-position="right" />
												<span class="unit-placeholder" />
											</div>
										</el-form-item>
										<el-form-item>
											<template #label>
												<span class="label-txt">初始延迟</span>
												<el-tooltip content="延迟 X 秒后开始启动第一批线程" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.step_initial_delay" :min="0" placeholder="0" style="width:100%" controls-position="right" />
												<span class="unit-label">秒</span>
											</div>
										</el-form-item>
										<el-form-item>
											<template #label>
												<span class="label-txt">初始线程数</span>
												<el-tooltip content="Start users count burst：第一个阶梯启动的线程数（初始爆发数）" placement="top">
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="input-with-unit">
												<el-input-number v-model="tab.step_start_users_burst" :min="0" :precision="0" placeholder="0" style="width:100%" controls-position="right" />
												<span class="unit-placeholder" />
											</div>
										</el-form-item>
										<!-- 每步加压 -->
										<el-form-item>
											<template #label>
												<span class="label-txt"><span class="label-star">*</span>每步加压</span>
												<el-tooltip placement="top">
													<template #content>
														<div>start_users_period：每个步骤的时间间隔（秒）</div>
														<div>rampUp：步骤内的爬坡时间（秒）</div>
														<div>start_users_count：每步新增线程数</div>
													</template>
													<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
												</el-tooltip>
											</template>
											<div class="inline-step-row">
												<span class="step-txt step-col1">每步间隔</span>
												<el-input-number v-model="tab.step_start_users_period" :min="1" :precision="0" placeholder="如30" controls-position="right" class="step-input" />
												<span class="step-txt step-col2">s，在</span>
												<el-input-number v-model="tab.step_ramp_up" :min="0" placeholder="0" controls-position="right" class="step-input" />
												<span class="step-txt">s 内新增</span>
												<el-input-number v-model="tab.step_start_users_count" :min="1" :precision="0" placeholder="如10" controls-position="right" class="step-input step-input-fill" />
												<span class="step-txt">线程</span>
											</div>
										</el-form-item>
										<!-- 持续时间 + 每步减压：双标签合并 -->
										<el-form-item class="step-combined-item">
											<template #label>
												<div class="step-combined-labels">
													<span class="step-combined-label">
														<span class="label-txt">持续时间</span>
														<el-tooltip content="flighttime：达到最大线程数后保持满载的持续时间（秒），0=不持续" placement="top">
															<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
														</el-tooltip>
													</span>
													<span class="step-combined-label">
														<span class="label-txt">每步减压</span>
														<el-tooltip placement="top">
															<template #content>
																<div>stop_users_period：每步减压的时间间隔（秒）</div>
																<div>stop_users_count：每步停止的线程数，0=不减少</div>
															</template>
															<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
														</el-tooltip>
													</span>
												</div>
											</template>
											<div class="step-combined-content">
												<div class="input-with-unit">
													<el-input-number v-model="tab.step_flight_time" :min="0" placeholder="0" style="width:100%" controls-position="right" />
													<span class="unit-label">秒</span>
												</div>
												<div class="inline-step-row">
													<span class="step-txt step-col1">每</span>
													<el-input-number v-model="tab.step_stop_users_period" :min="0" :precision="0" placeholder="0" controls-position="right" class="step-input" />
													<span class="step-txt step-col2">s 停止</span>
													<el-input-number v-model="tab.step_stop_users_count" :min="0" :precision="0" placeholder="0" controls-position="right" class="step-input" />
													<span class="step-txt">个线程</span>
												</div>
											</div>
										</el-form-item>
									</template>

									<!-- 自定义阶段 UltimateThreadGroup -->
									<template v-else-if="tab.thread_type === '3'">
										<el-table
											v-if="tab.ultimate_rows?.length"
											:data="tab.ultimate_rows"
											row-key="_idx"
											border
											size="small"
											class="ultimate-rows-table"
										>
											<el-table-column width="58" align="center">
												<template #header>
													<span>阶段</span>
													<el-tooltip content="UltimateThreadGroup 自定义阶段编号" placement="top">
														<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
													</el-tooltip>
												</template>
												<template #default="{ $index }">阶段{{ $index + 1 }}</template>
											</el-table-column>
											<el-table-column align="center">
												<template #header>
													<span>线程数</span>
													<el-tooltip content="start_threads：该阶段同时运行的线程数" placement="top">
														<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
													</el-tooltip>
												</template>
												<template #default="{ $index }">
													<el-input v-model.number="tab.ultimate_rows[$index].start_threads" type="number" size="small" style="width:100%" />
												</template>
											</el-table-column>
											<el-table-column align="center">
												<template #header>
													<span>初始延迟(s)</span>
													<el-tooltip content="initial_delay：该阶段开始前等待的延迟时间（秒）" placement="top">
														<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
													</el-tooltip>
												</template>
												<template #default="{ $index }">
													<el-input v-model.number="tab.ultimate_rows[$index].initial_delay" type="number" size="small" style="width:100%" />
												</template>
											</el-table-column>
											<el-table-column align="center">
												<template #header>
													<span>爬坡时间(s)</span>
													<el-tooltip content="startup_time：阶段启动到达目标线程数所用的时间（秒）" placement="top">
														<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
													</el-tooltip>
												</template>
												<template #default="{ $index }">
													<el-input v-model.number="tab.ultimate_rows[$index].startup_time" type="number" size="small" style="width:100%" />
												</template>
											</el-table-column>
											<el-table-column align="center">
												<template #header>
													<span>持续时间(s)</span>
													<el-tooltip content="hold_load_for：达到目标线后保持满载运行的时间（秒）" placement="top">
														<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
													</el-tooltip>
												</template>
												<template #default="{ $index }">
													<el-input v-model.number="tab.ultimate_rows[$index].hold_load_for" type="number" size="small" style="width:100%" />
												</template>
											</el-table-column>
											<el-table-column align="center">
												<template #header>
													<span>停止时间(s)</span>
													<el-tooltip content="shutdown_time：阶段结束后线程逐渐停止的时间（秒）" placement="top">
														<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
													</el-tooltip>
												</template>
												<template #default="{ $index }">
													<el-input v-model.number="tab.ultimate_rows[$index].shutdown_time" type="number" size="small" style="width:100%" />
												</template>
											</el-table-column>
											<el-table-column label="操作" width="70" align="center">
												<template #default="{ $index }">
													<el-button
														type="danger"
														size="small"
														circle
														:disabled="(tab.ultimate_rows?.length || 0) <= 1"
														@click="removeUltimateStage(tab, $index)"
													>
														<el-icon><ele-Minus /></el-icon>
													</el-button>
												</template>
											</el-table-column>
										</el-table>
										<div v-else class="ultimate-empty">暂无自定义阶段数据，请上传含 UltimateThreadGroup 的 JMX 脚本。</div>
										<div class="ultimate-add-row">
											<el-button type="primary" plain size="small" @click="addUltimateStage(tab)">
												<el-icon><ele-Plus /></el-icon>新增阶段配置
											</el-button>
										</div>
									</template>

								</div>
							</el-collapse-transition>
						</div>
					</div>
				</template>

				<!-- ② 无解析数据（未选脚本 / 脚本无 parsed 缓存）：沿用原单配置表单 -->
				<template v-else>
					<!-- 线程数 -->
					<el-form-item prop="threads">
						<template #label>
							<span class="label-txt"><span class="label-star">*</span>线程数</span>
							<el-tooltip content="并发用户数，即单节点同时运行的虚拟线程数量" placement="top">
								<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
							</el-tooltip>
						</template>
						<div class="input-with-unit">
							<el-input-number
								v-model="form.threads"
								:min="1"
								:max="10000"
								:precision="0"
								:step="1"
								placeholder="并发线程数，如100"
								style="width: 100%"
								controls-position="right"
							/>
							<span class="unit-placeholder" />
						</div>
					</el-form-item>

					<!-- Ramp-up时间 -->
					<el-form-item prop="ramp_up">
						<template #label>
							<span class="label-txt"><span class="label-star">*</span>Ramp-up 时间</span>
							<el-tooltip content="所有线程全部启动完毕所需的时间（秒），0表示同时启动" placement="top">
								<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
							</el-tooltip>
						</template>
						<div class="input-with-unit">
							<el-input-number
								v-model="form.ramp_up"
								:min="0"
								placeholder="如60"
								style="width: 100%"
								controls-position="right"
							/>
							<span class="unit-label">秒</span>
						</div>
					</el-form-item>

					<!-- 循环次数 -->
					<el-form-item prop="loop_count">
						<template #label>
							<span class="label-txt">循环次数</span>
							<el-tooltip content="每个线程执行测试计划的循环次数；若勾选永远循环，则必须设置持续时间" placement="top">
								<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
							</el-tooltip>
						</template>
						<div class="input-with-unit">
							<el-input-number
								v-model="form.loop_count"
								:min="1"
								:precision="0"
								:step="1"
								:disabled="form.forever"
								placeholder="如10"
								style="width: 100%"
								controls-position="right"
							/>
							<el-checkbox v-model="form.forever" class="unit-checkbox">永远</el-checkbox>
						</div>
					</el-form-item>

					<!-- 持续时间（永远时显示，必填） -->
					<el-form-item v-if="form.forever" prop="duration">
						<template #label>
							<span class="label-txt"><span class="label-star">*</span>持续时间</span>
							<el-tooltip content="压测持续运行的时间（秒），勾选永远循环时必须大于 0" placement="top">
								<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
							</el-tooltip>
						</template>
						<div class="input-with-unit">
							<el-input-number
								v-model="form.duration"
								:min="1"
								placeholder="如 3600（至少 1 秒）"
								style="width: 100%"
								controls-position="right"
							/>
							<span class="unit-label">秒</span>
						</div>
					</el-form-item>

					<!-- 启动延迟 -->
					<el-form-item prop="start_delay">
						<template #label>
							<span class="label-txt">启动延迟</span>
							<el-tooltip content="压测任务启动前的延迟等待时间（秒）" placement="top">
								<el-icon class="label-tip-icon"><ele-QuestionFilled /></el-icon>
							</el-tooltip>
						</template>
						<div class="input-with-unit">
							<el-input-number
								v-model="form.start_delay"
								:min="0"
								placeholder="如0"
								style="width: 100%"
								controls-position="right"
							/>
							<span class="unit-label">秒</span>
						</div>
					</el-form-item>
				</template>
			</template>
		</el-form>

		<template #footer>
			<el-button size="default" @click="drawerVisible = false">取 消</el-button>
			<el-button size="default" type="primary" :loading="submitLoading" @click="handleSubmit">确 定</el-button>
		</template>
	</el-drawer>
</template>

<script setup lang="ts" name="PerfSceneAddUpdate">
import { ref, reactive, computed, watchEffect, onMounted, onUnmounted } from 'vue';
import { ElMessage, FormInstance } from 'element-plus';
import { usePerformanceApi } from '/@/api/v1/performance';
import { useDictCache } from '/@/utils/dictCache';
import { THREAD_TYPE_LABELS, normalizeConfig, normalizeUltimateRows, buildConfigPayload } from './utils';

type OpenMode = 'add' | 'edit' | 'copy' | 'config-edit' | 'config-copy' | 'config-add';

const emit = defineEmits<{
	(e: 'success', payload: { mode: string; scenarioId: number | null; row?: any }): void;
}>();

const perfApi = usePerformanceApi();
const { getDictOptions } = useDictCache();

// ======================== 字典 ========================
const THREAD_TYPE_OPTIONS = ref<{ value: string; label: string }[]>([]);
const ENV_OPTIONS = ref<{ value: string; label: string }[]>([]);
const TEST_TYPE_OPTIONS = ref<{ value: string; label: string; tagType: string; desc: string }[]>([]);

const getThreadTypeLabel = (type: string) =>
	THREAD_TYPE_OPTIONS.value.find(o => o.value === type)?.label ?? THREAD_TYPE_LABELS[type] ?? type;

// ======================== 抽屉状态 ========================
const windowWidth = ref(window.innerWidth);
const onWindowResize = () => { windowWidth.value = window.innerWidth; };
const drawerSize = computed(() => {
	if (windowWidth.value >= 1600) return '36%';
	if (windowWidth.value >= 1200) return '44%';
	return '55%';
});
const drawerVisible = ref(false);
const drawerTitle = ref('新增压测场景');
const drawerMode = ref<'full' | 'config'>('full');
const submitLoading = ref(false);
const formRef = ref<FormInstance>();
const editId = ref<number | null>(null);
const editConfigId = ref<number | null>(null);
const currentRow = ref<any>(null);   // open() 时传入的父行，emit success 时携带
const _openMode = ref<string>('add'); // 记录本次 open 的模式，供 handleSubmit 使用

// ======================== JMX 脚本 ========================
const jmxScripts = ref<{ id: number; name: string; parsed_thread_config?: any[] | null; estimated_seconds?: number | null; duration_note?: string | null }[]>([]);
const jmxFilterQuery = ref('');

const loadJmxScripts = async () => {
	try {
		const res: any = await perfApi.getFileOptions({ file_type: 'jmx' });
		jmxScripts.value = (res?.data ?? []).map((f: any) => ({
			id: f.id,
			name: f.name,
			parsed_thread_config: f.parsed_thread_config ?? null,
			estimated_seconds: f.estimated_seconds ?? null,
			duration_note: f.duration_note ?? null,
		}));
	} catch (_) {
		ElMessage.error('加载JMX脚本列表失败');
	}
};

const filteredJmxScripts = computed(() => {
	const q = jmxFilterQuery.value.trim().toLowerCase();
	if (!q) return jmxScripts.value;
	return jmxScripts.value.filter(s =>
		String(s.id).includes(q) || s.name.toLowerCase().includes(q)
	);
});

const filterJmx = (q: string) => { jmxFilterQuery.value = q; };

// ======================== 线程组 Tab 配置 ========================
const parsedThreadGroups = ref<any[]>([]);
const tabConfigs = ref<any[]>([]);
const panelExpanded = reactive<Record<number, boolean>>({});
const toggleTgPanel = (idx: number) => { panelExpanded[idx] = !panelExpanded[idx]; };

// ======================== 表单 ========================
const defaultForm = () => ({
	name: '',
	script_id: undefined as number | undefined,
	test_type: undefined as string | undefined,
	estimated_duration: undefined as number | undefined,
	remark: '',
	distributed: false,
	worker_count: 2,
	env: undefined as string | undefined,
	advanced: false,
	threads: undefined as number | undefined,
	ramp_up: undefined as number | undefined,
	loop_count: undefined as number | undefined,
	forever: false,
	duration: undefined as number | undefined,
	start_delay: 0,
});

const form = reactive(defaultForm());

const formRules = computed(() => {
	const hasTabs = tabConfigs.value.length > 0;
	const isEdit  = _openMode.value === 'edit';
	return {
		name:         [{ required: true, message: '请输入任务名称',    trigger: 'blur'   }],
		script_id:    [{ required: true, message: '请选择JMX脚本',     trigger: 'change' }],
		worker_count: [{ required: true, message: '请输入Worker数量',  trigger: 'blur'   }],
		env:          [{ required: true, message: '请选择运行环境',    trigger: 'change' }],
		...(!hasTabs && !isEdit ? {
			threads: [{ required: true, message: '请输入线程数', trigger: 'blur' }],
			ramp_up: [{ required: true, message: '请输入 Ramp-up 时间', trigger: 'blur' }],
			duration: [{
				validator: (_rule: any, value: any, callback: (e?: Error) => void) => {
					if (form.forever) {
						if (value === undefined || value === null) {
							callback(new Error('勾选永远循环时，持续时间必填'));
						} else if (value < 1) {
							callback(new Error('持续时间必须大于 0（至少 1 秒）'));
						} else {
							callback();
						}
					} else {
						callback();
					}
				},
				trigger: ['blur', 'change'],
			}],
		} : {}),
	};
});

// ======================== 预计耗时 ========================
// config 模式：getter 直接读取线程组字段计算，Vue 自动追踪依赖，字段改变时 computed 立即更新
const configEstimatedDuration = computed({
	get: () => {
		if (!tabConfigs.value.length) return form.estimated_duration;
		const tab = tabConfigs.value[0];
		if (tab._manual) return tab.estimated_duration ?? undefined;
		// Ultimate 类型通过 watchEffect 更新的 ref 读取，确保深层 rows 字段变化能触发 computed 更新
		const auto = tab.thread_type === '3' ? (_ultimateTabDurations.value[0] ?? null) : calcSingleTabDuration(tab);
		// 可自动计算时返回计算值；循环次数模式无法计算时回退到存储值
		return auto !== null ? auto : (tab.estimated_duration ?? undefined);
	},
	set: (v: number | undefined) => {
		if (tabConfigs.value.length > 0) {
			tabConfigs.value[0].estimated_duration = v;
			tabConfigs.value[0]._manual = (v != null);  // 清空则恢复自动计算
		} else {
			form.estimated_duration = v;
		}
	},
});

const configDurationTooltip = computed(() => {
	const tt = tabConfigs.value.length > 0 ? (tabConfigs.value[0].thread_type ?? '1') : '1';
	if (tt === '2') {
		return [
			'<b>SteppingThreadGroup 计算公式</b>',
			'耗时 = 初始延迟',
			'　　＋ ⌈(目标线程数 − 初始线程数) ÷ 每步新增线程数⌉ × 每步间隔',
			'　　＋ 满载持续时间',
			'　　＋ ⌈目标线程数 ÷ 每步停止线程数⌉ × 减压间隔',
			'手动填写后以填写值为准，优先级高于自动解析计算',
      '第二、四步的除法结果均向上取整，如19.4向上取整后20'
		].join('<br>');
	}
	if (tt === '3') {
		return [
			'<b>UltimateThreadGroup 计算公式</b>',
			'耗时 = max(各阶段：初始延迟 + 爬坡时间 + 持续时间 + 停止时间)',
			'手动填写后以填写值为准，优先级高于自动解析计算',
		].join('<br>');
	}
	return [
		'<b>ThreadGroup 计算规则</b>',
		'永远循环 + 持续时间：ramp-up + 启动延迟 + 持续时间',
		'循环次数模式：ramp-up + 启动延迟（执行段不确定，标记 ⚠）',
		'手动填写后以填写值为准，优先级高于自动解析计算',
	].join('<br>');
});

// ======================== 工具函数（仅抽屉内部使用） ========================
function buildTabConfig(g: any, inheritForm?: any): any {
	return {
		id:           g.id ?? null,
		tg_name:      g.tg_name ?? g.name ?? '',
		thread_type:  g.thread_type ?? '1',
		threads:      g.threads      ?? g.thread_count      ?? undefined,
		ramp_up:      g.ramp_up      ?? g.ramp_up_time      ?? undefined,
		loop_count:   g.loop_count   ?? undefined,
		forever:      !!(g.forever || g.loop_forever),
		duration:     g.duration     ?? undefined,
		start_delay:  g.start_delay  ?? g.startup_delay     ?? 0,
		step_initial_delay:      g.step_initial_delay      ?? 0,
		step_start_users_count:  g.step_start_users_count  ?? undefined,
		step_start_users_burst:  g.step_start_users_burst  ?? 0,
		step_start_users_period: g.step_start_users_period ?? undefined,
		step_stop_users_count:   g.step_stop_users_count   ?? 0,
		step_stop_users_period:  g.step_stop_users_period  ?? 0,
		step_flight_time:        g.step_flight_time        ?? 0,
		step_ramp_up:            g.step_ramp_up            ?? 0,
		ultimate_rows: normalizeUltimateRows(g.ultimate_rows).map((r: any, idx: number) => ({ ...r, _idx: idx })),
		distributed:  inheritForm?.distributed ?? false,
		worker_count: inheritForm?.worker_count ?? 2,
		estimated_duration: g.estimated_duration ?? null,
		_manual: false,  // 用户手动修改预计耗时后置为 true，阻止自动覆盖
	};
}

const calcSingleTabDuration = (tab: any): number | null => {
	const tt = String(tab.thread_type ?? '1');
	if (tt === '0' || tt === '1') {
		if (!tab.forever) return null;
		const dur = tab.duration ?? 0;
		if (dur <= 0) return null;
		return (tab.start_delay ?? 0) + (tab.ramp_up ?? 0) + dur;
	}
	if (tt === '2') {
		const threads = tab.threads ?? 0;
		const burst   = tab.step_start_users_burst  ?? 0;
		const count   = tab.step_start_users_count  ?? 1;
		const period  = tab.step_start_users_period ?? 0;
		const rampUp  = tab.step_ramp_up            ?? 0;
		const flight  = tab.step_flight_time        ?? 0;
		const init    = tab.step_initial_delay      ?? 0;
		const sCnt    = tab.step_stop_users_count   ?? 0;
		const sPer    = tab.step_stop_users_period  ?? 0;
		if (count <= 0) return null;
		const stepsUp   = threads > burst ? Math.ceil((threads - burst) / count) : 0;
		const stepsDown = sCnt > 0 ? Math.ceil(threads / sCnt) : 0;
		return init + (stepsUp + 1) * rampUp + stepsUp * period + flight + stepsDown * sPer;
	}
	if (tt === '3') {
		const rows = tab.ultimate_rows ?? [];
		if (!rows.length) return null;
		return Math.max(...rows.map((r: any) =>
			(r.initial_delay ?? 0) + (r.startup_time ?? 0) + (r.hold_load_for ?? 0) + (r.shutdown_time ?? 0)
		));
	}
	return null;
};

const calcTabsDuration = (tabs: any[]): { secs: number | null; note: string } => {
	let total = 0;
	for (const tab of tabs) {
		const d = calcSingleTabDuration(tab);
		if (d == null) return { secs: null, note: '存在循环次数控制的线程组，无法精确计算时间，请手动输入' };
		total += d;
	}
	return { secs: total, note: '' };
};

// config 模式耗时提示：依赖 tab 字段动态响应，循环次数模式时显示警告
const configDurationNote = computed(() => {
	if (drawerMode.value !== 'config' || !tabConfigs.value.length) return '';
	const tab = tabConfigs.value[0];
	if (tab._manual) return '';
	return calcSingleTabDuration(tab) === null
		? '线程组配置了循环次数，执行时长不确定，请手动输入'
		: '';
});

// UltimateThreadGroup 各阶段字段嵌套较深，watchEffect 显式追踪 rows 深层变化，确保耗时 computed 实时更新
const _ultimateTabDurations = ref<(number | null)[]>([]);
watchEffect(() => {
	_ultimateTabDurations.value = tabConfigs.value.map((tab: any) => {
		if (tab.thread_type !== '3') return null;
		const rows: any[] = tab.ultimate_rows ?? [];
		if (!rows.length) return null;
		const times = rows.map((r: any) =>
			(r.initial_delay ?? 0) + (r.startup_time ?? 0) + (r.hold_load_for ?? 0) + (r.shutdown_time ?? 0)
		);
		return times.length > 0 ? Math.max(...times) : null;
	});
});

// full 模式预计耗时：getter 直接聚合所有 tab 计算，Vue 自动追踪依赖，任意 tab 字段改变时立即更新
const formEstimatedDuration = computed({
	get: () => {
		if (drawerMode.value !== 'full' || !tabConfigs.value.length) {
			return form.estimated_duration;
		}
		let total = 0;
		for (let i = 0; i < tabConfigs.value.length; i++) {
			const tab = tabConfigs.value[i];
			// Ultimate 类型通过 watchEffect 的 _ultimateTabDurations 读取，确保深层 rows 字段变化能触发更新
			const secs = tab.thread_type === '3' ? (_ultimateTabDurations.value[i] ?? null) : calcSingleTabDuration(tab);
			// 存在不可计算的线程组（循环次数模式）时回退到存储值
			if (secs === null) return form.estimated_duration;
			total += secs;
		}
		return total > 0 ? total : form.estimated_duration;
	},
	set: (v: number | undefined) => {
		form.estimated_duration = v;
	},
});

const getTgSummary = (tab: any): string => {
	const tt = tab.thread_type ?? '1';
	const n = tab.threads ?? '--';
	if (tt === '2') {
		const parts: string[] = [];
		const hasDelay = tab.step_initial_delay != null && tab.step_initial_delay !== '';
		const hasBurst = tab.step_start_users_burst != null && tab.step_start_users_burst !== '';
		const initial = hasDelay && hasBurst ? tab.step_start_users_burst : 0;
		parts.push(`${initial}→${n}`);
		if (tab.step_start_users_count != null && tab.step_start_users_period != null) {
			let s = `+${tab.step_start_users_count}/${tab.step_start_users_period}s`;
			if (tab.step_ramp_up != null && tab.step_ramp_up > 0) s += `(爬坡${tab.step_ramp_up}s)`;
			parts.push(s);
		}
		if (tab.step_flight_time != null && tab.step_flight_time > 0) parts.push(`持续${tab.step_flight_time}s`);
		if (tab.step_stop_users_count != null && tab.step_stop_users_period != null && tab.step_stop_users_count > 0) {
			parts.push(`减压-${tab.step_stop_users_count}/${tab.step_stop_users_period}s`);
		}
		return parts.join(' | ');
	}
	if (tt === '3') return `${tab.ultimate_rows?.length ?? 0}个自定义阶段`;
	const parts: string[] = [];
	if (tab.start_delay) parts.push(`延迟${tab.start_delay}s启动`);
	if (tab.ramp_up != null && tab.threads != null)
		parts.push(tab.start_delay ? `${tab.ramp_up}s ${n}个线程` : `${tab.ramp_up}s启动${n}个线程`);
	else if (tab.threads != null) parts.push(`${n}个线程`);
	if (tab.forever) {
		parts.push('永远执行');
		if (tab.duration != null) parts.push(`持续${tab.duration}s`);
	} else if (tab.loop_count != null) {
		parts.push(`循环${tab.loop_count}次`);
	}
	return parts.join(' · ') || '未配置';
};

const removeUltimateStage = (tab: any, sIdx: number) => {
	if (!tab?.ultimate_rows || tab.ultimate_rows.length <= 1) {
		ElMessage.warning('至少保留一条阶段配置');
		return;
	}
	tab.ultimate_rows.splice(sIdx, 1);
	tab.ultimate_rows.forEach((r: any, i: number) => { r._idx = i; });
};

const addUltimateStage = (tab: any) => {
	if (!Array.isArray(tab.ultimate_rows)) tab.ultimate_rows = [];
	const nextIdx = tab.ultimate_rows.length;
	tab.ultimate_rows.push({ start_threads: 0, initial_delay: 0, startup_time: 0, hold_load_for: 0, shutdown_time: 0, _idx: nextIdx });
};

// ======================== 脚本变化 ========================
const handleScriptChange = (id: number) => {
	const script = jmxScripts.value.find((s: any) => s.id === id);
	if (script && !form.name) {
		form.name = script.name.replace('.jmx', '') + '-压测';
	}
	parsedThreadGroups.value = [];
	tabConfigs.value = [];
	for (const k in panelExpanded) delete panelExpanded[k];
	const groups = script?.parsed_thread_config;
	if (Array.isArray(groups) && groups.length > 0) {
		parsedThreadGroups.value = groups;
		tabConfigs.value = groups.map((g: any) => buildTabConfig(g, form));
		// 第一个 panel 展开，其余折叠
		groups.forEach((_: any, i: number) => { panelExpanded[i] = i === 0; });
	}
	// 从 tabConfigs 自动计算预计耗时；不可计算（循环次数模式）时回退到 JMX 文件预存值
	if (tabConfigs.value.length > 0) {
		const { secs } = calcTabsDuration(tabConfigs.value);
		form.estimated_duration = secs != null ? secs : (script?.estimated_seconds ?? undefined);
	} else {
		form.estimated_duration = script?.estimated_seconds ?? undefined;
	}
};

// 仅更新 full 模式耗时提示 note；tab/form 实际显示值由 formEstimatedDuration / configEstimatedDuration computed 自动响应

// ======================== 表单操作 ========================
const resetForm = () => {
	formRef.value?.resetFields();
	Object.assign(form, defaultForm());
	editId.value = null;
	editConfigId.value = null;
	currentRow.value = null;
	parsedThreadGroups.value = [];
	tabConfigs.value = [];
	// 清理所有 panel 展开状态，避免跨次打开残留
	for (const k in panelExpanded) delete panelExpanded[k];
};

// ======================== 对外暴露：open() ========================
async function open(mode: OpenMode, payload?: { row?: any; cfg?: any }) {
	resetForm();
	_openMode.value = mode;
	currentRow.value = payload?.row ?? null;

	// 每次打开都刷新脚本列表
	await loadJmxScripts();

	if (mode === 'add') {
		drawerMode.value = 'full';
		drawerTitle.value = '新增压测场景';
		editId.value = null;

	} else if (mode === 'edit') {
		drawerMode.value = 'full';
		drawerTitle.value = '修改压测场景';
		const row = payload!.row;
		editId.value = row.id;
		// 修改仅维护基本信息，不加载子配置（子配置通过子列表单条修改维护）
		Object.assign(form, {
			name:        row.name,
			script_id:   row.script_id,
			test_type:   row.test_type,
			remark:      row.remark ?? '',
			env:         row.env,
			distributed: row.is_distributed ?? false,
			worker_count: row.node_count ?? 2,
		});

	} else if (mode === 'copy') {
		drawerMode.value = 'full';
		drawerTitle.value = '新增压测场景';
		editId.value = null;
		const row = payload!.row;
		try {
			const res: any = await perfApi.getScenarioConfigList(row.id);
			const configs: any[] = res.code === 200 ? (res.data ?? []).map(normalizeConfig) : [];
			const activeConfig = configs.find((c: any) => c.active) ?? configs[0];
			Object.assign(form, {
				name:               `${row.name}-副本`,
				script_id:          row.script_id,
				test_type:          row.test_type,
				estimated_duration: row.estimated_duration ?? undefined,
				remark:             row.remark ?? '',
				env:                row.env,
				distributed:        row.is_distributed ?? false,
				worker_count:       row.node_count ?? 2,
				advanced:           !!activeConfig,
				threads:            activeConfig?.threads,
				ramp_up:            activeConfig?.ramp_up,
				loop_count:         activeConfig?.loop_count,
				forever:            activeConfig?.forever ?? false,
				duration:           activeConfig?.duration,
				start_delay:        activeConfig?.start_delay ?? 0,
			});
			// 用 activeConfig 填充 tabConfigs，保留线程组类型（Stepping/Ultimate/Standard）及所有参数
			if (activeConfig) {
				tabConfigs.value = [buildTabConfig(activeConfig)];
				panelExpanded[0] = true;
			}
		} catch (_) { /* ignore */ }

	} else if (mode === 'config-edit') {
		drawerMode.value = 'config';
		drawerTitle.value = '编辑压测配置';
		const cfg = payload!.cfg;
		editId.value = payload!.row.id;
		editConfigId.value = cfg.id;
		tabConfigs.value = [buildTabConfig(cfg)];
		if (tabConfigs.value[0].estimated_duration == null && !cfg.has_unknown_times && (cfg.known_times ?? 0) > 0) {
			tabConfigs.value[0].estimated_duration = cfg.known_times;
		}
		panelExpanded[0] = true;

	} else if (mode === 'config-copy') {
		drawerMode.value = 'config';
		drawerTitle.value = '新增压测配置';
		const cfg = payload!.cfg;
		editId.value = payload!.row.id;
		editConfigId.value = null;
		tabConfigs.value = [buildTabConfig(cfg)];
		panelExpanded[0] = true;

	} else if (mode === 'config-add') {
		drawerMode.value = 'config';
		drawerTitle.value = '新增压测配置';
		editId.value = payload!.row.id;
		editConfigId.value = null;
		panelExpanded[0] = true;
	}

	drawerVisible.value = true;
}

defineExpose({ open });

// ======================== 提交 ========================
const handleSubmit = () => {
	formRef.value?.validate(async (valid) => {
		if (!valid) return;
		submitLoading.value = true;
		const savedEditId = editId.value;
		const useTabMode = tabConfigs.value.length > 0 && (drawerMode.value === 'full' ? form.advanced : true);

		const validateCfgDuration = (cfg: any): boolean => {
			const tt: string = cfg.thread_type ?? '1';
			if (!['0', '1'].includes(tt) || cfg.forever || cfg.estimated_duration == null) return true;
			const known = (cfg.ramp_up || 0) + (cfg.start_delay || 0);
			if (known > 0 && cfg.estimated_duration <= known) {
				ElMessage.error(`预计耗时须大于已知耗时（ramp-up ${cfg.ramp_up || 0}s + 启动延迟 ${cfg.start_delay || 0}s = ${known}s）`);
				return false;
			}
			return true;
		};

		// 将 computed 自动计算的耗时同步到 tab 对象，供 buildConfigPayload 正确取值
		for (const tab of tabConfigs.value) {
			if (!tab._manual) {
				const auto = calcSingleTabDuration(tab);
				if (auto !== null) tab.estimated_duration = auto;
			}
		}
		if (drawerMode.value === 'full') {
				const autoVal = formEstimatedDuration.value;
			if (autoVal != null) form.estimated_duration = autoVal;
		}

		try {
			if (drawerMode.value === 'config') {
				const cfgSrc = useTabMode ? tabConfigs.value[0] : form;
				if (!validateCfgDuration(cfgSrc)) { submitLoading.value = false; return; }
				if (editConfigId.value) {
					await perfApi.updateScenarioConfig(editId.value!, editConfigId.value!, buildConfigPayload(cfgSrc));
					ElMessage.success('配置已更新');
				} else {
					await perfApi.addScenarioConfig(editId.value!, buildConfigPayload(cfgSrc, 0));
					ElMessage.success('配置已新增');
				}

			} else if (editId.value) {
				// 修改仅更新基本信息，不涉及预计耗时和子配置（子配置通过子列表单条修改维护）
				const payload: any = {};
				if (form.name)      payload.name      = form.name;
				if (form.script_id) payload.script_id = form.script_id;
				if (form.test_type) payload.test_type = form.test_type;
				if (form.env)       payload.run_env   = form.env;
				payload.remark         = form.remark ?? '';
				payload.is_distributed = form.distributed ? 1 : 0;
				if (form.distributed)  payload.node_count = form.worker_count;
				await perfApi.updateScenario(editId.value, payload);
				ElMessage.success('修改成功');

			} else {
				const payload: any = {
					name:           form.name,
					script_id:      form.script_id,
					run_env:        form.env,
					is_distributed: form.distributed ? 1 : 0,
				};
				if (form.distributed) payload.node_count = form.worker_count;
				if (form.test_type) payload.test_type = form.test_type;
				if (form.remark)    payload.remark    = form.remark;
				if (form.estimated_duration != null) payload.estimated_duration = form.estimated_duration;

				if (useTabMode) {
					for (const t of tabConfigs.value) {
						if (!validateCfgDuration(t)) { submitLoading.value = false; return; }
					}
					payload.configs = tabConfigs.value.map((t: any, idx: number) =>
						buildConfigPayload(t, idx === 0 ? 1 : 0)
					);
				} else if (form.advanced) {
					if (!validateCfgDuration(form)) { submitLoading.value = false; return; }
					payload.configs = [buildConfigPayload(form, 1)];
				}
				const res: any = await perfApi.addScenario(payload);
				ElMessage.success('新增成功');
				drawerVisible.value = false;
				emit('success', { mode: _openMode.value, scenarioId: res?.data?.id ?? null, row: currentRow.value });
				return;
			}

			drawerVisible.value = false;
			emit('success', { mode: _openMode.value, scenarioId: savedEditId, row: currentRow.value });

		} catch (e: any) {
			ElMessage.error(e?.response?.data?.detail || '操作失败，请重试');
		} finally {
			submitLoading.value = false;
		}
	});
};

// ======================== 生命周期 ========================
onMounted(async () => {
	window.addEventListener('resize', onWindowResize);
	const [testTypeOpts, envOpts, tgTypeOpts] = await Promise.all([
		getDictOptions('perf_test_category').catch(() => []),
		getDictOptions('sys_env').catch(() => []),
		getDictOptions('perf_thread_group_type').catch(() => []),
	]);
	TEST_TYPE_OPTIONS.value = (testTypeOpts as any[]).map((o) => ({
		value: String(o.value),
		label: o.label,
		tagType: (o.raw?.list_class ?? '') as string,
		desc: o.raw?.remark ?? '',
	}));
	ENV_OPTIONS.value = (envOpts as any[]).map((o) => ({ value: String(o.value), label: o.label }));
	THREAD_TYPE_OPTIONS.value = (tgTypeOpts as any[]).map((o) => ({ value: String(o.value), label: o.label }));
});

onUnmounted(() => {
	window.removeEventListener('resize', onWindowResize);
});
</script>

<style scoped lang="scss">
// ---- 抽屉表单 ----
.scene-form {
	padding: 24px 20px 0;

	:deep(.el-form-item__label) {
		display: flex !important;
		align-items: center;
		padding-right: 8px !important;
		font-size: 13.5px;

		.label-txt {
			flex: 1;
			text-align: right;

			.label-star {
				color: var(--el-color-danger);
				margin-right: 2px;
			}
		}

		.label-tip-icon,
		.label-tip-placeholder {
			flex-shrink: 0;
			width: 16px;
			margin-left: 4px;
		}

		.el-tooltip__trigger {
			display: inline-flex !important;
			align-items: center;
		}

		.label-tip-icon {
			color: var(--el-text-color-secondary);
			cursor: help;
			font-size: 13.5px;

			&:hover {
				color: var(--el-color-primary);
			}
		}
	}

	:deep(.el-form-item) {
		margin-bottom: 14px;
	}

	:deep(.el-input__inner),
	:deep(.el-textarea__inner) {
		font-size: 13.5px;
	}

	:deep(.el-select__selected-item),
	:deep(.el-select__input) {
		font-size: 13.5px;
	}

	:deep(.el-input__inner::placeholder),
	:deep(.el-input-number .el-input__inner::placeholder),
	:deep(.el-textarea__inner::placeholder) {
		font-size: 13.5px;
	}

	:deep(.el-select__placeholder) {
		font-size: 13.5px;
	}

	:deep(.el-divider__text) {
		font-size: 13px;
		color: var(--el-text-color-regular);
	}

	:deep(.el-divider) {
		margin-top: 36px;
		margin-bottom: 36px;
	}

	.divider-advanced {
		font-size: 13px;
		color: var(--el-text-color-regular);
		display: flex;
		align-items: center;
	}

	.advanced-remark {
		display: flex;
		align-items: flex-start;
		gap: 6px;
		margin: -10px 0 10px;
		padding: 9px 14px;
		background: var(--el-color-warning-light-9);
		border: 1px solid var(--el-color-warning-light-7);
		border-radius: 4px;
		font-size: 13px;
		color: var(--el-color-warning-dark-2);
		line-height: 1.7;

		.advanced-remark__icon {
			flex-shrink: 0;
			margin-top: 2px;
			font-size: 14px;
			color: var(--el-color-warning);
		}
	}

	.input-with-unit {
		display: flex;
		align-items: center;
		width: 100%;
		gap: 8px;

		.unit-label {
			color: var(--el-text-color-regular);
			font-size: 13.5px;
			flex-shrink: 0;
			min-width: 50px;
		}

		.unit-placeholder {
			flex-shrink: 0;
			min-width: 50px;
		}

		.unit-checkbox {
			flex-shrink: 0;
			white-space: nowrap;
		}
	}
}

// ---- 高级设置 Panel 式线程组配置 ----
.tg-panels {
	display: flex;
	flex-direction: column;
	gap: 8px;
	margin: 0 0 8px;
}

.tg-panel {
	border: 1px solid var(--el-border-color-light);
	border-radius: 6px;
	overflow: hidden;
	background: var(--el-bg-color);

	.tg-panel-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 9px 14px;
		cursor: pointer;
		user-select: none;
		background: var(--el-fill-color-lighter);
		&:hover { background: var(--el-fill-color-light); }
	}

	.tg-panel-left {
		display: flex;
		align-items: center;
		gap: 8px;
		flex: 1;
		min-width: 0;
	}

	.tg-panel-name {
		font-size: 13.5px;
		font-weight: 500;
		color: var(--el-text-color-primary);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.tg-panel-right {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-shrink: 0;
	}

	.tg-panel-summary {
		font-size: 12.5px;
		color: var(--el-text-color-secondary);
	}

	.tg-panel-arrow {
		font-size: 13px;
		color: var(--el-text-color-secondary);
		transition: transform 0.2s;
		&.rotated { transform: rotate(180deg); }
	}

	.tg-panel-content {
		padding: 16px 0 8px;
		border-top: 1px solid var(--el-border-color-lighter);
	}

	.ultimate-rows-table {
		margin: 0;
		font-size: 13px;
		width: 100%;

		:deep(.el-table__header-wrapper th) {
			background-color: transparent;
			font-weight: 500;
			padding: 6px 0;
		}

		:deep(.el-table__body-wrapper td) {
			padding: 4px 0;
		}

		:deep(.el-button.is-circle) {
			width: 26px;
			height: 26px;
			padding: 0;

			.el-icon {
				font-size: 16px;
				svg {
					stroke: currentColor;
					stroke-width: 2;
				}
			}
		}

		:deep(.el-input__wrapper) {
			box-shadow: none;
			border-bottom: 1px solid var(--el-border-color);
			border-radius: 0;
			padding: 0 4px;
		}

		:deep(.el-input__inner) {
			text-align: center;
			font-size: 13px;
		}
	}

	.ultimate-empty {
		margin: 0 16px;
		padding: 12px 0;
		font-size: 13px;
		color: var(--el-text-color-secondary);
	}

	.ultimate-add-row {
		display: flex;
		justify-content: center;
		margin-top: 10px;
	}
}

// 持续时间+每步减压合并 form-item
.step-combined-item {
	:deep(.el-form-item__label) {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		height: auto;
		line-height: 32px;
		gap: 10px;
		padding-top: 2px;
	}

	.step-combined-labels {
		display: flex;
		flex-direction: column;
		gap: 10px;
		width: 100%;
	}

	.step-combined-label {
		display: flex;
		align-items: center;
		gap: 2px;
		line-height: 32px;
	}

	.step-combined-content {
		display: flex;
		flex-direction: column;
		gap: 10px;
		width: 100%;
	}
}

.inline-step-row {
	display: flex;
	align-items: center;
	gap: 6px;
	flex-wrap: nowrap;
	width: 100%;

	.step-txt {
		font-size: 13px;
		color: var(--el-text-color-regular);
		white-space: nowrap;
		flex-shrink: 0;
	}

	.step-input {
		width: 90px;
		flex-shrink: 0;
	}

	.step-input-fill {
		width: 90px;
	}
}

.step-col1 {
	display: inline-block;
	min-width: 4em;
	text-align: right;
}

.step-col2 {
	display: inline-block;
	min-width: 3em;
}

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

[data-theme='dark'] .tg-type-tag {
	&--0 { color: #b37feb; background: rgba(114, 46, 209, 0.18); border-color: rgba(114, 46, 209, 0.45); }
	&--1 { color: #69b1ff; background: rgba(22, 119, 255, 0.18); border-color: rgba(22, 119, 255, 0.45); }
	&--2 { color: #ffa940; background: rgba(212, 107, 8, 0.18); border-color: rgba(212, 107, 8, 0.45); }
	&--3 { color: #95de64; background: rgba(56, 158, 13, 0.18); border-color: rgba(56, 158, 13, 0.45); }
}
</style>

<style lang="scss">
// 抽屉底部按钮区域间距（drawer 传送至 body，需非 scoped 规则）
.el-drawer.perf-scene-drawer .el-drawer__footer {
	padding: 16px 24px;
	border-top: 1px solid var(--el-border-color-lighter);
	display: flex;
	justify-content: flex-end;
	gap: 12px;
}

// 测试类型下拉选项样式（teleport 到 body，需非 scoped）
.test-type-select-dropdown {
	.el-select-dropdown__item {
		height: auto !important;
		padding: 8px 12px;
		line-height: 1.4;
	}

	.test-type-option {
		display: flex;
		flex-direction: column;

		.test-type-name {
			font-size: 13px;
			font-weight: 500;
			color: var(--el-text-color-primary);
		}

		.test-type-desc {
			font-size: 12px;
			color: var(--el-text-color-secondary);
			margin-top: 3px;
			white-space: normal;
			line-height: 1.5;
		}
	}
}

/* 高级设置提示块：深色模式下背景压暗 */
[data-theme='dark'] .advanced-remark {
	background: #1e1e1e !important;
	border-color: #3a3a3a !important;
	color: var(--el-color-warning) !important;
}

/* 预计耗时输入框始终左对齐 */
.el-drawer.perf-scene-drawer .duration-input .el-input__inner {
	text-align: left !important;
}

/* 预计耗时未解析时占位文字显示为警告黄色 */
.el-drawer.perf-scene-drawer .duration-unparsed .el-input__inner::placeholder {
	color: var(--el-color-warning);
}
</style>