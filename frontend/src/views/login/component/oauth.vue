<template>
  <div class="oauth-login">
    <div class="oauth-login-title">第三方登录</div>
    <div class="oauth-carousel">
      <!-- 左箭头 -->
      <div 
        class="carousel-arrow carousel-arrow-left" 
        :class="{ disabled: scrollPosition <= 0 }"
        v-show="maxScroll > 0"
        @click="scrollLeft"
      >
        <el-icon><ArrowLeft /></el-icon>
      </div>

      <!-- OAuth 按钮容器 -->
      <div class="oauth-buttons-wrapper" ref="buttonsWrapper">
        <div class="oauth-buttons-container" ref="buttonsContainer">
          <el-tooltip
            v-for="provider in oauthProviders"
            :key="provider.name"
            :content="`使用 ${provider.label} 登录`"
            placement="top"
          >
            <div
              class="oauth-button"
              :class="`oauth-button-${provider.name}`"
              @click="handleOAuthLogin(provider.name)"
            >
              <Icon v-if="provider.icon" :icon="provider.icon" :size="16" />
              <span v-else class="oauth-text">{{ provider.label.substring(0, 2) }}</span>
            </div>
          </el-tooltip>
        </div>
      </div>

      <!-- 右箭头 -->
      <div 
        class="carousel-arrow carousel-arrow-right"
        :class="{ disabled: scrollPosition >= maxScroll }"
        v-show="maxScroll > 0"
        @click="scrollRight"
      >
        <el-icon><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="oauthLogin">
import { reactive, ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue';
import { useOAuthApi, type OAuthProvider } from '/@/api/v1/oauth';
import { Icon } from '@iconify/vue';

// OAuth 提供商配置
interface OAuthProviderConfig {
  name: OAuthProvider;
  label: string;
  icon: string;
  enabled: boolean;
}

const oauthProviders = reactive<OAuthProviderConfig[]>([
  { name: 'gitee', label: 'Gitee', icon: 'simple-icons:gitee', enabled: true },
  { name: 'github', label: 'GitHub', icon: 'mdi:github', enabled: true },
  { name: 'qq', label: 'QQ', icon: 'simple-icons:tencentqq', enabled: true },
  { name: 'google', label: 'Google', icon: 'logos:google-icon', enabled: true },
  { name: 'wechat', label: '微信', icon: 'simple-icons:wechat', enabled: true },
  { name: 'microsoft', label: 'Microsoft', icon: 'logos:microsoft-icon', enabled: true },
  { name: 'dingtalk', label: '钉钉', icon: 'ri:dingding-fill', enabled: true },
  { name: 'feishu', label: '飞书', icon: 'svg:oauth-feishu', enabled: true },
]);

// 滚动相关
const buttonsWrapper = ref<HTMLElement>();
const buttonsContainer = ref<HTMLElement>();
const scrollPosition = ref(0);
const maxScroll = ref(0);

/**
 * 更新滚动状态
 */
const updateScrollState = () => {
  if (buttonsWrapper.value && buttonsContainer.value) {
    const wrapper = buttonsWrapper.value;
    const container = buttonsContainer.value;
    scrollPosition.value = wrapper.scrollLeft;
    maxScroll.value = container.scrollWidth - wrapper.clientWidth;
  }
};

/**
 * 向左滚动
 */
const scrollLeft = () => {
  if (buttonsWrapper.value) {
    const scrollAmount = 240; // 每次滚动约 4 个按钮的距离
    buttonsWrapper.value.scrollBy({
      left: -scrollAmount,
      behavior: 'smooth'
    });
  }
};

/**
 * 向右滚动
 */
const scrollRight = () => {
  if (buttonsWrapper.value) {
    const scrollAmount = 240;
    buttonsWrapper.value.scrollBy({
      left: scrollAmount,
      behavior: 'smooth'
    });
  }
};

/**
 * 处理 OAuth 登录
 */
const handleOAuthLogin = async (provider: OAuthProvider) => {
  try {
    // 生成随机 state 参数（用于防止 CSRF 攻击）
    const state = Math.random().toString(36).substring(2, 15);
    
    // 保存 state 到 sessionStorage（回调时验证）
    sessionStorage.setItem('oauth_state', state);
    
    // 获取授权 URL
    const { data } = await useOAuthApi().getAuthorizeUrl(provider, state);
    
    // 跳转到授权页面
    window.location.href = data.authorize_url;
  } catch (error: any) {
    console.error('获取 OAuth 授权 URL 失败:', error);
    ElMessage.error(error.message || '获取授权链接失败，请稍后重试');
  }
};

// 生命周期
onMounted(() => {
  if (buttonsWrapper.value) {
    buttonsWrapper.value.addEventListener('scroll', updateScrollState);
    // 初始化滚动状态
    setTimeout(updateScrollState, 100);
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateScrollState);
});

onUnmounted(() => {
  if (buttonsWrapper.value) {
    buttonsWrapper.value.removeEventListener('scroll', updateScrollState);
  }
  window.removeEventListener('resize', updateScrollState);
});
</script>

<style scoped lang="scss">
.oauth-login {
  margin-top: 24px;
  padding-top: 16px;
  border-top: none;

  .oauth-login-title {
    text-align: center;
    font-size: 12px;
    color: var(--el-text-color-placeholder);
    margin-bottom: 12px;
    position: relative;

    &::before, &::after {
      content: '';
      position: absolute;
      top: 50%;
      width: 28%;
      height: 1px;
      background: var(--el-border-color-lighter);
    }
    &::before { left: 0; }
    &::after { right: 0; }
  }

  .oauth-carousel {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;

    .carousel-arrow {
      flex-shrink: 0;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      background: var(--el-fill-color-light);
      border: 1px solid var(--el-border-color-light);
      transition: all 0.2s ease;
      color: var(--el-text-color-regular);

      &:hover:not(.disabled) {
        background: var(--el-fill-color);
        border-color: var(--el-color-primary);
        color: var(--el-color-primary);
        transform: scale(1.05);
      }

      &.disabled {
        opacity: 0.3;
        cursor: not-allowed;
        pointer-events: none;
      }

      .el-icon { font-size: 12px; }
    }

    .oauth-buttons-wrapper {
      overflow-x: auto;
      overflow-y: hidden;
      scroll-behavior: smooth;
      max-width: 100%;
      
      &::-webkit-scrollbar { display: none; }
      -ms-overflow-style: none;
      scrollbar-width: none;

      .oauth-buttons-container {
        display: flex;
        justify-content: center;
        gap: 10px;
        padding: 4px 2px;

        .oauth-button {
          flex-shrink: 0;
          width: 34px;
          height: 34px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          border: 1px solid var(--el-border-color-light);
          background: var(--el-bg-color);
          position: relative;
          overflow: hidden;

          &:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-color: transparent;
          }

          &-gitee {
            background: linear-gradient(135deg, #c71d23, #e84545);
            border-color: transparent;
            :deep(svg) { color: #fff !important; fill: #fff !important; }
          }

          &-github {
            background: linear-gradient(135deg, #24292e, #444d56);
            border-color: transparent;
            :deep(svg) { color: #fff !important; fill: #fff !important; }
          }

          &-qq {
            background: #fff;
            :deep(svg) { color: #12b7f5; }
          }

          &-google { background: #fff; }

          &-wechat {
            background: linear-gradient(135deg, #07c160, #2aae67);
            border-color: transparent;
            :deep(svg) { color: #fff !important; fill: #fff !important; }
          }

          &-microsoft { background: #fff; }

          &-dingtalk {
            background: #fff;
            :deep(svg) { color: #0089ff; }
          }

          &-feishu {
            background: #fff;
            :deep(svg) { color: #00d6b9; }
          }

          .oauth-text {
            font-size: 11px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }

          :deep(svg) {
            width: 16px;
            height: 16px;
          }
        }
      }
    }
  }
}
</style>
