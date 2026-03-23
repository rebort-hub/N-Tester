// 兼容旧版 file_list(folder_path) 等接口
// 新架构当前没有完全对齐的“目录扫描”能力时，会在后端补齐；此处先透传
import axios from '@/utils/axios.ts';

enum API {
	FILE_LIST = '/api/v1/system/file/list',
}

export const file_list = (params: any) => axios.post(API.FILE_LIST, params);

