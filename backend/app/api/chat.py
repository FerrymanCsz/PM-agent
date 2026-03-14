"""
聊天API路由 - SSE流式输出
"""
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, Session, Message, ChatMonitor
from app.services.interview_agent import InterviewAgent
from app.services.llm_factory import llm_factory

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


async def generate_stream_response(
    session_id: str,
    message: str,
    resume_data: dict,
    job_info: dict,
    history: list,
    llm_config=None
) -> AsyncGenerator[str, None]:
    """
    生成流式响应
    
    返回SSE格式的事件流
    """
    try:
        # 创建Agent实例
        agent = InterviewAgent(llm_config=llm_config)
        
        # 发送开始事件
        yield f"event: start\ndata: {json.dumps({'session_id': session_id}, ensure_ascii=False)}\n\n"
        
        # 执行Agent工作流
        result = await agent.chat(
            session_id=session_id,
            user_id="test_user",  # TODO: 从认证获取
            message=message,
            resume_data=resume_data,
            job_info=job_info,
            history=history
        )
        
        # 发送思考过程
        thinking_process = result.get("thinking_process", [])
        for step in thinking_process:
            yield f"event: thinking\ndata: {json.dumps(step, ensure_ascii=False)}\n\n"
        
        # 发送回答内容（模拟流式，实际可以逐字发送）
        response = result.get("response", "")
        
        # 模拟流式输出
        chunk_size = 10  # 每10个字符发送一次
        for i in range(0, len(response), chunk_size):
            chunk = response[i:i+chunk_size]
            yield f"event: message\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        
        # 发送完成事件
        yield f"event: complete\ndata: {json.dumps({'phase': result.get('current_phase', 'general')}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        # 发送错误事件
        yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    流式聊天接口
    
    Request Body:
    {
        "session_id": "会话ID（可选，不传则新建）",
        "message": "面试官的问题",
        "resume_data": {},  // 简历数据
        "job_info": {},     // 岗位信息
        "llm_config_id": "LLM配置ID（可选）"
    }
    
    Returns: SSE流
    """
    session_id = request.get("session_id") or str(uuid.uuid4())
    message = request.get("message", "")
    resume_data = request.get("resume_data", {})
    job_info = request.get("job_info", {})
    history = request.get("history", [])
    
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    # TODO: 获取用户的LLM配置
    llm_config = None
    
    return StreamingResponse(
        generate_stream_response(
            session_id=session_id,
            message=message,
            resume_data=resume_data,
            job_info=job_info,
            history=history,
            llm_config=llm_config
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/monitor/{session_id}")
async def get_chat_monitor(
    session_id: str,
    round_number: int = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取聊天监控数据
    
    Args:
        session_id: 会话ID
        round_number: 轮次（可选，不传则返回所有轮次）
    """
    from sqlalchemy import select
    
    try:
        if round_number:
            # 获取指定轮次
            result = await db.execute(
                select(ChatMonitor).where(
                    ChatMonitor.session_id == session_id,
                    ChatMonitor.round_number == round_number
                )
            )
            monitor = result.scalar_one_or_none()
            
            if not monitor:
                raise HTTPException(status_code=404, detail="监控数据不存在")
            
            return {
                "id": monitor.id,
                "session_id": monitor.session_id,
                "round_number": monitor.round_number,
                "input": monitor.input_data,
                "prompt": monitor.prompt_data,
                "output": monitor.output_data,
                "stats": monitor.stats,
                "created_at": monitor.created_at.isoformat() if monitor.created_at else None
            }
        else:
            # 获取所有轮次
            result = await db.execute(
                select(ChatMonitor).where(
                    ChatMonitor.session_id == session_id
                ).order_by(ChatMonitor.round_number)
            )
            monitors = result.scalars().all()
            
            return [
                {
                    "id": m.id,
                    "session_id": m.session_id,
                    "round_number": m.round_number,
                    "input": m.input_data,
                    "prompt": m.prompt_data,
                    "output": m.output_data,
                    "stats": m.stats,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in monitors
            ]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def send_message(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    非流式聊天接口（用于测试）
    
    Request Body:
    {
        "session_id": "会话ID",
        "message": "面试官的问题",
        "resume_data": {},
        "job_info": {}
    }
    """
    import logging
    logger = logging.getLogger(__name__)
    
    session_id = request.get("session_id") or str(uuid.uuid4())
    message = request.get("message", "")
    resume_data = request.get("resume_data", {})
    job_info = request.get("job_info", {})
    history = request.get("history", [])
    
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    try:
        # 检查或创建会话
        from app.models.database import Session as SessionModel, Message as MessageModel
        from sqlalchemy import select
        
        result = await db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()
        
        if not session:
            # 创建新会话
            session = SessionModel(
                id=session_id,
                user_id="test_user",
                title=message[:20] + "..." if len(message) > 20 else message,
                job_info=job_info
            )
            db.add(session)
            await db.flush()
        
        # 保存用户消息
        user_message = MessageModel(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=message,
            meta_data={}
        )
        db.add(user_message)
        await db.flush()
        
        # 调用Agent生成回复
        agent = InterviewAgent()
        result = await agent.chat(
            session_id=session_id,
            user_id="test_user",
            message=message,
            resume_data=resume_data,
            job_info=job_info,
            history=history
        )
        
        # 保存AI回复
        ai_message_id = str(uuid.uuid4())
        monitor_data = result.get("monitor_data", {})
        output_data = monitor_data.get("output", {})
        ai_message = MessageModel(
            id=ai_message_id,
            session_id=session_id,
            role="assistant",
            content=result.get("response", ""),
            meta_data={
                "thinking_process": result.get("thinking_process", []),
                "current_phase": result.get("current_phase", "general"),
                "summary": output_data.get("summary", ""),  # 保存对话摘要
                "question": output_data.get("question", message)  # 保存问题
            }
        )
        db.add(ai_message)
        await db.flush()
        
        # 保存监控数据
        monitor_data = result.get("monitor_data", {})
        if monitor_data:
            # 获取当前轮次
            result_count = await db.execute(
                select(Message).where(Message.session_id == session_id)
            )
            round_number = len(result_count.scalars().all()) // 2  # 每轮包含用户和AI两条消息
            
            chat_monitor = ChatMonitor(
                id=str(uuid.uuid4()),
                session_id=session_id,
                message_id=ai_message_id,
                round_number=round_number,
                input_data=monitor_data.get("input", {}),
                prompt_data=monitor_data.get("prompt", {}),
                output_data=monitor_data.get("output", {}),
                stats=monitor_data.get("stats", {})
            )
            db.add(chat_monitor)
        
        await db.commit()
        
        return {
            "session_id": session_id,
            "response": result.get("response"),
            "thinking_process": result.get("thinking_process"),
            "current_phase": result.get("current_phase"),
            "summary": result.get("summary", "")  # 返回对话摘要
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"发送消息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db)
):
    """
    获取会话列表
    
    Returns:
        会话列表，按时间倒序排列
    """
    from sqlalchemy import select, func
    from app.models.database import Session as SessionModel, Message as MessageModel
    
    try:
        # 获取会话列表及最新消息时间
        result = await db.execute(
            select(
                SessionModel,
                func.count(MessageModel.id).label("message_count")
            )
            .outerjoin(MessageModel, SessionModel.id == MessageModel.session_id)
            .where(SessionModel.user_id == "test_user")
            .group_by(SessionModel.id)
            .order_by(SessionModel.updated_at.desc())
        )
        
        sessions = []
        for row in result.all():
            session = row[0]
            message_count = row[1]
            
            sessions.append({
                "id": session.id,
                "title": session.title or "新面试",
                "status": session.status,
                "job_info": session.job_info or {},
                "message_count": message_count,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            })
        
        return sessions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定会话的消息历史
    
    Args:
        session_id: 会话ID
        
    Returns:
        会话信息和消息列表
    """
    from sqlalchemy import select
    from app.models.database import Session as SessionModel, Message as MessageModel
    
    try:
        # 获取会话信息
        result = await db.execute(
            select(SessionModel).where(
                SessionModel.id == session_id,
                SessionModel.user_id == "test_user"
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        # 获取消息列表
        result = await db.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at)
        )
        messages = result.scalars().all()
        
        return {
            "session": {
                "id": session.id,
                "title": session.title or "新面试",
                "status": session.status,
                "job_info": session.job_info or {},
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None
            },
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "meta_data": m.meta_data or {},
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    删除会话及其所有消息
    
    Args:
        session_id: 会话ID
    """
    from sqlalchemy import select
    from app.models.database import Session as SessionModel
    
    try:
        result = await db.execute(
            select(SessionModel).where(
                SessionModel.id == session_id,
                SessionModel.user_id == "test_user"
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        await db.delete(session)
        await db.commit()
        
        return {"message": "会话已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/sessions/{session_id}/title")
async def update_session_title(
    session_id: str,
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    更新会话标题
    
    Args:
        session_id: 会话ID
        request: { "title": "新标题" }
    """
    from sqlalchemy import select
    from app.models.database import Session as SessionModel
    
    try:
        result = await db.execute(
            select(SessionModel).where(
                SessionModel.id == session_id,
                SessionModel.user_id == "test_user"
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        title = request.get("title", "").strip()
        if title:
            session.title = title
            await db.commit()
        
        return {"message": "标题已更新", "title": session.title}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
