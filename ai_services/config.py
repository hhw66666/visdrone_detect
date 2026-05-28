# -*- coding: utf-8 -*-
"""
AI 服务配置
统一管理 Agent、RAG、MCP、LangChain 等配置
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detect_system.config_loader import load_config

# 获取 AI 服务配置
def get_ai_config():
    """获取 AI 服务配置"""
    config = load_config()
    return config.get('ai_services', {})

def get_agent_config(agent_name=None):
    """获取 Agent 配置"""
    ai_config = get_ai_config()
    agents = ai_config.get('agents', {})

    if agent_name:
        return agents.get(agent_name, {})
    return agents

def get_rag_config():
    """获取 RAG 配置"""
    ai_config = get_ai_config()
    return ai_config.get('rag', {})

def get_mcp_config():
    """获取 MCP 配置"""
    ai_config = get_ai_config()
    return ai_config.get('mcp', {})

def get_langchain_config():
    """获取 LangChain 配置"""
    ai_config = get_ai_config()
    return ai_config.get('langchain', {})

# 默认 Agent 列表
AVAILABLE_AGENTS = {
    'xiaoyu': '小科客服助手'
}

# 默认配置模板
DEFAULT_AGENT_CONFIG = {
    'xiaoyu': {
        'name': '小科',
        'model': 'MiniMax-M2.7',
        'max_tokens': 1024,
        'temperature': 0.7,
        'system_prompt_template': 'default'
    }
}
