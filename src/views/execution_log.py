from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QPushButton, QHBoxLayout, QGroupBox, 
                            QLabel, QComboBox, QDateTimeEdit)
from PyQt5.QtCore import Qt, QDateTime

class ExecutionLogTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        
        # 创建日志过滤区域
        self.create_log_filter_area()
        
        # 创建日志显示区域
        self.create_log_display_area()
        
        # 创建日志操作按钮
        self.create_log_buttons()
    
    def create_log_filter_area(self):
        filter_group = QGroupBox("日志过滤")
        filter_layout = QHBoxLayout(filter_group)
        
        # 任务过滤器
        task_label = QLabel("任务:")
        self.task_filter = QComboBox()
        self.task_filter.addItem("所有任务")
        
        # 状态过滤器
        status_label = QLabel("状态:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["所有状态", "成功", "失败", "进行中"])
        
        # 时间范围过滤器
        time_label = QLabel("时间范围:")
        self.start_time = QDateTimeEdit()
        self.start_time.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.start_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        time_to_label = QLabel("至:")
        self.end_time = QDateTimeEdit()
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.end_time.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        # 应用过滤按钮
        self.apply_filter_btn = QPushButton("应用过滤")
        
        filter_layout.addWidget(task_label)
        filter_layout.addWidget(self.task_filter)
        filter_layout.addWidget(status_label)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(time_label)
        filter_layout.addWidget(self.start_time)
        filter_layout.addWidget(time_to_label)
        filter_layout.addWidget(self.end_time)
        filter_layout.addWidget(self.apply_filter_btn)
        
        self.main_layout.addWidget(filter_group)
    
    def create_log_display_area(self):
        log_group = QGroupBox("执行日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        
        log_layout.addWidget(self.log_text)
        self.main_layout.addWidget(log_group)
    
    def create_log_buttons(self):
        button_layout = QHBoxLayout()
        
        self.clear_log_btn = QPushButton("清空日志")
        self.export_log_btn = QPushButton("导出日志")
        self.refresh_log_btn = QPushButton("刷新日志")
        
        button_layout.addWidget(self.clear_log_btn)
        button_layout.addWidget(self.export_log_btn)
        button_layout.addWidget(self.refresh_log_btn)
        
        self.main_layout.addLayout(button_layout)    