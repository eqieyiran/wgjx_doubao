# ui/log_panel.py

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
        level = level.upper()
        if (level == "INFO" and not self.info_checkbox.isChecked()) or \
           (level == "WARNING" and not self.warning_checkbox.isChecked()) or \
           (level == "ERROR" and not self.error_checkbox.isChecked()):
            return

        fmt = QTextCharFormat()
        if level == "INFO":
            fmt.setForeground(QColor("white"))
        elif level == "WARNING":
            fmt.setForeground(QColor("yellow"))
        elif level == "ERROR":
            fmt.setForeground(QColor("red"))

        cursor = self.log_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.mergeCharFormat(fmt)
        cursor.insertText(f"[{level}] {message}\n")
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )

    def export_log(self, file_path):
        with open(file_path, 'w') as f:
            f.write(self.log_display.toPlainText())
