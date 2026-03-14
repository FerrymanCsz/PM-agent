"""
清空所有面试历史记录脚本
"""
import asyncio
from sqlalchemy import delete
from app.models.database import async_session_maker, Session, Message, ChatMonitor


async def clear_all_history():
    """清空所有面试历史记录"""
    async with async_session_maker() as db:
        try:
            # 先删除 chat_monitors（因为有外键依赖）
            result = await db.execute(delete(ChatMonitor))
            chat_monitor_count = result.rowcount
            print(f"✅ 已删除 {chat_monitor_count} 条聊天监控记录")

            # 删除 messages
            result = await db.execute(delete(Message))
            message_count = result.rowcount
            print(f"✅ 已删除 {message_count} 条消息记录")

            # 删除 sessions
            result = await db.execute(delete(Session))
            session_count = result.rowcount
            print(f"✅ 已删除 {session_count} 条会话记录")

            await db.commit()
            print("\n🎉 所有面试历史记录已清空！")

        except Exception as e:
            await db.rollback()
            print(f"❌ 清空历史记录失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(clear_all_history())
