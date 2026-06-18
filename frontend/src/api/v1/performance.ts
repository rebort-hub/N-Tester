import request from '/@/utils/request';
import { Session } from '/@/utils/storage';
import { getApiBaseUrl } from '/@/utils/config';

export function usePerformanceApi() {
	return {
		// 配置管理
		getConfigList: (params?: any) => {
			return request({ url: '/v1/performance/configs', method: 'GET', params });
		},
		// ========================== 压测场景接口映射 ==========================
		getScenarioList: (params?: any) => {
			return request({ url: '/v1/performance/scenario/list', method: 'GET', params });
		},
		addScenario: (data: any) => {
			return request({ url: '/v1/performance/scenario/add', method: 'POST', data });
		},
		updateScenario: (id: number, data: any) => {
			return request({ url: `/v1/performance/scenario/update/${id}`, method: 'PUT', data });
		},
		deleteScenario: (id: number) => {
			return request({ url: `/v1/performance/scenario/delete/${id}`, method: 'DELETE' });
		},
		// 场景子配置接口
		getScenarioConfigList: (scenarioId: number) => {
			return request({ url: `/v1/performance/scenario/${scenarioId}/config/list`, method: 'GET' });
		},
		addScenarioConfig: (scenarioId: number, data: any) => {
			return request({ url: `/v1/performance/scenario/${scenarioId}/config/add`, method: 'POST', data });
		},
		updateScenarioConfig: (scenarioId: number, configId: number, data: any) => {
			return request({ url: `/v1/performance/scenario/${scenarioId}/config/update/${configId}`, method: 'PUT', data });
		},
		deleteScenarioConfig: (scenarioId: number, configId: number) => {
			return request({ url: `/v1/performance/scenario/${scenarioId}/config/delete/${configId}`, method: 'DELETE' });
		},
		/**
		 * 切换子配置状态并一次性同步场景并发数 + 预计耗时。
		 * 替代原来的 updateScenarioConfig × N + getScenarioConfigList + updateScenario 链路。
		 * 返回 { configs, concurrent_count, estimated_duration, estimated_note }
		 */
		syncScenarioStats: (data: { scenario_id: number; config_id: number; status: number; thread_type: string }) => {
			return request({ url: '/v1/performance/scenario/config/sync_stats', method: 'POST', data });
		},

		/**
		 * 更新场景状态。当前支持：status=1（确认联调通过→待开始）。
		 */
		updateScenarioStatus: (data: { scenario_id: number; status: number }) => {
			return request({ url: '/v1/performance/scenario/updateStatus', method: 'PUT', data });
		},

		/**
		 * 联调预览 SSE 流式接口（只读，不推送）。
		 * 返回原始 Response，调用方通过 response.body.getReader() 逐块读取 SSE 事件。
		 * 事件结构：{ type: 'start'|'progress'|'done'|'error', ... }
		 * done 事件含 summary（JMX 摘要）、active_config（当前启用子配置）、inspect_params
		 */
		inspectScenarioStream: (scenarioId: number): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/scenario/${scenarioId}/inspect`, {
				method: 'GET',
				headers: { 'Authorization': `Bearer ${token}`, 'token': token ?? '' },
			});
		},

		/**
		 * 启动联调（action=inspect）或正式执行压测（action=execute）。
		 * inspect：预置调试参数注入 JMX → 推送 Master，场景状态不变。
		 * execute：子配置正式参数注入 JMX → 推送 Master → 场景状态置 running。
		 */
		executeScenario: (scenarioId: number, data: { action: 'inspect' | 'execute' }) => {
			return request({ url: `/v1/performance/scenario/${scenarioId}/execute`, method: 'POST', data });
		},

		/**
		 * 启动联调（action=inspect）或正式执行压测（action=execute）—— SSE 流式版本。
		 * 返回原始 Response，调用方通过 response.body.getReader() 逐块读取 SSE 事件。
		 * 事件格式：{ type: 'stage'|'log'|'progress'|'done'|'error', ... }
		 */
		executeScenarioStream: (scenarioId: number, data: { action: 'inspect' | 'execute' | 'recover' }): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/scenario/${scenarioId}/execute`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`,
					'token': token ?? '',
				},
				body: JSON.stringify(data),
			});
		},

		/**
		 * 强制停止正在运行的压测任务。
		 * kill JMeter 进程、更新 status=4（已取消）、停止日志收集。
		 */
		stopScenario: (scenarioId: number) => {
			return request({ url: `/v1/performance/scenario/${scenarioId}/stop`, method: 'POST' });
		},

		/**
		 * 压测实时监控 SSE 流式接口（GET /{id}/monitor）。
		 * 返回原始 Response；signal 可传入 AbortController.signal 用于主动断连。
		 * 事件格式：{ type: 'log'|'progress'|'ping'|'done'|'error', ... }
		 */
		monitorScenarioStream: (scenarioId: number, offset = 0, signal?: AbortSignal): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/scenario/${scenarioId}/monitor?offset=${offset}`, {
				method: 'GET',
				headers: {
					'Authorization': `Bearer ${token}`,
					'token': token ?? '',
				},
				signal,
			});
		},

		// ========================== 定时任务接口映射 ==========================
		getSchedulerList: (params?: any) => {
			return request({ url: '/v1/performance/schedulers/list', method: 'GET', params });
		},
		addScheduler: (data: any) => {
			return request({ url: '/v1/performance/schedulers/add', method: 'POST', data });
		},
		// id 放请求体
		updateScheduler: (data: any) => {
			return request({ url: '/v1/performance/schedulers/update', method: 'PUT', data });
		},
		// id 放查询参数
		deleteScheduler: (id: number) => {
			return request({ url: `/v1/performance/schedulers/delete?id=${id}`, method: 'DELETE' });
		},
		// id 放请求体
		cancelScheduler: (data: { id: number }) => {
			return request({ url: '/v1/performance/schedulers/cancel', method: 'PUT', data });
		},

		// 测试报告
		getReportList: (params?: any) => {
			return request({ url: '/v1/performance/reports/list', method: 'GET', params });
		},
		getReportDownloadUrl: (id: number, types?: string[]) => {
			const typesParam = types?.length ? `&types=${types.join(',')}` : '';
			return request({ url: `/v1/performance/reports/download?id=${id}${typesParam}`, method: 'GET' });
		},
		getReportLog: (id: number, logType: 'console' | 'collector', filename?: string) => {
			const fnParam = filename ? `&filename=${encodeURIComponent(filename)}` : '';
			return request({ url: `/v1/performance/reports/log?id=${id}&log_type=${logType}${fnParam}`, method: 'GET' });
		},
		deleteReport: (id: number) => {
			return request({ url: '/v1/performance/reports/delete', method: 'POST', data: { id } });
		},
		/** 强制停止收集中（status=1）的报告 */
		stopReport: (id: number) => {
			return request({ url: '/v1/performance/reports/stop', method: 'POST', data: { id } });
		},
		/** 恢复中断（status=3）的报告收集 */
		resumeReport: (id: number) => {
			return request({ url: '/v1/performance/reports/resume', method: 'POST', data: { id } });
		},
		/** 在线报告预览 URL，前端通过 window.open 新 Tab 打开 */
		getReportPreviewUrl: (reportCode: string) => {
			return `${getApiBaseUrl()}/v1/performance/reports/preview/${reportCode}/index.html`;
		},
		/**
		 * 报告收集进度 SSE 流式接口（GET /collectProcess?id=xx）。
		 * 返回原始 Response，调用方通过 response.body.getReader() 逐块读取 SSE 事件。
		 * 事件格式：{ step, pct, step_name, detail, status: 'running'|'done'|'failed' }
		 */
		collectProcessStream: (reportId: number, signal?: AbortSignal): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/reports/collectProcess?id=${reportId}`, {
				method: 'GET',
				headers: { 'Authorization': `Bearer ${token}`, 'token': token ?? '' },
				signal,
			});
		},


		// ============================= 文件管理接口 ======================================
		getFileList: (params?: any) => {
			return request({ url: '/v1/performance/files/list', method: 'GET', params });
		},
		// 文件下拉选项（轻量，仅 id+name，供表单选择器使用）
		getFileOptions: (params?: { file_type?: string }) => {
			return request({ url: '/v1/performance/files/options', method: 'GET', params });
		},
		// 小文件代理上传（≤100MB），支持上传进度回调
		uploadFile: (formData: FormData, onUploadProgress?: (e: ProgressEvent) => void) => {
			return request({
				url: '/v1/performance/files/upload',
				method: 'POST',
				data: formData,
				// 不手动设置 Content-Type：axios 探测到 FormData 会自动附加含 boundary 的正确值，
				// 手动设置反而会破坏 headers 合并，导致拦截器注入的 Authorization 丢失。
				onUploadProgress,
				timeout: 300000,
			} as any);
		},
		// 大文件预签名申请（>100MB，第一阶段）
		presignUpload: (data: { file_name: string; file_size: number; remark?: string }) => {
			return request({ url: '/v1/performance/files/presignUpload', method: 'POST', data });
		},
		// 大文件上传确认（第二阶段）
		confirmUpload: (data: { file_id: number; object_key: string }) => {
			return request({ url: '/v1/performance/files/confirm', method: 'POST', data });
		},
		// 获取预签名下载 URL
		getDownloadUrl: (fileId: number) => {
			return request({ url: `/v1/performance/files/${fileId}/downloadUrl`, method: 'GET' });
		},
		// 替换文件（覆盖原 MinIO 对象），支持上传进度回调
		reuploadFile: (fileId: number, formData: FormData, onUploadProgress?: (e: ProgressEvent) => void) => {
			return request({
				url: `/v1/performance/files/reupload/${fileId}`,
				method: 'PUT',
				data: formData,
				// 同上，不手动设置 Content-Type，让 axios 自动处理 FormData boundary
				onUploadProgress,
				timeout: 300000,
			} as any);
		},
		// 大文件替换申请预签名（>限制值，第一阶段）；file_id 放请求体
		presignReupload: (data: { file_id: number; file_name: string; file_size: number; remark?: string }) => {
			return request({ url: '/v1/performance/files/presignReupload', method: 'POST', data });
		},
		// 大文件替换确认（第二阶段）；file_id 放请求体
		confirmReupload: (data: { file_id: number; object_key: string; file_name: string }) => {
			return request({ url: '/v1/performance/files/confirmReupload', method: 'POST', data });
		},
		// 删除文件（MinIO + 软删 DB）
		deleteFile: (fileId: number) => {
			return request({ url: `/v1/performance/files/delete/${fileId}`, method: 'DELETE' });
		},
		// 更新 JMX 文件名称及引用的数据文件列表（覆盖式）；clear_dist=true 时同步清除分发记录
		setFileRefs: (fileId: number, data: { ref_file_ids: number[]; file_name?: string; clear_dist?: boolean }) => {
			return request({ url: `/v1/performance/files/update/${fileId}`, method: 'PUT', data });
		},

		/**
		 * 共享分发 SSE 流式接口。
		 * 使用原生 fetch（axios 不支持 ReadableStream 流式消费）。
		 * 返回原始 Response，调用方通过 response.body.getReader() 逐块读取 SSE 事件。
		 */
		shareDistributeStream: (data: { file_id: number; worker_count: number; machine_type: number }): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/files/distribute/share/stream`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`,
					'token': token ?? '',
				},
				body: JSON.stringify(data),
			});
		},

		/**
		 * 分割分发 SSE 流式接口（同共享分发，dist_status=2）。
		 */
		splitDistributeStream: (data: { file_id: number; worker_count: number; machine_type: number }): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/files/distribute/split/stream`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`,
					'token': token ?? '',
				},
				body: JSON.stringify(data),
			});
		},

		/**
		 * 清除分发 SSE 流式接口。
		 */
		clearDistributeStream: (data: { file_id: number; worker_count?: number }): Promise<Response> => {
			const token = Session.get('token');
			return fetch(`${getApiBaseUrl()}/v1/performance/files/distribute/clear/stream`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${token}`,
					'token': token ?? '',
				},
				body: JSON.stringify(data),
			});
		},


		// ========================== 压力机配置接口映射 =========================
		getMachineList: (params?: any) => {
			return request({ url: '/v1/performance/config/machines/list', method: 'GET', params });
		},
		addMachine: (data: any) => {
			return request({ url: '/v1/performance/config/machines/add', method: 'POST', data });
		},
		updateMachine: (id: number, data: any) => {
			return request({ url: `/v1/performance/config/machines/update/${id}`, method: 'PUT', data });
		},
		deleteMachine: (id: number) => {
			return request({ url: `/v1/performance/config/machines/delete/${id}`, method: 'DELETE' });
		},

		// =========================== 参数配置接口映射 ===========================
		getParamList: (params?: any) => {
			return request({ url: '/v1/performance/config/params/list', method: 'GET', params });
		},
		addParam: (data: any) => {
			return request({ url: '/v1/performance/config/params/add', method: 'POST', data });
		},
		updateParam: (id: number, data: any) => {
			return request({ url: `/v1/performance/config/params/update/${id}`, method: 'PUT', data });
		},
		deleteParam: (id: number) => {
			return request({ url: `/v1/performance/config/params/delete/${id}`, method: 'DELETE' });
		},
	};
}