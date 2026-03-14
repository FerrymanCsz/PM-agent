"""
检查工作经历原始数据
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, Resume


async def check_experience_data():
    """检查工作经历原始数据"""
    print("=" * 80)
    print("检查工作经历原始数据")
    print("=" * 80)
    
    async with async_session_maker() as db:
        result = await db.execute(select(Resume))
        resumes = result.scalars().all()
        
        for resume in resumes:
            print(f"\n简历ID: {resume.id}")
            
            experience = resume.parsed_data.get('experience', [])
            print(f"\n工作经历数量: {len(experience)}")
            
            for i, exp in enumerate(experience):
                print(f"\n--- 工作经历 {i+1} ---")
                print(f"所有字段: {list(exp.keys())}")
                print(f"完整数据: {json.dumps(exp, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    asyncio.run(check_experience_data())
