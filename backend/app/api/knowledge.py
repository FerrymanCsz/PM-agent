"""
知识库API路由
提供知识库文档的CRUD和搜索接口
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, KnowledgeDoc
from app.services.vector_index import vector_index_manager

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.post("/docs")
async def create_knowledge_doc(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    创建知识库文档
    
    Request Body:
    {
        "title": "文档标题",
        "content": "Markdown格式的正文内容",
        "category": "技术分类，如 backend/frontend/ai",
        "knowledge_type": "知识类型: technical/behavioral/career/general",
        "source_type": "来源类型: knowledge(手动上传)/resume(简历生成)"
    }
    """
    title = request.get("title", "").strip()
    content = request.get("content", "").strip()
    category = request.get("category", "general")
    knowledge_type = request.get("knowledge_type", "general")
    source_type = request.get("source_type", "knowledge")
    
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    if not content:
        raise HTTPException(status_code=400, detail="内容不能为空")
    
    try:
        # 1. 创建文档记录
        doc_id = str(uuid.uuid4())
        doc = KnowledgeDoc(
            id=doc_id,
            user_id="test_user",  # TODO: 从认证获取
            title=title,
            content=content,
            category=category,
            is_auto_generated=False,
            source_session_id=None
        )
        db.add(doc)
        await db.flush()
        
        # 2. 构建向量索引
        doc_data = {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "knowledge_type": knowledge_type,
            "source_type": source_type,
            "is_auto_generated": False
        }
        embedding_ids = vector_index_manager.index_knowledge(doc_id, doc_data)
        
        # 3. 更新文档的embedding_ids
        doc.embedding_ids = embedding_ids
        await db.commit()
        
        return {
            "id": doc_id,
            "title": title,
            "category": category,
            "knowledge_type": knowledge_type,
            "source_type": source_type,
            "chunk_count": len(embedding_ids),
            "created_at": doc.created_at.isoformat() if doc.created_at else None
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建文档失败: {str(e)}")


@router.get("/docs")
async def list_knowledge_docs(
    category: Optional[str] = Query(None, description="按分类过滤"),
    knowledge_type: Optional[str] = Query(None, description="按知识类型过滤"),
    source_type: Optional[str] = Query(None, description="按来源类型过滤"),
    keyword: Optional[str] = Query(None, description="关键词搜索标题"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识库文档列表
    
    Args:
        category: 技术分类过滤
        knowledge_type: 知识类型过滤 (technical/behavioral/career/general)
        source_type: 来源类型过滤 (knowledge/resume)
        keyword: 标题关键词搜索
        page: 页码
        page_size: 每页数量
    """
    try:
        # 构建查询条件
        query = select(KnowledgeDoc).where(KnowledgeDoc.user_id == "test_user")
        
        if category:
            query = query.where(KnowledgeDoc.category == category)
        if keyword:
            query = query.where(KnowledgeDoc.title.contains(keyword))
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.order_by(KnowledgeDoc.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        docs = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [
                {
                    "id": d.id,
                    "title": d.title,
                    "category": d.category,
                    "is_auto_generated": d.is_auto_generated,
                    "source_session_id": d.source_session_id,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                    "updated_at": d.updated_at.isoformat() if d.updated_at else None
                }
                for d in docs
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.get("/docs/{doc_id}")
async def get_knowledge_doc(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取知识库文档详情
    
    Args:
        doc_id: 文档ID
    """
    try:
        result = await db.execute(
            select(KnowledgeDoc).where(
                KnowledgeDoc.id == doc_id,
                KnowledgeDoc.user_id == "test_user"
            )
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 获取文档结构（从向量索引）
        structure = vector_index_manager.knowledge_index.get_document_structure(doc_id)
        
        return {
            "id": doc.id,
            "title": doc.title,
            "content": doc.content,
            "category": doc.category,
            "is_auto_generated": doc.is_auto_generated,
            "source_session_id": doc.source_session_id,
            "embedding_ids": doc.embedding_ids,
            "structure": structure,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档详情失败: {str(e)}")


@router.put("/docs/{doc_id}")
async def update_knowledge_doc(
    doc_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    更新知识库文档
    
    如果内容发生变化，会重新构建向量索引
    """
    try:
        result = await db.execute(
            select(KnowledgeDoc).where(
                KnowledgeDoc.id == doc_id,
                KnowledgeDoc.user_id == "test_user"
            )
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 更新字段
        title = request.get("title", "").strip()
        content = request.get("content", "").strip()
        category = request.get("category")
        
        if title:
            doc.title = title
        if content:
            doc.content = content
        if category:
            doc.category = category
        
        # 如果内容变化，重建索引
        if content and content != doc.content:
            doc_data = {
                "id": doc_id,
                "title": doc.title,
                "content": content,
                "category": doc.category,
                "is_auto_generated": doc.is_auto_generated
            }
            # 删除旧索引，创建新索引
            vector_index_manager.delete_knowledge_index(doc_id)
            embedding_ids = vector_index_manager.index_knowledge(doc_id, doc_data)
            doc.embedding_ids = embedding_ids
        
        await db.commit()
        
        return {
            "id": doc.id,
            "title": doc.title,
            "category": doc.category,
            "updated_at": doc.updated_at.isoformat() if doc.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新文档失败: {str(e)}")


@router.delete("/docs/{doc_id}")
async def delete_knowledge_doc(
    doc_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除知识库文档
    
    同时删除向量索引
    """
    try:
        result = await db.execute(
            select(KnowledgeDoc).where(
                KnowledgeDoc.id == doc_id,
                KnowledgeDoc.user_id == "test_user"
            )
        )
        doc = result.scalar_one_or_none()
        
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除向量索引
        vector_index_manager.delete_knowledge_index(doc_id)
        
        # 删除数据库记录
        await db.delete(doc)
        await db.commit()
        
        return {"message": "文档已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(e)}")


@router.post("/search")
async def search_knowledge(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    搜索知识库
    
    Request Body:
    {
        "query": "搜索关键词",
        "category": "分类过滤",
        "knowledge_type": "知识类型过滤",
        "source_type": "来源类型过滤",
        "top_k": 5
    }
    """
    query = request.get("query", "").strip()
    category = request.get("category")
    knowledge_type = request.get("knowledge_type")
    source_type = request.get("source_type")
    top_k = request.get("top_k", 5)
    
    if not query:
        raise HTTPException(status_code=400, detail="搜索关键词不能为空")
    
    try:
        # 使用向量索引搜索
        results = vector_index_manager.search_knowledge(
            query=query,
            category=category,
            top_k=top_k
        )
        
        # 进一步过滤（如果需要）
        filtered_results = results
        if knowledge_type:
            filtered_results = [r for r in filtered_results if r.get("knowledge_type") == knowledge_type]
        if source_type:
            filtered_results = [r for r in filtered_results if r.get("source_type") == source_type]
        
        return {
            "query": query,
            "total": len(filtered_results),
            "results": filtered_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/categories")
async def get_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有知识分类列表
    """
    try:
        result = await db.execute(
            select(KnowledgeDoc.category)
            .where(KnowledgeDoc.user_id == "test_user")
            .distinct()
        )
        categories = [c for c in result.scalars().all() if c]
        
        return {
            "categories": categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")
