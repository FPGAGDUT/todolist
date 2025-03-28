import threading
import time
import heapq
from datetime import datetime, timedelta
from PyQt5 import QtCore, QtWidgets
from .reminder_window import ReminderWindow
# from .reminders import Reminder

class Reminder(QtCore.QObject):
    """优化后的任务提醒系统 - 使用单一线程和优先队列管理所有提醒"""
    
    # 定义信号
    reminder_triggered = QtCore.pyqtSignal(str, str, datetime)  # 任务ID, 文本, 时间
    task_completed = QtCore.pyqtSignal(str)  # 通知任务完成
    
    def __init__(self):
        super().__init__()
        
        # 使用优先队列存储提醒（按时间排序）
        self.reminder_queue = []  # [(due_time, task_id, task_text), ...]
        
        # 当前活动的提醒
        self.active_reminders = set()  # 存储已触发但尚未处理的提醒
        
        # 控制线程和访问同步
        self.running = False
        self.thread = None
        self.mutex = threading.Lock()
        self.queue_updated = threading.Event()  # 用于唤醒线程检查队列变化
        
        # 创建单个提醒窗口实例（而非每个提醒一个窗口）
        self.reminder_window = ReminderWindow()
        
        # 连接提醒窗口信号
        self.reminder_window.task_completed.connect(self.on_task_completed)
        self.reminder_window.snooze_requested.connect(self.on_snooze_requested)
        self.reminder_window.dismissed.connect(self.on_dismissed)
        
        # 连接自己的提醒信号到显示提醒窗口的槽函数
        self.reminder_triggered.connect(self.show_reminder)
        
        # 提醒等待队列 - 用于处理同时有多个提醒的情况
        self.pending_reminders = []
        
        # 提醒显示状态
        self.is_showing_reminder = False
    
    def start(self):
        """启动提醒监控线程"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._reminder_monitor, daemon=True)
        self.thread.start()
        print("提醒系统已启动")
    
    def stop(self):
        """停止提醒监控线程"""
        self.running = False
        self.queue_updated.set()  # 唤醒线程让它能够退出
        
        if self.thread:
            self.thread.join(1.0)
            self.thread = None
        print("提醒系统已停止")
    
    def add_reminder(self, task_id, task_text, due_time):
        """添加任务提醒到优先队列"""
        with self.mutex:
            # 移除可能已存在的相同任务ID的提醒
            self.reminder_queue = [r for r in self.reminder_queue if r[1] != task_id]
            
            # 添加新提醒
            heapq.heappush(self.reminder_queue, (due_time, task_id, task_text))
            print(f"已添加任务提醒: {task_id}, {task_text}, 时间: {due_time}")
            
            # 触发队列更新事件，唤醒监控线程
            self.queue_updated.set()
    
    def remove_reminder(self, task_id):
        """移除任务提醒"""
        with self.mutex:
            # 从队列中移除特定任务ID的提醒
            self.reminder_queue = [r for r in self.reminder_queue if r[1] != task_id]
            heapq.heapify(self.reminder_queue)  # 重新建立堆结构
            
            # 从活动提醒集合中移除
            if task_id in self.active_reminders:
                self.active_reminders.remove(task_id)
                
            # 从等待队列中移除
            self.pending_reminders = [r for r in self.pending_reminders if r[1] != task_id]
    
    def _reminder_monitor(self):
        """单一线程监控所有提醒任务"""
        while self.running:
            next_reminder_time = None
            
            # 检查队列中最早的提醒
            with self.mutex:
                if self.reminder_queue:
                    next_reminder_time, _, _ = self.reminder_queue[0]  # 堆顶元素
            
            # 计算等待时间
            wait_time = 10.0  # 默认10秒检查一次
            
            if next_reminder_time:
                now = datetime.now()
                if now >= next_reminder_time:
                    # 有到期的提醒，立即处理
                    wait_time = 0
                else:
                    # 计算到下一个提醒的等待时间（最多30秒检查一次）
                    seconds_to_wait = (next_reminder_time - now).total_seconds()
                    wait_time = min(seconds_to_wait, 30.0)
            
            # 等待指定时间或直到队列更新
            self.queue_updated.wait(wait_time)
            self.queue_updated.clear()
            
            # 处理到期的提醒
            self._process_due_reminders()
    
    def _process_due_reminders(self):
        """处理所有到期的提醒"""
        now = datetime.now()
        triggered_reminders = []
        
        with self.mutex:
            # 检查并收集所有已到期的提醒
            while self.reminder_queue and self.reminder_queue[0][0] <= now:
                due_time, task_id, task_text = heapq.heappop(self.reminder_queue)
                
                # 避免重复触发已经活跃的提醒
                if task_id not in self.active_reminders:
                    triggered_reminders.append((due_time, task_id, task_text))
                    self.active_reminders.add(task_id)
        
        # 处理触发的提醒
        for due_time, task_id, task_text in triggered_reminders:
            # 如果当前有提醒在显示，将新提醒加入等待队列
            if self.is_showing_reminder:
                self.pending_reminders.append((due_time, task_id, task_text))
            else:
                # 直接显示提醒
                self.reminder_triggered.emit(task_id, task_text, due_time)
    
    @QtCore.pyqtSlot(str, str, datetime)
    def show_reminder(self, task_id, task_text, due_time):
        """显示提醒窗口"""
        self.is_showing_reminder = True
        self.reminder_window.show_reminder(task_id, task_text, due_time)
    
    def _process_next_reminder(self):
        """处理队列中的下一个提醒"""
        if not self.pending_reminders:
            self.is_showing_reminder = False
            return
        
        # 获取下一个待显示的提醒
        due_time, task_id, task_text = self.pending_reminders.pop(0)
        
        # 显示提醒
        self.reminder_triggered.emit(task_id, task_text, due_time)
    
    @QtCore.pyqtSlot(str)
    def on_task_completed(self, task_id):
        """处理任务完成事件"""
        # 从活动提醒中移除
        with self.mutex:
            if task_id in self.active_reminders:
                self.active_reminders.remove(task_id)
        
        # 发送信号通知主应用标记任务完成
        self.task_completed.emit(task_id)
        
        # 处理下一个提醒
        QtCore.QTimer.singleShot(500, self._process_next_reminder)
    
    @QtCore.pyqtSlot(str, int)
    def on_snooze_requested(self, task_id, minutes):
        """处理稍后提醒请求"""
        # 从活动提醒中移除
        with self.mutex:
            if task_id in self.active_reminders:
                self.active_reminders.remove(task_id)
        
        # 从所有等待队列中移除此任务的提醒
        self.pending_reminders = [r for r in self.pending_reminders if r[1] != task_id]
        
        # 创建新的延迟提醒
        task_text = None
        
        # 查找任务文本
        for _, t_id, text in self.reminder_queue:
            if t_id == task_id:
                task_text = text
                break
        
        # 如果没找到，可能已被触发，使用提醒窗口中的文本
        if not task_text:
            task_text = self.reminder_window.task_text.text()
        
        # 创建新的延迟提醒
        new_time = datetime.now() + timedelta(minutes=minutes)
        self.add_reminder(task_id, task_text, new_time)
        print(f"任务已延迟: {task_id}, {minutes}分钟后再提醒")
        
        # 处理下一个提醒
        QtCore.QTimer.singleShot(500, self._process_next_reminder)
    
    @QtCore.pyqtSlot()
    def on_dismissed(self):
        """处理提醒关闭事件"""
        # 处理下一个提醒
        QtCore.QTimer.singleShot(500, self._process_next_reminder)
    
    def get_pending_reminders_count(self):
        """获取待处理的提醒数量"""
        with self.mutex:
            return len(self.reminder_queue)