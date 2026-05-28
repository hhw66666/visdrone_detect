# -*- coding: utf-8 -*-
"""
工具注册表
"""

from typing import Any
from pydantic import BaseModel, Field

from .base import Tool, ToolResult


class ToolRegistry(BaseModel):
    """
    工具注册表

    管理所有可用工具的注册和调用
    """
    model_config = {"arbitrary_types_allowed": True}

    tools: dict[str, Tool] = Field(default_factory=dict)
    """工具名称 -> Tool 实例的映射"""

    def register(self, tool: Tool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例

        Raises:
            ValueError: 工具名称已存在
        """
        if tool.name in self.tools:
            raise ValueError(f"工具 {tool.name} 已存在")
        self.tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """
        注销工具

        Args:
            name: 工具名称

        Returns:
            是否成功注销
        """
        if name in self.tools:
            del self.tools[name]
            return True
        return False

    def get(self, name: str) -> Tool | None:
        """
        获取工具

        Args:
            name: 工具名称

        Returns:
            工具实例，如果不存在则返回 None
        """
        return self.tools.get(name)

    def list_tools(self) -> list[Tool]:
        """
        列出所有已注册的工具

        Returns:
            工具列表
        """
        return list(self.tools.values())

    def list_schemas(self) -> list[dict[str, Any]]:
        """
        获取所有工具的模式定义

        Returns:
            工具模式列表（用于给 LLM 了解可用的工具）
        """
        return [tool.get_schema() for tool in self.tools.values()]

    def invoke(self, name: str, **kwargs: Any) -> ToolResult:
        """
        调用工具

        Args:
            name: 工具名称
            **kwargs: 工具输入参数

        Returns:
            ToolResult: 执行结果

        Raises:
            ValueError: 工具不存在
        """
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"工具 {name} 不存在")

        return tool.invoke(**kwargs)

    async def ainvoke(self, name: str, **kwargs: Any) -> ToolResult:
        """
        异步调用工具

        Args:
            name: 工具名称
            **kwargs: 工具输入参数

        Returns:
            ToolResult: 执行结果

        Raises:
            ValueError: 工具不存在
        """
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"工具 {name} 不存在")

        return await tool.ainvoke(**kwargs)

    def clear(self) -> None:
        """清空所有工具"""
        self.tools.clear()

    @property
    def tool_names(self) -> list[str]:
        """获取所有工具名称"""
        return list(self.tools.keys())

    def __len__(self) -> int:
        return len(self.tools)

    def __contains__(self, name: str) -> bool:
        return name in self.tools


# 全局工具注册表实例
_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """
    获取全局工具注册表单例

    Returns:
        ToolRegistry 实例
    """
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
