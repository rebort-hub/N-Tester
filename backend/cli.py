#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移等命令行工具
"""

import os
import sys
from enum import Enum
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

# 创建 CLI 应用
app = typer.Typer(
    name="fastapiwebadmin",
    help="FastAPIwebAdmin 命令行工具",
    add_completion=False
)


class EnvironmentEnum(str, Enum):
    """环境枚举"""
    DEV = "dev"
    PROD = "prod"


def parse_db_url(url: str) -> dict:
    """
    安全解析数据库 URL，正确处理密码中的特殊字符（@、: 等）。
    支持 URL 编码的密码，例如 p%40ss%3Aw0rd 会被解码为 p@ss:w0rd。
    """
    from urllib.parse import urlparse, unquote

    # 去掉 driver 前缀，urlparse 只认标准 scheme
    normalized = url.replace("mysql+pymysql://", "mysql://", 1)
    parsed = urlparse(normalized)

    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "dbname": parsed.path.lstrip("/").split("?")[0],
    }


def get_alembic_config() -> Config:
    """获取 Alembic 配置"""
    # Alembic 配置文件路径
    alembic_ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")
    
    # 创建 Alembic 配置对象
    alembic_cfg = Config(alembic_ini_path)
    
    # 设置脚本位置（使用 app/alembic）
    alembic_cfg.set_main_option(
        "script_location",
        os.path.join(os.path.dirname(__file__), "app", "alembic")
    )
    
    return alembic_cfg


@app.command(name="revision", help="生成新的 Alembic 迁移脚本")
def revision(
    message: Annotated[str, typer.Option("--message", "-m", help="迁移描述信息")] = "auto migration",
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev"
) -> None:
    """
    生成新的 Alembic 迁移脚本
    
    示例:
        python cli.py revision -m "add user table"
        python cli.py revision --message "update user model" --env prod
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.echo("  生成 Alembic 迁移脚本")
    typer.echo("=" * 50)
    typer.echo()
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        alembic_cfg = get_alembic_config()
        
        typer.echo(f"环境: {env.value}")
        typer.echo(f"描述: {message}")
        typer.echo()
        typer.echo("正在生成迁移脚本...")
        
        # 对比模型和数据库，生成迁移脚本
        # 等效于: alembic revision --autogenerate -m "message"
        command.revision(alembic_cfg, autogenerate=True, message=message)
        
        typer.echo()
        typer.echo("迁移脚本已生成！")
        typer.echo()
        typer.echo("下一步:")
        typer.echo("  python cli.py upgrade")
        typer.echo()
        
    except Exception as e:
        typer.echo(f"生成迁移脚本失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="upgrade", help="应用最新的 Alembic 迁移")
def upgrade(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
    revision: Annotated[str, typer.Option("--revision", "-r", help="目标版本 (默认: head)")] = "head"
) -> None:
    """
    应用最新的 Alembic 迁移
    
    示例:
        python cli.py upgrade
        python cli.py upgrade --revision ae1027a6acf
        python cli.py upgrade --env prod
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.echo("  应用 Alembic 迁移")
    typer.echo("=" * 50)
    typer.echo()
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        alembic_cfg = get_alembic_config()
        
        typer.echo(f"环境: {env.value}")
        typer.echo(f"目标版本: {revision}")
        typer.echo()
        typer.echo("正在应用迁移...")
        
        # 执行迁移脚本，修改数据库结构
        # 等效于: alembic upgrade head
        command.upgrade(alembic_cfg, revision)
        
        typer.echo()
        typer.echo("所有迁移已应用！")
        typer.echo()
        
    except Exception as e:
        typer.echo(f"应用迁移失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="downgrade", help="回滚 Alembic 迁移")
def downgrade(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
    revision: Annotated[str, typer.Option("--revision", "-r", help="目标版本 (默认: -1)")] = "-1"
) -> None:
    """
    回滚 Alembic 迁移
    
    示例:
        python cli.py downgrade
        python cli.py downgrade -r -2
        python cli.py downgrade --revision ae1027a6acf
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.echo("  回滚 Alembic 迁移")
    typer.echo("=" * 50)
    typer.echo()
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        alembic_cfg = get_alembic_config()
        
        typer.echo(f"环境: {env.value}")
        typer.echo(f"目标版本: {revision}")
        typer.echo()
        
        # 确认操作
        if not typer.confirm("确定要回滚迁移吗？"):
            typer.echo("已取消")
            raise typer.Exit()
        
        typer.echo("正在回滚迁移...")
        
        # 回滚迁移
        # 等效于: alembic downgrade -1
        command.downgrade(alembic_cfg, revision)
        
        typer.echo()
        typer.echo("迁移已回滚！")
        typer.echo()
        
    except Exception as e:
        typer.echo(f"回滚迁移失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="current", help="显示当前迁移版本")
def current(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev"
) -> None:
    """
    显示当前迁移版本
    
    示例:
        python cli.py current
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        alembic_cfg = get_alembic_config()
        
        typer.echo("当前迁移版本:")
        typer.echo()
        
        # 显示当前版本
        # 等效于: alembic current
        command.current(alembic_cfg)
        
    except Exception as e:
        typer.echo(f"获取当前版本失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="history", help="显示迁移历史")
def history(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="显示详细信息")] = False
) -> None:
    """
    显示迁移历史
    
    示例:
        python cli.py history
        python cli.py history --verbose
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        alembic_cfg = get_alembic_config()
        
        typer.echo("迁移历史:")
        typer.echo()
        
        # 显示迁移历史
        # 等效于: alembic history --verbose
        command.history(alembic_cfg, verbose=verbose)
        
    except Exception as e:
        typer.echo(f"获取迁移历史失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="init-db", help="初始化数据库（生成并应用迁移）")
def init_db(
    message: Annotated[str, typer.Option("--message", "-m", help="迁移描述信息")] = "initial migration",
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
    force: Annotated[bool, typer.Option("--force", "-f", help="强制重新初始化")] = False
) -> None:
    """
    初始化数据库（一键完成：检查/创建 alembic + 生成迁移 + 应用迁移）
    
    示例:
        python cli.py init-db
        python cli.py init-db -m "initial setup"
        python cli.py init-db --force
        python cli.py init-db --env prod
    """
    # 验证环境参数
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'，必须是 'dev' 或 'prod'", err=True)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.echo("  初始化数据库")
    typer.echo("=" * 50)
    typer.echo()
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        # 检查 alembic 目录是否存在
        alembic_dir = os.path.join(os.path.dirname(__file__), "app", "alembic")
        if not os.path.exists(alembic_dir):
            typer.echo("检测到 alembic 目录不存在")
            typer.echo("正在自动初始化 Alembic...")
            typer.echo()
            
            # 创建目录结构
            os.makedirs(alembic_dir, exist_ok=True)
            versions_dir = os.path.join(alembic_dir, "versions")
            os.makedirs(versions_dir, exist_ok=True)
            
            # 创建 versions/__init__.py
            with open(os.path.join(versions_dir, "__init__.py"), 'w', encoding='utf-8') as f:
                f.write("# Alembic migrations\n")
            
            # 创建 env.py
            env_py_content = '''from logging.config import fileConfig
import sys
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

# 添加项目根目录到 Python 路径（从 app/alembic 向上两级）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入配置
from config import config as app_config

# this is the Alembic Config object
config = context.config

# 设置数据库 URL（从 .env 读取）
config.set_main_option('sqlalchemy.url', app_config.DATABASE_URI_SYNC)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入模型的 metadata
target_metadata = None

try:
    # 导入 Base 和所有模型
    from app.models.base import Base
    target_metadata = Base.metadata
    

    from app.models import rbac_models, celery_beat_models, api_models
    
    # 导入 AI 模型
    from app.models.ai.conversation import ConversationModel
    from app.models.ai.message import MessageModel
    from app.models.ai.llm_config import LLMConfigModel
    
    # 直接导入模型模块，避免触发 controller 和 service 的导入
    import sys
    import os
    backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, backend_path)
    
    # 导入所有模块的 model.py（只导入模块，不导入具体类）
    # 系统模块
    from app.api.v1.system.user import model as user_model
    from app.api.v1.system.role import model as role_model
    from app.api.v1.system.menu import model as menu_model
    from app.api.v1.system.permission import model as permission_model
    from app.api.v1.system.dept import model as dept_model
    from app.api.v1.system.dict import model as dict_model
    from app.api.v1.system.log import model as log_model
    from app.api.v1.system.file import model as file_model
    from app.api.v1.system.code_generator import model as code_gen_model
    
    # AI 相关模块
    from app.api.v1.ai_intelligence import model as ai_intelligence_model
    
    # 项目管理模块
    from app.api.v1.projects import model as projects_model
    
    # 测试用例模块
    from app.api.v1.testcases import model as testcases_model
    
    # API 测试模块
    from app.api.v1.api_testing import model as api_testing_model
    
    # API 自动化模块
    from app.api.v1.api_automation import model as api_automation_model
    
    # UI 自动化模块
    from app.api.v1.ui_automation import model as ui_automation_model
    
    # APP 管理模块
    from app.api.v1.app_management import model as app_management_model
    
    # APP Mitmproxy 模块
    from app.api.v1.app_mitmproxy import model as app_mitmproxy_model
    
    # Web 管理模块
    from app.api.v1.web_management import model as web_management_model
    
    # 通知模块
    from app.api.v1.notifications import model as notifications_model
    
    # 任务调度模块
    from app.api.v1.task_scheduler import model as task_scheduler_model
    
    # 评审模块
    from app.api.v1.reviews import model as reviews_model
    
    # 助手模块
    from app.api.v1.assistant import model as assistant_model
    
    # 云设备模块
    from app.api.v1.cloud_device import model as cloud_device_model
    
    # 数据工厂模块
    from app.api.v1.data_factory import model as data_factory_model
    
    print(f"成功导入 {len(target_metadata.tables)} 个表")
    
except Exception as e:
    print(f"导入模型失败: {e}")
    print("请确保：")
    print("1. 已安装所有依赖: pip install -r requirements")
    print("2. .env 配置正确")
    print("3. 在虚拟环境中运行")
    import traceback
    traceback.print_exc()
    raise


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
            
            env_py_path = os.path.join(alembic_dir, "env.py")
            with open(env_py_path, 'w', encoding='utf-8') as f:
                f.write(env_py_content)
            
            # 创建 script.py.mako
            script_mako_content = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''
            
            script_mako_path = os.path.join(alembic_dir, "script.py.mako")
            with open(script_mako_path, 'w', encoding='utf-8') as f:
                f.write(script_mako_content)
            
            typer.echo("Alembic 自动初始化完成")
            typer.echo()
        
        alembic_cfg = get_alembic_config()
        
        if force:
            typer.echo("强制模式：将清理旧的迁移文件")
            if not typer.confirm("确定要继续吗？"):
                typer.echo("已取消")
                raise typer.Exit()
            

            versions_dir = os.path.join(os.path.dirname(__file__), "app", "alembic", "versions")
            if os.path.exists(versions_dir):
                import glob
                for file in glob.glob(os.path.join(versions_dir, "*.py")):
                    if not file.endswith("__init__.py"):
                        os.remove(file)
                        typer.echo(f"  删除: {os.path.basename(file)}")
            typer.echo()
        
        # 1. 生成迁移脚本
        typer.echo("[1/2] 生成迁移脚本...")
        command.revision(alembic_cfg, autogenerate=True, message=message)
        typer.echo("迁移脚本已生成")
        typer.echo()
        
        # 2. 应用迁移
        typer.echo("[2/2] 应用迁移...")
        command.upgrade(alembic_cfg, "head")
        typer.echo("迁移已应用")
        typer.echo()
        
        typer.echo("=" * 50)
        typer.echo("数据库初始化完成！")
        typer.echo("=" * 50)
        typer.echo()
        
        # 询问是否导入初始数据
        if typer.confirm("是否导入初始数据（用户、角色、菜单等）？", default=True):
            typer.echo()
            typer.echo("=" * 50)
            typer.echo("  导入初始数据")
            typer.echo("=" * 50)
            typer.echo()
            
            # 调用 seed 命令的逻辑
            import pymysql
            from config import config
            
            # 解析数据库 URL（安全处理特殊字符密码）
            db = parse_db_url(config.DATABASE_URI_SYNC)
            
            # 连接数据库
            conn = pymysql.connect(
                host=db["host"],
                port=db["port"],
                user=db["user"],
                password=db["password"],
                database=db["dbname"],
                charset='utf8mb4'
            )
            cursor = conn.cursor()
            
            # 读取 SQL 文件
            sql_file = os.path.join(os.path.dirname(__file__), "db_script", "db_init.sql")
            
            if os.path.exists(sql_file):
                typer.echo(f"读取 SQL 文件: {sql_file}")
                
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # 提取所有 INSERT 语句
                import re
                insert_statements = re.findall(
                    r'INSERT INTO[^;]+;',
                    sql_content,
                    re.IGNORECASE | re.DOTALL
                )
                
                typer.echo("正在导入数据...")
                success_count = 0
                error_count = 0
                errors = []
                
                for statement in insert_statements:
                    try:
                        cursor.execute(statement)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        if "Duplicate entry" not in str(e):
                            # 记录非重复数据的错误
                            table_match = re.search(r'INSERT INTO `?(\w+)`?', statement, re.IGNORECASE)
                            table_name = table_match.group(1) if table_match else 'unknown'
                            errors.append(f"{table_name}: {str(e)[:100]}")
                
                conn.commit()
                cursor.close()
                conn.close()
                
                typer.echo()
                typer.echo(f"成功导入: {success_count} 条")
                if error_count > 0:
                    typer.echo(f"失败/跳过: {error_count} 条")
                    if errors:
                        typer.echo("\n错误详情:")
                        for err in errors[:10]:  # 只显示前10个错误
                            typer.echo(f"  - {err}")
                        if len(errors) > 10:
                            typer.echo(f"  ... 还有 {len(errors) - 10} 个错误")
                typer.echo()
                typer.echo("=" * 50)
                typer.echo("初始数据导入完成！")
                typer.echo("=" * 50)
                typer.echo()
                typer.echo("默认账号信息:")
                typer.echo("  用户名: admin")
                typer.echo("  密码: 123456")
                typer.echo()
            else:
                typer.echo(f"警告：找不到初始数据文件: {sql_file}")
                typer.echo()
        
        typer.echo("下一步:")
        typer.echo("  python main.py")
        typer.echo()
        
    except Exception as e:
        typer.echo(f"初始化数据库失败: {e}", err=True)
        typer.echo()
        
        # 提供有用的错误提示
        error_msg = str(e)
        if "No module named" in error_msg:
            typer.echo("提示：缺少依赖包")
            typer.echo("   请先安装所有依赖：")
            typer.echo("   pip install -r requirements")
            typer.echo()
        elif "Can't connect" in error_msg or "Access denied" in error_msg:
            typer.echo("提示：数据库连接失败")
            typer.echo("   请检查：")
            typer.echo("   1. MySQL 服务是否启动")
            typer.echo("   2. .env 文件中的数据库配置是否正确")
            typer.echo("   3. 数据库是否已创建")
            typer.echo()
        
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(name="check", help="检查数据库配置")
def check(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev"
) -> None:
    """
    检查数据库配置
    
    示例:
        python cli.py check
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.echo("  检查数据库配置")
    typer.echo("=" * 50)
    typer.echo()
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        # 导入配置
        from config import config
        
        typer.echo("配置文件加载成功")
        typer.echo()
        typer.echo(f"异步数据库 URL: {config.DATABASE_URI[:50]}...")
        typer.echo(f"同步数据库 URL: {config.DATABASE_URI_SYNC[:50]}...")
        typer.echo()
        
        # 测试数据库连接
        typer.echo("测试数据库连接...")
        import pymysql
        
        # 解析数据库 URL（安全处理特殊字符密码）
        db = parse_db_url(config.DATABASE_URI_SYNC)
        
        conn = pymysql.connect(
            host=db["host"],
            port=db["port"],
            user=db["user"],
            password=db["password"],
            database=db["dbname"]
        )
        conn.close()
        
        typer.echo(f"数据库连接成功: {db['dbname']}")
        typer.echo()
        typer.echo("=" * 50)
        typer.echo("所有检查通过！")
        typer.echo("=" * 50)
        
    except Exception as e:
        typer.echo(f"检查失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="seed", help="导入初始数据（种子数据）")
def seed(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
    force: Annotated[bool, typer.Option("--force", "-f", help="强制导入（清空现有数据）")] = False
) -> None:
    """
    导入初始数据（用户、角色、菜单等）
    
    示例:
        python cli.py seed
        python cli.py seed --force
    """
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)
    
    typer.echo("=" * 50)
    typer.echo("  导入初始数据")
    typer.echo("=" * 50)
    typer.echo()
    
    os.environ["ENVIRONMENT"] = env
    
    try:
        # 导入配置
        from config import config
        import pymysql
        
        # 解析数据库 URL（安全处理特殊字符密码）
        db = parse_db_url(config.DATABASE_URI_SYNC)
        
        # 连接数据库
        conn = pymysql.connect(
            host=db["host"],
            port=db["port"],
            user=db["user"],
            password=db["password"],
            database=db["dbname"],
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        
        if user_count > 0 and not force:
            typer.echo(f"数据库中已有 {user_count} 个用户")
            if not typer.confirm("是否继续导入（可能会有重复数据）？"):
                typer.echo("已取消")
                cursor.close()
                conn.close()
                raise typer.Exit()
        
        # 读取 SQL 文件
        sql_file = os.path.join(os.path.dirname(__file__), "db_script", "db_init.sql")
        
        if not os.path.exists(sql_file):
            typer.echo(f"错误：找不到初始数据文件: {sql_file}")
            raise typer.Exit(code=1)
        
        typer.echo(f"读取 SQL 文件: {sql_file}")
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割 SQL 语句（只执行 INSERT 语句）
        typer.echo("正在导入数据...")
        
        # 提取所有 INSERT 语句
        import re
        insert_statements = re.findall(
            r'INSERT INTO[^;]+;',
            sql_content,
            re.IGNORECASE | re.DOTALL
        )
        
        success_count = 0
        error_count = 0
        
        for statement in insert_statements:
            try:
                cursor.execute(statement)
                success_count += 1
            except Exception as e:
                error_count += 1
                if "Duplicate entry" not in str(e):
                    typer.echo(f"警告: {str(e)[:100]}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        typer.echo()
        typer.echo(f"成功导入: {success_count} 条")
        if error_count > 0:
            typer.echo(f"跳过/失败: {error_count} 条（可能是重复数据）")
        typer.echo()
        typer.echo("=" * 50)
        typer.echo("初始数据导入完成！")
        typer.echo("=" * 50)
        typer.echo()
        typer.echo("默认账号信息:")
        typer.echo("  用户名: admin")
        typer.echo("  密码: 123456")
        typer.echo()
        
    except Exception as e:
        typer.echo(f"导入失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
