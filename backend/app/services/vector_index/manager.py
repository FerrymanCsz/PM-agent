"""
统一向量索引管理器

提供统一的接口管理所有类型的向量索引。
支持混合检索：向量检索 + BM25 + RRF融合
"""
from typing import Dict, List, Optional, Any
from app.core.config import settings
from .resume_index import ResumeIndex
from .knowledge_index import KnowledgeIndex
from .bm25_index import BM25Index
from .rank_fusion import rank_fusion, FusionResult


class VectorIndexManager:
    """
    统一向量索引管理器

    提供统一的接口管理所有类型的向量索引
    支持混合检索：向量检索 + BM25 + RRF融合
    """

    _instance = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        self.db_path = db_path or settings.CHROMA_DB_PATH
        self.resume_index = ResumeIndex(self.db_path)
        self.knowledge_index = KnowledgeIndex(self.db_path)
        # 初始化 BM25 索引
        self.bm25_index = BM25Index("./bm25_index.db")
        self._initialized = True

    # ========== 简历索引接口 ==========

    def index_resume(self, resume_id: str, resume_data: Dict) -> List[str]:
        """索引简历"""
        return self.resume_index.build_index(resume_id, resume_data)

    def search_resume(
        self,
        query: str,
        resume_id: str,
        question_type: str = None,
        top_k: int = 2,
        min_score: float = 0.2
    ) -> List[Dict[str, Any]]:
        """
        搜索简历相关内容

        根据问题类型自动选择搜索的块类型
        """
        # 问题类型到块类型的映射
        type_mapping = {
            "self_intro": ["basic_info", "education", "experience"],
            "project_experience": ["project"],
            "technical": ["project", "skills", "experience"],
            "behavioral": ["experience"],
            "career_planning": ["experience", "education"],
            "salary": ["experience"],
            "general": None  # 搜索所有类型
        }

        chunk_types = type_mapping.get(question_type)

        results = self.resume_index.search_relevant(
            query=query,
            resume_id=resume_id,
            top_k=top_k,
            chunk_types=chunk_types,
            min_score=min_score  # 添加最小相似度阈值
        )

        return [
            {
                "content": r.content,
                "type": r.metadata.get("chunk_type"),
                "score": r.score,
                "metadata": {k: v for k, v in r.metadata.items() if not k.startswith("_")}
            }
            for r in results
        ]

    def get_resume_prompt_context(
        self,
        resume_id: str,
        query: str = None,
        question_type: str = None,
        max_length: int = 500
    ) -> str:
        """
        获取用于提示词的简历基础信息（仅基础信息，不包含详细内容）
        
        相关详细内容由 _retrieve_knowledge 统一处理
        """
        # 获取简历摘要
        summary = self.resume_index.get_resume_summary(resume_id)

        # 构建基础信息（仅基础统计，不检索详细内容）
        context_parts = [
            f"姓名: {summary['basic_info'].get('name', '未知')}",
            f"职位: {summary['basic_info'].get('title', '未知')}",
            f"教育经历: {summary['education_count']}段",
            f"工作经历: {summary['experience_count']}段",
            f"项目经验: {summary['project_count']}个",
        ]

        # 添加技能（最多10个）
        skills = summary['skills'][:10]
        if skills:
            context_parts.append(f"技能: {', '.join(skills)}")

        context = "\n".join(context_parts)

        return context

    def delete_resume_index(self, resume_id: str) -> bool:
        """删除简历索引"""
        return self.resume_index.delete_by_filter({"resume_id": {"$eq": resume_id}})

    # ========== 知识库索引接口 ==========

    def index_knowledge(self, doc_id: str, doc_data: Dict) -> List[str]:
        """
        索引知识库文档
        
        同时构建向量索引和 BM25 索引
        """
        # 1. 构建向量索引
        embedding_ids = self.knowledge_index.build_index(doc_id, doc_data)
        
        # 2. 构建 BM25 索引
        self._build_bm25_index(doc_id, doc_data)
        
        return embedding_ids

    def _build_bm25_index(self, doc_id: str, doc_data: Dict):
        """
        构建 BM25 索引
        
        从 doc_data 中提取分块并添加到 BM25 索引
        """
        title = doc_data.get("title", "")
        category = doc_data.get("category", "general")
        source_type = doc_data.get("source_type", "knowledge")
        
        # 分块
        chunks = self.knowledge_index.chunk_document(doc_data)
        
        # 添加到 BM25 索引
        for chunk in chunks:
            chunk_id = chunk.id
            content = chunk.content
            metadata = chunk.metadata
            
            self.bm25_index.add_document(
                doc_id=doc_id,
                chunk_id=chunk_id,
                title=title,
                content=content,
                category=category,
                source_type=source_type,
                metadata=metadata
            )

    def search_knowledge(
        self,
        query: str,
        category: str = None,
        doc_id: str = None,
        source_type: str = None,
        top_k: int = 5,
        min_score: float = 0.3,
        use_fusion: bool = True,
        fusion_method: str = "rrf"
    ) -> List[Dict[str, Any]]:
        """
        搜索知识库（支持混合检索）
        
        Args:
            query: 搜索查询
            category: 分类过滤 (general/ai/community/voice_room)
            doc_id: 指定文档ID
            source_type: 来源类型过滤 (knowledge/resume)
            top_k: 返回结果数
            min_score: 最小相似度阈值（仅向量检索）
            use_fusion: 是否使用融合检索（向量+BM25）
            fusion_method: 融合方法，"rrf" 或 "weighted"
            
        Returns:
            搜索结果列表
        """
        if not use_fusion:
            # 纯向量检索（兼容旧逻辑）
            return self._search_knowledge_vector_only(
                query, category, doc_id, source_type, top_k, min_score
            )
        
        # 混合检索：向量 + BM25 + RRF融合
        return self._search_knowledge_fusion(
            query, category, doc_id, source_type, top_k, fusion_method
        )

    def _search_knowledge_vector_only(
        self,
        query: str,
        category: str = None,
        doc_id: str = None,
        source_type: str = None,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """纯向量检索"""
        results = self.knowledge_index.search_relevant(
            query=query,
            category=category,
            doc_id=doc_id,
            source_type=source_type,
            top_k=top_k,
            min_score=min_score
        )

        return [
            {
                "content": r.content,
                "doc_id": r.metadata.get("doc_id"),
                "doc_title": r.metadata.get("doc_title"),
                "category": r.metadata.get("category"),
                "source_type": r.metadata.get("source_type"),
                "header_path": r.metadata.get("header_path"),
                "section": r.metadata.get("section_title"),
                "score": r.score,
                "sources": ["vector"]
            }
            for r in results
        ]

    def _search_knowledge_fusion(
        self,
        query: str,
        category: str = None,
        doc_id: str = None,
        source_type: str = None,
        top_k: int = 5,
        fusion_method: str = "rrf"
    ) -> List[Dict[str, Any]]:
        """
        混合检索：向量 + BM25 + RRF融合
        """
        # 1. 向量检索（扩大召回数量，过滤低质量结果）
        vector_results_raw = self.knowledge_index.search_relevant(
            query=query,
            category=category,
            doc_id=doc_id,
            source_type=source_type,
            top_k=top_k * 2,  # 召回更多用于融合
            min_score=0.2     # 过滤相似度低于0.2的结果，减少噪声
        )
        
        # 格式化向量结果
        vector_results = [
            {
                "content": r.content,
                "doc_id": r.metadata.get("doc_id"),
                "chunk_id": r.id,
                "doc_title": r.metadata.get("doc_title"),
                "category": r.metadata.get("category"),
                "source_type": r.metadata.get("source_type"),
                "header_path": r.metadata.get("header_path"),
                "section_title": r.metadata.get("section_title"),
                "score": r.score
            }
            for r in vector_results_raw
        ]
        
        # 2. BM25 检索
        bm25_results_raw = self.bm25_index.search(
            query=query,
            category=category,
            source_type=source_type,
            top_k=top_k * 2
        )
        
        # 格式化 BM25 结果
        bm25_results = [
            {
                "content": r.content,
                "doc_id": r.doc_id,
                "chunk_id": r.chunk_id,
                "title": r.title,
                "category": r.metadata.get("category"),
                "source_type": r.metadata.get("source_type"),
                "header_path": r.metadata.get("header_path"),
                "section_title": r.metadata.get("section_title"),
                "score": r.score
            }
            for r in bm25_results_raw
        ]
        
        # 3. RRF 融合
        fusion_results = rank_fusion.fuse(
            vector_results=vector_results,
            bm25_results=bm25_results,
            method=fusion_method,
            top_k=top_k
        )
        
        # 4. 格式化返回结果
        return [
            {
                "content": r.content,
                "doc_id": r.doc_id,
                "doc_title": r.metadata.get("doc_title", ""),
                "category": r.metadata.get("category", ""),
                "source_type": r.metadata.get("source_type", ""),
                "header_path": r.metadata.get("header_path", ""),
                "section": r.metadata.get("section", ""),
                "score": r.score,  # 融合后的分数
                "sources": r.sources,  # ["vector", "bm25"] 或 ["vector"] 等
                "vector_rank": r.vector_rank,
                "bm25_rank": r.bm25_rank,
                "vector_score": r.vector_score,
                "bm25_score": r.bm25_score
            }
            for r in fusion_results
        ]

    def delete_knowledge_index(self, doc_id: str) -> bool:
        """
        删除知识库索引
        
        同时删除向量索引和 BM25 索引
        """
        # 删除向量索引
        vector_deleted = self.knowledge_index.delete_by_filter({"doc_id": {"$eq": doc_id}})
        
        # 删除 BM25 索引
        self.bm25_index.delete_by_doc_id(doc_id)
        
        return vector_deleted

    def rebuild_bm25_index(self):
        """
        重建 BM25 索引
        
        从向量索引中导出所有文档并重建 BM25 索引
        """
        # 获取所有知识库文档
        all_docs = self.knowledge_index.collection.get(include=["metadatas", "documents"])
        
        if not all_docs or not all_docs.get("ids"):
            print("没有知识库文档需要重建")
            return
        
        # 按 doc_id 分组
        doc_chunks = {}
        for doc_id, metadata, content in zip(
            all_docs["ids"],
            all_docs["metadatas"],
            all_docs["documents"]
        ):
            parent_doc_id = metadata.get("doc_id")
            if parent_doc_id not in doc_chunks:
                doc_chunks[parent_doc_id] = []
            doc_chunks[parent_doc_id].append({
                "chunk_id": doc_id,
                "content": content,
                "metadata": metadata
            })
        
        # 重建每个文档的 BM25 索引
        for doc_id, chunks in doc_chunks.items():
            # 获取文档标题
            title = chunks[0]["metadata"].get("doc_title", "")
            category = chunks[0]["metadata"].get("category", "general")
            source_type = chunks[0]["metadata"].get("source_type", "knowledge")
            
            for chunk in chunks:
                self.bm25_index.add_document(
                    doc_id=doc_id,
                    chunk_id=chunk["chunk_id"],
                    title=title,
                    content=chunk["content"],
                    category=category,
                    source_type=source_type,
                    metadata=chunk["metadata"]
                )
        
        print(f"BM25 索引重建完成，共 {len(doc_chunks)} 个文档")

    # ========== 通用接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        bm25_stats = self.bm25_index.get_stats()
        
        return {
            "resume_chunks": self.resume_index.get_document_count(),
            "knowledge_chunks": self.knowledge_index.get_document_count(),
            "bm25_stats": bm25_stats
        }

    def reset_all(self) -> bool:
        """重置所有索引（谨慎使用）"""
        try:
            # 获取所有简历ID并删除
            resume_results = self.resume_index.collection.get(include=["metadatas"])
            if resume_results and resume_results.get("ids"):
                for doc_id in resume_results["ids"]:
                    self.resume_index.delete_by_ids([doc_id])
            
            # 获取所有知识库ID并删除
            knowledge_results = self.knowledge_index.collection.get(include=["metadatas"])
            if knowledge_results and knowledge_results.get("ids"):
                for doc_id in knowledge_results["ids"]:
                    self.knowledge_index.delete_by_ids([doc_id])
            
            # 清空 BM25 索引
            self.bm25_index.rebuild_index([])
            
            return True
        except Exception as e:
            print(f"重置索引失败: {e}")
            return False


# 全局实例
vector_index_manager = VectorIndexManager()
