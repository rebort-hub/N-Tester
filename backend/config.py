# -*- coding: utf-8 -*-
# @author: Rebort
import os
import typing

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

project_desc = """
    🎉 N-Tester2.0 接口文档汇总 🎉
    ✨ 账号: admin ✨
    ✨ 密码: 123456 ✨
    ✨ 权限(scopes): admin ✨
"""


class Configs(BaseSettings):
    SERVER_DESC: str = project_desc  # 描述
    SERVER_VERSION: typing.Union[int, str] = 2.0  # 版本
    BASE_URL: AnyHttpUrl = "http://127.0.0.1:8100"  # 开发环境

    API_PREFIX: str = "/api"  # 接口前缀 - v1版本通过路由器添加
    STATIC_DIR: str = 'static'  # 静态文件目录
    GLOBAL_ENCODING: str = 'utf8'  # 全局编码
    CORS_ORIGINS: typing.List[typing.Any] = ["*"]  # 跨域请求

    SECRET_KEY: str = "kPBDjVk0o3Y1wLxdODxBpjwEjo7-Euegg4kdnzFIRjc"  # 密钥(每次重启服务密钥都会改变, token解密失败导致过期, 可设置为常量)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 1  # token过期时间: 60 minutes * 24 hours * 1 days = 1 days

    # redis
    REDIS_URI: str = Field(..., validation_alias="REDIS_URI")  # redis

    # DATABASE_URI: str = "sqlite+aiosqlite:///./sql_app.db?check_same_thread=False"  # Sqlite(异步)
    DATABASE_URI: str = Field(..., validation_alias="MYSQL_DATABASE_URI")  # MySQL(异步)
    DATABASE_URI_SYNC: str = Field(..., validation_alias="MYSQL_DATABASE_URI_SYNC")  # MySQL(同步，用于 Alembic)
    # DATABASE_URI: str = "postgresql+asyncpg://postgres:123456@localhost:5432/postgres"  # PostgreSQL(异步)
    DATABASE_ECHO: bool = False  # 是否打印数据库日志 (可看到创建表、表数据增删改查的信息)

    # logger
    LOGGER_DIR: str = "logs"  # 日志文件夹名
    LOGGER_NAME: str = 'N-Tetser.log'  # 日志文件名  (时间格式 {time:YYYY-MM-DD_HH-mm-ss}.log)
    LOGGER_LEVEL: str = 'INFO'  # 日志等级: ['DEBUG' | 'INFO']
    LOGGER_ROTATION: str = "10 MB"  # 日志分片: 按 时间段/文件大小 切分日志. 例如 ["500 MB" | "12:00" | "1 week"]
    LOGGER_RETENTION: str = "7 days"  # 日志保留的时间: 超出将删除最早的日志. 例如 ["1 days"]

    # dir
    BASEDIR: str = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

    # celery
    broker_url: str = Field(..., validation_alias="CELERY_BROKER_URL")
    result_backend: str = Field(..., validation_alias="CELERY_RESULT_BACKEND")
    accept_content: typing.List[str] = ["json"]
    result_serializer: str = "json"
    timezone: str = "Asia/Shanghai"
    enable_utc: bool = False
    # 并发工作进程/线程/绿色线程执行任务的数量 默认10
    worker_concurrency: int = 10
    # 一次预取多少消息乘以并发进程数 默认4
    worker_prefetch_multiplier: int = 4
    # 池工作进程在被新任务替换之前可以执行的最大任务数。默认是没有限制
    worker_max_tasks_per_child: int = 100
    # 连接池中可以打开的最大连接数 默认10
    broker_pool_limit: int = 10
    # 传递给底层传输的附加选项的字典。设置可见性超时的示例（Redis 和 SQS 传输支持）
    result_backend_transport_options: typing.Dict[str, typing.Any] = {'visibility_timeout': 3600}
    include: typing.List[typing.Any] = [
        'celery_worker.tasks.test_case',
        'celery_worker.tasks.common',
    ]
    # task_queues = (
    #     Queue("case", )
    # )
    TEST_FILES_DIR: str = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'files')

    task_run_pool: int = 3

    # celery beat
    beat_db_uri: str = Field(..., validation_alias="CELERY_BEAT_DB_URL")

    # ================================================= #
    # ******** OAuth 配置 *********** #
    # ================================================= #
    
    # 是否给 OAuth 登录用户授予管理员权限（生产环境建议关闭）
    GRANT_ADMIN_TO_OAUTH_USER: bool = True
    
    # Gitee OAuth
    GITEE_CLIENT_ID: str = Field(default="", validation_alias="GITEE_CLIENT_ID")
    GITEE_CLIENT_SECRET: str = Field(default="", validation_alias="GITEE_CLIENT_SECRET")
    GITEE_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/gitee/callback", validation_alias="GITEE_REDIRECT_URI")
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str = Field(default="", validation_alias="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", validation_alias="GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/github/callback", validation_alias="GITHUB_REDIRECT_URI")
    
    # QQ 互联 OAuth
    QQ_APP_ID: str = Field(default="", validation_alias="QQ_APP_ID")
    QQ_APP_KEY: str = Field(default="", validation_alias="QQ_APP_KEY")
    QQ_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/qq/callback", validation_alias="QQ_REDIRECT_URI")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/google/callback", validation_alias="GOOGLE_REDIRECT_URI")
    
    # 微信开放平台 OAuth
    WECHAT_APP_ID: str = Field(default="", validation_alias="WECHAT_APP_ID")
    WECHAT_APP_SECRET: str = Field(default="", validation_alias="WECHAT_APP_SECRET")
    WECHAT_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/wechat/callback", validation_alias="WECHAT_REDIRECT_URI")
    
    # Microsoft OAuth
    MICROSOFT_CLIENT_ID: str = Field(default="", validation_alias="MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET: str = Field(default="", validation_alias="MICROSOFT_CLIENT_SECRET")
    MICROSOFT_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/microsoft/callback", validation_alias="MICROSOFT_REDIRECT_URI")
    
    # 钉钉 OAuth
    DINGTALK_APP_ID: str = Field(default="", validation_alias="DINGTALK_APP_ID")
    DINGTALK_APP_SECRET: str = Field(default="", validation_alias="DINGTALK_APP_SECRET")
    DINGTALK_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/dingtalk/callback", validation_alias="DINGTALK_REDIRECT_URI")
    
    # 飞书 OAuth
    FEISHU_APP_ID: str = Field(default="", validation_alias="FEISHU_APP_ID")
    FEISHU_APP_SECRET: str = Field(default="", validation_alias="FEISHU_APP_SECRET")
    FEISHU_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/feishu/callback", validation_alias="FEISHU_REDIRECT_URI")
    
    # ================================================= #
    # ******** 邮件配置 *********** #
    # ================================================= #
    EMAIL_HOST: str = Field(default="smtp.qq.com", validation_alias="EMAIL_HOST")
    EMAIL_PORT: int = Field(default=587, validation_alias="EMAIL_PORT")
    EMAIL_USE_TLS: bool = Field(default=True, validation_alias="EMAIL_USE_TLS")
    EMAIL_HOST_USER: str = Field(default="", validation_alias="EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD: str = Field(default="", validation_alias="EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL: str = Field(default="", validation_alias="DEFAULT_FROM_EMAIL")
    
    # ================================================= #
    # ******** AI 平台配置（已废弃） *********** #
    # ================================================= #
    # 注意：以下配置已不再使用！
    # 保留这些字段仅为了向后兼容，避免启动报错
    
    # OpenAI
    OPENAI_API_KEY: str = Field(default="", validation_alias="OPENAI_API_KEY")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", validation_alias="OPENAI_API_BASE")
    
    # Anthropic Claude
    ANTHROPIC_API_KEY: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    
    # 阿里通义千问
    QWEN_API_KEY: str = Field(default="", validation_alias="QWEN_API_KEY")
    
    # 阿里云百炼 DashScope
    DASHSCOPE_API_KEY: str = Field(default="", validation_alias="DASHSCOPE_API_KEY")
    
    # Ollama (本地)
    OLLAMA_HOST: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", env_file_encoding="utf-8", extra="ignore")


config = Configs()
