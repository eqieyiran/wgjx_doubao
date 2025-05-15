from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, 
                            QWidget, QMessageBox)
from src.views.task_manager import TaskManagerTab
from src.views.execution_log import ExecutionLogTab
from src.views.settings import SettingsTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("图像识别自动化任务执行程序")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 创建标签页
        self.create_tabs()
        
        # 初始化应用设置
        self.init_settings()
    
    def create_tabs(self):
        self.tabs = QTabWidget()
        
        # 添加任务管理标签页
        self.task_manager_tab = TaskManagerTab()
        self.tabs.addTab(self.task_manager_tab, "任务管理")
        
        # 添加执行日志标签页
        self.execution_log_tab = ExecutionLogTab()
        self.tabs.addTab(self.execution_log_tab, "执行日志")
        
        # 添加设置标签页
        self.settings_tab = SettingsTab()
        self.tabs.addTab(self.settings_tab, "设置")
        
        self.layout.addWidget(self.tabs)
    
    def init_settings(self):
        # 加载或初始化应用设置
        pass
    
    def closeEvent(self, event):
        # 关闭应用前的清理工作
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出应用程序吗?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 保存设置和任务状态
            event.accept()
        else:
            event.ignore()    