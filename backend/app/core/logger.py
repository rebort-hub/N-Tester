# -*- coding: utf-8 -*-
# @author: rebort
"""
应用日志：控制台 + backend/logs 文件（全量 +错误）。
"""
import os
import sys
import logging
from pathlib import Path
from loguru import logger
from app.config.setting import config
from app.core.local import g
from app.utils import create_dir
from app.utils.common import get_str_uuid


def _log_dir() -> Path:
    """确保 backend/logs 存在并返回路径。"""
    return Path(create_dir(config.LOGGER_DIR))


def correlation_id_filter(record):
    if not g.trace_id:
        g.trace_id = get_str_uuid()
    record["trace_id"] = g.trace_id
    return record


_FMT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>| {thread} | "
    "<level>{level: <8}</level> | <yellow> {trace_id} </yellow> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)
_FMT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS}| {thread} | {level: <8} | {trace_id} | "
    "{name}:{function}:{line} | {message}"
)

_configured = False


def configure_logger() -> None:
    """配置控制台与文件日志（可重复调用，仅首次生效）。"""
    global _configured
    if _configured:
        return

    logger.remove()

    # 控制台
    logger.add(
        sys.stdout,
        level=config.LOGGER_LEVEL,
        colorize=True,
        filter=correlation_id_filter,
        format=_FMT_CONSOLE,
    )

    log_dir = _log_dir()
    encoding = getattr(config, "GLOBAL_ENCODING", "utf-8") or "utf-8"

    
    logger.add(
        str(log_dir / config.LOGGER_NAME),
        level=config.LOGGER_LEVEL,
        encoding=encoding,
        rotation=config.LOGGER_ROTATION,
        retention=config.LOGGER_RETENTION,
        filter=correlation_id_filter,
        format=_FMT_FILE,
        enqueue=True,
    )

   
    logger.add(
        str(log_dir / "error.log"),
        level="ERROR",
        encoding=encoding,
        rotation=config.LOGGER_ROTATION,
        retention=config.LOGGER_RETENTION,
        filter=correlation_id_filter,
        format=_FMT_FILE,
        enqueue=True,
    )

    _configured = True



configure_logger()


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(level, record.getMessage())


def init_logger():
    """挂接标准库 logging，并确保文件日志已配置。"""
    configure_logger()

    logger_name_list = [name for name in logging.root.manager.loggerDict]

    for logger_name in logger_name_list:
        effective_level = logging.getLogger(logger_name).getEffectiveLevel()
        if effective_level < logging.getLevelName(config.LOGGER_LEVEL.upper()):
            logging.getLogger(logger_name).setLevel(config.LOGGER_LEVEL.upper())
        if "." not in logger_name:
            logging.getLogger(logger_name).handlers = []
            logging.getLogger(logger_name).addHandler(InterceptHandler())
