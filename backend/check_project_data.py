"""
检查简历项目数据和向量索引内容
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, Resume
from app.services.vector_index import vector_index_manager


async def check_project_data():
    """检查项目数据和向量索引"""
    print("=" * 80)
    print("检查项目数据和向量索引")
    print("=" * 80)
    
    async with async_session_maker() as db:
        result = await db.execute(select(Resume))
        resumes = result.scalars().all()
        
        for resume in resumes:
            print(f"\n简历ID: {resume.id}")
            print(f"文件名: {resume.file_name}")
            
            # 检查原始项目数据
            projects = resume.parsed_data.get('projects', [])
            print(f"\n项目数量: {len(projects)}")
            
            for i, proj in enumerate(projects):
                print(f"\n--- 项目 {i+1} ---")
                print(f"名称: {proj.get('name', 'N/A')}")
                print(f"角色: {proj.get('role', 'N/A')}")
                print(f"时间: {proj.get('time', 'N/A')}")
                print(f"描述: {proj.get('description', 'N/A')[:100]}...")
                print(f"技术栈: {proj.get('tech_stack', 'N/A')}")
                print(f"个人贡献: {proj.get('contribution', 'N/A')[:100] if proj.get('contribution') else 'N/A'}...")
                print(f"项目成果: {proj.get('results', 'N/A')[:100] if proj.get('results') else 'N/A'}...")
                
                # 打印所有字段
                print(f"\n所有字段: {list(proj.keys())}")
            
            # 检查向量索引中的项目内容
            print("\n" + "=" * 80)
            print("向量索引中的项目块内容:")
            print("=" * 80)
            
            try:
                # 获取所有索引块
                results = vector_index_manager.resume_index.collection.get(
                    where={"resume_id": {"$eq": resume.id}},
                    include=["metadatas", "documents"]
                )
                
                if results and results.get("ids"):
                    for i, (doc_id, metadata, content) in enumerate(zip(
                        results["ids"], results["metadatas"], results["documents"]
                    ), 1):
                        if "project" in metadata.get("chunk_type", ""):
                            print(f"\n--- 索引块 {i} ---")
                            print(f"ID: {doc_id}")
                            print(f"类型: {metadata.get('chunk_type')}")
                            print(f"项目名: {metadata.get('project_name', 'N/A')}")
                            print(f"内容长度: {len(content)} 字符")
                            print(f"内容:\n{content}")
            except Exception as e:
                print(f"获取索引失败: {e}")


if __name__ == "__main__":
    asyncio.run(check_project_data())
