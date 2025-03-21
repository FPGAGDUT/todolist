import sys
import os
import time  # 添加这一行
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QTimer, QPoint
from datetime import datetime
from .reminders import Reminder
from .floatingButton import FloatingButton
from .network_manager import NetworkManager
from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject
import threading
from ..ai.nlp_parser import NLPTaskParser
from ..ai.llm_parser import LLMTaskParser

# 开启代理
os.environ["http_proxy"] = "http://127.0.0.1:10808"
os.environ["https_proxy"] = "http://127.0.0.1:10808"

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

class TodoApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能 Todo 助手")
        self.setMinimumSize(400, 600)
        # 设置为无边框窗口
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # 添加阴影效果
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.threadpool = QThreadPool()

        # 初始化网络管理器 - 修改为本地优先模式
        self.network_manager = NetworkManager(
            base_url="http://localhost:8083/v1", 
            api_key="your-api-key",
            local_first=True  # 添加本地优先标志
        )

        api_key = os.environ.get("DEEPSEEK_API_KEY", "")  # 从环境变量获取API密钥
        print(f"API Key: {api_key}")
        self.llm_parser = LLMTaskParser(api_key=api_key)
        
        # 初始化提醒系统
        self.reminder = Reminder()
        self.reminder.start()
        
        # 设置拖动相关变量
        self.oldPos = self.pos()
        self.pressing = False
        
        # 设置应用样式
        self.apply_styles()
        
        # 初始化 UI
        self.init_ui()
        
        # 设置系统托盘
        self.setup_tray_icon()
        self.floating_button = FloatingButton(self)

        

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
            QWidget#central_widget {
                background-color: #f8f9fa;
                border-radius: 10px;
                border: 1px solid #ced4da;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#main_frame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e9ecef;
            }
            QLabel#header_label {
                font-size: 20px;  /* 稍微减小标题大小 */
                font-weight: bold;
                color: #343a40;
                margin: 0;  /* 移除默认边距 */
            }
            QLabel#date_label {
                font-size: 12px;  /* 减小日期字体大小 */
                color: #6c757d;
                margin: 0;  /* 移除默认边距 */
        }
            QPushButton#add_btn {
                background-color: #007bff;
                color: white;
                border-radius: 18px;
                min-height: 36px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton#add_btn:hover {
                background-color: #0069d9;
            }
            QPushButton#minimize_btn {
                background-color: transparent;
                border-radius: 15px;
                padding: 5px;
            }
            QPushButton#minimize_btn:hover {
                background-color: #e9ecef;
            }
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 8px 12px;
                background-color: white;
                selection-background-color: #007bff;
                min-height: 36px;
            }
            QLineEdit:focus {
                border: 2px solid #80bdff;
                outline: none;
            }
            QComboBox {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 8px 12px;
                background-color: white;
                min-height: 36px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QPushButton#category_btn {
                background-color: #6c757d;
                color: white;
                border-radius: 3px;
                padding: 3px 8px;
            }
            QPushButton#category_btn:hover {
                background-color: #5a6268;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #adb5bd;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6c757d;
            }
            QCheckBox {
                spacing: 6px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid #ced4da;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
                border: 1px solid #28a745;
            }
            QStatusBar {
                background-color: #f8f9fa;
                color: #6c757d;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)

    def show_task_breakdown(self, task_text):
        """显示任务拆分对话框"""
        # 先尝试拆分任务
        breakdown = self.llm_parser.break_down_complex_task(task_text)
        
        if not breakdown.get("subtasks"):
            return False  # 没有拆分出子任务，不显示对话框
        
        # 创建对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("任务拆分")
        dialog.setMinimumSize(400, 300)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # 显示主任务
        main_task_label = QtWidgets.QLabel(f"<b>{breakdown.get('main_task', task_text)}</b>")
        layout.addWidget(main_task_label)
        
        # 显示子任务列表
        subtasks_group = QtWidgets.QGroupBox("子任务列表")
        subtasks_layout = QtWidgets.QVBoxLayout(subtasks_group)
        
        checkboxes = []
        for subtask in breakdown.get("subtasks", []):
            checkbox = QtWidgets.QCheckBox(subtask)
            checkboxes.append(checkbox)
            subtasks_layout.addWidget(checkbox)
        
        layout.addWidget(subtasks_group)
        
        # 添加按钮
        button_layout = QtWidgets.QHBoxLayout()
        cancel_btn = QtWidgets.QPushButton("取消")
        add_btn = QtWidgets.QPushButton("添加所选子任务")
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        def add_selected_tasks():
            for i, checkbox in enumerate(checkboxes):
                if checkbox.isChecked():
                    subtask_text = breakdown["subtasks"][i]
                    # 解析子任务
                    task_data = self.llm_parser.parse(subtask_text)
                    # 创建子任务
                    self.create_task_item(
                        task_data["text"],
                        task_data["category"],
                        False,
                        f"temp_{int(time.time()*1000)}_{i}"
                    )
            dialog.accept()
        
        add_btn.clicked.connect(add_selected_tasks)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
        return True
    
    def show_task_suggestions(self, task_text):
        """显示任务建议对话框"""
        # 获取现有任务文本列表
        existing_tasks = []
        for i in range(self.task_list_layout.count()):
            widget = self.task_list_layout.itemAt(i).widget()
            if widget:
                checkbox = widget.findChild(QtWidgets.QCheckBox)
                if checkbox:
                    existing_tasks.append(checkbox.text())
        
        # 获取任务建议
        suggestions = self.llm_parser.suggest_related_tasks(task_text, existing_tasks)
        
        if not suggestions:
            return False  # 没有建议，不显示对话框
        
        # 创建对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("相关任务建议")
        dialog.setMinimumSize(400, 250)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        info_label = QtWidgets.QLabel(f"基于'{task_text}'，系统为您提供以下相关任务建议:")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 建议列表
        suggestions_group = QtWidgets.QGroupBox("您可能还需要:")
        suggestions_layout = QtWidgets.QVBoxLayout(suggestions_group)
        
        checkboxes = []
        for suggestion in suggestions:
            checkbox = QtWidgets.QCheckBox(suggestion.get("task", ""))
            checkbox.setToolTip(f"类别: {suggestion.get('category', '其他')}")
            checkboxes.append(checkbox)
            suggestions_layout.addWidget(checkbox)
        
        layout.addWidget(suggestions_group)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        dismiss_btn = QtWidgets.QPushButton("关闭")
        add_btn = QtWidgets.QPushButton("添加所选建议")
        
        button_layout.addWidget(dismiss_btn)
        button_layout.addStretch()
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        def add_selected_suggestions():
            for i, checkbox in enumerate(checkboxes):
                if checkbox.isChecked():
                    suggestion = suggestions[i]
                    # 创建建议的任务
                    self.create_task_item(
                        suggestion.get("task", ""),
                        suggestion.get("category", "其他"),
                        False,
                        f"temp_{int(time.time()*1000)}_s{i}"
                    )
            dialog.accept()
        
        add_btn.clicked.connect(add_selected_suggestions)
        dismiss_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
        return True
        

    def init_ui(self):
        # 创建中央部件，带有阴影效果
        central_widget = QtWidgets.QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        # main_layout.setContentsMargins(10, 10, 10, 10)  # 留出阴影空间
        main_layout.setContentsMargins(0, 0, 0, 0)  # 留出阴影空间

        main_layout.setSpacing(0)
        
        # 创建主框架
        main_frame = QtWidgets.QFrame()
        main_frame.setObjectName("main_frame")
        main_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        
        # frame_layout = QtWidgets.QVBoxLayout(main_frame)
        # frame_layout.setContentsMargins(20, 20, 20, 20)
        
        # 头部区域
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)  # 减少内边距
        header_layout.setSpacing(5)  # 减少间距
        
        # 标题和日期
        title_date_layout = QtWidgets.QVBoxLayout()
        title_date_layout.setContentsMargins(0, 0, 0, 0)  # 减少内边距
        title_date_layout.setSpacing(0)  # 减少标题和日期间的间距
        
        header_label = QtWidgets.QLabel("我的待办事项")
        header_label.setObjectName("header_label")
        
        date_label = QtWidgets.QLabel(datetime.now().strftime("%Y年%m月%d日 %A"))
        date_label.setObjectName("date_label")
        
        title_date_layout.addWidget(header_label)
        title_date_layout.addWidget(date_label)
        
        # 头部右侧布局改为水平布局
        header_right_layout = QtWidgets.QHBoxLayout()
        header_right_layout.setContentsMargins(0, 0, 0, 0)
        header_right_layout.setSpacing(10)  # 图标之间的间距
        
        # 创建最小化按钮
        minimize_btn = QtWidgets.QPushButton()
        minimize_btn.setObjectName("minimize_btn")
        minimize_btn.setFixedSize(28, 28)
        minimize_btn.setToolTip("最小化到托盘")
        
        # 加载SVG图标
        svg_path = "e:\\document\\MyOwn\\project\\tools\\todo\\ai-todolist\\icon\\最小化.svg"
        if os.path.exists(svg_path):
            icon = QtGui.QIcon(svg_path)
            minimize_btn.setIcon(icon)
            minimize_btn.setIconSize(QtCore.QSize(16, 16))
        else:
            minimize_btn.setText("—")
        
        minimize_btn.clicked.connect(self.hide)
        
        # 头部右侧图标
        icon_label = QtWidgets.QLabel()
        icon_pixmap = QtGui.QPixmap(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogDetailedView).pixmap(28, 28))  # 稍微缩小图标
        icon_label.setPixmap(icon_pixmap)
        
        # 将按钮和图标添加到同一水平布局
        header_right_layout.addWidget(icon_label)
        header_right_layout.addWidget(minimize_btn)
        
        # 将所有布局添加到头部区域
        header_layout.addLayout(title_date_layout)
        header_layout.addStretch()
        header_layout.addLayout(header_right_layout)
        
        # 修改主框架的内边距以减少垂直空间
        frame_layout = QtWidgets.QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(15, 10, 15, 15)  # 减少上下内边距
        frame_layout.setSpacing(8)  # 减少组件间距
        
        frame_layout.addLayout(header_layout)
        
        # 分隔线
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setStyleSheet("background-color: #e9ecef; margin: 5px 0;")  # 减小margin
        frame_layout.addWidget(line)
        
        # 输入区域
        input_layout = QtWidgets.QHBoxLayout()
        
        self.task_input = QtWidgets.QLineEdit()
        self.task_input.setPlaceholderText("输入你的需求...")
        
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItem("自动")  # 添加自动选项
        self.category_combo.addItems(["工作", "生活", "学习", "其他"])
        self.category_combo.setFixedWidth(90)
        
        
        add_btn = QtWidgets.QPushButton("添加")
        add_btn.setObjectName("add_btn")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self.add_task)
        
        input_layout.addWidget(self.task_input)
        input_layout.addWidget(self.category_combo)
        input_layout.addWidget(add_btn)
        
        frame_layout.addLayout(input_layout)
        
        # 过滤器
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.setContentsMargins(0, 0, 0, 0)
        filter_layout.setSpacing(5)  # 减少间距
        
        filter_label = QtWidgets.QLabel("筛选:")
        filter_label.setStyleSheet("color: #495057;")
        
        self.filter_all = QtWidgets.QPushButton("全部")
        self.filter_all.setObjectName("category_btn")
        self.filter_all.setCheckable(True)
        self.filter_all.setChecked(True)
        
        self.filter_work = QtWidgets.QPushButton("工作")
        self.filter_work.setObjectName("category_btn")
        self.filter_work.setCheckable(True)
        
        self.filter_life = QtWidgets.QPushButton("生活")
        self.filter_life.setObjectName("category_btn")
        self.filter_life.setCheckable(True)
        
        self.filter_study = QtWidgets.QPushButton("学习")
        self.filter_study.setObjectName("category_btn")
        self.filter_study.setCheckable(True)

        # 状态信息区域（替代状态栏）
        # self.status_layout = QtWidgets.QHBoxLayout()
        # self.status_layout.setContentsMargins(0, 5, 0, 0)

        # self.status_label = QtWidgets.QLabel("准备就绪 | 今日待办: 0 | 已完成: 0")
        # self.status_label.setStyleSheet("""
        #     color: #6c757d;
        #     font-size: 12px;
        #     padding: 5px 0;
        # """)

        # self.status_layout.addWidget(self.status_label)
        # self.status_layout.addStretch()

        # frame_layout.addLayout(self.status_layout)

        self.filter_all.clicked.connect(lambda: self.filter_tasks("全部"))
        self.filter_work.clicked.connect(lambda: self.filter_tasks("工作"))
        self.filter_life.clicked.connect(lambda: self.filter_tasks("生活"))
        self.filter_study.clicked.connect(lambda: self.filter_tasks("学习"))

        self.filter_btn_group = QtWidgets.QButtonGroup(self)
        self.filter_btn_group.addButton(self.filter_all)
        self.filter_btn_group.addButton(self.filter_work)
        self.filter_btn_group.addButton(self.filter_life)
        self.filter_btn_group.addButton(self.filter_study)
        self.filter_btn_group.setExclusive(True)  # 设置按钮组为互斥
        
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_all)
        filter_layout.addWidget(self.filter_work)
        filter_layout.addWidget(self.filter_life)
        filter_layout.addWidget(self.filter_study)
        filter_layout.addStretch()
        
        frame_layout.addLayout(filter_layout)
        
        # 任务列表区域
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        self.task_list_widget = QtWidgets.QWidget()
        self.task_list_layout = QtWidgets.QVBoxLayout(self.task_list_widget)
        self.task_list_layout.setAlignment(Qt.AlignTop)
        self.task_list_layout.setContentsMargins(0, 5, 0, 5)  # 减少上下内边距
        self.task_list_layout.setSpacing(6)  # 减少任务项目间距
        
        self.scroll_area.setWidget(self.task_list_widget)
        frame_layout.addWidget(self.scroll_area)

        # 状态信息区域（替代状态栏）
        self.status_layout = QtWidgets.QHBoxLayout()
        self.status_layout.setContentsMargins(0, 8, 0, 0)  # 增加一点顶部边距

        self.status_label = QtWidgets.QLabel("准备就绪 | 今日待办: 0 | 已完成: 0")
        self.status_label.setStyleSheet("""
            color: #6c757d;
            font-size: 12px;
            padding: 5px 0;
            border-top: 1px solid #e9ecef;  /* 添加上边框，增强视觉分隔 */
        """)

        self.status_layout.addWidget(self.status_label)
        self.status_layout.addStretch()

        frame_layout.addLayout(self.status_layout)
        
        # 添加主框架到主布局
        main_layout.addWidget(main_frame)
        
        # 状态栏
        # self.statusBar().showMessage("准备就绪 | 今日待办: 0 | 已完成: 0")
        
        # 添加示例任务
        # self.add_sample_tasks()
        self.load_tasks()
        
        # 连接回车键
        self.task_input.returnPressed.connect(self.add_task)
        
        # 更新日期时间
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_date)
        self.timer.start(60000)  # 每分钟更新一次

        # 添加连接状态指示器到状态栏
        connection_layout = QtWidgets.QHBoxLayout()
        
        self.connection_status = QtWidgets.QLabel("在线")
        self.connection_status.setStyleSheet("""
            color: #28a745;
            font-size: 12px;
            padding: 2px 8px;
            border: 1px solid #28a745;
            border-radius: 10px;
        """)
        
        self.sync_btn = QtWidgets.QPushButton("同步")
        self.sync_btn.setFixedSize(60, 24)
        self.sync_btn.clicked.connect(self.force_sync)
        self.sync_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
        """)
        
        connection_layout.addWidget(self.connection_status)
        connection_layout.addWidget(self.sync_btn)
        
        # 添加到状态布局或其他适当位置
        self.status_layout.addStretch()
        self.status_layout.addLayout(connection_layout)
        
        # 启动定时器定期更新连接状态
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.update_connection_status)
        self.connection_timer.start(5000)  # 每5秒更新一次

    def show_smart_input(self):
        """显示智能输入对话框"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("智能任务输入")
        dialog.setMinimumSize(500, 350)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # 添加说明标签
        info_label = QtWidgets.QLabel("请用自然语言描述您的任务，例如：")
        info_label.setStyleSheet("color: #6c757d;")
        
        examples_label = QtWidgets.QLabel(
            "• 明天下午3点开项目会议\n"
            "• 周五前完成季度报告\n"
            "• 下周一早上9点健身"
        )
        examples_label.setStyleSheet("color: #6c757d; background-color: #f8f9fa; padding: 10px; border-radius: 5px;")
        
        # 输入文本框
        text_edit = QtWidgets.QTextEdit()
        text_edit.setPlaceholderText("在此输入任务描述...")
        text_edit.setMinimumHeight(100)
        
        # 解析结果预览
        preview_group = QtWidgets.QGroupBox("解析结果预览")
        preview_layout = QtWidgets.QFormLayout(preview_group)
        
        task_preview = QtWidgets.QLabel("任务内容将在这里显示")
        category_preview = QtWidgets.QLabel("待定")
        date_preview = QtWidgets.QLabel("无")
        time_preview = QtWidgets.QLabel("无")
        priority_preview = QtWidgets.QLabel("正常")
        
        preview_layout.addRow("任务内容:", task_preview)
        preview_layout.addRow("分类:", category_preview)
        preview_layout.addRow("日期:", date_preview)
        preview_layout.addRow("时间:", time_preview)
        preview_layout.addRow("优先级:", priority_preview)
        
        # 按钮
        button_layout = QtWidgets.QHBoxLayout()
        
        parse_btn = QtWidgets.QPushButton("解析")
        parse_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        
        add_btn = QtWidgets.QPushButton("添加任务")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.setEnabled(False)  # 初始禁用，直到解析完成
        
        cancel_btn = QtWidgets.QPushButton("取消")
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(parse_btn)
        button_layout.addWidget(add_btn)
        
        # 添加所有组件到主布局
        layout.addWidget(info_label)
        layout.addWidget(examples_label)
        layout.addWidget(text_edit)
        layout.addWidget(preview_group)
        layout.addLayout(button_layout)
        
        # 解析的任务数据
        task_data = {}
        
        # 连接按钮信号
        def parse_text():
            nonlocal task_data
            input_text = text_edit.toPlainText().strip()
            if not input_text:
                return
                
            # 解析文本
            task_data = self.nlp_parser.parse(input_text)
            
            # 更新预览
            task_preview.setText(task_data["text"])
            category_preview.setText(task_data["category"])
            
            if task_data["due_date"]:
                date_preview.setText(task_data["due_date"].strftime("%Y年%m月%d日"))
            else:
                date_preview.setText("无")
                
            if task_data["due_time"]:
                time_preview.setText(task_data["due_time"].strftime("%H:%M"))
            else:
                time_preview.setText("无")
                
            priority_preview.setText(task_data["priority"])
            
            # 启用添加按钮
            add_btn.setEnabled(True)
        
        def add_parsed_task():
            nonlocal task_data
            if task_data:
                # 创建任务
                self.create_task_item(
                    task_data["text"],
                    task_data["category"],
                    False,
                    f"temp_{int(time.time()*1000)}"
                )
                
                # 如果有日期和时间，设置提醒
                if task_data["due_date"] and task_data["due_time"]:
                    due_datetime = datetime.datetime.combine(
                        task_data["due_date"], 
                        task_data["due_time"]
                    )
                    # 添加提醒代码 (需要实现)
                
                dialog.accept()
        
        parse_btn.clicked.connect(parse_text)
        add_btn.clicked.connect(add_parsed_task)
        cancel_btn.clicked.connect(dialog.reject)
        
        # 实时解析 (可选)
        text_edit.textChanged.connect(lambda: QtCore.QTimer.singleShot(500, parse_text))
        
        dialog.exec_()

    # 添加更新连接状态的方法
    def update_connection_status(self):
        """更新连接状态显示"""
        status = self.network_manager.get_connection_status()
        
        if status["online"]:
            if status["syncing"]:
                self.connection_status.setText("同步中")
                self.connection_status.setStyleSheet("""
                    color: #007bff;
                    font-size: 12px;
                    padding: 2px 8px;
                    border: 1px solid #007bff;
                    border-radius: 10px;
                """)
            else:
                self.connection_status.setText("在线")
                self.connection_status.setStyleSheet("""
                    color: #28a745;
                    font-size: 12px;
                    padding: 2px 8px;
                    border: 1px solid #28a745;
                    border-radius: 10px;
                """)
        else:
            self.connection_status.setText("离线")
            self.connection_status.setStyleSheet("""
                color: #dc3545;
                font-size: 12px;
                padding: 2px 8px;
                border: 1px solid #dc3545;
                border-radius: 10px;
            """)
        
        # 根据是否有待同步操作更新同步按钮状态
        if status["pending_operations"] > 0 and status["online"]:
            self.sync_btn.setEnabled(True)
            self.sync_btn.setText(f"同步({status['pending_operations']})")
        else:
            self.sync_btn.setEnabled(False)
            self.sync_btn.setText("同步")

    def force_sync(self):
        """强制同步数据"""
        result = self.network_manager.force_sync()
        if result["success"]:
            QtWidgets.QMessageBox.information(self, "同步", "数据同步已开始")
        else:
            QtWidgets.QMessageBox.warning(self, "同步失败", result["error"])


    def filter_tasks(self, category):
        """根据分类筛选任务"""
        total_visible = 0
        completed_visible = 0
        
        # 遍历所有任务项
        for i in range(self.task_list_layout.count()):
            item = self.task_list_layout.itemAt(i).widget()
            if item:
                # 获取任务项的分类
                item_category = item.property("category")
                
                # 如果选择"全部"或分类匹配，则显示
                if category == "全部" or item_category == category:
                    item.setVisible(True)
                    total_visible += 1
                    
                    # 检查是否已完成
                    checkbox = item.layout().itemAt(0).widget()
                    if checkbox.isChecked():
                        completed_visible += 1
                else:
                    item.setVisible(False)
        
        # 更新状态栏显示筛选后的统计信息
        if category == "全部":
            self.status_label.setText(f"准备就绪 | 今日待办: {total_visible} | 已完成: {completed_visible}")
        else:
            self.status_label.setText(f"筛选: {category} | 待办: {total_visible} | 已完成: {completed_visible}")
            
        # 确保选中对应的筛选按钮
        if category == "全部":
            self.filter_all.setChecked(True)
        elif category == "工作":
            self.filter_work.setChecked(True)
        elif category == "生活":
            self.filter_life.setChecked(True)
        elif category == "学习":
            self.filter_study.setChecked(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self.pressing = True

    def mouseMoveEvent(self, event):
        if self.pressing and (event.buttons() == Qt.LeftButton):
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pressing = False

    def setup_tray_icon(self):
        # 创建系统托盘图标
        icon = QtGui.QIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogDetailedView))
        
        self.tray_icon = QtWidgets.QSystemTrayIcon(icon, self)
        
        # 创建托盘菜单
        tray_menu = QtWidgets.QMenu()
        
        show_action = tray_menu.addAction("显示")
        show_action.triggered.connect(self.show)
        
        add_task_action = tray_menu.addAction("快速添加")
        add_task_action.triggered.connect(self.quick_add_task)
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("退出")
        exit_action.triggered.connect(self.safe_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def hide(self):
        """重写hide方法，在隐藏主窗口时显示浮窗"""
        super().hide()
        self.floating_button.show()
    
    def show(self):
        """重写show方法，在显示主窗口时隐藏浮窗"""
        self.floating_button.hide()
        super().show()

    def quick_add_task(self):
        task_text, ok = QtWidgets.QInputDialog.getText(None, "快速添加任务", "输入新任务:")
        if ok and task_text:
            self.create_task_item(task_text, "工作")

    def add_sample_tasks(self):
        tasks = [
            ("完成项目文档", "工作", False),
            ("准备团队会议", "工作", True),
            ("健身锻炼", "生活", False),
            ("学习Python高级特性", "学习", False)
        ]
        
        for text, category, completed in tasks:
            self.create_task_item(text, category, completed)
        
        self.update_status()

    def create_task_item(self, text, category, completed=False, task_id=None):
        # 创建任务容器
        task_widget = QtWidgets.QFrame()
        task_widget.setProperty("category", category)
        task_widget.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 6px;
                border: 1px solid #dee2e6;
                padding: 5px;
            }
            QFrame:hover {
                border: 1px solid #adb5bd;
                background-color: #f8f9fa;
            }
        """)
        
        # 任务布局
        task_layout = QtWidgets.QHBoxLayout(task_widget)
        task_layout.setContentsMargins(8, 3, 8, 3)  # 减少内边距使任务项更紧凑
        task_layout.setSpacing(5)  # 减少组件间距
        task_widget.setProperty("task_id", task_id)
        # 复选框
        checkbox = QtWidgets.QCheckBox(text)
        checkbox.setChecked(completed)
        if completed:
            checkbox.setStyleSheet("QCheckBox { color: #6c757d; text-decoration: line-through; }")
        
        # 连接状态改变事件
        checkbox.stateChanged.connect(lambda state, cb=checkbox: self.task_state_changed(cb, task_widget))
        
        # 分类标签
        category_label = QtWidgets.QLabel(category)
        category_label.setAlignment(Qt.AlignCenter)
        category_label.setFixedWidth(50)
        
        # 设置不同分类的颜色
        if category == "工作":
            bg_color = "#007bff"
        elif category == "生活":
            bg_color = "#28a745"
        elif category == "学习":
            bg_color = "#fd7e14"
        else:
            bg_color = "#6c757d"
            
        category_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                border-radius: 3px;
                padding: 2px 5px;
                font-size: 12px;
            }}
        """)
        
        # 删除按钮
        delete_btn = QtWidgets.QPushButton("×")
        delete_btn.setFixedSize(25, 25)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                color: #dc3545;
                border: none;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        
        # 连接删除按钮点击事件
        delete_btn.clicked.connect(lambda: self.delete_task(task_widget))
        
        # 添加组件到布局
        task_layout.addWidget(checkbox, 1)
        task_layout.addWidget(category_label)
        task_layout.addWidget(delete_btn)
        
        # 添加任务项到任务列表
        self.task_list_layout.addWidget(task_widget)

        # 获取当前选中的筛选按钮
        current_filter = "全部"
        for btn in [self.filter_all, self.filter_work, self.filter_life, self.filter_study]:
            if btn.isChecked():
                current_filter = btn.text()
                break
        
        # 如果当前筛选不是"全部"且与新任务分类不匹配，则隐藏该任务
        if current_filter != "全部" and current_filter != category:
            task_widget.setVisible(False)
        
        # 更新状态栏
        self.update_status()

    def task_state_changed(self, checkbox, task_widget):
        """当任务状态改变时调用"""
        # 更新UI显示
        if checkbox.isChecked():
            checkbox.setStyleSheet("QCheckBox { color: #6c757d; text-decoration: line-through; }")
        else:
            checkbox.setStyleSheet("QCheckBox { color: #212529; text-decoration: none; }")
        
        self.update_status()
        
        # 确保我们有任务ID
        task_id = task_widget.property("task_id")
        if task_id:
            # 使用直接更新方法(而非批量操作)
            worker = Worker(
                self.network_manager.update_task_direct, 
                task_id, 
                {"completed": checkbox.isChecked()}
            )
            worker.signals.finished.connect(self.handle_task_update_result)
            self.threadpool.start(worker)

    # 添加处理任务更新结果的方法
    def handle_task_update_result(self, result):
        """处理任务更新结果"""
        if not result.get("success"):
            print(f"任务更新失败: {result.get('error')}")
            # 可以在这里添加UI通知

    # 修改delete_task方法
    def delete_task(self, task_widget):
        # 先从UI中删除
        task_id = task_widget.property("task_id")
        task_widget.deleteLater()
        QtCore.QTimer.singleShot(10, self.update_status)
        
        # 如果有任务ID，在线程池中删除
        if task_id:
            worker = Worker(self.network_manager.delete_task, task_id)
            self.threadpool.start(worker)

    def _show_task_insights(self, task_text):
        """显示任务相关的洞察（拆分或建议）"""
        # 首先尝试显示任务拆分
        if len(task_text) > 10:  # 仅对较长的任务尝试拆分
            if "," in task_text or "，" in task_text or len(task_text) > 15:
                # 长任务或包含逗号的任务可能需要拆分
                breakdown_shown = self.show_task_breakdown(task_text)
                if breakdown_shown:
                    return
        
        # 如果没有显示拆分，尝试显示建议
        self.show_task_suggestions(task_text)

    # 修改add_task方法使用线程池
    def add_task(self):
        """添加新任务，支持自然语言输入和智能解析"""
        # 获取任务文本并检查是否为空
        text = self.task_input.text().strip()
        if not text:
            return
        
        # 获取用户选择的分类
        category = self.category_combo.currentText()
        selected_category = category
        
        # 生成临时ID用于任务追踪
        task_id = f"temp_{int(time.time()*1000)}"
        
        # 初始化任务数据结构
        task_data = {
            "text": text,
            "category": category, 
            "completed": False,
            "due_date": None,
            "due_time": None,
            "priority": "正常",
            "subtasks": []
        }
        
        # 第一阶段：自然语言解析
        try:
            # 优先使用大模型解析(如果可用)
            if hasattr(self, 'llm_parser') and self.llm_parser:
                try:
                    parsed_data = self.llm_parser.parse(text)
                    if not parsed_data.get("text"):  # 如果大模型解析结果为空
                        raise ValueError("大模型解析结果为空")
                except Exception as e:
                    print(f"大模型解析错误，回退到基本NLP: {str(e)}")
                    parsed_data = self.nlp_parser.parse(text)
            else:
                # 使用基本NLP解析
                parsed_data = self.nlp_parser.parse(text)
                
            # 更新任务内容
            task_data["text"] = parsed_data.get("text", text)
            task_data["due_date"] = parsed_data.get("due_date")
            task_data["due_time"] = parsed_data.get("due_time")
            task_data["priority"] = parsed_data.get("priority", "正常")
            
            # 如果解析出了子任务，保存它们
            if "subtasks" in parsed_data and parsed_data["subtasks"]:
                task_data["subtasks"] = parsed_data["subtasks"]
            
            # 如果选择了"自动"分类，使用解析出的分类
            if category == "自动":
                selected_category = parsed_data.get("category", "其他")
                task_data["category"] = selected_category
                
            # 显示工具提示，告知用户解析结果
            if parsed_data.get("due_date") or parsed_data.get("due_time") or category == "自动":
                date_str = "无" if not parsed_data.get("due_date") else parsed_data["due_date"].strftime("%m月%d日")
                time_str = "无" if not parsed_data.get("due_time") else parsed_data["due_time"].strftime("%H:%M")
                
                tooltip_text = f"已智能解析：{task_data['text']} | 类别：{selected_category}"
                
                if parsed_data.get("due_date") or parsed_data.get("due_time"):
                    tooltip_text += f" | 日期：{date_str} | 时间：{time_str}"
                    
                if parsed_data.get("priority") != "正常":
                    tooltip_text += f" | 优先级：{parsed_data['priority']}"
                    
                QtWidgets.QToolTip.showText(
                    self.task_input.mapToGlobal(QtCore.QPoint(0, -40)),
                    tooltip_text,
                    self.task_input,
                    QtCore.QRect(),
                    3000  # 提示显示3秒
                )
                    
        except Exception as e:
            print(f"自然语言解析错误: {str(e)}")
            # 解析失败时不做特殊处理，使用原始输入
        
        # 第二阶段：在UI中创建任务项
        self.create_task_item(
            task_data["text"], 
            selected_category, 
            False, 
            task_id
        )
        
        # 清空输入框并更新状态
        self.task_input.clear()
        self.update_status()
        
        # 第三阶段：异步保存任务到服务器
        save_data = {
            "text": task_data["text"],
            "category": selected_category,
            "completed": False
        }
        
        # 如果解析出了日期和时间，添加到保存数据中
        if task_data["due_date"]:
            save_data["due_date"] = task_data["due_date"].strftime("%Y-%m-%d")
        
        if task_data["due_time"]:
            save_data["due_time"] = task_data["due_time"].strftime("%H:%M")
        
        if task_data["priority"] != "正常":
            save_data["priority"] = task_data["priority"]
        
        # 使用工作线程创建任务
        worker = Worker(self.network_manager.create_task, save_data)
        
        # 设置任务创建完成后的回调
        def on_task_created(result):
            if result.get("success"):
                # 如果有日期和时间信息，设置提醒
                if task_data["due_date"] and task_data["due_time"]:
                    due_datetime = datetime.combine(task_data["due_date"], task_data["due_time"])
                    # 如果有提醒系统，添加提醒
                    if hasattr(self, 'reminder') and self.reminder:
                        try:
                            self.reminder.add_reminder(
                                task_id=task_id if task_id else result["data"].get("id"),
                                task_text=task_data["text"],
                                due_time=due_datetime
                            )
                        except Exception as e:
                            print(f"设置提醒失败: {str(e)}")
                
                # 第四阶段：尝试显示任务洞察(子任务或相关建议)
                if len(task_data.get("subtasks", [])) > 0:
                    # 如果已经解析出子任务，直接显示任务拆分对话框
                    QtCore.QTimer.singleShot(300, lambda: self.show_task_breakdown_from_data(
                        task_data["text"], task_data["subtasks"]
                    ))
                else:
                    # 否则，延迟尝试显示洞察
                    QtCore.QTimer.singleShot(300, lambda: self._show_task_insights(task_data["text"]))
            else:
                # 任务创建失败
                print(f"任务创建失败: {result.get('error')}")
        
        # 设置完成回调并启动工作线程
        worker.signals.finished.connect(on_task_created)
        self.threadpool.start(worker)

    def load_tasks(self):
        """从服务器加载任务"""
        result = self.network_manager.get_tasks()
        
        if not result["success"]:
            QtWidgets.QMessageBox.warning(
                self, 
                "网络错误", 
                f"无法加载任务: {result.get('error', '未知错误')}"
            )
            return
        
        # 清除现有任务显示
        while self.task_list_layout.count():
            widget = self.task_list_layout.itemAt(0).widget()
            if widget:
                self.task_list_layout.removeWidget(widget)
                widget.deleteLater()
        
        # 显示从服务器加载的任务
        tasks = result["data"].get("tasks", [])
        for task in tasks:
            self.create_task_item(
                task["text"],
                task["category"],
                task["completed"],
                task["id"]
            )
        
        # 更新状态
        self.update_status()

    def update_task_visibility(self, category):
        """更新任务可见性"""
        # 遍历所有任务项
        for i in range(self.task_list_layout.count()):
            item = self.task_list_layout.itemAt(i).widget()
            if item:
                # 获取任务项的分类
                item_category = item.property("category")
                
                # 如果选择"全部"或分类匹配，则显示
                if category == "全部" or item_category == category:
                    item.setVisible(True)
                else:
                    item.setVisible(False)

    def update_status(self):
        """更新状态栏信息"""
        # 获取当前选中的筛选按钮
        current_filter = "全部"
        for btn in [self.filter_all, self.filter_work, self.filter_life, self.filter_study]:
            if btn.isChecked():
                current_filter = btn.text()
                break
        
        # 统计可见任务
        total_visible = 0
        completed_visible = 0
        
        # 遍历所有任务项
        for i in range(self.task_list_layout.count()):
            item = self.task_list_layout.itemAt(i).widget()
            if item and isinstance(item, QtWidgets.QFrame):  # 确保是任务项
                item_category = item.property("category")
                
                # 根据过滤条件决定是否计入统计
                if current_filter == "全部" or item_category == current_filter:
                    total_visible += 1
                    
                    # 检查是否已完成
                    checkbox = item.layout().itemAt(0).widget()
                    if checkbox and checkbox.isChecked():
                        completed_visible += 1
        
        # 更新状态信息
        if current_filter == "全部":
            self.status_label.setText(f"准备就绪 | 今日待办: {total_visible} | 已完成: {completed_visible}")
        else:
            self.status_label.setText(f"筛选: {current_filter} | 待办: {total_visible} | 已完成: {completed_visible}")
        
        # 根据需要更新任务可见性
        self.update_task_visibility(current_filter)


    def show_task_breakdown_from_data(self, main_task, subtasks):
        """显示已解析的子任务列表"""
        if not subtasks:
            return False
        
        # 创建对话框
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("任务拆分")
        dialog.setMinimumSize(400, 300)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # 显示主任务
        main_task_label = QtWidgets.QLabel(f"<b>{main_task}</b>")
        layout.addWidget(main_task_label)
        
        # 显示子任务列表
        subtasks_group = QtWidgets.QGroupBox("子任务列表")
        subtasks_layout = QtWidgets.QVBoxLayout(subtasks_group)
        
        checkboxes = []
        for subtask in subtasks:
            checkbox = QtWidgets.QCheckBox(subtask)
            checkboxes.append(checkbox)
            subtasks_layout.addWidget(checkbox)
        
        layout.addWidget(subtasks_group)
        
        # 添加按钮
        button_layout = QtWidgets.QHBoxLayout()
        cancel_btn = QtWidgets.QPushButton("取消")
        add_btn = QtWidgets.QPushButton("添加所选子任务")
        
        button_layout.addWidget(cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        def add_selected_tasks():
            for i, checkbox in enumerate(checkboxes):
                if checkbox.isChecked():
                    subtask_text = subtasks[i]
                    # 尝试解析子任务
                    try:
                        if hasattr(self, 'llm_parser') and self.llm_parser:
                            task_data = self.llm_parser.parse(subtask_text)
                        else:
                            task_data = self.nlp_parser.parse(subtask_text)
                    except:
                        task_data = {"text": subtask_text, "category": "其他"}
                    
                    # 创建子任务
                    self.create_task_item(
                        task_data.get("text", subtask_text),
                        task_data.get("category", "其他"),
                        False,
                        f"temp_{int(time.time()*1000)}_{i}"
                    )
            dialog.accept()
        
        add_btn.clicked.connect(add_selected_tasks)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.exec_()
        return True


    def update_date(self):
        for i in range(self.centralWidget().layout().count()):
            item = self.centralWidget().layout().itemAt(i).widget()
            if item:
                for j in range(item.layout().count()):
                    sub_item = item.layout().itemAt(j)
                    if isinstance(sub_item, QtWidgets.QLayout):
                        for k in range(sub_item.count()):
                            widget = sub_item.itemAt(k).widget()
                            if isinstance(widget, QtWidgets.QLabel) and widget.objectName() == "date_label":
                                widget.setText(datetime.now().strftime("%Y年%m月%d日 %A"))

    # 修改 closeEvent 方法
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 询问用户是否想要退出
        reply = QtWidgets.QMessageBox.question(
            self, '确认退出', 
            '您确定要退出程序吗？',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            safe_exit_result = self.safe_exit()
            if not safe_exit_result:
                event.ignore()
                return
            
            event.accept()
        else:
            event.ignore()
            self.hide()  # 隐藏窗口而不是关闭应用

    def keyPressEvent(self, event):
        """捕获按键事件"""
        # 检查是否按下了ESC键
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()  # 隐藏窗口到系统托盘
        else:
            # 对于其他按键，使用默认处理方式
            super().keyPressEvent(event)

    # 添加阴影效果
    def paintEvent(self, event):
        # 绘制窗口阴影
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # 定义阴影颜色和形状
        shadowColor = QtGui.QColor(0, 0, 0, 30)
        
        # 绘制圆角矩形
        path = QtGui.QPainterPath()
        rect = QtCore.QRectF(10, 10, self.width()-20, self.height()-20)
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

    def safe_exit(self):
        """安全退出，确保所有数据已同步"""
        # 检查是否有待同步操作
        status = self.network_manager.get_connection_status()
        
        if status["pending_operations"] > 0:
            # 显示同步进度对话框
            progress_dialog = QtWidgets.QProgressDialog(
                "正在同步未保存的更改...", "取消", 0, 100, self)
            progress_dialog.setWindowTitle("正在同步")
            progress_dialog.setMinimumDuration(0)
            progress_dialog.setValue(0)
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setAutoClose(True)
            
            # 启动同步进度更新计时器
            progress_timer = QTimer(self)
            progress_value = [0]  # 使用列表作为可变对象
            
            def update_progress():
                """更新进度条"""
                current_status = self.network_manager.get_connection_status()
                if current_status["pending_operations"] == 0:
                    progress_dialog.setValue(100)
                    progress_timer.stop()
                    return
                
                # 增加进度值，模拟进度
                progress_value[0] += 5
                if progress_value[0] > 95:
                    progress_value[0] = 95
                progress_dialog.setValue(progress_value[0])
            
            progress_timer.timeout.connect(update_progress)
            progress_timer.start(200)  # 每200毫秒更新一次
            
            # 执行同步并等待
            def perform_sync():
                success = self.network_manager.sync_and_wait(timeout=15)
                progress_timer.stop()
                progress_dialog.setValue(100)
                return success
            
            # 在后台线程中执行同步
            sync_thread = threading.Thread(target=perform_sync)
            sync_thread.daemon = True
            sync_thread.start()
            
            # 显示对话框并处理结果
            result = progress_dialog.exec_()
            
            # 如果用户取消，询问是否仍要退出
            if result == QtWidgets.QProgressDialog.Rejected:
                reply = QtWidgets.QMessageBox.question(
                    self, '确认退出', 
                    '同步尚未完成，确定要退出吗？未同步的更改可能会丢失。',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.No:
                    return False  # 不退出
        
        # 执行退出
        QtWidgets.qApp.quit()
        return True

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出程序
    
    todo_app = TodoApp()
     # 从服务器或本地存储加载任务，而不是添加示例任务
    # todo_app.load_tasks()
    todo_app.show()

    app.aboutToQuit.connect(lambda: todo_app.network_manager.local_storage.save_data())
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()