# 后端开发规范与操作手册

## 目录

- [项目概况](#项目概况)
- [技术栈](#技术栈)
- [项目目录结构](#项目目录结构)
- [分层架构详解](#分层架构详解)
- [核心基础设施](#核心基础设施)
- [环境准备](#环境准备)
- [开发新功能：完整流程](#开发新功能完整流程)
- [命名规范](#命名规范)
- [权限系统](#权限系统)
- [常见模式速查](#常见模式速查)
- [禁止事项](#禁止事项)
- [Alembic 数据库迁移](#alembic-数据库迁移)
- [常用命令速查](#常用命令速查)
- [版本混乱排查](#版本混乱排查)
- [菜单管理](#菜单管理)

---

## 项目概况

| 项目 | 说明 |
|------|------|
| 框架 | FastAPI + SQLAlchemy (async) + Alembic |
| 数据库 | MySQL |
| 迁移工具 | Alembic（配置文件：`alembic.ini`） |
| 迁移文件目录 | `app/alembic/versions/` |
| 当前 Head Revision | `9f0791a8bfdf`（initial_migration，整合了历史所有表结构） |

> **重要背景**：历史多个迁移文件已被合并为单个 `initial_migration`（revision: `9f0791a8bfdf`）。
> 若数据库 `alembic_version` 表中存储的是旧 revision id，需手动修正后再执行升级，见 [版本混乱排查](#版本混乱排查)。

---

## 技术栈

| 组件 | 库 / 版本说明 |
|------|--------------|
| Web 框架 | FastAPI（全异步） |
| ORM | SQLAlchemy（async） + aiomysql（Windows） |
| 数据验证 | Pydantic v2 |
| 数据库迁移 | Alembic |
| 异步任务 | Celery + Redis Broker |
| 缓存 | Redis |
| 日志 | loguru |
| 配置管理 | pydantic_settings（读取 `.env`） |
| CLI 工具 | Typer（`cli.py`） |

---

## 项目目录结构

```
backend/
├── app/
│   ├── alembic/                # Alembic 迁移环境
│   │   ├── env.py              # 迁移运行入口，需在此注册新模型
│   │   └── versions/           # 自动生成的迁移脚本
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py     # 路由总注册文件（新模块必须在此注册）
│   │       ├── system/         # 系统模块（用户/角色/权限/菜单/部门）
│   │       ├── [业务模块]/     # 各业务功能模块，见分层说明
│   │       └── business/
│   │           └── example/    # 权限使用示例，开发前必读
│   ├── common/
│   │   ├── response.py         # 统一响应函数（success_response / error_response）
│   │   └── enums.py            # 全局枚举定义
│   ├── core/
│   │   ├── base_crud.py        # BaseCRUD 泛型基类（所有 CRUD 继承）
│   │   ├── base_model.py       # TimestampMixin / AuditMixin
│   │   ├── base_schema.py      # BaseSchema / TimestampSchema / PageSchema
│   │   ├── dependencies.py     # FastAPI 依赖：get_current_user_id
│   │   ├── permission.py       # API 权限装饰器
│   │   └── data_permission.py  # 数据权限过滤
│   ├── db/
│   │   ├── sqlalchemy.py       # 异步引擎、get_db 依赖、事务装饰器
│   │   └── redis.py            # Redis 客户端
│   └── models/
│       ├── base.py             # Base（所有模型继承自此）
│       ├── rbac_models.py      # RBAC 相关模型
│       └── api_models.py       # 通用 API 模型
├── celery_worker/              # Celery 异步任务
├── db_script/
│   └── db_init.sql             # 全量初始化 SQL（新部署时使用）
├── config.py                   # 全局配置（pydantic_settings，读 .env）
├── cli.py                      # 命令行工具（数据库初始化/迁移）
├── main.py                     # FastAPI 应用入口
├── alembic.ini                 # Alembic 配置
└── .env                        # 环境变量（不提交 Git）
```

---

## 分层架构详解

每个业务模块位于 `app/api/v1/<模块名>/`，固定包含以下文件，**职责严格分离**：

```
app/api/v1/<module_name>/
├── __init__.py      # 导出 router（供 v1/__init__.py 注册）
├── model.py         # 数据库模型（SQLAlchemy ORM）
├── schema.py        # 数据契约（Pydantic 校验/序列化）
├── controller.py    # 路由处理（FastAPI APIRouter）
├── service.py       # 业务逻辑层
└── crud.py          # 数据访问层
```

### 各层职责

| 层 | 文件 | 职责 | 禁止做的事 |
|----|------|------|-----------|
| **Model** | `model.py` | 定义表结构 | 不写业务逻辑 |
| **Schema** | `schema.py` | 入参校验、出参序列化 | 不访问数据库 |
| **Controller** | `controller.py` | 接收请求、调用 Service、返回响应 | 不直接操作数据库 |
| **Service** | `service.py` | 核心业务逻辑、编排 CRUD | 不直接执行 SQL |
| **CRUD** | `crud.py` | 封装数据库查询操作 | 不写业务判断 |

---

## 核心基础设施

### Base 模型（`app/models/base.py`）

所有数据库模型**必须继承 `Base`**，它自动提供以下公共字段：

```python
id            BigInteger   # 主键，自增
creation_date DateTime     # 创建时间（自动填充）
created_by    BigInteger   # 创建人 ID（业务层手动赋值）
updation_date DateTime     # 更新时间（自动更新）
updated_by    BigInteger   # 更新人 ID（业务层手动赋值）
enabled_flag  Boolean      # 软删除标志：1=正常，0=已删除
trace_id      String(255)  # 链路追踪 ID
```

**软删除约定**：删除操作设置 `enabled_flag=0`，所有查询必须过滤 `enabled_flag==1`。

### BaseCRUD（`app/core/base_crud.py`）

泛型基类，提供标准 CRUD 方法，业务 CRUD 类继承后即可使用：

```python
from app.core.base_crud import BaseCRUD

class MyModelCRUD(BaseCRUD[MyModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(MyModel, db)
    # 自动继承以下方法：
    # await crud.get_by_id_crud(id)         -> Model | None
    # await crud.get_list_crud(conditions, order_by, skip, limit) -> (list, total)
    # await crud.create_crud(data_dict)     -> Model
    # await crud.update_crud(id, data_dict) -> Model
    # await crud.delete_crud([id1, id2])    -> None（硬删除）
    # await crud.soft_delete_crud([id])     -> None（软删除，推荐）
```

### Schema 基类（`app/core/base_schema.py`）

| 基类 | 用途 |
|------|------|
| `BaseSchema` | 所有 Schema 的基类，启用 `from_attributes=True` |
| `TimestampSchema` | 输出 Schema 继承，包含创建/更新时间字段 |
| `PageSchema[T]` | 分页响应包装 |

### 统一响应（`app/common/response.py`）

**所有接口必须使用以下函数返回**，禁止直接返回裸字典：

```python
from app.common.response import success_response, error_response, page_response

return success_response(data=result, message="创建成功")
return error_response(message="资源不存在", code=404)
return page_response(items=items, total=total, page=page, page_size=page_size)
```

响应格式固定为：`{ "code": 200, "message": "操作成功", "data": { ... } }`

### 数据库会话（`app/db/sqlalchemy.py`）

在 Controller 中通过 FastAPI 依赖注入获取会话，自动处理 commit/rollback/close：

```python
from app.db.sqlalchemy import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def my_endpoint(db: AsyncSession = Depends(get_db)):
    ...
```

---

## 环境准备

### PyCharm 终端建议使用 cmd

PyCharm 默认使用 PowerShell，可能不继承完整系统 PATH（如 mysql 命令找不到）。

> Settings → Tools → Terminal → Shell path → 改为 `C:\Windows\System32\cmd.exe`

或在 PowerShell 终端输入 `cmd` 临时切换。

### 激活虚拟环境

```cmd
.venv\Scripts\activate
```

### `.env` 数据库配置

`DB_PASSWORD` 填写**原始明文密码**，代码内部会自动 URL 编码，不要手动编码：

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=My@Password.   # 直接填原始密码，含 @ 也不用写成 %40
DB_NAME=ntest_platform2
```

---

## 开发新功能：完整流程

### 场景一：新增业务模块（有新表结构）

**第 1 步：创建模块目录**

```
app/api/v1/my_feature/
├── __init__.py
├── model.py
├── schema.py
├── controller.py
├── service.py
└── crud.py
```

**第 2 步：定义数据库模型（`model.py`）**

```python
from sqlalchemy import Column, BigInteger, String, Text, Boolean, Integer
from app.models.base import Base

class MyFeatureModel(Base):
    __tablename__ = 'my_features'     # 小写下划线，复数

    project_id  = Column(BigInteger, nullable=False, comment='关联项目ID', index=True)
    name        = Column(String(200), nullable=False, comment='名称')
    description = Column(Text, comment='描述')
    status      = Column(String(20), default='PENDING', comment='状态')
    is_active   = Column(Boolean, default=True, comment='是否启用')
    order_num   = Column(Integer, default=0, comment='排序')
    # id / creation_date / enabled_flag 等公共字段由 Base 自动提供，无需重复定义
```

**第 3 步：定义 Schema（`schema.py`）**

每个资源固定三类：Create / Update / Out

```python
from typing import Optional
from pydantic import BaseModel, Field
from app.core.base_schema import TimestampSchema, BaseSchema

class MyFeatureCreateSchema(BaseModel):
    project_id:  int            = Field(..., description='关联项目ID')
    name:        str            = Field(..., max_length=200, description='名称')
    description: Optional[str] = Field(None, description='描述')

class MyFeatureUpdateSchema(BaseModel):       # 所有字段可选
    name:        Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None

class MyFeatureOutSchema(TimestampSchema):    # 继承带时间字段
    id:          int
    project_id:  int
    name:        str
    description: Optional[str] = None

class MyFeaturePageSchema(BaseSchema):
    total: int;  page: int;  page_size: int
    items: list[MyFeatureOutSchema]
```

**第 4 步：实现 CRUD（`crud.py`）** *(按需创建)*

> **什么情况需要 crud.py？**
>
> `BaseCRUD` 已提供五个通用方法（按 ID 查、分页查、创建、更新、删除）。**只有当这五个方法不够用时，才需要新建 crud.py 继承 `BaseCRUD` 并扩展自定义方法**：
>
> | 需要扩展的场景 | 举例 |
> |--------------|------|
> | 按非 ID 字段查询 | 按 `project_id` 分页、按 `name` 查唯一记录 |
> | 多表 JOIN 查询 | 查项目同时带出成员列表 |
> | 复杂条件/树形结构 | 多字段动态筛选、递归查子集合 |
> | 同一查询逻辑多处复用 | 两个 service 方法都需要同一个条件组合 |
>
> 如果 `BaseCRUD` 的五个方法能满足需求，直接在 service 里用 `BaseCRUD(MyModel, db).create_crud(...)` 即可，不必新建 crud.py。

```python
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.core.base_crud import BaseCRUD
from .model import MyFeatureModel

class MyFeatureCRUD(BaseCRUD[MyFeatureModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(MyFeatureModel, db)

    async def get_by_project(
        self, project_id: int, skip: int = 0, limit: int = 20
    ) -> Tuple[List[MyFeatureModel], int]:
        cond = [
            self.model.project_id == project_id,
            self.model.enabled_flag == 1        # 必须过滤软删除
        ]
        total = (await self.db.execute(
            select(func.count(self.model.id)).where(and_(*cond))
        )).scalar() or 0
        items = (await self.db.execute(
            select(self.model).where(and_(*cond)).offset(skip).limit(limit)
        )).scalars().all()
        return list(items), total
```

**第 5 步：实现 Service（`service.py`）**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from .crud import MyFeatureCRUD
from .schema import MyFeatureCreateSchema, MyFeatureUpdateSchema, MyFeatureOutSchema

class MyFeatureService:

    @staticmethod
    async def create(db, data: MyFeatureCreateSchema, user_id: int):
        crud = MyFeatureCRUD(db)
        obj = await crud.create_crud({**data.model_dump(), 'created_by': user_id})
        return MyFeatureOutSchema.model_validate(obj).model_dump()

    @staticmethod
    async def get_list(db, project_id: int, page: int, page_size: int):
        crud = MyFeatureCRUD(db)
        items, total = await crud.get_by_project(
            project_id, skip=(page - 1) * page_size, limit=page_size
        )
        return {
            'items': [MyFeatureOutSchema.model_validate(i).model_dump() for i in items],
            'total': total, 'page': page, 'page_size': page_size
        }

    @staticmethod
    async def get_detail(db, item_id: int):
        obj = await MyFeatureCRUD(db).get_by_id_crud(item_id)
        if not obj or not obj.enabled_flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='资源不存在')
        return MyFeatureOutSchema.model_validate(obj).model_dump()

    @staticmethod
    async def update(db, item_id: int, data: MyFeatureUpdateSchema, user_id: int):
        obj = await MyFeatureCRUD(db).update_crud(
            item_id, {**data.model_dump(exclude_unset=True), 'updated_by': user_id}
        )
        return MyFeatureOutSchema.model_validate(obj).model_dump()

    @staticmethod
    async def delete(db, item_id: int, user_id: int):
        await MyFeatureCRUD(db).soft_delete_crud([item_id])   # 软删除
```

**第 6 步：实现 Controller（`controller.py`）**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.sqlalchemy import get_db
from app.common.response import success_response
from app.core.dependencies import get_current_user_id
from .schema import MyFeatureCreateSchema, MyFeatureUpdateSchema
from .service import MyFeatureService

router = APIRouter(prefix="/my_feature", tags=["我的新功能"])

@router.post("", summary="创建")
async def create(data: MyFeatureCreateSchema, db: AsyncSession = Depends(get_db),
                 user_id: int = Depends(get_current_user_id)):
    return success_response(data=await MyFeatureService.create(db, data, user_id), message="创建成功")

@router.get("", summary="列表（分页）")
async def get_list(project_id: int = Query(...), page: int = Query(1, ge=1),
                   page_size: int = Query(20, ge=1, le=200),
                   db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return success_response(data=await MyFeatureService.get_list(db, project_id, page, page_size))

@router.get("/{item_id}", summary="详情")
async def get_detail(item_id: int, db: AsyncSession = Depends(get_db),
                     user_id: int = Depends(get_current_user_id)):
    return success_response(data=await MyFeatureService.get_detail(db, item_id))

@router.put("/{item_id}", summary="更新")
async def update(item_id: int, data: MyFeatureUpdateSchema, db: AsyncSession = Depends(get_db),
                 user_id: int = Depends(get_current_user_id)):
    return success_response(data=await MyFeatureService.update(db, item_id, data, user_id), message="更新成功")

@router.delete("/{item_id}", summary="删除")
async def delete(item_id: int, db: AsyncSession = Depends(get_db),
                 user_id: int = Depends(get_current_user_id)):
    await MyFeatureService.delete(db, item_id, user_id)
    return success_response(message="删除成功")
```

**第 7 步：注册路由（`app/api/v1/__init__.py`）**

```python
from app.api.v1.my_feature.controller import router as my_feature_router
# ...
router.include_router(my_feature_router, tags=["我的新功能"])
```

**第 8 步：注册模型到 Alembic（`app/alembic/env.py`）**

在 `try` 块内的模型导入区域追加：

```python
from app.api.v1.my_feature import model as my_feature_model
```

**第 9 步：生成并执行数据库迁移**

```bash
python cli.py revision -m "add my_feature table"
python cli.py upgrade

# 全新部署时也可直接全量初始化
python cli.py init-db
```

---

### 场景二：仅新增菜单（无表结构变化）

```
1. 手动创建迁移文件（不用 autogenerate）
       alembic revision -m "add_{模块名}_menus"
   或直接复制已有菜单迁移文件修改

2. 在迁移文件中编写 INSERT SQL（见下方菜单迁移文件模板）

3. 执行迁移
       alembic upgrade head

4. 同步更新 db_script/db_init.sql
   在文件末尾对应位置追加相同的 INSERT 语句
   （db_init.sql 用于全新部署初始化，必须与迁移保持一致）

5. 提交代码
```

### 场景三：修改已有接口/业务逻辑（无表结构变化）

```
直接修改代码，无需迁移操作，重启服务即可生效。
```

### 场景四：修改已有表字段

```
1. 修改对应 model.py 中的字段定义
2. 生成迁移文件
       alembic revision --autogenerate -m "alter_{表名}_{字段说明}"
3. 检查并执行
       alembic upgrade head
```

---

## 命名规范

### 文件与目录

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块目录 | `snake_case` | `api_testing/`, `web_management/` |
| Python 文件 | `snake_case.py` | `model.py`, `base_crud.py` |
| 数据库表名 | `snake_case`（复数） | `api_projects`, `my_features` |

### 类名

| 类型 | 规范 | 示例 |
|------|------|------|
| 模型类 | `{名称}Model` | `APIProjectModel` |
| CRUD 类 | `{名称}CRUD` | `APIProjectCRUD` |
| Service 类 | `{名称}Service` | `APIProjectService` |
| 创建 Schema | `{名称}CreateSchema` | `APIProjectCreateSchema` |
| 更新 Schema | `{名称}UpdateSchema` | `APIProjectUpdateSchema` |
| 输出 Schema | `{名称}OutSchema` | `APIProjectOutSchema` |
| 分页 Schema | `{名称}PageSchema` | `APIProjectPageSchema` |

### API 路由

- 路径全小写 + 下划线或连字符：`/api_testing`、`/ssl-certificates`
- 资源集合用复数：`/projects`、`/users`
- 操作用 HTTP 动词：`GET`/`POST`/`PUT`/`DELETE`
- 特殊操作用 `POST /{id}/action`：`/test_suites/{id}/execute`

---

## 权限系统

### 仅验证登录（推荐大多数接口）

```python
from app.core.dependencies import get_current_user_id

user_id: int = Depends(get_current_user_id)
```

### 验证 API 权限（需要细粒度控制时）

```python
from app.api.v1.system.auth.dependencies import require_api_permission, require_any_api_permission

# 单权限
current_user = Depends(require_api_permission("module:resource:action"))

# 多权限之一即可
current_user = Depends(require_any_api_permission("module:admin:op", "module:user:op"))
```

权限字符串格式：`模块:资源:操作`，例如 `business:user:list`、`api_testing:project:delete`。

### 数据权限（跨部门/租户场景）

```python
from app.core.data_permission import apply_data_permission

stmt = select(MyModel).where(MyModel.status == 1)
stmt = await apply_data_permission(stmt, MyModel, db, current_user)
```

详见 `app/api/v1/business/example/controller.py` 完整示例。

---

## 常见模式速查

### 分页查询

```python
# CRUD 层
items, total = await crud.get_list_crud(
    conditions=[MyModel.enabled_flag == 1],
    skip=(page - 1) * page_size,
    limit=page_size
)

# Service 层返回
return {
    'items': [MyOutSchema.model_validate(i).model_dump() for i in items],
    'total': total, 'page': page, 'page_size': page_size
}
```

### 存在性检查

```python
obj = await crud.get_by_id_crud(item_id)
if not obj or not obj.enabled_flag:
    raise HTTPException(status_code=404, detail="资源不存在")
```

### Schema 序列化

```python
MyOutSchema.model_validate(model_obj).model_dump()      # Model -> Dict（输出）
data.model_dump()                                        # Schema -> Dict（创建）
data.model_dump(exclude_unset=True)                      # 仅含用户传入字段（更新）
```

### 异步事务（非路由场景）

```python
from app.db.sqlalchemy import content_transaction

async with content_transaction() as session:
    # 自动 commit 或 rollback
    ...
```

---

## 禁止事项

| 禁止 | 原因 |
|------|------|
| Controller 层直接写 SQL 或调用 ORM | 违反分层原则，难以维护 |
| 查询时不过滤 `enabled_flag == 1` | 会查出软删除的数据 |
| 硬删除（`delete_crud`）业务数据 | 统一使用软删除 `soft_delete_crud` |
| Schema 中直接操作数据库 | Schema 只做数据验证和序列化 |
| 直接返回裸字典而不用 `success_response` | 响应格式不统一，前端解析失败 |
| `.env` 中 `DB_PASSWORD` 填 URL 编码后的密码 | 会被代码再次编码，导致认证失败 |
| 修改已执行的迁移文件 | 已应用的迁移不可变，必须新建迁移 |
| 新模型不在 `env.py` 中 import | Alembic 自动生成迁移时检测不到新表 |
| 在 `app/api/v1/__init__.py` 漏注册路由 | 接口不可访问 |
| model.py 中重复定义 `id` / `enabled_flag` 等公共字段 | Base 已提供，重复定义会报错 |

---

## Alembic 数据库迁移

### 迁移文件结构

```python
# app/alembic/versions/20260408_1200_add_performance_menus.py

"""add performance menus

Revision ID: a1b2c3d4e5f7        ← 当前文件的唯一标识
Revises: 9f0791a8bfdf             ← 上一个迁移的 revision id（必须正确！）
Create Date: 2026-04-08 12:00:00
"""
from alembic import op

revision = 'a1b2c3d4e5f7'
down_revision = '9f0791a8bfdf'    # 必须是已存在的 revision id
branch_labels = None
depends_on = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
```

### 菜单迁移文件模板

```python
from alembic import op

NOW = '2026-04-08 12:00:00'

def upgrade() -> None:
    # 1. 先插入父目录（menu_type='M', parent_id=0）
    op.execute(f"""
        INSERT INTO `sys_menu`
        (menu_name, menu_type, parent_id, path, component, query, perms, icon,
         order_num, visible, status, is_frame, is_cache, remark,
         id, creation_date, created_by, updation_date, updated_by,
         enabled_flag, trace_id, created_at, updated_at)
        VALUES
        ('模块名称', 'M', 0, '/route-path', 'Layout', NULL, NULL, 'ele-IconName',
         排序号, 1, 1, 1, 0, '模块备注',
         菜单ID, '{NOW}', 1, '{NOW}', 1, 1, NULL, '{NOW}', '{NOW}')
    """)

    # 2. 插入子页面（menu_type='C'）
    op.execute(f"""
        INSERT INTO `sys_menu`
        (menu_name, menu_type, parent_id, path, component, query, perms, icon,
         order_num, visible, status, is_frame, is_cache, remark,
         id, creation_date, created_by, updation_date, updated_by,
         enabled_flag, trace_id, created_at, updated_at)
        VALUES
        ('子菜单名', 'C', 父目录ID, '/route-path/sub', 'views路径/index', NULL,
         'module:resource:action', 'ele-IconName',
         1, 1, 1, 1, 0, '子菜单备注',
         子菜单ID, '{NOW}', 1, '{NOW}', 1, 1, NULL, '{NOW}', '{NOW}')
    """)

def downgrade() -> None:
    op.execute("DELETE FROM `sys_menu` WHERE id IN (父目录ID, 子菜单ID, ...)")
```

### 菜单字段说明

| 字段 | 类型值 | 说明 |
|------|--------|------|
| menu_type | M | 目录（侧边栏分组，不可点击） |
| menu_type | C | 页面菜单（可点击，有路由） |
| menu_type | F | 按钮权限（不显示在菜单，用于接口鉴权） |
| parent_id | 0 | 顶级目录 |
| component | `Layout` | menu_type=M 时填此值 |
| component | `views路径/index` | 对应 frontend/src/views/ 下的相对路径（不含 .vue） |
| is_frame | 1 | 内部路由（正常情况） |
| visible | 1/0 | 显示/隐藏 |
| status | 1/0 | 启用/停用 |
| enabled_flag | 1 | 逻辑未删除（必须为 1） |

### 菜单 ID 分配记录

> 新增菜单时，ID 不能与已有 ID 冲突，按以下区间分配：

| 区间 | 用途 |
|------|------|
| 1 – 99 | 系统管理（用户/角色/菜单/权限等） |
| 100 – 199 | AI 管理 |
| 110 – 199 | 项目管理 |
| 200 – 999 | 测试管理（API/UI/用例等） |
| 1000 – 4099 | 其他业务模块 |
| 4100 – 4133 | App 测试管理 |
| **4200 – 4299** | **性能测试模块（当前已用 4200-4206）** |
| 4300 + | 后续新模块 |

---

## 常用命令速查

```cmd
:: 查看数据库当前版本
alembic current

:: 查看完整迁移历史链
alembic history --verbose

:: 升级到最新版本
alembic upgrade head

:: 升级指定步数
alembic upgrade +1

:: 回滚到上一版本（开发调试用）
alembic downgrade -1

:: 回滚到指定版本
alembic downgrade <revision_id>

:: 生成迁移文件（有 Model 变更）
alembic revision --autogenerate -m "简短描述"

:: 生成空迁移文件（手写 SQL，如菜单数据）
alembic revision -m "简短描述"

:: 强制标记当前版本（不执行迁移内容，仅修改版本记录）
alembic stamp <revision_id>

:: 标记为最新版本
alembic stamp head
```

---

## 版本混乱排查

### 症状

```
ERROR: Can't locate revision identified by 'xxxxxxxx'
```

### 原因

数据库 `alembic_version` 表记录的 revision id，在本地迁移文件中找不到。
通常发生在：历史迁移文件被合并/删除后，数据库里还保留旧 id。

### 修复步骤

**步骤 1：确认当前 head revision**

```cmd
alembic history
```

当前 head: `9f0791a8bfdf`（initial_migration）

**步骤 2：查看数据库中记录的版本**

```cmd
:: 方式一：cmd 中（需 mysql 在 PATH 中）
mysql -u root -p 数据库名 -e "SELECT * FROM alembic_version;"

:: 方式二：Python 脚本（任何终端均可）
python -c "
from config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings.DATABASE_URI_SYNC)
with engine.connect() as conn:
    print(conn.execute(text('SELECT * FROM alembic_version')).fetchall())
"
```

**情况 A：只有一行，但 revision id 不在本地迁移文件中** → 执行步骤 3

**情况 B：有多行，包含孤立旧 revision（脏数据）**

```
+--------------+
| version_num  |
+--------------+
| 7b11cf4447c0 |   ← 孤立的旧版本，本地已无对应文件（脏数据）
| 9f0791a8bfdf |   ← 正确版本
+--------------+
```

直接删除孤立行（`alembic_version` 只存书签，删除不影响任何业务数据）：

```cmd
mysql -u root -p 数据库名 -e "DELETE FROM alembic_version WHERE version_num='7b11cf4447c0';"
```

清理后直接跳到步骤 4，无需执行步骤 3。

**步骤 3：修正版本记录（仅情况 A）**

```cmd
:: 方式一
mysql -u root -p 数据库名 -e "UPDATE alembic_version SET version_num='9f0791a8bfdf';"

:: 方式二：Python 脚本
python -c "
from config import settings
from sqlalchemy import create_engine, text
engine = create_engine(settings.DATABASE_URI_SYNC)
with engine.connect() as conn:
    conn.execute(text(\"UPDATE alembic_version SET version_num='9f0791a8bfdf'\"))
    conn.commit()
    print('version updated')
"
```

**步骤 4：正常升级**

```cmd
alembic upgrade head
```

### 全新部署（无历史数据）

```cmd
:: 1. 初始化数据库（执行 db_init.sql）
mysql -u root -p 数据库名 < db_script/db_init.sql

:: 2. 标记为当前最新版本（数据已通过 SQL 导入，无需再执行迁移）
alembic stamp head
```

### 场景：只执行部分迁移（跳过已手动录入的种子数据）

当 `versions/` 目录有 **两条待执行迁移**，但后一条的数据已通过后台手动录入时，
不能直接 `alembic upgrade head`（会重复插入数据），正确做法如下：

**背景示例**

| 顺序 | Revision | 说明 |
|------|----------|------|
| 1st  | `f1a2b3c4d5e6` | 建表（需执行） |
| 2nd  | `g2b3c4d5e6f7` | 种子数据（**跳过**，已手动录入） |

**步骤**

```cmd
:: 第 1 步：确认当前版本（仅用于核对，可跳过）
alembic current

:: 第 2 步：升级到第一个迁移（指定 revision id，不用 head）
alembic upgrade f1a2b3c4d5e6

:: 第 3 步：将第二个迁移标记为"已执行"（只写版本号，不执行 upgrade() 内容）
alembic stamp g2b3c4d5e6f7

:: 第 4 步：验证结果，应输出 g2b3c4d5e6f7 (head)
alembic current
```

> **关键点**
> - `alembic upgrade <revision_id>` 只升级到指定版本，不继续往后执行。
> - `alembic stamp <revision_id>` 仅在 `alembic_version` 表写入版本号，**不执行**对应迁移文件的 `upgrade()` 函数，相当于告诉 Alembic"此版本已就绪"。
> - 执行后 `alembic current` 显示 `g2b3c4d5e6f7 (head)`，后续 `alembic upgrade head` 不会再触发这两条迁移。

---

## 菜单管理

### 新增菜单后前端为何不生效

菜单由后端数据库驱动，前端首次加载时会缓存到 SessionStorage。
**新增菜单后，需要重新登录或清除浏览器缓存**才能看到新菜单。

### 为角色分配新菜单权限

菜单插入数据库后，默认没有分配给任何角色，需要在系统管理中操作：

```
系统管理 → 角色管理 → 选择角色 → 分配权限 → 勾选新增菜单 → 保存
```

或直接执行 SQL（批量分配给指定角色）：

```sql
-- 将菜单 4200-4206 分配给 role_id=1 的角色（通常是超级管理员）
INSERT INTO sys_role_menu (role_id, menu_id) VALUES
(1, 4200), (1, 4201), (1, 4202), (1, 4203), (1, 4204), (1, 4205), (1, 4206);
```

### 前端组件路径规范

| DB component 字段 | 对应前端文件 |
|-------------------|-------------|
| `testing/performance/config/index` | `src/views/testing/performance/config/index.vue` |
| `system/user/index` | `src/views/system/user/index.vue` |
| `Layout` | 框架布局组件（目录节点专用） |

---

*最后更新：2026-04-14*