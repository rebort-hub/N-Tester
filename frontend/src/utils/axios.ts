/**
 * 兼容旧版 axios 封装（l-vue-ui 使用 axios.post(...)）
 * 新架构底层使用 /@/utils/request（axios 实例 + token/codes 兼容）
 */
import request from '/@/utils/request';

function normalizeUrl(url: string): string {
	// request.baseURL 通常已包含 VITE_API_PREFIX（例如：/api）
	// 兼容旧代码仍传 /api/v1/...，需要避免拼成 /api/api/v1/...
	const baseURL = ((request as any)?.defaults?.baseURL as string | undefined) || '';
	if (baseURL.includes('/api') && url.startsWith('/api/')) {
		return url.slice('/api'.length);
	}
	return url;
}

const axiosCompat = {
	post(url: string, data?: any, config?: any) {
		return (request as any).post(normalizeUrl(url), data, config);
	},
	get(url: string, params?: any, config?: any) {
		return (request as any).get(normalizeUrl(url), { params, ...(config || {}) });
	},
};

export default axiosCompat;

