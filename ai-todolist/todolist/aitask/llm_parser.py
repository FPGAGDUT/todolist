import json
import datetime
from typing import Dict, List, Optional, Any
import openai  # 添加对OpenAI库的导入

class LLMTaskParser:
    """基于大模型API的任务解析器"""
    
    def __init__(self, api_key=None, model="deepseek-chat",end_point="https://api.deepseek.com", timeout=15):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        
        # 初始化OpenAI客户端
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key, base_url=end_point)
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析任务文本"""
        if not text.strip():
            return self._get_default_response(text)
        
        prompt = self._create_parsing_prompt(text)
        response = self._call_llm_api(prompt)
        
        # 解析响应
        if not response:
            return self._get_default_response(text)
            
        return self._process_response(response, text)
    
    def _get_default_response(self, text: str) -> Dict[str, Any]:
        """返回默认响应"""
        return {
            "text": text,
            "category": "其他",
            "due_date": None,
            "due_time": None,
            "priority": "正常",
            "subtasks": []
        }
    
    def _create_parsing_prompt(self, text: str) -> List[Dict[str, str]]:
        """创建提示词"""
        return [
            {"role": "system", "content": """你是一个待办事项解析助手，擅长从自然语言描述中提取关键信息。
请分析用户输入的待办事项，提取任务本身、分类、日期时间和优先级等信息，并以JSON格式返回。
分类必须是以下之一：工作、学习、生活、其他。
优先级必须是以下之一：高、正常、低。"""},
            {"role": "user", "content": f"""分析这个待办事项："{text}"
返回以下JSON格式（不要包含其他解释）：
{{
  "task": "提取的核心任务内容，删除日期时间等信息",
  "category": "工作/学习/生活/其他",
  "due_date": "截止日期，格式为YYYY-MM-DD，如无则为null",
  "due_time": "截止时间，格式为HH:MM，如无则为null",
  "priority": "高/正常/低",
  "subtasks": ["可能的子任务1", "可能的子任务2"]
}}"""}
        ]
    
    def _call_llm_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """使用OpenAI库调用大模型API"""
        try:
            # 使用OpenAI客户端发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=500,
                timeout=self.timeout
            )
            
            # 提取响应内容
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                print("API响应没有包含内容")
                return None
                
        except openai.APITimeoutError:
            print("API请求超时")
            return None
        except openai.RateLimitError:
            print("达到API速率限制")
            return None
        except openai.APIError as e:
            print(f"API错误: {str(e)}")
            return None
        except Exception as e:
            print(f"调用大模型API时出错: {str(e)}")
            return None
    
    # 其他方法保持不变，但_call_llm_api需要更新
    def suggest_related_tasks(self, task_text: str, existing_tasks: List[str] = []) -> List[Dict[str, str]]:
        """根据当前任务建议相关任务"""
        prompt = [
            {"role": "system", "content": "你是一个任务规划助手，可以根据用户的现有任务提供相关任务建议。"},
            {"role": "user", "content": f"""
根据以下任务，建议2-3个相关的后续任务:

当前任务: {task_text}

已有任务列表:
{', '.join(existing_tasks[:5]) if existing_tasks else '无'}

以JSON格式返回建议 (不要有其他说明):
{{
  "suggestions": [
    {{
      "task": "建议任务1",
      "category": "工作/学习/生活/其他"
    }},
    ...
  ]
}}
"""}
        ]
        
        response = self._call_llm_api(prompt)
        if not response:
            return []
            
        try:
            data = json.loads(response)
            return data.get("suggestions", [])
        except:
            return []
    
    def break_down_complex_task(self, task_text: str) -> Dict[str, Any]:
        """将复杂任务分解为更小的子任务"""
        prompt = [
            {"role": "system", "content": "你是一个任务分解专家，帮助用户将复杂任务拆解为具体可行的子任务。"},
            {"role": "user", "content": f"""
请将以下任务分解为3-5个具体可行的子任务:

任务: {task_text}

以JSON格式返回 (不要有其他说明):
{{
  "main_task": "原任务的核心内容",
  "subtasks": [
    "子任务1",
    "子任务2",
    ...
  ]
}}
"""}
        ]
        
        response = self._call_llm_api(prompt)
        if not response:
            return {"main_task": task_text, "subtasks": []}
            
        try:
            return json.loads(response)
        except:
            return {"main_task": task_text, "subtasks": []}
    
    def _process_response(self, response_text: str, original_text: str) -> Dict[str, Any]:
        """处理API返回的结果 - 保持原有实现"""
        try:
            # 尝试解析JSON
            data = json.loads(response_text)
            
            # 提取任务文本
            text = data.get("task", original_text)
            
            # 提取分类
            category = data.get("category", "其他")
            if category not in ["工作", "学习", "生活", "其他"]:
                category = "其他"
                
            # 提取日期和时间
            due_date = None
            if data.get("due_date") and data["due_date"] != "null":
                try:
                    due_date = datetime.datetime.strptime(data["due_date"], "%Y-%m-%d").date()
                except:
                    pass
                    
            due_time = None
            if data.get("due_time") and data["due_time"] != "null":
                try:
                    time_parts = data["due_time"].split(':')
                    due_time = datetime.time(int(time_parts[0]), int(time_parts[1]))
                except:
                    pass
            
            # 提取优先级
            priority = data.get("priority", "正常")
            if priority not in ["高", "正常", "低"]:
                priority = "正常"
                
            # 提取子任务
            subtasks = data.get("subtasks", [])
            if not isinstance(subtasks, list):
                subtasks = []
                
            return {
                "text": text,
                "category": category,
                "due_date": due_date,
                "due_time": due_time,
                "priority": priority,
                "subtasks": subtasks
            }
            
        except json.JSONDecodeError:
            print("无法解析API返回的JSON")
            return {
                "text": original_text,
                "category": "其他",
                "due_date": None,
                "due_time": None,
                "priority": "正常",
                "subtasks": []
            }