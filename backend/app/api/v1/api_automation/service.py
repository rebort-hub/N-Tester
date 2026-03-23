"""
接口自动化模块 - 业务逻辑服务
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import pymysql
import requests
import uuid
from datetime import timedelta
from jsonpath_ng import parse as jsonpath_parse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_

from .model import (
    ApiModel,
    ApiProjectModel,
    ApiServiceModel,
    ApiMenuModel,
    ApiEnvironmentModel,
    ApiVariableModel,
    ApiDatabaseModel,
    ApiParamsModel,
    ApiResultModel,
    ApiEditModel,
    ApiScriptModel,
    ApiScriptResultListModel,
    ApiScriptResultModel,
    ApiCodeModel,
    ApiFunctionModel,
    ApiUpdateModel,
)

from config import config as app_config

from pathlib import Path
import os
from app.api.v1.system.user.crud import UserCRUD
from app.api.v1.task_scheduler.service import TaskSchedulerService
from app.api.v1.task_scheduler.model import MsgNoticeModel


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
    async def _complete_var(db: AsyncSession, env_id: int, key: str) -> Any:
        env = await db.execute(
            select(ApiEnvironmentModel).where(ApiEnvironmentModel.id == env_id, ApiEnvironmentModel.enabled_flag == 1)
        )
        env_row = env.scalar_one_or_none()
        if env_row:
            for i in (env_row.config or []):
                if i.get("name") == key:
                    return i.get("value")
            for j in (env_row.variable or []):
                if j.get("name") == key:
                    return j.get("value")

        g = await db.execute(
            select(ApiVariableModel).where(ApiVariableModel.enabled_flag == 1, ApiVariableModel.name == key)
        )
        g_row = g.scalar_one_or_none()
        if g_row:
            return g_row.value
        return ""

    @staticmethod
    async def _find_var(db: AsyncSession, env_id: int, s: str) -> str:
        import re

        keys = re.findall(r"\{{(.+?)}}", s) if ("{{" in s and "}}" in s) else []
        for k in keys:
            var = "{{" + k + "}}"
            val = await ApiAutomationService._complete_var(db, env_id, var)
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
            if i.get("status"):
                res[i.get("key")] = i.get("value")
        return res

    
    @staticmethod
    def _jsonpath_value(
        res_type: int,
        expr: str,
        res: Dict[str, Any],
        header: Dict[str, Any],
        body: Any,
    ) -> Tuple[bool, str]:
        """
        对齐旧 jsonpath_value：
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
        base = Path(app_config.BASEDIR) / "static" / "api_results" / str(result_id)
        if not base.exists():
            os.makedirs(base, exist_ok=True)
        return base

    @staticmethod
    def _append_log_file(file_path: Path, text: str) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

   
    @staticmethod
    async def get_projects(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        stmt = (
            select(ApiProjectModel)
            .where(ApiProjectModel.enabled_flag == 1, ApiProjectModel.created_by == user_id)
            .order_by(ApiProjectModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data = [r.__dict__ for r in rows]
        for d in data:
            d.pop("_sa_instance_state", None)
        return {"content": data, "total": len(data)}

    @staticmethod
    async def get_services(db: AsyncSession, project_id: Optional[int], user_id: int) -> Dict[str, Any]:
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
    async def get_projects_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        page, page_size = ApiAutomationService._extract_page(body)
        search = body.get("search") or {}
        name_like = ApiAutomationService._extract_contains(search, "name__contains", "name__icontains", "name")
        stmt = select(ApiProjectModel).where(ApiProjectModel.enabled_flag == 1, ApiProjectModel.created_by == user_id)
        if name_like:
            stmt = stmt.where(ApiProjectModel.name.like(f"%{name_like}%"))
        stmt = stmt.order_by(ApiProjectModel.id.desc())
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
    async def get_services_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        page, page_size = ApiAutomationService._extract_page(body)
        search = body.get("search") or {}
        name_like = ApiAutomationService._extract_contains(search, "name__contains", "name__icontains", "name")
        project_id = body.get("project_id") or body.get("api_project_id") or search.get("api_project_id")
        stmt = select(ApiServiceModel).where(ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
        if project_id:
            stmt = stmt.where(ApiServiceModel.api_project_id == int(project_id))
        if name_like:
            stmt = stmt.where(ApiServiceModel.name.like(f"%{name_like}%"))
        stmt = stmt.order_by(ApiServiceModel.id.desc())
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
    async def add_project(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        proj = ApiProjectModel(
            name=str(body["name"]),
            img=str(body.get("img") or ""),
            description=str(body.get("description") or ""),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(proj)
        await db.commit()

    @staticmethod
    async def edit_project(db: AsyncSession, project_id: int, body: Dict[str, Any], user_id: int) -> None:
        await db.execute(
            update(ApiProjectModel)
            .where(ApiProjectModel.id == int(project_id), ApiProjectModel.enabled_flag == 1, ApiProjectModel.created_by == user_id)
            .values(
                name=body.get("name"),
                img=body.get("img"),
                description=body.get("description"),
                updated_by=user_id,
            )
        )
        await db.commit()

    @staticmethod
    async def delete_project(db: AsyncSession, project_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiProjectModel)
            .where(ApiProjectModel.id == int(project_id), ApiProjectModel.enabled_flag == 1, ApiProjectModel.created_by == user_id)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def add_service(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        svc = ApiServiceModel(
            name=str(body["name"]),
            api_project_id=int(body["api_project_id"]),
            img=str(body.get("img") or ""),
            description=str(body.get("description") or ""),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(svc)
        await db.commit()

    @staticmethod
    async def edit_service(db: AsyncSession, service_id: int, body: Dict[str, Any], user_id: int) -> None:
        await db.execute(
            update(ApiServiceModel)
            .where(ApiServiceModel.id == int(service_id), ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
            .values(
                name=body.get("name"),
                api_project_id=body.get("api_project_id"),
                img=body.get("img"),
                description=body.get("description"),
                updated_by=user_id,
            )
        )
        await db.commit()

    @staticmethod
    async def delete_service(db: AsyncSession, service_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiServiceModel)
            .where(ApiServiceModel.id == int(service_id), ApiServiceModel.enabled_flag == 1, ApiServiceModel.created_by == user_id)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    
    @staticmethod
    async def get_params_list(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        stmt = (
            select(ApiParamsModel)
            .where(ApiParamsModel.enabled_flag == 1, ApiParamsModel.created_by == user_id)
            .order_by(ApiParamsModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": len(data)}

    @staticmethod
    async def add_params(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        row = ApiParamsModel(
            name=str(body["name"]),
            value=body.get("value") or {},
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(row)
        await db.commit()

    @staticmethod
    async def edit_params(db: AsyncSession, params_id: int, body: Dict[str, Any], user_id: int) -> None:
        await db.execute(
            update(ApiParamsModel)
            .where(ApiParamsModel.id == int(params_id), ApiParamsModel.enabled_flag == 1, ApiParamsModel.created_by == user_id)
            .values(name=body.get("name"), value=body.get("value"), updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def delete_params(db: AsyncSession, params_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiParamsModel)
            .where(ApiParamsModel.id == int(params_id), ApiParamsModel.enabled_flag == 1, ApiParamsModel.created_by == user_id)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def get_functions(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        stmt = (
            select(ApiFunctionModel)
            .where(ApiFunctionModel.enabled_flag == 1, ApiFunctionModel.created_by == user_id)
            .order_by(ApiFunctionModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": len(data)}

    @staticmethod
    async def add_function(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        row = ApiFunctionModel(
            name=str(body["name"]),
            description=str(body.get("description") or ""),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(row)
        await db.commit()

    @staticmethod
    async def edit_function(db: AsyncSession, function_id: int, body: Dict[str, Any], user_id: int) -> None:
        await db.execute(
            update(ApiFunctionModel)
            .where(ApiFunctionModel.id == int(function_id), ApiFunctionModel.enabled_flag == 1, ApiFunctionModel.created_by == user_id)
            .values(name=body.get("name"), description=body.get("description"), updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def delete_function(db: AsyncSession, function_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiFunctionModel)
            .where(ApiFunctionModel.id == int(function_id), ApiFunctionModel.enabled_flag == 1, ApiFunctionModel.created_by == user_id)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def get_codes(db: AsyncSession) -> List[Dict[str, Any]]:
        stmt = select(ApiCodeModel).where(ApiCodeModel.enabled_flag == 1).order_by(ApiCodeModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return data

    @staticmethod
    async def get_codes_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        page, page_size = ApiAutomationService._extract_page(body)
        search = body.get("search") or {}
        name_like = ApiAutomationService._extract_contains(search, "name__contains", "name__icontains", "name")
        code_like = ApiAutomationService._extract_contains(search, "code__contains", "code__icontains", "code")
        stmt = select(ApiCodeModel).where(ApiCodeModel.enabled_flag == 1, ApiCodeModel.created_by == user_id)
        if name_like and code_like:
            stmt = stmt.where(or_(ApiCodeModel.name.like(f"%{name_like}%"), ApiCodeModel.code.like(f"%{code_like}%")))
        elif name_like:
            stmt = stmt.where(ApiCodeModel.name.like(f"%{name_like}%"))
        elif code_like:
            stmt = stmt.where(ApiCodeModel.code.like(f"%{code_like}%"))
        stmt = stmt.order_by(ApiCodeModel.id.desc())
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
    async def add_code(db: AsyncSession, body: Dict[str, Any], user_id: int) -> None:
        row = ApiCodeModel(
            code=str(body["code"]),
            name=str(body["name"]),
            description=str(body.get("description") or ""),
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(row)
        await db.commit()

    @staticmethod
    async def edit_code(db: AsyncSession, code_id: int, body: Dict[str, Any], user_id: int) -> None:
        await db.execute(
            update(ApiCodeModel)
            .where(ApiCodeModel.id == int(code_id), ApiCodeModel.enabled_flag == 1, ApiCodeModel.created_by == user_id)
            .values(code=body.get("code"), name=body.get("name"), description=body.get("description"), updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def delete_code(db: AsyncSession, code_id: int, user_id: int) -> None:
        await db.execute(
            update(ApiCodeModel)
            .where(ApiCodeModel.id == int(code_id), ApiCodeModel.enabled_flag == 1, ApiCodeModel.created_by == user_id)
            .values(enabled_flag=0, updated_by=user_id)
        )
        await db.commit()

    @staticmethod
    async def get_functions_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        page, page_size = ApiAutomationService._extract_page(body)
        search = body.get("search") or {}
        name_like = ApiAutomationService._extract_contains(search, "name__contains", "name__icontains", "name")
        stmt = select(ApiFunctionModel).where(ApiFunctionModel.enabled_flag == 1, ApiFunctionModel.created_by == user_id)
        if name_like:
            stmt = stmt.where(ApiFunctionModel.name.like(f"%{name_like}%"))
        stmt = stmt.order_by(ApiFunctionModel.id.desc())
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
    async def get_params_list_paged(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        page, page_size = ApiAutomationService._extract_page(body)
        search = body.get("search") or {}
        name_like = ApiAutomationService._extract_contains(search, "name__contains", "name__icontains", "name")
        stmt = select(ApiParamsModel).where(ApiParamsModel.enabled_flag == 1, ApiParamsModel.created_by == user_id)
        if name_like:
            stmt = stmt.where(ApiParamsModel.name.like(f"%{name_like}%"))
        stmt = stmt.order_by(ApiParamsModel.id.desc())
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
    async def params_select(db: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
        stmt = select(ApiParamsModel).where(ApiParamsModel.enabled_flag == 1, ApiParamsModel.created_by == user_id).order_by(ApiParamsModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            data.append({"id": r.id, "name": r.name, "value": r.value})
        return data

    @staticmethod
    async def get_updates(db: AsyncSession, api_service_id: Optional[int], user_id: int) -> Dict[str, Any]:
        stmt = select(ApiUpdateModel).where(ApiUpdateModel.enabled_flag == 1)
        if api_service_id:
            stmt = stmt.where(ApiUpdateModel.api_service_id == int(api_service_id))
       
        stmt = stmt.where(ApiUpdateModel.created_by == user_id).order_by(ApiUpdateModel.id.desc())
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": len(data)}

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
    async def add_database(db: AsyncSession, data: Dict[str, Any], user_id: int) -> None:
        model = ApiDatabaseModel(
            name=data["name"],
            config=data.get("config") or {},
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(model)
        await db.commit()

    @staticmethod
    async def edit_database(db: AsyncSession, db_id: int, data: Dict[str, Any], user_id: int) -> None:
        await db.execute(
            update(ApiDatabaseModel)
            .where(
                ApiDatabaseModel.id == db_id,
                ApiDatabaseModel.enabled_flag == 1,
                ApiDatabaseModel.created_by == user_id,
            )
            .values(
                name=data.get("name"),
                config=data.get("config"),
                updated_by=user_id,
            )
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
        # 逻辑删除
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
        data.pop("id", None)  
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
        new_req = body.get("req") or {}
        await db.execute(
            update(ApiModel)
            .where(ApiModel.id == api_id, ApiModel.enabled_flag == 1)
            .values(url=body.get("url"), req=new_req, updated_by=user_id)
        )
        edits = ApiAutomationService._compare_data(old_req, new_req)
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
    async def get_request_history(db: AsyncSession, user_id: int) -> Dict[str, Any]:
        stmt = (
            select(ApiResultModel)
            .where(ApiResultModel.enabled_flag == 1, ApiResultModel.created_by == user_id)
            .order_by(ApiResultModel.id.desc())
        )
        rows = (await db.execute(stmt)).scalars().all()
        data: List[Dict[str, Any]] = []
        for r in rows:
            d = r.__dict__.copy()
            d.pop("_sa_instance_state", None)
            data.append(d)
        return {"content": data, "total": len(data)}

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
                env_row = (
                    await db.execute(
                        select(ApiEnvironmentModel).where(
                            ApiEnvironmentModel.id == env_id,
                            ApiEnvironmentModel.enabled_flag == 1,
                            ApiEnvironmentModel.created_by == user_id,
                        )
                    )
                ).scalar_one_or_none()
                if not env_row:
                    return {"status": 0, "message": f"前置操作-设置环境变量：{name} 失败，原因：环境不存在"}
                vars_list = list(env_row.variable or [])
                found = False
                for item in vars_list:
                    if item.get("name") == name:
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
    ) -> List[Dict[str, Any]]:
        """
        pre_request：
        - type=1: 预请求接口
        - type=2: 设置变量
        - type=3: 等待
        """
        results: List[Dict[str, Any]] = []
        for op in ops or []:
            try:
                t = int(op.get("type") or 0)
                if t == 1:
                    # 对齐旧 pre_request：通过菜单(type=3)定位 Api，再走 pre_request_api（不执行 before）
                    api_id_list = op.get("api_id") or []
                    menu_id = int(api_id_list[-1]) if api_id_list else 0
                    if not menu_id:
                        results.append(
                            {
                                "status": 0,
                                "message": "前置操作-预请求接口：未选择接口用例，请求失败",
                                "content": [],
                                "type": t,
                            }
                        )
                        continue
                    menu_row = (
                        await db.execute(
                            select(ApiMenuModel).where(
                                ApiMenuModel.id == menu_id,
                                ApiMenuModel.type == 3,
                                ApiMenuModel.enabled_flag == 1,
                            )
                        )
                    ).scalar_one_or_none()
                    if not menu_row or not menu_row.api_id:
                        results.append(
                            {
                                "status": 0,
                                "message": "前置操作-预请求接口：未选择接口用例，请求失败",
                                "content": [],
                                "type": t,
                            }
                        )
                        continue
                    api_row = (
                        await db.execute(
                            select(ApiModel).where(
                                ApiModel.id == int(menu_row.api_id),
                                ApiModel.enabled_flag == 1,
                            )
                        )
                    ).scalar_one_or_none()
                    if not api_row:
                        results.append(
                            {
                                "status": 0,
                                "message": "前置操作-预请求接口：接口不存在，请求失败",
                                "content": [],
                                "type": t,
                            }
                        )
                        continue
                    res = await ApiAutomationService._pre_request_api(
                        db=db,
                        api=api_row,
                        env_id=int(op.get("env_id") or env_id),
                        user_id=user_id,
                    )
                    results.append(res)
                elif t == 2:
                    r = await ApiAutomationService._pre_set_var(db, op, env_id, user_id)
                    r["type"] = t
                    results.append(r)
                elif t == 3:
                    r = await ApiAutomationService._pre_wait_time(int(op.get("wait_time") or 0))
                    r["type"] = t
                    results.append(r)
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
        api_req = api.req or {}

        body_payload = await ApiAutomationService.handle_var(db, env_id, api_req.get("body") or {})
        method = int(api_req.get("method") or 2)
        body_type = int(api_req.get("body_type") or 2)
        headers = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("header")))
        params = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("params")))
        form_data = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("form_data")))
        form_urlencoded = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(api_req.get("form_urlencoded")))
        file_paths = api_req.get("file_path") or []
        config = api_req.get("config") or {"retry": 0, "req_timeout": 5, "res_timeout": 5}

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
                env_row = (
                    await db.execute(
                        select(ApiEnvironmentModel).where(
                            ApiEnvironmentModel.id == env_id,
                            ApiEnvironmentModel.enabled_flag == 1,
                            ApiEnvironmentModel.created_by == user_id,
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
                    if item.get("name") == target_name:
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
    ) -> List[Dict[str, Any]]:
        """
        after_request：
        - type=1: 提取变量
        - type=2: 等待
        """
        results: List[Dict[str, Any]] = []
        for op in ops or []:
            try:
                t = int(op.get("type") or 0)
                if t == 1:
                    results.append(await ApiAutomationService._after_set_var(db, op, res, header, body, env_id, user_id))
                elif t == 2:
                    results.append(await ApiAutomationService._after_wait_time(int(op.get("wait_time") or 0)))
                else:
                    results.append({"status": 0, "message": f"未知后置操作类型：{t}"})
            except Exception as e:
                results.append({"status": 0, "message": f"后置操作执行失败，原因：{str(e)}"})
        return results

    @staticmethod
    async def _res_assert(rule: Dict[str, Any], res: Dict[str, Any], header: Dict[str, Any], body: Any) -> Dict[str, Any]:
        """res_assert：比较期望值和实际值"""
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
    ) -> List[Dict[str, Any]]:
        """
        handle_assert：
        - type=1: 响应结果断言
        - type=4: 直连数据库断言
        """
        results: List[Dict[str, Any]] = []
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
                else:
                    results.append({"status": 0, "message": f"未知断言类型：{t}", "type": t})
            except Exception as e:
                results.append({"status": 0, "message": f"断言操作执行失败，原因：{str(e)}"})
        return results

    @staticmethod
    async def _send_request(method: int, url: str, headers: Dict[str, Any], params: Dict[str, Any], body_type: int, body: Any,
                            form_data: Dict[str, Any], form_urlencoded: Dict[str, Any], file_paths: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
        timeout = (config.get("req_timeout", 5), config.get("res_timeout", 5))
        try:
            if method == 1:
                r = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method == 2:
                if body_type in (1, 2):
                    r = requests.post(url, headers=headers, json=(body if body_type == 2 else {}), timeout=timeout)
                elif body_type == 3:
                    r = requests.post(url, headers=headers, data=form_data, timeout=timeout)
                elif body_type == 4:
                    r = requests.post(url, headers=headers, data=form_urlencoded, timeout=timeout)
                elif body_type == 5:
                    files = []
                    for p in file_paths or []:
                        files.append(("file", (p.split("/")[-1], open(p, "rb"), "application/octet-stream")))
                    r = requests.request("POST", url=url, files=files, data={}, timeout=timeout)
                else:
                    r = requests.post(url, headers=headers, json=body, timeout=timeout)
            elif method == 3:
                r = requests.put(url, headers=headers, params=params, json=body, timeout=timeout)
            elif method == 4:
                r = requests.delete(url, headers=headers, params=params, timeout=timeout)
            else:
                r = requests.request("GET", url=url, headers=headers, timeout=timeout)

            try:
                body_json = r.json()
            except Exception:
                body_json = {"raw": r.text}
            return {
                "code": r.status_code,
                "res_time": str(round(r.elapsed.total_seconds() * 1000, 2)),
                "body": body_json,
                "header": dict(r.headers),
                "size": str((len(r.text.encode("utf-8")) if r.text else 0) + (len(str(r.headers).encode("utf-8")))),
            }
        except Exception as e:
            return {
                "code": 500,
                "body": {"msg": "接口请求失败", "exception": str(e)},
                "header": {},
                "size": 0,
                "res_time": 0,
            }

    @staticmethod
    async def execute_api_send(db: AsyncSession, body: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
       输入 body 基本结构
        """
        env_id = int(body.get("env_id") or 0)
        req = body.get("req") or {}
       
        raw_url = body.get("url") or req.get("url") or ""
        url = await ApiAutomationService.handle_var(db, env_id, raw_url)

        # 参数依赖
        params_id = req.get("params_id")
        if params_id is not None:
            p = (await db.execute(select(ApiParamsModel).where(ApiParamsModel.id == int(params_id), ApiParamsModel.enabled_flag == 1))).scalar_one_or_none()
            if p and isinstance(req.get("body"), dict) and isinstance(p.value, dict):
                req["body"].update(p.value)

        body_payload = await ApiAutomationService.handle_var(db, env_id, req.get("body") or {})
        method = int(req.get("method") or 2)
        body_type = int(req.get("body_type") or 2)
        headers = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("header")))
        params = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("params")))
        form_data = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("form_data")))
        form_urlencoded = await ApiAutomationService.handle_var(db, env_id, ApiAutomationService.params_header(req.get("form_urlencoded")))
        file_paths = req.get("file_path") or []
        config = req.get("config") or {"retry": 0, "req_timeout": 5, "res_timeout": 5}

     
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
            )

        res["before"] = before_list
        res["after"] = after_list
        res["assert"] = assert_list
        res["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                    "params_id": params_id,
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

    # -------------------- 场景执行与结果 --------------------
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

        # 创建汇总记录
        summary = ApiScriptResultListModel(
            result_id=int(result_id),
            name=data["name"],
            script=[],
            config=data.get("config") or {},
            result={},
            created_by=user_id,
            updated_by=user_id,
        )
        db.add(summary)
        await db.flush()

        all_pass = 0
        all_fail = 0
        total = 0

        for case in data.get("run_list", []):
            case["status"] = 1
            case["pass"] = 0
            case["fail"] = 0
            case_uuid = await ApiAutomationService._new_uuid()
            case["uuid"] = case_uuid

            params_id = case.get("config", {}).get("params_id")

            for step in case.get("script", []):
               
                total = total + len(case.get("script") or [])
                step_uuid = await ApiAutomationService._new_uuid()
                step["uuid"] = step_uuid

                await ApiAutomationService._write_log_line(
                    case_uuid, result_id, f"开始执行接口-{step.get('name')}"
                )

                success, api_req, api_res = await ApiAutomationService._execute_script_step(
                    db=db,
                    step=step,
                    result_id=result_id,
                    menu_uuid=case_uuid,
                    env_id=env_id,
                    params_id=params_id,
                    user_id=user_id,
                )

                if success:
                    case["pass"] += 1
                    all_pass += 1
                else:
                    case["status"] = 0
                    case["fail"] += 1
                    all_fail += 1

                await ApiAutomationService._write_log_line(
                    case_uuid, result_id, f"接口-{step.get('name')}执行完成"
                )
                time.sleep(3)

        percent = round(all_pass / total * 100, 2) if total else 0
        summary.script = data.get("run_list") or []
        summary.result = {
            "total": total,
            "pass": all_pass,
            "fail": all_fail,
            "percent": percent,
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

    @staticmethod
    async def _execute_script_step(
        db: AsyncSession,
        step: Dict[str, Any],
        result_id: str,
        menu_uuid: str,
        env_id: int,
        params_id: Optional[int],
        user_id: int,
    ) -> Tuple[bool, Dict[str, Any], Dict[str, Any]]:
        """单步执行逻辑，对handle_api_request（before -> request -> after -> assert）。"""
        req: Dict[str, Any] = {}
        try:
            api_id = int(step["api_id"])
            api_row = (
                await db.execute(
                    select(ApiModel).where(
                        ApiModel.id == api_id,
                        ApiModel.enabled_flag == 1,
                    )
                )
            ).scalar_one()
            api_cfg = api_row.req or {}

            
            try:
                url = await ApiAutomationService.handle_var(db, env_id, api_row.url)
                await ApiAutomationService._write_log_line(menu_uuid, result_id, f"请求地址-url：{url}")
            except Exception as e:
                await ApiAutomationService._write_log_line(menu_uuid, result_id, f"请求url地址解析失败，原因是：{e}")
                url = str(e)

            async def _safe_handle_params(raw: Any, t: str) -> Dict[str, Any]:
                try:
                    d = ApiAutomationService.params_header(raw)
                    d = await ApiAutomationService.handle_var(db, env_id, d)
                    await ApiAutomationService._write_log_line(menu_uuid, result_id, f"请求参数-{t}：{d}")
                    return d
                except Exception as e:
                    await ApiAutomationService._write_log_line(menu_uuid, result_id, f"请求参数解析失败，原因：{str(e)}")
                    return {"Exception": str(e)}

            async def _safe_handle_body(raw: Any) -> Any:
                try:
                    d = await ApiAutomationService.handle_var(db, env_id, raw)
                    await ApiAutomationService._write_log_line(menu_uuid, result_id, f"请求体-body：{d}")
                    return d
                except Exception as e:
                    await ApiAutomationService._write_log_line(menu_uuid, result_id, f"请求体解析失败，原因：{str(e)}")
                    return {"Exception": str(e)}

            headers = await _safe_handle_params(api_cfg.get("header"), "header") if api_cfg.get("header") else {}
            params = await _safe_handle_params(api_cfg.get("params"), "params") if api_cfg.get("params") else {}

            if api_cfg.get("params_id") is not None and params_id is not None:
                p = (
                    await db.execute(
                        select(ApiParamsModel).where(
                            ApiParamsModel.id == int(params_id),
                            ApiParamsModel.enabled_flag == 1,
                        )
                    )
                ).scalar_one_or_none()
                if p and isinstance(api_cfg.get("body"), dict) and isinstance(p.value, dict):
                    api_cfg["body"].update(p.value)

            body = await _safe_handle_body(api_cfg.get("body") or {})
            form_data = await _safe_handle_params(api_cfg.get("form_data"), "form_data") if api_cfg.get("form_data") else {}
            form_urlencoded = await _safe_handle_params(api_cfg.get("form_urlencoded"), "form_urlencoded") if api_cfg.get("form_urlencoded") else {}
            file_paths = api_cfg.get("file_path") or []
            config = api_cfg.get("config") or {"retry": 0, "req_timeout": 5, "res_timeout": 5}

            
            before_ops = api_cfg.get("before") or []
            after_ops = api_cfg.get("after") or []
            assert_ops = api_cfg.get("assert") or []

            before_list: List[Dict[str, Any]] = []
            if before_ops:
                before_list = await ApiAutomationService._pre_request(
                    db=db,
                    ops=before_ops,
                    env_id=env_id,
                    user_id=user_id,
                )
            before_status = all(int(i.get("status") or 0) == 1 for i in before_list) if before_ops else True
            for item in before_list:
                if item.get("message"):
                    await ApiAutomationService._write_log_line(menu_uuid, result_id, str(item.get("message")))

            res = await ApiAutomationService._send_request(
                method=int(api_cfg.get("method") or 2),
                url=str(url),
                headers=headers,
                params=params,
                body_type=int(api_cfg.get("body_type") or 2),
                body=body,
                form_data=form_data,
                form_urlencoded=form_urlencoded,
                file_paths=file_paths,
                config=config,
            )
            await ApiAutomationService._write_log_line(
                menu_uuid, result_id, f"请求结果：{res.get('body')}"
            )

            after_list: List[Dict[str, Any]] = []
            if after_ops:
                after_list = await ApiAutomationService._after_request(
                    db=db,
                    ops=after_ops,
                    res=res,
                    header=headers,
                    body=body,
                    env_id=env_id,
                    user_id=user_id,
                )
          
                for idx, op in enumerate(after_ops):
                    if idx < len(after_list) and isinstance(after_list[idx], dict) and "type" not in after_list[idx]:
                        after_list[idx]["type"] = op.get("type")
            after_status = all(int(i.get("status") or 0) == 1 for i in after_list) if after_ops else True
            for item in after_list:
                if item.get("message"):
                    await ApiAutomationService._write_log_line(menu_uuid, result_id, str(item.get("message")))

            assert_list: List[Dict[str, Any]] = []
            if assert_ops:
                assert_list = await ApiAutomationService._handle_assert(
                    db=db,
                    ops=assert_ops,
                    res=res,
                    header=headers,
                    body=body,
                    user_id=user_id,
                )
            assert_status = all(int(i.get("status") or 0) == 1 for i in assert_list) if assert_ops else True
        
            for item in assert_list:
                if int(item.get("type") or 0) == 1:
                    if item.get("message"):
                        await ApiAutomationService._write_log_line(menu_uuid, result_id, str(item.get("message")))
                elif int(item.get("type") or 0) == 4:
                    for sub in item.get("content") or []:
                        if not int(sub.get("status") or 0):
                            if sub.get("message"):
                                await ApiAutomationService._write_log_line(menu_uuid, result_id, str(sub.get("message")))

            res["before"] = before_list
            res["after"] = after_list
            res["assert"] = assert_list

            success = bool(before_status and after_status and assert_status and int(res.get("code") or 0) == 200)

            def _to_kv_list(d: Dict[str, Any]) -> List[Dict[str, Any]]:
                if not d:
                    return []
                return [{"key": k, "value": v, "status": True} for k, v in d.items()]

            req = {
                "params_id": params_id,
                "method": api_cfg.get("method"),
                "body_type": api_cfg.get("body_type"),
                "url": url,
                "header": _to_kv_list(headers),
                "params": _to_kv_list(params),
                "body": body,
                "form_data": _to_kv_list(form_data),
                "form_urlencoded": _to_kv_list(form_urlencoded),
                "file_path": file_paths,
                "assert": api_cfg.get("assert") or [],
                "before": api_cfg.get("before") or [],
                "config": config,
                "after": api_cfg.get("after") or [],
            }

            row = ApiScriptResultModel(
                name=step.get("name") or "",
                uuid=str(step.get("uuid") or ""),
                menu_id=menu_uuid,
                result_id=int(result_id),
                status=1 if success else 0,
                req=req,
                res=res,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(row)
            await db.flush()
            return success, req, res
        except Exception as e:
            await ApiAutomationService._write_log_line(
                menu_uuid, result_id, f"构建请求失败，原因：{str(e)}"
            )
            error_res = {
                "status": 0,
                "message": f"请求接口失败， 原因是：{str(e)}",
                "code": 500,
                "body": {"msg": "接口请求失败", "exception": str(e)},
                "header": {},
                "size": 0,
                "res_time": 0,
            }
            row = ApiScriptResultModel(
                name=step.get("name") or "",
                uuid=str(step.get("uuid") or ""),
                menu_id=menu_uuid,
                result_id=int(result_id),
                status=0,
                req=req,
                res=error_res,
                created_by=user_id,
                updated_by=user_id,
            )
            db.add(row)
            await db.flush()
            return False, req, error_res

    # 结果查询 & 日志
    @staticmethod
    async def get_script_result(db: AsyncSession, result_id: int, user_id: int) -> List[Dict[str, Any]]:
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
    async def get_script_result_list(db: AsyncSession, user_id: int, page: int, page_size: int) -> Dict[str, Any]:
        stmt = (
            select(ApiScriptResultListModel)
            .where(ApiScriptResultListModel.enabled_flag == 1)
            .order_by(ApiScriptResultListModel.id.desc())
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
    async def handle_gitlab_import(db: AsyncSession, apis: List[Dict[str, Any]], service_id: int, user_id: int) -> None:
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

        for i in apis or []:
            if int(i.get("isFolder") or 0) != 1:
                continue
            first_id = await get_or_create_menu(i.get("name") or "", 0, 0)
            for j in i.get("items") or []:
                if int(j.get("isFolder") or 0) != 1:
                    continue
                menu_id = await get_or_create_menu(j.get("name") or "", 1, first_id)
                for k in j.get("items") or []:
                    try:
                        body_type, method = await ApiAutomationService._gitlab_handle_data(k.get("contentType") or "", k.get("httpMethod") or "")
                        params = await ApiAutomationService._gitlab_handle_params(k.get("queryParams") or [])
                        header = await ApiAutomationService._gitlab_handle_header(k.get("headerParams") or [])
                        body = await ApiAutomationService._gitlab_handle_body(k.get("requestParams") or [])
                        url = str(k.get("url") or "/")

                       
                        api_row = (
                            await db.execute(
                                select(ApiModel).where(
                                    ApiModel.enabled_flag == 1,
                                    ApiModel.api_service_id == service_id,
                                    (ApiModel.url == url) | (ApiModel.url == (service_name + url)),
                                )
                            )
                        ).scalar_one_or_none()

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
                            new_url = url if service_name in str(api_row.url) else (service_name + url)
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

        # upsert commonErrorCodes
        for i in body.get("commonErrorCodes") or []:
            code = str(i.get("code") or "")
            msg = str(i.get("msg") or "")
            if not code:
                continue
            row = (
                await db.execute(select(ApiCodeModel).where(ApiCodeModel.code == code, ApiCodeModel.enabled_flag == 1))
            ).scalar_one_or_none()
            if row:
                await db.execute(update(ApiCodeModel).where(ApiCodeModel.id == row.id).values(name=msg, updated_by=user_id))
            else:
                db.add(ApiCodeModel(code=code, name=msg, created_by=user_id, updated_by=user_id))

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
        # 旧逻辑 user_id=1
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