# -*- coding: utf-8 -*-
"""
图状态定义
"""

from typing import Any, TypedDict, NotRequired
from enum import Enum


class GraphNode(str, Enum):
    """图的节点"""
    START = "start"
    CLASSIFY_INTENT = "classify_intent"
    RAG_RETRIEVE = "rag_retrieve"
    SHOULD_USE_TOOL = "should_use_tool"
    CALL_TOOL = "call_tool"
    GENERATE_RESPONSE = "generate_response"
    END = "end"


class GraphState(TypedDict, total=False):
    """
    图执行状态

    用于 LangGraph 或简化状态图的统一状态定义
    """
    # ===== 输入 =====
    user_input: str                    # 用户原始输入

    # ===== 对话 =====
    messages: list[dict[str, Any]]      # 对话历史

    # ===== 意图识别 =====
    intent: str | None                  # 识别的意图
    intent_confidence: float | None     # 意图置信度

    # ===== RAG =====
    retrieved_context: str | None       # 检索到的上下文
    retrieve_success: bool              # 检索是否成功

    # ===== 工具 =====
    should_use_tool: bool              # 是否使用工具
    tool_name: str | None              # 要使用的工具名
    tool_args: dict[str, Any] | None   # 工具参数
    tool_result: Any | None            # 工具执行结果
    tool_error: str | None             # 工具执行错误

    # ===== 生成 =====
    generated_response: str | None     # 生成的回复
    generation_error: str | None       # 生成错误

    # ===== 控制流 =====
    current_node: GraphNode            # 当前节点
    next_node: GraphNode | None       # 下一个节点
    steps: int                          # 已执行步骤数
    max_steps: int                     # 最大步骤数

    # ===== 结果 =====
    final_response: str | None         # 最终回复
    success: bool                      # 是否成功
    error: str | None                  # 错误信息


def create_graph_state(
    user_input: str,
    max_steps: int = 10,
    **kwargs
) -> GraphState:
    """
    创建初始图状态

    Args:
        user_input: 用户输入
        max_steps: 最大步骤数
        **kwargs: 其他初始字段

    Returns:
        GraphState: 初始状态
    """
    return GraphState(
        user_input=user_input,
        messages=[{"role": "user", "content": user_input}],
        intent=None,
        intent_confidence=None,
        retrieved_context=None,
        retrieve_success=False,
        should_use_tool=False,
        tool_name=None,
        tool_args=None,
        tool_result=None,
        tool_error=None,
        generated_response=None,
        generation_error=None,
        current_node=GraphNode.START,
        next_node=GraphNode.CLASSIFY_INTENT,
        steps=0,
        max_steps=max_steps,
        final_response=None,
        success=False,
        error=None,
        **kwargs
    )
