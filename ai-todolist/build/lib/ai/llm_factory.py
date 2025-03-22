from typing import Optional
from .llm_config import LLMConfigManager
from .llm_providers.base_provider import BaseLLMProvider
from .llm_providers.deepseek import DeepseekProvider
from .llm_providers.volcanoark import VolcanoArkProvider
# from .llm_providers.openai_provider import OpenAIProvider
import os

class LLMFactory:
    """LLM提供商工厂类"""

    @staticmethod
    def setup_global_proxy(config_file: str = "config.ini") -> bool:
        """设置全局代理环境变量"""
        config = LLMConfigManager(config_file)
        proxy_host, proxy_port = config.get_proxy()
        
        # 如果配置了代理，设置环境变量
        if proxy_host and proxy_port:
            proxy_url = f"{proxy_host}:{proxy_port}"
            os.environ["http_proxy"] = proxy_url
            os.environ["https_proxy"] = proxy_url
            print(f"已设置全局代理: {proxy_url}")
            return True
        else:
            # 清除可能存在的代理设置
            if "http_proxy" in os.environ:
                del os.environ["http_proxy"]
            if "https_proxy" in os.environ:
                del os.environ["https_proxy"]
            print("未配置全局代理")
            return False
    
    @staticmethod
    def create_provider(config_file: str = "config.ini") -> Optional[BaseLLMProvider]:
        """根据配置文件创建适当的LLM提供商实例"""
        LLMFactory.setup_global_proxy(config_file)
        config = LLMConfigManager(config_file)
        provider_name = config.get_provider_name()
        api_key = config.get_api_key()
        
        if not api_key:
            print(f"错误: {provider_name.upper()}_API_KEY 环境变量未设置")
            return None
                
        if provider_name.lower() == "deepseek":
            return DeepseekProvider(
                api_key=api_key,
                model_name=config.get_model_name(),
                endpoint=config.get_endpoint(),
                timeout=config.get_timeout()
            )
        elif provider_name.lower() == "volcanoark":
            return VolcanoArkProvider(
                api_key=api_key,
                model_name=config.get_model_name(),
                endpoint=config.get_endpoint(),
                timeout=config.get_timeout()
            )
        elif provider_name.lower() == "openai":
            return OpenAIProvider(
                api_key=api_key,
                model_name=config.get_model_name(),
                endpoint=config.get_endpoint(),
                timeout=config.get_timeout()
            )
        else:
            print(f"不支持的LLM提供商: {provider_name}")
            return None