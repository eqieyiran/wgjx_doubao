# utils/input_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QHBoxLayout

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入")
        self.value = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel("请输入:")
        layout.addWidget(self.label)

        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")

        ok_button.clicked.connect(self.on_ok)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

    def on_ok(self):
        self.value = self.line_edit.text()
        self.accept()

    @staticmethod
    def getText(parent, title, label, text=""):
        dialog = InputDialog(parent)
        dialog.setWindowTitle(title)
        dialog.label.setText(label)
        dialog.line_edit.setText(text)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.value, True
        else:
            return None, False

    @staticmethod
    def get_confirmation(parent, title, message):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(parent, title, message,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes
