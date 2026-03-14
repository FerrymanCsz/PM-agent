"""
测试优化后的系统功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.interview_agent import InterviewAgent


async def test_chat_flow():
    """测试对话流程"""
    print("=" * 80)
    print("测试优化后的对话流程")
    print("=" * 80)
    
    agent = InterviewAgent()
    
    # 测试数据
    session_id = "test_session_001"
    user_id = "test_user"
    
    resume_data = {
        "id": "9e207090-93b9-41e2-957e-4ee880b5d5d1",
        "name": "陈圣哲",
        "title": "产品经理/代理产品主管",
        "education": [{"school": "新南威尔士大学", "major": "商业分析"}],
        "experience": [{"company": "华中时讯", "position": "产品经理"}],
        "projects": [{"name": "AI智能体项目"}],
        "skills": ["产品策划", "数据分析", "AI产品落地"]
    }
    
    job_info = {
        "company": "字节跳动",
        "position": "产品经理",
        "department": "抖音",
        "requirements": ["3年以上经验", "数据敏感"]
    }
    
    # 第一轮对话：自我介绍
    print("\n" + "=" * 80)
    print("第一轮：自我介绍")
    print("=" * 80)
    
    result1 = await agent.chat(
        session_id=session_id,
        user_id=user_id,
        message="简单介绍一下自己吧",
        resume_data=resume_data,
        job_info=job_info,
        history=[]
    )
    
    print(f"\n问题类型: {result1.get('current_phase')}")
    print(f"执行步骤: {result1.get('executed_steps')}")
    print(f"是否包含summary: {'summary' in result1}")
    print(f"\nAI回答（前200字）:")
    print(result1.get('response', '')[:200] + "...")
    print(f"\n摘要:")
    print(result1.get('summary', '无'))
    
    # 第二轮对话：项目经验
    print("\n" + "=" * 80)
    print("第二轮：项目经验")
    print("=" * 80)
    
    history = [
        {"role": "user", "content": "简单介绍一下自己吧"},
        {"role": "assistant", "content": result1.get('response', ''), "summary": result1.get('summary', '')}
    ]
    
    result2 = await agent.chat(
        session_id=session_id,
        user_id=user_id,
        message="聊聊你做过的AI项目",
        resume_data=resume_data,
        job_info=job_info,
        history=history
    )
    
    print(f"\n问题类型: {result2.get('current_phase')}")
    print(f"执行步骤: {result2.get('executed_steps')}")
    print(f"\nAI回答（前200字）:")
    print(result2.get('response', '')[:200] + "...")
    print(f"\n摘要:")
    print(result2.get('summary', '无'))
    
    # 第三轮对话：工作经历
    print("\n" + "=" * 80)
    print("第三轮：工作经历")
    print("=" * 80)
    
    history.append({"role": "user", "content": "聊聊你做过的AI项目"})
    history.append({"role": "assistant", "content": result2.get('response', ''), "summary": result2.get('summary', '')})
    
    result3 = await agent.chat(
        session_id=session_id,
        user_id=user_id,
        message="你在华中时讯主要负责什么工作？",
        resume_data=resume_data,
        job_info=job_info,
        history=history
    )
    
    print(f"\n问题类型: {result3.get('current_phase')}")
    print(f"执行步骤: {result3.get('executed_steps')}")
    print(f"\nAI回答（前200字）:")
    print(result3.get('response', '')[:200] + "...")
    print(f"\n摘要:")
    print(result3.get('summary', '无'))
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_chat_flow())
