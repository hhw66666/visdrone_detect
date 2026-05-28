# -*- coding: utf-8 -*-
"""
错误恢复与自我修正机制
"""

import time
import asyncio
import logging
from typing import Callable, Any, TypeVar, Awaitable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class ErrorRecord:
    """错误记录"""
    error: str
    error_type: str
    attempt: int
    timestamp: float = field(default_factory=time.time)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class RecoveryStrategy:
    """恢复策略配置"""
    max_retries: int = 2                    # 最大重试次数
    base_delay: float = 1.0                  # 基础延迟（秒）
    exponential_backoff: bool = True          # 是否指数退避
    max_delay: float = 30.0                 # 最大延迟
    enable_self_correct: bool = True        # 是否启用自我修正
    self_correct_prompt: str | None = None   # 自我修正提示词


class ErrorRecovery:
    """
    错误恢复与自我修正

    策略：
    1. 首次失败 -> 记录错误
    2. 重试一次或多次
    3. 如果还是失败，触发自我修正（让 LLM 分析错误原因）
    """

    def __init__(
        self,
        strategy: RecoveryStrategy | None = None,
        self_correct_func: Callable[[str, dict], Awaitable[str]] | None = None,
    ):
        """
        初始化错误恢复器

        Args:
            strategy: 恢复策略配置
            self_correct_func: 自我修正函数，接收 (错误信息, 上下文)，返回修正后的输入
        """
        self.strategy = strategy or RecoveryStrategy()
        self.self_correct_func = self_correct_func
        self.error_history: list[ErrorRecord] = []

    def record_error(self, error: Exception | str, context: dict[str, Any] | None = None) -> ErrorRecord:
        """
        记录错误

        Args:
            error: 错误对象或错误信息
            context: 错误上下文

        Returns:
            ErrorRecord: 错误记录
        """
        if isinstance(error, Exception):
            error_type = type(error).__name__
            error_msg = str(error)
        else:
            error_type = "UnknownError"
            error_msg = error

        record = ErrorRecord(
            error=error_msg,
            error_type=error_type,
            attempt=len([r for r in self.error_history if r.error == error_msg]) + 1,
            context=context or {}
        )

        self.error_history.append(record)

        if self.strategy.enable_self_correct:
            logger.warning(f"[ErrorRecovery] 记录错误: {error_type} - {error_msg}")

        return record

    def get_retry_delay(self, attempt: int) -> float:
        """
        计算重试延迟

        Args:
            attempt: 当前尝试次数（从1开始）

        Returns:
            延迟时间（秒）
        """
        if self.strategy.exponential_backoff:
            delay = self.strategy.base_delay * (2 ** (attempt - 1))
        else:
            delay = self.strategy.base_delay * attempt

        return min(delay, self.strategy.max_delay)

    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        **kwargs
    ) -> T:
        """
        带重试的异步执行

        Args:
            func: 异步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            最后一次执行的异常
        """
        last_error = None

        for attempt in range(1, self.strategy.max_retries + 2):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_error = e
                self.record_error(e, {"attempt": attempt, "args": str(args)[:100]})

                if attempt <= self.strategy.max_retries + 1:
                    delay = self.get_retry_delay(attempt)
                    logger.info(f"[ErrorRecovery] 重试 {attempt}/{self.strategy.max_retries + 1}, 延迟 {delay}s")
                    await asyncio.sleep(delay)

                    # 尝试自我修正
                    if self.strategy.enable_self_correct and self.self_correct_func:
                        try:
                            corrected_input = await self.self_correct_func(str(e), {"args": args, "kwargs": kwargs})
                            if corrected_input:
                                # 用修正后的参数重新执行
                                kwargs = corrected_input
                        except Exception as ce:
                            logger.warning(f"[ErrorRecovery] 自我修正失败: {ce}")

        raise last_error

    def execute_with_retry_sync(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> T:
        """
        带重试的同步执行

        Args:
            func: 同步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值
        """
        last_error = None

        for attempt in range(1, self.strategy.max_retries + 2):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                self.record_error(e, {"attempt": attempt})

                if attempt <= self.strategy.max_retries + 1:
                    delay = self.get_retry_delay(attempt)
                    logger.info(f"[ErrorRecovery] 重试 {attempt}/{self.strategy.max_retries + 1}, 延迟 {delay}s")
                    time.sleep(delay)

        raise last_error

    def clear_history(self):
        """清空错误历史"""
        self.error_history.clear()

    def get_error_summary(self) -> dict[str, Any]:
        """获取错误摘要"""
        if not self.error_history:
            return {"total_errors": 0, "error_types": {}}

        error_types: dict[str, int] = {}
        for record in self.error_history:
            error_types[record.error_type] = error_types.get(record.error_type, 0) + 1

        return {
            "total_errors": len(self.error_history),
            "error_types": error_types,
            "last_error": self.error_history[-1].error if self.error_history else None
        }


class CircuitBreaker:
    """
    熔断器

    防止持续调用一个会失败的外部服务
    当失败次数达到阈值时，暂时"熔断"，不再调用
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        """
        初始化熔断器

        Args:
            failure_threshold: 失败次数阈值
            recovery_timeout: 恢复超时（秒）
            expected_exception: 预期的异常类型
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._is_open = False

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        通过熔断器调用函数

        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数返回值

        Raises:
            熔断打开时抛出 CircuitBreakerOpen
        """
        if self._is_open:
            # 检查是否可以尝试半开
            if self._last_failure_time and \
               time.time() - self._last_failure_time > self.recovery_timeout:
                self._is_open = False
                self._failure_count = 0
                logger.info("[CircuitBreaker] 熔断恢复，尝试半开")
            else:
                raise CircuitBreakerOpen(
                    f"CircuitBreaker is open. Failures: {self._failure_count}"
                )

        try:
            result = func(*args, **kwargs)
            # 成功调用，重置计数
            if self._failure_count > 0:
                self._failure_count -= 1
            return result
        except self.expected_exception as e:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                self._is_open = True
                logger.warning(f"[CircuitBreaker] 熔断打开！失败次数: {self._failure_count}")

            raise

    @property
    def is_open(self) -> bool:
        return self._is_open

    @property
    def failure_count(self) -> int:
        return self._failure_count


class CircuitBreakerOpen(Exception):
    """熔断器打开异常"""
    pass
