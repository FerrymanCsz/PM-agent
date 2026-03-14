"""
统一向量索引管理器

提供统一的接口管理所有类型的向量索引。
"""
from typing import Dict, List, Optional, Any
from app.core.config import settings
from .resume_index import ResumeIndex
from .knowledge_index import KnowledgeIndex


class VectorIndexManager:
    """
    统一向量索引管理器

    提供统一的接口管理所有类型的向量索引
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
        top_k: int = 3
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
            chunk_types=chunk_types
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
        """索引知识库文档"""
        return self.knowledge_index.build_index(doc_id, doc_data)

    def search_knowledge(
        self,
        query: str,
        category: str = None,
        doc_id: str = None,
        source_type: str = None,
        knowledge_type: str = None,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """搜索知识库
        
        Args:
            query: 搜索查询
            category: 技术分类过滤
            doc_id: 指定文档ID
            source_type: 来源类型过滤 (knowledge/resume)
            knowledge_type: 知识类型过滤 (technical/behavioral/career/general)
            top_k: 返回结果数
            min_score: 最小相似度阈值
        """
        results = self.knowledge_index.search_relevant(
            query=query,
            category=category,
            doc_id=doc_id,
            source_type=source_type,
            knowledge_type=knowledge_type,
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
                "knowledge_type": r.metadata.get("knowledge_type"),
                "section": r.metadata.get("section_title"),
                "score": r.score
            }
            for r in results
        ]

    def delete_knowledge_index(self, doc_id: str) -> bool:
        """删除知识库索引"""
        return self.knowledge_index.delete_by_filter({"doc_id": {"$eq": doc_id}})

    # ========== 通用接口 ==========

    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        return {
            "resume_chunks": self.resume_index.get_document_count(),
            "knowledge_chunks": self.knowledge_index.get_document_count()
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
            
            return True
        except Exception as e:
            print(f"重置索引失败: {e}")
            return False


# 全局实例
vector_index_manager = VectorIndexManager()
