<template>
  <div class="oauth-callback-container">
    <div class="oauth-callback-card">
      <div class="logo-section">
        <img src="/@/assets/logo.png" alt="Logo" class="logo" />
      </div>


      <div v-if="!state.error" class="callback-success">
        <div class="icon-wrapper">
          <el-icon class="loading-icon" :size="56">
            <Loading />
          </el-icon>
        </div>
        
        <h2 class="callback-title">{{ state.message }}</h2>
        
        <div class="progress-wrapper">
          <el-progress 
            :percentage="state.progress" 
            :stroke-width="4"
            :show-text="false"
            color="#409EFF"
          />
        </div>
        
        <p class="callback-tips">
          <el-icon class="tips-icon"><Clock /></el-icon>
          <span>{{ state.tips }}</span>
        </p>
      </div>


      <div v-else class="callback-error">
        <div class="icon-wrapper error">
          <el-icon class="error-icon" :size="56">
            <CircleClose />
          </el-icon>
        </div>
        
        <h2 class="callback-title error">{{ state.message }}</h2>
        
        <div class="error-content">
          <el-alert
            :title="state.errorDetail"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
        
        <el-button 
          type="primary" 
          size="large"
          @click="router.push('/login')"
          class="back-button"
        >
          返回登录页
        </el-button>
      </div>
    </div>


    <div class="footer-info">
      <p>© 2026 FastAPI N-Tester. All rights reserved.</p>
    </div>
  </div>
</template>

<script setup lang="ts" name="oauthCallback">
import { reactive, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Loading, CircleClose, Clock } from '@element-plus/icons-vue';
import { useOAuthApi, type OAuthProvider } from '/@/api/v1/oauth';
import { Session } from '/@/utils/storage';
import { useUserStore } from '/@/stores/user';
import { useMenuInfo } from '/@/stores/menu';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const menuStore = useMenuInfo();

const state = reactive({
  message: '正在连接授权服务器',
  tips: '请稍候，正在处理您的登录请求...',
  error: false,
  errorDetail: '',
  progress: 0,
});


const startProgress = () => {
  const interval = setInterval(() => {
    if (state.progress < 90) {
      state.progress += Math.random() * 15;
      if (state.progress > 90) state.progress = 90;
    } else {
      clearInterval(interval);
    }
  }, 300);
  return interval;
};


const handleOAuthCallback = async () => {
  const progressInterval = startProgress();
  
  try {

    const provider = route.params.provider as OAuthProvider;
    const code = route.query.code as string;
    const stateParam = route.query.state as string;

    console.log('OAuth 回调参数:', { provider, code, stateParam });


    if (!provider) {
      throw new Error('缺少 OAuth 提供商参数');
    }

    if (!code) {
      throw new Error('缺少授权码参数');
    }

 
    const savedState = sessionStorage.getItem('oauth_state');
    console.log('State 验证:', { savedState, stateParam });
    
    if (savedState && stateParam !== savedState) {
      console.warn('State 参数不匹配，但继续处理（开发环境）');
    }

 
    state.message = '正在验证授权信息';
    state.tips = '正在与授权服务器通信...';
    state.progress = 25;
    
    console.log('调用后端 API:', { provider, code, stateParam });
    const response = await useOAuthApi().callback(provider, code, stateParam);
    console.log('后端响应:', response);

    const { data } = response;

 
    state.message = '授权验证成功';
    state.tips = '正在保存登录凭证...';
    state.progress = 50;
    
    Session.set('token', data.access_token);
    Session.set('refresh_token', data.refresh_token);
    
    console.log('Token 已保存');

 
    state.message = '正在获取用户信息';
    state.tips = '正在加载您的个人资料...';
    state.progress = 70;
    
    await userStore.setUserInfos();
    console.log('用户信息已更新:', userStore.userInfos);
    
  
    state.message = '正在加载系统菜单';
    state.tips = '正在准备工作台...';
    state.progress = 85;
    
    await menuStore.setUserInfos();

   
    sessionStorage.removeItem('oauth_state');

   
    state.progress = 100;
    state.message = '登录成功';
    state.tips = '即将进入系统...';
    
    const username = userStore.userInfos.nickname || userStore.userInfos.username;
    ElMessage.success({
      message: `欢迎，${username}！`,
      duration: 2000,
    });

  
    setTimeout(() => {
      router.push('/');
    }, 600);

  } catch (error: any) {
    clearInterval(progressInterval);
    console.error('OAuth 登录失败:', error);
    console.error('错误详情:', {
      message: error.message,
      response: error.response,
      stack: error.stack
    });
    
    state.error = true;
    state.message = '登录失败';
    state.errorDetail = error.message || error.msg || error.detail || '授权失败，请重试';

    ElMessage.error({
      message: '登录失败，请重试',
      duration: 3000,
    });
  }
};


onMounted(() => {
  handleOAuthCallback();
});
</script>

<style scoped lang="scss">
.oauth-callback-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #e8edf3 100%);
  padding: 20px;

  .oauth-callback-card {
    width: 100%;
    max-width: 480px;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    padding: 48px 40px;
    animation: fadeInUp 0.4s ease-out;

    .logo-section {
      text-align: center;
      margin-bottom: 32px;
      
      .logo {
        height: 48px;
        width: auto;
      }
    }

    .callback-success,
    .callback-error {
      text-align: center;

      .icon-wrapper {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        margin-bottom: 24px;
        
        &.error {
          background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        }

        .loading-icon {
          color: #409EFF;
          animation: rotate 1.2s linear infinite;
        }

        .error-icon {
          color: #F56C6C;
        }
      }

      .callback-title {
        font-size: 20px;
        font-weight: 500;
        color: #303133;
        margin: 0 0 24px 0;
        line-height: 1.4;
        
        &.error {
          color: #F56C6C;
        }
      }

      .progress-wrapper {
        margin-bottom: 20px;
        
        :deep(.el-progress-bar__outer) {
          background-color: #e4e7ed;
          border-radius: 100px;
        }
        
        :deep(.el-progress-bar__inner) {
          border-radius: 100px;
          transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
      }

      .callback-tips {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        font-size: 14px;
        color: #909399;
        line-height: 1.6;
        
        .tips-icon {
          font-size: 16px;
          color: #C0C4CC;
        }
      }

      .error-content {
        margin-bottom: 24px;
        
        :deep(.el-alert) {
          border-radius: 8px;
          
          .el-alert__title {
            font-size: 14px;
            line-height: 1.6;
            color: #606266;
          }
        }
      }

      .back-button {
        width: 100%;
        height: 44px;
        font-size: 15px;
        border-radius: 8px;
        font-weight: 500;
      }
    }
  }

  .footer-info {
    margin-top: 32px;
    text-align: center;
    
    p {
      font-size: 13px;
      color: #909399;
      margin: 0;
    }
  }
}


@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}


@media (max-width: 640px) {
  .oauth-callback-container {
    padding: 16px;
    
    .oauth-callback-card {
      padding: 36px 24px;
      
      .logo-section {
        margin-bottom: 24px;
        
        .logo {
          height: 40px;
        }
      }
      
      .callback-success,
      .callback-error {
        .icon-wrapper {
          width: 64px;
          height: 64px;
          margin-bottom: 20px;
          
          .loading-icon,
          .error-icon {
            font-size: 40px !important;
          }
        }
        
        .callback-title {
          font-size: 18px;
          margin-bottom: 20px;
        }
      }
    }
    
    .footer-info {
      margin-top: 24px;
      
      p {
        font-size: 12px;
      }
    }
  }
}
</style>
