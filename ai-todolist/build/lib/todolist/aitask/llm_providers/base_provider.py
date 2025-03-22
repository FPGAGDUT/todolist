import abc
from typing import Dict, List, Optional, Any
import json
import datetime

class BaseLLMProvider(abc.ABC):
    """LLM 提供商的抽象基类"""
    
    def __init__(self, api_key: str, model_name: str, endpoint: str, timeout: int = 15):
        self.api_key = api_key
        self.model_name = model_name
        self.endpoint = endpoint
        self.timeout = timeout
    
    @abc.abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], 
                        temperature: float = 0.7, 
                        max_tokens: int = 500,
                        **kwargs) -> Optional[str]:
        """对话完成请求的抽象方法"""
        pass
        
    def parse_task(self, text: str) -> Dict[str, Any]:
        """解析任务描述通用方法"""
        prompt = self._create_task_parsing_prompt(text)
        response = self.chat_completion(prompt, temperature=0.3)
        # print(f"解析任务响应: {response}")
        
        if not response:
            return self._get_default_task_response(text)
        
        return self._process_task_response(response, text)
        
    def suggest_related_tasks(self, task: str, existing_tasks: List[str] = []) -> List[Dict[str, str]]:
        """建议相关任务通用方法"""
        prompt = self._create_suggestion_prompt(task, existing_tasks)
        response = self.chat_completion(prompt, temperature=0.7)
        
        if not response:
            return []
            
        return self._process_suggestion_response(response)
        
    def break_down_task(self, task: str) -> Dict[str, Any]:
        """分解任务通用方法"""
        prompt = self._create_breakdown_prompt(task)
        response = self.chat_completion(prompt, temperature=0.5)
        
        if not response:
            return {"main_task": task, "subtasks": []}
            
        return self._process_breakdown_response(response, task)
    
    # 内部辅助方法
    def _create_task_parsing_prompt(self, text: str) -> List[Dict[str, str]]:
        """创建任务解析提示"""
        # 获取当前日期时间
        today = datetime.datetime.now()
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        
        date_str = today.strftime("%Y年%m月%d日 %A")  # 例如：2025年3月21日 星期五
        
        return [
            {"role": "system", "content": f"""你是一个待办事项解析助手，擅长从自然语言描述中提取关键信息。
今天是{date_str}。

请分析用户输入的待办事项，提取任务本身、分类、日期时间和优先级等信息，并以JSON格式返回。
分类必须是以下之一：工作、学习、生活、其他。
优先级必须是以下之一：高、正常、低。

特别注意：当用户提到相对时间，如"今天"、"明天"、"后天"、"下周"等，请将其转换为具体日期：
- 今天 = {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})
- 明天 = {tomorrow.strftime('%Y-%m-%d')} ({tomorrow.strftime('%A')})
- 后天 = {(today + datetime.timedelta(days=2)).strftime('%Y-%m-%d')} ({(today + datetime.timedelta(days=2)).strftime('%A')})
- 下周一 = {(today + datetime.timedelta(days=(0-today.weekday()+7))).strftime('%Y-%m-%d')}
- 下周末 = {(today + datetime.timedelta(days=(5-today.weekday()+7))).strftime('%Y-%m-%d')}
"""},
        {"role": "user", "content": f"""分析这个待办事项："{text}"
返回以下JSON格式（不要包含其他解释）：
{{
"task": "提取的核心任务内容，删除日期时间等信息",
"category": "工作/学习/生活/其他",
"due_date": "截止日期，格式为YYYY-MM-DD，如无则为null",
"due_time": "截止时间，格式为HH:MM，如无则为null",
"priority": "高/正常/低",
"subtasks": ["可能的子任务1", "可能的子任务2"]
}}

示例1：
待办事项："明天下午3点开会讨论项目进展"
结果：
{{
"task": "开会讨论项目进展",
"category": "工作",
"due_date": "{tomorrow.strftime('%Y-%m-%d')}",
"due_time": "15:00",
"priority": "高",
"subtasks": []
}}

示例2：
待办事项："下周一交报告"
结果：
{{
"task": "交报告",
"category": "工作",
"due_date": "{(today + datetime.timedelta(days=(0-today.weekday()+7))).strftime('%Y-%m-%d')}",
"due_time": null,
"priority": "高",
"subtasks": []
}}"""}
        ]
    
    # 其他内部辅助方法实现...
    def _get_default_task_response(self, text: str) -> Dict[str, Any]:
        """返回默认的任务解析结果"""
        return {
            "text": text,
            "category": "其他",
            "due_date": None,
            "due_time": None,
            "priority": "正常",
            "subtasks": []
        }
    

    def _create_suggestion_prompt(self, task: str, existing_tasks: List[str]) -> List[Dict[str, str]]:
        """创建任务建议提示"""
        return [
            {"role": "system", "content": "你是一个任务规划助手，可以根据用户的现有任务提供相关任务建议。"},
            {"role": "user", "content": f"""
根据以下任务，建议2-3个相关的后续任务:

当前任务: {task}

已有任务列表:
{', '.join(existing_tasks[:5]) if existing_tasks else '无'}

以JSON格式返回建议 (不要包含其他解释):
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
    
    def _process_suggestion_response(self, response: str) -> List[Dict[str, str]]:
        """处理任务建议响应"""
        try:
            data = json.loads(response)
            return data.get("suggestions", [])
        except json.JSONDecodeError:
            print("无法解析任务建议响应JSON")
            return []
    
    def _create_breakdown_prompt(self, task: str) -> List[Dict[str, str]]:
        """创建任务分解提示"""
        return [
            {"role": "system", "content": "你是一个任务分解专家，帮助用户将复杂任务拆解为具体可行的子任务。"},
            {"role": "user", "content": f"""
请将以下任务分解为3-5个具体可行的子任务:

任务: {task}

以JSON格式返回 (不要包含其他解释):
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
    
    def _process_breakdown_response(self, response: str, original_task: str) -> Dict[str, Any]:
        """处理任务分解响应"""
        try:
            data = json.loads(response)
            main_task = data.get("main_task", original_task)
            subtasks = data.get("subtasks", [])
            
            if not isinstance(subtasks, list):
                subtasks = []
                
            return {
                "main_task": main_task,
                "subtasks": subtasks
            }
        except json.JSONDecodeError:
            print("无法解析任务分解响应JSON")
            return {"main_task": original_task, "subtasks": []}
    
    def _process_task_response(self, response_text: str, original_text: str) -> Dict[str, Any]:
        """处理任务解析响应"""
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
                    # 修复这里: 使用datetime.datetime.strptime而不是datetime.strptime
                    due_date = datetime.datetime.strptime(data["due_date"], "%Y-%m-%d").date()
                except Exception as e:
                    print(f"解析日期出错: {e} - {data['due_date']}")
                    pass
                    
            due_time = None
            if data.get("due_time") and data["due_time"] != "null":
                try:
                    time_parts = data["due_time"].split(':')
                    due_time = datetime.time(int(time_parts[0]), int(time_parts[1]))
                except Exception as e:
                    print(f"解析时间出错: {e} - {data['due_time']}")
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