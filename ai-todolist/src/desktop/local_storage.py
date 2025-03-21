import json
import os
import time

class LocalStorage:
    """用于在网络不可用时提供本地存储支持"""
    
    def __init__(self, file_path='local_tasks.json'):
        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        self.pending_operations = []
        self.tasks = {}
        self.load_data()
    
    def load_data(self):
        """加载本地数据"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pending_operations = data.get('pending_operations', [])
                    self.tasks = data.get('tasks', {})
            except Exception as e:
                print(f"加载本地数据错误: {e}")
    
    def save_data(self):
        """保存数据到本地文件"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'pending_operations': self.pending_operations,
                    'tasks': self.tasks
                }, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存本地数据错误: {e}")
            return False
    
    def add_operation(self, operation):
        """添加待处理的操作"""
        self.pending_operations.append(operation)
        self.save_data()
    
    def get_pending_operations(self):
        """获取所有待处理的操作"""
        return self.pending_operations
    
    def clear_operations(self, count):
        """清除已处理的操作"""
        if count > 0:
            self.pending_operations = self.pending_operations[count:]
            self.save_data()
    
    def update_task(self, task_id, task_data):
        """更新或添加任务到本地存储"""
        self.tasks[task_id] = task_data
        self.save_data()
    
    def delete_task(self, task_id):
        """从本地存储中删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_data()
    
    def get_all_tasks(self):
        """获取所有本地存储的任务"""
        return list(self.tasks.values())