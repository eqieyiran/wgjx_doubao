# ui/task_edit_dialog.py

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QComboBox

class TaskEditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建任务")
        self.task_data = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

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

        # 分组（可选）
        group_layout = QHBoxLayout()
        group_label = QLabel("所属分组:")
        self.group_input = QLineEdit()
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_input)

        # 参数（示例为字符串输入）
        param_layout = QHBoxLayout()
        param_label = QLabel("参数 (JSON):")
        self.param_input = QLineEdit()
        self.param_input.setText('{"location": [100, 200]}')
        param_layout.addWidget(param_label)
        param_layout.addWidget(self.param_input)

        # 按钮区域
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")

        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)

        # 组合布局
        layout.addLayout(name_layout)
        layout.addLayout(type_layout)
        layout.addLayout(group_layout)
        layout.addLayout(param_layout)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_task_data(self):
        """获取用户输入的任务数据"""
        return {
            "name": self.name_input.text(),
            "task_type": self.type_combo.currentText(),
            "parameters": self.param_input.text(),
            "group": self.group_input.text()
        }