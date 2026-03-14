"""
调试简历加载问题
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, Resume
from app.services.vector_index import vector_index_manager


async def debug_resume():
    """调试简历数据"""
    print("=" * 70)
    print("调试简历加载")
    print("=" * 70)
    
    async with async_session_maker() as db:
        # 获取激活的简历
        result = await db.execute(
            select(Resume).where(Resume.is_active == True)
        )
        resumes = result.scalars().all()
        
        print(f"\n激活的简历数量: {len(resumes)}")
        
        for resume in resumes:
            print(f"\n简历ID: {resume.id}")
            print(f"文件名: {resume.file_name}")
            print(f"是否激活: {resume.is_active}")
            
            if resume.parsed_data:
                print(f"\n解析数据键: {list(resume.parsed_data.keys())}")
                
                # 检查关键字段
                name = resume.parsed_data.get('name', 'N/A')
                education = resume.parsed_data.get('education', [])
                experience = resume.parsed_data.get('experience', [])
                projects = resume.parsed_data.get('projects', [])
                skills = resume.parsed_data.get('skills', [])
                
                print(f"姓名: {name}")
                print(f"教育经历: {len(education)} 段")
                print(f"工作经历: {len(experience)} 段")
                print(f"项目经验: {len(projects)} 个")
                print(f"技能: {len(skills)} 项")
                
                # 测试向量检索
                print(f"\n测试向量检索...")
                try:
                    summary = vector_index_manager.resume_index.get_resume_summary(resume.id)
                    print(f"向量索引摘要:")
                    print(f"  基础信息: {summary['basic_info']}")
                    print(f"  教育数量: {summary['education_count']}")
                    print(f"  工作经历: {summary['experience_count']}")
                    print(f"  项目数量: {summary['project_count']}")
                    print(f"  技能数量: {len(summary['skills'])}")
                except Exception as e:
                    print(f"  获取摘要失败: {e}")
                
                # 测试提示词生成
                print(f"\n测试提示词生成...")
                try:
                    context = vector_index_manager.get_resume_prompt_context(
                        resume_id=resume.id,
                        query="请介绍一下你自己",
                        question_type="self_intro",
                        max_length=1000
                    )
                    print(f"生成的上下文长度: {len(context)} 字符")
                    print(f"前200字符:\n{context[:200]}...")
                except Exception as e:
                    print(f"  生成失败: {e}")
            else:
                print("警告: 简历没有解析数据！")


if __name__ == "__main__":
    asyncio.run(debug_resume())
