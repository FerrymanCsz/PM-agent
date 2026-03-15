"""
向量索引模块

提供统一的向量索引管理能力，支持简历索引和知识库索引。
支持混合检索：向量检索 + BM25 + RRF融合
"""

from .base import BaseVectorIndex, IndexDocument, SearchResult
from .resume_index import ResumeIndex
from .knowledge_index import KnowledgeIndex
from .bm25_index import BM25Index, BM25Result
from .rank_fusion import RankFusion, FusionResult, rank_fusion
from .manager import VectorIndexManager, vector_index_manager

__all__ = [
    "BaseVectorIndex",
    "IndexDocument",
    "SearchResult",
    "ResumeIndex",
    "KnowledgeIndex",
    "BM25Index",
    "BM25Result",
    "RankFusion",
    "FusionResult",
    "rank_fusion",
    "VectorIndexManager",
    "vector_index_manager",
]
