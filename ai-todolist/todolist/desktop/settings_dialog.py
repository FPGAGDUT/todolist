from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
import configparser
import os

class SettingsDialog(QtWidgets.QDialog):
    """设置窗口，用于配置API平台和代理设置"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(450, 350)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowTitleHint)
        
        # 读取当前配置
        self.config_path = self.get_config_path()
        self.config = self.load_config()
        
        self.init_ui()
        self.load_values_from_config()
    
    def get_config_path(self):
        """获取配置文件路径"""
        # 先检查用户主目录下是否有配置文件
        home_config = os.path.join(os.path.expanduser("~"), ".todolist", "config.ini")
        if os.path.exists(home_config):
            return home_config
            
        # 再检查当前目录
        current_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "config.ini")
        if os.path.exists(current_config):
            return current_config
            
        # 最后尝试相对路径
        return "./config.ini"
    
    def load_config(self):
        """加载配置文件"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(self.config_path, encoding='utf-8')
        return config
    
    def init_ui(self):
        """初始化UI元素"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # 创建标签页
        tabs = QtWidgets.QTabWidget()
        
        # API设置标签页
        api_tab = QtWidgets.QWidget()
        api_layout = QtWidgets.QVBoxLayout(api_tab)
        
        # API提供商选择
        api_group = QtWidgets.QGroupBox("API提供商")
        api_group_layout = QtWidgets.QVBoxLayout()
        
        # 提供商选择下拉框
        provider_layout = QtWidgets.QHBoxLayout()
        provider_label = QtWidgets.QLabel("选择提供商:")
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItems(["volcanoark", "openai", "deepseek"])
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo, 1)
        
        # 模型名称
        model_layout = QtWidgets.QHBoxLayout()
        model_label = QtWidgets.QLabel("模型名称:")
        self.model_input = QtWidgets.QLineEdit()
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_input, 1)
        
        # API端点
        endpoint_layout = QtWidgets.QHBoxLayout()
        endpoint_label = QtWidgets.QLabel("API端点:")
        self.endpoint_input = QtWidgets.QLineEdit()
        endpoint_layout.addWidget(endpoint_label)
        endpoint_layout.addWidget(self.endpoint_input, 1)
        
        # API超时设置
        timeout_layout = QtWidgets.QHBoxLayout()
        timeout_label = QtWidgets.QLabel("超时设置(秒):")
        self.timeout_spin = QtWidgets.QSpinBox()
        self.timeout_spin.setMinimum(5)
        self.timeout_spin.setMaximum(60)
        self.timeout_spin.setValue(15)
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(self.timeout_spin, 1)
        
        api_group_layout.addLayout(provider_layout)
        api_group_layout.addLayout(model_layout)
        api_group_layout.addLayout(endpoint_layout)
        api_group_layout.addLayout(timeout_layout)
        api_group.setLayout(api_group_layout)
        
        # 连接提供商变更事件
        self.provider_combo.currentTextChanged.connect(self.provider_changed)
        
        # 代理设置
        proxy_group = QtWidgets.QGroupBox("代理设置")
        proxy_layout = QtWidgets.QVBoxLayout()
        
        self.enable_proxy = QtWidgets.QCheckBox("启用代理")
        proxy_layout.addWidget(self.enable_proxy)
        
        # 代理地址
        proxy_host_layout = QtWidgets.QHBoxLayout()
        proxy_host_label = QtWidgets.QLabel("代理地址:")
        self.proxy_host_input = QtWidgets.QLineEdit()
        proxy_host_layout.addWidget(proxy_host_label)
        proxy_host_layout.addWidget(self.proxy_host_input, 1)
        
        # 代理端口
        proxy_port_layout = QtWidgets.QHBoxLayout()
        proxy_port_label = QtWidgets.QLabel("代理端口:")
        self.proxy_port_input = QtWidgets.QLineEdit()
        proxy_port_layout.addWidget(proxy_port_label)
        proxy_port_layout.addWidget(self.proxy_port_input, 1)
        
        proxy_layout.addLayout(proxy_host_layout)
        proxy_layout.addLayout(proxy_port_layout)
        proxy_group.setLayout(proxy_layout)
        
        # 启用/禁用代理设置
        self.enable_proxy.stateChanged.connect(self.toggle_proxy_fields)
        
        # 将组添加到API标签页
        api_layout.addWidget(api_group)
        api_layout.addWidget(proxy_group)
        api_layout.addStretch()
        
        # 常规设置标签页
        general_tab = QtWidgets.QWidget()
        general_layout = QtWidgets.QVBoxLayout(general_tab)
        
        # 应用程序设置组
        app_group = QtWidgets.QGroupBox("应用程序设置")
        app_layout = QtWidgets.QVBoxLayout()
        
        # 应用名称
        app_name_layout = QtWidgets.QHBoxLayout()
        app_name_label = QtWidgets.QLabel("应用名称:")
        self.app_name_input = QtWidgets.QLineEdit()
        app_name_layout.addWidget(app_name_label)
        app_name_layout.addWidget(self.app_name_input, 1)
        
        # 版本
        version_layout = QtWidgets.QHBoxLayout()
        version_label = QtWidgets.QLabel("版本:")
        self.version_input = QtWidgets.QLineEdit()
        self.version_input.setReadOnly(True)  # 版本号不可编辑
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_input, 1)
        
        app_layout.addLayout(app_name_layout)
        app_layout.addLayout(version_layout)
        app_group.setLayout(app_layout)
        
        # 日志设置组
        log_group = QtWidgets.QGroupBox("日志设置")
        log_layout = QtWidgets.QVBoxLayout()
        
        # 日志级别
        log_level_layout = QtWidgets.QHBoxLayout()
        log_level_label = QtWidgets.QLabel("日志级别:")
        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_level_layout.addWidget(log_level_label)
        log_level_layout.addWidget(self.log_level_combo, 1)
        
        log_layout.addLayout(log_level_layout)
        log_group.setLayout(log_layout)
        
        # 将组添加到常规标签页
        general_layout.addWidget(app_group)
        general_layout.addWidget(log_group)
        general_layout.addStretch()
        
        # 添加标签页
        tabs.addTab(api_tab, "API设置")
        tabs.addTab(general_tab, "常规设置")
        
        layout.addWidget(tabs)
        
        # 添加按钮
        button_layout = QtWidgets.QHBoxLayout()
        self.save_btn = QtWidgets.QPushButton("保存")
        self.cancel_btn = QtWidgets.QPushButton("取消")
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 连接按钮信号
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
    
    def provider_changed(self, provider):
        """当API提供商改变时更新UI"""
        # 根据选择的提供商预填充设置
        if provider == "volcanoark":
            self.endpoint_input.setText("https://ark.cn-beijing.volces.com/api/v3/chat/completions")
            self.model_input.setText("deepseek-v3-241226")
        elif provider == "openai":
            self.endpoint_input.setText("https://api.openai.com/v1/chat/completions")
            self.model_input.setText("gpt-3.5-turbo")
        elif provider == "deepseek":
            self.endpoint_input.setText("https://api.deepseek.com")
            self.model_input.setText("deepseek-chat")
    
    def toggle_proxy_fields(self, state):
        """启用/禁用代理输入字段"""
        enabled = state == Qt.Checked
        self.proxy_host_input.setEnabled(enabled)
        self.proxy_port_input.setEnabled(enabled)
    
    def load_values_from_config(self):
        """从配置加载值到UI"""
        try:
            # API设置
            if 'llm' in self.config:
                self.provider_combo.setCurrentText(self.config.get('llm', 'provider', fallback='volcanoark'))
                self.model_input.setText(self.config.get('llm', 'model_name', fallback='deepseek-v3-241226'))
                self.endpoint_input.setText(self.config.get('llm', 'endpoint', fallback='https://ark.cn-beijing.volces.com/api/v3/chat/completions'))
                self.timeout_spin.setValue(self.config.getint('llm', 'timeout', fallback=15))
                
                # 代理设置
                proxy_host = self.config.get('llm', 'proxy_host', fallback='')
                proxy_port = self.config.get('llm', 'proxy_port', fallback='')
                
                if proxy_host and proxy_port:
                    self.enable_proxy.setChecked(True)
                    self.proxy_host_input.setText(proxy_host)
                    self.proxy_port_input.setText(proxy_port)
                else:
                    self.enable_proxy.setChecked(False)
                    self.proxy_host_input.setText('http://127.0.0.1')
                    self.proxy_port_input.setText('10808')
                
                # 初始调用一次，确保状态正确
                self.toggle_proxy_fields(self.enable_proxy.checkState())
            
            # 常规设置
            if 'settings' in self.config:
                self.app_name_input.setText(self.config.get('settings', 'app_name', fallback='AI ToDo List').strip('"'))
                self.version_input.setText(self.config.get('settings', 'version', fallback='1.0.0').strip('"'))
            
            # API日志设置
            if 'api' in self.config:
                self.log_level_combo.setCurrentText(self.config.get('api', 'log_level', fallback='INFO'))
                
        except Exception as e:
            print(f"加载配置出错: {e}")
            # 加载错误时使用默认值
            self.reset_to_defaults()
    
    def reset_to_defaults(self):
        """重置为默认值"""
        self.provider_combo.setCurrentText('volcanoark')
        self.model_input.setText('deepseek-v3-241226')
        self.endpoint_input.setText('https://ark.cn-beijing.volces.com/api/v3/chat/completions')
        self.timeout_spin.setValue(15)
        self.enable_proxy.setChecked(False)
        self.proxy_host_input.setText('http://127.0.0.1')
        self.proxy_port_input.setText('10808')
        self.app_name_input.setText('AI ToDo List')
        self.version_input.setText('1.0.0')
        self.log_level_combo.setCurrentText('INFO')
    
    def save_settings(self):
        """保存设置到配置文件"""
        try:
            # 确保配置节存在
            if 'settings' not in self.config:
                self.config.add_section('settings')
            if 'llm' not in self.config:
                self.config.add_section('llm')
            if 'api' not in self.config:
                self.config.add_section('api')
                
            # 保存API设置
            self.config.set('llm', 'provider', self.provider_combo.currentText())
            self.config.set('llm', 'model_name', self.model_input.text())
            self.config.set('llm', 'endpoint', self.endpoint_input.text())
            self.config.set('llm', 'timeout', str(self.timeout_spin.value()))
            
            # 保存代理设置
            if self.enable_proxy.isChecked():
                self.config.set('llm', 'proxy_host', self.proxy_host_input.text())
                self.config.set('llm', 'proxy_port', self.proxy_port_input.text())
            else:
                self.config.set('llm', 'proxy_host', '')
                self.config.set('llm', 'proxy_port', '')
                
            # 保存常规设置
            self.config.set('settings', 'app_name', f'"{self.app_name_input.text()}"')
            # 版本不可编辑，所以不保存
            
            # 保存日志设置
            self.config.set('api', 'log_level', self.log_level_combo.currentText())
            
            # 写入配置文件
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)
                
            # 应用配置变更
            self.apply_config_changes()
                
            QtWidgets.QMessageBox.information(self, "成功", "设置已保存")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"保存设置失败: {str(e)}")
    
    def apply_config_changes(self):
        """应用配置变更到当前应用程序"""
        # 应用代理设置
        if self.enable_proxy.isChecked():
            proxy = f"{self.proxy_host_input.text()}:{self.proxy_port_input.text()}"
            os.environ["http_proxy"] = proxy
            os.environ["https_proxy"] = proxy
            print(f"已设置全局代理: {proxy}")
        else:
            if "http_proxy" in os.environ:
                del os.environ["http_proxy"]
            if "https_proxy" in os.environ:
                del os.environ["https_proxy"]
            print("已禁用全局代理")

    def set_config(self, config):
        """设置配置对象"""
        self.config = config
        self.load_values_from_config()
        
    def get_config(self):
        """获取当前配置对象"""
        return self.config