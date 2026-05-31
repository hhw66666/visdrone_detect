# -*- coding: utf-8 -*-
"""
小科客服 Agent
科大巡弋智能航拍目标检测系统的 AI 客服助手
"""

import json
import logging
from typing import Any, AsyncIterator, Optional

from .base import BaseAgent
from ..config import get_agent_config
from ..prompts import XIAOYU_SYSTEM_PROMPT, format_xiaoyu_prompt

logger = logging.getLogger(__name__)


class XiaoyuAgent(BaseAgent):
    """
    小科客服 Agent

    继承自 BaseAgent，实现智能航拍检测系统的客服功能
    支持同步和异步调用
    """

    def __init__(self):
        """初始化小科客服"""
        config = get_agent_config('xiaoyu')

        super().__init__(
            name=config.get('name', '小科'),
            model=config.get('model', 'MiniMax-M2.7'),
            max_tokens=config.get('max_tokens', 1024),
            temperature=config.get('temperature', 0.7)
        )

        self.system_prompt_template = config.get('system_prompt_template', 'default')
        self._load_api_config()
        self._init_rag_retriever()

    def _init_rag_retriever(self):
        """初始化 RAG 检索器"""
        self.retriever = None
        try:
            from ..rag.retriever import get_retriever
            self.retriever = get_retriever()
            logger.info("RAG 检索器初始化成功")
        except Exception as e:
            logger.warning(f"RAG 检索器初始化失败: {e}")

    def _load_api_config(self):
        """加载 API 配置"""
        try:
            from detect_system.config_loader import get_minimax_config
            minimax_config = get_minimax_config()
            self.api_key = minimax_config.get('api_key', '')
            self.base_url = minimax_config.get('base_url', 'https://api.minimaxi.com/anthropic/v1')
            self.model = minimax_config.get('model', self.model)
        except Exception:
            self.api_key = ''
            self.base_url = 'https://api.minimaxi.com/anthropic/v1'
            logger.warning("无法加载 MiniMax API 配置")

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return XIAOYU_SYSTEM_PROMPT

    def chat(self, user_message: str, user_ip: str = None, user_location: dict = None) -> str:
        """
        同步处理用户消息并返回回复

        Args:
            user_message: 用户输入的消息
            user_ip: 用户的 IP 地址（已废弃，使用 user_location 替代）
            user_location: 用户浏览器 GPS 坐标 {'latitude': float, 'longitude': float}

        Returns:
            小科的回复内容
        """
        import urllib.request
        import urllib.error

        # 先检查是否需要使用工具
        tool_result = self._try_call_tool(user_message, user_ip, user_location)
        if tool_result:
            self.add_message('user', user_message)
            self.add_message('assistant', tool_result)
            return tool_result

        # 构建用户消息，包含位置信息（如果获取到）
        full_message = user_message

        # 记录用户消息
        self.add_message('user', full_message)

        # 构建 API 请求（包含 system prompt）
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + [msg.to_dict() for msg in self.conversation_history]

        # RAG 检索增强：如果有 retriever，先进行知识库检索
        if self.retriever:
            try:
                rag_context = self.retriever.get_context(user_message, top_k=3)
                if rag_context:
                    logger.info("RAG 检索到相关知识")
                    messages.insert(1, {
                        "role": "system",
                        "content": f"【知识库检索结果】：\n{rag_context}\n\n请基于上述信息回答用户问题。"
                    })
            except Exception as e:
                logger.warning(f"RAG 检索失败: {e}")

        try:
            reply = self._call_minimax_api_sync(messages)
            # 记录助手回复
            self.add_message('assistant', reply)
            return reply
        except Exception as e:
            error_reply = f'抱歉，小科暂时无法回答这个问题。'
            self.add_message('assistant', error_reply)
            logger.error(f"[XiaoyuAgent] chat 错误: {e}")
            return error_reply

    def _try_call_tool(self, user_message: str, user_ip: str = None, user_location: dict = None) -> str:
        """
        尝试调用工具处理用户消息

        Args:
            user_message: 用户输入的消息
            user_ip: 用户的 IP 地址
            user_location: 用户浏览器 GPS 坐标 {'latitude': float, 'longitude': float}

        Returns:
            工具执行结果，如果不需要工具则返回空字符串
        """
        msg = user_message.strip()

        # 天气查询
        if any(kw in msg for kw in ['天气', '温度', '下雨', '晴天', 'weather']):
            city = self._extract_city(msg)
            if city:
                result = self._amap_weather(city)
                if result:
                    return result

        # 地点搜索
        if any(kw in msg for kw in ['在哪里', '位置', '地址', '找', '搜索', '怎么走', '离我']):
            # 尝试提取地点名称
            place = self._extract_place(msg)
            if place:
                result = self._amap_place_search(place)
                if result:
                    return result

        # 地理编码（地址转经纬度）
        if any(kw in msg for kw in ['经纬度', '坐标', 'latitude', 'longitude']):
            address = self._extract_address(msg)
            if address:
                result = self._amap_geocode(address)
                if result:
                    return result

        # 用户询问自己的位置
        if any(kw in msg for kw in ['我在哪', '我的位置', '我在哪里', '我现在在哪']):
            # 优先使用浏览器 GPS 坐标
            if user_location and isinstance(user_location, dict):
                lat = user_location.get('latitude')
                lon = user_location.get('longitude')
                if lat and lon:
                    # 使用坐标反查地址
                    address = self._reverse_geocode(lat, lon)
                    if address:
                        return f"根据你的设备GPS定位，你的当前位置是：{address}，经纬度：{lat},{lon}"
                    return f"根据你的设备GPS定位，你的当前位置经纬度是：{lat},{lon}"
            # 回退到 IP 定位
            if user_ip:
                location = self._get_ip_location(user_ip)
                if location and '无法' not in location:
                    return f"根据你的 IP 地址，你的当前位置是：{location}"
                else:
                    return "抱歉，小科暂时无法获取你的位置信息。如果你能告诉我你所在的城市，我可以帮你查询天气或位置信息。"
            return "抱歉，小科暂时无法获取你的位置信息。"

        return ""

    def _extract_city(self, msg: str) -> str:
        """从消息中提取城市名"""
        # 常见城市列表
        cities = [
            '北京', '上海', '广州', '深圳', '杭州', '成都', '武汉', '西安', '重庆',
            '天津', '南京', '长沙', '沈阳', '青岛', '济南', '郑州', '石家庄', '福州',
            '厦门', '南昌', '合肥', '昆明', '贵阳', '南宁', '海口', '太原', '拉萨',
            '兰州', '西宁', '银川', '乌鲁木齐', '哈尔滨', '长春', '大连', '苏州', '无锡',
            '宁波', '温州', '佛山', '东莞', '珠海', '中山', '惠州', '汕头', '湛江',
            '常州', '徐州', '南通', '扬州', '盐城', '昆山', '嘉兴', '绍兴', '金华',
            '台州', '湖州', '芜湖', '蚌埠', '淮南', '马鞍山', '湘潭', '株洲', '衡阳',
            '岳阳', '常德', '张家界', '益阳', '邵阳', '娄底', '郴州', '永州', '怀化',
        ]
        for city in cities:
            if city in msg:
                return city
        return ""

    def _extract_place(self, msg: str) -> str:
        """从消息中提取地点名称"""
        place = ""

        # 模式1: "XX在哪里"、"XX在哪儿"、"XX怎么走" -> 提取XX
        for suffix in ['在哪里', '在哪儿', '怎么走']:
            if suffix in msg:
                idx = msg.find(suffix)
                place = msg[:idx].strip()
                if place:
                    return place

        # 模式2: "帮我找XX"、"搜索XX" -> 提取XX
        for prefix in ['帮我找', '搜索', '找一下', '查找']:
            if prefix in msg:
                parts = msg.split(prefix)
                if len(parts) >= 2:
                    place = parts[-1].strip()
                    # 去掉后缀
                    for s in ['附近', '那边', '这里', '那儿']:
                        if s in place:
                            place = place.split(s)[0].strip()
                    if place:
                        return place

        # 模式3: "离我最近的XX"、"离我XX" -> 提取XX
        for prefix in ['离我最近的', '离我', '最近的']:
            if prefix in msg:
                parts = msg.split(prefix)
                if len(parts) >= 2:
                    place = parts[-1].strip()
                    if place:
                        return place

        # 模式4: "我在XX"、"我的位置在XX" -> 提取XX
        for prefix in ['我在', '我现在在', '我的位置在']:
            if prefix in msg:
                parts = msg.split(prefix)
                if len(parts) >= 2:
                    place = parts[-1].strip()
                    if place:
                        return place

        return place

    def _extract_address(self, msg: str) -> str:
        """从消息中提取地址"""
        for kw in ['经纬度', '坐标', 'latitude', 'longitude']:
            if kw in msg:
                # 提取 kw 之后的内容作为地址
                idx = msg.find(kw)
                addr = msg[idx + len(kw):].strip()
                if addr:
                    return addr
        return ""

    def _amap_weather(self, city: str) -> str:
        """调用天气工具"""
        try:
            from ..tools.setup import _amap_weather_impl
            import json
            result = _amap_weather_impl(city)
            if result.get('success'):
                data = result['data']
                if isinstance(data, str):
                    data = json.loads(data)
                weather = data.get('weather', '未知')
                temp = data.get('temperature', '?')
                humidity = data.get('humidity', '?')
                wind = data.get('wind_speed', '?')
                return f"{city}今天的天气：{weather}，温度 {temp}，湿度 {humidity}，风速 {wind}。"
            return ""
        except Exception as e:
            logger.error(f"天气查询失败: {e}")
            return ""

    def _amap_place_search(self, keywords: str) -> str:
        """调用地点搜索工具"""
        try:
            from ..tools.setup import _amap_place_search_impl
            import json
            result = _amap_place_search_impl(keywords)
            if result.get('success'):
                data = result.get('data', '')
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
                if isinstance(data, dict):
                    pois = data.get('pois', [])
                    if pois:
                        first = pois[0]
                        name = first.get('name', keywords)
                        address = first.get('address', '未知地址')
                        location = first.get('location', '')
                        return f"{keywords}的位置信息：{name}，地址：{address}，经纬度：{location}。"
                    return f"抱歉，未找到 '{keywords}' 的位置信息。"
                elif isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    name = first.get('name', keywords)
                    address = first.get('address', '未知地址')
                    return f"{keywords}的位置信息：{name}，地址：{address}。"
            return ""
        except Exception as e:
            logger.error(f"地点搜索失败: {e}")
            return ""

    def _amap_geocode(self, address: str) -> str:
        """调用地理编码工具"""
        try:
            from ..tools.setup import _amap_geocode_impl
            import json
            result = _amap_geocode_impl(address)
            if result.get('success'):
                data = result.get('data', '')
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        pass
                if isinstance(data, dict):
                    location = data.get('location', '')
                    if location:
                        return f"{address}的经纬度坐标是：{location}。"
                elif isinstance(data, list) and len(data) > 0:
                    location = data[0].get('location', '')
                    if location:
                        return f"{address}的经纬度坐标是：{location}。"
            return ""
        except Exception as e:
            logger.error(f"地理编码失败: {e}")
            return ""

    def _get_ip_location(self, ip: str) -> str:
        """
        通过 IP 获取地理位置

        Args:
            ip: IP 地址

        Returns:
            位置描述字符串
        """
        import urllib.request
        import json

        # 跳过内网 IP
        if not ip or ip.startswith(('10.', '172.16.', '172.17.', '172.18.', '172.19.',
                                    '172.20.', '172.21.', '172.22.', '172.23.',
                                    '172.24.', '172.25.', '172.26.', '172.27.',
                                    '172.28.', '172.29.', '172.30.', '172.31.',
                                    '192.168.', '127.', 'localhost')):
            return "无法获取位置信息（内网IP或无效IP）"

        # 先尝试从缓存获取
        try:
            from ai_services.cache.redis_cache import cache_get, cache_set
            cache_key = f"cache:ip_location:{ip}"
            cached = cache_get(cache_key)
            if cached:
                logger.info(f"IP 定位缓存命中: {ip}")
                return cached.get('location', '')
        except ImportError:
            pass

        # 尝试 ipapi.co
        try:
            url = f"https://ipapi.co/{ip}/json/"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            city = data.get('city') or data.get('region')
            if city:
                location = (f"国家: {data.get('country_name', '未知')}, "
                        f"省份: {data.get('region', '未知')}, "
                        f"城市: {data.get('city', '未知')}, "
                        f"ISP: {data.get('org', '未知')}, "
                        f"经纬度: {data.get('latitude', '?')},{data.get('longitude', '?')}")
                # 缓存结果（24小时）
                try:
                    from ai_services.cache.redis_cache import cache_set
                    cache_key = f"cache:ip_location:{ip}"
                    cache_set(cache_key, {'location': location}, ttl=86400)
                except ImportError:
                    pass
                return location
        except Exception as e:
            logger.warning(f"ipapi.co 查询失败: {e}")

        # 尝试 ip-api.com
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,regionName,city,district,isp,org,lat,lon"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == 'success':
                location = (f"国家: {data.get('country', '未知')} ({data.get('countryCode', '')}), "
                        f"省份: {data.get('regionName', '未知')}, "
                        f"城市: {data.get('city', '未知')}, "
                        f"区/县: {data.get('district', '未知')}, "
                        f"ISP: {data.get('isp', '未知')}, "
                        f"经纬度: {data.get('lat', '?')},{data.get('lon', '?')}")
                # 缓存结果（24小时）
                try:
                    from ai_services.cache.redis_cache import cache_set
                    cache_key = f"cache:ip_location:{ip}"
                    cache_set(cache_key, {'location': location}, ttl=86400)
                except ImportError:
                    pass
                return location
        except Exception as e:
            logger.warning(f"ip-api.com 查询失败: {e}")

        # 尝试 ipinfo.io
        try:
            url = f"https://ipinfo.io/{ip}/json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
            if data.get('city') or data.get('region'):
                loc = data.get('loc', '')
                location = (f"国家: {data.get('country', '未知')}, "
                        f"省份: {data.get('region', '未知')}, "
                        f"城市: {data.get('city', '未知')}, "
                        f"ISP: {data.get('org', '未知')}, "
                        f"经纬度: {loc or '?'}")
                # 缓存结果（24小时）
                try:
                    from ai_services.cache.redis_cache import cache_set
                    cache_key = f"cache:ip_location:{ip}"
                    cache_set(cache_key, {'location': location}, ttl=86400)
                except ImportError:
                    pass
                return location
        except Exception as e:
            logger.warning(f"ipinfo.io 查询失败: {e}")

        return "无法获取位置信息（该IP可能不支持定位）"

    def _reverse_geocode(self, lat: float, lon: float) -> str:
        """
        通过经纬度坐标反查地址（使用 Nominatim 免费的逆地理编码服务）

        Args:
            lat: 纬度
            lon: 经度

        Returns:
            地址描述字符串
        """
        import urllib.request
        import json

        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))

            if data.get('display_name'):
                addr = data.get('address', {})
                parts = []
                # 尝试构建更简洁的地址
                for key in ['city', 'town', 'village', 'county', 'state', 'country']:
                    val = addr.get(key)
                    if val:
                        parts.append(val)
                if parts:
                    return ' '.join(parts)
                return data.get('display_name', '')[:100]
        except Exception as e:
            logger.warning(f"逆地理编码失败: {e}")

        return ""

    async def achat(self, user_message: str) -> str:
        """
        异步处理用户消息并返回回复

        Args:
            user_message: 用户输入的消息

        Returns:
            小科的回复内容
        """
        # 记录用户消息
        self.add_message('user', user_message)

        # 构建 API 请求（包含 system prompt）
        messages = [
            {"role": "system", "content": self.get_system_prompt()}
        ] + [msg.to_dict() for msg in self.conversation_history]

        try:
            reply = await self._call_minimax_api_async(messages)
            # 记录助手回复
            self.add_message('assistant', reply)
            return reply
        except Exception as e:
            error_reply = f'抱歉，小科暂时无法回答这个问题。'
            self.add_message('assistant', error_reply)
            logger.error(f"[XiaoyuAgent] achat 错误: {e}")
            return error_reply

    def _call_minimax_api_sync(self, messages: list[dict[str, str]]) -> str:
        """
        同步调用 MiniMax API（支持 function calling）

        Args:
            messages: 对话消息列表

        Returns:
            API 返回的回复文本
        """
        import urllib.request
        import urllib.error

        # 使用 OpenAI 兼容格式的 endpoint
        # 确保 base_url 不包含路径
        base = self.base_url.split('/anthropic')[0]  # 处理 https://api.minimaxi.com/anthropic/v1 -> https://api.minimaxi.com
        url = f"{base}/v1/chat/completions"

        # 构建 tools
        tools = self._get_tools()

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }

        # 如果有工具，添加到 payload 中
        if tools:
            payload["tools"] = tools

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            },
            method='POST'
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return self._handle_response(result)

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else str(e)
            logger.error(f"[XiaoyuAgent] HTTP 错误: {e.code} - {error_body}")
            raise Exception(f'API 请求失败: {error_body}')
        except Exception as e:
            logger.error(f"[XiaoyuAgent] API 调用失败: {e}")
            raise

    def _get_tools(self) -> list:
        """获取工具定义列表"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取某个城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "城市名称，如：北京、上海、湘潭"
                            }
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_place",
                    "description": "搜索某个地点的位置信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "string",
                                "description": "搜索关键词，如：故宫、天安门、东方明珠"
                            },
                            "city": {
                                "type": "string",
                                "description": "城市名称（可选），如：上海"
                            }
                        },
                        "required": ["keywords"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "geocode",
                    "description": "将地址转换为经纬度坐标",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "address": {
                                "type": "string",
                                "description": "详细地址，如：北京市朝阳区天安门广场"
                            },
                            "city": {
                                "type": "string",
                                "description": "城市名称（可选）"
                            }
                        },
                        "required": ["address"]
                    }
                }
            }
        ]

    def _handle_response(self, result: dict) -> str:
        """
        处理 API 响应，支持 function calling 循环

        Args:
            result: API 响应字典

        Returns:
            最终的回复文本
        """
        import urllib.request
        import urllib.error

        # 检查是否是 function calling 响应
        choices = result.get('choices', [])
        if not choices:
            return "抱歉，小科暂时无法回答这个问题。"

        choice = choices[0]
        message = choice.get('message', {})

        # 检查是否有 tool_calls
        tool_calls = message.get('tool_calls', [])
        finish_reason = choice.get('finish_reason', '')

        # 如果有工具调用
        if tool_calls and finish_reason == 'tool_calls':
            # 将助手的 tool_call 响应添加到消息历史
            assistant_msg = {
                "role": "assistant",
                "content": message.get('content', ''),
                "tool_calls": message.get('tool_calls', [])
            }

            # 执行每个工具调用
            tool_results = []
            for tool_call in tool_calls:
                func = tool_call.get('function', {})
                func_name = func.get('name', '')
                func_args = func.get('arguments', '{}')

                # 解析参数
                try:
                    args = json.loads(func_args) if isinstance(func_args, str) else func_args
                except:
                    args = {}

                # 调用工具
                tool_result = self._execute_tool(func_name, args)
                tool_results.append({
                    "tool_call_id": tool_call.get('id', ''),
                    "role": "tool",
                    "content": tool_result
                })

            # 构建新的消息列表进行下一轮对话
            # 需要包含系统提示和完整历史
            all_messages = [{"role": "system", "content": self.get_system_prompt()}]

            # 添加对话历史
            for msg in self.conversation_history:
                all_messages.append(msg.to_dict())

            # 添加助手的消息
            all_messages.append(assistant_msg)

            # 添加工具结果
            for tr in tool_results:
                all_messages.append(tr)

            # 再次调用 API 获取最终回复
            base = self.base_url.split('/anthropic')[0]
            url = f"{base}/v1/chat/completions"
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": all_messages,
                "tools": self._get_tools()
            }

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}'
                },
                method='POST'
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    choices = result.get('choices', [])
                    if choices:
                        content = choices[0].get('message', {}).get('content', '抱歉，小科暂时无法回答这个问题。')
                        import re
                        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
                        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
                        return content.strip()
            except Exception as e:
                logger.error(f"[XiaoyuAgent] function calling 第二轮调用失败: {e}")

        # 普通回复
        content = message.get('content', '抱歉，小科暂时无法回答这个问题。')
        # 过滤掉思考过程标签
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL)
        return content.strip()

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """
        执行工具并返回结果

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果（字符串）
        """
        try:
            if tool_name == 'get_weather':
                city = arguments.get('city', '')
                if city:
                    result = self._amap_weather(city)
                    return result if result else "天气查询暂时不可用"

            elif tool_name == 'search_place':
                keywords = arguments.get('keywords', '')
                city = arguments.get('city', '全国')
                if keywords:
                    result = self._amap_place_search(keywords, city)
                    return result if result else "地点搜索暂时不可用"

            elif tool_name == 'geocode':
                address = arguments.get('address', '')
                city = arguments.get('city', '')
                if address:
                    result = self._amap_geocode(address, city)
                    return result if result else "地理编码暂时不可用"

            return f"未知工具: {tool_name}"
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 失败: {e}")
            return f"工具执行出错: {str(e)}"

    async def _call_minimax_api_async(self, messages: list[dict[str, str]]) -> str:
        """
        异步调用 MiniMax API

        Args:
            messages: 对话消息列表

        Returns:
            API 返回的回复文本
        """
        try:
            import aiohttp
        except ImportError:
            logger.warning("aiohttp 未安装，回退到同步调用")
            return self._call_minimax_api_sync(messages)

        url = f"{self.base_url}/messages"

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.get_system_prompt(),
            "messages": messages
        }

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'anthropic-version': '2023-06-01'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    result = await response.json()
                    return self._parse_response(result)

        except aiohttp.ClientError as e:
            logger.error(f"[XiaoyuAgent] aiohttp 错误: {e}")
            raise Exception(f'API 请求失败: {e}')
        except Exception as e:
            logger.error(f"[XiaoyuAgent] 异步 API 调用失败: {e}")
            raise

    def _parse_response(self, result: dict[str, Any]) -> str:
        """
        解析 MiniMax API 响应

        Args:
            result: API 响应字典

        Returns:
            解析后的回复文本
        """
        # MiniMax API 返回格式
        content = result.get('content', [])
        reply = '抱歉，小科暂时无法回答这个问题。'

        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text':
                    reply = item.get('text', reply)
                    break

        return reply

    def chat_with_context(self, user_message: str, context: str) -> str:
        """
        使用上下文信息处理用户消息

        Args:
            user_message: 用户输入的消息
            context: 检索到的上下文信息

        Returns:
            小科的回复内容
        """
        # 格式化提示词
        prompt = format_xiaoyu_prompt(
            user_message=user_message,
            context=context,
        )

        # 记录用户消息（使用格式化后的提示）
        self.add_message('user', user_message)

        try:
            # 直接调用同步 API
            reply = self._call_minimax_api_sync([
                {"role": "user", "content": prompt}
            ])
            self.add_message('assistant', reply)
            return reply
        except Exception as e:
            error_reply = f'抱歉，小科暂时无法回答这个问题。'
            logger.error(f"[XiaoyuAgent] chat_with_context 错误: {e}")
            return error_reply

    def reset(self):
        """重置对话"""
        self.clear_history()


# 全局单例
_xiaoyu_agent: Optional[XiaoyuAgent] = None


def get_xiaoyu_agent() -> XiaoyuAgent:
    """获取小科 Agent 单例"""
    global _xiaoyu_agent
    if _xiaoyu_agent is None:
        _xiaoyu_agent = XiaoyuAgent()
    return _xiaoyu_agent


def reset_xiaoyu_agent() -> None:
    """重置小科 Agent 单例"""
    global _xiaoyu_agent
    if _xiaoyu_agent is not None:
        _xiaoyu_agent.reset()
    _xiaoyu_agent = None
