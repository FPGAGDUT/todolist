from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QThreadPool, pyqtSignal, QPoint
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
from .worker import Worker



class RegisterWindow(QtWidgets.QDialog):
    """注册窗口"""
    register_successful = pyqtSignal(dict)  # 发送注册成功的信号及用户信息
    
    def __init__(self, network_manager):
        super().__init__()
        self.network_manager = network_manager
        self.threadpool = QThreadPool()
        self.setWindowTitle("注册新账户")
        self.setMinimumSize(400, 500)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        # 添加阴影效果
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化UI
        self.init_ui()
        
        # 设置拖动相关变量
        self.oldPos = self.pos()
        self.pressing = False
    
    def init_ui(self):
        # 创建主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建注册卡片
        register_card = QtWidgets.QFrame()
        register_card.setObjectName("register_card")
        register_card.setStyleSheet("""
            QFrame#register_card {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        card_layout = QtWidgets.QVBoxLayout(register_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # 头部标题
        header_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("创建新账户")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border-radius: 15px;
                font-size: 20px;
                color: #dc3545;
                border: none;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        card_layout.addLayout(header_layout)
        
        # 描述文字
        desc_label = QtWidgets.QLabel("填写以下信息创建您的账户")
        desc_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        card_layout.addWidget(desc_label)
        
        # 用户名输入
        username_layout = QtWidgets.QVBoxLayout()
        username_layout.setSpacing(5)
        
        username_label = QtWidgets.QLabel("用户名")
        username_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("选择一个用户名")
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 2px solid #80bdff;
                background-color: white;
            }
        """)
        self.username_input.setMinimumHeight(40)
        
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        
        card_layout.addLayout(username_layout)
        
        # 邮箱输入
        email_layout = QtWidgets.QVBoxLayout()
        email_layout.setSpacing(5)
        
        email_label = QtWidgets.QLabel("电子邮箱")
        email_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.email_input = QtWidgets.QLineEdit()
        self.email_input.setPlaceholderText("输入您的电子邮箱")
        self.email_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 2px solid #80bdff;
                background-color: white;
            }
        """)
        self.email_input.setMinimumHeight(40)
        
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        
        card_layout.addLayout(email_layout)
        
        # 密码输入
        password_layout = QtWidgets.QVBoxLayout()
        password_layout.setSpacing(5)
        
        password_label = QtWidgets.QLabel("密码")
        password_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("创建一个强密码")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 2px solid #80bdff;
                background-color: white;
            }
        """)
        self.password_input.setMinimumHeight(40)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        
        card_layout.addLayout(password_layout)
        
        # 确认密码
        confirm_layout = QtWidgets.QVBoxLayout()
        confirm_layout.setSpacing(5)
        
        confirm_label = QtWidgets.QLabel("确认密码")
        confirm_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.confirm_input = QtWidgets.QLineEdit()
        self.confirm_input.setPlaceholderText("再次输入密码")
        self.confirm_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 10px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border: 2px solid #80bdff;
                background-color: white;
            }
        """)
        self.confirm_input.setMinimumHeight(40)
        
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        
        card_layout.addLayout(confirm_layout)
        
        # 协议同意
        terms_layout = QtWidgets.QHBoxLayout()
        
        self.terms_check = QtWidgets.QCheckBox("我同意服务条款和隐私政策")
        self.terms_check.setStyleSheet("""
            QCheckBox {
                color: #6c757d;
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
        """)
        
        terms_layout.addWidget(self.terms_check)
        
        card_layout.addLayout(terms_layout)
        
        # 注册按钮
        self.register_btn = QtWidgets.QPushButton("创建账户")
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 5px;
                padding: 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.register_btn.setMinimumHeight(45)
        self.register_btn.clicked.connect(self.handle_register)
        
        card_layout.addWidget(self.register_btn)
        
        # 错误消息标签
        self.error_label = QtWidgets.QLabel("")
        self.error_label.setStyleSheet("color: #dc3545; margin-top: 10px;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.setVisible(False)
        
        card_layout.addWidget(self.error_label)
        
        # 分隔线
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator.setStyleSheet("background-color: #e9ecef; margin: 10px 0;")
        
        card_layout.addWidget(separator)
        
        # 返回登录区域
        login_back_layout = QtWidgets.QHBoxLayout()
        
        login_back_label = QtWidgets.QLabel("已有账户?")
        login_back_label.setStyleSheet("color: #6c757d;")
        
        login_back_btn = QtWidgets.QPushButton("返回登录")
        login_back_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #007bff;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #0056b3;
                text-decoration: underline;
            }
        """)
        login_back_btn.setCursor(Qt.PointingHandCursor)
        login_back_btn.clicked.connect(self.reject)
        
        login_back_layout.addWidget(login_back_label)
        login_back_layout.addWidget(login_back_btn)
        login_back_layout.setAlignment(Qt.AlignCenter)
        
        card_layout.addLayout(login_back_layout)
        
        # 添加卡片到主布局
        main_layout.addWidget(register_card)
        
        # 添加键盘事件
        self.confirm_input.returnPressed.connect(self.handle_register)
        self.password_input.returnPressed.connect(lambda: self.confirm_input.setFocus())
        self.email_input.returnPressed.connect(lambda: self.password_input.setFocus())
        self.username_input.returnPressed.connect(lambda: self.email_input.setFocus())
    
    def handle_register(self):
        """处理注册请求"""
        # 获取输入
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_input.text()
        
        # 基本验证
        if not username:
            self.show_error("请输入用户名")
            return
        
        if not email:
            self.show_error("请输入电子邮箱")
            return
        
        if not password:
            self.show_error("请输入密码")
            return
        
        if password != confirm_password:
            self.show_error("两次输入的密码不一致")
            return
        
        if len(password) < 8:
            self.show_error("密码长度至少为8个字符")
            return
        
        if not self.terms_check.isChecked():
            self.show_error("请同意服务条款和隐私政策")
            return
        
        # 禁用注册按钮防止重复点击
        self.register_btn.setEnabled(False)
        self.register_btn.setText("注册中...")
        
        # 清除错误消息
        self.error_label.setVisible(False)
        
        # 创建注册任务
        register_worker = Worker(
            self.network_manager.register, 
            username, 
            email, 
            password
        )
        
        # 设置回调
        register_worker.signals.finished.connect(self.handle_register_result)
        register_worker.signals.error.connect(lambda e: self.show_error(f"注册出错: {str(e)}"))
        
        # 启动任务
        self.threadpool.start(register_worker)
    
    def handle_register_result(self, result):
        """处理注册结果"""
        # 恢复注册按钮状态
        self.register_btn.setEnabled(True)
        self.register_btn.setText("创建账户")
        
        if result.get('success'):
            # 发送注册成功信号
            self.register_successful.emit(result.get('data', {}))
            
            # 关闭注册窗口
            self.accept()
        else:
            # 显示错误消息
            error_message = result.get('error', '注册失败，请重试')
            self.show_error(error_message)
    
    def show_error(self, message):
        """显示错误消息"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        
        # 恢复注册按钮状态
        self.register_btn.setEnabled(True)
        self.register_btn.setText("创建账户")
    
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
    
    def paintEvent(self, event):
        """绘制窗口阴影"""
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