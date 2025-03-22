import json
import openai
from typing import Dict, List, Optional, Any
from .base_provider import BaseLLMProvider

class DeepseekProvider(BaseLLMProvider):
    """DeepSeek API实现"""
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat", 
                 endpoint: str = "https://api.deepseek.com", timeout: int = 15):
        super().__init__(api_key, model_name, endpoint, timeout)
        self.client = openai.OpenAI(api_key=api_key, base_url=endpoint)
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                        temperature: float = 0.7, 
                        max_tokens: int = 500,
                        **kwargs) -> Optional[str]:
        """调用DeepSeek API获取对话响应"""
        print("调用DeepSeek API")
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                print("DeepSeek API响应没有内容")
                return None
                
        except openai.APITimeoutError:
            print("DeepSeek API请求超时")
            return None
        except openai.RateLimitError:
            print("DeepSeek API达到速率限制")
            return None
        except openai.APIError as e:
            print(f"DeepSeek API错误: {str(e)}")
            return None
        except Exception as e:
            print(f"调用DeepSeek API时出错: {str(e)}")
            return None