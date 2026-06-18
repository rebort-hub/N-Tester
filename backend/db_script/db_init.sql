/*
 Navicat Premium Dump SQL

 Source Server         : rebort-测试开发平台开发
 Source Server Type    : MySQL
 Source Server Version : 80042 (8.0.42)
 Source Host           : localhost:3306
 Source Schema         : ntester

 Target Server Type    : MySQL
 Target Server Version : 80042 (8.0.42)
 File Encoding         : 65001

 Date: 09/04/2026 15:47:51
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;



-- ----------------------------
-- Table structure for ai_assistant_configs
-- ----------------------------
DROP TABLE IF EXISTS `ai_assistant_configs`;
CREATE TABLE `ai_assistant_configs`  (
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '助手名称',
  `dify_api_key` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Dify API Key',
  `dify_base_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Dify Base URL',
  `assistant_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '助手类型: chatbot/workflow/agent',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `created_by` bigint NOT NULL COMMENT '创建者ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_active`(`is_active` ASC) USING BTREE,
  INDEX `idx_created_by`(`created_by` ASC) USING BTREE,
  INDEX `ix_ai_assistant_configs_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_assistant_configs
-- ----------------------------


-- ----------------------------
-- Table structure for ai_cases
-- ----------------------------
DROP TABLE IF EXISTS `ai_cases`;
CREATE TABLE `ai_cases`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ui_project_id` bigint NULL DEFAULT NULL COMMENT '所属UI项目ID',
  `source_project_id` bigint NULL DEFAULT NULL COMMENT '来源项目ID（测试管理项目）',
  `source_module_id` bigint NULL DEFAULT NULL COMMENT '来源模块ID（测试管理模块）',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用例名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '描述',
  `task_description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务描述',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '状态: draft-草稿, active-激活, archived-归档',
  `source_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '来源类型: manual-手动创建, import-Excel导入, testcase-测试用例',
  `priority` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '优先级: P0-最高, P1-高, P2-中, P3-低',
  `precondition` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '前置条件',
  `test_steps` json NULL COMMENT '测试步骤',
  `expected_result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '预期结果',
  `execution_mode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行模式',
  `timeout` int NULL DEFAULT NULL COMMENT '超时时间(秒)',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建者ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `updated_by` bigint NULL DEFAULT NULL,
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI智能浏览器用例表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_cases
-- ----------------------------


-- ----------------------------
-- Table structure for ai_conversations
-- ----------------------------
DROP TABLE IF EXISTS `ai_conversations`;
CREATE TABLE `ai_conversations`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `assistant_config_id` bigint NOT NULL COMMENT '助手配置ID',
  `conversation_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Dify会话ID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '对话标题',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_assistant_config`(`assistant_config_id` ASC) USING BTREE,
  INDEX `idx_conversation_id`(`conversation_id` ASC) USING BTREE,
  INDEX `idx_user`(`user_id` ASC) USING BTREE,
  INDEX `ix_ai_conversations_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_conversations
-- ----------------------------


-- ----------------------------
-- Table structure for ai_execution_records
-- ----------------------------
DROP TABLE IF EXISTS `ai_execution_records`;
CREATE TABLE `ai_execution_records`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ui_project_id` bigint NULL DEFAULT NULL COMMENT '所属UI项目ID',
  `ai_case_id` bigint NULL DEFAULT NULL COMMENT '关联AI用例ID',
  `case_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用例名称快照',
  `task_description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '任务描述',
  `execution_mode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行模式',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行状态',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `duration` float NULL DEFAULT NULL COMMENT '执行时长(秒)',
  `logs` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行日志',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '错误信息',
  `steps_completed` json NULL COMMENT '已完成步骤',
  `planned_tasks` json NULL COMMENT '规划任务',
  `executed_by` bigint NULL DEFAULT NULL COMMENT '执行人ID',
  `gif_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'GIF录制路径',
  `screenshots_sequence` json NULL COMMENT '截图序列',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建者ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `updated_by` bigint NULL DEFAULT NULL,
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `total_tokens` int NULL DEFAULT NULL COMMENT 'Token总使用量',
  `prompt_tokens` int NULL DEFAULT NULL COMMENT '提示词Token数',
  `completion_tokens` int NULL DEFAULT NULL COMMENT '完成Token数',
  `api_calls` int NULL DEFAULT NULL COMMENT 'API调用次数',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI执行记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_execution_records
-- ----------------------------


-- ----------------------------
-- Table structure for ai_messages
-- ----------------------------
DROP TABLE IF EXISTS `ai_messages`;
CREATE TABLE `ai_messages`  (
  `conversation_id` bigint NOT NULL COMMENT '对话ID',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色: user/assistant',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '消息内容',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_conversation`(`conversation_id` ASC) USING BTREE,
  INDEX `idx_role`(`role` ASC) USING BTREE,
  INDEX `ix_ai_messages_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_messages
-- ----------------------------


-- ----------------------------
-- Table structure for ai_model_configs
-- ----------------------------
DROP TABLE IF EXISTS `ai_model_configs`;
CREATE TABLE `ai_model_configs`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '配置名称',
  `model_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模型类型: deepseek/qwen/siliconflow/zhipu/other',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色: writer/reviewer/browser_use_text',
  `api_key` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'API Key',
  `base_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'API Base URL',
  `model_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模型名称',
  `max_tokens` int NULL DEFAULT NULL COMMENT '最大Token数',
  `temperature` float NULL DEFAULT NULL COMMENT '温度参数',
  `top_p` float NULL DEFAULT NULL COMMENT 'Top P参数',
  `is_active` int NULL DEFAULT NULL COMMENT '是否启用',
  `created_by` bigint NOT NULL COMMENT '创建者ID',
  `llm_config_id` bigint NULL DEFAULT NULL COMMENT '关联的LLM配置ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP,
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `updated_by` bigint NULL DEFAULT NULL,
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI模型配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_model_configs
-- ----------------------------


-- ----------------------------
-- Table structure for ai_test_reports
-- ----------------------------
DROP TABLE IF EXISTS `ai_test_reports`;
CREATE TABLE `ai_test_reports`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `report_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '报告ID',
  `report_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '报告名称',
  `project_id` bigint NULL DEFAULT NULL COMMENT '项目ID',
  `project_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '项目名称',
  `start_date` date NULL DEFAULT NULL COMMENT '开始日期',
  `end_date` date NULL DEFAULT NULL COMMENT '结束日期',
  `date_range` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '时间范围',
  `status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '报告状态',
  `total_cases` int NULL DEFAULT NULL COMMENT '总用例数',
  `total_executions` int NULL DEFAULT NULL COMMENT '总执行次数',
  `success_count` int NULL DEFAULT NULL COMMENT '成功次数',
  `failed_count` int NULL DEFAULT NULL COMMENT '失败次数',
  `success_rate` decimal(5, 2) NULL DEFAULT NULL COMMENT '成功率',
  `total_duration` decimal(10, 2) NULL DEFAULT NULL COMMENT '总执行时长(秒)',
  `avg_duration` decimal(10, 2) NULL DEFAULT NULL COMMENT '平均时长(秒)',
  `total_tokens` bigint NULL DEFAULT NULL COMMENT '总Token使用量',
  `report_data` json NULL COMMENT '报告详细数据',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `report_id`(`report_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI测试报告表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_test_reports
-- ----------------------------


-- ----------------------------
-- Table structure for ai_test_suite_executions
-- ----------------------------
DROP TABLE IF EXISTS `ai_test_suite_executions`;
CREATE TABLE `ai_test_suite_executions`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `suite_id` int NOT NULL COMMENT '套件ID',
  `suite_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '套件名称（冗余字段）',
  `execution_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行名称',
  `execution_mode` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行模式：headless/headed',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '状态：running/completed/failed',
  `start_time` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `duration` decimal(10, 2) NULL DEFAULT NULL COMMENT '执行时长（秒）',
  `total_modules` int NULL DEFAULT NULL COMMENT '总模块数',
  `completed_modules` int NULL DEFAULT NULL COMMENT '已完成模块数',
  `failed_modules` int NULL DEFAULT NULL COMMENT '失败模块数',
  `total_cases` int NULL DEFAULT NULL COMMENT '总用例数',
  `passed_cases` int NULL DEFAULT NULL COMMENT '通过用例数',
  `failed_cases` int NULL DEFAULT NULL COMMENT '失败用例数',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '错误信息',
  `created_by` int NULL DEFAULT NULL COMMENT '创建人ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` int NULL DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI测试套件执行记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_test_suite_executions
-- ----------------------------


-- ----------------------------
-- Table structure for ai_test_suite_module_executions
-- ----------------------------
DROP TABLE IF EXISTS `ai_test_suite_module_executions`;
CREATE TABLE `ai_test_suite_module_executions`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `suite_execution_id` int NOT NULL COMMENT '套件执行记录ID',
  `module_id` int NOT NULL COMMENT '模块ID',
  `module_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模块名称',
  `execution_order` int NULL DEFAULT NULL COMMENT '执行顺序',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '状态：pending/running/completed/failed',
  `start_time` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `duration` decimal(10, 2) NULL DEFAULT NULL COMMENT '执行时长（秒）',
  `total_cases` int NULL DEFAULT NULL COMMENT '总用例数',
  `passed_cases` int NULL DEFAULT NULL COMMENT '通过用例数',
  `failed_cases` int NULL DEFAULT NULL COMMENT '失败用例数',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '错误信息',
  `created_by` int NULL DEFAULT NULL COMMENT '创建人ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` int NULL DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI测试套件模块执行记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_test_suite_module_executions
-- ----------------------------
INSERT INTO `ai_test_suite_module_executions` VALUES (1, 1, 2, '默认模块', 1, 'completed', '2026-04-01 11:56:40', '2026-04-01 11:56:40', 0.05, 0, 0, 0, NULL, 1, '2026-04-01 11:56:39', 1, NULL, '2026-04-01 11:56:40', NULL);


-- ----------------------------
-- Table structure for ai_test_suite_modules
-- ----------------------------
DROP TABLE IF EXISTS `ai_test_suite_modules`;
CREATE TABLE `ai_test_suite_modules`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `suite_id` int NOT NULL COMMENT '套件ID',
  `module_id` int NOT NULL COMMENT '模块ID',
  `module_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模块名称（冗余字段，方便查询）',
  `execution_order` int NOT NULL COMMENT '执行顺序',
  `created_by` int NULL DEFAULT NULL COMMENT '创建人ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` int NULL DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI测试套件模块关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_test_suite_modules
-- ----------------------------

INSERT INTO `ai_test_suite_modules` VALUES (8, 4, 6, '默认模块', 4, 1, '2026-03-01 17:45:00', 0, NULL, '2026-03-23 09:07:08', NULL);
INSERT INTO `ai_test_suite_modules` VALUES (13, 8, 2, '默认模块', 1, 1, '2026-04-01 11:49:24', 1, NULL, '2026-04-01 11:49:24', NULL);


-- ----------------------------
-- Table structure for ai_test_suites
-- ----------------------------
DROP TABLE IF EXISTS `ai_test_suites`;
CREATE TABLE `ai_test_suites`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '套件名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '套件描述',
  `project_id` int NOT NULL COMMENT '关联项目ID',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '状态：active/archived',
  `created_by` int NULL DEFAULT NULL COMMENT '创建人ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` int NULL DEFAULT NULL COMMENT '更新人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI测试套件表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ai_test_suites
-- ----------------------------


-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version`  (
  `version_num` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`version_num`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of alembic_version
-- ----------------------------




INSERT INTO `alembic_version` VALUES ('74c098babcee');


-- ----------------------------
-- Table structure for api_automation_apis
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_apis`;
CREATE TABLE `api_automation_apis`  (
  `url` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '接口URL',
  `req` json NULL COMMENT '请求配置',
  `document` json NULL COMMENT '接口文档',
  `api_service_id` bigint NOT NULL COMMENT '服务ID',
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '接口名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '接口描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 194 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_apis
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_cases
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_cases`;
CREATE TABLE `api_automation_cases`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '用例名称',
  `description` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '用例描述',
  `suite_id` bigint NOT NULL COMMENT '所属用例集ID',
  `script` json NULL COMMENT '步骤列表（接口步骤数组）',
  `status` int NULL DEFAULT NULL COMMENT '状态：0=未执行，1=通过，2=失败',
  `case_type` int NULL DEFAULT NULL COMMENT '用例类型：1=正向，2=负向，3=边界值，4=安全性，5=其他',
  `step_rely` int NULL DEFAULT NULL COMMENT '步骤依赖：1=是（步骤间共享变量），0=否（每步骤独立）',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_cases
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_codes
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_codes`;
CREATE TABLE `api_automation_codes`  (
  `code` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '错误码',
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '错误码名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '错误码描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_codes
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_databases
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_databases`;
CREATE TABLE `api_automation_databases`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '数据库名称',
  `config` json NULL COMMENT '数据库配置',
  `db_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '数据库类型',
  `host` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '主机地址',
  `port` int NULL DEFAULT NULL COMMENT '端口',
  `database_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '数据库名',
  `username` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '用户名',
  `password` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '密码',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_databases
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_edits
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_edits`;
CREATE TABLE `api_automation_edits`  (
  `api_id` bigint NOT NULL COMMENT '接口ID',
  `edit` json NULL COMMENT '变更内容',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_edits
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_environments
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_environments`;
CREATE TABLE `api_automation_environments`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '环境名称',
  `config` json NULL COMMENT '环境配置',
  `variable` json NULL COMMENT '环境变量',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '环境描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_environments
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_functions
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_functions`;
CREATE TABLE `api_automation_functions`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '公共函数名称',
  `description` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '公共函数描述',
  `code` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT 'Python 函数代码',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_functions
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_menus
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_menus`;
CREATE TABLE `api_automation_menus`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '菜单名称',
  `type` int NOT NULL COMMENT '菜单类型',
  `pid` bigint NOT NULL COMMENT '父菜单ID',
  `api_id` bigint NULL DEFAULT NULL COMMENT '接口ID',
  `api_service_id` bigint NOT NULL COMMENT '服务ID',
  `status` int NOT NULL COMMENT '状态',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 234 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_menus
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_ntest_scripts
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_ntest_scripts`;
CREATE TABLE `api_automation_ntest_scripts`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '脚本名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '脚本描述',
  `code` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT 'Python代码',
  `api_service_id` bigint NOT NULL COMMENT '所属服务ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_ntest_scripts
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_params
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_params`;
CREATE TABLE `api_automation_params`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '参数名称',
  `value` json NULL COMMENT '参数值',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_params
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_projects
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_projects`;
CREATE TABLE `api_automation_projects`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '项目名称',
  `img` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '项目图标',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '项目描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_projects
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_results
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_results`;
CREATE TABLE `api_automation_results`  (
  `req` json NULL COMMENT '请求数据',
  `res` json NULL COMMENT '响应数据',
  `api_id` bigint NOT NULL COMMENT '接口ID',
  `status_code` int NULL DEFAULT NULL COMMENT '状态码',
  `response_time` float NULL DEFAULT NULL COMMENT '响应时间',
  `error_message` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '错误信息',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_results
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_script_result_lists
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_script_result_lists`;
CREATE TABLE `api_automation_script_result_lists`  (
  `result_id` bigint NOT NULL COMMENT '执行ID',
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '场景名称',
  `script` json NULL COMMENT '场景配置',
  `config` json NULL COMMENT '执行配置',
  `result` json NULL COMMENT '执行结果',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `api_service_id` bigint NULL DEFAULT NULL COMMENT '关联服务ID，可为空（兼容历史数据）',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_script_result_lists
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_script_results
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_script_results`;
CREATE TABLE `api_automation_script_results`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '步骤名称',
  `uuid` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '唯一标识',
  `menu_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '菜单ID',
  `result_id` bigint NOT NULL COMMENT '执行ID',
  `status` int NULL DEFAULT NULL COMMENT '执行状态',
  `req` json NULL COMMENT '请求数据',
  `res` json NULL COMMENT '响应数据',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 119 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_script_results
-- ----------------------------
INSERT INTO `api_automation_script_results` VALUES ('uploads an image', '939a79c8-1631-43ea-b251-ddfd0dc49f5c', 'ac8575db-e844-48f0-8e9c-3071a82fef29', 483174911971927, 0, '{\"url\": \"/pet/{petId}/uploadImage\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [{\"key\": \"petId\", \"value\": \"\", \"status\": true}], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet/{petId}/uploadImage\': No scheme supplied. Perhaps you meant https:///pet/{petId}/uploadImage?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 92, '2026-04-16 16:22:51', 1, '2026-04-16 16:22:51', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('Add a new pet to the store', 'd801beda-a771-48e4-8410-aa3712e468c2', '2f592a0a-670b-424e-9cf7-3232c698a8e2', 483174911971927, 0, '{\"url\": \"/pet\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet\': No scheme supplied. Perhaps you meant https:///pet?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 93, '2026-04-16 16:22:54', 1, '2026-04-16 16:22:54', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 483174911971927, 1, '{}', '{}', 94, '2026-04-16 16:22:57', 1, '2026-04-16 16:22:57', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('uploads an image', 'eb4e51ea-a3c9-4f70-acad-9ca581c42752', '4bad0d91-ffb2-4e99-823c-ffcd949c2ce5', 598828799093799, 0, '{\"url\": \"/pet/{petId}/uploadImage\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [{\"key\": \"petId\", \"value\": \"\", \"status\": true}], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet/{petId}/uploadImage\': No scheme supplied. Perhaps you meant https:///pet/{petId}/uploadImage?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 96, '2026-04-16 16:32:59', 1, '2026-04-16 16:32:59', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('Add a new pet to the store', 'f99626dd-5c0f-400d-ad22-b2218807b0aa', 'e17cf643-6a43-46c9-a2a0-6a35da086e4a', 598828799093799, 0, '{\"url\": \"/pet\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet\': No scheme supplied. Perhaps you meant https:///pet?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 97, '2026-04-16 16:33:02', 1, '2026-04-16 16:33:02', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 598828799093799, 1, '{}', '{}', 98, '2026-04-16 16:33:05', 1, '2026-04-16 16:33:05', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('uploads an image', '27cf132f-8da2-4b04-9edf-6fb05c949a6a', 'a7a260b3-d03b-4ad3-ab87-62d9e29570d6', 371491775148030, 0, '{\"url\": \"/pet/{petId}/uploadImage\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [{\"key\": \"petId\", \"value\": \"\", \"status\": true}], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet/{petId}/uploadImage\': No scheme supplied. Perhaps you meant https:///pet/{petId}/uploadImage?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 100, '2026-04-16 16:55:01', 1, '2026-04-16 16:55:01', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('Add a new pet to the store', '03f7616a-2f76-4ed9-a268-7a9bda645576', '03a6308c-43e1-47ef-9bae-0ecd275c2383', 371491775148030, 0, '{\"url\": \"/pet\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet\': No scheme supplied. Perhaps you meant https:///pet?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 101, '2026-04-16 16:55:04', 1, '2026-04-16 16:55:04', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 371491775148030, 1, '{}', '{}', 102, '2026-04-16 16:55:07', 1, '2026-04-16 16:55:07', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('uploads an image', '13ce92a4-5046-47a3-ba90-9390d33111a7', 'b36bcf67-1c01-4dc5-a1c6-445884b5bf67', 1776330468462, 0, '{\"url\": \"/pet/{petId}/uploadImage\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [{\"key\": \"petId\", \"value\": \"\", \"status\": true}], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet/{petId}/uploadImage\': No scheme supplied. Perhaps you meant https:///pet/{petId}/uploadImage?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 104, '2026-04-16 17:07:52', 1, '2026-04-16 17:07:52', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('Add a new pet to the store', '02c7589a-57ef-48c3-a878-7e94e9e6aef3', '25d70f5a-2743-4d8a-aa1c-e4f8e42cb1b3', 1776330468462, 0, '{\"url\": \"/pet\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet\': No scheme supplied. Perhaps you meant https:///pet?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 105, '2026-04-16 17:07:56', 1, '2026-04-16 17:07:56', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 1776330468462, 1, '{}', '{}', 106, '2026-04-16 17:07:59', 1, '2026-04-16 17:07:59', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('uploads an image', 'd05f423f-f212-48f3-9c54-957c569bcd62', 'a915e076-1185-4dd3-8c82-e5c952f304a7', 1776332265893, 0, '{\"url\": \"/pet/{petId}/uploadImage\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [{\"key\": \"petId\", \"value\": \"\", \"status\": true}], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet/{petId}/uploadImage\': No scheme supplied. Perhaps you meant https:///pet/{petId}/uploadImage?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 108, '2026-04-16 17:37:52', 1, '2026-04-16 17:37:52', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('Add a new pet to the store', '4c9ab277-cc71-4b50-956b-316a9653fbed', 'cb32fb2a-62bd-45cc-80ff-7a1117623a42', 1776332265893, 0, '{\"url\": \"/pet\", \"body\": {}, \"after\": [], \"assert\": [], \"before\": [], \"config\": {\"retry\": 0, \"req_timeout\": 5, \"res_timeout\": 5}, \"header\": [], \"method\": 2, \"params\": [], \"body_type\": 1, \"file_path\": [], \"form_data\": [], \"params_id\": null, \"form_urlencoded\": []}', '{\"body\": {\"msg\": \"接口请求失败\", \"exception\": \"Invalid URL \'/pet\': No scheme supplied. Perhaps you meant https:///pet?\"}, \"code\": 500, \"size\": 0, \"after\": [], \"assert\": [], \"before\": [], \"header\": {}, \"cookies\": [], \"res_time\": 0, \"raw_request\": null}', 109, '2026-04-16 17:37:55', 1, '2026-04-16 17:37:55', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 1776332265893, 1, '{}', '{}', 110, '2026-04-16 17:37:58', 1, '2026-04-16 17:37:58', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 542633149214560, 1, '{}', '{}', 113, '2026-04-22 18:05:11', 1, '2026-04-22 18:05:11', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 185519059943626, 1, '{}', '{}', 114, '2026-04-22 18:11:12', 1, '2026-04-22 18:11:12', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 347373744857226, 1, '{}', '{}', 115, '2026-04-23 09:34:01', 1, '2026-04-23 09:34:01', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 183947679192885, 1, '{}', '{}', 116, '2026-04-23 09:41:39', 1, '2026-04-23 09:41:39', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 646586113602223, 1, '{}', '{}', 117, '2026-04-23 17:12:45', 1, '2026-04-23 17:12:45', 1, 1, NULL);
INSERT INTO `api_automation_script_results` VALUES ('执行结束', '', '', 1545269149742, 1, '{}', '{}', 118, '2026-04-23 17:49:50', 1, '2026-04-23 17:49:50', 1, 1, NULL);


-- ----------------------------
-- Table structure for api_automation_scripts
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_scripts`;
CREATE TABLE `api_automation_scripts`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '场景名称',
  `type` int NULL DEFAULT NULL COMMENT '场景类型',
  `script` json NOT NULL COMMENT '场景步骤',
  `config` json NULL COMMENT '场景配置',
  `description` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '场景描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_scripts
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_services
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_services`;
CREATE TABLE `api_automation_services`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '服务名称',
  `api_project_id` bigint NOT NULL COMMENT '项目ID',
  `img` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '服务图标',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '服务描述',
  `source_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '接口文档类型：swagger/apifox',
  `source_addr` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '接口文档地址',
  `last_pull_status` int NULL DEFAULT NULL COMMENT '拉取状态：0=未拉取，1=成功，2=失败',
  `manager` bigint NULL DEFAULT NULL COMMENT '负责人用户ID',
  `business_id` bigint NULL DEFAULT NULL COMMENT '业务线ID',
  `sort` int NULL DEFAULT NULL COMMENT '排序权重',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_services
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_suites
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_suites`;
CREATE TABLE `api_automation_suites`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '用例集名称',
  `parent` bigint NULL DEFAULT NULL COMMENT '父用例集ID，顶级为null',
  `api_service_id` bigint NOT NULL COMMENT '所属服务ID',
  `sort` int NULL DEFAULT NULL COMMENT '同级排序权重',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_suites
-- ----------------------------
INSERT INTO `api_automation_suites` VALUES ('2', 0, 1, 7, 1, '2026-04-15 16:43:52', 1, '2026-04-16 11:15:53', 1, 0, NULL);
INSERT INTO `api_automation_suites` VALUES ('3', 0, 2, 7, 2, '2026-04-15 16:44:07', 1, '2026-04-16 11:15:48', 1, 0, NULL);


-- ----------------------------
-- Table structure for api_automation_updates
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_updates`;
CREATE TABLE `api_automation_updates`  (
  `req` json NULL COMMENT '变更内容',
  `api_id` bigint NOT NULL COMMENT '接口ID',
  `api_service_id` bigint NOT NULL COMMENT '服务ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_updates
-- ----------------------------


-- ----------------------------
-- Table structure for api_automation_variables
-- ----------------------------
DROP TABLE IF EXISTS `api_automation_variables`;
CREATE TABLE `api_automation_variables`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '变量名',
  `value` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '变量值',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '变量描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_automation_variables
-- ----------------------------
INSERT INTO `api_automation_variables` VALUES ('测试环境', '你好', NULL, 1, '2026-04-29 13:49:49', 1, '2026-04-29 13:49:49', 1, 1, NULL);


-- ----------------------------
-- Table structure for api_collections
-- ----------------------------
DROP TABLE IF EXISTS `api_collections`;
CREATE TABLE `api_collections`  (
  `api_project_id` bigint NOT NULL COMMENT 'API项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '集合名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '集合描述',
  `parent_id` bigint NULL DEFAULT NULL COMMENT '父级集合ID',
  `order_num` int NULL DEFAULT NULL COMMENT '排序',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_collections_api_project_id`(`api_project_id` ASC) USING BTREE,
  INDEX `ix_api_collections_parent_id`(`parent_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_collections
-- ----------------------------


-- ----------------------------
-- Table structure for api_database_configs
-- ----------------------------
DROP TABLE IF EXISTS `api_database_configs`;
CREATE TABLE `api_database_configs`  (
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '连接名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '连接描述',
  `db_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '数据库类型: mysql/postgresql/mongodb/redis',
  `host` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '主机地址',
  `port` int NOT NULL COMMENT '端口',
  `database_name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '数据库名',
  `username` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '用户名',
  `password` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '密码（加密存储）',
  `connection_params` json NULL COMMENT '其他连接参数',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_database_configs_project_id`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_database_configs
-- ----------------------------


-- ----------------------------
-- Table structure for api_environments
-- ----------------------------
DROP TABLE IF EXISTS `api_environments`;
CREATE TABLE `api_environments`  (
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '环境名称',
  `scope` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '作用域: GLOBAL/LOCAL',
  `variables` json NULL COMMENT '环境变量',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否激活',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_environments_project_id`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_environments
-- ----------------------------


-- ----------------------------
-- Table structure for api_projects
-- ----------------------------
DROP TABLE IF EXISTS `api_projects`;
CREATE TABLE `api_projects`  (
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'API项目名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '项目描述',
  `project_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '类型: HTTP/WEBSOCKET',
  `base_url` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '基础URL',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_projects_project_id`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_projects
-- ----------------------------
INSERT INTO `api_projects` VALUES (2, '00', '00', 'HTTP', '00', 1, '2026-04-01 11:07:17', NULL, '2026-04-01 11:07:17', NULL, 1, NULL);


-- ----------------------------
-- Table structure for api_public_scripts
-- ----------------------------
DROP TABLE IF EXISTS `api_public_scripts`;
CREATE TABLE `api_public_scripts`  (
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '脚本名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '脚本描述',
  `script_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '脚本类型: javascript/python',
  `script_content` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '脚本内容',
  `category` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '分类',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_public_scripts_category`(`category` ASC) USING BTREE,
  INDEX `ix_api_public_scripts_project_id`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_public_scripts
-- ----------------------------
INSERT INTO `api_public_scripts` VALUES (2, '1', '00', '00', 'python', '00', 0, 1, '2026-02-07 17:35:05', 1, '2026-02-07 17:35:05', 1, 1, NULL);


-- ----------------------------
-- Table structure for api_request_histories
-- ----------------------------
DROP TABLE IF EXISTS `api_request_histories`;
CREATE TABLE `api_request_histories`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `request_id` bigint NOT NULL COMMENT '关联请求ID',
  `environment_id` bigint NULL DEFAULT NULL COMMENT '使用环境ID',
  `environment_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '环境名称',
  `request_data` json NULL COMMENT '请求数据',
  `response_data` json NULL COMMENT '响应数据',
  `status_code` int NULL DEFAULT NULL COMMENT '状态码',
  `response_time` float NULL DEFAULT NULL COMMENT '响应时间(ms)',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '错误信息',
  `assertions_results` json NULL COMMENT '断言结果',
  `assertions_passed` tinyint(1) NULL DEFAULT NULL COMMENT '断言是否通过',
  `executed_by` bigint NOT NULL COMMENT '执行者ID',
  `executed_at` datetime NULL DEFAULT NULL COMMENT '执行时间',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_request_histories_executed_at`(`executed_at` ASC) USING BTREE,
  INDEX `ix_api_request_histories_request_id`(`request_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_request_histories
-- ----------------------------
INSERT INTO `api_request_histories` VALUES (1, 1, NULL, NULL, '{\"url\": \"00\", \"body\": null, \"method\": \"POST\", \"params\": {}, \"headers\": {}}', '{\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}', 0, 923.179, 'Request URL is missing an \'http://\' or \'https://\' protocol.', '[]', NULL, 1, '2026-04-01 11:07:39', '2026-04-01 11:07:38', NULL, '2026-04-01 11:07:38', NULL, 1, NULL);


-- ----------------------------
-- Table structure for api_requests
-- ----------------------------
DROP TABLE IF EXISTS `api_requests`;
CREATE TABLE `api_requests`  (
  `collection_id` bigint NOT NULL COMMENT '所属集合ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '请求名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '请求描述',
  `request_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '请求类型: HTTP/WEBSOCKET',
  `method` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '请求方法',
  `url` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '请求URL',
  `headers` json NULL COMMENT '请求头',
  `params` json NULL COMMENT 'URL参数',
  `body` json NULL COMMENT '请求体',
  `cookies` json NULL COMMENT 'Cookies',
  `auth` json NULL COMMENT '认证信息',
  `pre_request_script` json NULL COMMENT '前置操作列表',
  `post_request_script` json NULL COMMENT '后置操作列表',
  `assertions` json NULL COMMENT '断言规则',
  `verify_ssl` tinyint(1) NULL DEFAULT NULL COMMENT 'SSL证书验证',
  `follow_redirects` tinyint(1) NULL DEFAULT NULL COMMENT '自动跟随重定向',
  `timeout` int NULL DEFAULT NULL COMMENT '超时时间(毫秒)',
  `order_num` int NULL DEFAULT NULL COMMENT '排序',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_requests_collection_id`(`collection_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_requests
-- ----------------------------


-- ----------------------------
-- Table structure for api_ssl_certificate
-- ----------------------------
DROP TABLE IF EXISTS `api_ssl_certificate`;
CREATE TABLE `api_ssl_certificate`  (
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '证书名称',
  `cert_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '证书类型: CA/CLIENT',
  `domain` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '适用域名（支持通配符）',
  `ca_cert` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT 'CA证书内容（PEM格式）',
  `client_cert` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '客户端证书内容（CRT/PEM格式）',
  `client_key` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '客户端私钥内容（KEY/PEM格式）',
  `passphrase` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '私钥密码（加密存储）',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_ssl_certificate_domain`(`domain` ASC) USING BTREE,
  INDEX `ix_api_ssl_certificate_project_id`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_ssl_certificate
-- ----------------------------


-- ----------------------------
-- Table structure for api_test_executions
-- ----------------------------
DROP TABLE IF EXISTS `api_test_executions`;
CREATE TABLE `api_test_executions`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `test_suite_id` bigint NOT NULL COMMENT '测试套件ID',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行状态',
  `start_time` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `total_requests` int NULL DEFAULT NULL COMMENT '总请求数',
  `passed_requests` int NULL DEFAULT NULL COMMENT '通过请求数',
  `failed_requests` int NULL DEFAULT NULL COMMENT '失败请求数',
  `results` json NULL COMMENT '执行结果',
  `executed_by` bigint NOT NULL COMMENT '执行者ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_test_executions_status`(`status` ASC) USING BTREE,
  INDEX `ix_api_test_executions_test_suite_id`(`test_suite_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 17 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_test_executions
-- ----------------------------
INSERT INTO `api_test_executions` VALUES (1, 3, 'FAILED', '2026-02-07 09:23:44', '2026-02-07 09:23:45', 1, 0, 1, '[{\"result\": {\"history_id\": 2, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 271.6479301452637, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 4}]', 1, '2026-02-07 09:23:44', NULL, '2026-02-07 09:23:44', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (2, 4, 'FAILED', '2026-02-07 09:26:14', '2026-02-07 09:26:14', 1, 0, 1, '[{\"result\": {\"history_id\": 4, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 251.11770629882812, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 5}]', 1, '2026-02-07 09:26:13', NULL, '2026-02-07 09:26:14', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (3, 5, 'FAILED', '2026-02-07 09:28:30', '2026-02-07 09:28:30', 1, 0, 1, '[{\"result\": {\"history_id\": 6, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 253.11708450317383, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 6}]', 1, '2026-02-07 09:28:30', NULL, '2026-02-07 09:28:30', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (4, 6, 'FAILED', '2026-02-07 09:29:44', '2026-02-07 09:29:45', 1, 0, 1, '[{\"result\": {\"history_id\": 8, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 253.7741661071777, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 7}]', 1, '2026-02-07 09:29:44', NULL, '2026-02-07 09:29:44', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (5, 7, 'FAILED', '2026-02-07 09:32:17', '2026-02-07 09:32:17', 1, 0, 1, '[{\"result\": {\"history_id\": 10, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 376.72948837280273, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 8}]', 1, '2026-02-07 09:32:16', NULL, '2026-02-07 09:32:17', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (6, 8, 'FAILED', '2026-02-07 09:34:10', '2026-02-07 09:34:11', 1, 0, 1, '[{\"result\": {\"history_id\": 12, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 271.56901359558105, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 9}]', 1, '2026-02-07 09:34:10', NULL, '2026-02-07 09:34:10', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (7, 9, 'FAILED', '2026-02-07 09:35:18', '2026-02-07 09:35:18', 1, 0, 1, '[{\"result\": {\"history_id\": 14, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 250.12612342834473, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 10}]', 1, '2026-02-07 09:35:17', NULL, '2026-02-07 09:35:18', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (8, 10, 'FAILED', '2026-02-07 09:38:11', '2026-02-07 09:38:12', 1, 0, 1, '[{\"result\": {\"history_id\": 16, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 262.2687816619873, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 11}]', 1, '2026-02-07 09:38:11', NULL, '2026-02-07 09:38:11', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (9, 11, 'FAILED', '2026-02-07 09:39:49', '2026-02-07 09:39:49', 1, 0, 1, '[{\"result\": {\"history_id\": 18, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 250.4403591156006, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 12}]', 1, '2026-02-07 09:39:48', NULL, '2026-02-07 09:39:49', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (10, 12, 'FAILED', '2026-02-07 09:42:05', '2026-02-07 09:42:05', 1, 0, 1, '[{\"result\": {\"history_id\": 20, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 249.56178665161133, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 13}]', 1, '2026-02-07 09:42:04', NULL, '2026-02-07 09:42:05', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (11, 14, 'FAILED', '2026-02-07 13:57:54', '2026-02-07 13:57:55', 1, 0, 1, '[{\"result\": {\"history_id\": 45, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 257.0202350616455, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 15}]', 1, '2026-02-07 13:57:54', NULL, '2026-02-07 13:57:54', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (12, 14, 'FAILED', '2026-02-07 14:06:01', '2026-02-07 14:06:02', 1, 0, 1, '[{\"result\": {\"history_id\": 48, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 264.0042304992676, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 15}]', 1, '2026-02-07 14:06:01', NULL, '2026-02-07 14:06:01', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (13, 14, 'FAILED', '2026-02-07 14:35:00', '2026-02-07 14:35:00', 1, 0, 1, '[{\"result\": {\"history_id\": 64, \"status_code\": 0, \"updated_env\": null, \"error_message\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\", \"response_data\": {\"error\": \"Request URL is missing an \'http://\' or \'https://\' protocol.\"}, \"response_time\": 272.3374366760254, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 15}]', 1, '2026-02-07 14:34:59', NULL, '2026-02-07 14:34:59', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (14, 15, 'SUCCESS', '2026-02-07 14:35:50', '2026-02-07 14:35:50', 1, 1, 0, '[{\"result\": {\"history_id\": 65, \"status_code\": 200, \"updated_env\": null, \"error_message\": null, \"response_data\": {\"body\": {\"code\": 200, \"data\": {\"expires_in\": 86400, \"token_type\": \"Bearer\", \"access_token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsInNlc3Npb25faWQiOiIyOWQ5NmU0NGI0MGI0NzhjYjgwNzM4Y2I3NmRiODA1ZiIsImV4cCI6MTc3MDUzMjU1MH0.ftu3vZs3Y7nbgRdvcPLIkHe6fpgo8qHkWzPp5UeUodI\", \"refresh_token\": \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsInNlc3Npb25faWQiOiIyOWQ5NmU0NGI0MGI0NzhjYjgwNzM4Y2I3NmRiODA1ZiIsImV4cCI6MTc3MTA1MDk1MCwidHlwZSI6InJlZnJlc2gifQ.wqYvF0xWdYpYeXA0KkIHV3dFdrr5_I5E8HkSLP9KLMM\"}, \"message\": \"登录成功\"}, \"headers\": {\"date\": \"Sat, 07 Feb 2026 06:35:49 GMT\", \"server\": \"uvicorn\", \"content-type\": \"application/json\", \"x-request-id\": \"16308a9e49f745f5afad9fa34aaea9ff\", \"content-length\": \"563\"}, \"status_code\": 200, \"response_time\": 592.6196575164795}, \"response_time\": 592.6196575164795, \"assertions_passed\": true, \"assertions_results\": []}, \"order_num\": 1, \"request_id\": 15}]', 1, '2026-02-07 14:35:49', NULL, '2026-02-07 14:35:50', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (15, 15, 'SUCCESS', '2026-02-07 14:39:47', '2026-02-07 14:39:48', 1, 1, 0, '[{\"passed\": true, \"order_num\": 1, \"request_id\": 15, \"status_code\": 200, \"request_name\": \"登录\", \"error_message\": null, \"response_time\": 794.1465377807617, \"assertions_results\": []}]', 1, '2026-02-07 14:39:47', NULL, '2026-02-07 14:39:48', NULL, 1, NULL);
INSERT INTO `api_test_executions` VALUES (16, 15, 'SUCCESS', '2026-02-07 14:41:08', '2026-02-07 14:41:09', 1, 1, 0, '[{\"passed\": true, \"order_num\": 1, \"request_id\": 15, \"status_code\": 200, \"request_name\": \"登录\", \"error_message\": null, \"response_time\": 728.6155223846436, \"assertions_results\": []}]', 1, '2026-02-07 14:41:08', NULL, '2026-02-07 14:41:08', NULL, 1, NULL);


-- ----------------------------
-- Table structure for api_test_suite_requests
-- ----------------------------
DROP TABLE IF EXISTS `api_test_suite_requests`;
CREATE TABLE `api_test_suite_requests`  (
  `test_suite_id` bigint NOT NULL COMMENT '测试套件ID',
  `request_id` bigint NOT NULL COMMENT 'API请求ID',
  `order_num` int NULL DEFAULT NULL COMMENT '执行顺序',
  `assertions` json NULL COMMENT '断言规则',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_test_suite_requests
-- ----------------------------


-- ----------------------------
-- Table structure for api_test_suites
-- ----------------------------
DROP TABLE IF EXISTS `api_test_suites`;
CREATE TABLE `api_test_suites`  (
  `api_project_id` bigint NOT NULL COMMENT 'API项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '套件名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '套件描述',
  `environment_id` bigint NULL DEFAULT NULL COMMENT '执行环境ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_api_test_suites_api_project_id`(`api_project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_test_suites
-- ----------------------------


-- ----------------------------
-- Table structure for app_airtest_images
-- ----------------------------
DROP TABLE IF EXISTS `app_airtest_images`;
CREATE TABLE `app_airtest_images`  (
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '图片名称',
  `file_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '图片地址',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `menu_id` bigint NULL DEFAULT NULL COMMENT '所属菜单',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP自动化 Airtest 图像库' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_airtest_images
-- ----------------------------
INSERT INTO `app_airtest_images` VALUES ('nova_11.png', 'http://127.0.0.1:8100/static/upload/20260319/26d345c584c24b83ba577cf50d055ca9.png', '2026-03-19 19:54:38', NULL, 7, '2026-03-19 19:54:38', NULL, '2026-03-19 19:54:38', NULL, 1, NULL);
INSERT INTO `app_airtest_images` VALUES ('nova_11.png', 'http://127.0.0.1:8100/static/upload/20260319/08128e2a150a482ebf52c5f95fb07066.png', '2026-03-19 19:56:59', NULL, 8, '2026-03-19 19:56:59', NULL, '2026-03-19 19:56:59', NULL, 1, NULL);
INSERT INTO `app_airtest_images` VALUES ('nova_11.png', 'http://127.0.0.1:8100/static/upload/20260320/41bf1fd12ea840d6b284dc7157b17f23.png', '2026-03-20 09:26:03', NULL, 9, '2026-03-20 09:26:03', NULL, '2026-03-20 09:26:03', NULL, 1, NULL);
INSERT INTO `app_airtest_images` VALUES ('nova_11.png', 'http://127.0.0.1:8100/static/upload/20260320/1ccc366c70584e11b3b605a33e491285.png', '2026-03-20 09:26:39', NULL, 10, '2026-03-20 09:26:39', NULL, '2026-03-20 09:26:39', NULL, 1, NULL);
INSERT INTO `app_airtest_images` VALUES ('nova_11.png', 'http://127.0.0.1:8100/static/upload/20260320/ccabdcfee40a49e9a5a3cead1a521e5a.png', '2026-03-20 09:27:07', NULL, 11, '2026-03-20 09:27:07', NULL, '2026-03-20 09:27:07', NULL, 1, NULL);
INSERT INTO `app_airtest_images` VALUES ('nova_11.png', 'http://127.0.0.1:8100/static/upload/20260320/29f3e8d7dae14f6290616a6a7e2d54c9.png', '2026-03-20 09:51:05', NULL, 12, '2026-03-20 09:51:05', NULL, '2026-03-20 09:51:05', NULL, 1, NULL);


-- ----------------------------
-- Table structure for app_menus
-- ----------------------------
DROP TABLE IF EXISTS `app_menus`;
CREATE TABLE `app_menus`  (
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '名称',
  `pid` bigint NOT NULL COMMENT '父id',
  `type` int NOT NULL COMMENT '类型',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 57 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP自动化菜单表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_menus
-- ----------------------------
INSERT INTO `app_menus` VALUES ('根目录', 0, 0, 1, 47, '2026-03-30 16:04:45', NULL, '2026-03-30 16:04:45', NULL, 1, NULL);
INSERT INTO `app_menus` VALUES ('登录', 47, 1, 1, 53, '2026-04-14 17:09:18', NULL, '2026-04-14 17:09:18', NULL, 1, NULL);
INSERT INTO `app_menus` VALUES ('登录脚本', 53, 2, 1, 56, '2026-04-14 17:12:06', NULL, '2026-04-14 17:12:06', NULL, 1, NULL);


-- ----------------------------
-- Table structure for app_result_lists
-- ----------------------------
DROP TABLE IF EXISTS `app_result_lists`;
CREATE TABLE `app_result_lists`  (
  `task_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务名称',
  `device_list` json NOT NULL COMMENT '设备列表',
  `result_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '结果id',
  `script_list` json NOT NULL COMMENT '脚本列表',
  `script_status` json NOT NULL COMMENT '脚本执行情况',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `result_id`(`result_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP自动化结果汇总表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_result_lists
-- ----------------------------


-- ----------------------------
-- Table structure for app_results
-- ----------------------------
DROP TABLE IF EXISTS `app_results`;
CREATE TABLE `app_results`  (
  `device` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '设备',
  `result_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '结果id',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '脚本名称',
  `status` int NOT NULL COMMENT '状态 0失败 1成功 2进行中(兼容旧)',
  `log` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '详情',
  `assert_value` json NULL COMMENT '断言详情',
  `before_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行前截图地址',
  `after_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行后截图地址',
  `video` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '视频地址',
  `performance` json NULL COMMENT '实时性能',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP自动化执行结果表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_results
-- ----------------------------
INSERT INTO `app_results` VALUES ('69900dc9', '1773992584691', '执行异常', 0, 'Appium连接失败: HTTPConnectionPool(host=\'127.0.0.1\', port=4723): Max retries exceeded with url: /session (Caused by NewConnectionError(\"HTTPConnection(host=\'127.0.0.1\', port=4723): Failed to establish a new connection: [WinError 10061] 由于目标计算机积极拒绝，无法连接。\"))', '{}', '', '', '', '{\"cpu\": [0], \"time\": [\"43:52\"], \"memory\": [0], \"up_network\": [0], \"temperature\": [0], \"down_network\": [0]}', 2, '2026-03-20 15:43:54', 1, 3, '2026-03-20 15:43:54', NULL, '2026-03-20 15:43:54', NULL, 1, NULL);
INSERT INTO `app_results` VALUES ('69900dc9', '1773992584691', '执行结束', 0, '执行结束', '{}', '', '', '', '{\"cpu\": [0, 0], \"time\": [\"43:52\", \"43:54\"], \"memory\": [0, 0], \"up_network\": [0, 0], \"temperature\": [0, 0], \"down_network\": [0, 0]}', 2, '2026-03-20 15:43:54', 1, 4, '2026-03-20 15:43:54', NULL, '2026-03-20 15:43:54', NULL, 1, NULL);


-- ----------------------------
-- Table structure for app_scripts
-- ----------------------------
DROP TABLE IF EXISTS `app_scripts`;
CREATE TABLE `app_scripts`  (
  `script` json NOT NULL COMMENT '脚本',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `menu_id`(`menu_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP自动化脚本表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_scripts
-- ----------------------------
INSERT INTO `app_scripts` VALUES ('[]', 53, 1, '2026-04-14 17:09:18', '2026-04-14 17:09:18', 6, '2026-04-14 17:09:18', NULL, '2026-04-14 17:09:18', NULL, 1, NULL);
INSERT INTO `app_scripts` VALUES ('[]', 56, 1, '2026-04-14 17:12:06', '2026-04-14 17:12:06', 9, '2026-04-14 17:12:06', NULL, '2026-04-14 17:12:06', NULL, 1, NULL);


-- ----------------------------
-- Table structure for app_ui_elements
-- ----------------------------
DROP TABLE IF EXISTS `app_ui_elements`;
CREATE TABLE `app_ui_elements`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `page_id` bigint NOT NULL COMMENT '页面 id',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '元素名称',
  `locate_type` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '定位类型 id/xpath/accessibility_id 等',
  `locate_value` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '定位值',
  `num` int NULL DEFAULT NULL COMMENT '排序',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP UI 元素表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_ui_elements
-- ----------------------------


-- ----------------------------
-- Table structure for app_ui_pages
-- ----------------------------
DROP TABLE IF EXISTS `app_ui_pages`;
CREATE TABLE `app_ui_pages`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `module_menu_id` bigint NOT NULL COMMENT '所属模块=app_menus 文件夹 id',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '页面名称',
  `num` int NULL DEFAULT NULL COMMENT '排序',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '备注',
  `activity` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Activity / 页面标识',
  `package_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '包名（可选）',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_app_ui_pages_user_module_name`(`user_id` ASC, `module_menu_id` ASC, `name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP UI 页面表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_ui_pages
-- ----------------------------


-- ----------------------------
-- Table structure for app_ui_test_run_phone
-- ----------------------------
DROP TABLE IF EXISTS `app_ui_test_run_phone`;
CREATE TABLE `app_ui_test_run_phone`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '设备别名',
  `num` int NULL DEFAULT NULL COMMENT '排序序号',
  `phone_os` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Android / ios',
  `os_version` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '系统版本',
  `device_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'adb devices / UDID',
  `extends` json NULL COMMENT '扩展字段',
  `screen` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分辨率',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_app_ui_test_run_phone_user_name`(`user_id` ASC, `name` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP测试运行终端表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_ui_test_run_phone
-- ----------------------------


-- ----------------------------
-- Table structure for app_ui_test_run_server
-- ----------------------------
DROP TABLE IF EXISTS `app_ui_test_run_server`;
CREATE TABLE `app_ui_test_run_server`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '服务器名称',
  `num` int NULL DEFAULT NULL COMMENT '排序序号',
  `server_os` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '系统类型 windows/mac/linux',
  `ip` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'IP',
  `port` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '端口',
  `appium_version` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'Appium 主版本 1.x/2.x/3.x',
  `status` int NOT NULL COMMENT '连通性 0未检测 1失败 2成功',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_app_ui_test_run_server_user_name`(`user_id` ASC, `name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'APP测试运行服务器表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of app_ui_test_run_server
-- ----------------------------


-- ----------------------------
-- Table structure for business_requirements
-- ----------------------------
DROP TABLE IF EXISTS `business_requirements`;
CREATE TABLE `business_requirements`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `title` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '需求标题',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '需求描述',
  `project_id` bigint NULL DEFAULT NULL COMMENT '项目ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of business_requirements
-- ----------------------------


-- ----------------------------
-- Table structure for celery_crontab_schedule
-- ----------------------------
DROP TABLE IF EXISTS `celery_crontab_schedule`;
CREATE TABLE `celery_crontab_schedule`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `minute` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '分钟',
  `hour` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '小时',
  `day_of_week` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '日期',
  `day_of_month` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '月份',
  `month_of_year` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '年',
  `timezone` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '时区',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of celery_crontab_schedule
-- ----------------------------


-- ----------------------------
-- Table structure for celery_interval_schedule
-- ----------------------------
DROP TABLE IF EXISTS `celery_interval_schedule`;
CREATE TABLE `celery_interval_schedule`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `every` int NULL DEFAULT NULL COMMENT '区间数',
  `period` varchar(24) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '间隔单位',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of celery_interval_schedule
-- ----------------------------


-- ----------------------------
-- Table structure for celery_periodic_task
-- ----------------------------
DROP TABLE IF EXISTS `celery_periodic_task`;
CREATE TABLE `celery_periodic_task`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '定时任务名',
  `task` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '任务路径',
  `args` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '参数',
  `kwargs` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '关键字参数',
  `queue` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '队列',
  `exchange` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '交换',
  `routing_key` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '路由密钥',
  `expires` datetime NULL DEFAULT NULL COMMENT '到期时间',
  `one_off` tinyint(1) NULL DEFAULT NULL COMMENT '执行一次',
  `start_time` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `enabled` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '是否启用, 1启动，0停用',
  `last_run_at` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '上次运行时间',
  `total_run_count` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '运行总次数',
  `date_changed` datetime NULL DEFAULT NULL COMMENT '更改日期',
  `description` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '备注',
  `crontab_id` int NULL DEFAULT NULL COMMENT '定时器id',
  `crontab` int NULL DEFAULT NULL COMMENT 'crontab 表达式',
  `interval_id` int NULL DEFAULT NULL COMMENT '间隔id',
  `interval_every` int NULL DEFAULT NULL COMMENT '间隔时间',
  `interval_period` varchar(24) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '间隔类型',
  `task_type` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'crontab interval',
  `project_id` int NULL DEFAULT NULL COMMENT '项目id',
  `module_id` int NOT NULL COMMENT '模块id',
  `suite_id` int NOT NULL COMMENT '套件id',
  `case_env_id` int NOT NULL COMMENT 'case_env_id 用例环境',
  `case_ids` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '用例集合',
  `ui_env_id` int NOT NULL COMMENT 'case_env_id 用例环境',
  `ui_ids` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'ui用例集合',
  `script_ids` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '脚本id',
  `task_tags` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务标签',
  `remarks` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务描述',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of celery_periodic_task
-- ----------------------------


-- ----------------------------
-- Table structure for celery_periodic_task_changed
-- ----------------------------
DROP TABLE IF EXISTS `celery_periodic_task_changed`;
CREATE TABLE `celery_periodic_task_changed`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `last_update` datetime NULL DEFAULT NULL COMMENT '到期时间',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of celery_periodic_task_changed
-- ----------------------------


-- ----------------------------
-- Table structure for data_factory_records
-- ----------------------------
DROP TABLE IF EXISTS `data_factory_records`;
CREATE TABLE `data_factory_records`  (
  `user_id` int NOT NULL COMMENT '用户ID',
  `tool_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '工具名称',
  `tool_category` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '工具分类',
  `tool_scenario` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '使用场景',
  `input_data` json NULL COMMENT '输入数据',
  `output_data` json NOT NULL COMMENT '输出数据',
  `is_saved` tinyint(1) NULL DEFAULT NULL COMMENT '是否保存',
  `tags` json NULL COMMENT '标签',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_tool_category`(`tool_category` ASC) USING BTREE,
  INDEX `idx_tool_scenario`(`tool_scenario` ASC) USING BTREE,
  INDEX `idx_user_created`(`user_id` ASC, `creation_date` ASC) USING BTREE,
  INDEX `ix_data_factory_records_tool_category`(`tool_category` ASC) USING BTREE,
  INDEX `ix_data_factory_records_tool_name`(`tool_name` ASC) USING BTREE,
  INDEX `ix_data_factory_records_tool_scenario`(`tool_scenario` ASC) USING BTREE,
  INDEX `ix_data_factory_records_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '数据工厂使用记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of data_factory_records
-- ----------------------------
INSERT INTO `data_factory_records` VALUES (1, 'generate_chinese_name', 'test_data', 'test_data', '{}', '{\"result\": \"邓发\"}', 1, 'null', 1, '2026-04-20 19:18:04', 1, '2026-04-20 19:18:04', 1, 1, NULL);
INSERT INTO `data_factory_records` VALUES (1, 'regex_test', 'string', 'string', '{\"text\": \"00\", \"flags\": \"\", \"pattern\": \"00\"}', '{\"groups\": [], \"matches\": [\"00\"], \"is_valid\": true, \"groupdict\": {}, \"match_count\": 1}', 1, 'null', 2, '2026-04-29 16:48:54', 1, '2026-04-29 16:48:54', 1, 1, NULL);


-- ----------------------------
-- Table structure for desktop_menus
-- ----------------------------
DROP TABLE IF EXISTS `desktop_menus`;
CREATE TABLE `desktop_menus`  (
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '名称',
  `pid` bigint NOT NULL COMMENT '父ID，0为根',
  `type` int NOT NULL COMMENT '0=目录 1=脚本组 2=脚本',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `project_id` bigint NULL DEFAULT NULL COMMENT '所属项目ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '客户端UI自动化菜单表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of desktop_menus
-- ----------------------------


-- ----------------------------
-- Table structure for desktop_result_lists
-- ----------------------------
DROP TABLE IF EXISTS `desktop_result_lists`;
CREATE TABLE `desktop_result_lists`  (
  `task_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务名称',
  `result_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行ID',
  `framework` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行框架',
  `script_list` json NOT NULL COMMENT '脚本列表',
  `script_status` json NOT NULL COMMENT '执行状态',
  `project_id` bigint NULL DEFAULT NULL COMMENT '所属项目ID',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `result_id`(`result_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '客户端UI自动化执行汇总表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of desktop_result_lists
-- ----------------------------


-- ----------------------------
-- Table structure for desktop_results
-- ----------------------------
DROP TABLE IF EXISTS `desktop_results`;
CREATE TABLE `desktop_results`  (
  `result_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行ID',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '步骤名称',
  `status` int NOT NULL COMMENT '0=失败 1=成功 2=进行中',
  `log` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '日志',
  `before_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行前截图',
  `after_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行后截图',
  `assert_value` json NULL COMMENT '断言详情',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '客户端UI自动化步骤结果表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of desktop_results
-- ----------------------------


-- ----------------------------
-- Table structure for desktop_scripts
-- ----------------------------
DROP TABLE IF EXISTS `desktop_scripts`;
CREATE TABLE `desktop_scripts`  (
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `framework` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行框架: pywinauto | pyautogui | winappdriver | sikuli',
  `script` json NOT NULL COMMENT '步骤列表',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `menu_id`(`menu_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '客户端UI自动化脚本表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of desktop_scripts
-- ----------------------------


-- ----------------------------
-- Table structure for figma_api_call_logs
-- ----------------------------
DROP TABLE IF EXISTS `figma_api_call_logs`;
CREATE TABLE `figma_api_call_logs`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `api_endpoint` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'API端点',
  `request_data` json NULL COMMENT '请求数据',
  `response_data` json NULL COMMENT '响应数据',
  `status_code` int NULL DEFAULT NULL COMMENT '状态码',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of figma_api_call_logs
-- ----------------------------


-- ----------------------------
-- Table structure for figma_configs
-- ----------------------------
DROP TABLE IF EXISTS `figma_configs`;
CREATE TABLE `figma_configs`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `config_name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '配置名称',
  `api_token` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'Figma API Token',
  `file_key` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'Figma文件Key',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of figma_configs
-- ----------------------------


-- ----------------------------
-- Table structure for figma_extraction_tasks
-- ----------------------------
DROP TABLE IF EXISTS `figma_extraction_tasks`;
CREATE TABLE `figma_extraction_tasks`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务名称',
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '任务状态',
  `result` json NULL COMMENT '提取结果',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of figma_extraction_tasks
-- ----------------------------


-- ----------------------------
-- Table structure for figma_file_cache
-- ----------------------------
DROP TABLE IF EXISTS `figma_file_cache`;
CREATE TABLE `figma_file_cache`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `file_key` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'Figma文件Key',
  `cache_data` json NULL COMMENT '缓存数据',
  `last_updated` datetime NULL DEFAULT NULL COMMENT '最后更新时间',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of figma_file_cache
-- ----------------------------


-- ----------------------------
-- Table structure for generated_test_cases
-- ----------------------------
DROP TABLE IF EXISTS `generated_test_cases`;
CREATE TABLE `generated_test_cases`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `case_name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '用例名称',
  `case_content` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '用例内容',
  `task_id` bigint NULL DEFAULT NULL COMMENT '任务ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of generated_test_cases
-- ----------------------------


-- ----------------------------
-- Table structure for generation_configs
-- ----------------------------
DROP TABLE IF EXISTS `generation_configs`;
CREATE TABLE `generation_configs`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `config_name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '配置名称',
  `config_data` json NULL COMMENT '配置数据',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of generation_configs
-- ----------------------------


-- ----------------------------
-- Table structure for knowledge_base
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_base`;
CREATE TABLE `knowledge_base`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '描述',
  `chunk_size` int NULL DEFAULT NULL COMMENT '分块大小',
  `chunk_overlap` int NULL DEFAULT NULL COMMENT '分块重叠',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_kb_project`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知识库表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of knowledge_base
-- ----------------------------


-- ----------------------------
-- Table structure for knowledge_document
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_document`;
CREATE TABLE `knowledge_document`  (
  `knowledge_base_id` bigint NOT NULL COMMENT '知识库ID',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '标题',
  `document_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '类型 pdf/docx/txt/md/...',
  `file_path` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '相对存储路径',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '提取的纯文本（用于关键词检索）',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'pending/processing/completed/failed',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误信息',
  `file_size` int NULL DEFAULT NULL COMMENT '字节大小',
  `word_count` int NULL DEFAULT NULL COMMENT '字数',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_kdoc_kb`(`knowledge_base_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知识库文档表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of knowledge_document
-- ----------------------------


-- ----------------------------
-- Table structure for knowledge_global_config
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_global_config`;
CREATE TABLE `knowledge_global_config`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `embedding_service` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '嵌入服务类型',
  `api_base_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'API Base URL',
  `api_key` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'API Key',
  `model_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '嵌入模型名',
  `chunk_size` int NULL DEFAULT NULL COMMENT '默认分块大小',
  `chunk_overlap` int NULL DEFAULT NULL COMMENT '默认分块重叠',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_kgc_user`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知识库全局配置' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of knowledge_global_config
-- ----------------------------


-- ----------------------------
-- Table structure for knowledge_vector_global_config
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_vector_global_config`;
CREATE TABLE `knowledge_vector_global_config`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `embedding_provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '嵌入提供商',
  `embedding_base_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '嵌入服务Base URL',
  `embedding_api_key` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '嵌入API Key',
  `embedding_model` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '嵌入模型',
  `vector_enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用向量检索',
  `vector_provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '向量库类型',
  `vector_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '向量库地址',
  `vector_api_key` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '向量库API Key',
  `vector_collection` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '默认集合',
  `vector_dimension` int NULL DEFAULT NULL COMMENT '向量维度',
  `retrieval_top_k` int NULL DEFAULT NULL COMMENT '检索TopK',
  `chunk_size` int NULL DEFAULT NULL COMMENT '默认切块大小',
  `chunk_overlap` int NULL DEFAULT NULL COMMENT '默认切块重叠',
  `distance_metric` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '向量距离度量',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '备注',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_kvgc_user`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知识库全局向量配置' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of knowledge_vector_global_config
-- ----------------------------


-- ----------------------------
-- Table structure for legacy_module_info
-- ----------------------------
DROP TABLE IF EXISTS `legacy_module_info`;
CREATE TABLE `legacy_module_info`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '模块ID',
  `name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '模块名称',
  `project_id` int NOT NULL COMMENT '所属项目ID',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '模块描述',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of legacy_module_info
-- ----------------------------


-- ----------------------------
-- Table structure for legacy_msg_notices
-- ----------------------------
DROP TABLE IF EXISTS `legacy_msg_notices`;
CREATE TABLE `legacy_msg_notices`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '通知名称',
  `type` int NOT NULL COMMENT '通知类型: 1-邮件, 2-钉钉, 3-企业微信, 4-飞书',
  `value` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '通知地址/Webhook',
  `status` int NOT NULL COMMENT '通知状态: 0-停用, 1-启用',
  `script` json NULL COMMENT '通知脚本配置',
  `description` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '通知描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of legacy_msg_notices
-- ----------------------------


-- ----------------------------
-- Table structure for legacy_scheduler_tasks
-- ----------------------------
DROP TABLE IF EXISTS `legacy_scheduler_tasks`;
CREATE TABLE `legacy_scheduler_tasks`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务名称',
  `type` int NOT NULL COMMENT '任务类型: 1-APP自动化, 2-Web UI自动化, 3-接口自动化',
  `status` int NOT NULL COMMENT '任务状态: 0-停用, 1-启用',
  `script` json NULL COMMENT '任务脚本配置',
  `time` json NULL COMMENT '时间配置',
  `notice` json NULL COMMENT '通知配置',
  `description` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '任务描述',
  `scheduler_job_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '调度器任务ID',
  `last_run_at` datetime NULL DEFAULT NULL COMMENT '上次运行时间',
  `next_run_at` datetime NULL DEFAULT NULL COMMENT '下次运行时间',
  `total_run_count` int NULL DEFAULT NULL COMMENT '总运行次数',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 9 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of legacy_scheduler_tasks
-- ----------------------------
INSERT INTO `legacy_scheduler_tasks` VALUES ('API定时任务', 3, 1, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 1, \"interval\": 1, \"run_time\": \"yyyy-04-We 09:23:00\", \"week_date\": [], \"week_run_time\": \"\"}', '{\"status\": 1, \"notice_id\": null}', '定时执行', NULL, NULL, NULL, 0, 1, '2026-04-08 09:22:05', 1, '2026-04-08 10:06:38', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('API定时任务', 3, 1, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 1, \"interval\": 1, \"run_time\": \"yyyy-04-We 09:23:00\", \"week_date\": [], \"week_run_time\": \"\"}', '{\"status\": 1, \"notice_id\": null}', '定时执行', NULL, NULL, NULL, 0, 2, '2026-04-08 09:22:36', 1, '2026-04-08 10:06:41', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('定时任务', 3, 1, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 1, \"interval\": 1, \"run_time\": \"yyyy-04-We 09:41:05\", \"week_date\": [], \"week_run_time\": \"\"}', '{\"status\": 1, \"notice_id\": null}', '', NULL, NULL, NULL, 0, 3, '2026-04-08 09:42:02', 1, '2026-04-08 10:06:43', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('定时任务', 3, 1, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 1, \"interval\": 1, \"run_time\": \"2026-04-08 10:09:17\", \"week_date\": [\"fri\"], \"week_run_time\": \"01:30\"}', '{\"status\": 1, \"notice_id\": null}', '9999999', '4', NULL, NULL, 0, 4, '2026-04-08 10:08:33', 1, '2026-04-08 10:27:03', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('定时执行', 3, 0, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 3, \"interval\": 1, \"run_time\": \"2026-04-08 10:44:05\", \"week_date\": [], \"week_run_time\": \"12:00\"}', '{\"status\": 1, \"notice_id\": 1}', '', NULL, '2026-04-08 12:00:01', NULL, 4, 5, '2026-04-08 10:28:27', 1, '2026-04-08 13:33:41', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('UI', 3, 0, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 4, \"interval\": 1, \"run_time\": \"\", \"week_date\": [\"wed\"], \"week_run_time\": \"12:00\"}', '{\"status\": 1, \"notice_id\": null}', '', NULL, '2026-04-08 12:00:01', NULL, 1, 6, '2026-04-08 10:49:29', 1, '2026-04-08 14:16:02', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('UI自动化定时测试任务', 2, 0, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [1], \"params_id\": null, \"web_group_list\": [1], \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": [1]}', '{\"type\": 1, \"interval\": 1, \"run_time\": \"2026-04-08 14:13:13\", \"week_date\": [], \"week_run_time\": \"\"}', '{\"status\": 1, \"notice_id\": 1}', '', NULL, '2026-04-08 14:13:14', NULL, 11, 7, '2026-04-08 11:04:43', 1, '2026-04-08 14:16:04', 1, 0, NULL);
INSERT INTO `legacy_scheduler_tasks` VALUES ('9999', 3, 0, '{\"width\": 1920, \"device\": [], \"env_id\": 1, \"height\": 1080, \"browser\": [], \"params_id\": null, \"api_script_list\": [2], \"app_script_list\": [], \"web_script_list\": []}', '{\"type\": 1, \"interval\": 1, \"run_time\": \"2026-04-08 14:00:00\", \"week_date\": [], \"week_run_time\": \"\"}', '{\"status\": 1, \"notice_id\": 1}', '', NULL, '2026-04-08 14:00:01', NULL, 4, 8, '2026-04-08 11:08:12', 1, '2026-04-08 14:16:06', 1, 0, NULL);


-- ----------------------------
-- Table structure for legacy_task_execution_histories
-- ----------------------------
DROP TABLE IF EXISTS `legacy_task_execution_histories`;
CREATE TABLE `legacy_task_execution_histories`  (
  `task_id` bigint NOT NULL COMMENT '任务ID',
  `execution_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行ID',
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行状态: success/failed/running',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `duration` int NULL DEFAULT NULL COMMENT '执行时长(秒)',
  `result` json NULL COMMENT '执行结果',
  `error_message` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '错误信息',
  `trigger_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '触发类型: scheduled/manual',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 52 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of legacy_task_execution_histories
-- ----------------------------
INSERT INTO `legacy_task_execution_histories` VALUES (5, '2a189cf4-aa20-4a7c-aace-a2a0663dd5b8', 'running', '2026-04-08 10:36:06', NULL, NULL, 'null', NULL, 'scheduled', 1, '2026-04-08 10:36:06', NULL, '2026-04-08 10:36:06', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, '2cec88bf-996c-4426-ac60-db85f4198ea3', 'running', '2026-04-08 10:42:46', NULL, NULL, 'null', NULL, 'scheduled', 2, '2026-04-08 10:42:46', NULL, '2026-04-08 10:42:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, '2cec88bf-996c-4426-ac60-db85f4198ea3', 'timeout', '2026-04-08 10:42:46', '2026-04-08 10:42:46', 0, 'null', 'job missed run time', 'scheduled', 3, '2026-04-08 10:42:46', NULL, '2026-04-08 10:42:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, 'df8b35c7-91a0-4a18-832b-b4e84ec301ea', 'running', '2026-04-08 10:44:05', NULL, NULL, 'null', NULL, 'scheduled', 4, '2026-04-08 10:44:05', NULL, '2026-04-08 10:44:05', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, 'df8b35c7-91a0-4a18-832b-b4e84ec301ea', 'success', '2026-04-08 10:44:05', '2026-04-08 10:44:06', 0, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 5, \"duration\": 0, \"end_time\": \"2026-04-08T10:44:05.617760\", \"start_time\": \"2026-04-08T10:44:05.369157\", \"execution_id\": \"67471afd-f843-4b54-bb59-00d93d7312ce\", \"error_message\": null}', NULL, 'scheduled', 5, '2026-04-08 10:44:05', NULL, '2026-04-08 10:44:05', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, 'd2646fa3-b2f2-47dc-b7cf-16cb4524c4b0', 'running', '2026-04-08 10:47:49', NULL, NULL, 'null', NULL, 'scheduled', 6, '2026-04-08 10:47:48', NULL, '2026-04-08 10:47:48', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, 'd2646fa3-b2f2-47dc-b7cf-16cb4524c4b0', 'success', '2026-04-08 10:47:49', '2026-04-08 10:47:49', 0, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 5, \"duration\": 0, \"end_time\": \"2026-04-08T10:47:49.024434\", \"start_time\": \"2026-04-08T10:47:48.970435\", \"execution_id\": \"756cbc04-6347-4e0f-a21a-cb62a349a91e\", \"error_message\": null}', NULL, 'scheduled', 7, '2026-04-08 10:47:49', NULL, '2026-04-08 10:47:49', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, '9b1eb809-48c1-473d-9593-20cb7d7c13a9', 'running', '2026-04-08 10:48:49', NULL, NULL, 'null', NULL, 'scheduled', 8, '2026-04-08 10:48:48', NULL, '2026-04-08 10:48:48', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, '9b1eb809-48c1-473d-9593-20cb7d7c13a9', 'success', '2026-04-08 10:48:49', '2026-04-08 10:48:49', 0, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 5, \"duration\": 0, \"end_time\": \"2026-04-08T10:48:48.711234\", \"start_time\": \"2026-04-08T10:48:48.672529\", \"execution_id\": \"f99c8567-2e4f-4e2a-b74d-c8e9862b51e5\", \"error_message\": null}', NULL, 'scheduled', 9, '2026-04-08 10:48:48', NULL, '2026-04-08 10:48:48', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '6b04b899-80a5-4aa2-ab0b-0e5874aafeee', 'running', '2026-04-08 11:05:18', NULL, NULL, 'null', NULL, 'scheduled', 10, '2026-04-08 11:05:18', NULL, '2026-04-08 11:05:18', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '6b04b899-80a5-4aa2-ab0b-0e5874aafeee', 'success', '2026-04-08 11:05:18', '2026-04-08 11:05:31', 12, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:05:18.996206\", \"start_time\": \"2026-04-08T11:05:18.865701\", \"execution_id\": \"f1c3151d-2608-4603-ae1e-9c4f43763eb1\", \"error_message\": null}', NULL, 'scheduled', 11, '2026-04-08 11:05:30', NULL, '2026-04-08 11:05:30', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '7571b898-61fe-4d3b-ad81-356131b3a6d2', 'running', '2026-04-08 11:08:13', NULL, NULL, 'null', NULL, 'scheduled', 12, '2026-04-08 11:08:12', NULL, '2026-04-08 11:08:12', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '7571b898-61fe-4d3b-ad81-356131b3a6d2', 'timeout', '2026-04-08 11:08:13', '2026-04-08 11:08:13', 0, 'null', 'job missed run time', 'scheduled', 13, '2026-04-08 11:08:13', NULL, '2026-04-08 11:08:13', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, '917d461e-071e-4050-9656-9ae0428c4a31', 'running', '2026-04-08 11:09:13', NULL, NULL, 'null', NULL, 'scheduled', 14, '2026-04-08 11:09:13', NULL, '2026-04-08 11:09:13', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, '917d461e-071e-4050-9656-9ae0428c4a31', 'success', '2026-04-08 11:09:13', '2026-04-08 11:09:14', 0, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 8, \"duration\": 0, \"end_time\": \"2026-04-08T11:09:13.208139\", \"start_time\": \"2026-04-08T11:09:13.058333\", \"execution_id\": \"02f137f3-1e65-44cc-a4f0-83bd74c58d36\", \"error_message\": null}', NULL, 'scheduled', 15, '2026-04-08 11:09:13', NULL, '2026-04-08 11:09:13', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, 'eb50bb13-fbfd-4d09-b5b6-a56ae6b8ffd6', 'running', '2026-04-08 11:10:13', NULL, NULL, 'null', NULL, 'scheduled', 16, '2026-04-08 11:10:13', NULL, '2026-04-08 11:10:13', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, 'eb50bb13-fbfd-4d09-b5b6-a56ae6b8ffd6', 'success', '2026-04-08 11:10:13', '2026-04-08 11:10:14', 1, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 8, \"duration\": 0, \"end_time\": \"2026-04-08T11:10:13.386117\", \"start_time\": \"2026-04-08T11:10:13.349657\", \"execution_id\": \"307f99c8-3273-4189-ba8b-20eb615f53bb\", \"error_message\": null}', NULL, 'scheduled', 17, '2026-04-08 11:10:14', NULL, '2026-04-08 11:10:14', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'aa033e61-ee79-4dad-9047-6f8566e9ee5c', 'running', '2026-04-08 11:10:14', NULL, NULL, 'null', NULL, 'scheduled', 18, '2026-04-08 11:10:14', NULL, '2026-04-08 11:10:14', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'aa033e61-ee79-4dad-9047-6f8566e9ee5c', 'timeout', '2026-04-08 11:10:14', '2026-04-08 11:10:15', 0, 'null', 'job missed run time', 'scheduled', 19, '2026-04-08 11:10:14', NULL, '2026-04-08 11:10:14', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, 'e2d90344-91f5-42ba-9349-971168200e12', 'running', '2026-04-08 11:11:15', NULL, NULL, 'null', NULL, 'scheduled', 20, '2026-04-08 11:11:14', NULL, '2026-04-08 11:11:14', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, 'e2d90344-91f5-42ba-9349-971168200e12', 'success', '2026-04-08 11:11:15', '2026-04-08 11:11:31', 16, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 8, \"duration\": 0, \"end_time\": \"2026-04-08T11:11:15.122771\", \"start_time\": \"2026-04-08T11:11:14.886348\", \"execution_id\": \"a784c0c4-4a41-4443-9a3e-8782c86a647c\", \"error_message\": null}', NULL, 'scheduled', 21, '2026-04-08 11:11:31', NULL, '2026-04-08 11:11:31', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '1ce99d06-2836-4fab-a516-032b96760d52', 'running', '2026-04-08 11:11:57', NULL, NULL, 'null', NULL, 'scheduled', 22, '2026-04-08 11:11:57', NULL, '2026-04-08 11:11:57', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '1ce99d06-2836-4fab-a516-032b96760d52', 'timeout', '2026-04-08 11:11:57', '2026-04-08 11:11:57', 0, 'null', 'job missed run time', 'scheduled', 23, '2026-04-08 11:11:57', NULL, '2026-04-08 11:11:57', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '6bb97ca2-1436-4308-a835-229c13c3cb9b', 'running', '2026-04-08 11:27:47', NULL, NULL, 'null', NULL, 'scheduled', 24, '2026-04-08 11:27:47', NULL, '2026-04-08 11:27:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '6bb97ca2-1436-4308-a835-229c13c3cb9b', 'success', '2026-04-08 11:27:47', '2026-04-08 11:27:49', 2, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:27:47.334766\", \"start_time\": \"2026-04-08T11:27:47.334766\", \"execution_id\": \"780546bd-d31a-4388-8750-9a58f052b33d\", \"error_message\": null}', NULL, 'scheduled', 25, '2026-04-08 11:27:49', NULL, '2026-04-08 11:27:49', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '6752146f-51b2-4dab-9f68-c6e617bcd827', 'running', '2026-04-08 11:28:47', NULL, NULL, 'null', NULL, 'scheduled', 26, '2026-04-08 11:28:46', NULL, '2026-04-08 11:28:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '6752146f-51b2-4dab-9f68-c6e617bcd827', 'success', '2026-04-08 11:28:47', '2026-04-08 11:28:47', 0, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:28:46.880356\", \"start_time\": \"2026-04-08T11:28:46.880356\", \"execution_id\": \"e6129617-0843-4c7a-adaa-91ec502de202\", \"error_message\": null}', NULL, 'scheduled', 27, '2026-04-08 11:28:47', NULL, '2026-04-08 11:28:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '98a43aba-cf88-42eb-be7f-d566898f3836', 'running', '2026-04-08 11:29:47', NULL, NULL, 'null', NULL, 'scheduled', 28, '2026-04-08 11:29:46', NULL, '2026-04-08 11:29:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '98a43aba-cf88-42eb-be7f-d566898f3836', 'success', '2026-04-08 11:29:47', '2026-04-08 11:29:48', 0, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:29:47.037532\", \"start_time\": \"2026-04-08T11:29:47.037532\", \"execution_id\": \"de9bac83-8fbf-4b55-96f8-88a4d1f05d13\", \"error_message\": null}', NULL, 'scheduled', 29, '2026-04-08 11:29:47', NULL, '2026-04-08 11:29:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '1150d91c-cabb-4f4c-95e4-9679c4ee9f17', 'running', '2026-04-08 11:30:47', NULL, NULL, 'null', NULL, 'scheduled', 30, '2026-04-08 11:30:46', NULL, '2026-04-08 11:30:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '1150d91c-cabb-4f4c-95e4-9679c4ee9f17', 'success', '2026-04-08 11:30:47', '2026-04-08 11:30:48', 1, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:30:46.976361\", \"start_time\": \"2026-04-08T11:30:46.976361\", \"execution_id\": \"d3603070-80d4-4240-be7b-dc6eaae69291\", \"error_message\": null}', NULL, 'scheduled', 31, '2026-04-08 11:30:47', NULL, '2026-04-08 11:30:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '075bcfee-12fa-4c72-b8d2-f5e2f2fe12b0', 'running', '2026-04-08 11:31:47', NULL, NULL, 'null', NULL, 'scheduled', 32, '2026-04-08 11:31:46', NULL, '2026-04-08 11:31:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '075bcfee-12fa-4c72-b8d2-f5e2f2fe12b0', 'success', '2026-04-08 11:31:47', '2026-04-08 11:31:47', 0, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:31:46.850984\", \"start_time\": \"2026-04-08T11:31:46.850984\", \"execution_id\": \"09250b38-843e-42c5-a34f-b429805dc0e1\", \"error_message\": null}', NULL, 'scheduled', 33, '2026-04-08 11:31:47', NULL, '2026-04-08 11:31:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '762f805b-20b4-4835-8b62-ef0159fed0ce', 'running', '2026-04-08 11:32:47', NULL, NULL, 'null', NULL, 'scheduled', 34, '2026-04-08 11:32:46', NULL, '2026-04-08 11:32:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '762f805b-20b4-4835-8b62-ef0159fed0ce', 'success', '2026-04-08 11:32:47', '2026-04-08 11:32:48', 0, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:32:46.989305\", \"start_time\": \"2026-04-08T11:32:46.989305\", \"execution_id\": \"792f7d4d-0c2d-4af8-81aa-7f45a8f8e045\", \"error_message\": null}', NULL, 'scheduled', 35, '2026-04-08 11:32:47', NULL, '2026-04-08 11:32:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '9dc5704c-31eb-4a97-b14d-3b955a483e00', 'running', '2026-04-08 11:33:47', NULL, NULL, 'null', NULL, 'scheduled', 36, '2026-04-08 11:33:46', NULL, '2026-04-08 11:33:46', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '9dc5704c-31eb-4a97-b14d-3b955a483e00', 'success', '2026-04-08 11:33:47', '2026-04-08 11:33:47', 0, '{\"result\": {\"message\": \"scheduled trigger ok (execution engine not integrated yet)\"}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:33:46.805012\", \"start_time\": \"2026-04-08T11:33:46.805012\", \"execution_id\": \"80e68682-14fe-4374-a024-c9c2a5b7f756\", \"error_message\": null}', NULL, 'scheduled', 37, '2026-04-08 11:33:47', NULL, '2026-04-08 11:33:47', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '271d09d8-30e5-476a-92ec-b1b1c810cbfa', 'running', '2026-04-08 11:35:16', NULL, NULL, 'null', NULL, 'scheduled', 38, '2026-04-08 11:35:15', NULL, '2026-04-08 11:35:15', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, '271d09d8-30e5-476a-92ec-b1b1c810cbfa', 'success', '2026-04-08 11:35:16', '2026-04-08 11:35:19', 2, '{\"result\": {\"message\": \"web automation scheduled executed\", \"script_count\": 1, \"web_group_list\": [1]}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:35:16.508311\", \"start_time\": \"2026-04-08T11:35:15.994919\", \"execution_id\": \"74b8d7b2-d940-4e75-ade1-a04f269943a5\", \"error_message\": null}', NULL, 'scheduled', 39, '2026-04-08 11:35:18', NULL, '2026-04-08 11:35:18', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'aa62431a-b4ac-4b54-bfc7-9bf22105babe', 'running', '2026-04-08 11:36:16', NULL, NULL, 'null', NULL, 'scheduled', 40, '2026-04-08 11:36:18', NULL, '2026-04-08 11:36:18', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'aa62431a-b4ac-4b54-bfc7-9bf22105babe', 'timeout', '2026-04-08 11:36:16', '2026-04-08 11:36:19', 3, 'null', 'job missed run time', 'scheduled', 41, '2026-04-08 11:36:19', NULL, '2026-04-08 11:36:19', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'f7ac7ec4-0290-44a2-b11a-7bf3038523c7', 'running', '2026-04-08 11:37:16', NULL, NULL, 'null', NULL, 'scheduled', 42, '2026-04-08 11:37:16', NULL, '2026-04-08 11:37:16', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'f7ac7ec4-0290-44a2-b11a-7bf3038523c7', 'success', '2026-04-08 11:37:16', '2026-04-08 11:37:18', 1, '{\"result\": {\"message\": \"web automation scheduled executed\", \"script_count\": 1, \"web_group_list\": [1]}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T11:37:16.561137\", \"start_time\": \"2026-04-08T11:37:16.430121\", \"execution_id\": \"eea87193-87a0-41cd-9da4-a8de538e79b7\", \"error_message\": null}', NULL, 'scheduled', 43, '2026-04-08 11:37:17', NULL, '2026-04-08 11:37:17', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, '7e43baf2-cf44-462f-b28a-8a4806fc5fc6', 'running', '2026-04-08 12:00:00', NULL, NULL, 'null', NULL, 'scheduled', 44, '2026-04-08 12:00:00', NULL, '2026-04-08 12:00:00', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (6, 'c9698967-1d98-4607-8d4a-8c4077f3a53a', 'running', '2026-04-08 12:00:00', NULL, NULL, 'null', NULL, 'scheduled', 45, '2026-04-08 12:00:00', NULL, '2026-04-08 12:00:00', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (6, 'c9698967-1d98-4607-8d4a-8c4077f3a53a', 'success', '2026-04-08 12:00:00', '2026-04-08 12:00:02', 1, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 6, \"duration\": 1, \"end_time\": \"2026-04-08T12:00:01.489897\", \"start_time\": \"2026-04-08T12:00:00.393637\", \"execution_id\": \"ca1ebfbd-0d4f-4297-82ae-80b564b0fc74\", \"error_message\": null}', NULL, 'scheduled', 46, '2026-04-08 12:00:02', NULL, '2026-04-08 12:00:02', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (5, '7e43baf2-cf44-462f-b28a-8a4806fc5fc6', 'success', '2026-04-08 12:00:00', '2026-04-08 12:00:03', 2, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2]}, \"status\": \"success\", \"task_id\": 5, \"duration\": 1, \"end_time\": \"2026-04-08T12:00:01.428870\", \"start_time\": \"2026-04-08T12:00:00.392668\", \"execution_id\": \"28ba60fd-1594-4346-9391-54963c344821\", \"error_message\": null}', NULL, 'scheduled', 47, '2026-04-08 12:00:02', NULL, '2026-04-08 12:00:02', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, '1dd521fe-75ef-4db4-be1e-6a234e483eb6', 'running', '2026-04-08 14:00:00', NULL, NULL, 'null', NULL, 'scheduled', 48, '2026-04-08 14:00:00', NULL, '2026-04-08 14:00:00', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (8, '1dd521fe-75ef-4db4-be1e-6a234e483eb6', 'success', '2026-04-08 14:00:00', '2026-04-08 14:00:03', 2, '{\"result\": {\"message\": \"api automation scheduled executed\", \"scripts\": [2], \"api_result_id\": 1775628000696}, \"status\": \"success\", \"task_id\": 8, \"duration\": 0, \"end_time\": \"2026-04-08T14:00:01.436808\", \"start_time\": \"2026-04-08T14:00:00.680910\", \"execution_id\": \"be67ca03-4976-4732-a974-c652801b44c6\", \"error_message\": null}', NULL, 'scheduled', 49, '2026-04-08 14:00:02', NULL, '2026-04-08 14:00:02', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'f4510265-9101-4f1b-8467-c81963a3843a', 'running', '2026-04-08 14:13:13', NULL, NULL, 'null', NULL, 'scheduled', 50, '2026-04-08 14:13:13', NULL, '2026-04-08 14:13:13', NULL, 1, NULL);
INSERT INTO `legacy_task_execution_histories` VALUES (7, 'f4510265-9101-4f1b-8467-c81963a3843a', 'success', '2026-04-08 14:13:13', '2026-04-08 14:13:15', 1, '{\"result\": {\"message\": \"web automation scheduled executed\", \"script_count\": 1, \"web_result_id\": \"1775628793233\", \"web_group_list\": [1]}, \"status\": \"success\", \"task_id\": 7, \"duration\": 0, \"end_time\": \"2026-04-08T14:13:13.839248\", \"start_time\": \"2026-04-08T14:13:13.205412\", \"execution_id\": \"46c01a0a-3318-4ec8-8f06-4f6bd1810f7b\", \"error_message\": null}', NULL, 'scheduled', 51, '2026-04-08 14:13:14', NULL, '2026-04-08 14:13:14', NULL, 1, NULL);


-- ----------------------------
-- Table structure for legacy_task_notification_logs
-- ----------------------------
DROP TABLE IF EXISTS `legacy_task_notification_logs`;
CREATE TABLE `legacy_task_notification_logs`  (
  `task_id` bigint NOT NULL COMMENT '任务ID',
  `execution_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行ID',
  `notice_id` bigint NOT NULL COMMENT '通知配置ID',
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '通知状态: success/failed',
  `send_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发送时间',
  `response` json NULL COMMENT '通知响应',
  `error_message` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '错误信息',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of legacy_task_notification_logs
-- ----------------------------


-- ----------------------------
-- Table structure for mini_menus
-- ----------------------------
DROP TABLE IF EXISTS `mini_menus`;
CREATE TABLE `mini_menus`  (
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '名称',
  `pid` bigint NOT NULL COMMENT '父ID',
  `type` int NOT NULL COMMENT '0=目录 1=脚本组 2=脚本',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `project_id` bigint NULL DEFAULT NULL COMMENT '所属项目ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '小程序自动化菜单表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mini_menus
-- ----------------------------


-- ----------------------------
-- Table structure for mini_result_lists
-- ----------------------------
DROP TABLE IF EXISTS `mini_result_lists`;
CREATE TABLE `mini_result_lists`  (
  `task_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务名称',
  `result_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行ID',
  `platform` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '平台',
  `framework` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '框架',
  `device_info` json NULL COMMENT '设备信息',
  `script_list` json NOT NULL COMMENT '脚本列表',
  `script_status` json NOT NULL COMMENT '执行状态',
  `project_id` bigint NULL DEFAULT NULL COMMENT '所属项目ID',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `result_id`(`result_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '小程序自动化执行汇总表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mini_result_lists
-- ----------------------------


-- ----------------------------
-- Table structure for mini_results
-- ----------------------------
DROP TABLE IF EXISTS `mini_results`;
CREATE TABLE `mini_results`  (
  `result_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '执行ID',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '步骤名称',
  `status` int NOT NULL COMMENT '0=失败 1=成功 2=进行中',
  `log` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '日志',
  `before_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行前截图',
  `after_img` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '执行后截图',
  `assert_value` json NULL COMMENT '断言详情',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '执行时间',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '小程序自动化步骤结果表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mini_results
-- ----------------------------


-- ----------------------------
-- Table structure for mini_scripts
-- ----------------------------
DROP TABLE IF EXISTS `mini_scripts`;
CREATE TABLE `mini_scripts`  (
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `platform` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '平台: wechat | alipay | douyin | baidu | generic',
  `framework` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '框架: minium | appium | playwright',
  `script` json NOT NULL COMMENT '步骤列表',
  `platform_config` json NULL COMMENT '平台配置',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `create_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `menu_id`(`menu_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '小程序自动化脚本表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of mini_scripts
-- ----------------------------


-- ----------------------------
-- Table structure for module_info
-- ----------------------------
DROP TABLE IF EXISTS `module_info`;
CREATE TABLE `module_info`  (
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '模块名称',
  `project_id` int NOT NULL COMMENT '所属项目ID',
  `parent_id` bigint NULL DEFAULT NULL COMMENT '父模块ID',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '模块描述',
  `sort_order` int NULL DEFAULT NULL COMMENT '排序顺序',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_module_parent`(`parent_id` ASC) USING BTREE,
  INDEX `idx_module_project`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '测试模块信息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of module_info
-- ----------------------------
INSERT INTO `module_info` VALUES ('默认模块', 1, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 1, 1, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 2, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 2, 2, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 3, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 3, 3, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 4, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 4, 4, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 5, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 5, 5, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 6, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 6, 6, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 7, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 7, 7, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 13, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 8, 8, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 14, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 9, 9, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 15, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 10, 10, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('默认模块', 16, NULL, '系统自动创建的默认模块，用于存放未分类的测试用例', 11, 11, '2026-02-26 13:50:58', 1, NULL, NULL, 1, NULL);
INSERT INTO `module_info` VALUES ('99', 2, NULL, '', 0, 12, '2026-04-01 11:28:52', 1, '2026-04-01 11:28:56', NULL, 0, NULL);


-- ----------------------------
-- Table structure for notification_histories
-- ----------------------------
DROP TABLE IF EXISTS `notification_histories`;
CREATE TABLE `notification_histories`  (
  `config_id` bigint NOT NULL COMMENT '通知配置ID',
  `title` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '通知标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '通知内容',
  `recipient` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '接收者',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '发送状态: pending/success/failed',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误信息',
  `sent_at` int NULL DEFAULT NULL COMMENT '发送时间戳',
  `response_data` json NULL COMMENT '响应数据',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_config_id`(`config_id` ASC) USING BTREE,
  INDEX `idx_sent_at`(`sent_at` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '通知历史记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of notification_histories
-- ----------------------------


-- ----------------------------
-- Table structure for ntest_coverage_detail
-- ----------------------------
DROP TABLE IF EXISTS `ntest_coverage_detail`;
CREATE TABLE `ntest_coverage_detail`  (
  `report_id` bigint NOT NULL COMMENT '关联报告 ID',
  `package_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '包名',
  `class_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '类名',
  `class_file_content` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '类源代码内容',
  `class_source_path` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '源文件路径',
  `class_md5` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '源文件 MD5',
  `class_missed` int NULL DEFAULT NULL COMMENT '类未覆盖数',
  `class_covered` int NULL DEFAULT NULL COMMENT '类已覆盖数',
  `methods` json NULL COMMENT '方法覆盖详情列表 (JSON)',
  `branch_missed` int NULL DEFAULT NULL,
  `branch_covered` int NULL DEFAULT NULL,
  `instruction_missed` int NULL DEFAULT NULL,
  `instruction_covered` int NULL DEFAULT NULL,
  `line_missed` int NULL DEFAULT NULL,
  `line_covered` int NULL DEFAULT NULL,
  `method_missed` int NULL DEFAULT NULL,
  `method_covered` int NULL DEFAULT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ntest_coverage_detail_package_name`(`package_name` ASC) USING BTREE,
  INDEX `ix_ntest_coverage_detail_report_id`(`report_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ntest_coverage_detail
-- ----------------------------


-- ----------------------------
-- Table structure for ntest_coverage_report
-- ----------------------------
DROP TABLE IF EXISTS `ntest_coverage_report`;
CREATE TABLE `ntest_coverage_report`  (
  `name` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '报告名称',
  `service_id` bigint NOT NULL COMMENT '关联 API 服务 ID',
  `repo_id` bigint NOT NULL COMMENT '关联仓库 ID',
  `coverage_type` int NOT NULL COMMENT '覆盖类型: 10=全量, 20=增量',
  `coverage_rate` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '覆盖率, 如 \"85.3%\"',
  `new_branches` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '新分支',
  `new_last_commit_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '新 Commit ID',
  `old_branches` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '旧分支 (增量模式)',
  `old_last_commit_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '旧 Commit ID (增量模式)',
  `package_count` int NULL DEFAULT NULL COMMENT '包数量',
  `class_count` int NULL DEFAULT NULL COMMENT '类数量',
  `method_count` int NULL DEFAULT NULL COMMENT '方法数量',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ntest_coverage_report_name`(`name` ASC) USING BTREE,
  INDEX `ix_ntest_coverage_report_service_id`(`service_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ntest_coverage_report
-- ----------------------------


-- ----------------------------
-- Table structure for ntest_repository
-- ----------------------------
DROP TABLE IF EXISTS `ntest_repository`;
CREATE TABLE `ntest_repository`  (
  `name` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '仓库名称',
  `html_url` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '仓库地址（Git URL）',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '仓库描述',
  `service_id` bigint NOT NULL COMMENT '关联 API 服务 ID',
  `service_host` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '服务部署地址（IP/域名），用于 jacoco dump',
  `jacoco_port` int NULL DEFAULT NULL COMMENT 'JaCoCo agent TCP 端口，默认 6300',
  `lang_type` varchar(32) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '语言类型: java / python / javascript / go',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ntest_repository_name`(`name` ASC) USING BTREE,
  INDEX `ix_ntest_repository_service_id`(`service_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ntest_repository
-- ----------------------------


-- ----------------------------
-- Table structure for permission
-- ----------------------------
DROP TABLE IF EXISTS `permission`;
CREATE TABLE `permission`  (
  `permission_code` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '权限编码',
  `permission_name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '权限名称',
  `permission_type` smallint NOT NULL COMMENT '1菜单权限 2按钮权限 3数据权限 4API权限',
  `resource_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '资源类型',
  `resource_id` bigint NULL DEFAULT NULL COMMENT '关联资源ID',
  `status` smallint NULL DEFAULT NULL COMMENT '1启用 0禁用',
  `sort` int NULL DEFAULT NULL COMMENT '排序',
  `description` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_permission_permission_code`(`permission_code` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 131 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of permission
-- ----------------------------
INSERT INTO `permission` VALUES ('user:query', '查询用户', 2, 'user', NULL, 1, 1, NULL, 48, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('user:add', '新增用户', 2, 'user', NULL, 1, 2, NULL, 49, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('user:edit', '编辑用户', 2, 'user', NULL, 1, 3, NULL, 50, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('user:disable', '禁用用户', 2, 'user', NULL, 1, 4, NULL, 51, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('user:resetpwd', '重置密码', 2, 'user', NULL, 1, 5, NULL, 52, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('user:delete', '删除用户', 2, 'user', NULL, 1, 6, NULL, 53, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('role:query', '查询角色', 2, 'role', NULL, 1, 1, NULL, 54, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('role:add', '新增角色', 2, 'role', NULL, 1, 2, NULL, 55, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('role:edit', '编辑角色', 2, 'role', NULL, 1, 3, NULL, 56, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('role:delete', '删除角色', 2, 'role', NULL, 1, 4, NULL, 57, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('dept:add', '新增部门', 2, 'dept', NULL, 1, 1, NULL, 58, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('dept:edit', '编辑部门', 2, 'dept', NULL, 1, 2, NULL, 59, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('dept:disable', '禁用部门', 2, 'dept', NULL, 1, 3, NULL, 60, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('dept:delete', '删除部门', 2, 'dept', NULL, 1, 4, NULL, 61, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('project:query', '查询项目', 2, 'project', NULL, 1, 1, NULL, 62, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('project:add', '新增项目', 2, 'project', NULL, 1, 2, NULL, 63, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('project:edit', '编辑项目', 2, 'project', NULL, 1, 3, NULL, 64, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('project:delete', '删除项目', 2, 'project', NULL, 1, 4, NULL, 65, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('loginRecord:query', '查询记录', 2, 'loginRecord', NULL, 1, 1, NULL, 66, '2026-01-30 16:28:24', NULL, '2026-01-30 16:28:24', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('dept:query', '查询部门', 2, 'dept', NULL, 1, 0, NULL, 79, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('menu:query', '查询菜单', 2, 'menu', NULL, 1, 0, NULL, 80, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('dict:query', '查询字典', 2, 'dict', NULL, 1, 0, NULL, 81, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('file:query', '查询文件', 2, 'file', NULL, 1, 0, NULL, 82, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('depy:query', '查询部门', 2, 'depy', NULL, 1, 0, NULL, 83, '2026-01-31 08:55:08', 1, '2026-01-31 08:55:08', 1, 1, NULL);
INSERT INTO `permission` VALUES ('dict:add', '新增字典', 2, 'dict', NULL, 1, 0, NULL, 84, '2026-01-31 08:58:14', 1, '2026-01-31 08:58:14', 1, 1, NULL);
INSERT INTO `permission` VALUES ('dict:edit', '编辑字典', 2, 'dict', NULL, 1, 0, NULL, 85, '2026-01-31 08:58:59', 1, '2026-01-31 08:58:59', 1, 1, NULL);
INSERT INTO `permission` VALUES ('dict:delete', '删除字典', 2, 'dict', NULL, 1, 0, NULL, 86, '2026-01-31 08:59:50', 1, '2026-01-31 08:59:50', 1, 1, NULL);
INSERT INTO `permission` VALUES ('menu:add', '新增菜单', 2, 'menu', NULL, 1, 0, NULL, 87, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('menu:edit', '编辑菜单', 2, 'menu', NULL, 1, 0, NULL, 88, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('menu:delete', '删除菜单', 2, 'menu', NULL, 1, 0, NULL, 89, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('monitor:server:list', '服务器监控查看', 1, 'menu', NULL, 1, 1, '查看服务器监控信息', 90, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('monitor:server:info', '获取服务器信息', 4, 'api', NULL, 1, 2, '获取服务器监控详细信息', 91, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('monitor:online:list', '在线用户查看', 1, 'menu', NULL, 1, 3, '查看在线用户列表', 92, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('monitor:online:stats', '在线用户统计', 4, 'api', NULL, 1, 4, '获取在线用户统计信息', 93, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('monitor:online:force-offline', '强制用户下线', 2, 'button', NULL, 1, 5, '强制指定用户下线', 94, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('monitor:online:cleanup', '清理过期用户', 2, 'button', NULL, 1, 6, '清理过期的在线用户', 95, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:user:list', '用户列表API', 4, 'api', NULL, 1, 0, '获取用户列表的API权限', 96, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:user:detail', '用户详情API', 4, 'api', NULL, 1, 0, '获取用户详情的API权限', 97, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:user:create', '创建用户API', 4, 'api', NULL, 1, 0, '创建用户的API权限', 98, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:user:update', '更新用户API', 4, 'api', NULL, 1, 0, '更新用户的API权限', 99, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:user:delete', '删除用户API', 4, 'api', NULL, 1, 0, '删除用户的API权限', 100, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:user:reset-password', '重置密码API', 4, 'api', NULL, 1, 0, '重置用户密码的API权限', 101, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:role:list', '角色列表API', 4, 'api', NULL, 1, 0, '获取角色列表的API权限', 102, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:role:detail', '角色详情API', 4, 'api', NULL, 1, 0, '获取角色详情的API权限', 103, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:role:create', '创建角色API', 4, 'api', NULL, 1, 0, '创建角色的API权限', 104, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:role:update', '更新角色API', 4, 'api', NULL, 1, 0, '更新角色的API权限', 105, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:role:delete', '删除角色API', 4, 'api', NULL, 1, 0, '删除角色的API权限', 106, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:dept:list', '部门列表API', 4, 'api', NULL, 1, 0, '获取部门列表的API权限', 107, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:dept:detail', '部门详情API', 4, 'api', NULL, 1, 0, '获取部门详情的API权限', 108, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:dept:create', '创建部门API', 4, 'api', NULL, 1, 0, '创建部门的API权限', 109, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:dept:update', '更新部门API', 4, 'api', NULL, 1, 0, '更新部门的API权限', 110, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('api:dept:delete', '删除部门API', 4, 'api', NULL, 1, 0, '删除部门的API权限', 111, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('business:user:list', '业务用户列表', 4, 'api', NULL, 1, 0, '业务模块用户列表权限', 112, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('business:user:detail', '业务用户详情', 4, 'api', NULL, 1, 0, '业务模块用户详情权限', 113, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('business:user:reset-password', '业务重置密码', 4, 'api', NULL, 1, 0, '业务模块重置密码权限', 114, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('business:admin:reset-password', '管理员重置密码', 4, 'api', NULL, 1, 0, '管理员重置任意用户密码权限', 115, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('business:stats:view', '查看统计信息', 4, 'api', NULL, 1, 0, '查看业务统计信息权限', 116, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('data:user:all', '用户全部数据', 3, 'data', NULL, 1, 0, '可以查看所有用户数据', 117, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('data:user:dept', '用户部门数据', 3, 'data', NULL, 1, 0, '可以查看本部门用户数据', 118, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('data:user:dept-child', '用户部门及下级数据', 3, 'data', NULL, 1, 0, '可以查看本部门及下级部门用户数据', 119, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('data:user:self', '用户个人数据', 3, 'data', NULL, 1, 0, '只能查看自己创建的用户数据', 120, '2026-02-03 11:40:53', 1, '2026-02-03 11:40:53', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:login:list', '查看登录日志', 4, 'log', NULL, 1, 1, '查看登录日志列表', 121, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:login:query', '查询登录日志', 2, 'log', NULL, 1, 2, '查询登录日志', 122, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:login:detail', '查看登录日志详情', 2, 'log', NULL, 1, 3, '查看登录日志详情信息', 123, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:login:delete', '删除登录日志', 2, 'log', NULL, 1, 4, '删除登录日志记录', 124, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:login:clean', '清理登录日志', 2, 'log', NULL, 1, 5, '清理旧的登录日志记录', 125, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:operation:list', '查看操作日志', 4, 'log', NULL, 1, 6, '查看操作日志列表', 126, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:operation:query', '查询操作日志', 2, 'log', NULL, 1, 7, '查询操作日志', 127, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:operation:detail', '查看操作日志详情', 2, 'log', NULL, 1, 8, '查看操作日志详情信息', 128, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:operation:delete', '删除操作日志', 2, 'log', NULL, 1, 9, '删除操作日志记录', 129, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);
INSERT INTO `permission` VALUES ('system:log:operation:clean', '清理操作日志', 2, 'log', NULL, 1, 10, '清理旧的操作日志记录', 130, '2026-02-03 15:32:00', NULL, '2026-02-03 15:32:00', NULL, 1, NULL);


-- ----------------------------
-- Table structure for project_api_key
-- ----------------------------
DROP TABLE IF EXISTS `project_api_key`;
CREATE TABLE `project_api_key`  (
  `user_id` bigint NOT NULL COMMENT '所属用户',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '密钥名称',
  `service_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '服务类型 openai/claude/...',
  `key_value` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '密钥值',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '描述',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_project_apikey_user_name`(`user_id` ASC, `name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'API 密钥表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_api_key
-- ----------------------------


-- ----------------------------
-- Table structure for project_environments
-- ----------------------------
DROP TABLE IF EXISTS `project_environments`;
CREATE TABLE `project_environments`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '环境名称',
  `base_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '基础URL',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '环境描述',
  `variables` json NULL COMMENT '环境变量',
  `is_default` tinyint(1) NULL DEFAULT NULL COMMENT '是否默认',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_pe_project`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '项目环境表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_environments
-- ----------------------------


-- ----------------------------
-- Table structure for project_info
-- ----------------------------
DROP TABLE IF EXISTS `project_info`;
CREATE TABLE `project_info`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '项目ID',
  `name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '项目名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '项目描述',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_info
-- ----------------------------
INSERT INTO `project_info` VALUES (1, '99', '99', '2026-01-30 16:56:10', 1, '2026-01-30 16:56:15', 1, 0, NULL);
INSERT INTO `project_info` VALUES (2, '9988', '99', '2026-01-30 17:56:11', 5, '2026-01-30 18:03:34', 7, 1, NULL);
INSERT INTO `project_info` VALUES (3, '77777', '7777', '2026-01-30 18:05:24', 7, '2026-01-30 18:05:35', 7, 1, NULL);


-- ----------------------------
-- Table structure for prompt_configs
-- ----------------------------
DROP TABLE IF EXISTS `prompt_configs`;
CREATE TABLE `prompt_configs`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '配置名称',
  `prompt_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '提示词类型: writer/reviewer',
  `content` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '提示词内容',
  `is_active` int NULL DEFAULT NULL COMMENT '是否启用',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NOT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of prompt_configs
-- ----------------------------
INSERT INTO `prompt_configs` VALUES (6, '默认编写提示词', 'writer', '你是一位拥有20年经验的资深测试用例编写专家，能够根据需求精确生成高质量的测试用例。\n# 核心目标\n生成高覆盖率、颗粒度细致的测试用例，确保不遗漏任何功能逻辑、异常场景和边界条件。\n# 角色设定\n1. 身份：精通全栈测试（Web/App/API）的高级QA专家\n2. 测试风格：破坏性测试思维，善于发现潜在Bug\n3. 输出原则：详细、独立、可执行\n# 用例设计规范\n1. **独立性**：每条用例只验证一个具体的测试点，严禁合并多个场景。\n2. **完整性**：\n- 包含用例ID（[模块]_[序号]）\n- 清晰的测试目标\n- 准确的前置条件\n- 步骤化操作描述\n- 具体的预期结果\n3. **覆盖维度**：\n- [正向] 功能正向流程（Happy Path）\n- [异常] 异常流程（输入错误、权限不足、网络异常）\n- [边界] 边界值（最大/最小值、空值、特殊字符）\n- [约束] 业务约束（状态机流转、数据依赖）\n# 输出格式\n请严格按照以下Markdown表格格式输出，不要包含任何开场白或结束语：\n## 重要：输出顺序要求\n1. **必须按用例编号从小到大的顺序输出**（如：001, 002, 003...）\n2. **绝对不能跳号、重复或乱序输出**\n3. 编号必须连续，中间不能有遗漏\n4. 所有用例必须一次性完整输出，不能中断\n```markdown\n| 用例ID | 测试标题 | 前置条件 | 操作步骤 | 预期结果 | 优先级 | 测试类型 | 关联需求 |\n|--------|--------|--------|--------|--------|--------|--------|--------|\n| LOGIN_001 | 验证手机号格式校验 | 在登录页 | 1. 输入10位手机号<br>2. 点击获取验证码 | 提示\"手机号格式不正确\"，发送按钮不可点 | P1 | 功能验证 | 登录模块 |\n```', 1, '2026-02-25 16:53:28', 1, '2026-03-03 10:46:11', NULL, 1, NULL);
INSERT INTO `prompt_configs` VALUES (7, '默认评审提示词', 'reviewer', '你是一名资深测试专家（Test Architect），拥有极高的质量标准。你的任务是对生成的测试用例进行严格的评审。\n# 核心职责\n不只是简单通过，而是要作为\"质量守门员\"，敏锐地发现遗漏的场景、逻辑漏洞和描述不清的问题。\n# 评审维度\n1. **覆盖率检查**：\n- 是否遗漏了需求文档中的关键功能点？\n- 是否包含了必要的异常场景（如断网、服务超时、数据错误）？\n- 是否覆盖了边界条件（如最大长度、空值、特殊字符）？\n2. **逻辑性检查**：\n- 前置条件是否充分？（例如测试\"支付功能\"前是否检查了\"余额充足\"）\n- 预期结果是否具体？（拒绝模糊的\"显示正确\"，必须说明具体提示文案或状态变化）\n3. **规范性检查**：\n- 用例标题是否清晰表达了测试意图？\n- 步骤是否可执行？\n# 输出要求\n请输出一份结构化的评审报告：\n1. **总体评价**：给出一个质量评分（0-100分）和总体结论（通过/需修改）。\n2. **发现的问题**：列出具体的问题点，精确到具体的用例ID。\n3. **补充建议**：直接给出建议补充的测试场景或用例。\n4. **修正后的用例**（可选）：如果发现严重问题，请直接提供修正后的用例版本。', 1, '2026-02-25 16:53:28', 1, '2026-02-25 16:53:28', NULL, 1, NULL);


-- ----------------------------
-- Table structure for requirement_analyses
-- ----------------------------
DROP TABLE IF EXISTS `requirement_analyses`;
CREATE TABLE `requirement_analyses`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `document_id` bigint NULL DEFAULT NULL COMMENT '文档ID',
  `analysis_result` json NULL COMMENT '分析结果',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of requirement_analyses
-- ----------------------------


-- ----------------------------
-- Table structure for requirement_documents
-- ----------------------------
DROP TABLE IF EXISTS `requirement_documents`;
CREATE TABLE `requirement_documents`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `title` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '文档标题',
  `file_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '文档文件路径',
  `document_type` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '文档类型: pdf/docx/txt/md',
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '状态: uploaded/analyzing/analyzed/failed',
  `file_size` int NULL DEFAULT NULL COMMENT '文件大小(bytes)',
  `extracted_text` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '提取的文本内容',
  `uploaded_by` bigint NOT NULL COMMENT '上传者ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of requirement_documents
-- ----------------------------


-- ----------------------------
-- Table structure for review_assignments
-- ----------------------------
DROP TABLE IF EXISTS `review_assignments`;
CREATE TABLE `review_assignments`  (
  `review_id` bigint NOT NULL COMMENT '评审ID',
  `reviewer_id` bigint NOT NULL COMMENT '评审人ID',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '评审状态: pending/in_progress/completed/rejected',
  `comment` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '评审意见',
  `checklist_results` json NULL COMMENT '检查清单结果',
  `reviewed_at` datetime NULL DEFAULT NULL COMMENT '评审时间',
  `assigned_at` datetime NULL DEFAULT NULL COMMENT '分配时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_review_reviewer`(`review_id` ASC, `reviewer_id` ASC) USING BTREE,
  INDEX `idx_review`(`review_id` ASC) USING BTREE,
  INDEX `idx_reviewer`(`reviewer_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `ix_review_assignments_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of review_assignments
-- ----------------------------


-- ----------------------------
-- Table structure for review_comments
-- ----------------------------
DROP TABLE IF EXISTS `review_comments`;
CREATE TABLE `review_comments`  (
  `review_id` bigint NOT NULL COMMENT '评审ID',
  `test_case_id` bigint NULL DEFAULT NULL COMMENT '相关用例ID',
  `author_id` bigint NOT NULL COMMENT '评论者ID',
  `comment_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '意见类型: general/suggestion/issue/question',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '意见内容',
  `step_number` int NULL DEFAULT NULL COMMENT '步骤序号',
  `is_resolved` tinyint(1) NULL DEFAULT NULL COMMENT '是否已解决',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_author`(`author_id` ASC) USING BTREE,
  INDEX `idx_resolved`(`is_resolved` ASC) USING BTREE,
  INDEX `idx_review`(`review_id` ASC) USING BTREE,
  INDEX `idx_test_case`(`test_case_id` ASC) USING BTREE,
  INDEX `ix_review_comments_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of review_comments
-- ----------------------------


-- ----------------------------
-- Table structure for review_results
-- ----------------------------
DROP TABLE IF EXISTS `review_results`;
CREATE TABLE `review_results`  (
  `review_id` bigint NOT NULL COMMENT '评审ID',
  `test_case_id` bigint NOT NULL COMMENT '测试用例ID',
  `reviewer_id` bigint NOT NULL COMMENT '评审人ID',
  `result` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '评审结果: pass/fail/modify',
  `comment` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '评审意见',
  `reviewed_at` datetime NULL DEFAULT NULL COMMENT '评审时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_review_case_reviewer`(`review_id` ASC, `test_case_id` ASC, `reviewer_id` ASC) USING BTREE,
  INDEX `idx_result`(`result` ASC) USING BTREE,
  INDEX `idx_review`(`review_id` ASC) USING BTREE,
  INDEX `idx_reviewer`(`reviewer_id` ASC) USING BTREE,
  INDEX `idx_test_case`(`test_case_id` ASC) USING BTREE,
  INDEX `ix_review_results_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of review_results
-- ----------------------------
INSERT INTO `review_results` VALUES (1, 3, 1, 'fail', '99', '2026-04-01 11:26:23', 1, '2026-04-01 11:26:23', 1, '2026-04-01 11:26:23', 1, 1, NULL, '2026-04-01 11:26:23', '2026-04-01 11:26:23');


-- ----------------------------
-- Table structure for review_templates
-- ----------------------------
DROP TABLE IF EXISTS `review_templates`;
CREATE TABLE `review_templates`  (
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '模板描述',
  `checklist` json NULL COMMENT '检查清单',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_active`(`is_active` ASC) USING BTREE,
  INDEX `idx_creator`(`creator_id` ASC) USING BTREE,
  INDEX `ix_review_templates_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of review_templates
-- ----------------------------


-- ----------------------------
-- Table structure for review_test_cases
-- ----------------------------
DROP TABLE IF EXISTS `review_test_cases`;
CREATE TABLE `review_test_cases`  (
  `review_id` bigint NOT NULL COMMENT '评审ID',
  `test_case_id` bigint NOT NULL COMMENT '测试用例ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_review_case`(`review_id` ASC, `test_case_id` ASC) USING BTREE,
  INDEX `idx_review`(`review_id` ASC) USING BTREE,
  INDEX `idx_test_case`(`test_case_id` ASC) USING BTREE,
  INDEX `ix_review_test_cases_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of review_test_cases
-- ----------------------------


-- ----------------------------
-- Table structure for role_menu
-- ----------------------------
DROP TABLE IF EXISTS `role_menu`;
CREATE TABLE `role_menu`  (
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_role_menu_menu_id`(`menu_id` ASC) USING BTREE,
  INDEX `ix_role_menu_role_id`(`role_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 322 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_menu
-- ----------------------------
INSERT INTO `role_menu` VALUES (2, 93, 191, '2026-01-30 17:11:31', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_menu` VALUES (2, 94, 192, '2026-01-30 17:11:31', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_menu` VALUES (2, 1, 193, '2026-01-30 17:11:31', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 1, 197, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 28, 198, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 29, 199, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 30, 200, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 31, 201, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 51, 202, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 61, 203, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 63, 204, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 64, 205, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 65, 206, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 66, 207, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 67, 208, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 76, 209, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 77, 210, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 78, 211, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 79, 212, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 80, 213, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 81, 214, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 82, 215, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 83, 216, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 84, 217, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 85, 218, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 86, 219, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 87, 220, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 88, 221, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 89, 222, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 90, 223, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 91, 224, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 92, 225, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 93, 226, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 94, 227, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 95, 228, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 96, 229, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (1, 97, 230, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (3, 1, 231, '2026-01-30 17:18:59', 1, '2026-01-30 17:18:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (3, 93, 232, '2026-01-30 17:18:59', 1, '2026-01-30 17:18:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (3, 94, 233, '2026-01-30 17:18:59', 1, '2026-01-30 17:18:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 1, 234, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 93, 235, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 94, 236, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 29, 237, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 85, 238, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 86, 239, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 87, 240, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 88, 241, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 89, 242, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 90, 243, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 91, 244, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 92, 245, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 79, 246, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 80, 247, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 81, 248, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 82, 249, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 83, 250, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 84, 251, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 51, 252, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 66, 253, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 61, 254, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (4, 67, 255, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 1, 291, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 93, 292, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 29, 293, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 85, 294, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 89, 295, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 79, 296, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 101, 297, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 66, 298, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 61, 299, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (8, 67, 300, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 1, 311, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 93, 312, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 105, 313, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 85, 314, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 100, 315, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 89, 316, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 79, 317, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 101, 318, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 66, 319, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 61, 320, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);
INSERT INTO `role_menu` VALUES (6, 67, 321, '2026-01-31 09:24:59', 1, '2026-01-31 09:24:59', 1, 1, NULL);


-- ----------------------------
-- Table structure for role_permission
-- ----------------------------
DROP TABLE IF EXISTS `role_permission`;
CREATE TABLE `role_permission`  (
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `permission_id` bigint NOT NULL COMMENT '权限ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_role_permission_permission_id`(`permission_id` ASC) USING BTREE,
  INDEX `ix_role_permission_role_id`(`role_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 243 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of role_permission
-- ----------------------------
INSERT INTO `role_permission` VALUES (1, 48, 126, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 49, 127, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 50, 128, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 51, 129, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 52, 130, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 53, 131, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 54, 132, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 55, 133, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 56, 134, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 57, 135, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 58, 136, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 59, 137, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 60, 138, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 61, 139, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 62, 140, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 63, 141, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 64, 142, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 65, 143, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 66, 144, '2026-01-30 17:18:09', 1, '2026-01-30 17:18:09', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (3, 62, 145, '2026-01-30 17:18:59', 1, '2026-01-30 17:18:59', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (3, 63, 146, '2026-01-30 17:18:59', 1, '2026-01-30 17:18:59', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 48, 147, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 49, 148, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 50, 149, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 51, 150, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 52, 151, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 53, 152, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 54, 153, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 55, 154, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 56, 155, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 57, 156, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 58, 157, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 59, 158, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 60, 159, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 61, 160, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 62, 161, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (4, 63, 162, '2026-01-30 17:20:48', 1, '2026-01-30 17:20:48', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 79, 184, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 80, 185, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 81, 186, '2026-01-30 18:28:17', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 82, 187, '2026-01-30 18:28:18', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (8, 48, 188, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (8, 54, 189, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (8, 58, 190, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (8, 62, 191, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (8, 81, 192, '2026-01-31 09:02:21', 1, '2026-01-31 09:02:21', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 84, 198, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 85, 199, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 86, 200, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 87, 201, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 88, 202, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 89, 203, '2026-01-31 09:08:52', 1, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 48, 204, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 54, 205, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 58, 206, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 62, 207, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 83, 208, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 81, 209, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (6, 80, 210, '2026-01-31 09:25:00', 1, '2026-01-31 09:25:00', 1, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 95, 211, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 94, 212, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 92, 213, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 93, 214, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 91, 215, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 90, 216, '2026-02-03 09:50:03', NULL, NULL, NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 83, 217, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 96, 218, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 97, 219, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 98, 220, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 99, 221, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 100, 222, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 101, 223, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 102, 224, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 103, 225, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 104, 226, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 105, 227, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 106, 228, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 107, 229, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 108, 230, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 109, 231, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 110, 232, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 111, 233, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 112, 234, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 113, 235, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 114, 236, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 115, 237, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 116, 238, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 117, 239, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 118, 240, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 119, 241, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);
INSERT INTO `role_permission` VALUES (1, 120, 242, '2026-02-03 11:40:54', 1, '2026-02-03 11:40:54', NULL, 1, NULL);


-- ----------------------------
-- Table structure for skill_execution_artifact
-- ----------------------------
DROP TABLE IF EXISTS `skill_execution_artifact`;
CREATE TABLE `skill_execution_artifact`  (
  `job_id` bigint NOT NULL,
  `kind` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'screenshots/artifacts',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '文件名',
  `relative_path` varchar(1200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '相对路径',
  `size` bigint NULL DEFAULT NULL COMMENT '大小',
  `content_type` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '类型（可选）',
  `is_deleted` tinyint(1) NULL DEFAULT NULL COMMENT '是否已删除',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_sea_job`(`job_id` ASC) USING BTREE,
  INDEX `idx_sea_job_kind`(`job_id` ASC, `kind` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Skill执行产物索引' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of skill_execution_artifact
-- ----------------------------


-- ----------------------------
-- Table structure for skill_execution_event
-- ----------------------------
DROP TABLE IF EXISTS `skill_execution_event`;
CREATE TABLE `skill_execution_event`  (
  `job_id` bigint NOT NULL,
  `seq` int NOT NULL COMMENT '事件序号（单job递增）',
  `level` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '级别',
  `message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '事件内容',
  `ts` datetime NULL DEFAULT NULL COMMENT '事件时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_see_job`(`job_id` ASC) USING BTREE,
  INDEX `idx_see_job_seq`(`job_id` ASC, `seq` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Skill执行事件流（日志）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of skill_execution_event
-- ----------------------------


-- ----------------------------
-- Table structure for skill_execution_job
-- ----------------------------
DROP TABLE IF EXISTS `skill_execution_job`;
CREATE TABLE `skill_execution_job`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `skill_id` bigint NOT NULL,
  `action_name` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '动作名（如 template/agent-browser-open）',
  `command` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '最终执行命令（runner执行）',
  `input_args` json NULL COMMENT '输入参数（表单/高级JSON合并后）',
  `session_id` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '会话ID（用于持久化浏览器/复用上下文）',
  `status` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '状态',
  `queued_at` datetime NULL DEFAULT NULL COMMENT '入队时间',
  `started_at` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `finished_at` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `return_code` int NULL DEFAULT NULL COMMENT '返回码',
  `stdout` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '标准输出（截断）',
  `stderr` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误输出（截断）',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '错误信息（非进程stderr）',
  `runtime_key` varchar(120) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'runtime目录key（用于产物路径）',
  `runner_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'runner类型 local/docker',
  `runner_meta` json NULL COMMENT 'runner元信息（镜像/容器id/节点等）',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_sej_project`(`project_id` ASC) USING BTREE,
  INDEX `idx_sej_skill`(`skill_id` ASC) USING BTREE,
  INDEX `idx_sej_status`(`status` ASC) USING BTREE,
  INDEX `idx_sej_user`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'Skill执行任务表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of skill_execution_job
-- ----------------------------


-- ----------------------------
-- Table structure for sys_code_sequence
-- ----------------------------
DROP TABLE IF EXISTS `sys_code_sequence`;
CREATE TABLE `sys_code_sequence`  (
  `business_type` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '业务类型',
  `prefix` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '前缀',
  `date_key` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '日期键（用于按日期重置）',
  `current_seq` int NULL DEFAULT NULL COMMENT '当前序号',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_business_prefix_date`(`business_type` ASC, `prefix` ASC, `date_key` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci COMMENT = '编码序号表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_code_sequence
-- ----------------------------
INSERT INTO `sys_code_sequence` VALUES ('2', 'test_contract', 'CONTRACT', 202602, 1, '2026-02-05 11:02:50', NULL, '2026-02-05 11:02:50', NULL, 1, NULL);
INSERT INTO `sys_code_sequence` VALUES ('1', 'test_order_seq', 'ORDER', 20260205, 3, '2026-02-05 11:02:48', NULL, '2026-02-05 11:02:49', NULL, 1, NULL);


-- ----------------------------
-- Table structure for sys_dept
-- ----------------------------
DROP TABLE IF EXISTS `sys_dept`;
CREATE TABLE `sys_dept`  (
  `dept_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '部门名称',
  `dept_code` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '部门编码',
  `parent_id` int NULL DEFAULT NULL COMMENT '父部门ID（0表示顶级部门）',
  `ancestors` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '祖级列表（逗号分隔）',
  `leader_id` bigint NULL DEFAULT NULL COMMENT '负责人ID',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '联系电话',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '邮箱',
  `sort` int NULL DEFAULT NULL COMMENT '排序',
  `status` int NULL DEFAULT NULL COMMENT '状态（0:禁用 1:启用）',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '部门描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_sys_dept_dept_code`(`dept_code` ASC) USING BTREE,
  INDEX `ix_sys_dept_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '部门表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_dept
-- ----------------------------


-- ----------------------------
-- Table structure for sys_dict_type
-- ----------------------------
DROP TABLE IF EXISTS `sys_dict_type`;
CREATE TABLE `sys_dict_type`  (
  `dict_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '字典名称',
  `dict_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '字典类型',
  `status` int NULL DEFAULT NULL COMMENT '状态（0:禁用 1:启用）',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_sys_dict_type_dict_type`(`dict_type` ASC) USING BTREE,
  INDEX `ix_sys_dict_type_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '字典类型表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_dict_type
-- ----------------------------
INSERT INTO `sys_dict_type` VALUES ('通知配置', 'notification_config_type', 1, '通知配置', 1, '2026-04-09 13:47:14', 1, '2026-04-09 13:47:14', 1, 1, NULL, '2026-04-09 13:47:15', '2026-04-09 13:47:15');
INSERT INTO `sys_dict_type` VALUES ('环境分类', 'sys_env', 1, '环境分类，如开发环境、测试环境、生产环境等。', 2, '2026-04-09 12:38:49', 1, '2026-04-09 13:32:02', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 13:32:03');
INSERT INTO `sys_dict_type` VALUES ('性能测试数据文件类型', 'perf_file_type', 1, '文件类型，如：JMX/CSV/TXT/JSON等。', 3, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('性能测试文件状态', 'perf_file_status', 1, '数据文件引用状态，如：已引用、未引用', 4, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('按钮状态', 'sys_btn_status', 1, '开关状态，如：启用、禁用。', 5, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('性能测试用例执行状态', 'perf_case_status', 1, '用例执行状态，如：进行中、未开始等。', 6, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('性能测试数据文件分发状态', 'perf_file_distribute_type', 1, '数据文件分发状态，如：未分发、已共享、已分割等。', 7, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('压力机类型', 'perf_machine_type', 1, '压力机类型，如：单机、Master、Slave等。', 8, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('性能测试类型', 'perf_test_category', 1, '性能测试场景分类，如：基准测试、负载测试、压力测试等。', 9, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('线程组类型', 'perf_thread_group_type', 1, '压测场景子配置的线程组类型：ThreadGroup/SteppingThreadGroup/UltimateThreadGroup', 10, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_type` VALUES ('是否分布式', 'perf_is_distributed', 1, '是否分布式', 11, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');


-- ----------------------------
-- Table structure for sys_dict_data
-- ----------------------------
DROP TABLE IF EXISTS `sys_dict_data`;
CREATE TABLE `sys_dict_data`  (
  `dict_sort` int NULL DEFAULT NULL COMMENT '字典排序',
  `dict_label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '字典标签',
  `dict_value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '字典键值',
  `dict_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '字典类型',
  `css_class` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '样式属性（CSS类名）',
  `list_class` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '表格回显样式',
  `is_default` int NULL DEFAULT NULL COMMENT '是否默认（0:否 1:是）',
  `status` int NULL DEFAULT NULL COMMENT '状态（0:禁用 1:启用）',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_sys_dict_data_dict_type`(`dict_type` ASC) USING BTREE,
  INDEX `ix_sys_dict_data_id`(`id` ASC) USING BTREE,
  CONSTRAINT `sys_dict_data_ibfk_1` FOREIGN KEY (`dict_type`) REFERENCES `sys_dict_type` (`dict_type`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '字典数据表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_dict_data
-- ----------------------------
-- sys_env
INSERT INTO `sys_dict_data` VALUES (0, '开发环境', '1', 'sys_env', NULL, NULL, 0, 1, '', 6, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, '测试环境', '2', 'sys_env', NULL, NULL, 0, 1, '', 7, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '预发布环境', '3', 'sys_env', NULL, NULL, 0, 1, '', 8, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, '生产环境', '4', 'sys_env', NULL, NULL, 0, 1, '', 9, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (4, '性能环境', '5', 'sys_env', NULL, NULL, 0, 1, '', 10, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_file_type
INSERT INTO `sys_dict_data` VALUES (1, 'CSV', '1', 'perf_file_type', NULL, NULL, 0, 1, '', 11, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, 'XLS', '2', 'perf_file_type', NULL, NULL, 0, 1, '', 12, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, 'XLSX', '3', 'perf_file_type', NULL, NULL, 0, 1, '', 13, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (4, 'TXT', '4', 'perf_file_type', NULL, NULL, 0, 1, '', 14, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (5, 'YAML', '5', 'perf_file_type', NULL, NULL, 0, 1, '', 15, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (6, 'JSON', '6', 'perf_file_type', NULL, NULL, 0, 1, '', 16, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (7, 'JMX', '7', 'perf_file_type', NULL, NULL, 0, 1, '', 17, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (8, 'GZ',  '8', 'perf_file_type', NULL, NULL, 0, 1, '', 18, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (9, 'ZIP', '9', 'perf_file_type', NULL, NULL, 0, 1, '', 19, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_file_status
INSERT INTO `sys_dict_data` VALUES (0, '未引用', '0', 'perf_file_status', NULL, NULL, 0, 1, '', 20, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, '已引用', '1', 'perf_file_status', NULL, NULL, 0, 1, '', 21, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '已关联', '2', 'perf_file_status', NULL, NULL, 0, 1, '', 22, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, '使用中', '3', 'perf_file_status', NULL, NULL, 0, 1, '', 23, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- sys_btn_status
INSERT INTO `sys_dict_data` VALUES (0, '启用', '1', 'sys_btn_status', NULL, NULL, 0, 1, '', 23, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, '禁用', '0', 'sys_btn_status', NULL, NULL, 0, 1, '', 24, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_case_status
INSERT INTO `sys_dict_data` VALUES (0, '待联调', '0', 'perf_case_status', NULL, NULL, 0, 1, '', 25, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, '待开始', '1', 'perf_case_status', NULL, NULL, 0, 1, '', 26, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '运行中', '2', 'perf_case_status', NULL, NULL, 0, 1, '', 27, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, '已完成', '3', 'perf_case_status', NULL, NULL, 0, 1, '', 28, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (4, '已取消', '4', 'perf_case_status', NULL, NULL, 0, 1, '', 29, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (5, '失败', '5', 'perf_case_status', NULL, NULL, 0, 1, '', 30, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_file_distribute_type
INSERT INTO `sys_dict_data` VALUES (0, '未分发', '0', 'perf_file_distribute_type', NULL, NULL, 0, 1, '', 31, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, '已共享', '1', 'perf_file_distribute_type', NULL, NULL, 0, 1, '', 32, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '已分割', '2', 'perf_file_distribute_type', NULL, NULL, 0, 1, '', 33, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_machine_type
INSERT INTO `sys_dict_data` VALUES (1, 'Master', '1', 'perf_machine_type', NULL, NULL, 0, 1, '', 34, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, 'Slave', '2', 'perf_machine_type', NULL, NULL, 0, 1, '', 35, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, '单机', '3', 'perf_machine_type', NULL, NULL, 0, 1, '', 36, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_test_category
INSERT INTO `sys_dict_data` VALUES (1, '基准测试', '1', 'perf_test_category', NULL, NULL, 0, 1, '在低压力下，测试系统的性能基线。', 37, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '负载测试', '2', 'perf_test_category', NULL, NULL, 0, 1, '梯度增加负载，直到达到预定的性能指标。', 38, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, '压力测试', '3', 'perf_test_category', NULL, NULL, 0, 1, '施加正常或超出系统预期峰值的负载，检查系统在高并发压力下的性能表现。', 39, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (4, '尖峰测试', '4', 'perf_test_category', NULL, NULL, 0, 1, '短时间内突然施加远超正常水平的极端负载或高并发，测试系统的弹性恢复能力。。', 40, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (5, '稳定性测试', '5', 'perf_test_category', NULL, NULL, 0, 0, '通过模拟真实或预期的业务负载，让系统长时间运行。', 41, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (6, '业务造数', '6', 'perf_test_category', NULL, NULL, 0, 1, '基于业务接口进行批量造数，非常规压测任务。', 42, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- perf_thread_group_type
INSERT INTO `sys_dict_data` VALUES (0, 'SetUp', '0', 'perf_thread_group_type', NULL, NULL, 0, 1, 'JMeter SetupThreadGroup，用于前置处理逻辑。', 43, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, 'ThreadGroup', '1', 'perf_thread_group_type', NULL, NULL, 0, 1, 'JMeter ThreadGroup，固定线程数，常规并发测试。', 44, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, 'SteppingThreadGroup', '2', 'perf_thread_group_type', NULL, NULL, 0, 1, 'JMeter SteppingThreadGroup，按阶梯逐步增加并发线程数。', 45, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, 'UltimateThreadGroup', '3', 'perf_thread_group_type', NULL, NULL, 0, 1, 'JMeter UltimateThreadGroup，通过自定义阶段精细控制线程启停。', 46, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
-- is_distribute
INSERT INTO `sys_dict_data` VALUES (1, '是', '1', 'perf_is_distributed', NULL, NULL, 0, 1, '是', 47, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '否', '0', 'perf_is_distributed', NULL, NULL, 0, 1, '否', 48, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');


-- ----------------------------
-- Table structure for sys_file
-- ----------------------------
DROP TABLE IF EXISTS `sys_file`;
CREATE TABLE `sys_file`  (
  `file_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '存储的文件名',
  `original_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '原始文件名',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '文件路径',
  `file_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件访问URL',
  `file_size` int NOT NULL COMMENT '文件大小（字节）',
  `file_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件MIME类型',
  `file_ext` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件扩展名',
  `upload_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '上传类型（local/oss/database）',
  `storage_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '存储路径',
  `file_content` longblob NULL COMMENT '文件二进制内容（用于数据库存储模式，MEDIUMBLOB 级别）',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文件描述',
  `tags` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件标签',
  `download_count` int NOT NULL COMMENT '下载次数',
  `is_public` int NOT NULL COMMENT '是否公开（0:私有 1:公开）',
  `uploaded_by` int NOT NULL COMMENT '上传用户ID',
  `uploaded_at` datetime NOT NULL COMMENT '上传时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文件管理表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_file
-- ----------------------------


-- ----------------------------
-- Table structure for sys_llm_config
-- ----------------------------
DROP TABLE IF EXISTS `sys_llm_config`;
CREATE TABLE `sys_llm_config`  (
  `config_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '用户自定义的配置名称，如\'生产环境OpenAI\'、\'测试Claude配置\'',
  `name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '模型名称，如 gpt-4, claude-3-sonnet',
  `provider` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'LLM 提供商',
  `model_name` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '模型名称（兼容字段）',
  `api_key` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'API 密钥（本地模型如 Ollama 可为空）',
  `base_url` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'API 基础URL',
  `system_prompt` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '指导LLM行为的系统级提示词',
  `temperature` float NULL DEFAULT NULL COMMENT '温度参数',
  `max_tokens` int NULL DEFAULT NULL COMMENT '最大令牌数',
  `supports_vision` tinyint(1) NULL DEFAULT NULL COMMENT '模型是否支持图片/多模态输入（如GPT-4V、Qwen-VL等）',
  `context_limit` int NULL DEFAULT NULL COMMENT '模型最大上下文Token数（GPT-4o: 128000, Claude: 200000, Gemini: 1000000）',
  `is_default` tinyint(1) NULL DEFAULT NULL COMMENT '是否为默认配置',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci COMMENT = 'LLM 配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_llm_config
-- ----------------------------


-- ----------------------------
-- Table structure for sys_conversation
-- ----------------------------
DROP TABLE IF EXISTS `sys_conversation`;
CREATE TABLE `sys_conversation`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `session_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '会话ID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '对话标题',
  `llm_config_id` bigint NULL DEFAULT NULL COMMENT 'LLM配置ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `is_active` int NULL DEFAULT NULL COMMENT '是否活跃（1是 0否）',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_sys_conversation_session_id`(`session_id` ASC) USING BTREE,
  INDEX `llm_config_id`(`llm_config_id` ASC) USING BTREE,
  INDEX `ix_sys_conversation_user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `sys_conversation_ibfk_1` FOREIGN KEY (`llm_config_id`) REFERENCES `sys_llm_config` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 67 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI 对话表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_conversation
-- ----------------------------
INSERT INTO `sys_conversation` VALUES (1, 'b5bfb5d9-2b53-4b4c-b56d-fe555cb57bfc', '更新后的标题', NULL, 1, 1, '2026-02-05 14:48:58', 1, '2026-02-05 14:49:05', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (2, '3bfda608-85b8-4828-9353-00eb049e21e9', '更新后的标题', NULL, 1, 1, '2026-02-05 14:49:42', 1, '2026-02-05 14:49:47', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (3, '61104b18-c6a0-47a6-a7fe-f430bd703f83', '用python写个冒泡排序', NULL, 1, 1, '2026-02-05 15:13:01', 1, '2026-02-05 15:15:47', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (4, '7cb3e0c0-0e7c-4254-b588-225e176ed509', '你是谁9', NULL, 1, 1, '2026-02-05 15:18:27', 1, '2026-02-05 16:15:09', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (5, '54013f33-19ad-46d2-98f0-b45eaa092b29', '新对话', NULL, 1, 1, '2026-02-05 15:31:44', 1, '2026-02-05 16:37:53', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (6, '94fd0319-1cbc-4fb6-990f-c7a3c16088d4', '你是谁', NULL, 1, 1, '2026-02-05 15:42:17', 1, '2026-02-05 16:37:48', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (7, '98df2a1f-2300-4d70-bfc5-ac11b7e43304', '新对话', NULL, 1, 1, '2026-02-05 15:47:06', 1, '2026-02-05 16:37:51', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (8, '927e8b99-62a5-4ab3-bcfe-7c3376331d7a', '你是谁', NULL, 1, 1, '2026-02-05 15:57:32', 1, '2026-02-05 16:18:14', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (9, '3e93745d-4386-4cca-83bb-d24a72754f6a', '新对话', NULL, 1, 1, '2026-02-05 16:12:20', 1, '2026-02-05 16:37:46', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (10, '9541b11b-9e9e-404d-827f-fe6b3fe2a892', '新对话', NULL, 1, 1, '2026-02-05 16:27:00', 1, '2026-02-05 16:37:43', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (11, 'd76f35ae-4b17-48ec-a697-9ed7e028dbbc', '新对话', NULL, 1, 1, '2026-02-05 16:36:41', 1, '2026-02-05 16:37:41', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (12, '3a659b23-0d5c-4c02-823c-ccb24cadfd17', '新对话', NULL, 1, 1, '2026-02-05 16:37:30', 1, '2026-02-05 16:37:38', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (13, 'afbdfbd6-90dc-4840-809b-fe62d13daf50', '新对话', NULL, 1, 1, '2026-02-05 16:37:57', 1, '2026-02-05 17:16:48', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (14, '93e174e7-d01c-4ffd-90ad-73e156066787', '新对话', NULL, 1, 1, '2026-02-05 16:40:23', 1, '2026-02-05 18:21:44', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (15, 'f37be5a6-1ead-4f25-a88a-7c7d32482413', '新对话', NULL, 1, 1, '2026-02-05 17:21:45', 1, '2026-02-05 18:21:47', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (16, 'ddf71dce-c5d0-4270-b8f5-f028e968022f', '新对话', NULL, 1, 1, '2026-02-05 17:32:47', 1, '2026-02-05 18:21:50', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (17, 'ea70d41d-1a6e-4445-a85c-c18d0e6b140e', '测试对话', NULL, 1, 1, '2026-02-05 18:07:53', 1, '2026-02-05 18:22:02', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (18, '66763110-9fb7-409d-8a56-abbdb5fdc7ba', '新对话', NULL, 1, 1, '2026-02-05 18:22:03', 1, '2026-03-03 14:12:48', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (19, '2adcbccc-0545-48e7-8228-cd85b4e3b682', '新对话', NULL, 1, 1, '2026-02-05 18:36:08', 1, '2026-03-03 14:12:42', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (20, 'b1ac79fe-fe96-4971-b7d3-fc3005f274a3', '新对话', NULL, 1, 1, '2026-02-25 17:27:59', 1, '2026-02-27 08:54:45', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (21, '8d02c788-50f7-40e4-a8c9-f856c78281f9', '新对话', NULL, 1, 1, '2026-03-02 11:04:19', 1, '2026-03-03 14:12:40', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (22, 'd783dd8d-7141-4201-a3cf-71169b1f80ee', '新对话', NULL, 1, 1, '2026-03-03 14:12:30', 1, '2026-03-03 14:12:37', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (23, '752f9c41-7736-40d4-9153-133fcfbd7d31', '新对话henaho de ', NULL, 1, 1, '2026-03-03 14:12:50', 1, '2026-03-03 14:13:01', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (24, '6c01aad0-22c0-40ae-a29b-64027ba59e3b', '新对话', NULL, 1, 1, '2026-03-08 13:47:27', 1, '2026-03-09 11:49:50', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (25, '0714ffc2-d5ac-40dc-a161-80afda070b35', '新对话', NULL, 1, 1, '2026-03-09 11:49:28', 1, '2026-03-09 11:49:48', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (26, '139b0010-a868-4a3c-b802-30768c3b002e', '新对话', NULL, 1, 1, '2026-03-09 11:49:36', 1, '2026-03-09 11:49:45', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (27, '1eb9c4a8-51dc-482c-a5d0-ea86b82c08ea', '新对话', NULL, 1, 1, '2026-03-09 11:49:52', 1, '2026-03-09 11:58:03', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (28, '158115e9-73cc-4502-afac-7e7699c2254a', '新对话', NULL, 1, 1, '2026-03-09 11:54:41', 1, '2026-03-09 11:58:08', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (29, 'b44b128f-5d62-4416-a972-b647ff2dab84', '新对话', NULL, 1, 1, '2026-03-09 11:58:10', 1, '2026-03-09 11:58:15', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (30, '5c79fbb2-ac9c-44ee-bd6e-ce01bfe4271c', '新对话', NULL, 1, 1, '2026-03-09 11:58:16', 1, '2026-03-10 17:06:49', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (31, '6b767e2e-7b30-4405-8207-2406c12eff19', '新对话', NULL, 1, 1, '2026-03-09 12:05:59', 1, '2026-03-09 19:15:05', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (32, '0cdeb081-3035-45ae-8575-1ff5167d6a4a', '新对话', NULL, 1, 1, '2026-03-09 12:10:35', 1, '2026-03-09 19:14:59', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (33, '4fc29093-19b8-428d-9990-03f0b6052157', '新对话', NULL, 1, 1, '2026-03-09 12:12:34', 1, '2026-03-09 19:14:56', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (34, '5cfc3dbe-9396-4b9c-aac9-395980160df4', '新对话', NULL, 1, 1, '2026-03-09 19:14:12', 1, '2026-03-09 19:14:53', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (35, 'b4654df9-5af7-4d2f-ada9-644709f9e4c0', '新对话', NULL, 1, 1, '2026-03-10 17:06:50', 1, '2026-03-23 08:56:54', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (36, '9c3e5201-866c-4256-8d9e-849df63af796', '新对话', NULL, 1, 1, '2026-03-10 17:32:37', 1, '2026-03-30 14:41:22', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (37, '6b898f47-fe02-4fd6-8b3c-824673919c45', '新对话', NULL, 1, 1, '2026-03-10 17:34:13', 1, '2026-03-30 14:41:19', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (38, 'b32c847b-0435-4bce-a02e-1e0b85658518', '新对话', NULL, 1, 1, '2026-04-01 10:17:06', 1, '2026-04-08 09:07:02', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (39, '51cc8024-e896-4958-bd44-844104884efe', '新对话', NULL, 1, 1, '2026-04-07 15:51:20', 1, '2026-04-08 09:06:59', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (40, 'e43072a9-5cce-47f8-97b8-0a539b0ef93c', '新对话', NULL, 1, 1, '2026-04-07 15:59:18', 1, '2026-04-08 09:06:57', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (41, '3bfd3bc7-bfe4-4eb8-9c06-8290e11dc833', '新对话', NULL, 1, 1, '2026-04-07 16:02:36', 1, '2026-04-08 09:06:53', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (42, '29fce366-983f-429e-b691-7bbc064389aa', '新对话', NULL, 1, 1, '2026-04-07 16:22:46', 1, '2026-04-08 09:06:49', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (43, 'ddd17830-4cb4-4070-a824-d22fbde05a7e', '新对话', NULL, 1, 1, '2026-04-08 09:07:05', 1, '2026-04-08 09:11:27', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (44, 'd71c0c4a-8fd2-4ea0-8cd5-4f170276e4de', '新对话', NULL, 1, 1, '2026-04-08 09:10:14', 1, '2026-04-08 09:11:25', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (45, '030ad0ea-78bb-48ae-acd7-091a565e966b', '新对话', NULL, 1, 1, '2026-04-09 17:18:04', 1, '2026-04-09 19:57:23', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (46, '0377433f-de0d-4054-95f5-5ee670677311', '打开百度首页，搜索查询深圳的天气，告诉我结果', NULL, 1, 1, '2026-04-09 19:50:32', 1, '2026-04-09 19:57:20', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (47, '121f65cc-8b4f-451c-be08-31c6988e2e2c', '打开百度', NULL, 1, 1, '2026-04-09 19:56:20', 1, '2026-04-09 19:57:18', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (48, '970b0b83-024f-4e16-917b-e6dc78374c28', '打开百度首页搜索你好', NULL, 1, 1, '2026-04-09 19:59:22', 1, '2026-04-10 11:27:08', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (49, '26309fdc-781c-4a9e-a2cd-bbab39b43d48', '打开百度页面', NULL, 1, 1, '2026-04-10 11:31:08', 1, '2026-04-10 16:57:13', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (50, '8bc99300-4e2f-4a4e-ad26-bc5764c141b0', '打开百度', NULL, 1, 1, '2026-04-10 14:02:27', 1, '2026-04-10 16:57:16', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (51, 'e0250f2f-2a24-4456-8129-a805c0f8383a', '新对话', NULL, 1, 1, '2026-04-10 15:32:40', 1, '2026-04-11 11:17:04', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (52, '56da4fb4-beb0-42db-b7b7-f0d05c0e9f40', '新对话', NULL, 1, 1, '2026-04-10 15:34:58', 1, '2026-04-10 16:57:19', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (53, 'ea427a7c-8b6f-4d43-8d17-c445dc2a8c3c', '新对话', NULL, 1, 1, '2026-04-10 16:11:22', 1, '2026-04-10 16:57:10', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (54, 'ee2c82e4-7785-4cb5-ae68-164fed6c0239', '新对话', NULL, 1, 1, '2026-04-10 16:50:39', 1, '2026-04-10 16:57:07', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (55, 'ce0f15b8-3758-4332-a087-81b817dd3ad4', '新对话', NULL, 1, 1, '2026-04-10 16:57:05', 1, '2026-04-11 11:16:58', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (56, 'aea96edb-8e93-4299-9313-85a2dd0c8e3e', '新对话', NULL, 1, 1, '2026-04-10 17:08:22', 1, '2026-04-11 11:16:48', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (57, '2a087476-a4dd-4d03-8d4c-2641d7d8e0ac', '新对话', NULL, 1, 1, '2026-04-10 17:08:22', 1, '2026-04-11 11:16:52', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (58, '64e23ee1-8734-4f0a-a730-cf1abd13ea74', '打开百度', NULL, 1, 1, '2026-04-10 17:45:41', 1, '2026-04-11 11:16:37', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (59, 'fa0d5d38-5967-496a-bde4-ad27039ab743', '打开地址http://47.113.104.130:9966...', NULL, 1, 1, '2026-04-10 17:49:27', 1, '2026-04-11 11:16:44', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (60, 'b1e0b165-2ffc-4a3a-b75c-abdf822babf2', '打开百度并截图', NULL, 1, 1, '2026-04-11 11:17:06', 1, '2026-04-13 16:53:07', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (61, '5d0c5011-5fa8-4f92-a834-ac886aa6cae9', '新对话', NULL, 1, 1, '2026-04-11 11:30:09', 1, '2026-04-13 16:53:12', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (62, 'd05ee643-3a17-459b-992a-c09cb30d5235', '新对话', NULL, 1, 1, '2026-04-11 11:30:09', 1, '2026-04-13 16:53:09', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (63, 'f206e9a5-94e6-4258-beaa-87d8e4ea8537', '新对话', NULL, 1, 1, '2026-04-14 11:56:23', 1, '2026-04-14 15:41:57', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (64, 'a131fec6-afc0-4b6e-a564-db90a419dc8f', '新对话', NULL, 1, 1, '2026-04-25 08:53:34', 1, '2026-04-25 08:55:01', 1, 0, NULL);
INSERT INTO `sys_conversation` VALUES (65, '6b1e77ab-ec24-4333-82e9-e618bcaa739f', '新对话', NULL, 1, 1, '2026-04-30 09:40:44', 1, '2026-04-30 09:40:44', 1, 1, NULL);
INSERT INTO `sys_conversation` VALUES (66, '037df627-1774-4cee-bbe4-2117d9a82604', '新对话', NULL, 1, 1, '2026-04-30 09:57:08', 1, '2026-04-30 09:57:08', 1, 1, NULL);


-- ----------------------------
-- Table structure for sys_login_log
-- ----------------------------
DROP TABLE IF EXISTS `sys_login_log`;
CREATE TABLE `sys_login_log`  (
  `user_id` bigint NULL DEFAULT NULL COMMENT '用户ID',
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名',
  `login_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '登录类型',
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '登录IP',
  `location` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '登录地点',
  `user_agent` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '用户代理',
  `browser` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '浏览器',
  `os` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作系统',
  `status` int NOT NULL COMMENT '登录状态（0:失败 1:成功）',
  `message` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '登录信息',
  `login_time` datetime NOT NULL COMMENT '登录时间',
  `logout_time` datetime NULL DEFAULT NULL COMMENT '退出时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '登录日志表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_login_log
-- ----------------------------


-- ----------------------------
-- Table structure for sys_mcp_execution_record
-- ----------------------------
DROP TABLE IF EXISTS `sys_mcp_execution_record`;
CREATE TABLE `sys_mcp_execution_record`  (
  `conversation_id` bigint NOT NULL COMMENT '对话ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `project_id` bigint NULL DEFAULT NULL COMMENT '项目ID',
  `knowledge_base_id` bigint NULL DEFAULT NULL COMMENT '知识库ID',
  `mcp_config_id` bigint NULL DEFAULT NULL COMMENT 'MCP配置ID',
  `phase` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '阶段 auto_plan/tool_call/forced_call',
  `tool_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '工具名',
  `tool_arguments` json NULL COMMENT '工具参数',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '状态 success/failed/skipped',
  `duration_ms` int NULL DEFAULT NULL COMMENT '耗时毫秒',
  `output_summary` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '输出摘要',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '错误信息',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_sys_mcp_execution_record_conversation_id`(`conversation_id` ASC) USING BTREE,
  INDEX `ix_sys_mcp_execution_record_mcp_config_id`(`mcp_config_id` ASC) USING BTREE,
  INDEX `ix_sys_mcp_execution_record_project_id`(`project_id` ASC) USING BTREE,
  INDEX `ix_sys_mcp_execution_record_user_id`(`user_id` ASC) USING BTREE,
  CONSTRAINT `sys_mcp_execution_record_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `sys_conversation` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'MCP 执行记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_mcp_execution_record
-- ----------------------------
INSERT INTO `sys_mcp_execution_record` VALUES (61, 1, 1, NULL, 1, 'forced_call', '打开百度，测试搜索场景', '{\"query\": \"打开百度，测试搜索场景\", \"attachments\": []}', 'failed', 1330, NULL, '工具不存在: 打开百度，测试搜索场景', 6, '2026-04-11 11:31:09', 1, '2026-04-11 11:31:09', 1, 1, NULL);


-- ----------------------------
-- Table structure for sys_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_menu`;
CREATE TABLE `sys_menu`  (
  `menu_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '菜单名称',
  `menu_type` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '菜单类型（M:目录 C:菜单 F:按钮）',
  `parent_id` int NULL DEFAULT NULL COMMENT '父菜单ID（0表示顶级）',
  `path` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '路由路径',
  `component` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '组件路径',
  `query` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '路由参数',
  `perms` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '权限标识',
  `icon` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '菜单图标',
  `order_num` int NULL DEFAULT NULL COMMENT '显示顺序',
  `visible` int NULL DEFAULT NULL COMMENT '菜单状态（0:隐藏 1:显示）',
  `status` int NULL DEFAULT NULL COMMENT '菜单状态（0:停用 1:正常）',
  `is_frame` int NULL DEFAULT NULL COMMENT '是否为外链（0:是 1:否）',
  `is_cache` int NULL DEFAULT NULL COMMENT '是否缓存（0:缓存 1:不缓存）',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_sys_menu_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4217 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '菜单表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_menu
-- ----------------------------
INSERT INTO `sys_menu` VALUES ('系统管理', 'M', 0, '/system', '', NULL, NULL, 'ele-BellFilled', 8, 1, 1, 1, 0, '系统管理目录', 1, '2026-01-31 18:24:44', NULL, '2026-03-06 13:35:29', 1, 1, NULL, '2026-01-31 18:24:44', '2026-03-06 13:35:29');
INSERT INTO `sys_menu` VALUES ('用户管理', 'C', 1, '/system/user', 'system/user/index', NULL, 'system:user:list', 'ele-User', 1, 1, 1, 1, 0, '用户管理菜单', 2, '2026-01-31 18:24:44', NULL, '2026-02-03 14:50:18', NULL, 1, NULL, '2026-01-31 18:24:44', '2026-01-31 18:24:44');
INSERT INTO `sys_menu` VALUES ('角色管理', 'C', 1, '/system/role', 'system/role/index', NULL, 'system:role:list', 'ele-UserFilled', 2, 1, 1, 1, 0, '角色管理菜单', 3, '2026-01-31 18:24:44', NULL, '2026-02-03 14:50:18', NULL, 1, NULL, '2026-01-31 18:24:44', '2026-01-31 18:24:44');
INSERT INTO `sys_menu` VALUES ('菜单管理', 'C', 1, '/system/menu', 'system/menu/index', NULL, 'system:menu:list', 'ele-Menu', 3, 1, 1, 1, 0, '菜单管理菜单', 4, '2026-01-31 18:24:44', NULL, '2026-02-03 14:39:47', NULL, 1, NULL, '2026-01-31 18:24:44', '2026-01-31 18:24:44');
INSERT INTO `sys_menu` VALUES ('部门管理', 'C', 1, '/system/dept', 'system/dept/index', NULL, 'system:dept:list', 'ele-CreditCard', 4, 1, 1, 1, 0, '部门管理菜单', 5, '2026-01-31 18:24:44', NULL, '2026-02-03 14:50:18', NULL, 1, NULL, '2026-01-31 18:24:44', '2026-01-31 18:24:44');
INSERT INTO `sys_menu` VALUES ('字典管理', 'C', 1, '/system/dic', 'system/dic/index', NULL, 'system:dict:list', 'ele-CreditCard', 5, 1, 1, 1, 0, '字典管理菜单', 6, '2026-01-31 18:24:44', NULL, '2026-02-03 14:50:18', NULL, 1, NULL, '2026-01-31 18:24:44', '2026-01-31 18:24:44');
INSERT INTO `sys_menu` VALUES ('控制台', 'C', 0, '/home', 'home/index', NULL, 'system:menu', 'ele-HomeFilled', 0, 1, 1, 1, 0, '首页', 7, '2026-01-31 18:24:44', NULL, '2026-04-24 11:32:24', 1, 1, NULL, '2026-01-31 18:24:44', '2026-04-24 11:32:25');
INSERT INTO `sys_menu` VALUES ('用户查询', 'F', 2, NULL, NULL, NULL, 'system:user:list', NULL, 1, 1, 1, 1, 0, '用户查询按钮', 8, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('用户新增', 'F', 2, NULL, NULL, NULL, 'system:user:add', NULL, 2, 1, 1, 1, 0, '用户新增按钮', 9, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('用户编辑', 'F', 2, NULL, NULL, NULL, 'system:user:edit', NULL, 3, 1, 1, 1, 0, '用户编辑按钮', 10, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('用户删除', 'F', 2, NULL, NULL, NULL, 'system:user:delete', NULL, 4, 1, 1, 1, 0, '用户删除按钮', 11, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('用户状态', 'F', 2, NULL, NULL, NULL, 'system:user:status', NULL, 5, 1, 1, 1, 0, '用户状态切换按钮', 12, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('重置密码', 'F', 2, NULL, NULL, NULL, 'system:user:reset-password', NULL, 6, 1, 1, 1, 0, '重置密码按钮', 13, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('角色查询', 'F', 3, NULL, NULL, NULL, 'system:role:list', NULL, 1, 1, 1, 1, 0, '角色查询按钮', 14, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('角色新增', 'F', 3, NULL, NULL, NULL, 'system:role:add', NULL, 2, 1, 1, 1, 0, '角色新增按钮', 15, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('角色编辑', 'F', 3, NULL, NULL, NULL, 'system:role:edit', NULL, 3, 1, 1, 1, 0, '角色编辑按钮', 16, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('角色删除', 'F', 3, NULL, NULL, NULL, 'system:role:delete', NULL, 4, 1, 1, 1, 0, '角色删除按钮', 17, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('分配权限', 'F', 3, NULL, NULL, NULL, 'system:role:menu', NULL, 5, 1, 1, 1, 0, '分配菜单权限按钮', 18, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('部门新增', 'F', 5, NULL, NULL, NULL, 'system:dept:add', NULL, 2, 1, 1, 1, 0, '部门新增按钮', 20, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('部门编辑', 'F', 5, NULL, NULL, NULL, 'system:dept:edit', NULL, 3, 1, 1, 1, 0, '部门编辑按钮', 21, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('部门删除', 'F', 5, NULL, NULL, NULL, 'system:dept:delete', NULL, 4, 1, 1, 1, 0, '部门删除按钮', 22, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('菜单查询', 'F', 4, NULL, NULL, NULL, 'system:menu:list', NULL, 1, 1, 1, 1, 0, '菜单查询按钮', 23, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('菜单新增', 'F', 4, NULL, NULL, NULL, 'system:menu:add', NULL, 2, 1, 1, 1, 0, '菜单新增按钮', 24, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('菜单编辑', 'F', 4, NULL, NULL, NULL, 'system:menu:edit', NULL, 3, 1, 1, 1, 0, '菜单编辑按钮', 25, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('菜单删除', 'F', 4, NULL, NULL, NULL, 'system:menu:delete', NULL, 4, 1, 1, 1, 0, '菜单删除按钮', 26, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('字典查询', 'F', 6, NULL, NULL, NULL, 'system:dict:list', NULL, 1, 1, 1, 1, 0, '字典查询按钮', 27, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('字典新增', 'F', 6, NULL, NULL, NULL, 'system:dict:add', NULL, 2, 1, 1, 1, 0, '字典新增按钮', 28, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('字典编辑', 'F', 6, NULL, NULL, NULL, 'system:dict:edit', NULL, 3, 1, 1, 1, 0, '字典编辑按钮', 29, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('字典删除', 'F', 6, NULL, NULL, NULL, 'system:dict:delete', NULL, 4, 1, 1, 1, 0, '字典删除按钮', 30, '2026-02-02 08:57:41', NULL, '2026-02-02 08:57:41', NULL, 1, NULL, '2026-02-02 08:57:41', '2026-02-02 08:57:41');
INSERT INTO `sys_menu` VALUES ('平台接口', 'C', 1, '/system/apiDoc', 'system/apiDoc/index', 'layout', NULL, 'ele-CreditCard', 50, 1, 1, 0, 1, '接口管理', 34, '2026-02-02 10:10:58', 1, '2026-04-28 15:33:01', 1, 1, NULL, '2026-02-02 10:10:59', '2026-04-28 15:33:01');
INSERT INTO `sys_menu` VALUES ('Swagger文档', 'C', 34, '/system/apiDoc/swagger', 'system/apiDoc/swagger', NULL, NULL, 'ele-ChatLineSquare', 1, 1, 1, 1, 1, NULL, 35, '2026-02-02 10:12:48', 1, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-02 10:12:48', '2026-02-02 15:32:05');
INSERT INTO `sys_menu` VALUES ('Redoc文档', 'C', 34, '/system/apiDoc/redoc', 'system/apiDoc/redoc', NULL, NULL, 'ele-CopyDocument', 2, 1, 1, 1, 1, NULL, 36, '2026-02-02 10:57:27', 1, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-02 10:57:28', '2026-02-02 15:33:15');
INSERT INTO `sys_menu` VALUES ('部门查询', 'F', 5, NULL, NULL, NULL, 'system:dept:query', NULL, 1, 1, 1, 1, 0, NULL, 44, '2026-02-02 13:51:59', 1, '2026-02-02 13:51:59', 1, 1, NULL, '2026-02-02 13:51:59', '2026-02-02 13:51:59');
INSERT INTO `sys_menu` VALUES ('启用禁用', 'F', 5, NULL, NULL, NULL, 'system:dept:disable', NULL, 5, 1, 1, 1, 0, NULL, 45, '2026-02-02 13:51:59', 1, '2026-02-02 13:51:59', 1, 1, NULL, '2026-02-02 13:51:59', '2026-02-02 13:51:59');
INSERT INTO `sys_menu` VALUES ('字典类型查询', 'F', 6, NULL, NULL, NULL, 'system:dict:type:query', NULL, 1, 1, 1, 1, 0, NULL, 46, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典类型新增', 'F', 6, NULL, NULL, NULL, 'system:dict:type:add', NULL, 2, 1, 1, 1, 0, NULL, 47, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典类型编辑', 'F', 6, NULL, NULL, NULL, 'system:dict:type:edit', NULL, 3, 1, 1, 1, 0, NULL, 48, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典类型删除', 'F', 6, NULL, NULL, NULL, 'system:dict:type:delete', NULL, 4, 1, 1, 1, 0, NULL, 49, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典数据查询', 'F', 6, NULL, NULL, NULL, 'system:dict:data:query', NULL, 5, 1, 1, 1, 0, NULL, 50, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典数据新增', 'F', 6, NULL, NULL, NULL, 'system:dict:data:add', NULL, 6, 1, 1, 1, 0, NULL, 51, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典数据编辑', 'F', 6, NULL, NULL, NULL, 'system:dict:data:edit', NULL, 7, 1, 1, 1, 0, NULL, 52, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('字典数据删除', 'F', 6, NULL, NULL, NULL, 'system:dict:data:delete', NULL, 8, 1, 1, 1, 0, NULL, 53, '2026-02-02 14:24:20', 1, '2026-02-02 14:24:20', 1, 1, NULL, '2026-02-02 14:24:20', '2026-02-02 14:24:20');
INSERT INTO `sys_menu` VALUES ('个人中心', 'C', 1, '/system/personal', 'system/personal/index', NULL, NULL, 'ele-Avatar', 6, 1, 1, 1, 0, NULL, 55, '2026-02-02 15:58:29', 1, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-02 15:58:29', '2026-02-02 15:58:51');
INSERT INTO `sys_menu` VALUES ('系统文件管理', 'C', 1, '/system/file', 'system/file/index', NULL, 'system:file:list', 'ele-FolderOpened', 10, 1, 1, 1, 0, '文件管理菜单', 58, '2026-02-02 17:04:03', 1, '2026-04-28 15:32:17', 1, 1, NULL, '2026-02-02 17:04:03', '2026-04-28 15:32:18');
INSERT INTO `sys_menu` VALUES ('文件查询', 'F', 58, '', '', '', 'system:file:query', '', 1, 1, 1, 1, 0, '文件查询按钮', 59, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('文件上传', 'F', 58, '', '', '', 'system:file:upload', '', 2, 1, 1, 1, 0, '文件上传按钮', 60, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('文件下载', 'F', 58, '', '', '', 'system:file:download', '', 3, 1, 1, 1, 0, '文件下载按钮', 61, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('文件编辑', 'F', 58, '', '', '', 'system:file:edit', '', 4, 1, 1, 1, 0, '文件编辑按钮', 62, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('文件删除', 'F', 58, '', '', '', 'system:file:delete', '', 5, 1, 1, 1, 0, '文件删除按钮', 63, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('批量删除', 'F', 58, '', '', '', 'system:file:batch:delete', '', 6, 1, 1, 1, 0, '批量删除按钮', 64, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('文件详情', 'F', 58, '', '', '', 'system:file:detail', '', 7, 1, 1, 1, 0, '文件详情按钮', 65, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('文件统计', 'F', 58, '', '', '', 'system:file:stats', '', 8, 1, 1, 1, 0, '文件统计按钮', 66, '2026-02-02 17:04:03', 1, '2026-02-02 17:04:03', 1, 1, NULL, '2026-02-02 17:04:03', '2026-02-02 17:04:03');
INSERT INTO `sys_menu` VALUES ('日志管理', 'M', 1, 'log', '', NULL, NULL, 'ele-Coin', 10, 1, 1, 1, 0, '日志管理目录', 67, '2026-02-02 21:08:02', NULL, '2026-04-28 15:32:32', 1, 1, NULL, '2026-02-02 21:08:02', '2026-04-28 15:32:33');
INSERT INTO `sys_menu` VALUES ('登录日志', 'C', 67, '/system/loginRecord', 'system/loginRecord/index', NULL, 'system:log:login:list', 'ele-Message', 1, 1, 1, 1, 0, '登录日志菜单', 68, '2026-02-02 21:08:03', NULL, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:33:38');
INSERT INTO `sys_menu` VALUES ('操作日志', 'C', 67, '/system/operationLog', 'system/operationLog/index', NULL, 'system:log:operation:list', 'ele-LocationFilled', 2, 1, 1, 1, 0, '操作日志菜单', 69, '2026-02-02 21:08:03', NULL, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:34:25');
INSERT INTO `sys_menu` VALUES ('登录日志查询', 'F', 68, '', '', NULL, 'system:log:login:query', '', 1, 1, 1, 1, 0, '登录日志查询按钮', 70, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('登录日志详情', 'F', 68, '', '', NULL, 'system:log:login:detail', '', 2, 1, 1, 1, 0, '登录日志详情按钮', 71, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('登录日志删除', 'F', 68, '', '', NULL, 'system:log:login:delete', '', 3, 1, 1, 1, 0, '登录日志删除按钮', 72, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('登录日志清理', 'F', 68, '', '', NULL, 'system:log:login:clean', '', 4, 1, 1, 1, 0, '登录日志清理按钮', 73, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('操作日志查询', 'F', 69, '', '', NULL, 'system:log:operation:query', '', 1, 1, 1, 1, 0, '操作日志查询按钮', 74, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('操作日志详情', 'F', 69, '', '', NULL, 'system:log:operation:detail', '', 2, 1, 1, 1, 0, '操作日志详情按钮', 75, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('操作日志删除', 'F', 69, '', '', NULL, 'system:log:operation:delete', '', 3, 1, 1, 1, 0, '操作日志删除按钮', 76, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('操作日志清理', 'F', 69, '', '', NULL, 'system:log:operation:clean', '', 4, 1, 1, 1, 0, '操作日志清理按钮', 77, '2026-02-02 21:08:03', NULL, '2026-02-02 21:08:03', NULL, 1, NULL, '2026-02-02 21:08:03', '2026-02-02 21:08:03');
INSERT INTO `sys_menu` VALUES ('系统监控', 'M', 1, 'monitor', '', NULL, NULL, 'ele-Platform', 11, 1, 1, 1, 0, '系统监控目录', 78, '2026-02-03 09:50:03', NULL, '2026-04-28 15:32:48', 1, 1, NULL, '2026-02-03 09:50:03', '2026-04-28 15:32:49');
INSERT INTO `sys_menu` VALUES ('服务器监控', 'C', 78, '/system/monitor/server', 'monitor/server/index', NULL, 'monitor:server:list', 'ele-Histogram', 1, 1, 1, 1, 0, '服务器监控菜单', 79, '2026-02-03 09:50:03', NULL, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-03 09:50:03', '2026-02-03 10:05:24');
INSERT INTO `sys_menu` VALUES ('在线用户', 'C', 78, '/system/monitor/online', 'monitor/online/index', NULL, 'monitor:online:list', 'ele-User', 2, 1, 1, 1, 0, '在线用户监控菜单', 80, '2026-02-03 09:50:03', NULL, '2026-02-03 14:50:18', 1, 1, NULL, '2026-02-03 09:50:03', '2026-02-03 10:14:54');
INSERT INTO `sys_menu` VALUES ('权限管理', 'C', 1, '/system/permission', 'system/permission/index', NULL, 'system:permission:list', 'ele-Key', 7, 1, 1, 1, 0, NULL, 81, '2026-02-03 11:57:13', 1, '2026-02-03 11:58:34', 1, 1, '6c0cda86-00b4-11f1-aceb-00ffed48fd0d', '2026-02-03 11:57:13', '2026-02-03 11:58:34');
INSERT INTO `sys_menu` VALUES ('新增权限', 'F', 81, NULL, NULL, NULL, 'system:permission:add', NULL, 1, 1, 1, 1, 0, NULL, 82, '2026-02-03 11:57:13', 1, '2026-02-03 11:57:13', 1, 1, '6c15fdcf-00b4-11f1-aceb-00ffed48fd0d', '2026-02-03 11:57:13', '2026-02-03 11:57:13');
INSERT INTO `sys_menu` VALUES ('编辑权限', 'F', 81, NULL, NULL, NULL, 'system:permission:edit', NULL, 2, 1, 1, 1, 0, NULL, 83, '2026-02-03 11:57:13', 1, '2026-02-03 11:57:13', 1, 1, '6c17ebf2-00b4-11f1-aceb-00ffed48fd0d', '2026-02-03 11:57:13', '2026-02-03 11:57:13');
INSERT INTO `sys_menu` VALUES ('删除权限', 'F', 81, NULL, NULL, NULL, 'system:permission:delete', NULL, 3, 1, 1, 1, 0, NULL, 84, '2026-02-03 11:57:13', 1, '2026-02-03 11:57:13', 1, 1, '6c1830bf-00b4-11f1-aceb-00ffed48fd0d', '2026-02-03 11:57:13', '2026-02-03 11:57:13');
INSERT INTO `sys_menu` VALUES ('查看权限', 'F', 81, NULL, NULL, NULL, 'system:permission:view', NULL, 4, 1, 1, 1, 0, NULL, 85, '2026-02-03 11:57:13', 1, '2026-02-03 11:57:13', 1, 1, '6c186d06-00b4-11f1-aceb-00ffed48fd0d', '2026-02-03 11:57:13', '2026-02-03 11:57:13');
INSERT INTO `sys_menu` VALUES ('AI 管理', 'M', 0, '/ai', 'Layout', NULL, NULL, 'ele-Comment', 0, 1, 1, 1, 0, 'AI 模块管理', 92, '2026-02-05 14:09:33', 1, '2026-03-19 15:20:07', 1, 1, NULL, '2026-02-05 14:09:33', '2026-03-19 15:20:07');
INSERT INTO `sys_menu` VALUES ('LLM 配置管理', 'C', 92, '/ai/llm-config', 'ai/llmConfig/index', NULL, 'ai:llm:view', 'ele-Connection', 2, 1, 1, 1, 0, 'LLM 配置管理菜单', 93, '2026-02-05 14:09:33', 1, '2026-02-05 15:07:29', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 15:07:29');
INSERT INTO `sys_menu` VALUES ('查询配置', 'F', 93, '', '', NULL, 'ai:llm:list', '#', 1, 1, 1, 1, 0, '查询 LLM 配置列表', 94, '2026-02-05 14:09:33', 1, '2026-02-05 14:09:33', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 14:09:33');
INSERT INTO `sys_menu` VALUES ('新增配置', 'F', 93, '', '', NULL, 'ai:llm:create', '#', 2, 1, 1, 1, 0, '新增 LLM 配置', 95, '2026-02-05 14:09:33', 1, '2026-02-05 14:09:33', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 14:09:33');
INSERT INTO `sys_menu` VALUES ('编辑配置', 'F', 93, '', '', NULL, 'ai:llm:update', '#', 3, 1, 1, 1, 0, '编辑 LLM 配置', 96, '2026-02-05 14:09:33', 1, '2026-02-05 14:09:33', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 14:09:33');
INSERT INTO `sys_menu` VALUES ('删除配置', 'F', 93, '', '', NULL, 'ai:llm:delete', '#', 4, 1, 1, 1, 0, '删除 LLM 配置', 97, '2026-02-05 14:09:33', 1, '2026-02-05 14:09:33', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 14:09:33');
INSERT INTO `sys_menu` VALUES ('设置默认', 'F', 93, '', '', NULL, 'ai:llm:setdefault', '#', 5, 1, 1, 1, 0, '设置默认 LLM 配置', 98, '2026-02-05 14:09:33', 1, '2026-02-05 14:09:33', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 14:09:33');
INSERT INTO `sys_menu` VALUES ('测试配置', 'F', 93, '', '', NULL, 'ai:llm:test', '#', 6, 1, 1, 1, 0, '测试 LLM 配置连接', 99, '2026-02-05 14:09:33', 1, '2026-02-05 14:09:33', 1, 1, NULL, '2026-02-05 14:09:33', '2026-02-05 14:09:33');
INSERT INTO `sys_menu` VALUES ('AI 聊天助手', 'C', 92, '/ai/chat', 'ai/chat/index', NULL, 'ai:chat:view', 'ele-ChatDotRound', 1, 1, 1, 1, 0, 'AI 聊天助手菜单', 105, '2026-02-05 15:08:58', 1, '2026-02-05 15:08:58', 1, 1, NULL, '2026-02-05 15:08:58', '2026-02-05 15:08:58');
INSERT INTO `sys_menu` VALUES ('创建对话', 'F', 105, '', '', NULL, 'ai:chat:create', '#', 1, 1, 1, 1, 0, '创建新对话', 106, '2026-02-05 15:08:58', 1, '2026-02-05 15:08:58', 1, 1, NULL, '2026-02-05 15:08:58', '2026-02-05 15:08:58');
INSERT INTO `sys_menu` VALUES ('发送消息', 'F', 105, '', '', NULL, 'ai:chat:send', '#', 2, 1, 1, 1, 0, '发送聊天消息', 107, '2026-02-05 15:08:58', 1, '2026-02-05 15:08:58', 1, 1, NULL, '2026-02-05 15:08:58', '2026-02-05 15:08:58');
INSERT INTO `sys_menu` VALUES ('更新对话', 'F', 105, '', '', NULL, 'ai:chat:update', '#', 3, 1, 1, 1, 0, '更新对话标题', 108, '2026-02-05 15:08:58', 1, '2026-02-05 15:08:58', 1, 1, NULL, '2026-02-05 15:08:58', '2026-02-05 15:08:58');
INSERT INTO `sys_menu` VALUES ('删除对话', 'F', 105, '', '', NULL, 'ai:chat:delete', '#', 4, 1, 1, 1, 0, '删除对话', 109, '2026-02-05 15:08:58', 1, '2026-02-05 15:08:58', 1, 1, NULL, '2026-02-05 15:08:58', '2026-02-05 15:08:58');
INSERT INTO `sys_menu` VALUES ('项目管理', 'M', 0, '/projects', 'Layout', NULL, NULL, 'ele-FolderOpened', 0, 1, 1, 1, 0, '项目管理目录', 110, '2026-02-06 12:42:28', 1, '2026-03-16 14:05:39', 1, 1, NULL, '2026-02-06 12:42:28', '2026-03-16 14:05:39');
INSERT INTO `sys_menu` VALUES ('项目列表', 'C', 110, '/projects/list', 'projects/list/index', NULL, 'projects:list:view', 'ele-List', 1, 1, 1, 1, 0, '项目列表页面', 111, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('查询项目', 'F', 111, '', '', NULL, 'projects:list:query', '#', 1, 1, 1, 1, 0, '查询项目列表', 112, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('新增项目', 'F', 111, '', '', NULL, 'projects:list:add', '#', 2, 1, 1, 1, 0, '创建新项目', 113, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('编辑项目', 'F', 111, '', '', NULL, 'projects:list:edit', '#', 3, 1, 1, 1, 0, '编辑项目信息', 114, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('删除项目', 'F', 111, '', '', NULL, 'projects:list:delete', '#', 4, 1, 1, 1, 0, '删除项目', 115, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('管理成员', 'F', 111, '', '', NULL, 'projects:member:manage', '#', 5, 1, 1, 1, 0, '管理项目成员', 116, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('管理环境', 'F', 111, '', '', NULL, 'projects:environment:manage', '#', 6, 1, 1, 1, 0, '管理项目环境', 117, '2026-02-06 12:42:28', 1, '2026-02-06 12:42:28', 1, 1, NULL, '2026-02-06 12:42:28', '2026-02-06 12:42:28');
INSERT INTO `sys_menu` VALUES ('测试管理', 'M', 0, '/testing', 'Layout', NULL, NULL, 'ele-Document', 3, 1, 1, 1, 0, '测试管理模块，包含测试用例和版本管理', 121, '2026-02-06 16:57:33', 1, '2026-04-23 14:26:04', 1, 1, NULL, '2026-02-06 16:57:33', '2026-04-23 14:26:05');
INSERT INTO `sys_menu` VALUES ('测试用例', 'C', 121, '/testing/testcases', 'testing/testcases/index', NULL, NULL, 'ele-Document', 10, 1, 1, 1, 0, '测试用例管理页面，支持用例创建、编辑、查询和步骤管理', 122, '2026-02-06 16:57:33', 1, '2026-02-06 17:13:51', 1, 1, NULL, '2026-02-06 16:57:33', '2026-02-06 17:13:52');
INSERT INTO `sys_menu` VALUES ('版本管理', 'C', 121, '/testing/versions', 'testing/versions/index', NULL, NULL, 'ele-FolderOpened', 20, 1, 1, 1, 0, '版本管理页面，支持版本创建、编辑和用例关联', 123, '2026-02-06 16:57:33', 1, '2026-02-06 17:14:05', 1, 1, NULL, '2026-02-06 16:57:33', '2026-02-06 17:14:06');
INSERT INTO `sys_menu` VALUES ('查询测试用例', 'F', 122, '', '', NULL, 'testcase:query', '#', 1, 0, 0, 1, 0, '查询测试用例按钮权限', 124, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('新增测试用例', 'F', 122, '', '', NULL, 'testcase:add', '#', 2, 0, 0, 1, 0, '新增测试用例按钮权限', 125, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('编辑测试用例', 'F', 122, '', '', NULL, 'testcase:edit', '#', 3, 0, 0, 1, 0, '编辑测试用例按钮权限', 126, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('删除测试用例', 'F', 122, '', '', NULL, 'testcase:delete', '#', 4, 0, 0, 1, 0, '删除测试用例按钮权限', 127, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('查看测试用例', 'F', 122, '', '', NULL, 'testcase:view', '#', 5, 0, 0, 1, 0, '查看测试用例详情按钮权限', 128, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('查询版本', 'F', 123, '', '', NULL, 'version:query', '#', 1, 0, 0, 1, 0, '查询版本按钮权限', 129, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('新增版本', 'F', 123, '', '', NULL, 'version:add', '#', 2, 0, 0, 1, 0, '新增版本按钮权限', 130, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('编辑版本', 'F', 123, '', '', NULL, 'version:edit', '#', 3, 0, 0, 1, 0, '编辑版本按钮权限', 131, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('删除版本', 'F', 123, '', '', NULL, 'version:delete', '#', 4, 0, 0, 1, 0, '删除版本按钮权限', 132, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('关联测试用例', 'F', 123, '', '', NULL, 'version:associate', '#', 5, 0, 0, 1, 0, '关联测试用例按钮权限', 133, '2026-02-06 17:11:07', 1, '2026-02-06 17:11:07', NULL, 1, NULL, '2026-02-06 17:11:07', '2026-02-06 17:11:07');
INSERT INTO `sys_menu` VALUES ('接口工具', 'C', 121, '/testing/api-testing', 'testing/api-testing/index', NULL, NULL, 'ele-Connection', 30, 1, 1, 1, 0, 'API测试管理页面，支持HTTP请求测试、环境管理、测试套件等功能', 134, '2026-02-07 09:57:07', 1, '2026-04-23 19:15:40', 1, 1, NULL, '2026-02-07 09:57:07', '2026-04-23 19:15:41');
INSERT INTO `sys_menu` VALUES ('查询API项目', 'F', 134, '', '', NULL, 'api_testing:project:query', '#', 1, 0, 0, 1, 0, '查询API项目列表按钮权限', 135, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('新增API项目', 'F', 134, '', '', NULL, 'api_testing:project:add', '#', 2, 0, 0, 1, 0, '新增API项目按钮权限', 136, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('编辑API项目', 'F', 134, '', '', NULL, 'api_testing:project:edit', '#', 3, 0, 0, 1, 0, '编辑API项目按钮权限', 137, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('删除API项目', 'F', 134, '', '', NULL, 'api_testing:project:delete', '#', 4, 0, 0, 1, 0, '删除API项目按钮权限', 138, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('导出API项目', 'F', 134, '', '', NULL, 'api_testing:project:export', '#', 5, 0, 0, 1, 0, '导出API项目按钮权限', 139, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('导入API项目', 'F', 134, '', '', NULL, 'api_testing:project:import', '#', 6, 0, 0, 1, 0, '导入API项目按钮权限', 140, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('查询API集合', 'F', 134, '', '', NULL, 'api_testing:collection:query', '#', 7, 0, 0, 1, 0, '查询API集合树按钮权限', 141, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('新增API集合', 'F', 134, '', '', NULL, 'api_testing:collection:add', '#', 8, 0, 0, 1, 0, '新增API集合按钮权限', 142, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('编辑API集合', 'F', 134, '', '', NULL, 'api_testing:collection:edit', '#', 9, 0, 0, 1, 0, '编辑API集合按钮权限', 143, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('删除API集合', 'F', 134, '', '', NULL, 'api_testing:collection:delete', '#', 10, 0, 0, 1, 0, '删除API集合按钮权限', 144, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('查询API请求', 'F', 134, '', '', NULL, 'api_testing:request:query', '#', 11, 0, 0, 1, 0, '查询API请求列表按钮权限', 145, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('新增API请求', 'F', 134, '', '', NULL, 'api_testing:request:add', '#', 12, 0, 0, 1, 0, '新增API请求按钮权限', 146, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('编辑API请求', 'F', 134, '', '', NULL, 'api_testing:request:edit', '#', 13, 0, 0, 1, 0, '编辑API请求按钮权限', 147, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('删除API请求', 'F', 134, '', '', NULL, 'api_testing:request:delete', '#', 14, 0, 0, 1, 0, '删除API请求按钮权限', 148, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('执行API请求', 'F', 134, '', '', NULL, 'api_testing:request:execute', '#', 15, 0, 0, 1, 0, '执行API请求按钮权限', 149, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('查看请求历史', 'F', 134, '', '', NULL, 'api_testing:request:history', '#', 16, 0, 0, 1, 0, '查看请求历史按钮权限', 150, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('查询环境变量', 'F', 134, '', '', NULL, 'api_testing:environment:query', '#', 17, 0, 0, 1, 0, '查询环境变量列表按钮权限', 151, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('新增环境变量', 'F', 134, '', '', NULL, 'api_testing:environment:add', '#', 18, 0, 0, 1, 0, '新增环境变量按钮权限', 152, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('编辑环境变量', 'F', 134, '', '', NULL, 'api_testing:environment:edit', '#', 19, 0, 0, 1, 0, '编辑环境变量按钮权限', 153, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('删除环境变量', 'F', 134, '', '', NULL, 'api_testing:environment:delete', '#', 20, 0, 0, 1, 0, '删除环境变量按钮权限', 154, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('激活环境变量', 'F', 134, '', '', NULL, 'api_testing:environment:activate', '#', 21, 0, 0, 1, 0, '激活环境变量按钮权限', 155, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('查询测试套件', 'F', 134, '', '', NULL, 'api_testing:suite:query', '#', 22, 0, 0, 1, 0, '查询测试套件列表按钮权限', 156, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('新增测试套件', 'F', 134, '', '', NULL, 'api_testing:suite:add', '#', 23, 0, 0, 1, 0, '新增测试套件按钮权限', 157, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('编辑测试套件', 'F', 134, '', '', NULL, 'api_testing:suite:edit', '#', 24, 0, 0, 1, 0, '编辑测试套件按钮权限', 158, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('删除测试套件', 'F', 134, '', '', NULL, 'api_testing:suite:delete', '#', 25, 0, 0, 1, 0, '删除测试套件按钮权限', 159, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('执行测试套件', 'F', 134, '', '', NULL, 'api_testing:suite:execute', '#', 26, 0, 0, 1, 0, '执行测试套件按钮权限', 160, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('查看执行历史', 'F', 134, '', '', NULL, 'api_testing:suite:history', '#', 27, 0, 0, 1, 0, '查看测试套件执行历史按钮权限', 161, '2026-02-07 09:57:07', 1, '2026-02-07 09:57:07', NULL, 1, NULL, '2026-02-07 09:57:07', '2026-02-07 09:57:07');
INSERT INTO `sys_menu` VALUES ('UI项目列表', 'C', 199, '/testing/ui-automation/index', 'testing/ui-automation/index', NULL, 'ui_automation:view', 'ele-Monitor', 30, 1, 1, 1, 0, NULL, 162, '2026-02-08 13:36:05', 1, '2026-03-30 19:52:05', 1, 1, NULL, '2026-02-08 13:36:05', '2026-03-06 16:18:04');
INSERT INTO `sys_menu` VALUES ('新建UI项目', 'F', 162, NULL, NULL, NULL, 'ui_automation:project:create', NULL, 1, 1, 1, 1, 0, NULL, 163, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('编辑UI项目', 'F', 162, NULL, NULL, NULL, 'ui_automation:project:edit', NULL, 2, 1, 1, 1, 0, NULL, 164, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('删除UI项目', 'F', 162, NULL, NULL, NULL, 'ui_automation:project:delete', NULL, 3, 1, 1, 1, 0, NULL, 165, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('生成项目代码', 'F', 162, NULL, NULL, NULL, 'ui_automation:project:generate_code', NULL, 4, 1, 1, 1, 0, NULL, 166, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('新建元素分组', 'F', 162, NULL, NULL, NULL, 'ui_automation:element_group:create', NULL, 5, 1, 1, 1, 0, NULL, 167, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('编辑元素分组', 'F', 162, NULL, NULL, NULL, 'ui_automation:element_group:edit', NULL, 6, 1, 1, 1, 0, NULL, 168, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('删除元素分组', 'F', 162, NULL, NULL, NULL, 'ui_automation:element_group:delete', NULL, 7, 1, 1, 1, 0, NULL, 169, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('新建UI元素', 'F', 162, NULL, NULL, NULL, 'ui_automation:element:create', NULL, 8, 1, 1, 1, 0, NULL, 170, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('编辑UI元素', 'F', 162, NULL, NULL, NULL, 'ui_automation:element:edit', NULL, 9, 1, 1, 1, 0, NULL, 171, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('删除UI元素', 'F', 162, NULL, NULL, NULL, 'ui_automation:element:delete', NULL, 10, 1, 1, 1, 0, NULL, 172, '2026-02-08 13:36:05', 1, '2026-02-08 13:36:05', NULL, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:36:05');
INSERT INTO `sys_menu` VALUES ('验证元素定位器', 'F', 162, '', '', NULL, 'ui_automation:element:validate', NULL, 11, 1, 1, 1, 0, NULL, 173, '2026-02-08 13:36:05', 1, '2026-02-08 13:38:20', 1, 1, NULL, '2026-02-08 13:36:05', '2026-02-08 13:38:21');
INSERT INTO `sys_menu` VALUES ('新建页面对象', 'F', 162, NULL, NULL, NULL, 'ui_automation:page_object:create', NULL, 12, 1, 1, 1, 0, NULL, 174, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('编辑页面对象', 'F', 162, NULL, NULL, NULL, 'ui_automation:page_object:edit', NULL, 13, 1, 1, 1, 0, NULL, 175, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('删除页面对象', 'F', 162, NULL, NULL, NULL, 'ui_automation:page_object:delete', NULL, 14, 1, 1, 1, 0, NULL, 176, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('管理页面对象元素', 'F', 162, '', '', NULL, 'ui_automation:page_object:manage_elements', NULL, 15, 1, 1, 1, 0, NULL, 177, '2026-02-08 13:36:06', 1, '2026-02-08 13:38:09', 1, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:38:10');
INSERT INTO `sys_menu` VALUES ('生成页面对象代码', 'F', 162, NULL, NULL, NULL, 'ui_automation:page_object:generate_code', NULL, 16, 1, 1, 1, 0, NULL, 178, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('预览页面对象代码', 'F', 162, NULL, NULL, NULL, 'ui_automation:page_object:preview_code', NULL, 17, 1, 1, 1, 0, NULL, 179, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('新建测试用例', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_case:create', NULL, 18, 1, 1, 1, 0, NULL, 180, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('编辑测试用例', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_case:edit', NULL, 19, 1, 1, 1, 0, NULL, 181, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('删除测试用例', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_case:delete', NULL, 20, 1, 1, 1, 0, NULL, 182, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('编辑测试步骤', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_case:edit_steps', NULL, 21, 1, 1, 1, 0, NULL, 183, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('执行测试用例', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_case:execute', NULL, 22, 1, 1, 1, 0, NULL, 184, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('生成测试用例代码', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_case:generate_code', NULL, 23, 1, 1, 1, 0, NULL, 185, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('新建测试套件', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_suite:create', NULL, 24, 1, 1, 1, 0, NULL, 186, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('编辑测试套件', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_suite:edit', NULL, 25, 1, 1, 1, 0, NULL, 187, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('删除测试套件', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_suite:delete', NULL, 26, 1, 1, 1, 0, NULL, 188, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('管理套件用例', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_suite:manage_cases', NULL, 27, 1, 1, 1, 0, NULL, 189, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('执行测试套件', 'F', 162, NULL, NULL, NULL, 'ui_automation:test_suite:execute', NULL, 28, 1, 1, 1, 0, NULL, 190, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('查看执行历史', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:view', NULL, 29, 1, 1, 1, 0, NULL, 191, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('查看执行详情', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:detail', NULL, 30, 1, 1, 1, 0, NULL, 192, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('查看执行日志', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:logs', NULL, 31, 1, 1, 1, 0, NULL, 193, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('停止执行', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:stop', NULL, 32, 1, 1, 1, 0, NULL, 194, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('删除执行记录', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:delete', NULL, 33, 1, 1, 1, 0, NULL, 195, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('导出执行报告', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:export', NULL, 34, 1, 1, 1, 0, NULL, 196, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('查看执行统计', 'F', 162, NULL, NULL, NULL, 'ui_automation:execution:statistics', NULL, 35, 1, 1, 1, 0, NULL, 197, '2026-02-08 13:36:06', 1, '2026-02-08 13:36:06', NULL, 1, NULL, '2026-02-08 13:36:06', '2026-02-08 13:36:06');
INSERT INTO `sys_menu` VALUES ('UI自动化管理', 'C', 199, '/testing/ui-automation/manage', 'testing/ui-automation/manage', NULL, 'ui_automation:manage', 'ele-HelpFilled', 31, 1, 1, 1, 0, NULL, 198, '2026-02-08 13:55:19', 1, '2026-03-30 19:52:05', 1, 1, NULL, '2026-02-08 13:55:19', '2026-02-08 14:26:55');
INSERT INTO `sys_menu` VALUES ('Selenium', 'M', 4208, '/testing/ui-automation', 'Layout', NULL, NULL, 'ele-ChromeFilled', 1, 1, 1, 1, 0, NULL, 199, '2026-02-08 14:11:44', 1, '2026-04-23 14:20:14', 1, 1, NULL, '2026-02-08 14:11:44', '2026-04-23 14:20:15');
INSERT INTO `sys_menu` VALUES ('测试报告', 'C', 199, '/testing/ui-automation/report', 'testing/ui-automation/report', NULL, 'ui_automation:report:view', 'ele-Document', 32, 1, 1, 1, 0, NULL, 200, '2026-02-24 15:09:25', 1, '2026-02-24 15:09:25', NULL, 1, NULL, '2026-02-24 15:09:25', '2026-02-24 15:09:25');
INSERT INTO `sys_menu` VALUES ('查看报告详情', 'F', 200, NULL, NULL, NULL, 'ui_automation:report:detail', NULL, 1, 1, 1, 1, 0, NULL, 201, '2026-02-24 15:09:25', 1, '2026-02-24 15:09:25', NULL, 1, NULL, '2026-02-24 15:09:25', '2026-02-24 15:09:25');
INSERT INTO `sys_menu` VALUES ('查看报告日志', 'F', 200, NULL, NULL, NULL, 'ui_automation:report:logs', NULL, 2, 1, 1, 1, 0, NULL, 202, '2026-02-24 15:09:25', 1, '2026-02-24 15:09:25', NULL, 1, NULL, '2026-02-24 15:09:25', '2026-02-24 15:09:25');
INSERT INTO `sys_menu` VALUES ('导出测试报告', 'F', 200, NULL, NULL, NULL, 'ui_automation:report:export', NULL, 3, 1, 1, 1, 0, NULL, 203, '2026-02-24 15:09:25', 1, '2026-02-24 15:09:25', NULL, 1, NULL, '2026-02-24 15:09:25', '2026-02-24 15:09:25');
INSERT INTO `sys_menu` VALUES ('查看报告统计', 'F', 200, NULL, NULL, NULL, 'ui_automation:report:statistics', NULL, 4, 1, 1, 1, 0, NULL, 204, '2026-02-24 15:09:25', 1, '2026-02-24 15:09:25', NULL, 1, NULL, '2026-02-24 15:09:25', '2026-02-24 15:09:25');
INSERT INTO `sys_menu` VALUES ('AI智能化', 'M', 121, '/ai/intelligence', 'ParentView', NULL, NULL, 'ele-Cpu', 3, 1, 1, 1, 0, 'AI智能化模块', 205, '2026-02-25 15:05:24', 1, '2026-04-23 14:20:42', 1, 1, NULL, '2026-02-25 15:05:24', '2026-04-23 14:20:42');
INSERT INTO `sys_menu` VALUES ('需求文档管理', 'C', 205, '/ai/intelligence/requirement-analysis', 'ai/intelligence/requirement-analysis/index', NULL, 'ai_intelligence:requirement:view', 'ele-Document', 1, 1, 1, 1, 0, '需求文档管理', 206, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', 1, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('AI模型配置', 'C', 205, '/ai/intelligence/model-config', 'ai/intelligence/model-config/index', NULL, 'ai_intelligence:model:view', 'ele-Connection', 2, 1, 1, 1, 0, 'AI模型配置管理', 207, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', 1, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('提示词配置', 'C', 205, '/ai/intelligence/prompt-config', 'ai/intelligence/prompt-config/index', NULL, 'ai_intelligence:prompt:view', 'ele-ChatDotRound', 3, 1, 1, 1, 0, '提示词配置管理', 208, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', 1, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('测试用例生成', 'C', 205, '/ai/intelligence/case-generation', 'ai/intelligence/case-generation/index', NULL, 'ai_intelligence:generation:view', 'ele-MagicStick', 4, 1, 1, 1, 0, '测试用例生成', 209, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', 1, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('上传需求文档', 'F', 206, NULL, NULL, NULL, 'ai_intelligence:requirement:upload', NULL, 1, 1, 1, 1, 0, NULL, 211, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('查看需求文档', 'F', 206, NULL, NULL, NULL, 'ai_intelligence:requirement:detail', NULL, 2, 1, 1, 1, 0, NULL, 212, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('更新需求文档', 'F', 206, NULL, NULL, NULL, 'ai_intelligence:requirement:update', NULL, 3, 1, 1, 1, 0, NULL, 213, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('删除需求文档', 'F', 206, NULL, NULL, NULL, 'ai_intelligence:requirement:delete', NULL, 4, 1, 1, 1, 0, NULL, 214, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('分析需求文档', 'F', 206, NULL, NULL, NULL, 'ai_intelligence:requirement:analyze', NULL, 5, 1, 1, 1, 0, NULL, 215, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('新增模型配置', 'F', 207, NULL, NULL, NULL, 'ai_intelligence:model:create', NULL, 1, 1, 1, 1, 0, NULL, 216, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('编辑模型配置', 'F', 207, NULL, NULL, NULL, 'ai_intelligence:model:update', NULL, 2, 1, 1, 1, 0, NULL, 217, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('删除模型配置', 'F', 207, NULL, NULL, NULL, 'ai_intelligence:model:delete', NULL, 3, 1, 1, 1, 0, NULL, 218, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('查看模型配置', 'F', 207, NULL, NULL, NULL, 'ai_intelligence:model:detail', NULL, 4, 1, 1, 1, 0, NULL, 219, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('测试模型连接', 'F', 207, NULL, NULL, NULL, 'ai_intelligence:model:test', NULL, 5, 1, 1, 1, 0, NULL, 220, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('新增提示词', 'F', 208, NULL, NULL, NULL, 'ai_intelligence:prompt:create', NULL, 1, 1, 1, 1, 0, NULL, 221, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('编辑提示词', 'F', 208, NULL, NULL, NULL, 'ai_intelligence:prompt:update', NULL, 2, 1, 1, 1, 0, NULL, 222, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('删除提示词', 'F', 208, NULL, NULL, NULL, 'ai_intelligence:prompt:delete', NULL, 3, 1, 1, 1, 0, NULL, 223, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('查看提示词', 'F', 208, NULL, NULL, NULL, 'ai_intelligence:prompt:detail', NULL, 4, 1, 1, 1, 0, NULL, 224, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('复制提示词', 'F', 208, NULL, NULL, NULL, 'ai_intelligence:prompt:copy', NULL, 5, 1, 1, 1, 0, NULL, 225, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('创建生成任务', 'F', 209, NULL, NULL, NULL, 'ai_intelligence:generation:create', NULL, 1, 1, 1, 1, 0, NULL, 226, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('查看生成任务', 'F', 209, NULL, NULL, NULL, 'ai_intelligence:generation:detail', NULL, 2, 1, 1, 1, 0, NULL, 227, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('查看生成结果', 'F', 209, NULL, NULL, NULL, 'ai_intelligence:generation:result', NULL, 3, 1, 1, 1, 0, NULL, 228, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('保存到用例库', 'F', 209, NULL, NULL, NULL, 'ai_intelligence:generation:save', NULL, 4, 1, 1, 1, 0, NULL, 229, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('导出测试用例', 'F', 209, NULL, NULL, NULL, 'ai_intelligence:generation:export', NULL, 5, 1, 1, 1, 0, NULL, 230, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('重新生成', 'F', 209, NULL, NULL, NULL, 'ai_intelligence:generation:regenerate', NULL, 6, 1, 1, 1, 0, NULL, 231, '2026-02-25 15:05:24', 1, '2026-02-25 15:05:24', NULL, 1, NULL, '2026-02-25 15:05:24', '2026-02-25 15:05:24');
INSERT INTO `sys_menu` VALUES ('AI用例生成历史', 'C', 205, '/ai/intelligence/generation-history', 'ai/intelligence/generation-history/index', NULL, 'ai_intelligence:history:view', 'ele-Clock', 6, 1, 1, 1, 0, 'AI用例生成历史记录', 243, '2026-02-25 19:58:35', 1, '2026-02-25 19:58:35', 1, 1, NULL, '2026-02-25 19:58:35', '2026-02-25 19:58:35');
INSERT INTO `sys_menu` VALUES ('查看历史记录', 'F', 243, NULL, NULL, NULL, 'ai_intelligence:history:view', NULL, 1, 1, 1, 1, 0, NULL, 244, '2026-02-25 19:58:35', 1, '2026-02-25 19:58:35', NULL, 1, NULL, '2026-02-25 19:58:35', '2026-02-25 19:58:35');
INSERT INTO `sys_menu` VALUES ('查看用例详情', 'F', 243, NULL, NULL, NULL, 'ai_intelligence:history:detail', NULL, 2, 1, 1, 1, 0, NULL, 245, '2026-02-25 19:58:35', 1, '2026-02-25 19:58:35', NULL, 1, NULL, '2026-02-25 19:58:35', '2026-02-25 19:58:35');
INSERT INTO `sys_menu` VALUES ('导出历史用例', 'F', 243, NULL, NULL, NULL, 'ai_intelligence:history:export', NULL, 3, 1, 1, 1, 0, NULL, 246, '2026-02-25 19:58:35', 1, '2026-02-25 19:58:35', NULL, 1, NULL, '2026-02-25 19:58:35', '2026-02-25 19:58:35');
INSERT INTO `sys_menu` VALUES ('删除历史记录', 'F', 243, NULL, NULL, NULL, 'ai_intelligence:history:delete', NULL, 4, 1, 1, 1, 0, NULL, 247, '2026-02-25 19:58:35', 1, '2026-02-25 19:58:35', NULL, 1, NULL, '2026-02-25 19:58:35', '2026-02-25 19:58:35');
INSERT INTO `sys_menu` VALUES ('模板管理', 'C', 205, '/ai/intelligence/template-management', 'ai/intelligence/template-management/index', NULL, 'ai_intelligence:template:view', 'ele-Document', 7, 1, 1, 1, 0, '测试用例模板管理', 248, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', 1, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('查看模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:view', NULL, 1, 1, 1, 1, 0, NULL, 249, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('新建模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:create', NULL, 2, 1, 1, 1, 0, NULL, 250, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('编辑模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:edit', NULL, 3, 1, 1, 1, 0, NULL, 251, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('删除模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:delete', NULL, 4, 1, 1, 1, 0, NULL, 252, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('导出模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:export', NULL, 5, 1, 1, 1, 0, NULL, 253, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('导入模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:import', NULL, 6, 1, 1, 1, 0, NULL, 254, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('预览模板', 'F', 248, NULL, NULL, NULL, 'ai_intelligence:template:preview', NULL, 7, 1, 1, 1, 0, NULL, 255, '2026-02-26 11:47:27', 1, '2026-02-26 11:47:27', NULL, 1, NULL, '2026-02-26 11:47:27', '2026-02-26 11:47:27');
INSERT INTO `sys_menu` VALUES ('模块管理', 'C', 121, '/testing/modules', 'testing/modules/index', NULL, 'testing:module:list', 'ele-FolderOpened', 15, 1, 1, 1, 0, '测试模块管理页面，支持模块创建、编辑、删除和用例归属管理', 256, '2026-02-26 14:27:12', 1, '2026-02-26 14:29:54', 1, 1, NULL, '2026-02-26 14:27:12', '2026-02-26 14:29:55');
INSERT INTO `sys_menu` VALUES ('查看模块', 'F', 256, '', '', NULL, 'testing:module:query', '', 1, 0, 0, 1, 0, '查看模块列表和详情', 257, '2026-02-26 14:27:12', 1, '2026-02-26 14:27:12', NULL, 1, NULL, '2026-02-26 14:27:12', '2026-02-26 14:27:12');
INSERT INTO `sys_menu` VALUES ('新增模块', 'F', 256, '', '', NULL, 'testing:module:add', '', 2, 0, 0, 1, 0, '创建新的测试模块', 258, '2026-02-26 14:27:12', 1, '2026-02-26 14:27:12', NULL, 1, NULL, '2026-02-26 14:27:12', '2026-02-26 14:27:12');
INSERT INTO `sys_menu` VALUES ('编辑模块', 'F', 256, '', '', NULL, 'testing:module:edit', '', 3, 0, 0, 1, 0, '编辑模块信息', 259, '2026-02-26 14:27:12', 1, '2026-02-26 14:27:12', NULL, 1, NULL, '2026-02-26 14:27:12', '2026-02-26 14:27:12');
INSERT INTO `sys_menu` VALUES ('删除模块', 'F', 256, '', '', NULL, 'testing:module:delete', '', 4, 0, 0, 1, 0, '删除测试模块（需要模块下无用例）', 260, '2026-02-26 14:27:12', 1, '2026-02-26 14:27:12', NULL, 1, NULL, '2026-02-26 14:27:12', '2026-02-26 14:27:12');
INSERT INTO `sys_menu` VALUES ('Figma配置', 'C', 92, '/ai/intelligence/figma-config', 'ai/intelligence/figma-config/index', NULL, NULL, 'ele-Connection', 4, 1, 1, 1, 1, NULL, 262, '2026-02-27 17:02:08', NULL, '2026-03-30 19:52:05', 1, 1, NULL, '2026-02-27 17:02:08', '2026-02-27 17:05:58');
INSERT INTO `sys_menu` VALUES ('AI用例管理', 'C', 263, '/ai/intelligence/browser-use/cases', 'ai/intelligence/browser-use/cases/index', NULL, 'ai_browser:case:view', 'ele-Document', 1, 1, 1, 1, 1, 'AI智能浏览器用例管理', 264, '2026-02-28 11:06:30', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('执行记录', 'C', 263, '/ai/intelligence/browser-use/executions', 'ai/intelligence/browser-use/executions/index', NULL, 'ai_browser:execution:view', 'ele-List', 2, 1, 1, 1, 1, 'AI智能浏览器执行记录', 265, '2026-02-28 11:06:30', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('执行统计', 'C', 263, '/ai/intelligence/browser-use/statistics', 'ai/intelligence/browser-use/statistics/index', NULL, 'ai_browser:statistics:view', 'ele-DataAnalysis', 3, 1, 1, 1, 1, 'AI智能浏览器执行统计', 266, '2026-02-28 11:06:30', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('AI测试报告', 'C', 263, '/ai/intelligence/browser-use/reports', 'ai/intelligence/browser-use/reports/index', NULL, 'ai_browser:report:view', 'ele-Document', 4, 1, 1, 1, 1, 'AI智能浏览器测试报告', 267, '2026-02-28 11:06:30', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查询用例', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:query', NULL, 1, 1, 1, 1, 0, NULL, 268, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('新增用例', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:add', NULL, 2, 1, 1, 1, 0, NULL, 269, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('编辑用例', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:edit', NULL, 3, 1, 1, 1, 0, NULL, 270, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('删除用例', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:delete', NULL, 4, 1, 1, 1, 0, NULL, 271, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('导入Excel', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:import', NULL, 5, 1, 1, 1, 0, NULL, 272, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('导出用例', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:export', NULL, 6, 1, 1, 1, 0, NULL, 273, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('执行用例', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:execute', NULL, 7, 1, 1, 1, 0, NULL, 274, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('批量执行', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:batch_execute', NULL, 8, 1, 1, 1, 0, NULL, 275, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('停止执行', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:stop', NULL, 9, 1, 1, 1, 0, NULL, 276, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 264, NULL, NULL, NULL, 'ai_browser:case:detail', NULL, 10, 1, 1, 1, 0, NULL, 277, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查询记录', 'F', 265, NULL, NULL, NULL, 'ai_browser:execution:query', NULL, 1, 1, 1, 1, 0, NULL, 278, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 265, NULL, NULL, NULL, 'ai_browser:execution:detail', NULL, 2, 1, 1, 1, 0, NULL, 279, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查看日志', 'F', 265, NULL, NULL, NULL, 'ai_browser:execution:log', NULL, 3, 1, 1, 1, 0, NULL, 280, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查看截图', 'F', 265, NULL, NULL, NULL, 'ai_browser:execution:screenshot', NULL, 4, 1, 1, 1, 0, NULL, 281, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('删除记录', 'F', 265, NULL, NULL, NULL, 'ai_browser:execution:delete', NULL, 5, 1, 1, 1, 0, NULL, 282, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('导出记录', 'F', 265, NULL, NULL, NULL, 'ai_browser:execution:export', NULL, 6, 1, 1, 1, 0, NULL, 283, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查询统计', 'F', 266, NULL, NULL, NULL, 'ai_browser:statistics:query', NULL, 1, 1, 1, 1, 0, NULL, 284, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('导出统计', 'F', 266, NULL, NULL, NULL, 'ai_browser:statistics:export', NULL, 2, 1, 1, 1, 0, NULL, 285, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('刷新统计', 'F', 266, NULL, NULL, NULL, 'ai_browser:statistics:refresh', NULL, 3, 1, 1, 1, 0, NULL, 286, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查询报告', 'F', 267, NULL, NULL, NULL, 'ai_browser:report:query', NULL, 1, 1, 1, 1, 0, NULL, 287, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('查看报告', 'F', 267, NULL, NULL, NULL, 'ai_browser:report:view', NULL, 2, 1, 1, 1, 0, NULL, 288, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('导出报告', 'F', 267, NULL, NULL, NULL, 'ai_browser:report:export', NULL, 3, 1, 1, 1, 0, NULL, 289, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('删除报告', 'F', 267, NULL, NULL, NULL, 'ai_browser:report:delete', NULL, 4, 1, 1, 1, 0, NULL, 290, '2026-02-28 11:06:30', 1, '2026-02-28 11:06:30', 1, 1, '0', '2026-02-28 11:06:30', '2026-02-28 11:06:30');
INSERT INTO `sys_menu` VALUES ('AI用例管理', 'C', 291, '/ai/intelligence/browser-use/cases', 'ai/intelligence/browser-use/cases/index', NULL, 'ai_browser:case:view', 'ele-Document', 1, 1, 1, 1, 1, 'AI智能浏览器用例管理', 292, '2026-02-28 11:27:57', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('执行记录', 'C', 291, '/ai/intelligence/browser-use/executions', 'ai/intelligence/browser-use/executions/index', NULL, 'ai_browser:execution:view', 'ele-List', 2, 1, 1, 1, 1, 'AI智能浏览器执行记录', 293, '2026-02-28 11:27:57', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('执行统计', 'C', 291, '/ai/intelligence/browser-use/statistics', 'ai/intelligence/browser-use/statistics/index', NULL, 'ai_browser:statistics:view', 'ele-DataAnalysis', 3, 1, 1, 1, 1, 'AI智能浏览器执行统计', 294, '2026-02-28 11:27:57', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('AI测试报告', 'C', 291, '/ai/intelligence/browser-use/reports', 'ai/intelligence/browser-use/reports/index', NULL, 'ai_browser:report:view', 'ele-Document', 4, 1, 1, 1, 1, 'AI智能浏览器测试报告', 295, '2026-02-28 11:27:57', 1, '2026-02-28 11:35:00', 1, 0, NULL, '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查询用例', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:query', NULL, 1, 1, 1, 1, 0, NULL, 296, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('新增用例', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:add', NULL, 2, 1, 1, 1, 0, NULL, 297, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('编辑用例', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:edit', NULL, 3, 1, 1, 1, 0, NULL, 298, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('删除用例', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:delete', NULL, 4, 1, 1, 1, 0, NULL, 299, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('导入Excel', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:import', NULL, 5, 1, 1, 1, 0, NULL, 300, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('导出用例', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:export', NULL, 6, 1, 1, 1, 0, NULL, 301, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('执行用例', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:execute', NULL, 7, 1, 1, 1, 0, NULL, 302, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('批量执行', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:batch_execute', NULL, 8, 1, 1, 1, 0, NULL, 303, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('停止执行', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:stop', NULL, 9, 1, 1, 1, 0, NULL, 304, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 292, NULL, NULL, NULL, 'ai_browser:case:detail', NULL, 10, 1, 1, 1, 0, NULL, 305, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查询记录', 'F', 293, NULL, NULL, NULL, 'ai_browser:execution:query', NULL, 1, 1, 1, 1, 0, NULL, 306, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 293, NULL, NULL, NULL, 'ai_browser:execution:detail', NULL, 2, 1, 1, 1, 0, NULL, 307, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查看日志', 'F', 293, NULL, NULL, NULL, 'ai_browser:execution:log', NULL, 3, 1, 1, 1, 0, NULL, 308, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查看截图', 'F', 293, NULL, NULL, NULL, 'ai_browser:execution:screenshot', NULL, 4, 1, 1, 1, 0, NULL, 309, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('删除记录', 'F', 293, NULL, NULL, NULL, 'ai_browser:execution:delete', NULL, 5, 1, 1, 1, 0, NULL, 310, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('导出记录', 'F', 293, NULL, NULL, NULL, 'ai_browser:execution:export', NULL, 6, 1, 1, 1, 0, NULL, 311, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查询统计', 'F', 294, NULL, NULL, NULL, 'ai_browser:statistics:query', NULL, 1, 1, 1, 1, 0, NULL, 312, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('导出统计', 'F', 294, NULL, NULL, NULL, 'ai_browser:statistics:export', NULL, 2, 1, 1, 1, 0, NULL, 313, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('刷新统计', 'F', 294, NULL, NULL, NULL, 'ai_browser:statistics:refresh', NULL, 3, 1, 1, 1, 0, NULL, 314, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查询报告', 'F', 295, NULL, NULL, NULL, 'ai_browser:report:query', NULL, 1, 1, 1, 1, 0, NULL, 315, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('查看报告', 'F', 295, NULL, NULL, NULL, 'ai_browser:report:view', NULL, 2, 1, 1, 1, 0, NULL, 316, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('导出报告', 'F', 295, NULL, NULL, NULL, 'ai_browser:report:export', NULL, 3, 1, 1, 1, 0, NULL, 317, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('删除报告', 'F', 295, NULL, NULL, NULL, 'ai_browser:report:delete', NULL, 4, 1, 1, 1, 0, NULL, 318, '2026-02-28 11:27:57', 1, '2026-02-28 11:27:57', 1, 1, '0', '2026-02-28 11:27:57', '2026-02-28 11:27:57');
INSERT INTO `sys_menu` VALUES ('AI浏览器', 'M', 121, '/ai/intelligence/browser-use', 'ParentView', NULL, NULL, 'ele-Monitor', 3, 1, 1, 1, 0, 'AI智能浏览器模块', 319, '2026-02-28 11:28:39', 1, '2026-04-23 14:20:59', 1, 1, NULL, '2026-02-28 11:28:39', '2026-04-23 14:20:59');
INSERT INTO `sys_menu` VALUES ('AI用例管理', 'C', 319, '/ai/intelligence/browser-use/cases', 'ai/intelligence/browser-use/cases/index', NULL, 'ai_browser:case:view', 'ele-Document', 1, 1, 1, 1, 1, 'AI智能浏览器用例管理', 320, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, NULL, '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('执行记录', 'C', 319, '/ai/intelligence/browser-use/executions', 'ai/intelligence/browser-use/executions/index', NULL, 'ai_browser:execution:view', 'ele-List', 2, 1, 1, 1, 1, 'AI智能浏览器执行记录', 321, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, NULL, '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('执行统计', 'C', 319, '/ai/intelligence/browser-use/statistics', 'ai/intelligence/browser-use/statistics/index', NULL, 'ai_browser:statistics:view', 'ele-DataAnalysis', 3, 1, 1, 1, 1, 'AI智能浏览器执行统计', 322, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, NULL, '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('AI测试报告', 'C', 319, '/ai/intelligence/browser-use/reports', 'ai/intelligence/browser-use/reports/index', NULL, 'ai_browser:report:view', 'ele-Document', 4, 1, 1, 1, 1, 'AI智能浏览器测试报告', 323, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, NULL, '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查询用例', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:query', NULL, 1, 1, 1, 1, 0, NULL, 324, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('新增用例', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:add', NULL, 2, 1, 1, 1, 0, NULL, 325, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('编辑用例', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:edit', NULL, 3, 1, 1, 1, 0, NULL, 326, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('删除用例', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:delete', NULL, 4, 1, 1, 1, 0, NULL, 327, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('导入Excel', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:import', NULL, 5, 1, 1, 1, 0, NULL, 328, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('导出用例', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:export', NULL, 6, 1, 1, 1, 0, NULL, 329, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('执行用例', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:execute', NULL, 7, 1, 1, 1, 0, NULL, 330, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('批量执行', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:batch_execute', NULL, 8, 1, 1, 1, 0, NULL, 331, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('停止执行', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:stop', NULL, 9, 1, 1, 1, 0, NULL, 332, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 320, NULL, NULL, NULL, 'ai_browser:case:detail', NULL, 10, 1, 1, 1, 0, NULL, 333, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查询记录', 'F', 321, NULL, NULL, NULL, 'ai_browser:execution:query', NULL, 1, 1, 1, 1, 0, NULL, 334, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 321, NULL, NULL, NULL, 'ai_browser:execution:detail', NULL, 2, 1, 1, 1, 0, NULL, 335, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查看日志', 'F', 321, NULL, NULL, NULL, 'ai_browser:execution:log', NULL, 3, 1, 1, 1, 0, NULL, 336, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查看截图', 'F', 321, NULL, NULL, NULL, 'ai_browser:execution:screenshot', NULL, 4, 1, 1, 1, 0, NULL, 337, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('删除记录', 'F', 321, NULL, NULL, NULL, 'ai_browser:execution:delete', NULL, 5, 1, 1, 1, 0, NULL, 338, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('导出记录', 'F', 321, NULL, NULL, NULL, 'ai_browser:execution:export', NULL, 6, 1, 1, 1, 0, NULL, 339, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查询统计', 'F', 322, NULL, NULL, NULL, 'ai_browser:statistics:query', NULL, 1, 1, 1, 1, 0, NULL, 340, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('导出统计', 'F', 322, NULL, NULL, NULL, 'ai_browser:statistics:export', NULL, 2, 1, 1, 1, 0, NULL, 341, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('刷新统计', 'F', 322, NULL, NULL, NULL, 'ai_browser:statistics:refresh', NULL, 3, 1, 1, 1, 0, NULL, 342, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查询报告', 'F', 323, NULL, NULL, NULL, 'ai_browser:report:query', NULL, 1, 1, 1, 1, 0, NULL, 343, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('查看报告', 'F', 323, NULL, NULL, NULL, 'ai_browser:report:view', NULL, 2, 1, 1, 1, 0, NULL, 344, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('导出报告', 'F', 323, NULL, NULL, NULL, 'ai_browser:report:export', NULL, 3, 1, 1, 1, 0, NULL, 345, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('删除报告', 'F', 323, NULL, NULL, NULL, 'ai_browser:report:delete', NULL, 4, 1, 1, 1, 0, NULL, 346, '2026-02-28 11:28:39', 1, '2026-02-28 11:28:39', 1, 1, '0', '2026-02-28 11:28:39', '2026-02-28 11:28:39');
INSERT INTO `sys_menu` VALUES ('AI测试套件', 'C', 319, '/ai/intelligence/test-suites', 'ai/intelligence/test-suites/index', NULL, 'ai_test_suite:view', 'ele-Collection', 5, 1, 1, 1, 1, 'AI测试套件管理', 357, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, NULL, '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('查询套件', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:query', NULL, 1, 1, 1, 1, 0, NULL, 358, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('新增套件', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:add', NULL, 2, 1, 1, 1, 0, NULL, 359, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('编辑套件', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:edit', NULL, 3, 1, 1, 1, 0, NULL, 360, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('删除套件', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:delete', NULL, 4, 1, 1, 1, 0, NULL, 361, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('执行套件', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:execute', NULL, 5, 1, 1, 1, 0, NULL, 362, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('查看详情', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:detail', NULL, 6, 1, 1, 1, 0, NULL, 363, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('执行记录', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:execution_list', NULL, 7, 1, 1, 1, 0, NULL, 364, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('执行监控', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:execution_monitor', NULL, 8, 1, 1, 1, 0, NULL, 365, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('导出套件', 'F', 357, NULL, NULL, NULL, 'ai_test_suite:export', NULL, 9, 1, 1, 1, 0, NULL, 366, '2026-03-01 17:02:01', 1, '2026-03-01 17:02:01', 1, 1, '0', '2026-03-01 17:02:01', '2026-03-01 17:02:01');
INSERT INTO `sys_menu` VALUES ('数据工厂', 'M', 0, '/data-factory', 'Layout', NULL, NULL, 'ele-DataAnalysis', 5, 1, 1, 1, 0, '数据工厂主菜单', 2001, '2026-03-03 16:43:23', 1, '2026-03-04 11:28:58', 1, 1, '09ee327f-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-04 11:28:58');
INSERT INTO `sys_menu` VALUES ('工具箱', 'C', 2001, '/data-factory/tools', 'testing/data-factory/tools/index', '', 'data_factory:tools:view', 'ele-Tools', 1, 1, 1, 1, 1, '数据工厂工具箱', 2002, '2026-03-03 16:43:23', 1, '2026-03-30 19:52:05', 1, 1, '09f31a00-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('使用记录', 'C', 2001, '/data-factory/records', 'testing/data-factory/records/index', '', 'data_factory:records:view', 'ele-List', 2, 1, 1, 1, 1, '数据工厂使用记录', 2003, '2026-03-03 16:43:23', 1, '2026-03-30 19:52:05', 1, 1, '09fdf021-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('统计分析', 'C', 2001, '/data-factory/statistics', 'testing/data-factory/statistics/index', '', 'data_factory:statistics:view', 'ele-PieChart', 3, 1, 1, 1, 1, '数据工厂统计分析', 2004, '2026-03-03 16:43:23', 1, '2026-03-30 19:52:05', 1, 1, '09fe08ae-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('获取工具分类', 'F', 2002, '', '', '', 'data_factory:tools:categories', '', 1, 1, 1, 1, 0, '获取工具分类权限', 2005, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09fe19a8-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('执行工具', 'F', 2002, '', '', '', 'data_factory:tools:execute', '', 2, 1, 1, 1, 0, '执行工具权限', 2006, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09fe1b6c-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('批量生成', 'F', 2002, '', '', '', 'data_factory:tools:batch', '', 3, 1, 1, 1, 0, '批量生成权限', 2007, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09fe1c36-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('查看记录', 'F', 2003, '', '', '', 'data_factory:records:list', '', 1, 1, 1, 1, 0, '查看记录权限', 2008, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09ff631f-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('删除记录', 'F', 2003, '', '', '', 'data_factory:records:delete', '', 2, 1, 1, 1, 0, '删除记录权限', 2009, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09ff65ee-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('导出记录', 'F', 2003, '', '', '', 'data_factory:records:export', '', 3, 1, 1, 1, 0, '导出记录权限', 2010, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09ff66aa-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('查看统计', 'F', 2004, '', '', '', 'data_factory:statistics:view', '', 1, 1, 1, 1, 0, '查看统计权限', 2011, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09ff96f0-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('获取标签', 'F', 2004, '', '', '', 'data_factory:statistics:tags', '', 2, 1, 1, 1, 0, '获取标签权限', 2012, '2026-03-03 16:43:23', 1, '2026-03-03 16:43:23', 1, 1, '09ff9c2c-16dd-11f1-a16b-00ffed48fd0d', '2026-03-03 16:43:23', '2026-03-03 16:43:23');
INSERT INTO `sys_menu` VALUES ('用例评审', 'M', 0, '/reviews', 'Layout', NULL, NULL, 'ele-Document', 4, 1, 1, 1, 0, '用例评审主菜单', 3001, '2026-03-04 11:26:29', 1, '2026-04-23 14:26:19', 1, 1, 'ef05daf7-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-04-23 14:26:19');
INSERT INTO `sys_menu` VALUES ('评审管理', 'C', 3001, '/reviews/index', 'reviews/index', '', 'reviews:manage:view', 'ele-List', 1, 1, 1, 1, 1, '评审管理页面', 3002, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef1023d0-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('评审模板', 'C', 3001, '/reviews/templates', 'reviews/templates', '', 'reviews:templates:view', 'ele-Setting', 2, 1, 1, 1, 1, '评审模板管理页面', 3003, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef10dbbb-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('评审统计', 'C', 3001, '/reviews/statistics', 'reviews/statistics', '', 'reviews:statistics:view', 'ele-DataAnalysis', 3, 1, 1, 1, 1, '评审统计分析页面', 3004, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef111683-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看评审', 'F', 3002, '', '', '', 'reviews:manage:list', '', 1, 1, 1, 1, 0, '查看评审列表权限', 3005, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef124763-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('创建评审', 'F', 3002, '', '', '', 'reviews:manage:create', '', 2, 1, 1, 1, 0, '创建评审权限', 3006, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef124d92-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('编辑评审', 'F', 3002, '', '', '', 'reviews:manage:edit', '', 3, 1, 1, 1, 0, '编辑评审权限', 3007, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef124f65-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('删除评审', 'F', 3002, '', '', '', 'reviews:manage:delete', '', 4, 1, 1, 1, 0, '删除评审权限', 3008, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef125025-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('分配评审人', 'F', 3002, '', '', '', 'reviews:manage:assign', '', 5, 1, 1, 1, 0, '分配评审人权限', 3009, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef1250da-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('提交评审', 'F', 3002, '', '', '', 'reviews:manage:submit', '', 6, 1, 1, 1, 0, '提交评审结果权限', 3010, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef1251ad-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看意见', 'F', 3002, '', '', '', 'reviews:comments:view', '', 7, 1, 1, 1, 0, '查看评审意见权限', 3011, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef127c9e-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('添加意见', 'F', 3002, '', '', '', 'reviews:comments:add', '', 8, 1, 1, 1, 0, '添加评审意见权限', 3012, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef128230-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('解决意见', 'F', 3002, '', '', '', 'reviews:comments:resolve', '', 9, 1, 1, 1, 0, '解决评审意见权限', 3013, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef128354-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看模板', 'F', 3003, '', '', '', 'reviews:templates:list', '', 1, 1, 1, 1, 0, '查看模板列表权限', 3014, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef12ca31-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('创建模板', 'F', 3003, '', '', '', 'reviews:templates:create', '', 2, 1, 1, 1, 0, '创建模板权限', 3015, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef12d0bc-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('编辑模板', 'F', 3003, '', '', '', 'reviews:templates:edit', '', 3, 1, 1, 1, 0, '编辑模板权限', 3016, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef12d1bb-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('删除模板', 'F', 3003, '', '', '', 'reviews:templates:delete', '', 4, 1, 1, 1, 0, '删除模板权限', 3017, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef12d274-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('启用/禁用模板', 'F', 3003, '', '', '', 'reviews:templates:toggle', '', 5, 1, 1, 1, 0, '启用/禁用模板权限', 3018, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef12d322-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看统计', 'F', 3004, '', '', '', 'reviews:statistics:view', '', 1, 1, 1, 1, 0, '查看评审统计权限', 3019, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef185aff-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('导出报告', 'F', 3004, '', '', '', 'reviews:statistics:export', '', 2, 1, 1, 1, 0, '导出统计报告权限', 3020, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef186231-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('我的任务', 'C', 3001, '/reviews/my-tasks', 'reviews/my-tasks', '', 'reviews:tasks:view', 'ele-User', 1, 1, 1, 1, 1, '我的评审任务页面', 3021, '2026-03-04 16:15:23', 1, '2026-03-30 19:52:05', 1, 1, '4b0f69fd-17a2-11f1-a16b-00ffed48fd0d', '2026-03-04 16:15:23', '2026-03-04 16:15:23');
INSERT INTO `sys_menu` VALUES ('评审执行', 'C', 3001, '/reviews/execute', 'reviews/execute', '', 'reviews:execute:view', 'ele-Edit', 5, 1, 1, 1, 1, '评审执行页面', 3025, '2026-04-01 11:21:47', 1, '2026-04-01 11:21:47', 1, 1, 'f58b1486-17b5-11f1-a16b-00ffed48fd0d', '2026-04-01 11:21:47', '2026-04-01 11:21:47');
INSERT INTO `sys_menu` VALUES ('评审结果', 'C', 3001, '/reviews/result', 'reviews/result', '', 'reviews:result:view', 'ele-View', 6, 1, 1, 1, 1, '评审结果页面', 3026, '2026-04-01 11:21:47', 1, '2026-04-01 11:21:47', 1, 1, 'f593d639-17b5-11f1-a16b-00ffed48fd0d', '2026-04-01 11:21:47', '2026-04-01 11:21:47');
INSERT INTO `sys_menu` VALUES ('执行评审', 'F', 3025, '', '', '', 'reviews:execute:perform', '', 1, 1, 1, 1, 0, '执行评审权限', 3027, '2026-03-04 18:36:10', 1, '2026-03-04 18:36:10', 1, 1, 'f5941b0a-17b5-11f1-a16b-00ffed48fd0d', '2026-03-04 18:36:10', '2026-03-04 18:36:10');
INSERT INTO `sys_menu` VALUES ('保存评审结果', 'F', 3025, '', '', '', 'reviews:execute:save', '', 2, 1, 1, 1, 0, '保存评审结果权限', 3028, '2026-03-04 18:36:10', 1, '2026-03-04 18:36:10', 1, 1, 'f59421f7-17b5-11f1-a16b-00ffed48fd0d', '2026-03-04 18:36:10', '2026-03-04 18:36:10');
INSERT INTO `sys_menu` VALUES ('提交评审', 'F', 3025, '', '', '', 'reviews:execute:submit', '', 3, 1, 1, 1, 0, '提交评审权限', 3029, '2026-03-04 18:36:10', 1, '2026-03-04 18:36:10', 1, 1, 'f59424bd-17b5-11f1-a16b-00ffed48fd0d', '2026-03-04 18:36:10', '2026-03-04 18:36:10');
INSERT INTO `sys_menu` VALUES ('查看用例详情', 'F', 3025, '', '', '', 'reviews:execute:case-detail', '', 4, 1, 1, 1, 0, '查看测试用例详情权限', 3030, '2026-03-04 18:36:10', 1, '2026-03-04 18:36:10', 1, 1, 'f59426f0-17b5-11f1-a16b-00ffed48fd0d', '2026-03-04 18:36:10', '2026-03-04 18:36:10');
INSERT INTO `sys_menu` VALUES ('查看结果', 'F', 3026, '', '', '', 'reviews:result:view', '', 1, 1, 1, 1, 0, '查看评审结果权限', 3031, '2026-03-04 18:36:10', 1, '2026-03-04 18:36:10', 1, 1, 'f595864c-17b5-11f1-a16b-00ffed48fd0d', '2026-03-04 18:36:10', '2026-03-04 18:36:10');
INSERT INTO `sys_menu` VALUES ('导出结果', 'F', 3026, '', '', '', 'reviews:result:export', '', 2, 1, 1, 1, 0, '导出评审结果权限', 3032, '2026-03-04 18:36:10', 1, '2026-03-04 18:36:10', 1, 1, 'f5958c69-17b5-11f1-a16b-00ffed48fd0d', '2026-03-04 18:36:10', '2026-03-04 18:36:10');
INSERT INTO `sys_menu` VALUES ('Dify助手', 'M', 121, '/assistant', 'Layout', NULL, NULL, 'ele-ChatDotRound', 3, 1, 1, 1, 0, 'AI助手主菜单', 4001, '2026-03-04 11:26:29', 1, '2026-04-23 14:24:36', 1, 1, 'ef356126-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-04-23 14:24:36');
INSERT INTO `sys_menu` VALUES ('助手管理', 'C', 4001, '/assistant/index', 'assistant/index', NULL, 'assistant:manage:view', 'ele-Basketball', 1, 1, 1, 1, 1, '助手管理页面', 4002, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef36e0a9-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 13:37:15');
INSERT INTO `sys_menu` VALUES ('配置管理', 'C', 4001, '/assistant/configs', 'assistant/configs', '', 'assistant:configs:view', 'ele-Setting', 2, 1, 1, 1, 1, '助手配置管理页面', 4003, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef36f0d8-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('对话管理', 'C', 4001, '/assistant/conversations', 'assistant/conversations', '', 'assistant:conversations:view', 'ele-ChatLineRound', 3, 1, 1, 1, 1, '对话管理页面', 4004, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef36fdec-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('助手统计', 'C', 4001, '/assistant/statistics', 'assistant/statistics', '', 'assistant:statistics:view', 'ele-DataAnalysis', 4, 1, 1, 1, 1, '助手统计分析页面', 4005, '2026-03-04 11:26:29', 1, '2026-03-30 19:52:05', 1, 1, 'ef370d9d-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('开始对话', 'F', 4002, '', '', '', 'assistant:manage:chat', '', 1, 1, 1, 1, 0, '开始对话权限', 4006, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37390d-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看助手', 'F', 4002, '', '', '', 'assistant:manage:list', '', 2, 1, 1, 1, 0, '查看助手列表权限', 4007, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef3740d4-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看配置', 'F', 4003, '', '', '', 'assistant:configs:list', '', 1, 1, 1, 1, 0, '查看配置列表权限', 4008, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37b0c7-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('创建配置', 'F', 4003, '', '', '', 'assistant:configs:create', '', 2, 1, 1, 1, 0, '创建配置权限', 4009, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37b5e8-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('编辑配置', 'F', 4003, '', '', '', 'assistant:configs:edit', '', 3, 1, 1, 1, 0, '编辑配置权限', 4010, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37b6b8-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('删除配置', 'F', 4003, '', '', '', 'assistant:configs:delete', '', 4, 1, 1, 1, 0, '删除配置权限', 4011, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37b796-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('启用/禁用配置', 'F', 4003, '', '', '', 'assistant:configs:toggle', '', 5, 1, 1, 1, 0, '启用/禁用配置权限', 4012, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37b833-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看对话', 'F', 4004, '', '', '', 'assistant:conversations:list', '', 1, 1, 1, 1, 0, '查看对话列表权限', 4013, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37d153-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('创建对话', 'F', 4004, '', '', '', 'assistant:conversations:create', '', 2, 1, 1, 1, 0, '创建对话权限', 4014, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37d39a-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('编辑对话', 'F', 4004, '', '', '', 'assistant:conversations:edit', '', 3, 1, 1, 1, 0, '编辑对话权限', 4015, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37d464-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('删除对话', 'F', 4004, '', '', '', 'assistant:conversations:delete', '', 4, 1, 1, 1, 0, '删除对话权限', 4016, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37d550-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('继续对话', 'F', 4004, '', '', '', 'assistant:conversations:continue', '', 5, 1, 1, 1, 0, '继续对话权限', 4017, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37d5ec-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看消息', 'F', 4004, '', '', '', 'assistant:messages:view', '', 6, 1, 1, 1, 0, '查看消息权限', 4018, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37eac6-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('发送消息', 'F', 4004, '', '', '', 'assistant:messages:send', '', 7, 1, 1, 1, 0, '发送消息权限', 4019, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37ed48-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('Dify聊天', 'F', 4004, '', '', '', 'assistant:chat:dify', '', 8, 1, 1, 1, 0, 'Dify聊天权限', 4020, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef37ee0d-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('查看统计', 'F', 4005, '', '', '', 'assistant:statistics:view', '', 1, 1, 1, 1, 0, '查看助手统计权限', 4021, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef380388-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('导出报告', 'F', 4005, '', '', '', 'assistant:statistics:export', '', 2, 1, 1, 1, 0, '导出统计报告权限', 4022, '2026-03-04 11:26:29', 1, '2026-03-04 11:26:29', 1, 1, 'ef380863-1779-11f1-a16b-00ffed48fd0d', '2026-03-04 11:26:29', '2026-03-04 11:26:29');
INSERT INTO `sys_menu` VALUES ('通知管理', 'M', 0, '/notifications', 'Layout', NULL, NULL, 'ele-Bell', 7, 1, 1, 1, 0, '统一通知系统管理', 4023, '2026-03-05 17:38:36', 1, '2026-03-06 13:35:08', 1, 1, NULL, '2026-03-05 17:38:36', '2026-03-06 13:35:08');
INSERT INTO `sys_menu` VALUES ('通知配置', 'C', 4023, '/notifications/configs', 'notifications/configs/index', NULL, 'notifications:config:list', 'ele-ChatLineSquare', 1, 1, 1, 1, 0, '通知配置管理', 4024, '2026-03-05 17:38:38', 1, '2026-03-30 19:52:05', 1, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 18:13:38');
INSERT INTO `sys_menu` VALUES ('通知历史', 'C', 4023, '/notifications/histories', 'notifications/histories/index', NULL, 'notifications:history:list', 'ele-Coffee', 2, 1, 1, 1, 0, '通知发送历史', 4025, '2026-03-05 17:38:38', 1, '2026-03-30 19:52:05', 1, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 18:15:17');
INSERT INTO `sys_menu` VALUES ('任务通知', 'C', 4023, '/notifications/task-settings', 'notifications/task-settings/index', NULL, 'notifications:task:list', 'ele-Collection', 3, 1, 1, 1, 0, '任务通知设置', 4026, '2026-03-05 17:38:38', 1, '2026-03-30 19:52:05', 1, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 18:15:53');
INSERT INTO `sys_menu` VALUES ('通知配置查询', 'F', 4024, '', '', NULL, 'notifications:config:query', '#', 1, 0, 0, 1, 0, '', 4027, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知配置新增', 'F', 4024, '', '', NULL, 'notifications:config:add', '#', 2, 0, 0, 1, 0, '', 4028, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知配置修改', 'F', 4024, '', '', NULL, 'notifications:config:edit', '#', 3, 0, 0, 1, 0, '', 4029, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知配置删除', 'F', 4024, '', '', NULL, 'notifications:config:remove', '#', 4, 0, 0, 1, 0, '', 4030, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知配置测试', 'F', 4024, '', '', NULL, 'notifications:config:test', '#', 5, 0, 0, 1, 0, '', 4031, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('设置默认配置', 'F', 4024, '', '', NULL, 'notifications:config:default', '#', 6, 0, 0, 1, 0, '', 4032, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知历史查询', 'F', 4025, '', '', NULL, 'notifications:history:query', '#', 1, 0, 0, 1, 0, '', 4033, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知历史详情', 'F', 4025, '', '', NULL, 'notifications:history:detail', '#', 2, 0, 0, 1, 0, '', 4034, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知重发', 'F', 4025, '', '', NULL, 'notifications:history:resend', '#', 3, 0, 0, 1, 0, '', 4035, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('任务通知查询', 'F', 4026, '', '', NULL, 'notifications:task:query', '#', 1, 0, 0, 1, 0, '', 4036, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('任务通知新增', 'F', 4026, '', '', NULL, 'notifications:task:add', '#', 2, 0, 0, 1, 0, '', 4037, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('任务通知修改', 'F', 4026, '', '', NULL, 'notifications:task:edit', '#', 3, 0, 0, 1, 0, '', 4038, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('任务通知删除', 'F', 4026, '', '', NULL, 'notifications:task:remove', '#', 4, 0, 0, 1, 0, '', 4039, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('发送通知', 'F', 4023, '', '', NULL, 'notifications:send', '#', 4, 0, 0, 1, 0, '发送通知权限', 4040, '2026-03-05 17:38:38', 1, '2026-03-05 17:38:38', NULL, 1, NULL, '2026-03-05 17:38:38', '2026-03-05 17:38:38');
INSERT INTO `sys_menu` VALUES ('通知历史删除', 'F', 4025, '', '', NULL, 'notifications:history:remove', '#', 4, 0, 0, 1, 0, '', 4077, '2026-03-06 08:39:38', 1, '2026-03-06 08:39:38', NULL, 1, NULL, '2026-03-06 08:39:38', '2026-03-06 08:39:38');
INSERT INTO `sys_menu` VALUES ('接口自动化', 'M', 0, '/api-automation', 'layout/routerView/parent', NULL, NULL, 'ele-Connection', 0, 1, 1, 1, 0, NULL, 4080, '2026-03-12 15:48:50', NULL, '2026-04-23 14:16:59', 1, 1, NULL, '2026-03-12 15:48:50', '2026-04-23 14:17:00');
INSERT INTO `sys_menu` VALUES ('接口中心', 'C', 4080, '/api-automation/index', 'testing/api-automation/index', NULL, NULL, 'ele-Connection', 1, 1, 1, 1, 0, NULL, 4081, '2026-03-12 15:48:50', NULL, '2026-04-23 14:16:40', 1, 1, NULL, '2026-03-12 15:48:50', '2026-04-23 14:16:41');
INSERT INTO `sys_menu` VALUES ('新增项目', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:project:add', NULL, 1, 0, 1, 1, 0, NULL, 4082, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('删除项目', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:project:delete', NULL, 2, 0, 1, 1, 0, NULL, 4083, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('新增服务', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:service:add', NULL, 3, 0, 1, 1, 0, NULL, 4084, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('删除服务', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:service:delete', NULL, 4, 0, 1, 1, 0, NULL, 4085, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('新建菜单节点', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:tree:add', NULL, 5, 0, 1, 1, 0, NULL, 4086, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('重命名菜单节点', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:tree:edit', NULL, 6, 0, 1, 1, 0, NULL, 4087, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('删除菜单节点', 'F', 4081, NULL, NULL, NULL, 'apiAutomation:tree:delete', NULL, 7, 0, 1, 1, 0, NULL, 4088, '2026-03-12 15:48:50', NULL, '2026-03-12 15:48:50', NULL, 1, NULL, '2026-03-12 15:48:50', '2026-03-12 15:48:50');
INSERT INTO `sys_menu` VALUES ('接口用例', 'C', 4080, '/api-automation/script', 'testing/api-automation/apiscript', NULL, NULL, 'ele-Coin', 2, 1, 1, 1, 0, NULL, 4090, '2026-03-12 16:16:06', NULL, '2026-04-23 19:39:43', 1, 1, NULL, '2026-03-12 16:16:06', '2026-04-23 19:39:43');
INSERT INTO `sys_menu` VALUES ('接口结果', 'C', 4080, '/api-automation/results', 'testing/api-automation/api_result_list', NULL, NULL, 'ele-Flag', 3, 1, 1, 1, 0, NULL, 4091, '2026-03-12 16:16:06', NULL, '2026-04-16 17:02:16', 1, 1, NULL, '2026-03-12 16:16:06', '2026-04-16 17:02:17');
INSERT INTO `sys_menu` VALUES ('任务管理', 'M', 0, '/task', 'layout/routerView/parent', NULL, NULL, 'ele-Calendar', 7, 1, 1, 1, 0, NULL, 4092, '2026-03-13 11:47:51', NULL, '2026-03-16 14:07:41', 1, 1, NULL, '2026-03-13 11:47:51', '2026-03-16 14:07:41');
INSERT INTO `sys_menu` VALUES ('定时任务', 'C', 4092, '/task/scheduler', 'testing/scheduler/index', NULL, NULL, 'ele-Timer', 1, 1, 1, 1, 0, NULL, 4093, '2026-03-13 11:47:51', NULL, '2026-03-13 11:47:51', NULL, 1, NULL, '2026-03-13 11:47:51', '2026-03-13 11:47:51');
INSERT INTO `sys_menu` VALUES ('新增任务', 'F', 4093, NULL, NULL, NULL, 'scheduler:task:add', NULL, 1, 0, 1, 1, 0, NULL, 4094, '2026-03-13 11:47:51', NULL, '2026-03-13 11:47:51', NULL, 1, NULL, '2026-03-13 11:47:51', '2026-03-13 11:47:51');
INSERT INTO `sys_menu` VALUES ('编辑任务', 'F', 4093, NULL, NULL, NULL, 'scheduler:task:edit', NULL, 2, 0, 1, 1, 0, NULL, 4095, '2026-03-13 11:47:51', NULL, '2026-03-13 11:47:51', NULL, 1, NULL, '2026-03-13 11:47:51', '2026-03-13 11:47:51');
INSERT INTO `sys_menu` VALUES ('删除任务', 'F', 4093, NULL, NULL, NULL, 'scheduler:task:delete', NULL, 3, 0, 1, 1, 0, NULL, 4096, '2026-03-13 11:47:51', NULL, '2026-03-13 11:47:51', NULL, 1, NULL, '2026-03-13 11:47:51', '2026-03-13 11:47:51');
INSERT INTO `sys_menu` VALUES ('Playwright', 'M', 4208, '/web-management', 'layout/routerView/parent', NULL, NULL, 'ele-ChromeFilled', 0, 1, 1, 1, 0, NULL, 4097, '2026-03-13 15:57:19', NULL, '2026-04-23 14:19:55', 1, 1, NULL, '2026-03-13 15:57:19', '2026-04-23 14:19:55');
INSERT INTO `sys_menu` VALUES ('元素管理', 'C', 4097, '/web/element', 'web_view/element_manager', NULL, NULL, 'ele-Grid', 1, 1, 1, 1, 0, NULL, 4098, '2026-03-13 15:57:19', NULL, '2026-04-16 19:40:09', 1, 1, NULL, '2026-03-13 15:57:19', '2026-04-16 19:40:09');
INSERT INTO `sys_menu` VALUES ('脚本管理', 'C', 4097, '/web/automation', 'web_view/web', NULL, NULL, 'ele-ChromeFilled', 2, 1, 1, 1, 0, NULL, 4099, '2026-03-13 15:57:19', NULL, '2026-04-16 19:41:09', 1, 1, NULL, '2026-03-13 15:57:19', '2026-04-16 19:41:10');
INSERT INTO `sys_menu` VALUES ('用例管理', 'C', 4097, '/web/group', 'web_view/web_group', NULL, NULL, 'ele-LocationInformation', 3, 1, 1, 1, 0, NULL, 4100, '2026-03-13 15:57:19', NULL, '2026-04-16 19:41:35', 1, 1, NULL, '2026-03-13 15:57:19', '2026-04-16 19:41:36');
INSERT INTO `sys_menu` VALUES ('测试结果', 'C', 4097, '/web/result', 'web_view/web_result_list', NULL, NULL, 'ele-Platform', 4, 1, 1, 1, 0, NULL, 4101, '2026-03-13 15:57:19', NULL, '2026-04-16 19:41:59', 1, 1, NULL, '2026-03-13 15:57:19', '2026-04-16 19:41:59');
INSERT INTO `sys_menu` VALUES ('元素查询', 'F', 4098, NULL, NULL, NULL, 'web:element:list', NULL, 1, 0, 1, 1, 0, NULL, 4102, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('元素新增', 'F', 4098, NULL, NULL, NULL, 'web:element:add', NULL, 2, 0, 1, 1, 0, NULL, 4103, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('元素编辑', 'F', 4098, NULL, NULL, NULL, 'web:element:edit', NULL, 3, 0, 1, 1, 0, NULL, 4104, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('元素删除', 'F', 4098, NULL, NULL, NULL, 'web:element:delete', NULL, 4, 0, 1, 1, 0, NULL, 4105, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('脚本查询', 'F', 4099, NULL, NULL, NULL, 'web:script:list', NULL, 1, 0, 1, 1, 0, NULL, 4106, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('脚本保存', 'F', 4099, NULL, NULL, NULL, 'web:script:save', NULL, 2, 0, 1, 1, 0, NULL, 4107, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('脚本执行', 'F', 4099, NULL, NULL, NULL, 'web:script:run', NULL, 3, 0, 1, 1, 0, NULL, 4108, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('场景查询', 'F', 4100, NULL, NULL, NULL, 'web:group:list', NULL, 1, 0, 1, 1, 0, NULL, 4109, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('场景新增', 'F', 4100, NULL, NULL, NULL, 'web:group:add', NULL, 2, 0, 1, 1, 0, NULL, 4110, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('场景编辑', 'F', 4100, NULL, NULL, NULL, 'web:group:edit', NULL, 3, 0, 1, 1, 0, NULL, 4111, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('场景删除', 'F', 4100, NULL, NULL, NULL, 'web:group:delete', NULL, 4, 0, 1, 1, 0, NULL, 4112, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('场景执行', 'F', 4100, NULL, NULL, NULL, 'web:group:run', NULL, 5, 0, 1, 1, 0, NULL, 4113, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('结果查询', 'F', 4101, NULL, NULL, NULL, 'web:result:list', NULL, 1, 0, 1, 1, 0, NULL, 4114, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('结果详情', 'F', 4101, NULL, NULL, NULL, 'web:result:detail', NULL, 2, 0, 1, 1, 0, NULL, 4115, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('结果报告', 'F', 4101, NULL, NULL, NULL, 'web:result:report', NULL, 3, 0, 1, 1, 0, NULL, 4116, '2026-03-13 15:57:19', NULL, '2026-03-13 15:57:19', NULL, 1, NULL, '2026-03-13 15:57:19', '2026-03-13 15:57:19');
INSERT INTO `sys_menu` VALUES ('报告', 'C', 4097, '/web/report', 'web_view/web_report', NULL, NULL, 'ele-Document', 5, 1, 1, 1, 0, NULL, 4117, '2026-03-14 17:12:14', NULL, '2026-04-16 19:42:15', 1, 1, NULL, '2026-03-14 17:12:14', '2026-04-16 19:42:16');
INSERT INTO `sys_menu` VALUES ('接口报告', 'C', 4080, '/api-automation/report', 'testing/api-automation/api_report', NULL, NULL, 'ele-Memo', 4, 1, 1, 1, 0, NULL, 4118, '2026-03-16 18:00:44', 1, '2026-03-17 12:28:25', 1, 1, NULL, '2026-03-16 18:00:45', '2026-03-17 12:28:26');
INSERT INTO `sys_menu` VALUES ('APP自动化', 'M', 0, '/app_manage', 'Layout', NULL, NULL, 'ele-Iphone', 2, 1, 1, 1, 0, NULL, 4128, '2026-03-19 15:08:39', NULL, '2026-04-23 14:25:42', 1, 1, NULL, '2026-03-19 15:08:39', '2026-04-23 14:25:42');
INSERT INTO `sys_menu` VALUES ('APP用例管理', 'C', 4128, '/app_manage/package', 'testing/app-management/case/index', NULL, NULL, 'ele-SetUp', 2, 1, 1, 1, 0, NULL, 4129, '2026-03-19 15:08:39', NULL, '2026-04-12 12:51:43', 1, 1, NULL, '2026-03-19 15:08:39', '2026-04-12 12:51:44');
INSERT INTO `sys_menu` VALUES ('APP页面管理', 'C', 4128, '/app_manage/automation', 'testing/app-management/page/index', NULL, NULL, 'ele-Iphone', 1, 1, 1, 1, 0, NULL, 4130, '2026-03-19 15:08:39', NULL, '2026-04-11 22:30:31', 1, 1, NULL, '2026-03-19 15:08:39', '2026-04-11 22:30:32');
INSERT INTO `sys_menu` VALUES ('APP测试报告', 'C', 4128, '/testing/app_report', 'testing/app-management/report/index.vue', NULL, NULL, 'ele-Document', 4, 1, 1, 1, 0, NULL, 4133, '2026-03-19 15:08:39', NULL, '2026-04-11 22:22:49', 1, 1, NULL, '2026-03-19 15:08:39', '2026-04-11 22:22:50');
INSERT INTO `sys_menu` VALUES ('知识库', 'C', 92, '/ai/knowledge', 'ai/knowledge/index', NULL, 'ai:platform:knowledge:view', 'ele-Collection', 10, 1, 1, 1, 0, '项目知识库', 4134, '2026-04-07 10:22:09', 1, '2026-04-07 10:22:09', 1, 1, NULL, '2026-04-07 10:22:09', '2026-04-07 10:22:09');
INSERT INTO `sys_menu` VALUES ('MCP 配置', 'C', 92, '/ai/mcp-config', 'ai/mcp-config/index', NULL, 'ai:platform:mcp:view', 'ele-Connection', 11, 1, 1, 1, 0, 'MCP 远程配置', 4135, '2026-04-07 10:22:09', 1, '2026-04-07 10:22:09', 1, 1, NULL, '2026-04-07 10:22:09', '2026-04-07 10:22:09');
INSERT INTO `sys_menu` VALUES ('API 密钥', 'C', 92, '/ai/api-keys', 'ai/api-keys/index', NULL, 'ai:platform:apikey:view', 'ele-Key', 12, 1, 1, 1, 0, '第三方 API 密钥', 4136, '2026-04-07 10:22:09', 1, '2026-04-07 10:22:09', 1, 1, NULL, '2026-04-07 10:22:09', '2026-04-07 10:22:09');
INSERT INTO `sys_menu` VALUES ('Skills管理', 'C', 92, '/ai/skills', 'ai/skills/index', NULL, NULL, 'ele-Money', 13, 1, 1, 1, 0, NULL, 4137, '2026-04-09 19:04:46', 1, '2026-04-09 19:04:46', 1, 1, NULL, '2026-04-09 19:04:46', '2026-04-09 19:04:46');
INSERT INTO `sys_menu` VALUES ('APP控制台', 'C', 4128, '/testing/app-management/index', 'testing/app-management/index', NULL, NULL, 'ele-Aim', 0, 1, 1, 1, 0, NULL, 4138, '2026-04-11 22:11:34', 1, '2026-04-11 22:29:53', 1, 1, NULL, '2026-04-11 22:11:34', '2026-04-11 22:29:54');
INSERT INTO `sys_menu` VALUES ('性能测试', 'M', 0, '/performance', 'Layout', NULL, NULL, 'ele-Odometer', 0, 1, 1, 1, 0, '性能测试模块', 4200, '2026-04-08 12:00:00', 1, '2026-04-14 15:38:56', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-14 15:38:56');
INSERT INTO `sys_menu` VALUES ('配置管理', 'C', 4200, '/performance/config', 'testing/performance/config/index', NULL, 'performance:config:list', 'ele-Setting', 1, 1, 1, 1, 0, '配置管理页面', 4201, '2026-04-08 12:00:00', 1, '2026-04-08 12:00:00', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-08 12:00:00');
INSERT INTO `sys_menu` VALUES ('造数管理', 'C', 4200, '/performance/data', 'testing/performance/data/index', NULL, 'performance:data:list', 'ele-DataAnalysis', 2, 1, 1, 1, 0, '造数管理页面', 4202, '2026-04-08 12:00:00', 1, '2026-04-08 12:00:00', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-08 12:00:00');
INSERT INTO `sys_menu` VALUES ('文件管理', 'C', 4200, '/performance/files', 'testing/performance/files/index', NULL, 'performance:file:list', 'ele-FolderOpened', 3, 1, 1, 1, 0, '文件管理页面', 4203, '2026-04-08 12:00:00', 1, '2026-04-08 12:00:00', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-08 12:00:00');
INSERT INTO `sys_menu` VALUES ('压测场景', 'C', 4200, '/performance/scenario', 'testing/performance/scenario/index', NULL, 'performance:scenario:list', 'ele-Cpu', 4, 1, 1, 1, 0, '压测场景页面', 4204, '2026-04-08 12:00:00', 1, '2026-04-08 12:00:00', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-08 12:00:00');
INSERT INTO `sys_menu` VALUES ('定时任务', 'C', 4200, '/performance/scheduler', 'testing/performance/scheduler/index', NULL, 'performance:scheduler:list', 'ele-Clock', 5, 1, 1, 1, 0, '定时任务页面', 4205, '2026-04-08 12:00:00', 1, '2026-04-08 12:00:00', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-08 12:00:00');
INSERT INTO `sys_menu` VALUES ('测试报告', 'C', 4200, '/performance/report', 'testing/performance/report/index', NULL, 'performance:report:list', 'ele-Document', 6, 1, 1, 1, 0, '测试报告页面', 4206, '2026-04-08 12:00:00', 1, '2026-04-08 12:00:00', 1, 1, NULL, '2026-04-08 12:00:00', '2026-04-08 12:00:00');
INSERT INTO `sys_menu` VALUES ('接口代码生成', 'C', 4080, '/api-automation/api_codegen', 'testing/api-automation/api_codegen', NULL, NULL, 'ele-Monitor', 5, 1, 1, 1, 0, NULL, 4207, '2026-04-15 10:45:53', 1, '2026-04-15 10:45:53', 1, 1, NULL, '2026-04-15 10:45:53', '2026-04-15 10:45:53');
INSERT INTO `sys_menu` VALUES ('UI自动化', 'M', 0, '/web', 'Layout', NULL, NULL, 'ele-ChromeFilled', 1, 1, 1, 1, 0, NULL, 4208, '2026-04-23 14:19:30', 1, '2026-04-23 14:29:05', 1, 1, NULL, '2026-04-23 14:19:30', '2026-04-23 14:29:06');
INSERT INTO `sys_menu` VALUES ('节点管理', 'C', 4210, '/testing/api-automation/workflow/', 'testing/api-automation/workflow/WorkflowEditor', NULL, NULL, 'ele-Menu', 6, 1, 1, 1, 0, NULL, 4209, '2026-04-23 14:45:14', 1, '2026-04-23 16:51:30', 1, 1, NULL, '2026-04-23 14:45:15', '2026-04-23 16:51:30');
INSERT INTO `sys_menu` VALUES ('工作流', 'M', 0, '/workflow', 'Layout', NULL, NULL, 'ele-Share', 2, 1, 1, 1, 0, NULL, 4210, '2026-04-23 16:50:17', 1, '2026-04-24 11:34:33', 1, 1, NULL, '2026-04-23 16:50:18', '2026-04-24 11:34:33');
INSERT INTO `sys_menu` VALUES ('客户端自动化', 'M', 4208, '/desktop', 'layout', NULL, NULL, 'ele-Platform', 10, 1, 1, 1, 0, NULL, 4211, '2026-04-30 11:07:44', 1, '2026-04-30 11:18:14', 1, 1, NULL, '2026-04-30 11:07:44', '2026-04-30 11:18:15');
INSERT INTO `sys_menu` VALUES ('小程序自动化', 'M', 4208, '/miniprogram', 'layout', NULL, NULL, 'ele-Avatar', 11, 1, 1, 1, 0, NULL, 4212, '2026-04-30 11:08:46', 1, '2026-04-30 11:18:30', 1, 1, NULL, '2026-04-30 11:08:46', '2026-04-30 11:18:31');
INSERT INTO `sys_menu` VALUES ('客户端脚本', 'C', 4211, '/testing/desktop-automation/index', 'testing/desktop-automation/index', NULL, NULL, 'ele-Platform', 0, 1, 1, 1, 0, NULL, 4213, '2026-04-30 11:15:08', 1, '2026-04-30 11:15:08', 1, 1, NULL, '2026-04-30 11:15:08', '2026-04-30 11:15:08');
INSERT INTO `sys_menu` VALUES ('客户端结果', 'C', 4211, '/testing/desktop-automation/results', 'testing/desktop-automation/results', NULL, NULL, 'ele-Platform', 1, 1, 1, 1, 0, NULL, 4214, '2026-04-30 11:15:56', 1, '2026-04-30 11:15:56', 1, 1, NULL, '2026-04-30 11:15:56', '2026-04-30 11:15:56');
INSERT INTO `sys_menu` VALUES ('小程序脚本', 'C', 4212, '/testing/miniprogram-automation/index', 'testing/miniprogram-automation/index', NULL, NULL, 'ele-Avatar', 0, 1, 1, 1, 0, NULL, 4215, '2026-04-30 11:17:06', 1, '2026-04-30 11:17:06', 1, 1, NULL, '2026-04-30 11:17:07', '2026-04-30 11:17:07');
INSERT INTO `sys_menu` VALUES ('小程序结果', 'C', 4212, '/testing/miniprogram-automation/results', 'testing/miniprogram-automation/results', NULL, NULL, 'ele-Avatar', 0, 1, 1, 1, 0, NULL, 4216, '2026-04-30 11:18:01', 1, '2026-04-30 11:18:01', 1, 1, NULL, '2026-04-30 11:18:01', '2026-04-30 11:18:01');


-- ----------------------------
-- Table structure for sys_message
-- ----------------------------
DROP TABLE IF EXISTS `sys_message`;
CREATE TABLE `sys_message`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `conversation_id` bigint NOT NULL COMMENT '对话ID',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色（system/user/assistant）',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '消息内容',
  `message_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '消息类型',
  `metadata` json NULL COMMENT '元数据',
  `tokens_used` int NULL DEFAULT NULL COMMENT '使用的令牌数',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_sys_message_conversation_id`(`conversation_id` ASC) USING BTREE,
  CONSTRAINT `sys_message_ibfk_1` FOREIGN KEY (`conversation_id`) REFERENCES `sys_conversation` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 293 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'AI 消息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_message
-- ----------------------------
INSERT INTO `sys_message` VALUES (1, 1, 'user', '你好，请用一句话介绍你自己。', 'text', 'null', NULL, '2026-02-05 14:49:00', 1, '2026-02-05 14:49:00', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (2, 1, 'assistant', '你好！我是一个由阿里云研发的超大规模语言模型，能够回答问题、创作文字、编程等，致力于为你提供准确、有用和友好的帮助。', 'text', 'null', 50, '2026-02-05 14:49:03', 1, '2026-02-05 14:49:03', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (3, 2, 'user', '你好，请用一句话介绍你自己。', 'text', 'null', NULL, '2026-02-05 14:49:43', 1, '2026-02-05 14:49:43', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (4, 2, 'assistant', '你好！我是通义千问，阿里巴巴集团旗下的超大规模语言模型，能够回答问题、创作文字、编程等，致力于为你提供准确、有用和友好的帮助。', 'text', 'null', 52, '2026-02-05 14:49:45', 1, '2026-02-05 14:49:45', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (5, 3, 'user', '你是谁', 'text', 'null', NULL, '2026-02-05 15:13:11', 1, '2026-02-05 15:13:11', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (6, 3, 'assistant', '我是通义千问，阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，比如写故事、写公文、写邮件、写剧本、逻辑推理、编程等等，还能表达观点，玩游戏等。如果你有任何问题或需要帮助，欢迎随时告诉我！', 'text', 'null', 70, '2026-02-05 15:13:13', 1, '2026-02-05 15:13:13', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (7, 3, 'user', '用python写个冒泡排序', 'text', 'null', NULL, '2026-02-05 15:14:18', 1, '2026-02-05 15:14:18', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (8, 3, 'assistant', '当然可以！下面是一个用 Python 实现的冒泡排序（Bubble Sort）函数：\n\n```python\ndef bubble_sort(arr):\n    \"\"\"\n    对列表 arr 进行冒泡排序（升序）\n    \"\"\"\n    n = len(arr)\n    # 遍历所有数组元素\n    for i in range(n):\n        # 标志位：如果某一轮没有发生交换，说明已经有序，可以提前结束\n        swapped = False\n        # 最后 i 个元素已经排好序了，不需要再比较\n        for j in range(0, n - i - 1):\n            if arr[j] > arr[j + 1]:\n                # 交换元素\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n                swapped = True\n        # 如果没有发生交换，说明数组已经有序\n        if not swapped:\n            break\n    return arr\n\n# 示例使用\nif __name__ == \"__main__\":\n    data = [64, 34, 25, 12, 22, 11, 90]\n    print(\"原始数组:\", data)\n    sorted_data = bubble_sort(data.copy())  # 使用 copy() 避免修改原列表\n    print(\"排序后数组:\", sorted_data)\n```\n\n### 输出：\n```\n原始数组: [64, 34, 25, 12, 22, 11, 90]\n排序后数组: [11, 12, 22, 25, 34, 64, 90]\n```\n\n### 说明：\n- 冒泡排序通过重复遍历列表，比较相邻元素并交换顺序错误的元素。\n- 时间复杂度：最坏和平均为 O(n²)，最好情况（已排序）为 O(n)（因为加了 `swapped` 优化）。\n- 空间复杂度：O(1)，是原地排序。\n\n如果你需要降序排序，只需把 `>` 改成 `<` 即可。需要我帮你改成降序版本吗？', 'text', 'null', 543, '2026-02-05 15:14:29', 1, '2026-02-05 15:14:29', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (9, 4, 'user', '你是谁', 'text', 'null', NULL, '2026-02-05 15:24:47', 1, '2026-02-05 15:24:47', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (10, 4, 'assistant', '我是通义千问，阿里巴巴集团旗下的超大规模语言模型。我能够回答问题、创作文字，比如写故事、写公文、写邮件、写剧本、逻辑推理、编程等等，还能表达观点，玩游戏等。如果你有任何问题或需要帮助，欢迎随时告诉我！', 'text', 'null', 70, '2026-02-05 15:24:50', 1, '2026-02-05 15:24:50', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (11, 6, 'user', '你哈', 'text', 'null', NULL, '2026-02-05 15:56:59', 1, '2026-02-05 15:56:59', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (12, 6, 'assistant', '', 'text', 'null', 0, '2026-02-05 15:57:02', 1, '2026-02-05 15:57:02', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (13, 6, 'user', '你是谁', 'text', 'null', NULL, '2026-02-05 15:57:17', 1, '2026-02-05 15:57:17', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (14, 6, 'assistant', '', 'text', 'null', 0, '2026-02-05 15:57:20', 1, '2026-02-05 15:57:20', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (15, 8, 'user', '你是谁', 'text', 'null', NULL, '2026-02-05 15:57:40', 1, '2026-02-05 15:57:40', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (16, 8, 'assistant', '', 'text', 'null', 0, '2026-02-05 15:57:43', 1, '2026-02-05 15:57:43', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (17, 7, 'user', '你好，请介绍一下你自己', 'text', 'null', NULL, '2026-02-05 16:01:48', 1, '2026-02-05 16:01:48', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (18, 7, 'assistant', '', 'text', 'null', 0, '2026-02-05 16:01:52', 1, '2026-02-05 16:01:52', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (19, 6, 'user', '你哈', 'text', 'null', NULL, '2026-02-05 16:08:20', 1, '2026-02-05 16:08:20', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (20, 6, 'assistant', '你好！看起来你可能是想跟我打招呼 😊  \n如果你有任何问题、需要帮助，或者只是想聊聊，尽管说！我在这儿呢～', 'text', 'null', 53, '2026-02-05 16:08:23', 1, '2026-02-05 16:08:23', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (21, 6, 'user', '你是谁', 'text', 'null', NULL, '2026-02-05 16:10:03', 1, '2026-02-05 16:10:03', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (22, 6, 'assistant', '你好！我是 **通义千问**（Qwen），是由阿里巴巴集团旗下的通义实验室自主研发的超大规模语言模型。我可以回答问题、创作文字（比如写故事、写公文、写邮件、写剧本、逻辑推理、编程等等），还能表达观点，玩游戏等。\n\n简单来说，我是一个能跟你聊天、帮你做事的AI助手！  \n有什么我可以帮你的吗？😊', 'text', 'null', 147, '2026-02-05 16:10:07', 1, '2026-02-05 16:10:07', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (23, 6, 'user', 'python好学吗', 'text', 'null', NULL, '2026-02-05 16:10:28', 1, '2026-02-05 16:10:28', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (24, 6, 'assistant', 'Python 是**公认比较好学的编程语言之一**，尤其适合编程初学者。以下是几个原因：\n\n### ✅ 为什么 Python 好学？\n1. **语法简洁清晰**  \n   Python 的代码看起来很像英语，缩进代替大括号，结构直观。  \n   比如打印“Hello, World!”只需一行：\n   ```python\n   print(\"Hello, World!\")\n   ```\n\n2. **上手快，成就感强**  \n   很快就能写出实用的小程序，比如自动整理文件、爬取网页数据、做简单数据分析等。\n\n3. **丰富的学习资源**  \n   网上有大量免费教程、视频、书籍（比如《Python Crash Course》《Automate the Boring Stuff with Python》），中文资料也非常多。\n\n4. **强大的社区支持**  \n   遇到问题很容易在网上找到答案（比如 Stack Overflow、知乎、B站等）。\n\n5. **应用广泛**  \n   Python 在**数据分析、人工智能、Web开发、自动化脚本、科学计算**等领域都很流行，学了有用武之地。\n\n---\n\n### ⚠️ 但也要注意：\n- “好学”不等于“不用努力”——任何编程语言都需要动手练习。\n- 初期可能对**变量、循环、函数、缩进规则**等概念感到陌生，但坚持几天就会适应。\n- 后期深入（比如面向对象、异步编程、性能优化）也有挑战，但可以循序渐进。\n\n---\n\n### 🎯 给初学者的建议：\n- **边学边写代码**：不要只看不练！\n- **从兴趣出发**：想做游戏？试试 PyGame；想分析数据？学 pandas；想建网站？试试 Flask/Django。\n- **善用工具**：安装 VS Code 或 PyCharm，配合 Jupyter Notebook 学习更高效。\n\n> 💡 一句话总结：**Python 是入门友好的“第一门编程语言”，坚持一周，你就能写出自己的小工具！**\n\n如果你刚开始学，我可以帮你制定学习计划、解释概念，或者一起写代码 😊  \n想试试吗？', 'text', 'null', 899, '2026-02-05 16:10:45', 1, '2026-02-05 16:10:45', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (25, 9, 'user', '今天星期几', 'text', 'null', NULL, '2026-02-05 16:12:29', 1, '2026-02-05 16:12:29', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (26, 9, 'assistant', '我无法获取你设备的当前日期和时间，因此无法直接告诉你今天是星期几。不过，你可以通过以下方式快速查看：\n\n- **手机/电脑**：查看屏幕右上角或右下角的时间，通常点击后会显示详细日期和星期。\n- **语音助手**：对 Siri、小爱同学、小度等说“今天星期几”。\n- **手动计算**：如果你知道某个已知日期是星期几（比如 2024 年 6 月 10 日是星期一），可以推算出今天的星期。\n\n如果你告诉我今天的具体日期（例如“2024年6月15日”），我可以帮你算出是星期几！', 'text', 'null', 238, '2026-02-05 16:12:34', 1, '2026-02-05 16:12:34', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (27, 9, 'user', '你好', 'text', 'null', NULL, '2026-02-05 16:13:14', 1, '2026-02-05 16:13:14', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (28, 9, 'assistant', '你好！有什么可以帮你的吗？😊', 'text', 'null', 14, '2026-02-05 16:13:15', 1, '2026-02-05 16:13:15', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (29, 9, 'user', '如何学习vue', 'text', 'null', NULL, '2026-02-05 16:13:49', 1, '2026-02-05 16:13:49', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (30, 9, 'assistant', '学习 Vue.js 是一个非常明智的选择，它是一个渐进式、易上手又功能强大的前端框架。以下是系统学习 Vue 的建议路径，适合初学者到进阶者：\n\n---\n\n### 🌱 一、前置知识（建议掌握）\n在学习 Vue 之前，确保你已经掌握以下基础：\n- **HTML / CSS**：网页结构与样式\n- **JavaScript（ES6+）**：变量、函数、数组方法、箭头函数、解构、模块化等\n- **基本命令行操作**（如使用 npm）\n\n> ✅ 不需要会 React 或 Angular，Vue 可以独立入门。\n\n---\n\n### 📚 二、官方文档是最佳起点\nVue 官方文档写得非常清晰、友好，且有中文版：\n- 官网：[https://vuejs.org](https://vuejs.org)\n- 中文文档（Vue 3）：[https://cn.vuejs.org](https://cn.vuejs.org)\n\n> 🔥 强烈建议从 **Vue 3** 开始学（当前主流版本），不要学 Vue 2（已进入维护阶段）。\n\n---\n\n### 🧩 三、学习路线建议\n\n#### 第 1 阶段：基础核心概念（1–2 周）\n- 创建 Vue 应用（`createApp`）\n- 模板语法（插值 `{{}}`、指令 `v-if`、`v-for`、`v-bind`、`v-on`）\n- 响应式数据（`ref`、`reactive`）\n- 计算属性（`computed`）和侦听器（`watch`）\n- 事件处理\n- 组件基础（父子组件、props、emit）\n\n✅ 动手练习：做一个待办事项（Todo List）应用\n\n#### 第 2 阶段：组件进阶与状态管理（1–2 周）\n- 组件通信（props / emit / provide/inject / 事件总线）\n- 插槽（slot）\n- 生命周期钩子（onMounted 等）\n- 使用 **Pinia**（官方推荐的状态管理库，替代 Vuex）\n- 路由：**Vue Router**\n\n✅ 项目练习：做一个博客列表 + 详情页，带路由跳转和状态共享\n\n#### 第 3 阶段：工程化与工具链（1 周+）\n- 使用 **Vite** 创建项目（比 Vue CLI 更快）\n  ```bash\n  npm create vue@latest\n  ```\n- 单文件组件（.vue 文件结构）\n- 组合式 API（Composition API） vs 选项式 API\n- 自定义 Hook（可复用逻辑）\n- Axios 请求数据\n- 表单验证、动画、过渡效果\n\n✅ 项目练习：调用公开 API（如 JSONPlaceholder）做一个用户管理系统\n\n#### 第 4 阶段：实战与优化\n- 代码拆分、懒加载\n- TypeScript 支持（可选但推荐）\n- 单元测试（Vitest / Vue Test Utils）\n- 部署上线（Vercel / Netlify / GitHub Pages）\n\n---\n\n### 🛠️ 四、推荐工具\n- 编辑器：VS Code + Volar 插件（Vue 官方推荐）\n- 浏览器插件：Vue Devtools（调试组件和状态）\n- 包管理：npm / pnpm / yarn\n\n---\n\n### 🎯 五、学习资源推荐\n- **免费教程**：\n  - [Vue Mastery 免费课程](https://www.vuemastery.com/courses/)\n  - B站：搜索 “Vue 3 入门到实战”（推荐“技术蛋老师”、“程序员鱼皮”等）\n- **书籍**：\n  - 《Vue.js 设计与实现》（深入原理，适合进阶）\n- **实战项目灵感**：\n  - GitHub 上找 `vue3 + pinia + vite` 的开源项目\n  - 尝试复刻：天气 App、电影搜索、电商商品页等\n\n---\n\n### 💡 小贴士\n- **不要死记 API**，多写代码、多查文档。\n- **从小项目开始**，逐步增加复杂度。\n- 遇到问题先看官方文档 → 再查 Stack Overflow / GitHub Issues。\n\n---\n\n如果你告诉我你的当前水平（比如“刚学完 JavaScript”或“会 React 想转 Vue”），我可以给你更个性化的建议！ 😊\n\n要不要我帮你生成一个简单的 Vue 3 入门示例？', 'text', 'null', 1853, '2026-02-05 16:14:20', 1, '2026-02-05 16:14:20', 1, 1, NULL);
INSERT INTO `sys_message` VALUES (31, 9, 'user', '帮我写一个测试用例模板', 'text', 'null', NULL, '2026-02-05 16:17:20', 1, '2026-02-05 16:17:20', 1, 1, NULL);


-- ----------------------------
-- Table structure for sys_operation_log
-- ----------------------------
DROP TABLE IF EXISTS `sys_operation_log`;
CREATE TABLE `sys_operation_log`  (
  `user_id` bigint NULL DEFAULT NULL COMMENT '操作用户ID',
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作用户名',
  `operation` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '操作类型',
  `method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '请求方法',
  `url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '请求URL',
  `ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作IP',
  `location` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作地点',
  `user_agent` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '用户代理',
  `module` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作模块',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作描述',
  `request_data` json NULL COMMENT '请求参数',
  `response_data` json NULL COMMENT '响应数据',
  `status` int NOT NULL COMMENT '操作状态（0:失败 1:成功）',
  `error_msg` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '错误信息',
  `execution_time` int NULL DEFAULT NULL COMMENT '执行时间(毫秒)',
  `operation_time` datetime NOT NULL COMMENT '操作时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '操作日志表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_operation_log
-- ----------------------------


-- ----------------------------
-- Table structure for sys_permission
-- ----------------------------
DROP TABLE IF EXISTS `sys_permission`;
CREATE TABLE `sys_permission`  (
  `permission_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '权限名称',
  `permission_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '权限编码',
  `permission_type` int NOT NULL COMMENT '权限类型（1:菜单 2:按钮 3:接口 4:数据）',
  `resource_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '资源类型',
  `resource_id` int NULL DEFAULT NULL COMMENT '关联资源ID',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '权限描述',
  `status` int NULL DEFAULT NULL COMMENT '状态（0:禁用 1:启用）',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_sys_permission_permission_code`(`permission_code` ASC) USING BTREE,
  INDEX `ix_sys_permission_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '权限表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_permission
-- ----------------------------


-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role`  (
  `role_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色名称',
  `role_key` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色权限字符串',
  `role_sort` int NULL DEFAULT NULL COMMENT '显示顺序',
  `data_scope` int NULL DEFAULT NULL COMMENT '数据范围（1:仅本人 2:本部门 3:本部门及以下 4:全部 5:自定义）',
  `status` int NULL DEFAULT NULL COMMENT '角色状态（0:停用 1:正常）',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '备注',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `role_key`(`role_key` ASC) USING BTREE,
  UNIQUE INDEX `role_name`(`role_name` ASC) USING BTREE,
  INDEX `ix_sys_role_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 18 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
INSERT INTO `sys_role` VALUES ('超级管理员', 'admin', 0, 4, 1, '超级管理员角色，拥有所有权限', 1, '2026-01-31 18:06:08', NULL, '2026-04-30 11:18:45', 1, 1, NULL, '2026-03-19 16:00:51', '2026-04-30 11:18:46');
INSERT INTO `sys_role` VALUES ('普通角色', 'user', 0, 4, 1, NULL, 16, '2026-02-04 18:21:02', 1, '2026-03-06 11:39:09', 1, 1, NULL, '2026-02-04 18:21:03', '2026-03-06 11:39:10');
INSERT INTO `sys_role` VALUES ('管理员', 'admin1', 0, 4, 1, NULL, 17, '2026-02-04 18:39:48', 1, '2026-02-04 18:39:48', 1, 1, NULL, '2026-02-04 18:39:48', '2026-02-04 18:39:48');


-- ----------------------------
-- Table structure for sys_role_dept
-- ----------------------------
DROP TABLE IF EXISTS `sys_role_dept`;
CREATE TABLE `sys_role_dept`  (
  `role_id` bigint NOT NULL,
  `dept_id` bigint NOT NULL,
  PRIMARY KEY (`role_id`, `dept_id`) USING BTREE,
  INDEX `dept_id`(`dept_id` ASC) USING BTREE,
  CONSTRAINT `sys_role_dept_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `sys_dept` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `sys_role_dept_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_role_dept
-- ----------------------------


-- ----------------------------
-- Table structure for sys_role_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_role_menu`;
CREATE TABLE `sys_role_menu`  (
  `role_id` bigint NOT NULL,
  `menu_id` bigint NOT NULL,
  PRIMARY KEY (`role_id`, `menu_id`) USING BTREE,
  INDEX `menu_id`(`menu_id` ASC) USING BTREE,
  CONSTRAINT `sys_role_menu_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `sys_menu` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `sys_role_menu_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_role_menu
-- ----------------------------
INSERT INTO `sys_role_menu` VALUES (1, 1);
INSERT INTO `sys_role_menu` VALUES (1, 2);
INSERT INTO `sys_role_menu` VALUES (1, 3);
INSERT INTO `sys_role_menu` VALUES (1, 4);
INSERT INTO `sys_role_menu` VALUES (1, 5);
INSERT INTO `sys_role_menu` VALUES (1, 6);
INSERT INTO `sys_role_menu` VALUES (1, 7);
INSERT INTO `sys_role_menu` VALUES (1, 8);
INSERT INTO `sys_role_menu` VALUES (1, 9);
INSERT INTO `sys_role_menu` VALUES (1, 10);
INSERT INTO `sys_role_menu` VALUES (1, 11);
INSERT INTO `sys_role_menu` VALUES (1, 12);
INSERT INTO `sys_role_menu` VALUES (1, 13);
INSERT INTO `sys_role_menu` VALUES (1, 14);
INSERT INTO `sys_role_menu` VALUES (1, 15);
INSERT INTO `sys_role_menu` VALUES (1, 16);
INSERT INTO `sys_role_menu` VALUES (1, 17);
INSERT INTO `sys_role_menu` VALUES (1, 18);
INSERT INTO `sys_role_menu` VALUES (1, 20);
INSERT INTO `sys_role_menu` VALUES (1, 21);
INSERT INTO `sys_role_menu` VALUES (1, 22);
INSERT INTO `sys_role_menu` VALUES (1, 23);
INSERT INTO `sys_role_menu` VALUES (1, 24);
INSERT INTO `sys_role_menu` VALUES (1, 25);
INSERT INTO `sys_role_menu` VALUES (1, 26);
INSERT INTO `sys_role_menu` VALUES (1, 27);
INSERT INTO `sys_role_menu` VALUES (1, 28);
INSERT INTO `sys_role_menu` VALUES (1, 29);
INSERT INTO `sys_role_menu` VALUES (1, 30);
INSERT INTO `sys_role_menu` VALUES (1, 35);
INSERT INTO `sys_role_menu` VALUES (1, 36);
INSERT INTO `sys_role_menu` VALUES (1, 44);
INSERT INTO `sys_role_menu` VALUES (1, 45);
INSERT INTO `sys_role_menu` VALUES (1, 46);
INSERT INTO `sys_role_menu` VALUES (1, 47);
INSERT INTO `sys_role_menu` VALUES (1, 48);
INSERT INTO `sys_role_menu` VALUES (1, 49);
INSERT INTO `sys_role_menu` VALUES (1, 50);
INSERT INTO `sys_role_menu` VALUES (1, 51);
INSERT INTO `sys_role_menu` VALUES (1, 52);
INSERT INTO `sys_role_menu` VALUES (1, 53);
INSERT INTO `sys_role_menu` VALUES (1, 55);
INSERT INTO `sys_role_menu` VALUES (1, 58);
INSERT INTO `sys_role_menu` VALUES (1, 59);
INSERT INTO `sys_role_menu` VALUES (1, 60);
INSERT INTO `sys_role_menu` VALUES (1, 61);
INSERT INTO `sys_role_menu` VALUES (1, 62);
INSERT INTO `sys_role_menu` VALUES (1, 63);
INSERT INTO `sys_role_menu` VALUES (1, 64);
INSERT INTO `sys_role_menu` VALUES (1, 65);
INSERT INTO `sys_role_menu` VALUES (1, 66);
INSERT INTO `sys_role_menu` VALUES (1, 67);
INSERT INTO `sys_role_menu` VALUES (1, 68);
INSERT INTO `sys_role_menu` VALUES (1, 69);
INSERT INTO `sys_role_menu` VALUES (1, 70);
INSERT INTO `sys_role_menu` VALUES (1, 71);
INSERT INTO `sys_role_menu` VALUES (1, 72);
INSERT INTO `sys_role_menu` VALUES (1, 73);
INSERT INTO `sys_role_menu` VALUES (1, 74);
INSERT INTO `sys_role_menu` VALUES (1, 75);
INSERT INTO `sys_role_menu` VALUES (1, 76);
INSERT INTO `sys_role_menu` VALUES (1, 77);
INSERT INTO `sys_role_menu` VALUES (1, 78);
INSERT INTO `sys_role_menu` VALUES (1, 79);
INSERT INTO `sys_role_menu` VALUES (1, 80);
INSERT INTO `sys_role_menu` VALUES (1, 81);
INSERT INTO `sys_role_menu` VALUES (1, 82);
INSERT INTO `sys_role_menu` VALUES (1, 83);
INSERT INTO `sys_role_menu` VALUES (1, 84);
INSERT INTO `sys_role_menu` VALUES (1, 85);
INSERT INTO `sys_role_menu` VALUES (1, 92);
INSERT INTO `sys_role_menu` VALUES (1, 93);
INSERT INTO `sys_role_menu` VALUES (1, 94);
INSERT INTO `sys_role_menu` VALUES (1, 95);
INSERT INTO `sys_role_menu` VALUES (1, 96);
INSERT INTO `sys_role_menu` VALUES (1, 97);
INSERT INTO `sys_role_menu` VALUES (1, 98);
INSERT INTO `sys_role_menu` VALUES (1, 99);
INSERT INTO `sys_role_menu` VALUES (1, 105);
INSERT INTO `sys_role_menu` VALUES (1, 106);
INSERT INTO `sys_role_menu` VALUES (1, 107);
INSERT INTO `sys_role_menu` VALUES (1, 108);
INSERT INTO `sys_role_menu` VALUES (1, 109);
INSERT INTO `sys_role_menu` VALUES (1, 110);
INSERT INTO `sys_role_menu` VALUES (1, 111);
INSERT INTO `sys_role_menu` VALUES (1, 112);
INSERT INTO `sys_role_menu` VALUES (1, 113);
INSERT INTO `sys_role_menu` VALUES (1, 114);
INSERT INTO `sys_role_menu` VALUES (1, 115);
INSERT INTO `sys_role_menu` VALUES (1, 116);
INSERT INTO `sys_role_menu` VALUES (1, 117);
INSERT INTO `sys_role_menu` VALUES (1, 121);
INSERT INTO `sys_role_menu` VALUES (1, 122);
INSERT INTO `sys_role_menu` VALUES (1, 123);
INSERT INTO `sys_role_menu` VALUES (1, 124);
INSERT INTO `sys_role_menu` VALUES (1, 125);
INSERT INTO `sys_role_menu` VALUES (1, 126);
INSERT INTO `sys_role_menu` VALUES (1, 127);
INSERT INTO `sys_role_menu` VALUES (1, 128);
INSERT INTO `sys_role_menu` VALUES (1, 129);
INSERT INTO `sys_role_menu` VALUES (1, 130);
INSERT INTO `sys_role_menu` VALUES (1, 131);
INSERT INTO `sys_role_menu` VALUES (1, 132);
INSERT INTO `sys_role_menu` VALUES (1, 133);
INSERT INTO `sys_role_menu` VALUES (1, 134);
INSERT INTO `sys_role_menu` VALUES (1, 135);
INSERT INTO `sys_role_menu` VALUES (1, 136);
INSERT INTO `sys_role_menu` VALUES (1, 137);
INSERT INTO `sys_role_menu` VALUES (1, 138);
INSERT INTO `sys_role_menu` VALUES (1, 139);
INSERT INTO `sys_role_menu` VALUES (1, 140);
INSERT INTO `sys_role_menu` VALUES (1, 141);
INSERT INTO `sys_role_menu` VALUES (1, 142);
INSERT INTO `sys_role_menu` VALUES (1, 143);
INSERT INTO `sys_role_menu` VALUES (1, 144);
INSERT INTO `sys_role_menu` VALUES (1, 145);
INSERT INTO `sys_role_menu` VALUES (1, 146);
INSERT INTO `sys_role_menu` VALUES (1, 147);
INSERT INTO `sys_role_menu` VALUES (1, 148);
INSERT INTO `sys_role_menu` VALUES (1, 149);
INSERT INTO `sys_role_menu` VALUES (1, 150);
INSERT INTO `sys_role_menu` VALUES (1, 151);
INSERT INTO `sys_role_menu` VALUES (1, 152);
INSERT INTO `sys_role_menu` VALUES (1, 153);
INSERT INTO `sys_role_menu` VALUES (1, 154);
INSERT INTO `sys_role_menu` VALUES (1, 155);
INSERT INTO `sys_role_menu` VALUES (1, 156);
INSERT INTO `sys_role_menu` VALUES (1, 157);
INSERT INTO `sys_role_menu` VALUES (1, 158);
INSERT INTO `sys_role_menu` VALUES (1, 159);
INSERT INTO `sys_role_menu` VALUES (1, 160);
INSERT INTO `sys_role_menu` VALUES (1, 161);
INSERT INTO `sys_role_menu` VALUES (1, 162);
INSERT INTO `sys_role_menu` VALUES (1, 163);
INSERT INTO `sys_role_menu` VALUES (1, 164);
INSERT INTO `sys_role_menu` VALUES (1, 165);
INSERT INTO `sys_role_menu` VALUES (1, 166);
INSERT INTO `sys_role_menu` VALUES (1, 167);
INSERT INTO `sys_role_menu` VALUES (1, 168);
INSERT INTO `sys_role_menu` VALUES (1, 169);
INSERT INTO `sys_role_menu` VALUES (1, 170);
INSERT INTO `sys_role_menu` VALUES (1, 171);
INSERT INTO `sys_role_menu` VALUES (1, 172);
INSERT INTO `sys_role_menu` VALUES (1, 173);
INSERT INTO `sys_role_menu` VALUES (1, 174);
INSERT INTO `sys_role_menu` VALUES (1, 175);
INSERT INTO `sys_role_menu` VALUES (1, 176);
INSERT INTO `sys_role_menu` VALUES (1, 177);
INSERT INTO `sys_role_menu` VALUES (1, 178);
INSERT INTO `sys_role_menu` VALUES (1, 179);
INSERT INTO `sys_role_menu` VALUES (1, 180);
INSERT INTO `sys_role_menu` VALUES (1, 181);
INSERT INTO `sys_role_menu` VALUES (1, 182);
INSERT INTO `sys_role_menu` VALUES (1, 183);
INSERT INTO `sys_role_menu` VALUES (1, 184);
INSERT INTO `sys_role_menu` VALUES (1, 185);
INSERT INTO `sys_role_menu` VALUES (1, 186);
INSERT INTO `sys_role_menu` VALUES (1, 187);
INSERT INTO `sys_role_menu` VALUES (1, 188);
INSERT INTO `sys_role_menu` VALUES (1, 189);
INSERT INTO `sys_role_menu` VALUES (1, 190);
INSERT INTO `sys_role_menu` VALUES (1, 191);
INSERT INTO `sys_role_menu` VALUES (1, 192);
INSERT INTO `sys_role_menu` VALUES (1, 193);
INSERT INTO `sys_role_menu` VALUES (1, 194);
INSERT INTO `sys_role_menu` VALUES (1, 195);
INSERT INTO `sys_role_menu` VALUES (1, 196);
INSERT INTO `sys_role_menu` VALUES (1, 197);
INSERT INTO `sys_role_menu` VALUES (1, 198);
INSERT INTO `sys_role_menu` VALUES (1, 199);
INSERT INTO `sys_role_menu` VALUES (1, 200);
INSERT INTO `sys_role_menu` VALUES (1, 201);
INSERT INTO `sys_role_menu` VALUES (1, 202);
INSERT INTO `sys_role_menu` VALUES (1, 203);
INSERT INTO `sys_role_menu` VALUES (1, 204);
INSERT INTO `sys_role_menu` VALUES (1, 205);
INSERT INTO `sys_role_menu` VALUES (1, 206);
INSERT INTO `sys_role_menu` VALUES (1, 207);
INSERT INTO `sys_role_menu` VALUES (1, 208);
INSERT INTO `sys_role_menu` VALUES (1, 209);
INSERT INTO `sys_role_menu` VALUES (1, 211);
INSERT INTO `sys_role_menu` VALUES (1, 212);
INSERT INTO `sys_role_menu` VALUES (1, 213);
INSERT INTO `sys_role_menu` VALUES (1, 214);
INSERT INTO `sys_role_menu` VALUES (1, 215);
INSERT INTO `sys_role_menu` VALUES (1, 216);
INSERT INTO `sys_role_menu` VALUES (1, 217);
INSERT INTO `sys_role_menu` VALUES (1, 218);
INSERT INTO `sys_role_menu` VALUES (1, 219);
INSERT INTO `sys_role_menu` VALUES (1, 220);
INSERT INTO `sys_role_menu` VALUES (1, 221);
INSERT INTO `sys_role_menu` VALUES (1, 222);
INSERT INTO `sys_role_menu` VALUES (1, 223);
INSERT INTO `sys_role_menu` VALUES (1, 224);
INSERT INTO `sys_role_menu` VALUES (1, 225);
INSERT INTO `sys_role_menu` VALUES (1, 226);
INSERT INTO `sys_role_menu` VALUES (1, 227);
INSERT INTO `sys_role_menu` VALUES (1, 228);
INSERT INTO `sys_role_menu` VALUES (1, 229);
INSERT INTO `sys_role_menu` VALUES (1, 230);
INSERT INTO `sys_role_menu` VALUES (1, 231);
INSERT INTO `sys_role_menu` VALUES (1, 243);
INSERT INTO `sys_role_menu` VALUES (1, 244);
INSERT INTO `sys_role_menu` VALUES (1, 245);
INSERT INTO `sys_role_menu` VALUES (1, 246);
INSERT INTO `sys_role_menu` VALUES (1, 247);
INSERT INTO `sys_role_menu` VALUES (1, 248);
INSERT INTO `sys_role_menu` VALUES (1, 249);
INSERT INTO `sys_role_menu` VALUES (1, 250);
INSERT INTO `sys_role_menu` VALUES (1, 251);
INSERT INTO `sys_role_menu` VALUES (1, 252);
INSERT INTO `sys_role_menu` VALUES (1, 253);
INSERT INTO `sys_role_menu` VALUES (1, 254);
INSERT INTO `sys_role_menu` VALUES (1, 255);
INSERT INTO `sys_role_menu` VALUES (1, 256);
INSERT INTO `sys_role_menu` VALUES (1, 257);
INSERT INTO `sys_role_menu` VALUES (1, 258);
INSERT INTO `sys_role_menu` VALUES (1, 259);
INSERT INTO `sys_role_menu` VALUES (1, 260);
INSERT INTO `sys_role_menu` VALUES (1, 262);
INSERT INTO `sys_role_menu` VALUES (1, 319);
INSERT INTO `sys_role_menu` VALUES (1, 320);
INSERT INTO `sys_role_menu` VALUES (1, 321);
INSERT INTO `sys_role_menu` VALUES (1, 322);
INSERT INTO `sys_role_menu` VALUES (1, 323);
INSERT INTO `sys_role_menu` VALUES (1, 324);
INSERT INTO `sys_role_menu` VALUES (1, 325);
INSERT INTO `sys_role_menu` VALUES (1, 326);
INSERT INTO `sys_role_menu` VALUES (1, 327);
INSERT INTO `sys_role_menu` VALUES (1, 328);
INSERT INTO `sys_role_menu` VALUES (1, 329);
INSERT INTO `sys_role_menu` VALUES (1, 330);
INSERT INTO `sys_role_menu` VALUES (1, 331);
INSERT INTO `sys_role_menu` VALUES (1, 332);
INSERT INTO `sys_role_menu` VALUES (1, 333);
INSERT INTO `sys_role_menu` VALUES (1, 334);
INSERT INTO `sys_role_menu` VALUES (1, 335);
INSERT INTO `sys_role_menu` VALUES (1, 336);
INSERT INTO `sys_role_menu` VALUES (1, 337);
INSERT INTO `sys_role_menu` VALUES (1, 338);
INSERT INTO `sys_role_menu` VALUES (1, 339);
INSERT INTO `sys_role_menu` VALUES (1, 340);
INSERT INTO `sys_role_menu` VALUES (1, 341);
INSERT INTO `sys_role_menu` VALUES (1, 342);
INSERT INTO `sys_role_menu` VALUES (1, 343);
INSERT INTO `sys_role_menu` VALUES (1, 344);
INSERT INTO `sys_role_menu` VALUES (1, 345);
INSERT INTO `sys_role_menu` VALUES (1, 346);
INSERT INTO `sys_role_menu` VALUES (1, 357);
INSERT INTO `sys_role_menu` VALUES (1, 358);
INSERT INTO `sys_role_menu` VALUES (1, 359);
INSERT INTO `sys_role_menu` VALUES (1, 360);
INSERT INTO `sys_role_menu` VALUES (1, 361);
INSERT INTO `sys_role_menu` VALUES (1, 362);
INSERT INTO `sys_role_menu` VALUES (1, 363);
INSERT INTO `sys_role_menu` VALUES (1, 364);
INSERT INTO `sys_role_menu` VALUES (1, 365);
INSERT INTO `sys_role_menu` VALUES (1, 366);
INSERT INTO `sys_role_menu` VALUES (1, 2001);
INSERT INTO `sys_role_menu` VALUES (1, 2002);
INSERT INTO `sys_role_menu` VALUES (1, 2003);
INSERT INTO `sys_role_menu` VALUES (1, 2004);
INSERT INTO `sys_role_menu` VALUES (1, 2005);
INSERT INTO `sys_role_menu` VALUES (1, 2006);
INSERT INTO `sys_role_menu` VALUES (1, 2007);
INSERT INTO `sys_role_menu` VALUES (1, 2008);
INSERT INTO `sys_role_menu` VALUES (1, 2009);
INSERT INTO `sys_role_menu` VALUES (1, 2010);
INSERT INTO `sys_role_menu` VALUES (1, 2011);
INSERT INTO `sys_role_menu` VALUES (1, 2012);
INSERT INTO `sys_role_menu` VALUES (1, 3001);
INSERT INTO `sys_role_menu` VALUES (1, 3002);
INSERT INTO `sys_role_menu` VALUES (1, 3003);
INSERT INTO `sys_role_menu` VALUES (1, 3004);
INSERT INTO `sys_role_menu` VALUES (1, 3005);
INSERT INTO `sys_role_menu` VALUES (1, 3006);
INSERT INTO `sys_role_menu` VALUES (1, 3007);
INSERT INTO `sys_role_menu` VALUES (1, 3008);
INSERT INTO `sys_role_menu` VALUES (1, 3009);
INSERT INTO `sys_role_menu` VALUES (1, 3010);
INSERT INTO `sys_role_menu` VALUES (1, 3011);
INSERT INTO `sys_role_menu` VALUES (1, 3012);
INSERT INTO `sys_role_menu` VALUES (1, 3013);
INSERT INTO `sys_role_menu` VALUES (1, 3014);
INSERT INTO `sys_role_menu` VALUES (1, 3015);
INSERT INTO `sys_role_menu` VALUES (1, 3016);
INSERT INTO `sys_role_menu` VALUES (1, 3017);
INSERT INTO `sys_role_menu` VALUES (1, 3018);
INSERT INTO `sys_role_menu` VALUES (1, 3019);
INSERT INTO `sys_role_menu` VALUES (1, 3020);
INSERT INTO `sys_role_menu` VALUES (1, 3021);
INSERT INTO `sys_role_menu` VALUES (1, 3025);
INSERT INTO `sys_role_menu` VALUES (17, 3025);
INSERT INTO `sys_role_menu` VALUES (1, 3026);
INSERT INTO `sys_role_menu` VALUES (17, 3026);
INSERT INTO `sys_role_menu` VALUES (1, 3027);
INSERT INTO `sys_role_menu` VALUES (1, 3028);
INSERT INTO `sys_role_menu` VALUES (1, 3029);
INSERT INTO `sys_role_menu` VALUES (1, 3030);
INSERT INTO `sys_role_menu` VALUES (1, 3031);
INSERT INTO `sys_role_menu` VALUES (1, 3032);
INSERT INTO `sys_role_menu` VALUES (1, 4001);
INSERT INTO `sys_role_menu` VALUES (1, 4002);
INSERT INTO `sys_role_menu` VALUES (1, 4003);
INSERT INTO `sys_role_menu` VALUES (1, 4004);
INSERT INTO `sys_role_menu` VALUES (1, 4005);
INSERT INTO `sys_role_menu` VALUES (1, 4006);
INSERT INTO `sys_role_menu` VALUES (1, 4007);
INSERT INTO `sys_role_menu` VALUES (1, 4008);
INSERT INTO `sys_role_menu` VALUES (1, 4009);
INSERT INTO `sys_role_menu` VALUES (1, 4010);
INSERT INTO `sys_role_menu` VALUES (1, 4011);
INSERT INTO `sys_role_menu` VALUES (1, 4012);
INSERT INTO `sys_role_menu` VALUES (1, 4013);
INSERT INTO `sys_role_menu` VALUES (1, 4014);
INSERT INTO `sys_role_menu` VALUES (1, 4015);
INSERT INTO `sys_role_menu` VALUES (1, 4016);
INSERT INTO `sys_role_menu` VALUES (1, 4017);
INSERT INTO `sys_role_menu` VALUES (1, 4018);
INSERT INTO `sys_role_menu` VALUES (1, 4019);
INSERT INTO `sys_role_menu` VALUES (1, 4020);
INSERT INTO `sys_role_menu` VALUES (1, 4021);
INSERT INTO `sys_role_menu` VALUES (1, 4022);
INSERT INTO `sys_role_menu` VALUES (1, 4023);
INSERT INTO `sys_role_menu` VALUES (1, 4024);
INSERT INTO `sys_role_menu` VALUES (1, 4025);
INSERT INTO `sys_role_menu` VALUES (1, 4026);
INSERT INTO `sys_role_menu` VALUES (1, 4027);
INSERT INTO `sys_role_menu` VALUES (1, 4028);
INSERT INTO `sys_role_menu` VALUES (1, 4029);
INSERT INTO `sys_role_menu` VALUES (1, 4030);
INSERT INTO `sys_role_menu` VALUES (1, 4031);
INSERT INTO `sys_role_menu` VALUES (1, 4032);
INSERT INTO `sys_role_menu` VALUES (1, 4033);
INSERT INTO `sys_role_menu` VALUES (1, 4034);
INSERT INTO `sys_role_menu` VALUES (1, 4035);
INSERT INTO `sys_role_menu` VALUES (1, 4036);
INSERT INTO `sys_role_menu` VALUES (1, 4037);
INSERT INTO `sys_role_menu` VALUES (1, 4038);
INSERT INTO `sys_role_menu` VALUES (1, 4039);
INSERT INTO `sys_role_menu` VALUES (1, 4040);
INSERT INTO `sys_role_menu` VALUES (1, 4077);
INSERT INTO `sys_role_menu` VALUES (1, 4080);
INSERT INTO `sys_role_menu` VALUES (1, 4081);
INSERT INTO `sys_role_menu` VALUES (1, 4082);
INSERT INTO `sys_role_menu` VALUES (1, 4083);
INSERT INTO `sys_role_menu` VALUES (1, 4084);
INSERT INTO `sys_role_menu` VALUES (1, 4085);
INSERT INTO `sys_role_menu` VALUES (1, 4086);
INSERT INTO `sys_role_menu` VALUES (1, 4087);
INSERT INTO `sys_role_menu` VALUES (1, 4088);
INSERT INTO `sys_role_menu` VALUES (1, 4090);
INSERT INTO `sys_role_menu` VALUES (1, 4091);
INSERT INTO `sys_role_menu` VALUES (1, 4092);
INSERT INTO `sys_role_menu` VALUES (1, 4093);
INSERT INTO `sys_role_menu` VALUES (1, 4094);
INSERT INTO `sys_role_menu` VALUES (1, 4095);
INSERT INTO `sys_role_menu` VALUES (1, 4096);
INSERT INTO `sys_role_menu` VALUES (1, 4097);
INSERT INTO `sys_role_menu` VALUES (1, 4098);
INSERT INTO `sys_role_menu` VALUES (1, 4099);
INSERT INTO `sys_role_menu` VALUES (1, 4100);
INSERT INTO `sys_role_menu` VALUES (1, 4101);
INSERT INTO `sys_role_menu` VALUES (1, 4102);
INSERT INTO `sys_role_menu` VALUES (1, 4103);
INSERT INTO `sys_role_menu` VALUES (1, 4104);
INSERT INTO `sys_role_menu` VALUES (1, 4105);
INSERT INTO `sys_role_menu` VALUES (1, 4106);
INSERT INTO `sys_role_menu` VALUES (1, 4107);
INSERT INTO `sys_role_menu` VALUES (1, 4108);
INSERT INTO `sys_role_menu` VALUES (1, 4109);
INSERT INTO `sys_role_menu` VALUES (1, 4110);
INSERT INTO `sys_role_menu` VALUES (1, 4111);
INSERT INTO `sys_role_menu` VALUES (1, 4112);
INSERT INTO `sys_role_menu` VALUES (1, 4113);
INSERT INTO `sys_role_menu` VALUES (1, 4114);
INSERT INTO `sys_role_menu` VALUES (1, 4115);
INSERT INTO `sys_role_menu` VALUES (1, 4116);
INSERT INTO `sys_role_menu` VALUES (1, 4117);
INSERT INTO `sys_role_menu` VALUES (1, 4118);
INSERT INTO `sys_role_menu` VALUES (1, 4128);
INSERT INTO `sys_role_menu` VALUES (1, 4129);
INSERT INTO `sys_role_menu` VALUES (1, 4130);
INSERT INTO `sys_role_menu` VALUES (1, 4133);
INSERT INTO `sys_role_menu` VALUES (1, 4134);
INSERT INTO `sys_role_menu` VALUES (1, 4135);
INSERT INTO `sys_role_menu` VALUES (1, 4136);
INSERT INTO `sys_role_menu` VALUES (1, 4137);
INSERT INTO `sys_role_menu` VALUES (1, 4138);
INSERT INTO `sys_role_menu` VALUES (1, 4200);
INSERT INTO `sys_role_menu` VALUES (1, 4201);
INSERT INTO `sys_role_menu` VALUES (1, 4202);
INSERT INTO `sys_role_menu` VALUES (1, 4203);
INSERT INTO `sys_role_menu` VALUES (1, 4204);
INSERT INTO `sys_role_menu` VALUES (1, 4205);
INSERT INTO `sys_role_menu` VALUES (1, 4206);
INSERT INTO `sys_role_menu` VALUES (1, 4207);
INSERT INTO `sys_role_menu` VALUES (1, 4208);
INSERT INTO `sys_role_menu` VALUES (1, 4209);
INSERT INTO `sys_role_menu` VALUES (1, 4210);
INSERT INTO `sys_role_menu` VALUES (1, 4211);
INSERT INTO `sys_role_menu` VALUES (1, 4212);
INSERT INTO `sys_role_menu` VALUES (1, 4213);
INSERT INTO `sys_role_menu` VALUES (1, 4214);
INSERT INTO `sys_role_menu` VALUES (1, 4215);
INSERT INTO `sys_role_menu` VALUES (1, 4216);


-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名',
  `password` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码（加密）',
  `nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户昵称',
  `email` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '邮箱',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '手机号',
  `avatar` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '头像URL',
  `user_type` int NOT NULL COMMENT '用户类型（0:普通用户 10:超级管理员）',
  `status` int NOT NULL COMMENT '用户状态（0:禁用 1:启用）',
  `gender` int NULL DEFAULT NULL COMMENT '性别（0:未知 1:男 2:女）',
  `dept_id` bigint NULL DEFAULT NULL COMMENT '部门ID',
  `post` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '岗位',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `tags` json NULL COMMENT '个性标签（JSON数组）',
  `last_login_time` datetime NULL DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '最后登录IP',
  `oauth_provider` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'OAuth 提供商',
  `last_login_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '最后登录方式',
  `gitee_id` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Gitee 用户 ID',
  `github_id` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'GitHub 用户 ID',
  `qq_openid` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'QQ OpenID',
  `google_id` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Google 用户 ID',
  `wechat_unionid` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '微信 UnionID',
  `microsoft_id` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'Microsoft 用户 ID',
  `dingtalk_unionid` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '钉钉 UnionID',
  `feishu_union_id` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '飞书 UnionID',
  `bio` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '个人简介',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ix_sys_user_username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_dingtalk_unionid`(`dingtalk_unionid` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_feishu_union_id`(`feishu_union_id` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_gitee_id`(`gitee_id` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_github_id`(`github_id` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_google_id`(`google_id` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_microsoft_id`(`microsoft_id` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_qq_openid`(`qq_openid` ASC) USING BTREE,
  UNIQUE INDEX `ix_sys_user_wechat_unionid`(`wechat_unionid` ASC) USING BTREE,
  INDEX `dept_id`(`dept_id` ASC) USING BTREE,
  INDEX `ix_sys_user_id`(`id` ASC) USING BTREE,
  CONSTRAINT `sys_user_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `sys_dept` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 36 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
INSERT INTO `sys_user` VALUES ('admin', '$2b$12$XdwqiDrVu3Qdvjlx5Je4D.2uPbcs4wiGtsfxKowL06Npvcn5sbGNq', '超级管理员', 'adminrebort@example.com', NULL, '/static/upload/avatars/avatar_1_0e5c807e.jpeg', 10, 1, 0, NULL, NULL, '超级管理员', '[\"超级管理员\"]', '2026-04-30 11:19:08', '127.0.0.1', '2026-01-31 18:06:08', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 1, '2026-01-31 18:06:08', NULL, '2026-04-30 11:19:08', NULL, 1, NULL, '2026-01-31 18:06:08', '2026-04-30 11:19:08');
INSERT INTO `sys_user` VALUES ('测试用户', '$2b$12$sbHGXGxc0wMVI0fIvfsFS.JCMqovwKH8mdJHYRXk6o5oqL5PLlFWm', '普通用户', NULL, NULL, NULL, 20, 1, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 34, '2026-02-06 14:03:47', 1, '2026-04-01 10:14:17', 1, 1, NULL, '2026-02-06 14:03:48', '2026-04-01 10:14:18');
INSERT INTO `sys_user` VALUES ('Rebort', '$2b$12$yv8UjM.kyQnGq/wtzN.gsO4rYVCk/2bn37nJAbOXp9JVwH1084yum', 'Rebort', NULL, NULL, NULL, 20, 1, 0, NULL, NULL, NULL, NULL, '2026-03-06 11:31:06', '127.0.0.1', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 35, '2026-02-06 18:41:03', 1, '2026-03-06 11:31:06', 1, 1, NULL, '2026-02-06 18:41:04', '2026-03-06 11:31:06');


-- ----------------------------
-- Table structure for project_mcp_config
-- ----------------------------
DROP TABLE IF EXISTS `project_mcp_config`;
CREATE TABLE `project_mcp_config`  (
  `user_id` bigint NOT NULL COMMENT '所属用户',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '配置名称',
  `url` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT 'MCP 服务 URL',
  `transport` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '传输协议',
  `headers` json NULL COMMENT '请求头 JSON',
  `is_enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_project_mcp_user_name`(`user_id` ASC, `name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'MCP 配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_mcp_config
-- ----------------------------
INSERT INTO `project_mcp_config` VALUES (1, 'mcp', 'http://localhost:8931/mcp', 'streamable-http', '{}', 1, 1, '2026-04-09 10:55:57', 1, '2026-04-13 16:53:20', 1, 0, NULL);


-- ----------------------------
-- Table structure for projects
-- ----------------------------
DROP TABLE IF EXISTS `projects`;
CREATE TABLE `projects`  (
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '项目名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '项目描述',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '状态: active/paused/completed/archived',
  `owner_id` bigint NOT NULL COMMENT '负责人ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_project_owner`(`owner_id` ASC) USING BTREE,
  INDEX `idx_project_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '项目表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of projects
-- ----------------------------
INSERT INTO `projects` VALUES ('测试项目', '0', 'active', 1, 1, '2026-04-07 10:39:06', 1, '2026-04-07 10:52:07', 1, 1, NULL);
INSERT INTO `projects` VALUES ('测试', '', 'active', 1, 2, '2026-04-16 14:10:38', 1, '2026-04-16 14:10:38', NULL, 1, NULL);


-- ----------------------------
-- Table structure for project_members
-- ----------------------------
DROP TABLE IF EXISTS `project_members`;
CREATE TABLE `project_members`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '角色: owner/admin/developer/tester/viewer',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_pm_project_user`(`project_id` ASC, `user_id` ASC) USING BTREE,
  INDEX `idx_pm_user`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '项目成员表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_members
-- ----------------------------
INSERT INTO `project_members` VALUES (1, 1, 'owner', 1, '2026-04-07 10:39:06', 1, '2026-04-07 10:39:06', NULL, 1, NULL);
INSERT INTO `project_members` VALUES (2, 1, 'owner', 2, '2026-04-16 14:10:38', 1, '2026-04-16 14:10:38', NULL, 1, NULL);


-- ----------------------------
-- Table structure for project_skill
-- ----------------------------
DROP TABLE IF EXISTS `project_skill`;
CREATE TABLE `project_skill`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `user_id` bigint NOT NULL COMMENT '所属用户',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '技能名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '技能描述',
  `scenario_category` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '场景分类，如agent-browser-skill',
  `source_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '来源类型 builtin/github/gitee/upload',
  `repo_url` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '仓库URL',
  `skill_path` varchar(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '技能本地目录',
  `entry_command` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '执行命令',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `extra_config` json NULL COMMENT '附加配置',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uq_project_skill_user_project_name`(`user_id` ASC, `project_id` ASC, `name` ASC) USING BTREE,
  INDEX `idx_project_skill_project`(`project_id` ASC) USING BTREE,
  INDEX `idx_project_skill_user`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 14 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '项目技能表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_skill
-- ----------------------------
INSERT INTO `project_skill` VALUES (1, 1, 'agent-browser', 'Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, testing web apps, or automating any browser task. Triggers include requests to \"open a website\", \"fill out a form\", \"click a button\", \"take a screenshot\", \"scrape data from a page\", \"test this web app\", \"login to a site\", \"automate browser actions\", or any task requiring programmatic web interaction.', 'agent-browser', 'github', 'https://github.com/vercel-labs/agent-browser.git', 'uploads\\skills\\1\\1\\9ff222848089_agent-browser\\skills\\agent-browser', 'agent-browser open https://www.baidu.com', 1, '{\"pack_root\": \"uploads\\\\skills\\\\1\\\\1\\\\9ff222848089_agent-browser\", \"allowed_tools\": \"Bash(npx agent-browser:*), Bash(agent-browser:*)\"}', 8, '2026-04-10 11:27:54', 1, '2026-04-10 14:33:25', 1, 1, NULL);
INSERT INTO `project_skill` VALUES (1, 1, 'agentcore', 'Run agent-browser on AWS Bedrock AgentCore cloud browsers. Use when the user wants to use AgentCore, run browser automation on AWS, use a cloud browser with AWS credentials, or needs a managed browser session backed by AWS infrastructure. Triggers include \"use agentcore\", \"run on AWS\", \"cloud browser with AWS\", \"bedrock browser\", \"agentcore session\", or any task requiring AWS-hosted browser automation.', 'agentcore', 'github', 'https://github.com/vercel-labs/agent-browser.git', 'uploads\\skills\\1\\1\\9ff222848089_agent-browser\\skills\\agentcore', NULL, 1, '{\"pack_root\": \"uploads\\\\skills\\\\1\\\\1\\\\9ff222848089_agent-browser\", \"allowed_tools\": \"Bash(agent-browser:*), Bash(npx agent-browser:*)\"}', 9, '2026-04-10 11:27:54', 1, '2026-04-10 11:27:54', 1, 1, NULL);
INSERT INTO `project_skill` VALUES (1, 1, 'dogfood', 'Systematically explore and test a web application to find bugs, UX issues, and other problems. Use when asked to \"dogfood\", \"QA\", \"exploratory test\", \"find issues\", \"bug hunt\", \"test this app/site/platform\", or review the quality of a web application. Produces a structured report with full reproduction evidence -- step-by-step screenshots, repro videos, and detailed repro steps for every issue -- so findings can be handed directly to the responsible teams.', 'dogfood', 'github', 'https://github.com/vercel-labs/agent-browser.git', 'uploads\\skills\\1\\1\\9ff222848089_agent-browser\\skills\\dogfood', NULL, 1, '{\"pack_root\": \"uploads\\\\skills\\\\1\\\\1\\\\9ff222848089_agent-browser\", \"allowed_tools\": \"Bash(agent-browser:*), Bash(npx agent-browser:*)\"}', 10, '2026-04-10 11:27:54', 1, '2026-04-10 11:27:54', 1, 1, NULL);
INSERT INTO `project_skill` VALUES (1, 1, 'electron', 'Automate Electron desktop apps (VS Code, Slack, Discord, Figma, Notion, Spotify, etc.) using agent-browser via Chrome DevTools Protocol. Use when the user needs to interact with an Electron app, automate a desktop app, connect to a running app, control a native app, or test an Electron application. Triggers include \"automate Slack app\", \"control VS Code\", \"interact with Discord app\", \"test this Electron app\", \"connect to desktop app\", or any task requiring automation of a native Electron application.', 'electron', 'github', 'https://github.com/vercel-labs/agent-browser.git', 'uploads\\skills\\1\\1\\9ff222848089_agent-browser\\skills\\electron', NULL, 1, '{\"pack_root\": \"uploads\\\\skills\\\\1\\\\1\\\\9ff222848089_agent-browser\", \"allowed_tools\": \"Bash(agent-browser:*), Bash(npx agent-browser:*)\"}', 11, '2026-04-10 11:27:55', 1, '2026-04-10 11:27:55', 1, 1, NULL);
INSERT INTO `project_skill` VALUES (1, 1, 'slack', 'Interact with Slack workspaces using browser automation. Use when the user needs to check unread channels, navigate Slack, send messages, extract data, find information, search conversations, or automate any Slack task. Triggers include \"check my Slack\", \"what channels have unreads\", \"send a message to\", \"search Slack for\", \"extract from Slack\", \"find who said\", or any task requiring programmatic Slack interaction.', 'slack', 'github', 'https://github.com/vercel-labs/agent-browser.git', 'uploads\\skills\\1\\1\\9ff222848089_agent-browser\\skills\\slack', NULL, 1, '{\"pack_root\": \"uploads\\\\skills\\\\1\\\\1\\\\9ff222848089_agent-browser\", \"allowed_tools\": \"Bash(agent-browser:*), Bash(npx agent-browser:*)\"}', 12, '2026-04-10 11:27:55', 1, '2026-04-10 11:27:55', 1, 1, NULL);
INSERT INTO `project_skill` VALUES (1, 1, 'vercel-sandbox', 'Run agent-browser + Chrome inside Vercel Sandbox microVMs for browser automation from any Vercel-deployed app. Use when the user needs browser automation in a Vercel app (Next.js, SvelteKit, Nuxt, Remix, Astro, etc.), wants to run headless Chrome without binary size limits, needs persistent browser sessions across commands, or wants ephemeral isolated browser environments. Triggers include \"Vercel Sandbox browser\", \"microVM Chrome\", \"agent-browser in sandbox\", \"browser automation on Vercel\", or any task requiring Chrome in a Vercel Sandbox.', 'vercel-sandbox', 'github', 'https://github.com/vercel-labs/agent-browser.git', 'uploads\\skills\\1\\1\\9ff222848089_agent-browser\\skills\\vercel-sandbox', NULL, 1, '{\"pack_root\": \"uploads\\\\skills\\\\1\\\\1\\\\9ff222848089_agent-browser\", \"allowed_tools\": \"\"}', 13, '2026-04-10 11:27:55', 1, '2026-04-10 11:27:55', 1, 1, NULL);


-- ----------------------------
-- Table structure for sys_user_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_user_role`;
CREATE TABLE `sys_user_role`  (
  `user_id` bigint NOT NULL,
  `role_id` bigint NOT NULL,
  PRIMARY KEY (`user_id`, `role_id`) USING BTREE,
  INDEX `role_id`(`role_id` ASC) USING BTREE,
  CONSTRAINT `sys_user_role_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `sys_role` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `sys_user_role_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sys_user_role
-- ----------------------------
INSERT INTO `sys_user_role` VALUES (1, 1);
INSERT INTO `sys_user_role` VALUES (34, 16);
INSERT INTO `sys_user_role` VALUES (35, 16);


-- ----------------------------
-- Table structure for task_notification_settings
-- ----------------------------
DROP TABLE IF EXISTS `task_notification_settings`;
CREATE TABLE `task_notification_settings`  (
  `task_id` bigint NOT NULL COMMENT '任务ID',
  `task_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '任务类型: API/UI',
  `notification_config_id` bigint NOT NULL COMMENT '通知配置ID',
  `is_enabled` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `notify_on_success` tinyint(1) NULL DEFAULT NULL COMMENT '成功时通知',
  `notify_on_failure` tinyint(1) NULL DEFAULT NULL COMMENT '失败时通知',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_config`(`notification_config_id` ASC) USING BTREE,
  INDEX `idx_task`(`task_id` ASC, `task_type` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '任务通知配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of task_notification_settings
-- ----------------------------


-- ----------------------------
-- Table structure for template_default_reviewers
-- ----------------------------
DROP TABLE IF EXISTS `template_default_reviewers`;
CREATE TABLE `template_default_reviewers`  (
  `template_id` bigint NOT NULL COMMENT '模板ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_template_user`(`template_id` ASC, `user_id` ASC) USING BTREE,
  INDEX `idx_template`(`template_id` ASC) USING BTREE,
  INDEX `idx_user`(`user_id` ASC) USING BTREE,
  INDEX `ix_template_default_reviewers_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of template_default_reviewers
-- ----------------------------


-- ----------------------------
-- Table structure for template_projects
-- ----------------------------
DROP TABLE IF EXISTS `template_projects`;
CREATE TABLE `template_projects`  (
  `template_id` bigint NOT NULL COMMENT '模板ID',
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_template_project`(`template_id` ASC, `project_id` ASC) USING BTREE,
  INDEX `idx_project`(`project_id` ASC) USING BTREE,
  INDEX `idx_template`(`template_id` ASC) USING BTREE,
  INDEX `ix_template_projects_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of template_projects
-- ----------------------------


-- ----------------------------
-- Table structure for test_case_reviews
-- ----------------------------
DROP TABLE IF EXISTS `test_case_reviews`;
CREATE TABLE `test_case_reviews`  (
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '评审标题',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '评审描述',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '评审状态: pending/in_progress/completed/cancelled',
  `priority` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '优先级: low/medium/high/urgent',
  `deadline` datetime NULL DEFAULT NULL COMMENT '截止日期',
  `template_id` bigint NULL DEFAULT NULL COMMENT '使用的模板ID',
  `creator_id` bigint NOT NULL COMMENT '创建人ID',
  `completed_at` datetime NULL DEFAULT NULL COMMENT '完成时间',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `updated_at` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_creator`(`creator_id` ASC) USING BTREE,
  INDEX `idx_project`(`project_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `ix_test_case_reviews_id`(`id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_case_reviews
-- ----------------------------


-- ----------------------------
-- Table structure for test_cases
-- ----------------------------
DROP TABLE IF EXISTS `test_cases`;
CREATE TABLE `test_cases`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `module_id` bigint NULL DEFAULT NULL COMMENT '模块ID',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用例标题',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用例描述',
  `preconditions` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '前置条件',
  `expected_result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '预期结果',
  `priority` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '优先级: low/medium/high/critical',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '状态: draft/active/deprecated',
  `test_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '类型: functional/integration/api/ui/performance/security',
  `tags` json NULL COMMENT '标签',
  `author_id` bigint NOT NULL COMMENT '作者ID',
  `assignee_id` bigint NULL DEFAULT NULL COMMENT '指派人ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_testcase_author`(`author_id` ASC) USING BTREE,
  INDEX `idx_testcase_project`(`project_id` ASC) USING BTREE,
  INDEX `idx_testcase_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '测试用例表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_cases
-- ----------------------------


-- ----------------------------
-- Table structure for test_case_steps
-- ----------------------------
DROP TABLE IF EXISTS `test_case_steps`;
CREATE TABLE `test_case_steps`  (
  `test_case_id` bigint NOT NULL COMMENT '测试用例ID',
  `step_number` int NOT NULL COMMENT '步骤序号',
  `action` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '操作',
  `expected` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '预期结果',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_step_case`(`test_case_id` ASC) USING BTREE,
  CONSTRAINT `test_case_steps_ibfk_1` FOREIGN KEY (`test_case_id`) REFERENCES `test_cases` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '测试用例步骤表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_case_steps
-- ----------------------------


-- ----------------------------
-- Table structure for testcase_generation_tasks
-- ----------------------------
DROP TABLE IF EXISTS `testcase_generation_tasks`;
CREATE TABLE `testcase_generation_tasks`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_id` bigint NULL DEFAULT NULL COMMENT '关联项目ID',
  `task_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务ID',
  `title` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务标题',
  `requirement_text` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '需求描述',
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '状态',
  `progress` int NULL DEFAULT NULL COMMENT '进度百分比',
  `output_mode` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '输出模式: stream/complete',
  `stream_buffer` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '流式输出缓冲区',
  `stream_position` int NULL DEFAULT NULL COMMENT '流式输出位置',
  `last_stream_update` datetime NULL DEFAULT NULL COMMENT '最后流式更新时间',
  `writer_model_config_id` bigint NULL DEFAULT NULL COMMENT '编写模型配置ID',
  `reviewer_model_config_id` bigint NULL DEFAULT NULL COMMENT '评审模型配置ID',
  `writer_prompt_config_id` bigint NULL DEFAULT NULL COMMENT '编写提示词配置ID',
  `reviewer_prompt_config_id` bigint NULL DEFAULT NULL COMMENT '评审提示词配置ID',
  `generated_test_cases` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '生成的测试用例',
  `review_feedback` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '评审反馈',
  `final_test_cases` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '最终测试用例',
  `generation_log` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '生成日志',
  `error_message` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '错误信息',
  `created_by` bigint NOT NULL COMMENT '创建者ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `completed_at` datetime NULL DEFAULT NULL COMMENT '完成时间',
  `is_saved_to_records` int NULL DEFAULT NULL COMMENT '是否已保存到记录',
  `saved_at` datetime NULL DEFAULT NULL COMMENT '保存到记录时间',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `task_id`(`task_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of testcase_generation_tasks
-- ----------------------------


-- ----------------------------
-- Table structure for testcase_templates
-- ----------------------------
DROP TABLE IF EXISTS `testcase_templates`;
CREATE TABLE `testcase_templates`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模板名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '模板描述',
  `template_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模板类型: ui/api/performance/main',
  `field_mapping` json NOT NULL COMMENT '字段映射配置',
  `is_default` int NULL DEFAULT NULL COMMENT '是否默认模板',
  `is_active` int NULL DEFAULT NULL COMMENT '是否启用',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` int NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '测试用例模板配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of testcase_templates
-- ----------------------------
INSERT INTO `testcase_templates` VALUES (1, '默认UI测试用例模板', '系统预置的默认UI测试用例模板，支持标准字段映射', 'ui', '{\"columns\": [{\"type\": \"string\", \"source\": \"用例ID\", \"target\": \"case_id\", \"required\": false}, {\"type\": \"string\", \"source\": \"测试标题\", \"target\": \"name\", \"required\": true}, {\"type\": \"text\", \"source\": \"前置条件\", \"target\": \"preconditions\", \"required\": false}, {\"type\": \"text\", \"source\": \"操作步骤\", \"target\": \"steps\", \"required\": true, \"parse_steps\": true}, {\"type\": \"text\", \"source\": \"预期结果\", \"target\": \"expected_result\", \"required\": true}, {\"type\": \"enum\", \"source\": \"优先级\", \"target\": \"priority\", \"values\": {\"P1\": \"high\", \"P2\": \"medium\", \"P3\": \"low\"}, \"default\": \"medium\"}]}', 1, 1, '2026-02-26 09:49:15', 1, '2026-03-02 14:06:02', 1, 1, NULL);
INSERT INTO `testcase_templates` VALUES (3, '默认主项目测试用例模板', '系统预置的默认主项目测试用例模板，支持标准字段映射', 'main', '{\"columns\": [{\"type\": \"string\", \"source\": \"用例ID\", \"target\": \"case_id\", \"required\": false}, {\"type\": \"string\", \"source\": \"测试标题\", \"target\": \"title\", \"required\": true}, {\"type\": \"text\", \"source\": \"用例描述\", \"target\": \"description\", \"required\": false}, {\"type\": \"text\", \"source\": \"前置条件\", \"target\": \"preconditions\", \"required\": false}, {\"type\": \"text\", \"source\": \"操作步骤\", \"target\": \"test_steps\", \"required\": false, \"description\": \"测试执行的详细步骤\"}, {\"type\": \"text\", \"source\": \"预期结果\", \"target\": \"expected_result\", \"required\": true}, {\"type\": \"enum\", \"source\": \"优先级\", \"target\": \"priority\", \"values\": {\"P1\": \"high\", \"P2\": \"medium\", \"P3\": \"low\"}, \"default\": \"medium\"}, {\"type\": \"enum\", \"source\": \"测试类型\", \"target\": \"test_type\", \"values\": {\"功能测试\": \"functional\", \"安全测试\": \"security\", \"性能测试\": \"performance\", \"兼容性测试\": \"compatibility\"}, \"default\": \"functional\"}], \"target_table\": \"test_cases\"}', 1, 1, '2026-02-26 10:28:26', 1, '2026-03-03 10:42:19', 1, 1, NULL);
INSERT INTO `testcase_templates` VALUES (4, 'API测试用例默认模板', 'API测试用例的默认字段映射模板', 'api', '{\"url\": \"请求URL\", \"body\": \"请求体\", \"name\": \"用例名称\", \"method\": \"请求方法\", \"params\": \"请求参数\", \"headers\": \"请求头\", \"assertions\": \"断言\", \"description\": \"用例描述\", \"expected_result\": \"预期结果\"}', 1, 1, '2026-02-26 11:20:52', 1, '2026-02-26 11:20:52', NULL, 1, NULL);


-- ----------------------------
-- Table structure for ui_element_groups
-- ----------------------------
DROP TABLE IF EXISTS `ui_element_groups`;
CREATE TABLE `ui_element_groups`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ui_project_id` bigint NOT NULL COMMENT '关联UI项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '分组名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '分组描述',
  `parent_id` bigint NULL DEFAULT NULL COMMENT '父分组ID',
  `order_num` int NULL DEFAULT NULL COMMENT '排序',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_element_groups_parent_id`(`parent_id` ASC) USING BTREE,
  INDEX `ix_ui_element_groups_ui_project_id`(`ui_project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_element_groups
-- ----------------------------


-- ----------------------------
-- Table structure for ui_elements
-- ----------------------------
DROP TABLE IF EXISTS `ui_elements`;
CREATE TABLE `ui_elements`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `group_id` bigint NOT NULL COMMENT '关联分组ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '元素名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '元素描述',
  `element_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '元素类型',
  `locator_strategy` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '定位策略',
  `locator_value` varchar(1000) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '定位器值',
  `backup_locators` json NULL COMMENT '备用定位器列表',
  `wait_time` int NULL DEFAULT NULL COMMENT '等待时间(毫秒)',
  `is_dynamic` tinyint(1) NULL DEFAULT NULL COMMENT '是否动态元素',
  `screenshot` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '元素截图路径',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_elements_group_id`(`group_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_elements
-- ----------------------------


-- ----------------------------
-- Table structure for ui_executions
-- ----------------------------
DROP TABLE IF EXISTS `ui_executions`;
CREATE TABLE `ui_executions`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ui_project_id` bigint NULL DEFAULT NULL COMMENT 'UI项目ID',
  `suite_id` bigint NULL DEFAULT NULL COMMENT '关联套件ID',
  `test_case_id` bigint NULL DEFAULT NULL COMMENT '关联用例ID',
  `engine_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行引擎',
  `browser_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '浏览器类型',
  `status` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行状态',
  `start_time` datetime NULL DEFAULT NULL COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `duration` int NULL DEFAULT NULL COMMENT '执行时长(毫秒)',
  `total_steps` int NULL DEFAULT NULL COMMENT '总步骤数',
  `passed_steps` int NULL DEFAULT NULL COMMENT '通过步骤数',
  `failed_steps` int NULL DEFAULT NULL COMMENT '失败步骤数',
  `error_message` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '错误信息',
  `screenshots` json NULL COMMENT '截图列表',
  `video_path` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '录屏路径',
  `logs` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '执行日志',
  `executed_by` bigint NULL DEFAULT NULL COMMENT '执行人ID',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_executions_start_time`(`start_time` ASC) USING BTREE,
  INDEX `ix_ui_executions_status`(`status` ASC) USING BTREE,
  INDEX `ix_ui_executions_suite_id`(`suite_id` ASC) USING BTREE,
  INDEX `ix_ui_executions_test_case_id`(`test_case_id` ASC) USING BTREE,
  INDEX `ix_ui_executions_ui_project_id`(`ui_project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_executions
-- ----------------------------


-- ----------------------------
-- Table structure for ui_page_object_elements
-- ----------------------------
DROP TABLE IF EXISTS `ui_page_object_elements`;
CREATE TABLE `ui_page_object_elements`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `page_object_id` bigint NOT NULL COMMENT '关联页面对象ID',
  `element_id` bigint NOT NULL COMMENT '关联元素ID',
  `method_name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '方法名称',
  `is_property` tinyint(1) NULL DEFAULT NULL COMMENT '是否为属性',
  `order_num` int NULL DEFAULT NULL COMMENT '排序',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_page_object_elements_element_id`(`element_id` ASC) USING BTREE,
  INDEX `ix_ui_page_object_elements_page_object_id`(`page_object_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_page_object_elements
-- ----------------------------


-- ----------------------------
-- Table structure for ui_page_objects
-- ----------------------------
DROP TABLE IF EXISTS `ui_page_objects`;
CREATE TABLE `ui_page_objects`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ui_project_id` bigint NOT NULL COMMENT '关联UI项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '页面对象名称',
  `class_name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '类名',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '页面对象描述',
  `url_pattern` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'URL模式',
  `template_code` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '生成的代码模板',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_page_objects_ui_project_id`(`ui_project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_page_objects
-- ----------------------------


-- ----------------------------
-- Table structure for ui_projects
-- ----------------------------
DROP TABLE IF EXISTS `ui_projects`;
CREATE TABLE `ui_projects`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `project_id` bigint NOT NULL COMMENT '关联项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT 'UI项目名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '项目描述',
  `base_url` varchar(500) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '基础URL',
  `browser_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '浏览器类型',
  `viewport_width` int NULL DEFAULT NULL COMMENT '视口宽度',
  `viewport_height` int NULL DEFAULT NULL COMMENT '视口高度',
  `timeout` int NULL DEFAULT NULL COMMENT '默认超时时间(毫秒)',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_projects_project_id`(`project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_projects
-- ----------------------------


-- ----------------------------
-- Table structure for ui_suite_cases
-- ----------------------------
DROP TABLE IF EXISTS `ui_suite_cases`;
CREATE TABLE `ui_suite_cases`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `suite_id` bigint NOT NULL COMMENT '关联套件ID',
  `test_case_id` bigint NOT NULL COMMENT '关联测试用例ID',
  `order_num` int NULL DEFAULT NULL COMMENT '执行顺序',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_suite_cases_suite_id`(`suite_id` ASC) USING BTREE,
  INDEX `ix_ui_suite_cases_test_case_id`(`test_case_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_suite_cases
-- ----------------------------


-- ----------------------------
-- Table structure for ui_test_cases
-- ----------------------------
DROP TABLE IF EXISTS `ui_test_cases`;
CREATE TABLE `ui_test_cases`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ui_project_id` bigint NOT NULL COMMENT '关联UI项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '用例名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '用例描述',
  `priority` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '优先级',
  `tags` json NULL COMMENT '标签列表',
  `preconditions` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '前置条件',
  `expected_result` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '预期结果',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_test_cases_ui_project_id`(`ui_project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 136 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_test_cases
-- ----------------------------
INSERT INTO `ui_test_cases` VALUES (1, 2, '更新后的登录功能测试', '测试用户登录功能', 'medium', '[\"登录\", \"冒烟测试\"]', '用户已注册', '登录成功', '2026-02-08 11:39:25', NULL, '2026-02-08 11:39:33', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (5, 6, 'TestCase', NULL, 'high', 'null', NULL, NULL, '2026-02-08 11:47:30', NULL, '2026-02-08 11:47:30', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (10, 11, '登录测试', NULL, 'high', 'null', NULL, NULL, '2026-02-08 12:09:39', NULL, '2026-02-08 12:09:39', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (13, 14, '更新后的测试用例', '测试用户登录功能', 'high', 'null', NULL, NULL, '2026-02-08 12:44:58', NULL, '2026-02-08 12:45:05', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (23, 25, '44', '44', 'medium', '[\"44\"]', '44', '44', '2026-02-08 14:03:37', NULL, '2026-02-08 14:03:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (40, 1, '验证用户名长度下限（4字符）正常登录', 'LOGIN_001', 'high', NULL, '用户已注册，用户名为4字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (41, 1, '验证用户名长度上限（20字符）正常登录', 'LOGIN_002', 'high', NULL, '用户已注册，用户名为20字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (42, 1, '验证用户名长度为3字符时无法登录', 'LOGIN_003', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (43, 1, '验证用户名长度为21字符时无法登录', 'LOGIN_004', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (44, 1, '验证用户名为空时无法登录', 'LOGIN_005', 'high', NULL, '在登录页', '提示“用户名不能为空”，登录失败', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (45, 1, '验证密码长度下限（6字符）正常登录', 'LOGIN_006', 'high', NULL, '用户已注册，密码为6字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (46, 1, '验证密码长度上限（20字符）正常登录', 'LOGIN_007', 'high', NULL, '用户已注册，密码为20字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (47, 1, '验证密码长度为5字符时无法登录', 'LOGIN_008', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:12:26', 1, '2026-02-26 10:12:26', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (48, 1, '验证密码长度为21字符时无法登录', 'LOGIN_009', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (49, 1, '验证密码为空时无法登录', 'LOGIN_010', 'high', NULL, '在登录页', '提示“密码不能为空”，登录失败', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (50, 1, '验证用户名和密码均正确时成功跳转首页', 'LOGIN_011', 'high', NULL, '用户已注册', '成功跳转至首页，URL变为 /home', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (51, 1, '验证用户名错误时显示错误提示', 'LOGIN_012', 'high', NULL, '至少存在两个已注册用户（A和B）', '显示“用户名或密码错误”', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (52, 1, '验证密码错误时显示错误提示', 'LOGIN_013', 'high', NULL, '用户已注册', '显示“用户名或密码错误”', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (53, 1, '验证用户名和密码均错误时显示错误提示', 'LOGIN_014', 'high', NULL, '在登录页', '显示“用户名或密码错误”', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (54, 1, '验证勾选“记住密码”后7天内免密登录', 'LOGIN_015', 'medium', NULL, '用户已注册', '用户名和密码自动填充，可直接登录', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (55, 1, '验证未勾选“记住密码”则不保存凭证', 'LOGIN_016', 'medium', NULL, '用户已注册', '用户名和密码字段为空', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (56, 1, '验证“记住密码”超过7天后失效', 'LOGIN_017', 'medium', NULL, '用户已注册并已勾选记住密码', '用户名和密码未自动填充', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (57, 1, '验证第1次登录失败不触发锁定', 'LOGIN_018', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (58, 1, '验证第2次连续登录失败不触发锁定', 'LOGIN_019', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定，可继续尝试', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (59, 1, '验证第3次连续登录失败后账号锁定', 'LOGIN_020', 'high', NULL, '用户已注册', '第三次失败后提示“账号已锁定，请30分钟后重试”，登录按钮前端禁用且后端拒绝请求', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (60, 1, '验证账号锁定后30分钟内无法登录（即使密码正确）', 'LOGIN_021', 'high', NULL, '用户账号已被锁定', '提示“账号已锁定，请30分钟后重试”，无法登录', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (61, 1, '验证账号锁定30分钟后自动解锁', 'LOGIN_022', 'high', NULL, '用户账号已被锁定', '成功登录并跳转首页，URL为 /home', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (62, 1, '验证非连续失败（中间成功）不累计失败次数', 'LOGIN_023', 'medium', NULL, '用户已注册', '第三次失败后仅计1次失败，账号未锁定', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (63, 1, '验证点击“找回密码”跳转至找回密码页面', 'LOGIN_024', 'medium', NULL, '在登录页', '页面跳转至 /forgot-password，URL正确', '2026-02-26 10:12:27', 1, '2026-02-26 10:12:27', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (64, 1, '验证用户名长度下限（4字符）正常登录', 'LOGIN_001', 'high', NULL, '用户已注册，用户名为4字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (65, 1, '验证用户名长度上限（20字符）正常登录', 'LOGIN_002', 'high', NULL, '用户已注册，用户名为20字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (66, 1, '验证用户名长度为3字符时无法登录', 'LOGIN_003', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (67, 1, '验证用户名长度为21字符时无法登录', 'LOGIN_004', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (68, 1, '验证用户名为空时无法登录', 'LOGIN_005', 'high', NULL, '在登录页', '提示“用户名不能为空”，登录失败', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (69, 1, '验证密码长度下限（6字符）正常登录', 'LOGIN_006', 'high', NULL, '用户已注册，密码为6字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (70, 1, '验证密码长度上限（20字符）正常登录', 'LOGIN_007', 'high', NULL, '用户已注册，密码为20字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (71, 1, '验证密码长度为5字符时无法登录', 'LOGIN_008', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (72, 1, '验证密码长度为21字符时无法登录', 'LOGIN_009', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (73, 1, '验证密码为空时无法登录', 'LOGIN_010', 'high', NULL, '在登录页', '提示“密码不能为空”，登录失败', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (74, 1, '验证用户名和密码均正确时成功跳转首页', 'LOGIN_011', 'high', NULL, '用户已注册', '成功跳转至首页，URL变为 /home', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (75, 1, '验证用户名错误时显示错误提示', 'LOGIN_012', 'high', NULL, '至少存在两个已注册用户（A和B）', '显示“用户名或密码错误”', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (76, 1, '验证密码错误时显示错误提示', 'LOGIN_013', 'high', NULL, '用户已注册', '显示“用户名或密码错误”', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (77, 1, '验证用户名和密码均错误时显示错误提示', 'LOGIN_014', 'high', NULL, '在登录页', '显示“用户名或密码错误”', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (78, 1, '验证勾选“记住密码”后7天内免密登录', 'LOGIN_015', 'medium', NULL, '用户已注册', '用户名和密码自动填充，可直接登录', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (79, 1, '验证未勾选“记住密码”则不保存凭证', 'LOGIN_016', 'medium', NULL, '用户已注册', '用户名和密码字段为空', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (80, 1, '验证“记住密码”超过7天后失效', 'LOGIN_017', 'medium', NULL, '用户已注册并已勾选记住密码', '用户名和密码未自动填充', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (81, 1, '验证第1次登录失败不触发锁定', 'LOGIN_018', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (82, 1, '验证第2次连续登录失败不触发锁定', 'LOGIN_019', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定，可继续尝试', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (83, 1, '验证第3次连续登录失败后账号锁定', 'LOGIN_020', 'high', NULL, '用户已注册', '第三次失败后提示“账号已锁定，请30分钟后重试”，登录按钮前端禁用且后端拒绝请求', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (84, 1, '验证账号锁定后30分钟内无法登录（即使密码正确）', 'LOGIN_021', 'high', NULL, '用户账号已被锁定', '提示“账号已锁定，请30分钟后重试”，无法登录', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (85, 1, '验证账号锁定30分钟后自动解锁', 'LOGIN_022', 'high', NULL, '用户账号已被锁定', '成功登录并跳转首页，URL为 /home', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (86, 1, '验证非连续失败（中间成功）不累计失败次数', 'LOGIN_023', 'medium', NULL, '用户已注册', '第三次失败后仅计1次失败，账号未锁定', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (87, 1, '验证点击“找回密码”跳转至找回密码页面', 'LOGIN_024', 'medium', NULL, '在登录页', '页面跳转至 /forgot-password，URL正确', '2026-02-26 10:14:44', 1, '2026-02-26 10:14:44', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (88, 1, '验证用户名长度下限（4字符）正常登录', 'LOGIN_001', 'high', NULL, '用户已注册，用户名为4字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (89, 1, '验证用户名长度上限（20字符）正常登录', 'LOGIN_002', 'high', NULL, '用户已注册，用户名为20字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (90, 1, '验证用户名长度为3字符时无法登录', 'LOGIN_003', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (91, 1, '验证用户名长度为21字符时无法登录', 'LOGIN_004', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (92, 1, '验证用户名为空时无法登录', 'LOGIN_005', 'high', NULL, '在登录页', '提示“用户名不能为空”，登录失败', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (93, 1, '验证密码长度下限（6字符）正常登录', 'LOGIN_006', 'high', NULL, '用户已注册，密码为6字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (94, 1, '验证密码长度上限（20字符）正常登录', 'LOGIN_007', 'high', NULL, '用户已注册，密码为20字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (95, 1, '验证密码长度为5字符时无法登录', 'LOGIN_008', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (96, 1, '验证密码长度为21字符时无法登录', 'LOGIN_009', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (97, 1, '验证密码为空时无法登录', 'LOGIN_010', 'high', NULL, '在登录页', '提示“密码不能为空”，登录失败', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (98, 1, '验证用户名和密码均正确时成功跳转首页', 'LOGIN_011', 'high', NULL, '用户已注册', '成功跳转至首页，URL变为 /home', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (99, 1, '验证用户名错误时显示错误提示', 'LOGIN_012', 'high', NULL, '至少存在两个已注册用户（A和B）', '显示“用户名或密码错误”', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (100, 1, '验证密码错误时显示错误提示', 'LOGIN_013', 'high', NULL, '用户已注册', '显示“用户名或密码错误”', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (101, 1, '验证用户名和密码均错误时显示错误提示', 'LOGIN_014', 'high', NULL, '在登录页', '显示“用户名或密码错误”', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (102, 1, '验证勾选“记住密码”后7天内免密登录', 'LOGIN_015', 'medium', NULL, '用户已注册', '用户名和密码自动填充，可直接登录', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (103, 1, '验证未勾选“记住密码”则不保存凭证', 'LOGIN_016', 'medium', NULL, '用户已注册', '用户名和密码字段为空', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (104, 1, '验证“记住密码”超过7天后失效', 'LOGIN_017', 'medium', NULL, '用户已注册并已勾选记住密码', '用户名和密码未自动填充', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (105, 1, '验证第1次登录失败不触发锁定', 'LOGIN_018', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (106, 1, '验证第2次连续登录失败不触发锁定', 'LOGIN_019', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定，可继续尝试', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (107, 1, '验证第3次连续登录失败后账号锁定', 'LOGIN_020', 'high', NULL, '用户已注册', '第三次失败后提示“账号已锁定，请30分钟后重试”，登录按钮前端禁用且后端拒绝请求', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (108, 1, '验证账号锁定后30分钟内无法登录（即使密码正确）', 'LOGIN_021', 'high', NULL, '用户账号已被锁定', '提示“账号已锁定，请30分钟后重试”，无法登录', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (109, 1, '验证账号锁定30分钟后自动解锁', 'LOGIN_022', 'high', NULL, '用户账号已被锁定', '成功登录并跳转首页，URL为 /home', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (110, 1, '验证非连续失败（中间成功）不累计失败次数', 'LOGIN_023', 'medium', NULL, '用户已注册', '第三次失败后仅计1次失败，账号未锁定', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (111, 1, '验证点击“找回密码”跳转至找回密码页面', 'LOGIN_024', 'medium', NULL, '在登录页', '页面跳转至 /forgot-password，URL正确', '2026-02-26 10:15:34', 1, '2026-02-26 10:15:34', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (112, 1, '验证用户名长度下限（4字符）正常登录', 'LOGIN_001', 'high', NULL, '用户已注册，用户名为4字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (113, 1, '验证用户名长度上限（20字符）正常登录', 'LOGIN_002', 'high', NULL, '用户已注册，用户名为20字符，密码正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (114, 1, '验证用户名长度为3字符时无法登录', 'LOGIN_003', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (115, 1, '验证用户名长度为21字符时无法登录', 'LOGIN_004', 'high', NULL, '在登录页', '提示“用户名长度应为4-20个字符”，登录失败', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (116, 1, '验证用户名为空时无法登录', 'LOGIN_005', 'high', NULL, '在登录页', '提示“用户名不能为空”，登录失败', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (117, 1, '验证密码长度下限（6字符）正常登录', 'LOGIN_006', 'high', NULL, '用户已注册，密码为6字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (118, 1, '验证密码长度上限（20字符）正常登录', 'LOGIN_007', 'high', NULL, '用户已注册，密码为20字符且正确', '成功跳转至首页，URL为 /home', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (119, 1, '验证密码长度为5字符时无法登录', 'LOGIN_008', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (120, 1, '验证密码长度为21字符时无法登录', 'LOGIN_009', 'high', NULL, '在登录页', '提示“密码长度应为6-20个字符”，登录失败', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (121, 1, '验证密码为空时无法登录', 'LOGIN_010', 'high', NULL, '在登录页', '提示“密码不能为空”，登录失败', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (122, 1, '验证用户名和密码均正确时成功跳转首页', 'LOGIN_011', 'high', NULL, '用户已注册', '成功跳转至首页，URL变为 /home', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (123, 1, '验证用户名错误时显示错误提示', 'LOGIN_012', 'high', NULL, '至少存在两个已注册用户（A和B）', '显示“用户名或密码错误”', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (124, 1, '验证密码错误时显示错误提示', 'LOGIN_013', 'high', NULL, '用户已注册', '显示“用户名或密码错误”', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (125, 1, '验证用户名和密码均错误时显示错误提示', 'LOGIN_014', 'high', NULL, '在登录页', '显示“用户名或密码错误”', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (126, 1, '验证勾选“记住密码”后7天内免密登录', 'LOGIN_015', 'medium', NULL, '用户已注册', '用户名和密码自动填充，可直接登录', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (127, 1, '验证未勾选“记住密码”则不保存凭证', 'LOGIN_016', 'medium', NULL, '用户已注册', '用户名和密码字段为空', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (128, 1, '验证“记住密码”超过7天后失效', 'LOGIN_017', 'medium', NULL, '用户已注册并已勾选记住密码', '用户名和密码未自动填充', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (129, 1, '验证第1次登录失败不触发锁定', 'LOGIN_018', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (130, 1, '验证第2次连续登录失败不触发锁定', 'LOGIN_019', 'high', NULL, '用户已注册', '显示“用户名或密码错误”，账号未锁定，可继续尝试', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (131, 1, '验证第3次连续登录失败后账号锁定', 'LOGIN_020', 'high', NULL, '用户已注册', '第三次失败后提示“账号已锁定，请30分钟后重试”，登录按钮前端禁用且后端拒绝请求', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (132, 1, '验证账号锁定后30分钟内无法登录（即使密码正确）', 'LOGIN_021', 'high', NULL, '用户账号已被锁定', '提示“账号已锁定，请30分钟后重试”，无法登录', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (133, 1, '验证账号锁定30分钟后自动解锁', 'LOGIN_022', 'high', NULL, '用户账号已被锁定', '成功登录并跳转首页，URL为 /home', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (134, 1, '验证非连续失败（中间成功）不累计失败次数', 'LOGIN_023', 'medium', NULL, '用户已注册', '第三次失败后仅计1次失败，账号未锁定', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);
INSERT INTO `ui_test_cases` VALUES (135, 1, '验证点击“找回密码”跳转至找回密码页面', 'LOGIN_024', 'medium', NULL, '在登录页', '页面跳转至 /forgot-password，URL正确', '2026-02-26 10:16:37', 1, '2026-02-26 10:16:37', NULL, 1, NULL);


-- ----------------------------
-- Table structure for ui_test_steps
-- ----------------------------
DROP TABLE IF EXISTS `ui_test_steps`;
CREATE TABLE `ui_test_steps`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `test_case_id` bigint NOT NULL COMMENT '关联测试用例ID',
  `step_number` int NOT NULL COMMENT '步骤序号',
  `action_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '操作类型',
  `element_id` bigint NULL DEFAULT NULL COMMENT '关联元素ID',
  `action_value` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '操作值',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '步骤描述',
  `assertion_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '断言类型',
  `assertion_value` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '断言值',
  `screenshot_on_failure` tinyint(1) NULL DEFAULT NULL COMMENT '失败时截图',
  `continue_on_failure` tinyint(1) NULL DEFAULT NULL COMMENT '失败时继续',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_test_steps_test_case_id`(`test_case_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_test_steps
-- ----------------------------
INSERT INTO `ui_test_steps` VALUES (1, 136, 1, 'click', 20, '', '', NULL, '', 1, 0, '2026-04-01 11:40:42', NULL, '2026-04-01 11:40:42', NULL, 1, NULL);


-- ----------------------------
-- Table structure for ui_test_suites
-- ----------------------------
DROP TABLE IF EXISTS `ui_test_suites`;
CREATE TABLE `ui_test_suites`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `ui_project_id` bigint NOT NULL COMMENT '关联UI项目ID',
  `name` varchar(200) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '套件名称',
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL COMMENT '套件描述',
  `engine_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '执行引擎',
  `browser_type` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '浏览器类型',
  `headless` tinyint(1) NULL DEFAULT NULL COMMENT '无头模式',
  `parallel` tinyint(1) NULL DEFAULT NULL COMMENT '并行执行',
  `max_workers` int NULL DEFAULT NULL COMMENT '最大并行数',
  `creation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NULL DEFAULT NULL COMMENT '启用标志',
  `trace_id` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '追踪ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_ui_test_suites_ui_project_id`(`ui_project_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ui_test_suites
-- ----------------------------


-- ----------------------------
-- Table structure for unified_notification_configs
-- ----------------------------
DROP TABLE IF EXISTS `unified_notification_configs`;
CREATE TABLE `unified_notification_configs`  (
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '配置名称',
  `config_type` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '配置类型: webhook_feishu/webhook_wechat/webhook_dingtalk/telegram/email',
  `notification_config` json NULL COMMENT '通知配置信息(JSON格式，根据不同类型存储不同字段)',
  `is_default` tinyint(1) NULL DEFAULT NULL COMMENT '是否默认配置',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否启用',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_config_type`(`config_type` ASC) USING BTREE,
  INDEX `idx_is_active`(`is_active` ASC) USING BTREE,
  INDEX `idx_is_default`(`is_default` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '统一通知配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of unified_notification_configs
-- ----------------------------


-- ----------------------------
-- Table structure for user_role
-- ----------------------------
DROP TABLE IF EXISTS `user_role`;
CREATE TABLE `user_role`  (
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `role_id` bigint NOT NULL COMMENT '角色ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `ix_user_role_role_id`(`role_id` ASC) USING BTREE,
  INDEX `ix_user_role_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 17 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of user_role
-- ----------------------------
INSERT INTO `user_role` VALUES (2, 3, 2, '2026-01-30 17:35:05', 1, NULL, NULL, 1, NULL);
INSERT INTO `user_role` VALUES (3, 4, 3, '2026-01-30 17:35:05', 1, NULL, NULL, 1, NULL);
INSERT INTO `user_role` VALUES (1, 1, 4, '2026-01-30 17:35:29', 1, NULL, NULL, 1, NULL);
INSERT INTO `user_role` VALUES (7, 6, 7, '2026-01-30 18:02:56', 1, '2026-01-30 18:02:56', 1, 1, NULL);
INSERT INTO `user_role` VALUES (8, 8, 10, '2026-01-30 18:22:57', 1, '2026-01-30 18:22:57', 1, 1, NULL);
INSERT INTO `user_role` VALUES (21, 1, 11, '2026-02-04 18:35:21', 21, '2026-02-04 18:35:21', NULL, 1, NULL);
INSERT INTO `user_role` VALUES (22, 1, 12, '2026-02-04 18:40:41', 22, '2026-02-04 18:40:41', NULL, 1, NULL);
INSERT INTO `user_role` VALUES (23, 1, 13, '2026-02-04 18:43:16', 23, '2026-02-04 18:43:16', NULL, 1, NULL);
INSERT INTO `user_role` VALUES (24, 1, 14, '2026-02-04 18:56:00', 24, '2026-02-04 18:56:00', NULL, 1, NULL);
INSERT INTO `user_role` VALUES (25, 1, 15, '2026-02-04 21:05:48', 25, '2026-02-04 21:05:48', NULL, 1, NULL);
INSERT INTO `user_role` VALUES (29, 1, 16, '2026-02-05 09:15:55', 29, '2026-02-05 09:15:55', NULL, 1, NULL);


-- ----------------------------
-- Table structure for versions
-- ----------------------------
DROP TABLE IF EXISTS `versions`;
CREATE TABLE `versions`  (
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '版本名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '版本描述',
  `is_baseline` tinyint(1) NULL DEFAULT NULL COMMENT '是否基线版本',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_version_baseline`(`is_baseline` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '版本表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of versions
-- ----------------------------
INSERT INTO `versions` VALUES ('1.0.0', '', 1, 1, '2026-04-01 11:30:50', 1, '2026-04-01 11:30:50', NULL, 1, NULL);


-- ----------------------------
-- Table structure for project_versions
-- ----------------------------
DROP TABLE IF EXISTS `project_versions`;
CREATE TABLE `project_versions`  (
  `project_id` bigint NOT NULL COMMENT '项目ID',
  `version_id` bigint NOT NULL COMMENT '版本ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_pv_project`(`project_id` ASC) USING BTREE,
  INDEX `idx_pv_version`(`version_id` ASC) USING BTREE,
  CONSTRAINT `project_versions_ibfk_1` FOREIGN KEY (`version_id`) REFERENCES `versions` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '项目版本关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of project_versions
-- ----------------------------


-- ----------------------------
-- Table structure for test_case_versions
-- ----------------------------
DROP TABLE IF EXISTS `test_case_versions`;
CREATE TABLE `test_case_versions`  (
  `test_case_id` bigint NOT NULL COMMENT '测试用例ID',
  `version_id` bigint NOT NULL COMMENT '版本ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_tcv_case`(`test_case_id` ASC) USING BTREE,
  INDEX `idx_tcv_version`(`version_id` ASC) USING BTREE,
  CONSTRAINT `test_case_versions_ibfk_1` FOREIGN KEY (`test_case_id`) REFERENCES `test_cases` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `test_case_versions_ibfk_2` FOREIGN KEY (`version_id`) REFERENCES `versions` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用例版本关联表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of test_case_versions
-- ----------------------------


-- ----------------------------
-- Table structure for web_management_element_menus
-- ----------------------------
DROP TABLE IF EXISTS `web_management_element_menus`;
CREATE TABLE `web_management_element_menus`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '元素菜单名称',
  `pid` bigint NOT NULL COMMENT '父菜单ID',
  `type` int NOT NULL COMMENT '菜单类型',
  `element_id` bigint NULL DEFAULT NULL COMMENT '元素ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_element_menus
-- ----------------------------
INSERT INTO `web_management_element_menus` VALUES ('默认分组', 0, 0, NULL, 1, '2026-03-14 12:17:27', NULL, NULL, NULL, 1, NULL);
INSERT INTO `web_management_element_menus` VALUES ('测试一下', 2, 2, 4, 6, '2026-04-09 10:38:50', 1, '2026-04-09 10:45:02', NULL, 0, NULL);


-- ----------------------------
-- Table structure for web_management_elements
-- ----------------------------
DROP TABLE IF EXISTS `web_management_elements`;
CREATE TABLE `web_management_elements`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '元素名称',
  `element` json NOT NULL COMMENT '元素选择器信息',
  `menu_id` bigint NULL DEFAULT NULL COMMENT '菜单ID',
  `element_type` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '元素类型',
  `locator_strategy` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '定位策略',
  `locator_value` varchar(1000) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '定位器值',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_elements
-- ----------------------------
INSERT INTO `web_management_elements` VALUES ('测试一下', '{\"type\": 1, \"value\": \"99\", \"browser\": 1, \"locator_type\": 1, \"locator_role_type\": 1, \"locator_select_type\": 1}', 2, NULL, NULL, NULL, 4, '2026-04-09 10:38:50', 1, '2026-04-09 10:45:02', NULL, 0, NULL);


-- ----------------------------
-- Table structure for web_management_groups
-- ----------------------------
DROP TABLE IF EXISTS `web_management_groups`;
CREATE TABLE `web_management_groups`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '脚本集名称',
  `script` json NULL COMMENT '脚本集配置',
  `description` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '脚本集描述',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 19 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_groups
-- ----------------------------
INSERT INTO `web_management_groups` VALUES ('UI自动化测试场景', '[{\"id\": 2, \"pid\": 1, \"name\": \"打开百度\", \"type\": 2}]', '', 1, '2026-04-03 17:01:50', 1, '2026-04-08 16:45:01', NULL, 0, NULL);
INSERT INTO `web_management_groups` VALUES ('00', '[{\"id\": 2, \"pid\": 1, \"name\": \"打开百度\", \"type\": 2}]', '', 2, '2026-04-09 10:36:47', 1, '2026-04-09 10:37:43', NULL, 0, NULL);
INSERT INTO `web_management_groups` VALUES ('999', '[{\"id\": 8, \"name\": \"888\", \"type\": 2}]', '', 18, '2026-04-20 13:44:21', 1, '2026-04-20 13:44:21', NULL, 1, NULL);


-- ----------------------------
-- Table structure for web_management_menus
-- ----------------------------
DROP TABLE IF EXISTS `web_management_menus`;
CREATE TABLE `web_management_menus`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '菜单名称',
  `pid` bigint NOT NULL COMMENT '父菜单ID',
  `type` int NOT NULL COMMENT '菜单类型: 0-文件夹, 1-脚本组, 2-脚本',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 10 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_menus
-- ----------------------------
INSERT INTO `web_management_menus` VALUES ('默认分组', 0, 0, 1, '2026-03-14 12:17:27', NULL, NULL, NULL, 1, NULL);
INSERT INTO `web_management_menus` VALUES ('888', 1, 2, 8, '2026-04-14 16:24:16', 1, '2026-04-14 16:24:16', NULL, 1, NULL);
INSERT INTO `web_management_menus` VALUES ('测试', 1, 1, 9, '2026-04-17 11:28:48', 1, '2026-04-17 11:28:48', NULL, 1, NULL);


-- ----------------------------
-- Table structure for web_management_result_details
-- ----------------------------
DROP TABLE IF EXISTS `web_management_result_details`;
CREATE TABLE `web_management_result_details`  (
  `name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '脚本名称',
  `result_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行ID',
  `browser` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '浏览器类型',
  `log` text CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行日志',
  `status` int NOT NULL COMMENT '执行状态: 0-失败, 1-成功',
  `before_img` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '执行前截图',
  `after_img` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '执行后截图',
  `video` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT '视频地址',
  `trace` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'Playwright trace文件',
  `assert_result` json NOT NULL COMMENT '断言结果',
  `menu_id` bigint NULL DEFAULT NULL COMMENT '脚本菜单ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 88 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_result_details
-- ----------------------------
INSERT INTO `web_management_result_details` VALUES ('打开', '1775635068864', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 2, 15, '2026-04-08 15:58:44', NULL, '2026-04-08 15:58:44', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1775635068864', '1', '执行结束', 1, '', '', '', '/media/playwright/1775635068864/1/trace.zip', '[]', NULL, 16, '2026-04-08 15:58:57', NULL, '2026-04-08 15:58:57', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776155078059', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 70, '2026-04-14 16:25:24', NULL, '2026-04-14 16:25:24', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776155078059', '1', '执行结束', 1, '', '', '', '/media/playwright/1776155078059/1/trace.zip', '[]', NULL, 71, '2026-04-14 16:25:25', NULL, '2026-04-14 16:25:25', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776155146397', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 72, '2026-04-14 16:25:57', NULL, '2026-04-14 16:25:57', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776155146397', '1', '执行结束', 1, '', '', '', '/media/playwright/1776155146397/1/trace.zip', '[]', NULL, 73, '2026-04-14 16:25:57', NULL, '2026-04-14 16:25:57', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776155190504', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 74, '2026-04-14 16:26:40', NULL, '2026-04-14 16:26:40', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776155190504', '1', '执行结束', 1, '', '', '', '/media/playwright/1776155190504/1/trace.zip', '[]', NULL, 75, '2026-04-14 16:26:40', NULL, '2026-04-14 16:26:40', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776155207071', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 76, '2026-04-14 16:26:57', NULL, '2026-04-14 16:26:57', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776155207071', '1', '执行结束', 1, '', '', '', '/media/playwright/1776155207071/1/trace.zip', '[]', NULL, 77, '2026-04-14 16:26:58', NULL, '2026-04-14 16:26:58', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776156319827', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 78, '2026-04-14 16:46:00', NULL, '2026-04-14 16:46:00', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776156319827', '1', '执行结束', 1, '', '', '', '/media/playwright/1776156319827/1/trace.zip', '[]', NULL, 79, '2026-04-14 16:46:03', NULL, '2026-04-14 16:46:03', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776156375014', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 80, '2026-04-14 16:47:34', NULL, '2026-04-14 16:47:34', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776156375014', '1', '执行结束', 1, '', '', '', '/media/playwright/1776156375014/1/trace.zip', '[]', NULL, 81, '2026-04-14 16:47:38', NULL, '2026-04-14 16:47:38', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776388760585', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 82, '2026-04-17 09:21:33', NULL, '2026-04-17 09:21:33', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776388760585', '1', '执行结束', 1, '', '', '', '/media/playwright/1776388760585/1/trace.zip', '[]', NULL, 83, '2026-04-17 09:21:36', NULL, '2026-04-17 09:21:36', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776388916048', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 84, '2026-04-17 09:22:48', NULL, '2026-04-17 09:22:48', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776388916048', '1', '执行结束', 1, '', '', '', '/media/playwright/1776388916048/1/trace.zip', '[]', NULL, 85, '2026-04-17 09:22:54', NULL, '2026-04-17 09:22:54', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('打开', '1776664071084', '1', '元素https://www.baidu.com识别失败，未找到元素', 0, '', '', '', '', '[]', 8, 86, '2026-04-20 13:49:50', NULL, '2026-04-20 13:49:50', NULL, 1, NULL);
INSERT INTO `web_management_result_details` VALUES ('执行结束', '1776664071084', '1', '执行结束', 1, '', '', '', '/media/playwright/1776664071084/1/trace.zip', '[]', NULL, 87, '2026-04-20 13:49:57', NULL, '2026-04-20 13:49:57', NULL, 1, NULL);


-- ----------------------------
-- Table structure for web_management_result_lists
-- ----------------------------
DROP TABLE IF EXISTS `web_management_result_lists`;
CREATE TABLE `web_management_result_lists`  (
  `task_name` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '任务名称',
  `result_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL COMMENT '执行ID',
  `script_list` json NOT NULL COMMENT '脚本列表',
  `browser_list` json NOT NULL COMMENT '浏览器列表',
  `result` json NOT NULL COMMENT '执行结果',
  `pid_list` json NULL COMMENT '执行进程PID列表（兼容旧 stop_web_script）',
  `start_time` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '结束时间',
  `status` int NULL DEFAULT NULL COMMENT '执行状态: 0-执行中, 1-完成',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 48 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_result_lists
-- ----------------------------
INSERT INTO `web_management_result_lists` VALUES ('UI自动化测试场景', '1775635068864', '[{\"id\": 2, \"pid\": 1, \"name\": \"打开百度\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[1608]', '2026-04-08 15:57:49', '2026-04-08 15:59:02', 1, 8, '2026-04-08 15:57:49', 1, '2026-04-08 15:59:34', NULL, 0, NULL);
INSERT INTO `web_management_result_lists` VALUES ('00', '1776155078059', '[{\"id\": 8, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[16908]', '2026-04-14 16:24:38', '2026-04-14 16:25:26', 1, 39, '2026-04-14 16:24:38', 1, '2026-04-14 16:25:26', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('999', '1776155146397', '[{\"id\": 8, \"pid\": 1, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[27388]', '2026-04-14 16:25:46', '2026-04-14 16:25:58', 1, 40, '2026-04-14 16:25:46', 1, '2026-04-14 16:25:58', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('999', '1776155190504', '[{\"id\": 8, \"pid\": 1, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[31088]', '2026-04-14 16:26:31', '2026-04-14 16:26:41', 1, 41, '2026-04-14 16:26:30', 1, '2026-04-14 16:26:41', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('99', '1776155207071', '[{\"id\": 8, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[2952]', '2026-04-14 16:26:47', '2026-04-14 16:26:59', 1, 42, '2026-04-14 16:26:47', 1, '2026-04-14 16:26:58', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('00', '1776156319827', '[{\"id\": 8, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[24160]', '2026-04-14 16:45:20', '2026-04-14 16:46:05', 1, 43, '2026-04-14 16:45:20', 1, '2026-04-14 16:46:05', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('999', '1776156375014', '[{\"id\": 8, \"pid\": 1, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[27776]', '2026-04-14 16:46:15', '2026-04-14 16:47:42', 1, 44, '2026-04-14 16:46:15', 1, '2026-04-14 16:47:41', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('99', '1776388760585', '[{\"id\": 8, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[6504]', '2026-04-17 09:19:22', '2026-04-17 09:21:38', 1, 45, '2026-04-17 09:19:22', 1, '2026-04-17 09:21:38', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('999', '1776388916048', '[{\"id\": 8, \"pid\": 1, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[22876]', '2026-04-17 09:21:56', '2026-04-17 09:22:57', 1, 46, '2026-04-17 09:21:56', 1, '2026-04-17 09:22:56', NULL, 1, NULL);
INSERT INTO `web_management_result_lists` VALUES ('999', '1776664071084', '[{\"id\": 8, \"name\": \"888\", \"type\": 2}]', '[1]', '[{\"total\": 1, \"browser\": 1, \"run_true\": 0, \"run_false\": 1}]', '[18932]', '2026-04-20 13:47:53', '2026-04-20 13:50:04', 1, 47, '2026-04-20 13:47:53', 1, '2026-04-20 13:50:04', NULL, 1, NULL);


-- ----------------------------
-- Table structure for web_management_scripts
-- ----------------------------
DROP TABLE IF EXISTS `web_management_scripts`;
CREATE TABLE `web_management_scripts`  (
  `script` json NOT NULL COMMENT '脚本步骤',
  `menu_id` bigint NOT NULL COMMENT '菜单ID',
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除, 0 删除 1 非删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `menu_id`(`menu_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 7 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of web_management_scripts
-- ----------------------------
INSERT INTO `web_management_scripts` VALUES ('[{"name": "打开", "type": 0, "action": {"type": 1, "input": "", "assert": [], "target": "", "cookies": [], "element": "https://www.baidu.com", "locator": 1, "timeout": 15, "up_type": 1, "sway_type": 1, "target_id": "", "wait_time": 1, "after_wait": 1, "element_id": null, "before_wait": 1, "target_type": 1, "localstorage": [], "locator_select": 1, "target_locator": 1, "target_locator_select": 1}, "status": true, "children": []}]', 8, 6, '2026-04-14 16:24:16', 1, '2026-04-14 16:24:31', NULL, 1, NULL);

-- ----------------------------
-- Table structure for perf_config_machines
-- ----------------------------
DROP TABLE IF EXISTS `perf_config_machines`;
CREATE TABLE `perf_config_machines`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '压力机名称',
  `machine_type` int NOT NULL COMMENT '机器类型：1-Master 2-Slave 3-单机',
  `status` int NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `ip` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '机器IP或DNS域名；物理机/云主机填IP，K8S Pod填Headless Service DNS',
  `ssh_port` int NOT NULL DEFAULT 22 COMMENT 'SSH端口，默认22',
  `rmi_port` int NOT NULL COMMENT 'JMeter RMI监听端口，默认1099',
  `monitor` int NULL DEFAULT NULL COMMENT 'Prometheus监听端口',
  `max_concurrency` int NULL DEFAULT NULL COMMENT '最大并发数',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '备注',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除：0删除 1未删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '压力机配置' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of perf_config_machines
-- ----------------------------


-- ----------------------------
-- Table structure for perf_config_params
-- ----------------------------
DROP TABLE IF EXISTS `perf_config_params`;
CREATE TABLE `perf_config_params`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键',
  `name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '参数名称（中文说明）',
  `param_key` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '参数名（英文标识，如 PROXY_UPLOAD_MAX_BYTES）',
  `param_value` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '参数值（字符串存储）',
  `status` int NOT NULL DEFAULT 1 COMMENT '状态：1启用 0禁用',
  `is_system` int NOT NULL DEFAULT 0 COMMENT '是否系统参数：1-是 0-否；系统参数不可修改或删除',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '备注',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除：0删除 1未删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 11 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '性能参数配置' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of perf_config_params
-- ----------------------------
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (1, '代理上传文件大小限制', 'PROXY_UPLOAD_MAX_BYTES', '200MB', 1, 1, '文件代理上传大小上限，超过此值需使用预签名直传', '2026-04-09 12:00:00', 1, '2026-04-09 12:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (2, '共享分发最大并发数', 'SHARE_DIST_MAX_WORKERS', '10', 1, 1, '共享分发同时并发的最大机器数量，直拉MinIO（方案A）和控制机中转SFTP（方案B）均受此上限约束，建议不要修改', '2026-04-09 12:00:00', 1, '2026-04-09 12:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (3, '控制机上行带宽', 'CTRL_BANDWIDTH_MBPS', '500Mbps', 1, 0, '控制机到压力机的可用上行带宽（单位Mbps）。如500M带宽填写500Mbps，1G带宽填写1000Mbps。仅在共享分发走控制机中转SFTP时生效，用于动态计算安全并发数', '2026-04-09 12:00:00', 1, '2026-04-09 12:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (4, '压力机数据文件目录', 'PERF_WORKER_DATA_DIR', 'data/jmeter/', 1, 0, '文件分发到压力机后存放的目录路径（POSIX格式，末尾可带/），如 /data/jmeter/', '2026-04-09 12:00:00', 1, '2026-04-09 12:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (5, '标准线程组基准测试联调参数', 'BASE_THREAD_GROUP_INSPECT', '{"thread_count": 1, "ramp_up_time": 2, "loop_count": 10, "loop_forever": false, "duration": 0, "startup_delay": 0}', 1, 1, '用于同样ThreadGroup线程组基准测试场景的联调；2s内启动1个线程后循环请求10次。', '2026-05-02 10:30:00', 1, '2026-05-02 10:30:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (6, '标准线程组负载测试联调参数', 'LOAD_THREAD_GROUP_INSPECT', '{"thread_count": 5, "ramp_up_time": 2, "loop_count": 0, "loop_forever": true, "duration": 10, "startup_delay": 0}', 1, 1, '用于通用ThreadGroup线程组负载/压力测试场景联调；2s启动5个线程持续运行10s检查启动运行正常。', '2026-05-02 10:30:00', 1, '2026-05-02 10:30:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (7, '阶梯加压线程组联调参数', 'STEPPING_THREAD_GROUP_INSPECT', '{"thread_count": 10, "step_initial_delay": 0, "step_start_users_count": 2, "step_start_users_burst": 0, "step_start_users_period": 5, "step_stop_users_count": 0, "step_stop_users_period": 0, "step_flight_time": 10, "step_ramp_up": 0}', 1, 1, '用于 SteppingThreadGroup 梯度线程组负载测试场景联调；小并发阶梯验证加压逻辑', '2026-05-02 10:30:00', 1, '2026-05-02 10:30:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (8, '自定义阶段线程组联调参数', 'ULTIMATE_THREAD_GROUP_INSPECT', '{"ultimate_rows": [{"start_threads": 5, "initial_delay": 0, "startup_time": 10, "hold_load_for": 30, "shutdown_time": 5}]}', 1, 1, '用于 UltimateThreadGroup 终极线程组负载测试场景联调；单阶段小并发验证阶段配置是否生效', '2026-05-02 10:30:00', 1, '2026-05-02 10:30:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (9, '清理JMeter进程开关', 'IS_CLEAR_JMETER_PID', 'true', 1, 0, '分布式模式下是否在压测启动前清理所有Worker上的JMeter进程，仅pod分布式部署时生效；执行脚本：ssh_kill_jmeter.sh', '2026-05-04 10:00:00', 1, '2026-05-04 10:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (10, '清理JMeter日志开关', 'IS_CLEAR_JMETER_LOG', 'true', 1, 0, '分布式模式下是否在压测启动前清理所有Worker上的jmeter.log日志和无关数据文件，仅pod分布式部署时生效；执行脚本：ssh_remve_csv_log', '2026-05-04 10:00:00', 1, '2026-05-04 10:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (11, 'JMeter汇总打印间隔（秒）', 'JMETER_SUMMARISER_INTERVAL', '10', 1, 1, 'JMeter非GUI模式 -J summariser.interval 参数值，控制压测结果汇总打印频率（秒）。', '2026-05-23 10:00:00', 1, '2026-05-23 10:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (12, '压测平台收集JMeter日志轮询间隔（秒）', 'JMETER_LOG_POLL_INTERVAL', '5', 1, 1, 'APScheduler日志收集任务每隔多少秒通过SSH增量读取jmeter.log新行，建议 ≤ JMETER_SUMMARISER_INTERVAL 的一半，默认5秒。', '2026-05-23 10:00:00', 1, '2026-05-23 10:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (13, '压测平台SSE监控心跳间隔（秒）', 'JMETER_MONITOR_HEARTBEAT', '20', 1, 1, 'SSE /monitor 接口在无新日志时每隔多少秒发送一次ping心跳事件，防止客户端连接超时断开，建议 > JMETER_SUMMARISER_INTERVAL，默认20秒', '2026-05-23 10:00:00', 1, '2026-05-23 10:00:00', 1, 1, NULL);
INSERT INTO `perf_config_params` (`id`, `name`, `param_key`, `param_value`, `status`, `is_system`, `remark`, `creation_date`, `created_by`, `updation_date`, `updated_by`, `enabled_flag`, `trace_id`) VALUES (14, 'JMeter压测启动命令', 'JMETER_START_CMD', 'jmeter -n -t ''{jmx_file}'' -l ./results/result.jtl -f -j ./logs/jmeter.log -J summariser.name=summary -J summariser.interval={summariser_interval} -e -o ./reports/report -X', 1, 1, 'JMeter非GUI启动命令模板；占位符：{jmx_file}（JMX脚本文件名）、{summariser_interval}（汇总间隔秒数）；分布式 -R 参数由系统自动追加，无需写入模板', '2026-05-31 10:00:00', 1, '2026-05-31 10:00:00', 1, 1, NULL);


-- ----------------------------
-- Table structure for perf_schedulers
-- ----------------------------
DROP TABLE IF EXISTS `perf_schedulers`;
CREATE TABLE `perf_schedulers`  (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '任务主键ID，从1000开始',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '任务名称，最长100字符',
  `scenario_id` bigint NOT NULL COMMENT '关联压测场景ID（perf_scenarios.id）',
  `is_active` int NOT NULL DEFAULT 1 COMMENT '启用状态：1-启用 0-禁用',
  `task_status` int NOT NULL DEFAULT 0 COMMENT '任务状态（字典 perf_scheduler_status）：0-待触发 1-进行中 2-已结束 3-已取消',
  `plan_time` datetime NOT NULL COMMENT '计划执行时间',
  `end_time` datetime NULL DEFAULT NULL COMMENT '实际结束时间（调度完成后写入）',
  `remark` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '备注',
  `creation_date` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` bigint NULL DEFAULT NULL COMMENT '创建人ID',
  `updation_date` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` bigint NULL DEFAULT NULL COMMENT '更新人ID',
  `enabled_flag` tinyint(1) NOT NULL COMMENT '是否删除：0删除 1未删除',
  `trace_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'trace_id',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_scenario_id`(`scenario_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 1000 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '性能测试定时任务' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of perf_schedulers
-- ----------------------------


-- perf_scheduler_status 字典类型
INSERT INTO `sys_dict_type` VALUES ('定时任务状态', 'perf_scheduler_status', 1, '性能测试定时任务状态：待触发、进行中、已结束、已取消', 12, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');

-- perf_scheduler_status 字典数据
INSERT INTO `sys_dict_data` VALUES (0, '待触发', '0', 'perf_scheduler_status', NULL, NULL, 0, 1, '任务已创建，等待到达计划执行时间', 49, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (1, '进行中', '1', 'perf_scheduler_status', NULL, NULL, 0, 1, '调度已触发，压测任务正在执行', 50, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (2, '已结束', '2', 'perf_scheduler_status', NULL, NULL, 0, 1, '压测任务已执行完成', 51, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (3, '已取消', '3', 'perf_scheduler_status', NULL, NULL, 0, 1, '任务已被手动取消', 52, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');
INSERT INTO `sys_dict_data` VALUES (4, '失败', '4', 'perf_scheduler_status', NULL, NULL, 0, 1, '任务触发后压测启动失败', 53, '2026-04-09 12:38:49', 1, '2026-04-09 12:38:49', 1, 1, NULL, '2026-04-09 12:38:49', '2026-04-09 12:38:49');


SET FOREIGN_KEY_CHECKS = 1;
