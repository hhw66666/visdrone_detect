# -*- coding: utf-8 -*-
"""
限流中间件 - 基于 Redis 滑动窗口算法
"""
import redis
import time
from functools import wraps
from django.http import JsonResponse

_redis_client = None


def get_redis():
    """获取 Redis 连接，单例模式"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    return _redis_client


def sliding_window_rate_limit(key_prefix: str, limit: int, window: int = 60):
    """
    滑动窗口限流装饰器

    Args:
        key_prefix: 限流 key 前缀（如 'detect', 'chat'）
        limit: 时间窗口内允许的最大请求数
        window: 时间窗口大小（秒），默认 60 秒

    Usage:
        @sliding_window_rate_limit('detect', limit=10, window=60)
        def api_detect_image(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                r = get_redis()
            except Exception:
                # Redis 不可用时放行，不影响正常功能
                return view_func(request, *args, **kwargs)

            # 生成用户维度的 key（已登录用用户名，未登录用 IP）
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.username
            else:
                user_id = request.META.get('REMOTE_ADDR', 'anonymous')
                if user_id == '127.0.0.1':
                    # 尝试获取真实 IP
                    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
                    if x_forwarded:
                        user_id = x_forwarded.split(',')[0].strip()

            key = f"ratelimit:{key_prefix}:{user_id}"
            now = time.time()
            window_start = now - window

            try:
                pipe = r.pipeline()
                # 删除窗口外的旧记录
                pipe.zremrangebyscore(key, 0, window_start)
                # 统计当前窗口内请求数
                pipe.zcard(key)
                # 添加当前请求
                pipe.zadd(key, {str(now): now})
                # 设置过期时间
                pipe.expire(key, window + 1)
                results = pipe.execute()

                current_count = results[1]
                if current_count >= limit:
                    return JsonResponse({
                        'success': False,
                        'error': '请求过于频繁，请稍后再试'
                    }, status=429)

            except Exception:
                # Redis 操作失败时放行
                return view_func(request, *args, **kwargs)

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator