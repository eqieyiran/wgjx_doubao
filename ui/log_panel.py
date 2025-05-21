# ui/log_panel.py
from PyQt5 import Qt
from PyQt5.QtWidgets import QTextEdit, QCheckBox, QHBoxLayout, QVBoxLayout, QWidget
from PyQt5.QtGui import QTextCharFormat, QColor, QTextCursor


class LogPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 过滤选项
        filter_layout = QHBoxLayout()
        self.info_checkbox = QCheckBox("INFO")
        self.warning_checkbox = QCheckBox("WARNING")
        self.error_checkbox = QCheckBox("ERROR")
        self.info_checkbox.setChecked(True)
        self.warning_checkbox.setChecked(True)
        self.error_checkbox.setChecked(True)

        filter_layout.addWidget(self.info_checkbox)
        filter_layout.addWidget(self.warning_checkbox)
        filter_layout.addWidget(self.error_checkbox)

        # 日志显示区域
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addLayout(filter_layout)
        layout.addWidget(self.log_display)

    def log(self, level, message):
        """根据日志级别设置颜色并输出信息"""
        color_map = {
            "INFO": QColor("#000000"),  # 黑色
            "DEBUG": QColor("#808080"),  # 灰色
            "WARNING": QColor("#FFA500"),  # 橙色
            "ERROR": QColor("#FF0000"),  # 红色
            "SUCCESS": QColor("#00FF00")  # 绿色
        }

        icon = {
            "INFO": "ℹ️",
            "DEBUG": "🛠️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅"
        }.get(level, "📝")

        full_text = f"{icon} [{level}] {message}"

        text_cursor = self.log_display.textCursor()  # ✅ 改为 log_display 的 cursor
        text_cursor.movePosition(QTextCursor.End)

        fmt = self.log_display.currentCharFormat()  # ✅ 改为 log_display 的 format
        fmt.setForeground(color_map.get(level, QColor("#000000")))
        text_cursor.setCharFormat(fmt)

        text_cursor.insertText(full_text + "\n")
        self.log_display.setTextCursor(text_cursor)  # ✅ 设置回 log_display
        self.log_display.ensureCursorVisible()  # ✅ 自动滚动到底部

    def export_log(self, file_path):
        with open(file_path, 'w') as f:
            f.write(self.log_display.toPlainText())
