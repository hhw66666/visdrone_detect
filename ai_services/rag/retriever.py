# -*- coding: utf-8 -*-
"""
检索器
基于向量相似度检索相关文档
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
import os

from .embedder import Embedder, get_embedder


@dataclass
class Document:
    """文档对象"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None

    def set_embedding(self, embedding: List[float]):
        self.embedding = embedding

    def __repr__(self):
        return f"<Document(id='{self.id}', content='{self.content[:50]}...')>"


class Retriever:
    """
    检索器

    基于向量相似度检索相关文档
    支持 ChromaDB 或内存模式
    """

    def __init__(
        self,
        embedder: Embedder = None,
        top_k: int = 3,
        persist_directory: str = None,
        collection_name: str = "knowledge_base",
        use_chroma: bool = True,
    ):
        """
        初始化检索器

        Args:
            embedder: 向量化器实例，默认使用 sentence_transformers
            top_k: 默认返回的最相关文档数
            persist_directory: ChromaDB 持久化目录
            collection_name: ChromaDB collection 名称
            use_chroma: 是否使用 ChromaDB（False 则使用内存模式）
        """
        self.embedder = embedder or get_embedder('sentence_transformers')
        self.top_k = top_k
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.use_chroma = use_chroma

        self._chroma_client = None
        self._chroma_collection = None
        self._in_memory_docs: List[Document] = []

        if self.use_chroma:
            self._init_chroma()

    def _init_chroma(self):
        """初始化 ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings

            if self.persist_directory is None:
                self.persist_directory = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "data",
                    "chroma_db"
                )

            os.makedirs(self.persist_directory, exist_ok=True)

            self._chroma_client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )

            # 获取或创建 collection
            try:
                self._chroma_collection = self._chroma_client.get_collection(
                    name=self.collection_name
                )
            except Exception:
                # Collection 不存在，创建新的
                self._chroma_collection = self._chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )

        except ImportError:
            raise ImportError(
                "ChromaDB 未安装。请运行: pip install chromadb"
            )
        except Exception as e:
            raise RuntimeError(f"初始化 ChromaDB 失败: {e}")

    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any] = None,
        doc_id: str = None,
    ) -> Document:
        """
        添加文档

        Args:
            content: 文档内容
            metadata: 文档元数据
            doc_id: 文档 ID（可选，自动生成）

        Returns:
            创建的文档对象
        """
        if doc_id is None:
            doc_id = f"doc_{len(self._in_memory_docs) + 1}"

        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata or {},
        )

        # 计算向量
        embedding = self.embedder.embed(content)
        doc.set_embedding(embedding)

        if self.use_chroma and self._chroma_collection is not None:
            self._chroma_collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata or {}],
                embeddings=[embedding],
            )
        else:
            self._in_memory_docs.append(doc)

        return doc

    def add_documents(self, docs: List[Dict[str, Any]]) -> List[Document]:
        """
        批量添加文档

        Args:
            docs: 文档列表，每项包含 content 和可选的 metadata、id

        Returns:
            创建的文档对象列表
        """
        if not docs:
            return []

        if self.use_chroma and self._chroma_collection is not None:
            ids = []
            contents = []
            metadatas = []
            embeddings = []

            for doc_data in docs:
                doc_id = doc_data.get('id', f"doc_{len(self._in_memory_docs) + len(ids) + 1}")
                content = doc_data['content']
                metadata = doc_data.get('metadata', {})

                ids.append(doc_id)
                contents.append(content)
                metadatas.append(metadata)
                embeddings.append(self.embedder.embed(content))

            self._chroma_collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas,
                embeddings=embeddings,
            )

            return [Document(id=d['id'], content=d['content'], metadata=d.get('metadata', {}))
                    for d in docs]
        else:
            results = []
            for doc_data in docs:
                results.append(self.add_document(
                    content=doc_data['content'],
                    metadata=doc_data.get('metadata'),
                    doc_id=doc_data.get('id'),
                ))
            return results

    def retrieve(self, query: str, top_k: int = None) -> List[Tuple[Document, float]]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回的最相关文档数

        Returns:
            (文档, 相似度分数) 列表，按相似度降序排列
        """
        if top_k is None:
            top_k = self.top_k

        if self.use_chroma and self._chroma_collection is not None:
            # 查询向量
            query_embedding = self.embedder.embed(query)

            results = self._chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            docs = []
            if results and results['ids']:
                for i, doc_id in enumerate(results['ids'][0]):
                    idx = 0  # 只有一条查询
                    content = results['documents'][idx][i] if results['documents'] else ""
                    metadata = results['metadatas'][idx][i] if results['metadatas'] else {}
                    distance = results['distances'][idx][i] if results['distances'] else 0.0

                    # ChromaDB 返回的是余弦距离，转为相似度
                    similarity = 1.0 - distance if distance is not None else 0.0

                    doc = Document(
                        id=doc_id,
                        content=content,
                        metadata=metadata,
                    )
                    docs.append((doc, similarity))

            return docs

        else:
            # 内存模式：暴力搜索
            if not self._in_memory_docs:
                return []

            query_embedding = self.embedder.embed(query)

            results = []
            for doc in self._in_memory_docs:
                if doc.embedding is None:
                    continue
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                results.append((doc, similarity))

            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np

        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def get_context(self, query: str, top_k: int = None) -> str:
        """
        获取检索到的上下文

        Args:
            query: 查询文本
            top_k: 使用的文档数

        Returns:
            拼接的上下文字符串
        """
        results = self.retrieve(query, top_k)

        if not results:
            return ""

        context_parts = []
        for doc, score in results:
            context_parts.append(f"[相关度: {score:.2f}] {doc.content}")

        return "\n\n".join(context_parts)

    def count(self) -> int:
        """获取文档数量"""
        if self.use_chroma and self._chroma_collection is not None:
            return self._chroma_collection.count()
        return len(self._in_memory_docs)

    def clear(self):
        """清空所有文档"""
        if self.use_chroma and self._chroma_client is not None:
            try:
                self._chroma_client.delete_collection(self.collection_name)
            except Exception:
                pass
            # 重新创建
            self._init_chroma()
        self._in_memory_docs = []


# 全局检索器实例（懒加载）
_retriever = None


def _get_default_embedder_type() -> str:
    """从配置获取默认 embedder 类型"""
    try:
        from detect_system.config_loader import load_config
        config = load_config()
        return config.get('configuration', {}).get('ai_services', {}).get('rag', {}).get('embedder_type', 'dashscope')
    except Exception:
        return 'dashscope'


def get_retriever(
    embedder_type: str = None,
    top_k: int = 3,
    **kwargs
) -> Retriever:
    """
    获取全局检索器实例

    Args:
        embedder_type: 向量化器类型
        top_k: 返回的最相关文档数
        **kwargs: 其他参数

    Returns:
        Retriever 实例
    """
    global _retriever

    if embedder_type is None:
        embedder_type = _get_default_embedder_type()

    if _retriever is None:
        _retriever = Retriever(
            embedder=get_embedder(embedder_type),
            top_k=top_k,
            **kwargs
        )

    return _retriever


def reset_retriever():
    """重置全局检索器实例"""
    global _retriever
    _retriever = None
