"""
LLM工厂类 - 支持多提供商动态切换
"""
from typing import Dict, Type, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from app.models.database import LLMConfig


class LLMFactory:
    """LLM工厂类 - 支持多提供商动态切换"""
    
    _providers: Dict[str, Type] = {
        "openai": ChatOpenAI,
        "anthropic": ChatAnthropic,
        "deepseek": ChatOpenAI,  # DeepSeek兼容OpenAI接口
        "openrouter": ChatOpenAI,  # OpenRouter兼容OpenAI接口
        "custom": ChatOpenAI,  # 自定义OpenAI兼容接口
    }
    
    @classmethod
    def create_llm(cls, config: LLMConfig) -> BaseChatModel:
        """
        根据配置创建LLM实例
        
        Args:
            config: LLM配置对象
            
        Returns:
            BaseChatModel: LangChain聊天模型实例
        """
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"不支持的提供商: {config.provider}")
        
        # 检测是否为 Kimi 模型（Kimi 模型对 temperature 有特殊限制）
        # 同时检测 moonshot，因为 kimi 模型通常使用 moonshot API
        model_lower = config.model.lower()
        is_kimi = "kimi" in model_lower or "moonshot" in model_lower
        
        # 调试日志
        print(f"[DEBUG] Creating LLM with model={config.model}, is_kimi={is_kimi}")
        
        init_params = {
            "model": config.model,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
        }
        
        # 对于 Kimi/Moonshot 模型，必须显式设置 temperature=1（使用整数）
        # 对于其他模型，根据配置设置 temperature
        if is_kimi:
            init_params["temperature"] = 1  # 使用整数 1 而不是 1.0
            print(f"[DEBUG] Kimi/Moonshot model detected, setting temperature=1")
        else:
            # 处理 temperature - 可能是 JSON 对象
            raw_temp = config.temperature
            if isinstance(raw_temp, (list, dict)):
                if isinstance(raw_temp, list) and len(raw_temp) > 0:
                    raw_temp = raw_temp[0]
                elif isinstance(raw_temp, dict) and 'value' in raw_temp:
                    raw_temp = raw_temp['value']
                else:
                    raw_temp = 0.7
            
            try:
                temp = float(raw_temp) if raw_temp is not None else 0.7
            except (TypeError, ValueError):
                temp = 0.7
            
            init_params["temperature"] = temp
            print(f"[DEBUG] Using temperature={temp}")
        
        # 不同提供商的参数处理
        if config.provider in ["openai", "deepseek", "openrouter", "custom"]:
            init_params["base_url"] = config.base_url
            init_params["api_key"] = config.api_key
        elif config.provider == "anthropic":
            init_params["anthropic_api_url"] = config.base_url
            init_params["anthropic_api_key"] = config.api_key
        
        print(f"[DEBUG] Final init_params: {init_params}")
        return provider_class(**init_params)
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type):
        """
        注册新的提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def get_supported_providers(cls) -> list:
        """获取支持的提供商列表"""
        return list(cls._providers.keys())


# 全局LLM工厂实例
llm_factory = LLMFactory()
