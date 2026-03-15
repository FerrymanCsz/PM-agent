"""
知识库向量索引

提供知识库文档的智能分块和向量索引功能。
"""
from typing import List, Dict, Any, Optional
import re
from .base import BaseVectorIndex, IndexDocument, SearchResult


class KnowledgeIndex(BaseVectorIndex):
    """知识库向量索引"""

    def __init__(self, db_path: str = "./chroma_db"):
        super().__init__("knowledge_chunks", db_path)

    def chunk_document(self, doc_data: Dict) -> List[IndexDocument]:
        """
        知识库文档分块策略

        支持多种分块策略：
        1. 按标题分块（Markdown标题）
        2. 按段落分块
        3. 按固定长度分块（带重叠）
        """
        content = doc_data.get("content", "")
        doc_id = doc_data.get("id", "unknown")
        category = doc_data.get("category", "general")

        if not content:
            return []

        # 检测文档类型并选择分块策略
        if self._is_markdown(content):
            chunks = self._chunk_by_markdown(content, doc_id)
        else:
            chunks = self._chunk_by_paragraph(content, doc_id)

        # 添加文档级元数据
        for chunk in chunks:
            chunk.metadata.update({
                "doc_id": doc_id,
                "doc_title": doc_data.get("title", ""),
                "category": category,
                "source_type": doc_data.get("source_type", "knowledge"),  # 来源类型: knowledge/resume
                "is_auto_generated": str(doc_data.get("is_auto_generated", False)),
                "source_session_id": doc_data.get("source_session_id", "")
            })

        return chunks

    def _is_markdown(self, content: str) -> bool:
        """检测是否为Markdown格式"""
        markdown_patterns = [
            r'^#{1,6}\s',  # 标题
            r'^\s*[-*+]\s',  # 列表
            r'^\s*\d+\.\s',  # 有序列表
            r'\[.*?\]\(.*?\)',  # 链接
            r'```[\s\S]*?```',  # 代码块
        ]

        for pattern in markdown_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False

    def _chunk_by_markdown(
        self,
        content: str,
        doc_id: str
    ) -> List[IndexDocument]:
        """
        按Markdown标题分块（支持多级标题结构）
        
        分块策略：
        1. 按所有标题级别 (# ~ ######) 识别文档结构
        2. 优先按二级标题 (##) 分块
        3. 如果没有二级标题，按一级标题分块
        4. 如果块太大，进一步分割，保留子标题信息
        """
        chunks = []
        
        # 分析文档结构，提取所有标题
        headers = self._extract_headers(content)
        
        # 决定分割策略
        if self._has_header_level(headers, 2):
            # 有二级标题，按二级标题分割
            sections = self._split_by_header_level(content, 2)
        elif self._has_header_level(headers, 1):
            # 只有一级标题，按一级标题分割
            sections = self._split_by_header_level(content, 1)
        else:
            # 没有标题，按段落分块
            return self._chunk_by_paragraph(content, doc_id)

        for idx, (section, header_info) in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            # 提取标题层级信息
            section_title = header_info.get("title", f"Section {idx}")
            header_level = header_info.get("level", 0)
            header_path = header_info.get("path", section_title)

            # 如果块太大，进一步分割（保留子标题上下文）
            sub_chunks = self._split_large_chunk_with_context(section, max_length=1000)

            for sub_idx, (sub_chunk, sub_context) in enumerate(sub_chunks):
                chunk_id = f"{doc_id}_md_{idx}_{sub_idx}"
                
                # 构建元数据
                metadata = {
                    "chunk_type": "markdown_section",
                    "chunk_index": f"{idx}.{sub_idx}",
                    "section_title": section_title,
                    "section_index": idx,
                    "header_level": header_level,
                    "header_path": header_path,
                }
                
                # 如果有子上下文（子标题），添加到元数据
                if sub_context:
                    metadata["sub_context"] = sub_context[:200]  # 限制长度
                
                # 标记是否是大块的分割
                if sub_idx > 0:
                    metadata["is_split_chunk"] = True
                    metadata["parent_chunk"] = f"{doc_id}_md_{idx}_0"
                
                chunks.append(IndexDocument(
                    id=chunk_id,
                    content=sub_chunk,
                    metadata=metadata
                ))

        return chunks

    def _extract_headers(self, content: str) -> List[Dict]:
        """提取文档中的所有标题信息"""
        headers = []
        # 匹配所有级别的标题
        pattern = r'^(#{1,6})\s*(.+)$'
        for match in re.finditer(pattern, content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append({
                "level": level,
                "title": title,
                "position": match.start()
            })
        return headers

    def _has_header_level(self, headers: List[Dict], level: int) -> bool:
        """检查是否有指定级别的标题"""
        return any(h["level"] == level for h in headers)

    def _split_by_header_level(self, content: str, level: int) -> List[tuple]:
        """
        按指定级别的标题分割文档
        
        Returns:
            List[(section_content, header_info)]
        """
        # 找到所有指定级别的标题位置
        # 构建匹配模式，如 level=2 时匹配 ^##\s+(.+)$
        hashes = '#' * level
        header_pattern = rf'^{hashes}\s+(.+)$'
        headers = list(re.finditer(header_pattern, content, re.MULTILINE))
        
        result = []
        
        for i, header_match in enumerate(headers):
            # 确定当前段落的起始和结束位置
            start = header_match.start()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(content)
            
            # 提取段落内容
            section = content[start:end].strip()
            if not section:
                continue
            
            # 提取当前段的标题
            title = header_match.group(1).strip()
            
            # 构建路径：只包含当前标题（因为是按同级标题分割）
            header_info = {
                "level": level,
                "title": title,
                "path": title
            }
            
            result.append((section, header_info))
        
        return result

    def _parse_section_header(self, section: str, current_path: List[str]) -> Dict:
        """解析段落的标题信息"""
        # 匹配标题
        match = re.match(r'^(#{1,6})\s*(.+)$', section.strip(), re.MULTILINE)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            return {
                "level": level,
                "title": title,
                "path": ""
            }
        
        # 没有标题的段落
        return {
            "level": 0,
            "title": "无标题段落",
            "path": " > ".join(current_path) if current_path else "正文"
        }

    def _split_large_chunk_with_context(self, content: str, max_length: int = 1000) -> List[tuple]:
        """
        分割大文本块，保留子标题作为上下文
        
        Returns:
            List[(chunk_content, sub_context)]
        """
        if len(content) <= max_length:
            return [(content, "")]
        
        # 提取子标题（三级及以下）
        sub_headers = re.findall(r'^(#{3,6})\s*(.+)$', content, re.MULTILINE)
        
        # 按句子分割
        sentences = re.split(r'(?<=[。！？.!?])\s+', content)
        
        chunks = []
        current_chunk = []
        current_length = 0
        current_context = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 检查是否是子标题行
            header_match = re.match(r'^(#{3,6})\s*(.+)$', sentence)
            if header_match:
                # 更新上下文为当前子标题
                current_context = header_match.group(2).strip()[:100]
            
            sentence_length = len(sentence)
            
            # 单句超过限制，强制分割
            if sentence_length > max_length:
                if current_chunk:
                    chunks.append((''.join(current_chunk), current_context))
                    current_chunk = []
                    current_length = 0
                
                for i in range(0, sentence_length, max_length):
                    chunks.append((sentence[i:i + max_length], current_context))
            
            # 加入当前块
            elif current_length + sentence_length < max_length:
                current_chunk.append(sentence)
                current_length += sentence_length
            
            # 保存当前块，开始新块
            else:
                if current_chunk:
                    chunks.append((''.join(current_chunk), current_context))
                current_chunk = [sentence]
                current_length = sentence_length
        
        # 保存最后一个块
        if current_chunk:
            chunks.append((''.join(current_chunk), current_context))
        
        return chunks

    def _chunk_by_paragraph(
        self,
        content: str,
        doc_id: str
    ) -> List[IndexDocument]:
        """按段落分块"""
        chunks = []

        # 按段落分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        current_chunk = []
        current_length = 0
        chunk_idx = 0

        for para in paragraphs:
            para_length = len(para)

            # 如果当前段落太长，需要分割
            if para_length > 500:
                # 先保存当前块
                if current_chunk:
                    chunk_content = '\n\n'.join(current_chunk)
                    chunks.append(IndexDocument(
                        id=f"{doc_id}_para_{chunk_idx}",
                        content=chunk_content,
                        metadata={
                            "chunk_type": "paragraph",
                            "chunk_index": chunk_idx,
                            "paragraph_count": len(current_chunk)
                        }
                    ))
                    chunk_idx += 1
                    current_chunk = []
                    current_length = 0

                # 分割长段落
                sub_paras = self._split_large_chunk(para, max_length=500)
                for sub_idx, sub_para in enumerate(sub_paras):
                    chunks.append(IndexDocument(
                        id=f"{doc_id}_para_{chunk_idx}_{sub_idx}",
                        content=sub_para,
                        metadata={
                            "chunk_type": "paragraph",
                            "chunk_index": f"{chunk_idx}.{sub_idx}",
                            "is_sub_chunk": True
                        }
                    ))

            # 如果加入当前段落后不超过限制，就加入
            elif current_length + para_length < 800:
                current_chunk.append(para)
                current_length += para_length

            # 否则保存当前块，开始新块
            else:
                if current_chunk:
                    chunk_content = '\n\n'.join(current_chunk)
                    chunks.append(IndexDocument(
                        id=f"{doc_id}_para_{chunk_idx}",
                        content=chunk_content,
                        metadata={
                            "chunk_type": "paragraph",
                            "chunk_index": chunk_idx,
                            "paragraph_count": len(current_chunk)
                        }
                    ))
                    chunk_idx += 1

                current_chunk = [para]
                current_length = para_length

        # 保存最后一个块
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunks.append(IndexDocument(
                id=f"{doc_id}_para_{chunk_idx}",
                content=chunk_content,
                metadata={
                    "chunk_type": "paragraph",
                    "chunk_index": chunk_idx,
                    "paragraph_count": len(current_chunk)
                }
            ))

        return chunks

    def _split_large_chunk(self, content: str, max_length: int = 1000) -> List[str]:
        """分割大文本块（按句子，保持语义完整）"""
        # 按句子分割
        sentences = re.split(r'(?<=[。！？.!?])\s+', content)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # 单句就超过限制，强制分割
            if sentence_length > max_length:
                if current_chunk:
                    chunks.append(''.join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # 按固定长度分割
                for i in range(0, sentence_length, max_length):
                    chunks.append(sentence[i:i + max_length])

            # 加入当前块
            elif current_length + sentence_length < max_length:
                current_chunk.append(sentence)
                current_length += sentence_length

            # 保存当前块，开始新块
            else:
                if current_chunk:
                    chunks.append(''.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length

        # 保存最后一个块
        if current_chunk:
            chunks.append(''.join(current_chunk))

        return chunks

    def build_index(self, doc_id: str, doc_data: Dict) -> List[str]:
        """构建知识库索引"""
        # 先删除旧索引
        self.delete_by_filter({"doc_id": {"$eq": doc_id}})

        # 分块并索引
        chunks = self.chunk_document({**doc_data, "id": doc_id})
        return self.add_documents(chunks)

    def search_relevant(
        self,
        query: str,
        category: str = None,
        doc_id: str = None,
        source_type: str = None,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[SearchResult]:
        """
        搜索知识库

        Args:
            query: 查询问题
            category: 指定类别过滤 (general/ai/community/voice_room)
            doc_id: 指定文档过滤
            source_type: 来源类型过滤 (knowledge/resume)
            top_k: 返回结果数
            min_score: 最小相似度阈值
        """
        filter_conditions = []

        if doc_id:
            filter_conditions.append({"doc_id": {"$eq": doc_id}})
        if category:
            filter_conditions.append({"category": {"$eq": category}})
        if source_type:
            filter_conditions.append({"source_type": {"$eq": source_type}})

        # 构建过滤字典
        if len(filter_conditions) == 0:
            filter_dict = None
        elif len(filter_conditions) == 1:
            filter_dict = filter_conditions[0]
        else:
            filter_dict = {"$and": filter_conditions}

        results = self.search(query, filter_dict, top_k * 2)

        # 过滤低分结果
        filtered_results = [r for r in results if r.score >= min_score]

        return filtered_results[:top_k]

    def get_document_structure(self, doc_id: str) -> Dict[str, Any]:
        """获取文档结构（用于展示大纲）"""
        try:
            results = self.collection.get(
                where={"doc_id": {"$eq": doc_id}},
                include=["metadatas"]
            )
        except Exception as e:
            print(f"获取文档结构失败: {e}")
            return {
                "doc_id": doc_id,
                "sections": [],
                "total_chunks": 0
            }

        structure = {
            "doc_id": doc_id,
            "sections": [],
            "total_chunks": len(results.get("ids", []))
        }

        seen_titles = set()
        for metadata in results.get("metadatas", []):
            if metadata.get("chunk_type") == "markdown_section":
                section_title = metadata.get("section_title", "")
                if section_title and section_title not in seen_titles:
                    seen_titles.add(section_title)
                    structure["sections"].append({
                        "title": section_title,
                        "index": metadata.get("section_index", 0)
                    })

        structure["sections"].sort(key=lambda x: x["index"])
        return structure
