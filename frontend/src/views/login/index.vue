<template>
  <div class="login-page">
    <div class="login-brand">
      <div class="brand-logo">
        <img :src="logos.white" alt="Logo" class="brand-logo-img" />
        <span class="brand-name">N-Tester</span>
      </div>
      <div class="brand-inner">
        <div class="brand-hero">
          <div class="brand-tag">AI FULL-STACK TESTING PLATFORM</div>
          <h1 class="brand-title">欢迎使用 {{ getThemeConfig.globalTitle }}</h1>
          <p class="brand-desc">面向企业级的全栈自动化测试平台，集接口自动化、UI自动化、APP自动化于一体，让测试更高效、让业务更卓越。</p>
          <div class="brand-dots">
            <span class="dot dot-active"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

  
    <div class="login-form-area">
      <div class="login-toolbar">
        <div class="theme-colors">
          <span
            v-for="c in themePresets"
            :key="c.color"
            class="theme-dot"
            :style="{ background: c.color }"
            :class="{ active: isActiveTheme(c.color) }"
            :title="c.name"
            @click="switchTheme(c)"
          >
            <el-icon v-if="isActiveTheme(c.color)" class="theme-dot-check"><ele-Check /></el-icon>
          </span>
          <el-color-picker
            v-model="getThemeConfig.primary"
            size="small"
            class="theme-custom-picker"
            title="自定义颜色"
            @change="onColorPickerChange"
          />
        </div>
        <el-tooltip :content="getThemeConfig.isIsDark ? '切换浅色' : '切换深色'" placement="bottom">
          <button class="dark-toggle" @click="toggleDark">
            <el-icon v-if="getThemeConfig.isIsDark"><ele-Sunny /></el-icon>
            <el-icon v-else><ele-Moon /></el-icon>
          </button>
        </el-tooltip>
      </div>

      <div class="login-form-card">
        <div class="login-form-header">
          <h2 class="login-form-title">欢迎回来</h2>
          <p class="login-form-sub">输入您的账号和密码登录系统</p>
        </div>

        <div class="login-form-body">
          <div v-if="!state.isScan">
            <el-tabs v-model="state.tabsActiveName" class="login-tabs">
              <el-tab-pane label="账号密码登录" name="account">
                <Account />
              </el-tab-pane>
            </el-tabs>
            <OAuth />
          </div>
          <Scan v-if="state.isScan" />
        </div>
      </div>

  
      <div class="login-copyright">
        <span>N-Tester平台</span>
        <span class="sep">|</span>
        <a href="https://beian.miit.gov.cn/" target="_blank">贵ICP备202698015号</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="loginIndex">
import { computed, defineAsyncComponent, onMounted, reactive } from 'vue';
import { storeToRefs } from 'pinia';
import { useThemeConfig } from '/@/stores/themeConfig';
import { NextLoading } from '/@/utils/loading';
import { logos } from '/@/config/assets';
import { onColorPickerChange, onAddDarkChange } from '/@/layout/navBars/topBar/settings/index';
import { getHexColor } from '/@/utils/theme';

const Account = defineAsyncComponent(() => import('/@/views/login/component/account.vue'));
const Mobile = defineAsyncComponent(() => import('/@/views/login/component/mobile.vue'));
const Scan = defineAsyncComponent(() => import('/@/views/login/component/scan.vue'));
const OAuth = defineAsyncComponent(() => import('/@/views/login/component/oauth.vue'));

const storesThemeConfig = useThemeConfig();
const { themeConfig } = storeToRefs(storesThemeConfig);
const state = reactive({ tabsActiveName: 'account', isScan: false });

const getThemeConfig = computed(() => themeConfig.value);

const themePresets = [
  { color: '#409eff', name: '默认蓝' },
  { color: 'hsl(245 82% 67%)', name: '紫罗兰' },
  { color: 'hsl(231 98% 65%)', name: '天蓝色' },
  { color: 'hsl(161 90% 43%)', name: '浅绿色' },
  { color: 'hsl(181 84% 32%)', name: '深绿色' },
  { color: 'hsl(42 84% 61%)', name: '柠檬黄' },
  { color: 'hsl(18 89% 40%)', name: '橙黄色' },
  { color: 'hsl(347 77% 60%)', name: '樱花粉' },
];

const switchTheme = (preset: { color: string }) => {
  onColorPickerChange(preset.color);
};

const toggleDark = () => {
  onAddDarkChange(getThemeConfig.value.isIsDark ? 'light' : 'dark');
};

const isActiveTheme = (color: string) => {
  return getHexColor(color) === getThemeConfig.value.primary;
};

onMounted(() => { NextLoading.done(); });
</script>

<style scoped lang="scss">
.login-page {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background: var(--el-bg-color-page);
}


.login-brand {
  flex: 1;
  position: relative;
  background: linear-gradient(145deg, #f0f4ff 0%, #e8f0fe 40%, #dbeafe 70%, #bfdbfe 100%);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;

  &::before {
    content: '';
    position: absolute;
    bottom: -120px;
    left: -80px;
    width: 420px;
    height: 420px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(99,102,241,.18) 0%, rgba(59,130,246,.08) 60%, transparent 100%);
  }

  &::after {
    content: '';
    position: absolute;
    top: -60px;
    right: -60px;
    width: 280px;
    height: 280px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(14,165,233,.12) 0%, transparent 70%);
  }
}

.brand-inner {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 56px;
  width: 100%;
}

.brand-logo {
  position: absolute;
  top: 32px;
  left: 40px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo-img {
  width: 56px;
  height: 56px;
  object-fit: contain;
  filter: drop-shadow(0 2px 8px rgba(99,102,241,.35));
}

.brand-name {
  font-size: 26px;
  font-weight: 700;
  color: #1e40af;
  letter-spacing: .5px;
}

.brand-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.brand-tag {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #6366f1;
  margin-bottom: 16px;
}

.brand-title {
  font-size: 38px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.25;
  margin: 0 0 18px;
}

.brand-desc {
  font-size: 14px;
  color: #64748b;
  line-height: 1.8;
  max-width: 380px;
  margin: 0 0 28px;
}

.brand-dots {
  display: flex;
  gap: 8px;
}

.dot {
  width: 24px;
  height: 4px;
  border-radius: 2px;
  background: #cbd5e1;
  transition: all .3s;
}

.dot-active {
  width: 40px;
  background: #6366f1;
}

.brand-deco { display: none; }


.login-form-area {
  width: 680px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 80px;
  background: var(--el-bg-color);
  border-left: 1px solid var(--el-border-color-light);
  position: relative;
}

.login-form-card {
  width: 100%;
  max-width: 520px;
}

.login-form-header {
  margin-bottom: 28px;
}

.login-form-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 6px;
}

.login-form-sub {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.login-form-body {
  :deep(.el-tabs__header) { margin-bottom: 20px; }
  :deep(.el-tabs__nav-wrap::after) { display: none; }
  :deep(.el-tabs) { --el-tabs-header-height: 36px; }
  :deep(.el-tabs__content) { overflow: visible; border: none; }
  :deep(.el-tab-pane) { border: none; }
  :deep(.login-content-form) { border: none; }
  :deep(.el-tabs__item) {
    font-size: 14px; color: #94a3b8; padding: 0 4px; height: 36px; line-height: 36px;
    &.is-active { color: var(--el-color-primary); font-weight: 600; }
  }
  :deep(.el-tabs__active-bar) { background: var(--el-color-primary); height: 2px; border-radius: 1px; }
  :deep(.el-input__wrapper) {
    border-radius: 8px;
    box-shadow: none !important;
    border: 1px solid var(--el-border-color);
    transition: border-color .2s;
    &:hover { border-color: var(--el-color-primary-light-3); }
    &.is-focus { border-color: var(--el-color-primary); border-width: 2px; }
  }
  :deep(.el-form-item) { margin-bottom: 22px; overflow: visible; }
  :deep(.el-form-item__content) { overflow: visible; }
  :deep(.el-form-item__error) { padding-top: 4px; font-size: 12px; }
  :deep(.login-content-submit) {
    width: 100%; height: 44px; border-radius: 8px;
    background: var(--el-color-primary);
    border: none; font-size: 15px; font-weight: 600; letter-spacing: .5px; transition: all .2s; margin-top: 8px;
    &:hover { background: var(--el-color-primary-dark-2); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,.2); }
  }
  
  :deep(.oauth-login) { margin-top: 0; }
}

.login-copyright {
  position: absolute;
  bottom: 20px;
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 8px;

  a { color: #94a3b8; text-decoration: none; &:hover { color: var(--el-color-primary); } }
  .sep { color: #cbd5e1; }
}


.login-toolbar {
  position: absolute;
  top: 20px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 24px;
  padding: 6px 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}

.theme-colors {
  display: flex;
  align-items: center;
  gap: 6px;
}

.theme-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform .15s, box-shadow .15s;
  flex-shrink: 0;

  &:hover { transform: scale(1.15); }

  &.active {
    box-shadow: 0 0 0 2px #fff, 0 0 0 3px currentColor;
  }

  .theme-dot-check {
    color: #fff;
    font-size: 13px;
  }
}

.theme-custom-picker {
  :deep(.el-color-picker__trigger) {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: none;
    padding: 0;
  }
  :deep(.el-color-picker__color) {
    border-radius: 50%;
    border: none;
  }
  :deep(.el-color-picker__icon) { display: none; }
}

.dark-toggle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-regular);
  font-size: 16px;
  transition: color .2s, background .2s;
  padding: 0;

  &:hover {
    background: var(--el-fill-color-light);
    color: var(--el-color-primary);
  }
}


@media (max-width: 768px) {
  .login-page {
    flex-direction: column;
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }

  
  .login-brand {
    flex: none;
    height: 140px;
    width: 100%;
    justify-content: flex-start;
    padding: 0 24px;

    .brand-inner { display: none; }

    .brand-logo {
      position: static;
      padding: 0;
    }

    .brand-logo-img { width: 36px; height: 36px; }
    .brand-name { font-size: 20px; }
  }

  
  .login-form-area {
    width: 100%;
    flex-shrink: unset;
    border-left: none;
    border-top: 1px solid var(--el-border-color-light);
    padding: 32px 24px 80px;
    min-height: calc(100vh - 140px);
    justify-content: flex-start;
  }

  .login-form-card {
    max-width: 100%;
  }

  
  .login-toolbar {
    top: 12px;
    right: 12px;
    padding: 4px 8px;
    gap: 4px;
  }

  .theme-dot {
    width: 18px;
    height: 18px;
  }

  .theme-custom-picker {
    :deep(.el-color-picker__trigger) {
      width: 18px;
      height: 18px;
    }
  }

  .dark-toggle {
    width: 24px;
    height: 24px;
    font-size: 14px;
  }

  .login-form-title { font-size: 22px; }

  .login-copyright {
    position: static;
    margin-top: 24px;
    justify-content: center;
  }
}
</style>
