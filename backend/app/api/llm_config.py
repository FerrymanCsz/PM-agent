"""
LLM配置API路由 - 模型自动适配版
用户只需配置：名称、Base URL、API Key、模型名称
其他参数根据模型自动匹配
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.database import get_db, LLMConfig
from app.services.llm_factory import llm_factory
from app.services.model_configs import get_model_config, get_preset_models, validate_temperature

router = APIRouter(prefix="/api/v1/llm-configs", tags=["llm-configs"])


@router.get("/preset-models")
async def get_preset_models_list():
    """获取预设模型列表"""
    return {
        "models": get_preset_models()
    }


@router.get("/list")
async def list_llm_configs(
    db: AsyncSession = Depends(get_db)
):
    """获取用户的LLM配置列表"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.user_id == "test_user").where(LLMConfig.is_active == True)
    )
    configs = result.scalars().all()
    
    return {
        "configs": [
            {
                "id": c.id,
                "name": c.name,
                "model": c.model,
                "base_url": c.base_url,
                "api_key": f"{c.api_key[:8]}****" if len(c.api_key) > 8 else "****",
                "is_default": c.is_default,
                "is_active": c.is_active
            }
            for c in configs
        ]
    }


@router.post("/create")
async def create_llm_config(
    config_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """创建LLM配置 - 根据模型名称自动匹配参数"""
    model_name = config_data.get("model", "kimi-k2.5")
    
    # 获取模型自动配置
    model_config = get_model_config(model_name)
    
    # 创建新配置
    config = LLMConfig(
        id=str(uuid.uuid4()),
        user_id="test_user",
        name=config_data.get("name", "未命名配置"),
        provider=model_config.provider,
        base_url=config_data.get("base_url", "https://api.moonshot.cn/v1"),
        api_key=config_data.get("api_key", ""),
        model=model_config.model,
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens,
        timeout=model_config.timeout,
        is_default=False,
        is_active=True
    )
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return {
        "id": config.id,
        "name": config.name,
        "model": config.model,
        "provider": config.provider,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "message": "配置创建成功"
    }


@router.put("/{config_id}")
async def update_llm_config(
    config_id: str,
    config_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """更新LLM配置 - 如果修改了模型，自动更新相关参数"""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.id == config_id).where(LLMConfig.user_id == "test_user")
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    # 更新名称
    if config_data.get("name"):
        config.name = config_data["name"]
    
    # 更新 Base URL
    if config_data.get("base_url"):
        config.base_url = config_data["base_url"]
    
    # 更新 API Key
    if config_data.get("api_key"):
        config.api_key = config_data["api_key"]
    
    # 如果修改了模型，自动更新相关参数
    if config_data.get("model") and config_data["model"] != config.model:
        model_name = config_data["model"]
        model_config = get_model_config(model_name)
        
        config.model = model_config.model
        config.provider = model_config.provider
        config.temperature = model_config.temperature
        config.max_tokens = model_config.max_tokens
        config.timeout = model_config.timeout
    
    await db.commit()
    await db.refresh(config)
    
    return {
        "id": config.id,
        "name": config.name,
        "model": config.model,
        "provider": config.provider,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "message": "配置更新成功"
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
            "model": config.model,
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
