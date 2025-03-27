import json
import requests
from typing import Dict, List, Optional, Any
from .base_provider import BaseLLMProvider

class VolcanoArkProvider(BaseLLMProvider):
    """火山方舟 API 实现"""
    
    def __init__(self, api_key: str, model_name: str = "Spark-3", 
                 endpoint: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions", 
                 timeout: int = 15):
        super().__init__(api_key, model_name, endpoint, timeout)
        
    def chat_completion(self, messages: List[Dict[str, str]], 
                        temperature: float = 0.7, 
                        max_tokens: int = 500,
                        **kwargs) -> Optional[str]:
        """调用火山方舟 API 获取对话响应"""
        print("调用火山方舟API")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 添加其他可能的参数
        for key, value in kwargs.items():
            if key not in data:
                data[key] = value
                
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    print("火山方舟API响应格式无效")
                    return None
            else:
                print(f"火山方舟API错误: {response.status_code}, {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("火山方舟API请求超时")
            return None
        except requests.exceptions.RequestException as e:
            print(f"火山方舟API请求错误: {str(e)}")
            return None
        except Exception as e:
            print(f"调用火山方舟API时出错: {str(e)}")
            return None