import axios, {AxiosInstance, AxiosRequestConfig} from 'axios';
import {ElMessage, ElMessageBox} from 'element-plus';
import {Session} from '/@/utils/storage';
import qs from 'qs';
import {getApiBaseUrl} from "/@/utils/config";
import {handlerRedirectUrl} from "/@/utils/urlHandler";

const cancelToken = axios.CancelToken
const source = cancelToken.source()

// 防止重复弹窗
let isShowingAuthDialog = false;

// 配置新建一个 axios 实例
const service: AxiosInstance = axios.create({
	baseURL: getApiBaseUrl(),
	timeout: 50000,
	headers: {'Content-Type': 'application/json'},
	paramsSerializer: {
		serialize(params) {
			return qs.stringify(params, {allowDots: true});
		},
	},
});

// 添加请求拦截器
service.interceptors.request.use(
	(config: AxiosRequestConfig) => {
		// 在发送请求之前做些什么 token
		if (Session.get('token')) {
			// 新API使用Authorization: Bearer token格式
			config.headers!['Authorization'] = `Bearer ${Session.get('token')}`;
			// 兼容旧API的token header
			config.headers!['token'] = `${Session.get('token')}`;
		}
		return config;
	},
	(error) => {
		// 对请求错误做些什么
		return Promise.reject(error);
	}
);

// 添加响应拦截器
service.interceptors.response.use(
	(response) => {
		// 对响应数据做点什么
		const res = response.data;
		// 新API使用code: 200表示成功，旧API使用code: 0表示成功
		const isSuccess = res.code === 0 || res.code === 200;
		
		if (res.code && !isSuccess) {
			// `token` 过期或者账号已在别处登录
			if (res.code === 11000 || res.code === 401) {
				ElMessageBox.confirm('登录信息已失效，是否重新登录？', '提示', {
					confirmButtonText: '确认',
					cancelButtonText: '取消',
					type: 'warning',
				})
					.then(() => {
						Session.clear(); // 清除浏览器全部临时缓存
						window.location.href = handlerRedirectUrl() || '/'; // 去登录页
					})
					.catch(() => {
					});
			}
			// 不在这里显示错误消息，让组件自己处理
			// 将错误信息附加到error对象上
			const error: any = new Error(res.msg || res.message || '接口错误');
			error.response = response;
			error.code = res.code;
			return Promise.reject(error);
		} else {
			// 兼容新旧API的数据格式
			if (res.data) {
				// 1. 分页数据格式转换
				// 新API返回: { items: [], total: 10, page: 1, page_size: 10 }
				// 旧API期望: { rows: [], rowTotal: 10 }
				if (res.data.items !== undefined && res.data.total !== undefined) {
					res.data.rows = res.data.items;
					res.data.rowTotal = res.data.total;
				}
				
				// 2. 单个对象或数组的字段映射（与后端 web_management 等接口对齐）
				const mapFields = (obj: any) => {
					if (!obj || typeof obj !== 'object') return obj;
					
					// 时间字段映射（后端常用 creation_date / updation_date，前端表格常用 create_time / update_time）
					if (obj.created_at) obj.creation_date = obj.created_at;
					if (obj.updated_at) obj.updation_date = obj.updated_at;
					if (obj.creation_date !== undefined) obj.create_time = obj.create_time ?? obj.creation_date;
					if (obj.updation_date !== undefined) obj.update_time = obj.update_time ?? obj.updation_date;
					
					// 备注字段映射
					if (obj.remark !== undefined) obj.remarks = obj.remark;
					
					// 角色字段映射
					if (obj.role_ids !== undefined) obj.roles = obj.role_ids;
					if (obj.role_name !== undefined) obj.name = obj.role_name;
					if (obj.role_code !== undefined) obj.code = obj.role_code;
					
					// 部门字段映射 - 注释掉，保持新字段名
					// if (obj.dept_name !== undefined && !obj.name) obj.name = obj.dept_name;
					// if (obj.dept_code !== undefined && !obj.code) obj.code = obj.dept_code;
					if (obj.order_num !== undefined) obj.sort = obj.order_num;
					
					// 菜单字段映射
					if (obj.menu_name !== undefined) obj.title = obj.menu_name;
					if (obj.perms !== undefined) obj.permission = obj.perms;
					
					// 字典字段映射
					if (obj.dict_code !== undefined && !obj.code) obj.code = obj.dict_code;
					if (obj.dict_name !== undefined && !obj.name) obj.name = obj.dict_name;
					if (obj.dict_label !== undefined) obj.label = obj.dict_label;
					if (obj.dict_value !== undefined) obj.value = obj.dict_value;
					
					// 递归处理children（用于树形结构）
					if (obj.children && Array.isArray(obj.children)) {
						obj.children = obj.children.map(mapFields);
					}
					
					return obj;
				};
				
				// 如果是 { content: [], total } 格式（web_management 场景列表等），只映射 content 每项，保留 total
				if (
					typeof res.data === 'object' &&
					Array.isArray((res.data as any).content) &&
					typeof (res.data as any).total === 'number'
				) {
					(res.data as any).content = (res.data as any).content.map(mapFields);
				}
				// 如果是 items + total 分页格式
				else if (Array.isArray(res.data.items)) {
					res.data.items = res.data.items.map(mapFields);
					if (res.data.rows) {
						res.data.rows = res.data.rows.map(mapFields);
					}
				}
				// 如果data本身是数组
				else if (Array.isArray(res.data)) {
					res.data = res.data.map(mapFields);
				}
				// 如果是单个对象（避免对 { content, total } 整对象 mapFields 导致 content 被误改）
				else if (typeof res.data === 'object') {
					res.data = mapFields(res.data);
				}
			}
			return response.data;
		}
	},
	(error) => {
		// 对响应错误做点什么
		if (error.message.indexOf('timeout') != -1) {
			ElMessage.error('网络超时');
		} else if (error.message == 'Network Error') {
			ElMessage.error('网络连接错误');
		} else {
			// 处理HTTP错误状态码
			if (error.response?.data) {
				const errorData = error.response.data;
				// 提取错误信息
				const errorMessage = errorData.detail || errorData.message || errorData.msg || error.response.statusText;
				error.message = errorMessage;
				
				// 处理 401 未授权错误
				if (error.response.status === 401) {
					// 统一处理 token 过期
					if (isShowingAuthDialog) {
						return Promise.reject(error);
					}
					isShowingAuthDialog = true;
					
					ElMessageBox.confirm('登录信息已失效，是否重新登录？', '系统提示', {
						confirmButtonText: '确认',
						cancelButtonText: '取消',
						type: 'warning',
						showClose: false,
						closeOnClickModal: false,
						closeOnPressEscape: false,
						center: true
					})
						.then(() => {
							Session.clear(); // 清除浏览器全部临时缓存
							window.location.href = handlerRedirectUrl() || '/'; // 去登录页
						})
						.catch(() => {
							// 用户点击取消，也清除缓存
							Session.clear();
							isShowingAuthDialog = false;
						});
					return Promise.reject(error);
				}
				
				// 对于其他业务错误（如400），直接抛出错误让组件处理
				if (error.response.status >= 400 && error.response.status < 500) {
					const businessError: any = new Error(errorMessage);
					businessError.response = error.response;
					businessError.code = error.response.status;
					return Promise.reject(businessError);
				}
			}
		}
		return Promise.reject(error);
	}
);

// 导出 axios 实例
export default service;
