<template>
	<div class="perf-files-container">
		<el-card shadow="hover">
			<!-- 工具栏 -->
			<div class="toolbar">
				<div class="toolbar-left">
					<el-input
						v-model="query.name"
						placeholder="搜索文件名称"
						clearable
						style="width: 300px"
						@keyup.enter="handleQuery"
					>
						<template #prefix><el-icon><ele-Search /></el-icon></template>
					</el-input>
					<el-select v-model="query.file_type" placeholder="文件类型" clearable style="width: 160px" @change="handleQuery">
						<el-option v-for="t in fileTypeOptions" :key="t.value" :label="t.label" :value="t.value" />
					</el-select>
					<el-select v-model="query.status" placeholder="文件状态" clearable style="width: 160px" @change="handleQuery">
						<el-option v-for="s in fileStatusOptions" :key="s.value" :label="s.label" :value="s.value" />
					</el-select>
					<el-button type="primary" @click="handleQuery">
						<el-icon><ele-Search /></el-icon>搜索
					</el-button>
					<el-button @click="resetQuery">
						<el-icon><ele-Refresh /></el-icon>重置
					</el-button>
				</div>
				<div class="toolbar-right">
					<el-upload
						v-if="!selectingDownload"
						:show-file-list="false"
						:before-upload="handleBeforeUpload"
						:http-request="handleUpload"
						accept=".csv,.txt,.xlsx,.xls,.json,.yaml,.yml,.jmx"
					>
						<el-button type="primary">
							<el-icon><ele-Upload /></el-icon>上传文件
						</el-button>
					</el-upload>
					<el-button v-if="!selectingDownload" type="success" @click="enterDownloadMode">
						<el-icon><ele-Download /></el-icon>下载文件
					</el-button>
					<template v-else>
						<el-button type="success" @click="startDownload">
							<el-icon><ele-Download /></el-icon>开始下载
						</el-button>
						<el-button @click="cancelDownload">取 消</el-button>
					</template>
					<el-button v-if="!selectingDownload" :loading="statusRefreshing" @click="handleRefreshStatus">
						<el-icon><ele-Refresh /></el-icon>刷新状态
					</el-button>
				</div>
			</div>

			<!-- 表格 -->
			<el-table v-loading="loading" :data="fileList" border stripe style="width: 100%">
				<el-table-column width="60" align="center" fixed="left">
					<template #header>
						<span>{{ selectingDownload ? '选择' : 'ID' }}</span>
					</template>
					<template #default="{ row }">
						<span v-if="!selectingDownload">{{ row.id }}</span>
						<el-checkbox
							v-else
							:model-value="selectedDownloadIds.has(row.id)"
							@change="(val: boolean) => toggleDownload(row.id, val)"
						/>
					</template>
				</el-table-column>
				<el-table-column prop="name" min-width="200" align="center" fixed="left">
					<template #header><span>文件名称</span></template>
					<template #default="{ row }">
						<span class="file-type-badge" :style="{ background: fileIconBg(row.file_type) }">
							{{ fileTypeLabel(row.file_type) }}
						</span>
						<el-tooltip :content="row.name" placement="top" :show-after="300">
							<span class="file-name-text">{{ row.name }}</span>
						</el-tooltip>
					</template>
				</el-table-column>
				<el-table-column prop="status" min-width="90" align="center">
					<template #header>
						<span>文件状态</span>
						<el-tooltip content="未引用：未被 JMX 脚本使用；已引用：被脚本引用；已关联：jmx脚本已被压测场景关联。" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<el-tag :type="statusTagType(row.status)" size="small" :effect="row.status === 'running' ? 'dark' : 'light'">
							{{ statusLabel(row.status) }}
						</el-tag>
					</template>
				</el-table-column>
				<el-table-column min-width="90" align="center">
					<template #header>
						<span>分发状态</span>
						<el-tooltip placement="top">
							<template #content>
								<div style="max-width:220px;line-height:1.6">
									<b>共享分发：</b>文件完整复制，各节点独立持有相同副本<br>
									<b>分割分发：</b>文件按节点数等比分片，各节点仅持有对应分片
								</div>
							</template>
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<el-tag v-if="row.distribute_type === 'shared'" type="success" size="small" effect="light">已共享</el-tag>
						<el-tag v-else-if="row.distribute_type === 'split'" type="warning" size="small" effect="light">已分割</el-tag>
						<el-tag v-else type="info" size="small" effect="light">未分发</el-tag>
					</template>
				</el-table-column>
				<el-table-column prop="workers" min-width="80" align="center">
					<template #header>
						<span>Workers</span>
						<el-tooltip content="已成功分发文件的压力机数量" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<span v-if="!row.distribute_type" class="text-placeholder">--</span>
						<span v-else>{{ row.workers }}</span>
					</template>
				</el-table-column>
				<el-table-column prop="size" label="文件大小" min-width="120" align="center">
					<template #default="{ row }">{{ row.size }}</template>
				</el-table-column>
				<el-table-column min-width="140" show-overflow-tooltip align="center">
					<template #header>
						<span>引用文件</span>
						<el-tooltip content="JMX 脚本所引用的数据文件列表" placement="top">
							<el-icon class="tip-icon"><ele-QuestionFilled /></el-icon>
						</el-tooltip>
					</template>
					<template #default="{ row }">
						<template v-if="row.jmx_refs && row.jmx_refs.length">
							<el-tooltip :content="row.jmx_refs.join('、')" placement="top" :show-after="300">
								<span class="jmx-ref-text">{{ row.jmx_refs.join('、') }}</span>
							</el-tooltip>
						</template>
						<span v-else class="text-placeholder">--</span>
					</template>
				</el-table-column>
				<el-table-column prop="created_at" label="上传时间" min-width="160" align="center">
					<template #default="{ row }">
						<span style="white-space: nowrap">{{ formatDateTime(row.created_at) }}</span>
					</template>
				</el-table-column>
				<el-table-column label="分发时间" min-width="160" align="center">
					<template #default="{ row }">
						<template v-if="row.distribute_type && row.distributed_at
							&& new Date(row.created_at) > new Date(row.distributed_at)">
							<el-tooltip
								content="文件内容已更新但未分发到压力机！"
								placement="top"
							>
								<span class="dist-outdated">
									<el-icon class="dist-warn-icon"><ele-WarningFilled /></el-icon>
									{{ formatDateTime(row.distributed_at) }}
								</span>
							</el-tooltip>
						</template>
						<span v-else style="white-space:nowrap">
							{{ row.distributed_at ? formatDateTime(row.distributed_at) : '--' }}
						</span>
					</template>
				</el-table-column>
				<el-table-column prop="operator" label="操作人" min-width="80" align="center" show-overflow-tooltip />
				<el-table-column label="备注" min-width="180">
					<template #default="{ row }">
						<el-tooltip
							v-if="row.remark && isDistFailRemark(row.remark)"
							placement="top"
							:show-after="300"
							popper-style="max-width:50vw;white-space:normal;line-height:1.7"
						>
							<template #content>
								<div v-for="(line, i) in row.remark.split('\n').filter(Boolean)" :key="i">{{ line }}</div>
							</template>
							<span class="dist-fail-remark normal-remark-text">{{ row.remark.split('\n')[0] }}</span>
						</el-tooltip>
						<el-tooltip
							v-else-if="row.remark"
							placement="top"
							:show-after="300"
							popper-style="max-width:50vw;white-space:pre-wrap"
						>
							<template #content>{{ row.remark }}</template>
							<span class="normal-remark-text">{{ row.remark }}</span>
						</el-tooltip>
						<span v-else style="color: var(--el-text-color-placeholder)">--</span>
					</template>
				</el-table-column>
				<el-table-column label="操作" width="230" fixed="right" align="center" class-name="operation-col">
					<template #default="{ row }">
						<div class="action-btns">
							<!-- 更新区域 -->
							<div class="update-slot">
								<!-- JMX · 正常模式 -->
								<template v-if="row.file_type === 'jmx'">
									<el-tooltip
										content="该脚本已被压测场景关联，更新时文件名必须与原文件名保持一致"
										placement="bottom"
										trigger="manual"
										:visible="updateWarnTipVisible[row.id] ?? false"
									>
										<el-button type="warning" size="small" text @click="triggerJmxFileUpdate(row)">
											<el-icon><ele-Upload /></el-icon>更新
										</el-button>
									</el-tooltip>
								</template>

								<!-- 非 JMX · 正常更新 -->
								<template v-else>
									<el-upload
										:show-file-list="false"
										:before-upload="handleBeforeUpload"
										:http-request="(opt: any) => handleUpdate(opt, row)"
										:accept="'.' + row.file_type"
										style="display:inline-flex"
									>
										<el-button type="warning" size="small" text>
											<el-icon><ele-Upload /></el-icon>更新
										</el-button>
									</el-upload>
								</template>
							</div>

							<!-- 修改引用（仅 JMX） -->
							<el-button
								v-if="row.file_type === 'jmx'"
								type="success"
								size="small"
								text
								@click="openRefDrawer(row)"
							>
								<el-icon><ele-Link /></el-icon>修改
							</el-button>

							<!-- 分发（仅非 JMX） -->
							<template v-if="row.file_type !== 'jmx'">
								<el-button
									v-if="!row.distribute_type"
									type="primary"
									size="small"
									text
									@click="handleDistribute('open-dialog', row)"
								>
									<el-icon><ele-Share /></el-icon>分发
								</el-button>
								<el-button
									v-else
									size="small"
									text
									@click="handleDistribute('clear', row)"
								>
									<el-icon><ele-CircleClose /></el-icon>清除
								</el-button>
							</template>

							<!-- 清除JMX分发记录（仅 JMX 且已有分发记录，不SSH删除机器文件） -->
							<el-button
								v-if="row.file_type === 'jmx' && row.distribute_type"
								size="small"
								text
								:loading="clearingJmxDistIds.has(row.id)"
								@click="handleClearJmxDist(row)"
							>
								<el-icon><ele-CircleClose /></el-icon>清除
							</el-button>

							<!-- 删除 -->
							<el-button
								type="danger"
								size="small"
								text
								:loading="deletingIds.has(row.id)"
								:disabled="deletingIds.has(row.id)"
								@click="handleDelete(row)"
							>
								<el-icon v-if="!deletingIds.has(row.id)"><ele-Delete /></el-icon>
								{{ deletingIds.has(row.id) ? '删除中' : '删除' }}
							</el-button>
						</div>
					</template>
				</el-table-column>
			</el-table>

			<!-- 分页 -->
			<el-pagination
				v-show="total > 0"
				v-model:current-page="query.page"
				v-model:page-size="query.page_size"
			:page-sizes="[20, 50, 100]"
				:total="total"
				layout="total, sizes, prev, pager, next, jumper"
				class="pagination"
				@size-change="handleQuery"
				@current-change="handleQuery"
			/>
		</el-card>

		<!-- 文件分发抽屉（仅表单配置） -->
		<el-drawer
			v-model="distributeDrawerVisible"
			:title="distributeForm.type === 'clear' ? '清除分发' : '文件分发'"
			direction="rtl"
			size="560px"
			:close-on-click-modal="false"
			class="distribute-drawer"
		>
			<div class="distribute-drawer-form">
				<el-form label-width="100px" label-position="right">
					<el-form-item label="文件名称">
						<span class="distribute-filename">{{ distributeRow?.name }}</span>
					</el-form-item>

					<!-- 清除分发：显示清除 worker 数量 -->
					<template v-if="distributeForm.type === 'clear'">
						<el-form-item label="清除 Worker" required>
							<el-input-number
								v-model="distributeForm.clearWorkerCount"
								style="width: 400px"
								:min="1"
								:max="distributeRow?.workers || 1"
							/>
							<span style="margin-left:8px;font-size:12px;color:var(--el-text-color-secondary)">
								最多 {{ distributeRow?.workers || 0 }} 台（已分发数量）
							</span>
						</el-form-item>
						<el-form-item label=" " class="desc-form-item">
							<span class="distribute-type-desc">删除各压力机上已分发的文件，释放磁盘空间或为重新分发做准备。</span>
						</el-form-item>
					</template>

					<!-- 共享/分割分发：选择压力机类型 -->
					<template v-else>
						<el-form-item label="压力机类型" required>
							<el-radio-group v-model="distributeForm.machineCategory" @change="onMachineCategoryChange">
								<el-radio
									v-for="opt in machineTypeOptions"
									:key="opt.value"
									:value="opt.value"
									:disabled="distributeForm.type === 'split' && opt.value === '3'"
								>{{ opt.label }}</el-radio>
							</el-radio-group>
						</el-form-item>

						<!-- 分布式：显示分发方式 -->
						<template v-if="distributeForm.machineCategory !== '3'">
							<el-form-item label="分发方式" required>
								<el-radio-group v-model="distributeForm.type">
									<el-radio value="shared">共享分发</el-radio>
									<el-radio value="split">分割分发</el-radio>
								</el-radio-group>
							</el-form-item>
							<el-form-item label=" " class="desc-form-item">
								<span class="distribute-type-desc">
									<template v-if="distributeForm.type === 'shared'">
										将文件完整复制并独立分发到各压力机，各节点持有相同副本。
									</template>
									<template v-else>
										将文件按压力机节点数量等比例分割，各节点分别接收对应分片。
									</template>
								</span>
							</el-form-item>
						</template>

						<!-- 分发 Worker -->
						<el-form-item label="分发 Worker" required>
							<div style="display: flex; align-items: center; gap: 8px">
								<el-select
									v-if="distributeForm.machineCategory === '3'"
									v-model="distributeForm.standaloneWorkerId"
									placeholder="请选择目标压力机"
									style="width: 400px"
									:teleported="false"
									:loading="machinesLoading"
								>
									<el-option
										v-for="m in standaloneMachines"
										:key="m.id"
										:label="m.name"
										:value="m.id"
									/>
								</el-select>
								<el-input-number
									v-if="distributeForm.machineCategory !== '3'"
									v-model="distributeForm.workerCount"
									style="width: 400px"
									:min="distributeForm.type === 'split' ? 2 : 1"
									:max="maxSlaveCount || 100"
								/>
							</div>
						</el-form-item>
						<el-form-item label=" " class="notice-form-item">
							<div class="distribute-notice">
								<ul>
									<li>执行分发前务必检查<b>配置管理 - 参数配置</b>中的各项配置是否正确；</li>
									<li>分发文件名在压力机中存在同名文件时，<b>会被覆盖</b>；</li>
									<li>输入分发 Worker 数量，系统会获取<b>未删除 + 启用</b>状态的压力机，按数据 ID <b>升序排序</b>，再取指定数量的 Worker 进行分发（即从小到大依次取用）；</li>
									<li>压力机类型选择<b>单机</b>时，仅支持分发到单机；选择 <b>Slave</b> 时支持分发到分布式 Worker 节点；</li>
                  <li>如果直接在服务器中清理了已分发的文件，不会更新前端文件分发状态，需要时尽量在前端清除分发；</li>
									<li v-if="distributeForm.type === 'split'">分割分发到各 Worker 的文件名和源文件名<b>相同</b>，便于清理和 JMX 脚本调用。</li>
								</ul>
							</div>
						</el-form-item>
					</template>
				</el-form>

				<div class="drawer-footer">
					<el-button @click="distributeDrawerVisible = false">取消</el-button>
					<el-button type="primary" @click="startDistribute">
						{{ distributeForm.type === 'clear' ? '确认清除' : '确认分发' }}
					</el-button>
				</div>
			</div>
		</el-drawer>

		<!-- 分发进度抽屉 -->
		<el-drawer
			v-model="distributeProgressVisible"
			:title="distributeForm.type === 'clear' ? `清除分发进度（${distributeRow?.name || ''}）` : distributeForm.type === 'split' ? `分割分发进度（${distributeRow?.name || ''}）` : `共享分发进度（${distributeRow?.name || ''}）`"
			direction="rtl"
			size="560px"
			:close-on-click-modal="false"
			:close-on-press-escape="!distributeStreaming"
			:show-close="!distributeStreaming"
			class="distribute-drawer"
		>
			<div class="dist-result-panel">

				<!-- 列头（带背景色，全局唯一一行） -->
				<div
					class="dist-col-header"
					:style="{ gridTemplateColumns: distributeForm.type === 'split' ? '22px 1fr 60px 52px 130px 32px' : '22px 1fr 52px 130px 32px' }"
				>
					<span class="col-status"></span>
					<span class="col-name">机器名称 (IP)</span>
					<span v-if="distributeForm.type === 'split'" class="col-chunk">分片大小</span>
					<span class="col-connect">连接</span>
					<span class="col-dist">进度</span>
					<span class="col-expand"></span>
				</div>

				<!-- 分发方案标识（method 事件写入后展示） -->
				<div v-if="distributeMethod" class="dist-method-label">{{ distributeMethod }}</div>

				<!-- Master 拉取 MinIO 进度条（方案B专用，仅 Master 拉取阶段显示） -->
				<div v-if="masterPullProgress.visible" class="master-pull-bar">
					<span class="master-pull-label">{{ masterPullProgress.message }}</span>
					<el-progress
						:percentage="masterPullProgress.pct"
						:stroke-width="4"
						:show-text="false"
						color="#409eff"
						style="flex:1;min-width:80px"
					/>
					<span class="master-pull-pct">{{ masterPullProgress.pct }}%</span>
				</div>

				<!-- 方案C：平台机中转 MinIO 下载行（持久显示，不因下载完成消失） -->
				<template v-if="platformMinioRow">
					<div class="dist-row" :style="{ gridTemplateColumns: '22px 1fr 52px 130px 32px' }">
						<div class="col-status">
							<el-icon v-if="platformMinioRow.status === 'running'" class="spin-icon"><ele-Loading /></el-icon>
							<el-icon v-else-if="platformMinioRow.status === 'success'" class="icon-ok"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="icon-fail"><ele-CircleCloseFilled /></el-icon>
						</div>
						<span class="row-name">平台机 → MinIO → 下载文件</span>
						<div class="col-connect">
							<el-icon v-if="platformMinioRow.conn_status === 'connecting'" class="spin-icon"><ele-Loading /></el-icon>
							<el-icon v-else-if="platformMinioRow.conn_status === 'connected'" class="icon-ok"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="icon-fail"><ele-CircleCloseFilled /></el-icon>
						</div>
						<div class="col-dist">
							<el-tooltip placement="top" :show-after="0" :hide-after="0" :enterable="false" :content="platformMinioRow.message">
								<div class="dist-progress-wrap">
									<el-progress
										:percentage="platformMinioRow.progress"
										:stroke-width="5"
										:show-text="false"
										:color="platformMinioRow.status === 'success' ? '#67c23a' : platformMinioRow.status === 'failed' ? '#f56c6c' : '#409eff'"
										style="width:85px;flex-shrink:0"
									/>
									<span class="dist-pct-text" :style="{ color: platformMinioRow.status === 'success' ? '#67c23a' : platformMinioRow.status === 'failed' ? '#f56c6c' : '#409eff' }">
										{{ platformMinioRow.status === 'success' ? '100%' : `${platformMinioRow.progress}%` }}
									</span>
								</div>
							</el-tooltip>
						</div>
						<div class="col-expand">
							<el-icon v-if="platformMinioRow.status === 'failed'" class="expand-btn" @click="toggleExpand(-2)">
								<ele-ArrowDown v-if="!expandedNodes.has(-2)" />
								<ele-ArrowUp v-else />
							</el-icon>
						</div>
					</div>
					<div v-if="expandedNodes.has(-2)" class="expand-detail">{{ platformMinioRow.message }}</div>
				</template>

				<!-- Master 行（如有） -->
				<template v-if="masterStatus">
					<div
						class="dist-row"
						:style="{ gridTemplateColumns: distributeForm.type === 'split' ? '22px 1fr 60px 52px 130px 32px' : '22px 1fr 52px 130px 32px' }"
					>
						<div class="col-status">
							<el-icon v-if="masterStatus.status === 'connecting'" class="spin-icon"><ele-Loading /></el-icon>
							<el-icon v-else-if="masterStatus.status === 'success'" class="icon-ok"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="icon-fail"><ele-CircleCloseFilled /></el-icon>
						</div>
						<el-tooltip :content="`${masterStatus.name} (${masterStatus.ip})`" placement="top" :show-after="400">
							<span class="row-name">
								{{ masterStatus.name }}<span class="row-ip"> ({{ masterStatus.ip }})</span>
								<el-tag type="info" size="small" effect="plain" style="margin-left:6px;vertical-align:middle;font-size:11px">Master</el-tag>
							</span>
						</el-tooltip>
						<div v-if="distributeForm.type === 'split'" class="col-chunk"></div>
						<div class="col-connect">
							<el-icon v-if="masterStatus.status === 'connecting'" class="spin-icon"><ele-Loading /></el-icon>
							<el-icon v-else-if="masterStatus.status === 'success'" class="icon-ok"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="icon-fail"><ele-CircleCloseFilled /></el-icon>
						</div>
						<div class="col-dist"></div>
						<div class="col-expand">
							<el-icon v-if="masterStatus.status === 'failed'" class="expand-btn" @click="toggleExpand(-1)">
								<ele-ArrowDown v-if="!expandedNodes.has(-1)" />
								<ele-ArrowUp v-else />
							</el-icon>
						</div>
					</div>
					<div v-if="expandedNodes.has(-1)" class="expand-detail">{{ masterStatus.message }}</div>
				</template>

				<!-- Slave / 清除机行 -->
				<div v-for="node in Object.values(nodeMap)" :key="node.machine_id">
					<div
						class="dist-row"
						:style="{ gridTemplateColumns: distributeForm.type === 'split' ? '22px 1fr 60px 52px 130px 32px' : '22px 1fr 52px 130px 32px' }"
					>
						<!-- 行状态图标 -->
						<div class="col-status">
							<el-icon v-if="node.status === 'pending' || node.status === 'running'" class="spin-icon"><ele-Loading /></el-icon>
							<el-icon v-else-if="node.status === 'success'" class="icon-ok"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="icon-fail"><ele-CircleCloseFilled /></el-icon>
						</div>
						<!-- 机器名称 -->
						<el-tooltip :content="`${node.name} (${node.ip})`" placement="top" :show-after="400">
							<span class="row-name">{{ node.name }}<span class="row-ip"> ({{ node.ip }})</span></span>
						</el-tooltip>
						<!-- 分片大小（仅分割分发） -->
						<div v-if="distributeForm.type === 'split'" class="col-chunk">{{ node.chunk_size || '--' }}</div>
						<!-- SSH 连接状态 -->
						<div class="col-connect">
							<el-icon v-if="!node.conn_status" class="spin-icon"><ele-Loading /></el-icon>
							<el-icon v-else-if="node.conn_status === 'connected'" class="icon-ok"><ele-CircleCheckFilled /></el-icon>
							<el-icon v-else class="icon-fail"><ele-CircleCloseFilled /></el-icon>
						</div>
						<!-- 分发进度：始终显示进度条，悬停显示当前操作阶段 -->
						<div class="col-dist">
							<el-tooltip placement="top" :show-after="0" :hide-after="0" :enterable="false"
								:content="getNodeStageLabel(node)">
								<div class="dist-progress-wrap">
									<el-progress
										:percentage="node.status === 'success' || node.status === 'failed' ? 100 : (node.progress || 0)"
										:stroke-width="5"
										:show-text="false"
										:color="node.status === 'pending' ? '#dcdfe6' : node.status === 'success' ? '#67c23a' : node.status === 'failed' ? '#f56c6c' : '#409eff'"
										style="width:85px;flex-shrink:0"
									/>
									<span
										class="dist-pct-text"
										:style="{ color: node.status === 'success' ? '#67c23a' : node.status === 'failed' ? '#f56c6c' : node.status === 'pending' ? '#c0c4cc' : '#409eff' }"
									>
										{{ node.status === 'success' ? '100%' : node.status === 'failed' ? '失败' : `${node.progress || 0}%` }}
									</span>
								</div>
							</el-tooltip>
						</div>
						<!-- 展开按钮（仅失败节点可展开查看错误信息） -->
						<div class="col-expand">
							<el-icon v-if="node.status === 'failed'" class="expand-btn" @click="toggleExpand(node.machine_id)">
								<ele-ArrowDown v-if="!expandedNodes.has(node.machine_id)" />
								<ele-ArrowUp v-else />
							</el-icon>
						</div>
					</div>
					<div v-if="expandedNodes.has(node.machine_id)" class="expand-detail">{{ node.message }}</div>
				</div>

				<!-- 汇总 -->
				<div v-if="doneResult" class="dist-summary">
					<el-divider />
					<el-tag type="success" size="large" effect="light">成功 {{ doneResult.success_count }} 台</el-tag>
					<el-tag type="danger" size="large" effect="light" style="margin-left:10px">失败 {{ doneResult.failed_count }} 台</el-tag>
				</div>
			</div>
			<template #footer>
				<div style="display:flex;justify-content:flex-end;padding:12px 20px;gap:8px">
					<el-button
						v-if="distributeStreaming"
						@click="distributeStreaming = false; distributeProgressVisible = false"
					>强制关闭</el-button>
					<el-button
						v-else
						type="primary"
						@click="distributeProgressVisible = false"
					>关 闭</el-button>
				</div>
			</template>
		</el-drawer>

		<!-- JMX文件修改抽屉 -->
		<el-drawer
			v-model="refDrawerVisible"
			title="修改文件"
			direction="rtl"
			size="520px"
			:close-on-click-modal="false"
			class="ref-files-drawer"
			@close="refFilterQuery = ''; refDrawerFileName = ''"
		>
			<div style="padding: 16px 4px 0; font-size: 13.5px" dir="ltr">
				<el-form label-width="90px">
					<el-form-item label="文件名称">
						<el-input v-model="refDrawerFileName" placeholder="请输入文件名称" style="width:100%" />
					</el-form-item>
					<el-form-item label="引用文件">
						<el-select
							v-model="refDrawerSelectedIds"
							multiple
							filterable
							:filter-method="filterRefFiles"
							placement="bottom-start"
							:teleported="true"
							:popper-options="{ modifiers: [{ name: 'flip', options: { fallbackPlacements: [] } }, { name: 'preventOverflow', options: { altAxis: false } }] }"
							placeholder="请选择引用的数据文件（可多选，支持ID或名称搜索）"
							style="width: 100%"
							:loading="refFilesLoading"
						>
							<el-option
								v-for="f in filteredNonJmxFiles"
								:key="f.id"
								:label="`${f.id}：${f.name}`"
								:value="f.id"
							/>
						</el-select>
					</el-form-item>
				</el-form>
			</div>
			<template #footer>
				<div style="display:flex;justify-content:flex-end;gap:10px;padding:12px 20px;margin:12px 20px;">
					<el-button @click="refDrawerVisible = false">取消</el-button>
					<el-button type="primary" :loading="refSaving" @click="saveRefDrawer">确认修改</el-button>
				</div>
			</template>
		</el-drawer>

		<!-- 隐藏的 JMX 文件更新 input -->		<input ref="jmxFileInputRef" type="file" accept=".jmx" style="display:none" @change="onJmxFileInputChange" />

		<!-- 上传进度对话框 -->
		<el-dialog
			v-model="uploading"
			title="文件上传中"
			width="420px"
			:close-on-click-modal="false"
			:show-close="false"
			:close-on-press-escape="false"
			align-center
		>
			<div style="padding: 8px 0 20px">
				<p style="margin-bottom: 14px; font-size: 13.5px; color: var(--el-text-color-regular); word-break: break-all">
					{{ uploadFileName }}
				</p>
				<el-progress :percentage="uploadProgress" :stroke-width="14" />
				<p style="margin-top: 10px; font-size: 12px; color: var(--el-text-color-secondary); text-align: center">
					{{ uploadProgress < 100 ? '上传中，请勿关闭页面…' : '上传成功！' }}
				</p>
			</div>
		</el-dialog>
	</div>
</template>

<script setup lang="ts" name="PerformanceFiles">
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';

// 将字节数格式化为带单位的字符串，与 report/index.vue 保持一致
function formatFileSize(bytes: number): string {
	if (!bytes || bytes <= 0) return '0 B';
	const units = ['B', 'KB', 'MB', 'GB', 'TB'];
	const i = Math.floor(Math.log(bytes) / Math.log(1024));
	return (bytes / Math.pow(1024, i)).toFixed(1).replace(/\.0$/, '') + ' ' + units[i];
}
import { ElMessage, ElMessageBox } from 'element-plus';
import { usePerformanceApi } from '/@/api/v1/performance';
import { useDictCache } from '/@/utils/dictCache';

const route = useRoute();
const perfApi = usePerformanceApi();
const { getDictOptions } = useDictCache();

// 代理上传大小阈值，onMounted 从后端 PROXY_UPLOAD_MAX_BYTES 参数动态获取，默认 100MB
const proxyUploadMaxBytes = ref(100 * 1024 * 1024);

// ======================== 常量 ========================
// 文件类型/文件状态选项从字典表动态加载（onMounted 中赋值）
const fileTypeOptions = ref<{ label: string; value: string }[]>([]);
const fileStatusOptions = ref<{ label: string; value: string }[]>([]);

// ref_status 整数 → 内部字符串键（用于表格徽章展示）
const STATUS_STR_MAP: Record<number, string> = { 0: 'unused', 1: 'referenced', 2: 'linked', 3: 'running' };
// dist_status 整数 → distribute_type 字符串
const DIST_TYPE_MAP: Record<number, string | null> = { 0: null, 1: 'shared', 2: 'split' };

// 状态文字：字典加载完成后动态填充，未加载时回退到内置中文兜底
const _FALLBACK_STATUS_LABEL: Record<string, string> = { unused: '未引用', referenced: '已引用', linked: '已关联', running: '使用中' };
const dynamicStatusLabelMap = ref<Record<string, string>>({});
const statusLabel = (s: string) => dynamicStatusLabelMap.value[s] ?? _FALLBACK_STATUS_LABEL[s] ?? s;

// ======================== 工具函数 ========================
const formatDateTime = (val: string) => {
	if (!val) return '-';
	return val.replace('T', ' ').substring(0, 19);
};

const statusTagType = (s: string): '' | 'success' | 'warning' | 'danger' | 'info' => {
	const map: Record<string, '' | 'success' | 'warning' | 'danger' | 'info'> = {
		unused: 'info', referenced: 'success', linked: '', running: 'warning',
	};
	return map[s] ?? 'info';
};

const fileIconBg = (type: string) => {
	const map: Record<string, string> = {
		csv: '#67c23a', txt: '#909399', xlsx: '#1d6f42', xls: '#1d6f42',
		json: '#e6a23c', yaml: '#409eff', yml: '#409eff', jmx: '#f56c6c',
	};
	return map[type] ?? '#909399';
};

const fileTypeLabel = (type: string) => {
	const map: Record<string, string> = {
		csv: 'CSV', txt: 'TXT', xlsx: 'XLS', xls: 'XLS',
		json: 'JSON', yaml: 'YAML', yml: 'YAML', jmx: 'JMX',
	};
	return map[type] ?? type.toUpperCase().substring(0, 4);
};

// 将后端 PerfFileRespSchema 字段映射为前端模板所需字段
// 分发失败备注：旧格式 "5-jmeter-worker-3：msg"，新格式 "【5】jmeter-worker-3：msg"
const isDistFailRemark = (remark: string) =>
	remark.includes('【') || /^\d+-/.test(remark);

const mapFileItem = (item: any) => ({
	...item,
	name: item.file_name,
	size: formatFileSize(item.file_size),                              // 字节数格式化显示
	status: STATUS_STR_MAP[item.ref_status as number] ?? 'unused',
	distribute_type: DIST_TYPE_MAP[item.dist_status as number] ?? null,
	workers: (item.dist_worker_ids || []).length,
	created_at: item.creation_date,
	distributed_at: item.dist_time,
	operator: item.operator_name,
	jmx_refs: (item.ref_files || []).map((f: any) => f.file_name),    // 仅 JMX 行有值
});

// ======================== 列表 ========================
const loading = ref(false);
const fileList = ref<any[]>([]);
const total = ref(0);

const query = reactive({
	name: '',
	file_type: undefined as string | undefined,
	status: undefined as string | undefined,
	page: 1,
	page_size: 20,
});

const handleQuery = async () => {
	loading.value = true;
	try {
		const params: any = { page: query.page, page_size: query.page_size };
		if (query.name) params.name = query.name;
		if (query.file_type) params.file_type = query.file_type;
		if (query.status) params.ref_status = Number(query.status);

		const res: any = await perfApi.getFileList(params);
		fileList.value = (res.data?.items || []).map(mapFileItem);
		total.value = res.data?.total ?? 0;
	} catch (e: any) {
		ElMessage.error(e.message || '获取文件列表失败');
	} finally {
		loading.value = false;
	}
};

const resetQuery = () => {
	query.name = '';
	query.file_type = undefined;
	query.status = undefined;
	query.page = 1;
	handleQuery();
};

// ======================== 刷新状态 ========================
const statusRefreshing = ref(false);

const handleRefreshStatus = async () => {
	statusRefreshing.value = true;
	try {
		await handleQuery();
		ElMessage.success('文件使用状态已刷新');
	} finally {
		statusRefreshing.value = false;
	}
};

// ======================== 上传进度 ========================
const uploading = ref(false);
const uploadProgress = ref(0);
const uploadFileName = ref('');

// 小文件代理上传（≤100MB）
const doProxyUpload = (file: File, remark?: string): Promise<any> => {
	const formData = new FormData();
	formData.append('file', file);
	if (remark) formData.append('remark', remark);
	return perfApi.uploadFile(formData, (e: ProgressEvent) => {
		// 字节传完不等于服务端处理完，最高设 99 留给最终完成状态
		if (e.total) uploadProgress.value = Math.min(99, Math.round((e.loaded / e.total) * 100));
	});
};

// 大文件预签名两阶段直传（>100MB）
const doPresignUpload = async (file: File, remark?: string): Promise<void> => {
	uploadProgress.value = 0;
	const presignRes: any = await perfApi.presignUpload({
		file_name: file.name,
		file_size: file.size,
		remark,
	});
	const { file_id, upload_url, object_key } = presignRes.data;

	// 直接 PUT 到 MinIO（XHR 支持进度事件，无需鉴权 Header）
	await new Promise<void>((resolve, reject) => {
		const xhr = new XMLHttpRequest();
		xhr.open('PUT', upload_url);
		xhr.upload.onprogress = (e) => {
			if (e.total) uploadProgress.value = Math.round((e.loaded / e.total) * 90);
		};
		xhr.onload = () => (xhr.status === 200 ? resolve() : reject(new Error(`存储上传失败 (${xhr.status})`)));
		xhr.onerror = () => reject(new Error('网络错误，上传失败'));
		xhr.send(file);
	});
	uploadProgress.value = 95;
	await perfApi.confirmUpload({ file_id, object_key });
	uploadProgress.value = 99; // 100 由 handleUpload 在全部完成后统一设置
};

// ======================== 上传 ========================
// 不限制文件大小：≤100MB 走代理上传，>100MB 走 MinIO 预签名直传，MinIO 本身无大小上限
const handleBeforeUpload = (_: File) => { // eslint-disable-line @typescript-eslint/no-unused-vars, no-unused-vars
	return true;
};

const handleUpload = async ({ file }: { file: File }) => {
	uploading.value = true;
	uploadFileName.value = file.name;
	uploadProgress.value = 0;
	try {
		if (file.size <= proxyUploadMaxBytes.value) {
			await doProxyUpload(file);
		} else {
			await doPresignUpload(file);
		}
		// 所有操作完成后推到 100%，显示"上传成功！"，1s 后关闭弹窗
		uploadProgress.value = 100;
		await new Promise((r) => setTimeout(r, 1000));
		ElMessage.success(`「${file.name}」上传成功`);
		handleQuery();
	} catch (e: any) {
		ElMessage.error(e.message || '上传失败');
	} finally {
		uploading.value = false;
		// 不在此处重置 uploadProgress，避免对话框关闭前进度条闪回 0%
		// 下次上传开始时 handleUpload 开头会重置为 0
	}
};

// ======================== 更新（替换） ========================
const handleUpdate = async ({ file }: { file: File }, row: any) => {
	const ext = file.name.split('.').pop()?.toLowerCase() ?? row.file_type;
	if (ext !== row.file_type) {
		ElMessage.error(`文件类型不匹配，请上传 .${row.file_type} 格式的文件`);
		return;
	}
	if (row.file_type === 'jmx' && row.status === 'linked') {
		if (file.name !== row.name) {
			updateWarnTipVisible.value[row.id] = true;
			setTimeout(() => { updateWarnTipVisible.value[row.id] = false; }, 3500);
			return;
		}
	}
	uploading.value = true;
	uploadFileName.value = file.name;
	uploadProgress.value = 0;
	try {
		if (file.size <= proxyUploadMaxBytes.value) {
			// 小文件：代理替换（后端读取后直传 MinIO）
			const formData = new FormData();
			formData.append('file', file);
			await perfApi.reuploadFile(row.id, formData, (e: ProgressEvent) => {
				if (e.total) uploadProgress.value = Math.round((e.loaded / e.total) * 100);
			});
		} else {
			// 大文件：预签名两阶段替换（前端直传 MinIO，原地更新 DB 记录）
			const presignRes: any = await perfApi.presignReupload({
				file_id:   row.id,
				file_name: file.name,
				file_size: file.size,
			});
			const { upload_url, object_key } = presignRes.data;
			await new Promise<void>((resolve, reject) => {
				const xhr = new XMLHttpRequest();
				xhr.open('PUT', upload_url);
				xhr.upload.onprogress = (e) => {
					if (e.total) uploadProgress.value = Math.round((e.loaded / e.total) * 90);
				};
				xhr.onload = () => (xhr.status === 200 ? resolve() : reject(new Error(`存储上传失败 (${xhr.status})`)));
				xhr.onerror = () => reject(new Error('网络错误，上传失败'));
				xhr.send(file);
			});
			uploadProgress.value = 95;
			await perfApi.confirmReupload({ file_id: row.id, object_key, file_name: file.name });
			uploadProgress.value = 100;
		}
		await new Promise((r) => setTimeout(r, 400));
		ElMessage.success(`「${row.name || file.name}」已更新`);
		handleQuery();
	} catch (e: any) {
		ElMessage.error(e.message || '更新失败');
	} finally {
		uploading.value = false;
		// 不在此处重置 uploadProgress，避免对话框关闭前进度条闪回 0%
	}
};

// ======================== JMX 更新文件 ========================
const jmxFileInputRef = ref<HTMLInputElement | null>(null);
const currentUpdateRow = ref<any>(null);
const updateWarnTipVisible = ref<Record<number, boolean>>({});

const triggerJmxFileUpdate = (row: any) => {
	currentUpdateRow.value = row;
	jmxFileInputRef.value?.click();
};

const onJmxFileInputChange = (e: Event) => {
	const file = (e.target as HTMLInputElement).files?.[0];
	if (!file || !currentUpdateRow.value) return;
	const ok = handleBeforeUpload(file);
	if (ok !== false) handleUpdate({ file }, currentUpdateRow.value);
	(e.target as HTMLInputElement).value = '';
	currentUpdateRow.value = null;
};

// ======================== 引用文件修改抽屉 ========================
const refDrawerVisible    = ref(false);
const refDrawerRow        = ref<any>(null);
const refDrawerFileName   = ref('');
const refDrawerSelectedIds = ref<number[]>([]);
const nonJmxFiles         = ref<{ id: number; name: string }[]>([]);
const refFilesLoading     = ref(false);
const refSaving           = ref(false);
const refFilterQuery      = ref('');

const filteredNonJmxFiles = computed(() => {
	const q = refFilterQuery.value.trim().toLowerCase();
	if (!q) return nonJmxFiles.value;
	return nonJmxFiles.value.filter(f =>
		String(f.id).includes(q) || f.name.toLowerCase().includes(q)
	);
});

const filterRefFiles = (q: string) => { refFilterQuery.value = q; };

const openRefDrawer = async (row: any) => {
	refDrawerRow.value = row;
	refDrawerFileName.value = row.name;
	refDrawerSelectedIds.value = [...(row.ref_file_ids || [])];
	refDrawerVisible.value = true;
	// 仅首次加载，之后复用缓存（数据文件变动可刷新页面）
	if (nonJmxFiles.value.length === 0) {
		refFilesLoading.value = true;
		try {
			const res: any = await perfApi.getFileList({ page: 1, page_size: 100 });
			const all: any[] = res.data?.items ?? [];
			nonJmxFiles.value = all
				.filter((f: any) => f.file_type !== 'jmx')
				.map((f: any) => ({ id: f.id, name: f.file_name }));
		} catch (e: any) {
			ElMessage.error(e.message || '加载数据文件列表失败');
		} finally {
			refFilesLoading.value = false;
		}
	}
};

const saveRefDrawer = async () => {
	if (!refDrawerRow.value) return;
	refSaving.value = true;
	try {
		await perfApi.setFileRefs(refDrawerRow.value.id, {
			ref_file_ids: refDrawerSelectedIds.value,
			file_name: refDrawerFileName.value || undefined,
		});
		refDrawerVisible.value = false;
		handleQuery();
		ElMessage.success('引用关系更新成功');
	} catch (e: any) {
		ElMessage.error(e.message || '更新引用关系失败');
	} finally {
		refSaving.value = false;
	}
};

// ======================== 分发 ========================
const distributeDrawerVisible = ref(false);
const distributeRow    = ref<any>(null);
const distributeForm   = reactive({
	type: 'shared',
	machineCategory: '2',
	standaloneWorkerId: null as number | null,
	workerCount: 1,
	clearWorkerCount: 1,
});

watch(() => distributeForm.type, (type) => {
	if (type === 'split' && distributeForm.workerCount < 2) {
		distributeForm.workerCount = 2;
	}
	if (type === 'split' && distributeForm.machineCategory === '3') {
		distributeForm.machineCategory = '2';
		distributeForm.standaloneWorkerId = null;
	}
});
const machineTypeOptions = ref<{ label: string; value: string }[]>([]);
const standaloneMachines = ref<any[]>([]);
const maxSlaveCount      = ref(0);
const machinesLoading    = ref(false);
const distributePhase  = ref<'form' | 'progress'>('form');  // 抽屉当前阶段
const distributeStreaming = ref(false);                     // SSE 流式请求进行中，禁止关闭对话框
const distributeProgressVisible = ref(false);              // 进度对话框可见性

// 进度状态数据（SSE 事件实时填充）
const masterStatus     = ref<any>(null);       // master 事件
const distributeMethod = ref('');              // method 事件描述（方案A/B/C）
const connectionInfo   = ref<{ auth_method: string; tunnel_type: string } | null>(null); // 连接方式
const nodeMap = ref<Record<number, any>>({});  // 节点状态 Map（machine_id → 状态对象，保证响应式）
const doneResult       = ref<any>(null);       // done 事件汇总数据
const expandedNodes    = ref(new Set<number>());  // 展开详情的节点 ID 集合（-1 = Master）
// 方案B：Master 拉取 MinIO 的全局进度
const masterPullProgress = ref({ visible: false, pct: 0, message: '' });
// 方案C：平台机中转 MinIO 下载行（minio_connect/minio_download 阶段填充，持久显示）
const platformMinioRow = ref<null | { status: string; conn_status: string; progress: number; message: string }>(null);

const toggleExpand = (id: number) => {
	const s = new Set(expandedNodes.value);
	s.has(id) ? s.delete(id) : s.add(id);
	expandedNodes.value = s;
};

const loadMachinesForDistribute = async () => {
	machinesLoading.value = true;
	try {
		const res: any = await perfApi.getMachineList({ status: 1 });
		const machines: any[] = res.data?.items || [];
		standaloneMachines.value = machines.filter((m: any) => m.machine_type === 3);
		maxSlaveCount.value = machines.filter((m: any) => m.machine_type === 2).length;
	} catch (e: any) {
		ElMessage.error(e.message || '获取压力机列表失败');
	} finally {
		machinesLoading.value = false;
	}
};

const onMachineCategoryChange = () => {
	if (distributeForm.machineCategory === '3') {
		distributeForm.type = 'shared';
	}
	distributeForm.standaloneWorkerId = null;
};

// 清除 JMX 文件分发记录（不SSH删除机器文件，仅重置DB元数据）
const clearingJmxDistIds = ref<Set<number>>(new Set());

const handleClearJmxDist = async (row: any) => {
	try {
		clearingJmxDistIds.value.add(row.id);
		await perfApi.setFileRefs(row.id, { ref_file_ids: row.ref_file_ids ?? [], clear_dist: true });
		row.distribute_type = null;
		row.workers = 0;
		row.distributed_at = null;
		row.remark = null;
		ElMessage.success('已清除分发记录');
	} catch (e: any) {
		ElMessage.error(e.message || '清除失败');
	} finally {
		clearingJmxDistIds.value.delete(row.id);
	}
};

const handleDistribute = (cmd: string, row: any) => {
	if (cmd === 'open-dialog') {
		// 重置表单阶段状态，打开抽屉
		distributeRow.value = row;
		distributeForm.type = 'shared';
		distributeForm.machineCategory = '2';
		distributeForm.standaloneWorkerId = null;
		distributeForm.workerCount = 1;
		distributePhase.value = 'form';
		masterStatus.value = null;
		distributeMethod.value = '';
		connectionInfo.value = null;
		nodeMap.value = {};
		doneResult.value = null;
		distributeDrawerVisible.value = true;
		loadMachinesForDistribute();
	} else if (cmd === 'clear') {
		// 直接打开抽屉，预选清除分发，无需确认弹窗
		distributeRow.value = row;
		distributeForm.type = 'clear';
		distributeForm.machineCategory = '2';
		distributeForm.standaloneWorkerId = null;
		distributeForm.workerCount = 1;
		distributeForm.clearWorkerCount = row.workers || 1;
		distributePhase.value = 'form';
		masterStatus.value = null;
		distributeMethod.value = '';
		connectionInfo.value = null;
		nodeMap.value = {};
		doneResult.value = null;
		distributeDrawerVisible.value = true;
	}
};

/** 节点进度条悬停tooltip文字 */
const getNodeStageLabel = (node: any): string => {
	if (node.status === 'pending' && !node.stage) return '等待分发';
	if (node.status === 'success') return '分发成功';
	if (node.status === 'failed')  return '分发失败';
	const pct = node.progress || 0;
	const stageMap: Record<string, string> = {
		slave_pulling:  'Slave拉取MinIO文件',
		master_pulling: 'Master拉取MinIO文件',
		sftp_start:     'SSH已连接，等待传输开始',
		master_pushing: `Master上传到Slave  ${pct}%`,
	};
	return stageMap[node.stage as string] || `传输中  ${pct}%`;
};

/** SSE 事件处理：根据 type 字段更新 nodeMap，驱动进度面板实时渲染 */
const handleDistributeEvent = (evtData: any) => {
	switch (evtData.type) {
		case 'master':
			// 更新 Master 连接状态（connecting→success/failed），记录认证方式
			masterStatus.value = evtData;
			if (evtData.auth_method) {
				connectionInfo.value = { auth_method: evtData.auth_method, tunnel_type: connectionInfo.value?.tunnel_type ?? '' };
			}
			break;
		case 'node_pending':
			// 预渲染节点行，status=pending，conn_status 为空表示尚未建连
			nodeMap.value = {
				...nodeMap.value,
				[evtData.machine_id]: { ...evtData, status: 'pending', progress: 0, conn_status: '', stage: '' },
			};
			break;
		case 'node_progress':
			// 更新进度：status 置为 running；conn_status 置为 connected（有进度说明连接已成功）
			if (nodeMap.value[evtData.machine_id]) {
				nodeMap.value = {
					...nodeMap.value,
					[evtData.machine_id]: {
						...nodeMap.value[evtData.machine_id],
						progress: evtData.progress,
						status: 'running',
						conn_status: 'connected',
						stage: evtData.stage || '',
					},
				};
			}
			break;
		case 'method':
			// 展示分发方案（方案A/B），记录隧道类型
			distributeMethod.value = evtData.message;
			if (evtData.tunnel_type) {
				connectionInfo.value = { auth_method: connectionInfo.value?.auth_method ?? '', tunnel_type: evtData.tunnel_type };
			}
			// 方案A：Slave 正在直拉 MinIO；方案B：Master 正在拉取 MinIO，节点在等待
			// 两种情况下节点均无 node_progress，更新 stage 让 tooltip 有意义
			if (evtData.use_direct || evtData.use_master_relay) {
				const stageVal = evtData.use_direct ? 'slave_pulling' : 'master_pulling';
				const updated: Record<number, any> = {};
				for (const [id, node] of Object.entries(nodeMap.value)) {
					updated[Number(id)] = { ...(node as any), stage: stageVal };
				}
				nodeMap.value = { ...nodeMap.value, ...updated };
			}
			break;
		case 'node_done':
			// 完成：progress=100，status=success/failed；
			// conn_status：连接失败时 failed，否则 connected
			if (nodeMap.value[evtData.machine_id]) {
				nodeMap.value = {
					...nodeMap.value,
					[evtData.machine_id]: {
						...nodeMap.value[evtData.machine_id],
						...evtData,
						progress: 100,
						status: evtData.success ? 'success' : 'failed',
						conn_status: evtData.failure_stage === 'connect' ? 'failed' : 'connected',
					},
				};
			}
			break;
		case 'progress':
			// 方案C：平台机 MinIO 阶段 → 更新持久行（不会因 pct=100 消失）
			if (evtData.stage === 'minio_connect') {
				platformMinioRow.value = { status: 'running', conn_status: 'connecting', progress: 0, message: evtData.message || '正在连接 MinIO...' };
			} else if (evtData.stage === 'minio_download') {
				const pct = evtData.progress ?? 0;
				platformMinioRow.value = { status: pct >= 100 ? 'success' : 'running', conn_status: 'connected', progress: pct, message: evtData.message || `下载中 ${pct}%` };
			// 方案B：Master 拉取 MinIO → 进度条（下载完成后自动隐藏）
			} else if (evtData.stage === 'master_pull') {
				masterPullProgress.value = { visible: (evtData.progress ?? 100) < 100, pct: evtData.progress ?? 0, message: evtData.message || 'Master 拉取中...' };
			}
			break;
		case 'done':
			// 全部完成，显示汇总统计，隐藏 Master 拉取进度条
			doneResult.value = evtData;
			masterPullProgress.value = { visible: false, pct: 100, message: '' };
			distributeStreaming.value = false;
			break;
		case 'error':
			ElMessage.error(evtData.message);
			masterPullProgress.value = { visible: false, pct: 0, message: '' };
			distributeStreaming.value = false;
			break;
	}
};

/** 点击"确认分发"：关闭抽屉，打开进度对话框并开始消费 SSE 流 */
const startDistribute = async () => {
	if (!distributeRow.value) return;

	// 前置校验
	if (distributeForm.machineCategory === '3' && distributeForm.type !== 'clear' && !distributeForm.standaloneWorkerId) {
		ElMessage.warning('请选择目标压力机');
		return;
	}
	if (distributeForm.type === 'clear') {
		const maxWorkers = distributeRow.value.workers || 0;
		if (distributeForm.clearWorkerCount > maxWorkers) {
			ElMessage.warning(`清除数量不能超过已分发数量（${maxWorkers} 台）`);
			return;
		}
	}

	// 关闭表单抽屉，打开进度对话框（先设 streaming=true 避免抽屉一瞬间显示关闭按钮）
	distributeStreaming.value = true;
	distributeDrawerVisible.value = false;
	distributeProgressVisible.value = true;

	// 重置进度状态
	distributePhase.value = 'progress';
	masterStatus.value = null;
	distributeMethod.value = '';
	connectionInfo.value = null;
	nodeMap.value = {};
	doneResult.value = null;
	masterPullProgress.value = { visible: false, pct: 0, message: '' };
	// 单机共享/分割分发（方案C）：页面打开即预渲染平台机中转行，不等 SSE 事件
	platformMinioRow.value = (distributeForm.machineCategory === '3' && distributeForm.type !== 'clear')
		? { status: 'running', conn_status: 'connecting', progress: 0, message: '正在连接 MinIO...' }
		: null;
	expandedNodes.value = new Set();

	const row = distributeRow.value;
	let streamFn: () => Promise<Response>;
	if (distributeForm.type === 'clear') {
		streamFn = () => perfApi.clearDistributeStream({ file_id: row.id, worker_count: distributeForm.clearWorkerCount });
	} else if (distributeForm.machineCategory === '3') {
		// 单机：强制 worker_count=1，走共享分发接口
		streamFn = () => perfApi.shareDistributeStream({ file_id: row.id, worker_count: 1, machine_type: 3 });
	} else {
		const fn = distributeForm.type === 'shared' ? perfApi.shareDistributeStream : perfApi.splitDistributeStream;
		streamFn = () => fn({ file_id: row.id, worker_count: distributeForm.workerCount, machine_type: 2 });
	}

	try {
		const response = await streamFn();

		if (!response.ok) {
			const errText = await response.text();
			throw new Error(`请求失败 (${response.status}): ${errText}`);
		}

		const reader  = response.body!.getReader();
		const decoder = new TextDecoder();
		let buffer    = '';

		// 逐块读取 SSE 流，按 \n\n 分割事件
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const parts = buffer.split('\n\n');
			buffer = parts.pop()!;              // 未完整的尾部留到下次拼接
			for (const part of parts) {
				const line = part.trim();
				if (!line.startsWith('data: ')) continue;
				try {
					handleDistributeEvent(JSON.parse(line.slice(6)));
				} catch {
					// 忽略单条解析错误，不中断整个流
				}
			}
		}
		handleQuery();  // 分发结束后刷新文件列表（dist_status 更新）
	} catch (e: any) {
		ElMessage.error(e.message || '分发请求失败');
	} finally {
		// 无论流正常结束、Master失败提前return、还是异常，都重置 streaming 状态
		distributeStreaming.value = false;
	}
};

// ======================== 下载 ========================
const selectingDownload = ref(false);
const selectedDownloadIds = ref<Set<number>>(new Set());

const enterDownloadMode = () => {
	selectingDownload.value = true;
	selectedDownloadIds.value = new Set();
};

const cancelDownload = () => {
	selectingDownload.value = false;
	selectedDownloadIds.value = new Set();
};

const toggleDownload = (id: number, val: boolean) => {
	const set = new Set(selectedDownloadIds.value);
	val ? set.add(id) : set.delete(id);
	selectedDownloadIds.value = set;
};

const startDownload = () => {
	if (selectedDownloadIds.value.size === 0) {
		ElMessage.warning('请至少勾选一个文件');
		return;
	}
	const selected = fileList.value.filter((r) => selectedDownloadIds.value.has(r.id));
	selected.forEach((r) => handleDownload(r));
	cancelDownload();
};

const handleDownload = async (row: any) => {
	try {
		const res: any = await perfApi.getDownloadUrl(row.id);
		const { download_url, file_name } = res.data;
		const a = document.createElement('a');
		a.href = download_url;
		a.download = file_name;
		a.target = '_blank';
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
	} catch (e: any) {
		ElMessage.error(e.message || `「${row.name}」下载链接获取失败`);
	}
};

// ======================== 删除 ========================
const handleDelete = (row: any) => {
	if (row.status === 'running') {
		ElMessage.warning(`文件「${row.name}」当前正在压测任务中使用，无法删除，请等待压测任务结束后再操作。`);
		return;
	}
	if (row.status === 'referenced') {
		ElMessage.warning(`文件「${row.name}」已被 JMX 脚本引用，欲删除需要在 JMX 编辑页面解除引用。`);
		return;
	}
	if (row.status === 'linked') {
		ElMessage.warning(`文件「${row.name}」已被引用且关联了压测场景，欲删除需先解除场景关联，再在 JMX 编辑页面移除引用。`);
		return;
	}
	ElMessageBox.confirm(`确定要删除文件「${row.name}」吗？`, '提示', {
		type: 'warning',
		confirmButtonText: '确定',
		cancelButtonText: '取消',
	}).then(() => doDelete(row)).catch(() => {});
};

// ======================== 删除 ========================
const deletingIds = ref(new Set<number>());

const doDelete = async (row: any) => {
	deletingIds.value.add(row.id);
	try {
		await perfApi.deleteFile(row.id);
		handleQuery();
		ElMessage.success('删除成功');
	} catch (e: any) {
		ElMessage.error(e.message || '删除失败');
	} finally {
		deletingIds.value.delete(row.id);
		deletingIds.value = new Set(deletingIds.value);
	}
};

// ======================== 初始化 ========================
onMounted(async () => {
	if (route.query.name) {
		query.name = route.query.name as string;
	}
	// 从字典表加载文件类型和文件状态选项
	// perf_file_type：value 用 dict_label.lower()（扩展名字符串），供后端 file_type 参数过滤
	// perf_file_status：value 用 dict_value（数字字符串），供后端 ref_status 参数过滤
	const [ftOpts, fsOpts, mtOpts] = await Promise.all([
		getDictOptions('perf_file_type'),
		getDictOptions('perf_file_status'),
		getDictOptions('perf_machine_type'),
	]);
	fileTypeOptions.value = ftOpts.map((o) => ({ label: o.label, value: o.label.toLowerCase() }));
	fileStatusOptions.value = fsOpts.map((o) => ({ label: o.label, value: String(o.value) }));
	// 同步构建状态文字 map：字典 value（数字）→ 内部字符串键 → 字典 label
	const labelMap: Record<string, string> = {};
	fsOpts.forEach((o: any) => {
		const strKey = STATUS_STR_MAP[Number(o.value)];
		if (strKey) labelMap[strKey] = o.label;
	});
	dynamicStatusLabelMap.value = labelMap;
	machineTypeOptions.value = mtOpts
		.filter((o) => String(o.value) !== '1')
		.map((o) => ({ label: o.label, value: String(o.value) }));
	// 从后端参数配置动态获取代理上传大小限制，获取失败时保持默认值 100MB
	try {
		const paramRes: any = await perfApi.getParamList({ name: 'PROXY_UPLOAD_MAX_BYTES', page_size: 1 });
		const item = paramRes?.data?.items?.[0];
		if (item?.param_key === 'PROXY_UPLOAD_MAX_BYTES' && item.param_value) {
			const mb = parseInt(String(item.param_value).match(/\d+/)?.[0] ?? '100', 10);
			if (!isNaN(mb) && mb > 0) proxyUploadMaxBytes.value = mb * 1024 * 1024;
		}
	} catch { /* 保持默认值 */ }
	handleQuery();
});
</script>

<style scoped lang="scss">
.perf-files-container {
	padding: 10px 10px 20px 10px;

	:deep(.el-card__body) {
		padding: 10px 10px 20px 10px;
	}

	// ---- 全局控件字体统一 ----
	:deep(.el-button > span) {
		display: inline-flex !important;
		align-items: center !important;
		line-height: 1 !important;
	}

	:deep(.el-input__inner),
	:deep(.el-textarea__inner) {
		font-size: 13.5px;
	}

	// 输入框与下拉框均使用 el-config-provider 全局 size 控制高度，不单独覆盖

	:deep(.el-select__placeholder),
	:deep(.el-select__selected-item) {
		font-size: 13.5px;
	}

	.toolbar {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;

		.toolbar-left {
			display: flex;
			align-items: center;
			gap: 10px;
			flex-wrap: wrap;
		}

		.toolbar-right {
			display: flex;
			align-items: center;
			gap: 10px;

			:deep(.el-upload) {
				display: inline-flex;
				align-items: center;
			}
		}
	}

	:deep(.el-tag) {
		font-size: 13px;
		padding: 0 8px;
	}

	.tip-icon {
		margin-left: 4px;
		color: var(--el-text-color-secondary);
		cursor: help;
		vertical-align: middle;
		font-size: 13.5px;

		&:hover {
			color: var(--el-color-primary);
		}
	}

	.file-type-badge {
		display: inline-block;
		padding: 1px 5px;
		border-radius: 3px;
		font-size: 12px;
		font-weight: 600;
		color: #fff;
		margin-right: 6px;
		vertical-align: middle;
		line-height: 18px;
	}

	:deep(.el-table) {
		font-size: 13.5px;

		// 表头背景：使用 element 填充色变量，自动适配深色/浅色
		.el-table__header th {
			font-size: 13.5px;
			background-color: var(--el-fill-color-light);
		}

		// 让带 ? 图标的表头文案与图标垂直居中
		.el-table__header th .cell {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			white-space: nowrap;
		}

		.el-table__cell {
			padding: 10px 0;
		}

		// 操作列背景：使用 element fill-color-light 变量，浅色 #f5f7fa 明显灰，深色由 dark.scss 强制为 #303030
		td.operation-col {
			background-color: var(--el-fill-color-light) !important;
		}
	}

	.file-name-text {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		max-width: calc(100% - 52px);
		display: inline-block;
		vertical-align: middle;
	}

	// 选择引用模式下的复选框：只放大视觉方块，不改变元素高度，不撑高行
	:deep(.el-table .el-table__cell .el-checkbox) {
		height: auto !important;
		display: inline-flex;
		align-items: center;
	}

	:deep(.el-table .el-table__cell .el-checkbox__inner) {
		transform: scale(1.3);
		transform-origin: center;
	}

	.jmx-ref-text {
		color: var(--el-color-primary);
		font-size: 13.5px;
		cursor: default;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		display: inline-block;
		max-width: 100%;
		vertical-align: middle;
	}

	.text-placeholder {
		color: var(--el-text-color-placeholder);
	}

	// 分发失败备注：使用 danger 主题色变量
	.dist-fail-remark {
		color: var(--el-color-danger);
		font-size: 12px;
	}

	// 数据文件已更新但未重新分发：红色警告
	.dist-outdated {
		color: var(--el-color-danger);
		white-space: nowrap;
		display: inline-flex;
		align-items: center;
		gap: 3px;
		cursor: default;
	}
	.dist-warn-icon {
		font-size: 13px;
		flex-shrink: 0;
	}

	.normal-remark-text {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		color: var(--el-color-danger);
	}

	.action-btns {
		display: flex;
		align-items: center;
		justify-content: center;
		flex-wrap: nowrap;

		:deep(.el-button) {
			padding: 0 4px;
			font-weight: 600;

			.el-icon {
				margin-right: 2px;
			}
		}

		// 确定按钮（实心）覆盖 padding
		:deep(.el-button:not(.is-text)) {
			padding: 0 8px;
		}

		.update-slot {
			display: inline-flex;
			align-items: center;
			justify-content: center;
			gap: 2px;
		}

		:deep(.el-dropdown-menu__item) {
			font-size: 13.5px;
		}
	}

	.pagination {
		margin-top: 16px;
		display: flex;
		justify-content: flex-end;
	}

	.distribute-drawer-form {
		padding: 16px 4px 0;

		:deep(.el-form-item__label),
		:deep(.el-form-item__content),
		:deep(.el-radio__label),
		:deep(.el-input__inner),
		:deep(.el-tag) {
			font-size: 13.5px;
		}

		.distribute-filename {
			font-size: 13.5px;
			font-weight: 600;
			color: var(--el-text-color-primary);
			word-break: break-all;
		}

		// 分发说明：黄色提示框，使用 warning 主题色变量自动适配深色
		.distribute-type-desc {
			display: inline-flex;
			align-items: flex-start;
			gap: 6px;
			font-size: 13.5px;
			color: var(--el-color-warning);
			background: var(--el-color-warning-light-9);
			border: 1px solid var(--el-color-warning-light-7);
			border-radius: 4px;
			padding: 6px 10px;
			line-height: 1.6;
		}

		:deep(.desc-form-item.el-form-item) {
			margin-top: -12px;
			margin-bottom: 18px;
		}

		:deep(.notice-form-item.el-form-item) {
			margin-bottom: 0;
		}

		:deep(.desc-form-item .el-form-item__content) {
			line-height: 1.4;
			padding-top: 0;
		}

		.unit-label {
			margin-left: 8px;
			color: var(--el-text-color-regular);
			font-size: 13.5px;
		}
	}

	// 分发须知：红色提示框，使用 danger 主题色变量自动适配深色
	.distribute-notice {
		width: 400px;
		margin: 0;
		padding: 10px 14px;
		border: 1px solid var(--el-color-danger-light-7);
		border-radius: 6px;
		background: var(--el-color-danger-light-9);
		color: var(--el-color-danger);
		font-size: 12.5px;
		line-height: 1.8;

		ul {
			margin: 0;
			padding-left: 18px;

			li { margin-bottom: 2px; }
			li:last-child { margin-bottom: 0; }
			b { font-weight: 600; }
		}
	}

	.drawer-footer {
		display: flex;
		justify-content: flex-end;
		gap: 10px;
		margin-top: 24px;
		margin-right: 50px;
		padding-top: 16px;
		border-top: 1px solid var(--el-border-color-lighter);
	}

	.dist-result-panel {
		padding: 0 4px;
		font-size: 13.5px;


		// ── 分发方案标识 ──
		.dist-method-label {
			font-size: 12px;
			color: var(--el-text-color-secondary);
			padding: 5px 4px 3px;
			border-bottom: 1px solid var(--el-border-color-extra-light);
			margin-bottom: 4px;
		}

		// ── Master 拉取进度条（方案B）──
		.master-pull-bar {
			display: flex;
			align-items: center;
			gap: 8px;
			padding: 6px 4px 4px;
			margin-bottom: 4px;
			border-bottom: 1px solid var(--el-border-color-extra-light);

			.master-pull-label {
				font-size: 12px;
				color: var(--el-text-color-secondary);
				white-space: nowrap;
				flex-shrink: 0;
				max-width: 220px;
				overflow: hidden;
				text-overflow: ellipsis;
			}

			.master-pull-pct {
				font-size: 12px;
				color: var(--el-color-primary);
				flex-shrink: 0;
			}
		}

		// ── 列头（带背景色，全局唯一一行）──
		.dist-col-header {
			display: grid;
			grid-template-columns: 22px 1fr 52px 130px 32px;
			padding: 6px 0;
			color: var(--el-text-color-secondary);
			font-size: 12px;
			font-weight: 500;
			background: var(--el-fill-color-light);
			border-radius: 4px;
			margin-bottom: 2px;

			.col-name { padding-left: 4px; }
			.col-chunk { text-align: center; font-size: 11px; color: var(--el-text-color-secondary); }
			.col-connect, .col-dist { text-align: center; }
		}

		// ── 数据行 ──
		.dist-row {
			display: grid;
			grid-template-columns: 22px 1fr 52px 130px 32px;
			align-items: center;
			padding: 9px 0;
			border-bottom: 1px solid var(--el-border-color-extra-light);

			&:last-child { border-bottom: none; }

			.col-status {
				display: flex;
				align-items: center;
				justify-content: center;
				font-size: 15px;
			}

			.row-name {
				font-weight: 500;
				overflow: hidden;
				text-overflow: ellipsis;
				white-space: nowrap;
				cursor: default;
				color: var(--el-text-color-primary);

				.row-ip {
					color: var(--el-text-color-secondary);
					font-size: 12px;
					font-weight: 400;
				}
			}

			.col-chunk {
				display: flex;
				align-items: center;
				justify-content: center;
				font-size: 11px;
				color: var(--el-text-color-secondary);
			}

			.col-connect, .col-dist {
				display: flex;
				align-items: center;
				justify-content: center;
				font-size: 16px;
			}

			.col-expand {
				display: flex;
				align-items: center;
				justify-content: center;

				.expand-btn {
					font-size: 14px;
					color: var(--el-text-color-secondary);
					cursor: pointer;
					&:hover { color: var(--el-color-primary); }
				}
			}
		}

		// ── 展开详情行 ──
		.expand-detail {
			padding: 8px 12px 10px;
			margin: 0 0 2px;
			background: var(--el-fill-color-light);
			border-radius: 4px;
			font-size: 12.5px;
			color: var(--el-color-danger);
			line-height: 1.6;
			word-break: break-all;
			border-bottom: 1px solid var(--el-border-color-extra-light);
		}

		// ── 汇总 ──
		.dist-summary {
			margin-top: 4px;
			text-align: center;
		}

		// ── 状态图标颜色：使用 element 主题色变量自动适配深色 ──
		.icon-ok   { color: var(--el-color-success); }
		.icon-fail { color: var(--el-color-danger); }
		.icon-disabled { color: var(--el-disabled-text-color); font-size: 15px; }

		.dist-progress-wrap {
			display: flex;
			flex-direction: row;
			align-items: center;
			gap: 4px;
			width: 100%;
		}
		.dist-pct-text {
			font-size: 11px;
			color: var(--el-color-primary);
			line-height: 1;
		}
	}

	// Loading 图标旋转动画
	.spin-icon { animation: spin 1s linear infinite; color: var(--el-color-primary); }
}

@keyframes spin { to { transform: rotate(360deg); } }
</style>

<style lang="scss">
/* 按钮内 slot wrapper span 设为 flex，使图标与文字垂直居中 */
.perf-files-container .el-button > span {
	display: inline-flex !important;
	align-items: center !important;
	line-height: 1 !important;
}

/* 文件管理操作列下拉菜单（teleport 到 body，需非 scoped 覆盖） */
.perf-files-dropdown .el-dropdown-menu__item {
	font-size: 13.5px;
}

/* 分发/进度抽屉 body 区域超长时可滚动 */
.distribute-drawer .el-drawer__body {
	overflow-y: auto;
}

/* 分发弹窗提示块：深色模式下背景压暗 */
[data-theme='dark'] .distribute-type-desc {
	background: #1e1e1e !important;
	border-color: #3a3a3a !important;
}
[data-theme='dark'] .distribute-notice {
	background: #1e1e1e !important;
	border-color: #3a3a3a !important;
}

/* 引用修改抽屉：统一 13.5px 字号 */
.ref-files-drawer .el-drawer__body {
	overflow-y: auto;
}
.ref-files-drawer .el-form-item__label,
.ref-files-drawer .el-input__inner,
.ref-files-drawer .el-select__placeholder,
.ref-files-drawer .el-select__selected-item,
.ref-files-drawer .el-tag {
	font-size: 13.5px;
}
</style>