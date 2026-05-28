# -*- coding: utf-8 -*-
"""
Agent 异常定义
"""


class AgentError(Exception):
    """Agent 基类异常"""
    def __init__(self, message: str, code: str | None = None, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": self.message,
            "code": self.code,
            "details": self.details
        }


class ToolError(AgentError):
    """工具执行异常"""
    def __init__(self, tool_name: str, message: str, **kwargs):
        super().__init__(
            message=f"[{tool_name}] {message}",
            code="TOOL_ERROR",
            details={"tool_name": tool_name, **kwargs}
        )
        self.tool_name = tool_name


class MaxIterationsError(AgentError):
    """达到最大迭代次数异常"""
    def __init__(self, max_steps: int):
        super().__init__(
            message=f"达到最大迭代次数 ({max_steps})，退出",
            code="MAX_ITERATIONS",
            details={"max_steps": max_steps}
        )
        self.max_steps = max_steps


class RecursionLimitError(AgentError):
    """递归深度超限异常"""
    def __init__(self, limit: int):
        super().__init__(
            message=f"递归深度超限 ({limit})，退出",
            code="RECURSION_LIMIT",
            details={"recursion_limit": limit}
        )
        self.recursion_limit = limit


class InvalidStateError(AgentError):
    """无效状态异常"""
    def __init__(self, message: str, current_status: str | None = None):
        super().__init__(
            message=message,
            code="INVALID_STATE",
            details={"current_status": current_status}
        )


class APIClientError(AgentError):
    """API 调用异常"""
    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        super().__init__(
            message=message,
            code="API_ERROR",
            details={
                "status_code": status_code,
                "response_body": response_body
            }
        )
        self.status_code = status_code
        self.response_body = response_body
