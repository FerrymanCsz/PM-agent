"""
LLM配置API路由
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.database import get_db, LLMConfig
from app.services.llm_factory import llm_factory

router = APIRouter(prefix="/api/v1/llm-configs", tags=["llm-configs"])


@router.get("/list")
async def list_llm_configs(
    db: AsyncSession = Depends(get_db)
):
    """获取用户的LLM配置列表"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.user_id == "test_user").where(LLMConfig.is_active == True)
    )
    configs = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "provider": c.provider,
            "model": c.model,
            "base_url": c.base_url,
            "api_key_masked": f"{c.api_key[:8]}****" if len(c.api_key) > 8 else "****",
            "temperature": c.temperature,
            "max_tokens": c.max_tokens,
            "is_default": c.is_default,
            "is_active": c.is_active
        }
        for c in configs
    ]


@router.post("/create")
async def create_llm_config(
    config_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """创建LLM配置"""
    # 验证提供商
    if config_data.get("provider") not in llm_factory.get_supported_providers():
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的提供商: {config_data.get('provider')}"
        )
    
    # 如果设置为默认，取消其他默认配置
    if config_data.get("is_default"):
        await db.execute(
            update(LLMConfig)
            .where(LLMConfig.user_id == "test_user")
            .values(is_default=False)
        )
    
    # 创建新配置
    config = LLMConfig(
        id=str(uuid.uuid4()),
        user_id="test_user",
        name=config_data.get("name"),
        provider=config_data.get("provider"),
        base_url=config_data.get("base_url"),
        api_key=config_data.get("api_key"),
        model=config_data.get("model"),
        temperature=config_data.get("temperature", 0.7),
        max_tokens=config_data.get("max_tokens", 4096),
        timeout=config_data.get("timeout", 60),
        is_default=config_data.get("is_default", False),
        is_active=True
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return {
        "id": config.id,
        "name": config.name,
        "provider": config.provider,
        "model": config.model,
        "message": "配置创建成功"
    }


@router.post("/{config_id}/test")
async def test_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """测试LLM配置连接"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id).where(LLMConfig.user_id == "test_user")
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    try:
        # 创建LLM实例
        llm = llm_factory.create_llm(config)
        
        # 测试调用
        import time
        start_time = time.time()
        response = llm.invoke("Hello")
        latency = int((time.time() - start_time) * 1000)
        
        return {
            "success": True,
            "latency_ms": latency,
            "message": "连接测试成功"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "连接测试失败"
        }


@router.post("/{config_id}/set-default")
async def set_default_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """设置默认配置"""
    # 取消所有默认配置
    await db.execute(
        update(LLMConfig)
        .where(LLMConfig.user_id == "test_user")
        .values(is_default=False)
    )
    
    # 设置指定配置为默认
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id).where(LLMConfig.user_id == "test_user")
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    config.is_default = True
    await db.commit()
    
    return {"message": "已设置为默认配置"}


@router.delete("/{config_id}")
async def delete_llm_config(
    config_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除LLM配置"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id).where(LLMConfig.user_id == "test_user")
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 软删除
    config.is_active = False
    await db.commit()
    
    return {"message": "配置已删除"}
