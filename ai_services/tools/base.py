# -*- coding: utf-8 -*-
"""
工具基类定义
"""

from typing import Any, Callable, Awaitable
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ToolCategory(str, Enum):
    """工具类别"""
    QUERY = "query"           # 数据查询
    RETRIEVAL = "retrieval"   # 信息检索
    COMPUTATION = "computation"  # 计算
    API = "api"               # API 调用
    FILE = "file"             # 文件操作
    CUSTOM = "custom"         # 自定义


class Tool:
    """
    工具定义

    表示一个可被 Agent 调用的外部能力
    """

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Callable[..., Any] | None = None,
        async_handler: Callable[..., Awaitable[Any]] | None = None,
        category: ToolCategory = ToolCategory.CUSTOM,
        metadata: dict[str, Any] | None = None,
    ):
        """
        初始化工具

        Args:
            name: 工具名称（唯一标识）
            description: 工具描述（给 LLM 看的）
            input_schema: 输入参数模式（JSON Schema 格式）
            handler: 同步处理函数
            async_handler: 异步处理函数
            category: 工具类别
            metadata: 额外元数据
        """
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler
        self.async_handler = async_handler
        self.category = category
        self.metadata = metadata or {}

        # 验证至少有一个 handler
        if handler is None and async_handler is None:
            raise ValueError(f"Tool {name} 必须提供 handler 或 async_handler")

    def invoke(self, **kwargs: Any) -> ToolResult:
        """
        同步调用工具

        Args:
            **kwargs: 工具输入参数

        Returns:
            ToolResult: 执行结果
        """
        import time

        start_time = time.time()

        try:
            if self.handler is None:
                raise NotImplementedError(f"Tool {self.name} 不支持同步调用")

            output = self.handler(**kwargs)

            # 如果 handler 返回的是 ToolResult，直接返回
            if isinstance(output, ToolResult):
                return output

            return ToolResult(
                success=True,
                output=output,
                duration_ms=(time.time() - start_time) * 1000
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )

    async def ainvoke(self, **kwargs: Any) -> ToolResult:
        """
        异步调用工具

        Args:
            **kwargs: 工具输入参数

        Returns:
            ToolResult: 执行结果
        """
        import time

        start_time = time.time()

        try:
            if self.async_handler:
                output = await self.async_handler(**kwargs)
            elif self.handler:
                # 如果没有异步 handler，在线程池中执行同步 handler
                import asyncio
                loop = asyncio.get_event_loop()
                output = await loop.run_in_executor(None, lambda: self.handler(**kwargs))
            else:
                raise NotImplementedError(f"Tool {self.name} 不支持异步调用")

            if isinstance(output, ToolResult):
                return output

            return ToolResult(
                success=True,
                output=output,
                duration_ms=(time.time() - start_time) * 1000
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000
            )

    def get_schema(self) -> dict[str, Any]:
        """
        获取工具模式定义（用于给 LLM 了解工具）

        Returns:
            工具模式字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "category": self.category.value if isinstance(self.category, ToolCategory) else self.category,
            **self.metadata
        }

    def __repr__(self) -> str:
        return f"<Tool(name='{self.name}', category='{self.category}')>"
