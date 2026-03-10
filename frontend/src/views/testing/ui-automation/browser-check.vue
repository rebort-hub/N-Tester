<template>
  <div class="browser-check-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="title">
            <el-icon><Monitor /></el-icon>
            浏览器可用性检查
          </span>
          <el-button type="primary" :icon="Refresh" @click="checkAllBrowsers" :loading="loading">
            刷新检查
          </el-button>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="statistics-row">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-card stat-card-success">
              <div class="stat-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ availableCount }}</div>
                <div class="stat-label">可用浏览器</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card stat-card-danger">
              <div class="stat-icon">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ unavailableCount }}</div>
                <div class="stat-label">不可用浏览器</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card stat-card-primary">
              <div class="stat-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ totalCount }}</div>
                <div class="stat-label">总计</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card stat-card-warning">
              <div class="stat-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ availabilityRate }}%</div>
                <div class="stat-label">可用率</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 浏览器列表 -->
      <el-table :data="browsers" v-loading="loading" border stripe class="browser-table">
        <el-table-column label="浏览器" width="180">
          <template #default="{ row }">
            <div class="browser-info">
              <span class="browser-icon" v-html="getBrowserIcon(row.browser_type)"></span>
              <span class="browser-name">{{ getBrowserName(row.browser_type) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_available ? 'success' : 'danger'" size="large" class="status-tag">
              <el-icon><component :is="row.is_available ? 'CircleCheck' : 'CircleClose'" /></el-icon>
              {{ row.is_available ? '可用' : '不可用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="说明" min-width="300">
          <template #default="{ row }">
            <div class="message-content">
              <el-icon v-if="row.is_available" class="success-icon"><SuccessFilled /></el-icon>
              <el-icon v-else class="error-icon"><WarningFilled /></el-icon>
              <span>{{ row.message }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              v-if="!row.is_available" 
              type="primary" 
              size="small"
              :icon="Document"
              @click="showInstallGuide(row)"
            >
              安装指南
            </el-button>
            <el-button 
              v-else
              type="success" 
              size="small"
              :icon="Check"
              disabled
            >
              已安装
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 提示信息 -->
      <el-alert
        title="提示"
        type="info"
        :closable="false"
        class="tip-alert"
      >
        <template #default>
          <div class="tip-content">
            <p><strong>关于浏览器检查：</strong></p>
            <ul>
              <li>此功能会检测系统中已安装的浏览器</li>
              <li>Selenium 引擎支持：Chrome、Firefox、Edge、Safari（仅 macOS）</li>
              <li>Playwright 引擎支持：Chromium、Firefox、WebKit</li>
              <li>首次使用时，webdriver-manager 会自动下载对应的浏览器驱动</li>
              <li>建议至少安装一个浏览器以进行 UI 自动化测试</li>
            </ul>
          </div>
        </template>
      </el-alert>
    </el-card>

    <!-- 安装指南对话框 -->
    <el-dialog
      v-model="installGuideVisible"
      :title="`${currentBrowser?.browser_type} 安装指南`"
      width="600px"
    >
      <div class="install-guide" v-if="currentBrowser">
        <el-alert
          :title="`${getBrowserName(currentBrowser.browser_type)} 浏览器未安装`"
          type="warning"
          :closable="false"
          show-icon
        />

        <div class="install-steps">
          <h3>安装方法：</h3>
          
          <el-tabs v-model="activeTab">
            <el-tab-pane label="Windows" name="windows">
              <div class="install-content">
                <p class="install-desc">{{ getInstallTip(currentBrowser.browser_type, 'windows') }}</p>
                <el-button type="primary" @click="openDownloadLink(currentBrowser.browser_type)">
                  前往下载
                </el-button>
              </div>
            </el-tab-pane>

            <el-tab-pane label="macOS" name="macos">
              <div class="install-content">
                <p class="install-desc">使用 Homebrew 安装（推荐）：</p>
                <el-input
                  :value="getInstallCommand(currentBrowser.browser_type, 'macos')"
                  readonly
                  class="command-input"
                >
                  <template #append>
                    <el-button @click="copyCommand(getInstallCommand(currentBrowser.browser_type, 'macos'))">
                      <el-icon><DocumentCopy /></el-icon>
                      复制
                    </el-button>
                  </template>
                </el-input>
                <p class="install-note">或者前往官网下载安装包</p>
              </div>
            </el-tab-pane>

            <el-tab-pane label="Linux" name="linux">
              <div class="install-content">
                <p class="install-desc">使用包管理器安装：</p>
                <el-input
                  :value="getInstallCommand(currentBrowser.browser_type, 'linux')"
                  readonly
                  class="command-input"
                >
                  <template #append>
                    <el-button @click="copyCommand(getInstallCommand(currentBrowser.browser_type, 'linux'))">
                      <el-icon><DocumentCopy /></el-icon>
                      复制
                    </el-button>
                  </template>
                </el-input>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>

        <el-alert
          title="安装后请刷新此页面以重新检查浏览器可用性"
          type="success"
          :closable="false"
          show-icon
          class="refresh-tip"
        />
      </div>

      <template #footer>
        <el-button @click="installGuideVisible = false">关闭</el-button>
        <el-button type="primary" @click="checkAllBrowsers">重新检查</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Monitor, Refresh, CircleCheck, CircleClose, TrendCharts, 
  Document, Check, SuccessFilled, WarningFilled, DocumentCopy 
} from '@element-plus/icons-vue'
import { uiBrowserApi } from '/@/api/v1/ui_automation'

// 定义组件名称
defineOptions({
  name: 'BrowserCheck'
})

interface Browser {
  browser_type: string
  is_available: boolean
  message: string
}

const loading = ref(false)
const browsers = ref<Browser[]>([])
const installGuideVisible = ref(false)
const currentBrowser = ref<Browser | null>(null)
const activeTab = ref('windows')

// 统计数据
const availableCount = computed(() => browsers.value.filter(b => b.is_available).length)
const unavailableCount = computed(() => browsers.value.filter(b => !b.is_available).length)
const totalCount = computed(() => browsers.value.length)
const availabilityRate = computed(() => {
  if (totalCount.value === 0) return 0
  return Math.round((availableCount.value / totalCount.value) * 100)
})

// 检查所有浏览器
const checkAllBrowsers = async () => {
  loading.value = true
  try {
    const res = await uiBrowserApi.checkAll()
    if (res.code === 200) {
      browsers.value = res.data.browsers
      ElMessage.success('浏览器检查完成')
    }
  } catch (error) {
    ElMessage.error('检查失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 获取浏览器名称
const getBrowserName = (type: string) => {
  const names: Record<string, string> = {
    chrome: 'Google Chrome',
    firefox: 'Mozilla Firefox',
    edge: 'Microsoft Edge',
    safari: 'Apple Safari'
  }
  return names[type] || type
}

// 获取浏览器图标（使用 SVG）
const getBrowserIcon = (type: string) => {
  const icons: Record<string, string> = {
    chrome: `<svg viewBox="0 0 24 24" width="28" height="28">
      <circle cx="12" cy="12" r="10" fill="#4285F4"/>
      <circle cx="12" cy="12" r="7" fill="white"/>
      <circle cx="12" cy="12" r="4.5" fill="#4285F4"/>
      <path d="M12 2 L12 7 L7 12 L12 12 Z" fill="#EA4335"/>
      <path d="M12 7 L17 12 L12 17 L12 12 Z" fill="#FBBC04"/>
      <path d="M7 12 L12 17 L12 22 L12 12 Z" fill="#34A853"/>
    </svg>`,
    firefox: `<svg viewBox="0 0 24 24" width="28" height="28">
      <circle cx="12" cy="12" r="10" fill="#FF7139"/>
      <path d="M12 4 Q16 6 16 10 Q16 14 12 16 Q8 14 8 10 Q8 6 12 4 Z" fill="#FF9500"/>
      <ellipse cx="12" cy="11" rx="4" ry="5" fill="#FFCA00"/>
    </svg>`,
    edge: `<svg viewBox="0 0 24 24" width="28" height="28">
      <path d="M3 12 Q3 6 8 4 Q13 2 18 6 Q21 9 21 12 Q21 18 15 21 Q9 24 4 18 Q3 15 3 12 Z" fill="#0078D7"/>
      <path d="M8 8 Q12 6 16 8 Q18 10 18 13 Q18 16 15 18 Q12 20 9 18 Q6 16 6 13 Q6 10 8 8 Z" fill="#00BCF2"/>
    </svg>`,
    safari: `<svg viewBox="0 0 24 24" width="28" height="28">
      <circle cx="12" cy="12" r="10" fill="#006CFF"/>
      <circle cx="12" cy="12" r="8" fill="white"/>
      <path d="M12 4 L12 20 M4 12 L20 12" stroke="#006CFF" stroke-width="1"/>
      <path d="M12 6 L14 12 L12 18 L10 12 Z" fill="#FF3B30"/>
    </svg>`
  }
  return icons[type] || icons.chrome
}

// 显示安装指南
const showInstallGuide = (browser: Browser) => {
  currentBrowser.value = browser
  installGuideVisible.value = true
}

// 获取安装提示
const getInstallTip = (browserType: string, platform: string) => {
  const tips: Record<string, Record<string, string>> = {
    chrome: {
      windows: '访问 Google Chrome 官网下载最新版本的安装包',
      macos: '使用 Homebrew 或访问官网下载',
      linux: '使用系统包管理器安装'
    },
    firefox: {
      windows: '访问 Mozilla Firefox 官网下载最新版本的安装包',
      macos: '使用 Homebrew 或访问官网下载',
      linux: '使用系统包管理器安装'
    },
    edge: {
      windows: 'Windows 10+ 系统自带 Microsoft Edge 浏览器',
      macos: '使用 Homebrew 或访问官网下载',
      linux: '访问 Microsoft Edge 官网下载 Linux 版本'
    },
    safari: {
      windows: 'Safari 浏览器不支持 Windows 系统',
      macos: 'macOS 系统自带 Safari 浏览器，需执行: sudo safaridriver --enable',
      linux: 'Safari 浏览器不支持 Linux 系统'
    }
  }
  return tips[browserType]?.[platform] || '请访问官网下载'
}

// 获取安装命令
const getInstallCommand = (browserType: string, platform: string) => {
  const commands: Record<string, Record<string, string>> = {
    chrome: {
      macos: 'brew install --cask google-chrome',
      linux: 'sudo apt-get install google-chrome-stable'
    },
    firefox: {
      macos: 'brew install --cask firefox',
      linux: 'sudo apt-get install firefox'
    },
    edge: {
      macos: 'brew install --cask microsoft-edge',
      linux: 'curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg && sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/'
    },
    safari: {
      macos: 'sudo safaridriver --enable',
      linux: 'Safari 不支持 Linux'
    }
  }
  return commands[browserType]?.[platform] || ''
}

// 复制命令
const copyCommand = (command: string) => {
  navigator.clipboard.writeText(command).then(() => {
    ElMessage.success('命令已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

// 打开下载链接
const openDownloadLink = (browserType: string) => {
  const links: Record<string, string> = {
    chrome: 'https://www.google.com/chrome/',
    firefox: 'https://www.mozilla.org/firefox/',
    edge: 'https://www.microsoft.com/edge',
    safari: 'https://www.apple.com/safari/'
  }
  const link = links[browserType]
  if (link) {
    window.open(link, '_blank')
  }
}

onMounted(() => {
  checkAllBrowsers()
})
</script>

<style scoped lang="scss">
.browser-check-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .statistics-row {
    margin-bottom: 24px;

    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      border-radius: 8px;
      color: white;
      box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
      transition: transform 0.3s ease, box-shadow 0.3s ease;

      &:hover {
        transform: translateY(-4px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      }

      // Element Plus 成功色 - 绿色
      &.stat-card-success {
        background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
      }

      // Element Plus 危险色 - 红色
      &.stat-card-danger {
        background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
      }

      // Element Plus 主色 - 蓝色
      &.stat-card-primary {
        background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
      }

      // Element Plus 警告色 - 橙色
      &.stat-card-warning {
        background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
      }

      .stat-icon {
        font-size: 48px;
        margin-right: 16px;
        opacity: 0.9;
      }

      .stat-content {
        flex: 1;

        .stat-value {
          font-size: 32px;
          font-weight: 700;
          line-height: 1;
          margin-bottom: 8px;
        }

        .stat-label {
          font-size: 14px;
          opacity: 0.9;
        }
      }
    }
  }

  .browser-table {
    margin-bottom: 20px;

    :deep(.el-table__cell) {
      vertical-align: middle;
    }

    .status-tag {
      display: inline-flex !important;
      align-items: center !important;
      justify-content: center;
      gap: 4px;
      line-height: 1;
      
      :deep(.el-icon) {
        display: flex;
        align-items: center;
        margin: 0;
      }
      
      :deep(span) {
        display: flex;
        align-items: center;
        line-height: 1;
      }
    }

    .browser-info {
      display: flex;
      align-items: center;
      gap: 12px;

      .browser-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;

        :deep(svg) {
          width: 28px;
          height: 28px;
        }
      }

      .browser-name {
        font-weight: 500;
        font-size: 14px;
      }
    }

    .message-content {
      display: flex;
      align-items: center;
      gap: 8px;

      .success-icon {
        color: #67c23a;
      }

      .error-icon {
        color: #f56c6c;
      }
    }
  }

  .tip-alert {
    margin-top: 20px;

    .tip-content {
      p {
        margin-bottom: 8px;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          margin-bottom: 4px;
          line-height: 1.6;
        }
      }
    }
  }

  .install-guide {
    .install-steps {
      margin-top: 20px;

      h3 {
        margin-bottom: 16px;
        font-size: 16px;
      }

      .install-content {
        padding: 16px 0;

        .install-desc {
          margin-bottom: 12px;
          color: #606266;
        }

        .command-input {
          margin-bottom: 12px;
          font-family: 'Courier New', monospace;
        }

        .install-note {
          margin-top: 12px;
          font-size: 14px;
          color: #909399;
        }
      }
    }

    .refresh-tip {
      margin-top: 20px;
    }
  }
}
</style>
