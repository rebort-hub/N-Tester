#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Lucas
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePosixPath
from typing import Optional, Tuple
import xml.etree.ElementTree as ET

from loguru import logger

from app.common.constants import JMETER_DEBUG_GUI_LABEL

"""
JMeter JMX 脚本解析与修改工具

JMX 是标准 XML，所有可配置值均以 <xxxProp name="Key">value</xxxProp> 形式存储。
本模块只修改已有节点的 text 值，不新增、不删除任何 XML 节点，保证脚本结构不变。

修改范围：
  - 用户自定义变量（TestPlan.user_defined_variables）
  - 线程组配置（标准 / SteppingThreadGroup / UltimateThreadGroup）

只读范围（供前端展示和压测前检查）：
  - BackendListener（InfluxDB 配置）
  - ResultCollector / DebugSampler（调试组件启用状态）
  - CSVDataSet 引用的数据文件名
"""

# ====================== 数据结构 ======================

@dataclass
class SteppingConfig:
    """SteppingThreadGroup 独有的阶梯加压参数"""
    initial_delay: int        # 初始延迟（秒，Threads initial delay）
    start_users_count: int    # 每步新增线程数（Start users count）
    start_users_burst: int    # 突发加载数（Start users count burst）
    start_users_period: int   # 每步时间间隔（秒，Start users period）
    stop_users_count: int     # 每步减少线程数（Stop users count）
    stop_users_period: int    # 停止步骤间隔（秒，Stop users period）
    flight_time: int          # 保持满载时间（秒，flighttime）
    ramp_up: int              # 爬坡时间（秒，rampUp）


@dataclass
class UltimateConfig:
    """UltimateThreadGroup 的单行阶段配置（按 XML 列顺序对应）"""
    start_threads: int  # 该阶段线程数
    initial_delay: int  # 初始延迟（秒）
    startup_time: int   # 爬坡时间（秒）
    hold_load_for: int  # 持续时间（秒）
    shutdown_time: int  # 停止时间（秒）


@dataclass
class ThreadGroupConfig:
    """
    统一的线程组配置快照，通过 thread_type 区分类型。

    thread_type 取值：
      "standard"  → ThreadGroup / SetupThreadGroup / TearDownThreadGroup
      "stepping"  → kg.apc.jmeter.threads.SteppingThreadGroup
      "ultimate"  → kg.apc.jmeter.threads.UltimateThreadGroup
    stepping / ultimate_rows 仅对应类型填充，其余为 None。
    """
    index: int                     # 线程组在 JMX 中的顺序编号（0-based），用于 apply_thread_group 定位
    thread_type: str               # 线程组类型：standard / stepping / ultimate
    tag: str                       # XML 元素标签名，原样保留，不做语义判断
    testname: str                  # JMeter 中显示的线程组名称
    enabled: bool                  # 是否启用；disabled 的线程组压测时不执行
    num_threads_raw: str           # XML 原始值，可能是数字字符串或 ${varname} 变量引用
    num_threads: Optional[int]     # 解析后的整数并发数；变量无法解析时为 None
    ramp_time: int                 # Ramp-up 爬坡时间（秒），standard 类型有效
    loop_count: int                # 循环次数；loop_forever=True 时忽略此值
    loop_forever: bool             # 是否永远循环，对应 LoopController.continue_forever
    scheduler: bool                # 是否启用调度器；loop_forever 模式下配合 duration 使用
    duration: int                  # 持续压测时间（秒），scheduler=True 时生效
    delay: int                     # 线程组启动延迟（秒），多线程组错峰启动时使用
    stepping: Optional[SteppingConfig] = None             # 仅 stepping 类型填充，其余为 None
    ultimate_rows: Optional[list[UltimateConfig]] = None  # 仅 ultimate 类型填充，每项对应一个阶段行


@dataclass
class JMXSummary:
    """JMX 脚本全量摘要，用于前端展示和压测前检查"""
    test_plan_name: str
    user_vars: dict[str, str]        # {变量名: 当前值}
    thread_groups: list[ThreadGroupConfig]
    backend_listeners: list[dict]    # 每项: {testname, enabled, classname, influxdb_url, ...}
    result_collectors: list[dict]    # 每项: {testname, enabled, gui_class, is_debug}
    csv_data_files: list[str]        # 数据文件 basename 列表
    total_threads: int               # 全部 enabled 线程组的线程数之和
    debug_listeners_on: list[str]    # 仍处于 enabled=true 的调试组件 testname 列表
    http_samplers: list[dict]        # HTTP 请求，按线程组分组：[{thread_group_name, samplers:[...]}]
    user_var_descs: dict[str, str]   # {变量名: 备注/描述（Argument.desc）}


# =============================== 常量 ===================================

_STD_TG_TAGS  = {"ThreadGroup", "SetupThreadGroup", "TearDownThreadGroup"}
_STEPPING_TAG = "kg.apc.jmeter.threads.SteppingThreadGroup"
_ULTIMATE_TAG = "kg.apc.jmeter.threads.UltimateThreadGroup"
_ALL_TG_TAGS  = _STD_TG_TAGS | {_STEPPING_TAG, _ULTIMATE_TAG}

# InfluxDB 后端监听器实现类
_INFLUXDB_CLASSNAME = (
    "org.apache.jmeter.visualizers.backend.influxdb.InfluxdbBackendListenerClient"
)


# ============================= 核心解析器 =============================

class JMXParser:
    """
    JMeter JMX 脚本解析 / 修改器。
    只操作已有节点的 text 值，不改变 XML 结构。
    写入操作仅限：用户自定义变量、线程组配置字段。

    典型用法::
        parser = JMXParser(jmx_bytes)
        summary = parser.get_summary()           # 读取全量摘要
        parser.apply_thread_group(0, num_threads=100, ramp_time=60)
        new_bytes = parser.to_bytes()            # 序列化后上传压力机
    """

    def __init__(self, content: bytes | str) -> None:
        """
        初始化解析器，将 JMX 内容解析为 XML 树，并初始化节点缓存。

        Args:
            content: JMX 文件内容，bytes 或 str 均可；str 会按 utf-8 编码转换
        """
        if isinstance(content, str):
            content = content.encode("utf-8")
        self._tree = ET.parse(BytesIO(content))  # type: ignore[arg-type]
        self._root = self._tree.getroot()
        # 缓存高频访问节点，避免重复遍历整棵树
        self._user_vars_cache: Optional[dict[str, str]] = None
        self._test_plan_el: Optional[ET.Element] = None
        self._user_vars_col_el: Optional[ET.Element] = None  # 用户变量集合节点

    # ──────────────── 私有工具方法 ────────────────

    def _get_prop(self, el: ET.Element, name: str, default: str = "") -> str:
        """
        在 el 子树中查找名为 name 的 Prop 节点并返回其 text。

        JMeter 中属性值以不同标签存储（stringProp / boolProp / intProp / longProp），
        本方法统一兼容四种标签，调用方无需关心底层标签类型。
        节点不存在或 text 为空时返回 default。

        Args:
            el:      要在其子树中查找的父节点
            name:    Prop 节点的 name 属性值（如 "ThreadGroup.num_threads"）
            default: 节点不存在或值为空时的默认返回值
        Returns:
            找到的 text 值，或 default
        """
        for tag in ("stringProp", "boolProp", "intProp", "longProp"):
            node = el.find(f".//{tag}[@name='{name}']")
            if node is not None:
                return node.text or default
        return default

    def _set_prop(self, el: ET.Element, name: str, value: str) -> bool:
        """
        修改 el 子树中名为 name 的 Prop 节点的 text。

        不新增节点（保持 XML 结构不变），节点不存在时直接返回 False。
        与 _get_prop 对应，同样兼容四种 Prop 标签。

        Args:
            el:    目标父节点
            name:  Prop 的 name 属性值
            value: 要写入的字符串值
        Returns:
            True=找到并修改成功，False=节点不存在
        """
        for tag in ("stringProp", "boolProp", "intProp", "longProp"):
            node = el.find(f".//{tag}[@name='{name}']")
            if node is not None:
                node.text = value
                return True
        return False

    def _get_all_arguments(self, col_el: ET.Element) -> dict[str, str]:
        """
        解析 Arguments.arguments 集合节点，返回所有参数的键值对。

        JMeter 的参数集合结构：collectionProp > elementProp（每个参数）
          > stringProp[@name='Argument.name']  参数名
          > stringProp[@name='Argument.value'] 参数值

        Args:
            col_el: collectionProp[@name='Arguments.arguments'] 节点
        Returns:
            {Argument.name: Argument.value} 字典
        """
        result: dict[str, str] = {}
        for item in col_el.iter("elementProp"):
            name_node = item.find("stringProp[@name='Argument.name']")
            val_node  = item.find("stringProp[@name='Argument.value']")
            if name_node is not None and name_node.text:
                result[name_node.text] = val_node.text if val_node is not None else ""
        return result

    def _set_argument(self, col_el: ET.Element, name: str, value: str) -> bool:
        """
        修改 Arguments.arguments 集合中指定参数的值。

        遍历集合中每个 elementProp，匹配 Argument.name 后写入 Argument.value。
        参数不存在时返回 False，不新增节点。

        Args:
            col_el: collectionProp[@name='Arguments.arguments'] 节点
            name:   要修改的参数名（Argument.name 的值）
            value:  要写入的新值
        Returns:
            True=找到并修改成功，False=参数名不存在
        """
        for item in col_el.iter("elementProp"):
            name_node = item.find("stringProp[@name='Argument.name']")
            if name_node is not None and name_node.text == name:
                val_node = item.find("stringProp[@name='Argument.value']")
                if val_node is not None:
                    val_node.text = value
                    return True
        return False

    def _resolve(self, text: str, vars_map: dict[str, str]) -> Optional[int]:
        """
        将 Prop text 解析为整数，透明处理变量引用。

        支持三种格式：
          1. 纯数字字符串（如 "100"）→ 直接转 int
          2. 简单变量引用 ${varname} → 从 vars_map 查实际值再转 int
          3. JMeter 属性函数 ${__P(propName)} / ${__P(propName,defaultValue)}
             → 优先从 vars_map 按 propName 查值，查不到时使用 defaultValue

        转换失败（变量不存在、值非数字）→ 返回 None，由调用方决定如何处理。
        """
        raw = (text or "").strip()
        if not raw:
            return None

        # ${__P(propName)} 或 ${__P(propName,defaultValue)} —— JMeter 属性函数
        m_p = re.match(r'^\$\{__P\((\w+)(?:,([^)]*))?\)\}$', raw)
        if m_p:
            prop_name   = m_p.group(1)
            default_val = (m_p.group(2) or "").strip()
            raw = vars_map.get(prop_name) or default_val
            if not raw:
                return None
        else:
            # ${varname} —— 简单变量引用
            m = re.match(r'^\$\{(\w+)\}$', raw)
            if m:
                raw = vars_map.get(m.group(1), "")

        try:
            return int(raw)
        except (ValueError, TypeError):
            try:
                return int(float(raw))  # 兜底：处理 "60.0" 等浮点字符串
            except (ValueError, TypeError):
                return None

    def _resolve_str(self, text: str, vars_map: dict[str, str]) -> str:
        """将 text 中所有 ${varname} 替换为变量表中的实际值（字符串层面，保留非变量部分）。"""
        return re.sub(r'\$\{(\w+)\}', lambda m: vars_map.get(m.group(1), m.group(0)), text or "")

    @staticmethod
    def _iter_enabled_http_samplers(tree_el: ET.Element):
        """
        递归遍历 hashTree，跳过禁用容器（TestFragmentController、任意 Controller 等）
        下的整个子树，只 yield 可达路径上的 HTTPSamplerProxy 元素。

        JMX 结构规律：每个组件元素后紧跟一个 hashTree 兄弟节点作为其子树；
        若该组件 enabled=false，则跳过其后的子 hashTree，不再递归进入。
        """
        children = list(tree_el)
        i = 0
        while i < len(children):
            el = children[i]
            if el.tag == 'hashTree':
                i += 1
                continue
            # 紧随其后的兄弟 hashTree 是该元素的子树
            child_tree = (
                children[i + 1]
                if i + 1 < len(children) and children[i + 1].tag == 'hashTree'
                else None
            )
            enabled = el.get('enabled', 'true') == 'true'
            if enabled:
                if el.tag == 'HTTPSamplerProxy':
                    yield el
                if child_tree is not None:
                    yield from JMXParser._iter_enabled_http_samplers(child_tree)
            i += 2 if child_tree is not None else 1

    def _get_tg_hashtree_map(self) -> list[tuple[ET.Element, ET.Element]]:
        """
        遍历 XML 树，收集所有「线程组元素 → 其直属 hashTree」配对（按文档顺序）。
        在 JMX 中，ThreadGroup 与其子树 hashTree 始终是相邻兄弟节点，
        hashTree 包含该线程组内所有的 Sampler / Controller 等子元素。
        """
        pairs: list[tuple[ET.Element, ET.Element]] = []
        for parent in self._root.iter():
            children = list(parent)
            for i, child in enumerate(children):
                if child.tag in _ALL_TG_TAGS:
                    if i + 1 < len(children) and children[i + 1].tag == 'hashTree':
                        pairs.append((child, children[i + 1]))
        return pairs

    def _find_thread_groups(self) -> list[ET.Element]:
        """
        遍历整棵 XML 树，按文档顺序返回所有线程组元素。

        JMeter 三种线程组的 XML 标签均不同（见 _ALL_TG_TAGS），
        统一按标签名过滤，保证顺序与 JMeter GUI 中展示的一致。

        Returns:
            按 XML 出现顺序排列的线程组元素列表
        """
        return [el for el in self._root.iter() if el.tag in _ALL_TG_TAGS]

    def _get_test_plan_el(self) -> Optional[ET.Element]:
        """查找并缓存 TestPlan 元素（整个脚本只有一个），避免重复遍历"""
        if self._test_plan_el is None:
            self._test_plan_el = self._root.find(".//TestPlan")
        return self._test_plan_el

    def _get_user_vars_col_el(self) -> Optional[ET.Element]:
        """
        查找并缓存用户自定义变量的 Arguments.arguments 集合节点。

        JMeter 有两种配置全局变量的方式，本方法两种均支持：
          方式1（TestPlan 内嵌，较少见）：
            TestPlan > elementProp[@name='TestPlan.user_defined_variables']
                     > collectionProp[@name='Arguments.arguments']
          方式2（独立"用户定义的变量"组件，更常见）：
            hashTree > Arguments[guiclass='ArgumentsPanel']
                     > collectionProp[@name='Arguments.arguments']

        优先使用方式1（非空时）；方式1为空则查找方式2的第一个有效集合。
        结果缓存，后续调用直接返回，不重复遍历 XML。

        Returns:
            Arguments.arguments 的 collectionProp 节点；脚本无用户变量时返回 None
        """
        if self._user_vars_col_el is not None:
            return self._user_vars_col_el

        # 方式1：TestPlan 内嵌变量表（有子节点才算有效）
        tp = self._get_test_plan_el()
        if tp is not None:
            ep = tp.find("elementProp[@name='TestPlan.user_defined_variables']")
            if ep is not None:
                col = ep.find("collectionProp[@name='Arguments.arguments']")
                if col is not None and len(col) > 0:
                    self._user_vars_col_el = col
                    return self._user_vars_col_el

        # 方式2：独立的"用户定义的变量"Arguments 组件
        for el in self._root.iter("Arguments"):
            if el.get("guiclass") == "ArgumentsPanel":
                col = el.find("collectionProp[@name='Arguments.arguments']")
                if col is not None and len(col) > 0:
                    self._user_vars_col_el = col
                    return self._user_vars_col_el

        return None

    # ──────────────── 读取方法 ────────────────

    def get_user_var_descs(self) -> dict[str, str]:
        """读取用户变量的备注描述（Argument.desc），与 get_user_vars() 键名一一对应。"""
        col = self._get_user_vars_col_el()
        if col is None:
            return {}
        result: dict[str, str] = {}
        for item in col.iter("elementProp"):
            name_node = item.find("stringProp[@name='Argument.name']")
            desc_node = item.find("stringProp[@name='Argument.desc']")
            if name_node is not None and name_node.text:
                result[name_node.text] = (desc_node.text or "") if desc_node is not None else ""
        return result

    def get_user_vars(self) -> dict[str, str]:
        """
        读取 TestPlan 级别的用户自定义变量。

        结果缓存在内存中，后续调用直接返回，避免重复解析 XML。
        调用 set_user_vars 写入后缓存会同步更新，读取结果始终与 XML 一致。

        Returns:
            {变量名: 当前值} 字典；脚本未定义变量时返回空字典
        """
        if self._user_vars_cache is not None:
            return self._user_vars_cache
        col = self._get_user_vars_col_el()
        self._user_vars_cache = self._get_all_arguments(col) if col is not None else {}
        return self._user_vars_cache

    def get_thread_groups(self) -> list[ThreadGroupConfig]:
        """
        解析所有线程组，按 XML 文档顺序返回配置快照列表。

        三种线程组类型均支持，通过 ThreadGroupConfig.thread_type 字段区分：
          - "standard"：读取 num_threads / ramp_time / loop_count / scheduler 等完整字段
          - "stepping"：stepping 字段填充 SteppingConfig，standard 字段填 0/默认值
          - "ultimate"：ultimate_rows 填充各阶段行，num_threads 为各行 start_threads 之和

        num_threads 解析说明：
          XML 中若是 ${varname} 格式，则从用户变量表解析实际整数值；
          变量不存在或值非数字时 num_threads=None，num_threads_raw 保留原始字符串。

        Returns:
            list[ThreadGroupConfig]，按 XML 顺序排列
        """
        vars_map = self.get_user_vars()
        configs: list[ThreadGroupConfig] = []

        for idx, tg in enumerate(self._find_thread_groups()):
            tag      = tg.tag
            testname = tg.get("testname", "")
            enabled  = tg.get("enabled", "true") == "true"

            if tag in _STD_TG_TAGS:
                configs.append(self._read_std_tg(idx, tg, tag, testname, enabled, vars_map))
            elif tag == _STEPPING_TAG:
                configs.append(self._read_stepping_tg(idx, tg, testname, enabled, vars_map))
            elif tag == _ULTIMATE_TAG:
                configs.append(self._read_ultimate_tg(idx, tg, testname, enabled))

        return configs

    def _read_std_tg(
        self, idx: int, tg: ET.Element, tag: str,
        testname: str, enabled: bool, vars_map: dict
    ) -> ThreadGroupConfig:
        """
        解析单个标准线程组（ThreadGroup / SetupThreadGroup / TearDownThreadGroup）。

        JMeter 中循环配置不在 ThreadGroup 本身，而在其嵌套的 LoopController 子节点
        （elementProp[@name='ThreadGroup.main_controller']）内，需单独读取。

        Args:
            idx:      当前线程组的顺序编号（0-based）
            tg:       线程组 XML 元素
            tag:      XML 标签名（SetupThreadGroup / ThreadGroup 等）
            testname: 线程组显示名称
            enabled:  是否启用
            vars_map: 用户变量字典，用于解析 ${varname} 引用
        Returns:
            填充完整字段的 ThreadGroupConfig
        """
        # 循环配置位于嵌套的 LoopController 子节点，需先定位
        loop_el           = tg.find("elementProp[@name='ThreadGroup.main_controller']")
        loop_forever_text = ""
        loop_count_text   = "1"
        if loop_el is not None:
            loop_forever_text = self._get_prop(loop_el, "LoopController.continue_forever")
            loop_count_text   = self._get_prop(loop_el, "LoopController.loops", "1")

        num_threads_raw = self._get_prop(tg, "ThreadGroup.num_threads", "1")
        return ThreadGroupConfig(
            index           = idx,
            thread_type     = "standard",
            tag             = tag,
            testname        = testname,
            enabled         = enabled,
            num_threads_raw = num_threads_raw,
            num_threads     = self._resolve(num_threads_raw, vars_map),
            ramp_time       = self._resolve(self._get_prop(tg, "ThreadGroup.ramp_time", "1"), vars_map) or 1,
            loop_count      = self._resolve(loop_count_text, vars_map) or 1,
            loop_forever    = loop_forever_text == "true",
            scheduler       = self._get_prop(tg, "ThreadGroup.scheduler") == "true",
            duration        = self._resolve(self._get_prop(tg, "ThreadGroup.duration", "0"), vars_map) or 0,
            delay           = self._resolve(self._get_prop(tg, "ThreadGroup.delay", "0"), vars_map) or 0,
        )

    def _read_stepping_tg(
        self, idx: int, tg: ET.Element,
        testname: str, enabled: bool, vars_map: dict
    ) -> ThreadGroupConfig:
        """
        解析单个 SteppingThreadGroup（阶梯加压线程组）。

        SteppingThreadGroup 无 LoopController，循环/调度字段均无意义，填默认值。
        阶梯参数（SteppingConfig）从其特有的 XML Prop 中读取，
        Prop name 使用 JMeter 英文原文，如 "Start users count"。

        Args:
            idx:      顺序编号（0-based）
            tg:       线程组 XML 元素
            testname: 线程组显示名称
            enabled:  是否启用
            vars_map: 用户变量字典
        Returns:
            stepping 字段已填充的 ThreadGroupConfig
        """
        num_threads_raw = self._get_prop(tg, "ThreadGroup.num_threads", "0")
        return ThreadGroupConfig(
            index           = idx,
            thread_type     = "stepping",
            tag             = _STEPPING_TAG,
            testname        = testname,
            enabled         = enabled,
            num_threads_raw = num_threads_raw,
            num_threads     = self._resolve(num_threads_raw, vars_map),
            ramp_time=0, loop_count=1, loop_forever=False,
            scheduler=False, duration=0, delay=0,
            stepping=SteppingConfig(
                initial_delay      = self._resolve(self._get_prop(tg, "Threads initial delay", "0"), vars_map) or 0,
                start_users_count  = self._resolve(self._get_prop(tg, "Start users count", "0"), vars_map) or 0,
                start_users_burst  = self._resolve(self._get_prop(tg, "Start users count burst", "0"), vars_map) or 0,
                start_users_period = self._resolve(self._get_prop(tg, "Start users period", "0"), vars_map) or 0,
                stop_users_count   = self._resolve(self._get_prop(tg, "Stop users count", "0"), vars_map) or 0,
                stop_users_period  = self._resolve(self._get_prop(tg, "Stop users period", "0"), vars_map) or 0,
                flight_time        = self._resolve(self._get_prop(tg, "flighttime", "0"), vars_map) or 0,
                ramp_up            = self._resolve(self._get_prop(tg, "rampUp", "0"), vars_map) or 0,
            ),
        )

    def _read_ultimate_tg(
        self, idx: int, tg: ET.Element, testname: str, enabled: bool
    ) -> ThreadGroupConfig:
        """
        解析单个 UltimateThreadGroup（自定义阶段线程组）。

        行数据存储在 ultimatethreadgroupdata 集合中，每行是一个 collectionProp，
        其下 5 个 stringProp 按固定位置对应：线程数/初始延迟/爬坡/持续/停止时间。
        collectionProp 的 name 属性是 hashCode，不具语义，按位置索引读取。
        num_threads 汇总为各行 start_threads 之和，便于前端展示总并发数。

        Args:
            idx:      顺序编号（0-based）
            tg:       线程组 XML 元素
            testname: 线程组显示名称
            enabled:  是否启用
        Returns:
            ultimate_rows 字段已填充的 ThreadGroupConfig
        """
        def _safe_int(text: Optional[str]) -> int:
            try:
                return int(text or "0")
            except (ValueError, TypeError):
                return 0

        rows: list[UltimateConfig] = []
        data_col = tg.find("collectionProp[@name='ultimatethreadgroupdata']")
        if data_col is not None:
            for row_col in data_col.findall("collectionProp"):
                props = row_col.findall("stringProp")
                if len(props) >= 5:
                    p0, p1, p2, p3, p4 = props[:5]  # type: ignore[misc]
                    rows.append(UltimateConfig(
                        start_threads = _safe_int(p0.text),
                        initial_delay = _safe_int(p1.text),
                        startup_time  = _safe_int(p2.text),
                        hold_load_for = _safe_int(p3.text),
                        shutdown_time = _safe_int(p4.text),
                    ))

        total = sum(r.start_threads for r in rows)
        return ThreadGroupConfig(
            index           = idx,
            thread_type     = "ultimate",
            tag             = _ULTIMATE_TAG,
            testname        = testname,
            enabled         = enabled,
            num_threads_raw = str(total),
            num_threads     = total,
            ramp_time=0, loop_count=1, loop_forever=False,
            scheduler=False, duration=0, delay=0,
            ultimate_rows=rows,
        )

    def get_backend_listeners(self) -> list[dict]:
        """
        读取所有 BackendListener（后端监听器）配置。

        BackendListener 的参数存放在嵌套结构中：
          BackendListener > elementProp[@name='arguments']
                         > collectionProp[@name='Arguments.arguments']
        classname 为 InfluxDB 实现类时，额外解析 influxdb_url / application / measurement。

        Returns:
            list[dict]，每项结构：
              {testname, enabled, classname, influxdb_url,
               application（仅 InfluxDB 类型）, measurement（仅 InfluxDB 类型）}
        """
        result: list[dict] = []
        for el in self._root.iter("BackendListener"):
            classname = self._get_prop(el, "classname")
            # 读取 BackendListener 的参数集合
            args: dict[str, str] = {}
            args_ep = el.find("elementProp[@name='arguments']")
            if args_ep is not None:
                col = args_ep.find("collectionProp[@name='Arguments.arguments']")
                if col is not None:
                    args = self._get_all_arguments(col)

            item: dict = {
                "testname":    el.get("testname", ""),
                "enabled":     el.get("enabled", "true") == "true",
                "classname":   classname,
                "influxdb_url": None,
            }
            # InfluxDB 类型额外字段
            if classname == _INFLUXDB_CLASSNAME:
                item["influxdb_url"] = args.get("influxdbUrl")
                item["application"]  = args.get("application", "")
                item["measurement"]  = args.get("measurement", "jmeter")
            result.append(item)
        return result

    def get_result_collectors(self) -> list[dict]:
        """
        读取所有调试监听器和调试取样器配置，用于压测前检查是否有未关闭的调试组件。

        扫描两类 XML 元素：
          1. ResultCollector / kg.apc.jmeter.vizualizers.CorrectedResultCollector（监听器）：
             JMeter 内置监听器使用 ResultCollector 标签；jp@gc 插件监听器使用
             CorrectedResultCollector 标签（jp@gc 对 ResultCollector 的修正子类）。
             两者统一按 guiclass 属性判断是否属于调试类（见 JMETER_DEBUG_GUI_LABEL）。
          2. DebugSampler（调试取样器）：独立 XML 标签，不是 ResultCollector，
             无需判断 guiclass，直接标记 is_debug=True。

        is_debug=True 且 enabled=True 的组件会出现在 JMXSummary.debug_listeners_on 告警列表中。

        Returns:
            list[dict]，每项结构：{testname, enabled, gui_class, is_debug}
        """
        result: list[dict] = []
        # JMeter 内置监听器标签为 ResultCollector；
        # jp@gc 插件监听器标签为 kg.apc.jmeter.vizualizers.CorrectedResultCollector，
        # 两者均需扫描，统一按 guiclass 属性判断是否属于调试类
        for tag in ("ResultCollector", "kg.apc.jmeter.vizualizers.CorrectedResultCollector"):
            for el in self._root.iter(tag):
                gui_class = el.get("guiclass", "")
                result.append({
                    "testname":  el.get("testname", ""),
                    "enabled":   el.get("enabled", "true") == "true",
                    "gui_class": gui_class,
                    "is_debug":  gui_class in JMETER_DEBUG_GUI_LABEL,
                })
        # 调试取样器是独立标签，非 ResultCollector，单独收集并无条件标记为调试组件
        for el in self._root.iter("DebugSampler"):
            result.append({
                "testname":  el.get("testname", ""),
                "enabled":   el.get("enabled", "true") == "true",
                "gui_class": "DebugSampler",
                "is_debug":  True,
            })
        return result

    def get_csv_data_files(self) -> list[str]:
        """
        读取所有 CSVDataSet 引用的数据文件名。

        只返回 basename，忽略脚本中配置的本地绝对路径（路径在不同机器上不同，无参考价值）。
        去重并保持 XML 出现顺序，便于前端展示关联数据文件列表。

        Returns:
            文件名列表，如 ["users.csv", "orders.csv"]
        """
        seen: dict[str, None] = {}
        for el in self._root.iter("CSVDataSet"):
            text = self._get_prop(el, "filename")
            if text:
                name = PurePosixPath(text.replace("\\", "/")).name
                seen.setdefault(name, None)
        return list(seen)

    def get_http_samplers(self) -> list[dict]:
        """
        读取 JMX 中所有 HTTPSamplerProxy，按线程组分组返回。
        - URL 由 protocol + domain + port + path 拼接，${varname} 自动解析为用户变量值。
        - referenced_vars：记录该请求字段中引用的用户变量名，供"引用变量"项过滤使用。
        - 只返回含 HTTP 请求的线程组（无 HTTP 请求的线程组不出现在结果中）。

        Returns:
            list[dict]，每项结构：
            {
              thread_group_name: str,
              thread_group_type: str,   # SetUp / TearDown / ThreadGroup / SteppingThreadGroup / UltimateThreadGroup
              thread_group_tag:  str,   # XML 原始 tag，用于区分 SetupThreadGroup / TearDownThreadGroup
              thread_group_enabled: bool,
              samplers: [
                {testname, method, url, enabled, referenced_vars: [str]}
              ]
            }
        """
        _TAG_LABEL: dict[str, str] = {
            "ThreadGroup":        "ThreadGroup",
            "SetupThreadGroup":   "SetUp",
            "TearDownThreadGroup": "TearDown",
            _STEPPING_TAG:        "SteppingThreadGroup",
            _ULTIMATE_TAG:        "UltimateThreadGroup",
        }
        vars_map  = self.get_user_vars()
        tg_pairs  = self._get_tg_hashtree_map()
        result: list[dict] = []

        for tg_el, hashtree in tg_pairs:
            tg_enabled = tg_el.get("enabled", "true") == "true"
            samplers: list[dict] = []

            for sampler in self._iter_enabled_http_samplers(hashtree):
                sampler_enabled = sampler.get("enabled", "true") == "true"

                # 读取原始字段（可能含 ${varname}）
                raw_protocol = self._get_prop(sampler, "HTTPSampler.protocol", "http")
                raw_domain   = self._get_prop(sampler, "HTTPSampler.domain",   "")
                raw_port     = self._get_prop(sampler, "HTTPSampler.port",     "")
                raw_path     = self._get_prop(sampler, "HTTPSampler.path",     "")

                # 域名若为纯变量引用（${varName}），保留原始串直接展示，不展开为实际值
                protocol = self._resolve_str(raw_protocol, vars_map) or "http"
                domain   = raw_domain if re.fullmatch(r'\$\{[^}]+\}', raw_domain.strip()) else self._resolve_str(raw_domain, vars_map)
                port     = self._resolve_str(raw_port,     vars_map)
                path     = self._resolve_str(raw_path,     vars_map)

                if domain:
                    url = f"{protocol}://{domain}"
                    if port:
                        url += f":{port}"
                    url += path
                else:
                    url = path or "—"

                # 收集当前请求字段中被引用的用户变量名（仅收录已在用户变量表中存在的）
                referenced_vars = sorted({
                    m.group(1)
                    for raw in (raw_protocol, raw_domain, raw_port, raw_path)
                    for m in re.finditer(r'\$\{(\w+)\}', raw)
                    if m.group(1) in vars_map
                })

                samplers.append({
                    "testname":        sampler.get("testname", ""),
                    "method":          self._get_prop(sampler, "HTTPSampler.method", "GET"),
                    "url":             url,
                    "enabled":         sampler_enabled,
                    "referenced_vars": referenced_vars,
                })

            if samplers:
                result.append({
                    "thread_group_name":    tg_el.get("testname", ""),
                    "thread_group_type":    _TAG_LABEL.get(tg_el.tag, tg_el.tag),
                    "thread_group_tag":     tg_el.tag,
                    "thread_group_enabled": tg_enabled,
                    "samplers":             samplers,
                })

        return result

    def get_summary(self) -> JMXSummary:
        """
        一次性解析 JMX 脚本的全量摘要，汇总所有读取方法的结果。

        调用链：get_thread_groups → get_user_vars（已缓存）→ get_backend_listeners
                → get_result_collectors → get_csv_data_files

        debug_listeners_on 从 result_collectors 中过滤 is_debug=True 且 enabled=True 的项，
        作为压测前的告警依据（有值则说明存在未关闭的调试组件）。

        Returns:
            JMXSummary 数据类实例
        """
        tp         = self._get_test_plan_el()
        tg_list    = self.get_thread_groups()
        collectors = self.get_result_collectors()
        return JMXSummary(
            test_plan_name    = tp.get("testname", "") if tp is not None else "",
            user_vars         = self.get_user_vars(),
            thread_groups     = tg_list,
            backend_listeners = self.get_backend_listeners(),
            result_collectors = collectors,
            csv_data_files    = self.get_csv_data_files(),
            total_threads     = sum(tg.num_threads or 0 for tg in tg_list if tg.enabled),  # type: ignore[arg-type]
            debug_listeners_on= [c["testname"] for c in collectors if c["is_debug"] and c["enabled"]],
            http_samplers     = self.get_http_samplers(),
            user_var_descs    = self.get_user_var_descs(),
        )

    # ──────────────── 写入方法 ────────────────

    def set_user_vars(self, updates: dict[str, str]) -> dict[str, bool]:
        """
        批量修改用户自定义变量，单个变量传 {name: value} 即可。

        _get_user_vars_col_el 只调用一次，比逐条操作少一次节点查找。
        变量不存在时对应项返回 False，不新增节点（保持脚本结构不变）。
        修改成功后同步更新内存缓存，使 get_user_vars() 立即反映新值。

        Args:
            updates: {变量名: 新值} 字典
        Returns:
            {变量名: 是否找到并修改} 字典
        """
        col = self._get_user_vars_col_el()
        if col is None:
            return {name: False for name in updates}
        result: dict[str, bool] = {}
        for name, value in updates.items():
            ok = self._set_argument(col, name, value)
            if ok and self._user_vars_cache is not None:
                self._user_vars_cache[name] = value
            result[name] = ok
        return result

    def apply_thread_group(self, index: int, **fields) -> None:
        """
        修改指定线程组的配置字段（按文档顺序 0-based 索引定位）。

        变量引用智能处理（_write_field 实现）：
          写入时先检查目标 Prop 的当前值；若是 ${varname} 格式，则改写用户变量表中
          对应变量的值，保持 XML 引用关系不变；若是硬编码数字，则直接改 Prop text。

        各类型支持的 fields 字段：
          标准线程组（standard）：
            num_threads, ramp_time, loop_count, loop_forever, scheduler, duration, delay
          SteppingThreadGroup（stepping）：
            num_threads, initial_delay, start_users_count, start_users_burst,
            start_users_period, stop_users_count, stop_users_period, flight_time, ramp_up
          UltimateThreadGroup（ultimate）：
            rows: list[UltimateConfig] — 按位置覆盖现有行数据，不增删行

        Args:
            index:  线程组序号（0-based，按 XML 出现顺序，与 ThreadGroupConfig.index 对应）
            fields: 要修改的字段，以 keyword argument 传入
        Raises:
            IndexError: index 超出线程组数量范围
        """
        tgs = self._find_thread_groups()
        if index >= len(tgs):
            raise IndexError(
                f"线程组索引越界：index={index}，当前 JMX 共有 {len(tgs)} 个线程组"
            )
        tg = tgs[index]  # type: ignore[index]
        if tg.tag in _STD_TG_TAGS:
            self._apply_standard_tg(tg, fields)
        elif tg.tag == _STEPPING_TAG:
            self._apply_stepping_tg(tg, fields)
        elif tg.tag == _ULTIMATE_TAG:
            self._apply_ultimate_tg(tg, fields)

    # ──────────────── 线程组写入辅助 ────────────────

    def _write_field(self, tg: ET.Element, prop_name: str, value: int) -> None:
        """
        向线程组的指定 Prop 写入整数值，自动处理变量引用。

        写入流程：
          1. 读取该 Prop 当前 text
          2. 若是 ${varname} → 改用户变量表（保持 XML 引用关系完整）
          3. 若是硬编码值 → 直接改 Prop text

        Args:
            tg:        线程组 Element
            prop_name: Prop 的 name 属性值（如 "ThreadGroup.num_threads"）
            value:     要写入的整数值
        """
        raw = self._get_prop(tg, prop_name)
        m = re.match(r"^\$\{(\w+)}", raw)
        if m:
            self.set_user_vars({m.group(1): str(value)})
        else:
            self._set_prop(tg, prop_name, str(value))

    def _apply_standard_tg(self, tg: ET.Element, fields: dict) -> None:
        """
        写入标准线程组字段（内部辅助，供 apply_thread_group 调用）。

        num_threads / ramp_time / duration / delay 经 _write_field 处理变量引用；
        scheduler 直接写布尔字符串（"true"/"false"）；
        loop 相关字段写入 LoopController 子节点（不在 ThreadGroup 本身）。

        Args:
            tg:     标准线程组 XML 元素
            fields: 待写入的字段字典（只处理已包含的 key，未传入的字段不覆盖）
        """
        for prop_name, key in (
            ("ThreadGroup.num_threads", "num_threads"),
            ("ThreadGroup.ramp_time",   "ramp_time"),
            ("ThreadGroup.duration",    "duration"),
            ("ThreadGroup.delay",       "delay"),
        ):
            if key in fields:
                self._write_field(tg, prop_name, int(fields[key]))

        if "scheduler" in fields:
            self._set_prop(tg, "ThreadGroup.scheduler", str(fields["scheduler"]).lower())

        # 循环配置存在嵌套的 LoopController 子节点中
        loop_el = tg.find("elementProp[@name='ThreadGroup.main_controller']")
        if loop_el is not None:
            if "loop_forever" in fields:
                self._set_prop(loop_el, "LoopController.continue_forever",
                               str(bool(fields["loop_forever"])).lower())
            if "loop_count" in fields:
                self._set_prop(loop_el, "LoopController.loops", str(fields["loop_count"]))

    def _apply_stepping_tg(self, tg: ET.Element, fields: dict) -> None:
        """
        写入 SteppingThreadGroup 字段（内部辅助，供 apply_thread_group 调用）。

        字段名到 XML Prop name 的映射在 mapping 中维护，
        均经 _write_field 处理，支持 ${varname} 变量引用透明写入。

        Args:
            tg:     SteppingThreadGroup XML 元素
            fields: 待写入的字段字典
        """
        mapping = {
            "num_threads":        "ThreadGroup.num_threads",
            "initial_delay":      "Threads initial delay",
            "start_users_count":  "Start users count",
            "start_users_burst":  "Start users count burst",
            "start_users_period": "Start users period",
            "stop_users_count":   "Stop users count",
            "stop_users_period":  "Stop users period",
            "flight_time":        "flighttime",
            "ramp_up":            "rampUp",
        }
        for key, prop_name in mapping.items():
            if key in fields:
                self._write_field(tg, prop_name, int(fields[key]))

    def _apply_ultimate_tg(self, tg: ET.Element, fields: dict) -> None:
        """
        写入 UltimateThreadGroup 行数据（内部辅助，供 apply_thread_group 调用）。

        UltimateThreadGroup 行数据无语义 key，按位置写入（与读取时的位置顺序一致）。
        超出现有行数的 rows 项自动忽略，不增删行，保证 XML 结构不变。

        Args:
            tg:     UltimateThreadGroup XML 元素
            fields: 必须包含 "rows" key，值为 list[UltimateConfig]
        """
        rows: Optional[list[UltimateConfig]] = fields.get("rows")
        if not rows:
            return
        data_col = tg.find("collectionProp[@name='ultimatethreadgroupdata']")
        if data_col is None:
            return
        row_cols = data_col.findall("collectionProp")
        for i, row in enumerate(rows):
            if i >= len(row_cols):
                break
            props = row_cols[i].findall("stringProp")  # type: ignore[index]
            if len(props) < 5:
                continue
            for j, val in enumerate([
                row.start_threads, row.initial_delay,
                row.startup_time, row.hold_load_for, row.shutdown_time,
            ]):
                props[j].text = str(val)

    # ──────────────── 序列化 ────────────────

    def to_bytes(self, encoding: str = "utf-8") -> bytes:
        """
        将当前（含修改）的 XML 树序列化为 bytes。

        Args:
            encoding: 字符编码，默认 utf-8
        Returns:
            完整的 JMX 文件内容（bytes），含 XML 声明头，可直接写文件或通过 SFTP 上传
        """
        buf = BytesIO()
        self._tree.write(buf, encoding=encoding, xml_declaration=True)  # type: ignore[arg-type]
        return buf.getvalue()

    def to_string(self, encoding: str = "utf-8") -> str:
        """将 XML 树序列化为字符串，编码默认 utf-8"""
        return self.to_bytes(encoding).decode(encoding)


# ====================== 业务函数 ======================

def apply_scenario_config(
    jmx_content: bytes,
    *,
    thread_count: int,
    ramp_up_time: int,
    loop_count: Optional[int] = 1,
    loop_forever: bool = False,
    duration: Optional[int] = None,
    startup_delay: int = 0,
) -> bytes:
    """
    压测执行前将场景配置注入 JMX，返回修改后的 bytes。

    执行链路：MinIO 下载 JMX → 本函数注入参数 → SFTP 上传到压力机执行。
    自动处理变量引用：若脚本中线程数是 ${threads}，则修改变量表保持引用不变。

    loop_forever 与 duration 互斥说明：
      loop_forever=True  → 启用调度器（scheduler=True），duration 必填，loop_count 无效
      loop_forever=False → 关闭调度器，使用 loop_count，duration 参数忽略

    UltimateThreadGroup 行结构无法统一赋值，自动跳过；disabled 线程组同样跳过。

    Args:
        jmx_content:   原始 JMX 文件内容（bytes，从 MinIO 下载）
        thread_count:  单节点并发线程数（对应 PerfScenarioConfigModel.thread_count）
        ramp_up_time:  Ramp-up 爬坡时间（秒，对应 .ramp_up_time）
        loop_count:    循环次数（对应 .loop_count；loop_forever=True 时忽略）
        loop_forever:  是否永远循环（对应 .loop_forever==1）
        duration:      持续时间（秒；loop_forever=True 时必填，对应 .duration）
        startup_delay: 启动延迟（秒，对应 .startup_delay）
    Returns:
        修改后的 JMX bytes，可直接通过 SFTP 写入压力机
    """
    parser = JMXParser(jmx_content)

    # 组装写入字段：loop_forever/loop_count 互斥，按模式选择不同字段
    fields: dict = {
        "num_threads":  thread_count,
        "ramp_time":    ramp_up_time,
        "delay":        startup_delay,
        "loop_forever": loop_forever,
    }
    if loop_forever:
        fields["scheduler"] = True
        fields["duration"]  = duration or 0
    else:
        fields["scheduler"]  = False
        fields["loop_count"] = loop_count if loop_count is not None else 1

    # 遍历所有线程组，跳过 UltimateThreadGroup（行结构无法统一赋值）和 disabled 项
    for tg in parser.get_thread_groups():
        if tg.thread_type == "ultimate" or not tg.enabled:
            continue
        parser.apply_thread_group(tg.index, **fields)

    return parser.to_bytes()


def _build_standard_jmx_fields(p: dict) -> dict:
    """
    将 DB 子配置字段（standard 类型）映射为 apply_thread_group 所需的 kwargs。
    loop_forever 互斥说明：
      loop_forever=True  → scheduler=True，duration 必填，loop_count 忽略
      loop_forever=False → scheduler=False，使用 loop_count，duration 忽略
    """
    loop_forever = bool(p.get('loop_forever', False))
    fields: dict = {
        'num_threads':  int(p['thread_count']),
        'ramp_time':    int(p.get('ramp_up_time') or 1),
        'delay':        int(p.get('startup_delay') or 0),
        'loop_forever': loop_forever,
    }
    if loop_forever:
        fields['scheduler'] = True
        fields['duration']  = int(p.get('duration') or 0)
    else:
        fields['scheduler']  = False
        fields['loop_count'] = int(p.get('loop_count') or 1)
    return fields


def _build_stepping_jmx_fields(p: dict) -> dict:
    """
    将 DB 子配置字段（stepping 类型，step_ 前缀）映射为 apply_thread_group 所需的 kwargs。

    DB 字段名（step_*）→ JMX 写入字段名（无前缀）的映射在此处统一维护，
    与 _apply_stepping_tg 内的 Prop name 保持一致。
    """
    return {
        'num_threads':        int(p['thread_count']),
        'initial_delay':      int(p.get('step_initial_delay') or 0),
        'start_users_count':  int(p.get('step_start_users_count') or 1),
        'start_users_burst':  int(p.get('step_start_users_burst') or 0),
        'start_users_period': int(p.get('step_start_users_period') or 5),
        'stop_users_count':   int(p.get('step_stop_users_count') or 0),
        'stop_users_period':  int(p.get('step_stop_users_period') or 0),
        'flight_time':        int(p.get('step_flight_time') or 30),
        'ramp_up':            int(p.get('step_ramp_up') or 0),
    }


def _build_ultimate_jmx_fields(p: dict) -> dict:
    """
    将 DB 子配置字段（ultimate 类型）映射为 apply_thread_group 所需的 kwargs。

    ultimate_rows 为 JSON 数组（list[dict]），每项转换为 UltimateConfig dataclass。
    字段名与 UltimateConfig 完全一致，可直接 **解包。
    """
    raw_rows: list = p.get('ultimate_rows') or []
    rows = [
        UltimateConfig(
            start_threads = int(r.get('start_threads', 1)),
            initial_delay = int(r.get('initial_delay', 0)),
            startup_time  = int(r.get('startup_time',  0)),
            hold_load_for = int(r.get('hold_load_for', 0)),
            shutdown_time = int(r.get('shutdown_time', 0)),
        )
        for r in raw_rows
    ]
    return {'rows': rows}


def apply_jmx_by_type(
    jmx_bytes: bytes,
    thread_type: str,
    db_params: dict,
    tg_index: Optional[int] = None,
) -> bytes:
    """
    按线程组类型将参数注入 JMX，只修改类型匹配且已启用的线程组，返回修改后的 bytes。

    使用场景：
      - 联调（inspect）：db_params 来自 perf_config_params 中的预置 JSON 配置项
      - 正式执行（execute）：db_params 来自 perf_scenario_configs 当前启用子配置

    db_params 使用 DB 字段名（与 PerfScenarioConfigModel 保持一致）：
      standard  : thread_count, ramp_up_time, loop_count, loop_forever, duration, startup_delay
      stepping  : thread_count, step_initial_delay, step_start_users_count, ...（step_ 前缀字段）
      ultimate  : ultimate_rows（list[dict]，每项含 start_threads/initial_delay/...)

    Args:
        jmx_bytes:   原始 JMX bytes（从 MinIO 下载）
        thread_type: 线程组类型（standard / stepping / ultimate）
        db_params:   参数字典，key 为 DB 字段名
        tg_index:    指定写入的线程组位置（0-based XML 顺序）；
                     None=广播写入所有匹配类型的已启用线程组（联调 / 单配置执行）；
                     非 None=精确写入指定位置的线程组（多配置执行时按位置配对）
    Returns:
        注入参数后的 JMX bytes
    """
    parser = JMXParser(jmx_bytes)

    # 按类型组装 JMX 写入字段
    if thread_type == 'standard':
        fields = _build_standard_jmx_fields(db_params)
    elif thread_type == 'stepping':
        fields = _build_stepping_jmx_fields(db_params)
    elif thread_type == 'ultimate':
        fields = _build_ultimate_jmx_fields(db_params)
    else:
        return jmx_bytes  # 未知类型不做修改，原样返回

    # 只修改类型匹配的已启用线程组；tg_index 非 None 时进一步限定到指定位置
    for tg in parser.get_thread_groups():
        if tg.thread_type != thread_type or not tg.enabled:
            continue
        if tg_index is not None and tg.index != tg_index:
            continue
        parser.apply_thread_group(tg.index, **fields)

    return parser.to_bytes()


def parse_jmx_summary(jmx_content: bytes) -> dict:
    """
    解析 JMX 文件摘要，返回可直接 JSON 序列化入库的 dict。

    在文件上传确认（confirm_upload）后调用，将摘要缓存到 DB 字段，
    避免前端每次查看文件详情都重新解析 XML。

    Args:
        jmx_content: JMX 文件内容（bytes，从 MinIO 读取）
    Returns:
        dict，结构如下：
        {
          "test_plan_name": str,
          "user_vars": {name: value},
          "thread_groups": [
            {
              index, tg_type, testname, enabled,
              num_threads_raw, num_threads,
              ramp_time, loop_count, loop_forever, scheduler, duration, delay,
              stepping: {initial_delay, start_users_count, start_users_burst,
                         start_users_period, stop_users_count, stop_users_period,
                         flight_time, ramp_up} | None,
              ultimate_rows: [{start_threads, initial_delay, startup_time,
                               hold_load_for, shutdown_time}] | None
            }
          ],
          "backend_listeners": [{testname, enabled, classname, influxdb_url, ...}],
          "result_collectors": [{testname, enabled, gui_class, is_debug}],
          "csv_data_files": [str],
          "total_threads": int,
          "debug_listeners_on": [str]
        }
    """
    parser = JMXParser(jmx_content)
    s      = parser.get_summary()

    def _tg_to_dict(tg: ThreadGroupConfig) -> dict:
        """将 ThreadGroupConfig dataclass 转换为可 JSON 序列化的 dict"""
        d: dict = {
            "index":           tg.index,
            "tg_type":         tg.thread_type,
            "tag":             tg.tag,
            "testname":        tg.testname,
            "enabled":         tg.enabled,
            "num_threads_raw": tg.num_threads_raw,
            "num_threads":     tg.num_threads,
            "ramp_time":       tg.ramp_time,
            "loop_count":      tg.loop_count,
            "loop_forever":    tg.loop_forever,
            "scheduler":       tg.scheduler,
            "duration":        tg.duration,
            "delay":           tg.delay,
            "stepping":        None,
            "ultimate_rows":   None,
        }
        if tg.stepping is not None:
            d["stepping"] = {
                "initial_delay":      tg.stepping.initial_delay,
                "start_users_count":  tg.stepping.start_users_count,
                "start_users_burst":  tg.stepping.start_users_burst,
                "start_users_period": tg.stepping.start_users_period,
                "stop_users_count":   tg.stepping.stop_users_count,
                "stop_users_period":  tg.stepping.stop_users_period,
                "flight_time":        tg.stepping.flight_time,
                "ramp_up":            tg.stepping.ramp_up,
            }
        if tg.ultimate_rows is not None:
            d["ultimate_rows"] = [
                {
                    "start_threads": r.start_threads,
                    "initial_delay": r.initial_delay,
                    "startup_time":  r.startup_time,
                    "hold_load_for": r.hold_load_for,
                    "shutdown_time": r.shutdown_time,
                }
                for r in tg.ultimate_rows
            ]
        return d

    return {
        "test_plan_name":     s.test_plan_name,
        "user_vars":          s.user_vars,
        "thread_groups":      [_tg_to_dict(tg) for tg in s.thread_groups],
        "backend_listeners":  s.backend_listeners,
        "result_collectors":  s.result_collectors,
        "csv_data_files":     s.csv_data_files,
        "total_threads":      s.total_threads,
        "debug_listeners_on": s.debug_listeners_on,
        "http_samplers":      s.http_samplers,
        "user_var_descs":     s.user_var_descs,
    }


def extract_jmx_thread_config(jmx_content: bytes) -> Optional[str]:
    """
    提取 JMX 中所有启用的线程组配置，序列化为 JSON 字符串存入 perf_files.parsed_thread_config。

    只保留场景子配置表单所需字段（字段名与 PerfScenarioConfig Schema 完全对齐），含 tg_index
    （XML 中的位置，0-based），供前端新建场景时自动识别线程组类型并预填参数。

    存储格式（thread_type 与字典 perf_thread_group_type 值对应）：
      SetUp / ThreadGroup (thread_type='0'/'1')：
        tg_index, thread_type, name,
        thread_count, ramp_up_time, loop_count, loop_forever, duration, startup_delay
      SteppingThreadGroup (thread_type='2')：
        tg_index, thread_type, name,
        thread_count, step_initial_delay, step_start_users_count, step_start_users_burst,
        step_start_users_period, step_stop_users_count, step_stop_users_period,
        step_flight_time, step_ramp_up
      UltimateThreadGroup (thread_type='3')：
        tg_index, thread_type, name, ultimate_rows

    disabled 线程组不存储；无启用线程组或解析出错返回 None。
    """
    import json as _json

    # XML tag → (DB dict value, tg_type 标识)
    _TAG_MAP = {
        'SetupThreadGroup':     ('0', 'setup'),
        'TearDownThreadGroup':  ('0', 'teardown'),   # 与 setup 共用 thread_type='0'
        'ThreadGroup':          ('1', 'standard'),
    }

    try:
        summary = parse_jmx_summary(jmx_content)
    except Exception:
        return None

    groups: list[dict] = []
    for tg in summary.get('thread_groups', []):
        if not tg.get('enabled', True):
            continue

        raw_type = tg.get('tg_type', 'standard')   # 'standard' | 'stepping' | 'ultimate'
        tag      = tg.get('tag', 'ThreadGroup')
        idx      = tg.get('index', 0)

        if raw_type == 'standard':
            db_type, _ = _TAG_MAP.get(tag, ('1', 'standard'))
            lf         = tg.get('loop_forever', False)
            raw_lc     = tg.get('loop_count', 1)
            # JMeter 有两种"永远循环"写法：
            #   1. LoopController.continue_forever=true → loop_forever=True
            #   2. LoopController.loops=-1（部分 JMeter 版本的旧写法）
            # 统一归一为 loop_forever=1，loop_count 置 None
            if raw_lc == -1:
                lf = True
            dur  = tg.get('duration') or None
            item: dict = {
                'tg_index':     idx,
                'thread_type':  db_type,
                'name':         tg.get('testname', ''),
                'thread_count': tg.get('num_threads', 1),
                'ramp_up_time': tg.get('ramp_time', 1),
                'loop_count':   None if lf else raw_lc,
                'loop_forever': 1 if lf else 0,
                'duration':     dur,
                'startup_delay': tg.get('delay', 0),
            }
        elif raw_type == 'stepping':
            s    = tg.get('stepping') or {}
            item = {
                'tg_index':                idx,
                'thread_type':             '2',
                'name':                    tg.get('testname', ''),
                'thread_count':            tg.get('num_threads', 0),
                'step_initial_delay':      s.get('initial_delay', 0),
                'step_start_users_count':  s.get('start_users_count', 1),
                'step_start_users_burst':  s.get('start_users_burst', 0),
                'step_start_users_period': s.get('start_users_period', 1),
                'step_stop_users_count':   s.get('stop_users_count', 0),
                'step_stop_users_period':  s.get('stop_users_period', 0),
                'step_flight_time':        s.get('flight_time', 0),
                'step_ramp_up':            s.get('ramp_up', 0),
            }
        elif raw_type == 'ultimate':
            item = {
                'tg_index':      idx,
                'thread_type':   '3',
                'name':          tg.get('testname', ''),
                'ultimate_rows': tg.get('ultimate_rows') or [],
            }
        else:
            continue

        groups.append(item)

    if not groups:
        return None
    return _json.dumps({'thread_groups': groups}, ensure_ascii=False)


def calc_jmx_estimated_duration(thread_groups: list) -> Tuple[Optional[int], bool]:
    """
    根据启用线程组列表估算压测总耗时（累加模式：多线程组顺序执行含启动延迟）。

    计算规则：
      SetUp/ThreadGroup (loop_forever=0) → 不可精确计算，标记 has_unknown=True，跳过累加
      SetUp/ThreadGroup (loop_forever=1, duration>0) → startup_delay + ramp_up_time + duration
      SteppingThreadGroup → step_initial_delay + T_up + step_flight_time + T_down
        T_up   = ceil((thread_count - burst) / count) × period
        T_down = ceil(thread_count / stop_count) × stop_period
      UltimateThreadGroup → max(initial_delay + startup_time + hold_load_for + shutdown_time) per row

    Returns:
        (known_secs, has_unknown)：
          - known_secs：可计算部分的累计秒数（None 表示无可算线程组）
          - has_unknown：True 表示存在使用循环次数的线程组，耗时为估算值，进度条仅供参考
    """
    if not thread_groups:
        return None, False

    total       = 0
    has_unknown = False

    for g in thread_groups:
        tt = str(g.get('thread_type', '1'))

        if tt in ('0', '1'):
            lf  = g.get('loop_forever', 0)
            dur = g.get('duration') or 0
            # startup_delay / ramp_up_time 不依赖循环方式，始终可算
            total += (g.get('startup_delay') or 0) + (g.get('ramp_up_time') or 0)
            if lf and dur:
                # 永远循环 + 已填持续时间 → duration 也可算
                total += dur
            else:
                # 循环次数控制，或永远循环但未填 duration → 执行时长未知
                has_unknown = True

        elif tt == '2':
            max_t  = g.get('thread_count') or 0
            burst  = g.get('step_start_users_burst') or 0
            count  = g.get('step_start_users_count') or 0
            period = g.get('step_start_users_period') or 0
            s_cnt  = g.get('step_stop_users_count') or 0
            s_per  = g.get('step_stop_users_period') or 0
            flight = g.get('step_flight_time') or 0
            init   = g.get('step_initial_delay') or 0

            steps_up   = math.ceil((max_t - burst) / count) if count > 0 and max_t > burst else 0
            t_up       = steps_up * period
            steps_down = math.ceil(max_t / s_cnt) if s_cnt > 0 and max_t > 0 else 0
            t_down     = steps_down * s_per
            total     += init + t_up + flight + t_down

        elif tt == '3':
            rows = g.get('ultimate_rows') or []
            if not rows:
                continue
            row_times = [
                (r.get('initial_delay') or 0) + (r.get('startup_time') or 0) +
                (r.get('hold_load_for') or 0) + (r.get('shutdown_time') or 0)
                for r in rows
            ]
            total += max(row_times) if row_times else 0

    return (total if total > 0 else None), has_unknown
