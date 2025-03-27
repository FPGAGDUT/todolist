from PyQt5.QtCore import QRunnable, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

class Worker(QRunnable):
    """处理后台任务的工作线程"""
    
    class Signals(QObject):
        finished = pyqtSignal(object)
        error = pyqtSignal(Exception)
    
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = Worker.Signals()
    
    def run(self):
        """执行工作函数"""
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(e)