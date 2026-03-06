<template>
  <div class="ai-browser-cases-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>AI用例管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增用例
            </el-button>
            <el-button type="success" @click="handleImportTestcase">
              <el-icon><Download /></el-icon>
              从测试用例导入
            </el-button>
            <el-button type="warning" @click="handleImportExcel">
              <el-icon><Upload /></el-icon>
              导入Excel
            </el-button>
            <el-button 
              type="info" 
              :disabled="selectedCases.length === 0"
              @click="handleBatchExecute"
            >
              <el-icon><VideoPlay /></el-icon>
              批量执行 ({{ selectedCases.length }})
            </el-button>
            <el-button 
              type="danger" 
              :disabled="selectedCases.length === 0"
              @click="handleBatchDelete"
            >
              <el-icon><Delete /></el-icon>
              批量删除 ({{ selectedCases.length }})
            </el-button>
          </div>
        </div>
      </template>

      <!-- 筛选条件 -->
      <el-form :inline="true" :model="queryForm" class="query-form">
        <el-form-item label="项目">
          <el-select 
            v-model="queryForm.source_project_id" 
            placeholder="请选择项目" 
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="模块">
          <el-select 
            v-model="queryForm.source_module_id" 
            :key="`module-${queryForm.source_project_id || 'none'}`"
            placeholder="请选择模块" 
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="module in moduleList"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select 
            v-model="queryForm.status" 
            placeholder="请选择状态" 
            clearable
            style="width: 150px"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="激活" value="active" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="来源">
          <el-select 
            v-model="queryForm.source_type" 
            placeholder="请选择来源" 
            clearable
            style="width: 150px"
          >
            <el-option label="手动创建" value="manual" />
            <el-option label="Excel导入" value="import" />
            <el-option label="测试用例" value="testcase" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table 
        :data="tableData" 
        v-loading="loading" 
        border 
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="case_id" label="用例编号" width="120" />
        <el-table-column prop="title" label="用例标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source_type" label="来源" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ getSourceTypeLabel(row.source_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_execution_status" label="最后执行" width="100">
          <template #default="{ row }">
            <el-tag 
              v-if="row.last_execution_status"
              :type="getExecutionStatusType(row.last_execution_status)" 
              size="small"
            >
              {{ getExecutionStatusLabel(row.last_execution_status) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="execution_count" label="执行次数" width="100" align="center" />
        <el-table-column prop="last_execution_time" label="最后执行时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.last_execution_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="380" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-dropdown @command="(command) => handleExecute(row, command)">
              <el-button type="success" size="small">
                执行<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="headless">无头执行</el-dropdown-item>
                  <el-dropdown-item command="headed">有头执行</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button type="info" size="small" @click="handleViewRecords(row)">记录</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="queryForm.page"
        v-model:page-size="queryForm.page_size"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="getList"
        @current-change="getList"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 用例详情/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="用例编号" prop="case_id">
          <el-input v-model="form.case_id" placeholder="请输入用例编号" />
        </el-form-item>
        
        <el-form-item label="用例标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入用例标题" />
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" placeholder="请选择优先级">
            <el-option label="P0" value="P0" />
            <el-option label="P1" value="P1" />
            <el-option label="P2" value="P2" />
            <el-option label="P3" value="P3" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="用例描述">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入用例描述"
          />
        </el-form-item>
        
        <el-form-item label="前置条件">
          <el-input 
            v-model="form.precondition" 
            type="textarea" 
            :rows="2"
            placeholder="请输入前置条件"
          />
        </el-form-item>
        
        <el-form-item label="测试步骤" prop="test_steps">
          <div class="steps-container">
            <div 
              v-for="(step, index) in form.test_steps" 
              :key="index"
              class="step-item"
            >
              <div class="step-header">
                <span class="step-num">步骤 {{ index + 1 }}</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  text
                  @click="removeStep(index)"
                >
                  删除
                </el-button>
              </div>
              <el-input 
                v-model="step.description" 
                placeholder="步骤描述"
                style="margin-bottom: 8px"
              />
              <el-input 
                v-model="step.expected" 
                placeholder="该步骤的预期结果"
              />
            </div>
            <el-button type="primary" @click="addStep" style="width: 100%">
              <el-icon><Plus /></el-icon>
              添加步骤
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="整体预期结果">
          <el-input 
            v-model="form.expected_result" 
            type="textarea" 
            :rows="3"
            placeholder="请输入整体预期结果（可选）"
          />
        </el-form-item>
        
        <el-form-item label="执行模式">
          <el-radio-group v-model="form.execution_mode">
            <el-radio label="headless">无头执行</el-radio>
            <el-radio label="headed">有头执行</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="超时时间(秒)">
          <el-input-number v-model="form.timeout" :min="60" :max="3600" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog 
      v-model="viewDialogVisible" 
      title="用例详情"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用例编号">
          {{ viewCaseData.case_id }}
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag :type="getPriorityType(viewCaseData.priority)" size="small">
            {{ viewCaseData.priority }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="用例标题" :span="2">
          {{ viewCaseData.title || viewCaseData.name }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(viewCaseData.status)" size="small">
            {{ getStatusLabel(viewCaseData.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="来源">
          <el-tag size="small">{{ getSourceTypeLabel(viewCaseData.source_type) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="执行次数">
          {{ viewCaseData.execution_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="最后执行状态">
          <el-tag 
            v-if="viewCaseData.last_execution_status"
            :type="getExecutionStatusType(viewCaseData.last_execution_status)" 
            size="small"
          >
            {{ getExecutionStatusLabel(viewCaseData.last_execution_status) }}
          </el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="最后执行时间" :span="2">
          {{ formatDateTime(viewCaseData.last_execution_time) }}
        </el-descriptions-item>
        <el-descriptions-item label="用例描述" :span="2">
          {{ viewCaseData.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="任务描述" :span="2">
          <div style="white-space: pre-wrap;">{{ viewCaseData.task_description || '-' }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(viewCaseData.creation_date) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(viewCaseData.updation_date) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <template #footer>
        <el-button @click="viewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleEdit(viewCaseData); viewDialogVisible = false">
          编辑
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量执行对话框 -->
    <el-dialog 
      v-model="batchDialogVisible" 
      title="批量执行"
      width="500px"
    >
      <el-form :model="batchForm" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="batchForm.task_name" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="执行模式">
          <el-radio-group v-model="batchForm.execution_mode">
            <el-radio label="headless">无头执行</el-radio>
            <el-radio label="headed">有头执行</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="并行数量">
          <el-input-number v-model="batchForm.parallel_count" :min="1" :max="5" />
        </el-form-item>
        
        <el-form-item label="选中用例">
          <el-tag>{{ selectedCases.length }} 个用例</el-tag>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitBatchExecute">开始执行</el-button>
      </template>
    </el-dialog>

    <!-- 从测试用例导入对话框 -->
    <el-dialog 
      v-model="importDialogVisible" 
      title="从测试用例导入"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="importForm" label-width="100px">
        <el-form-item label="选择项目">
          <el-select 
            v-model="importForm.project_id" 
            placeholder="请选择项目" 
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="project in importProjectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择模块">
          <el-tree
            v-if="importModuleTree.length > 0"
            :data="importModuleTree"
            show-checkbox
            node-key="id"
            :props="{ children: 'children', label: 'name' }"
            @check="(data, checked) => {
              selectedModules = checked.checkedKeys
            }"
            style="max-height: 400px; overflow-y: auto; border: 1px solid #dcdfe6; border-radius: 4px; padding: 10px"
          />
          <el-empty 
            v-else 
            description="请先选择项目" 
            :image-size="80"
          />
        </el-form-item>
        
        <el-form-item>
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #title>
              已选择 {{ selectedModules.length }} 个模块，将导入这些模块下的所有测试用例
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="submitImport"
          :loading="importLoading"
          :disabled="selectedModules.length === 0"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行监控对话框 -->
    <el-dialog
      v-model="monitorDialogVisible"
      title="AI执行监控"
      width="80%"
      :close-on-click-modal="false"
      @close="handleMonitorDialogClose"
    >
      <div class="execution-monitor">
        <!-- 状态信息 -->
        <el-descriptions :column="3" border>
          <el-descriptions-item label="用例名称">
            {{ currentMonitorCase?.title || currentMonitorCase?.name }}
          </el-descriptions-item>
          <el-descriptions-item label="执行状态">
            <el-tag :type="getMonitorStatusType()">
              {{ getMonitorStatusText() }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行进度">
            {{ monitorData.progress }} 步
          </el-descriptions-item>
          <el-descriptions-item label="执行耗时">
            {{ monitorData.duration ? monitorData.duration.toFixed(2) : 0 }}s
          </el-descriptions-item>
          <el-descriptions-item label="GIF录制" :span="2">
            <el-button
              v-if="monitorData.gif_path"
              type="primary"
              size="small"
              @click="handleViewGif"
            >
              查看回放
            </el-button>
            <span v-else-if="monitorData.status === 'failed'" class="text-gray">执行失败，无录制</span>
            <span v-else-if="monitorData.status === 'completed'" class="text-gray">执行完成，未生成GIF</span>
            <span v-else class="text-gray">执行完成后生成</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 错误信息 -->
        <el-alert
          v-if="monitorData.error_message"
          type="error"
          title="执行失败"
          :description="monitorData.error_message"
          :closable="false"
          show-icon
          style="margin-top: 15px;"
        />

        <!-- 执行日志 -->
        <el-divider>执行日志</el-divider>
        <el-scrollbar height="400px">
          <pre class="execution-logs">{{ monitorData.logs || '等待执行日志...' }}</pre>
        </el-scrollbar>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button 
            v-if="['completed', 'failed'].includes(monitorData.status)" 
            @click="handleMonitorDialogClose"
          >
            关闭
          </el-button>
          <el-button 
            v-else 
            type="warning" 
            @click="handleStopMonitoring"
          >
            停止监控
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量执行监控对话框 -->
    <el-dialog
      v-model="batchMonitorDialogVisible"
      title="批量执行监控"
      width="80%"
      :close-on-click-modal="false"
      @close="handleBatchMonitorDialogClose"
    >
      <div class="batch-execution-monitor">
        <!-- 统计信息 -->
        <el-row :gutter="20" style="margin-bottom: 20px;">
          <el-col :span="6">
            <el-statistic title="总用例数" :value="batchMonitorData.total">
              <template #suffix>个</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="执行中" :value="batchMonitorData.running">
              <template #suffix>个</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="已完成" :value="batchMonitorData.completed">
              <template #suffix>个</template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="失败" :value="batchMonitorData.failed">
              <template #suffix>个</template>
            </el-statistic>
          </el-col>
        </el-row>

        <!-- 进度条 -->
        <el-progress 
          :percentage="Math.round((batchMonitorData.completed + batchMonitorData.failed) / batchMonitorData.total * 100)" 
          :status="batchMonitorData.failed > 0 ? 'warning' : 'success'"
          style="margin-bottom: 20px;"
        />

        <!-- 用例列表 -->
        <el-divider>用例执行状态</el-divider>
        <el-table :data="batchMonitorData.cases" style="width: 100%" max-height="400">
          <el-table-column prop="name" label="用例名称" min-width="200" show-overflow-tooltip />
          <el-table-column label="执行模式" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="row.execution_mode === 'headless' ? 'info' : 'warning'">
                {{ row.execution_mode === 'headless' ? '无头模式' : '有头模式' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag :type="getBatchCaseStatusType(row.status)">
                {{ getBatchCaseStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="进度" width="100">
            <template #default="{ row }">
              {{ row.progress }} 步
            </template>
          </el-table-column>
          <el-table-column label="错误信息" min-width="200" show-overflow-tooltip>
            <template #default="{ row }">
              <span v-if="row.error_message" class="text-danger">{{ row.error_message }}</span>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button 
            v-if="batchMonitorData.running === 0" 
            @click="handleBatchMonitorDialogClose"
          >
            关闭
          </el-button>
          <el-button 
            v-else 
            type="warning" 
            @click="handleStopBatchMonitoring"
          >
            停止监控
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- GIF回放对话框 -->
    <el-dialog
      v-model="gifDialogVisible"
      title="执行回放"
      width="70%"
    >
      <div class="gif-player">
        <img
          :src="currentGifUrl"
          alt="执行回放"
          style="width: 100%; border: 1px solid #ddd; border-radius: 4px;"
        />
      </div>
    </el-dialog>

    <!-- 执行记录对话框 -->
    <el-dialog
      v-model="recordsDialogVisible"
      title="执行记录"
      width="900px"
    >
      <el-table :data="recordsList" border stripe v-loading="recordsLoading">
        <el-table-column prop="id" label="记录ID" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getExecutionStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="90">
          <template #default="{ row }">
            {{ row.steps_completed?.length || 0 }} 步
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="耗时(秒)" width="100">
          <template #default="{ row }">
            {{ row.duration ? row.duration.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="start_time" label="开始时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.gif_path"
              type="primary"
              size="small"
              @click="viewRecordGif(row)"
            >
              查看回放
            </el-button>
            <span v-else class="text-gray">无回放</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- Excel导入对话框 -->
    <el-dialog 
      v-model="excelImportDialogVisible" 
      title="从Excel导入"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form label-width="100px">
        <el-form-item label="选择项目" required>
          <el-select 
            v-model="excelProjectId" 
            placeholder="请选择项目" 
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="project in projectList"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="选择模块">
          <el-select 
            v-model="excelModuleId" 
            :key="`excel-module-${excelProjectId || 'none'}`"
            placeholder="不选择则按Sheet名称匹配模块" 
            clearable
            style="width: 100%"
            :disabled="!excelProjectId"
            :loading="excelModuleLoading"
          >
            <el-option
              v-for="module in excelModuleList"
              :key="module.id"
              :label="module.name"
              :value="module.id"
            />
          </el-select>
          <div style="color: #909399; font-size: 12px; margin-top: 5px;">
            <div>• 指定模块：所有Sheet的用例导入到该模块</div>
            <div>• 不指定模块：每个Sheet名称对应一个模块名称</div>
          </div>
        </el-form-item>
        
        <el-form-item label="选择文件">
          <el-upload
            :auto-upload="false"
            :on-change="handleExcelFileChange"
            :limit="1"
            accept=".xlsx,.xls"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将Excel文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只支持 .xlsx 和 .xls 格式的Excel文件
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item>
          <el-alert
            type="info"
            :closable="false"
            show-icon
          >
            <template #title>
              <div>
                <div style="font-weight: bold; margin-bottom: 8px;">Excel文件格式要求：</div>
                <ul style="margin: 5px 0; padding-left: 20px;">
                  <li>必需列：用例标题</li>
                  <li>可选列：用例编号、描述、优先级、前置条件、测试步骤、预期结果、任务描述</li>
                  <li>测试步骤格式：每行一个步骤，或使用编号格式（1. 步骤描述）</li>
                </ul>
                <div style="font-weight: bold; margin: 10px 0 5px 0;">多模块导入：</div>
                <ul style="margin: 5px 0; padding-left: 20px;">
                  <li>创建多个Sheet，每个Sheet名称对应一个模块名称</li>
                  <li>例如：Sheet1命名为"登录模块"，Sheet2命名为"搜索模块"</li>
                  <li>系统会自动将用例导入到对应的模块中</li>
                </ul>
                <a 
                  :href="excelTemplateUrl"
                  download="AI_TestCase_Template.xlsx"
                  style="color: #409eff; text-decoration: none; margin-top: 5px; display: inline-block;"
                  target="_blank"
                >
                  📥 下载Excel模板
                </a>
              </div>
            </template>
          </el-alert>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="excelImportDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="submitExcelImport"
          :loading="excelImportLoading"
          :disabled="!excelProjectId || !excelFile"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Upload, VideoPlay, ArrowDown, Delete, UploadFilled } from '@element-plus/icons-vue'
import { getProjectList } from '/@/api/v1/project'
import { getModuleList, getModuleTree } from '/@/api/v1/modules'
import { getTestCaseList } from '/@/api/v1/testcases'
// 导入旧的AI智能浏览器API（用于执行功能）
import { aiCaseApi, aiExecutionRecordApi } from '/@/api/v1/ai_intelligence'

// 数据
const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const selectedCases = ref([])
const projectList = ref([])
const moduleList = ref([])

// 查询表单
const queryForm = reactive({
  source_project_id: null,  // 改为来源项目ID
  source_module_id: null,   // 改为来源模块ID
  status: null,
  source_type: null,
  page: 1,
  page_size: 20
})

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('新增用例')
const submitLoading = ref(false)
const formRef = ref()

// 表单
const form = reactive({
  case_id: '',
  title: '',
  description: '',
  priority: 'P2',
  status: 'active',
  source_type: 'manual',
  precondition: '',
  test_steps: [],
  expected_result: '',
  execution_mode: 'headless',
  timeout: 300
})

// 表单验证规则
const rules = {
  case_id: [{ required: true, message: '请输入用例编号', trigger: 'blur' }],
  title: [{ required: true, message: '请输入用例标题', trigger: 'blur' }],
  test_steps: [{ required: true, message: '请添加测试步骤', trigger: 'change' }]
}

// 查看详情
const viewDialogVisible = ref(false)
const viewCaseData = ref<any>({})

// 批量执行
const batchDialogVisible = ref(false)
const batchForm = reactive({
  task_name: '',
  execution_mode: 'headless',
  parallel_count: 1
})

// 执行监控
const monitorDialogVisible = ref(false)
const currentMonitorCase = ref<any | null>(null)
const monitorData = reactive({
  status: 'running',
  progress: 0,
  logs: '',
  duration: 0,
  error_message: '',
  gif_path: ''
})
let monitorTimer: number | null = null

// 批量执行监控
const batchMonitorDialogVisible = ref(false)
const batchMonitorCases = ref<any[]>([])
const batchMonitorData = reactive({
  total: 0,
  completed: 0,
  failed: 0,
  running: 0,
  cases: [] as any[]
})
let batchMonitorTimer: number | null = null

// GIF回放
const gifDialogVisible = ref(false)
const currentGifUrl = ref('')

// 执行记录
const recordsDialogVisible = ref(false)
const recordsList = ref<any[]>([])
const recordsLoading = ref(false)

// 执行日志
const logsDialogVisible = ref(false)
const executionLogs = ref<any[]>([])
const logsLoading = ref(false)
let logsPollingTimer: number | null = null
const currentCaseIdForLogs = ref<number | null>(null)

// 执行日志详情
const logDetailDialogVisible = ref(false)
const currentLogDetail = ref<any | null>(null)

// 获取列表
const getList = async () => {
  loading.value = true
  try {
    // 使用旧API获取用例列表
    const params: any = {
      page: queryForm.page,
      page_size: queryForm.page_size
    }
    
    // 添加筛选条件
    if (queryForm.source_project_id) params.source_project_id = queryForm.source_project_id
    if (queryForm.source_module_id) params.source_module_id = queryForm.source_module_id
    if (queryForm.status) params.status = queryForm.status
    if (queryForm.source_type) params.source_type = queryForm.source_type
    
    const res = await aiCaseApi.list(params)
    if (res.code === 200) {
      // 处理返回数据
      const data = res.data || {}
      const cases = data.items || data.list || data.results || []
      
      tableData.value = cases
      total.value = data.total || cases.length
    }
  } catch (error) {
    console.error('获取列表失败:', error)
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

// 获取项目列表
const getProjects = async () => {
  try {
    console.log('开始获取主项目列表...')
    // 使用主项目API而不是UI项目API
    const res = await getProjectList({ page: 1, page_size: 100 })
    console.log('主项目列表API响应:', res)
    if (res.code === 200) {
      projectList.value = res.data.list || res.data.items || res.data || []
      console.log('主项目列表:', projectList.value)
    }
  } catch (error) {
    console.error('获取主项目列表失败:', error)
  }
}

// 获取模块列表
const getModules = async () => {
  if (!queryForm.source_project_id) {
    moduleList.value = []
    return
  }
  try {
    const res = await getModuleList({ project_id: queryForm.source_project_id, page: 1, page_size: 1000 })
    if (res.code === 200) {
      moduleList.value = res.data.list || res.data.items || []
    }
  } catch (error) {
    console.error('获取模块列表失败:', error)
  }
}

// 监听项目变化，重新加载模块
watch(() => queryForm.source_project_id, () => {
  // 先清空模块ID和模块列表，避免渲染错误
  queryForm.source_module_id = null
  moduleList.value = []
  // 然后加载新的模块列表
  getModules()
})

// 查询
const handleQuery = () => {
  queryForm.page = 1
  getList()
}

// 重置
const handleReset = () => {
  Object.assign(queryForm, {
    source_project_id: null,
    source_module_id: null,
    status: null,
    source_type: null,
    page: 1,
    page_size: 20
  })
  getList()
}

// 新增
const handleAdd = () => {
  dialogTitle.value = '新增用例'
  Object.assign(form, {
    id: undefined,  // 清除id，确保是新增模式
    case_id: '',
    title: '',
    description: '',
    priority: 'P2',
    status: 'active',
    source_type: 'manual',
    precondition: '',
    test_steps: [],
    expected_result: '',
    execution_mode: 'headless',
    timeout: 300
  })
  
  // 清除表单验证状态
  if (formRef.value) {
    formRef.value.clearValidate()
  }
  
  dialogVisible.value = true
}

// 查看
const handleView = (row: any) => {
  viewDialogVisible.value = true
  viewCaseData.value = { ...row }
}

// 编辑
const handleEdit = (row: any) => {
  dialogTitle.value = '编辑用例'
  
  // 确保所有字段都正确赋值，特别处理test_steps
  const testSteps = row.test_steps && Array.isArray(row.test_steps) && row.test_steps.length > 0
    ? row.test_steps
    : []
  
  Object.assign(form, {
    id: row.id,
    case_id: row.case_id,
    title: row.title || row.name,
    description: row.description || '',
    priority: row.priority || 'P2',
    status: row.status || 'active',
    source_type: row.source_type || 'manual',
    project_id: row.ui_project_id,
    precondition: row.precondition || '',
    test_steps: testSteps,
    expected_result: row.expected_result || '',
    execution_mode: row.execution_mode || 'headless',
    timeout: row.timeout || 300
  })
  
  // 清除表单验证状态
  if (formRef.value) {
    formRef.value.clearValidate()
  }
  
  dialogVisible.value = true
}

// 删除
const handleDelete = (row: any) => {
  ElMessageBox.confirm(
    '确定要删除该用例吗？删除后数据将无法恢复！', 
    '删除确认', 
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await aiCaseApi.delete(row.id)
      ElMessage.success('删除成功')
      getList()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedCases.value.length === 0) {
    ElMessage.warning('请先选择要删除的用例')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedCases.value.length} 个用例吗？删除后数据将无法恢复！`, 
    '批量删除确认', 
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
      distinguishCancelAndClose: true
    }
  ).then(async () => {
    try {
      const caseIds = selectedCases.value.map((c: any) => c.id)
      await aiCaseApi.batchDelete(caseIds)
      ElMessage.success(`成功删除 ${caseIds.length} 个用例`)
      selectedCases.value = []
      getList()
    } catch (error) {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }).catch(() => {
    // 用户取消删除
  })
}

// 执行
const handleExecute = async (row: any, mode: string) => {
  ElMessageBox.confirm(
    `确定要执行该AI用例吗？执行模式：${mode === 'headless' ? '无头模式（后台执行）' : '有头模式（显示浏览器）'}`,
    '执行确认',
    {
      confirmButtonText: '执行',
      cancelButtonText: '取消',
      type: 'info'
    }
  ).then(async () => {
    try {
      const headless = mode === 'headless'
      // 调用旧的AI智能浏览器API执行
      const res = await aiCaseApi.execute(row.id, headless)
      if (res.code === 200) {
        ElMessage.success('AI用例执行已启动')
        // 打开监控对话框
        showExecutionMonitor(row)
      }
    } catch (error: any) {
      ElMessage.error(error.message || '启动执行失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      const caseData = {
        name: form.title,
        description: form.description,
        task_description: form.description || form.title,
        ui_project_id: form.project_id,
        status: form.status || 'active',
        source_type: form.source_type || 'manual',
        priority: form.priority || 'P2',
        precondition: form.precondition,
        test_steps: form.test_steps,
        expected_result: form.expected_result,
        execution_mode: form.execution_mode || 'headless',
        timeout: form.timeout || 300
      }
      
      if (form.id) {
        // 更新
        await aiCaseApi.update(form.id, caseData)
        ElMessage.success('更新成功')
      } else {
        // 创建
        const res = await aiCaseApi.create(caseData)
        
        if (res.code === 200) {
          ElMessage.success('创建成功')
        }
      }
      dialogVisible.value = false
      getList()
    } catch (error) {
      console.error('操作失败:', error)
      ElMessage.error('操作失败')
    } finally {
      submitLoading.value = false
    }
  })
}

// 添加步骤
const addStep = () => {
  form.test_steps.push({
    step_num: form.test_steps.length + 1,
    description: '',
    expected: ''
  })
}

// 删除步骤
const removeStep = (index: number) => {
  form.test_steps.splice(index, 1)
  // 重新编号
  form.test_steps.forEach((step, i) => {
    step.step_num = i + 1
  })
}

// 选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedCases.value = selection
}

// 批量执行
const handleBatchExecute = () => {
  batchForm.task_name = `批量执行任务_${new Date().getTime()}`
  batchForm.execution_mode = 'headless'  // 默认无头模式
  batchForm.parallel_count = 1  // 默认并行数量
  batchDialogVisible.value = true
}

// 提交批量执行
const submitBatchExecute = async () => {
  try {
    const res = await aiCaseApi.batchExecute({
      ...batchForm,
      case_ids: selectedCases.value.map((c: any) => c.id)
    })
    
    if (res.code === 200) {
      ElMessage.success('批量执行任务已创建')
      batchDialogVisible.value = false
      
      // 打开批量执行监控对话框
      showBatchExecutionMonitor(selectedCases.value, batchForm.execution_mode)
    }
  } catch (error: any) {
    console.error('批量执行失败:', error)
    ElMessage.error(error.message || '批量执行失败')
  }
}

// 导入测试用例
const handleImportTestcase = () => {
  importDialogVisible.value = true
  getProjectsForImport()
}

// 导入相关数据
const importDialogVisible = ref(false)
const importLoading = ref(false)
const importProjectList = ref([])
const importModuleTree = ref([])
const selectedModules = ref<number[]>([])
const importForm = reactive({
  project_id: null,
  module_ids: []
})

// 获取项目列表（用于导入）
const getProjectsForImport = async () => {
  try {
    const res = await getProjectList({ page: 1, page_size: 100 })
    if (res.code === 200) {
      importProjectList.value = res.data.list || res.data.items || res.data || []
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

// 监听项目变化，加载模块树
watch(() => importForm.project_id, async (projectId) => {
  // 清空选中的模块和模块树
  selectedModules.value = []
  importModuleTree.value = []
  
  if (!projectId) {
    return
  }
  
  try {
    const res = await getModuleTree(projectId)
    if (res.code === 200) {
      importModuleTree.value = res.data || []
    }
  } catch (error) {
    console.error('获取模块树失败:', error)
    ElMessage.error('获取模块树失败')
  }
})

// 提交导入
const submitImport = async () => {
  if (!importForm.project_id) {
    ElMessage.warning('请选择项目')
    return
  }
  
  if (selectedModules.value.length === 0) {
    ElMessage.warning('请至少选择一个模块')
    return
  }
  
  importLoading.value = true
  try {
    // 调用批量导入API
    const res = await aiCaseApi.importFromModules({
      project_id: importForm.project_id,
      module_ids: selectedModules.value
    })
    
    if (res.code === 200) {
      const importedCount = res.data?.imported_count || 0
      ElMessage.success(`成功导入 ${importedCount} 个用例`)
      importDialogVisible.value = false
      
      // 重置表单
      importForm.project_id = null
      selectedModules.value = []
      
      // 刷新列表
      getList()
    }
  } catch (error: any) {
    console.error('导入失败:', error)
    ElMessage.error(error.message || '导入失败')
  } finally {
    importLoading.value = false
  }
}

// 导入Excel
const excelImportDialogVisible = ref(false)
const excelImportLoading = ref(false)
const excelFile = ref<File | null>(null)
const excelProjectId = ref<number | null>(null)
const excelModuleId = ref<number | null>(null)
const excelModuleList = ref([])
const excelModuleLoading = ref(false)

// Excel模板下载URL
const excelTemplateUrl = `${import.meta.env.VITE_API_BASE_URL}/static/templates/AI_TestCase_Template.xlsx`

const handleImportExcel = () => {
  // 重置状态
  excelProjectId.value = null
  excelModuleId.value = null
  excelModuleList.value = []
  excelFile.value = null
  excelModuleLoading.value = false
  
  excelImportDialogVisible.value = true
}

// 监听Excel项目变化，自动加载模块列表
watch(() => excelProjectId.value, async (projectId, oldProjectId) => {
  // 如果项目ID没有实际变化，不执行
  if (projectId === oldProjectId) {
    return
  }
  
  console.log('Excel项目变化:', { projectId, oldProjectId })
  
  // 先清空模块ID和模块列表，避免渲染错误
  excelModuleId.value = null
  excelModuleList.value = []
  
  if (!projectId) {
    excelModuleLoading.value = false
    return
  }
  
  // 加载模块列表
  excelModuleLoading.value = true
  try {
    console.log('开始加载项目模块:', projectId)
    const res = await getModuleList({ project_id: projectId, page: 1, page_size: 1000 })
    console.log('模块列表响应:', res)
    
    if (res.code === 200) {
      const modules = res.data.list || res.data.items || []
      console.log('加载到的模块数量:', modules.length)
      excelModuleList.value = modules
    } else {
      console.error('加载模块失败:', res)
      ElMessage.error('加载模块失败')
    }
  } catch (error) {
    console.error('获取模块列表失败:', error)
    ElMessage.error('获取模块列表失败')
  } finally {
    excelModuleLoading.value = false
    console.log('模块加载完成')
  }
})

// 选择Excel文件
const handleExcelFileChange = (file: any) => {
  excelFile.value = file.raw
  return false // 阻止自动上传
}

// 提交Excel导入
const submitExcelImport = async () => {
  if (!excelFile.value) {
    ElMessage.warning('请选择Excel文件')
    return
  }
  
  if (!excelProjectId.value) {
    ElMessage.warning('请选择项目')
    return
  }
  
  excelImportLoading.value = true
  try {
    const res = await aiCaseApi.importFromExcel(
      excelFile.value, 
      excelProjectId.value, 
      excelModuleId.value || undefined
    )
    
    if (res.code === 200) {
      const data = res.data || {}
      const imported = data.imported_count || 0
      const skipped = data.skipped_count || 0
      const errors = data.error_count || 0
      const mode = data.mode
      
      let message = `成功导入 ${imported} 个用例`
      if (skipped > 0) {
        message += `，跳过 ${skipped} 个已存在的用例`
      }
      if (errors > 0) {
        message += `，${errors} 个失败`
      }
      
      ElMessage.success(message)
      
      // 如果是多模块模式，显示详细结果
      if (mode === 'multi_module' && data.sheet_results) {
        console.log('多模块导入结果:', data.sheet_results)
        
        // 统计成功和失败的Sheet
        const successSheets = data.sheet_results.filter((r: any) => r.status === 'success')
        const failedSheets = data.sheet_results.filter((r: any) => r.status !== 'success')
        
        if (failedSheets.length > 0) {
          const failedNames = failedSheets.map((r: any) => r.sheet).join(', ')
          ElMessage.warning(`以下Sheet导入失败或跳过: ${failedNames}`)
        }
      }
      
      excelImportDialogVisible.value = false
      excelFile.value = null
      excelProjectId.value = null
      excelModuleId.value = null
      excelModuleList.value = []
      
      // 刷新列表
      getList()
    }
  } catch (error: any) {
    console.error('Excel导入失败:', error)
    ElMessage.error(error.message || 'Excel导入失败')
  } finally {
    excelImportLoading.value = false
  }
}

// 辅助函数
const getPriorityType = (priority: string) => {
  const map: any = { P0: 'danger', P1: 'warning', P2: '', P3: 'info' }
  return map[priority] || ''
}

const getSourceTypeLabel = (type: string) => {
  const map: any = { manual: '手动', import: 'Excel', testcase: '测试用例' }
  return map[type] || type
}

const getStatusType = (status: string) => {
  const map: any = { draft: 'info', active: 'success', archived: 'warning' }
  return map[status] || ''
}

const getStatusLabel = (status: string) => {
  const map: any = { draft: '草稿', active: '激活', archived: '归档' }
  return map[status] || status
}

const getExecutionStatusType = (status: string) => {
  const map: any = { success: 'success', failed: 'danger', running: 'warning' }
  return map[status] || ''
}

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// ==================== 执行监控相关函数 ====================

// 显示执行监控
const showExecutionMonitor = (caseData: any) => {
  currentMonitorCase.value = caseData
  monitorData.status = 'running'
  monitorData.progress = 0
  monitorData.logs = '正在启动AI执行...\n'
  monitorData.duration = 0
  monitorData.error_message = ''
  monitorData.gif_path = ''
  monitorDialogVisible.value = true
  
  // 开始轮询
  startMonitorPolling()
}

// 开始轮询执行状态
const startMonitorPolling = () => {
  let hasNotified = false
  let pollCount = 0
  const MAX_POLL_COUNT = 300 // 最多轮询5分钟（300次 * 1秒）
  
  // 先等待1秒，让后台任务启动
  setTimeout(() => {
    monitorTimer = window.setInterval(async () => {
      try {
        pollCount++
        
        // 获取最新的执行记录
        const res = await aiExecutionRecordApi.list({
          ai_case_id: currentMonitorCase.value?.id,
          page: 1,
          page_size: 1
        })
        
        console.log(`[轮询 ${pollCount}] 执行记录API响应:`, res)
        
        const records = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.items || [])
        
        if (records && records.length > 0) {
          const latestRecord = records[0]
          
          console.log(`[轮询 ${pollCount}] 最新执行记录:`, {
            id: latestRecord.id,
            status: latestRecord.status,
            steps: latestRecord.steps_completed?.length || 0,
            error: latestRecord.error_message
          })
          
          // 更新监控数据
          Object.assign(monitorData, {
            status: latestRecord.status,
            progress: latestRecord.steps_completed ? latestRecord.steps_completed.length : 0,
            logs: String(latestRecord.logs || '执行中...'),
            duration: latestRecord.duration || 0,
            error_message: latestRecord.error_message || '',
            gif_path: latestRecord.gif_path || ''
          })
          
          // 如果完成或失败，停止轮询
          if (['completed', 'failed', 'success'].includes(latestRecord.status)) {
            stopMonitorPolling()
            
            if (!hasNotified) {
              hasNotified = true
              if (latestRecord.status === 'completed' || latestRecord.status === 'success') {
                ElMessage.success('AI用例执行完成')
              } else if (latestRecord.status === 'failed') {
                ElMessage.error(`AI用例执行失败: ${latestRecord.error_message || '未知错误'}`)
              }
            }
            
            // 刷新列表
            getList()
          }
        } else {
          console.log(`[轮询 ${pollCount}] 暂无执行记录，继续等待...`)
          
          // 如果轮询超过30次（30秒）还没有记录，显示警告
          if (pollCount === 30) {
            monitorData.logs += '\n[警告] 30秒后仍未检测到执行记录，请检查后端日志\n'
          }
        }
        
        // 超过最大轮询次数，停止轮询
        if (pollCount >= MAX_POLL_COUNT) {
          stopMonitorPolling()
          ElMessage.warning('执行监控超时，请手动刷新查看结果')
          console.warn('轮询超时，已停止监控')
        }
      } catch (error: any) {
        console.error(`[轮询 ${pollCount}] 轮询执行状态失败:`, error)
        monitorData.logs += `\n[错误] 轮询失败: ${error.message}\n`
      }
    }, 1000) // 改为1秒轮询一次，更快响应
  }, 1000) // 1秒后开始轮询
}

// 停止轮询
const stopMonitorPolling = () => {
  if (monitorTimer) {
    clearInterval(monitorTimer)
    monitorTimer = null
  }
}

// 关闭监控对话框
const handleMonitorDialogClose = () => {
  stopMonitorPolling()
  monitorDialogVisible.value = false
  currentMonitorCase.value = null
}

// 停止监控（用户主动停止）
const handleStopMonitoring = () => {
  ElMessageBox.confirm(
    '确定要停止监控吗？执行任务将继续在后台运行。',
    '停止监控',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    handleMonitorDialogClose()
    ElMessage.info('已停止监控，任务继续在后台执行')
  }).catch(() => {})
}

// 获取监控状态类型
const getMonitorStatusType = () => {
  const map: Record<string, any> = {
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return map[monitorData.status] || 'info'
}

// 获取监控状态文本
const getMonitorStatusText = () => {
  const map: Record<string, string> = {
    running: '执行中',
    completed: '执行完成',
    failed: '执行失败'
  }
  return map[monitorData.status] || '未知'
}

// ==================== 批量执行监控相关函数 ====================

// 显示批量执行监控
const showBatchExecutionMonitor = (cases: any[], executionMode: string) => {
  batchMonitorCases.value = cases
  batchMonitorData.total = cases.length
  batchMonitorData.completed = 0
  batchMonitorData.failed = 0
  batchMonitorData.running = cases.length
  batchMonitorData.cases = cases.map(c => ({
    id: c.id,
    name: c.name || c.title,
    status: 'pending',
    progress: 0,
    error_message: '',
    execution_mode: executionMode
  }))
  
  batchMonitorDialogVisible.value = true
  
  // 开始轮询批量执行状态
  startBatchMonitorPolling()
}

// 开始轮询批量执行状态
const startBatchMonitorPolling = () => {
  let pollCount = 0
  const MAX_POLL_COUNT = 600 // 最多轮询10分钟
  
  // 先等待1秒，让后台任务启动
  setTimeout(() => {
    batchMonitorTimer = window.setInterval(async () => {
      try {
        pollCount++
        
        // 遍历每个用例，获取最新的执行记录
        let allCompleted = true
        let completedCount = 0
        let failedCount = 0
        let runningCount = 0
        
        for (const caseItem of batchMonitorData.cases) {
          try {
            const res = await aiExecutionRecordApi.list({
              ai_case_id: caseItem.id,
              page: 1,
              page_size: 1
            })
            
            if (res.code === 200 && res.data?.items?.length > 0) {
              const latestRecord = res.data.items[0]
              
              // 更新用例状态
              caseItem.status = latestRecord.status
              caseItem.progress = latestRecord.steps_completed ? latestRecord.steps_completed.length : 0
              caseItem.error_message = latestRecord.error_message || ''
              
              // 统计状态
              if (['completed', 'success'].includes(latestRecord.status)) {
                completedCount++
              } else if (latestRecord.status === 'failed') {
                failedCount++
              } else {
                runningCount++
                allCompleted = false
              }
            } else {
              // 还没有执行记录
              allCompleted = false
              runningCount++
            }
          } catch (error) {
            console.error(`获取用例 ${caseItem.id} 执行状态失败:`, error)
          }
        }
        
        // 更新统计数据
        batchMonitorData.completed = completedCount
        batchMonitorData.failed = failedCount
        batchMonitorData.running = runningCount
        
        // 如果全部完成，停止轮询
        if (allCompleted) {
          stopBatchMonitorPolling()
          
          if (failedCount > 0) {
            ElMessage.warning(`批量执行完成：成功 ${completedCount} 个，失败 ${failedCount} 个`)
          } else {
            ElMessage.success(`批量执行完成：全部 ${completedCount} 个用例执行成功`)
          }
        }
        
        // 超过最大轮询次数，停止轮询
        if (pollCount >= MAX_POLL_COUNT) {
          stopBatchMonitorPolling()
          ElMessage.warning('批量执行监控超时，请手动刷新查看结果')
        }
      } catch (error: any) {
        console.error(`批量执行轮询失败:`, error)
      }
    }, 2000) // 每2秒轮询一次
  }, 1000)
}

// 停止批量执行轮询
const stopBatchMonitorPolling = () => {
  if (batchMonitorTimer) {
    clearInterval(batchMonitorTimer)
    batchMonitorTimer = null
  }
}

// 关闭批量执行监控对话框
const handleBatchMonitorDialogClose = () => {
  stopBatchMonitorPolling()
  batchMonitorDialogVisible.value = false
  batchMonitorCases.value = []
  
  // 刷新列表
  getList()
}

// 停止批量执行监控（用户主动停止）
const handleStopBatchMonitoring = () => {
  ElMessageBox.confirm(
    '确定要停止监控吗？执行任务将继续在后台运行。',
    '停止监控',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    handleBatchMonitorDialogClose()
    ElMessage.info('已停止监控，任务继续在后台执行')
  }).catch(() => {})
}

// 获取批量执行用例状态类型
const getBatchCaseStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    success: 'success',
    failed: 'danger'
  }
  return map[status] || 'info'
}

// 获取批量执行用例状态文本
const getBatchCaseStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待执行',
    running: '执行中',
    completed: '执行完成',
    success: '执行成功',
    failed: '执行失败'
  }
  return map[status] || '未知'
}

// 查看GIF回放
const handleViewGif = () => {
  if (!monitorData.gif_path) {
    ElMessage.warning('暂无GIF录制')
    return
  }
  currentGifUrl.value = `/api/static/upload/${monitorData.gif_path}`
  gifDialogVisible.value = true
}

// 查看执行记录
const handleViewRecords = async (row: any) => {
  recordsLoading.value = true
  try {
    console.log('查看执行记录，用例ID:', row.id)
    const res = await aiExecutionRecordApi.list({ ai_case_id: row.id })
    console.log('执行记录API响应:', res)
    
    // 兼容不同的返回格式
    const records = Array.isArray(res.data) ? res.data : (res.data?.results || res.data?.items || [])
    console.log('解析后的执行记录:', records)
    
    recordsList.value = records
    recordsDialogVisible.value = true
    
    if (records.length === 0) {
      ElMessage.info('暂无执行记录')
    }
  } catch (error) {
    console.error('获取执行记录失败:', error)
    ElMessage.error('获取执行记录失败')
  } finally {
    recordsLoading.value = false
  }
}

// 从执行记录查看GIF
const viewRecordGif = (record: any) => {
  if (!record.gif_path) {
    ElMessage.warning('该记录没有GIF录制')
    return
  }
  currentGifUrl.value = `/api/static/upload/${record.gif_path}`
  gifDialogVisible.value = true
}

// 获取状态标签类型
const getStatusTagType = (status?: string) => {
  const map: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    success: 'success',
    failed: 'danger'
  }
  return map[status || 'pending'] || ''
}

// 获取执行状态标签文本
const getExecutionStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    pending: '待执行',
    running: '执行中',
    completed: '已完成',
    success: '成功',
    failed: '失败'
  }
  return map[status || 'pending'] || status
}

// 初始化
onMounted(() => {
  getProjects()
  getList()
})
</script>

<style scoped lang="scss">
.ai-browser-cases-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.query-form {
  margin-bottom: 20px;
}

// 表格操作按钮间距
.el-table {
  .el-button + .el-button,
  .el-button + .el-dropdown {
    margin-left: 8px;
  }
  
  .el-dropdown + .el-button {
    margin-left: 8px;
  }
}

.steps-container {
  width: 100%;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
  
  // 滚动条样式
  &::-webkit-scrollbar {
    width: 6px;
  }
  
  &::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 3px;
  }
  
  &::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 3px;
    
    &:hover {
      background: #555;
    }
  }
}

.step-item {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 12px;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.step-num {
  font-weight: bold;
  color: #409eff;
}

// 执行监控样式
.execution-monitor {
  .execution-logs {
    background-color: #1e1e1e;
    color: #d4d4d4;
    padding: 15px;
    border-radius: 4px;
    font-family: 'Courier New', Consolas, Monaco, monospace;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
    min-height: 100px;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .text-gray {
    color: #909399;
  }
}

.gif-player {
  text-align: center;
  
  img {
    max-width: 100%;
    height: auto;
  }
}
</style>
