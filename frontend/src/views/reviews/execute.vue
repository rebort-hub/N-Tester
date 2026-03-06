<template>
	<div class="review-execution-container">
		<!-- 选择评审界面 (当没有有效reviewId时显示) -->
		<div v-if="!reviewId" class="review-selection-container">
			<el-card shadow="hover" class="selection-card">
				<div class="selection-header">
					<h2 class="page-title">
						<el-icon><Document /></el-icon>
						选择要执行的评审
					</h2>
					<p class="page-description">请从下面的列表中选择一个评审任务进行执行</p>
				</div>
				
				<div class="selection-content">
					<el-table 
						v-loading="selectionLoading"
						:data="availableReviews" 
						stripe 
						style="width: 100%"
						@row-click="selectReview"
					>
						<el-table-column prop="title" label="评审标题" min-width="200" show-overflow-tooltip />
						<el-table-column prop="priority" label="优先级" width="100">
							<template #default="{ row }">
								<el-tag :type="getPriorityType(row.priority)">
									{{ getPriorityText(row.priority) }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column prop="my_status" label="状态" width="100">
							<template #default="{ row }">
								<el-tag :type="getStatusType(row.my_status)">
									{{ getStatusText(row.my_status) }}
								</el-tag>
							</template>
						</el-table-column>
						<el-table-column prop="my_progress" label="进度" width="120">
							<template #default="{ row }">
								<el-progress :percentage="row.my_progress" :stroke-width="6" />
							</template>
						</el-table-column>
						<el-table-column label="操作" width="120" fixed="right">
							<template #default="{ row }">
								<el-button size="small" type="primary" @click.stop="selectReview(row)">
									选择
								</el-button>
							</template>
						</el-table-column>
					</el-table>
				</div>
			</el-card>
		</div>

		<!-- 正常的评审执行界面 (当有有效reviewId时显示) -->
		<div v-else>
			<!-- 页面头部 -->
			<el-card shadow="hover" class="page-header-card">
				<div class="page-header">
					<div class="header-left">
						<h2 class="page-title">
							<el-icon><Document /></el-icon>
							评审执行 - {{ reviewInfo.title }}
						</h2>
						<p class="page-description">{{ reviewInfo.description }}</p>
					</div>
					<div class="header-right">
						<el-button @click="$router.push('/reviews/my-tasks')">
							<el-icon><ArrowLeft /></el-icon>
							返回任务列表
						</el-button>
						<el-button type="primary" @click="saveProgress">
							<el-icon><DocumentCopy /></el-icon>
							保存进度
						</el-button>
					</div>
				</div>
			</el-card>

		<!-- 评审进度 -->
		<el-card shadow="hover" class="progress-card">
			<div class="progress-header">
				<h3>评审进度</h3>
				<span class="progress-text">{{ currentIndex + 1 }} / {{ testCases.length }}</span>
			</div>
			<el-progress 
				:percentage="progress" 
				:stroke-width="8"
				:color="progressColor"
			/>
		</el-card>

		<!-- 检查清单 -->
		<el-card v-if="checklist.length > 0" shadow="hover" class="checklist-card">
			<div class="card-header">
				<h3>
					<el-icon><List /></el-icon>
					检查清单
				</h3>
			</div>
			<div class="checklist-content">
				<el-checkbox-group v-model="checkedItems">
					<div v-for="item in checklist" :key="item.id" class="checklist-item">
						<el-checkbox :label="item.id">
							{{ item.title }}
						</el-checkbox>
						<p v-if="item.description" class="item-description">{{ item.description }}</p>
					</div>
				</el-checkbox-group>
			</div>
		</el-card>

		<!-- 测试用例评审 -->
		<el-card v-if="testCases.length > 0" shadow="hover" class="testcase-card">
			<div class="card-header">
				<h3>
					<el-icon><Files /></el-icon>
					测试用例评审
				</h3>
				<div class="navigation-controls">
					<el-button 
						:disabled="currentIndex === 0" 
						@click="previousCase"
					>
						<el-icon><ArrowLeft /></el-icon>
						上一个
					</el-button>
					<el-button 
						:disabled="currentIndex === testCases.length - 1" 
						@click="nextCase"
					>
						下一个
						<el-icon><ArrowRight /></el-icon>
					</el-button>
				</div>
			</div>

			<div v-if="currentTestCase" class="testcase-content">
				<!-- 用例信息表格 -->
				<div class="testcase-table-container">
					<el-table :data="testCaseTableData" border stripe class="testcase-table">
						<el-table-column prop="label" label="字段" width="120" class-name="label-column">
							<template #default="{ row }">
								<strong>{{ row.label }}</strong>
							</template>
						</el-table-column>
						<el-table-column prop="content" label="内容" class-name="content-column">
							<template #default="{ row }">
								<div v-if="row.type === 'steps'" class="steps-container">
									<div v-for="step in row.content" :key="step.id" class="step-row">
										<div class="step-info">
											<span class="step-number">步骤 {{ step.step_number }}</span>
											<span class="step-desc">{{ step.description }}</span>
										</div>
										<div v-if="step.expected_result" class="step-expected">
											<strong>期望结果：</strong>{{ step.expected_result }}
										</div>
									</div>
								</div>
								<div v-else class="content-text">
									{{ row.content }}
								</div>
							</template>
						</el-table-column>
					</el-table>
				</div>

				<!-- 评审结果 -->
				<div class="review-result-section">
					<h5>评审结果</h5>
					<el-radio-group v-model="currentReview.result" class="result-options">
						<el-radio value="pass" class="result-pass">
							<el-icon><Check /></el-icon>
							通过
						</el-radio>
						<el-radio value="fail" class="result-fail">
							<el-icon><Close /></el-icon>
							不通过
						</el-radio>
						<el-radio value="modify" class="result-modify">
							<el-icon><Edit /></el-icon>
							需修改
						</el-radio>
					</el-radio-group>
				</div>

				<!-- 评审意见 -->
				<div class="review-comment-section">
					<h5>评审意见</h5>
					<el-input
						v-model="currentReview.comment"
						type="textarea"
						:rows="4"
						placeholder="请输入评审意见..."
						class="comment-input"
					/>
				</div>

				<!-- AI评审结果 -->
				<div v-if="aiReviewResult" class="ai-review-result">
					<h5>
						<el-icon><MagicStick /></el-icon>
						AI评审建议
					</h5>
					
					<!-- AI建议列表 -->
					<div v-if="aiReviewResult.suggestions && aiReviewResult.suggestions.length > 0" class="ai-suggestions">
						<h6>改进建议</h6>
						<div 
							v-for="(suggestion, index) in aiReviewResult.suggestions" 
							:key="index"
							class="suggestion-item"
						>
							<div class="suggestion-content">
								<el-tag 
									:type="suggestion.priority === 'high' ? 'danger' : suggestion.priority === 'medium' ? 'warning' : 'info'"
									size="small"
								>
									{{ suggestion.priority === 'high' ? '高优先级' : suggestion.priority === 'medium' ? '中优先级' : '低优先级' }}
								</el-tag>
								<span class="suggestion-text">{{ suggestion.description }}</span>
							</div>
							<el-button 
								size="small" 
								type="primary" 
								@click="applyAISuggestion(suggestion)"
							>
								应用建议
							</el-button>
						</div>
					</div>
					
					<!-- AI发现的问题 -->
					<div v-if="aiReviewResult.issues && aiReviewResult.issues.length > 0" class="ai-issues">
						<h6>发现的问题</h6>
						<div 
							v-for="(issue, index) in aiReviewResult.issues" 
							:key="index"
							class="issue-item"
						>
							<el-tag type="danger" size="small">问题</el-tag>
							<span class="issue-text">{{ issue.description }}</span>
						</div>
					</div>
					
					<!-- AI识别的优点 -->
					<div v-if="aiReviewResult.strengths && aiReviewResult.strengths.length > 0" class="ai-strengths">
						<h6>用例优点</h6>
						<div 
							v-for="(strength, index) in aiReviewResult.strengths" 
							:key="index"
							class="strength-item"
						>
							<el-tag type="success" size="small">优点</el-tag>
							<span class="strength-text">{{ strength }}</span>
						</div>
					</div>
					
					<!-- AI模型信息 -->
					<div class="ai-model-info">
						<el-text size="small" type="info">
							由 {{ aiReviewResult.ai_model }} 提供评审建议
						</el-text>
					</div>
				</div>

				<!-- 操作按钮 -->
				<div class="action-buttons">
					<!-- AI评审按钮 -->
					<el-button 
						v-if="aiAvailability?.available" 
						@click="aiReviewCurrentCase"
						:loading="aiReviewLoading"
						type="info"
					>
						<el-icon><MagicStick /></el-icon>
						AI评审
					</el-button>
					
					<el-button @click="saveCurrentReview">
						<el-icon><DocumentCopy /></el-icon>
						保存当前评审
					</el-button>
					<el-button 
						v-if="currentIndex < testCases.length - 1" 
						type="primary" 
						@click="saveAndNext"
					>
						保存并下一个
						<el-icon><ArrowRight /></el-icon>
					</el-button>
					<el-button 
						v-else 
						type="success" 
						@click="completeReviewTask"
					>
						<el-icon><Check /></el-icon>
						完成评审
					</el-button>
				</div>
			</div>
		</el-card>

		<!-- 空状态 -->
		<el-empty v-if="!loading && testCases.length === 0" description="暂无测试用例需要评审" />
		</div> <!-- 闭合正常评审执行界面的div -->
	</div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
	Document, ArrowLeft, DocumentCopy, List, Files, ArrowRight, 
	Check, Close, Edit, MagicStick 
} from '@element-plus/icons-vue';
import { 
	getReviewDetail, 
	getReviewTestCases, 
	startReviewTask,
	saveReviewResult,
	completeReview,
	getMyReviewResults,
	getMyReviewTasks,
	checkAIReviewAvailability,
	aiReviewSingleTestCase
} from '/@/api/v1/reviews';

const route = useRoute();
const router = useRouter();

// 响应式数据
const loading = ref(false);

// 获取并验证 reviewId
const getReviewId = () => {
	// 优先从路由参数获取
	let id = route.params.reviewId as string;
	
	// 如果路由参数没有，尝试从查询参数获取
	if (!id || id === ':reviewId' || id === 'undefined') {
		id = route.query.reviewId as string;
	}
	
	// 验证ID是否有效
	if (!id || isNaN(parseInt(id))) {
		return null;
	}
	return parseInt(id);
};

const reviewId = ref(getReviewId());

// 选择评审相关数据
const selectionLoading = ref(false);
const availableReviews = ref<any[]>([]);

// 评审信息
const reviewInfo = reactive({
	id: 0,
	title: '',
	description: '',
	status: '',
	priority: '',
	deadline: '',
});

// 检查清单
const checklist = ref<any[]>([]);
const checkedItems = ref<number[]>([]);

// 测试用例
const testCases = ref<any[]>([]);
const currentIndex = ref(0);

// AI评审相关
const aiAvailability = ref<any>(null);
const aiReviewLoading = ref(false);
const aiReviewResult = ref<any>(null);

// 当前测试用例
const currentTestCase = computed(() => {
	return testCases.value[currentIndex.value] || null;
});

// 测试用例表格数据
const testCaseTableData = computed(() => {
	if (!currentTestCase.value) return [];
	
	const tableData = [];
	
	// 项目名称
	if (currentTestCase.value.project_name) {
		tableData.push({
			label: '项目',
			content: currentTestCase.value.project_name,
			type: 'text'
		});
	}
	
	// 用例标题
	tableData.push({
		label: '用例标题',
		content: currentTestCase.value.title,
		type: 'text'
	});
	
	// 用例描述
	if (currentTestCase.value.description) {
		tableData.push({
			label: '用例描述',
			content: currentTestCase.value.description,
			type: 'text'
		});
	}
	
	// 前置条件
	if (currentTestCase.value.preconditions) {
		tableData.push({
			label: '前置条件',
			content: currentTestCase.value.preconditions,
			type: 'text'
		});
	}
	
	// 测试步骤
	if (currentTestCase.value.steps && currentTestCase.value.steps.length > 0) {
		tableData.push({
			label: '测试步骤',
			content: currentTestCase.value.steps,
			type: 'steps'
		});
	}
	
	// 预期结果
	if (currentTestCase.value.expected_result) {
		tableData.push({
			label: '预期结果',
			content: currentTestCase.value.expected_result,
			type: 'text'
		});
	}
	
	return tableData;
});

// 评审结果
const reviewResults = ref<Record<number, any>>({});

// 当前评审结果
const currentReview = reactive({
	result: '',
	comment: ''
});

// 监听当前用例变化，加载对应的评审结果
watch(currentIndex, (newIndex) => {
	const caseId = testCases.value[newIndex]?.id;
	if (caseId && reviewResults.value[caseId]) {
		currentReview.result = reviewResults.value[caseId].result || '';
		currentReview.comment = reviewResults.value[caseId].comment || '';
	} else {
		currentReview.result = '';
		currentReview.comment = '';
	}
});

// 监听评审结果变化，自动保存到reviewResults
watch(currentReview, (newValue) => {
	const caseId = currentTestCase.value?.id;
	if (caseId) {
		if (!reviewResults.value[caseId]) {
			reviewResults.value[caseId] = {};
		}
		reviewResults.value[caseId].result = newValue.result;
		reviewResults.value[caseId].comment = newValue.comment;
	}
}, { deep: true });

// 评审进度
const progress = computed(() => {
	if (testCases.value.length === 0) return 0;
	
	const reviewedCount = Object.keys(reviewResults.value).filter(
		caseId => {
			const result = reviewResults.value[parseInt(caseId)];
			return result && result.result;
		}
	).length;
	
	// 使用一位小数保持与任务列表一致
	return Math.round((reviewedCount / testCases.value.length) * 100 * 10) / 10;
});

// 进度条颜色
const progressColor = computed(() => {
	if (progress.value < 30) return '#f56c6c';
	if (progress.value < 70) return '#e6a23c';
	return '#67c23a';
});

// 加载可用的评审任务
const loadAvailableReviews = async () => {
	selectionLoading.value = true;
	try {
		const response = await getMyReviewTasks({
			page: 1,
			page_size: 50,
			// 评审执行页面显示待开始和进行中的任务
			status: ''  // 不筛选状态，显示所有任务
		});
		
		if (response.code === 200) {
			// 过滤出可以执行的任务（待开始和进行中）
			availableReviews.value = (response.data.rows || []).filter(task => 
				task.my_status === 'pending' || task.my_status === 'in_progress'
			);
		} else {
			ElMessage.error(response.message || '加载评审任务失败');
		}
	} catch (error) {
		console.error('加载评审任务失败:', error);
		ElMessage.error('加载评审任务失败');
	} finally {
		selectionLoading.value = false;
	}
};

// 选择评审
const selectReview = (review: any) => {
	router.push(`/reviews/execute?reviewId=${review.id}`);
};

// 获取优先级类型
const getPriorityType = (priority: string) => {
	const types: Record<string, string> = {
		low: 'info',
		medium: 'warning',
		high: 'danger',
		urgent: 'danger',
	};
	return types[priority] || 'info';
};

// 获取优先级文本
const getPriorityText = (priority: string) => {
	const texts: Record<string, string> = {
		low: '低',
		medium: '中',
		high: '高',
		urgent: '紧急',
	};
	return texts[priority] || priority;
};

// 获取状态类型
const getStatusType = (status: string) => {
	const types: Record<string, string> = {
		pending: 'warning',
		in_progress: 'primary',
		completed: 'success',
	};
	return types[status] || 'info';
};

// 获取状态文本
const getStatusText = (status: string) => {
	const texts: Record<string, string> = {
		pending: '待开始',
		in_progress: '进行中',
		completed: '已完成',
	};
	return texts[status] || status;
};

// 加载评审详情
const loadReviewDetail = async () => {
	try {
		const response = await getReviewDetail(reviewId.value);
		
		if (response.code === 200) {
			Object.assign(reviewInfo, response.data);
		} else {
			ElMessage.error(response.message || '加载评审详情失败');
		}
	} catch (error) {
		console.error('加载评审详情失败:', error);
		ElMessage.error('加载评审详情失败');
	}
};

// 加载已保存的评审结果
const loadSavedResults = async () => {
	try {
		const response = await getMyReviewResults(reviewId.value);
		
		if (response.code === 200 && response.data) {
			// 恢复已保存的评审结果
			reviewResults.value = {};
			for (const [testCaseId, result] of Object.entries(response.data)) {
				reviewResults.value[parseInt(testCaseId)] = {
					result: result.result,
					comment: result.comment || ''
				};
			}
			
			console.log('已加载保存的评审结果:', reviewResults.value);
			
			// 找到第一个未评审的用例作为当前用例
			const unreviewed = testCases.value.findIndex(tc => {
				const result = reviewResults.value[tc.id];
				return !result || !result.result;
			});
			
			if (unreviewed >= 0) {
				currentIndex.value = unreviewed;
				console.log('设置当前用例索引为:', unreviewed);
			} else if (testCases.value.length > 0) {
				// 如果所有用例都已评审，显示最后一个
				currentIndex.value = testCases.value.length - 1;
			}
			
			// 更新当前评审结果显示
			const currentCaseId = testCases.value[currentIndex.value]?.id;
			if (currentCaseId && reviewResults.value[currentCaseId]) {
				currentReview.result = reviewResults.value[currentCaseId].result || '';
				currentReview.comment = reviewResults.value[currentCaseId].comment || '';
			}
		}
	} catch (error) {
		console.warn('加载已保存的评审结果失败:', error);
		// 不影响页面正常使用
	}
};
const loadTestCases = async () => {
	try {
		const response = await getReviewTestCases(reviewId.value);
		
		if (response.code === 200 && response.data && response.data.length > 0) {
			// 使用后端返回的数据
			testCases.value = response.data;
		} else {
			// 使用模拟数据作为后备
			console.warn('后端未返回测试用例数据，使用模拟数据');
			testCases.value = [
				{
					id: 1,
					title: '用户登录功能测试',
					description: '测试用户使用正确的用户名和密码登录系统',
					priority: 'high',
					steps: [
						{
							id: 1,
							step_number: 1,
							description: '打开登录页面',
							expected_result: '显示登录表单，包含用户名和密码输入框'
						},
						{
							id: 2,
							step_number: 2,
							description: '输入正确的用户名和密码',
							expected_result: '输入框正常显示输入内容'
						},
						{
							id: 3,
							step_number: 3,
							description: '点击登录按钮',
							expected_result: '系统验证用户信息并跳转到主页'
						}
					]
				},
				{
					id: 2,
					title: '密码错误登录测试',
					description: '测试用户输入错误密码时的处理',
					priority: 'medium',
					steps: [
						{
							id: 4,
							step_number: 1,
							description: '打开登录页面',
							expected_result: '显示登录表单'
						},
						{
							id: 5,
							step_number: 2,
							description: '输入正确用户名和错误密码',
							expected_result: '输入框正常显示输入内容'
						},
						{
							id: 6,
							step_number: 3,
							description: '点击登录按钮',
							expected_result: '显示"用户名或密码错误"提示信息'
						}
					]
				},
				{
					id: 3,
					title: '用户名为空登录测试',
					description: '测试用户名为空时的验证',
					priority: 'medium',
					steps: [
						{
							id: 7,
							step_number: 1,
							description: '打开登录页面',
							expected_result: '显示登录表单'
						},
						{
							id: 8,
							step_number: 2,
							description: '用户名输入框留空，输入密码',
							expected_result: '密码输入框正常显示内容'
						},
						{
							id: 9,
							step_number: 3,
							description: '点击登录按钮',
							expected_result: '显示"请输入用户名"提示信息'
						}
					]
				}
			];
		}
		
		// 初始化第一个用例的评审结果
		if (testCases.value.length > 0) {
			const firstCaseId = testCases.value[0].id;
			if (reviewResults.value[firstCaseId]) {
				currentReview.result = reviewResults.value[firstCaseId].result || '';
				currentReview.comment = reviewResults.value[firstCaseId].comment || '';
			}
		}
		
	} catch (error) {
		console.error('加载测试用例失败:', error);
		ElMessage.warning('加载测试用例失败，使用模拟数据进行演示');
		
		// 出错时使用模拟数据
		testCases.value = [
			{
				id: 1,
				title: '用户登录功能测试',
				description: '测试用户使用正确的用户名和密码登录系统',
				priority: 'high',
				steps: [
					{
						id: 1,
						step_number: 1,
						description: '打开登录页面',
						expected_result: '显示登录表单，包含用户名和密码输入框'
					},
					{
						id: 2,
						step_number: 2,
						description: '输入正确的用户名和密码',
						expected_result: '输入框正常显示输入内容'
					},
					{
						id: 3,
						step_number: 3,
						description: '点击登录按钮',
						expected_result: '系统验证用户信息并跳转到主页'
					}
				]
			}
		];
	}
};

// 上一个用例
const previousCase = () => {
	if (currentIndex.value > 0) {
		currentIndex.value--;
	}
};

// 下一个用例
const nextCase = () => {
	if (currentIndex.value < testCases.value.length - 1) {
		currentIndex.value++;
	}
};

// 保存当前评审
const saveCurrentReview = async () => {
	const caseId = currentTestCase.value?.id;
	if (!caseId) return;
	
	if (!currentReview.result) {
		ElMessage.warning('请选择评审结果');
		return;
	}
	
	try {
		const response = await saveReviewResult(reviewId.value, caseId, {
			result: currentReview.result,
			comment: currentReview.comment
		});
		
		if (response.code === 200) {
			// 保存到本地状态
			reviewResults.value[caseId] = {
				result: currentReview.result,
				comment: currentReview.comment
			};
			ElMessage.success('保存成功');
		} else {
			ElMessage.error(response.message || '保存失败');
		}
	} catch (error) {
		console.error('保存评审结果失败:', error);
		ElMessage.error('保存评审结果失败');
	}
};

// 保存并下一个
const saveAndNext = async () => {
	await saveCurrentReview();
	nextCase();
};

// 保存进度
const saveProgress = async () => {
	try {
		// 批量保存所有已评审的结果
		const promises = [];
		for (const caseId in reviewResults.value) {
			const result = reviewResults.value[parseInt(caseId)];
			if (result && result.result) {
				promises.push(
					saveReviewResult(reviewId.value, parseInt(caseId), {
						result: result.result,
						comment: result.comment || ''
					})
				);
			}
		}
		
		if (promises.length > 0) {
			await Promise.all(promises);
			ElMessage.success(`保存了 ${promises.length} 个评审结果`);
		} else {
			ElMessage.info('暂无评审结果需要保存');
		}
	} catch (error) {
		console.error('保存进度失败:', error);
		ElMessage.error('保存进度失败');
	}
};

// 完成评审
const completeReviewTask = async () => {
	// 检查是否所有用例都已评审
	const unreviewed = testCases.value.filter(tc => {
		const result = reviewResults.value[tc.id];
		return !result || !result.result;
	});
	
	if (unreviewed.length > 0) {
		const result = await ElMessageBox.confirm(
			`还有 ${unreviewed.length} 个测试用例未评审，确定要完成评审吗？`,
			'确认完成评审',
			{
				confirmButtonText: '确定完成',
				cancelButtonText: '继续评审',
				type: 'warning',
			}
		).catch(() => false);
		
		if (!result) return;
	}
	
	try {
		// 先保存所有进度
		await saveProgress();
		
		// 完成评审
		const response = await completeReview(reviewId.value);
		
		if (response.code === 200) {
			ElMessage.success('评审完成');
			router.push('/reviews/my-tasks');
		} else {
			ElMessage.error(response.message || '完成评审失败');
		}
	} catch (error) {
		console.error('完成评审失败:', error);
		ElMessage.error('完成评审失败');
	}
};

// AI评审相关方法
const checkAIAvailability = async () => {
	if (!reviewId.value) return;
	
	try {
		const response = await checkAIReviewAvailability(reviewId.value);
		if (response.code === 200) {
			aiAvailability.value = response.data;
		}
	} catch (error) {
		console.error('检查AI评审可用性失败:', error);
	}
};

const aiReviewCurrentCase = async () => {
	if (!currentTestCase.value || !aiAvailability.value?.available) {
		ElMessage.warning('AI评审功能不可用');
		return;
	}
	
	aiReviewLoading.value = true;
	aiReviewResult.value = null;
	
	try {
		const response = await aiReviewSingleTestCase(reviewId.value, currentTestCase.value);
		
		if (response.code === 200 && response.data.success) {
			aiReviewResult.value = response.data;
			ElMessage.success('AI评审完成');
		} else {
			ElMessage.error(response.data?.error || 'AI评审失败');
		}
	} catch (error) {
		console.error('AI评审失败:', error);
		ElMessage.error('AI评审失败');
	} finally {
		aiReviewLoading.value = false;
	}
};

const applyAISuggestion = (suggestion: any) => {
	// 将AI建议应用到当前评审
	const currentReview = reviewResults.value[currentTestCase.value?.id];
	if (currentReview) {
		// 如果已有评审意见，追加AI建议
		const existingComment = currentReview.comment || '';
		const aiSuggestion = `AI建议: ${suggestion.description}`;
		currentReview.comment = existingComment ? `${existingComment}\n\n${aiSuggestion}` : aiSuggestion;
	} else {
		// 创建新的评审结果
		reviewResults.value[currentTestCase.value?.id] = {
			result: 'modify', // 默认设为需修改
			comment: `AI建议: ${suggestion.description}`
		};
	}
	
	ElMessage.success('AI建议已应用到评审意见');
};

// 监听当前评审结果变化，自动保存
// (已在上面定义，此处删除重复)

// 监听路由参数和查询参数变化
watch([() => route.params.reviewId, () => route.query.reviewId], () => {
	reviewId.value = getReviewId();
	// 重新加载数据
	if (reviewId.value) {
		loadReviewDetail();
		loadTestCases();
		loadSavedResults();
	} else {
		loadAvailableReviews();
	}
});

// 组件挂载时加载数据
onMounted(async () => {
	if (!reviewId.value) {
		// 如果没有有效的reviewId，加载可用的评审任务
		await loadAvailableReviews();
		return;
	}
	
	loading.value = true;
	try {
		await Promise.all([
			loadReviewDetail(),
			loadTestCases(),
			checkAIAvailability() // 检查AI评审可用性
		]);
		
		// 自动开始评审任务
		try {
			await startReviewTask(reviewId.value);
			console.log('评审任务已开始');
		} catch (error) {
			// 如果任务已经开始或其他错误，不影响页面加载
			console.warn('开始评审任务失败:', error);
		}
		
		// 加载已有的评审结果
		await loadSavedResults();
		
	} finally {
		loading.value = false;
	}
});
</script>

<style scoped>
.review-execution-container {
	padding: 20px;
}

/* 选择评审界面样式 */
.review-selection-container {
	padding: 20px;
}

.selection-card {
	margin-bottom: 20px;
}

.selection-header {
	text-align: center;
	margin-bottom: 30px;
}

.selection-header .page-title {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	margin: 0 0 8px 0;
	font-size: 24px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.selection-header .page-description {
	margin: 0;
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.selection-content {
	margin-top: 20px;
}

.selection-content .el-table {
	cursor: pointer;
}

.selection-content .el-table tbody tr:hover {
	background-color: var(--el-table-row-hover-bg-color);
}

.page-header-card {
	margin-bottom: 20px;
}

.page-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.header-left {
	flex: 1;
}

.page-title {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0 0 8px 0;
	font-size: 24px;
	font-weight: 600;
	color: var(--el-text-color-primary);
}

.page-description {
	margin: 0;
	color: var(--el-text-color-regular);
	font-size: 14px;
}

.header-right {
	display: flex;
	gap: 12px;
}

.progress-card {
	margin-bottom: 20px;
}

.progress-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 15px;
}

.progress-header h3 {
	margin: 0;
	color: var(--el-text-color-primary);
}

.progress-text {
	font-size: 14px;
	color: var(--el-text-color-regular);
}

.checklist-card,
.testcase-card {
	margin-bottom: 20px;
}

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 20px;
	padding-bottom: 15px;
	border-bottom: 1px solid var(--el-border-color-light);
}

.card-header h3 {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0;
	color: var(--el-text-color-primary);
}

.navigation-controls {
	display: flex;
	gap: 8px;
}

.checklist-content {
	padding: 10px 0;
}

.checklist-item {
	margin-bottom: 15px;
}

.item-description {
	margin: 5px 0 0 24px;
	font-size: 12px;
	color: var(--el-text-color-regular);
}

.testcase-content {
	padding: 10px 0;
}

.testcase-table-container {
	margin-bottom: 25px;
}

.testcase-table {
	width: 100%;
}

.testcase-table :deep(.label-column) {
	background-color: var(--el-color-primary-light-9);
	font-weight: 600;
}

.testcase-table :deep(.label-column .cell) {
	color: var(--el-color-primary);
}

.testcase-table :deep(.content-column .cell) {
	padding: 12px;
}

.content-text {
	line-height: 1.6;
	color: var(--el-text-color-primary);
}

.steps-container {
	padding: 0;
}

.step-row {
	margin-bottom: 15px;
	padding: 12px;
	background: var(--el-bg-color-page);
	border-radius: 6px;
	border-left: 3px solid var(--el-color-primary);
}

.step-row:last-child {
	margin-bottom: 0;
}

.step-info {
	display: flex;
	align-items: center;
	gap: 10px;
	margin-bottom: 8px;
}

/* AI评审结果样式 */
.ai-review-result {
	margin-top: 20px;
	padding: 20px;
	background: var(--el-bg-color-page);
	border: 1px solid var(--el-border-color-light);
	border-radius: 8px;
}

.ai-review-result h5 {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 0 0 15px 0;
	color: var(--el-color-primary);
	font-size: 16px;
	font-weight: 600;
}

.ai-review-result h6 {
	margin: 15px 0 10px 0;
	color: var(--el-text-color-primary);
	font-size: 14px;
	font-weight: 600;
}

.ai-suggestions,
.ai-issues,
.ai-strengths {
	margin-bottom: 15px;
}

.suggestion-item,
.issue-item,
.strength-item {
	display: flex;
	align-items: flex-start;
	gap: 10px;
	margin-bottom: 10px;
	padding: 10px;
	background: var(--el-color-white);
	border: 1px solid var(--el-border-color-lighter);
	border-radius: 6px;
}

.suggestion-item {
	justify-content: space-between;
}

.suggestion-content {
	display: flex;
	align-items: flex-start;
	gap: 8px;
	flex: 1;
}

.suggestion-text,
.issue-text,
.strength-text {
	flex: 1;
	line-height: 1.5;
	color: var(--el-text-color-primary);
}

.ai-model-info {
	margin-top: 15px;
	padding-top: 10px;
	border-top: 1px solid var(--el-border-color-lighter);
	text-align: right;
}

/* 深色主题适配 */
html.dark .ai-review-result {
	background: var(--el-bg-color-overlay);
	border-color: var(--el-border-color);
}

html.dark .suggestion-item,
html.dark .issue-item,
html.dark .strength-item {
	background: var(--el-bg-color);
	border-color: var(--el-border-color);
}

.step-number {
	display: inline-block;
	padding: 4px 8px;
	background: var(--el-color-primary);
	color: white;
	border-radius: 4px;
	font-size: 12px;
	font-weight: bold;
	flex-shrink: 0;
}

.step-desc {
	color: var(--el-text-color-primary);
	line-height: 1.5;
}

.step-expected {
	color: var(--el-text-color-regular);
	font-size: 13px;
	line-height: 1.5;
	padding-left: 12px;
	border-left: 2px solid var(--el-border-color-light);
	margin-left: 20px;
}

.review-result-section,
.review-comment-section {
	margin-bottom: 25px;
}

.review-result-section h5,
.review-comment-section h5 {
	margin: 0 0 15px 0;
	color: var(--el-text-color-primary);
	font-size: 16px;
}

.result-options {
	display: flex;
	gap: 20px;
}

.result-options .el-radio {
	margin-right: 0;
	padding: 10px 15px;
	border: 1px solid var(--el-border-color-light);
	border-radius: 6px;
	transition: all 0.3s;
}

.result-options .el-radio:hover {
	border-color: var(--el-color-primary);
}

.result-options .el-radio.is-checked {
	border-color: var(--el-color-primary);
	background: var(--el-color-primary-light-9);
}

.result-pass.is-checked {
	border-color: var(--el-color-success);
	background: var(--el-color-success-light-9);
}

.result-fail.is-checked {
	border-color: var(--el-color-danger);
	background: var(--el-color-danger-light-9);
}

.result-modify.is-checked {
	border-color: var(--el-color-warning);
	background: var(--el-color-warning-light-9);
}

.comment-input {
	width: 100%;
}

.action-buttons {
	display: flex;
	gap: 12px;
	justify-content: flex-end;
	padding-top: 20px;
	border-top: 1px solid var(--el-border-color-light);
}

/* 深色主题适配 */
.dark .testcase-table :deep(.label-column) {
	background-color: var(--el-color-primary-dark-2);
}

.dark .step-row {
	background: var(--el-bg-color-overlay);
	border-left-color: var(--el-color-primary);
}

.dark .step-expected {
	border-left-color: var(--el-border-color);
}
</style>