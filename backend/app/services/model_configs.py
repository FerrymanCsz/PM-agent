"""
模型配置管理 - 根据模型名称自动匹配参数
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """模型配置"""
    provider: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int = 60
    description: str = ""


# 预设模型配置
PRESET_MODELS: Dict[str, ModelConfig] = {
    # Moonshot / Kimi
    "kimi-k2.5": ModelConfig(
        provider="openai",
        model="kimi-k2.5",
        temperature=1.0,
        max_tokens=128000,
        description="Kimi K2.5 - 支持128K上下文"
    ),
    "moonshot-v1-8k": ModelConfig(
        provider="openai",
        model="moonshot-v1-8k",
        temperature=0.7,
        max_tokens=8192,
        description="Moonshot 8K"
    ),
    "moonshot-v1-32k": ModelConfig(
        provider="openai",
        model="moonshot-v1-32k",
        temperature=0.7,
        max_tokens=32768,
        description="Moonshot 32K"
    ),
    "moonshot-v1-128k": ModelConfig(
        provider="openai",
        model="moonshot-v1-128k",
        temperature=0.7,
        max_tokens=128000,
        description="Moonshot 128K"
    ),
    
    # OpenAI
    "gpt-4": ModelConfig(
        provider="openai",
        model="gpt-4",
        temperature=0.7,
        max_tokens=8192,
        description="GPT-4"
    ),
    "gpt-4-turbo": ModelConfig(
        provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.7,
        max_tokens=128000,
        description="GPT-4 Turbo"
    ),
    "gpt-3.5-turbo": ModelConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=4096,
        description="GPT-3.5 Turbo"
    ),
    
    # Anthropic / Claude
    "claude-3-opus": ModelConfig(
        provider="anthropic",
        model="claude-3-opus-20240229",
        temperature=0.7,
        max_tokens=200000,
        description="Claude 3 Opus"
    ),
    "claude-3-sonnet": ModelConfig(
        provider="anthropic",
        model="claude-3-sonnet-20240229",
        temperature=0.7,
        max_tokens=200000,
        description="Claude 3 Sonnet"
    ),
    "claude-3-haiku": ModelConfig(
        provider="anthropic",
        model="claude-3-haiku-20240307",
        temperature=0.7,
        max_tokens=200000,
        description="Claude 3 Haiku"
    ),
    
    # DeepSeek
    "deepseek-chat": ModelConfig(
        provider="deepseek",
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=8192,
        description="DeepSeek Chat"
    ),
    "deepseek-coder": ModelConfig(
        provider="deepseek",
        model="deepseek-coder",
        temperature=0.7,
        max_tokens=8192,
        description="DeepSeek Coder"
    ),
    
    # Google / Gemini
    "gemini-pro": ModelConfig(
        provider="openai",  # 通过兼容模式
        model="gemini-pro",
        temperature=0.7,
        max_tokens=32768,
        description="Gemini Pro"
    ),
    "gemini-ultra": ModelConfig(
        provider="openai",
        model="gemini-ultra",
        temperature=0.7,
        max_tokens=1048576,  # 1M
        description="Gemini Ultra"
    ),
}


def get_model_config(model_name: str) -> ModelConfig:
    """
    根据模型名称获取配置
    
    Args:
        model_name: 模型名称
        
    Returns:
        ModelConfig: 模型配置
    """
    # 直接匹配
    if model_name in PRESET_MODELS:
        return PRESET_MODELS[model_name]
    
    # 模糊匹配 - 检查是否包含关键词
    model_lower = model_name.lower()
    
    # Kimi 模型检测
    if "kimi" in model_lower:
        if "k2.5" in model_lower or "k2-5" in model_lower:
            return PRESET_MODELS["kimi-k2.5"]
    
    # Moonshot 模型检测
    if "moonshot" in model_lower:
        if "128k" in model_lower:
            return PRESET_MODELS["moonshot-v1-128k"]
        elif "32k" in model_lower:
            return PRESET_MODELS["moonshot-v1-32k"]
        else:
            return PRESET_MODELS["moonshot-v1-8k"]
    
    # GPT 模型检测
    if "gpt-4" in model_lower:
        if "turbo" in model_lower:
            return PRESET_MODELS["gpt-4-turbo"]
        else:
            return PRESET_MODELS["gpt-4"]
    if "gpt-3.5" in model_lower:
        return PRESET_MODELS["gpt-3.5-turbo"]
    
    # Claude 模型检测
    if "claude" in model_lower:
        if "opus" in model_lower:
            return PRESET_MODELS["claude-3-opus"]
        elif "sonnet" in model_lower:
            return PRESET_MODELS["claude-3-sonnet"]
        elif "haiku" in model_lower:
            return PRESET_MODELS["claude-3-haiku"]
    
    # DeepSeek 模型检测
    if "deepseek" in model_lower:
        if "coder" in model_lower:
            return PRESET_MODELS["deepseek-coder"]
        else:
            return PRESET_MODELS["deepseek-chat"]
    
    # Gemini 模型检测
    if "gemini" in model_lower:
        if "ultra" in model_lower:
            return PRESET_MODELS["gemini-ultra"]
        else:
            return PRESET_MODELS["gemini-pro"]
    
    # 默认配置 - 使用 OpenAI 兼容模式
    return ModelConfig(
        provider="openai",
        model=model_name,
        temperature=1.0,  # 保守设置，避免不支持的温度值
        max_tokens=4096,
        description=f"自定义模型: {model_name}"
    )


def get_preset_models() -> Dict[str, str]:
    """获取预设模型列表（用于前端展示）"""
    return {
        key: config.description 
        for key, config in PRESET_MODELS.items()
    }


def validate_temperature(model_name: str, temperature: float) -> float:
    """
    验证并修正 temperature 值
    
    Args:
        model_name: 模型名称
        temperature: 请求的 temperature
        
    Returns:
        float: 修正后的 temperature
    """
    config = get_model_config(model_name)
    
    # 如果模型要求固定 temperature
    if config.model == "kimi-k2.5":
        return 1.0
    
    # 其他模型根据 provider 限制
    if config.provider == "anthropic":
        return max(0.0, min(1.0, temperature))
    else:
        return max(0.0, min(2.0, temperature))
