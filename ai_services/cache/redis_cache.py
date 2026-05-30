# -*- coding: utf-8 -*-
"""
Redis 缓存模块
提供通用的缓存读写功能，支持降级处理
"""
import redis
import json
import hashlib
from typing import Optional

_redis_client = None


def get_redis():
    """获取 Redis 连接，单例模式"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    return _redis_client


def cache_get(key: str) -> Optional[dict]:
    """
    获取缓存数据

    Args:
        key: 缓存 key

    Returns:
        缓存的数据（dict），未命中或 Redis 不可用时返回 None
    """
    try:
        r = get_redis()
        data = r.get(key)
        return json.loads(data) if data else None
    except Exception:
        return None


def cache_set(key: str, value: dict, ttl: int):
    """
    设置缓存数据

    Args:
        key: 缓存 key
        value: 缓存的数据（dict）
        ttl: 过期时间（秒）

    Note:
        Redis 不可用时静默降级，不影响正常功能
    """
    try:
        r = get_redis()
        r.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except Exception:
        pass


def hash_key(s: str) -> str:
    """
    生成 MD5 hash 作为缓存 key 的一部分

    Args:
        s: 需要 hash 的字符串

    Returns:
        MD5 hash 字符串
    """
    return hashlib.md5(s.encode('utf-8')).hexdigest()