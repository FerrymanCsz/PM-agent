"""
查看简历数据库结构和向量索引详情
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, Resume
from app.services.vector_index import vector_index_manager


async def show_resume_structure():
    """显示简历结构和向量索引详情"""
    
    print("=" * 70)
    print("数据库中的简历结构")
    print("=" * 70)
    
    async with async_session_maker() as db:
        # 获取所有简历
        result = await db.execute(select(Resume))
        resumes = result.scalars().all()
        
        print(f"\n总共有 {len(resumes)} 份简历\n")
        
        for resume in resumes:
            print("-" * 70)
            print(f"简历ID: {resume.id}")
            print(f"文件名: {resume.file_name}")
            print(f"用户ID: {resume.user_id}")
            print(f"是否激活: {resume.is_active}")
            print(f"创建时间: {resume.created_at}")
            
            if resume.parsed_data:
                print("\n解析数据结构:")
                for key in resume.parsed_data.keys():
                    value = resume.parsed_data[key]
                    if isinstance(value, list):
                        print(f"  - {key}: 列表[{len(value)}项]")
                    elif isinstance(value, dict):
                        print(f"  - {key}: 字典")
                    else:
                        value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                        print(f"  - {key}: {value_str}")
            else:
                print("  无解析数据")
            print()


def show_vector_index_details():
    """显示向量索引详情"""
    print("=" * 70)
    print("向量索引详情")
    print("=" * 70)
    
    # 获取统计
    stats = vector_index_manager.get_stats()
    print(f"\n简历索引块总数: {stats['resume_chunks']}")
    print(f"知识库索引块总数: {stats['knowledge_chunks']}")
    
    print("\n" + "-" * 70)
    print("简历索引块列表:")
    print("-" * 70)
    
    # 获取所有简历索引
    try:
        results = vector_index_manager.resume_index.collection.get(
            include=["metadatas"]
        )
        
        if results and results.get("ids"):
            for i, (chunk_id, metadata) in enumerate(zip(results["ids"], results["metadatas"]), 1):
                print(f"\n{i}. ID: {chunk_id}")
                print(f"   简历ID: {metadata.get('resume_id', 'N/A')}")
                print(f"   块类型: {metadata.get('chunk_type', 'N/A')}")
                print(f"   块索引: {metadata.get('chunk_index', 'N/A')}")
                print(f"   来源字段: {metadata.get('source_field', 'N/A')}")
                
                # 显示额外信息
                if metadata.get('company'):
                    print(f"   公司: {metadata.get('company')}")
                if metadata.get('position'):
                    print(f"   职位: {metadata.get('position')}")
                if metadata.get('school'):
                    print(f"   学校: {metadata.get('school')}")
                if metadata.get('project_name'):
                    print(f"   项目: {metadata.get('project_name')}")
                if metadata.get('skills'):
                    skills = metadata.get('skills', '')[:50]
                    print(f"   技能: {skills}...")
        else:
            print("  无索引数据")
            
    except Exception as e:
        print(f"获取索引详情失败: {e}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # 显示数据库结构
    asyncio.run(show_resume_structure())
    
    # 显示向量索引详情
    show_vector_index_details()
