import json
import os
import time
import datetime
import uuid

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
                    self.pending_operations = data.get('operations', [])  # 注意这里的键名应与save_data一致
                    self.tasks = data.get('tasks', {})
                    
                    print(f"加载了 {len(self.tasks)} 个任务和 {len(self.pending_operations)} 个待处理操作")
                    
                    # 如果有任务，打印第一个任务的详细信息进行调试
                    if self.tasks:
                        first_task_id = list(self.tasks.keys())[0]
                        print(f"示例任务: {self.tasks[first_task_id]}")
            except Exception as e:
                print(f"加载本地数据错误: {e}")
                # 备份可能损坏的文件
                if os.path.exists(self.file_path):
                    backup_path = f"{self.file_path}.backup_{int(time.time())}"
                    try:
                        os.rename(self.file_path, backup_path)
                        print(f"已备份可能损坏的数据文件到: {backup_path}")
                    except:
                        pass
    
    def save_data(self):
        """保存数据到本地文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # 序列化任务数据
            serialized_data = {
                "tasks": self.tasks,
                "operations": self.pending_operations
            }
            
            # 使用临时文件确保写入完整性
            temp_file = f"{self.file_path}.temp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(serialized_data, f)
                f.flush()  # 确保数据写入系统缓冲区
            
            # 安全地用临时文件替换原文件
            if os.path.exists(self.file_path):
                os.replace(temp_file, self.file_path)
            else:
                os.rename(temp_file, self.file_path)
                
            print(f"成功保存数据到: {self.file_path}")
            print(f"保存了 {len(self.tasks)} 个任务")
            
            return True
        except Exception as e:
            print(f"保存数据失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _serialize_datetime(self, obj):
        """序列化日期时间对象"""
        if isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, datetime.time):
            return obj.strftime("%H:%M")
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    def add_operation(self, operation):
        """添加一个待处理的操作"""
        try:
            self.pending_operations.append(operation)
            saved = self.save_data()
            print(f"添加操作到待处理队列 {'成功' if saved else '失败'}")
            return saved
        except Exception as e:
            print(f"添加操作失败: {e}")
            return False
    
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