# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 模块
连接外部工具和服务
"""

from .client import MCPClient, Tool
from .modelscope_client import ModelScopeMCPClient, get_modelscope_client, init_modelscope_client

__all__ = ['MCPClient', 'Tool', 'ModelScopeMCPClient', 'get_modelscope_client', 'init_modelscope_client']
