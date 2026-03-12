"""
简历API路由
"""
import os
import uuid
import shutil
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.database import get_db, Resume
from app.services.resume_parser import resume_parser
from app.core.config import settings

router = APIRouter(prefix="/api/v1/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    上传简历文件
    
    - 支持 .docx 格式
    - 自动解析简历内容
    - 保存到数据库
    """
    # 检查文件类型
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="只支持 .docx 格式的简历文件")
    
    # 检查文件大小
    file_size = 0
    content = await file.read()
    file_size = len(content)
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB")
    
    # 重置文件指针
    await file.seek(0)
    
    try:
        # 生成唯一ID
        resume_id = str(uuid.uuid4())
        
        # 确保上传目录存在
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(settings.UPLOAD_DIR, f"{resume_id}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 解析简历
        parsed_data = resume_parser.parse_docx(file_path)
        
        # 保存到数据库
        resume = Resume(
            id=resume_id,
            user_id="test_user",  # TODO: 从认证获取
            file_name=file.filename,
            file_path=file_path,
            parsed_data=parsed_data.model_dump(),
            is_active=True
        )
        
        # 将其他简历设为非活跃
        await db.execute(
            update(Resume)
            .where(Resume.user_id == "test_user")
            .where(Resume.is_active == True)
            .values(is_active=False)
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        return {
            "id": resume.id,
            "file_name": resume.file_name,
            "parsed_data": resume.parsed_data,
            "message": "简历上传成功"
        }
        
    except Exception as e:
        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"简历处理失败: {str(e)}")


@router.get("/list")
async def list_resumes(
    db: AsyncSession = Depends(get_db)
):
    """获取简历列表"""
    result = await db.execute(
        select(Resume).where(Resume.user_id == "test_user").order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "file_name": r.file_name,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat(),
            "parsed_data": {
                "name": r.parsed_data.get("name", ""),
                "education": r.parsed_data.get("education", []),
                "experience": r.parsed_data.get("experience", [])
            }
        }
        for r in resumes
    ]


@router.get("/current")
async def get_current_resume(
    db: AsyncSession = Depends(get_db)
):
    """获取当前使用的简历"""
    result = await db.execute(
        select(Resume).where(Resume.user_id == "test_user").where(Resume.is_active == True)
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="没有激活的简历")
    
    return {
        "id": resume.id,
        "file_name": resume.file_name,
        "parsed_data": resume.parsed_data
    }


@router.post("/{resume_id}/activate")
async def activate_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """激活指定简历"""
    # 查找简历
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id).where(Resume.user_id == "test_user")
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    
    # 将所有简历设为非活跃
    await db.execute(
        update(Resume)
        .where(Resume.user_id == "test_user")
        .where(Resume.is_active == True)
        .values(is_active=False)
    )
    
    # 激活指定简历
    resume.is_active = True
    await db.commit()
    
    return {"message": "简历已激活"}


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除简历"""
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id).where(Resume.user_id == "test_user")
    )
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    
    # 删除文件
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)
    
    # 删除数据库记录
    await db.delete(resume)
    await db.commit()
    
    return {"message": "简历已删除"}
