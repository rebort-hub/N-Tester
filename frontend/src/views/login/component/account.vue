<template>
  <el-form ref="loginFormRef" :model="state.ruleForm" :rules="state.rules" size="large" class="login-content-form">
    <el-form-item class="login-animation1" prop="userName">
      <el-input text placeholder="请输入用户名" v-model="state.ruleForm.userName" clearable
                autocomplete="off">
        <template #prefix>
          <el-icon class="el-input__icon">
            <ele-User/>
          </el-icon>
        </template>
      </el-input>
    </el-form-item>
    <el-form-item class="login-animation2" prop="password">
      <el-input :type="state.isShowPassword ? 'text' : 'password'" placeholder="请输入登录密码"
                v-model="state.ruleForm.password" autocomplete="off">
        <template #prefix>
          <el-icon class="el-input__icon">
            <ele-Unlock/>
          </el-icon>
        </template>
        <template #suffix>
          <i
              class="iconfont el-input__icon login-content-password"
              :class="state.isShowPassword ? 'icon-yincangmima' : 'icon-xianshimima'"
              @click="state.isShowPassword = !state.isShowPassword"
          >
          </i>
        </template>
      </el-input>
    </el-form-item>
    <el-form-item class="login-animation3" prop="code">
      <el-col :span="15">
        <el-input text maxlength="4" placeholder="请输入验证码" v-model="state.ruleForm.code" clearable
                  autocomplete="off" @keyup.enter="onSignIn">
          <template #prefix>
            <el-icon class="el-input__icon">
              <ele-Position/>
            </el-icon>
          </template>
        </el-input>
      </el-col>
      <el-col :span="1"></el-col>
      <el-col :span="8">
        <Captcha ref="captchaRef" @update:code="onCaptchaUpdate" :width="100" :height="40" />
      </el-col>
    </el-form-item>
    <el-form-item class="login-animation4">
      <el-button type="primary" class="login-content-submit" round v-waves @click="onSignIn"
                 :loading="state.loading.signIn">
        <span>登 录</span>
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts" name="loginAccount">
import {computed, reactive, ref} from 'vue';
import {useRoute, useRouter} from 'vue-router';
import {ElMessage} from 'element-plus';
import {storeToRefs} from 'pinia';
import Captcha from '/@/components/Captcha/index.vue';
import {useThemeConfig} from '/@/stores/themeConfig';
import {initBackEndControlRoutes} from '/@/router/backEnd';
import {Session} from '/@/utils/storage';
import {formatAxis} from '/@/utils/formatTime';
import {NextLoading} from '/@/utils/loading';
import {useUserApi} from "/@/api/v1/system/user";
import {useUserStore} from "/@/stores/user";

// 定义变量内容
const loginFormRef = ref();
const captchaRef = ref();
const storesThemeConfig = useThemeConfig();
const {themeConfig} = storeToRefs(storesThemeConfig);
const route = useRoute();
const router = useRouter();

// 验证码值
const captchaCode = ref('');

const state = reactive({
  isShowPassword: false,
  ruleForm: {
    userName: 'admin',
    password: '123456',
    code: '',
  },
  rules: {
    userName: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
    ],
    code: [
      { required: true, message: '请输入验证码', trigger: 'blur' },
      { len: 4, message: '验证码长度为 4 个字符', trigger: 'blur' },
      { 
        validator: (rule: any, value: any, callback: any) => {
          if (value.toLowerCase() !== captchaCode.value.toLowerCase()) {
            callback(new Error('验证码错误'));
          } else {
            callback();
          }
        }, 
        trigger: 'blur' 
      }
    ]
  },
  loading: {
    signIn: false,
  },
});

// 验证码更新回调
const onCaptchaUpdate = (code: string) => {
  captchaCode.value = code;
};

// 时间获取
const currentTime = computed(() => {
  return formatAxis(new Date());
});
// 登录
const onSignIn = async () => {
  // 先进行表单验证
  if (!loginFormRef.value) return;
  
  await loginFormRef.value.validate((valid: boolean) => {
    if (!valid) {
      ElMessage.error('请检查输入信息');
      // 验证失败，刷新验证码
      captchaRef.value?.refreshCode();
      state.ruleForm.code = '';
      return false;
    }
    
    // 验证通过，开始登录
    state.loading.signIn = true;
    useUserApi().signIn({username: state.ruleForm.userName, password: state.ruleForm.password})
        .then(async res => {

          const token = res.data.access_token || res.data.token;
          Session.set('token', token);
          // 如果有refresh_token，也保存
          if (res.data.refresh_token) {
            Session.set('refresh_token', res.data.refresh_token);
          }
          await useUserStore().setUserInfos();
          await initBackEndControlRoutes();
          signInSuccess(false);
        })
        .catch((e) => {
          console.log('错误信息： ', e)
          state.loading.signIn = false;
          // 登录失败，刷新验证码
          captchaRef.value?.refreshCode();
          state.ruleForm.code = '';
        })
  });
};
// 登录成功后的跳转
const signInSuccess = (isNoPower: boolean) => {
  if (isNoPower) {
    ElMessage.warning('抱歉，您没有登录权限');
    Session.clear();
  } else {
    // 初始化登录成功时间问候语
    let currentTimeInfo = currentTime.value;
    // 登录成功，跳到转首页
    // 如果是复制粘贴的路径，非首页/登录页，那么登录成功后重定向到对应的路径中
    const params = route.query!.params || {}
    if (route.query?.redirect) {
      router.push({
        path: route.query?.redirect,
        query: Object.keys(params).length > 0 ? JSON.parse(params) : '',
      });
    } else {
      router.push('/home');
    }
    // 登录成功提示
    const signInText = '欢迎回来！';
    ElMessage.success(`${currentTimeInfo}，${signInText}`);
    // 添加 loading，防止第一次进入界面时出现短暂空白
    NextLoading.start();
  }
  state.loading.signIn = false;
};
</script>

<style scoped lang="scss">
.login-content-form {
  margin-top: 20px;
  border: none;

  // 给所有输入框添加圆角
  :deep(.el-input__wrapper) {
    border-radius: 10px;
  }

  // 给验证码按钮添加圆角
  .login-content-code {
    border-radius: 10px;
  }

  // 给登录按钮添加圆角
  .login-content-submit {
    border-radius: 25px;
  }

  @for $i from 1 through 4 {
    .login-animation#{$i} {
      opacity: 0;
      animation-name: error-num;
      animation-duration: 0.5s;
      animation-fill-mode: forwards;
      animation-delay: calc($i/10) + s;
    }
  }

  .login-content-password {
    display: inline-block;
    width: 20px;
    cursor: pointer;

    &:hover {
      color: #909399;
    }
  }

  .login-content-code {
    width: 100%;
    padding: 0;
    font-weight: bold;
    letter-spacing: 5px;
  }

  .login-content-submit {
    width: 100%;
    letter-spacing: 2px;
    font-weight: 300;
    margin-top: 15px;
  }

  // 登录按钮所在的 form-item 去掉底部间距
  .login-animation4 {
    :deep(.el-form-item__content) {
      border-bottom: none !important;
    }
  }
}
</style>
