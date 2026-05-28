# -*- coding: utf-8 -*-
"""
Agent 基类
定义 Agent 的通用接口和功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import time


class Message:
    """聊天消息"""

    def __init__(self, role: str, content: str, timestamp: float = None):
        self.role = role  # 'user' / 'assistant' / 'system'
        self.content = content
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, str]:
        return {
            'role': self.role,
            'content': self.content
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]):
        return cls(
            role=data.get('role', 'user'),
            content=data.get('content', '')
        )


class BaseAgent(ABC):
    """
    Agent 基类

    所有 Agent 都应继承此类并实现:
    - get_system_prompt(): 返回系统提示词
    - chat(user_message): 处理用户消息并返回回复
    """

    def __init__(self, name: str, model: str = None, max_tokens: int = 1024, temperature: float = 0.7):
        """
        初始化 Agent

        Args:
            name: Agent 名称
            model: 使用的模型
            max_tokens: 最大生成 token 数
            temperature: 温度参数 (0-1)
        """
        self.name = name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.conversation_history: List[Message] = []

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词
        子类应重写此方法返回特定的身份设定和规则
        """
        pass

    @abstractmethod
    def chat(self, user_message: str) -> str:
        """
        处理用户消息并返回回复

        Args:
            user_message: 用户输入的消息

        Returns:
            Agent 的回复内容
        """
        pass

    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.conversation_history.append(Message(role, content))

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return [msg.to_dict() for msg in self.conversation_history]

    def save_history(self) -> List[Dict[str, Any]]:
        """保存对话历史（用于持久化）"""
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp
            }
            for msg in self.conversation_history
        ]

    def load_history(self, history: List[Dict[str, Any]]):
        """加载对话历史"""
        self.conversation_history = [
            Message(
                role=item.get('role', 'user'),
                content=item.get('content', ''),
                timestamp=item.get('timestamp', time.time())
            )
            for item in history
        ]

    def call_api(self, messages: List[Dict[str, str]], system_prompt: str = None) -> Dict[str, Any]:
        """
        调用 AI API 的通用方法

        Args:
            messages: 对话消息列表
            system_prompt: 系统提示词（可选）

        Returns:
            API 响应结果
        """
        raise NotImplementedError("子类必须实现 call_api 方法")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', model='{self.model}')>"
