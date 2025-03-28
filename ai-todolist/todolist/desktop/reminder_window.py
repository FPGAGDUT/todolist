import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

class ReminderWindow(QtWidgets.QWidget):
    """美观的任务提醒窗口"""
    
    # 信号定义
    task_completed = QtCore.pyqtSignal(str)  # 任务完成信号
    snooze_requested = QtCore.pyqtSignal(str, int)  # 稍后提醒信号(任务ID, 分钟)
    dismissed = QtCore.pyqtSignal()  # 关闭提醒信号
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(320, 200)
        self.setMaximumSize(320, 200)
        
        # 当前显示的任务ID
        self.current_task_id = None
        
        # 初始化UI
        self.init_ui()
        
        # 设置窗口动画效果
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 自动关闭计时器
        self.auto_close_timer = QTimer(self)
        self.auto_close_timer.timeout.connect(self.start_fade_out)
        
        # 位置相关变量
        self.old_pos = self.pos()
        self.pressing = False
    
    def init_ui(self):
        """初始化UI界面"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # 内容容器
        content_container = QtWidgets.QWidget(self)
        content_container.setObjectName("reminder_container")
        content_container.setStyleSheet("""
            #reminder_container {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        content_layout = QtWidgets.QVBoxLayout(content_container)
        
        # 标题栏
        title_bar = QtWidgets.QFrame()
        title_bar.setMaximumHeight(40)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: #4285f4;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
        title_layout = QtWidgets.QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # 标题图标和文本
        title_icon = QtWidgets.QLabel()
        title_icon.setPixmap(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_MessageBoxInformation).pixmap(24, 24))
        
        title_text = QtWidgets.QLabel("任务提醒")
        title_text.setStyleSheet("color: white; font-weight: bold;")
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                background-color: transparent;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.dismiss)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        
        # 任务内容区域
        content_frame = QtWidgets.QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        task_layout = QtWidgets.QVBoxLayout(content_frame)
        
        # 任务图标和文本
        task_info = QtWidgets.QHBoxLayout()
        task_icon = QtWidgets.QLabel()
        task_icon.setPixmap(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogDetailedView).pixmap(32, 32))
        
        self.task_text = QtWidgets.QLabel("任务内容将显示在这里")
        self.task_text.setWordWrap(True)
        self.task_text.setStyleSheet("font-size: 14px; color: #333;")
        
        task_info.addWidget(task_icon)
        task_info.addWidget(self.task_text, 1)
        
        # 时间信息
        time_layout = QtWidgets.QHBoxLayout()
        time_icon = QtWidgets.QLabel()
        time_icon.setPixmap(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_ToolBarHorizontalExtensionButton).pixmap(16, 16))
        
        self.time_label = QtWidgets.QLabel("计划时间: 00:00")
        self.time_label.setStyleSheet("color: #666; font-size: 12px;")
        
        time_layout.addWidget(time_icon)
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        
        # 操作按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        self.complete_btn = QtWidgets.QPushButton("完成任务")
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                border-radius: 5px;
                padding: 6px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367d6;
            }
        """)
        
        self.snooze_btn = QtWidgets.QPushButton("稍后提醒")
        self.snooze_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                color: #4285f4;
                border: 1px solid #dadce0;
                border-radius: 5px;
                padding: 6px 15px;
            }
            QPushButton:hover {
                background-color: #e8f0fe;
            }
        """)
        
        button_layout.addWidget(self.snooze_btn)
        button_layout.addWidget(self.complete_btn)
        
        # 连接按钮信号
        self.complete_btn.clicked.connect(self.complete_task)
        self.snooze_btn.clicked.connect(self.show_snooze_options)
        
        # 添加所有元素到任务布局
        task_layout.addLayout(task_info)
        task_layout.addLayout(time_layout)
        task_layout.addSpacing(10)
        task_layout.addLayout(button_layout)
        
        # 组装主布局
        content_layout.addWidget(title_bar)
        content_layout.addWidget(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # 设置主布局
        layout.addWidget(content_container)
        layout.setContentsMargins(10, 10, 10, 10)  # 为阴影留出空间
    
    def show_reminder(self, task_id, task_text, due_time):
        """显示提醒窗口"""
        self.current_task_id = task_id
        self.task_text.setText(task_text)
        self.time_label.setText(f"计划时间: {due_time.strftime('%H:%M')}")
        
        # 设置窗口位置在屏幕右下角
        screen_geometry = QtWidgets.QApplication.desktop().availableGeometry()
        x = screen_geometry.width() - self.width() - 20
        y = screen_geometry.height() - self.height() - 20
        self.move(x, y)
        
        # 显示窗口并启动动画
        self.show()
        self.animation.setDirection(QPropertyAnimation.Forward)
        self.animation.start()
        
        # 设置自动关闭计时器 (30秒后自动关闭)
        self.auto_close_timer.start(30000)
    
    def start_fade_out(self):
        """开始淡出动画"""
        self.animation.setDirection(QPropertyAnimation.Backward)
        self.animation.finished.connect(self.close)
        self.animation.start()
    
    def complete_task(self):
        """标记任务为已完成"""
        if self.current_task_id:
            self.task_completed.emit(self.current_task_id)
        self.start_fade_out()
    
    def show_snooze_options(self):
        """显示稍后提醒选项"""
        if not self.current_task_id:
            return
            
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #dadce0;
                border-radius: 8px;
                padding: 5px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
            }
        """)
        
        # 添加时间选项
        times = [
            ("5分钟后", 5),
            ("10分钟后", 10),
            ("30分钟后", 30),
            ("1小时后", 60),
            ("2小时后", 120),
            ("明天", 24 * 60)
        ]
        
        for label, minutes in times:
            action = menu.addAction(label)
            action.triggered.connect(lambda checked, m=minutes: self.snooze(m))
        
        # 显示菜单
        menu.exec_(self.snooze_btn.mapToGlobal(QtCore.QPoint(0, self.snooze_btn.height())))
    
    def snooze(self, minutes):
        """稍后提醒"""
        if self.current_task_id:
            self.snooze_requested.emit(self.current_task_id, minutes)
        self.start_fade_out()
    
    def dismiss(self):
        """关闭提醒"""
        self.auto_close_timer.stop()
        self.dismissed.emit()
        self.start_fade_out()
    
    def paintEvent(self, event):
        """绘制阴影效果"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 定义阴影颜色和形状
        shadowColor = QtGui.QColor(0, 0, 0, 30)
        
        # 绘制圆角矩形阴影
        path = QtGui.QPainterPath()
        rect = QtCore.QRectF(10, 10, self.width() - 20, self.height() - 20)
        path.addRoundedRect(rect, 10, 10)
        
        # 设置阴影
        for i in range(10):
            shadow_path = QtGui.QPainterPath()
            shadow_rect = rect.adjusted(-i, -i, i, i)
            shadow_path.addRoundedRect(shadow_rect, 10+i/2, 10+i/2)
            color = QtGui.QColor(shadowColor)
            color.setAlpha(max(0, 30 - i*3))
            painter.setPen(QtGui.QPen(color, 1))
            painter.drawPath(shadow_path)
    
    def mousePressEvent(self, event):
        """处理鼠标按下事件，用于窗口拖动"""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.pressing = True
    
    def mouseMoveEvent(self, event):
        """处理鼠标移动事件，用于窗口拖动"""
        if self.pressing and (event.buttons() == Qt.LeftButton):
            delta = QtCore.QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
    
    def mouseReleaseEvent(self, event):
        """处理鼠标释放事件，用于窗口拖动"""
        if event.button() == Qt.LeftButton:
            self.pressing = False