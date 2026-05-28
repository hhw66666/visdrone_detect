# -*- coding: utf-8 -*-
"""
ModelScope MCP 客户端
使用 Streamable HTTP 协议连接 ModelScope MCP 服务器
"""

import logging
import json
import requests
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ModelScopeMCPClient:
    """
    ModelScope MCP 客户端

    使用 Streamable HTTP 协议连接 ModelScope MCP 服务器
    """

    def __init__(self, server_url: str, api_key: str = ""):
        """
        初始化 ModelScope MCP 客户端

        Args:
            server_url: ModelScope MCP 服务器 URL
            api_key: API Key
        """
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self._session_id: Optional[str] = None
        self._headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
        if self.api_key:
            self._headers['Authorization'] = f'Bearer {self.api_key}'

    def connect(self) -> bool:
        """建立与 MCP 服务器的连接，获取 session_id"""
        try:
            # 发送 initialize 请求
            init_request = {
                'jsonrpc': '2.0',
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'xiaoyu-client', 'version': '1.0'}
                },
                'id': 1
            }

            resp = requests.post(
                self.server_url,
                json=init_request,
                headers=self._headers,
                timeout=10
            )

            if resp.status_code != 200:
                logger.error(f"MCP 初始化失败: {resp.status_code} - {resp.text}")
                return False

            result = resp.json()
            if 'error' in result:
                logger.error(f"MCP 初始化错误: {result['error']}")
                return False

            # 获取 session_id
            self._session_id = resp.headers.get('Mcp-Session-Id')
            if not self._session_id:
                logger.error("MCP 未返回 session_id")
                return False

            logger.info(f"MCP 连接成功，session_id: {self._session_id}")
            logger.info(f"Server: {result.get('result', {}).get('serverInfo', {})}")

            # 发送 initialized 通知
            self._send_notification('notifications/initialized', {})

            return True

        except Exception as e:
            logger.error(f"MCP 连接失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_headers(self) -> dict:
        """获取带 session_id 的请求头"""
        headers = {**self._headers}
        if self._session_id:
            headers['Mcp-Session-Id'] = self._session_id
        return headers

    def _send_notification(self, method: str, params: dict):
        """发送 JSON-RPC 通知（不等待响应）"""
        try:
            notif = {
                'jsonrpc': '2.0',
                'method': method,
                'params': params
            }
            resp = requests.post(
                self.server_url,
                json=notif,
                headers=self._get_headers(),
                timeout=10
            )
            return resp.status_code == 202 or resp.status_code == 200
        except Exception as e:
            logger.warning(f"发送通知 {method} 失败: {e}")
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._session_id is not None

    def list_tools(self) -> list:
        """列出所有可用工具"""
        if not self._session_id:
            logger.warning("MCP 未连接，无法获取工具列表")
            return []

        try:
            req = {
                'jsonrpc': '2.0',
                'method': 'tools/list',
                'params': {},
                'id': 2
            }

            resp = requests.post(
                self.server_url,
                json=req,
                headers=self._get_headers(),
                timeout=10
            )

            if resp.status_code != 200:
                logger.error(f"获取工具列表失败: {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            if 'error' in data:
                logger.error(f"获取工具列表错误: {data['error']}")
                return []

            tools = data.get('result', {}).get('tools', [])
            logger.info(f"获取到 {len(tools)} 个工具")
            return tools

        except Exception as e:
            logger.error(f"获取工具列表异常: {e}")
            import traceback
            traceback.print_exc()
            return []

    def call_tool(self, tool_name: str, arguments: dict, timeout: float = 15.0) -> dict:
        """
        调用 MCP 工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            timeout: 超时秒数

        Returns:
            工具执行结果
        """
        if not self._session_id:
            return {"success": False, "error": "未连接到 ModelScope MCP 服务器"}

        try:
            req = {
                'jsonrpc': '2.0',
                'method': 'tools/call',
                'params': {
                    'name': tool_name,
                    'arguments': arguments
                },
                'id': 3
            }

            resp = requests.post(
                self.server_url,
                json=req,
                headers=self._get_headers(),
                timeout=timeout
            )

            if resp.status_code != 200:
                logger.error(f"调用工具失败: {resp.status_code} - {resp.text}")
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}

            data = resp.json()
            if 'error' in data:
                error_msg = data['error'].get('message', str(data['error']))
                logger.error(f"工具调用错误: {error_msg}")
                return {"success": False, "error": error_msg}

            result = data.get('result', {})
            content = result.get('content', [])
            if content and isinstance(content, list):
                text = content[0].get('text', '')
                is_error = result.get('isError', False)
                if is_error:
                    return {"success": False, "error": text}
                return {"success": True, "data": text}

            return {"success": True, "data": str(result)}

        except Exception as e:
            logger.error(f"调用 MCP 工具 {tool_name} 失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def disconnect(self):
        """断开连接"""
        self._session_id = None


# 全局客户端实例
_mcp_client: Optional[ModelScopeMCPClient] = None


def get_modelscope_client() -> Optional[ModelScopeMCPClient]:
    """获取全局 ModelScope MCP 客户端"""
    global _mcp_client
    return _mcp_client


def init_modelscope_client() -> Optional[ModelScopeMCPClient]:
    """初始化 ModelScope MCP 客户端"""
    global _mcp_client

    try:
        from detect_system.config_loader import CONFIG

        # 从配置中获取 ai_services.mcp 配置
        ai_services = CONFIG.get('configuration', {}).get('ai_services', {})
        mcp_config = ai_services.get('mcp', {})

        if not mcp_config.get('enable', False):
            logger.info("ModelScope MCP 未启用")
            return None

        server_url = mcp_config.get('server_url', '')
        if not server_url:
            logger.warning("ModelScope MCP server_url 未配置")
            return None

        api_key = mcp_config.get('api_key', '')

        _mcp_client = ModelScopeMCPClient(server_url, api_key=api_key)
        connected = _mcp_client.connect()

        if connected:
            tools = _mcp_client.list_tools()
            tool_names = [t.get('name') for t in tools]
            logger.info(f"MCP 可用工具: {tool_names}")
        else:
            logger.warning("MCP 连接失败")

        return _mcp_client

    except Exception as e:
        logger.error(f"初始化 ModelScope MCP 客户端失败: {e}")
        import traceback
        traceback.print_exc()
        return None
