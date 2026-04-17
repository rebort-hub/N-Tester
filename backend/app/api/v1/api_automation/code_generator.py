"""
测试框架代码生成器
支持：pytest / unittest / TestNG / Jest
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


# ── 工具函数 ──────────────────────────────────────────────────────────

# method 字段存的是数字（与前端 method_list 对应）
_METHOD_MAP = {1: "GET", 2: "POST", 3: "PUT", 4: "DELETE", 5: "PATCH", 6: "OPTIONS"}


def _resolve_method(method: any) -> str:
    """将数字或字符串 method 统一转为大写字符串"""
    if isinstance(method, int):
        return _METHOD_MAP.get(method, "GET")
    return str(method or "GET").upper()

def _safe_name(name: str) -> str:
    """将接口名称转为合法的函数/方法名"""
    s = re.sub(r"[^\w\u4e00-\u9fff]", "_", name or "api")
    s = re.sub(r"_+", "_", s).strip("_")
    if s and s[0].isdigit():
        s = "api_" + s
    return s or "api_test"


def _indent(code: str, spaces: int = 4) -> str:
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in code.splitlines())


def _headers_repr(headers: List[Dict]) -> str:
    """把 header 列表转为 dict 字面量字符串"""
    active = {h["key"]: h["value"] for h in headers if h.get("status") and h.get("key")}
    return json.dumps(active, ensure_ascii=False, indent=8) if active else "{}"


def _params_repr(params: List[Dict]) -> str:
    active = {p["key"]: p["value"] for p in params if p.get("status") and p.get("key")}
    return json.dumps(active, ensure_ascii=False, indent=8) if active else "{}"


def _body_repr(req: Dict) -> Optional[str]:
    body_type = req.get("body_type", 1)
    if body_type == 2:
        body = req.get("body", "")
        try:
            obj = json.loads(body) if isinstance(body, str) else body
            return json.dumps(obj, ensure_ascii=False, indent=8)
        except Exception:
            return json.dumps(body, ensure_ascii=False)
    if body_type in (3, 4):
        form = {f["key"]: f["value"] for f in req.get("form_data", []) if f.get("status") and f.get("key")}
        return json.dumps(form, ensure_ascii=False, indent=8) if form else None
    return None


def _assert_comments(asserts: List[Dict]) -> List[str]:
    lines = []
    for a in asserts:
        if not a.get("status"):
            continue
        path = a.get("path", "")
        op = a.get("operator", "==")
        val = a.get("value", "")
        lines.append(f"# assert: {path} {op} {val}")
    return lines



def _gen_pytest(apis: List[Dict], base_url: str, class_name: str) -> str:
    lines = [
        "import pytest",
        "import requests",
        "",
        "",
        f"BASE_URL = \"{base_url}\"",
        "",
        "",
        f"class Test{class_name}:",
        "",
    ]
    for api in apis:
        req = api.get("req") or {}
        url = api.get("url", "/")
        method = _resolve_method(req.get("method"))
        name = _safe_name(api.get("name") or url)
        headers = _headers_repr(req.get("header") or [])
        params = _params_repr(req.get("params") or [])
        body = _body_repr(req)
        asserts = _assert_comments(req.get("assert") or [])

        fn = [f"    def test_{name}(self):"]
        fn.append(f'        url = BASE_URL + "{url}"')
        fn.append(f"        headers = {headers}")
        fn.append(f"        params = {params}")
        if body:
            fn.append(f"        json_body = {body}")
        for ac in asserts:
            fn.append(f"        {ac}")

        call_args = 'url, headers=headers, params=params'
        if body:
            body_type = req.get("body_type", 1)
            call_args += ", json=json_body" if body_type == 2 else ", data=json_body"

        fn.append(f"        response = requests.{method.lower()}({call_args})")
        fn.append("        assert response.status_code == 200")
        fn.append("")
        lines.extend(fn)

    return "\n".join(lines)


def _gen_unittest(apis: List[Dict], base_url: str, class_name: str) -> str:
    lines = [
        "import unittest",
        "import requests",
        "",
        "",
        f"BASE_URL = \"{base_url}\"",
        "",
        "",
        f"class Test{class_name}(unittest.TestCase):",
        "",
    ]
    for api in apis:
        req = api.get("req") or {}
        url = api.get("url", "/")
        method = _resolve_method(req.get("method"))
        name = _safe_name(api.get("name") or url)
        headers = _headers_repr(req.get("header") or [])
        params = _params_repr(req.get("params") or [])
        body = _body_repr(req)
        asserts = _assert_comments(req.get("assert") or [])

        fn = [f"    def test_{name}(self):"]
        fn.append(f'        url = BASE_URL + "{url}"')
        fn.append(f"        headers = {headers}")
        fn.append(f"        params = {params}")
        if body:
            fn.append(f"        json_body = {body}")
        for ac in asserts:
            fn.append(f"        {ac}")

        call_args = 'url, headers=headers, params=params'
        if body:
            body_type = req.get("body_type", 1)
            call_args += ", json=json_body" if body_type == 2 else ", data=json_body"

        fn.append(f"        response = requests.{method.lower()}({call_args})")
        fn.append("        self.assertEqual(response.status_code, 200)")
        fn.append("")
        lines.extend(fn)

    lines.extend(["", "if __name__ == '__main__':", "    unittest.main()"])
    return "\n".join(lines)


def _gen_testng(apis: List[Dict], base_url: str, class_name: str) -> str:
    lines = [
        "import io.restassured.RestAssured;",
        "import io.restassured.response.Response;",
        "import org.testng.Assert;",
        "import org.testng.annotations.BeforeClass;",
        "import org.testng.annotations.Test;",
        "import java.util.HashMap;",
        "import java.util.Map;",
        "",
        f"public class Test{class_name} {{",
        "",
        f'    private static final String BASE_URL = "{base_url}";',
        "",
        "    @BeforeClass",
        "    public void setUp() {",
        f'        RestAssured.baseURI = BASE_URL;',
        "    }",
        "",
    ]
    for api in apis:
        req = api.get("req") or {}
        url = api.get("url", "/")
        method = _resolve_method(req.get("method"))
        name = _safe_name(api.get("name") or url)
        headers = {h["key"]: h["value"] for h in (req.get("header") or []) if h.get("status") and h.get("key")}
        params = {p["key"]: p["value"] for p in (req.get("params") or []) if p.get("status") and p.get("key")}
        body = _body_repr(req)
        asserts = _assert_comments(req.get("assert") or [])

        fn = ["    @Test", f"    public void test_{name}() {{"]
        fn.append("        Map<String, String> headers = new HashMap<>();")
        for k, v in headers.items():
            fn.append(f'        headers.put("{k}", "{v}");')
        fn.append("        Map<String, String> params = new HashMap<>();")
        for k, v in params.items():
            fn.append(f'        params.put("{k}", "{v}");')
        for ac in asserts:
            fn.append(f"        // {ac}")

        spec = "RestAssured.given().headers(headers).queryParams(params)"
        if body:
            spec += f'\n            .contentType("application/json")\n            .body({json.dumps(body)})'
        fn.append(f"        Response response = {spec}")
        fn.append(f'            .{method.lower()}("{url}");')
        fn.append("        Assert.assertEquals(response.getStatusCode(), 200);")
        fn.append("    }")
        fn.append("")
        lines.extend(fn)

    lines.append("}")
    return "\n".join(lines)


def _gen_jest(apis: List[Dict], base_url: str, class_name: str) -> str:
    lines = [
        "const axios = require('axios');",
        "",
        f"const BASE_URL = '{base_url}';",
        "",
        f"describe('{class_name}', () => {{",
        "",
    ]
    for api in apis:
        req = api.get("req") or {}
        url = api.get("url", "/")
        method = _resolve_method(req.get("method")).lower()
        name = _safe_name(api.get("name") or url)
        headers = {h["key"]: h["value"] for h in (req.get("header") or []) if h.get("status") and h.get("key")}
        params = {p["key"]: p["value"] for p in (req.get("params") or []) if p.get("status") and p.get("key")}
        body_raw = _body_repr(req)
        asserts = _assert_comments(req.get("assert") or [])

        fn = [f"  test('{name}', async () => {{"]
        fn.append(f"    const url = BASE_URL + '{url}';")
        fn.append(f"    const headers = {json.dumps(headers, ensure_ascii=False)};")
        fn.append(f"    const params = {json.dumps(params, ensure_ascii=False)};")
        if body_raw:
            fn.append(f"    const data = {body_raw};")
        for ac in asserts:
            fn.append(f"    {ac}")

        config = "{ headers, params"
        if body_raw:
            config += ", data"
        config += " }"
        fn.append(f"    const response = await axios.{method}(url, {config});")
        fn.append("    expect(response.status).toBe(200);")
        fn.append("  });")
        fn.append("")
        lines.extend(fn)

    lines.append("});")
    return "\n".join(lines)


# ── 公开入口 ─────────────────────────────────────────────────────────

FRAMEWORK_MAP = {
    "pytest": _gen_pytest,
    "unittest": _gen_unittest,
    "testng": _gen_testng,
    "jest": _gen_jest,
}


def generate_test_code(
    apis: List[Dict],
    framework: str,
    base_url: str = "",
    class_name: str = "AutoGenerated",
) -> str:
    """
    生成测试框架代码。

    :param apis:       接口列表，每项含 url / name / req(method/header/params/body_type/body/assert)
    :param framework:  pytest | unittest | testng | jest
    :param base_url:   服务基础 URL
    :param class_name: 生成的类/describe 名称
    :return:           代码字符串
    """
    fn = FRAMEWORK_MAP.get(framework.lower())
    if fn is None:
        raise ValueError(f"不支持的框架：{framework}，可选：{list(FRAMEWORK_MAP)}")
    return fn(apis, base_url, class_name)
