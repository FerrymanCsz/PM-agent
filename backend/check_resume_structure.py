"""
检查简历数据结构
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, Resume


async def check_resume():
    """检查简历数据结构"""
    print("=" * 70)
    print("检查简历数据结构")
    print("=" * 70)
    
    async with async_session_maker() as db:
        result = await db.execute(select(Resume))
        resumes = result.scalars().all()
        
        for resume in resumes:
            print(f"\n简历: {resume.file_name}")
            print(f"\n完整数据结构:")
            print(json.dumps(resume.parsed_data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(check_resume())
