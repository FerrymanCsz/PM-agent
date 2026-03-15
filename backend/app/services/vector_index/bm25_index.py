"""
BM25 全文检索索引

基于 SQLite FTS5 实现，提供倒排索引和 BM25 排序功能。
与向量索引配合使用，实现混合检索。
支持中英文分词（使用 jieba 进行中文分词）。
"""
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

# 导入 jieba 中文分词
try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    print("警告: jieba 未安装，中文分词功能将不可用")


@dataclass
class BM25Result:
    """BM25 搜索结果"""
    doc_id: str
    chunk_id: str
    title: str
    content: str
    score: float
    metadata: Dict[str, Any]


class BM25Index:
    """BM25 全文检索索引管理器"""
    
    def __init__(self, db_path: str = "./bm25_index.db"):
        """
        初始化 BM25 索引
        
        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 创建 FTS5 虚拟表用于全文检索
        # 使用 porter 分词器支持英文词干提取
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                doc_id,
                chunk_id,
                title,
                content,
                category,
                source_type,
                tokenize='porter'
            )
        """)
        
        # 创建元数据表存储额外信息
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunk_metadata (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                title TEXT,
                header_path TEXT,
                section_title TEXT,
                category TEXT,
                source_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引加速查询
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metadata_doc_id 
            ON chunk_metadata(doc_id)
        """)
        
        self.conn.commit()
    
    def add_document(
        self,
        doc_id: str,
        chunk_id: str,
        title: str,
        content: str,
        category: str = "general",
        source_type: str = "knowledge",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        添加文档到 BM25 索引
        
        Args:
            doc_id: 文档ID
            chunk_id: 块ID
            title: 标题
            content: 内容
            category: 分类
            source_type: 来源类型
            metadata: 额外元数据
        """
        cursor = self.conn.cursor()
        
        # 插入 FTS 索引
        cursor.execute("""
            INSERT OR REPLACE INTO knowledge_fts 
            (doc_id, chunk_id, title, content, category, source_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, chunk_id, title, content, category, source_type))
        
        # 插入元数据
        header_path = metadata.get("header_path", "") if metadata else ""
        section_title = metadata.get("section_title", "") if metadata else ""
        
        cursor.execute("""
            INSERT OR REPLACE INTO chunk_metadata 
            (chunk_id, doc_id, title, header_path, section_title, category, source_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chunk_id, doc_id, title, header_path, section_title, category, source_type))
        
        self.conn.commit()
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        批量添加文档
        
        Args:
            documents: 文档列表，每个文档是一个字典
        """
        for doc in documents:
            self.add_document(
                doc_id=doc["doc_id"],
                chunk_id=doc["chunk_id"],
                title=doc.get("title", ""),
                content=doc["content"],
                category=doc.get("category", "general"),
                source_type=doc.get("source_type", "knowledge"),
                metadata=doc.get("metadata", {})
            )
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        source_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[BM25Result]:
        """
        BM25 检索
        
        Args:
            query: 查询文本
            category: 分类过滤
            source_type: 来源类型过滤
            top_k: 返回结果数
            
        Returns:
            BM25 搜索结果列表
        """
        cursor = self.conn.cursor()
        
        # 清理查询文本，移除特殊字符
        query = self._clean_query(query)
        if not query:
            return []
        
        # 构建基础查询
        base_sql = """
            SELECT 
                fts.doc_id,
                fts.chunk_id,
                fts.title,
                fts.content,
                bm25(knowledge_fts) as score
            FROM knowledge_fts fts
            WHERE knowledge_fts MATCH ?
        """
        
        params = [query]
        
        # 添加过滤条件
        if category:
            base_sql += " AND fts.category = ?"
            params.append(category)
        
        if source_type:
            base_sql += " AND fts.source_type = ?"
            params.append(source_type)
        
        # 排序和限制
        base_sql += " ORDER BY score DESC LIMIT ?"
        params.append(top_k)
        
        try:
            cursor.execute(base_sql, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                # 获取元数据
                metadata = self._get_metadata(row["chunk_id"])
                
                results.append(BM25Result(
                    doc_id=row["doc_id"],
                    chunk_id=row["chunk_id"],
                    title=row["title"],
                    content=row["content"],
                    score=float(row["score"]),
                    metadata=metadata or {}
                ))
            
            return results
            
        except sqlite3.Error as e:
            print(f"BM25 检索失败: {e}")
            return []
    
    def _get_metadata(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """获取块的元数据"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chunk_metadata WHERE chunk_id = ?
        """, (chunk_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                "doc_id": row["doc_id"],
                "title": row["title"],
                "header_path": row["header_path"],
                "section_title": row["section_title"],
                "category": row["category"],
                "source_type": row["source_type"]
            }
        return None
    
    def _clean_query(self, query: str) -> str:
        """
        清理查询文本并分词
        
        支持中英文分词：
        - 英文：按空格分割，porter 词干提取
        - 中文：使用 jieba 分词
        
        SQLite FTS5 对特殊字符敏感，需要清理
        """
        if not query or not query.strip():
            return ""
        
        # 移除特殊字符，保留中英文和数字
        query = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        
        if not query:
            return ""
        
        # 分词处理
        words = self._tokenize(query)
        
        if len(words) > 1:
            # 使用 AND 连接多个词（必须同时包含）
            return " AND ".join(words)
        elif len(words) == 1:
            return words[0]
        return ""
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词处理
        
        - 中文：使用 jieba 分词
        - 英文：按空格分割
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果列表
        """
        if not text:
            return []
        
        words = []
        
        # 检查是否包含中文
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', text))
        
        if has_chinese and JIEBA_AVAILABLE:
            # 使用 jieba 进行中文分词
            # cut_for_search 模式更适合搜索引擎
            seg_list = jieba.cut_for_search(text)
            words = [w.strip() for w in seg_list if w.strip() and len(w.strip()) > 1]
        else:
            # 英文或 jieba 不可用时，按空格分割
            words = [w.strip() for w in text.split() if w.strip() and len(w.strip()) > 1]
        
        # 去重并保持顺序
        seen = set()
        unique_words = []
        for w in words:
            w_lower = w.lower()
            if w_lower not in seen:
                seen.add(w_lower)
                unique_words.append(w)
        
        return unique_words
    
    def delete_by_doc_id(self, doc_id: str):
        """
        根据文档ID删除所有相关块
        
        Args:
            doc_id: 文档ID
        """
        cursor = self.conn.cursor()
        
        # 获取该文档的所有 chunk_id
        cursor.execute("""
            SELECT chunk_id FROM chunk_metadata WHERE doc_id = ?
        """, (doc_id,))
        
        chunk_ids = [row["chunk_id"] for row in cursor.fetchall()]
        
        # 从 FTS 索引删除
        for chunk_id in chunk_ids:
            cursor.execute("""
                DELETE FROM knowledge_fts WHERE chunk_id = ?
            """, (chunk_id,))
        
        # 从元数据表删除
        cursor.execute("""
            DELETE FROM chunk_metadata WHERE doc_id = ?
        """, (doc_id,))
        
        self.conn.commit()
    
    def delete_by_chunk_id(self, chunk_id: str):
        """
        根据块ID删除
        
        Args:
            chunk_id: 块ID
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            DELETE FROM knowledge_fts WHERE chunk_id = ?
        """, (chunk_id,))
        
        cursor.execute("""
            DELETE FROM chunk_metadata WHERE chunk_id = ?
        """, (chunk_id,))
        
        self.conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取索引统计信息"""
        cursor = self.conn.cursor()
        
        # 文档数量
        cursor.execute("SELECT COUNT(DISTINCT doc_id) FROM chunk_metadata")
        doc_count = cursor.fetchone()[0]
        
        # 块数量
        cursor.execute("SELECT COUNT(*) FROM chunk_metadata")
        chunk_count = cursor.fetchone()[0]
        
        # 分类统计
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM chunk_metadata 
            GROUP BY category
        """)
        category_stats = {row["category"]: row["count"] for row in cursor.fetchall()}
        
        return {
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "category_stats": category_stats
        }
    
    def rebuild_index(self, documents: List[Dict[str, Any]]):
        """
        重建整个索引
        
        Args:
            documents: 所有文档的列表
        """
        # 清空现有索引
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM knowledge_fts")
        cursor.execute("DELETE FROM chunk_metadata")
        self.conn.commit()
        
        # 重新添加所有文档
        self.add_documents(documents)
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
    
    def __del__(self):
        """析构时关闭连接"""
        if hasattr(self, 'conn'):
            self.conn.close()
