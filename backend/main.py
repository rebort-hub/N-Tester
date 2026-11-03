# -*- coding: utf-8 -*-
# @author: Rebort
from contextlib import asynccontextmanager
import asyncio
import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.core.logger import init_logger, logger
from app.core.register import (
    init_cors,
    init_exception,
    init_middleware,
    init_minio,
    init_scheduler,
    shutdown_scheduler,
    load_perf_pending_jobs,
    init_router,
    init_mount,
    init_limiter,
)
from app.config.setting import config


@asynccontextmanager
async def start_app(app: FastAPI):
    """ 注册中心 """

    from app.core.redis import get_redis_pool
    redis_pool_instance = get_redis_pool()
    redis_pool_instance.init_by_config(config=config)
    
    init_logger()
    logger.info("日志初始化成功！！!")
    logger.info(f"数据库类型: {config.DATABASE_TYPE}")

 
    if config.DB_AUTO_INIT:
        try:
            from app.scripts.initialize import InitializeData
            await InitializeData().init_db()
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    # 初始化限流器（异步）
    await init_limiter(app)

    # 初始化Minio文件服务
    await init_minio()

    # 启动 APScheduler 定时任务调度器
    init_scheduler()

    # 恢复性能测试待触发定时任务（MemoryJobStore 重启后清空）
    await load_perf_pending_jobs()

    yield

    
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.warning(f"关闭 APScheduler 失败: {e}")

    try:
        redis = redis_pool_instance.redis
        if redis is not None:
            close = getattr(redis, "aclose", None) or redis.close
            await asyncio.wait_for(close(), timeout=3)
    except Exception as e:
        logger.warning(f"关闭 Redis 失败: {e}")

    try:
        from app.core.database import engine
        await asyncio.wait_for(engine.dispose(), timeout=5)
    except Exception as e:
        logger.warning(f"关闭数据库引擎失败: {e}")

    # loguru enqueue=True 时需 complete，否则后台写日志线程会拖住进程
    try:
        await asyncio.wait_for(logger.complete(), timeout=2)
    except Exception:
        pass


def create_app() -> FastAPI:
    app: FastAPI = FastAPI(
        title="N-Tester2.0 API",
        description=config.SERVER_DESC,
        version=str(config.SERVER_VERSION),  # 确保版本号是字符串
        lifespan=start_app,
        docs_url=None,  # 禁用默认的 /docs
        redoc_url=None,  # 禁用默认的 /redoc
        openapi_url="/openapi.json",  # OpenAPI schema 路径
    )
    init_exception(app)  # 注册捕获全局异常
    init_router(app)  # 注册路由
    init_middleware(app)  # 注册请求响应拦截
    init_cors(app)  # 初始化跨域
    init_mount(app)  # 挂载静态文件

    # 自定义 API 文档路由
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Swagger UI 文档"""
        with open("static/swagger/swagger.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """ReDoc 文档"""
        with open("static/swagger/redoc.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return app


app = create_app()


if __name__ == '__main__':
    # Windows 下 reload=True（WatchFiles 父子进程）Ctrl+C 后父进程经常挂死；
    # 默认关闭热重载；需要时设置环境变量 UVICORN_RELOAD=1
    _reload = os.getenv("UVICORN_RELOAD", "0").strip().lower() in {"1", "true", "yes", "on"}
    uvicorn.run(app='main:app', host="0.0.0.0", port=8100, reload=_reload)
    # gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8101
