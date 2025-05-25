# ui/task_edit_dialog.py

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox
from PyQt5.QtCore import Qt


class TaskEditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建/编辑任务")
        self.task_data = None
        self.group_combo = None  # 提前声明
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 任务名称
        name_layout = QHBoxLayout()
        name_label = QLabel("任务名称:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)

        # 任务类型
        type_layout = QHBoxLayout()
        type_label = QLabel("任务类型:")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["click", "match", "drag", "type", "swipe"])
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)

        # 所属分组（下拉框）
        group_layout = QHBoxLayout()
        group_label = QLabel("所属分组:")
        self.group_combo = QComboBox()
        self.group_combo.addItem("根任务组")  # 默认选项

        # 动态加载所有任务组
        try:
            for group in self.main_window.group_manager.get_all_groups():
                if group.name != "根任务组":  # 避免重复添加
                    self.group_combo.addItem(group.name)
        except Exception as e:
            print(f"⚠️ 分组加载失败: {e}")

        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_combo)

        # 参数（JSON 格式输入）
        param_layout = QHBoxLayout()
        param_label = QLabel("参数 (JSON):")
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText('例如: {"location": [100, 200]}')
        param_layout.addWidget(param_label)
        param_layout.addWidget(self.param_input)

        # 按钮区域
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # 组合布局
        layout.addLayout(name_layout)
        layout.addLayout(type_layout)
        layout.addLayout(group_layout)
        layout.addLayout(param_layout)
        layout.addLayout(btn_layout)

        # 连接事件：当任务类型变化时自动填充示例参数
        self.type_combo.currentTextChanged.connect(self.update_placeholder)

    def set_default_group(self, group_name):
        """安全地设置默认分组"""
        index = self.group_combo.findText(group_name)
        if index >= 0:
            self.group_combo.setCurrentIndex(index)

    def update_placeholder(self, task_type):
        """根据任务类型更新参数输入框的占位符和默认值"""
        if task_type == "click":
            self.param_input.setText('{"location": [100, 200]}')
        elif task_type == "match":
            self.param_input.setText('{"template": "image.png"}')
        elif task_type == "drag":
            self.param_input.setText('{"start": [100, 100], "end": [200, 200]}')
        elif task_type == "type":
            self.param_input.setText('{"text": "默认输入"}')
        elif task_type == "swipe":
            self.param_input.setText('{"start": [100, 100], "end": [300, 300], "duration": 500}')
        else:
            self.param_input.setText('{}')

    def get_task_data(self):
        """获取用户输入的任务数据"""
        return {
            "name": self.name_input.text(),
            "task_type": self.type_combo.currentText(),
            "parameters": self.param_input.text(),
            "group": self.group_combo.currentText()
        }

