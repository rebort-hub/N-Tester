#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

from __future__ import annotations

import asyncio
import json
import re
import threading
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pymysql
import requests
import uuid
from datetime import timedelta
from jsonpath_ng import parse as jsonpath_parse
import yaml
from sqlalchemy import select, update, delete, text, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .model import (
    ApiModel,
    ApiProjectModel,
    ApiServiceModel,
    ApiMenuModel,
    ApiEnvironmentModel,
    ApiVariableModel,
    ApiDatabaseModel,
    ApiResultModel,
    ApiEditModel,
    ApiScriptModel,
    ApiScriptResultListModel,
    ApiScriptResultModel,
    ApiUpdateModel,
)

from config import config as app_config

from pathlib import Path
import os
from app.api.v1.system.user.crud import UserCRUD
from app.api.v1.Ntesterc_module.Ntesterc_task_scheduler.service import TaskSchedulerService
from app.api.v1.Ntesterc_module.Ntesterc_task_scheduler.model import MsgNoticeModel


async def _get_username_map(db: AsyncSession, user_ids: List[int]) -> Dict[int, str]:
    if not user_ids:
        return {}
    try:
        res = await db.execute(
            text("SELECT id, COALESCE(username, '') AS name FROM sys_user WHERE id IN :ids"),
            {"ids": tuple(set(user_ids))},
        )
        rows = res.fetchall()
        return {r.id: (r.name or "") for r in rows}
    except Exception:
        return {}


def _build_tree(items: List[Dict[str, Any]], pid_key: str = "pid", id_key: str = "id") -> List[Dict[str, Any]]:
    by_id: Dict[Any, Dict[str, Any]] = {}
    roots: List[Dict[str, Any]] = []
    for it in items:
        node = dict(it)
        node.setdefault("children", [])
        by_id[node.get(id_key)] = node
    for node in by_id.values():
        pid = node.get(pid_key)
        if pid in (None, 0, "0"):
            roots.append(node)
        else:
            parent = by_id.get(pid)
            if parent:
                parent.setdefault("children", []).append(node)
            else:
                roots.append(node)
    return roots


class ApiAutomationService:
    """接口自动化服务"""

    
    @staticmethod
    def _normalize_var_name(name: Any) -> str:
        """统一变量名"""
        n = str(name or "").strip()
        if n.startswith("{{") and n.endswith("}}"):
            n = n[2:-2].strip()
        return n

    @staticmethod
    async def _complete_var(db: AsyncSession, env_id: int, key: str) -> Any:
        lookup = ApiAutomationService._normalize_var_name(key)
        if not lookup:
            return ""

        if env_id:
            env = await db.execute(
                select(ApiEnvironmentModel).where(ApiEnvironmentModel.id == env_id, ApiEnvironmentModel.enabled_flag == 1)
            )
            env_row = env.scalar_one_or_none()
            if env_row:
                for i in (env_row.config or []):
                    if isinstance(i, dict) and ApiAutomationService._normalize_var_name(i.get("name")) == lookup:
                        return i.get("value")
                for j in (env_row.variable or []):
                    if isinstance(j, dict) and ApiAutomationService._normalize_var_name(j.get("name")) == lookup:
                        return j.get("value")

        g = await db.execute(select(ApiVariableModel).where(ApiVariableModel.enabled_flag == 1))
        for row in g.scalars().all():
            if ApiAutomationService._normalize_var_name(row.name) == lookup:
                return row.value
        return ""

    @staticmethod
    async def _find_var(db: AsyncSession, env_id: int, s: str) -> str:
        keys = re.findall(r"\{\{(.+?)\}\}", s) if ("{{" in s and "}}" in s) else []
        for k in keys:
            var = "{{" + k + "}}"
            val = await ApiAutomationService._complete_var(db, env_id, k)
            
            if val is None or val == "":
                continue
            s = s.replace(var, str(val))
        return s

    @staticmethod
    async def handle_var(db: AsyncSession, env_id: int, data: Any) -> Any:
        if isinstance(data, str):
            if "{{" in data and "}}" in data:
                return await ApiAutomationService._find_var(db, env_id, data)
            return data
        if isinstance(data, dict):
            out = {}
            for k, v in data.items():
                out[k] = await ApiAutomationService.handle_var(db, env_id, v)
            return out
        if isinstance(data, list):
            return [await ApiAutomationService.handle_var(db, env_id, x) for x in data]
        return data

    @staticmethod
    def params_header(params: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        if not params:
            return {}
        res: Dict[str, Any] = {}
        for i in params:
            if not isinstance(i, dict):
                continue
            if i.get("status"):
                key = i.get("key")
                if key:
                    res[key] = i.get("value")
        return res

    @staticmethod
    def _set_header_ci(headers: Dict[str, Any], name: str, value: str) -> None:
        """按大小写不敏感方式设置 Header，避免重复键。"""
        target = None
        for k in list(headers.keys()):
            if str(k).lower() == name.lower():
                target = k
                break
        if target is not None and target != name:
            headers.pop(target, None)
        headers[name] = value

    @staticmethod
    async def _resolve_oauth2_token(db: AsyncSession, env_id: int, req: Dict[str, Any]) -> str:
        """OAuth 2.0：支持直接填 Access Token，或 Client Credentials / Password 换取。"""
        grant = str(req.get("auth_oauth_grant") or "access_token").strip().lower()
        prefix_ready = str(req.get("auth_oauth_access_token") or req.get("auth_token") or "").strip()
        if grant in ("access_token", "token", ""):
            token = await ApiAutomationService.handle_var(db, env_id, prefix_ready)
            return str(token or "").strip()

        token_url = str(
            await ApiAutomationService.handle_var(db, env_id, req.get("auth_oauth_token_url") or "")
        ).strip()
        client_id = str(
            await ApiAutomationService.handle_var(db, env_id, req.get("auth_oauth_client_id") or "")
        ).strip()
        client_secret = str(
            await ApiAutomationService.handle_var(db, env_id, req.get("auth_oauth_client_secret") or "")
        ).strip()
        scope = str(
            await ApiAutomationService.handle_var(db, env_id, req.get("auth_oauth_scope") or "")
        ).strip()
        if not token_url:
            raise ValueError("OAuth 2.0 缺少 Token URL")
        if not client_id:
            raise ValueError("OAuth 2.0 缺少 Client ID")

        data: Dict[str, Any] = {}
        auth = None
        client_auth = str(req.get("auth_oauth_client_auth") or "basic").strip().lower()
        if grant in ("client_credentials", "client"):
            data["grant_type"] = "client_credentials"
            if scope:
                data["scope"] = scope
        elif grant in ("password", "password_credentials"):
            data["grant_type"] = "password"
            data["username"] = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_username") or "")
            ).strip()
            data["password"] = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_password") or "")
            ).strip()
            if scope:
                data["scope"] = scope
            if not data["username"]:
                raise ValueError("OAuth 2.0 Password 模式缺少用户名")
        else:
            raise ValueError(f"不支持的 OAuth 2.0 Grant Type：{grant}")

        if client_auth == "body":
            data["client_id"] = client_id
            data["client_secret"] = client_secret
        else:
            from requests.auth import HTTPBasicAuth

            auth = HTTPBasicAuth(client_id, client_secret)

        resp = requests.post(token_url, data=data, auth=auth, timeout=30)
        try:
            payload = resp.json()
        except Exception:
            payload = {}
        if resp.status_code >= 400:
            raise ValueError(
                f"OAuth 2.0 获取 Token 失败 HTTP {resp.status_code}: "
                f"{payload or (resp.text or '')[:300]}"
            )
        token = str(payload.get("access_token") or "").strip()
        if not token:
            raise ValueError(f"OAuth 2.0 响应中无 access_token：{payload}")
        return token

    @staticmethod
    async def _build_jwt_bearer_token(db: AsyncSession, env_id: int, req: Dict[str, Any]) -> str:
        """JWT Bearer：可直接填 Token，或按密钥/Payload 现场签发。"""
        mode = str(req.get("auth_jwt_mode") or "token").strip().lower()
        if mode != "generate":
            token = await ApiAutomationService.handle_var(db, env_id, req.get("auth_token") or "")
            return str(token or "").strip()

        import jwt as pyjwt

        alg = str(req.get("auth_jwt_alg") or "HS256").strip() or "HS256"
        secret = str(
            await ApiAutomationService.handle_var(db, env_id, req.get("auth_jwt_secret") or "")
        )
        if not secret:
            raise ValueError("JWT Bearer 生成模式缺少 Secret / Private Key")

        raw_payload = req.get("auth_jwt_payload") or "{}"
        raw_headers = req.get("auth_jwt_headers") or "{}"
        raw_payload = await ApiAutomationService.handle_var(db, env_id, raw_payload)
        raw_headers = await ApiAutomationService.handle_var(db, env_id, raw_headers)

        def _as_dict(v: Any, label: str) -> Dict[str, Any]:
            if isinstance(v, dict):
                return v
            text = str(v or "").strip() or "{}"
            try:
                obj = json.loads(text)
            except Exception as e:
                raise ValueError(f"JWT Bearer {label} 不是合法 JSON：{e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"JWT Bearer {label} 必须是 JSON 对象")
            return obj

        payload = _as_dict(raw_payload, "Payload")
        headers = _as_dict(raw_headers, "Header")
        token = pyjwt.encode(payload, secret, algorithm=alg, headers=headers or None)
        return token if isinstance(token, str) else token.decode("utf-8")

    @staticmethod
    async def apply_request_auth(
        db: AsyncSession,
        env_id: int,
        req: Dict[str, Any],
        headers: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Any]:
        """
        将 Auth / Cookies 应用到请求。
        返回 (headers, params, requests_auth)；requests_auth 仅 Digest 时非空。
        """
        headers = dict(headers or {})
        params = dict(params or {})
        requests_auth = None

        # Cookies
        cookie_parts: List[str] = []
        for c in (req.get("cookies") or []):
            if not isinstance(c, dict) or c.get("status") is False:
                continue
            name = str(c.get("name") or c.get("key") or "").strip()
            if not name:
                continue
            val = await ApiAutomationService.handle_var(db, env_id, c.get("value") or "")
            cookie_parts.append(f"{name}={val}")
        if cookie_parts:
            existing = ""
            for k, v in list(headers.items()):
                if str(k).lower() == "cookie":
                    existing = str(v or "")
                    break
            merged = "; ".join([p for p in [existing.strip().rstrip(";"), *cookie_parts] if p])
            ApiAutomationService._set_header_ci(headers, "Cookie", merged)

        auth_type = str(req.get("auth_type") or "none").strip().lower()
        if auth_type in ("", "none", "noauth"):
            return headers, params, None

        prefix = str(
            await ApiAutomationService.handle_var(
                db, env_id, req.get("auth_prefix") if req.get("auth_prefix") is not None else "Bearer"
            )
        ).strip()

        if auth_type in ("bearer", "bearer_token"):
            token = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_token") or "")
            ).strip()
            if token:
                value = f"{prefix} {token}".strip() if prefix else token
                ApiAutomationService._set_header_ci(headers, "Authorization", value)

        elif auth_type in ("jwt", "jwt_bearer"):
            token = await ApiAutomationService._build_jwt_bearer_token(db, env_id, req)
            if token:
                value = f"{prefix} {token}".strip() if prefix else token
                ApiAutomationService._set_header_ci(headers, "Authorization", value)

        elif auth_type in ("basic", "basic_auth"):
            import base64

            username = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_username") or "")
            )
            password = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_password") or "")
            )
            raw = f"{username}:{password}".encode("utf-8")
            ApiAutomationService._set_header_ci(
                headers, "Authorization", "Basic " + base64.b64encode(raw).decode("ascii")
            )

        elif auth_type in ("digest", "digest_auth"):
            from requests.auth import HTTPDigestAuth

            username = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_username") or "")
            )
            password = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_password") or "")
            )
            requests_auth = HTTPDigestAuth(username, password)

        elif auth_type in ("apikey", "api_key", "api-key"):
            key = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_key") or "")
            ).strip()
            value = str(
                await ApiAutomationService.handle_var(db, env_id, req.get("auth_value") or "")
            )
            if key:
                dest = str(req.get("auth_in") or "header").strip().lower()
                if dest in ("query", "params", "param"):
                    params[key] = value
                else:
                    ApiAutomationService._set_header_ci(headers, key, value)

        elif auth_type in ("oauth2", "oauth_2", "oauth 2.0"):
            token = await ApiAutomationService._resolve_oauth2_token(db, env_id, req)
            if token:
                value = f"{prefix} {token}".strip() if prefix else token
                ApiAutomationService._set_header_ci(headers, "Authorization", value)

        else:
            
            pass

        return headers, params, requests_auth

    @staticmethod
    def _jsonpath_value(
        res_type: int,
        expr: str,
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
    ) -> Tuple[bool, str]:
        """
        对齐jsonpath_value：
        - res_type: 1=响应体, 2=header(请求头), 3=body(请求体), 4=res['header'](响应头)
        - expr: jsonpath 表达式
        """
        try:
            if res_type == 1:
                json_data = res.get("body") or {}
            elif res_type == 2:
                json_data = header or {}
            elif res_type == 3:
                json_data = body or {}
            elif res_type == 4:
                json_data = res.get("header") or {}
            else:
                json_data = res.get("body") or {}

            if not expr:
                return False, "jsonpath 表达式为空"
            jp = jsonpath_parse(expr)
            matches = [m.value for m in jp.find(json_data)]
            if not matches:
                return False, "获取断言目标值失败，原因：jsonpath 未匹配到结果"
            return True, str(matches[0])
        except Exception as e:
            return False, f"获取断言目标值失败，原因：{str(e)}"

    @staticmethod
    def _jsonpath_value_advanced(
        rule: Dict[str, Any],
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
    ) -> Tuple[bool, str]:
        """
        兼容调用：多数规则使用 rule['name'] 作为 jsonpath 表达式。
        注意：db_assert 使用 rule['value'] 作为表达式，因此 DB 断言不要用这个方法。
        """
        res_type = int(rule.get("res_type") or 1)
        expr = str(rule.get("name") or "")
        return ApiAutomationService._jsonpath_value(res_type, expr, res, header, body)

    # -------------------- 结果日志目录 --------------------
    @staticmethod
    def _get_api_result_dir(result_id: str) -> Path:
        """
        结果文件目录:{BASEDIR}/static/api_results/{result_id}
        """
       
        backend_root = Path(__file__).resolve().parents[4]
        base = backend_root / app_config.STATIC_DIR / "api_results" / str(result_id)
        if not base.exists():
            os.makedirs(base, exist_ok=True)
        return base

    @staticmethod
    def _append_log_file(file_path: Path, text: str) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    _api_script_cancel_lock = threading.Lock()
    _api_script_cancel_ids: set[str] = set()

    @staticmethod
    def _request_cancel_api_script_result(result_id: str) -> None:
        with ApiAutomationService._api_script_cancel_lock:
            ApiAutomationService._api_script_cancel_ids.add(str(result_id))

    @staticmethod
    def _is_api_script_result_cancel_requested(result_id: str) -> bool:
        with ApiAutomationService._api_script_cancel_lock:
            return str(result_id) in ApiAutomationService._api_script_cancel_ids

    @staticmethod
    def _clear_api_script_cancel(result_id: str) -> None:
        with ApiAutomationService._api_script_cancel_lock:
            ApiAutomationService._api_script_cancel_ids.discard(str(result_id))
        
        if hasattr(ApiAutomationService, '_step_ctx_cache'):
            keys = [k for k in ApiAutomationService._step_ctx_cache if k.startswith(str(result_id))]
            for k in keys:
                del ApiAutomationService._step_ctx_cache[k]

    @staticmethod
    async def _load_env_vars(db: AsyncSession, env_id: int) -> Dict[str, Any]:
        """加载环境配置/变量为字典。
        """
        if not env_id:
            return {}
        try:
            env_row = (
                await db.execute(
                    select(ApiEnvironmentModel).where(
                        ApiEnvironmentModel.id == int(env_id),
                        ApiEnvironmentModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            if not env_row:
                return {}
            result: Dict[str, Any] = {}

            def _put(raw_name: Any, value: Any) -> None:
                name = ApiAutomationService._normalize_var_name(raw_name)
                if name:
                    result[name] = value

            for item in (env_row.config or []):
                if isinstance(item, dict):
                    _put(item.get("name") or item.get("key"), item.get("value"))
            for item in (env_row.variable or []):
                if isinstance(item, dict):
                    _put(item.get("name") or item.get("key"), item.get("value"))
            return result
        except Exception:
            return {}

    @staticmethod
    async def _api_script_delay_seconds(result_id: str, seconds: float) -> None:
        deadline = time.monotonic() + float(seconds)
        while time.monotonic() < deadline:
            if ApiAutomationService._is_api_script_result_cancel_requested(result_id):
                return
            await asyncio.sleep(0.2)

    @staticmethod
    def _remove_api_result_files(result_id: str) -> None:
        try:
            backend_root = Path(__file__).resolve().parents[4]
            base = backend_root / app_config.STATIC_DIR / "api_results" / str(result_id)
            if base.exists():
                shutil.rmtree(base, ignore_errors=True)
        except Exception:
            pass

   
    @staticmethod
    async def get_services(db: AsyncSession, project_id: Optional[int], user_id: int) -> Dict[str, Any]:
        await ApiAutomationService._ensure_service_common_params_column(db)
        stmt = select(ApiServiceModel).where(ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
        if project_id:
            stmt = stmt.where(ApiServiceModel.api_project_id == int(project_id))
        stmt = stmt.order_by(ApiServiceModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        data = [r.__dict__ for r in rows]
        for d in data:
            d.pop("_sa_instance_state", None)
        return {"content": data, "total": len(data)}

    
    @staticmethod
    def _extract_page(body: Dict[str, Any]) -> Tuple[int, int]:
        page = int(body.get("page") or body.get("currentPage") or 1)
        page_size = int(body.get("pageSize") or body.get("page_size") or 10)
        return page, page_size

    @staticmethod
    def _extract_contains(search: Dict[str, Any], *keys: str) -> Optional[str]:
        for k in keys:
            v = search.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return None

    @staticmethod
    async def get_services_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        await ApiAutomationService._ensure_service_common_params_column(db)
        page, page_size = ApiAutomationService._extract_page(body)
        search = body.get("search") or {}
       
        name_like = ApiAutomationService._extract_contains(search, "name__contains", "name__icontains", "name") \
                    or ApiAutomationService._extract_contains(body, "name")
        project_id = body.get("project_id") or body.get("api_project_id") or search.get("api_project_id")
        manager = body.get("manager") or search.get("manager")
        business_id = body.get("business_id") or search.get("business_id")
        stmt = select(ApiServiceModel).where(ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
        if project_id:
            stmt = stmt.where(ApiServiceModel.api_project_id == int(project_id))
        if name_like:
            stmt = stmt.where(ApiServiceModel.name.like(f"%{name_like}%"))
        if manager:
            stmt = stmt.where(ApiServiceModel.manager == int(manager))
        if business_id:
            stmt = stmt.where(ApiServiceModel.business_id == int(business_id))
        stmt = stmt.order_by(ApiServiceModel.sort.asc(), ApiServiceModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = rows[start:end]
        content = []
        for r in page_rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            content.append(d)
        return {"content": content, "total": total, "page": page, "pageSize": page_size}

    @staticmethod
    async def add_service(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        svc = ApiServiceModel(
            name=str(body["name"]),
            api_project_id=int(body["api_project_id"]),
            img=str(body.get("img") or ""),
            description=str(body.get("description") or ""),
            source_type=body.get("source_type"),
            source_addr=body.get("source_addr"),
            last_pull_status=0,
            manager=body.get("manager"),
            business_id=body.get("business_id"),
            sort=0,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(svc)
        await db.commit()

    @staticmethod
    async def edit_service(db: AsyncSession, service_id: int, body: Dict[str, Any], user_id: int) -> None:
        values: Dict[str, Any] = {"updated_by": user_id}
        for field in ("name", "api_project_id", "img", "description", "source_type", "source_addr", "manager", "business_id"):
            if field in body and body[field] is not None:
                values[field] = body[field]
        if "common_params" in body and body["common_params"] is not None:
            await ApiAutomationService._ensure_service_common_params_column(db)
            values["common_params"] = body["common_params"]
        await db.execute(
            update(ApiServiceModel)
            .where(ApiServiceModel.id == int(service_id), ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
            .values(**values)
        )
        await db.commit()

    @staticmethod
    async def _ensure_service_common_params_column(db: AsyncSession) -> None:
        """兼容旧库"""
        try:
            await db.execute(text(
                "ALTER TABLE api_automation_services ADD COLUMN common_params JSON NULL"
            ))
            await db.commit()
        except Exception:
            await db.rollback()

    @staticmethod
    def _empty_common_params() -> Dict[str, List[Dict[str, Any]]]:
        return {"header": [], "cookie": [], "query": [], "body": []}

    @staticmethod
    def _normalize_common_params(raw: Any) -> Dict[str, List[Dict[str, Any]]]:
        base = ApiAutomationService._empty_common_params()
        if not isinstance(raw, dict):
            return base
        for src, dst in (("header", "header"), ("cookie", "cookie"), ("cookies", "cookie"), ("query", "query"), ("params", "query"), ("body", "body")):
            items = raw.get(src)
            if not isinstance(items, list):
                continue
            out: List[Dict[str, Any]] = []
            for it in items:
                if not isinstance(it, dict):
                    continue
                key = str(it.get("key") or it.get("name") or "").strip()
                if not key:
                    continue
                row: Dict[str, Any] = {
                    "key": key,
                    "value": "" if it.get("value") is None else str(it.get("value")),
                    "status": False if it.get("status") is False else True,
                }
                if dst == "cookie" and it.get("domain") is not None:
                    row["domain"] = str(it.get("domain") or "")
                out.append(row)
            base[dst] = out
        return base

    @staticmethod
    async def get_common_params(db: AsyncSession, api_service_id: int, user_id: int) -> Dict[str, Any]:
        await ApiAutomationService._ensure_service_common_params_column(db)
        svc = (
            await db.execute(
                select(ApiServiceModel).where(
                    ApiServiceModel.id == int(api_service_id),
                    ApiServiceModel.enabled_flag == 1,
                    ApiServiceModel.created_by == user_id,
                )
            )
        ).scalar_one_or_none()
        if not svc:
            raise ValueError("服务不存在或无权限")
        return ApiAutomationService._normalize_common_params(getattr(svc, "common_params", None))

    @staticmethod
    async def save_common_params(db: AsyncSession, api_service_id: int, common_params: Any, user_id: int) -> None:
        await ApiAutomationService._ensure_service_common_params_column(db)
        normalized = ApiAutomationService._normalize_common_params(common_params)
        result = await db.execute(
            update(ApiServiceModel)
            .where(
                ApiServiceModel.id == int(api_service_id),
                ApiServiceModel.enabled_flag == 1,
                ApiServiceModel.created_by == user_id,
            )
            .values(common_params=normalized, updated_by=user_id)
        )
        if not result.rowcount:
            raise ValueError("服务不存在或无权限")
        await db.commit()

    @staticmethod
    async def _load_common_params_by_api(db: AsyncSession, api_id: Optional[int] = None, api_service_id: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """按接口或服务加载全局参数"""
        await ApiAutomationService._ensure_service_common_params_column(db)
        sid = int(api_service_id or 0)
        if not sid and api_id:
            api_row = (
                await db.execute(
                    select(ApiModel).where(ApiModel.id == int(api_id), ApiModel.enabled_flag == 1)
                )
            ).scalar_one_or_none()
            if api_row:
                sid = int(api_row.api_service_id or 0)
        if not sid:
            return ApiAutomationService._empty_common_params()
        svc = (
            await db.execute(
                select(ApiServiceModel).where(
                    ApiServiceModel.id == sid,
                    ApiServiceModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not svc:
            return ApiAutomationService._empty_common_params()
        return ApiAutomationService._normalize_common_params(getattr(svc, "common_params", None))

    @staticmethod
    def _kv_item_key(item: Dict[str, Any], *, cookie: bool = False) -> str:
        if cookie:
            return str(item.get("name") or item.get("key") or "").strip()
        return str(item.get("key") or item.get("name") or "").strip()

    @staticmethod
    def _merge_kv_lists(common_list: Any, request_list: Any, *, cookie: bool = False) -> List[Dict[str, Any]]:
        """全局参数在前，同名以请求侧为准（请求侧存在该 key 即覆盖，不论是否勾选）。"""
        req_items = [x for x in (request_list or []) if isinstance(x, dict)]
        req_keys = set()
        for it in req_items:
            k = ApiAutomationService._kv_item_key(it, cookie=cookie)
            if k:
                req_keys.add(k.lower())
        merged: List[Dict[str, Any]] = []
        for it in (common_list or []):
            if not isinstance(it, dict) or it.get("status") is False:
                continue
            k = ApiAutomationService._kv_item_key(it, cookie=cookie)
            if not k or k.lower() in req_keys:
                continue
            if cookie:
                merged.append({
                    "name": k,
                    "value": "" if it.get("value") is None else str(it.get("value")),
                    "status": True,
                    "domain": str(it.get("domain") or ""),
                })
            else:
                merged.append({
                    "key": k,
                    "value": "" if it.get("value") is None else str(it.get("value")),
                    "status": True,
                })
        merged.extend(req_items)
        return merged

    @staticmethod
    def _common_body_dict(common: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for it in (common.get("body") or []):
            if not isinstance(it, dict) or it.get("status") is False:
                continue
            k = str(it.get("key") or "").strip()
            if k:
                out[k] = it.get("value")
        return out

    @staticmethod
    def apply_common_params_to_req(req: Dict[str, Any], common: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """将服务级全局参数合并进请求"""
        if not isinstance(req, dict):
            req = {}
        else:
            req = dict(req)
        common = ApiAutomationService._normalize_common_params(common)
        if not any(common.get(k) for k in ("header", "cookie", "query", "body")):
            return req

        req["header"] = ApiAutomationService._merge_kv_lists(common.get("header"), req.get("header"))
        req["params"] = ApiAutomationService._merge_kv_lists(common.get("query"), req.get("params"))
        req["cookies"] = ApiAutomationService._merge_kv_lists(common.get("cookie"), req.get("cookies"), cookie=True)

        body_dict = ApiAutomationService._common_body_dict(common)
        if body_dict:
            body_type = int(req.get("body_type") or 2)
            if body_type == 3:
                form_kv = [{"key": k, "value": v, "status": True} for k, v in body_dict.items()]
                req["form_data"] = ApiAutomationService._merge_kv_lists(form_kv, req.get("form_data"))
            elif body_type == 4:
                form_kv = [{"key": k, "value": v, "status": True} for k, v in body_dict.items()]
                req["form_urlencoded"] = ApiAutomationService._merge_kv_lists(form_kv, req.get("form_urlencoded"))
            elif body_type in (0, 2):
                raw_body = req.get("body")
                parsed: Any = raw_body
                if isinstance(raw_body, str):
                    text_body = raw_body.strip()
                    if not text_body:
                        parsed = {}
                    else:
                        try:
                            parsed = json.loads(text_body)
                        except Exception:
                            parsed = None
                if isinstance(parsed, dict):
                    merged_body = {**body_dict, **parsed}
                    
                    req["body"] = json.dumps(merged_body, ensure_ascii=False) if isinstance(raw_body, str) else merged_body
                elif parsed is None and not raw_body:
                    req["body"] = body_dict
        return req

    @staticmethod
    async def delete_service(db: AsyncSession, service_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiServiceModel)
            .where(ApiServiceModel.id == int(service_id), ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def api_tree_list(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        return await ApiAutomationService.get_api_tree(db, {}, user_id)

    @staticmethod
    async def api_list(db: AsyncSession, pid: int, user_id: int) -> List[Dict[str, Any]]:
        """
        根据菜单 pid 返回子节点中 type==2 的接口列表
        注意：接口最终 return 的还是 data（菜单），这里保持更合理：返回匹配到的 Api 列表
        """
        rows = (
            await db.execute(
                select(ApiMenuModel).where(
                    ApiMenuModel.enabled_flag == 1,
                    ApiMenuModel.created_by == user_id,
                    ApiMenuModel.pid == int(pid),
                )
            )
        ).scalars().all()
        api_ids = [r.api_id for r in rows if int(r.type) == 2 and r.api_id]
        if not api_ids:
            return []
        apis = (
            await db.execute(
                select(ApiModel).where(
                    ApiModel.enabled_flag == 1,
                    ApiModel.created_by == user_id,
                    ApiModel.id.in_(api_ids),
                )
            )
        ).scalars().all()
        data: List[Dict[str, Any]] = []
        for a in apis:
            d = a.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

   
    @staticmethod
    async def get_envs(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        stmt = (
            select(ApiEnvironmentModel)
            .where(ApiEnvironmentModel.enabled_flag == 1, ApiEnvironmentModel.created_by == user_id)
            .order_by(ApiEnvironmentModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            item = r.__dict__.copy()
            item.pop("_sa_instance_state", None)
            data.append(item)
        return data

    @staticmethod
    async def get_env_info(db: AsyncSession, env_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        stmt = select(ApiEnvironmentModel).where(
            ApiEnvironmentModel.id == env_id,
            ApiEnvironmentModel.enabled_flag == 1,
            ApiEnvironmentModel.created_by == user_id,
        )
        row = (await db.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        d = row.__dict__.copy()
        d.pop("_sa_instance_state", None)
        return d

    @staticmethod
    async def save_envs(db: AsyncSession, env_list: List[Dict[str, Any]], user_id: int) -> None:
        for env in env_list:
            env_id = int(env["id"])
            await db.execute(
                update(ApiEnvironmentModel)
                .where(
                    ApiEnvironmentModel.id == env_id,
                    ApiEnvironmentModel.enabled_flag == 1,
                    ApiEnvironmentModel.created_by == user_id,
                )
                .values(
                    name=env.get("name"),
                    config=env.get("config"),
                    variable=env.get("variable"),
                    updated_by=user_id,
                )
            )
        await db.commit()

    @staticmethod
    async def add_env(db: AsyncSession, data: Dict[str, Any], user_id: int) -> None:
        env = ApiEnvironmentModel(
            name=data["name"],
            config=data.get("config") or [],
            variable=data.get("variable") or [],
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(env)
        await db.commit()

    @staticmethod
    async def delete_env(db: AsyncSession, env_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiEnvironmentModel)
            .where(
                ApiEnvironmentModel.id == env_id,
                ApiEnvironmentModel.enabled_flag == 1,
                ApiEnvironmentModel.created_by == user_id,
            )
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def get_vars(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        stmt = (
            select(ApiVariableModel)
            .where(ApiVariableModel.enabled_flag == 1, ApiVariableModel.created_by == user_id)
            .order_by(ApiVariableModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": len(data)}

    @staticmethod
    async def add_var(db: AsyncSession, name: str, value: str, user_id: int) -> None:
        var = ApiVariableModel(name=name, value=value, created_by=user_id, updated_by=user_id)
        db.add(var)
        await db.commit()

    @staticmethod
    async def edit_var(db: AsyncSession, var_id: int, name: str, value: str, user_id: int) -> None:
        await db.execute(
            update(ApiVariableModel)
            .where(
                ApiVariableModel.id == var_id,
                ApiVariableModel.enabled_flag == 1,
                ApiVariableModel.created_by == user_id,
            )
            .values(name=name, value=value, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def delete_var(db: AsyncSession, var_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiVariableModel)
            .where(
                ApiVariableModel.id == var_id,
                ApiVariableModel.enabled_flag == 1,
                ApiVariableModel.created_by == user_id,
            )
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

  
    @staticmethod
    async def get_databases(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        stmt = (
            select(ApiDatabaseModel)
            .where(ApiDatabaseModel.enabled_flag == 1, ApiDatabaseModel.created_by == user_id)
            .order_by(ApiDatabaseModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": len(data)}

    @staticmethod
    async def get_all_databases(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        stmt = select(ApiDatabaseModel).where(
            ApiDatabaseModel.enabled_flag == 1,
            ApiDatabaseModel.created_by == user_id,
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

    @staticmethod
    async def get_databases_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """直连数据库"""
        body = body or {}
        page, page_size = ApiAutomationService._extract_page(body)
        has_paging = any(k in body for k in ("page", "currentPage", "pageSize", "page_size"))
        search = body.get("search") or {}
        name_like = ApiAutomationService._extract_contains(
            search, "name__contains", "name__icontains", "name"
        ) or ApiAutomationService._extract_contains(body, "name")
        stmt = select(ApiDatabaseModel).where(
            ApiDatabaseModel.enabled_flag == 1,
            ApiDatabaseModel.created_by == user_id,
        )
        if name_like:
            stmt = stmt.where(ApiDatabaseModel.name.like(f"%{name_like}%"))
        stmt = stmt.order_by(ApiDatabaseModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        total = len(rows)
        if has_paging:
            start = (page - 1) * page_size
            end = start + page_size
            page_rows = rows[start:end]
        else:
            page_rows = rows
            page = 1
            page_size = total or page_size
        content: List[Dict[str, Any]] = []
        for r in page_rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            content.append(d)
        return {"content": content, "total": total, "page": page, "pageSize": page_size}

    @staticmethod
    async def add_database(db: AsyncSession, data: Dict[str, Any], user_id: int) -> None:
        cfg = data.get("config") or {}
        model = ApiDatabaseModel(
            name=data["name"],
            config=cfg,
            db_type=data.get("db_type") or cfg.get("db_type") or "mysql",
            host=cfg.get("host") or "",
            port=int(cfg.get("port") or 3306),
            database_name=cfg.get("database") or "",
            username=cfg.get("user") or cfg.get("username") or "",
            password=cfg.get("password") or "",
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(model)
        await db.commit()

    @staticmethod
    async def edit_database(db: AsyncSession, db_id: int, data: Dict[str, Any], user_id: int) -> None:
        cfg = data.get("config") or {}
        values: Dict[str, Any] = {
            "name": data.get("name"),
            "config": cfg,
            "updated_by": user_id,
        }
        
        if cfg:
            values["db_type"] = data.get("db_type") or cfg.get("db_type") or "mysql"
            values["host"] = cfg.get("host") or ""
            values["port"] = int(cfg.get("port") or 3306)
            values["database_name"] = cfg.get("database") or ""
            values["username"] = cfg.get("user") or cfg.get("username") or ""
            
            new_pwd = cfg.get("password")
            if new_pwd:
                values["password"] = new_pwd
        await db.execute(
            update(ApiDatabaseModel)
            .where(
                ApiDatabaseModel.id == db_id,
                ApiDatabaseModel.enabled_flag == 1,
                ApiDatabaseModel.created_by == user_id,
            )
            .values(**values)
        )
        await db.commit()

    @staticmethod
    async def delete_database(db: AsyncSession, db_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiDatabaseModel)
            .where(
                ApiDatabaseModel.id == db_id,
                ApiDatabaseModel.enabled_flag == 1,
                ApiDatabaseModel.created_by == user_id,
            )
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def get_api_tree(db: AsyncSession, search: Dict[str, Any], user_id: int) -> List[Dict[str, Any]]:
    
        stmt = select(ApiMenuModel).where(ApiMenuModel.enabled_flag == 1, ApiMenuModel.created_by == user_id)
        if search.get("api_service_id"):
            stmt = stmt.where(ApiMenuModel.api_service_id == int(search["api_service_id"]))
        if search.get("name"):
            stmt = stmt.where(ApiMenuModel.name.like(f"%{search['name']}%"))
        rows = (await db.execute(stmt.order_by(ApiMenuModel.id.asc()))).scalars().all()
        items: List[Dict[str, Any]] = []
        api_ids: List[int] = []
        for r in rows:
            items.append(
                {
                    "id": r.id,
                    "name": r.name,
                    "pid": r.pid,
                    "type": r.type,
                    "api_id": r.api_id,
                    "api_service_id": r.api_service_id,
                }
            )
            if r.api_id:
                api_ids.append(int(r.api_id))

        
        method_map: Dict[int, int] = {}
        if api_ids:
            api_rows = (
                await db.execute(
                    select(ApiModel).where(
                        ApiModel.enabled_flag == 1,
                        ApiModel.created_by == user_id,
                        ApiModel.id.in_(api_ids),
                    )
                )
            ).scalars().all()
            for a in api_rows:
                req_cfg = a.req or {}
                try:
                    method_val = int(req_cfg.get("method") or 2)
                except Exception:
                    method_val = 2
                method_map[int(a.id)] = method_val

        for it in items:
            api_id = it.get("api_id")
            if api_id and int(api_id) in method_map:
                it["method"] = method_map[int(api_id)]

        return _build_tree(items)

    @staticmethod
    def _doc_method_to_int(method: str) -> int:
        mapping = {
            "get": 1,
            "post": 2,
            "put": 3,
            "delete": 4,
            "patch": 5,
            "options": 6,
        }
        return mapping.get(str(method or "").lower(), 2)

    @staticmethod
    def _extract_schema_example(schema: Dict[str, Any]) -> Any:
        if not isinstance(schema, dict):
            return {}
        if "example" in schema:
            return schema.get("example")
        schema_type = str(schema.get("type") or "").lower()
        if schema_type == "object":
            props = schema.get("properties") or {}
            out: Dict[str, Any] = {}
            for k, v in props.items():
                out[k] = ApiAutomationService._extract_schema_example(v or {})
            return out
        if schema_type == "array":
            item_schema = schema.get("items") or {}
            return [ApiAutomationService._extract_schema_example(item_schema)]
        if schema_type in ("integer", "number"):
            return 0
        if schema_type == "boolean":
            return False
        return ""

    @staticmethod
    def _build_req_from_openapi(path: str, method: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        params = []
        headers = []
        for p in (operation.get("parameters") or []):
            if not isinstance(p, dict):
                continue
            item = {"key": str(p.get("name") or ""), "value": "", "status": True}
            p_in = str(p.get("in") or "").lower()
            example = p.get("example")
            if example is None:
                example = ((p.get("schema") or {}).get("example"))
            item["value"] = "" if example is None else str(example)
            if not item["key"]:
                continue
            if p_in in ("header", "cookie"):
                headers.append(item)
            elif p_in in ("query", "path"):
                params.append(item)

        body_type = 1
        body: Any = {}
        request_body = operation.get("requestBody") or {}
        if isinstance(request_body, dict):
            content = request_body.get("content") or {}
            if "application/json" in content:
                body_type = 2
                json_info = content.get("application/json") or {}
                body = json_info.get("example")
                if body is None:
                    body = ApiAutomationService._extract_schema_example(json_info.get("schema") or {})
            elif "application/x-www-form-urlencoded" in content:
                body_type = 4
                form_schema = (content.get("application/x-www-form-urlencoded") or {}).get("schema") or {}
                body = ApiAutomationService._extract_schema_example(form_schema)
            elif "multipart/form-data" in content:
                body_type = 3
                multi_schema = (content.get("multipart/form-data") or {}).get("schema") or {}
                body = ApiAutomationService._extract_schema_example(multi_schema)

        return {
            "params_id": None,
            "body": body,
            "after": [],
            "assert": [],
            "before": [],
            "config": {"retry": 0, "req_timeout": 5, "res_timeout": 5},
            "header": headers,
            "method": ApiAutomationService._doc_method_to_int(method),
            "params": params,
            "body_type": body_type,
            "file_path": [],
            "form_data": [],
            "form_urlencoded": [],
            "url": path,
        }

    @staticmethod
    def _extract_apifox_param_rows(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            name = str(it.get("name") or "").strip()
            if not name:
                continue
            val_type = str(it.get("type") or "")
            required = "必填" if bool(it.get("required")) else "非必填"
            desc = str(it.get("description") or "")
            example = str(it.get("example") or "")
            rows.append({
                "key": name,
                "value": f"{val_type}; {required}; {desc}; {example}".strip("; ").strip(),
                "status": True,
            })
        return rows

    @staticmethod
    def _is_apifox_project_export(doc: Any) -> bool:
        if not isinstance(doc, dict):
            return False
        if doc.get("apifoxProject"):
            return True
        schema = doc.get("$schema")
        if isinstance(schema, dict) and str(schema.get("type") or "").lower() == "project":
            return True
        if isinstance(doc.get("apiCollection"), list) and doc.get("apiCollection"):
            return True
        return False

    @staticmethod
    def _normalize_doc_path(path: str) -> str:
        """
        规范化导入得到的请求地址：
        """
        path = str(path or "/").strip()
        if path.startswith("http://") or path.startswith("https://"):
            from urllib.parse import urlparse, urlunparse

            parsed = urlparse(path)
            clean_path = parsed.path or "/"
            while "//" in clean_path:
                clean_path = clean_path.replace("//", "/")
            return urlunparse((parsed.scheme, parsed.netloc, clean_path, "", parsed.query, ""))
        if not path.startswith("/"):
            path = "/" + path
        while "//" in path:
            path = path.replace("//", "/")
        return path or "/"

    @staticmethod
    def _extract_api_path_key(url: str) -> str:
        """
        提取用于去重比对的路径键
        """
        from urllib.parse import urlparse

        s = str(url or "").strip()
        if not s:
            return "/"
        if re.match(r"^https?://", s, flags=re.IGNORECASE):
            parsed = urlparse(s)
            s = parsed.path or "/"
        else:
            
            while True:
                m = re.match(r"^\{\{[^{}]+\}\}", s)
                if not m:
                    break
                s = s[m.end() :]
        s = (s or "").strip() or "/"
        if not s.startswith("/"):
            s = "/" + s
        while "//" in s:
            s = s.replace("//", "/")
        if len(s) > 1 and s.endswith("/"):
            s = s.rstrip("/")
        return s or "/"

    @staticmethod
    def _is_same_api_path(url_a: str, url_b: str) -> bool:
        """判断两条 URL"""
        a = ApiAutomationService._extract_api_path_key(url_a)
        b = ApiAutomationService._extract_api_path_key(url_b)
        if a == b:
            return True

        def _suffix_match(longer: str, shorter: str) -> bool:
            if not shorter or shorter == "/":
                return False
            if not longer.endswith(shorter):
                return False
            
            if shorter.startswith("/"):
                return True
            return len(longer) == len(shorter) or longer[-len(shorter) - 1] == "/"

        if len(a) >= len(b) and _suffix_match(a, b):
            return True
        if len(b) >= len(a) and _suffix_match(b, a):
            return True
        return False

    @staticmethod
    def _prefer_existing_url(existing_url: str, incoming_url: str) -> str:
        """去重"""
        existing_url = str(existing_url or "").strip()
        incoming_url = str(incoming_url or "").strip() or "/"
        if existing_url and ApiAutomationService._is_same_api_path(existing_url, incoming_url):
            return existing_url
        return incoming_url

    @staticmethod
    def _find_api_by_path_and_method(
        candidates: List[Any],
        path: str,
        method: int,
    ) -> Optional[Any]:
        """
        按路径键查找
        """
        exact: List[Any] = []
        fuzzy: List[Tuple[int, Any]] = []
        path_key = ApiAutomationService._extract_api_path_key(path)
        for row in candidates or []:
            row_req = row.req if isinstance(getattr(row, "req", None), dict) else {}
            row_method = int(row_req.get("method") or 2)
            if row_method != int(method):
                continue
            row_url = str(getattr(row, "url", None) or row_req.get("url") or "")
            if not ApiAutomationService._is_same_api_path(row_url, path):
                continue
            row_key = ApiAutomationService._extract_api_path_key(row_url)
            if row_key == path_key:
                exact.append(row)
            else:
                fuzzy.append((len(row_key), row))
        if exact:
            for row in exact:
                if str(getattr(row, "url", None) or "") == path:
                    return row
            return exact[0]
        if fuzzy:
            fuzzy.sort(key=lambda x: x[0], reverse=True)
            return fuzzy[0][1]
        return None

    @staticmethod
    def _build_req_from_apifox_api(
        api: Dict[str, Any],
        header_defaults: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        header_defaults = header_defaults or {}
        method_name = str(api.get("method") or "POST").lower()
        path = ApiAutomationService._normalize_doc_path(str(api.get("path") or api.get("url") or "/"))

        params_obj = api.get("parameters") if isinstance(api.get("parameters"), dict) else {}
        path_params = ApiAutomationService._extract_apifox_param_rows(params_obj.get("path") or [])
        query_params = ApiAutomationService._extract_apifox_param_rows(params_obj.get("query") or [])
        header_params = ApiAutomationService._extract_apifox_param_rows(params_obj.get("header") or [])

        if not header_params:
            common_headers = ((api.get("commonParameters") or {}).get("header") or []) if isinstance(api.get("commonParameters"), dict) else []
            for h in common_headers:
                if not isinstance(h, dict):
                    continue
                name = str(h.get("name") or "").strip()
                if not name:
                    continue
                header_params.append({
                    "key": name,
                    "value": str(header_defaults.get(name) or ""),
                    "status": True,
                })

        request_body = api.get("requestBody") if isinstance(api.get("requestBody"), dict) else {}
        req_type = str(request_body.get("type") or "").lower()
        body_type = 1
        body: Any = {}
        form_data: List[Dict[str, Any]] = []
        form_urlencoded: List[Dict[str, Any]] = []

        if req_type in ("application/json", "json"):
            body_type = 2
            body = request_body.get("jsonSchema") or request_body.get("example") or {}
            examples = request_body.get("examples") or []
            if (not body or body == {}) and examples and isinstance(examples[0], dict):
                raw = examples[0].get("value")
                if isinstance(raw, str) and raw.strip():
                    try:
                        body = json.loads(raw)
                    except Exception:
                        body = raw
                        body_type = 1
                elif raw is not None:
                    body = raw
        elif req_type in ("multipart/form-data",):
            body_type = 3
            for p in request_body.get("parameters") or []:
                if isinstance(p, dict) and p.get("name"):
                    form_data.append({
                        "key": str(p.get("name")),
                        "value": "" if p.get("example") is None else str(p.get("example")),
                        "status": bool(p.get("enable", True)),
                        "data_type": str(p.get("type") or ""),
                        "remark": str(p.get("description") or ""),
                    })
        elif req_type in ("application/x-www-form-urlencoded", "x-www-form-urlencoded"):
            body_type = 4
            for p in request_body.get("parameters") or []:
                if isinstance(p, dict) and p.get("name"):
                    form_urlencoded.append({
                        "key": str(p.get("name")),
                        "value": "" if p.get("example") is None else str(p.get("example")),
                        "status": bool(p.get("enable", True)),
                    })
        elif req_type in ("text/plain", "raw", "text"):
            examples = request_body.get("examples") or []
            raw_val: Any = None
            if examples and isinstance(examples[0], dict):
                raw_val = examples[0].get("value")
            if isinstance(raw_val, str) and raw_val.strip():
                try:
                    body = json.loads(raw_val)
                    body_type = 2
                except Exception:
                    body = raw_val
                    body_type = 1
            elif raw_val is not None:
                body = raw_val
                body_type = 1
            else:
                body = request_body.get("jsonSchema") or {}
                body_type = 2 if body else 1
        elif req_type in ("none", "", "null"):
            body_type = 1
            body = {}

        return {
            "params_id": None,
            "body": body,
            "after": [],
            "assert": [],
            "before": [],
            "config": {"retry": 0, "req_timeout": 5, "res_timeout": 5},
            "header": header_params or [{"key": None, "value": None, "status": True}],
            "method": ApiAutomationService._doc_method_to_int(method_name),
            "params": (path_params + query_params) or [{"key": None, "value": None, "status": True}],
            "body_type": body_type,
            "file_path": [],
            "form_data": form_data or [],
            "form_urlencoded": form_urlencoded or [],
            "url": path,
        }

    @staticmethod
    async def _import_apifox_project_export(
        db: AsyncSession,
        doc_json: Dict[str, Any],
        api_service_id: int,
        user_id: int,
    ) -> Dict[str, int]:
        """导入 Apifox 客户端"""
        collections = doc_json.get("apiCollection") or []
        if not isinstance(collections, list) or not collections:
            raise ValueError("Apifox 项目导出中未找到 apiCollection")

        header_defaults: Dict[str, str] = {}
        common = doc_json.get("commonParameters")
        if isinstance(common, dict):
            params = common.get("parameters") if isinstance(common.get("parameters"), dict) else {}
            for h in (params.get("header") or []):
                if isinstance(h, dict) and h.get("name"):
                    header_defaults[str(h["name"])] = str(h.get("defaultValue") or "")

        imported_count = 0
        updated_count = 0
        folder_count = 0
        existing_apis = list(
            (
                await db.execute(
                    select(ApiModel).where(
                        ApiModel.enabled_flag == 1,
                        ApiModel.created_by == user_id,
                        ApiModel.api_service_id == api_service_id,
                    )
                )
            ).scalars().all()
        )

        async def get_or_create_folder(name: str, pid: int) -> int:
            nonlocal folder_count
            key_name = (name or "").strip() or "默认分组"
            row = (
                await db.execute(
                    select(ApiMenuModel).where(
                        ApiMenuModel.enabled_flag == 1,
                        ApiMenuModel.created_by == user_id,
                        ApiMenuModel.api_service_id == api_service_id,
                        ApiMenuModel.type == 1,
                        ApiMenuModel.pid == pid,
                        ApiMenuModel.name == key_name,
                    )
                )
            ).scalar_one_or_none()
            if row:
                return int(row.id)
            menu = ApiMenuModel(
                name=key_name,
                type=1,
                pid=pid,
                api_service_id=api_service_id,
                status=1,
                api_id=None,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(menu)
            await db.flush()
            folder_count += 1
            return int(menu.id)

        async def upsert_api(
            api_name: str,
            api_obj: Dict[str, Any],
            folder_id: int,
            inherited_pre: Optional[List[Any]] = None,
            inherited_post: Optional[List[Any]] = None,
        ) -> None:
            nonlocal imported_count, updated_count
            req = ApiAutomationService._build_req_from_apifox_api(api_obj, header_defaults)
            pre = ApiAutomationService._resolve_apifox_processors(
                api_obj.get("preProcessors"), inherited_pre
            )
            post = ApiAutomationService._resolve_apifox_processors(
                api_obj.get("postProcessors"), inherited_post
            )
            req["before"] = ApiAutomationService._map_apifox_processors(pre, phase="before")
            req["after"] = ApiAutomationService._map_apifox_processors(post, phase="after")
            path = str(req.get("url") or "/")
            api_desc = str(api_obj.get("description") or "")
            display_name = str(api_name or api_obj.get("name") or f"{str(api_obj.get('method') or 'POST').upper()} {path}")

            target_method = int(req.get("method") or 2)
            target_api = ApiAutomationService._find_api_by_path_and_method(
                existing_apis, path, target_method
            )

            if target_api:
                keep_url = ApiAutomationService._prefer_existing_url(
                    str(target_api.url or (target_api.req or {}).get("url") or ""),
                    path,
                )
                req["url"] = keep_url
                
                old_req = target_api.req if isinstance(target_api.req, dict) else {}
                if old_req.get("assert"):
                    req["assert"] = old_req.get("assert")
                if old_req.get("config"):
                    req["config"] = old_req.get("config")
                await db.execute(
                    update(ApiModel)
                    .where(ApiModel.id == target_api.id, ApiModel.enabled_flag == 1)
                    .values(
                        url=keep_url,
                        req=req,
                        document=api_obj,
                        name=display_name,
                        description=api_desc,
                        updated_by=user_id,
                    )
                )
                api_id = int(target_api.id)
                updated_count += 1
            else:
                api_row = ApiModel(
                    api_service_id=api_service_id,
                    url=path,
                    req=req,
                    document=api_obj,
                    name=display_name,
                    description=api_desc,
                    created_by=user_id,
                    updated_by=user_id,
                )
                db.add(api_row)
                await db.flush()
                api_id = int(api_row.id)
                existing_apis.append(api_row)
                imported_count += 1

            leaf = (
                await db.execute(
                    select(ApiMenuModel).where(
                        ApiMenuModel.enabled_flag == 1,
                        ApiMenuModel.created_by == user_id,
                        ApiMenuModel.api_service_id == api_service_id,
                        ApiMenuModel.type == 2,
                        ApiMenuModel.api_id == api_id,
                    )
                )
            ).scalar_one_or_none()

            if leaf:
                await db.execute(
                    update(ApiMenuModel)
                    .where(ApiMenuModel.id == leaf.id, ApiMenuModel.enabled_flag == 1)
                    .values(name=display_name, pid=folder_id, status=1, updated_by=user_id)
                )
            else:
                db.add(
                    ApiMenuModel(
                        name=display_name,
                        type=2,
                        pid=folder_id,
                        api_service_id=api_service_id,
                        api_id=api_id,
                        status=1,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                )

        async def walk_items(
            items: Any,
            parent_folder_id: int,
            inherited_pre: Optional[List[Any]] = None,
            inherited_post: Optional[List[Any]] = None,
        ) -> None:
            if not isinstance(items, list):
                return
            inherited_pre = list(inherited_pre or [])
            inherited_post = list(inherited_post or [])
            for node in items:
                if not isinstance(node, dict):
                    continue
                api_obj = node.get("api")
                if isinstance(api_obj, dict) and (api_obj.get("path") or api_obj.get("url") or api_obj.get("method")):
                    await upsert_api(
                        str(node.get("name") or ""),
                        api_obj,
                        parent_folder_id,
                        inherited_pre=inherited_pre,
                        inherited_post=inherited_post,
                    )
                    continue
                # 目录节点
                child_items = node.get("items")
                if isinstance(child_items, list):
                    folder_name = str(node.get("name") or "默认分组")
                    next_pre = ApiAutomationService._resolve_apifox_processors(
                        node.get("preProcessors"), inherited_pre
                    )
                    next_post = ApiAutomationService._resolve_apifox_processors(
                        node.get("postProcessors"), inherited_post
                    )
                    
                    if folder_name.strip() in ("根目录", "Root", "root") and parent_folder_id == 0:
                        await walk_items(child_items, 0, next_pre, next_post)
                    else:
                        folder_id = await get_or_create_folder(folder_name, parent_folder_id)
                        await walk_items(child_items, folder_id, next_pre, next_post)

        for coll in collections:
            if not isinstance(coll, dict):
                continue
            name = str(coll.get("name") or "根目录")
            items = coll.get("items") or []
            coll_pre = ApiAutomationService._resolve_apifox_processors(coll.get("preProcessors"), [])
            coll_post = ApiAutomationService._resolve_apifox_processors(coll.get("postProcessors"), [])
            if name.strip() in ("根目录", "Root", "root"):
                await walk_items(items, 0, coll_pre, coll_post)
            else:
                folder_id = await get_or_create_folder(name, 0)
                await walk_items(items, folder_id, coll_pre, coll_post)

        if imported_count + updated_count <= 0:
            raise ValueError("Apifox 项目导出已识别，但未解析到可导入的 HTTP 接口（apiCollection.items[].api）")

        await db.execute(
            update(ApiServiceModel)
            .where(ApiServiceModel.id == api_service_id, ApiServiceModel.enabled_flag == 1)
            .values(last_pull_status=1)
        )
        await db.commit()
        return {"imported": imported_count, "updated": updated_count, "folders": folder_count}

    @staticmethod
    async def _pull_apifox_project_and_import(
        db: AsyncSession,
        api_service_id: int,
        project_id: str,
        auth_text: str,
        user_id: int,
    ) -> Dict[str, int]:
        auth_text = str(auth_text or "").strip()
        is_bearer = auth_text.lower().startswith("bearer ")
        base_headers = {
            "x-project-id": str(project_id),
            "x-client-version": "2.8.2-alpha.2",
            "accept": "application/json, text/plain, */*",
            "user-agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        if is_bearer:
            base_headers["authorization"] = auth_text

            base_headers["cookie"] = auth_text
        else:
            base_headers["cookie"] = auth_text

        def pull_data(url: str) -> Any:
            r = requests.get(url, headers=base_headers, timeout=30)
            ct = str(r.headers.get("Content-Type") or "").lower()
            text = (r.text or "").strip()
            if r.status_code >= 400:
                preview = text[:200] if text else "<empty>"
                raise ValueError(f"Apifox 请求失败（{url} HTTP {r.status_code}, Content-Type: {ct or 'unknown'}），响应片段: {preview}")
            try:
                data = r.json()
            except Exception:
                preview = text[:200] if text else "<empty>"
                raise ValueError(f"Apifox 返回非 JSON（{url} HTTP {r.status_code}, Content-Type: {ct or 'unknown'}），响应片段: {preview}")
            return data.get("data", data)

        tree_data = pull_data(f"https://api.apifox.com/api/v1/projects/{project_id}/api-tree-list?locale=zh-CN")
        detail_data = pull_data("https://api.apifox.com/api/v1/api-details?locale=zh-CN")

        detail_by_id: Dict[int, Dict[str, Any]] = {}
        for d in detail_data or []:
            if isinstance(d, dict) and d.get("id") is not None:
                detail_by_id[int(d["id"])] = d

        module_nodes = tree_data.get("children", []) if isinstance(tree_data, dict) else (tree_data or [])
        if (
            isinstance(module_nodes, list)
            and module_nodes
            and isinstance(module_nodes[0], dict)
            and "children" in module_nodes[0]
            and "api" not in module_nodes[0]
        ):
            module_nodes = module_nodes[0].get("children", [])

        folder_cache: Dict[str, int] = {}

        async def get_or_create_folder(folder_name: str) -> int:
            key = folder_name.strip() or "默认分组"
            if key in folder_cache:
                return folder_cache[key]
            row = (
                await db.execute(
                    select(ApiMenuModel).where(
                        ApiMenuModel.enabled_flag == 1,
                        ApiMenuModel.created_by == user_id,
                        ApiMenuModel.api_service_id == api_service_id,
                        ApiMenuModel.type == 1,
                        ApiMenuModel.pid == 0,
                        ApiMenuModel.name == key,
                    )
                )
            ).scalar_one_or_none()
            if row:
                folder_cache[key] = int(row.id)
                return int(row.id)
            menu = ApiMenuModel(
                name=key,
                type=1,
                pid=0,
                api_service_id=api_service_id,
                status=1,
                api_id=None,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(menu)
            await db.flush()
            folder_cache[key] = int(menu.id)
            return int(menu.id)

        imported_count = 0
        updated_count = 0
        folder_names = set()
        existing_apis = list(
            (
                await db.execute(
                    select(ApiModel).where(
                        ApiModel.enabled_flag == 1,
                        ApiModel.created_by == user_id,
                        ApiModel.api_service_id == api_service_id,
                    )
                )
            ).scalars().all()
        )

        for module_data in module_nodes or []:
            if not isinstance(module_data, dict):
                continue
            folder_name = str(module_data.get("name") or "默认分组")
            folder_id = await get_or_create_folder(folder_name)
            folder_names.add(folder_name)

            for node in module_data.get("children", []) or []:
                if not isinstance(node, dict) or not isinstance(node.get("api"), dict):
                    continue
                api_brief = node.get("api") or {}
                ext_api_id = api_brief.get("id")
                detail = detail_by_id.get(int(ext_api_id)) if ext_api_id is not None else {}
                detail = detail or {}

                method_name = str(api_brief.get("method") or "POST").lower()
                path = ApiAutomationService._normalize_doc_path(
                    str(api_brief.get("path") or api_brief.get("url") or "/")
                )
                api_name = str(api_brief.get("name") or f"{method_name.upper()} {path}")
                api_desc = str(detail.get("description") or api_brief.get("description") or "")

                params_obj = detail.get("parameters") or {}
                path_params = ApiAutomationService._extract_apifox_param_rows(params_obj.get("path") or [])
                query_params = ApiAutomationService._extract_apifox_param_rows(params_obj.get("query") or [])
                header_params = ApiAutomationService._extract_apifox_param_rows(params_obj.get("header") or [])

                request_body = detail.get("requestBody") or {}
                req_type = str(request_body.get("type") or "")
                body_type = 1
                body: Any = {}
                form_data: List[Dict[str, Any]] = []
                if req_type == "application/json":
                    body_type = 2
                    body = request_body.get("jsonSchema") or {}
                elif req_type == "multipart/form-data":
                    body_type = 3
                    for p in request_body.get("parameters") or []:
                        if isinstance(p, dict) and p.get("name"):
                            form_data.append(
                                {
                                    "key": str(p.get("name")),
                                    "value": "",
                                    "status": True,
                                    "data_type": str(p.get("type") or ""),
                                    "remark": str(p.get("description") or ""),
                                }
                            )

                req = {
                    "params_id": None,
                    "body": body,
                    "after": [],
                    "assert": [],
                    "before": [],
                    "config": {"retry": 0, "req_timeout": 5, "res_timeout": 5},
                    "header": header_params or [{"key": None, "value": None, "status": True}],
                    "method": ApiAutomationService._doc_method_to_int(method_name),
                    "params": (path_params + query_params) or [{"key": None, "value": None, "status": True}],
                    "body_type": body_type,
                    "file_path": [],
                    "form_data": form_data or [],
                    "form_urlencoded": [],
                    "url": path,
                }

                target_method = int(req.get("method") or 2)
                target_api = ApiAutomationService._find_api_by_path_and_method(
                    existing_apis, path, target_method
                )

                if target_api:
                    keep_url = ApiAutomationService._prefer_existing_url(
                        str(target_api.url or (target_api.req or {}).get("url") or ""),
                        path,
                    )
                    req["url"] = keep_url
                    old_req = target_api.req if isinstance(target_api.req, dict) else {}
                    if old_req.get("assert"):
                        req["assert"] = old_req.get("assert")
                    if old_req.get("before"):
                        req["before"] = old_req.get("before")
                    if old_req.get("after"):
                        req["after"] = old_req.get("after")
                    if old_req.get("config"):
                        req["config"] = old_req.get("config")
                    await db.execute(
                        update(ApiModel)
                        .where(ApiModel.id == target_api.id, ApiModel.enabled_flag == 1)
                        .values(
                            url=keep_url,
                            req=req,
                            document=detail or api_brief,
                            name=api_name,
                            description=api_desc,
                            updated_by=user_id,
                        )
                    )
                    api_id = int(target_api.id)
                    updated_count += 1
                else:
                    api_row = ApiModel(
                        api_service_id=api_service_id,
                        url=path,
                        req=req,
                        document=detail or api_brief,
                        name=api_name,
                        description=api_desc,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    db.add(api_row)
                    await db.flush()
                    api_id = int(api_row.id)
                    existing_apis.append(api_row)
                    imported_count += 1

                leaf = (
                    await db.execute(
                        select(ApiMenuModel).where(
                            ApiMenuModel.enabled_flag == 1,
                            ApiMenuModel.created_by == user_id,
                            ApiMenuModel.api_service_id == api_service_id,
                            ApiMenuModel.type == 2,
                            ApiMenuModel.api_id == api_id,
                        )
                    )
                ).scalar_one_or_none()

                if leaf:
                    await db.execute(
                        update(ApiMenuModel)
                        .where(ApiMenuModel.id == leaf.id, ApiMenuModel.enabled_flag == 1)
                        .values(name=api_name, pid=folder_id, status=1, updated_by=user_id)
                    )
                else:
                    db.add(
                        ApiMenuModel(
                            name=api_name,
                            type=2,
                            pid=folder_id,
                            api_service_id=api_service_id,
                            api_id=api_id,
                            status=1,
                            created_by=user_id,
                            updated_by=user_id,
                        )
                    )

        if imported_count + updated_count <= 0:
            auth_hint = "Bearer Token" if is_bearer else "Cookies"
            raise ValueError(
                f"Apifox 接口已请求成功但未解析到可导入接口，请检查项目权限和{auth_hint}是否有效（project_id={project_id}）"
            )

        await db.commit()
        return {"imported": imported_count, "updated": updated_count, "folders": len(folder_names)}

    @staticmethod
    async def pull_api_doc(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        api_service_id = int(body.get("api_service_id") or 0)
        doc_url = str(body.get("doc_url") or "").strip()
        source_type = str(body.get("source_type") or "swagger").strip().lower()
        doc_content = body.get("doc_content")
        cookies = str(body.get("cookies") or "").strip()

        if not api_service_id:
            raise ValueError("api_service_id 不能为空")
        if not doc_url and not isinstance(doc_content, dict):
            raise ValueError("文档地址或文档内容至少提供一个")
        if source_type not in ("swagger", "apifox"):
            raise ValueError("source_type 仅支持 swagger 或 apifox")

        service = (
            await db.execute(
                select(ApiServiceModel).where(
                    ApiServiceModel.id == api_service_id,
                    ApiServiceModel.enabled_flag == 1,
                    ApiServiceModel.created_by == user_id,
                )
            )
        ).scalar_one_or_none()
        if not service:
            raise ValueError("服务不存在或无权限")

        apifox_project_pull_error: Optional[str] = None
       
        if source_type == "apifox" and "app.apifox.com/project/" in doc_url:
            project_id = ""
            try:
                project_id = doc_url.split("/project/")[1].split("?")[0].split("/")[0].strip()
            except Exception:
                project_id = ""
            if project_id and cookies:
                try:
                    stats = await ApiAutomationService._pull_apifox_project_and_import(
                        db=db,
                        api_service_id=api_service_id,
                        project_id=project_id,
                        cookies=cookies,
                        user_id=user_id,
                    )
                    return {
                        "source_type": source_type,
                        "imported": int(stats.get("imported") or 0),
                        "updated": int(stats.get("updated") or 0),
                        "folders": int(stats.get("folders") or 0),
                        "mode": "apifox_project_url",
                    }
                except Exception as e:
      
                    apifox_project_pull_error = str(e)

        if isinstance(doc_content, dict):
            doc_json = doc_content
        else:
            try:
                headers = {
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    "Referer": doc_url,
                    "Origin": "https://app.apifox.com",
                }
                if source_type == "apifox" and cookies:
                    headers["Cookie"] = cookies

                def try_parse_json_response(resp_obj: requests.Response) -> Optional[Dict[str, Any]]:
                    ct = str(resp_obj.headers.get("Content-Type") or "").lower()
                    text_body = resp_obj.text or ""
                    if "application/json" in ct:
                        try:
                            return resp_obj.json()
                        except Exception:
                            return None
                    stripped_text = text_body.strip()
                    if stripped_text.startswith("{") or stripped_text.startswith("["):
                        try:
                            parsed = json.loads(stripped_text)
                            if isinstance(parsed, dict):
                                return parsed
                        except Exception:
                            return None
                    return None

                def try_parse_markdown_openapi(text_body: str) -> Optional[Dict[str, Any]]:
                    """
                    Apifox 文档页 / 导出页返回 markdown：
                    - Markdown 中包含 ```yaml ...``` 或 ```yml ...``` 的 OpenAPI 内容
                    """
                    import re

                    if not text_body:
                        return None
                    m = re.search(r"```(?:yaml|yml)\s*([\s\S]*?)```", text_body, flags=re.IGNORECASE)
                    if not m:
                        return None
                    yaml_text = (m.group(1) or "").strip()
                    if not yaml_text:
                        return None
                    try:
                        parsed = yaml.safe_load(yaml_text)
                        return parsed if isinstance(parsed, dict) else None
                    except Exception:
                        return None

                resp = requests.get(doc_url, headers=headers, timeout=20)
                resp.raise_for_status()
                parsed_json = try_parse_json_response(resp)
                if parsed_json is not None:
                    doc_json = parsed_json
                else:
                    text = (resp.text or "").strip()
                    md_parsed = try_parse_markdown_openapi(text)
                    if isinstance(md_parsed, dict) and (md_parsed.get("paths") or md_parsed.get("openapi") or md_parsed.get("swagger")):
                        doc_json = md_parsed
                    else:
                     
                        if source_type == "apifox" and "app.apifox.com/project/" in doc_url:
                            import re
                            m = re.search(r"/project/(\d+)", doc_url)
                            project_id = m.group(1) if m else ""
                            candidates: List[str] = []
                            if project_id:
                                candidates.extend([
                                    f"https://api.apifox.com/api/v1/projects/{project_id}/export-openapi",
                                    f"https://api.apifox.com/api/v1/projects/{project_id}/openapi",
                                    f"https://app.apifox.com/api/v1/projects/{project_id}/export-openapi",
                                    f"https://app.apifox.com/api/v1/projects/{project_id}/openapi",
                                ])
                            for c in candidates:
                                try:
                                    rr = requests.get(c, headers=headers, timeout=20)
                                    if rr.status_code >= 400:
                                        continue
                                    cand_json = try_parse_json_response(rr)
                                    if isinstance(cand_json, dict):
                                        if cand_json.get("paths") or cand_json.get("apis") or (cand_json.get("data") or {}).get("paths") or (cand_json.get("data") or {}).get("apis"):
                                            doc_json = cand_json
                                            break
                                except Exception:
                                    continue
                            else:
                                preview = text[:200] if text else "<empty>"
                                raise ValueError(
                                    "当前项目地址返回 HTML，且自动探测 JSON 导出接口失败。"
                                    f"请确认 Cookies 可用，或填写可直接返回 JSON 的导出地址。响应片段: {preview}"
                                )
                        else:
                            content_type = str(resp.headers.get("Content-Type") or "").lower()
                            preview = text[:200] if text else "<empty>"
                            if source_type == "apifox" and "app.apifox.com/project/" in doc_url:
                          
                                extra = f"；Apifox 专用拉取错误: {apifox_project_pull_error}" if apifox_project_pull_error else ""
                                raise ValueError(
                                    "Apifox 项目页返回的是 Markdown 页面而非 OpenAPI 文档。"
                                    f"{extra}；响应片段: {preview}"
                                )
                            raise ValueError(
                                f"返回内容不是 JSON（HTTP {resp.status_code}, Content-Type: {content_type or 'unknown'}），响应片段: {preview}"
                            )
            except Exception as e:
                raise ValueError(f"拉取文档失败: {str(e)}")

        
        if ApiAutomationService._is_apifox_project_export(doc_json):
            stats = await ApiAutomationService._import_apifox_project_export(
                db, doc_json, api_service_id, user_id
            )
            return {
                "source_type": source_type or "apifox",
                "imported": int(stats.get("imported") or 0),
                "updated": int(stats.get("updated") or 0),
                "folders": int(stats.get("folders") or 0),
                "mode": "apifox_project_export",
            }

        # 兼容多种文档结构：
        paths: Dict[str, Any] = {}
        candidates = [
            doc_json.get("paths"),
            (doc_json.get("data") or {}).get("paths") if isinstance(doc_json.get("data"), dict) else None,
            ((doc_json.get("data") or {}).get("openapi") or {}).get("paths")
            if isinstance(doc_json.get("data"), dict) and isinstance((doc_json.get("data") or {}).get("openapi"), dict)
            else None,
            (doc_json.get("openapi") or {}).get("paths") if isinstance(doc_json.get("openapi"), dict) else None,
        ]
        for c in candidates:
            if isinstance(c, dict) and c:
                paths = c
                break

        if not paths:
            apis = doc_json.get("apis")
            if not isinstance(apis, list):
                data = doc_json.get("data") or {}
                apis = data.get("apis") if isinstance(data, dict) else None
            if isinstance(apis, list) and apis:
                stats = await ApiAutomationService.handle_gitlab_import(db, apis, api_service_id, user_id)
                return {
                    "source_type": source_type,
                    "imported": int(stats.get("imported") or 0),
                    "updated": int(stats.get("updated") or 0),
                    "folders": int(stats.get("folders") or 0),
                    "mode": "apifox_apis",
                }
            
            top_keys = list(doc_json.keys()) if isinstance(doc_json, dict) else []
            data_keys = list((doc_json.get("data") or {}).keys()) if isinstance(doc_json, dict) and isinstance(doc_json.get("data"), dict) else []
            raise ValueError(
                "文档中未找到可解析接口（paths/apis/apiCollection），请确认 URL、Cookies 或导出文件格式；"
                f"top_keys={top_keys[:20]}, data_keys={data_keys[:20]}"
            )

        folder_cache: Dict[str, int] = {}

        async def get_or_create_folder(folder_name: str) -> int:
            key = folder_name.strip() or "默认分组"
            if key in folder_cache:
                return folder_cache[key]
            row = (
                await db.execute(
                    select(ApiMenuModel).where(
                        ApiMenuModel.enabled_flag == 1,
                        ApiMenuModel.created_by == user_id,
                        ApiMenuModel.api_service_id == api_service_id,
                        ApiMenuModel.type == 1,
                        ApiMenuModel.pid == 0,
                        ApiMenuModel.name == key,
                    )
                )
            ).scalar_one_or_none()
            if row:
                folder_cache[key] = int(row.id)
                return int(row.id)
            menu = ApiMenuModel(
                name=key,
                type=1,
                pid=0,
                api_service_id=api_service_id,
                status=1,
                api_id=None,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(menu)
            await db.flush()
            folder_cache[key] = int(menu.id)
            return int(menu.id)

        imported_count = 0
        updated_count = 0
        folder_names = set()
        existing_apis = list(
            (
                await db.execute(
                    select(ApiModel).where(
                        ApiModel.enabled_flag == 1,
                        ApiModel.created_by == user_id,
                        ApiModel.api_service_id == api_service_id,
                    )
                )
            ).scalars().all()
        )

        for raw_path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            api_path = ApiAutomationService._normalize_doc_path(str(raw_path or "/"))

            for method in ("get", "post", "put", "delete", "patch", "options"):
                operation = path_item.get(method)
                if not isinstance(operation, dict):
                    continue

                tags = operation.get("tags") or []
                folder_name = str(tags[0] if tags else "默认分组")
                folder_id = await get_or_create_folder(folder_name)
                folder_names.add(folder_name)

                req = ApiAutomationService._build_req_from_openapi(api_path, method, operation)
                api_name = str(operation.get("summary") or operation.get("operationId") or f"{method.upper()} {api_path}")
                api_desc = str(operation.get("description") or "")

                target_method = int(req.get("method") or 2)
                target_api = ApiAutomationService._find_api_by_path_and_method(
                    existing_apis, api_path, target_method
                )

                if target_api:
                    keep_url = ApiAutomationService._prefer_existing_url(
                        str(target_api.url or (target_api.req or {}).get("url") or ""),
                        api_path,
                    )
                    req["url"] = keep_url
                    old_req = target_api.req if isinstance(target_api.req, dict) else {}
                    if old_req.get("assert"):
                        req["assert"] = old_req.get("assert")
                    if old_req.get("before"):
                        req["before"] = old_req.get("before")
                    if old_req.get("after"):
                        req["after"] = old_req.get("after")
                    if old_req.get("config"):
                        req["config"] = old_req.get("config")
                    await db.execute(
                        update(ApiModel)
                        .where(ApiModel.id == target_api.id, ApiModel.enabled_flag == 1)
                        .values(
                            url=keep_url,
                            req=req,
                            document=operation,
                            name=api_name,
                            description=api_desc,
                            updated_by=user_id,
                        )
                    )
                    api_id = int(target_api.id)
                    updated_count += 1
                else:
                    api_row = ApiModel(
                        api_service_id=api_service_id,
                        url=api_path,
                        req=req,
                        document=operation,
                        name=api_name,
                        description=api_desc,
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    db.add(api_row)
                    await db.flush()
                    api_id = int(api_row.id)
                    existing_apis.append(api_row)
                    imported_count += 1

                leaf = (
                    await db.execute(
                        select(ApiMenuModel).where(
                            ApiMenuModel.enabled_flag == 1,
                            ApiMenuModel.created_by == user_id,
                            ApiMenuModel.api_service_id == api_service_id,
                            ApiMenuModel.type == 2,
                            ApiMenuModel.api_id == api_id,
                        )
                    )
                ).scalar_one_or_none()

                if leaf:
                    await db.execute(
                        update(ApiMenuModel)
                        .where(ApiMenuModel.id == leaf.id, ApiMenuModel.enabled_flag == 1)
                        .values(name=api_name, pid=folder_id, status=1, updated_by=user_id)
                    )
                else:
                    db.add(
                        ApiMenuModel(
                            name=api_name,
                            type=2,
                            pid=folder_id,
                            api_service_id=api_service_id,
                            api_id=api_id,
                            status=1,
                            created_by=user_id,
                            updated_by=user_id,
                        )
                    )

        # 更新拉取状态为成功
        await db.execute(
            update(ApiServiceModel)
            .where(ApiServiceModel.id == api_service_id, ApiServiceModel.enabled_flag == 1)
            .values(last_pull_status=1)
        )
        await db.commit()
        return {
            "source_type": source_type,
            "imported": imported_count,
            "updated": updated_count,
            "folders": len(folder_names),
        }

    @staticmethod
    async def add_menu(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
     
        api_id = None
        if int(body.get("type")) != 1:
            default_req = {
                "params_id": None,
                "body": {},
                "after": [],
                "assert": [],
                "before": [],
                "config": {"retry": 0, "req_timeout": 5, "res_timeout": 5},
                "header": [{"key": "Content-Type", "value": "application/json", "status": True}],
                "method": 2,
                "params": [],
                "body_type": 2,
                "file_path": [],
                "form_data": [],
                "form_urlencoded": [],
            }
            api = ApiModel(
                api_service_id=int(body["api_service_id"]),
                url="/",
                document={},
                req=default_req,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(api)
            await db.flush()
            api_id = api.id

        menu = ApiMenuModel(
            name=body["name"],
            pid=int(body["pid"]),
            type=int(body["type"]),
            api_service_id=int(body["api_service_id"]),
            status=1,
            api_id=api_id,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(menu)
        await db.commit()

    @staticmethod
    async def edit_menu(db: AsyncSession, menu_id: int, name: str, user_id: int) -> None:
        await db.execute(
            update(ApiMenuModel)
            .where(ApiMenuModel.id == int(menu_id), ApiMenuModel.enabled_flag == 1, ApiMenuModel.created_by == user_id)
            .values(name=name, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def del_menu(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        
        menu_id = int(body["id"])
        m = await db.execute(select(ApiMenuModel).where(ApiMenuModel.id == menu_id, ApiMenuModel.enabled_flag == 1))
        menu = m.scalar_one_or_none()
        if not menu:
            return
        if int(body.get("type", menu.type)) != 1 and menu.api_id:
            await db.execute(update(ApiModel).where(ApiModel.id == int(menu.api_id)).values(enabled_flag=0))
        await db.execute(update(ApiMenuModel).where(ApiMenuModel.id == menu_id).values(enabled_flag=0, updated_by=user_id))
        await db.commit()

    @staticmethod
    async def copy_menu(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        api_id = int(body["api_id"])
        api_row = (await db.execute(select(ApiModel).where(ApiModel.id == api_id, ApiModel.enabled_flag == 1))).scalar_one()
        new_api = ApiModel(
            url=api_row.url,
            req=api_row.req,
            document=api_row.document,
            api_service_id=api_row.api_service_id,
            name=api_row.name,
            description=api_row.description,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(new_api)
        await db.flush()

        menu_id = int(body["id"])
        menu_row = (await db.execute(select(ApiMenuModel).where(ApiMenuModel.id == menu_id, ApiMenuModel.enabled_flag == 1))).scalar_one()
        new_menu = ApiMenuModel(
            name=menu_row.name,
            type=menu_row.type,
            pid=menu_row.pid,
            api_id=new_api.id,
            api_service_id=menu_row.api_service_id,
            status=menu_row.status,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(new_menu)
        await db.commit()

    @staticmethod
    async def get_api_info(db: AsyncSession, api_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        row = (
            await db.execute(
                select(ApiModel).where(ApiModel.id == int(api_id), ApiModel.enabled_flag == 1, ApiModel.created_by == user_id)
            )
        ).scalar_one_or_none()
        if not row:
            return None
        data = row.__dict__.copy()
        data.pop("_sa_instance_state", None)

        return data

    @staticmethod
    def _compare_data(old_data: Any, new_data: Any, path: str = "") -> List[Dict[str, Any]]:
        changes: List[Dict[str, Any]] = []
        if isinstance(old_data, dict) and isinstance(new_data, dict):
            all_keys = set(old_data.keys()).union(new_data.keys())
            for key in all_keys:
                old_val = old_data.get(key, "__key_missing__")
                new_val = new_data.get(key, "__key_missing__")
                sub_path = f"{path}.{key}" if path else key
                if old_val == "__key_missing__":
                    changes.append({"field": sub_path, "type": "add", "old": None, "new": new_val})
                elif new_val == "__key_missing__":
                    changes.append({"field": sub_path, "type": "delete", "old": old_val, "new": None})
                else:
                    changes.extend(ApiAutomationService._compare_data(old_val, new_val, sub_path))
        elif isinstance(old_data, list) and isinstance(new_data, list):
            max_len = max(len(old_data), len(new_data))
            for i in range(max_len):
                old_val = old_data[i] if i < len(old_data) else "__index_missing__"
                new_val = new_data[i] if i < len(new_data) else "__index_missing__"
                sub_path = f"{path}[{i}]"
                if old_val == "__index_missing__":
                    changes.append({"field": sub_path, "type": "add", "old": None, "new": new_val})
                elif new_val == "__index_missing__":
                    changes.append({"field": sub_path, "type": "delete", "old": old_val, "new": None})
                else:
                    changes.extend(ApiAutomationService._compare_data(old_val, new_val, sub_path))
        else:
            if old_data != new_data:
                changes.append({"field": path, "type": "edit", "old": old_data, "new": new_data})
        return changes

    @staticmethod
    async def save_api(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        api_id = int(body["id"])
        row = (await db.execute(select(ApiModel).where(ApiModel.id == api_id, ApiModel.enabled_flag == 1))).scalar_one()
        old_req = row.req or {}
        values: Dict[str, Any] = {"updated_by": user_id}
        if "url" in body and body.get("url") is not None:
            values["url"] = body.get("url")
        if "req" in body:
            values["req"] = body.get("req") or {}
        if "document" in body:
            values["document"] = body.get("document") if body.get("document") is not None else {}
        if body.get("name") is not None:
            values["name"] = body.get("name")
        if body.get("description") is not None:
            values["description"] = body.get("description")
        await db.execute(
            update(ApiModel)
            .where(ApiModel.id == api_id, ApiModel.enabled_flag == 1)
            .values(**values)
        )
        if "req" in body:
            edits = ApiAutomationService._compare_data(old_req, values.get("req") or {})
            if edits:
                db.add(ApiEditModel(api_id=api_id, edit=edits, created_by=user_id, updated_by=user_id))
        await db.commit()

    @staticmethod
    async def save_api_case(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        """
        - 基于传入的接口配置新增一条 Api
        - 并在原接口所在菜单下创建一个 type=3 的用例节点
        """
        api_menu = (
            await db.execute(
                select(ApiMenuModel).where(
                    ApiMenuModel.enabled_flag == 1,
                    ApiMenuModel.created_by == user_id,
                    ApiMenuModel.api_id == int(body["id"]),
                )
            )
        ).scalar_one_or_none()
        if not api_menu:
            raise ValueError("未找到原接口对应的菜单节点")

        api = ApiModel(
            url=str(body.get("url") or "/"),
            req=body.get("req") or {},
            document=body.get("document") or {},
            api_service_id=int(body["api_service_id"]),
            name=body.get("name"),
            description=body.get("description"),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(api)
        await db.flush()

        menu = ApiMenuModel(
            api_id=api.id,
            name=str(body.get("name") or api.url),
            created_by=user_id,
            updated_by=user_id,
            type=3,
            pid=int(api_menu.id),
            api_service_id=int(body["api_service_id"]),
            status=1,
        )
        db.add(menu)
        await db.commit()

    @staticmethod
    async def save_api_case_to_suite(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """将接口调试结果保存为用例，存入指定用例集"""
        from .model import ApiCaseModel
        case = ApiCaseModel(
            name=str(body["name"]),
            description=body.get("description") or "",
            suite_id=int(body["suite_id"]),
            script=body.get("script") or [],
            status=0,
            case_type=int(body.get("case_type") or 1),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)
        d = case.__dict__.copy()
        d.pop("_sa_instance_state", None)
        return d

  
    @staticmethod
    async def get_request_history(
        db: AsyncSession,
        user_id: int,
        api_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Dict[str, Any]:
        page = max(int(page or 1), 1)
        page_size = min(max(int(page_size or 10), 1), 100)
        conditions = [
            ApiResultModel.enabled_flag == 1,
            ApiResultModel.created_by == user_id,
        ]
        if api_id:
            conditions.append(ApiResultModel.api_id == int(api_id))

        count_stmt = select(func.count()).select_from(ApiResultModel).where(*conditions)
        total = int((await db.execute(count_stmt)).scalar() or 0)

        stmt = (
            select(ApiResultModel)
            .where(*conditions)
            .order_by(ApiResultModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": total, "page": page, "pageSize": page_size}

    @staticmethod
    async def delete_request_history(db: AsyncSession, result_id: int, user_id: int) -> None:
        """删除单条调试记录。"""
        result = await db.execute(
            delete(ApiResultModel).where(
                ApiResultModel.id == int(result_id),
                ApiResultModel.created_by == user_id,
            )
        )
        if not result.rowcount:
            raise ValueError("调试记录不存在或无权限")
        await db.commit()

    @staticmethod
    async def get_edit_history(db: AsyncSession, api_id: int, user_id: int) -> List[Dict[str, Any]]:
        stmt = (
            select(ApiEditModel)
            .where(
                ApiEditModel.enabled_flag == 1,
                ApiEditModel.api_id == api_id,
                ApiEditModel.created_by == user_id,
            )
            .order_by(ApiEditModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

    @staticmethod
    async def get_api_case(db: AsyncSession, script: List[List[Any]], user_id: int) -> List[Dict[str, Any]]:
        """
        - script: [[..., api_id], ...]
        - 返回 ApiMenu(type=3) 列表
        """
        api_ids: List[int] = []
        for item in script or []:
            try:
                api_ids.append(int(item[-1]))
            except Exception:
                continue
        if not api_ids:
            return []
        rows = (
            await db.execute(
                select(ApiMenuModel).where(
                    ApiMenuModel.enabled_flag == 1,
                    ApiMenuModel.created_by == user_id,
                    ApiMenuModel.type == 3,
                    ApiMenuModel.api_id.in_(api_ids),
                )
            )
        ).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

  
    @staticmethod
    async def get_api_scripts(db: AsyncSession, user_id: int, page: int, page_size: int) -> Dict[str, Any]:
        stmt = (
            select(ApiScriptModel)
            .where(ApiScriptModel.enabled_flag == 1, ApiScriptModel.created_by == user_id)
            .order_by(ApiScriptModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = rows[start:end]
        content: List[Dict[str, Any]] = []
        for r in page_rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            content.append(d)
        return {"content": content, "total": total, "page": page, "pageSize": page_size}

    @staticmethod
    async def add_api_script(db: AsyncSession, data: Dict[str, Any], user_id: int) -> None:
        script = ApiScriptModel(
            name=data["name"],
            type=int(data.get("type", 1)),
            script=data.get("script") or [],
            config=data.get("config") or {},
            description=data.get("description", ""),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(script)
        await db.commit()

    @staticmethod
    async def edit_api_script(db: AsyncSession, data: Dict[str, Any], user_id: int) -> None:
        script_id = int(data["id"])
        await db.execute(
            update(ApiScriptModel)
            .where(
                ApiScriptModel.id == script_id,
                ApiScriptModel.enabled_flag == 1,
                ApiScriptModel.created_by == user_id,
            )
            .values(
                name=data.get("name"),
                type=int(data.get("type", 1)),
                script=data.get("script") or [],
                config=data.get("config") or {},
                description=data.get("description", ""),
                updated_by=user_id,
            )
        )
        await db.commit()

    @staticmethod
    async def delete_api_script(db: AsyncSession, script_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiScriptModel)
            .where(
                ApiScriptModel.id == script_id,
                ApiScriptModel.enabled_flag == 1,
                ApiScriptModel.created_by == user_id,
            )
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def get_api_script_simple_list(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        stmt = select(ApiScriptModel).where(
            ApiScriptModel.enabled_flag == 1,
            ApiScriptModel.created_by == user_id,
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            data.append({"id": r.id, "name": r.name})
        return data

    @staticmethod
    def _jsonpath_value_simple(expr: str, data: Any) -> Tuple[bool, str]:
        """
        简化版本：仅基于单个 data 进行 jsonpath 提取。
        注意：为避免与上方多参数 _jsonpath_value 重名，这里使用 _jsonpath_value_simple。
        """
        try:
            jp = jsonpath_parse(expr)
            matches = [m.value for m in jp.find(data)]
            if not matches:
                return False, "jsonpath 未匹配到结果"
            return True, str(matches[0])
        except Exception as e:
            return False, f"获取断言目标值失败，原因：{str(e)}"

    @staticmethod
    async def _pre_wait_time(wait_time: int) -> Dict[str, Any]:
        try:
            time.sleep(int(wait_time))
            return {"status": 1, "message": f"前置操作-等待时长：{wait_time} 秒 成功"}
        except Exception as e:
            return {"status": 0, "message": f"前置操作-等待时长：{wait_time} 秒 失败，原因是：{str(e)}"}

    @staticmethod
    async def _after_wait_time(wait_time: int) -> Dict[str, Any]:
        try:
            time.sleep(int(wait_time))
            return {"status": 1, "message": f"后置操作-等待时长：{wait_time} 秒 成功"}
        except Exception as e:
            return {"status": 0, "message": f"后置操作-等待时长：{wait_time} 秒 失败，原因是：{str(e)}"}

    @staticmethod
    async def _load_script_env_maps(
        db: AsyncSession, env_id: int, user_id: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """返回 (session_vars, env_vars) 供脚本 ntest 使用。"""
        session_vars: Dict[str, Any] = {}
        env_vars: Dict[str, Any] = {}
        if env_id:
            env_row = (
                await db.execute(
                    select(ApiEnvironmentModel).where(
                        ApiEnvironmentModel.id == env_id,
                        ApiEnvironmentModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            if env_row:
                for i in (env_row.config or []):
                    if isinstance(i, dict) and i.get("name") is not None:
                        env_vars[str(i.get("name"))] = i.get("value")
                for j in (env_row.variable or []):
                    if isinstance(j, dict) and j.get("name") is not None:
                        session_vars[str(j.get("name"))] = j.get("value")
        g_rows = (
            await db.execute(
                select(ApiVariableModel).where(
                    ApiVariableModel.enabled_flag == 1,
                    ApiVariableModel.created_by == user_id,
                )
            )
        ).scalars().all()
        for row in g_rows:
            if row.name and row.name not in session_vars:
                session_vars[str(row.name)] = row.value
        return session_vars, env_vars

    @staticmethod
    async def _apply_exported_vars(
        db: AsyncSession,
        exported: Dict[str, Any],
        env_id: int,
        user_id: int,
        request_ctx: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """将脚本导出的变量写入环境；__request__ 回写到 request_ctx。返回失败信息列表。"""
        errors: List[str] = []
        if not exported:
            return errors
        for key, value in exported.items():
            if key == "__request__":
                if isinstance(value, dict) and isinstance(request_ctx, dict):
                    request_ctx.clear()
                    request_ctx.update(value)
                continue
            set_res = await ApiAutomationService._pre_set_var(
                db,
                {
                    "name": key,
                    "value": value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str),
                    "env_type": 1 if env_id else 2,
                },
                env_id,
                user_id,
            )
            if isinstance(set_res, dict) and set_res.get("status") != 1:
                errors.append(str(set_res.get("message") or f"变量 {key} 写入失败"))
        return errors

    @staticmethod
    async def _op_run_script(
        db: AsyncSession,
        op: Dict[str, Any],
        env_id: int,
        user_id: int,
        *,
        phase: str,
        request_ctx: Optional[Dict[str, Any]] = None,
        response_ctx: Optional[Dict[str, Any]] = None,
        code_override: Optional[str] = None,
        language_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        from .script_runtime import normalize_language, run_script_async

        code = code_override if code_override is not None else str(op.get("code") or "")
        language = normalize_language(language_override or op.get("language") or "python")
        if not str(code).strip():
            return {"status": 0, "message": f"{phase}操作-自定义脚本：代码为空", "type": op.get("type")}

        session_vars, env_vars = await ApiAutomationService._load_script_env_maps(db, env_id, user_id)
        req_snap = dict(request_ctx) if isinstance(request_ctx, dict) else None
        run_res = await run_script_async(
            code,
            language=language,
            session_vars=session_vars,
            env_vars=env_vars,
            request_ctx=req_snap,
            response_ctx=response_ctx,
        )
        if not run_res.success:
            return {
                "status": 0,
                "message": f"{phase}操作-自定义脚本失败：{run_res.error or 'unknown'}",
                "type": op.get("type"),
                "output": run_res.output or "",
                "language": language,
            }
        write_errs = await ApiAutomationService._apply_exported_vars(
            db, run_res.vars or {}, env_id, user_id, request_ctx=request_ctx
        )
        msg = f"{phase}操作-自定义脚本成功（{language}）"
        if write_errs:
            msg = f"{msg}；变量写入告警：{'; '.join(write_errs[:3])}"
        return {
            "status": 1 if not write_errs else 0,
            "message": msg,
            "type": op.get("type"),
            "output": (run_res.output or "")[:500],
            "vars": {k: v for k, v in (run_res.vars or {}).items() if k != "__request__"},
            "language": language,
        }

    @staticmethod
    async def _op_run_script_lib(
        db: AsyncSession,
        op: Dict[str, Any],
        env_id: int,
        user_id: int,
        *,
        phase: str,
        request_ctx: Optional[Dict[str, Any]] = None,
        response_ctx: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from .model import NtestScriptModel
        from .script_runtime import normalize_language

        func_id = op.get("func_id")
        if not func_id:
            return {"status": 0, "message": f"{phase}操作-脚本库：未选择脚本", "type": op.get("type")}
        row = (
            await db.execute(
                select(NtestScriptModel).where(
                    NtestScriptModel.id == int(func_id),
                    NtestScriptModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not row or not (row.code or "").strip():
            return {"status": 0, "message": f"{phase}操作-脚本库：脚本不存在或为空", "type": op.get("type")}

        # 可选参数注入到 session
        params_raw = op.get("func_params") or ""
        extra_prefix = ""
        language = normalize_language(getattr(row, "language", None) or "python")
        if str(params_raw).strip():
            try:
                params_obj = json.loads(params_raw) if isinstance(params_raw, str) else params_raw
            except Exception:
                params_obj = None
            if isinstance(params_obj, dict):
                if language == "javascript":
                    extra_prefix = f"const __params = {json.dumps(params_obj, ensure_ascii=False)};\n"
                else:
                    extra_prefix = f"__params = {json.dumps(params_obj, ensure_ascii=False)}\n"

        result = await ApiAutomationService._op_run_script(
            db,
            op,
            env_id,
            user_id,
            phase=phase,
            request_ctx=request_ctx,
            response_ctx=response_ctx,
            code_override=extra_prefix + (row.code or ""),
            language_override=language,
        )
        if result.get("status") == 1 and op.get("result_var"):
            await ApiAutomationService._pre_set_var(
                db,
                {
                    "name": str(op.get("result_var")),
                    "value": str(result.get("output") or ""),
                    "env_type": 1,
                },
                env_id,
                user_id,
            )
        name = op.get("func_name") or row.name or str(func_id)
        if result.get("status") == 1:
            result["message"] = f"{phase}操作-脚本库「{name}」成功"
        return result

    @staticmethod
    async def _op_run_db(
        db: AsyncSession,
        op: Dict[str, Any],
        env_id: int,
        user_id: int,
        *,
        phase: str,
    ) -> Dict[str, Any]:
        db_id = op.get("db_id")
        sql = str(op.get("sql") or "").strip()
        if not db_id:
            return {"status": 0, "message": f"{phase}操作-数据库：未选择数据库", "type": op.get("type")}
        if not sql:
            return {"status": 0, "message": f"{phase}操作-数据库：SQL 为空", "type": op.get("type")}

        row = (
            await db.execute(
                select(ApiDatabaseModel).where(
                    ApiDatabaseModel.id == int(db_id),
                    ApiDatabaseModel.enabled_flag == 1,
                    ApiDatabaseModel.created_by == user_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {"status": 0, "message": f"{phase}操作-数据库：配置不存在", "type": op.get("type")}

        sql = await ApiAutomationService.handle_var(db, env_id, sql)
        try:
            cfg = row.config or {}
            host = cfg.get("host") or row.host
            user = cfg.get("user") or row.username
            password = cfg.get("password") or row.password
            database = cfg.get("database") or row.database_name
            port = int(cfg.get("port") or row.port or 3306)
            conn = pymysql.connect(host=host, user=user, passwd=password, db=database, port=port)
            cur = conn.cursor()
            cur.execute(sql)
            rows_data: Any
            if cur.description:
                cols = [c[0] for c in cur.description]
                fetched = cur.fetchall()
                rows_data = [dict(zip(cols, r)) for r in fetched]
            else:
                rows_data = {"affected": cur.rowcount}
                conn.commit()
            cur.close()
            conn.close()
            result_var = str(op.get("result_var") or "").strip()
            if result_var:
                val = json.dumps(rows_data, ensure_ascii=False, default=str)
                await ApiAutomationService._pre_set_var(
                    db, {"name": result_var, "value": val, "env_type": 1}, env_id, user_id
                )
            return {
                "status": 1,
                "message": f"{phase}操作-数据库执行成功",
                "type": op.get("type"),
                "data": rows_data if not isinstance(rows_data, list) or len(rows_data) <= 20 else rows_data[:20],
            }
        except Exception as e:
            return {"status": 0, "message": f"{phase}操作-数据库失败：{str(e)}", "type": op.get("type")}

    @staticmethod
    async def _op_import_api(
        db: AsyncSession,
        op: Dict[str, Any],
        env_id: int,
        user_id: int,
        *,
        phase: str,
    ) -> Dict[str, Any]:
        """引入接口。
        """
        raw = op.get("api_id")
        menu_id = 0
        if isinstance(raw, list) and raw:
            try:
                menu_id = int(raw[-1])
            except Exception:
                menu_id = 0
        elif raw is not None and str(raw).strip() != "":
            try:
                menu_id = int(raw)
            except Exception:
                menu_id = 0

        if not menu_id:
            return {
                "status": 0,
                "message": f"{phase}操作-引入接口：未选择接口",
                "content": [],
                "type": op.get("type"),
            }

        menu_row = (
            await db.execute(
                select(ApiMenuModel).where(
                    ApiMenuModel.id == menu_id,
                    ApiMenuModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not menu_row:
            return {
                "status": 0,
                "message": f"{phase}操作-引入接口：所选菜单不存在（id={menu_id}）",
                "content": [],
                "type": op.get("type"),
            }
        # type: 1=目录 2=接口 3=用例；引入接口应允许 2/3
        if int(menu_row.type or 0) not in (2, 3):
            return {
                "status": 0,
                "message": f"{phase}操作-引入接口：请选择接口或用例，不能选择目录",
                "content": [],
                "type": op.get("type"),
            }
        if not menu_row.api_id:
            return {
                "status": 0,
                "message": f"{phase}操作-引入接口：所选菜单未关联接口定义",
                "content": [],
                "type": op.get("type"),
            }

        api_row = (
            await db.execute(
                select(ApiModel).where(
                    ApiModel.id == int(menu_row.api_id),
                    ApiModel.enabled_flag == 1,
                )
            )
        ).scalar_one_or_none()
        if not api_row:
            return {
                "status": 0,
                "message": f"{phase}操作-引入接口：接口不存在（api_id={menu_row.api_id}）",
                "content": [],
                "type": op.get("type"),
            }
        res = await ApiAutomationService._pre_request_api(
            db=db,
            api=api_row,
            env_id=int(op.get("env_id") or env_id),
            user_id=user_id,
        )
        res["type"] = op.get("type")
        if res.get("status") is None and res.get("code") is not None:
            # _pre_request_api 返回的是请求结果结构，补齐操作结果字段
            code = int(res.get("code") or 0)
            res["status"] = 1 if 200 <= code < 400 else 0
            res["message"] = f"{phase}操作-引入接口「{api_row.name or menu_row.name}」完成（HTTP {code}）"
        elif not res.get("message"):
            res["message"] = f"{phase}操作-引入接口「{api_row.name or menu_row.name}」完成"
            res.setdefault("status", 1)
        return res

    @staticmethod
    def _map_apifox_processors(processors: Any, *, phase: str = "before") -> List[Dict[str, Any]]:
        """将 Apifox转为平台操作。"""
        from .script_runtime import normalize_language

        ops: List[Dict[str, Any]] = []
        for p in processors or []:
            if not isinstance(p, dict):
                continue
            t = str(p.get("type") or "").strip()
            if t in ("inheritProcessors", ""):
                continue
            data = p.get("data") if isinstance(p.get("data"), dict) else {}
            if t in ("customScript", "script"):
                code = str(data.get("script") or data.get("code") or "")
                if not code.strip():
                    continue
                lang = normalize_language(data.get("language") or "javascript")
                if phase == "before":
                    ops.append({"type": 4, "code": code, "language": lang})
                else:
                    ops.append({"type": 5, "code": code, "language": lang})
            elif t == "wait":
                wait_raw = data.get("waitTime") or data.get("duration") or data.get("time") or 1
                try:
                    wait_num = float(wait_raw)
                except Exception:
                    wait_num = 1
                # Apifox 常见毫秒；>=100 视为毫秒
                wait_s = int(wait_num / 1000) if wait_num >= 100 else int(wait_num)
                wait_s = max(wait_s, 0)
                if phase == "before":
                    ops.append({"type": 3, "wait_time": wait_s or 1})
                else:
                    ops.append({"type": 2, "wait_time": wait_s or 1})
        return ops

    @staticmethod
    def _resolve_apifox_processors(own: Any, inherited: Optional[List[Any]] = None) -> List[Any]:
        inherited = list(inherited or [])
        if not isinstance(own, list) or not own:
            return inherited
        resolved: List[Any] = []
        for p in own:
            if not isinstance(p, dict):
                continue
            if str(p.get("type") or "") == "inheritProcessors":
                resolved.extend(inherited)
            else:
                resolved.append(p)
        return resolved
  
    @staticmethod
    async def _pre_set_var(db: AsyncSession, data: Dict[str, Any], env_id: int, user_id: int) -> Dict[str, Any]:
        """
        前置操作-设置变量：
        - env_type 1: 环境变量 ApiEnvironmentModel.variable
        - env_type 2: 全局变量 ApiVariableModel
        """
        try:
            env_type = int(data.get("env_type") or 1)
            name = data.get("name", "")
            value = data.get("value", "")
            message = ""
            if env_type == 1:
                if not env_id:
                    return {"status": 0, "message": f"前置操作-设置环境变量：{name} 失败，原因：未选择环境"}
                # 与 _complete_var / _load_script_env_maps 一致：按 env_id 读写，不限制创建人
                env_row = (
                    await db.execute(
                        select(ApiEnvironmentModel).where(
                            ApiEnvironmentModel.id == env_id,
                            ApiEnvironmentModel.enabled_flag == 1,
                        )
                    )
                ).scalar_one_or_none()
                if not env_row:
                    return {"status": 0, "message": f"前置操作-设置环境变量：{name} 失败，原因：环境不存在"}
                vars_list = list(env_row.variable or [])
                found = False
                for item in vars_list:
                    if isinstance(item, dict) and ApiAutomationService._normalize_var_name(item.get("name")) == ApiAutomationService._normalize_var_name(name):
                        item["value"] = value
                        found = True
                        break
                if not found:
                    vars_list.append({"name": name, "value": value})
                await db.execute(
                    update(ApiEnvironmentModel)
                    .where(
                        ApiEnvironmentModel.id == env_row.id,
                        ApiEnvironmentModel.enabled_flag == 1,
                    )
                    .values(variable=vars_list, updated_by=user_id)
                )
                message = f"前置操作-设置环境变量：{name} 成功"
            else:
                # env_type == 2, 全局变量
                row = (
                    await db.execute(
                        select(ApiVariableModel).where(
                            ApiVariableModel.enabled_flag == 1,
                            ApiVariableModel.name == name,
                            ApiVariableModel.created_by == user_id,
                        )
                    )
                ).scalar_one_or_none()
                if row:
                    await db.execute(
                        update(ApiVariableModel)
                        .where(
                            ApiVariableModel.id == row.id,
                            ApiVariableModel.enabled_flag == 1,
                        )
                        .values(value=str(value), updated_by=user_id)
                    )
                else:
                    db.add(
                        ApiVariableModel(
                            name=name,
                            value=str(value),
                            created_by=user_id,
                            updated_by=user_id,
                        )
                    )
                message = f"前置操作-设置全局变量：{name} 成功"
            await db.commit()
            return {"status": 1, "message": message}
        except Exception as e:
            return {"status": 0, "message": f"前置操作-设置变量：{data.get('name')} 失败，原因：{str(e)}"}

    @staticmethod
    async def _pre_request(
        db: AsyncSession,
        ops: List[Dict[str, Any]],
        env_id: int,
        user_id: int,
        request_ctx: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        pre_request：
        - type=1: 预请求接口
        - type=2: 设置变量
        - type=3: 等待
        - type=4: 自定义脚本（python/javascript，支持 ntest/pm）
        - type=5: 数据库操作
        - type=6: 脚本库
        """
        results: List[Dict[str, Any]] = []
        for op in ops or []:
            try:
                t = int(op.get("type") or 0)
                if t == 1:
                    results.append(
                        await ApiAutomationService._op_import_api(
                            db, op, env_id, user_id, phase="前置"
                        )
                    )
                elif t == 2:
                    r = await ApiAutomationService._pre_set_var(db, op, env_id, user_id)
                    r["type"] = t
                    results.append(r)
                elif t == 3:
                    r = await ApiAutomationService._pre_wait_time(int(op.get("wait_time") or 0))
                    r["type"] = t
                    results.append(r)
                elif t == 4:
                    results.append(
                        await ApiAutomationService._op_run_script(
                            db, op, env_id, user_id, phase="前置", request_ctx=request_ctx
                        )
                    )
                elif t == 5:
                    results.append(
                        await ApiAutomationService._op_run_db(
                            db, op, env_id, user_id, phase="前置"
                        )
                    )
                elif t == 6:
                    results.append(
                        await ApiAutomationService._op_run_script_lib(
                            db, op, env_id, user_id, phase="前置", request_ctx=request_ctx
                        )
                    )
                else:
                    results.append({"status": 0, "message": f"未知前置操作类型：{t}", "type": t})
            except Exception as e:
                results.append({"status": 0, "message": f"前置操作执行失败，原因：{str(e)}"})
        return results

    @staticmethod
    async def _pre_request_api(db: AsyncSession, api: ApiModel, env_id: int, user_id: int) -> Dict[str, Any]:
        """
        pre_request_api：
        - 不执行 before
        - 执行主请求 + after + assert
        - before 固定为空
        """
        url = await ApiAutomationService.handle_var(db, env_id, api.url or "")
        api_req = dict(api.req or {}) if isinstance(api.req, dict) else {}
        common = await ApiAutomationService._load_common_params_by_api(
            db, api_id=getattr(api, "id", None), api_service_id=getattr(api, "api_service_id", None)
        )
        api_req = ApiAutomationService.apply_common_params_to_req(api_req, common)

        body_payload = await ApiAutomationService.handle_var(db, env_id, api_req.get("body") or {})
        method = int(api_req.get("method") or 2)
        body_type = int(api_req.get("body_type") or 2)
        headers = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("header")))
        params = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("params")))
        form_data = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("form_data")))
        form_urlencoded = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("form_urlencoded")))
        file_paths = api_req.get("file_path") or []
        config = api_req.get("config") or {"retry": 0, "req_timeout": 5, "res_timeout": 5}

        headers, params, req_auth = await ApiAutomationService.apply_request_auth(
            db, env_id, api_req, headers=headers, params=params
        )

        res = await ApiAutomationService._send_request(
            method=method,
            url=str(url),
            headers=headers,
            params=params,
            body_type=body_type,
            body=body_payload,
            form_data=form_data,
            form_urlencoded=form_urlencoded,
            file_paths=file_paths,
            config=config,
            auth=req_auth,
        )

        after_list: List[Dict[str, Any]] = []
        if api_req.get("after"):
            after_list = await ApiAutomationService._after_request(
                db=db,
                ops=api_req.get("after") or [],
                res=res,
                header=headers,
                body=body_payload,
                env_id=env_id,
                user_id=user_id,
            )

        assert_list: List[Dict[str, Any]] = []
        if api_req.get("assert"):
            assert_list = await ApiAutomationService._handle_assert(
                db=db,
                ops=api_req.get("assert") or [],
                res=res,
                header=headers,
                body=body_payload,
                user_id=user_id,
                env_id=env_id,
            )

        res["before"] = []
        res["after"] = after_list
        res["assert"] = assert_list
        res["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if int(res.get("code") or 0) == 200:
            return {"status": 1, "message": f"前置操作-预请求接口：{url} 成功", "content": res, "type": 1}
        return {"status": 0, "message": f"前置操作-预请求接口：{url} 失败", "content": res, "type": 1}

    @staticmethod
    async def _after_set_var(
        db: AsyncSession,
        data: Dict[str, Any],
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
        env_id: int,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        后置操作-提取变量，after_set_var：
        - 使用 jsonpath 提取值并写入环境变量或全局变量
        """
        try:
            ok, value = ApiAutomationService._jsonpath_value_advanced(data, res, header, body)
            if not ok:
                return {
                    "status": 0,
                    "message": f"后置操作-提取目标值失败，原因是：{value}",
                }

            env_type = int(data.get("env_type") or 1)
            target_name = data.get("value", "")

            if env_type == 1:
                if not env_id:
                    return {
                        "status": 0,
                        "message": f"后置操作-提取目标值：{data.get('name')} 失败，原因是：未选择环境",
                    }
                # 与读取路径一致：按 env_id 写入，不限制环境创建人
                env_row = (
                    await db.execute(
                        select(ApiEnvironmentModel).where(
                            ApiEnvironmentModel.id == env_id,
                            ApiEnvironmentModel.enabled_flag == 1,
                        )
                    )
                ).scalar_one_or_none()
                if not env_row:
                    return {
                        "status": 0,
                        "message": f"后置操作-提取目标值：{data.get('name')} 失败，原因是：环境不存在",
                    }
                vars_list = list(env_row.variable or [])
                found = False
                for item in vars_list:
                    if isinstance(item, dict) and ApiAutomationService._normalize_var_name(item.get("name")) == ApiAutomationService._normalize_var_name(target_name):
                        item["value"] = value
                        found = True
                        break
                if not found:
                    vars_list.append({"name": target_name, "value": value})
                await db.execute(
                    update(ApiEnvironmentModel)
                    .where(
                        ApiEnvironmentModel.id == env_row.id,
                        ApiEnvironmentModel.enabled_flag == 1,
                    )
                    .values(variable=vars_list, updated_by=user_id)
                )
            else:
                row = (
                    await db.execute(
                        select(ApiVariableModel).where(
                            ApiVariableModel.enabled_flag == 1,
                            ApiVariableModel.name == target_name,
                            ApiVariableModel.created_by == user_id,
                        )
                    )
                ).scalar_one_or_none()
                if row:
                    await db.execute(
                        update(ApiVariableModel)
                        .where(ApiVariableModel.id == row.id, ApiVariableModel.enabled_flag == 1)
                        .values(value=str(value), updated_by=user_id)
                    )
                else:
                    db.add(
                        ApiVariableModel(
                            name=target_name,
                            value=str(value),
                            created_by=user_id,
                            updated_by=user_id,
                        )
                    )
            await db.commit()
            return {
                "status": 1,
                "message": f"后置操作-提取目标值：{data.get('name')}={value} ，赋值给 {target_name} 成功",
            }
        except Exception as e:
            return {
                "status": 0,
                "message": f"后置操作-设置变量：{data.get('name')} 失败，原因：{str(e)}",
            }

    @staticmethod
    async def _after_request(
        db: AsyncSession,
        ops: List[Dict[str, Any]],
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
        env_id: int,
        user_id: int,
        request_ctx: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        after_request：
        - type=1: 提取变量
        - type=2: 等待
        - type=3: 断言
        - type=4: 数据库操作
        - type=5: 自定义脚本
        - type=6: 脚本库
        - type=7: 引入接口
        """
        results: List[Dict[str, Any]] = []
        response_ctx = {
            "code": res.get("code"),
            "body": res.get("body"),
            "header": res.get("header") or {},
            "res_time": res.get("res_time"),
        }
        for op in ops or []:
            try:
                t = int(op.get("type") or 0)
                if t == 1:
                    results.append(
                        await ApiAutomationService._after_set_var(
                            db, op, res, header, body, env_id, user_id
                        )
                    )
                elif t == 2:
                    results.append(
                        await ApiAutomationService._after_wait_time(int(op.get("wait_time") or 0))
                    )
                elif t == 3:
                    # 断言：复用 assert 处理
                    assert_op = {
                        "type": 1,
                        "assert_name": op.get("assert_name") or "后置断言",
                        "rules": op.get("rules") or [],
                        "name": op.get("name"),
                        "res_type": op.get("res_type"),
                        "value": op.get("value"),
                    }
                    ar = await ApiAutomationService._handle_assert(
                        db=db,
                        ops=[assert_op],
                        res=res,
                        header=header,
                        body=body,
                        user_id=user_id,
                        env_id=env_id,
                        request_ctx=request_ctx,
                    )
                    item = ar[0] if ar else {"status": 0, "message": "断言执行失败"}
                    item["type"] = t
                    results.append(item)
                elif t == 4:
                    results.append(
                        await ApiAutomationService._op_run_db(
                            db, op, env_id, user_id, phase="后置"
                        )
                    )
                elif t == 5:
                    results.append(
                        await ApiAutomationService._op_run_script(
                            db,
                            op,
                            env_id,
                            user_id,
                            phase="后置",
                            request_ctx=request_ctx,
                            response_ctx=response_ctx,
                        )
                    )
                elif t == 6:
                    results.append(
                        await ApiAutomationService._op_run_script_lib(
                            db,
                            op,
                            env_id,
                            user_id,
                            phase="后置",
                            request_ctx=request_ctx,
                            response_ctx=response_ctx,
                        )
                    )
                elif t == 7:
                    results.append(
                        await ApiAutomationService._op_import_api(
                            db, op, env_id, user_id, phase="后置"
                        )
                    )
                else:
                    results.append({"status": 0, "message": f"未知后置操作类型：{t}"})
            except Exception as e:
                results.append({"status": 0, "message": f"后置操作执行失败，原因：{str(e)}"})
        return results

    @staticmethod
    async def _res_assert(rule: Dict[str, Any], res: Dict[str, Any], header: Dict[str, Any], body: Any) -> Dict[str, Any]:
        """
        res_assert：支持新版 AssertEditor 格式（rules 数组）和旧版格式。

        新版格式（AssertEditor）：
          rule = {
            "rules": [
              {"target": "response_json", "path": "$.code", "comparator": "eq", "expect": "200"},
              ...
            ]
          }

        旧版格式：
          rule = {"name": "$.code", "res_type": 1, "value": "200"}
        """
        # ---- 新版格式：rules 数组 ----
        rules = rule.get("rules")
        if isinstance(rules, list):
            results = []
            all_pass = True
            for r in rules:
                result = await ApiAutomationService._eval_assert_rule(r, res, header, body)
                results.append(result)
                if not result.get("pass"):
                    all_pass = False
            return {
                "status": 1 if all_pass else 0,
                "message": "断言全部通过" if all_pass else "断言存在失败项",
                "details": results,
            }

        # ---- 旧版格式：单条 eq 断言 ----
        try:
            ok, actual = ApiAutomationService._jsonpath_value_advanced(rule, res, header, body)
            expect = str(rule.get("value", ""))
            name = rule.get("name", "")
            if not ok:
                return {
                    "status": 0,
                    "message": f"断言 {name} = {expect} 失败，原因是：{actual}",
                }
            if expect == actual:
                return {
                    "status": 1,
                    "message": f"断言 {name} = {expect} 成功",
                }
            return {
                "status": 0,
                "message": f"断言 {name} = {expect} 失败，实际值为：{actual}",
            }
        except Exception as e:
            return {
                "status": 0,
                "message": f"断言 {rule.get('name')} = {rule.get('value')} 失败，原因：{str(e)}",
            }

    @staticmethod
    def _extract_assert_target(target: str, path: str, res: Dict[str, Any], header: Dict[str, Any], body: Any) -> Tuple[bool, Any]:
        """
        根据 target 和 path 提取断言目标值。
        返回 (success, value)
        """
        import re as _re
        try:
            if target == "response_json":
                if not path:
                    return True, body
                from jsonpath_ng import parse as jp_parse
                matches = [m.value for m in jp_parse(path).find(body or {})]
                if not matches:
                    return False, f"JSONPath '{path}' 未匹配到结果"
                return True, matches[0]

            elif target == "response_text":
                raw = res.get("raw") or res.get("text") or ""
                if isinstance(body, (dict, list)):
                    import json as _json
                    raw = _json.dumps(body, ensure_ascii=False)
                return True, str(raw)

            elif target == "response_xml":
                raw = res.get("raw") or res.get("text") or ""
                if not path:
                    return True, raw
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(raw)
                    found = root.findall(path)
                    if not found:
                        return False, f"XPath '{path}' 未匹配到结果"
                    return True, found[0].text or ""
                except Exception as xe:
                    return False, f"XML 解析失败：{xe}"

            elif target == "response_header":
                if not path:
                    return True, header
                val = header.get(path) or header.get(path.lower()) or header.get(path.upper())
                if val is None:
                    return False, f"响应头 '{path}' 不存在"
                return True, str(val)

            elif target == "response_cookie":
                cookies = res.get("cookies") or {}
                if isinstance(cookies, list):
                    cookies = {c.get("name", ""): c.get("value", "") for c in cookies}
                if not path:
                    return True, cookies
                val = cookies.get(path)
                if val is None:
                    return False, f"Cookie '{path}' 不存在"
                return True, str(val)

            elif target == "http_code":
                return True, res.get("code") or res.get("status_code") or 0

            elif target == "response_time":
                return True, res.get("res_time") or res.get("response_time") or 0

            elif target in ("env_var", "global_var"):
                # Variables are resolved before execution; here we just return the path as-is
                # In practice the variable should already be substituted
                return True, path

            else:
                return False, f"未知断言目标：{target}"

        except Exception as e:
            return False, f"提取断言目标值失败：{e}"

    @staticmethod
    def _compare_assert(actual: Any, comparator: str, expect: str) -> Tuple[bool, str]:
        """执行比较，返回 (pass, message)"""
        import re as _re

        # Comparators that don't need expect value
        if comparator == "exists":
            return True, f"值存在：{actual}"
        if comparator == "not_exists":
            return False, f"值存在但期望不存在：{actual}"
        if comparator == "is_empty":
            ok = actual is None or str(actual).strip() == ""
            return ok, ("值为空，断言通过" if ok else f"值不为空：{actual}")
        if comparator == "not_empty":
            ok = actual is not None and str(actual).strip() != ""
            return ok, ("值不为空，断言通过" if ok else "值为空，断言失败")

        # Convert for numeric comparisons
        actual_str = str(actual) if actual is not None else ""

        if comparator == "eq":
            ok = actual_str == expect
            return ok, (f"等于 {expect}，通过" if ok else f"期望 {expect}，实际 {actual_str}")
        if comparator == "ne":
            ok = actual_str != expect
            return ok, (f"不等于 {expect}，通过" if ok else f"期望不等于 {expect}，但实际相等")
        if comparator in ("gt", "gte", "lt", "lte"):
            try:
                a_num = float(actual_str)
                e_num = float(expect)
                if comparator == "gt":
                    ok = a_num > e_num
                elif comparator == "gte":
                    ok = a_num >= e_num
                elif comparator == "lt":
                    ok = a_num < e_num
                else:
                    ok = a_num <= e_num
                op_map = {"gt": ">", "gte": ">=", "lt": "<", "lte": "<="}
                return ok, (f"{actual_str} {op_map[comparator]} {expect}，通过" if ok else f"{actual_str} 不满足 {op_map[comparator]} {expect}")
            except ValueError:
                return False, f"数值比较失败：{actual_str} 或 {expect} 不是有效数字"
        if comparator == "contains":
            ok = expect in actual_str
            return ok, (f"包含 '{expect}'，通过" if ok else f"不包含 '{expect}'，实际：{actual_str}")
        if comparator == "not_contains":
            ok = expect not in actual_str
            return ok, (f"不包含 '{expect}'，通过" if ok else f"包含了 '{expect}'，实际：{actual_str}")
        if comparator == "startswith":
            ok = actual_str.startswith(expect)
            return ok, (f"以 '{expect}' 开头，通过" if ok else f"不以 '{expect}' 开头，实际：{actual_str}")
        if comparator == "endswith":
            ok = actual_str.endswith(expect)
            return ok, (f"以 '{expect}' 结尾，通过" if ok else f"不以 '{expect}' 结尾，实际：{actual_str}")
        if comparator == "regex":
            try:
                ok = bool(_re.search(expect, actual_str))
                return ok, (f"正则 '{expect}' 匹配，通过" if ok else f"正则 '{expect}' 不匹配，实际：{actual_str}")
            except _re.error as re_err:
                return False, f"正则表达式错误：{re_err}"

        return False, f"未知比较符：{comparator}"

    @staticmethod
    async def _eval_assert_rule(rule: Dict[str, Any], res: Dict[str, Any], header: Dict[str, Any], body: Any) -> Dict[str, Any]:
        """
        执行单条 AssertEditor 规则。
        rule = {"target": str, "path": str, "comparator": str, "expect": str}
        """
        target = rule.get("target", "response_json")
        path = rule.get("path", "")
        comparator = rule.get("comparator", "eq")
        expect = str(rule.get("expect", ""))

        # For exists/not_exists, check if extraction succeeds
        if comparator == "not_exists":
            ok, _ = ApiAutomationService._extract_assert_target(target, path, res, header, body)
            passed = not ok
            return {
                "pass": passed,
                "target": target,
                "path": path,
                "comparator": comparator,
                "expect": expect,
                "actual": None,
                "message": "值不存在，通过" if passed else f"值存在但期望不存在",
            }

        ok, actual = ApiAutomationService._extract_assert_target(target, path, res, header, body)
        if not ok:
            if comparator == "exists":
                return {
                    "pass": False,
                    "target": target, "path": path, "comparator": comparator,
                    "expect": expect, "actual": None,
                    "message": f"值不存在：{actual}",
                }
            return {
                "pass": False,
                "target": target, "path": path, "comparator": comparator,
                "expect": expect, "actual": None,
                "message": f"提取失败：{actual}",
            }

        passed, msg = ApiAutomationService._compare_assert(actual, comparator, expect)
        return {
            "pass": passed,
            "target": target,
            "path": path,
            "comparator": comparator,
            "expect": expect,
            "actual": str(actual) if actual is not None else None,
            "message": msg,
        }

    @staticmethod
    async def _local_db_execute(db_model: ApiDatabaseModel, table: str, where: str) -> Any:
        """直连数据库查询，local_db_execute。"""
        try:
            cfg = db_model.config or {}
            host = cfg.get("host") or db_model.host
            user = cfg.get("user") or db_model.username
            password = cfg.get("password") or db_model.password
            database = cfg.get("database") or db_model.database_name
            port = int(cfg.get("port") or db_model.port or 3306)
            conn = pymysql.connect(host=host, user=user, passwd=password, db=database, port=port)
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table} where {where} limit 1")
            result = [dict(zip([column[0] for column in cur.description], row)) for row in cur.fetchall()]
            cur.close()
            conn.close()
            return result[0] if result else {}
        except Exception as e:
            return f"查询数据库失败，原因是：{str(e)}"

    @staticmethod
    async def test_db_connection(db: AsyncSession, db_id: int, user_id: int) -> Dict[str, Any]:
        """
        测试直连数据库连接是否可用。
        逻辑与 _local_db_execute 获取连接配置的方式一致，只做一次简单连接 + ping。
        """
        row = (
            await db.execute(
                select(ApiDatabaseModel).where(
                    ApiDatabaseModel.id == db_id,
                    ApiDatabaseModel.enabled_flag == 1,
                    ApiDatabaseModel.created_by == user_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {"success": False, "message": "数据库配置不存在或已被删除"}

        cfg = row.config or {}
        host = cfg.get("host") or row.host
        user = cfg.get("user") or row.username
        password = cfg.get("password") or row.password
        database = cfg.get("database") or row.database_name
        port = int(cfg.get("port") or row.port or 3306)

        try:
            conn = pymysql.connect(host=host, user=user, passwd=password, db=database, port=port)
            conn.ping(reconnect=True)
            conn.close()
            return {"success": True, "message": "数据库连接成功"}
        except Exception as e:
            return {"success": False, "message": f"数据库连接失败：{str(e)}"}

    @staticmethod
    async def _db_result_assert(rule: Dict[str, Any], actual: str) -> Dict[str, Any]:
        """
        db_result_assert：
        - rule['assert_value'] 为数据库字段值（字符串）
        - actual 为被测值（从响应/请求/常量提取）
        """
        expect = str(rule.get("assert_value", ""))
        name = str(rule.get("name", ""))
        value_expr = str(rule.get("value", ""))
        if expect == actual:
            return {"status": 1, "message": f"断言 {name} = {value_expr} 成功"}
        return {
            "status": 0,
            "message": f"断言 {name} = {value_expr} 失败，实际值为：{name}={expect}, {value_expr}={actual}",
        }

    @staticmethod
    async def _db_assert(rule: Dict[str, Any], res: Dict[str, Any], header: Dict[str, Any], body: Any, row: Dict[str, Any]) -> Dict[str, Any]:
        """db_assert：从响应/请求中取值，与数据库结果字段比较。"""
        try:
            t = int(rule.get("type") or 1)
            if t == 5:
                ok, actual = True, str(rule.get("value", ""))
            else:
                ok, actual = ApiAutomationService._jsonpath_value(
                    res_type=t,
                    expr=str(rule.get("value") or ""),
                    res=res,
                    header=header,
                    body=body,
                )
            if not ok:
                return {"status": 0, "message": actual}
            rule = dict(rule)
            rule["assert_value"] = str(row.get(str(rule.get("name", "")), ""))
            return await ApiAutomationService._db_result_assert(rule, str(actual))
        except Exception as e:
            return {
                "status": 0,
                "message": f"获取断言目标值失败，原因：{str(e)}",
            }

    @staticmethod
    async def _local_db_assert(
        db: AsyncSession,
        rule: Dict[str, Any],
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
        user_id: int,
    ) -> List[Dict[str, Any]]:
        """
        直连数据库断言，local_db_assert：
        rule 中包含:
        - local_db: 数据库配置ID
        - local_db_table/local_db_where
        - local_db_assert: 断言列表
        """
        try:
            db_id = int(rule.get("local_db") or 0)
            row_model = (
                await db.execute(
                    select(ApiDatabaseModel).where(
                        ApiDatabaseModel.id == db_id,
                        ApiDatabaseModel.enabled_flag == 1,
                        ApiDatabaseModel.created_by == user_id,
                    )
                )
            ).scalar_one_or_none()
            if not row_model:
                return [{"status": 0, "message": "直连-数据库配置不存在"}]
            table = str(rule.get("local_db_table") or "")
            where = str(rule.get("local_db_where") or "1=1")
            db_row = await ApiAutomationService._local_db_execute(row_model, table, where)
            if isinstance(db_row, str):
                return [{"status": 0, "message": db_row}]
            result: List[Dict[str, Any]] = []
            for item in rule.get("local_db_assert") or []:
                r = await ApiAutomationService._db_assert(item, res, header, body, db_row)
                result.append(r)
            return result
        except Exception as e:
            return [{"status": 0, "message": f"直连-数据库断言操作执行失败，原因：{str(e)}"}]

    @staticmethod
    async def _handle_assert(
        db: AsyncSession,
        ops: List[Dict[str, Any]],
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
        user_id: int,
        env_id: int = 0,
        request_ctx: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        handle_assert：
        - type=1: 响应结果断言（支持新版 rules 数组格式 和 旧版格式）
        - type=4: 直连数据库断言
        - type=5: 自定义断言（Python / JavaScript 脚本）
        """
        from .script_runtime import normalize_language, run_script_async

        results: List[Dict[str, Any]] = []
        response_ctx = {
            "code": res.get("code") or res.get("status_code") or 0,
            "body": res.get("body") if res.get("body") is not None else body,
            "header": res.get("header") or header or {},
            "res_time": res.get("res_time") or 0,
        }
        for op in ops or []:
            try:
                t = int(op.get("type") or 0)
                if t == 1:
                    r = await ApiAutomationService._res_assert(op, res, header, body)
                    r["type"] = t
                    results.append(r)
                elif t == 4:
                    r = {
                        "status": 1,
                        "message": "直连-数据库断言-全部成功",
                        "content": [],
                        "type": t,
                    }
                    content = await ApiAutomationService._local_db_assert(db, op, res, header, body, user_id)
                    r["content"] = content
                    for item in content:
                        if not item.get("status"):
                            r["status"] = 0
                            r["message"] = "直连-数据库断言执行完成，断言出现错误"
                            break
                    results.append(r)
                elif t == 5:
                    script = op.get("custom_script") or op.get("code") or ""
                    language = normalize_language(op.get("language") or "python")
                    name = str(op.get("custom_name") or "").strip()
                    label = f"自定义断言{('：' + name) if name else ''}"
                    if not str(script).strip():
                        results.append({"status": 1, "message": f"{label}：脚本为空，跳过", "type": t, "language": language})
                        continue
                    try:
                        session_vars, env_vars = await ApiAutomationService._load_script_env_maps(
                            db, int(env_id or 0), user_id
                        )
                        run_res = await run_script_async(
                            str(script),
                            language=language,
                            session_vars=session_vars,
                            env_vars=env_vars,
                            request_ctx=request_ctx if isinstance(request_ctx, dict) else None,
                            response_ctx=response_ctx,
                            extra_globals={
                                # 兼容旧版自定义断言注入
                                "status_code": response_ctx.get("code") or 0,
                                "headers": response_ctx.get("header") or {},
                                "res_time": response_ctx.get("res_time") or 0,
                                "body": response_ctx.get("body"),
                            },
                        )
                        if run_res.success:
                            write_errs = await ApiAutomationService._apply_exported_vars(
                                db, run_res.vars or {}, int(env_id or 0), user_id, request_ctx=request_ctx
                            )
                            msg = f"{label}：执行通过（{language}）"
                            if write_errs:
                                msg = f"{msg}；变量写入告警：{'; '.join(write_errs[:3])}"
                            results.append({
                                "status": 1 if not write_errs else 0,
                                "message": msg,
                                "type": t,
                                "language": language,
                                "output": (run_res.output or "")[:500],
                            })
                        else:
                            err = str(run_res.error or "unknown")
                            is_fail = "assert" in err.lower() or "failed" in err.lower() or "AssertionError" in err
                            results.append({
                                "status": 0,
                                "message": (f"{label}失败：{err}" if is_fail else f"{label}脚本执行错误：{err}"),
                                "type": t,
                                "language": language,
                                "output": (run_res.output or "")[:500],
                            })
                    except Exception as se:
                        results.append({
                            "status": 0,
                            "message": f"{label}脚本执行错误：{se}",
                            "type": t,
                            "language": language,
                        })
                else:
                    results.append({"status": 0, "message": f"未知断言类型：{t}", "type": t})
            except Exception as e:
                results.append({"status": 0, "message": f"断言操作执行失败，原因：{str(e)}"})
        return results

    @staticmethod
    def _json_request_kwargs(body: Any, headers: Dict[str, Any]) -> Dict[str, Any]:
        """
        JSON 请求体发送：
        - body 为 str 时按原文 data 发送（与签名脚本 request.raw_body / request.body 一致）
        - body 为对象时走 requests 的 json= 序列化
        """
        hdrs = dict(headers or {})
        if isinstance(body, str):
            if not any(str(k).lower() == "content-type" for k in hdrs.keys()):
                hdrs["Content-Type"] = "application/json; charset=utf-8"
            return {"headers": hdrs, "data": body.encode("utf-8")}
        if body is None:
            if not any(str(k).lower() == "content-type" for k in hdrs.keys()):
                hdrs["Content-Type"] = "application/json; charset=utf-8"
            return {"headers": hdrs, "data": b"{}"}
        return {"headers": hdrs, "json": body}

    @staticmethod
    async def _send_request(method: int, url: str, headers: Dict[str, Any], params: Dict[str, Any], body_type: int, body: Any,
                            form_data: Dict[str, Any], form_urlencoded: Dict[str, Any], file_paths: List[str], config: Dict[str, Any],
                            auth: Any = None) -> Dict[str, Any]:
        timeout = (config.get("req_timeout", 5), config.get("res_timeout", 5))
        ssl_verify = config.get("ssl_verify", True)
        allow_redirects = config.get("allow_redirects", True)
        common = {"timeout": timeout, "verify": ssl_verify, "allow_redirects": allow_redirects, "auth": auth}
        try:
            if method == 1:
                r = requests.get(url, headers=headers, params=params, **common)
            elif method == 2:
                if body_type == 1:
                    r = requests.post(url, headers=headers, params=params, **common)
                elif body_type == 2:
                    jk = ApiAutomationService._json_request_kwargs(body, headers)
                    r = requests.post(url, params=params, **jk, **common)
                elif body_type == 3:
                    r = requests.post(url, headers=headers, params=params, data=form_data, **common)
                elif body_type == 4:
                    r = requests.post(url, headers=headers, params=params, data=form_urlencoded, **common)
                elif body_type == 5:
                    files = []
                    for p in file_paths or []:
                        files.append(("file", (p.split("/")[-1], open(p, "rb"), "application/octet-stream")))
                    r = requests.request("POST", url=url, headers=headers, params=params, files=files, data={}, **common)
                else:
                    jk = ApiAutomationService._json_request_kwargs(body, headers)
                    r = requests.post(url, params=params, **jk, **common)
            elif method == 3:
                jk = ApiAutomationService._json_request_kwargs(body, headers)
                r = requests.put(url, params=params, **jk, **common)
            elif method == 4:
                r = requests.delete(url, headers=headers, params=params, **common)
            elif method == 5:
                jk = ApiAutomationService._json_request_kwargs(body, headers)
                r = requests.patch(url, params=params, **jk, **common)
            elif method == 6:
                r = requests.options(url, headers=headers, params=params, **common)
            else:
                r = requests.request("GET", url=url, headers=headers, params=params, **common)

            try:
                body_json = r.json()
            except Exception:
                body_json = {"raw": r.text}

            # cookies
            cookies_list = [
                {
                    "name": c.name,
                    "value": c.value,
                    "domain": c.domain or "",
                    "path": c.path or "/",
                    "expires": str(c.expires) if c.expires else "",
                    "httpOnly": False,
                    "secure": bool(c._rest.get("Secure")) if hasattr(c, "_rest") else False,
                }
                for c in r.cookies
            ]

            # raw_request — actual request sent by requests
            prep = r.request
            raw_req_headers = dict(prep.headers) if prep and prep.headers else {}
            raw_req_body = ""
            if prep and prep.body:
                try:
                    raw_req_body = prep.body.decode("utf-8") if isinstance(prep.body, bytes) else str(prep.body)
                except Exception:
                    raw_req_body = str(prep.body)

            return {
                "code": r.status_code,
                "res_time": str(round(r.elapsed.total_seconds() * 1000, 2)),
                "body": body_json,
                "header": dict(r.headers),
                "size": str((len(r.text.encode("utf-8")) if r.text else 0) + (len(str(r.headers).encode("utf-8")))),
                "cookies": cookies_list,
                "raw_request": {
                    "method": prep.method if prep else "",
                    "url": prep.url if prep else url,
                    "headers": raw_req_headers,
                    "body": raw_req_body,
                },
            }
        except Exception as e:
            return {
                "code": 500,
                "body": {"msg": "接口请求失败", "exception": str(e)},
                "header": {},
                "size": 0,
                "res_time": 0,
                "cookies": [],
                "raw_request": {"method": "", "url": url, "headers": {}, "body": ""},
            }

    @staticmethod
    async def execute_api_send(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
       输入 body 基本结构
        """
        env_id = int(body.get("env_id") or 0)
        req = body.get("req") or {}
        if not isinstance(req, dict):
            req = {}

        # 服务级全局参数（Header/Cookie/Query/Body），请求侧同名覆盖
        api_id = int(body.get("id") or req.get("id") or 0)
        common = await ApiAutomationService._load_common_params_by_api(db, api_id=api_id or None)
        req = ApiAutomationService.apply_common_params_to_req(req, common)

        # 可被前置脚本改写的请求上下文（含 raw_body，兼容 Apifox/签名脚本）
        _body_for_ctx = req.get("body")
        if isinstance(_body_for_ctx, str):
            _raw_body = _body_for_ctx
        elif _body_for_ctx is None:
            _raw_body = ""
        else:
            try:
                _raw_body = json.dumps(_body_for_ctx, ensure_ascii=False, separators=(",", ":"))
            except Exception:
                _raw_body = str(_body_for_ctx)
        request_ctx: Dict[str, Any] = {
            "url": body.get("url") or req.get("url") or "",
            "method": req.get("method"),
            "header": req.get("header"),
            "params": req.get("params"),
            "body": _body_for_ctx,
            "raw_body": _raw_body,
            "body_type": req.get("body_type"),
            "form_data": req.get("form_data"),
            "form_urlencoded": req.get("form_urlencoded"),
            "file_path": req.get("file_path"),
            "config": req.get("config"),
            "cookies": req.get("cookies"),
        }

        before_ops = req.get("before") or []
        after_ops = req.get("after") or []
        assert_ops = req.get("assert") or []

        before_list: List[Dict[str, Any]] = []
        if before_ops:
            before_list = await ApiAutomationService._pre_request(
                db=db,
                ops=before_ops,
                env_id=env_id,
                user_id=user_id,
                request_ctx=request_ctx,
            )

        # 前置可能改写 request_ctx / 环境变量，回写后再做变量替换
        if request_ctx.get("url") is not None:
            req["url"] = request_ctx.get("url")
        for k in ("header", "params", "body", "body_type", "form_data", "form_urlencoded", "file_path", "config", "method", "cookies"):
            if k in request_ctx and request_ctx.get(k) is not None:
                req[k] = request_ctx.get(k)
        # 脚本改了 body 时同步 raw_body，供排查；发送仍以 body 为准
        if "body" in request_ctx and request_ctx.get("body") is not None:
            b = request_ctx.get("body")
            request_ctx["raw_body"] = b if isinstance(b, str) else json.dumps(b, ensure_ascii=False, default=str)

        raw_url = request_ctx.get("url") or body.get("url") or req.get("url") or ""
        url = await ApiAutomationService.handle_var(db, env_id, raw_url)
        url = str(url or "").strip()
        if "{{" in url and "}}" in url:
            hint = "请先在右上角选择环境，并确认配置项名与 URL 中占位符一致（如配置 base_url 或 {{base_url}}，URL 写 {{base_url}}/...）"
            if not env_id:
                raise ValueError(f"URL 中的环境变量未替换（未选择环境）。{hint} 当前 URL：{url}")
            raise ValueError(f"URL 中的环境变量未替换，请检查环境配置项。{hint} 当前 URL：{url}")
        if url and not re.match(r"^https?://", url, re.I):
            raise ValueError(
                f"URL 缺少协议（http/https），当前为：{url}。"
                "请确认环境配置中的接口前缀（如 https://uapis.cn）已正确替换到 URL。"
            )

        body_payload = await ApiAutomationService.handle_var(db, env_id, req.get("body") or {})
        method = int(req.get("method") or 2)
        body_type = int(req.get("body_type") or 2)
        headers = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("header")))
        params = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("params")))
        form_data = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("form_data")))
        form_urlencoded = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("form_urlencoded")))
        file_paths = req.get("file_path") or []
        config = req.get("config") if isinstance(req.get("config"), dict) else None
        config = config or {"retry": 0, "req_timeout": 5, "res_timeout": 5}

        headers, params, req_auth = await ApiAutomationService.apply_request_auth(
            db, env_id, req, headers=headers, params=params
        )

        res = await ApiAutomationService._send_request(
            method=method,
            url=str(url),
            headers=headers,
            params=params,
            body_type=body_type,
            body=body_payload,
            form_data=form_data,
            form_urlencoded=form_urlencoded,
            file_paths=file_paths,
            config=config,
            auth=req_auth,
        )

        after_list: List[Dict[str, Any]] = []
        if after_ops:
            after_list = await ApiAutomationService._after_request(
                db=db,
                ops=after_ops,
                res=res,
                header=headers,
                body=body_payload,
                env_id=env_id,
                user_id=user_id,
                request_ctx=request_ctx,
            )

        assert_list: List[Dict[str, Any]] = []
        if assert_ops:
            assert_list = await ApiAutomationService._handle_assert(
                db=db,
                ops=assert_ops,
                res=res,
                header=headers,
                body=body_payload,
                user_id=user_id,
                env_id=env_id,
                request_ctx=request_ctx,
            )

        res["before"] = before_list
        res["after"] = after_list
        res["assert"] = assert_list
        res["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # console: collect log lines from before/after/assert results
        console_logs: List[Dict[str, Any]] = []
        for item in before_list:
            level = "info" if item.get("status") == 1 else "error"
            console_logs.append({"level": level, "msg": f"[前置] {item.get('message', '')}"})
        raw_req = res.get("raw_request") or {}
        console_logs.append({
            "level": "info" if int(res.get("code") or 0) < 400 else "error",
            "msg": f"[请求] {raw_req.get('method', '')} {raw_req.get('url', '')} → {res.get('code')} ({res.get('res_time')} ms)",
        })
        for item in after_list:
            level = "info" if item.get("status") == 1 else "error"
            console_logs.append({"level": level, "msg": f"[后置] {item.get('message', '')}"})
        for item in assert_list:
            level = "info" if item.get("status") == 1 else "error"
            console_logs.append({"level": level, "msg": f"[断言] {item.get('message', '')}"})
        res["console"] = console_logs

        db.add(
            ApiResultModel(
                req={
                    "url": url,
                    "body": req.get("body"),
                    "params": req.get("params"),
                    "header": req.get("header"),
                    "form_data": req.get("form_data"),
                    "file_path": file_paths,
                    "form_urlencoded": req.get("form_urlencoded"),
                    "config": config,
                    "body_type": body_type,
                    "method": method,
                    "before": req.get("before") or [],
                    "after": req.get("after") or [],
                    "assert": req.get("assert") or [],
                },
                res=res,
                api_id=int(body.get("id") or 0),
                status_code=int(res.get("code") or 0),
                response_time=float(res.get("res_time") or 0),
                error_message=(res.get("body") or {}).get("exception") if int(res.get("code") or 0) >= 400 else None,
                created_by=user_id,
                updated_by=user_id,
            )
        )
        await db.commit()
        return res

    # -------------------- 用例执行与结果 --------------------
    @staticmethod
    async def _new_uuid() -> str:
        return str(uuid.uuid4())

    @staticmethod
    async def run_api_script(db: AsyncSession, data: Dict[str, Any], user_id: int) -> None:
        """

        请求体关键字段：
        - result_id: 执行批次ID
        - name: 任务名称
        - config: {"env_id": int, ...}
        - run_list: [
            {
              "name": "...",
              "config": {"params_id": ..., ...},
              "script": [
                {"name": "...", "api_id": int, ...},
                ...
              ]
            },
            ...
          ]
        """
        result_id = str(data["result_id"])
        env_id = int(data["config"]["env_id"])
        try:
            # 创建汇总记录
            summary = ApiScriptResultListModel(
                result_id=int(result_id),
                name=data["name"],
                script=[],
                config=data.get("config") or {},
                result={},
                api_service_id=data.get("api_service_id"),
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(summary)
            await db.flush()

            all_pass = 0
            all_fail = 0
            total = 0
            execution_aborted = False

            for case in data.get("run_list", []):
                if ApiAutomationService._is_api_script_result_cancel_requested(result_id):
                    execution_aborted = True
                    break
                case["status"] = 1
                case["pass"] = 0
                case["fail"] = 0
                case_uuid = await ApiAutomationService._new_uuid()
                case["uuid"] = case_uuid

                for step in case.get("script", []):
                    if ApiAutomationService._is_api_script_result_cancel_requested(result_id):
                        execution_aborted = True
                        break

                    total += 1
                    step_uuid = await ApiAutomationService._new_uuid()
                    step["uuid"] = step_uuid

                    await ApiAutomationService._write_log_line(
                        case_uuid, result_id, f"开始执行步骤-{step.get('name')}"
                    )

                    # 使用 StepExecutor 支持多步骤类型
                    from .step_executor import StepExecutor, VariableContext
                    if not hasattr(ApiAutomationService, '_step_ctx_cache'):
                        ApiAutomationService._step_ctx_cache = {}
                    ctx_key = f"{result_id}_{case_uuid}"
                    # step_rely 从 case 配置中读取，默认为 True（步骤间共享变量）
                    step_rely = bool(int(case.get("config", {}).get("step_rely", 1)))
                    if ctx_key not in ApiAutomationService._step_ctx_cache:
                        env_vars = await ApiAutomationService._load_env_vars(db, env_id)
                        ApiAutomationService._step_ctx_cache[ctx_key] = VariableContext(env_vars)
                    ctx = ApiAutomationService._step_ctx_cache[ctx_key]

                    async def _log_fn(msg: str):
                        await ApiAutomationService._write_log_line(case_uuid, result_id, msg)

                    executor = StepExecutor(
                        db=db,
                        env_id=env_id,
                        user_id=user_id,
                        result_id=result_id,
                        ctx=ctx,
                        log_fn=_log_fn,
                        cancel_fn=lambda: ApiAutomationService._is_api_script_result_cancel_requested(result_id),
                        step_rely=step_rely,
                    )

                    step_result = await executor.execute(step)
                    success = step_result.success
                    api_req = step_result.request or {}
                    api_res = step_result.response or {}
                    # 写入日志
                    for log_line in step_result.logs:
                        await ApiAutomationService._write_log_line(case_uuid, result_id, log_line)

                    if success:
                        case["pass"] += 1
                        all_pass += 1
                    else:
                        case["status"] = 0
                        case["fail"] += 1
                        all_fail += 1

                    # 写入步骤详情，供执行监控统计总数/失败数
                    if not api_res and step_result.error:
                        api_res = {
                            "code": 500,
                            "body": {"msg": "步骤执行失败", "exception": step_result.error},
                            "header": {},
                            "size": 0,
                            "res_time": 0,
                        }
                    db.add(
                        ApiScriptResultModel(
                            name=step.get("name") or step_result.name or "",
                            uuid=step_uuid,
                            menu_id=case_uuid,
                            result_id=int(result_id),
                            status=1 if success else 0,
                            req=api_req,
                            res=api_res,
                            created_by=user_id,
                            updated_by=user_id,
                        )
                    )
                    await db.flush()

                    await ApiAutomationService._write_log_line(
                        case_uuid, result_id, f"接口-{step.get('name')}执行完成"
                    )
                    await ApiAutomationService._api_script_delay_seconds(result_id, 3.0)

                if execution_aborted:
                    break

            if execution_aborted:
                base_dir = ApiAutomationService._get_api_result_dir(result_id)
                all_log = base_dir / f"{result_id}.txt"
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ApiAutomationService._append_log_file(all_log, f"{now} 用户已请求停止，执行中断 ")

            percent = round(all_pass / total * 100, 2) if total else 0
            summary.script = data.get("run_list") or []
            summary.result = {
                "total": total,
                "pass": all_pass,
                "fail": all_fail,
                "percent": percent,
                "stopped": execution_aborted,
            }
            summary.end_time = datetime.now()
            await db.flush()

            # 结束标记
            end_row = ApiScriptResultModel(
                name="执行结束",
                uuid="",
                menu_id="",
                result_id=int(result_id),
                status=1,
                req={},
                res={},
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(end_row)
            await db.commit()

            notice_data = {
                "task_name": data.get("name"),
                "result_id": result_id,
                "total": total,
                "passed": all_pass,
                "fail": all_fail,
                "un_run": total - all_pass - all_fail,
                "percent": percent,
            }
            await ApiAutomationService._send_notice(db, 33, "api_report", notice_data, user_id=user_id)
        finally:
            ApiAutomationService._clear_api_script_cancel(result_id)

    # 结果查询 & 日志
    @staticmethod
    async def get_script_result(db: AsyncSession, result_id: int, user_id: int) -> List[Dict[str, Any]]:
        own = (
            await db.execute(
                select(ApiScriptResultListModel.id).where(
                    ApiScriptResultListModel.enabled_flag == 1,
                    ApiScriptResultListModel.result_id == result_id,
                    ApiScriptResultListModel.created_by == user_id,
                ).limit(1)
            )
        ).scalar_one_or_none()
        if own is None:
            return []
        stmt = (
            select(ApiScriptResultModel)
            .where(
                ApiScriptResultModel.enabled_flag == 1,
                ApiScriptResultModel.result_id == result_id,
            )
            .order_by(ApiScriptResultModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

    @staticmethod
    async def get_script_result_list(
        db: AsyncSession,
        user_id: int,
        page: int,
        page_size: int,
        search_name: str = "",
        api_service_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        stmt = select(ApiScriptResultListModel).where(
            ApiScriptResultListModel.enabled_flag == 1,
            ApiScriptResultListModel.created_by == user_id,
        )
        name_kw = (search_name or "").strip()
        if name_kw:
            stmt = stmt.where(ApiScriptResultListModel.name.contains(name_kw))
        if api_service_id:
            stmt = stmt.where(ApiScriptResultListModel.api_service_id == int(api_service_id))
        stmt = stmt.order_by(ApiScriptResultListModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        total = len(rows)
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = rows[start:end]
        user_ids = [int(r.created_by) for r in page_rows if getattr(r, "created_by", None)]
        username_map = await _get_username_map(db, user_ids)
        content: List[Dict[str, Any]] = []
        for r in page_rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            stopped = bool((r.result or {}).get("stopped"))
            d["status"] = 2 if stopped else (0 if r.end_time is None else 1)
            uid = getattr(r, "created_by", None)
            d["username"] = username_map.get(int(uid), "") if uid else ""
            content.append(d)
        return {"content": content, "total": total, "page": page, "pageSize": page_size}

    @staticmethod
    async def stop_api_script_result(db: AsyncSession, result_id: int, user_id: int) -> Dict[str, Any]:
        row = (
            await db.execute(
                select(ApiScriptResultListModel).where(
                    ApiScriptResultListModel.enabled_flag == 1,
                    ApiScriptResultListModel.result_id == result_id,
                    ApiScriptResultListModel.created_by == user_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {"stopped": False, "message": "未找到执行记录"}
        if row.end_time is not None:
            return {"stopped": False, "message": "任务已结束"}
        ApiAutomationService._request_cancel_api_script_result(str(result_id))
        row.result = {**(row.result or {}), "stopped": True}
        await db.flush()
        await db.commit()
        return {"stopped": True, "message": "已请求停止"}

    @staticmethod
    async def delete_api_script_result(db: AsyncSession, result_id: int, user_id: int) -> Dict[str, Any]:
        row = (
            await db.execute(
                select(ApiScriptResultListModel).where(
                    ApiScriptResultListModel.enabled_flag == 1,
                    ApiScriptResultListModel.result_id == result_id,
                    ApiScriptResultListModel.created_by == user_id,
                )
            )
        ).scalar_one_or_none()
        if not row:
            return {"deleted": False, "message": "未找到执行记录"}
        if row.end_time is None:
            ApiAutomationService._request_cancel_api_script_result(str(result_id))
        await db.execute(
            delete(ApiScriptResultModel).where(ApiScriptResultModel.result_id == result_id)
        )
        await db.execute(
            delete(ApiScriptResultListModel).where(
                ApiScriptResultListModel.result_id == result_id,
                ApiScriptResultListModel.created_by == user_id,
            )
        )
        await db.commit()
        ApiAutomationService._remove_api_result_files(str(result_id))
        ApiAutomationService._clear_api_script_cancel(str(result_id))
        return {"deleted": True, "message": "已删除"}

    @staticmethod
    async def get_script_result_detail(db: AsyncSession, result_id: int) -> Optional[Dict[str, Any]]:
        stmt = select(ApiScriptResultListModel).where(
            ApiScriptResultListModel.enabled_flag == 1,
            ApiScriptResultListModel.result_id == result_id,
        )
        row = (await db.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        d = row.__dict__.copy()
        d.pop("_sa_instance_state", None)
        return d

    @staticmethod
    async def get_script_result_detail_list(db: AsyncSession, result_id: int, menu_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(ApiScriptResultModel)
            .where(
                ApiScriptResultModel.enabled_flag == 1,
                ApiScriptResultModel.result_id == result_id,
                ApiScriptResultModel.menu_id == menu_id,
            )
            .order_by(ApiScriptResultModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

    @staticmethod
    async def get_script_result_report_list(db: AsyncSession, result_id: int, menu_id: str) -> List[Dict[str, Any]]:
        """对 /get_api_script_result_report_list：与 detail_list 一致"""
        return await ApiAutomationService.get_script_result_detail_list(db, result_id, menu_id)

  
    @staticmethod
    async def _find_keys_not_in_params(a_list: List[Dict[str, Any]], b_list: List[Dict[str, Any]]) -> List[str]:
        a_keys = {item.get("key") for item in (a_list or []) if item.get("key") is not None}
        b_keys = {item.get("key") for item in (b_list or []) if item.get("key") is not None}
        return list(b_keys - a_keys)

    @staticmethod
    async def _find_keys_not_in_dict(a: Dict[str, Any], b: Dict[str, Any], parent_key: str = "") -> List[str]:
        keys_not_in_a: List[str] = []
        for key in (b or {}):
            full_key = f"{parent_key}.{key}" if parent_key else str(key)
            if key not in (a or {}):
                keys_not_in_a.append(full_key)
            else:
                if isinstance(b[key], dict) and isinstance((a or {}).get(key), dict):
                    keys_not_in_a.extend(await ApiAutomationService._find_keys_not_in_dict((a or {})[key], b[key], full_key))
                elif isinstance(b[key], list) and isinstance((a or {}).get(key), list):
                    for i, item in enumerate(b[key]):
                        if isinstance(item, dict) and i < len((a or {})[key]) and isinstance((a or {})[key][i], dict):
                            keys_not_in_a.extend(
                                await ApiAutomationService._find_keys_not_in_dict((a or {})[key][i], item, f"{full_key}[{i}]")
                            )
        return keys_not_in_a

    @staticmethod
    async def _handle_check(old_headers, old_params, old_body, new_headers, new_params, new_body) -> List[Dict[str, Any]]:
        if not new_body:
            new_body = {}
        header_add = await ApiAutomationService._find_keys_not_in_params(old_headers or [], new_headers or [])
        params_add = await ApiAutomationService._find_keys_not_in_params(old_params or [], new_params or [])
        body_add = await ApiAutomationService._find_keys_not_in_dict(old_body or {}, new_body or {})

        header_del = await ApiAutomationService._find_keys_not_in_params(new_headers or [], old_headers or [])
        params_del = await ApiAutomationService._find_keys_not_in_params(new_params or [], old_params or [])
        body_del = await ApiAutomationService._find_keys_not_in_dict(new_body or {}, old_body or {})
        return [
            {"key": "headers", "add": header_add, "delete": header_del},
            {"key": "params", "add": params_add, "delete": params_del},
            {"key": "body", "add": body_add, "delete": body_del},
        ]

    @staticmethod
    async def _gitlab_handle_data(content_type: str, method: str) -> Tuple[int, int]:
        ct = content_type or ""
        if "application/json" in ct:
            body_type = 2
        elif "application/x-www-form-urlencoded" in ct:
            body_type = 4
        elif "form-data" in ct:
            body_type = 3
        else:
            body_type = 1
        m = (method or "").lower()
        http_method = 2
        if m == "get":
            http_method = 1
        elif m == "post":
            http_method = 2
        elif m == "put":
            http_method = 3
        elif m == "delete":
            http_method = 4
        return body_type, http_method

    @staticmethod
    async def _gitlab_handle_header(header_params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if header_params:
            return [{"key": i.get("name"), "value": i.get("example"), "status": True} for i in header_params]
        return [{"key": "Content-Type", "value": "application/json", "status": True}]

    @staticmethod
    async def _gitlab_handle_params(params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not params:
            return []
        return [{"key": j.get("name"), "value": j.get("example"), "status": True} for j in params]

    @staticmethod
    async def _gitlab_handle_body(body_params: List[Dict[str, Any]]) -> Dict[str, Any]:
 
        def handle_object(children: List[Dict[str, Any]]) -> Dict[str, Any]:
            out: Dict[str, Any] = {}
            for c in children or []:
                t = c.get("type")
                name = c.get("name")
                if not name:
                    continue
                if t == "object":
                    out[name] = handle_object(c.get("children") or [])
                elif t == "array":
                    out[name] = [handle_object(c.get("children") or [])]
                else:
                    out[name] = c.get("example")
            return out

        return handle_object(body_params or [])

    @staticmethod
    async def handle_gitlab_import(db: AsyncSession, apis: List[Dict[str, Any]], service_id: int, user_id: int) -> Dict[str, int]:
        service = (
            await db.execute(select(ApiServiceModel).where(ApiServiceModel.id == service_id, ApiServiceModel.enabled_flag == 1))
        ).scalar_one()
        service_name = "{{" + service.name + "}}"

   
        await db.execute(
            update(ApiMenuModel)
            .where(ApiMenuModel.api_service_id == service_id, ApiMenuModel.type == 2, ApiMenuModel.enabled_flag == 1)
            .values(status=0, updated_by=user_id)
        )

        async def get_or_create_menu(name: str, m_type: int, pid: int) -> int:
            row = (
                await db.execute(
                    select(ApiMenuModel).where(
                        ApiMenuModel.enabled_flag == 1,
                        ApiMenuModel.api_service_id == service_id,
                        ApiMenuModel.name == name,
                        ApiMenuModel.type == m_type,
                    )
                )
            ).scalar_one_or_none()
            if row:
                await db.execute(update(ApiMenuModel).where(ApiMenuModel.id == row.id).values(status=1, updated_by=user_id))
                return row.id
            menu = ApiMenuModel(
                name=name,
                type=m_type,
                pid=pid,
                api_service_id=service_id,
                status=1,
                api_id=None,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(menu)
            await db.flush()
            return menu.id

        imported_count = 0
        updated_count = 0
        folder_names = set()
        service_apis = list(
            (
                await db.execute(
                    select(ApiModel).where(
                        ApiModel.enabled_flag == 1,
                        ApiModel.api_service_id == service_id,
                    )
                )
            ).scalars().all()
        )

        for i in apis or []:
            if int(i.get("isFolder") or 0) != 1:
                continue
            first_id = await get_or_create_menu(i.get("name") or "", 0, 0)
            folder_names.add(str(i.get("name") or ""))
            for j in i.get("items") or []:
                if int(j.get("isFolder") or 0) != 1:
                    continue
                menu_id = await get_or_create_menu(j.get("name") or "", 1, first_id)
                folder_names.add(str(j.get("name") or ""))
                for k in j.get("items") or []:
                    try:
                        body_type, method = await ApiAutomationService._gitlab_handle_data(k.get("contentType") or "", k.get("httpMethod") or "")
                        params = await ApiAutomationService._gitlab_handle_params(k.get("queryParams") or [])
                        header = await ApiAutomationService._gitlab_handle_header(k.get("headerParams") or [])
                        body = await ApiAutomationService._gitlab_handle_body(k.get("requestParams") or [])
                        url = str(k.get("url") or "/")

                        api_row = ApiAutomationService._find_api_by_path_and_method(
                            service_apis, url, int(method)
                        )
                        if not api_row:
                            api_row = ApiAutomationService._find_api_by_path_and_method(
                                service_apis, service_name + url, int(method)
                            )

                        if api_row:
                            old_req = api_row.req or {}
                            req = {
                                "body_type": body_type,
                                "method": method,
                                "header": header,
                                "params": params,
                                "params_id": None,
                                "body": body,
                                "before": (old_req.get("before") or []),
                                "after": (old_req.get("after") or []),
                                "form_data": (old_req.get("form_data") or []),
                                "form_urlencoded": (old_req.get("form_urlencoded") or []),
                                "file_path": (old_req.get("file_path") or []),
                                "assert": (old_req.get("assert") or []),
                                "config": {"retry": 0, "req_timeout": 5, "res_timeout": 5},
                            }
                            key_check = await ApiAutomationService._handle_check(
                                old_req.get("header") or [],
                                old_req.get("params") or [],
                                old_req.get("body") or {},
                                header,
                                params,
                                body,
                            )
                            if key_check:
                                for m in key_check:
                                    if m.get("add") or m.get("delete"):
                                        db.add(
                                            ApiUpdateModel(
                                                req=key_check,
                                                api_id=int(api_row.id),
                                                api_service_id=int(service_id),
                                                created_by=user_id,
                                                updated_by=user_id,
                                            )
                                        )
                                        break
                            new_url = ApiAutomationService._prefer_existing_url(
                                str(api_row.url or ""),
                                service_name + url,
                            )
                            if service_name not in new_url and not re.match(r"^https?://", new_url, re.I):
                                # 无前置时仍按历史逻辑补上服务名占位
                                new_url = service_name + url
                            req["url"] = new_url
                            await db.execute(
                                update(ApiModel)
                                .where(ApiModel.id == api_row.id, ApiModel.enabled_flag == 1)
                                .values(
                                    url=new_url,
                                    req=req,
                                    document=k,
                                    updated_by=user_id,
                                )
                            )
                            api_id = api_row.id
                            updated_count += 1
                        else:
                            req = {
                                "body_type": body_type,
                                "method": method,
                                "header": header,
                                "params": params,
                                "body": body,
                                "before": [],
                                "after": [],
                                "form_data": [],
                                "form_urlencoded": [],
                                "file_path": [],
                                "assert": [],
                                "config": {"retry": 0, "req_timeout": 5, "res_timeout": 5},
                                "url": service_name + url,
                            }
                            api_value = ApiModel(
                                api_service_id=service_id,
                                url=service_name + url,
                                req=req,
                                document=k,
                                created_by=user_id,
                                updated_by=user_id,
                            )
                            db.add(api_value)
                            await db.flush()
                            api_id = api_value.id
                            service_apis.append(api_value)
                            imported_count += 1

                        # 菜单叶子节点（type=2）
                        leaf_name = k.get("name") or url
                        leaf_row = (
                            await db.execute(
                                select(ApiMenuModel).where(
                                    ApiMenuModel.enabled_flag == 1,
                                    ApiMenuModel.api_service_id == service_id,
                                    ApiMenuModel.type == 2,
                                    ApiMenuModel.api_id == int(api_id),
                                )
                            )
                        ).scalar_one_or_none()
                        if leaf_row:
                            await db.execute(update(ApiMenuModel).where(ApiMenuModel.id == leaf_row.id).values(status=1, updated_by=user_id))
                        else:
                            db.add(
                                ApiMenuModel(
                                    name=str(leaf_name),
                                    type=2,
                                    pid=int(menu_id),
                                    api_service_id=int(service_id),
                                    api_id=int(api_id),
                                    status=1,
                                    created_by=user_id,
                                    updated_by=user_id,
                                )
                            )
                    except Exception:
                        continue
        await db.commit()
        return {"imported": imported_count, "updated": updated_count, "folders": len(folder_names)}

    @staticmethod
    async def service_api_update(db: AsyncSession, body: Dict[str, Any]) -> None:
        """对service_api_update（开放给文档平台）"""
        if body.get("token") != "1fefb62cdd834925983f72c2bc9b9c55":
            raise ValueError("检验token失败，请联系-管理员")

        # author -> sys_user.username
        author = str(body.get("author") or "")
        u = await UserCRUD(db).get_by_username_crud(author)
        if not u:
            raise ValueError("author 对应用户不存在")
        user_id = int(u.id)

        server_name = str(body.get("serverName") or "")
        if not server_name:
            raise ValueError("serverName 不能为空")

    
        is_overseas = "overseas" in server_name
        project_name = "海外项目" if is_overseas else "国内项目"
        proj = (
            await db.execute(
                select(ApiProjectModel).where(ApiProjectModel.enabled_flag == 1, ApiProjectModel.name == project_name)
            )
        ).scalar_one_or_none()
        if not proj:
            proj = ApiProjectModel(name=project_name, img="", description="", created_by=1, updated_by=1)
            db.add(proj)
            await db.flush()

        service = (
            await db.execute(
                select(ApiServiceModel).where(ApiServiceModel.enabled_flag == 1, ApiServiceModel.name == server_name)
            )
        ).scalar_one_or_none()
        if not service:
            service = ApiServiceModel(
                name=server_name,
                img="",
                description="",
                api_project_id=int(proj.id),
                created_by=1,
                updated_by=1,
            )
            db.add(service)
            await db.flush()

        await db.commit()
        await ApiAutomationService.handle_gitlab_import(db, body.get("apis") or [], int(service.id), user_id)

    
    @staticmethod
    async def gitlab_ci_notice(db: AsyncSession, body: Dict[str, Any]) -> Dict[str, Any]:
        """
         gitlab_ci_notice：
        - 根据 api_project_id 找到脚本列表
        - 过滤 cn_service 包含 api_service
        - 创建 type=3 的定时任务（10 秒后执行一次）
        """
        api_project_id = int(body.get("api_project_id") or 0)
        api_service = str(body.get("api_service") or "")
        env_id = int(body.get("env_id") or 0)

        scripts = (
            await db.execute(
                select(ApiScriptModel).where(ApiScriptModel.enabled_flag == 1, ApiScriptModel.type == api_project_id)
            )
        ).scalars().all()
        script_ids: List[int] = []
        for s in scripts:
            cfg = s.config or {}
            cn_services = cfg.get("cn_service") or []
            if api_project_id == 1 and api_service and (api_service in cn_services):
                script_ids.append(int(s.id))

        result_id = int(time.time() * 1000)
        run_time = (datetime.now() + timedelta(seconds=10)).strftime("%Y-%m-%d %H:%M:%S")

        task_data = {
            "name": f"Gitlab CI: {api_service}",
            "type": 3,
            "status": 1,
            "script": {"api_script_list": script_ids, "env_id": env_id},
            "time": {"run_time": run_time, "type": 1},
            "notice": {"notice_id": [25], "status": 1},
            "description": "",
        }
    
        return await TaskSchedulerService.create_task(db, task_data, user_id=1)

    @staticmethod
    async def read_script_log(result_id: str) -> List[str]:
        base_dir = ApiAutomationService._get_api_result_dir(result_id)
        path = base_dir / f"{result_id}.txt"
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        lines = [l for l in lines if l.strip()]
        return list(reversed(lines))

    @staticmethod
    async def read_script_report_log(result_id: str, menu_id: str) -> List[str]:
        base_dir = ApiAutomationService._get_api_result_dir(result_id)
        path = base_dir / f"{menu_id}.txt"
        if not path.exists():
            return []
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        lines = [l for l in lines if l.strip()]
        return list(reversed(lines))

    @staticmethod
    async def _write_log_line(menu_uuid: str, result_id: str, message: str) -> None:
        base_dir = ApiAutomationService._get_api_result_dir(result_id)
        all_log = base_dir / f"{result_id}.txt"
        menu_log = base_dir / f"{menu_uuid}.txt"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{now} {message} "
        ApiAutomationService._append_log_file(all_log, line)
        ApiAutomationService._append_log_file(menu_log, line)

  
    @staticmethod
    async def _send_notice(
        db: AsyncSession,
        notice_id: int,
        notice_type: str,
        data: Dict[str, Any],
        user_id: int,
    ) -> None:
        try:
            notice = (
                await db.execute(
                    select(MsgNoticeModel).where(
                        MsgNoticeModel.id == int(notice_id),
                        MsgNoticeModel.enabled_flag == 1,
                    )
                )
            ).scalar_one_or_none()
            if not notice:
                return

            payload = {
                "id": notice.id,
                "type": notice.type,
                "value": notice.value,
                "status": notice.status,
                "script": notice.script or {},
            }

            
            if notice_type == "api_report":
                report_url = f"{app_config.BASE_URL}/_api_report?result_id={data.get('result_id')}"
                wechat = (payload.get("script") or {}).get("wechat") or {}
                content = str(wechat.get("content") or "")
                content = (
                    content.replace("{{result_id}}", str(data.get("result_id", "")))
                    .replace("{{device_name}}", str(data.get("device_name", "")))
                    .replace("{{percent}}", str(data.get("percent", "")))
                    .replace("{{total}}", str(data.get("total", "")))
                    .replace("{{passed}}", str(data.get("passed", "")))
                    .replace("{{fail}}", str(data.get("fail", "")))
                    .replace("{{un_run}}", str(data.get("un_run", "")))
                    .replace("{{report_url}}", report_url)
                )
                wechat["content"] = content
                payload["script"]["wechat"] = wechat
            elif notice_type == "app_report":
                base = str(getattr(app_config, "BASE_URL", "") or "").rstrip("/")
                report_url = f"{base}/app_report?result_id={data.get('result_id')}"
                wechat = (payload.get("script") or {}).get("wechat") or {}
                content = str(wechat.get("content") or "")
                content = (
                    content.replace("{{result_id}}", str(data.get("result_id", "")))
                    .replace("{{device_name}}", str(data.get("device_name", "")))
                    .replace("{{percent}}", str(data.get("percent", "")))
                    .replace("{{total}}", str(data.get("total", "")))
                    .replace("{{passed}}", str(data.get("passed", "")))
                    .replace("{{fail}}", str(data.get("fail", "")))
                    .replace("{{un_run}}", str(data.get("un_run", "")))
                    .replace("{{report_url}}", report_url)
                )
                wechat["content"] = content
                payload["script"]["wechat"] = wechat
            elif notice_type == "app_error_report":
                base = str(getattr(app_config, "BASE_URL", "") or "").rstrip("/")
                report_url = f"{base}/app_report?result_id={data.get('result_id', '')}"
                wechat = (payload.get("script") or {}).get("wechat") or {}
                content = str(wechat.get("content") or "")
                content = (
                    content.replace("{{device_name}}", str(data.get("device_name", "")))
                    .replace("{{result_id}}", str(data.get("result_id", "")))
                    .replace("{{report_url}}", report_url)
                )
                wechat["content"] = content
                payload["script"]["wechat"] = wechat
            else:
                wechat = (payload.get("script") or {}).get("wechat") or {}
                if "content" in wechat:
                    wechat["content"] = str(data)
                    payload["script"]["wechat"] = wechat

            # ：type==1 企业微信；type==2 钉钉；type==3 邮件
            if int(payload.get("type") or 0) == 1 and int(payload.get("status") or 0) == 1:
                ApiAutomationService._send_wechat_notice(payload)
        except Exception:

            return

    @staticmethod
    def _send_wechat_notice(notice: Dict[str, Any]) -> bool:
        try:
            web_hook_url = str(notice.get("value") or "")
            wechat = (notice.get("script") or {}).get("wechat") or {}
            msgtype = wechat.get("msgtype") or "text"
            mentioned_list = wechat.get("mentioned_list") or []

            if msgtype == "text":
                json_data = {
                    "msgtype": "text",
                    "text": {"content": wechat.get("content") or "", "mentioned_list": mentioned_list},
                }
            elif msgtype == "markdown":
                content = str(wechat.get("content") or "") + "\n"
                for u in mentioned_list:
                    content += f"<@{u}>"
                json_data = {"msgtype": "markdown", "markdown": {"content": content}}
            elif msgtype == "news":
                json_data = {
                    "msgtype": "news",
                    "news": {
                        "articles": (wechat.get("news") or {}).get("articles") or [],
                        "mentioned_list": mentioned_list,
                    },
                }
            else:
                json_data = {
                    "msgtype": "text",
                    "text": {"content": wechat.get("content") or "", "mentioned_list": mentioned_list},
                }

            headers = {"Content-Type": "application/json", "Charset": "UTF-8"}
            requests.post(web_hook_url, headers=headers, json=json_data)
            return True
        except Exception:
            return False


    # ── 代码生成辅助 ──────────────────────────────────────────────────

    @staticmethod
    async def get_apis_by_ids(db: AsyncSession, api_ids: list) -> list:
        """根据接口 ID 列表批量获取接口数据（用于代码生成）"""
        if not api_ids:
            return []
        result = await db.execute(
            select(ApiModel).where(ApiModel.id.in_(api_ids), ApiModel.enabled_flag == 1)
        )
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name or r.url,
                "url": r.url,
                "req": r.req or {},
            }
            for r in rows
        ]

    @staticmethod
    async def get_service_base_url(db: AsyncSession, service_id: int) -> str:
        """尝试从服务关联的环境配置中获取 base_url"""
        try:
            # 查找该服务下第一个环境的 host 配置
            result = await db.execute(
                select(ApiEnvironmentModel).where(ApiEnvironmentModel.enabled_flag == 1).limit(1)
            )
            env = result.scalar_one_or_none()
            if env and env.config:
                cfg = env.config if isinstance(env.config, list) else []
                for item in cfg:
                    if item.get("key") in ("host", "base_url", "baseUrl"):
                        return str(item.get("value", ""))
        except Exception:
            pass
        return ""


    # ── 服务排序 ──────────────────────────────────────────────────────

    @staticmethod
    async def sort_services(db: AsyncSession, ids: List[int], user_id: int) -> None:
        """按传入 ID 列表顺序更新服务的 sort 字段"""
        for idx, service_id in enumerate(ids):
            await db.execute(
                update(ApiServiceModel)
                .where(ApiServiceModel.id == int(service_id), ApiServiceModel.enabled_flag == 1)
                .values(sort=idx, updated_by=user_id)
            )
        await db.commit()

    # ── 用例集（Suite）CRUD ───────────────────────────────────────────

    @staticmethod
    def _build_suite_tree(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将平铺的用例集列表构建为树形结构"""
        by_id: Dict[int, Dict[str, Any]] = {}
        roots: List[Dict[str, Any]] = []
        for it in items:
            node = dict(it)
            node["children"] = []
            by_id[node["id"]] = node
        for node in by_id.values():
            pid = node.get("parent")
            if pid is None or pid not in by_id:
                roots.append(node)
            else:
                by_id[pid]["children"].append(node)
        return roots

    @staticmethod
    async def get_suite_list(db: AsyncSession, api_service_id: int, user_id: int) -> List[Dict[str, Any]]:
        from .model import ApiSuiteModel
        stmt = (
            select(ApiSuiteModel)
            .where(ApiSuiteModel.enabled_flag == 1, ApiSuiteModel.api_service_id == int(api_service_id))
            .order_by(ApiSuiteModel.sort.asc(), ApiSuiteModel.id.asc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        items = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            items.append(d)
        return ApiAutomationService._build_suite_tree(items)

    @staticmethod
    async def add_suite(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        from .model import ApiSuiteModel
        suite = ApiSuiteModel(
            name=str(body["name"]),
            parent=body.get("parent"),
            api_service_id=int(body["api_service_id"]),
            sort=0,
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(suite)
        await db.commit()
        await db.refresh(suite)
        d = suite.__dict__.copy()
        d.pop("_sa_instance_state", None)
        return d

    @staticmethod
    async def edit_suite(db: AsyncSession, suite_id: int, name: str, user_id: int) -> None:
        from .model import ApiSuiteModel
        await db.execute(
            update(ApiSuiteModel)
            .where(ApiSuiteModel.id == int(suite_id), ApiSuiteModel.enabled_flag == 1)
            .values(name=name, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def delete_suite(db: AsyncSession, suite_id: int, user_id: int) -> None:
        """级联删除用例集及其所有子用例集和用例"""
        from .model import ApiSuiteModel, ApiCaseModel
        # 递归收集所有子用例集 ID
        all_ids: List[int] = [int(suite_id)]
        queue = [int(suite_id)]
        while queue:
            current_ids = queue[:]
            queue = []
            children = (await db.execute(
                select(ApiSuiteModel.id).where(
                    ApiSuiteModel.enabled_flag == 1,
                    ApiSuiteModel.parent.in_(current_ids),
                )
            )).scalars().all()
            for cid in children:
                all_ids.append(cid)
                queue.append(cid)
        # 删除所有用例
        await db.execute(
            update(ApiCaseModel)
            .where(ApiCaseModel.suite_id.in_(all_ids), ApiCaseModel.enabled_flag == 1)
            .values(enabled_flag=0, updated_by=user_id)
        )
        # 删除所有用例集
        await db.execute(
            update(ApiSuiteModel)
            .where(ApiSuiteModel.id.in_(all_ids), ApiSuiteModel.enabled_flag == 1)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def sort_suites(db: AsyncSession, ids: List[int], user_id: int) -> None:
        from .model import ApiSuiteModel
        for idx, suite_id in enumerate(ids):
            await db.execute(
                update(ApiSuiteModel)
                .where(ApiSuiteModel.id == int(suite_id), ApiSuiteModel.enabled_flag == 1)
                .values(sort=idx, updated_by=user_id)
            )
        await db.commit()

    # ── 用例（Case）CRUD ──────────────────────────────────────────────

    @staticmethod
    async def get_case_list(db: AsyncSession, suite_id: int, user_id: int) -> List[Dict[str, Any]]:
        from .model import ApiCaseModel
        stmt = (
            select(ApiCaseModel)
            .where(ApiCaseModel.enabled_flag == 1, ApiCaseModel.suite_id == int(suite_id))
            .order_by(ApiCaseModel.id.asc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        result = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            result.append(d)
        return result

    @staticmethod
    async def add_case(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        from .model import ApiCaseModel
        case = ApiCaseModel(
            name=str(body["name"]),
            description=body.get("description") or "",
            suite_id=int(body["suite_id"]),
            script=body.get("script") or [],
            status=0,
            case_type=int(body.get("case_type") or 1),
            step_rely=int(body.get("step_rely", 1)),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(case)
        await db.commit()
        await db.refresh(case)
        d = case.__dict__.copy()
        d.pop("_sa_instance_state", None)
        return d

    @staticmethod
    async def edit_case(db: AsyncSession, case_id: int, body: Dict[str, Any], user_id: int) -> None:
        from .model import ApiCaseModel
        values: Dict[str, Any] = {"updated_by": user_id}
        for field in ("name", "description", "script", "case_type", "step_rely"):
            if field in body and body[field] is not None:
                values[field] = body[field]
        await db.execute(
            update(ApiCaseModel)
            .where(ApiCaseModel.id == int(case_id), ApiCaseModel.enabled_flag == 1)
            .values(**values)
        )
        await db.commit()

    @staticmethod
    async def delete_case(db: AsyncSession, case_id: int, user_id: int) -> None:
        from .model import ApiCaseModel
        await db.execute(
            update(ApiCaseModel)
            .where(ApiCaseModel.id == int(case_id), ApiCaseModel.enabled_flag == 1)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def run_api_case(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """执行用例：复用现有 run_api_script 逻辑，写入结果并关联 api_service_id"""
        from .model import ApiCaseModel, ApiSuiteModel
        case_ids = [int(i) for i in (body.get("case_ids") or [])]
        env_id = body.get("env_id")
        task_name = body.get("name") or f"用例执行_{uuid.uuid4().hex[:8]}"

        # 查询用例，获取 script 和所属服务 ID
        cases = (await db.execute(
            select(ApiCaseModel).where(ApiCaseModel.id.in_(case_ids), ApiCaseModel.enabled_flag == 1)
        )).scalars().all()
        if not cases:
            raise ValueError("未找到有效用例")

        # 通过第一个用例的 suite_id 获取 api_service_id
        suite = (await db.execute(
            select(ApiSuiteModel).where(ApiSuiteModel.id == cases[0].suite_id, ApiSuiteModel.enabled_flag == 1)
        )).scalar_one_or_none()
        api_service_id = suite.api_service_id if suite else None

        # 构建 run_list（复用现有用例执行格式）
        run_list = []
        case_id_map = {}  # name -> case_id 映射
        for case in cases:
            case_name = f"{case.name}_{case.id}"  # 确保唯一性
            run_list.append({
                "name": case.name,  # 显示原始名称
                "script": case.script or [],
                "config": {"env_id": env_id, "case_id": case.id, "step_rely": getattr(case, 'step_rely', 1)},
            })
            case_id_map[case_name] = case.id

        result_id = int(body.get("result_id") or uuid.uuid4().int % (10 ** 15))
        run_body = {
            "result_id": result_id,
            "name": task_name,
            "config": {"env_id": env_id},
            "run_list": run_list,
            "api_service_id": api_service_id,
        }
        await ApiAutomationService.run_api_script(db, run_body, user_id)

        # 执行完成后按用例单独更新状态
        pass_count = 0
        fail_count = 0
        try:
            from .model import ApiScriptResultModel
            # 查询该批次所有步骤结果，按 menu_id 分组
            result_rows = (await db.execute(
                select(ApiScriptResultModel).where(
                    ApiScriptResultModel.result_id == result_id,
                    ApiScriptResultModel.enabled_flag == 1,
                    ApiScriptResultModel.name != "执行结束",
                ).order_by(ApiScriptResultModel.id.asc())
            )).scalars().all()

            # 按 menu_id 分组，判断每组是否全部通过
            from collections import defaultdict, OrderedDict
            menu_pass: Dict[str, bool] = OrderedDict()
            for row in result_rows:
                mid = row.menu_id
                if mid not in menu_pass:
                    menu_pass[mid] = True
                if row.status == 0:
                    menu_pass[mid] = False

            # 按 run_list 顺序（即 cases 顺序）对应 menu_id
            menu_ids = list(menu_pass.keys())
            for i, case in enumerate(cases):
                if i < len(menu_ids):
                    is_pass = menu_pass[menu_ids[i]]
                else:
                    is_pass = True  # 无结果时默认通过
                new_status = 1 if is_pass else 2
                if is_pass:
                    pass_count += 1
                else:
                    fail_count += 1
                await db.execute(
                    update(ApiCaseModel)
                    .where(ApiCaseModel.id == case.id, ApiCaseModel.enabled_flag == 1)
                    .values(status=new_status, updated_by=user_id)
                )
            await db.commit()
        except Exception:
            pass

        total_count = len(cases)
        return {"result_id": str(result_id), "total": total_count, "pass": pass_count, "fail": fail_count}

    # ─── 脚本中心（NtestScript）CRUD ──────────────────────────────────────────

    @staticmethod
    async def _ensure_ntest_script_language_column(db: AsyncSession) -> None:
        """兼容旧库：缺少 language 列时自动补齐。"""
        try:
            await db.execute(text(
                "ALTER TABLE api_automation_ntest_scripts "
                "ADD COLUMN language VARCHAR(32) NOT NULL DEFAULT 'python'"
            ))
            await db.commit()
        except Exception:
            await db.rollback()

    @staticmethod
    async def get_ntest_scripts(db: AsyncSession, api_service_id: int, user_id: int) -> List[Dict]:
        """查询指定服务下的公共脚本列表（仅返回未软删除的记录）"""
        from .model import NtestScriptModel
        await ApiAutomationService._ensure_ntest_script_language_column(db)
        rows = (await db.execute(
            select(NtestScriptModel).where(
                NtestScriptModel.api_service_id == api_service_id,
                NtestScriptModel.enabled_flag == 1,
            ).order_by(NtestScriptModel.id.desc())
        )).scalars().all()
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "code": r.code,
                "language": getattr(r, "language", None) or "python",
                "api_service_id": r.api_service_id,
            }
            for r in rows
        ]

    @staticmethod
    async def add_ntest_script(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        """新增公共脚本"""
        from .model import NtestScriptModel
        from .script_runtime import normalize_language
        await ApiAutomationService._ensure_ntest_script_language_column(db)
        name = (body.get("name") or "").strip()
        if not name:
            raise ValueError("脚本名称不能为空")
        api_service_id = body.get("api_service_id")
        if not api_service_id:
            raise ValueError("api_service_id 不能为空")
        language = normalize_language(body.get("language") or "python")
        script = NtestScriptModel(
            name=name,
            description=body.get("description") or "",
            code=body.get("code") or "",
            language=language,
            api_service_id=int(api_service_id),
            created_by=user_id,
            enabled_flag=1,
        )
        db.add(script)
        await db.commit()

    @staticmethod
    async def edit_ntest_script(db: AsyncSession, script_id: int, body: Dict[str, Any], user_id: int) -> None:
        """编辑公共脚本"""
        from .script_runtime import normalize_language
        await ApiAutomationService._ensure_ntest_script_language_column(db)
        name = (body.get("name") or "").strip()
        if "name" in body and not name:
            raise ValueError("脚本名称不能为空")
        values: Dict[str, Any] = {"updated_by": user_id}
        if name:
            values["name"] = name
        if "description" in body:
            values["description"] = body["description"] or ""
        if "code" in body:
            values["code"] = body["code"] or ""
        if "language" in body:
            values["language"] = normalize_language(body.get("language") or "python")
        from .model import NtestScriptModel
        await db.execute(
            update(NtestScriptModel)
            .where(NtestScriptModel.id == script_id, NtestScriptModel.enabled_flag == 1)
            .values(**values)
        )
        await db.commit()

    @staticmethod
    async def delete_ntest_script(db: AsyncSession, script_id: int, user_id: int) -> None:
        """软删除公共脚本（将 enabled_flag 置为 0）"""
        from .model import NtestScriptModel
        await db.execute(
            update(NtestScriptModel)
            .where(NtestScriptModel.id == script_id, NtestScriptModel.enabled_flag == 1)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    # ─── 数据查询（QueryDB）─────────────────────────────────────────────────────

    @staticmethod
    def _is_select_only(sql: str) -> bool:
        """校验所有 SQL 语句是否均为 SELECT（支持多条语句，以 ; 分隔）"""
        import re
        # 去除注释
        cleaned = re.sub(r'--[^\n]*', '', sql)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        # 按分号拆分，过滤空语句
        stmts = [s.strip() for s in cleaned.split(';') if s.strip()]
        if not stmts:
            return False
        for stmt in stmts:
            first_word = stmt.split()[0].upper() if stmt.split() else ''
            if first_word != 'SELECT':
                return False
        return True

    @staticmethod
    async def execute_db_query(db: AsyncSession, db_id: int, sql: str) -> List[Dict]:
        """执行一条或多条 SELECT 查询，返回所有结果行的合并列表"""
        import re
        import pymysql
        import pymysql.cursors

        if not ApiAutomationService._is_select_only(sql):
            raise ValueError("仅支持 SELECT 查询语句")

        cfg = await ApiAutomationService._get_db_config(db, db_id)
        conn = pymysql.connect(
            host=cfg["host"], port=cfg["port"],
            user=cfg["user"], password=cfg["password"],
            database=cfg["database"] or None,
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor,
        )

        # 拆分多条语句
        cleaned = re.sub(r'--[^\n]*', '', sql)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        stmts = [s.strip() for s in cleaned.split(';') if s.strip()]

        all_results: List[Dict] = []
        try:
            with conn.cursor() as cur:
                for stmt in stmts:
                    cur.execute(stmt)
                    rows = cur.fetchall()
                    all_results.extend([dict(r) for r in rows])
        finally:
            conn.close()

        return all_results

    @staticmethod
    async def _get_db_config(db: AsyncSession, db_id: int) -> Dict[str, Any]:
        """从 ApiDatabaseModel 获取数据库连接配置"""
        from .model import ApiDatabaseModel
        row = (await db.execute(
            select(ApiDatabaseModel).where(
                ApiDatabaseModel.id == db_id,
                ApiDatabaseModel.enabled_flag == 1,
            )
        )).scalars().first()
        if not row:
            raise ValueError("数据库配置不存在")
        return {
            "host": row.host or "",
            "port": int(row.port or 3306),
            "user": row.username or "",
            "password": row.password or "",
            "database": row.database_name or "",
            "db_type": (row.db_type or "mysql").lower(),
        }

    @staticmethod
    async def get_db_databases(db: AsyncSession, db_id: int) -> List[Dict]:
        """获取指定数据库连接下的所有数据库名"""
        import pymysql
        cfg = await ApiAutomationService._get_db_config(db, db_id)
        conn = pymysql.connect(
            host=cfg["host"], port=cfg["port"],
            user=cfg["user"], password=cfg["password"],
            connect_timeout=10,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW DATABASES")
                rows = cur.fetchall()
            return [{"name": r[0], "type": "database", "hasChildren": True} for r in rows]
        finally:
            conn.close()

    @staticmethod
    async def get_db_tables(db: AsyncSession, db_id: int, database: str) -> List[Dict]:
        """获取指定数据库下的所有表名"""
        import pymysql
        cfg = await ApiAutomationService._get_db_config(db, db_id)
        conn = pymysql.connect(
            host=cfg["host"], port=cfg["port"],
            user=cfg["user"], password=cfg["password"],
            database=database,
            connect_timeout=10,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SHOW TABLES")
                rows = cur.fetchall()
            return [{"name": r[0], "type": "table", "isLeaf": True} for r in rows]
        finally:
            conn.close()

