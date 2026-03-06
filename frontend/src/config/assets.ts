/**
 * 资源配置文件
 * 统一管理系统中使用的图片资源路径
 */

// 背景图配置
export const backgroundImages = {
  // 登录页背景图
  loginBg: new URL('../assets/bakgrounImage/N-Tester.png', import.meta.url).href,
  // 锁屏背景图
  lockScreenBg: new URL('../assets/bakgrounImage/N-Tester.png', import.meta.url).href,
  // 默认背景图（可用于其他页面）
  defaultBg: new URL('../assets/bakgrounImage/bakgrounImage.jpg', import.meta.url).href,
};

// Logo配置
export const logos = {
  // 主Logo
  main: new URL('../assets/logo.svg', import.meta.url).href,
  // 白色Logo（用于深色背景）
  white: new URL('../assets/whiteLogo.svg', import.meta.url).href,
  // 迷你Logo（用于折叠菜单）
  mini: new URL('../assets/logo-mini.png', import.meta.url).href,
};

// 其他图片资源
export const images = {
  // 登录页装饰图
  loginMain: new URL('../assets/login-main.svg', import.meta.url).href,
  loginBgSvg: new URL('../assets/login-bg.svg', import.meta.url).href,
  // 微信二维码
  weixin: new URL('../assets/weixin.png', import.meta.url).href,
};

// 错误页面图片
export const errorImages = {
  error401: new URL('../assets/error/401.svg', import.meta.url).href,
  error404: new URL('../assets/error/404.svg', import.meta.url).href,
};

/**
 * 获取背景图样式对象
 * @param imageUrl 图片URL
 * @param options 额外的样式选项
 */
export const getBackgroundStyle = (
  imageUrl: string,
  options?: {
    size?: string;
    position?: string;
    repeat?: string;
    attachment?: string;
  }
) => {
  return {
    backgroundImage: `url(${imageUrl})`,
    backgroundSize: options?.size || 'cover',
    backgroundPosition: options?.position || 'center center',
    backgroundRepeat: options?.repeat || 'no-repeat',
    backgroundAttachment: options?.attachment || 'fixed',
  };
};

export default {
  backgroundImages,
  logos,
  images,
  errorImages,
  getBackgroundStyle,
};
