#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""脚本执行运行时"""

from __future__ import annotations

import asyncio
import builtins as _builtins
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.config.setting import config as app_config


_SAFE_IMPORT_MODULES = frozenset({
    "random", "math", "time", "json", "re", "datetime", "string",
    "hashlib", "base64", "uuid", "collections", "itertools", "functools",
    "copy", "decimal", "typing", "statistics", "operator", "bisect",
    "heapq", "array", "struct", "textwrap", "unicodedata", "calendar",
    "fractions", "numbers", "pprint", "reprlib", "enum", "dataclasses",
})

_REAL_IMPORT = _builtins.__import__
_RESULT_MARKER = "__NTEST_NATIVE_RESULT__"


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = str(name or "").split(".", 1)[0]
    if root not in _SAFE_IMPORT_MODULES:
        raise ImportError(f"不允许导入模块: {name}（沙盒仅支持常用标准库；可切换原生模式）")
    return _REAL_IMPORT(name, globals, locals, fromlist, level)


def build_script_builtins() -> Dict[str, Any]:
    blocked = {
        "open", "exec", "eval", "compile", "breakpoint", "input",
        "memoryview", "exit", "quit", "help", "copyright", "credits", "license",
    }
    safe = {k: v for k, v in _builtins.__dict__.items() if k not in blocked}
    safe["__import__"] = _safe_import
    return safe


def resolve_exec_mode(override: Optional[str] = None) -> str:
    """sandbox | native；请求覆盖优先，否则读全局配置。"""
    raw = (override or getattr(app_config, "SCRIPT_EXEC_MODE", None) or "sandbox")
    mode = str(raw).strip().lower()
    return "native" if mode in ("native", "host", "subprocess") else "sandbox"


@dataclass
class ScriptRunResult:
    success: bool
    output: str = ""
    vars: Dict[str, Any] = field(default_factory=dict)
    error: str = ""
    mode: str = "sandbox"
    logs: list = field(default_factory=list)


def run_sandbox(
    code: str,
    *,
    ntest: Any,
    extra_globals: Optional[Dict[str, Any]] = None,
) -> ScriptRunResult:
    import contextlib
    import io

    captured = io.StringIO()
    exec_globals: Dict[str, Any] = {
        "__builtins__": build_script_builtins(),
        "__name__": "<ntest_script>",
        "ntest": ntest,
        "json": _REAL_IMPORT("json"),
        "re": _REAL_IMPORT("re"),
        "datetime": _REAL_IMPORT("datetime"),
        "random": _REAL_IMPORT("random"),
        "math": _REAL_IMPORT("math"),
        "time": _REAL_IMPORT("time"),
        "uuid": _REAL_IMPORT("uuid"),
        "base64": _REAL_IMPORT("base64"),
        "hashlib": _REAL_IMPORT("hashlib"),
    }
    if extra_globals:
        exec_globals.update(extra_globals)
    # 若未显式注入 pm，用 ntest + request/response 构造薄兼容层
    if "pm" not in exec_globals:
        exec_globals["pm"] = build_pm_shim(
            ntest,
            request=exec_globals.get("request"),
            response=exec_globals.get("response"),
        )

    try:
        with contextlib.redirect_stdout(captured):
            exec(compile(code, "<script>", "exec"), exec_globals)  # noqa: S102
        output = captured.getvalue()
        exported = dict(getattr(ntest, "exported_vars", {}) or {})
        # 允许脚本直接改 request 对象并回写
        req_obj = exec_globals.get("request")
        if isinstance(req_obj, dict):
            exported["__request__"] = req_obj
        return ScriptRunResult(
            success=True,
            output=output,
            vars=exported,
            mode="sandbox",
            logs=[f"脚本输出: {output[:300]}" if output else "脚本执行完成（沙盒）"],
        )
    except Exception as e:
        return ScriptRunResult(
            success=False,
            output=captured.getvalue(),
            error=str(e)[:500],
            mode="sandbox",
            logs=[f"沙盒执行失败: {traceback.format_exc()[:300]}"],
        )


class SimpleNtest:
    """前后置脚本用的轻量 ntest（不依赖 VariableContext）。"""

    def __init__(self, session_vars: Optional[Dict[str, Any]] = None, env_vars: Optional[Dict[str, Any]] = None):
        self._vars = dict(session_vars or {})
        self._env = dict(env_vars or {})
        self.exported_vars: Dict[str, Any] = {}

    def get(self, key, default=None):
        if key in self._vars:
            return self._vars[key]
        return self._env.get(key, default)

    def set(self, key, value):
        self.exported_vars[key] = value
        self._vars[key] = value

    def env(self, key, default=None):
        return self._env.get(key, default)


def build_pm_shim(ntest: Any, request: Any = None, response: Any = None) -> Any:
    """Apifox/Postman 风格薄兼容：pm.environment / pm.variables / pm.request / pm.response / pm.test。"""

    class _Env:
        def get(self, key, default=None):
            return ntest.env(key, default) if hasattr(ntest, "env") else ntest.get(key, default)

        def set(self, key, value):
            ntest.set(key, value)

    class _Vars:
        def get(self, key, default=None):
            return ntest.get(key, default)

        def set(self, key, value):
            ntest.set(key, value)

    class _Resp:
        def __init__(self, res):
            self._res = res if isinstance(res, dict) else {}

        @property
        def code(self):
            return self._res.get("code")

        @property
        def headers(self):
            return self._res.get("header") or self._res.get("headers") or {}

        def json(self):
            return self._res.get("body")

        def text(self):
            body = self._res.get("body")
            if isinstance(body, str):
                return body
            try:
                return json.dumps(body, ensure_ascii=False)
            except Exception:
                return str(body)

    class _Pm:
        def __init__(self):
            self.environment = _Env()
            self.variables = _Vars()
            self.request = request if isinstance(request, dict) else {}
            self.response = _Resp(response) if response is not None else None

        def test(self, name, fn):
            try:
                fn()
            except Exception as e:
                raise AssertionError(f"pm.test({name!r}) failed: {e}") from e

    return _Pm()


def _python_bin() -> str:
    configured = str(getattr(app_config, "SCRIPT_NATIVE_PYTHON", "") or "").strip()
    if configured:
        return configured
    # 优先当前解释器，保证与后端同一环境
    return sys.executable or shutil.which("python") or shutil.which("python3") or "python"


def _node_bin() -> str:
    configured = str(getattr(app_config, "SCRIPT_NATIVE_NODE", "") or "").strip()
    return configured or shutil.which("node") or "node"


def _native_timeout() -> int:
    try:
        return max(int(getattr(app_config, "SCRIPT_NATIVE_TIMEOUT", 30) or 30), 1)
    except Exception:
        return 30


def _build_native_python_wrapper(user_code: str) -> str:
    # 注入 ntest / request / response / pm，并用 marker 回传 exported vars
    return f'''# -*- coding: utf-8 -*-
import json, os, sys
__name__ = "<ntest_script>"
_vars = json.loads(os.environ.get("NTEST_VARS", "{{}}") or "{{}}")
_env = json.loads(os.environ.get("NTEST_ENV", "{{}}") or "{{}}")
try:
    request = json.loads(os.environ.get("NTEST_REQUEST", "{{}}") or "{{}}")
except Exception:
    request = {{}}
try:
    response = json.loads(os.environ.get("NTEST_RESPONSE", "null") or "null")
except Exception:
    response = None
_exported = {{}}

class _Ntest:
    def get(self, key, default=None):
        if key in _vars:
            return _vars[key]
        return _env.get(key, default)
    def set(self, key, value):
        _exported[key] = value
        _vars[key] = value
    def env(self, key, default=None):
        return _env.get(key, default)

ntest = _Ntest()

class _PmEnv:
    def get(self, key, default=None):
        return ntest.env(key, default)
    def set(self, key, value):
        ntest.set(key, value)

class _PmVars:
    def get(self, key, default=None):
        return ntest.get(key, default)
    def set(self, key, value):
        ntest.set(key, value)

class _PmResp:
    def __init__(self, res):
        self._res = res if isinstance(res, dict) else {{}}
    @property
    def code(self):
        return self._res.get("code")
    @property
    def headers(self):
        return self._res.get("header") or self._res.get("headers") or {{}}
    def json(self):
        return self._res.get("body")
    def text(self):
        body = self._res.get("body")
        if isinstance(body, str):
            return body
        try:
            return json.dumps(body, ensure_ascii=False)
        except Exception:
            return str(body)

class _Pm:
    def __init__(self):
        self.environment = _PmEnv()
        self.variables = _PmVars()
        self.request = request
        self.response = _PmResp(response) if response is not None else None
    def test(self, name, fn):
        try:
            fn()
        except Exception as e:
            raise AssertionError("pm.test(%r) failed: %s" % (name, e)) from e

pm = _Pm()

try:
{ _indent(user_code, 4) }
except Exception as e:
    import traceback
    sys.stderr.write(traceback.format_exc())
    print("{_RESULT_MARKER}" + json.dumps({{"ok": False, "vars": _exported, "error": str(e)}}, ensure_ascii=False))
    raise SystemExit(1)

if isinstance(request, dict):
    _exported["__request__"] = request
print("{_RESULT_MARKER}" + json.dumps({{"ok": True, "vars": _exported}}, ensure_ascii=False, default=str))
'''


def _indent(code: str, spaces: int) -> str:
    pad = " " * spaces
    lines = (code or "").splitlines() or [""]
    return "\n".join(pad + (ln if ln.strip() else ln) for ln in lines)


def _parse_native_output(stdout: str) -> tuple[str, Dict[str, Any], Optional[str], bool]:
    output = stdout or ""
    vars_data: Dict[str, Any] = {}
    error = None
    ok = True
    if _RESULT_MARKER in output:
        before, _, after = output.rpartition(_RESULT_MARKER)
        output = before
        try:
            payload = json.loads(after.strip().splitlines()[0] if after.strip() else "{}")
            vars_data = payload.get("vars") or {}
            ok = bool(payload.get("ok", True))
            if payload.get("error"):
                error = str(payload["error"])
        except Exception:
            pass
    return output, vars_data, error, ok


def run_native_python(
    code: str,
    *,
    session_vars: Optional[Dict[str, Any]] = None,
    env_vars: Optional[Dict[str, Any]] = None,
    request_ctx: Optional[Dict[str, Any]] = None,
    response_ctx: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
) -> ScriptRunResult:
    py = _python_bin()
    timeout = timeout or _native_timeout()
    wrapper = _build_native_python_wrapper(code)
    env = os.environ.copy()
    env["NTEST_VARS"] = json.dumps(session_vars or {}, ensure_ascii=False, default=str)
    env["NTEST_ENV"] = json.dumps(env_vars or {}, ensure_ascii=False, default=str)
    env["NTEST_REQUEST"] = json.dumps(request_ctx or {}, ensure_ascii=False, default=str)
    env["NTEST_RESPONSE"] = json.dumps(response_ctx, ensure_ascii=False, default=str) if response_ctx is not None else "null"
    env["PYTHONIOENCODING"] = "utf-8"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8", prefix="ntest_script_"
        ) as f:
            f.write(wrapper)
            tmp_path = f.name

        proc = subprocess.run(
            [py, tmp_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            cwd=os.path.dirname(tmp_path),
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        output, vars_data, marker_err, ok = _parse_native_output(stdout)
        if proc.returncode != 0 or not ok:
            err = marker_err or (stderr.strip() or f"进程退出码 {proc.returncode}")
            return ScriptRunResult(
                success=False,
                output=(output + (("\n" + stderr) if stderr and stderr.strip() not in (output or "") else "")).strip(),
                vars=vars_data,
                error=err[:500],
                mode="native",
                logs=[f"原生 Python 执行失败（{py}）"],
            )
        return ScriptRunResult(
            success=True,
            output=output,
            vars=vars_data,
            mode="native",
            logs=[f"原生 Python 执行完成（{py}）" + (f"；stderr: {stderr[:200]}" if stderr.strip() else "")],
        )
    except subprocess.TimeoutExpired:
        return ScriptRunResult(
            success=False,
            error=f"原生执行超时（{timeout}s）",
            mode="native",
            logs=["原生 Python 执行超时"],
        )
    except FileNotFoundError:
        return ScriptRunResult(
            success=False,
            error=f"未找到 Python 可执行文件: {py}",
            mode="native",
            logs=["请配置 SCRIPT_NATIVE_PYTHON 或确保 PATH 中有 python"],
        )
    except Exception as e:
        return ScriptRunResult(
            success=False,
            error=str(e)[:500],
            mode="native",
            logs=[f"原生执行异常: {traceback.format_exc()[:300]}"],
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def run_native_js(
    code: str,
    *,
    session_vars: Optional[Dict[str, Any]] = None,
    env_vars: Optional[Dict[str, Any]] = None,
    request_ctx: Optional[Dict[str, Any]] = None,
    response_ctx: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
) -> ScriptRunResult:
    node = _node_bin()
    timeout = timeout or _native_timeout()
    wrapper = _build_native_js_wrapper(code)
    env = os.environ.copy()
    env["NTEST_VARS"] = json.dumps(session_vars or {}, ensure_ascii=False, default=str)
    env["NTEST_ENV"] = json.dumps(env_vars or {}, ensure_ascii=False, default=str)
    env["NTEST_REQUEST"] = json.dumps(request_ctx or {}, ensure_ascii=False, default=str)
    env["NTEST_RESPONSE"] = json.dumps(response_ctx, ensure_ascii=False, default=str) if response_ctx is not None else "null"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, encoding="utf-8", prefix="ntest_script_"
        ) as f:
            f.write(wrapper)
            tmp_path = f.name

        proc = subprocess.run(
            [node, tmp_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
            cwd=os.path.dirname(tmp_path),
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        output, vars_data, marker_err, ok = _parse_native_output(stdout)
        if proc.returncode != 0 or not ok:
            err = marker_err or (stderr.strip() or f"进程退出码 {proc.returncode}")
            return ScriptRunResult(
                success=False,
                output=(output + (("\n" + stderr) if stderr and stderr.strip() not in (output or "") else "")).strip(),
                vars=vars_data,
                error=err[:500],
                mode="native",
                logs=[f"原生 JavaScript 执行失败（{node}）"],
            )
        return ScriptRunResult(
            success=True,
            output=output,
            vars=vars_data,
            mode="native",
            logs=[f"原生 JavaScript 执行完成（{node}）" + (f"；stderr: {stderr[:200]}" if stderr.strip() else "")],
        )
    except subprocess.TimeoutExpired:
        return ScriptRunResult(
            success=False,
            error=f"原生执行超时（{timeout}s）",
            mode="native",
            logs=["原生 JavaScript 执行超时"],
        )
    except FileNotFoundError:
        return ScriptRunResult(
            success=False,
            error=f"未找到 Node.js 可执行文件: {node}",
            mode="native",
            logs=["请安装 Node.js，或在 .env 配置 SCRIPT_NATIVE_NODE"],
        )
    except Exception as e:
        return ScriptRunResult(
            success=False,
            error=str(e)[:500],
            mode="native",
            logs=[f"原生 JS 执行异常: {traceback.format_exc()[:300]}"],
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


def _build_native_js_wrapper(user_code: str) -> str:
    # CommonJS 包装，注入 global.ntest / request / response / pm，并用 marker 回传变量
    marker = _RESULT_MARKER
    return f"""'use strict';
const _vars = JSON.parse(process.env.NTEST_VARS || '{{}}');
const _env = JSON.parse(process.env.NTEST_ENV || '{{}}');
let _request = {{}};
try {{ _request = JSON.parse(process.env.NTEST_REQUEST || '{{}}'); }} catch (_) {{ _request = {{}}; }}
let _response = null;
try {{ _response = JSON.parse(process.env.NTEST_RESPONSE || 'null'); }} catch (_) {{ _response = null; }}
const _exported = {{}};
global.ntest = {{
  get(key, defVal) {{
    if (Object.prototype.hasOwnProperty.call(_vars, key)) return _vars[key];
    if (Object.prototype.hasOwnProperty.call(_env, key)) return _env[key];
    return defVal;
  }},
  set(key, value) {{
    _exported[key] = value;
    _vars[key] = value;
  }},
  env(key, defVal) {{
    if (Object.prototype.hasOwnProperty.call(_env, key)) return _env[key];
    return defVal;
  }},
}};
global.request = _request;
global.response = _response;
global.pm = {{
  environment: {{
    get: (k, d) => global.ntest.env(k, d),
    set: (k, v) => global.ntest.set(k, v),
  }},
  variables: {{
    get: (k, d) => global.ntest.get(k, d),
    set: (k, v) => global.ntest.set(k, v),
  }},
  request: global.request,
  response: _response ? {{
    code: _response.code,
    headers: _response.header || _response.headers || {{}},
    json: () => _response.body,
    text: () => {{
      const b = _response.body;
      if (typeof b === 'string') return b;
      try {{ return JSON.stringify(b); }} catch (_) {{ return String(b); }}
    }},
  }} : undefined,
  test: (name, fn) => {{
    try {{ fn(); }} catch (e) {{
      throw new Error('pm.test(' + JSON.stringify(name) + ') failed: ' + (e && e.message ? e.message : e));
    }}
  }},
}};

try {{
{ _indent(user_code, 2) }
  if (global.request && typeof global.request === 'object') {{
    _exported.__request__ = global.request;
  }}
  console.log('{marker}' + JSON.stringify({{ ok: true, vars: _exported }}));
}} catch (e) {{
  console.error(e && e.stack ? e.stack : String(e));
  console.log('{marker}' + JSON.stringify({{ ok: false, vars: _exported, error: String(e && e.message ? e.message : e) }}));
  process.exit(1);
}}
"""


def normalize_language(language: Optional[str]) -> str:
    lang = str(language or "python").strip().lower()
    if lang in ("js", "javascript", "node", "nodejs"):
        return "javascript"
    if lang in ("py", "python", ""):
        return "python"
    return lang


def run_native(
    code: str,
    *,
    language: str = "python",
    session_vars: Optional[Dict[str, Any]] = None,
    env_vars: Optional[Dict[str, Any]] = None,
    request_ctx: Optional[Dict[str, Any]] = None,
    response_ctx: Optional[Dict[str, Any]] = None,
    timeout: Optional[int] = None,
) -> ScriptRunResult:
    lang = normalize_language(language)
    if lang == "javascript":
        return run_native_js(
            code,
            session_vars=session_vars,
            env_vars=env_vars,
            request_ctx=request_ctx,
            response_ctx=response_ctx,
            timeout=timeout,
        )
    if lang == "python":
        return run_native_python(
            code,
            session_vars=session_vars,
            env_vars=env_vars,
            request_ctx=request_ctx,
            response_ctx=response_ctx,
            timeout=timeout,
        )
    return ScriptRunResult(
        success=False,
        error=f"暂不支持语言: {language}（当前支持 python / javascript）",
        mode="native",
    )


async def run_script_async(
    code: str,
    *,
    mode: Optional[str] = None,
    ntest: Any = None,
    session_vars: Optional[Dict[str, Any]] = None,
    env_vars: Optional[Dict[str, Any]] = None,
    language: str = "python",
    request_ctx: Optional[Dict[str, Any]] = None,
    response_ctx: Optional[Dict[str, Any]] = None,
    extra_globals: Optional[Dict[str, Any]] = None,
) -> ScriptRunResult:
    lang = normalize_language(language)

    if lang == "javascript":
        return await asyncio.to_thread(
            run_native_js,
            code,
            session_vars=session_vars,
            env_vars=env_vars,
            request_ctx=request_ctx,
            response_ctx=response_ctx,
        )
    resolved = resolve_exec_mode(mode)
    if resolved == "native":
        return await asyncio.to_thread(
            run_native_python,
            code,
            session_vars=session_vars,
            env_vars=env_vars,
            request_ctx=request_ctx,
            response_ctx=response_ctx,
        )
    if ntest is None:
        ntest = SimpleNtest(session_vars=session_vars, env_vars=env_vars)
    extras = dict(extra_globals or {})
    if request_ctx is not None and "request" not in extras:
        extras["request"] = request_ctx
    if response_ctx is not None and "response" not in extras:
        extras["response"] = response_ctx
    return await asyncio.to_thread(run_sandbox, code, ntest=ntest, extra_globals=extras or None)


# ── 代码生成：pytest / unittest 运行 ──────────────────────────────────

_CODEGEN_SAFE_IMPORTS = _SAFE_IMPORT_MODULES | frozenset({
    "requests", "pytest", "unittest", "urllib", "urllib3", "http", "ssl",
    "socket", "certifi", "charset_normalizer", "idna", "http.client",
})


def _codegen_safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = str(name or "").split(".", 1)[0]
    if root not in _CODEGEN_SAFE_IMPORTS:
        raise ImportError(f"不允许导入模块: {name}（沙盒仅支持常用库 + requests；可切换原生模式）")
    return _REAL_IMPORT(name, globals, locals, fromlist, level)


def _run_discovered_tests(module_dict: Dict[str, Any]) -> tuple[bool, str]:
    """发现 Test* 类中的 test_* 方法并执行（兼容 pytest 风格与 unittest.TestCase）。"""
    import contextlib
    import io
    import types
    import unittest

    lines: list[str] = []
    failed = 0
    passed = 0

    # 优先走 unittest 标准发现（覆盖 unittest.TestCase）
    mod = types.ModuleType("generated_test")
    for k, v in module_dict.items():
        if k.startswith("__") and k not in ("__name__", "__file__"):
            continue
        setattr(mod, k, v)
    try:
        suite = unittest.defaultTestLoader.loadTestsFromModule(mod)
        if suite.countTestCases() > 0:
            buf = io.StringIO()
            result = unittest.TextTestRunner(stream=buf, verbosity=2).run(suite)
            return result.wasSuccessful(), buf.getvalue()
    except Exception:
        pass

    # pytest 风格：普通类 + test_* 方法
    for name, obj in list(module_dict.items()):
        if not isinstance(obj, type) or not str(name).startswith("Test"):
            continue
        try:
            instance = obj()
        except Exception as e:
            lines.append(f"ERROR {name}: 实例化失败 - {e}")
            failed += 1
            continue
        for method_name in sorted(dir(instance)):
            if not method_name.startswith("test_"):
                continue
            method = getattr(instance, method_name, None)
            if not callable(method):
                continue
            label = f"{name}::{method_name}"
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                    method()
                out = buf.getvalue().strip()
                lines.append(f"PASSED {label}" + (f"\n{out}" if out else ""))
                passed += 1
            except AssertionError as e:
                out = buf.getvalue().strip()
                lines.append(f"FAILED {label}: {e}" + (f"\n{out}" if out else ""))
                failed += 1
            except Exception as e:
                out = buf.getvalue().strip()
                tb = traceback.format_exc()
                lines.append(f"ERROR {label}: {e}\n{tb}" + (f"\n{out}" if out else ""))
                failed += 1

    summary = f"\n{'=' * 40}\n{passed} passed, {failed} failed"
    lines.append(summary)
    return failed == 0 and passed > 0, "\n".join(lines) if lines else "未发现可执行的测试方法"


def run_generated_sandbox(code: str, framework: str = "pytest") -> ScriptRunResult:
    """沙盒运行生成的 Python 测试代码（注入 requests，受限 import）。"""
    import contextlib
    import io

    safe_builtins = build_script_builtins()
    safe_builtins["__import__"] = _codegen_safe_import

    captured = io.StringIO()
    exec_globals: Dict[str, Any] = {
        "__builtins__": safe_builtins,
        "__name__": "generated_test",
        "__file__": "<generated>",
    }
    try:
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            exec(compile(code, "<generated>", "exec"), exec_globals)  # noqa: S102
            ok, report = _run_discovered_tests(exec_globals)
        preamble = captured.getvalue()
        output = ((preamble + "\n") if preamble else "") + report
        return ScriptRunResult(
            success=ok,
            output=output,
            mode="sandbox",
            error="" if ok else "测试未全部通过",
            logs=[f"代码生成沙盒执行({framework})"],
        )
    except Exception as e:
        return ScriptRunResult(
            success=False,
            output=captured.getvalue(),
            error=str(e)[:500],
            mode="sandbox",
            logs=[f"沙盒执行失败: {traceback.format_exc()[:400]}"],
        )


def run_generated_native(code: str, framework: str = "pytest", timeout: Optional[int] = None) -> ScriptRunResult:
    """原生：本机 Python 跑 pytest / unittest。"""
    py = _python_bin()
    if not py:
        return ScriptRunResult(
            success=False,
            error="未找到 Python，请配置 SCRIPT_NATIVE_PYTHON",
            mode="native",
        )
    fw = (framework or "pytest").lower()
    to = timeout or max(_native_timeout(), 60)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        if fw == "unittest":
            cmd = [py, "-m", "unittest", tmp_path]
        else:
            cmd = [py, "-m", "pytest", tmp_path, "-v", "--tb=short", "--no-header"]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=to,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout or "") + (result.stderr or "")
        return ScriptRunResult(
            success=result.returncode == 0,
            output=output,
            mode="native",
            error="" if result.returncode == 0 else f"exit_code={result.returncode}",
            logs=[f"原生执行: {' '.join(cmd)}"],
        )
    except subprocess.TimeoutExpired:
        return ScriptRunResult(success=False, error=f"执行超时（{to}s）", mode="native")
    except Exception as e:
        return ScriptRunResult(
            success=False,
            error=str(e)[:500],
            mode="native",
            logs=[traceback.format_exc()[:400]],
        )
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


async def run_generated_code_async(
    code: str,
    *,
    framework: str = "pytest",
    mode: Optional[str] = None,
) -> ScriptRunResult:
    resolved = resolve_exec_mode(mode)
    if resolved == "native":
        return await asyncio.to_thread(run_generated_native, code, framework)
    return await asyncio.to_thread(run_generated_sandbox, code, framework)
