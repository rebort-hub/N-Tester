#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
常量定义
"""

# 响应状态码
SUCCESS_CODE = 200
ERROR_CODE = 500

# 缓存键前缀
CACHE_PREFIX_USER = "user:"
CACHE_PREFIX_ROLE = "role:"
CACHE_PREFIX_PERMISSION = "permission:"
CACHE_PREFIX_MENU = "menu:"

# 缓存过期时间（秒）
CACHE_EXPIRE_USER = 3600  # 1小时
CACHE_EXPIRE_ROLE = 3600  # 1小时
CACHE_EXPIRE_PERMISSION = 3600  # 1小时
CACHE_EXPIRE_MENU = 3600  # 1小时

# Token相关
TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7天

# 密码相关
PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 20

# 分页相关
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# SSH 连接失败异常错误类型
SSH_CONN_ERROR_SIGNS = (
    'permission denied',
    'authentication failed',
    'connection refused',
    'connection closed',
    'connection timed out',
    'no route to host',
    'host key verification failed',
    'could not resolve hostname',
    'network is unreachable',
)

# JMeter中CSV 配置元件引用的文件名称包含的特殊函数表达式
JMETER_CSV_NAME_EXPRESSION = {
    "${__P(csv.path, xxx.csv)}"     # 跨平台路径兼容获取csv文件表达式
}

# 调试组件 guiclass → 中文标签映射
# 键为 JMX ResultCollector 的 guiclass 属性值，同时用于：
#   1. 压测前检测（gui_class in JMETER_DEBUG_GUI_LABEL）
#   2. 联调页面调试组件列表的中文标签显示
JMETER_DEBUG_GUI_LABEL: dict[str, str] = {
    # -----------JMeter 内置监听器--------------
    "ViewResultsFullVisualizer": "查看结果树",
    "TableVisualizer": "用表格查看结果",
    "StatVisualizer": "聚合报告",
    "SummaryReport": "汇总报告",
    "AssertionVisualizer": "断言结果",
    "GraphVisualizer": "图形结果",
    "StatGraphVisualizer": "汇总图",
    "RespTimeGraphVisualizer": "响应时间图",
    "DebugSampler": "调试取样器",
    # ---------jp@gc JMeter Plugins Manager 插件监听器------------
    "kg.apc.jmeter.vizualizers.ResponseTimesOverTimeGui": "Response Times Over Time",
    "kg.apc.jmeter.vizualizers.TransactionsPerSecondGui": "Transactions per Second",
    "kg.apc.jmeter.vizualizers.ThreadsStateOverTimeGui": "Active Threads Over Time",
    "kg.apc.jmeter.vizualizers.HitsPerSecondGui": "每秒点击量图(jp@gc)",
    "kg.apc.jmeter.vizualizers.BytesThroughputOverTimeGui": "吞吐量图(jp@gc)",
    "kg.apc.jmeter.vizualizers.LatenciesOverTimeGui":  "响应延迟图(jp@gc)",
    "kg.apc.jmeter.vizualizers.ConnectTimeOverTimeGui": "连接时间图(jp@gc)",
}