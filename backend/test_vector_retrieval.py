"""
向量检索功能测试 - 模拟不同面试场景
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_index import vector_index_manager


# 测试用例：不同类型的问题
test_cases = [
    {
        "name": "自我介绍",
        "query": "请先做一下自我介绍",
        "question_type": "self_intro",
        "expected_types": ["basic_info", "education", "experience"]
    },
    {
        "name": "项目经验",
        "query": "请介绍一下你做过的项目",
        "question_type": "project_experience",
        "expected_types": ["project"]
    },
    {
        "name": "技术问题",
        "query": "你熟悉哪些技术栈和工具？",
        "question_type": "technical",
        "expected_types": ["skills", "project"]
    },
    {
        "name": "工作经历",
        "query": "你在华中时讯主要负责什么工作？",
        "question_type": "behavioral",
        "expected_types": ["experience"]
    },
    {
        "name": "AI项目",
        "query": "说说你做的AI智能体项目",
        "question_type": "project_experience",
        "expected_types": ["project"]
    },
    {
        "name": "社交产品",
        "query": "你在社交产品方面有什么经验？",
        "question_type": "project_experience",
        "expected_types": ["project", "experience"]
    }
]


def test_resume_search(resume_id: str):
    """测试简历向量检索"""
    print("=" * 80)
    print("简历向量检索测试")
    print("=" * 80)
    print(f"\n简历ID: {resume_id}\n")
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"测试 {i}: {test['name']}")
        print(f"{'─' * 80}")
        print(f"问题: {test['query']}")
        print(f"问题类型: {test['question_type']}")
        print(f"期望检索: {', '.join(test['expected_types'])}")
        
        try:
            # 执行检索
            results = vector_index_manager.search_resume(
                query=test['query'],
                resume_id=resume_id,
                question_type=test['question_type'],
                top_k=3
            )
            
            print(f"\n✓ 检索到 {len(results)} 条结果:")
            
            for j, result in enumerate(results, 1):
                match = "✓" if result['type'] in test['expected_types'] else "✗"
                print(f"\n  {match} 结果 {j}:")
                print(f"     类型: {result['type']}")
                print(f"     相似度: {result['score']:.3f}")
                # 显示内容预览
                content = result['content'][:150].replace('\n', ' ')
                print(f"     内容: {content}...")
            
            # 检查是否符合预期
            retrieved_types = [r['type'] for r in results]
            matched = any(t in retrieved_types for t in test['expected_types'])
            
            if matched:
                print(f"\n✅ 符合预期 - 检索到了期望的块类型")
            else:
                print(f"\n⚠️  不符合预期 - 未检索到期望的块类型")
                
        except Exception as e:
            print(f"\n✗ 检索失败: {e}")


def test_prompt_context(resume_id: str):
    """测试提示词上下文生成"""
    print("\n" + "=" * 80)
    print("提示词上下文生成测试")
    print("=" * 80)
    
    test_queries = [
        ("请介绍一下你自己", "self_intro"),
        ("说说你的项目经验", "project_experience"),
        ("你熟悉AI技术吗？", "technical"),
    ]
    
    for query, qtype in test_queries:
        print(f"\n{'─' * 80}")
        print(f"问题: {query} (类型: {qtype})")
        print(f"{'─' * 80}")
        
        try:
            context = vector_index_manager.get_resume_prompt_context(
                resume_id=resume_id,
                query=query,
                question_type=qtype,
                max_length=1500
            )
            
            print(f"\n生成的上下文 (长度: {len(context)} 字符):")
            print(f"{'─' * 40}")
            print(context)
            print(f"{'─' * 40}")
            
        except Exception as e:
            print(f"\n✗ 生成失败: {e}")


def test_stats():
    """显示统计信息"""
    print("\n" + "=" * 80)
    print("索引统计")
    print("=" * 80)
    
    stats = vector_index_manager.get_stats()
    print(f"\n简历索引块总数: {stats['resume_chunks']}")
    print(f"知识库索引块总数: {stats['knowledge_chunks']}")


if __name__ == "__main__":
    # 实际简历ID
    resume_id = "9e207090-93b9-41e2-957e-4ee880b5d5d1"
    
    print("\n" + "=" * 80)
    print("向量检索功能全面测试")
    print("=" * 80)
    
    # 运行测试
    test_resume_search(resume_id)
    test_prompt_context(resume_id)
    test_stats()
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)
