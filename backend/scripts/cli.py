#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort
"""
数据库迁移命令行工具
"""

import os
import sys
from enum import Enum
from typing import Annotated
import typer
from alembic import command
from alembic.config import Config


_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BACKEND_ROOT)

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
    支持 mysql / postgres / sqlite 驱动前缀。
    """
    from urllib.parse import urlparse, unquote

    normalized = url
    for prefix, scheme in (
        ("mysql+pymysql://", "mysql://"),
        ("mysql+aiomysql://", "mysql://"),
        ("postgresql+psycopg://", "postgresql://"),
        ("postgresql+asyncpg://", "postgresql://"),
        ("sqlite+aiosqlite:///", "sqlite:///"),
    ):
        if normalized.startswith(prefix):
            normalized = scheme + normalized[len(prefix):]
            break

    parsed = urlparse(normalized)
    if parsed.scheme == "sqlite":
        return {
            "host": "",
            "port": 0,
            "user": "",
            "password": "",
            "dbname": parsed.path.lstrip("/") or parsed.netloc,
        }

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
    alembic_ini_path = os.path.join(_BACKEND_ROOT, "alembic.ini")
    
    # 创建 Alembic 配置对象
    alembic_cfg = Config(alembic_ini_path)
    
    # 设置脚本位置（使用 app/alembic）
    alembic_cfg.set_main_option(
        "script_location",
        os.path.join(_BACKEND_ROOT, "app", "alembic")
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
        python scripts/cli.py revision -m "add user table"
        python scripts/cli.py revision --message "update user model" --env prod
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
        
        typer.echo(f"环境: {env}")
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
        typer.echo("  python scripts/cli.py upgrade")
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
        python scripts/cli.py upgrade
        python scripts/cli.py upgrade --revision ae1027a6acf
        python scripts/cli.py upgrade --env prod
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
        
        typer.echo(f"环境: {env}")
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
        python scripts/cli.py downgrade
        python scripts/cli.py downgrade -r -2
        python scripts/cli.py downgrade --revision ae1027a6acf
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
        
        typer.echo(f"环境: {env}")
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
        python scripts/cli.py current
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
        python scripts/cli.py history
        python scripts/cli.py history --verbose
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


@app.command(name="init-db", help="初始化数据库（create_all + 种子，多方言）")
def init_db(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
    yes: Annotated[bool, typer.Option("--yes", "-y", help="非交互确认（兼容旧脚本）")] = False,
) -> None:
    """空库自动建表并导入 sql/seed/*.json；存量库补齐表结构。"""
    _ = yes  # 兼容 portable 等非交互调用
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)

    typer.echo("=" * 50)
    typer.echo("  初始化数据库")
    typer.echo("=" * 50)
    typer.echo()
    os.environ["ENVIRONMENT"] = env

    try:
        import asyncio
        from app.config.setting import config
        from app.scripts.initialize import InitializeData

        typer.echo(f"环境: {env}")
        typer.echo(f"数据库类型: {config.DATABASE_TYPE}")
        typer.echo(f"同步 URI: {config.DATABASE_URI_SYNC}")
        typer.echo()
        asyncio.run(InitializeData().init_db())
        typer.echo()
        typer.echo("数据库初始化完成！")
        typer.echo("默认账号: admin / 123456")
        typer.echo()
    except Exception as e:
        typer.echo(f"初始化数据库失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


@app.command(name="check", help="检查数据库配置")
def check(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
) -> None:
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)

    typer.echo("=" * 50)
    typer.echo("  检查数据库配置")
    typer.echo("=" * 50)
    typer.echo()
    os.environ["ENVIRONMENT"] = env

    try:
        from sqlalchemy import text
        from app.config.setting import config
        from app.core.database import create_sync_engine

        typer.echo(f"DATABASE_TYPE: {config.DATABASE_TYPE}")
        typer.echo(f"异步 URI: {config.DATABASE_URI}")
        typer.echo(f"同步 URI: {config.DATABASE_URI_SYNC}")
        typer.echo()
        typer.echo("测试数据库连接...")
        eng = create_sync_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        eng.dispose()
        typer.echo("数据库连接成功")
        typer.echo("=" * 50)
        typer.echo("所有检查通过！")
    except Exception as e:
        typer.echo(f"检查失败: {e}", err=True)
        raise typer.Exit(code=1)


@app.command(name="seed", help="导入初始数据（JSON 种子，多方言）")
def seed(
    env: Annotated[str, typer.Option("--env", help="运行环境 (dev, prod)")] = "dev",
) -> None:
    """仅写入 sql/seed 中尚未有数据的表（幂等）。"""
    if env not in ["dev", "prod"]:
        typer.echo(f"错误: 无效的环境参数 '{env}'", err=True)
        raise typer.Exit(code=1)

    typer.echo("=" * 50)
    typer.echo("  导入初始数据")
    typer.echo("=" * 50)
    typer.echo()
    os.environ["ENVIRONMENT"] = env

    try:
        import asyncio
        from app.config.setting import config
        from app.scripts.initialize import InitializeData

        typer.echo(f"数据库类型: {config.DATABASE_TYPE}")
        asyncio.run(InitializeData().init_db())
        typer.echo()
        typer.echo("种子导入完成（已有数据的表会自动跳过）")
        typer.echo("默认账号: admin / 123456")
    except Exception as e:
        typer.echo(f"导入失败: {e}", err=True)
        import traceback
        traceback.print_exc()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
