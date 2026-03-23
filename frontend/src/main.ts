import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { directive } from '/@/directive/index';
import other from '/@/utils/other';

import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import '/@/theme/index.scss';
import { initStores } from "/@/stores";
import KoiCard from '/@/components/koi/KoiCard.vue';
import KoiDialog from '/@/components/koi/KoiDialog.vue';
import KoiDrawer from '/@/components/koi/KoiDrawer.vue';
import KoiUploadImages from '/@/components/koi/KoiUploadImages.vue';
import KoiUploadFiles from '/@/components/koi/KoiUploadFiles.vue';

async function initApplication() {
	const app = createApp(App);

	const namespace = `${import.meta.env.VITE_APP_NAMESPACE}`;
	await initStores(app, { namespace })

	// 兼容旧版：全局注册 koi 组件（支持 <koiCard> / <KoiCard> 等写法）
	app.component('koiCard', KoiCard);
	app.component('KoiCard', KoiCard);
	app.component('KoiDialog', KoiDialog);
	app.component('KoiDrawer', KoiDrawer);
	app.component('KoiUploadImages', KoiUploadImages);
	app.component('KoiUploadFiles', KoiUploadFiles);

	directive(app);
	other.apiPublicAssembly(app)
	app.use(router)
	app.use(ElementPlus)
	app.mount('#app');
}

initApplication()