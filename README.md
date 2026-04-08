# N-Tester AI 全栈测试平台

<div align="center">

**基于 FastAPI + Vue3 的AI智能化全栈测试管理平台**

一个集成AI智能、API测试、UI自动化、数据工厂、评审管理等功能的企业级测试平台

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5.8-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---
## 线上体验地址
http://106.54.166.76
用户：admin  密码：123456

## 🌈 项目介绍

N-Tester AI 全栈测试平台是一个面向企业级应用的现代化智能测试管理系统，采用前后端完全分离的架构设计，集成了AI智能测试、API接口测试、UI自动化测试、数据工厂、评审管理等多个核心功能模块。

**核心特性：**
- 🤖 AI智能测试：集成大语言模型，智能生成测试用例和执行测试
- 🔌 API接口测试：完整的API测试生命周期管理
- 🖥️ UI自动化测试：支持Web UI自动化测试执行和管理
- 🏭 数据工厂：强大的测试数据生成和管理工具
- 📋 评审管理：完善的测试用例评审流程
- 📊 智能报告：可视化测试报告和数据分析
- 🔐 完整的 RBAC 权限管理体系
- 📱  统一通知系统：支持飞书、钉钉、微信、Telegram、邮件等多种通知方式
- 🎯 动态路由注册，配置即可分配权限
- 🛡️ 多层级权限控制（菜单权限、按钮权限、数据权限、API权限）
- 📊 完善的日志管理系统（登录日志、操作日志）
- 🎨 支持主题切换和暗黑模式
- 📦 Docker 一键部署
- ⚡ 异步高性能架构

---

## 📋 技术栈

### 环境要求

| 技术        | 版本      | 说明      |
|-----------|---------|---------|
| Python    | < 3.13  | 后端运行环境  |
| Node.js   | 20.0 | 前端构建环境  |
| MySQL     | 8.0.23  | 主数据库    |
| Redis     | 6.0.9   | 缓存和任务队列 |

### 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.111.0 | 异步 Web 框架 |
| SQLAlchemy | 2.0.3 | 异步 ORM |
| Pydantic | 2.7.3 | 数据验证 |
| Alembic | 1.13.1 | 数据库迁移 |
| Celery | 5.2.7 | 异步任务队列 |
| Redis | 5.0.4 | 缓存和消息队列 |
| Loguru | 0.6.0 | 日志系统 |
| python-jose | 3.3.0 | JWT 认证 |
| asyncmy | 0.2.9 | 异步 MySQL 驱动 |

### 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5.8 | 渐进式框架 |
| Vite | 5.4.8 | 构建工具 |
| TypeScript | 4.9.4 | 类型系统 |
| Element Plus | 2.7.4 | UI 组件库 |
| Pinia | 2.0.28 | 状态管理 |
| Vue Router | 4.1.6 | 路由管理 |
| Axios | 1.2.1 | HTTP 客户端 |
| Monaco Editor | 0.34.1 | 代码编辑器 |
| ECharts | 5.6.0 | 数据可视化 |

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户层                               │
│                    (浏览器 / 移动端)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      前端层 (Vue 3)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  路由    │  │  状态    │  │  组件    │  │  指令    │   │
│  │ Router   │  │  Pinia   │  │ Element  │  │ 权限控制 │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   API 网关层 (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  认证    │  │  限流    │  │  日志    │  │  异常    │   │
│  │ 中间件   │  │ 中间件   │  │ 中间件   │  │  处理    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层 (Services)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ AI智能   │  │ API测试  │  │ UI自动化 │  │ 数据工厂 │   │
│  │ 测试     │  │ 服务     │  │ 服务     │  │ 服务     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 评审管理 │  │ 项目管理 │  │ 通知系统 │  │ 权限管理 │   │
│  │ 服务     │  │ 服务     │  │ 服务     │  │ 服务     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  数据访问层 (SQLAlchemy)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Models  │  │ Schemas  │  │  会话    │  │  事务    │   │
│  │  定义    │  │  验证    │  │  管理    │  │  管理    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┬──────────────┐
         ▼                               ▼              ▼
┌──────────────────┐          ┌──────────────┐  ┌─────────────┐
│   MySQL 8.0      │          │  Redis 6.0   │  │   Celery    │
│   主数据库       │          │  缓存/队列   │  │  任务队列   │
└──────────────────┘          └──────────────┘  └─────────────┘
```

### 核心功能模块

```
N-Tester AI 全栈测试平台
├── 🤖 AI智能测试模块
│   ├── AI对话助手          # 智能测试咨询和建议
│   ├── 智能用例生成        # 基于需求自动生成测试用例
│   ├── 智能执行引擎        # AI驱动的测试执行
│   └── LLM配置管理         # 大语言模型配置和管理
│
├── 🔌 API接口测试模块
│   ├── 接口项目管理        # API项目和环境管理
│   ├── 接口用例设计        # 接口测试用例编写
│   ├── 批量执行引擎        # 批量接口测试执行
│   ├── 断言验证系统        # 多种断言规则支持
│   └── 测试报告生成        # 详细的测试报告
│
├── 🖥️ UI自动化测试模块
│   ├── 页面元素管理        # Web元素定位和管理
│   ├── 测试脚本编写        # 自动化测试脚本
│   ├── 执行计划调度        # 定时和批量执行
│   ├── 截图和录像          # 执行过程记录
│   └── 失败重试机制        # 智能重试策略
│
├── 🏭 数据工厂模块
│   ├── 数据模板管理        # 测试数据模板定义
│   ├── 批量数据生成        # 大量测试数据生成
│   ├── 数据关联规则        # 数据间关联关系
│   ├── 数据导入导出        # 多格式数据交换
│   └── 数据清理工具        # 测试数据清理
│
├── 📋 评审管理模块
│   ├── 评审流程配置        # 自定义评审流程
│   ├── 用例评审管理        # 测试用例评审
│   ├── 评审意见收集        # 评审意见和建议
│   ├── 评审报告生成        # 评审结果报告
│   └── 评审统计分析        # 评审效率分析
│
├── 📊 项目管理模块
│   ├── 项目信息管理        # 项目基本信息
│   ├── 成员权限管理        # 项目成员和权限
│   ├── 环境配置管理        # 测试环境配置
│   ├── 版本管理系统        # 项目版本控制
│   └── 进度跟踪统计        # 项目进度监控
│
├── 📱 通知系统模块
│   ├── 多渠道通知支持      # 飞书/钉钉/微信/邮件/Telegram
│   ├── 通知模板管理        # 自定义通知模板
│   ├── 通知历史记录        # 通知发送历史
│   ├── 任务通知设置        # 任务相关通知配置
│   └── 通知统计分析        # 通知效果分析
│
├── 🔐 系统管理模块
│   ├── 用户管理系统        # 用户账号管理
│   ├── 角色权限管理        # RBAC权限体系
│   ├── 菜单路由管理        # 动态菜单配置
│   ├── 操作日志管理        # 系统操作审计
│   └── 系统监控面板        # 系统状态监控
│
└── 📈 数据分析模块
    ├── 测试数据统计        # 测试执行统计
    ├── 质量趋势分析        # 质量指标趋势
    ├── 效率分析报告        # 测试效率分析
    ├── 可视化图表          # 多维度数据展示
    └── 自定义报表          # 个性化报表定制
```

### 后端分层架构

```
backend/
├── app/
│   ├── api/               # API 路由层 - 处理 HTTP 请求
│   │   ├── v1/            # API 版本控制
│   │   │   ├── system/    # 系统管理模块
│   │   │   ├── projects/  # 项目管理模块
│   │   │   ├── testing/   # 测试管理模块
│   │   │   ├── ai/        # AI智能测试模块
│   │   │   ├── notifications/ # 通知系统模块
│   │   │   ├── reviews/   # 评审管理模块
│   │   │   ├── dashboard/ # 数据面板模块
│   │   │   └── common/    # 公共模块
│   │   └── __init__.py    # 路由注册
│   │
│   ├── core/              # 核心功能层
│   │   ├── base_crud.py   # 基础 CRUD 操作
│   │   ├── base_model.py  # 基础模型
│   │   ├── base_schema.py # 基础 Schema
│   │   ├── permission.py  # 权限控制核心
│   │   ├── data_permission.py # 数据权限过滤
│   │   └── api_permission.py  # API权限控制
│   │
│   ├── models/            # 数据模型层 - ORM 模型定义
│   │   ├── rbac_models.py # RBAC 权限模型
│   │   ├── api_models.py  # API 测试模型
│   │   ├── ai/            # AI 模块模型
│   │   └── base.py        # 基础模型
│   │
│   ├── schemas/           # 数据验证层 - Pydantic 模型
│   │   ├── base.py        # 基础 Schema
│   │   ├── common.py      # 公共 Schema
│   │   └── __init__.py    # Schema 导出
│   │
│   ├── services/          # 业务服务层
│   │   ├── ai/            # AI 服务
│   │   └── __init__.py    # 服务导出
│   │
│   ├── utils/             # 工具函数
│   │   ├── common.py      # 通用工具
│   │   ├── security.py    # 安全工具
│   │   ├── document_extractor.py # 文档提取工具
│   │   └── excel_importer.py # Excel导入工具
│   │
│   └── static/            # 静态文件
│       ├── upload/        # 上传文件
│       ├── templates/     # 模板文件
│       └── swagger/       # API 文档资源
│
├── celery_worker/         # Celery 任务
│   ├── tasks/             # 任务定义
│   ├── scheduler/         # 定时任务调度器
│   └── worker.py          # Worker 配置
│
├── alembic/               # 数据库迁移
│   └── versions/          # 迁移版本文件
│
├── script/                # SQL脚本文件
│   ├── system_menu.sql    # 系统菜单
│   ├── api_testing_menu.sql # API测试菜单
│   ├── ai_module_menu.sql # AI模块菜单
│   └── notification_module_menu.sql # 通知模块菜单
│
├── config.py              # 配置文件
├── main.py                # 应用入口
└── requirements           # 依赖文件
```

### 前端目录架构

```
frontend/src/
├── api/                   # API 接口封装
│   ├── v1/                # API 版本控制
│   │   ├── system/        # 系统管理接口
│   │   ├── projects/      # 项目管理接口
│   │   ├── testing/       # 测试管理接口
│   │   ├── ai/            # AI智能测试接口
│   │   ├── notifications/ # 通知系统接口
│   │   ├── reviews/       # 评审管理接口
│   │   └── dashboard/     # 数据面板接口
│   └── request.ts         # 请求封装
│
├── views/                 # 页面视图
│   ├── system/            # 系统管理
│   ├── projects/          # 项目管理
│   ├── testing/           # 测试管理
│   │   ├── api-testing/   # API接口测试
│   │   ├── ui-automation/ # UI自动化测试
│   │   ├── data-factory/  # 数据工厂
│   │   ├── testcases/     # 测试用例管理
│   │   ├── modules/       # 模块管理
│   │   └── versions/      # 版本管理
│   ├── ai/                # AI智能测试
│   │   ├── chat/          # AI对话助手
│   │   ├── intelligence/  # 智能测试
│   │   └── llmConfig/     # LLM配置
│   ├── notifications/     # 通知系统
│   │   ├── configs/       # 通知配置
│   │   ├── histories/     # 通知历史
│   │   └── task-settings/ # 任务通知设置
│   ├── reviews/           # 评审管理
│   ├── assistant/         # 智能助手
│   ├── monitor/           # 系统监控
│   ├── home/              # 首页仪表板
│   ├── login/             # 登录页
│   └── error/             # 错误页面
│
├── components/            # 公共组件
│   ├── Z-Table/           # 表格组件
│   ├── CodeGenerator/     # 代码生成器
│   ├── monaco/            # 代码编辑器
│   └── ZeroCard/          # 卡片组件
│
├── stores/                # Pinia 状态管理
│   ├── user.ts            # 用户状态
│   ├── auth.ts            # 认证状态
│   ├── menu.ts            # 菜单状态
│   └── themeConfig.ts     # 主题配置
│
├── utils/                 # 工具函数
│   ├── request.ts         # HTTP 请求封装
│   ├── authFunction.ts    # 权限验证函数
│   ├── common.ts          # 通用工具
│   └── formatTime.ts      # 时间格式化
│
├── theme/                 # 主题配置
│   ├── index.scss         # 主题入口
│   ├── dark.scss          # 暗色主题
│   └── element.scss       # Element Plus 样式
│
└── config/                # 配置文件
    └── assets.ts          # 资源配置
```

---

## ✨ 核心特性

### 🤖 AI智能测试模块

#### 1. AI对话助手
- **智能咨询**：基于大语言模型的测试咨询和建议
- **上下文理解**：理解项目背景，提供针对性建议
- **多轮对话**：支持连续对话，深入探讨测试问题
- **知识库集成**：集成测试最佳实践和经验知识

#### 2. 智能用例生成
- **需求分析**：自动分析需求文档，提取测试点
- **用例生成**：基于需求自动生成结构化测试用例
- **边界值分析**：智能识别边界条件和异常场景
- **用例优化**：根据历史数据优化用例覆盖率

#### 3. 智能执行引擎
- **自适应执行**：根据执行结果动态调整测试策略
- **异常处理**：智能识别和处理执行过程中的异常
- **结果分析**：自动分析测试结果，生成问题报告
- **持续学习**：从执行历史中学习，提升测试效率

### 🔌 API接口测试模块

#### 1. 完整的API测试生命周期
- **项目管理**：支持多项目、多环境的API测试管理
- **接口设计**：可视化接口用例设计和参数配置
- **批量执行**：支持单个、批量、定时执行测试用例
- **断言验证**：多种断言规则，支持JSON Path、正则表达式等

#### 2. 高级测试功能
- **数据驱动**：支持Excel、CSV等数据源驱动测试
- **参数化测试**：动态参数替换和数据关联
- **前置后置**：支持前置条件和后置清理操作
- **Mock服务**：内置Mock服务，支持接口模拟

#### 3. 测试报告和分析
- **详细报告**：生成详细的测试执行报告
- **趋势分析**：测试结果趋势分析和质量监控
- **性能监控**：接口响应时间和性能指标监控
- **失败分析**：自动分析失败原因，提供修复建议

### 🖥️ UI自动化测试模块

#### 1. 元素管理系统
- **智能定位**：多种元素定位策略，提高稳定性
- **元素库管理**：统一管理页面元素，支持复用
- **动态等待**：智能等待机制，处理页面加载时序
- **元素验证**：自动验证元素有效性，及时发现变更

#### 2. 脚本编写和执行
- **可视化编写**：拖拽式脚本编写，降低技术门槛
- **代码生成**：自动生成Selenium/Playwright代码
- **并发执行**：支持多浏览器并发执行测试
- **失败重试**：智能重试机制，提高执行稳定性

#### 3. 执行监控和报告
- **实时监控**：实时查看测试执行状态和进度
- **截图录像**：自动截图和录像，记录执行过程
- **详细日志**：完整的执行日志，便于问题定位
- **Allure报告**：集成Allure，生成专业测试报告

### 🏭 数据工厂模块

#### 1. 数据模板管理
- **模板定义**：灵活定义数据模板和生成规则
- **数据类型**：支持多种数据类型和格式
- **关联规则**：定义数据间的关联关系和约束
- **版本管理**：数据模板版本控制和变更管理

#### 2. 批量数据生成
- **大量生成**：支持百万级测试数据快速生成
- **多格式导出**：支持Excel、CSV、JSON、SQL等格式
- **数据校验**：生成数据的完整性和一致性校验
- **增量生成**：支持增量数据生成和更新

#### 3. 数据管理工具
- **数据清理**：测试完成后自动清理测试数据
- **数据备份**：重要数据的备份和恢复功能
- **数据脱敏**：生产数据脱敏处理，保护隐私
- **数据同步**：多环境间数据同步和一致性保证

### 📋 评审管理模块

#### 1. 评审流程配置
- **自定义流程**：灵活配置评审流程和节点
- **角色权限**：不同角色的评审权限和职责
- **审批规则**：自定义审批规则和条件
- **通知机制**：评审状态变更自动通知相关人员

#### 2. 用例评审管理
- **在线评审**：支持在线查看和评审测试用例
- **批注功能**：支持添加评审意见和建议
- **版本对比**：用例版本对比，跟踪变更历史
- **评审统计**：评审效率和质量统计分析

#### 3. 评审报告和分析
- **评审报告**：生成详细的评审结果报告
- **问题跟踪**：评审问题的跟踪和解决状态
- **质量分析**：用例质量分析和改进建议
- **效率监控**：评审效率监控和流程优化

### 📱 统一通知系统

#### 1. 多渠道通知支持
- **企业通讯**：飞书、钉钉、企业微信集成
- **即时通讯**：Telegram、微信通知
- **邮件通知**：SMTP邮件发送支持
- **Webhook**：自定义Webhook通知

#### 2. 智能通知管理
- **通知模板**：自定义通知模板和格式
- **通知规则**：基于条件的智能通知规则
- **通知历史**：完整的通知发送历史记录
- **失败重试**：通知发送失败自动重试机制

### 🔐 企业级权限管理

#### 1. RBAC权限体系
- **用户管理**：完整的用户生命周期管理
- **角色管理**：灵活的角色定义和权限分配
- **菜单权限**：动态菜单权限控制
- **按钮权限**：页面级按钮权限控制

#### 2. 数据权限控制
- **数据范围**：支持5种数据权限范围
- **部门权限**：基于部门的数据权限过滤
- **个人权限**：个人数据权限控制
- **自定义权限**：灵活的自定义权限规则

#### 3. 安全审计
- **登录日志**：详细的用户登录行为记录
- **操作日志**：完整的用户操作审计跟踪
- **权限变更**：权限变更历史和审计
- **安全监控**：异常行为检测和告警

---

## 🚀 快速开始
### 方式一：Docker 部署（推荐）

#### 1. 克隆项目

```bash
git clone https://github.com/rebort-hub/N-Tester.git
cd N-Tester
```

#### 2. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑 .env 文件，配置数据库密码等信息
```

#### 3. Docker部署，启动服务

```bash
# 一键启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

#### 4. 访问系统

- 前端地址：http://localhost
- 后端 API：http://localhost:8100
- API 文档：http://localhost:8100/docs

**默认账号**：admin / 123456   也可以快捷方式登录

---

### 方式二：源码部署

#### 后端部署

##### 1. 环境准备

```bash
# 确保已安装 Python 3.11-12、MySQL 8.0、Redis 6.0
python --version
mysql --version
redis-server --version
```

##### 2. 创建数据库

```sql
CREATE DATABASE ntester CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

##### 3. 配置环境

```bash
cd backend

# 复制配置文件
cp .env.example .env

# 编辑 .env 文件，修改数据库连接信息
# MYSQL_DATABASE_URI=mysql+asyncmy://用户名:密码@localhost:3306/ntester
# REDIS_URI=redis://localhost:6379/4
```
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

##### 4. 安装依赖

```bash
# 安装依赖(linux&mac)
pip install -r requirements
# windows 用户
pip install -r requirements-windows.txt
```

##### 5. 初始化数据库

```bash
# 一键初始化（推荐）
python cli.py init-db


# 或手动使用 Alembic
alembic upgrade heads
python cli.py init-data
```

##### 6. 启动后端服务

```bash
# 开发模式
python main.py

# 定时任务启动
python scheduler_runner.py

# 生产模式
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8100
```

##### 7. 启动 Celery（可选）

```bash
# Windows 启动 Worker（单线程）
celery -A celery_worker.worker.celery worker --pool=solo -l INFO

# Linux 启动 Worker（多线程）
celery -A celery_worker.worker.celery worker --loglevel=INFO -c 10 -P solo -n ntester-celery-worker

# 启动定时任务调度器
celery -A celery_worker.worker.celery beat -S celery_worker.scheduler.schedulers:DatabaseScheduler -l INFO

# 启动心跳监控
celery -A celery_worker.worker.celery beat -l INFO
```

#### 前端部署

##### 1. 环境准备

```bash
# 确保已安装 Node.js >=20.0
node -v  # v20.0
```

##### 2. 安装依赖管理工具

```bash
# 安装 cnpm（使用淘宝镜像）
npm install -g cnpm --registry=https://registry.npm.taobao.org

# 或安装 yarn
npm install -g yarn
```

##### 3. 安装项目依赖

```bash
cd frontend

# 使用 cnpm
cnpm install

# 或使用 yarn
yarn install  --registry=https://registry.npm.taobao.org
```

##### 4. 启动开发服务器

```bash
# 使用 cnpm
cnpm run dev

# 或使用 yarn
yarn dev
```

访问：http://localhost:5173

##### 5. 生产构建

```bash
# 使用 cnpm
cnpm run build

# 或使用 yarn
yarn build

# 构建产物在 dist/ 目录
```

---

## 🗄️ 数据库管理

### Alembic 迁移命令

```bash
# 初始化数据库（包含迁移和初始数据）
python cli.py init-db

# 生成迁移文件
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

## 📸 系统截图

### 登录页
![登录页](static/img/func.png)

### 首页
![首页](static/img/index.png)

### 项目管理
![项目管理](static/img/report.png)

### UI自动化管理
![UI自动化管理](static/img/case.png)

### AI用例生成
![AI用例生成](static/img/cass.png)

### AI智能对话
![AI智能对话](static/img/aise.png)

### AI智能浏览器
![AI智能浏览器](static/img/aec.png)

### 个人中心
![个人中心1](static/img/ge.png)

### 主题切换
![主题切换1](static/img/csssb.png)

---

## 🔧 开发指南

### 后端开发

#### 添加新的 API 接口

1. 在 `app/models/` 创建数据模型
2. 在 `app/schemas/` 创建 Pydantic Schema
3. 在 `app/api/v1/` 创建路由处理器
4. 使用权限装饰器控制访问权限

#### 示例：创建用户管理接口

```python
# app/models/rbac_models.py
from app.models.base import Base
from sqlalchemy import Column, String, Integer

class User(Base):
    __tablename__ = "sys_user"
    
    username = Column(String(50), nullable=False, unique=True, comment='用户名')
    email = Column(String(100), nullable=True, comment='邮箱')
    status = Column(Integer, nullable=False, default=1, comment='状态')

# app/schemas/common.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: Optional[str] = None
    status: int = 1

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    status: int

# app/api/v1/system/user/controller.py
from fastapi import APIRouter, Depends
from app.core.api_permission import ApiPermission
from app.core.data_permission import DataPermission

router = APIRouter()

@router.post("/", response_model=UserResponse)
@ApiPermission("system:user:add")  # API权限控制
async def create_user(user: UserCreate):
    # 业务逻辑
    pass

@router.get("/", response_model=List[UserResponse])
@ApiPermission("system:user:list")
@DataPermission(data_scope="dept")  # 数据权限控制
async def get_users():
    # 业务逻辑
    pass
```

#### 权限系统使用

```python
# 数据权限装饰器
@DataPermission(
    data_scope="dept",  # 数据范围：dept, user, all, custom
    dept_field="dept_id",  # 部门字段名
    user_field="created_by"  # 用户字段名
)
async def get_filtered_data():
    # 会自动根据用户权限过滤数据
    pass

# API权限装饰器
@ApiPermission("system:user:edit")
async def update_user():
    # 会检查用户是否有对应的API权限
    pass
```

### 前端开发

#### 添加新页面

1. 在 `src/views/` 创建页面组件
2. 在 `src/router/routes.ts` 配置路由
3. 在 `src/api/` 创建接口调用
4. 在后台菜单管理中配置菜单

#### 示例：创建用户列表页面

```typescript
// src/api/user.ts
import request from './request'

export const getUserList = (params: any) => {
  return request.get('/api/v1/users', { params })
}

// src/views/system/user/index.vue
<template>
  <div class="user-container">
    <el-table :data="userList">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUserList } from '@/api/user'

const userList = ref([])

onMounted(async () => {
  const res = await getUserList({})
  userList.value = res.data
})
</script>

// src/router/routes.ts
{
  path: '/system/user',
  name: 'SystemUser',
  component: () => import('@/views/system/user/index.vue'),
  meta: { title: '用户管理', permission: 'system:user:list' }
}
```

#### 权限控制

```vue
<!-- 按钮级权限控制 -->
<el-button v-auth="'system:user:add'">新增用户</el-button>
<el-button v-auth="'system:user:edit'">编辑</el-button>
<el-button v-auth="'system:user:delete'">删除</el-button>

<!-- 批量操作权限控制 -->
<el-button v-auth="'system:user:delete'" :disabled="selectedRows.length === 0">
  批量删除
</el-button>

<!-- 表格配置 -->
<z-table
  :columns="columns"
  :data="tableData"
  :options="{ stripe: true, border: true }"
  @selection-change="handleSelectionChange"
>
  <!-- 添加选择列 -->
  { columnType: 'selection', width: '50', align: 'center' }
</z-table>
```

#### 日志管理功能

```vue
<!-- 登录日志页面示例 -->
<template>
  <div class="login-record-container">
    <!-- 搜索条件 -->
    <div class="search-form">
      <el-input v-model="queryParams.username" placeholder="用户名" />
      <el-date-picker v-model="dateRange" type="datetimerange" />
      <el-button @click="search">查询</el-button>
      <el-button v-auth="'system:log:login:delete'" @click="batchDelete">
        批量删除
      </el-button>
      <el-button v-auth="'system:log:login:clean'" @click="clearLogs">
        清理日志
      </el-button>
    </div>
    
    <!-- 数据表格 -->
    <z-table
      :columns="columns"
      :data="logData"
      :options="{ stripe: true, border: true }"
      @selection-change="handleSelectionChange"
    />
  </div>
</template>
```

---

---

## 📦 部署

### 生产环境部署

#### 使用 Docker Compose（推荐）

```bash
# 生产环境配置
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend
```

#### 手动部署

**后端部署：**

```bash
# 使用 Gunicorn + Uvicorn
gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8100 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

**前端部署：**

```bash
# 构建
npm run build

# 使用 Nginx 部署
# 将 dist/ 目录内容复制到 Nginx 静态目录
cp -r dist/* /usr/share/nginx/html/
```

**Nginx 配置示例：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://localhost:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 🛠️ 常见问题

### 后端问题

**Q: 数据库连接失败？**

A: 检查 `.env` 文件中的数据库配置，确保 MySQL 服务已启动。

**Q: Redis 连接失败？**

A: 确保 Redis 服务已启动，检查 `REDIS_URI` 配置。

**Q: Celery 任务不执行？**

A: 确保 Celery Worker 和 Beat 都已启动，检查 Redis 连接。

### 前端问题

**Q: 启动报错 "Cannot find module"？**

A: 删除 `node_modules` 和 `package-lock.json`，重新安装依赖。

**Q: 接口请求 404？**

A: 检查 `src/config/` 中的 API 地址配置。

**Q: 权限控制不生效？**

A: 
1. 确保后台已配置菜单权限，并分配给对应角色
2. 检查权限编码是否正确（如：`system:user:add`）
3. 确认用户已分配相应角色
4. 检查前端 v-auth 指令使用是否正确

**Q: 数据权限不生效？**

A: 
1. 确保在接口上使用了 `@DataPermission` 装饰器
2. 检查用户角色的数据权限范围配置
3. 确认数据表中有对应的部门字段或用户字段

**Q: 日志记录不完整？**

A: 
1. 确保日志中间件已正确配置
2. 检查数据库中的日志表是否存在
3. 确认 Redis 连接正常（用于日志缓存）

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范

**后端：**
- 遵循 PEP 8 规范
- 使用类型注解
- 编写单元测试

**前端：**
- 遵循 Vue 3 风格指南
- 使用 TypeScript
- 组件命名使用 PascalCase

---

## 📄 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

---

## 🔗 相关链接

- **GitHub**: https://github.com/rebort-hub/N-Tester
- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **Vue 3 文档**: https://vuejs.org/
- **Element Plus 文档**: https://element-plus.org/

---

## 💬 交流群

### 微信群
<img src="static/img/weixin.png" width="200" alt="微信群" />

### QQ 群
<img src="static/img/qq.png" width="200" alt="QQ群" />

### 打赏作者，可以请作者喝杯咖啡，你的鼓励将是更新最大的动力
<img src="static/img/wx.png" width="200" alt="wx" />

欢迎加入交流群，一起学习进步！

---

## 💌 支持作者

如果这个项目对你有帮助，请在 [GitHub](https://github.com/rebort-hub/N-Tester) 上给个 ⭐ Star 支持一下！

你的支持是我持续更新的动力 🚀

---

<div align="center">

**Made with ❤️ by Rebort**

**N-Tester AI 全栈测试平台 - 让测试更智能，让质量更可靠**

</div>
