"""
向量索引基类

提供所有向量索引的基础功能。
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import chromadb
from chromadb.config import Settings as ChromaSettings


@dataclass
class IndexDocument:
    """索引文档标准格式"""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """搜索结果标准格式"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    distance: float


class BaseVectorIndex(ABC):
    """向量索引基类"""

    def __init__(self, collection_name: str, db_path: str = "./chroma_db"):
        self.collection_name = collection_name
        self.db_path = db_path
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """获取或创建集合"""
        try:
            return self.client.get_collection(name=self.collection_name)
        except Exception:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
            )

    @abstractmethod
    def chunk_document(self, document: Any) -> List[IndexDocument]:
        """文档分块策略（子类实现）"""
        pass

    @abstractmethod
    def build_index(self, document_id: str, document: Any) -> List[str]:
        """构建索引（子类实现）"""
        pass

    def add_documents(self, documents: List[IndexDocument]) -> List[str]:
        """添加文档到索引"""
        if not documents:
            return []

        ids = [doc.id for doc in documents]
        contents = [doc.content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        self.collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas
        )
        return ids

    def search(
        self,
        query: str,
        filter_dict: Optional[Dict] = None,
        top_k: int = 5
    ) -> List[SearchResult]:
        """语义搜索"""
        results = self.collection.query(
            query_texts=[query],
            where=filter_dict,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                search_results.append(SearchResult(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    score=1 - results["distances"][0][i],  # 距离转相似度
                    distance=results["distances"][0][i]
                ))

        return search_results

    def delete_by_filter(self, filter_dict: Dict) -> bool:
        """根据条件删除文档"""
        try:
            self.collection.delete(where=filter_dict)
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False

    def delete_by_ids(self, ids: List[str]) -> bool:
        """根据ID删除文档"""
        if not ids:
            return True
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False

    def update_document(self, doc_id: str, document: IndexDocument) -> bool:
        """更新文档"""
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[document.content],
                metadatas=[document.metadata]
            )
            return True
        except Exception as e:
            print(f"更新文档失败: {e}")
            return False

    def get_document_count(self) -> int:
        """获取文档数量"""
        return self.collection.count()
