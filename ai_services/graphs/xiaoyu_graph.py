# -*- coding: utf-8 -*-
"""
小科客服 Agent 图
基于状态图的对话流程编排
"""

import logging
from typing import Literal

from .state import GraphState, GraphNode, create_graph_state
from ..agents.xiaoyu import XiaoyuAgent, get_xiaoyu_agent
from ..tools import get_tool_registry

logger = logging.getLogger(__name__)


class XiaoyuGraph:
    """
    小科客服 Agent 工作流图

    流程:
    START -> CLASSIFY_INTENT -> RAG_RETRIEVE -> SHOULD_USE_TOOL
                                                        |
                              +------------+------------+
                              |                         |
                         use_tool=True              use_tool=False
                              |                         |
                              v                         v
                        CALL_TOOL                  (skip)
                              |                         |
                              +------------+------------+
                                          |
                                          v
                                   GENERATE_RESPONSE
                                          |
                                          v
                                           END
    """

    def __init__(
        self,
        agent: XiaoyuAgent | None = None,
        retriever=None,
        enable_rag: bool = False,
        enable_tools: bool = False,
        max_steps: int = 10,
    ):
        """
        初始化小科工作流图

        Args:
            agent: 小科 Agent 实例
            retriever: RAG 检索器实例
            enable_rag: 是否启用 RAG
            enable_tools: 是否启用工具
            max_steps: 最大步骤数
        """
        self.agent = agent or get_xiaoyu_agent()
        self.retriever = retriever
        self.enable_rag = enable_rag
        self.enable_tools = enable_tools
        self.max_steps = max_steps

    def run(self, user_input: str) -> GraphState:
        """
        同步运行工作流

        Args:
            user_input: 用户输入

        Returns:
            GraphState: 最终状态
        """
        state = create_graph_state(user_input, max_steps=self.max_steps)

        while not self._is_terminal(state) and state["steps"] < state["max_steps"]:
            state = self._step(state)
            state["steps"] += 1

            logger.debug(f"[XiaoyuGraph] 步骤 {state['steps']}: {state['current_node']} -> {state['next_node']}")

        return state

    async def arun(self, user_input: str) -> GraphState:
        """
        异步运行工作流

        Args:
            user_input: 用户输入

        Returns:
            GraphState: 最终状态
        """
        state = create_graph_state(user_input, max_steps=self.max_steps)

        while not self._is_terminal(state) and state["steps"] < state["max_steps"]:
            state = await self._astep(state)
            state["steps"] += 1

            logger.debug(f"[XiaoyuGraph] 异步步骤 {state['steps']}: {state['current_node']} -> {state['next_node']}")

        return state

    def _step(self, state: GraphState) -> GraphState:
        """执行单步（同步）"""
        node = state["next_node"] or state["current_node"]

        if node == GraphNode.CLASSIFY_INTENT:
            return self._classify_intent(state)
        elif node == GraphNode.RAG_RETRIEVE:
            return self._rag_retrieve(state)
        elif node == GraphNode.SHOULD_USE_TOOL:
            return self._should_use_tool(state)
        elif node == GraphNode.CALL_TOOL:
            return self._call_tool(state)
        elif node == GraphNode.GENERATE_RESPONSE:
            return self._generate_response(state)
        else:
            state["next_node"] = GraphNode.END
            return state

    async def _astep(self, state: GraphState) -> GraphState:
        """执行单步（异步）"""
        node = state["next_node"] or state["current_node"]

        if node == GraphNode.CLASSIFY_INTENT:
            return self._classify_intent(state)
        elif node == GraphNode.RAG_RETRIEVE:
            return self._rag_retrieve(state)
        elif node == GraphNode.SHOULD_USE_TOOL:
            return self._should_use_tool(state)
        elif node == GraphNode.CALL_TOOL:
            return await self._acall_tool(state)
        elif node == GraphNode.GENERATE_RESPONSE:
            return await self._agenerate_response(state)
        else:
            state["next_node"] = GraphNode.END
            return state

    def _classify_intent(self, state: GraphState) -> GraphState:
        """意图分类"""
        user_input = state["user_input"]

        # 简单关键词匹配
        intent = "general"
        if any(kw in user_input for kw in ["检测", "上传", "识别"]):
            intent = "detection"
        elif any(kw in user_input for kw in ["历史", "记录"]):
            intent = "history"
        elif any(kw in user_input for kw in ["多少", "统计"]):
            intent = "statistics"
        elif any(kw in user_input for kw in ["怎么", "如何", "帮助"]):
            intent = "guide"

        state["intent"] = intent
        state["intent_confidence"] = 0.9
        state["current_node"] = GraphNode.CLASSIFY_INTENT
        state["next_node"] = GraphNode.RAG_RETRIEVE if self.enable_rag else GraphNode.SHOULD_USE_TOOL

        return state

    def _rag_retrieve(self, state: GraphState) -> GraphState:
        """RAG 检索"""
        if not self.enable_rag or self.retriever is None:
            state["current_node"] = GraphNode.RAG_RETRIEVE
            state["next_node"] = GraphNode.SHOULD_USE_TOOL
            return state

        user_input = state.get("user_input", "")

        try:
            context = self.retriever.get_context(user_input)
            state["retrieved_context"] = context if context else None
            state["retrieve_success"] = bool(context)
        except Exception as e:
            logger.warning(f"[XiaoyuGraph] RAG 检索失败: {e}")
            state["retrieved_context"] = None
            state["retrieve_success"] = False

        state["current_node"] = GraphNode.RAG_RETRIEVE
        state["next_node"] = GraphNode.SHOULD_USE_TOOL

        return state

    def _should_use_tool(self, state: GraphState) -> GraphState:
        """判断是否使用工具"""
        if not self.enable_tools:
            state["should_use_tool"] = False
            state["current_node"] = GraphNode.SHOULD_USE_TOOL
            state["next_node"] = GraphNode.GENERATE_RESPONSE
            return state

        intent = state.get("intent", "general")
        user_input = state.get("user_input", "")

        # 需要工具的意图
        tool_intents = {"statistics", "history"}

        if intent in tool_intents:
            state["should_use_tool"] = True
            state["tool_name"] = "query_detection_records"
            state["current_node"] = GraphNode.SHOULD_USE_TOOL
            state["next_node"] = GraphNode.CALL_TOOL
        elif any(kw in user_input for kw in ["多少", "统计", "查询"]):
            state["should_use_tool"] = True
            state["tool_name"] = "query_detection_records"
            state["current_node"] = GraphNode.SHOULD_USE_TOOL
            state["next_node"] = GraphNode.CALL_TOOL
        else:
            state["should_use_tool"] = False
            state["current_node"] = GraphNode.SHOULD_USE_TOOL
            state["next_node"] = GraphNode.GENERATE_RESPONSE

        return state

    def _call_tool(self, state: GraphState) -> GraphState:
        """调用工具"""
        registry = get_tool_registry()
        tool_name = state.get("tool_name")

        if not tool_name or not registry.get(tool_name):
            state["tool_error"] = f"工具 {tool_name} 不存在"
            state["current_node"] = GraphNode.CALL_TOOL
            state["next_node"] = GraphNode.GENERATE_RESPONSE
            return state

        try:
            # 根据意图构建查询
            user_input = state.get("user_input", "")
            intent = state.get("intent", "general")
            sql = "SELECT * FROM detection_record LIMIT 10"

            if intent == "statistics" or "多少" in user_input:
                sql = "SELECT COUNT(*) as count FROM detection_record"

            result = registry.invoke(tool_name, sql=sql)
            state["tool_result"] = result.output if result.success else None
            state["tool_error"] = result.error

        except Exception as e:
            state["tool_error"] = str(e)
            state["tool_result"] = None

        state["current_node"] = GraphNode.CALL_TOOL
        state["next_node"] = GraphNode.GENERATE_RESPONSE

        return state

    async def _acall_tool(self, state: GraphState) -> GraphState:
        """异步调用工具"""
        registry = get_tool_registry()
        tool_name = state.get("tool_name")

        if not tool_name or not registry.get(tool_name):
            state["tool_error"] = f"工具 {tool_name} 不存在"
            state["current_node"] = GraphNode.CALL_TOOL
            state["next_node"] = GraphNode.GENERATE_RESPONSE
            return state

        try:
            user_input = state.get("user_input", "")
            intent = state.get("intent", "general")
            sql = "SELECT * FROM detection_record LIMIT 10"

            if intent == "statistics" or "多少" in user_input:
                sql = "SELECT COUNT(*) as count FROM detection_record"

            result = await registry.ainvoke(tool_name, sql=sql)
            state["tool_result"] = result.output if result.success else None
            state["tool_error"] = result.error

        except Exception as e:
            state["tool_error"] = str(e)
            state["tool_result"] = None

        state["current_node"] = GraphNode.CALL_TOOL
        state["next_node"] = GraphNode.GENERATE_RESPONSE

        return state

    def _generate_response(self, state: GraphState) -> GraphState:
        """生成回复"""
        user_input = state.get("user_input", "")
        context = state.get("retrieved_context")
        tool_result = state.get("tool_result")

        try:
            # 构建增强输入
            if context or tool_result:
                parts = []
                if context:
                    parts.append(f"【相关上下文】\n{context}")
                if tool_result:
                    parts.append(f"【查询结果】\n{tool_result}")
                parts.append(f"【用户问题】\n{user_input}")
                enhanced_input = "\n\n".join(parts)
            else:
                enhanced_input = user_input

            # 调用 Agent
            response = self.agent.chat(enhanced_input)

            state["generated_response"] = response
            state["final_response"] = response
            state["success"] = True
            state["generation_error"] = None

        except Exception as e:
            state["generated_response"] = "抱歉，小科暂时无法回答这个问题。"
            state["final_response"] = "抱歉，小科暂时无法回答这个问题。"
            state["success"] = False
            state["generation_error"] = str(e)

        state["current_node"] = GraphNode.GENERATE_RESPONSE
        state["next_node"] = GraphNode.END

        return state

    async def _agenerate_response(self, state: GraphState) -> GraphState:
        """异步生成回复"""
        user_input = state.get("user_input", "")
        context = state.get("retrieved_context")
        tool_result = state.get("tool_result")

        try:
            if context or tool_result:
                parts = []
                if context:
                    parts.append(f"【相关上下文】\n{context}")
                if tool_result:
                    parts.append(f"【查询结果】\n{tool_result}")
                parts.append(f"【用户问题】\n{user_input}")
                enhanced_input = "\n\n".join(parts)
            else:
                enhanced_input = user_input

            response = await self.agent.achat(enhanced_input)

            state["generated_response"] = response
            state["final_response"] = response
            state["success"] = True
            state["generation_error"] = None

        except Exception as e:
            state["generated_response"] = "抱歉，小科暂时无法回答这个问题。"
            state["final_response"] = "抱歉，小科暂时无法回答这个问题。"
            state["success"] = False
            state["generation_error"] = str(e)

        state["current_node"] = GraphNode.GENERATE_RESPONSE
        state["next_node"] = GraphNode.END

        return state

    def _is_terminal(self, state: GraphState) -> bool:
        """检查是否为终止状态"""
        return state["next_node"] == GraphNode.END or state["steps"] >= state["max_steps"]


def create_xiaoyu_graph(
    enable_rag: bool = False,
    enable_tools: bool = False,
    max_steps: int = 10,
    retriever=None,
) -> XiaoyuGraph:
    """
    创建小科工作流图

    Args:
        enable_rag: 是否启用 RAG
        enable_tools: 是否启用工具
        max_steps: 最大步骤数
        retriever: RAG 检索器实例

    Returns:
        XiaoyuGraph 实例
    """
    return XiaoyuGraph(
        enable_rag=enable_rag,
        enable_tools=enable_tools,
        max_steps=max_steps,
        retriever=retriever,
    )
