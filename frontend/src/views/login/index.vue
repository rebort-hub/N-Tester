<template>
  <div class="login-container flex h100" ref="loginContainerRef" :style="loginBgStyle">
    <div class="login-left">
      <!-- Logo -->
      <div class="login-left-logo">
        <img :src="logos.white" class="login-left-logo-img" alt="Logo"/>
      </div>
      <!--      <div class="login-left-img">-->
      <!--        <img :src="loginMain"/>-->
      <!--      </div>-->
      <!--      <img :src="loginBg" class="login-left-waves"/>-->
    </div>
    <div class="login-right flex">
      <div class="login-right-warp flex-margin">
        <span class="login-right-warp-one"></span>
        <span class="login-right-warp-two"></span>
        <div class="login-right-warp-mian">
          <div class="login-right-warp-main-title">{{ getThemeConfig.globalTitle }} 欢迎您！</div>
          <div class="login-right-warp-main-form">
            <div v-if="!state.isScan">
              <el-tabs v-model="state.tabsActiveName">
                <el-tab-pane label="账号密码登录" name="account">
                  <Account/>
                </el-tab-pane>
                <!--                <el-tab-pane label="手机号登录" name="mobile">-->
                <!--                  <Mobile/>-->
                <!--                </el-tab-pane>-->
              </el-tabs>
              <!-- OAuth 第三方登录 -->
              <OAuth/>
            </div>
            <Scan v-if="state.isScan"/>
            <!--            <div class="login-content-main-sacn" @click="state.isScan = !state.isScan">-->
            <!--              <i class="iconfont" :class="state.isScan ? 'icon-diannao1' : 'icon-barcode-qr'"></i>-->
            <!--              <div class="login-content-main-sacn-delta"></div>-->
            <!--            </div>-->
          </div>
        </div>
      </div>
    </div>

    <div class="login-footer">
      <div class="login-footer__content">
        <span style="color: #fff">N-Tester平台</span> |
        <a style="color: #fff" href="https://beian.miit.gov.cn/" class="slide" target="_blank">贵ICP备202698015号</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" name="loginIndex">
import {computed, defineAsyncComponent, onMounted, reactive, ref} from 'vue';
import {storeToRefs} from 'pinia';
import {useThemeConfig} from '/@/stores/themeConfig';
import {NextLoading} from '/@/utils/loading';
import {backgroundImages, getBackgroundStyle, logos} from '/@/config/assets';

const loginContainerRef = ref()

// 引入组件
const Account = defineAsyncComponent(() => import('/@/views/login/component/account.vue'));
const Mobile = defineAsyncComponent(() => import('/@/views/login/component/mobile.vue'));
const Scan = defineAsyncComponent(() => import('/@/views/login/component/scan.vue'));
const OAuth = defineAsyncComponent(() => import('/@/views/login/component/oauth.vue'));

// 定义变量内容
const storesThemeConfig = useThemeConfig();
const {themeConfig} = storeToRefs(storesThemeConfig);
const state = reactive({
  tabsActiveName: 'account',
  isScan: false,
});

// 获取布局配置信息
const getThemeConfig = computed(() => {
  return themeConfig.value;
});

// 获取登录背景样式
const loginBgStyle = computed(() => {
  return getBackgroundStyle(backgroundImages.loginBg);
});

// 页面加载时
onMounted(() => {
  NextLoading.done();
});
</script>

<style scoped lang="scss">
.login-container {
  // 背景图通过 :style 绑定动态设置，便于统一管理和替换

  .login-left {
    flex: 1;
    position: relative;
    //background-color: rgba(211, 239, 255, 1);
    margin-right: 100px;

    .login-left-logo {
      position: absolute;
      left: 50px;
      top: 50px;
      z-index: 1;
      animation: logoAnimation 0.3s ease;

      .login-left-logo-img {
        max-width: 120px;
        max-height: 120px;
        object-fit: contain;
      }
    }

    .login-left-img {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 100%;
      height: 52%;

      img {
        width: 100%;
        height: 100%;
        animation: error-num 0.6s ease;
      }
    }

    .login-left-waves {
      position: absolute;
      top: 0;
      right: -100px;
    }
  }

  .login-right {
    width: 700px;

    .login-right-warp {
      border-radius: 20px;
      width: 500px;
      min-height: 500px;  // 改为 min-height，允许内容撑开
      height: auto;       // 添加 auto 高度
      position: relative;
      overflow: visible;  // 改为 visible，允许内容溢出显示

      backdrop-filter: blur(5px);
      border: 1px rgba(255, 255, 255, 0.4) solid;
      background-color: rgba(0, 0, 0, 0.277);
      box-shadow: rgba(0, 0, 0, 0.3) 2px 8px 8px;
      border-bottom: 1px rgba(40, 40, 40, 0.35) solid;
      border-right: 1px rgba(40, 40, 40, 0.35) solid;

      .login-right-warp-one,
      .login-right-warp-two {
        position: absolute;
        display: block;
        width: inherit;
        height: inherit;

        &::before,
        &::after {
          content: '';
          position: absolute;
          z-index: 1;
        }
      }

      .login-right-warp-one {
        //&::before {
        //  filter: hue-rotate(0deg);
        //  top: 0px;
        //  left: 0;
        //  width: 100%;
        //  height: 3px;
        //  background: linear-gradient(90deg, transparent, var(--el-color-primary));
        //  animation: loginLeft 3s linear infinite;
        //}
        //
        //&::after {
        //  filter: hue-rotate(60deg);
        //  top: -100%;
        //  right: 2px;
        //  width: 3px;
        //  height: 100%;
        //  background: linear-gradient(180deg, transparent, var(--el-color-primary));
        //  animation: loginTop 3s linear infinite;
        //  animation-delay: 0.7s;
        //}
      }

      .login-right-warp-two {
        //&::before {
        //  filter: hue-rotate(120deg);
        //  bottom: 2px;
        //  right: -100%;
        //  width: 100%;
        //  height: 3px;
        //  background: linear-gradient(270deg, transparent, var(--el-color-primary));
        //  animation: loginRight 3s linear infinite;
        //  animation-delay: 1.4s;
        //}
        //
        //&::after {
        //  filter: hue-rotate(300deg);
        //  bottom: -100%;
        //  left: 0px;
        //  width: 3px;
        //  height: 100%;
        //  background: linear-gradient(360deg, transparent, var(--el-color-primary));
        //  animation: loginBottom 3s linear infinite;
        //  animation-delay: 2.1s;
        //}
      }

      .login-right-warp-mian {
        display: flex;
        flex-direction: column;
        min-height: 500px;  // 改为 min-height
        height: auto;       // 添加 auto 高度
        padding-bottom: 30px;  // 添加底部内边距

        .login-right-warp-main-title {
          height: 130px;
          line-height: 130px;
          font-size: 27px;
          text-align: center;
          letter-spacing: 3px;
          animation: logoAnimation 0.3s ease;
          animation-delay: 0.3s;
          color: #FFF;
        }

        .login-right-warp-main-form {
          flex: 1;
          padding: 0 50px 30px;  // 增加底部内边距从 50px 到 30px（因为外层已有 30px）
          min-height: 300px;     // 添加最小高度确保有足够空间

          .login-content-main-sacn {
            position: absolute;
            top: 0;
            right: 0;
            width: 50px;
            height: 50px;
            overflow: hidden;
            cursor: pointer;
            transition: all ease 0.3s;
            color: var(--el-color-primary);

            &-delta {
              position: absolute;
              width: 35px;
              height: 70px;
              z-index: 2;
              top: 2px;
              right: 21px;
              background: var(--el-color-white);
              transform: rotate(-45deg);
            }

            &:hover {
              opacity: 1;
              transition: all ease 0.3s;
              color: var(--el-color-primary) !important;
            }

            i {
              width: 47px;
              height: 50px;
              display: inline-block;
              font-size: 48px;
              position: absolute;
              right: 1px;
              top: 0px;
            }
          }
        }
      }
    }
  }
}

.login-footer {
  width: 100%;
  bottom: 30px;
  position: absolute;

  background-color: transparent;

  .login-footer__content {
    //margin: 0 auto;
    white-space: nowrap;
    mix-blend-mode: difference;
    transform: translate(-50%);
    position: absolute;
    left: 50%;

    .slide {
      text-decoration: none;
    }
  }
}
</style>
