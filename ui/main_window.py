# ui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QShortcut,
    QComboBox, QSlider, QCheckBox, QPushButton,
    QTableView, QHeaderView, QSplitter, QFrame, QApplication, QFileDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings
from PyQt5.QtGui import QKeySequence, QColor, QStandardItemModel, QStandardItem

from models.task_model import Task
from ui.log_panel import LogPanel
from managers.group_manager import GroupManager
from ui.task_group_panel import TaskGroupPanel
from utils.persistence import save_task_groups, load_task_groups
from ui.task_edit_dialog import TaskEditDialog
from engine.task_executor import TaskExecutor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动化任务辅助工具")
        self.resize(1200, 800)

        self.task_executor = TaskExecutor()
        self.task_executor.log_signal.connect(self.log_message)
        self.task_executor.task_status_updated.connect(self.update_task_status)

        self.settings = QSettings("MyCompany", "AutoTaskHelper")
        self.restore_window_state()

        loaded_group = load_task_groups()
        self.group_manager = GroupManager()
        if loaded_group:
            self.group_manager.root_group = loaded_group
        else:
            self._init_default_groups()

        self.current_save_path = "tasks.json"  # 默认保存路径

        self.group_panel = TaskGroupPanel(self.group_manager, self)
        self.group_panel.itemClicked.connect(self.on_group_selected)

        self.init_ui()
        self.setup_shortcuts()
        self.update_task_list(self._get_all_tasks())

    def _init_default_groups(self):
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

    def restore_window_state(self):
        if self.settings.contains("window/geometry"):
            geometry = self.settings.value("window/geometry")
            self.restoreGeometry(geometry)
        else:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        group_frame = QFrame()
        group_frame.setLayout(QVBoxLayout())
        group_frame.layout().addWidget(self.group_panel)
        group_frame.setFrameShape(QFrame.StyledPanel)

        control_layout = self._create_control_bar()
        main_layout.addLayout(control_layout)

        self.task_table = self._create_task_table()
        task_frame = QFrame()
        task_frame.setLayout(QVBoxLayout())
        task_frame.layout().addWidget(self.task_table)
        task_frame.setFrameShape(QFrame.StyledPanel)

        splitter.addWidget(group_frame)
        splitter.addWidget(task_frame)
        splitter.setSizes([300, 900])

        main_layout.addWidget(splitter)

        self.log_panel = LogPanel()
        main_layout.addWidget(self.log_panel)

        self.save_button = QPushButton("保存 (Ctrl+S)")
        self.save_button.clicked.connect(self.save_current_groups)
        control_layout.addWidget(self.save_button)

        self.save_as_button = QPushButton("另存为...")
        self.save_as_button.clicked.connect(self.save_current_groups_as)
        control_layout.addWidget(self.save_as_button)

        try:
            with open("resources/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"加载样式失败: {e}")

        main_widget.setLayout(main_layout)

    def _create_control_bar(self):
        layout = QHBoxLayout()

        self.group_combo = QComboBox()
        self.group_combo.addItem("全部分组")
        for group in self.group_manager.get_all_groups():
            self.group_combo.addItem(group.name)
        layout.addWidget(self.group_combo)

        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(100)
        self.threshold_slider.setValue(80)
        layout.addWidget(self.threshold_slider)

        self.random_delay_checkbox = QCheckBox("随机延迟")
        self.random_delay_checkbox.setChecked(True)
        layout.addWidget(self.random_delay_checkbox)

        self.start_button = QPushButton("开始 (Ctrl+E)")
        self.stop_button = QPushButton("停止 (Ctrl+S)")
        self.start_button.clicked.connect(self.start_task_execution)
        self.stop_button.clicked.connect(self.stop_task_execution)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems(["全部状态", "就绪", "运行中", "成功", "失败"])
        self.status_filter_combo.currentIndexChanged.connect(self.apply_filters)
        layout.addWidget(self.status_filter_combo)

        return layout

    def _create_task_table(self):
        table_view = TaskTableView(main_window=self)
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            "ID", "名称", "状态", "操作类型", "分组", "重试次数"
        ])

        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.table_model)
        table_view.setModel(proxy_model)

        header = table_view.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        table_view.customContextMenuRequested.connect(self.show_task_context_menu)
        table_view.doubleClicked.connect(self.on_task_double_clicked)

        return table_view

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_groups)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_current_groups_as)

    def apply_filters(self):
        selected_group = self.group_combo.currentText()
        selected_status = self.status_filter_combo.currentText()

        tasks = self._get_all_tasks()
        filtered = []

        for task in tasks:
            match_group = selected_group == "全部分组" or task.group == selected_group
            match_status = selected_status == "全部状态" or task.status == selected_status
            if match_group and match_status:
                filtered.append(task)

        self.update_task_list(filtered)

    def _get_all_tasks(self):
        def collect(group):
            tasks = list(group.tasks)
            for child in group.children:
                tasks.extend(collect(child))
            return tasks

        return collect(self.group_manager.root_group)

    def on_group_selected(self, item, column):
        selected_group = item.text(column)
        if selected_group == "根任务组":
            current_tasks = self._get_all_tasks()
            self.update_task_list(current_tasks)
        else:
            tasks = self.group_manager.get_tasks_by_group(selected_group)
            self.update_task_list(tasks)

    def update_task_list(self, tasks):
        self.table_model.removeRows(0, self.table_model.rowCount())

        status_icons = {
            "就绪": "🔄",
            "运行中": "⏳",
            "成功": "✅",
            "失败": "❌"
        }

        for task in tasks:
            status_text = task.status or "就绪"
            icon = status_icons.get(status_text, "📝")

            items = [
                QStandardItem(task.id),
                QStandardItem(task.name),
                QStandardItem(f"{icon} {status_text}"),
                QStandardItem(task.task_type),
                QStandardItem(task.group or ""),
                QStandardItem(str(task.retry_count)),
            ]

            if status_text == "成功":
                items[2].setBackground(Qt.green)
                items[2].setForeground(Qt.white)
            elif status_text == "失败":
                items[2].setBackground(Qt.red)
                items[2].setForeground(Qt.white)
            elif status_text == "运行中":
                items[2].setBackground(Qt.yellow)
            elif status_text == "就绪":
                items[2].setBackground(QColor("#f0f0f0"))

            self.table_model.appendRow(items)

    def update_task_status(self, row):
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        index = proxy.mapToSource(proxy.index(row, 0))

        task_item = source.item(index.row(), 0)
        if not task_item:
            return

        task_id = task_item.text()
        task = self.find_task_by_id(task_id)
        if not task:
            return

        status_index = index.siblingAtColumn(2)
        source.setData(status_index, f"{task.status}")

    def log_message(self, level, message):
        self.log_panel.log(level, message)

    def find_task_by_id(self, task_id):
        for group in self.group_manager.get_all_groups():
            for task in group.tasks:
                if task.id == task_id:
                    return task
        return None

    def start_task_execution(self):
        current_tasks = self._get_all_tasks()
        self.task_executor = TaskExecutor()
        self.task_executor.log_signal.connect(self.log_message)
        self.task_executor.task_status_updated.connect(self.update_task_status)
        self.task_executor.finished.connect(self.task_executor.deleteLater)

        self.task_executor.set_tasks(current_tasks)
        self.task_executor.start()

    def stop_task_execution(self):
        if self.task_executor.isRunning():
            self.task_executor.stop()

    def show_task_context_menu(self, position):
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        index = self.task_table.indexAt(position)
        if not index.isValid():
            return

        row = proxy.mapToSource(index).row()
        task_item = source.item(row, 0)
        if not task_item:
            return

        menu = QMenu(self.task_table)
        move_up = menu.addAction("⬆ 上移")
        move_down = menu.addAction("⬇ 下移")
        delete = menu.addAction("🗑 删除")

        action = menu.exec_(self.task_table.viewport().mapToGlobal(position))

        if action == move_up:
            self.move_task_row(row, -1)
        elif action == move_down:
            self.move_task_row(row, +1)
        elif action == delete:
            self.delete_task_row(row)

    def on_task_double_clicked(self, index):
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        row = proxy.mapToSource(index).row()

        task_item = source.item(row, 0)
        if not task_item:
            print("❌ 当前选中项为空")
            return

        task_id = task_item.text()
        task = self.find_task_by_id(task_id)
        if not task:
            return

        dialog = TaskEditDialog(self)
        dialog.name_input.setText(task.name)
        dialog.type_combo.setCurrentText(task.task_type)
        dialog.group_input.setText(task.group or "")
        dialog.param_input.setText(str(task.parameters))

        if dialog.exec_() == TaskEditDialog.Accepted:
            try:
                import json
                data = dialog.get_task_data()
                params = json.loads(data["parameters"])

                task.name = data["name"]
                task.task_type = data["task_type"]
                task.parameters = params
                task.group = data["group"]

                self.update_task_list(self._get_all_tasks())
            except Exception as e:
                print(f"❌ 更新任务失败: {e}")

    def move_task_row(self, row, direction):
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()

        if not (0 <= row < source_model.rowCount()):
            return

        task_item = source_model.item(row, 0)
        target_row = row + direction
        if not (0 <= target_row < source_model.rowCount()):
            return

        task_id = task_item.text()
        task = self.find_task_by_id(task_id)
        if not task or not task.group:
            print("❌ 源或目标任务组为空")
            return

        group = self.group_manager.find_group_by_name(task.group)
        if not group:
            print("❌ 找不到对应的任务组")
            return

        tasks = group.tasks[:]
        for i, t in enumerate(tasks):
            if t.id == task_id:
                moved_task = tasks.pop(i)
                tasks.insert(i + direction, moved_task)
                break

        group.tasks = tasks
        self.save_current_groups(force_dialog=False)
        self.update_task_list(self._get_all_tasks())

    def delete_task_row(self, row):
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        source.removeRow(row)
        self._update_task_order_in_group(source)

    def _update_task_order_in_group(self, source_model):
        updated_ids = [source_model.item(i, 0).text() for i in range(source_model.rowCount())]
        print("更新后的任务顺序:", updated_ids)

    def closeEvent(self, event):
        try:
            save_task_groups(self.group_manager)
            self.settings.setValue("window/geometry", self.saveGeometry())
            event.accept()
        except Exception as e:
            print(f"保存失败: {e}")
            event.ignore()

    def save_current_groups(self, force_dialog=False):
        if not force_dialog and self.current_save_path:
            success = self.group_manager.save_to_file(self.current_save_path)
            if success:
                self.log_message("INFO", f"✅ 已自动保存至 {self.current_save_path}")
            else:
                self.log_message("ERROR", "❌ 自动保存失败")
            return

        path, _ = QFileDialog.getSaveFileName(self, "保存任务组", self.current_save_path, "JSON (*.json)")
        if path:
            self.current_save_path = path
            success = self.group_manager.save_to_file(path)
            if success:
                self.log_message("INFO", f"✅ 已保存至 {path}")
            else:
                self.log_message("ERROR", "❌ 保存失败")

    def save_current_groups_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "另存为", "", "JSON (*.json)")
        if path:
            success = self.group_manager.save_to_file(path)
            if success:
                self.log_message("INFO", f"✅ 已另存为 {path}")
                self.current_save_path = path
            else:
                self.log_message("ERROR", "❌ 另存为失败")

    def save_current_groups(self, force_dialog=False):
        """
        保存当前任务组（可选弹窗）
        :param force_dialog: 是否强制弹出选择路径对话框
        """
        if not force_dialog and self.current_save_path:
            success = self.group_manager.save_to_file(self.current_save_path)
            if success:
                self.log_message("INFO", f"✅ 已自动保存至 {self.current_save_path}")
            else:
                self.log_message("ERROR", "❌ 自动保存失败")
            return

        path, _ = QFileDialog.getSaveFileName(self, "保存任务组", self.current_save_path, "JSON (*.json)")
        if path:
            self.current_save_path = path
            success = self.group_manager.save_to_file(path)
            if success:
                self.log_message("INFO", f"✅ 已保存至 {path}")
            else:
                self.log_message("ERROR", "❌ 保存失败")

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_groups)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_current_groups_as)


class TaskTableView(QTableView):
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTableView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        super().dropEvent(event)
        current_index = self.currentIndex()
        if current_index.isValid() and self.main_window:
            self.main_window.move_task_row(current_index.row(), 0)
