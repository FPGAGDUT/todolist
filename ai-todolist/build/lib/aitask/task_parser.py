from typing import Dict, List, Any, Optional
from .llm_factory import LLMFactory
from datetime import datetime

class AITaskParser:
    """AI任务解析器包装类"""
    
    def __init__(self, config_file: str = "config.ini"):
        self.provider = LLMFactory.create_provider(config_file)
        if not self.provider:
            raise ValueError("无法创建LLM提供商实例，请检查配置")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """解析任务文本"""
        if not text.strip():
            return self._get_default_response(text)
            
        return self.provider.parse_task(text)
    
    def suggest_related_tasks(self, task_text: str, existing_tasks: List[str] = []) -> List[Dict[str, str]]:
        """根据当前任务建议相关任务"""
        return self.provider.suggest_related_tasks(task_text, existing_tasks)
    
    def break_down_complex_task(self, task_text: str) -> Dict[str, Any]:
        """将复杂任务分解为更小的子任务"""
        return self.provider.break_down_task(task_text)
    
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