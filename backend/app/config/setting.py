# -*- coding: utf-8 -*-
# @author: Rebort
"""应用配置"""
import os
import typing
from pathlib import Path
from pydantic import AnyHttpUrl, Field, AliasChoices, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from app.config.db_url import build_redis_url, build_sqlalchemy_url
from app.config.path_conf import BACKEND_ROOT

project_desc = """
    🎉 N-Tester2.0.1 接口文档汇总 🎉
    ✨ 账号: admin ✨
    ✨ 密码: 123456 ✨
    ✨ 权限(scopes): admin ✨
"""


class Configs(BaseSettings):
    # ================================================= #
    # ******** 服务 *********** #
    # ================================================= #
    SERVER_DESC: str = project_desc
    SERVER_VERSION: typing.Union[int, str] = 2.0
    BASE_URL: AnyHttpUrl = Field(default="http://127.0.0.1:8100", validation_alias="BASE_URL")
    FRONTEND_BASE_URL: str = Field(default="", validation_alias="FRONTEND_BASE_URL")
    API_PREFIX: str = "/api"
    STATIC_DIR: str = "static"
    GLOBAL_ENCODING: str = "utf8"
    CORS_ORIGINS: typing.List[typing.Any] = ["*"]
    BASEDIR: str = str(BACKEND_ROOT.parent)
    ENVIRONMENT: str = Field(default="dev", validation_alias="ENVIRONMENT")
    DB_AUTO_INIT: bool = Field(default=True, validation_alias="DB_AUTO_INIT")

    # ================================================= #
    # ******** 安全 / JWT *********** #
    # ================================================= #
    SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, validation_alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # ================================================= #
    # ******** Redis *********** #
    # ================================================= #
    REDIS_URI: str = Field(default="", validation_alias="REDIS_URI")
    REDIS_HOST: str = Field(default="", validation_alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, validation_alias="REDIS_PORT")
    REDIS_USER: str = Field(default="", validation_alias="REDIS_USER")
    REDIS_PASSWORD: str = Field(default="", validation_alias="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=4, validation_alias="REDIS_DB")

    # ================================================= #
    # ******** 数据库 *********** #
    # ================================================= #
    # mysql-3306 / postgres-5432 / sqlite（sqlite 时 DATABASE_NAME 为文件名）
    DATABASE_TYPE: typing.Literal["mysql", "postgres", "sqlite"] = Field(
        default="mysql",
        validation_alias=AliasChoices("DATABASE_TYPE", "DB_TYPE"),
    )
    DATABASE_HOST: str = Field(
        default="localhost",
        validation_alias=AliasChoices("DATABASE_HOST", "DB_HOST"),
    )
    DATABASE_PORT: int = Field(
        default=3306,
        validation_alias=AliasChoices("DATABASE_PORT", "DB_PORT"),
    )
    DATABASE_USER: str = Field(
        default="root",
        validation_alias=AliasChoices("DATABASE_USER", "DB_USER"),
    )
    DATABASE_PASSWORD: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_PASSWORD", "DB_PASSWORD"),
    )
    DATABASE_NAME: str = Field(
        default="ntester",
        validation_alias=AliasChoices("DATABASE_NAME", "DB_NAME"),
    )
    # 兼容旧部署：完整 URI 优先于拆字段
    DATABASE_URI: str = Field(default="", validation_alias="MYSQL_DATABASE_URI")
    DATABASE_URI_SYNC: str = Field(default="", validation_alias="MYSQL_DATABASE_URI_SYNC")
    DATABASE_ECHO: bool = False
    POOL_SIZE: int = 10
    MAX_OVERFLOW: int = 20
    POOL_RECYCLE: int = 7200
    POOL_PRE_PING: bool = True

    # ================================================= #
    # ******** 验证码 *********** #
    # ================================================= #
    CAPTCHA_ENABLE: bool = Field(default=True, validation_alias="CAPTCHA_ENABLE")
    CAPTCHA_EXPIRE_SECONDS: int = Field(default=60, validation_alias="CAPTCHA_EXPIRE_SECONDS")
    CAPTCHA_LENGTH: int = Field(default=4, validation_alias="CAPTCHA_LENGTH")

    # ================================================= #
    # ******** 日志 *********** #
    # ================================================= #
    LOGGER_DIR: str = "logs"
    LOGGER_NAME: str = "N-Tester.log"
    LOGGER_LEVEL: str = "INFO"
    LOGGER_ROTATION: str = "10 MB"
    LOGGER_RETENTION: str = "7 days"

    # ================================================= #
    # ******** Celery *********** #
    # ================================================= #
    broker_url: str = Field(..., validation_alias="CELERY_BROKER_URL")
    result_backend: str = Field(..., validation_alias="CELERY_RESULT_BACKEND")
    accept_content: typing.List[str] = ["json"]
    result_serializer: str = "json"
    timezone: str = "Asia/Shanghai"
    enable_utc: bool = False
    worker_concurrency: int = 10
    worker_prefetch_multiplier: int = 4
    worker_max_tasks_per_child: int = 100
    broker_pool_limit: int = 10
    result_backend_transport_options: typing.Dict[str, typing.Any] = {"visibility_timeout": 3600}
    include: typing.List[typing.Any] = [
        "app.api.v1.Ntesterc_module.Ntesterc_task_scheduler.celery_worker.tasks.common",
    ]
    TEST_FILES_DIR: str = str(BACKEND_ROOT / "files")
    task_run_pool: int = 3
    beat_db_uri: str = Field(default="", validation_alias="CELERY_BEAT_DB_URL")

    # ================================================= #
    # ******** OAuth *********** #
    # ================================================= #
    GRANT_ADMIN_TO_OAUTH_USER: bool = True
    GITEE_CLIENT_ID: str = Field(default="", validation_alias="GITEE_CLIENT_ID")
    GITEE_CLIENT_SECRET: str = Field(default="", validation_alias="GITEE_CLIENT_SECRET")
    GITEE_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/gitee/callback", validation_alias="GITEE_REDIRECT_URI")
    GITHUB_CLIENT_ID: str = Field(default="", validation_alias="GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: str = Field(default="", validation_alias="GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/github/callback", validation_alias="GITHUB_REDIRECT_URI")
    QQ_APP_ID: str = Field(default="", validation_alias="QQ_APP_ID")
    QQ_APP_KEY: str = Field(default="", validation_alias="QQ_APP_KEY")
    QQ_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/qq/callback", validation_alias="QQ_REDIRECT_URI")
    GOOGLE_CLIENT_ID: str = Field(default="", validation_alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = Field(default="", validation_alias="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/google/callback", validation_alias="GOOGLE_REDIRECT_URI")
    WECHAT_APP_ID: str = Field(default="", validation_alias="WECHAT_APP_ID")
    WECHAT_APP_SECRET: str = Field(default="", validation_alias="WECHAT_APP_SECRET")
    WECHAT_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/wechat/callback", validation_alias="WECHAT_REDIRECT_URI")
    MICROSOFT_CLIENT_ID: str = Field(default="", validation_alias="MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET: str = Field(default="", validation_alias="MICROSOFT_CLIENT_SECRET")
    MICROSOFT_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/microsoft/callback", validation_alias="MICROSOFT_REDIRECT_URI")
    DINGTALK_APP_ID: str = Field(default="", validation_alias="DINGTALK_APP_ID")
    DINGTALK_APP_SECRET: str = Field(default="", validation_alias="DINGTALK_APP_SECRET")
    DINGTALK_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/dingtalk/callback", validation_alias="DINGTALK_REDIRECT_URI")
    FEISHU_APP_ID: str = Field(default="", validation_alias="FEISHU_APP_ID")
    FEISHU_APP_SECRET: str = Field(default="", validation_alias="FEISHU_APP_SECRET")
    FEISHU_REDIRECT_URI: str = Field(default="http://localhost:3000/oauth/feishu/callback", validation_alias="FEISHU_REDIRECT_URI")

    # ================================================= #
    # ******** 邮件 *********** #
    # ================================================= #
    EMAIL_HOST: str = Field(default="smtp.qq.com", validation_alias="EMAIL_HOST")
    EMAIL_PORT: int = Field(default=587, validation_alias="EMAIL_PORT")
    EMAIL_USE_TLS: bool = Field(default=True, validation_alias="EMAIL_USE_TLS")
    EMAIL_HOST_USER: str = Field(default="", validation_alias="EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD: str = Field(default="", validation_alias="EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL: str = Field(default="", validation_alias="DEFAULT_FROM_EMAIL")

    # ================================================= #
    # ******** MinIO *********** #
    # ================================================= #
    MINIO_ENDPOINT: str = Field(default="127.0.0.1:9000", validation_alias="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", validation_alias="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", validation_alias="MINIO_SECRET_KEY")
    MINIO_SECURE: bool = Field(default=False, validation_alias="MINIO_SECURE")
    MINIO_BUCKET: str = Field(default="performance", validation_alias="MINIO_BUCKET")

    # ================================================= #
    # ******** SSH（压力机分发） *********** #
    # ================================================= #
    PLATFORM_SSH_KEY_PATH: str = Field(default="/root/.ssh/id_rsa", validation_alias="PLATFORM_SSH_KEY_PATH")
    DEFAULT_SSH_KEY_PATH: str = Field(default="/root/.ssh/id_rsa", validation_alias="DEFAULT_SSH_KEY_PATH")
    SSH_DEFAULT_USER: str = Field(default="root", validation_alias="SSH_DEFAULT_USER")
    SSH_DEFAULT_PASSWORD: str = Field(default="", validation_alias="SSH_DEFAULT_PASSWORD")

    # ================================================= #
    # ******** APP 自动化 *********** #
    # ================================================= #
    APP_PROJECT_ROOT: str = Field(default="", validation_alias="APP_PROJECT_ROOT")
    PROJECT_PATH: str = Field(default="", validation_alias="PROJECT_PATH")
    APP_PUBLIC_BASE_URL: str = Field(default="", validation_alias="APP_PUBLIC_BASE_URL")
    APP_DEVICE_RM_PATHS: str = Field(default="", validation_alias="APP_DEVICE_RM_PATHS")
    APP_SMS_BODY_KEYWORD: str = Field(default="识别文案", validation_alias="APP_SMS_BODY_KEYWORD")
    USE_APPIUM_APP_EXECUTOR: str = Field(default="", validation_alias="USE_APPIUM_APP_EXECUTOR")
    APPIUM_SERVER_URL: str = Field(default="http://127.0.0.1:4723", validation_alias="APPIUM_SERVER_URL")
    APP_TEMPLATE_ROOT: str = Field(default="backend", validation_alias="APP_TEMPLATE_ROOT")

    # ================================================= #
    # ******** 脚本执行 *********** #
    # ================================================= #
    SCRIPT_EXEC_MODE: str = Field(default="sandbox", validation_alias="SCRIPT_EXEC_MODE")
    SCRIPT_NATIVE_PYTHON: str = Field(default="", validation_alias="SCRIPT_NATIVE_PYTHON")
    SCRIPT_NATIVE_NODE: str = Field(default="", validation_alias="SCRIPT_NATIVE_NODE")
    SCRIPT_NATIVE_TIMEOUT: int = Field(default=30, validation_alias="SCRIPT_NATIVE_TIMEOUT")

    # 兼容旧代码读取 DB_* 属性
    @property
    def DB_HOST(self) -> str:
        return self.DATABASE_HOST

    @property
    def DB_PORT(self) -> int:
        return self.DATABASE_PORT

    @property
    def DB_USER(self) -> str:
        return self.DATABASE_USER

    @property
    def DB_PASSWORD(self) -> str:
        return self.DATABASE_PASSWORD

    @property
    def DB_NAME(self) -> str:
        return self.DATABASE_NAME

    def _build_async_uri(self) -> str:
        if self.DATABASE_TYPE == "mysql":
            return build_sqlalchemy_url(
                "mysql+aiomysql",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT,
                database=self.DATABASE_NAME,
                query={"charset": "utf8mb4"},
            )
        if self.DATABASE_TYPE == "postgres":
            return build_sqlalchemy_url(
                "postgresql+asyncpg",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT,
                database=self.DATABASE_NAME,
            )
        name = self.DATABASE_NAME if str(self.DATABASE_NAME).endswith(".db") else f"{self.DATABASE_NAME}.db"
        db_path = Path(name)
        if not db_path.is_absolute():
            db_path = BACKEND_ROOT / name
        return f"sqlite+aiosqlite:///{db_path.as_posix()}"

    def _build_sync_uri(self) -> str:
        if self.DATABASE_TYPE == "mysql":
            return build_sqlalchemy_url(
                "mysql+pymysql",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT,
                database=self.DATABASE_NAME,
                query={"charset": "utf8mb4"},
            )
        if self.DATABASE_TYPE == "postgres":
            return build_sqlalchemy_url(
                "postgresql+psycopg",
                username=self.DATABASE_USER,
                password=self.DATABASE_PASSWORD,
                host=self.DATABASE_HOST,
                port=self.DATABASE_PORT,
                database=self.DATABASE_NAME,
            )
        name = self.DATABASE_NAME if str(self.DATABASE_NAME).endswith(".db") else f"{self.DATABASE_NAME}.db"
        db_path = Path(name)
        if not db_path.is_absolute():
            db_path = BACKEND_ROOT / name
        return f"sqlite:///{db_path.as_posix()}"

    @model_validator(mode="after")
    def build_uris(self) -> "Configs":
        if self.DATABASE_TYPE not in ("mysql", "postgres", "sqlite"):
            raise ValueError(f"不支持的 DATABASE_TYPE: {self.DATABASE_TYPE}，请选择 mysql / postgres / sqlite")

        # Redis：拆字段 → REDIS_URI
        if not str(self.REDIS_URI or "").strip():
            if not self.REDIS_HOST:
                raise ValueError(
                    "请在 .env 中配置 Redis：\n"
                    "  推荐：REDIS_URI=redis://localhost:6379/4\n"
                    "  或拆字段：REDIS_HOST / REDIS_PORT / REDIS_USER / REDIS_PASSWORD / REDIS_DB"
                )
            self.REDIS_URI = build_redis_url(
                username=str(self.REDIS_USER or ""),
                password=str(self.REDIS_PASSWORD or ""),
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                db=self.REDIS_DB,
            )

   
        if not (self.DATABASE_URI and self.DATABASE_URI_SYNC):
            if self.DATABASE_TYPE == "sqlite" or (self.DATABASE_HOST and self.DATABASE_USER and self.DATABASE_NAME):
                self.DATABASE_URI = self._build_async_uri()
                self.DATABASE_URI_SYNC = self._build_sync_uri()
            else:
                raise ValueError(
                    "请在 .env 中配置数据库连接：\n"
                    "  DATABASE_TYPE=mysql|postgres|sqlite\n"
                    "  DATABASE_HOST / DATABASE_PORT / DATABASE_USER / DATABASE_PASSWORD / DATABASE_NAME\n"
                    "  兼容旧字段：DB_* 或 MYSQL_DATABASE_URI*"
                )

        if not self.beat_db_uri:
            self.beat_db_uri = self.DATABASE_URI_SYNC
        return self

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = Configs()
