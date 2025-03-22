from PyQt5 import QtWidgets, QtGui
import sys

class TrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, parent=None):
        icon = QtGui.QIcon(QtWidgets.QApplication.style().standardIcon(
            QtWidgets.QStyle.SP_FileDialogDetailedView))
        super(TrayIcon, self).__init__(icon, parent)
        
        self.parent = parent
        self.menu = QtWidgets.QMenu()
        self.init_menu()
        self.setContextMenu(self.menu)
        self.activated.connect(self.on_activated)
        
        # 设置工具提示
        self.setToolTip("智能 Todo 助手")

    def init_menu(self):
        show_action = self.menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_window)
        
        add_task_action = self.menu.addAction("快速添加任务")
        add_task_action.triggered.connect(self.quick_add_task)
        
        self.menu.addSeparator()
        
        exit_action = self.menu.addAction("退出程序")
        exit_action.triggered.connect(QtWidgets.qApp.quit)

    def on_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.Trigger:
            self.toggle_window()

    def toggle_window(self):
        if self.parent:
            if self.parent.isVisible():
                self.parent.hide()
            else:
                self.parent.show()
                self.parent.activateWindow()
        else:
            self.show_window()

    def show_window(self):
        if self.parent:
            self.parent.show()
            self.parent.activateWindow()

    def quick_add_task(self):
        task_text, ok = QtWidgets.QInputDialog.getText(None, "快速添加任务", "输入新任务:")
        if ok and task_text and self.parent:
            # 如果存在父窗口并且有 create_task_item 方法，则调用它
            if hasattr(self.parent, 'create_task_item'):
                self.parent.create_task_item(task_text, "工作")