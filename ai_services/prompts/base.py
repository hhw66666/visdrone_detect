# -*- coding: utf-8 -*-
"""
提示词模板基类
"""

from typing import Any
from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """
    提示词模板

    支持变量替换和模板化
    """
    template: str                          # 模板字符串
    input_variables: list[str] = Field(default_factory=list)  # 输入变量名

    def format(self, **kwargs: Any) -> str:
        """
        格式化模板

        Args:
            **kwargs: 变量名=值的映射

        Returns:
            格式化后的字符串

        Raises:
            KeyError: 缺少必需的变量
        """
        missing = set(self.input_variables) - set(kwargs.keys())
        if missing:
            raise KeyError(f"缺少必需的模板变量: {missing}")

        return self.template.format(**kwargs)

    def format_partial(self, **kwargs: Any) -> str:
        """
        部分格式化（只替换提供的变量）

        Args:
            **kwargs: 变量名=值的映射

        Returns:
            格式化后的字符串，未提供的变量保持原样
        """
        import re

        def replacer(match):
            var_name = match.group(1)
            return str(kwargs.get(var_name, match.group(0)))

        # 替换 {var_name} 格式的变量
        pattern = r'\{(' + '|'.join(re.escape(v) for v in kwargs.keys()) + r')\}'
        return re.sub(pattern, replacer, self.template)

    def get_variable_names(self) -> list[str]:
        """获取所有变量名"""
        import re
        return re.findall(r'\{(\w+)\}', self.template)

    def merge(self, other: "PromptTemplate") -> "PromptTemplate":
        """
        合并两个模板

        Args:
            other: 另一个模板

        Returns:
            合并后的新模板
        """
        new_template = self.template + "\n" + other.template
        all_vars = list(set(self.get_variable_names() + other.get_variable_names()))
        return PromptTemplate(
            template=new_template,
            input_variables=all_vars
        )


class ChatPromptTemplate(BaseModel):
    """
    对话提示词模板

    支持多轮对话的模板定义
    """
    messages: list[dict[str, str]] = Field(default_factory=list)
    """消息列表，每条消息包含 role 和 content"""

    def add_system_message(self, content: str) -> "ChatPromptTemplate":
        """添加系统消息"""
        new_messages = [{"role": "system", "content": content}] + self.messages
        return ChatPromptTemplate(messages=new_messages)

    def add_user_message(self, content: str) -> "ChatPromptTemplate":
        """添加用户消息"""
        return ChatPromptTemplate(
            messages=self.messages + [{"role": "user", "content": content}]
        )

    def add_placeholder(self, name: str) -> "ChatPromptTemplate":
        """添加占位符消息"""
        placeholder = "{" + "{" + name + "}" + "}"
        return ChatPromptTemplate(
            messages=self.messages + [{"role": "placeholder", "content": placeholder}]
        )

    def format_messages(self, **kwargs: Any) -> list[dict[str, str]]:
        """
        格式化所有消息

        Args:
            **kwargs: 变量映射

        Returns:
            格式化后的消息列表
        """
        formatted = []
        for msg in self.messages:
            if msg.get("role") == "placeholder":
                continue
            formatted.append({
                "role": msg["role"],
                "content": msg["content"].format(**kwargs)
            })
        return formatted
