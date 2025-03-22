from typing import Optional
from .llm_config import LLMConfigManager
from .llm_providers.base_provider import BaseLLMProvider
from .llm_providers.deepseek import DeepseekProvider
from .llm_providers.volcanoark import VolcanoArkProvider
# from .llm_providers.openai_provider import OpenAIProvider
import os

class LLMFactory:
    """LLM提供商工厂类"""

    def __init__(self, config_file=None, config=None):
        """初始化LLM工厂
        
        参数:
            config_file (str, 可选): 配置文件路径
            config (ConfigParser, 可选): 现有配置对象
        """
        self.config_file = config_file
        self.config_object = config
        
        if config_file:
            self._load_config_from_file()
        elif config:
            self.config = config
        else:
            raise ValueError("必须提供config_file或config参数之一")
        
    def _load_config_from_file(self):
        """从文件加载配置"""
        import configparser
        self.config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file, encoding='utf-8')
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 创建默认配置
            self.config = configparser.ConfigParser()
            self.config['llm'] = {
                'provider': 'volcanoark',
                'model_name': 'deepseek-v3-241226',
                'endpoint': 'https://ark.cn-beijing.volces.com/api/v3/chat/completions',
                'timeout': '15',
                'proxy_host': '',
                'proxy_port': '',
            }

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
    
    @staticmethod
    def create_llm(config):
        """根据配置文件创建适当的LLM提供商实例"""
        provider_name = config.get('llm', 'provider', fallback='volcanoark')
        api_key = os.environ.get(f"{provider_name.upper()}_API_KEY", "")
        
        if not api_key:
            print(f"错误: {provider_name.upper()}_API_KEY 环境变量未设置")
            return None
                
        if provider_name == 'volcanoark':
            from .llm_providers.volcanoark import VolcanoArkProvider
            model_name = config.get('llm', 'model_name', fallback='deepseek-v3-241226')
            endpoint = config.get('llm', 'endpoint', fallback='https://ark.cn-beijing.volces.com/api/v3/chat/completions')
            timeout = config.getint('llm', 'timeout', fallback=15)
            return VolcanoArkProvider(
                api_key=api_key,
                model_name=model_name,  # 修正参数名
                endpoint=endpoint,
                timeout=timeout
            )
            
        elif provider_name == 'openai':
            from .llm_providers.openai_provider import OpenAIProvider
            model_name = config.get('llm', 'model_name', fallback='gpt-3.5-turbo')
            endpoint = config.get('llm', 'endpoint', fallback='https://api.openai.com/v1/chat/completions')
            timeout = config.getint('llm', 'timeout', fallback=15)
            return OpenAIProvider(
                api_key=api_key,
                model_name=model_name,  # 修正参数名
                endpoint=endpoint,
                timeout=timeout
            )
            
        elif provider_name == 'deepseek':
            from .llm_providers.deepseek import DeepseekProvider
            model_name = config.get('llm', 'model_name', fallback='deepseek-chat')
            endpoint = config.get('llm', 'endpoint', fallback='https://api.deepseek.com')
            timeout = config.getint('llm', 'timeout', fallback=15)
            return DeepseekProvider(
                api_key=api_key,
                model_name=model_name,  # 修正参数名
                endpoint=endpoint,
                timeout=timeout
            )
            
        else:
            raise ValueError(f"不支持的LLM提供商: {provider}")