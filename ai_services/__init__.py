# -*- coding: utf-8 -*-
"""
AI 服务模块
包含 Agent、RAG、MCP、LangChain 等 AI 服务的抽象和实现
"""

# Core - 核心组件
from .core.state import AgentState, AgentResult, AgentStatus
from .core.executor import AgentExecutor
from .core.exceptions import AgentError, ToolError, MaxIterationsError

# Agents - Agent 实现
from .agents.base import BaseAgent, Message
from .agents.xiaoyu import XiaoyuAgent, get_xiaoyu_agent

# Prompts - 提示词模板
from .prompts import (
    PromptTemplate,
    XIAOYU_SYSTEM_PROMPT,
    format_xiaoyu_prompt,
)

# Tools - 工具
from .tools import Tool, ToolResult, ToolRegistry, get_tool_registry, setup_tools
from .tools.predefined import (
    create_query_detection_records_tool,
    create_search_knowledge_tool,
)

# Nodes - 节点
from .nodes import (
    Node,
    NodeResult,
    NodeStatus,
    classify_intent_node,
    rag_retrieve_node,
    call_tool_node,
    generate_response_node,
)

# Graphs - 图编排
from .graphs import (
    GraphState,
    XiaoyuGraph,
    create_xiaoyu_graph,
)

# Chains - 链（兼容旧代码）
from .chains.chat_chain import ChatChain

__all__ = [
    # Core
    'AgentState',
    'AgentResult',
    'AgentStatus',
    'AgentExecutor',
    'AgentError',
    'ToolError',
    'MaxIterationsError',
    # Agents
    'BaseAgent',
    'Message',
    'XiaoyuAgent',
    'get_xiaoyu_agent',
    # Prompts
    'PromptTemplate',
    'XIAOYU_SYSTEM_PROMPT',
    'format_xiaoyu_prompt',
    # Tools
    'Tool',
    'ToolResult',
    'ToolRegistry',
    'get_tool_registry',
    'setup_tools',
    'create_query_detection_records_tool',
    'create_search_knowledge_tool',
    # Nodes
    'Node',
    'NodeResult',
    'NodeStatus',
    'classify_intent_node',
    'rag_retrieve_node',
    'call_tool_node',
    'generate_response_node',
    # Graphs
    'GraphState',
    'XiaoyuGraph',
    'create_xiaoyu_graph',
    # Chains
    'ChatChain',
]
