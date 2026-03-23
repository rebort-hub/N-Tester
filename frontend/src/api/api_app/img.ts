// 1:1 迁移自 l-vue-ui/src/api/api_app/img.ts
// 映射到新后端 /api/v1/app_management/*（后端将补齐 img_* 端点）
import axios from '@/utils/axios.ts';

enum API {
	IMG_LIST = '/api/v1/app_management/img_list',
	IMG_SELECT = '/api/v1/app_management/img_select',
	DELETE_IMG = '/api/v1/app_management/delete_img',
	EDIT_IMG = '/api/v1/app_management/edit_img',
}

export const img_list = (params: any) => axios.post(API.IMG_LIST, params);
export const img_select = (params: any) => axios.post(API.IMG_SELECT, params);
export const delete_img = (params: any) => axios.post(API.DELETE_IMG, params);
export const edit_img = (params: any) => axios.post(API.EDIT_IMG, params);

