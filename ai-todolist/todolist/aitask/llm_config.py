import os
import configparser
from typing import Optional, Tuple

class LLMConfigManager:
    """LLM配置管理器 - 支持环境变量API密钥和代理设置"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config_file = config_file
        
        # 读取配置文件
        if os.path.exists(config_file):
            self.config.read(config_file, encoding='utf-8')
        else:
            # 如果配置文件不存在，创建默认配置
            self._create_default_config()
            
    def _create_default_config(self):
        """创建默认配置"""
        self.config["llm"] = {
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "endpoint": "https://api.deepseek.com",
            "timeout": "15",
            "proxy_host": "",
            "proxy_port": ""
        }
        
        # 保存默认配置到文件
        with open(self.config_file, 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)
            
    def get_provider_name(self) -> str:
        """获取LLM提供商名称"""
        if "llm" in self.config and "provider" in self.config["llm"]:
            return self.config["llm"]["provider"]
        return "deepseek"  # 默认
    
    def get_api_key(self) -> str:
        """从环境变量获取API密钥"""
        provider = self.get_provider_name().upper()
        env_var = f"{provider}_API_KEY"
        api_key = os.environ.get(env_var, "")
        
        if not api_key:
            print(f"警告: 环境变量 {env_var} 未设置或为空")
            
        return api_key
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        if "llm" in self.config and "model_name" in self.config["llm"]:
            return self.config["llm"]["model_name"]
            
        # 返回默认值
        provider = self.get_provider_name().lower()
        if provider == "deepseek":
            return "deepseek-chat"
        elif provider == "volcanoark":
            return "Spark-3"
        elif provider == "openai":
            return "gpt-3.5-turbo"
        return "unknown-model"
    
    def get_endpoint(self) -> str:
        """获取API端点URL"""
        if "llm" in self.config and "endpoint" in self.config["llm"]:
            return self.config["llm"]["endpoint"]
            
        # 返回默认值
        provider = self.get_provider_name().lower()
        if provider == "deepseek":
            return "https://api.deepseek.com"
        elif provider == "volcanoark":
            return "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        elif provider == "openai":
            return "https://api.openai.com/v1"
        return ""
    
    def get_timeout(self) -> int:
        """获取超时设置"""
        try:
            if "llm" in self.config and "timeout" in self.config["llm"]:
                return int(self.config["llm"]["timeout"])
        except ValueError:
            pass
        return 15  # 默认15秒
    
    def get_proxy(self) -> Tuple[Optional[str], Optional[int]]:
        """获取代理设置
        
        Returns:
            tuple: (proxy_host, proxy_port) 如果未设置则返回 (None, None)
        """
        host = None
        port = None
        
        if "llm" in self.config:
            if "proxy_host" in self.config["llm"] and self.config["llm"]["proxy_host"]:
                host = self.config["llm"]["proxy_host"]
                
            if "proxy_port" in self.config["llm"] and self.config["llm"]["proxy_port"]:
                try:
                    port = int(self.config["llm"]["proxy_port"])
                except ValueError:
                    print(f"警告: 代理端口配置无效: {self.config['llm']['proxy_port']}")
        
        return host, port
    
    def has_proxy(self) -> bool:
        """检查是否配置了代理"""
        host, port = self.get_proxy()
        return host is not None and port is not None