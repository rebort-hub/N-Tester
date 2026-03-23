from logging.config import fileConfig
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
    
    # 导入模型以便 Alembic 检测
    from app.models import rbac_models, celery_beat_models, api_models
    # 导入云真机模块模型
    from app.api.v1.cloud_device import model as cloud_device_model
    # 导入接口自动化模块模型
    from app.api.v1.api_automation import model as api_automation_model
    # 导入 Web 管理（Web UI 自动化迁移模块）模型
    from app.api.v1.web_management import model as web_management_model
    # 导入 APP 抓包（mitmproxy）迁移模块模型
    from app.api.v1.app_mitmproxy import model as app_mitmproxy_model
    # 导入 APP 自动化（app_management）迁移模块模型
    from app.api.v1.app_management import model as app_management_model
    
    print(f"成功导入 {len(target_metadata.tables)} 个表")
    
except Exception as e:
    print(f"导入模型失败: {e}")
    print("请确保：")
    print("1. 已安装所有依赖: pip install -r requirements")
    print("2. .env 配置正确")
    print("3. 在虚拟环境中运行")
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
