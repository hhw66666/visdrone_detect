# -*- coding: utf-8 -*-
"""
向量化器
将文本转换为向量表示
"""

from abc import ABC, abstractmethod
from typing import List
import os
import logging

logger = logging.getLogger(__name__)

# 全局 embedder 实例缓存
_embedder_cache = {}


class Embedder(ABC):
    """
    向量化器基类

    所有向量化器都应继承此类
    """

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            文本的向量表示
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量

        Args:
            texts: 输入文本列表

        Returns:
            文本向量列表
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        获取向量的维度

        Returns:
            向量维度
        """
        pass


class DummyEmbedder(Embedder):
    """
    虚拟向量化器（用于测试）

    返回随机向量
    """

    def __init__(self, dimension: int = 768):
        self._dimension = dimension

    def embed(self, text: str) -> List[float]:
        """生成随机向量"""
        import numpy as np
        return np.random.randn(self._dimension).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成随机向量"""
        return [self.embed(text) for text in texts]

    def get_dimension(self) -> int:
        return self._dimension


class DashScopeEmbedder(Embedder):
    """
    基于阿里云 DashScope 的向量化器

    使用阿里云 DashScope Embedding API 将文本转换为向量
    模型: text-embedding-v1 (1536维)
    """

    def __init__(
        self,
        model: str = "text-embedding-v1",
        dimension: int = 1536,
    ):
        """
        初始化向量化器

        Args:
            model: DashScope embedding 模型名称
            dimension: 向量维度
        """
        self._model = model
        self._dimension = dimension
        self._client = None

    def _get_client(self):
        """获取 DashScope 客户端"""
        if self._client is None:
            from langchain_community.embeddings import DashScopeEmbeddings
            self._client = DashScopeEmbeddings(
                model=self._model,
            )
        return self._client

    def embed(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            文本的向量表示
        """
        try:
            client = self._get_client()
            return client.embed_query(text)
        except Exception as e:
            logger.error(f"[DashScopeEmbedder] embed 失败: {e}")
            return [0.0] * self._dimension

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量将文本转换为向量

        Args:
            texts: 输入文本列表

        Returns:
            文本向量列表
        """
        if not texts:
            return []

        try:
            client = self._get_client()
            return client.embed_documents(texts)
        except Exception as e:
            logger.error(f"[DashScopeEmbedder] embed_batch 失败: {e}")
            return [[0.0] * self._dimension for _ in texts]

    def get_dimension(self) -> int:
        """
        获取向量的维度

        Returns:
            向量维度
        """
        return self._dimension


# 可用的向量化器注册表
AVAILABLE_EMBEDDERS = {
    'dummy': DummyEmbedder,
    'dashscope': DashScopeEmbedder,
}


def get_embedder(name: str = 'dashscope', **kwargs) -> Embedder:
    """
    获取向量化器实例

    Args:
        name: 向量化器名称
        **kwargs: 传递给向量化器的参数

    Returns:
        向量化器实例
    """
    global _embedder_cache

    # 缓存key
    cache_key = f"{name}:{str(kwargs)}"

    if cache_key not in _embedder_cache:
        embedder_class = AVAILABLE_EMBEDDERS.get(name)
        if embedder_class is None:
            raise ValueError(f"未知的向量化器: {name}")
        _embedder_cache[cache_key] = embedder_class(**kwargs)

    return _embedder_cache[cache_key]