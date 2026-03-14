"""
岗位配置API路由
"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.database import get_db, JobConfig

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/current")
async def get_current_job(
    db: AsyncSession = Depends(get_db)
):
    """获取当前使用的岗位配置"""
    result = await db.execute(
        select(JobConfig).where(JobConfig.user_id == "test_user").where(JobConfig.is_default == True)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        # 如果没有默认配置，返回第一个配置
        result = await db.execute(
            select(JobConfig).where(JobConfig.user_id == "test_user").order_by(JobConfig.created_at.desc())
        )
        job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="没有配置岗位信息")
    
    return {
        "id": job.id,
        "company": job.company,
        "position": job.position,
        "level": job.level,
        "department": job.department,
        "job_description": job.job_description,
        "requirements": job.requirements,
        "skills": job.skills,
        "interview_focus": job.interview_focus
    }


@router.get("/list")
async def list_jobs(
    db: AsyncSession = Depends(get_db)
):
    """获取岗位配置列表"""
    result = await db.execute(
        select(JobConfig).where(JobConfig.user_id == "test_user").order_by(JobConfig.created_at.desc())
    )
    jobs = result.scalars().all()
    
    return [
        {
            "id": j.id,
            "company": j.company,
            "position": j.position,
            "level": j.level,
            "department": j.department,
            "is_default": j.is_default
        }
        for j in jobs
    ]


@router.post("/create")
async def create_job(
    job_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """创建岗位配置"""
    job = JobConfig(
        id=str(uuid.uuid4()),
        user_id="test_user",
        company=job_data.get("company"),
        position=job_data.get("position"),
        level=job_data.get("level"),
        department=job_data.get("department"),
        job_description=job_data.get("job_description"),
        requirements=job_data.get("requirements", []),
        skills=job_data.get("skills", []),
        interview_focus=job_data.get("interview_focus", []),
        is_default=job_data.get("is_default", False)
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    return {
        "id": job.id,
        "message": "岗位配置创建成功"
    }


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    job_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """更新岗位配置"""
    result = await db.execute(
        select(JobConfig).where(JobConfig.id == job_id).where(JobConfig.user_id == "test_user")
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="岗位配置不存在")
    
    # 更新字段
    if "company" in job_data:
        job.company = job_data["company"]
    if "position" in job_data:
        job.position = job_data["position"]
    if "level" in job_data:
        job.level = job_data["level"]
    if "department" in job_data:
        job.department = job_data["department"]
    if "job_description" in job_data:
        job.job_description = job_data["job_description"]
    if "requirements" in job_data:
        job.requirements = job_data["requirements"]
    if "skills" in job_data:
        job.skills = job_data["skills"]
    if "interview_focus" in job_data:
        job.interview_focus = job_data["interview_focus"]
    
    await db.commit()
    await db.refresh(job)
    
    return {
        "id": job.id,
        "message": "岗位配置更新成功"
    }


@router.post("/{job_id}/set-default")
async def set_default_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """设置默认岗位配置"""
    # 取消所有默认配置
    await db.execute(
        update(JobConfig)
        .where(JobConfig.user_id == "test_user")
        .values(is_default=False)
    )
    
    # 设置指定配置为默认
    result = await db.execute(
        select(JobConfig).where(JobConfig.id == job_id).where(JobConfig.user_id == "test_user")
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="岗位配置不存在")
    
    job.is_default = True
    await db.commit()
    
    return {"message": "已设置为默认岗位配置"}


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除岗位配置"""
    result = await db.execute(
        select(JobConfig).where(JobConfig.id == job_id).where(JobConfig.user_id == "test_user")
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="岗位配置不存在")
    
    await db.delete(job)
    await db.commit()
    
    return {"message": "岗位配置已删除"}
