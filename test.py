import os
import openai  # 添加对OpenAI库的导入

os.environ["http_proxy"] = "http://127.0.0.1:10808"
os.environ["https_proxy"] = "http://127.0.0.1:10808"

api_key = os.environ.get("DEEPSEEK_API_KEY", "") 
print(api_key)
client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

respone = client.chat.completions.create(model="deepseek-chat", messages=[{"role": "user", "content": "你好"}],
                                            temperature=0.3,
                                            max_tokens=500,
                                            timeout=15)
print(respone)