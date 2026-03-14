"""
为数据库中现有简历建立向量索引
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, Resume
from app.services.vector_index import vector_index_manager


async def index_existing_resumes():
    """为所有现有简历建立向量索引"""
    async with async_session_maker() as db:
        # 获取所有简历
        result = await db.execute(select(Resume))
        resumes = result.scalars().all()

        print(f"找到 {len(resumes)} 份简历")

        for resume in resumes:
            print(f"\n处理简历: {resume.id} - {resume.file_name}")

            if not resume.parsed_data:
                print(f"  ⚠️ 简历没有解析数据，跳过")
                continue

            try:
                # 准备简历数据
                resume_data = {
                    "id": resume.id,
                    **resume.parsed_data
                }

                # 建立向量索引
                chunk_ids = vector_index_manager.index_resume(resume.id, resume_data)

                # 更新数据库记录
                resume.embedding_ids = chunk_ids
                await db.commit()

                print(f"  ✓ 成功创建 {len(chunk_ids)} 个索引块")

            except Exception as e:
                print(f"  ✗ 索引失败: {e}")
                await db.rollback()

        print("\n" + "=" * 50)
        print("简历索引完成!")

        # 显示统计
        stats = vector_index_manager.get_stats()
        print(f"简历索引块总数: {stats['resume_chunks']}")


if __name__ == "__main__":
    asyncio.run(index_existing_resumes())
