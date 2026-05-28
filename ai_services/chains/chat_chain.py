# -*- coding: utf-8 -*-
"""
聊天链
基于 LangChain 的对话链式调用
"""

from typing import List, Dict, Any, Optional, Callable

from ..agents.base import BaseAgent, Message
from ..rag.retriever import Retriever, get_retriever
from ..mcp.client import MCPClient, get_mcp_client
from ..tools.base import Tool


class ChatChain:
    """
    聊天链

    整合 Agent、RAG 和 MCP 的链式调用

    流程:
    1. 用户输入 -> 2. RAG 检索（可选）-> 3. MCP 工具调用（可选）-> 4. Agent 处理 -> 5. 返回结果
    """

    def __init__(
        self,
        agent: BaseAgent,
        retriever: Retriever = None,
        mcp_client: MCPClient = None,
        enable_rag: bool = False,
        enable_mcp: bool = False
    ):
        """
        初始化聊天链

        Args:
            agent: Agent 实例
            retriever: RAG 检索器实例
            mcp_client: MCP 客户端实例
            enable_rag: 是否启用 RAG
            enable_mcp: 是否启用 MCP
        """
        self.agent = agent
        self.retriever = retriever or get_retriever()
        self.mcp_client = mcp_client or get_mcp_client()
        self.enable_rag = enable_rag
        self.enable_mcp = enable_mcp

    def process_message(self, user_message: str) -> str:
        """
        处理用户消息

        Args:
            user_message: 用户输入

        Returns:
            Agent 回复
        """
        # 1. 如果启用 RAG，检索相关上下文
        context = ""
        if self.enable_rag:
            context = self.retriever.get_context(user_message)
            if context:
                user_message = self._augment_message(user_message, context)

        # 2. 如果启用 MCP，检查是否需要调用工具
        if self.enable_mcp:
            # 简单的工具调用逻辑（后续可扩展为 ReAct 等策略）
            tools_result = self._check_tool_calls(user_message)
            if tools_result:
                user_message = self._augment_with_tools(user_message, tools_result)

        # 3. 调用 Agent
        reply = self.agent.chat(user_message)

        return reply

    def _augment_message(self, message: str, context: str) -> str:
        """
        使用上下文增强消息

        Args:
            message: 原始消息
            context: 检索到的上下文

        Returns:
            增强后的消息
        """
        return f"【相关上下文】\n{context}\n\n【用户问题】\n{message}"

    def _augment_with_tools(self, message: str, tools_result: str) -> str:
        """
        使用工具结果增强消息

        Args:
            message: 原始消息
            tools_result: 工具执行结果

        Returns:
            增强后的消息
        """
        return f"【工具执行结果】\n{tools_result}\n\n【用户问题】\n{message}"

    def _check_tool_calls(self, message: str) -> Optional[str]:
        """
        检查是否需要调用工具

        Args:
            message: 用户消息

        Returns:
            工具执行结果，如果没有调用工具则返回 None
        """
        # 简单的关键词匹配（后续可使用 LLM 判断）
        tools = self.mcp_client.list_tools()

        for tool in tools:
            if self._should_use_tool(message, tool):
                try:
                    # 简化：这里应该解析参数
                    result = tool.invoke()
                    return f"【{tool.name}】\n{result}"
                except Exception as e:
                    return f"【{tool.name}】\n执行失败: {str(e)}"

        return None

    def _should_use_tool(self, message: str, tool: Tool) -> bool:
        """
        判断是否应该使用某个工具

        Args:
            message: 用户消息
            tool: 工具实例

        Returns:
            是否应该使用
        """
        # 简化实现：后续可使用 LLM 或更复杂的策略
        tool_keywords = {
            'query_database': ['查询', '统计', '多少', '记录'],
            'read_file': ['读取', '查看', '文件'],
            'call_api': ['调用', '请求', 'API']
        }

        keywords = tool_keywords.get(tool.name, [])
        return any(kw in message for kw in keywords)

    def reset(self):
        """重置对话"""
        self.agent.clear_history()

    def get_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.agent.get_history()


# 预定义的聊天链工厂
def create_xiaoyu_chain(enable_rag: bool = False, enable_mcp: bool = False) -> ChatChain:
    """
    创建小科聊天链

    Args:
        enable_rag: 是否启用 RAG
        enable_mcp: 是否启用 MCP

    Returns:
        ChatChain 实例
    """
    from ..agents.xiaoyu import get_xiaoyu_agent

    return ChatChain(
        agent=get_xiaoyu_agent(),
        enable_rag=enable_rag,
        enable_mcp=enable_mcp
    )


# 全局聊天链实例
_chat_chain = None

def get_chat_chain(enable_rag: bool = False, enable_mcp: bool = False) -> ChatChain:
    """
    获取全局聊天链实例

    Args:
        enable_rag: 是否启用 RAG
        enable_mcp: 是否启用 MCP

    Returns:
        ChatChain 实例
    """
    global _chat_chain
    if _chat_chain is None:
        _chat_chain = create_xiaoyu_chain(enable_rag, enable_mcp)
    return _chat_chain
