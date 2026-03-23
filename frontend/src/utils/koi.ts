import { ElNotification, ElMessageBox, ElMessage } from 'element-plus';

type MessageType = 'info' | 'success' | 'error' | 'warning';

export function Msg(message: any, duration = 2000, type: MessageType = 'info', parseHtml = false) {
	ElMessage.closeAll();
	ElMessage({ message, type, duration, showClose: true, dangerouslyUseHTMLString: parseHtml });
}
export function MsgSuccess(message: any, duration = 2000, type: MessageType = 'success', parseHtml = false) {
	ElMessage.closeAll();
	ElMessage({ message, type, duration, showClose: true, dangerouslyUseHTMLString: parseHtml });
}
export function MsgError(message: any, duration = 2000, type: MessageType = 'error', parseHtml = false) {
	ElMessage.closeAll();
	ElMessage({ message, type, duration, showClose: true, dangerouslyUseHTMLString: parseHtml });
}
export function MsgWarning(message: any, duration = 2000, type: MessageType = 'warning', parseHtml = false) {
	ElMessage.closeAll();
	ElMessage({ message, type, duration, showClose: true, dangerouslyUseHTMLString: parseHtml });
}

export function koiNotice(message: any, title = '温馨提示', duration = 2000, type: MessageType = 'info', parseHtml = false) {
	ElNotification.closeAll();
	ElNotification({ message, title, type, duration, showClose: true, dangerouslyUseHTMLString: parseHtml });
}

export function MsgBox(
	message: any = '您确定进行关闭么？',
	title: string = '温馨提示：',
	confirmButtonText: string = '确定',
	cancelButtonText: string = '取消',
	type: string = 'warning'
): Promise<boolean> {
	return new Promise((resolve, reject) => {
		ElMessageBox.confirm(message as any, title as any, {
			confirmButtonText,
			cancelButtonText,
			type,
			draggable: true,
			dangerouslyUseHTMLString: true,
		} as any)
			.then(() => resolve(true))
			.catch(() => reject(false));
	});
}

// 兼容旧版命名
export const NoticeError = (message: any, duration = 2000) => koiNotice(message, '温馨提示', duration, 'error');
export const NoticeSuccess = (message: any, duration = 2000) => koiNotice(message, '温馨提示', duration, 'success');
export const koiNoticeWarning = (message: any, duration = 2000) => koiNotice(message, '温馨提示', duration, 'warning');

