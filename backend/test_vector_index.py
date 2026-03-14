"""
向量索引功能测试脚本
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_index import vector_index_manager


# 测试简历数据
test_resume = {
    "id": "test_resume_001",
    "name": "张三",
    "title": "高级软件工程师",
    "summary": "5年Java开发经验，精通微服务架构",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "education": [
        {
            "school": "北京大学",
            "major": "计算机科学",
            "degree": "本科",
            "start_date": "2015-09",
            "end_date": "2019-06",
            "description": "主修课程：数据结构、算法、操作系统"
        }
    ],
    "experience": [
        {
            "company": "阿里巴巴",
            "position": "高级Java工程师",
            "duration": "2021-03 至今",
            "responsibilities": "负责订单系统核心模块开发",
            "achievements": "优化系统性能提升50%，支持日均千万级订单"
        },
        {
            "company": "腾讯",
            "position": "Java工程师",
            "duration": "2019-07 至 2021-02",
            "responsibilities": "参与微信支付后端开发",
            "achievements": "完成支付核心模块重构"
        }
    ],
    "projects": [
        {
            "name": "分布式订单系统",
            "role": "技术负责人",
            "duration": "2022-01 至 2022-12",
            "description": "设计并实现高并发订单处理系统",
            "technologies": ["Java", "Spring Cloud", "MySQL", "Redis", "RocketMQ"],
            "contributions": "架构设计、核心代码开发、性能优化",
            "results": "支持10万QPS，系统可用性99.99%"
        }
    ],
    "skills": [
        "Java", "Spring Boot", "Spring Cloud", "MySQL", "Redis",
        "Kafka", "RocketMQ", "Docker", "Kubernetes", "微服务架构"
    ]
}


# 测试知识库数据
test_knowledge = {
    "id": "test_knowledge_001",
    "title": "Java并发编程指南",
    "category": "technical",
    "content": """
# Java并发编程指南

## 线程基础
Java中的线程是程序执行的最小单位。每个线程都有自己的程序计数器、寄存器和栈。

### 创建线程的方式
1. 继承Thread类
2. 实现Runnable接口
3. 实现Callable接口（可以返回结果）

## 线程池
线程池是管理线程的重要工具，可以有效控制并发线程数量。

### 常用线程池类型
- FixedThreadPool：固定大小线程池
- CachedThreadPool：可缓存线程池
- SingleThreadExecutor：单线程执行器
- ScheduledThreadPool：定时任务线程池

## 锁机制
Java提供了多种锁机制来保证线程安全。

### synchronized关键字
最基本的同步机制，可以修饰方法或代码块。

### ReentrantLock
可重入锁，提供了比synchronized更灵活的功能。

## 并发集合
Java提供了线程安全的集合类：
- ConcurrentHashMap
- CopyOnWriteArrayList
- BlockingQueue
"""
}


def test_resume_index():
    """测试简历索引功能"""
    print("=" * 50)
    print("测试简历索引功能")
    print("=" * 50)

    # 1. 构建索引
    print("\n1. 构建简历索引...")
    try:
        chunk_ids = vector_index_manager.index_resume(
            test_resume["id"],
            test_resume
        )
        print(f"   ✓ 成功创建 {len(chunk_ids)} 个索引块")
        print(f"   块ID: {chunk_ids[:3]}...")  # 只显示前3个
    except Exception as e:
        print(f"   ✗ 索引创建失败: {e}")
        return False

    # 2. 测试搜索
    print("\n2. 测试简历搜索...")
    test_queries = [
        ("请介绍一下你的项目经验", "project_experience"),
        ("你在阿里巴巴做了什么", "behavioral"),
        ("你熟悉哪些技术栈", "technical"),
    ]

    for query, qtype in test_queries:
        print(f"\n   查询: '{query}' (类型: {qtype})")
        try:
            results = vector_index_manager.search_resume(
                query=query,
                resume_id=test_resume["id"],
                question_type=qtype,
                top_k=2
            )
            print(f"   ✓ 找到 {len(results)} 条相关结果")
            for i, r in enumerate(results, 1):
                print(f"     {i}. [{r['type']}] 相似度: {r['score']:.3f}")
                # 只显示前100字符
                content_preview = r['content'][:100].replace('\n', ' ')
                print(f"        {content_preview}...")
        except Exception as e:
            print(f"   ✗ 搜索失败: {e}")

    # 3. 测试获取提示词上下文
    print("\n3. 测试获取提示词上下文...")
    try:
        context = vector_index_manager.get_resume_prompt_context(
            resume_id=test_resume["id"],
            query="介绍一下你的分布式系统经验",
            question_type="technical",
            max_length=1500
        )
        print(f"   ✓ 成功生成上下文 (长度: {len(context)} 字符)")
        print(f"   预览:\n{context[:500]}...")
    except Exception as e:
        print(f"   ✗ 获取上下文失败: {e}")

    return True


def test_knowledge_index():
    """测试知识库索引功能"""
    print("\n" + "=" * 50)
    print("测试知识库索引功能")
    print("=" * 50)

    # 1. 构建索引
    print("\n1. 构建知识库索引...")
    try:
        chunk_ids = vector_index_manager.index_knowledge(
            test_knowledge["id"],
            test_knowledge
        )
        print(f"   ✓ 成功创建 {len(chunk_ids)} 个索引块")
    except Exception as e:
        print(f"   ✗ 索引创建失败: {e}")
        return False

    # 2. 测试搜索
    print("\n2. 测试知识库搜索...")
    test_queries = [
        "Java线程池怎么用",
        "synchronized和ReentrantLock的区别",
        "什么是线程安全",
    ]

    for query in test_queries:
        print(f"\n   查询: '{query}'")
        try:
            results = vector_index_manager.search_knowledge(
                query=query,
                category="technical",
                top_k=2
            )
            print(f"   ✓ 找到 {len(results)} 条相关结果")
            for i, r in enumerate(results, 1):
                print(f"     {i}. [{r['category']}] 相似度: {r['score']:.3f}")
                content_preview = r['content'][:100].replace('\n', ' ')
                print(f"        {content_preview}...")
        except Exception as e:
            print(f"   ✗ 搜索失败: {e}")

    # 3. 测试获取文档结构
    print("\n3. 测试获取文档结构...")
    try:
        structure = vector_index_manager.knowledge_index.get_document_structure(
            test_knowledge["id"]
        )
        print(f"   ✓ 文档包含 {structure['total_chunks']} 个块")
        print(f"   章节: {[s['title'] for s in structure['sections']]}")
    except Exception as e:
        print(f"   ✗ 获取结构失败: {e}")

    return True


def test_stats():
    """测试统计信息"""
    print("\n" + "=" * 50)
    print("索引统计信息")
    print("=" * 50)

    try:
        stats = vector_index_manager.get_stats()
        print(f"\n简历索引块数: {stats['resume_chunks']}")
        print(f"知识库索引块数: {stats['knowledge_chunks']}")
        print("\n✓ 所有测试完成!")
    except Exception as e:
        print(f"\n✗ 获取统计失败: {e}")


def cleanup():
    """清理测试数据"""
    print("\n" + "=" * 50)
    print("清理测试数据")
    print("=" * 50)

    try:
        vector_index_manager.delete_resume_index("test_resume_001")
        vector_index_manager.delete_knowledge_index("test_knowledge_001")
        print("\n✓ 测试数据已清理")
    except Exception as e:
        print(f"\n✗ 清理失败: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("向量索引功能测试")
    print("=" * 60)

    # 运行测试
    resume_ok = test_resume_index()
    knowledge_ok = test_knowledge_index()
    test_stats()

    # 清理（可选）
    # cleanup()

    print("\n" + "=" * 60)
    if resume_ok and knowledge_ok:
        print("✓ 所有测试通过!")
    else:
        print("✗ 部分测试失败")
    print("=" * 60)
