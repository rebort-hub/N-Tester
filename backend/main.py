# -*- coding: utf-8 -*-
# @author: Rebort
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.corelibs.logger import init_logger, logger
from app.init.cors import init_cors
from app.init.exception import init_exception
from app.init.middleware import init_middleware
from app.init.routers import init_router
from app.init.mount import init_mount
from app.init.limiter import init_limiter
from config import config


@asynccontextmanager
async def start_app(app: FastAPI):
    """ 注册中心 """
    # 获取Redis连接池（延迟初始化）
    from app.db import get_redis_pool
    redis_pool_instance = get_redis_pool()
    redis_pool_instance.init_by_config(config=config)
    
    init_logger()
    logger.info("日志初始化成功！！!")
    
    # 初始化限流器（异步）
    await init_limiter(app)

    yield

    await redis_pool_instance.redis.close()


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
    uvicorn.run(app='main:app', host="0.0.0.0", port=8100, reload=True)
    # gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8101
