# 在文件顶部的导入部分添加
import math
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5 import QtWidgets, QtCore, QtGui


# 添加浮动按钮类
class FloatingButton(QtWidgets.QWidget):
    """圆形浮窗按钮，在主窗口最小化时显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置无边框、透明背景的窗口
        self.setWindowFlags(
            Qt.Tool | 
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置窗口大小
        self.size = 40
        self.setFixedSize(self.size, self.size)
        
        # 鼠标拖动相关变量
        self.pressing = False
        self.offset = QPoint()
        
        # 图标
        self.icon = QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogDetailedView)
        
        # 动画效果
        self.opacity = 0.8
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.pulse_animation)
        self.pulse_direction = 1
        self.timer.start(50)
        
        # 保存屏幕尺寸，用于避免窗口移出屏幕
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        
        # 默认位置：屏幕右侧中间
        self.move(self.screen_width - self.size - 20, self.screen_height // 2 - self.size)

    def paintEvent(self, event):
        """绘制圆形按钮"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 绘制圆形背景
        painter.setPen(Qt.NoPen)
        gradient = QtGui.QRadialGradient(self.size/2, self.size/2, self.size/2)
        gradient.setColorAt(0, QtGui.QColor(0, 123, 255, int(255 * self.opacity)))
        gradient.setColorAt(1, QtGui.QColor(0, 105, 217, int(255 * self.opacity)))
        painter.setBrush(QtGui.QBrush(gradient))
        painter.drawEllipse(0, 0, self.size, self.size)
        
        # 绘制图标
        icon_size = int(self.size * 0.6)
        icon_rect = QtCore.QRect(
            (self.size - icon_size) // 2,
            (self.size - icon_size) // 2,
            icon_size,
            icon_size
        )
        self.icon.paint(painter, icon_rect, Qt.AlignCenter)
        
        # 绘制阴影
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 30)))
        painter.drawEllipse(-1, -1, self.size + 2, self.size + 2)

    def pulse_animation(self):
        """呼吸灯效果"""
        self.opacity += 0.01 * self.pulse_direction
        if self.opacity >= 0.9:
            self.pulse_direction = -1
        elif self.opacity <= 0.7:
            self.pulse_direction = 1
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下事件，用于开始拖动"""
        if event.button() == Qt.LeftButton:
            self.pressing = True
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于拖动窗口"""
        if self.pressing and (event.buttons() == Qt.LeftButton):
            new_pos = self.mapToGlobal(event.pos() - self.offset)
            
            # 确保窗口不会移出屏幕
            x = max(0, min(new_pos.x(), self.screen_width - self.size))
            y = max(0, min(new_pos.y(), self.screen_height - self.size))
            
            self.move(x, y)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件，停止拖动"""
        if event.button() == Qt.LeftButton:
            self.pressing = False

    def mouseDoubleClickEvent(self, event):
        """双击事件，显示主窗口"""
        if event.button() == Qt.LeftButton:
            self.parent().show()
            self.parent().activateWindow()
            self.hide()

    def contextMenuEvent(self, event):
        """处理右键菜单事件"""
        # 创建菜单
        context_menu = QtWidgets.QMenu(self)
        
        # 添加菜单项
        show_action = context_menu.addAction("打开窗口")
        show_action.triggered.connect(self.show_main_window)
        
        add_task_action = context_menu.addAction("快速添加任务")
        add_task_action.triggered.connect(self.quick_add_task)
        
        context_menu.addSeparator()
        
        exit_action = context_menu.addAction("退出应用")
        exit_action.triggered.connect(QtWidgets.qApp.quit)
        
        # 在鼠标位置显示菜单
        context_menu.exec_(event.globalPos())

    def show_main_window(self):
        """显示主窗口"""
        self.parent().show()
        self.parent().activateWindow()
        self.hide()

    def quick_add_task(self):
        """快速添加任务"""
        # 调用父窗口的快速添加任务方法
        self.parent().quick_add_task()
        # 如果任务已添加，可以考虑显示主窗口
        # self.show_main_window()
