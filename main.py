import sys
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
import logging

# 启用日志系统
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
def main():
    app = QApplication(sys.argv)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
