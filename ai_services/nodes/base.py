# -*- coding: utf-8 -*-
"""
节点基类定义
"""

from typing import Any, Callable, Awaitable, TYPE_CHECKING
from pydantic import BaseModel, Field
from enum import Enum

if TYPE_CHECKING:
    from ..core.state import AgentState


class NodeStatus(str, Enum):
    """节点执行状态"""
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过（不需要执行）
    WAITING = "waiting"      # 等待（需要其他条件）


class NodeResult(BaseModel):
    """节点执行结果"""
    status: NodeStatus
    state_updates: dict[str, Any] = Field(default_factory=dict)
    """状态更新，会被合并到 AgentState"""
    output: Any = None
    """节点输出"""
    error: str | None = None
    """错误信息"""
    next_node: str | None = None
    """下一个节点名称（用于条件路由）"""

    class Config:
        arbitrary_types_allowed = True


# 节点函数类型
NodeFunc = Callable[["AgentState"], NodeResult | None]
AsyncNodeFunc = Awaitable[NodeResult | None]


class Node:
    """
    节点定义

    表示 Agent 工作流中的一个步骤
    """

    def __init__(
        self,
        name: str,
        handler: NodeFunc | AsyncNodeFunc,
        description: str = "",
        required_state_keys: list[str] | None = None,
        output_key: str | None = None,
    ):
        """
        初始化节点

        Args:
            name: 节点名称（唯一标识）
            handler: 节点处理函数
            description: 节点描述
            required_state_keys: 所需的 AgentState 键
            output_key: 输出结果存储的键名
        """
        self.name = name
        self.handler = handler
        self.description = description
        self.required_state_keys = required_state_keys or []
        self.output_key = output_key

    async def execute(self, state: "AgentState") -> NodeResult | None:
        """
        异步执行节点

        Args:
            state: Agent 状态

        Returns:
            NodeResult 或 None（如果被跳过）
        """
        import asyncio

        # 检查必需的状态键
        for key in self.required_state_keys:
            if key not in state:
                return NodeResult(
                    status=NodeStatus.WAITING,
                    error=f"缺少必需的状态键: {key}"
                )

        try:
            if asyncio.iscoroutinefunction(self.handler):
                result = await self.handler(state)
            else:
                # 在线程池中执行同步函数
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: self.handler(state))

            if result is None:
                return NodeResult(status=NodeStatus.SKIPPED)

            return result

        except Exception as e:
            return NodeResult(
                status=NodeStatus.FAILED,
                error=str(e)
            )

    def __repr__(self) -> str:
        return f"<Node(name='{self.name}')>"


def create_node(
    name: str,
    description: str = "",
    required_state_keys: list[str] | None = None,
    output_key: str | None = None,
) -> Callable[[NodeFunc], Node]:
    """
    节点装饰器

    用法:
        @create_node(name="my_node", description="我的节点")
        def my_node(state: AgentState) -> NodeResult:
            ...

    Args:
        name: 节点名称
        description: 节点描述
        required_state_keys: 所需的 AgentState 键
        output_key: 输出结果存储的键名

    Returns:
        装饰器函数
    """
    def decorator(func: NodeFunc) -> Node:
        return Node(
            name=name,
            handler=func,
            description=description,
            required_state_keys=required_state_keys,
            output_key=output_key,
        )
    return decorator
