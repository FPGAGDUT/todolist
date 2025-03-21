from datetime import datetime, timedelta
import time
import threading
import winsound  # For sound notification on Windows
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import pyqtSignal, QObject

class ReminderSignals(QObject):
    notify = pyqtSignal(str)

class Reminder(QObject):
    def __init__(self):
        super().__init__()
        self.reminders = []
        self.signals = ReminderSignals()

    def add_reminder(self, message, remind_time, repeat=False, repeat_interval=None):
        """
        添加提醒
        :param message: 提醒消息
        :param remind_time: 提醒时间
        :param repeat: 是否重复提醒
        :param repeat_interval: 重复间隔（秒）
        """
        self.reminders.append({
            'message': message,
            'time': remind_time,
            'repeat': repeat,
            'repeat_interval': repeat_interval
        })
        self.reminders.sort(key=lambda x: x['time'])  # 按时间排序

    def check_reminders(self):
        """检查是否有到期的提醒"""
        while True:
            now = datetime.now()
            reminders_to_remove = []
            reminders_to_add = []

            for reminder in self.reminders:
                if now >= reminder['time']:
                    self.notify(reminder['message'])
                    
                    # 如果是重复提醒，则重新添加
                    if reminder['repeat'] and reminder['repeat_interval']:
                        next_time = reminder['time'] + timedelta(seconds=reminder['repeat_interval'])
                        reminders_to_add.append({
                            'message': reminder['message'],
                            'time': next_time,
                            'repeat': reminder['repeat'],
                            'repeat_interval': reminder['repeat_interval']
                        })
                    
                    reminders_to_remove.append(reminder)
            
            # 移除已提醒的项目
            for reminder in reminders_to_remove:
                if reminder in self.reminders:
                    self.reminders.remove(reminder)
            
            # 添加重复提醒
            for reminder in reminders_to_add:
                self.reminders.append(reminder)
            
            time.sleep(10)  # 每10秒检查一次

    def notify(self, message):
        """通知用户"""
        print(f"提醒: {message}")
        winsound.Beep(1000, 500)  # 声音提醒
        self.signals.notify.emit(message)

    def start(self):
        """启动提醒检查线程"""
        reminder_thread = threading.Thread(target=self.check_reminders)
        reminder_thread.daemon = True
        reminder_thread.start()

# 示例用法
if __name__ == "__main__":
    reminder = Reminder()
    reminder.start()
    reminder.add_reminder("团队会议", datetime.now() + timedelta(seconds=10))
    reminder.add_reminder("提交报告", datetime.now() + timedelta(seconds=20))
    
    # 保持程序运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass