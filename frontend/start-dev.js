#!/usr/bin/env node

// 设置环境变量来静默Sass警告
process.env.SASS_SILENCE_DEPRECATIONS = 'legacy-js-api,import';

// 启动Vite开发服务器
const { spawn } = require('child_process');

const vite = spawn('npx', ['vite', '--force'], {
  stdio: 'inherit',
  shell: true,
  env: {
    ...process.env,
    SASS_SILENCE_DEPRECATIONS: 'legacy-js-api,import'
  }
});

vite.on('close', (code) => {
  process.exit(code);
});

vite.on('error', (err) => {
  console.error('启动失败:', err);
  process.exit(1);
});