# -*- coding: utf-8 -*-
"""
小科客服 Agent 节点
"""

from typing import Any
import json

from ..core.state import AgentState
from .base import NodeResult, NodeStatus


# ============ 意图分类节点 ============


def classify_intent_node(state: AgentState) -> NodeResult:
    """
    意图分类节点

    分析用户消息，判断用户意图
    """
    messages = state.get("messages", [])
    if not messages:
        return NodeResult(status=NodeStatus.FAILED, error="没有消息")

    last_message = messages[-1]
    if last_message.get("role") != "user":
        return NodeResult(status=NodeStatus.SKIPPED)

    user_content = last_message.get("content", "")

    # 意图分类
    intent = "general"  # 默认
    keywords_intent = {
        "检测": "detection",
        "上传": "detection",
        "识别": "detection",
        "历史": "history",
        "记录": "history",
        "统计": "statistics",
        "多少人": "statistics",
        "多少车": "statistics",
        "怎么": "guide",
        "如何": "guide",
        "帮助": "guide",
        "问题": "support",
        "错误": "support",
    }

    for keyword, intent_name in keywords_intent.items():
        if keyword in user_content:
            intent = intent_name
            break

    # 更新状态
    state_updates = {
        "intermediate_values": {
            **state.get("intermediate_values", {}),
            "intent": intent,
            "original_query": user_content,
        }
    }

    return NodeResult(
        status=NodeStatus.SUCCESS,
        state_updates=state_updates,
        output={"intent": intent},
        next_node="rag_retrieve"  # 下一步是 RAG 检索
    )


# ============ RAG 检索节点 ============


def rag_retrieve_node(state: AgentState) -> NodeResult:
    """
    RAG 检索节点

    根据用户问题检索相关上下文
    """
    retriever = state.get("intermediate_values", {}).get("retriever")

    if retriever is None:
        # RAG 未启用，跳过
        return NodeResult(status=NodeStatus.SKIPPED)

    user_query = state.get("intermediate_values", {}).get("original_query", "")
    if not user_query:
        return NodeResult(status=NodeStatus.SKIPPED)

    try:
        context = retriever.get_context(user_query, top_k=3)

        state_updates = {
            "intermediate_values": {
                **state.get("intermediate_values", {}),
                "retrieved_context": context,
            }
        }

        return NodeResult(
            status=NodeStatus.SUCCESS,
            state_updates=state_updates,
            output={"context": context},
            next_node="should_use_tool"
        )

    except Exception as e:
        return NodeResult(
            status=NodeStatus.SUCCESS,  # RAG 失败不影响主流程
            state_updates={},
            error=f"RAG 检索失败: {e}",
            next_node="should_use_tool"
        )


# ============ 条件判断节点 ============


def should_use_tool_node(state: AgentState) -> NodeResult:
    """
    工具使用条件判断节点

    判断是否需要调用工具
    """
    # 简单的关键词匹配
    user_query = state.get("intermediate_values", {}).get("original_query", "")
    intent = state.get("intermediate_values", {}).get("intent", "general")

    # 明确需要工具的意图
    tool_intents = {"statistics", "query"}

    if intent in tool_intents:
        return NodeResult(
            status=NodeStatus.SUCCESS,
            output={"should_use_tool": True, "reason": f"意图 {intent} 需要查询数据"},
            next_node="call_tool"
        )

    # 检查是否询问具体数据
    data_keywords = ["多少", "统计", "查询", "记录数"]
    if any(kw in user_query for kw in data_keywords):
        return NodeResult(
            status=NodeStatus.SUCCESS,
            output={"should_use_tool": True, "reason": "用户询问数据相关问题"},
            next_node="call_tool"
        )

    # 默认不需要工具
    return NodeResult(
        status=NodeStatus.SUCCESS,
        output={"should_use_tool": False},
        next_node="generate_response"
    )


# ============ 工具调用节点 ============


def call_tool_node(state: AgentState) -> NodeResult:
    """
    工具调用节点

    执行具体的工具调用
    """
    from ..tools import get_tool_registry

    user_query = state.get("intermediate_values", {}).get("original_query", "")
    intent = state.get("intermediate_values", {}).get("intent", "general")

    registry = get_tool_registry()
    tools = registry.list_schemas()

    # 根据意图选择工具
    tool_name = None
    tool_args = {}

    if intent == "statistics":
        # 尝试使用数据库查询工具
        if registry.get("query_detection_records"):
            tool_name = "query_detection_records"
            # 简单解析查询意图
            if "检测" in user_query and "多少" in user_query:
                tool_args = {"sql": "SELECT COUNT(*) as count FROM detection_record"}
            else:
                tool_args = {"sql": "SELECT * FROM detection_record LIMIT 10"}

    elif intent == "history":
        if registry.get("query_detection_records"):
            tool_name = "query_detection_records"
            tool_args = {"sql": "SELECT * FROM detection_record ORDER BY created_at DESC LIMIT 10"}

    # 如果没有匹配的意图和工具
    if tool_name is None:
        return NodeResult(
            status=NodeStatus.SUCCESS,
            output={"tool_called": False, "reason": "没有可用的工具"},
            next_node="generate_response"
        )

    try:
        result = registry.invoke(tool_name, **tool_args)

        state_updates = {
            "tool_calls": state.get("tool_calls", []) + [
                {
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": result.output if result.success else None,
                    "error": result.error,
                }
            ],
            "intermediate_values": {
                **state.get("intermediate_values", {}),
                "tool_result": result.output if result.success else None,
                "tool_error": result.error,
            }
        }

        return NodeResult(
            status=NodeStatus.SUCCESS,
            state_updates=state_updates,
            output={
                "tool_called": True,
                "tool_name": tool_name,
                "result": result.output
            },
            next_node="generate_response"
        )

    except Exception as e:
        return NodeResult(
            status=NodeStatus.SUCCESS,  # 工具调用失败不阻断
            output={"tool_called": False, "error": str(e)},
            next_node="generate_response"
        )


# ============ 生成回复节点 ============


def generate_response_node(state: AgentState) -> NodeResult:
    """
    生成回复节点

    调用 LLM 生成最终回复
    """
    from ..agents.xiaoyu import get_xiaoyu_agent

    user_query = state.get("intermediate_values", {}).get("original_query", "")
    context = state.get("intermediate_values", {}).get("retrieved_context", "")
    tool_result = state.get("intermediate_values", {}).get("tool_result")

    # 构建增强的输入
    enhanced_input = user_query

    if context:
        enhanced_input = f"【相关上下文】\n{context}\n\n【用户问题】\n{user_query}"

    if tool_result:
        enhanced_input = f"【工具查询结果】\n{tool_result}\n\n【用户问题】\n{user_query}"

    try:
        agent = get_xiaoyu_agent()

        # 调用 Agent（同步）
        response = agent.chat(enhanced_input)

        # 更新消息历史
        assistant_message = {"role": "assistant", "content": response}
        new_messages = state.get("messages", []) + [assistant_message]

        state_updates = {
            "messages": new_messages,
        }

        return NodeResult(
            status=NodeStatus.SUCCESS,
            state_updates=state_updates,
            output={"response": response}
            # 没有 next_node，表示流程结束
        )

    except Exception as e:
        return NodeResult(
            status=NodeStatus.FAILED,
            error=f"生成回复失败: {str(e)}"
        )
