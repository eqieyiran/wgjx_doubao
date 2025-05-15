from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                            QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
                            QComboBox, QFileDialog, QGroupBox, QFormLayout, 
                            QCheckBox, QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt
import os

class TaskManagerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        self.main_layout = QVBoxLayout(self)
        
        # 创建任务表格
        self.create_task_table()
        
        # 创建任务操作按钮
        self.create_task_buttons()
        
        # 创建任务配置区域
        self.create_task_config_area()
        
        # 连接信号和槽
        self.connect_signals()
    
    def create_task_table(self):
        table_group = QGroupBox("任务列表")
        table_layout = QVBoxLayout(table_group)
        
        self.task_table = QTableWidget()
        self.task_table.setColumnCount(6)
        self.task_table.setHorizontalHeaderLabels(["ID", "任务名称", "图片路径", "匹配动作", "失败动作", "状态"])
        
        # 设置表格属性
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table_layout.addWidget(self.task_table)
        self.main_layout.addWidget(table_group)
    
    def create_task_buttons(self):
        button_layout = QHBoxLayout()
        
        self.add_task_btn = QPushButton("添加任务")
        self.edit_task_btn = QPushButton("编辑任务")
        self.delete_task_btn = QPushButton("删除任务")
        self.execute_task_btn = QPushButton("执行选中任务")
        self.execute_all_btn = QPushButton("执行所有任务")
        
        button_layout.addWidget(self.add_task_btn)
        button_layout.addWidget(self.edit_task_btn)
        button_layout.addWidget(self.delete_task_btn)
        button_layout.addWidget(self.execute_task_btn)
        button_layout.addWidget(self.execute_all_btn)
        
        self.main_layout.addLayout(button_layout)
    
    def create_task_config_area(self):
        config_group = QGroupBox("任务配置")
        config_layout = QFormLayout(config_group)
        
        self.task_name_input = QLineEdit()
        self.image_path_input = QLineEdit()
        self.browse_btn = QPushButton("浏览...")
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.image_path_input)
        path_layout.addWidget(self.browse_btn)
        
        self.match_action_input = QLineEdit()
        self.fail_action_input = QLineEdit()
        
        self.recursive_checkbox = QCheckBox("递归搜索子目录")
        self.recursive_checkbox.setChecked(True)
        
        self.threshold_input = QLineEdit("0.8")
        
        config_layout.addRow("任务名称:", self.task_name_input)
        config_layout.addRow("图片路径:", path_layout)
        config_layout.addRow("匹配成功动作:", self.match_action_input)
        config_layout.addRow("匹配失败动作:", self.fail_action_input)
        config_layout.addRow("匹配阈值:", self.threshold_input)
        config_layout.addRow(self.recursive_checkbox)
        
        self.save_task_btn = QPushButton("保存任务配置")
        config_layout.addRow(self.save_task_btn)
        
        self.main_layout.addWidget(config_group)
    
    def connect_signals(self):
        self.add_task_btn.clicked.connect(self.add_task)
        self.edit_task_btn.clicked.connect(self.edit_task)
        self.delete_task_btn.clicked.connect(self.delete_task)
        self.execute_task_btn.clicked.connect(self.execute_selected_task)
        self.execute_all_btn.clicked.connect(self.execute_all_tasks)
        self.browse_btn.clicked.connect(self.browse_image_path)
        self.save_task_btn.clicked.connect(self.save_task_config)
    
    def browse_image_path(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        
        # 询问用户是选择文件还是目录
        choice = QMessageBox.question(
            self, "选择类型", 
            "请选择是要选择单个图片文件还是图片目录?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        
        if choice == QMessageBox.Yes:  # 选择文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择图片文件", "", "图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*)", options=options
            )
            if file_path:
                self.image_path_input.setText(file_path)
        else:  # 选择目录
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择图片目录", "", options=options
            )
            if dir_path:
                self.image_path_input.setText(dir_path)
    
    def add_task(self):
        # 实现添加任务逻辑
        pass
    
    def edit_task(self):
        # 实现编辑任务逻辑
        pass
    
    def delete_task(self):
        # 实现删除任务逻辑
        pass
    
    def execute_selected_task(self):
        # 实现执行选中任务逻辑
        pass
    
    def execute_all_tasks(self):
        # 实现执行所有任务逻辑
        pass
    
    def save_task_config(self):
        # 实现保存任务配置逻辑
        pass    