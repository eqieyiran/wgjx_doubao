import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
import logging
import traceback
# 启用日志系统
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
def main():
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

def exception_hook(exctype, value, traceback_obj):
    """全局异常钩子函数"""
    error_message = ''.join(traceback.format_exception(exctype, value, traceback_obj))
    print(f"致命错误: {error_message}")
    QMessageBox.critical(None, "致命错误", f"发生致命错误:\n{error_message}")
    sys.exit(1)

sys.excepthook = exception_hook

if __name__ == "__main__":
    main()
