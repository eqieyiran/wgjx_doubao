# ui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QShortcut,
    QComboBox, QSlider, QCheckBox, QPushButton,
    QTableView, QHeaderView, QSplitter, QFrame, QApplication, QFileDialog
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from ui.log_panel import LogPanel
from managers.group_manager import GroupManager
from ui.task_group_panel import TaskGroupPanel
from utils.persistence import save_task_groups, load_task_groups


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 初始化设置
        self.settings = QSettings("MyCompany", "AutoTaskHelper")

        # 尝试恢复窗口位置和大小
        self.restore_window_state()

        # 初始化管理器
        loaded_group = load_task_groups()
        if loaded_group:
            self.group_manager = GroupManager()
            self.group_manager.root_group = loaded_group
        else:
            self.group_manager = GroupManager()
            from models.task_model import Task

            daily_group = self.group_manager.create_group("日常任务")
            weekly_group = self.group_manager.create_group("周常任务")

            daily_group.tasks = [
                Task(name="每日签到", task_type="click", parameters={"location": (100, 200)}, group="日常任务"),
                Task(name="每日副本", task_type="match", parameters={"template": "daily.png"}, group="日常任务")
            ]

            weekly_group.tasks = [
                Task(name="周常副本", task_type="match", parameters={"template": "weekly.png"}, group="周常任务"),
                Task(name="周常挑战", task_type="click", parameters={"location": (300, 400)}, group="周常任务")
            ]

        # 左侧面板：任务组树状结构
        self.group_panel = TaskGroupPanel(self.group_manager)
        self.group_panel.itemClicked.connect(self.on_group_selected)

        # 初始化其他内容
        self.setWindowTitle("自动化任务辅助工具")

        self.init_ui()
        self.setup_shortcuts()

        # ✅ 添加这一行，在 UI 初始化后主动加载任务
        self.update_task_list(self._get_all_tasks())

    def on_group_selected(self, item, column):
        """当用户点击任务组时触发"""
        selected_group_name = item.text(column)
        if selected_group_name == "根任务组":
            tasks = self._get_all_tasks()
        else:
            tasks = self.group_manager.get_tasks_by_group(selected_group_name)

        self.update_task_list(tasks)

    def _get_all_tasks(self):
        """递归获取所有任务"""

        def collect(group):
            tasks = list(group.tasks)
            for child in group.children:
                tasks.extend(collect(child))
            return tasks

        return collect(self.group_manager.root_group)

    def restore_window_state(self):
        """从 QSettings 中恢复窗口大小和位置"""
        if self.settings.contains("window/geometry"):
            geometry = self.settings.value("window/geometry")
            self.restoreGeometry(geometry)
        else:
            screen = QApplication.primaryScreen().geometry()
            window_width, window_height = 1200, 800
            x = (screen.width() - window_width) // 2
            y = (screen.height() - window_height) // 2
            self.setGeometry(x, y, window_width, window_height)

    def init_ui(self):
        # 主容器
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        # ===== 创建并添加控制栏 =====
        control_layout = self._create_control_bar()
        main_layout.addLayout(control_layout)

        # ===== 分割面板：左侧任务组 + 右侧任务表格 =====
        splitter = QSplitter(Qt.Horizontal)

        # 左侧面板：任务组树状结构
        group_frame = QFrame()
        group_frame.setLayout(QVBoxLayout())
        group_frame.layout().addWidget(self.group_panel)
        group_frame.setFrameShape(QFrame.StyledPanel)

        # 右侧面板：任务表格
        self.task_table = self._create_task_table()
        task_frame = QFrame()
        task_frame.setLayout(QVBoxLayout())
        task_frame.layout().addWidget(self.task_table)
        task_frame.setFrameShape(QFrame.StyledPanel)

        splitter.addWidget(group_frame)
        splitter.addWidget(task_frame)
        splitter.setSizes([300, 900])  # 初始分割比例

        main_layout.addWidget(splitter)

        # ===== 底部日志面板 =====
        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

        main_widget.setLayout(main_layout)

        # ===== 保存按钮绑定（可选）=====
        self.save_button = QPushButton("保存 (Ctrl+S)")
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.save_current_groups)
        control_layout.addWidget(self.save_button)  # 将按钮加到控制栏中

        # 添加“另存为”按钮
        self.save_as_button = QPushButton("另存为...")
        self.save_as_button.setObjectName("saveAsButton")
        self.save_as_button.clicked.connect(self.save_current_groups_as)
        control_layout.addWidget(self.save_as_button)

        # ===== 样式加载 =====
        try:
            with open("resources/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"加载样式文件失败: {e}")

    def save_current_groups_as(self):
        """手动触发“另存为”操作"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "另存为任务组",
            "",
            "JSON 文件 (*.json)"
        )

        if file_path:
            success = self.group_manager.save_to_file(file_path)
            if success:
                self.log_message("INFO", f"✅ 任务组已另存为至: {file_path}")
            else:
                self.log_message("ERROR", "❌ 另存为失败，请检查权限或路径有效性")

    def setup_shortcuts(self):
        # 保存快捷键 Ctrl+S
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(self.save_current_groups)

        # 另存为快捷键 Ctrl+Shift+S
        shortcut_save_as = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        shortcut_save_as.activated.connect(self.save_current_groups_as)

    def _create_control_bar(self):
        """创建顶部控制栏"""
        control_layout = QHBoxLayout()

        # 分组选择下拉框
        self.group_combo = QComboBox()
        self.group_combo.setObjectName("groupCombo")
        self.group_combo.addItem("全部分组")
        for group in self.group_manager.get_all_groups():
            self.group_combo.addItem(group.name)
        control_layout.addWidget(self.group_combo)

        # 阈值滑动条
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(80)
        self.threshold_slider.setObjectName("thresholdSlider")
        control_layout.addWidget(self.threshold_slider)

        # 随机延迟开关
        self.random_delay_checkbox = QCheckBox("随机延迟")
        self.random_delay_checkbox.setChecked(True)
        self.random_delay_checkbox.setObjectName("randomDelayCheck")
        control_layout.addWidget(self.random_delay_checkbox)

        # 开始/停止按钮
        self.start_button = QPushButton("开始 (Ctrl+E)")
        self.stop_button = QPushButton("停止 (Ctrl+S)")
        self.start_button.setObjectName("startButton")
        self.stop_button.setObjectName("stopButton")

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)

        return control_layout

    def _create_task_table(self):
        """创建中央任务表格"""
        table_view = QTableView()
        table_view.setObjectName("taskTable")

        # 创建模型
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            "ID", "名称", "状态", "操作类型", "分组", "重试次数"
        ])

        # 创建代理模型用于排序
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.table_model)

        table_view.setModel(proxy_model)

        # 设置列宽自适应
        header = table_view.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        return table_view

    def update_task_list(self, tasks):
        """更新任务列表"""
        print(f"正在更新任务数量: {len(tasks)}")  # ✅ 添加调试信息
        self.table_model.removeRows(0, self.table_model.rowCount())

        for task in tasks:
            items = [
                QStandardItem(task.id),
                QStandardItem(task.name),
                QStandardItem(task.status),
                QStandardItem(task.task_type),
                QStandardItem(task.group or ""),
                QStandardItem(str(task.retry_count))
            ]
            self.table_model.appendRow(items)

    def closeEvent(self, event):
        """窗口关闭时自动保存任务组信息及窗口状态"""
        try:
            save_task_groups(self.group_manager)
            print("任务组信息已保存")
        except Exception as e:
            print(f"保存任务组信息失败: {e}")

        # 保存窗口状态
        self.settings.setValue("window/geometry", self.saveGeometry())

        event.accept()

    def setup_shortcuts(self):
        # 添加快捷键 Ctrl+S
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save_current_groups)

    def save_current_groups(self):
        """手动触发保存任务组结构"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存任务组",
            "tasks.json",
            "JSON 文件 (*.json)"
        )

        if file_path:
            success = self.group_manager.save_to_file(file_path)
            if success:
                self.log_message("INFO", f"✅ 任务组已保存至: {file_path}")
            else:
                self.log_message("ERROR", "❌ 保存任务组失败，请检查权限或路径有效性")

    def log_message(self, level, message):
        """记录日志消息"""
        self.log_panel.log(level, message)
