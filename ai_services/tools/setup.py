# -*- coding: utf-8 -*-
"""
工具初始化
注册真实工具到工具注册表
"""

import logging

logger = logging.getLogger(__name__)


def _query_detection_records_sql(sql: str) -> dict:
    """
    使用 Django ORM 查询检测记录

    Args:
        sql: SQL 查询语句（仅支持 SELECT）

    Returns:
        查询结果字典
    """
    # 安全检查：只允许 SELECT 语句
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith('SELECT'):
        return {"error": "只支持 SELECT 查询"}

    try:
        from detection.models import DetectionRecord
        from django.db import connection

        # 执行原始 SQL
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        # 转换为字典列表
        results = [dict(zip(columns, row)) for row in rows]

        return {
            "success": True,
            "data": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"查询检测记录失败: {e}")
        return {"success": False, "error": str(e)}


def _search_knowledge_impl(query: str, top_k: int = 3) -> dict:
    """
    搜索知识库

    Args:
        query: 搜索关键词
        top_k: 返回数量

    Returns:
        搜索结果
    """
    try:
        from ..rag.retriever import get_retriever

        retriever = get_retriever()
        results = retriever.retrieve(query, top_k=top_k)

        docs = []
        for doc, score in results:
            docs.append({
                "content": doc.content,
                "score": score,
                "metadata": doc.metadata,
            })

        return {
            "success": True,
            "data": docs,
            "count": len(docs),
        }
    except Exception as e:
        logger.error(f"搜索知识库失败: {e}")
        return {"success": False, "error": str(e)}


# 导入缓存模块
try:
    from ai_services.cache.redis_cache import cache_get, cache_set
    HAS_CACHE = True
except ImportError:
    HAS_CACHE = False


def _amap_weather_impl(city: str) -> dict:
    """
    查询天气（优先用高德 MCP，备用 wttr.in）

    Args:
        city: 城市名称

    Returns:
        天气结果
    """
    # 先尝试从缓存获取
    if HAS_CACHE:
        cache_key = f"cache:weather:{city}"
        cached = cache_get(cache_key)
        if cached:
            logger.info(f"天气缓存命中: {city}")
            return cached

    # 城市名中英映射（常用城市）
    CITY_NAME_MAP = {
        '北京': 'Beijing', '上海': 'Shanghai', '广州': 'Guangzhou',
        '深圳': 'Shenzhen', '杭州': 'Hangzhou', '成都': 'Chengdu',
        '武汉': 'Wuhan', '西安': "Xi'an", '重庆': 'Chongqing',
        '天津': 'Tianjin', '南京': 'Nanjing', '长沙': 'Changsha',
        '沈阳': 'Shenyang', '青岛': 'Qingdao', '济南': 'Jinan',
        '郑州': 'Zhengzhou', '石家庄': 'Shijiazhuang', '福州': 'Fuzhou',
        '厦门': 'Xiamen', '南昌': 'Nanchang', '合肥': 'Hefei',
        '昆明': 'Kunming', '贵阳': 'Guiyang', '南宁': 'Nanning',
        '海口': 'Haikou', '太原': 'Taiyuan', '拉萨': 'Lhasa',
        '兰州': 'Lanzhou', '西宁': 'Xining', '银川': 'Yinchuan',
        '乌鲁木齐': 'Urumqi', '哈尔滨': 'Harbin', '长春': 'Changchun',
        '大连': 'Dalian', '苏州': 'Suzhou', '无锡': 'Wuxi',
        '宁波': 'Ningbo', '温州': 'Wenzhou', '佛山': 'Foshan',
        '东莞': 'Dongguan', '珠海': 'Zhuhai', '中山': 'Zhongshan',
        '惠州': 'Huizhou', '汕头': 'Shantou', '湛江': 'Zhanjiang',
        '常州': 'Changzhou', '徐州': 'Xuzhou', '南通': 'Nantong',
        '扬州': 'Yangzhou', '盐城': 'Yancheng', '昆山': 'Kunshan',
        '嘉兴': 'Jiaxing', '绍兴': 'Shaoxing', '金华': 'Jinhua',
        '台州': 'Taizhou', '湖州': 'Huzhou', '芜湖': 'Wuhu',
        '蚌埠': 'Bengbu', '淮南': 'Huainan', '马鞍山': "Ma'anshan",
        '湘潭': 'Xiangtan', '株洲': 'Zhuzhou', '衡阳': 'Hengyang',
        '岳阳': 'Yueyang', '常德': 'Changde', '张家界': 'Zhangjiajie',
        '益阳': 'Yiyang', '邵阳': 'Shaoyang', '娄底': 'Loudi',
        '郴州': 'Chenzhou', '永州': 'Yongzhou', '怀化': 'Huaihua',
        '湘西': 'Xiangxi', '韶山': 'Shaoshan', '浏阳': 'Liuyang',
        '醴陵': 'Liling', '攸县': 'Youxian', '茶陵': 'Chaling',
        '炎陵': 'Yanling', '株州': 'Zhuzhou', '衡山': 'Hengshan',
        '祁东': 'Qidong', '祁阳': 'Qiyang', '安化': 'Anhua',
        '桃江': 'Taojiang', '新化': 'Xinhua', '涟源': 'Lianyuan',
    }

    # 先尝试直接调用 wttr.in 免费天气 API
    try:
        import requests

        # 中文城市名转英文
        en_city = CITY_NAME_MAP.get(city, city)
        url = f"https://wttr.in/{en_city}?format=j1"
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)

        if resp.status_code == 200:
            data = resp.json()
            current = data.get('current_condition', [{}])[0]
            temp = current.get('temp_C', '?')
            desc = current.get('weatherDesc', [{}])[0].get('value', '?')
            humidity = current.get('humidity', '?')
            wind = current.get('windspeedKmph', '?')
            return {
                "success": True,
                "data": {
                    "city": city,
                    "temperature": f"{temp}°C",
                    "weather": desc,
                    "humidity": f"{humidity}%",
                    "wind_speed": f"{wind} km/h"
                }
            }
        else:
            logger.warning(f"wttr.in 返回状态码 {resp.status_code}")
    except Exception as e:
        logger.error(f"wttr.in 天气查询失败: {e}")

    # 尝试高德 MCP
    try:
        from ..mcp.modelscope_client import get_modelscope_client
        mcp_client = get_modelscope_client()
        if mcp_client and mcp_client.is_connected():
            # 尝试 maps_weather 工具
            result = mcp_client.call_tool("maps_weather", {"city": city})
            if result.get("success"):
                logger.info("MCP 天气查询成功")
                # 缓存结果（30分钟）
                if HAS_CACHE:
                    cache_set(cache_key, result, ttl=1800)
                return result
            logger.warning(f"MCP 天气查询失败: {result.get('error', 'unknown')}")
        else:
            logger.info("MCP 未连接，跳过 MCP 调用")
    except Exception as e:
        logger.error(f"MCP 天气查询异常: {e}")

    return {"success": False, "error": "天气服务暂时不可用"}


def _amap_place_search_impl(keywords: str, city: str = "全国") -> dict:
    """
    搜索高德地点（优先 MCP，备用 Nominatim）

    Args:
        keywords: 关键词
        city: 城市

    Returns:
        地点搜索结果
    """
    # 先尝试从缓存获取
    if HAS_CACHE:
        from ai_services.cache.redis_cache import hash_key
        cache_key = f"cache:place:{hash_key(keywords + city)}"
        cached = cache_get(cache_key)
        if cached:
            logger.info(f"地点搜索缓存命中: {keywords}")
            return cached

    # 尝试高德 MCP
    try:
        from ..mcp.modelscope_client import get_modelscope_client

        mcp_client = get_modelscope_client()
        if mcp_client and mcp_client.is_connected():
            # 尝试 maps_text_search 工具
            result = mcp_client.call_tool("maps_text_search", {"keywords": keywords, "city": city})
            if result.get("success"):
                logger.info("MCP 地点搜索成功")
                return result
            logger.warning(f"MCP 地点搜索失败: {result.get('error', 'unknown')}")
        else:
            logger.info("MCP 未连接，跳过 MCP 调用")
    except Exception as e:
        logger.error(f"MCP 地点搜索异常: {e}")

    # 备用：使用 Nominatim (OpenStreetMap) 搜索
    try:
        import requests

        query = keywords if not city or city == "全国" else f"{city} {keywords}"
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"

        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)

        if resp.status_code == 200:
            data = resp.json()
            if data:
                first = data[0]
                result = {
                    "success": True,
                    "data": json.dumps({
                        "pois": [{
                            "name": first.get('display_name', keywords),
                            "address": first.get('display_name', ''),
                            "location": f"{first.get('lon', '')},{first.get('lat', '')}"
                        }]
                    }, ensure_ascii=False)
                }
                # 缓存结果（2小时）
                if HAS_CACHE:
                    cache_set(cache_key, result, ttl=7200)
                return result
    except Exception as e:
        logger.error(f"Nominatim 搜索失败: {e}")

    return {"success": False, "error": "地点搜索暂时不可用"}


def _amap_geocode_impl(address: str, city: str = "") -> dict:
    """
    地理编码（地址转经纬度，优先 MCP，备用 Nominatim）

    Args:
        address: 地址
        city: 城市

    Returns:
        地理编码结果
    """
    # 先尝试从缓存获取
    if HAS_CACHE:
        from ai_services.cache.redis_cache import hash_key
        cache_key = f"cache:geocode:{hash_key(address + city)}"
        cached = cache_get(cache_key)
        if cached:
            logger.info(f"地理编码缓存命中: {address}")
            return cached

    # 尝试高德 MCP
    try:
        from ..mcp.modelscope_client import get_modelscope_client

        mcp_client = get_modelscope_client()
        if mcp_client and mcp_client.is_connected():
            # 尝试 maps_geo 工具
            result = mcp_client.call_tool("maps_geo", {"address": address, "city": city})
            if result.get("success"):
                logger.info("MCP 地理编码成功")
                # 缓存结果（24小时）
                if HAS_CACHE:
                    cache_set(cache_key, result, ttl=86400)
                return result
            logger.warning(f"MCP 地理编码失败: {result.get('error', 'unknown')}")
        else:
            logger.info("MCP 未连接，跳过 MCP 调用")
    except Exception as e:
        logger.error(f"MCP 地理编码异常: {e}")

    # 备用：使用 Nominatim 地理编码
    try:
        import requests

        query = address if not city else f"{city} {address}"
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"

        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=8)

        if resp.status_code == 200:
            data = resp.json()
            if data:
                first = data[0]
                result = {
                    "success": True,
                    "data": json.dumps({
                        "location": f"{first.get('lon', '')},{first.get('lat', '')}",
                        "address": first.get('display_name', address)
                    }, ensure_ascii=False)
                }
                # 缓存结果（24小时）
                if HAS_CACHE:
                    cache_set(cache_key, result, ttl=86400)
                return result
    except Exception as e:
        logger.error(f"Nominatim 地理编码失败: {e}")

    return {"success": False, "error": "地理编码暂时不可用"}


def setup_tools():
    """
    初始化并注册所有工具

    应在 Django 应用启动时调用
    """
    from .predefined import (
        create_query_detection_records_tool,
        create_search_knowledge_tool,
        create_amap_weather_tool,
        create_amap_place_search_tool,
        create_amap_geocode_tool,
    )
    from .registry import get_tool_registry

    registry = get_tool_registry()

    # 注册检测记录查询工具
    if "query_detection_records" not in registry:
        tool = create_query_detection_records_tool(_query_detection_records_sql)
        registry.register(tool)
        logger.info("已注册工具: query_detection_records")

    # 注册知识库搜索工具
    if "search_knowledge" not in registry:
        tool = create_search_knowledge_tool(_search_knowledge_impl)
        registry.register(tool)
        logger.info("已注册工具: search_knowledge")

    # 注册高德地图工具
    try:
        from ..mcp.modelscope_client import get_modelscope_client
        mcp_client = get_modelscope_client()

        if mcp_client and mcp_client.is_connected():
            if "amap_weather" not in registry:
                tool = create_amap_weather_tool(_amap_weather_impl)
                registry.register(tool)
                logger.info("已注册工具: amap_weather")

            if "amap_place_search" not in registry:
                tool = create_amap_place_search_tool(_amap_place_search_impl)
                registry.register(tool)
                logger.info("已注册工具: amap_place_search")

            if "amap_geocode" not in registry:
                tool = create_amap_geocode_tool(_amap_geocode_impl)
                registry.register(tool)
                logger.info("已注册工具: amap_geocode")
        else:
            logger.info("ModelScope MCP 未连接，跳过高德地图工具注册")
    except Exception as e:
        logger.error(f"注册高德地图工具失败: {e}")

    return registry


def get_registered_tools():
    """
    获取已注册的工具列表

    Returns:
        工具列表
    """
    registry = get_tool_registry()
    return registry.list_tools()