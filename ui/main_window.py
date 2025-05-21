# ui/main_window.py

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QShortcut,
    QComboBox, QSlider, QCheckBox, QPushButton,
    QTableView, QHeaderView, QSplitter, QFrame, QApplication, QFileDialog, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from ui.log_panel import LogPanel
from managers.group_manager import GroupManager
from ui.task_group_panel import TaskGroupPanel
from utils.persistence import save_task_groups, load_task_groups
from ui.task_edit_dialog import TaskEditDialog
from engine.task_executor import TaskExecutor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.task_executor = TaskExecutor()
        self.task_executor.log_signal.connect(self.log_message)
        self.task_executor.task_status_updated.connect(self.update_task_status)
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
        self.group_panel = TaskGroupPanel(self.group_manager, self)
        self.group_panel.itemClicked.connect(self.on_group_selected)

        # 初始化其他内容
        self.setWindowTitle("自动化任务辅助工具")

        self.init_ui()
        self.setup_shortcuts()

        # ✅ 添加这一行，在 UI 初始化后主动加载任务
        self.update_task_list(self._get_all_tasks())

    def update_task_status(self, row):
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()

        task_item = source_model.item(row, 0)
        if task_item:
            task_id = task_item.text()
            task = self.find_task_by_id(task_id)
            if task:
                # 更新状态列
                status_index = source_model.index(row, 2)
                source_model.setData(status_index, task.status)

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
        # ===== 分割面板：左侧任务组 + 右侧任务表格 =====
        splitter = QSplitter(Qt.Horizontal)

        # 左侧面板：任务组树状结构
        self.group_panel = TaskGroupPanel(self.group_manager, self)  # 把 self 传给 group_panel
        group_frame = QFrame()
        group_frame.setLayout(QVBoxLayout())
        group_frame.layout().addWidget(self.group_panel)
        group_frame.setFrameShape(QFrame.StyledPanel)

        # ===== 创建并添加控制栏 =====
        control_layout = self._create_control_bar()
        main_layout.addLayout(control_layout)

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
        print("LogPanel 实例:", self.log_panel)  # ✅ 打印是否为 None
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
#  绑定按钮点击事件
        self.start_button.clicked.connect(self.start_task_execution)
        self.stop_button.clicked.connect(self.stop_task_execution)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)

        return control_layout

    def start_task_execution(self):
        """点击开始按钮执行任务"""
        current_tasks = self._get_all_tasks()  # 或根据当前分组获取任务

        # ✅ 每次执行都新建线程，防止状态混乱
        self.task_executor = TaskExecutor()
        self.task_executor.log_signal.connect(self.log_message)
        self.task_executor.task_status_updated.connect(self.update_task_status)
        self.task_executor.finished.connect(self.task_executor.deleteLater)  # 自动清理线程资源

        self.task_executor.set_tasks(current_tasks)
        self.task_executor.start()  # ✅ 使用 QThread.start() 启动


    def stop_task_execution(self):
        """点击停止按钮终止任务执行"""
        self.task_executor.stop()

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

        # ✅ 启用拖放支持
        table_view.setDragEnabled(True)
        table_view.setAcceptDrops(True)
        table_view.setDropIndicatorShown(True)
        table_view.setDragDropMode(QTableView.InternalMove)  # 内部移动
        table_view.setDefaultDropAction(Qt.MoveAction)

        # ✅ 绑定右键菜单事件
        table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        table_view.customContextMenuRequested.connect(self.show_task_context_menu)

        # ✅ 绑定双击事件
        table_view.doubleClicked.connect(self.on_task_double_clicked)
#  任务行拖放事件处理
        table_view.dropEvent = self.on_task_row_moved
        return table_view

    def show_task_context_menu(self, position):
        """显示任务表格右键菜单"""
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()
        index = self.task_table.indexAt(position)
        if not index.isValid():
            return

        row = proxy_model.mapToSource(index).row()
        task_item = source_model.item(row, 0)
        if not task_item:
            return

        menu = QMenu(self.task_table)
        move_up_action = QAction("⬆ 上移", self)
        move_down_action = QAction("⬇ 下移", self)
        delete_action = QAction("🗑 删除", self)

        menu.addAction(move_up_action)
        menu.addAction(move_down_action)
        menu.addSeparator()
        menu.addAction(delete_action)

        action = menu.exec_(self.task_table.viewport().mapToGlobal(position))

        if action == move_up_action:
            self.move_task_row(row, -1)
        elif action == move_down_action:
            self.move_task_row(row, +1)
        elif action == delete_action:
            self.delete_task_row(row)

    def move_task_row(self, row, direction):
        """将指定行向上或向下移动"""
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()

        if 0 <= row + direction < source_model.rowCount():
            # ✅ 取出当前行的所有列项（已经是 QStandardItem 列表）
            items = source_model.takeRow(row)
            source_model.insertRow(row + direction, items)

            # 更新实际任务顺序
            updated_tasks = [
                source_model.item(i, 0).text()  # 假设 ID 是第一列
                for i in range(source_model.rowCount())
            ]
            print("更新后的任务顺序:", updated_tasks)

    def delete_task_row(self, row):
        """删除指定行的任务"""
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()
        source_model.removeRow(row)

        # 更新任务列表
        updated_tasks = [
            source_model.item(i, 0).text()
            for i in range(source_model.rowCount())
        ]
        print("删除后任务列表:", updated_tasks)

    def on_task_row_moved(self, event):
        """处理任务行拖放事件"""
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()

        # 获取源索引和目标索引
        dragged_row = self.task_table.selectedIndexes()[0].row()
        target_index = self.task_table.indexAt(event.pos())
        if not target_index.isValid():
            return

        target_row = proxy_model.mapToSource(target_index).row()

        # 获取当前任务列表并交换位置
        current_tasks = self._get_all_tasks()  # 或者根据当前分组获取任务列表
        moved_task = current_tasks.pop(dragged_row)
        current_tasks.insert(target_row, moved_task)

        # 刷新任务列表
        self.update_task_list(current_tasks)

    def find_task_by_id(self, task_id):
        """根据任务 ID 查找任务对象"""
        for group in self.group_manager.get_all_groups():
            for task in group.tasks:
                if task.id == task_id:
                    return task
        return None
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

            # 设置状态颜色
            if task.status == "成功":
                items[2].setBackground(Qt.green)
            elif task.status == "失败":
                items[2].setBackground(Qt.red)
            elif task.status == "运行中":
                items[2].setBackground(Qt.yellow)

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
        print(f"[LOG] {level}: {message}")  # ✅ 用于调试，确认是否收到信号
        self.log_panel.log(level, message)

    def on_task_double_clicked(self, index):
        """双击任务项时弹出编辑对话框"""
        proxy_model = self.task_table.model()
        source_model = proxy_model.sourceModel()
        row = proxy_model.mapToSource(index).row()

        task_item = source_model.item(row, 0)
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
                from models.task_model import Task
                import json
                data = dialog.get_task_data()
                parameters = json.loads(data["parameters"])

                # 更新任务属性
                task.name = data["name"]
                task.task_type = data["task_type"]
                task.parameters = parameters
                task.group = data["group"]

                # 刷新表格
                self.update_task_list(self._get_all_tasks())
            except Exception as e:
                print(f"更新任务失败: {e}")