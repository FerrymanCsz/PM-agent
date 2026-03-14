"""
检查工作经历索引和检索
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_index import vector_index_manager


def check_experience_index():
    """检查工作经历索引"""
    print("=" * 80)
    print("检查工作经历索引")
    print("=" * 80)
    
    resume_id = "9e207090-93b9-41e2-957e-4ee880b5d5d1"
    
    # 获取所有索引块
    results = vector_index_manager.resume_index.collection.get(
        where={"resume_id": {"$eq": resume_id}},
        include=["metadatas", "documents"]
    )
    
    if results and results.get("ids"):
        print(f"\n总索引块数: {len(results['ids'])}")
        
        for i, (doc_id, metadata, content) in enumerate(zip(
            results["ids"], results["metadatas"], results["documents"]
        ), 1):
            chunk_type = metadata.get("chunk_type", "")
            print(f"\n--- 索引块 {i} ({chunk_type}) ---")
            print(f"ID: {doc_id}")
            print(f"类型: {chunk_type}")
            print(f"内容长度: {len(content)} 字符")
            
            # 只显示前300字符
            if len(content) > 300:
                print(f"内容:\n{content[:300]}...")
            else:
                print(f"内容:\n{content}")
    
    # 测试检索工作经历相关内容
    print("\n" + "=" * 80)
    print("测试检索工作经历相关内容")
    print("=" * 80)
    
    test_queries = [
        "你在华中时讯负责什么工作",
        "你的工作经历是什么",
        "你在公司做了什么",
        "聊聊你的工作经历"
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        print("-" * 40)
        
        try:
            results = vector_index_manager.search_resume(
                query=query,
                resume_id=resume_id,
                question_type="behavioral",
                top_k=3
            )
            
            print(f"检索到 {len(results)} 条结果:")
            for j, r in enumerate(results, 1):
                print(f"\n  结果 {j}:")
                print(f"    类型: {r['type']}")
                print(f"    相似度: {r['score']:.3f}")
                print(f"    内容: {r['content'][:150]}...")
        except Exception as e:
            print(f"  检索失败: {e}")


if __name__ == "__main__":
    check_experience_index()
