#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author: Rebort

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.core.database import get_db
from app.core.redis import get_redis_pool
from app.api.v1.system.user.model import UserModel
from app.api.v1.monitor.online.model import OnlineUserInfo, OnlineUserStats
from app.utils.common import parse_user_agent, get_location_by_ip


class OnlineUserService:
    """在线用户监控服务"""
    
    ONLINE_USER_PREFIX = "online_user:"
    ONLINE_STATS_KEY = "online_stats"
    ACTIVITY_TIMEOUT = 300  # 5分钟无活动视为不活跃
    
    @classmethod
    async def add_online_user(cls, user_id: int, username: str, nickname: str, avatar: str,
                            session_id: str, ip_address: str, user_agent: str) -> None:
        """添加在线用户"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            
            # 确保 Redis 已初始化
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            
            redis_client = redis_pool.redis
            
            if not redis_client:
                print(f"[OnlineUserService] Redis 客户端为 None，无法添加在线用户")
                return
            
            # 解析用户代理
            browser_info = parse_user_agent(user_agent)
            location = get_location_by_ip(ip_address)
            
            # 构建在线用户信息
            online_info = {
                "user_id": user_id,
                "username": username,
                "nickname": nickname or username,
                "avatar": avatar,
                "login_time": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "ip_address": ip_address,
                "location": location,
                "browser": browser_info.get("browser", "Unknown"),
                "os": browser_info.get("os", "Unknown"),
                "user_agent": user_agent,
                "session_id": session_id,
                "is_active": True
            }
            
            # 存储到Redis（使用原生命令避免双重 JSON 编码）
            key = f"{cls.ONLINE_USER_PREFIX}{user_id}:{session_id}"
            await redis_client.execute_command("SETEX", key, 86400, json.dumps(online_info))
            
            # 更新统计信息
            await cls._update_stats()
                
        except Exception as e:
            print(f"[OnlineUserService] 添加在线用户失败: {e}")
    
    @classmethod
    async def remove_online_user(cls, user_id: int, session_id: str) -> None:
        """移除在线用户"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            key = f"{cls.ONLINE_USER_PREFIX}{user_id}:{session_id}"
            await redis_client.delete(key)
            await cls._update_stats()
        except Exception as e:
            print(f"移除在线用户失败: {e}")
    
    @classmethod
    async def update_user_activity(cls, user_id: int, session_id: str) -> None:
        """更新用户活动时间"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            key = f"{cls.ONLINE_USER_PREFIX}{user_id}:{session_id}"
            
            # 获取现有信息（注意：redis_client.get 已经自动进行了 JSON 解析）
            # 使用原生的 get 方法，不进行自动 JSON 解析
            user_data = await redis_client.execute_command("GET", key)
            if user_data:
                online_info = json.loads(user_data)
                online_info["last_activity"] = datetime.now().isoformat()
                online_info["is_active"] = True
                
                # 更新Redis（使用原生命令）
                await redis_client.execute_command("SETEX", key, 86400, json.dumps(online_info))
        except Exception as e:
            # 静默失败，不影响正常请求
            pass
    
    @classmethod
    async def get_online_users(cls, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取在线用户列表"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            # 获取所有在线用户键
            pattern = f"{cls.ONLINE_USER_PREFIX}*"
            keys = await redis_client.keys(pattern)
            
            online_users = []
            current_time = datetime.now()
            
            for key in keys:
                try:
                    # 使用原生命令获取数据
                    user_data = await redis_client.execute_command("GET", key)
                    if user_data:
                        online_info = json.loads(user_data)
                        
                        # 计算在线时长
                        login_time = datetime.fromisoformat(online_info["login_time"])
                        duration = current_time - login_time
                        online_info["duration"] = str(duration).split('.')[0]
                        
                        # 检查是否活跃
                        last_activity = datetime.fromisoformat(online_info["last_activity"])
                        inactive_time = (current_time - last_activity).total_seconds()
                        online_info["is_active"] = inactive_time < cls.ACTIVITY_TIMEOUT
                        
                        # 格式化时间显示
                        online_info["login_time"] = login_time.strftime("%Y-%m-%d %H:%M:%S")
                        online_info["last_activity"] = last_activity.strftime("%Y-%m-%d %H:%M:%S")
                        
                        online_users.append(OnlineUserInfo(**online_info))
                        
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    # 数据格式错误，删除该键
                    print(f"解析在线用户数据失败: {e}, key: {key}")
                    await redis_client.delete(key)
                    continue
            
            # 按登录时间排序
            online_users.sort(key=lambda x: x.login_time, reverse=True)
            
            # 分页
            total = len(online_users)
            start = (page - 1) * page_size
            end = start + page_size
            items = online_users[start:end]
            
            return {
                "items": [user.dict() for user in items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            print(f"获取在线用户列表失败: {e}")
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "pages": 0
            }
    
    @classmethod
    async def get_online_stats(cls) -> OnlineUserStats:
        """获取在线用户统计"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            # 获取所有在线用户
            pattern = f"{cls.ONLINE_USER_PREFIX}*"
            keys = await redis_client.keys(pattern)
            
            total_online = len(keys) if keys else 0
            active_users = 0
            durations = []
            new_today = 0
            current_time = datetime.now()
            today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            for key in keys:
                try:
                    # 使用原生命令获取数据
                    user_data = await redis_client.execute_command("GET", key)
                    if user_data:
                        online_info = json.loads(user_data)
                        
                        # 检查是否活跃
                        last_activity = datetime.fromisoformat(online_info["last_activity"])
                        inactive_time = (current_time - last_activity).total_seconds()
                        if inactive_time < cls.ACTIVITY_TIMEOUT:
                            active_users += 1
                        
                        # 计算在线时长
                        login_time = datetime.fromisoformat(online_info["login_time"])
                        duration = (current_time - login_time).total_seconds()
                        durations.append(duration)
                        
                        # 统计今日新增（今天登录的用户）
                        if login_time >= today_start:
                            new_today += 1
                        
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f"解析统计数据失败: {e}")
                    continue
            
            # 计算平均在线时长
            avg_duration_seconds = sum(durations) / len(durations) if durations else 0
            avg_duration = str(timedelta(seconds=int(avg_duration_seconds))).split('.')[0]
            
            # 峰值设为当前在线人数（简化实现）
            peak_today = total_online
            
            return OnlineUserStats(
                total_online=total_online,
                active_users=active_users,
                new_today=new_today,
                peak_today=peak_today,
                avg_duration=avg_duration
            )
            
        except Exception as e:
            print(f"获取在线用户统计失败: {e}")
            import traceback
            traceback.print_exc()
            return OnlineUserStats(
                total_online=0,
                active_users=0,
                new_today=0,
                peak_today=0,
                avg_duration="0:00:00"
            )
    
    @classmethod
    async def force_offline(cls, user_id: int, session_id: str = None) -> bool:
        """强制用户下线（直接删除在线记录）"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            if session_id:
                # 下线指定会话
                key = f"{cls.ONLINE_USER_PREFIX}{user_id}:{session_id}"
                result = await redis_client.delete(key)
                await cls._update_stats()
                return result > 0
            else:
                # 下线用户的所有会话
                pattern = f"{cls.ONLINE_USER_PREFIX}{user_id}:*"
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                    await cls._update_stats()
                    return True
                return False
        except Exception as e:
            print(f"强制下线失败: {e}")
            return False
    
    @classmethod
    async def _update_stats(cls) -> None:
        """更新统计信息"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            stats = await cls.get_online_stats()
            if stats:
                # 使用原生命令存储
                await redis_client.execute_command("SETEX", cls.ONLINE_STATS_KEY, 300, json.dumps(stats.dict()))
        except Exception as e:
            print(f"更新统计信息失败: {e}")
    
    @classmethod
    async def cleanup_expired_users(cls) -> None:
        """清理过期的在线用户"""
        try:
            from app.config.setting import config
            redis_pool = get_redis_pool()
            if not redis_pool.redis:
                redis_pool.init_by_config(config=config)
            redis_client = redis_pool.redis
            
            pattern = f"{cls.ONLINE_USER_PREFIX}*"
            keys = await redis_client.keys(pattern)
            
            current_time = datetime.now()
            expired_keys = []
            
            for key in keys:
                try:
                    # 使用原生命令获取数据
                    user_data = await redis_client.execute_command("GET", key)
                    if user_data:
                        online_info = json.loads(user_data)
                        last_activity = datetime.fromisoformat(online_info["last_activity"])
                        
                        # 超过1小时无活动的用户视为离线
                        if (current_time - last_activity).total_seconds() > 3600:
                            expired_keys.append(key)
                            
                except (json.JSONDecodeError, ValueError, KeyError):
                    expired_keys.append(key)
            
            if expired_keys:
                await redis_client.delete(*expired_keys)
                await cls._update_stats()
        except Exception as e:
            print(f"清理过期用户失败: {e}")