# -*- coding: utf-8 -*-
"""
Agent 执行器
管理思考-行动-观察循环，防止死循环
"""

import time
import logging
from typing import Callable, Awaitable, TypeVar, ParamSpec
from dataclasses import dataclass

from .state import AgentState, AgentStatus, AgentResult, create_initial_state, state_to_result
from .exceptions import MaxIterationsError, RecursionLimitError, InvalidStateError

logger = logging.getLogger(__name__)

# 类型变量
P = ParamSpec('P')
T = TypeVar('T')

# 步骤处理器类型
StepHandler = Callable[[AgentState], AgentState | None]
AsyncStepHandler = Awaitable[AgentState | None]


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    final_state: AgentState
    duration_ms: float
    error: str | None = None


class AgentExecutor:
    """
    Agent 执行器

    核心职责：
    1. 管理状态机状态
    2. 控制思考-行动-观察循环
    3. 提供明确的退出条件
    4. 错误处理和恢复

    退出条件（满足任一即退出）：
    1. 达到 max_iterations
    2. 状态机进入 COMPLETED 或 FAILED
    3. 触发 recursion_limit
    4. 超时（如果设置了 timeout）
    """

    def __init__(
        self,
        max_iterations: int = 10,
        recursion_limit: int = 100,
        timeout_seconds: float | None = None,
        step_delay: float = 0.1,  # 步骤间延迟（秒）
        verbose: bool = False,
    ):
        """
        初始化执行器

        Args:
            max_iterations: 最大迭代次数，防止无限循环
            recursion_limit: 递归深度限制
            timeout_seconds: 超时时间（秒），None 表示不限制
            step_delay: 步骤间延迟
            verbose: 是否输出详细日志
        """
        self.max_iterations = max_iterations
        self.recursion_limit = recursion_limit
        self.timeout_seconds = timeout_seconds
        self.step_delay = step_delay
        self.verbose = verbose

        # 内部状态
        self._execution_count = 0

    def execute(
        self,
        initial_input: str,
        handlers: list[StepHandler],
        initial_state: AgentState | None = None,
    ) -> AgentResult:
        """
        同步执行 Agent

        Args:
            initial_input: 用户输入
            handlers: 步骤处理器列表，按顺序执行
            initial_state: 初始状态

        Returns:
            AgentResult: 执行结果

        Raises:
            MaxIterationsError: 达到最大迭代次数
            RecursionLimitError: 递归深度超限
            InvalidStateError: 无效状态
        """
        self._execution_count += 1

        # 初始化状态
        state = initial_state or create_initial_state(
            messages=[{"role": "user", "content": initial_input}],
            max_steps=self.max_iterations
        )

        start_time = time.time()

        if self.verbose:
            logger.info(f"[Executor] 开始执行，输入: {initial_input[:50]}...")

        # 主循环
        while self._should_continue(state):
            # 检查退出条件
            if state["current_step"] >= self.max_iterations:
                state["status"] = AgentStatus.MAX_ITERATIONS
                state["finish_reason"] = f"达到最大迭代次数 ({self.max_iterations})"
                if self.verbose:
                    logger.warning(f"[Executor] 达到最大迭代次数: {self.max_iterations}")
                break

            # 检查超时
            if self.timeout_seconds:
                elapsed = time.time() - state["last_step_at"]
                if elapsed > self.timeout_seconds:
                    state["status"] = AgentStatus.FAILED
                    state["finish_reason"] = f"执行超时 ({self.timeout_seconds}s)"
                    state["last_error"] = "Execution timeout"
                    break

            # 检查递归深度
            if state["current_step"] > self.recursion_limit:
                raise RecursionLimitError(self.recursion_limit)

            # 更新状态
            state["current_step"] += 1
            state["last_step_at"] = time.time()
            state["status"] = AgentStatus.RUNNING

            if self.verbose:
                logger.info(f"[Executor] 执行步骤 {state['current_step']}/{self.max_iterations}")

            # 执行处理器链
            next_state = None
            for handler in handlers:
                try:
                    result = handler(state)
                    if result is not None:
                        next_state = result
                        state = next_state
                except Exception as e:
                    state = self._handle_step_error(state, e)
                    if state["status"] == AgentStatus.FAILED:
                        break

            # 如果没有任何处理器返回新状态，退出循环
            if next_state is None:
                if state["status"] == AgentStatus.RUNNING:
                    state["status"] = AgentStatus.COMPLETED
                    state["finish_reason"] = "正常完成"
                break

            # 步骤间延迟
            if self.step_delay > 0:
                time.sleep(self.step_delay)

        # 计算耗时
        duration_ms = (time.time() - start_time) * 1000

        if self.verbose:
            logger.info(f"[Executor] 执行完成，步骤: {state['current_step']}, 状态: {state['status']}")

        return state_to_result(state, duration_ms)

    async def execute_async(
        self,
        initial_input: str,
        handlers: list[AsyncStepHandler | StepHandler],
        initial_state: AgentState | None = None,
    ) -> AgentResult:
        """
        异步执行 Agent

        Args:
            initial_input: 用户输入
            handlers: 步骤处理器列表
            initial_state: 初始状态

        Returns:
            AgentResult: 执行结果
        """
        import asyncio

        self._execution_count += 1

        state = initial_state or create_initial_state(
            messages=[{"role": "user", "content": initial_input}],
            max_steps=self.max_iterations
        )

        start_time = time.time()

        if self.verbose:
            logger.info(f"[Executor] 异步执行开始，输入: {initial_input[:50]}...")

        while self._should_continue(state):
            if state["current_step"] >= self.max_iterations:
                state["status"] = AgentStatus.MAX_ITERATIONS
                state["finish_reason"] = f"达到最大迭代次数 ({self.max_iterations})"
                break

            if self.timeout_seconds:
                elapsed = time.time() - state["last_step_at"]
                if elapsed > self.timeout_seconds:
                    state["status"] = AgentStatus.FAILED
                    state["finish_reason"] = f"执行超时 ({self.timeout_seconds}s)"
                    state["last_error"] = "Execution timeout"
                    break

            if state["current_step"] > self.recursion_limit:
                raise RecursionLimitError(self.recursion_limit)

            state["current_step"] += 1
            state["last_step_at"] = time.time()
            state["status"] = AgentStatus.RUNNING

            if self.verbose:
                logger.info(f"[Executor] 异步执行步骤 {state['current_step']}/{self.max_iterations}")

            next_state = None
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(state)
                    else:
                        result = handler(state)
                    if result is not None:
                        next_state = result
                        state = next_state
                except Exception as e:
                    state = self._handle_step_error(state, e)
                    if state["status"] == AgentStatus.FAILED:
                        break

            if next_state is None:
                if state["status"] == AgentStatus.RUNNING:
                    state["status"] = AgentStatus.COMPLETED
                    state["finish_reason"] = "正常完成"
                break

            if self.step_delay > 0:
                await asyncio.sleep(self.step_delay)

        duration_ms = (time.time() - start_time) * 1000

        return state_to_result(state, duration_ms)

    def _should_continue(self, state: AgentState) -> bool:
        """检查是否继续执行"""
        terminal_statuses = {
            AgentStatus.COMPLETED,
            AgentStatus.FAILED,
            AgentStatus.MAX_ITERATIONS
        }
        return state["status"] not in terminal_statuses

    def _handle_step_error(self, state: AgentState, error: Exception) -> AgentState:
        """处理步骤执行错误"""
        error_info = {
            "error": str(error),
            "step": state["current_step"],
            "timestamp": time.time()
        }

        state["error_history"].append(error_info)
        state["last_error"] = str(error)
        state["retry_count"] = state.get("retry_count", 0) + 1

        if self.verbose:
            logger.error(f"[Executor] 步骤执行错误: {error}")

        # 超过重试次数则失败
        if state["retry_count"] >= 3:
            state["status"] = AgentStatus.FAILED
            state["finish_reason"] = f"重试次数超限: {error}"
        else:
            # 可以继续重试
            state["status"] = AgentStatus.RUNNING

        return state
