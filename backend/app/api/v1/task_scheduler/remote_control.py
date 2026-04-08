from __future__ import annotations

import asyncio
import uuid
from typing import Any, Optional
from app.db import get_redis_pool
from config import config


QUEUE_KEY = "task_scheduler:cmd"
REPLY_KEY_PREFIX = "task_scheduler:reply:"


class SchedulerRemoteError(RuntimeError):
    pass


async def send_command(action: str, payload: Optional[dict[str, Any]] = None, timeout_s: float = 5.0) -> dict[str, Any]:
    """
    API 服务通过 Redis 向 scheduler_runner 发送控制命令，并等待回执。

    约定：
    - 命令入队：LPUSH QUEUE_KEY
    - 回执写入：SET reply_key (JSON) EX <ttl>
    """
    redis_pool = get_redis_pool()
    redis_pool.init_by_config(config=config)
    redis = redis_pool.redis

    correlation_id = str(uuid.uuid4())
    reply_key = f"{REPLY_KEY_PREFIX}{correlation_id}"

    cmd = {
        "id": correlation_id,
        "reply_key": reply_key,
        "action": action,
        "payload": payload or {},
    }

    await redis.cus_lpush(QUEUE_KEY, cmd)

    deadline = asyncio.get_event_loop().time() + float(timeout_s)
    while True:
        resp = await redis.get(reply_key)
        if resp is not None:
            try:
                await redis.delete(reply_key)
            except Exception:
                pass
            if isinstance(resp, dict) and resp.get("ok") is True:
                return resp.get("data") or {}
            raise SchedulerRemoteError((resp or {}).get("error") or "scheduler remote error")

        if asyncio.get_event_loop().time() >= deadline:
            raise SchedulerRemoteError("scheduler remote timeout")
        await asyncio.sleep(0.2)

