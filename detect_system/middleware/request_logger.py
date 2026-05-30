# -*- coding: utf-8 -*-
"""
请求日志中间件
为每个请求生成唯一 ID，便于日志追踪
"""
import uuid
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Django 中间件，为每个请求添加唯一 ID 并记录日志
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 生成请求唯一 ID（取前8位）
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id

        # 获取用户信息
        user = request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'

        # 记录请求开始
        logger.info(f"[{request_id}] {request.method} {request.path} - user: {user}")

        response = self.get_response(request)

        # 记录响应状态
        logger.info(f"[{request_id}] Response: {response.status_code}")
        return response