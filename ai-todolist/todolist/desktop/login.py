from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt, QThreadPool, pyqtSignal
from PyQt5.QtGui import QPainter, QPainterPath
from PyQt5.QtWidgets import QMessageBox
from .worker import Worker
from .register import RegisterWindow


class LoginWindow(QtWidgets.QWidget):
    """登录窗口"""
    login_successful = pyqtSignal(dict)  # 发送登录成功的信号及用户信息
    
    def __init__(self, network_manager, parent=None):
        super().__init__(parent)
        self.network_manager = network_manager
        self.threadpool = QThreadPool()
        self.setWindowTitle("登录到智能 Todo 助手")
        self.setMinimumSize(400, 450)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
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
        
        # 创建登录卡片
        login_card = QtWidgets.QFrame()
        login_card.setObjectName("login_card")
        login_card.setStyleSheet("""
            QFrame#login_card {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        card_layout = QtWidgets.QVBoxLayout(login_card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(20)
        
        # 头部标题
        header_layout = QtWidgets.QHBoxLayout()
        title_label = QtWidgets.QLabel("欢迎回来")
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
        # close_btn.clicked.connect(self.close)
        # close_btn.clicked.connect(QtWidgets.QApplication.quit)  # 直接退出应用
        close_btn.clicked.connect(self.handle_user_close)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        card_layout.addLayout(header_layout)
        
        # 描述文字
        desc_label = QtWidgets.QLabel("登录您的账户以同步您的任务")
        desc_label.setStyleSheet("color: #6c757d; margin-bottom: 15px;")
        card_layout.addWidget(desc_label)
        
        # 用户名输入
        username_layout = QtWidgets.QVBoxLayout()
        username_layout.setSpacing(5)
        
        username_label = QtWidgets.QLabel("用户名")
        username_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("输入您的用户名")
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
        
        # 密码输入
        password_layout = QtWidgets.QVBoxLayout()
        password_layout.setSpacing(5)
        
        password_label = QtWidgets.QLabel("密码")
        password_label.setStyleSheet("color: #495057; font-weight: bold;")
        
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("输入您的密码")
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
        
        # 记住我选项
        remember_layout = QtWidgets.QHBoxLayout()
        
        self.remember_me = QtWidgets.QCheckBox("记住密码")

        self.remember_me.setStyleSheet("""
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
                background-color: #007bff;
                border: 1px solid #007bff;
            }
        """)

        # 添加自动登录复选框
        self.auto_login = QtWidgets.QCheckBox("自动登录")
        self.auto_login.setStyleSheet("""
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
                background-color: #007bff;
                border: 1px solid #007bff;
            }
        """)

        # 当选中自动登录时，自动选中记住密码
        self.auto_login.toggled.connect(self.handle_auto_login_toggle)
      
        
        forgot_btn = QtWidgets.QPushButton("忘记密码?")
        forgot_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                color: #007bff;
                text-align: right;
            }
            QPushButton:hover {
                color: #0056b3;
                text-decoration: underline;
            }
        """)
        forgot_btn.setCursor(Qt.PointingHandCursor)
        
        remember_layout.addWidget(self.remember_me)
        remember_layout.addWidget(self.auto_login)
        remember_layout.addStretch()
        remember_layout.addWidget(forgot_btn)
        
        card_layout.addLayout(remember_layout)
        
        # 登录按钮
        self.login_btn = QtWidgets.QPushButton("登录")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 5px;
                padding: 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.login_btn.setMinimumHeight(45)
        self.login_btn.clicked.connect(self.handle_login)
        
        card_layout.addWidget(self.login_btn)
        
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
        
        # 注册区域
        register_layout = QtWidgets.QHBoxLayout()
        
        register_label = QtWidgets.QLabel("还没有账户?")
        register_label.setStyleSheet("color: #6c757d;")
        
        register_btn = QtWidgets.QPushButton("立即注册")
        register_btn.setStyleSheet("""
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
        register_btn.setCursor(Qt.PointingHandCursor)
        register_btn.clicked.connect(self.show_register_form)
        
        register_layout.addWidget(register_label)
        register_layout.addWidget(register_btn)
        register_layout.setAlignment(Qt.AlignCenter)
        
        card_layout.addLayout(register_layout)
        
        # 离线模式区域
        offline_layout = QtWidgets.QHBoxLayout()
        
        offline_btn = QtWidgets.QPushButton("离线使用")
        offline_btn.setStyleSheet("""
            QPushButton {
                background: none;
                border: 1px solid #6c757d;
                border-radius: 5px;
                color: #6c757d;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
            }
        """)
        offline_btn.clicked.connect(self.use_offline_mode)
        
        offline_layout.addStretch()
        offline_layout.addWidget(offline_btn)
        offline_layout.addStretch()
        
        card_layout.addLayout(offline_layout)
        
        # 添加卡片到主布局
        main_layout.addWidget(login_card)
        
        # 添加键盘事件
        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.returnPressed.connect(lambda: self.password_input.setFocus())
    
    # 添加一个新方法处理用户手动关闭
    def handle_user_close(self):
        """用户通过关闭按钮关闭窗口"""
        self._user_closed = True  # 标记为用户关闭
        self.close()

    def handle_login(self):
        """处理登录请求"""
        # 获取输入
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # 基本验证
        if not username:
            self.show_error("请输入用户名")
            return
        
        if not password:
            self.show_error("请输入密码")
            return
        
        # 禁用登录按钮防止重复点击
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        
        # 清除错误消息
        self.error_label.setVisible(False)
        
        # 创建登录任务
        login_worker = Worker(self.network_manager.login, username, password)
        
        # 设置回调
        login_worker.signals.finished.connect(self.handle_login_result)
        login_worker.signals.error.connect(lambda e: self.show_error(f"登录出错: {str(e)}"))
        
        # 启动任务
        self.threadpool.start(login_worker)

    def handle_auto_login_toggle(self, checked):
        """当自动登录选项变化时调用"""
        if checked:
            # 如果选中自动登录，也必须选中记住密码
            self.remember_me.setChecked(True)
            # 可选：禁用记住密码复选框
            self.remember_me.setEnabled(False)
        else:
            # 当取消自动登录时，重新启用记住密码复选框
            self.remember_me.setEnabled(True)

    def save_credentials(self, username, password=None):
        """保存用户凭据"""
        print(f"保存凭据: 用户名={username}, 是否记住密码={self.remember_me.isChecked()}")
        
        settings = QtCore.QSettings("AITodoList", "UserPrefs")
        settings.setValue("lastUsername", username)
        
        # 保存记住密码和自动登录设置
        settings.setValue("rememberPassword", self.remember_me.isChecked())
        settings.setValue("autoLogin", self.auto_login.isChecked())
        
        # 如果提供了密码且选择了记住密码，保存加密的密码
        if password and self.remember_me.isChecked():
            # 简单加密密码（生产环境中应使用更安全的方式）
            encrypted_password = self.encrypt_password(password)
            settings.setValue("encryptedPassword", encrypted_password)
            print(f"已保存加密密码: {encrypted_password[:10]}...")
        elif not self.remember_me.isChecked():
            # 如果没有选择记住密码，则清除已保存的密码
            settings.remove("encryptedPassword")
            print("已清除保存的密码")
        
        # 强制写入设置 - 确保立即保存
        settings.sync()

    # def closeEvent(self, event):
    #     """处理窗口关闭事件"""
    #     # 直接接受关闭事件，不显示确认对话框
    #     event.accept()
        
    #     # 可选：如果登录窗口是由主窗口打开的，考虑是否退出整个应用
    #     # 如果只想关闭登录窗口而不退出应用，可以使用以下逻辑
    #     parent = self.parent()
    #     if parent and isinstance(parent, QtWidgets.QMainWindow):
    #         # 如果用户未登录，显示主窗口
    #         if not parent.user_info:
    #             # 如果您希望在登录窗口关闭时也退出应用程序:
    #             QtWidgets.QApplication.quit()
    #     else:
    #         # 如果登录窗口是独立的（没有父窗口），可以选择退出应用
    #         QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 直接接受关闭事件，不显示确认对话框
        event.accept()
        
        # 不要在这里调用quit()
        # 登录窗口关闭不应该导致整个应用退出
        
        # 检查是否是通过关闭按钮关闭的窗口
        # 如果是通过close()方法关闭的，不做特殊处理
        # 如果是用户点击X按钮关闭的，才需要退出应用
        if hasattr(self, '_user_closed') and self._user_closed:
            QtWidgets.QApplication.quit()

    def encrypt_password(self, password):
        """简单加密密码（仅用于演示）"""
        # 在实际应用中应使用更安全的加密方法
        # 这里使用简单的base64编码作为示例
        import base64
        return base64.b64encode(password.encode()).decode()

    def decrypt_password(self, encrypted):
        """解密密码"""
        import base64
        try:
            return base64.b64decode(encrypted.encode()).decode()
        except:
            return ""

    def load_saved_credentials(self):
        """加载保存的凭据"""
        settings = QtCore.QSettings("AITodoList", "UserPrefs")
        remember = settings.value("rememberPassword", False, type=bool)
        auto_login = settings.value("autoLogin", False, type=bool)
        
        print(f"加载凭据: 记住密码={remember}, 自动登录={auto_login}")
        
        if remember or auto_login:
            username = settings.value("lastUsername", "")
            self.username_input.setText(username)
            self.remember_me.setChecked(remember)
            
            if hasattr(self, 'auto_login'):
                self.auto_login.setChecked(auto_login)
            
            # 如果设置了记住密码，加载密码
            if remember:
                encrypted_password = settings.value("encryptedPassword", "")
                if encrypted_password:
                    password = self.decrypt_password(encrypted_password)
                    self.password_input.setText(password)
                    print(f"已加载保存的密码: 长度={len(password)}")
                else:
                    print("未找到加密密码")
            
            # 如果设置了自动登录，自动点击登录按钮
            if auto_login and username and self.password_input.text() and hasattr(self, 'auto_login'):
                # 使用短延迟确保UI完全加载
                QtCore.QTimer.singleShot(500, self.handle_login)
    
    def handle_login_result(self, result):
        """处理登录结果"""
        # 恢复登录按钮状态
        self.login_btn.setEnabled(True)
        self.login_btn.setText("登录")
        
        if result.get('success'):
            print("登录成功，保存用户设置...")
            # 不管是否选中"记住密码"，都保存用户设置
            # 这样可以确保如果用户取消选中了"记住密码"，会清除已保存的密码
            username = self.username_input.text().strip()
            # 只有当选中"记住密码"时才传入密码
            password = self.password_input.text() if self.remember_me.isChecked() else None
            
            # 总是调用save_credentials，让它处理选项逻辑
            self.save_credentials(username, password)
            
            # 发送登录成功信号
            self.login_successful.emit(result.get('data', {}))
            
            # 关闭登录窗口
            self.close()
        else:
            # 显示错误消息
            error_message = result.get('error', '登录失败，请检查用户名和密码')
            self.show_error(error_message)
    
    def show_error(self, message):
        """显示错误消息"""
        self.error_label.setText(message)
        self.error_label.setVisible(True)
        
        # 恢复登录按钮状态
        self.login_btn.setEnabled(True)
        self.login_btn.setText("登录")
    
    def show_register_form(self):
        """显示注册表单"""
        # 创建注册窗口
        register_window = RegisterWindow(self.network_manager)
        
        # 连接注册成功信号
        register_window.register_successful.connect(self.handle_registration_success)
        
        # 隐藏当前窗口
        self.hide()
        
        # 显示注册窗口
        register_window.exec_()
        
        # 恢复当前窗口
        self.show()
    
    def handle_registration_success(self, user_data):
        """处理注册成功事件"""
        # 自动填充用户名
        self.username_input.setText(user_data.get('username', ''))
        
        # 显示成功消息
        QtWidgets.QMessageBox.information(
            self, 
            "注册成功", 
            "账户已成功创建，请使用您的凭据登录。"
        )
    
    def use_offline_mode(self):
        """使用离线模式"""
        # 创建一个模拟的成功登录响应
        offline_data = {
            'user_id': 'offline',
            'username': '离线用户',
            'is_offline': True  # 标记为离线模式
        }
        
        # 发送登录成功信号
        self.login_successful.emit(offline_data)
        
        # 关闭登录窗口
        self.close()
    
    
    def showEvent(self, event):
        """窗口显示时加载凭据"""
        self.load_saved_credentials()
        super().showEvent(event)
    
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