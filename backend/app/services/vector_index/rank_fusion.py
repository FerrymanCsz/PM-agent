"""
排序融合模块

提供多种结果融合算法：
- RRF (Reciprocal Rank Fusion): 倒数排序融合
- Weighted Fusion: 加权融合
- Normalize: 分数归一化
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class FusionResult:
    """融合后的搜索结果"""
    doc_id: str
    chunk_id: str
    content: str
    score: float  # 融合后的分数
    sources: List[str]  # 来源列表 ["vector", "bm25"]
    vector_rank: Optional[int] = None
    bm25_rank: Optional[int] = None
    vector_score: Optional[float] = None
    bm25_score: Optional[float] = None
    metadata: Dict[str, Any] = None


class RankFusion:
    """排序融合器"""
    
    def __init__(self, k: int = 60):
        """
        初始化融合器
        
        Args:
            k: RRF 常数，用于平滑排名影响，默认 60
        """
        self.k = k
    
    def rrf_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[FusionResult]:
        """
        RRF (Reciprocal Rank Fusion) 融合
        
        公式: score = Σ 1/(k + rank_i)
        
        Args:
            vector_results: 向量检索结果列表
            bm25_results: BM25 检索结果列表
            top_k: 返回结果数
            
        Returns:
            融合后的结果列表
        """
        # 存储每个文档的 RRF 分数和来源信息
        rrf_scores = defaultdict(float)
        sources = defaultdict(set)
        ranks = defaultdict(dict)
        scores = defaultdict(dict)
        contents = {}
        metadata = {}
        
        # 处理向量检索结果
        for rank, result in enumerate(vector_results, start=1):
            doc_id = result.get("doc_id", "")
            chunk_id = result.get("chunk_id", "")
            key = f"{doc_id}_{chunk_id}"
            
            rrf_scores[key] += 1.0 / (self.k + rank)
            sources[key].add("vector")
            ranks[key]["vector"] = rank
            scores[key]["vector"] = result.get("score", 0.0)
            
            if key not in contents:
                contents[key] = result.get("content", "")
                metadata[key] = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "doc_title": result.get("doc_title", ""),
                    "category": result.get("category", ""),
                    "header_path": result.get("header_path", ""),
                    "section": result.get("section", ""),
                }
        
        # 处理 BM25 检索结果
        for rank, result in enumerate(bm25_results, start=1):
            doc_id = result.get("doc_id", "")
            chunk_id = result.get("chunk_id", "")
            key = f"{doc_id}_{chunk_id}"
            
            rrf_scores[key] += 1.0 / (self.k + rank)
            sources[key].add("bm25")
            ranks[key]["bm25"] = rank
            scores[key]["bm25"] = result.get("score", 0.0)
            
            if key not in contents:
                contents[key] = result.get("content", "")
                metadata[key] = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "doc_title": result.get("title", ""),
                    "category": result.get("category", ""),
                    "header_path": result.get("metadata", {}).get("header_path", ""),
                    "section": result.get("metadata", {}).get("section_title", ""),
                }
        
        # 构建融合结果
        fusion_results = []
        for key, score in rrf_scores.items():
            fusion_results.append(FusionResult(
                doc_id=metadata[key]["doc_id"],
                chunk_id=metadata[key]["chunk_id"],
                content=contents[key],
                score=score,
                sources=list(sources[key]),
                vector_rank=ranks[key].get("vector"),
                bm25_rank=ranks[key].get("bm25"),
                vector_score=scores[key].get("vector"),
                bm25_score=scores[key].get("bm25"),
                metadata=metadata[key]
            ))
        
        # 按融合分数排序，取 top_k
        fusion_results.sort(key=lambda x: x.score, reverse=True)
        return fusion_results[:top_k]
    
    def weighted_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        top_k: int = 10
    ) -> List[FusionResult]:
        """
        加权融合
        
        公式: score = w1 * norm(score_vector) + w2 * norm(score_bm25)
        
        Args:
            vector_results: 向量检索结果列表
            bm25_results: BM25 检索结果列表
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            top_k: 返回结果数
            
        Returns:
            融合后的结果列表
        """
        # 归一化分数
        vector_norm = self._normalize_scores([r.get("score", 0) for r in vector_results])
        bm25_norm = self._normalize_scores([r.get("score", 0) for r in bm25_results])
        
        # 存储加权分数
        weighted_scores = defaultdict(float)
        sources = defaultdict(set)
        ranks = defaultdict(dict)
        original_scores = defaultdict(dict)
        contents = {}
        metadata = {}
        
        # 处理向量结果
        for rank, (result, norm_score) in enumerate(zip(vector_results, vector_norm), start=1):
            doc_id = result.get("doc_id", "")
            chunk_id = result.get("chunk_id", "")
            key = f"{doc_id}_{chunk_id}"
            
            weighted_scores[key] += vector_weight * norm_score
            sources[key].add("vector")
            ranks[key]["vector"] = rank
            original_scores[key]["vector"] = result.get("score", 0.0)
            
            if key not in contents:
                contents[key] = result.get("content", "")
                metadata[key] = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "doc_title": result.get("doc_title", ""),
                    "category": result.get("category", ""),
                    "header_path": result.get("header_path", ""),
                    "section": result.get("section", ""),
                }
        
        # 处理 BM25 结果
        for rank, (result, norm_score) in enumerate(zip(bm25_results, bm25_norm), start=1):
            doc_id = result.get("doc_id", "")
            chunk_id = result.get("chunk_id", "")
            key = f"{doc_id}_{chunk_id}"
            
            weighted_scores[key] += bm25_weight * norm_score
            sources[key].add("bm25")
            ranks[key]["bm25"] = rank
            original_scores[key]["bm25"] = result.get("score", 0.0)
            
            if key not in contents:
                contents[key] = result.get("content", "")
                metadata[key] = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "doc_title": result.get("title", ""),
                    "category": result.get("category", ""),
                    "header_path": result.get("metadata", {}).get("header_path", ""),
                    "section": result.get("metadata", {}).get("section_title", ""),
                }
        
        # 构建融合结果
        fusion_results = []
        for key, score in weighted_scores.items():
            fusion_results.append(FusionResult(
                doc_id=metadata[key]["doc_id"],
                chunk_id=metadata[key]["chunk_id"],
                content=contents[key],
                score=score,
                sources=list(sources[key]),
                vector_rank=ranks[key].get("vector"),
                bm25_rank=ranks[key].get("bm25"),
                vector_score=original_scores[key].get("vector"),
                bm25_score=original_scores[key].get("bm25"),
                metadata=metadata[key]
            ))
        
        # 排序并返回
        fusion_results.sort(key=lambda x: x.score, reverse=True)
        return fusion_results[:top_k]
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """
        Min-Max 归一化
        
        公式: norm_score = (score - min) / (max - min)
        
        Args:
            scores: 原始分数列表
            
        Returns:
            归一化后的分数列表
        """
        if not scores:
            return []
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def fuse(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        method: str = "rrf",
        top_k: int = 10,
        **kwargs
    ) -> List[FusionResult]:
        """
        统一的融合接口
        
        Args:
            vector_results: 向量检索结果列表
            bm25_results: BM25 检索结果列表
            method: 融合方法，"rrf" 或 "weighted"
            top_k: 返回结果数
            **kwargs: 额外参数（如 weight_vector, weight_bm25）
            
        Returns:
            融合后的结果列表
        """
        if method == "rrf":
            return self.rrf_fusion(vector_results, bm25_results, top_k)
        elif method == "weighted":
            vector_weight = kwargs.get("vector_weight", 0.6)
            bm25_weight = kwargs.get("bm25_weight", 0.4)
            return self.weighted_fusion(
                vector_results, bm25_results,
                vector_weight, bm25_weight, top_k
            )
        else:
            raise ValueError(f"Unknown fusion method: {method}")


# 全局融合器实例
rank_fusion = RankFusion(k=60)
