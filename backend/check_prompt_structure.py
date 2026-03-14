"""
检查当前 Prompt 架构
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.interview_agent import InterviewAgent, InterviewState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage


def check_prompt_structure():
    """检查 Prompt 结构"""
    print("=" * 80)
    print("检查 Prompt 架构")
    print("=" * 80)
    
    # 创建 Agent
    agent = InterviewAgent()
    
    # 模拟状态
    state = {
        "messages": [
            HumanMessage(content="你好，请介绍一下自己")
        ],
        "session_id": "test_session",
        "user_id": "test_user",
        "current_phase": "self_intro",
        "resume_data": {
            "id": "test_resume_001",
            "name": "陈圣哲",
            "title": "产品经理",
            "education": [{"school": "新南威尔士大学", "major": "商业分析"}],
            "experience": [{"company": "华中时讯", "position": "产品经理"}],
            "projects": [{"name": "AI智能体项目"}],
            "skills": ["产品策划", "数据分析"]
        },
        "job_info": {
            "company": "字节跳动",
            "position": "产品经理",
            "department": "抖音",
            "requirements": ["3年以上经验", "数据敏感"]
        },
        "knowledge_context": [
            "[项目经验] AI智能体网站项目，基于Trae搭建...",
            "[技能] 全链路产品操盘、需求调研..."
        ],
        "thinking_process": [],
        "llm_config": None,
        "conversation_history": [
            {
                "round_number": 1,
                "question": "你好，请介绍一下自己",
                "full_response": "面试官您好，我是陈圣哲...",
                "summary": "候选人陈圣哲完成自我介绍，提及2年产品经验、AI项目经验"
            },
            {
                "round_number": 2,
                "question": "说说你的项目经验",
                "full_response": "我做过AI智能体和语音房项目...",
                "summary": "候选人介绍AI智能体和语音房项目，强调零研发资源落地和数据成果"
            }
        ]
    }
    
    # 构建系统提示词
    prompt = agent._build_system_prompt(state)
    
    print("\n" + "=" * 80)
    print("生成的 Prompt 结构：")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # 检查各部分是否完整
    print("\n" + "=" * 80)
    print("Prompt 结构检查：")
    print("=" * 80)
    
    checks = [
        ("简历信息", "## 你的简历信息" in prompt),
        ("相关经历（向量检索）", "## 相关经历（从简历中检索到的相关内容）" in prompt),
        ("应聘岗位信息", "## 应聘岗位信息" in prompt),
        ("当前面试阶段", "## 当前面试阶段" in prompt),
        ("回答要求", "## 回答要求" in prompt),
        ("对话历史", "## 对话历史（按时间顺序）" in prompt),
        ("当前问题", "## 当前问题" in prompt),
        ("输出格式要求", "## 输出格式要求" in prompt),
        ("【摘要】标记", "【摘要】" in prompt),
    ]
    
    for name, exists in checks:
        status = "✅" if exists else "❌"
        print(f"{status} {name}")
    
    # 检查对话历史内容
    print("\n" + "=" * 80)
    print("对话历史内容：")
    print("=" * 80)
    conversation_history = agent._build_conversation_history(state, max_rounds=5)
    print(conversation_history)
    
    # 统计 Token
    print("\n" + "=" * 80)
    print("Token 统计：")
    print("=" * 80)
    chinese_chars = len([c for c in prompt if '\u4e00' <= c <= '\u9fff'])
    english_words = len([w for w in prompt.split() if w.isalpha()])
    total_chars = len(prompt)
    estimated_tokens = chinese_chars * 1.5 + english_words * 1.3 + (total_chars - chinese_chars - english_words) * 0.5
    
    print(f"中文字符数: {chinese_chars}")
    print(f"英文单词数: {english_words}")
    print(f"总字符数: {total_chars}")
    print(f"估算 Token 数: ~{int(estimated_tokens)}")


if __name__ == "__main__":
    check_prompt_structure()
