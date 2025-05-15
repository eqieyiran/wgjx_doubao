from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, 
                            QLineEdit, QPushButton, QGroupBox, 
                            QLabel, QSpinBox, QCheckBox, QComboBox)
import os

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        
        # 创建应用设置区域
        self.create_app_settings_area()
        
        # 创建图像处理设置区域
        self.create_image_processing_settings_area()
        
        # 创建保存设置按钮
        self.create_save_button()
    
    def create_app_settings_area(self):
        app_group = QGroupBox("应用设置")
        app_layout = QFormLayout(app_group)
        
        # 任务存储路径
        self.task_path_label = QLabel("任务存储路径:")
        self.task_path_input = QLineEdit()
        self.browse_task_path_btn = QPushButton("浏览...")
        
        task_path_layout = QHBoxLayout()
        task_path_layout.addWidget(self.task_path_input)
        task_path_layout.addWidget(self.browse_task_path_btn)
        
        # 日志存储路径
        self.log_path_label = QLabel("日志存储路径:")
        self.log_path_input = QLineEdit()
        self.browse_log_path_btn = QPushButton("浏览...")
        
        log_path_layout = QHBoxLayout()
        log_path_layout.addWidget(self.log_path_input)
        log_path_layout.addWidget(self.browse_log_path_btn)
        
        # 自动保存间隔
        self.auto_save_label = QLabel("自动保存间隔(分钟):")
        self.auto_save_spinbox = QSpinBox()
        self.auto_save_spinbox.setRange(1, 60)
        self.auto_save_spinbox.setValue(5)
        
        # 启动时自动加载任务
        self.auto_load_tasks = QCheckBox("启动时自动加载任务")
        self.auto_load_tasks.setChecked(True)
        
        app_layout.addRow(self.task_path_label, task_path_layout)
        app_layout.addRow(self.log_path_label, log_path_layout)
        app_layout.addRow(self.auto_save_label, self.auto_save_spinbox)
        app_layout.addRow(self.auto_load_tasks)
        
        self.main_layout.addWidget(app_group)
    
    def create_image_processing_settings_area(self):
        image_group = QGroupBox("图像处理设置")
        image_layout = QFormLayout(image_group)
        
        # 匹配算法选择
        self.algorithm_label = QLabel("匹配算法:")
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["模板匹配", "特征点匹配", "深度学习"])
        
        # 线程数设置
        self.thread_label = QLabel("处理线程数:")
        self.thread_spinbox = QSpinBox()
        self.thread_spinbox.setRange(1, os.cpu_count() or 4)
        self.thread_spinbox.setValue(min(4, os.cpu_count() or 4))
        
        # 批量处理大小
        self.batch_size_label = QLabel("批量处理大小:")
        self.batch_size_spinbox = QSpinBox()
        self.batch_size_spinbox.setRange(1, 100)
        self.batch_size_spinbox.setValue(10)
        
        # 图像预处理
        self.preprocess_checkbox = QCheckBox("启用图像预处理")
        self.preprocess_checkbox.setChecked(True)
        
        image_layout.addRow(self.algorithm_label, self.algorithm_combo)
        image_layout.addRow(self.thread_label, self.thread_spinbox)
        image_layout.addRow(self.batch_size_label, self.batch_size_spinbox)
        image_layout.addRow(self.preprocess_checkbox)
        
        self.main_layout.addWidget(image_group)
    
    def create_save_button(self):
        self.save_settings_btn = QPushButton("保存设置")
        self.main_layout.addWidget(self.save_settings_btn, alignment=Qt.AlignCenter)    