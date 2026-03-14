"""
调试监控数据中的简历信息
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.database import async_session_maker, ChatMonitor


async def debug_monitor():
    """查看最新的监控数据"""
    print("=" * 80)
    print("调试监控数据")
    print("=" * 80)
    
    async with async_session_maker() as db:
        # 获取最新的监控数据
        result = await db.execute(
            select(ChatMonitor).order_by(ChatMonitor.created_at.desc()).limit(1)
        )
        monitor = result.scalar_one_or_none()
        
        if not monitor:
            print("没有找到监控数据")
            return
        
        print(f"\n监控ID: {monitor.id}")
        print(f"会话ID: {monitor.session_id}")
        print(f"轮次: {monitor.round_number}")
        print(f"创建时间: {monitor.created_at}")
        
        print("\n" + "=" * 80)
        print("输入数据 (input_data):")
        print("=" * 80)
        input_data = monitor.input_data or {}
        print(json.dumps(input_data, ensure_ascii=False, indent=2))
        
        print("\n" + "=" * 80)
        print("简历数据 (resume_data):")
        print("=" * 80)
        resume_data = input_data.get('resume_data', {})
        print(f"简历ID: {resume_data.get('id', '未提供')}")
        print(f"姓名: {resume_data.get('name', '未提供')}")
        print(f"职位: {resume_data.get('title', '未提供')}")
        print(f"教育经历: {len(resume_data.get('education', []))} 段")
        print(f"工作经历: {len(resume_data.get('experience', []))} 段")
        print(f"项目经验: {len(resume_data.get('projects', []))} 个")
        print(f"技能: {len(resume_data.get('skills', []))} 项")
        
        print("\n" + "=" * 80)
        print("提示词数据 (prompt_data):")
        print("=" * 80)
        prompt_data = monitor.prompt_data or {}
        system_prompt = prompt_data.get('system_prompt', '')
        print(f"系统提示词长度: {len(system_prompt)} 字符")
        print(f"\n系统提示词前500字符:\n{system_prompt[:500]}...")


if __name__ == "__main__":
    asyncio.run(debug_monitor())
