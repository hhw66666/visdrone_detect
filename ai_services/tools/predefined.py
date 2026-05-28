# -*- coding: utf-8 -*-
"""
预定义工具
"""

from typing import Any

from .base import Tool, ToolCategory


def create_query_detection_records_tool(
    query_func: callable,
) -> Tool:
    """
    创建数据库查询工具

    Args:
        query_func: 查询函数，接收 SQL 参数，返回查询结果

    Returns:
        Tool: 数据库查询工具
    """
    async def async_handler(sql: str) -> dict[str, Any]:
        return await query_func(sql)

    def sync_handler(sql: str) -> dict[str, Any]:
        return query_func(sql)

    return Tool(
        name="query_detection_records",
        description="查询检测记录数据库。可以查询用户的检测历史、统计信息等。",
        input_schema={
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL 查询语句。例如：SELECT * FROM detection_record WHERE user_id = 1 LIMIT 10"
                },
                "params": {
                    "type": "array",
                    "description": "查询参数（可选）",
                    "items": {"type": "any"}
                }
            },
            "required": ["sql"]
        },
        handler=sync_handler,
        async_handler=async_handler,
        category=ToolCategory.QUERY,
    )


def create_search_knowledge_tool(
    search_func: callable,
) -> Tool:
    """
    创建知识库搜索工具

    Args:
        search_func: 搜索函数，接收查询字符串，返回相关文档

    Returns:
        Tool: 知识库搜索工具
    """
    async def async_handler(query: str, top_k: int = 3) -> dict[str, Any]:
        return await search_func(query, top_k)

    def sync_handler(query: str, top_k: int = 3) -> dict[str, Any]:
        return search_func(query, top_k)

    return Tool(
        name="search_knowledge",
        description="搜索知识库。用于查找系统使用说明、常见问题解答等。",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "top_k": {
                    "type": "integer",
                    "description": "返回的最相关结果数量（默认3）",
                    "default": 3
                }
            },
            "required": ["query"]
        },
        handler=sync_handler,
        async_handler=async_handler,
        category=ToolCategory.RETRIEVAL,
    )


def create_http_request_tool(
    request_func: callable,
) -> Tool:
    """
    创建 HTTP 请求工具

    Args:
        request_func: 请求函数，接收 url, method, data 参数

    Returns:
        Tool: HTTP 请求工具
    """
    async def async_handler(
        url: str,
        method: str = "GET",
        data: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        return await request_func(url, method, data, headers)

    def sync_handler(
        url: str,
        method: str = "GET",
        data: dict | None = None,
        headers: dict | None = None,
    ) -> dict[str, Any]:
        return request_func(url, method, data, headers)

    return Tool(
        name="http_request",
        description="发起 HTTP 请求。用于调用外部 API。",
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "请求 URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP 方法",
                    "enum": ["GET", "POST", "PUT", "DELETE"]
                },
                "data": {
                    "type": "object",
                    "description": "请求数据（可选）"
                },
                "headers": {
                    "type": "object",
                    "description": "请求头（可选）"
                }
            },
            "required": ["url"]
        },
        handler=sync_handler,
        async_handler=async_handler,
        category=ToolCategory.API,
    )


def create_amap_weather_tool(weather_func: callable) -> Tool:
    """
    创建高德天气查询工具

    Args:
        weather_func: 天气查询函数

    Returns:
        Tool: 高德天气工具
    """
    async def async_handler(city: str) -> dict[str, Any]:
        return await weather_func(city)

    def sync_handler(city: str) -> dict[str, Any]:
        return weather_func(city)

    return Tool(
        name="amap_weather",
        description="查询高德地图天气信息。可以查询任意城市的实时天气、天气预报等信息。",
        input_schema={
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称或城市编码，如：北京、上海、广州"
                }
            },
            "required": ["city"]
        },
        handler=sync_handler,
        async_handler=async_handler,
        category=ToolCategory.API,
    )


def create_amap_place_search_tool(search_func: callable) -> Tool:
    """
    创建高德地点搜索工具

    Args:
        search_func: 地点搜索函数

    Returns:
        Tool: 高德地点搜索工具
    """
    async def async_handler(keywords: str, city: str = "全国") -> dict[str, Any]:
        return await search_func(keywords, city)

    def sync_handler(keywords: str, city: str = "全国") -> dict[str, Any]:
        return search_func(keywords, city)

    return Tool(
        name="amap_place_search",
        description="搜索高德地图上的地点位置。输入关键词（如餐厅、酒店、景点名称）和城市，返回地点的详细地址、经纬度等信息。",
        input_schema={
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "搜索关键词，如：东方明珠、故宫、肯德基"
                },
                "city": {
                    "type": "string",
                    "description": "所在城市（可选，默认全国），如：上海、北京"
                }
            },
            "required": ["keywords"]
        },
        handler=sync_handler,
        async_handler=async_handler,
        category=ToolCategory.API,
    )


def create_amap_geocode_tool(geocode_func: callable) -> Tool:
    """
    创建高德地理编码工具（地址转经纬度）

    Args:
        geocode_func: 地理编码函数

    Returns:
        Tool: 高德地理编码工具
    """
    async def async_handler(address: str, city: str = "") -> dict[str, Any]:
        return await geocode_func(address, city)

    def sync_handler(address: str, city: str = "") -> dict[str, Any]:
        return geocode_func(address, city)

    return Tool(
        name="amap_geocode",
        description="将地址转换为经纬度坐标。输入详细地址，返回对应的经度和纬度坐标。",
        input_schema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "详细地址，如：北京市朝阳区建国门外大街1号"
                },
                "city": {
                    "type": "string",
                    "description": "所在城市（可选），如：北京、上海"
                }
            },
            "required": ["address"]
        },
        handler=sync_handler,
        async_handler=async_handler,
        category=ToolCategory.API,
    )
