import requests
import json
from datetime import datetime
import time
import threading
from .local_storage import LocalStorage
import logging
import uuid

class NetworkManager:
    """负责与服务器通信的模块"""
    
    def __init__(self, base_url="https://api.todo.example.com/v1", api_key=None, local_first=False):
        self.local_first = local_first
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 如果提供了API密钥，添加到头部
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        
        # 用于同步的变量
        self.sync_queue = []
        self.syncing = False
        self.sync_lock = threading.Lock()
        
        # 添加本地存储
        self.local_storage = LocalStorage()
        
        # 连接状态
        self.is_online = True
        self.connection_check_interval = 30  # 多久检查一次连接 (秒)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("NetworkManager")
        
        # 启动同步线程和连接监控线程
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()
        
        self.connection_thread = threading.Thread(target=self._connection_monitor, daemon=True)
        self.connection_thread.start()
        
        # 初始化时检查连接状态
        self._check_connection()
        self.logger.info(f"初始化完成, 连接状态: {'在线' if self.is_online else '离线'}")

    def _check_connection(self):
        """检查与服务器的连接状态"""
        try:
            response = requests.get(f"{self.base_url}/ping", timeout=5)
            was_online = self.is_online
            self.is_online = response.status_code == 200
            
            # 如果从离线切换到在线，触发同步
            if not was_online and self.is_online:
                self.logger.info("网络已恢复，开始同步本地数据")
                self._sync_local_data()
                
            return self.is_online
        except:
            was_online = self.is_online
            self.is_online = False
            
            if was_online:
                self.logger.warning("网络连接丢失，切换到离线模式")
                
            return False
    def _connection_monitor(self):
        """监控网络连接状态的后台线程"""
        while True:
            self._check_connection()
            time.sleep(self.connection_check_interval)
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """执行HTTP请求并处理可能的错误"""
        if not self.is_online:
            return {"success": False, "error": "当前处于离线模式"}
        
        url = f"{self.base_url}/{endpoint}"
        print(f"data: {data}")  # 调试信息
        try:
            # 将超时时间从10秒减少到5秒
            if method.lower() == "get":
                response = requests.get(url, headers=self.headers, params=params, timeout=5)
            elif method.lower() == "post":
                response = requests.post(url, headers=self.headers, json=data, timeout=5)
            elif method.lower() == "put":
                response = requests.put(url, headers=self.headers, json=data, timeout=5)
            elif method.lower() == "delete":
                response = requests.delete(url, headers=self.headers, timeout=5)
            else:
                return {"success": False, "error": "不支持的HTTP方法"}
            
            # 添加这部分处理响应的代码
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    return {"success": True, "data": response.json()}
                except json.JSONDecodeError:
                    # 如果响应不是有效JSON，但状态码是成功的
                    return {"success": True, "data": {"message": response.text}}
            else:
                self.logger.error(f"服务器错误: {response.status_code}, {response.text}")
                return {
                    "success": False,
                    "error": f"服务器错误 ({response.status_code})",
                    "details": response.text
                }
            
        except requests.exceptions.RequestException as e:
            self.is_online = False
            self.logger.warning(f"网络请求错误: {str(e)}, 切换到离线模式")
            return {"success": False, "error": f"网络请求错误: {str(e)}"}
        except json.JSONDecodeError:
            self.logger.error("服务器返回了无效的JSON响应")
            return {"success": False, "error": "无效的JSON响应"}
        
    def sync_and_wait(self, timeout=10):
        """同步数据并等待完成，返回是否成功同步
        
        Args:
            timeout: 等待超时时间(秒)
            
        Returns:
            bool: 是否成功完成同步
        """
        if not self.is_online or not self.sync_queue:
            return True  # 如果不在线或没有需要同步的内容，直接返回成功
        
        # 触发同步
        self._check_connection()
        if not self.is_online:
            return False
        
        # 创建事件用于通知同步完成
        sync_complete = threading.Event()
        original_queue_size = len(self.sync_queue)
        
        # 定义回调
        def sync_callback():
            """检查同步是否完成"""
            if len(self.sync_queue) < original_queue_size or not self.sync_queue:
                sync_complete.set()
        
        # 启动同步
        self._sync_local_data()
        self._trigger_sync()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=lambda: self._monitor_sync(sync_complete, sync_callback))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 等待同步完成或超时
        success = sync_complete.wait(timeout)
        return success

    def _monitor_sync(self, complete_event, callback_fn, check_interval=0.5):
        """监控同步进度"""
        start_time = time.time()
        while not complete_event.is_set():
            time.sleep(check_interval)
            callback_fn()
            
            # 如果同步状态改变了，也触发检查
            if not self.syncing:
                callback_fn()
        
    def update_task_direct(self, task_id, update_data):
        """直接更新任务，不经过LLM解析"""
        if task_id not in self.local_storage.tasks:
            return {"success": False, "error": "任务不存在"}
        
        # 获取原始任务
        task = self.local_storage.tasks[task_id].copy()
        
        # 序列化日期和时间
        if isinstance(update_data.get("due_date"), datetime.date):
            update_data["due_date"] = update_data["due_date"].strftime("%Y-%m-%d")
        
        if isinstance(update_data.get("due_time"), datetime.time):
            update_data["due_time"] = update_data["due_time"].strftime("%H:%M")
        
        # 更新任务字段
        for key, value in update_data.items():
            task[key] = value
        
        # 保存更新
        self.local_storage.tasks[task_id] = task
        self.local_storage.save_data()  # 立即保存
        
        # 添加到同步队列
        with self.sync_lock:
            operation = {
                "type": "update",
                "task_id": task_id,
                "data": update_data,
                "timestamp": datetime.now().isoformat()
            }
            self.sync_queue.append(operation)
            self.local_storage.add_operation(operation)
        
        # 如果在线，立即同步
        if self.is_online and not self.local_first:
            self._trigger_sync()
        
        return {"success": True}
    
    def get_tasks(self, filters=None):
        """获取任务列表"""
        if self.is_online:
            result = self._make_request("get", "tasks", params=filters)
            if result["success"]:
                # 同时更新本地缓存
                for task in result["data"].get("tasks", []):
                    self.local_storage.update_task(task["id"], task)
                return result
        
        # 如果在线请求失败或者处于离线模式，使用本地存储
        self.logger.info("使用本地数据获取任务")
        tasks = self.local_storage.get_all_tasks()
        
        # 应用过滤器
        if filters:
            category = filters.get("category")
            completed = filters.get("completed")
            
            if category:
                tasks = [t for t in tasks if t.get("category") == category]
            if completed is not None:
                tasks = [t for t in tasks if t.get("completed") == completed]
        
        return {"success": True, "data": {"tasks": tasks}}
    
    def create_task(self, task_data):
        """创建新任务"""
        print(f"创建任务数据: {task_data}")  # 调试信息
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 深拷贝任务数据，避免修改原始对象
        task_copy = task_data.copy() if task_data else {}

        # 安全处理日期和时间 - 避免使用可能导致卡住的isinstance
        try:
            # 如果due_date是日期对象，转换为字符串
            if task_copy.get("due_date") is not None:
                if not isinstance(task_copy["due_date"], str):
                    task_copy["due_date"] = task_copy["due_date"].strftime("%Y-%m-%d")
                print(f"处理后日期: {task_copy.get('due_date')}")
            
            # 如果due_time是时间对象，转换为字符串
            if task_copy.get("due_time") is not None:
                if not isinstance(task_copy["due_time"], str):
                    task_copy["due_time"] = task_copy["due_time"].strftime("%H:%M")
                print(f"处理后时间: {task_copy.get('due_time')}")
        except Exception as e:
            print(f"处理日期时间出错: {e}")
            # 异常处理 - 如果出现问题，将日期和时间设置为None
            task_copy["due_date"] = None
            task_copy["due_time"] = None
        # 创建完整任务记录
        task = {
            "id": task_id,
            "text": task_copy.get("text", ""),
            "category": task_copy.get("category", "其他"),
            "completed": task_copy.get("completed", False),
            "created_at": datetime.now().isoformat(),
            "due_date": task_copy.get("due_date"),
            "due_time": task_copy.get("due_time")
        }
        
        print(f"创建新任务: {task}")  # 调试信息
        
        try:
            # 保存到本地存储 - 只使用一种ID
            self.local_storage.tasks[task_id] = task
            saved = self.local_storage.save_data()  # 立即保存确保持久化
            print(f"保存到本地存储: {'成功' if saved else '失败'}")
            
            # 非阻塞方式添加到同步队列
            def add_to_sync_queue():
                try:
                    with self.sync_lock:
                        operation = {
                            "type": "create",
                            "task_id": task_id,
                            "data": task,
                            "timestamp": datetime.now().isoformat()
                        }
                        self.sync_queue.append(operation)
                        self.local_storage.add_operation(operation)
                    
                    print("已添加到同步队列")
                    
                    # 如果在线，立即触发同步但不等待结果
                    if self.is_online and not self.local_first:
                        print("触发同步")
                        self._trigger_sync()
                except Exception as e:
                    print(f"同步队列操作失败: {e}")
            
            # 在新线程中处理同步，不阻塞主线程
            threading.Thread(target=add_to_sync_queue, daemon=True).start()
            
            return {"success": True, "data": {"id": task_id}}
        except Exception as e:
            print(f"创建任务失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": f"创建任务失败: {str(e)}"}
    
    def update_task(self, task_id, task_data):
        """更新任务"""
        # 更新本地存储
        current_task = self._get_local_task(task_id)
        if current_task:
            updated_task = {**current_task, **task_data, "updated_at": datetime.now().isoformat()}
            self.local_storage.update_task(task_id, updated_task)
            
            # 添加到同步队列
            with self.sync_lock:
                operation = {
                    "type": "update",
                    "id": task_id,
                    "data": task_data,
                    "timestamp": datetime.now().isoformat()
                }
                self.sync_queue.append(operation)
                self.local_storage.add_operation(operation)
            
            # 如果在线，尝试立即同步
            if self.is_online:
                self._trigger_sync()
        
        return {"success": True, "data": {"id": task_id}}
    
    def delete_task(self, task_id):
        """删除任务"""
        # 从本地存储中删除
        self.local_storage.delete_task(task_id)
        
        with self.sync_lock:
            operation = {
                "type": "delete",
                "id": task_id,
                "timestamp": datetime.now().isoformat()
            }
            self.sync_queue.append(operation)
            self.local_storage.add_operation(operation)
        
        # 如果在线，尝试立即同步
        if self.is_online:
            self._trigger_sync()
        
        return {"success": True}
    
    def _get_local_task(self, task_id):
        """获取本地任务数据"""
        tasks = self.local_storage.get_all_tasks()
        for task in tasks:
            if task.get("id") == task_id:
                return task
        return None
    
    def _trigger_sync(self):
        """触发同步操作"""
        # 使用标志避免重复启动同步线程
        if not self.syncing and self.is_online:
            self.syncing = True
            # 启动一个新线程进行同步，不阻塞调用方
            threading.Thread(target=self._sync_with_server, daemon=True).start()
            print("同步线程已启动")
        else:
            print(f"未启动同步: 已在同步={self.syncing}, 在线状态={self.is_online}")
    
    def _sync_with_server(self):
        """与服务器同步待处理的操作"""
        try:
            if not self.is_online:
                self.syncing = False
                return
                
            with self.sync_lock:
                if not self.sync_queue:
                    self.syncing = False
                    return
                
                # 创建要发送的批量操作
                operations = self.sync_queue.copy()
                
                # 发送批量操作到服务器
                self.logger.info(f"正在同步 {len(operations)} 个操作到服务器")
                result = self._make_request("post", "tasks/batch", data={"operations": operations})
                
                if result["success"]:
                    # 同步成功，从队列中移除已处理的操作
                    self.sync_queue = self.sync_queue[len(operations):]
                    # 同时从本地存储的待处理操作中移除
                    self.local_storage.clear_operations(len(operations))
                    
                    # 处理服务器返回的ID映射
                    if "id_mapping" in result["data"]:
                        self._process_id_mapping(result["data"]["id_mapping"])
                        
                    self.logger.info("同步成功")
                else:
                    self.logger.error(f"同步失败: {result.get('error')}")
        except Exception as e:
            self.logger.error(f"同步过程中发生错误: {str(e)}")
        finally:
            self.syncing = False
            # 如果队列中还有操作，稍后继续同步
            if self.sync_queue and self.is_online:
                time.sleep(1)  # 避免立即重试导致请求过多
                self._trigger_sync()
    
    
    def _process_id_mapping(self, id_mapping):
        """处理服务器返回的ID映射，更新临时ID到永久ID"""
        for temp_id, permanent_id in id_mapping.items():
            # 获取临时ID对应的任务
            task = self._get_local_task(temp_id)
            if task:
                # 用永久ID更新任务
                task["id"] = permanent_id
                self.local_storage.update_task(permanent_id, task)
                self.local_storage.delete_task(temp_id)
                
                # 通知观察者(如果实现)
                self._notify_id_changed(temp_id, permanent_id)

    def _notify_id_changed(self, old_id, new_id):
        """通知观察者ID已更改"""
        # 在实际应用中实现，通知UI更新任务ID
        pass

    def _sync_local_data(self):
        """当网络恢复时，同步本地数据到服务器"""
        if not self.is_online:
            return
            
        # 加载本地存储中的待处理操作
        pending_ops = self.local_storage.get_pending_operations()
        
        # 添加到同步队列
        with self.sync_lock:
            for op in pending_ops:
                if op not in self.sync_queue:
                    self.sync_queue.append(op)
        
        # 触发同步
        if self.sync_queue:
            self._trigger_sync()
    
    def _sync_worker(self):
        """后台同步线程，定期检查是否有待同步操作"""
        while True:
            if self.sync_queue and self.is_online and not self.syncing:
                self._trigger_sync()
            time.sleep(5)  # 每5秒检查一次

    def force_sync(self):
        """强制进行同步，可在UI中调用"""
        self._check_connection()
        if self.is_online:
            self._sync_local_data()
            return {"success": True, "message": "同步已启动"}
        else:
            return {"success": False, "error": "当前处于离线模式，无法同步"}
    
    def toggle_online_mode(self, online=None):
        """手动切换在线/离线模式"""
        if online is None:
            self.is_online = not self.is_online
        else:
            self.is_online = online
            
        if self.is_online:
            # 检查是否真的能连接
            success = self._check_connection()
            if success:
                self._sync_local_data()
                return {"success": True, "message": "已切换到在线模式"}
            else:
                return {"success": False, "error": "无法连接到服务器"}
        else:
            return {"success": True, "message": "已切换到离线模式"}
    
    def get_connection_status(self):
        """获取当前连接状态"""
        return {
            "online": self.is_online,
            "pending_operations": len(self.sync_queue),
            "syncing": self.syncing
        }