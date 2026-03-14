"""
清理测试数据
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_index import vector_index_manager


def cleanup_test_data():
    """清理测试数据"""
    print("=" * 60)
    print("清理测试数据")
    print("=" * 60)

    # 删除测试简历索引
    test_resume_id = "test_resume_001"
    print(f"\n删除测试简历索引: {test_resume_id}")
    try:
        result = vector_index_manager.delete_resume_index(test_resume_id)
        if result:
            print("✓ 测试简历索引已删除")
        else:
            print("⚠ 未找到测试简历索引或删除失败")
    except Exception as e:
        print(f"✗ 删除失败: {e}")

    # 删除测试知识库索引
    test_knowledge_id = "test_knowledge_001"
    print(f"\n删除测试知识库索引: {test_knowledge_id}")
    try:
        result = vector_index_manager.delete_knowledge_index(test_knowledge_id)
        if result:
            print("✓ 测试知识库索引已删除")
        else:
            print("⚠ 未找到测试知识库索引或删除失败")
    except Exception as e:
        print(f"✗ 删除失败: {e}")

    # 显示清理后的统计
    print("\n" + "=" * 60)
    print("清理后的索引统计")
    print("=" * 60)
    stats = vector_index_manager.get_stats()
    print(f"\n简历索引块总数: {stats['resume_chunks']}")
    print(f"知识库索引块总数: {stats['knowledge_chunks']}")

    print("\n" + "=" * 60)
    print("清理完成!")
    print("=" * 60)


if __name__ == "__main__":
    cleanup_test_data()
