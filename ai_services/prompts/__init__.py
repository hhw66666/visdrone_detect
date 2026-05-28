# -*- coding: utf-8 -*-
"""
Prompts 模块
提示词模板定义
"""

from .base import PromptTemplate
from .xiaoyu_prompts import (
    XIAOYU_SYSTEM_PROMPT,
    XIAOYU_TOOL_CALL_PROMPT,
    XIAOYU_SELF_CORRECT_PROMPT,
    format_xiaoyu_prompt,
)

__all__ = [
    'PromptTemplate',
    'XIAOYU_SYSTEM_PROMPT',
    'XIAOYU_TOOL_CALL_PROMPT',
    'XIAOYU_SELF_CORRECT_PROMPT',
    'format_xiaoyu_prompt',
]
