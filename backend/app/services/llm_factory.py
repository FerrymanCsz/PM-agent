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
        
        # 构建初始化参数
        init_params = {
            "model": config.model,
            "temperature": config.temperature if isinstance(config.temperature, (int, float)) else 0.7,
            "max_tokens": config.max_tokens,
            "timeout": config.timeout,
        }
        
        # 不同提供商的参数处理
        if config.provider in ["openai", "deepseek", "openrouter", "custom"]:
            init_params["base_url"] = config.base_url
            init_params["api_key"] = config.api_key
        elif config.provider == "anthropic":
            init_params["anthropic_api_url"] = config.base_url
            init_params["anthropic_api_key"] = config.api_key
        
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
