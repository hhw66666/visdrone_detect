# -*- coding: utf-8 -*-
"""
MCP 客户端
管理工具注册和调用
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, List, Optional
import json


class Tool:
    """
    工具定义

    表示一个可调用的外部工具
    """

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], handler: Callable = None):
        """
        初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入参数模式
            handler: 处理函数
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def __repr__(self):
        return f"<Tool(name='{self.name}')>"

    def invoke(self, **kwargs) -> Any:
        """
        调用工具

        Args:
            **kwargs: 工具输入参数

        Returns:
            工具执行结果
        """
        if self.handler is None:
            raise NotImplementedError(f"工具 {self.name} 未设置处理函数")

        return self.handler(**kwargs)


class MCPClient:
    """
    MCP 客户端

    管理工具的注册和调用
    """

    def __init__(self, name: str = "MCP Client"):
        """
        初始化 MCP 客户端

        Args:
            name: 客户端名称
        """
        self.name = name
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool):
        """
        注册工具

        Args:
            tool: 工具实例
        """
        self.tools[tool.name] = tool

    def register_tools(self, tools: List[Tool]):
        """
        批量注册工具

        Args:
            tools: 工具实例列表
        """
        for tool in tools:
            self.register_tool(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在则返回 None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[Tool]:
        """
        列出所有已注册的工具

        Returns:
            工具列表
        """
        return list(self.tools.values())

    def invoke_tool(self, name: str, **kwargs) -> Any:
        """
        调用工具

        Args:
            name: 工具名称
            **kwargs: 工具输入参数

        Returns:
            工具执行结果
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"工具 {name} 不存在")

        return tool.invoke(**kwargs)

    def remove_tool(self, name: str) -> bool:
        """
        移除工具

        Args:
            name: 工具名称

        Returns:
            是否成功移除
        """
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def clear_tools(self):
        """清空所有工具"""
        self.tools.clear()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的模式定义（用于给 AI 了解可用的工具）

        Returns:
            工具模式列表
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in self.tools.values()
        ]


# 全局 MCP 客户端实例
_mcp_client = None

def get_mcp_client() -> MCPClient:
    """获取全局 MCP 客户端实例"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


# 预定义的工具工厂函数
def create_database_tool(query_handler: Callable) -> Tool:
    """
    创建数据库查询工具

    Args:
        query_handler: 查询处理函数

    Returns:
        数据库工具
    """
    return Tool(
        name="query_database",
        description="执行数据库查询，返回检测记录等信息",
        input_schema={
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL 查询语句"
                }
            },
            "required": ["sql"]
        },
        handler=query_handler
    )


def create_file_tool(read_handler: Callable) -> Tool:
    """
    创建文件读取工具

    Args:
        read_handler: 文件读取处理函数

    Returns:
        文件读取工具
    """
    return Tool(
        name="read_file",
        description="读取文件内容",
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                }
            },
            "required": ["path"]
        },
        handler=read_handler
    )


def create_api_tool(call_handler: Callable) -> Tool:
    """
    创建 API 调用工具

    Args:
        call_handler: API 调用处理函数

    Returns:
        API 调用工具
    """
    return Tool(
        name="call_api",
        description="调用外部 API",
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "API URL"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP 方法",
                    "enum": ["GET", "POST", "PUT", "DELETE"]
                },
                "data": {
                    "type": "object",
                    "description": "请求数据"
                }
            },
            "required": ["url", "method"]
        },
        handler=call_handler
    )
