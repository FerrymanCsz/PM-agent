"""
向量索引模块

提供统一的向量索引管理能力，支持简历索引和知识库索引。
"""

from .base import BaseVectorIndex, IndexDocument, SearchResult
from .resume_index import ResumeIndex
from .knowledge_index import KnowledgeIndex
from .manager import VectorIndexManager, vector_index_manager

__all__ = [
    "BaseVectorIndex",
    "IndexDocument",
    "SearchResult",
    "ResumeIndex",
    "KnowledgeIndex",
    "VectorIndexManager",
    "vector_index_manager",
]
