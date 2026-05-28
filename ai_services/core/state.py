# -*- coding: utf-8 -*-
"""
Agent 状态定义
使用 TypedDict 和 Pydantic 确保类型安全
"""

from enum import Enum
from typing import TypedDict, NotRequired, Literal, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent 运行状态"""
    IDLE = "idle"
    RUNNING = "running"
    WAITING_FOR_TOOL = "waiting_for_tool"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"


class ToolCall(BaseModel):
    """工具调用记录"""
    tool_name: str
    arguments: dict[str, Any]
    result: Any = None
    error: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: float | None = None


class AgentState(TypedDict, total=False):
    """
    Agent 核心状态机状态定义

    使用 TypedDict 确保：
    1. 编译时类型检查
    2. IDE 自动补全
    3. 文档化状态字段
    """
    # ===== 对话历史 =====
    messages: list[dict[str, Any]]  # [{"role": "user", "content": "..."}]

    # ===== 步骤控制（防止死循环） =====
    current_step: int                    # 当前执行步骤
    max_steps: int                      # 最大步骤数（退出条件）
    last_step_at: float                  # 上一步的时间戳（超时检测）

    # ===== 中间变量追踪 =====
    intermediate_values: dict[str, Any]   # {"context": "...", "intent": "...", ...}
    tool_calls: list[ToolCall]          # 工具调用历史

    # ===== 错误处理 =====
    last_error: str | None              # 最近一次错误
    error_history: list[dict[str, Any]] # 错误历史 [{"error": "...", "step": 1}, ...]
    retry_count: int                    # 当前重试次数

    # ===== 状态 =====
    status: AgentStatus                  # 当前状态
    finish_reason: str | None           # 结束原因


class AgentResult(BaseModel):
    """
    Agent 执行结果
    用于返回给调用方的结构化结果
    """
    success: bool
    response: str = ""
    messages: list[dict[str, Any]] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    intermediate_values: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    steps_used: int = 0
    finish_reason: str | None = None
    total_duration_ms: float | None = None

    class Config:
        # 允许任意类型
        arbitrary_types_allowed = True


def create_initial_state(
    messages: list[dict[str, Any]] | None = None,
    max_steps: int = 10,
    **kwargs
) -> AgentState:
    """
    创建初始状态

    Args:
        messages: 初始消息列表
        max_steps: 最大迭代次数
        **kwargs: 其他初始状态字段

    Returns:
        AgentState: 初始状态字典
    """
    import time

    return AgentState(
        messages=messages or [],
        current_step=0,
        max_steps=max_steps,
        last_step_at=time.time(),
        intermediate_values={},
        tool_calls=[],
        last_error=None,
        error_history=[],
        retry_count=0,
        status=AgentStatus.IDLE,
        finish_reason=None,
        **kwargs
    )


def state_to_result(state: AgentState, duration_ms: float | None = None) -> AgentResult:
    """
    将状态转换为结果

    Args:
        state: AgentState
        duration_ms: 总耗时

    Returns:
        AgentResult
    """
    return AgentResult(
        success=state["status"] == AgentStatus.COMPLETED,
        response=_get_last_response(state["messages"]),
        messages=state["messages"],
        tool_calls=[tc.model_dump() if isinstance(tc, ToolCall) else tc for tc in state["tool_calls"]],
        intermediate_values=state["intermediate_values"],
        error=state.get("last_error"),
        steps_used=state["current_step"],
        finish_reason=state.get("finish_reason"),
        total_duration_ms=duration_ms,
    )


def _get_last_response(messages: list[dict[str, Any]]) -> str:
    """获取最后一条助手回复"""
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            return msg.get("content", "")
    return ""
