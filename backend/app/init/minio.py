import asyncio
from app.corelibs.logger import logger
from app.utils.common import fmt_cloudflare_html_resp
from config import config


async def init_minio():
    """
    初始化Minio服务，检查或创建Minio Bucket对象
    """
    # 确保 MinIO Bucket 存在（不存在时自动创建），每次超时10s，最多重试3次
    # 服务端已返回 HTTP 响应（配置错误）时不重试；仅超时或连接失败才重试
    from app.core.minio_client import MinioClient
    _minio_ok = False
    for _attempt in range(1, 4):
        try:
            await asyncio.wait_for(MinioClient.ensure_bucket(config.MINIO_BUCKET), timeout=10)
            logger.info(f"MinIO Bucket 检查完成：{config.MINIO_BUCKET}")
            _minio_ok = True
            break
        except asyncio.TimeoutError:
            logger.warning(f"MinIO Bucket 初始化超时（第{_attempt}次）")
        except Exception as e:
            logger.warning(f"MinIO Bucket 初始化失败（第{_attempt}次）：{fmt_cloudflare_html_resp(e, '请检查 MinIO 地址或网络配置')}")
            # 服务端已响应（HTTP 状态码返回），属于配置问题，不再重试
            if 'Response code:' in str(e):
                break
        else:
            break
        if _attempt < 3:
            await asyncio.sleep(5)
    if not _minio_ok:
        logger.error("MinIO Bucket 初始化失败，文件上传功能不可用，已跳过!")
