"""
聊天API路由 - SSE流式输出
"""
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db, Session, Message
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
    session_id = request.get("session_id") or str(uuid.uuid4())
    message = request.get("message", "")
    resume_data = request.get("resume_data", {})
    job_info = request.get("job_info", {})
    history = request.get("history", [])
    
    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    try:
        agent = InterviewAgent()
        result = await agent.chat(
            session_id=session_id,
            user_id="test_user",
            message=message,
            resume_data=resume_data,
            job_info=job_info,
            history=history
        )
        
        return {
            "session_id": session_id,
            "response": result.get("response"),
            "thinking_process": result.get("thinking_process"),
            "current_phase": result.get("current_phase")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
