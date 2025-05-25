# ui/main_window.py
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QShortcut,
    QComboBox, QSlider, QCheckBox, QPushButton, QTableView, QHeaderView,
    QSplitter, QFrame, QApplication, QFileDialog, QMenu, QAction,
    QUndoStack, QUndoCommand, QLabel, QLineEdit
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QSettings, pyqtSignal
from PyQt5.QtGui import QKeySequence, QColor, QStandardItemModel, QStandardItem

from models.task_model import Task
from ui.log_panel import LogPanel
from managers.group_manager import GroupManager
from ui.task_group_panel import TaskGroupPanel
from utils.persistence import save_task_groups, load_task_groups
from ui.task_edit_dialog import TaskEditDialog
from engine.task_executor import TaskExecutor

logger = logging.getLogger(__name__)

class TaskOrderCommand(QUndoCommand):
    """任务排序的撤销命令"""

    def __init__(self, group_manager, old_orders, new_orders, description="Reorder Tasks"):
        super().__init__(description)
        self.group_manager = group_manager
        self.old_orders = old_orders
        self.new_orders = new_orders

    def redo(self):
        """执行排序操作"""
        for task_id, group_name, order in self.new_orders:
            task = self.find_task_by_id(task_id)
            if task:
                task.order = order

        # 更新所有组的任务顺序
        self._update_group_tasks()
        logger.info("✅ 执行排序操作")

    def undo(self):
        """撤销排序操作"""
        for task_id, group_name, order in self.old_orders:
            task = self.find_task_by_id(task_id)
            if task:
                task.order = order

        # 更新所有组的任务顺序
        self._update_group_tasks()
        logger.info("✅ 撤销排序操作")

    def _update_group_tasks(self):
        """根据任务的新顺序更新各组的任务列表"""
        logger.info("🔄 开始更新各组任务列表")

        # 创建一个以任务ID为键的映射表
        task_map = {}
        all_groups = self.group_manager.get_all_groups()

        # 收集所有任务
        for group in all_groups:
            for task in group.tasks:
                task_map[task.id] = task

        # 遍历所有组
        for group in all_groups:
            try:
                # 获取该组的所有任务（保持原有顺序）
                group_tasks = []
                for task_id in [t.id for t in group.tasks]:  # 保留原有序号
                    task = task_map.get(task_id)
                    if task and (task.group == group.name or getattr(task, 'group', None) == group.name):
                        group_tasks.append(task)

                # 只有当任务确实属于该组时才更新
                if group.tasks != group_tasks:
                    logger.debug(f"📌 更新组 [{group.name}] 的任务列表")
                    group.tasks = group_tasks.copy()

            except Exception as e:
                logger.error(f"❌ 更新组 [{group.name}] 时发生错误: {str(e)}", exc_info=True)

        logger.info("✅ 组任务列表更新完成")

    def find_task_by_id(self, task_id):
        """通过任务ID查找任务"""
        for group in self.group_manager.get_all_groups():
            for task in group.tasks:
                if task.id == task_id:
                    return task
        return None


class MainWindow(QMainWindow):
    tasks_reordered = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动化任务辅助工具")
        self.resize(1200, 800)
        print("✅ 初始化主窗口")

        # 初始化撤销栈
        self.undo_stack = QUndoStack(self)

        # 初始化 QSettings 和保存路径
        self.settings = QSettings("MyCompany", "AutomationTool")
        self.current_save_path = "tasks.json"

        # 初始化任务组管理器
        loaded_group = load_task_groups()
        print("✅ 加载配置文件中的任务组:", loaded_group)
        self.group_manager = GroupManager()
        if loaded_group:
            self.group_manager.root_group = loaded_group
            print("✅ 成功加载已保存的任务组")
        else:
            print("⚠️ 配置文件不存在，使用默认任务组")
            self._init_default_groups()

        # 初始化 UI
        self.init_ui()
        self.setup_shortcuts()
        self.restore_window_state()

        # 刷新任务列表
        tasks = self._get_all_tasks()
        print(f"📊 初始化时共加载 {len(tasks)} 个任务")
        self.update_task_list(tasks)

    def init_ui(self):
        print("✅ 开始初始化主窗口 UI")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()

        splitter = QSplitter(Qt.Horizontal)

        # 左侧任务组面板
        self.group_panel = TaskGroupPanel(self.group_manager, self)
        self.group_panel.itemClicked.connect(self.on_group_selected)
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

        # 序号列显示
        self.order_label = QLabel("序号:")
        self.order_input = QLineEdit()
        self.order_input.setFixedWidth(50)
        control_layout.addWidget(self.order_label)
        control_layout.addWidget(self.order_input)

        # 撤销/重做按钮
        self.undo_button = QPushButton("撤销 (Ctrl+Z)")
        self.redo_button = QPushButton("重做 (Ctrl+Y)")
        self.undo_button.clicked.connect(self.undo_stack.undo)
        self.redo_button.clicked.connect(self.undo_stack.redo)
        control_layout.addWidget(self.undo_button)
        control_layout.addWidget(self.redo_button)

        # 加载样式表
        try:
            with open("resources/style.qss", "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
            print("✅ 样式表加载成功")
        except Exception as e:
            print(f"⚠️ 样式表加载失败: {e}")

        main_widget.setLayout(main_layout)

    def _create_task_table(self):
        """创建任务表格"""
        print("✅ 创建任务表格")

        # 使用标准 QTableView
        table_view = QTableView()

        # 初始化数据模型
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            "ID", "名称", "状态", "操作类型", "分组", "重试次数", "序号"
        ])

        # 设置代理模型用于排序和过滤
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(self.table_model)
        table_view.setModel(proxy_model)

        # 设置表头自动拉伸填充
        header = table_view.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch if i < 6 else QHeaderView.ResizeToContents)

        # 设置表格行为
        table_view.setSelectionBehavior(QTableView.SelectRows)  # 按行选中
        table_view.setSelectionMode(QTableView.MultiSelection)  # 支持多选
        table_view.setContextMenuPolicy(Qt.CustomContextMenu)  # 自定义右键菜单
        table_view.customContextMenuRequested.connect(self.show_task_context_menu)  # 绑定右键事件
        table_view.doubleClicked.connect(self.on_task_double_clicked)  # 双击编辑任务

        # 移除所有与拖放相关的设置
        # 删除了以下配置：
        # - setDragEnabled
        # - setAcceptDrops
        # - setDropIndicatorShown
        # - setDragDropMode
        # - viewport().setAcceptDrops
        # - model().rowsMoved.connect

        return table_view

    def update_task_list(self, tasks=None):
        """刷新任务列表"""
        assert tasks is not None, "❌ 参数错误：tasks 不能为 None"
        print("🔄 开始刷新任务列表...")

        # 如果没有提供任务列表，则获取所有任务
        if tasks is None:
            tasks = self._get_all_tasks()

        self.table_model.setRowCount(0)

        # 按照分组和序号排序
        sorted_tasks = sorted(tasks, key=lambda t: (t.group or "", getattr(t, 'order', 0)))

        # 更新任务列表显示
        for idx, task in enumerate(sorted_tasks):
            print(f"📝 第 {idx + 1} 条任务:")
            print(f"   ID: {task.id}")
            print(f"   名称: {task.name}")
            print(f"   状态: {task.status}")
            print(f"   类型: {task.task_type}")
            print(f"   分组: {task.group or '无'}")

            items = [
                QStandardItem(task.id),
                QStandardItem(task.name),
                QStandardItem(task.status),
                QStandardItem(task.task_type),
                QStandardItem(task.group or ""),
                QStandardItem(str(task.retry_count)),
                QStandardItem(str(getattr(task, 'order', idx)))
            ]
            self.table_model.appendRow(items)

        print(f"✅ 任务列表刷新完成，共显示 {len(sorted_tasks)} 条任务")

        # 通知其他组件任务列表已更新
        self.tasks_reordered.emit()

    def show_task_context_menu(self, position):
        """任务表格右键菜单"""
        menu = QMenu(self.task_table)

        edit_action = QAction("编辑任务", self)
        delete_action = QAction("删除任务", self)
        move_to_group_action = QAction("移动到其他任务组", self)
        set_order_action = QAction("设置序号", self)

        edit_action.triggered.connect(self._edit_selected_task)
        delete_action.triggered.connect(self._delete_selected_task)
        move_to_group_action.triggered.connect(lambda: self._move_selected_tasks_to_group())
        set_order_action.triggered.connect(self._set_custom_order)

        menu.addAction(edit_action)
        menu.addAction(delete_action)
        menu.addAction(move_to_group_action)
        menu.addAction(set_order_action)

        menu.exec_(self.task_table.viewport().mapToGlobal(position))

    def _set_custom_order(self):
        """手动设置任务序号"""
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        indexes = self.task_table.selectedIndexes()

        if not indexes:
            print("❌ 设置序号失败：未选中任何任务")
            self.log_message("ERROR", "请先选择要设置序号的任务")
            return

        from PyQt5.QtWidgets import QInputDialog
        order, ok = QInputDialog.getInt(
            self,
            "设置自定义序号",
            "请输入起始序号:",
            value=0,
            min=0,
            max=1000
        )

        if not ok:
            return

        selected_rows = set(proxy.mapToSource(index).row() for index in indexes)
        updated_tasks = []

        for row in sorted(selected_rows):
            task_item = source.item(row, 0)
            if task_item:
                task_id = task_item.text()
                task = self.find_task_by_id(task_id)
                if task:
                    task.order = order
                    updated_tasks.append(task)
                    print(f"📌 更新任务 [{task.name}] 的序号为 {order}")
                    order += 1

        if updated_tasks:
            self.undo_stack.push(TaskOrderCommand(
                self.group_manager,
                [(t.id, t.group, getattr(t, 'order', 0)) for t in updated_tasks],
                [(t.id, t.group, t.order) for t in updated_tasks]
            ))
            self.update_task_list(self._get_all_tasks())
            self.log_message("SUCCESS", f"成功设置 {len(updated_tasks)} 个任务的序号")

    def setup_shortcuts(self):
        print("✅ 设置快捷键 Ctrl+S / Ctrl+Shift+S / Ctrl+Z / Ctrl+Y")
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_groups)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self.save_current_groups_as)
        QShortcut(QKeySequence("Ctrl+Z"), self, self.undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self, self.undo_stack.redo)

    def _move_selected_tasks_to_group(self, target_group=None, task_ids=None):
        """将选中的多个任务移动到其他任务组"""
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        indexes = self.task_table.selectedIndexes()

        if not indexes and not task_ids:
            print("❌ 移动失败：未选中任何任务")
            return False

        # 提取所有选中任务的 ID 或使用传入的 ID
        selected_rows = set(proxy.mapToSource(index).row() for index in indexes)
        task_ids = task_ids or []

        for row in selected_rows:
            task_item = source.item(row, 0)
            if task_item:
                task_id = task_item.text()
                task = self.find_task_by_id(task_id)
                if task:
                    task_ids.append(task_id)

        if not task_ids:
            print("❌ 没有可移动的任务")
            return False

        # 如果没有指定目标分组，弹出选择对话框
        if not target_group:
            from PyQt5.QtWidgets import QInputDialog
            target_group, ok = QInputDialog.getItem(
                self,
                "选择目标任务组",
                "请选择要移动到的任务组:",
                [group.name for group in self.group_manager.get_all_groups()],
                editable=False
            )

            if not (ok and target_group):
                print("❌ 任务移动取消")
                return False

        moved = self.group_panel.on_move_to_group(target_group, task_ids)
        if moved:
            print(f"✅ 共 {len(task_ids)} 个任务已成功移动到 [{target_group}]")
            # 更新所有任务的 order 字段
            self._update_task_orders_in_group(target_group)
            self.update_task_list(self._get_all_tasks())
            return True
        else:
            print(f"⚠️ 移动失败或没有任务被移动")
            return False

    def _update_task_orders_in_group(self, group_name):
        """更新指定分组中任务的序号"""
        group = self.group_manager.find_group_by_name(group_name)
        if group and hasattr(group, 'tasks'):
            for idx, task in enumerate(group.tasks):
                task.order = idx
                print(f"📝 更新任务 [{task.name}] 的序号为 {idx}")

    def log_message(self, level, message):
        """接收并转发日志信息到日志面板"""
        print(f"[{level}] {message}")
        self.log_panel.log(level, message)

    def save_current_groups(self):
        """保存当前任务组配置"""
        try:
            self.group_manager.save_to_file(self.current_save_path)
            self.log_message("SUCCESS", "任务配置保存成功")
        except Exception as e:
            self.log_message("ERROR", f"保存任务配置失败: {e}")

    def save_current_groups_as(self):
        """另存为任务组配置"""
        file_path, _ = QFileDialog.getSaveFileName(self, "保存任务配置", "", "JSON 文件 (*.json)")
        if file_path:
            try:
                self.group_manager.save_to_file(file_path)
                self.current_save_path = file_path
                self.log_message("SUCCESS", f"任务配置另存为成功: {file_path}")
            except Exception as e:
                self.log_message("ERROR", f"保存任务配置失败: {e}")

    def closeEvent(self, event):
        print("🚪 窗口关闭事件触发")
        try:
            self.group_manager.save_to_file()
            self.settings.setValue("window/geometry", self.saveGeometry())
            event.accept()
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            event.ignore()

    def apply_filters(self):
        """根据状态筛选任务列表"""
        selected_status = self.status_filter_combo.currentText()
        all_tasks = self._get_all_tasks()
        print(f"🔍 正在应用状态筛选: {selected_status}")

        if selected_status == "全部状态":
            filtered_tasks = all_tasks
        else:
            filtered_tasks = [task for task in all_tasks if task.status == selected_status]

        print(f"📊 筛选后任务数量: {len(filtered_tasks)}")
        self.update_task_list(filtered_tasks)

    def on_group_selected(self, item):
        """当任务组被点击时触发"""
        group_name = item.text(0)
        print(f"📌 点击了任务组: {group_name}")

        # 打印当前根任务组结构
        print("🔍 当前根任务组结构:")

        def _print_group_structure(group, indent=0):
            try:
                print(f"{' ' * indent}📁 {group.name} ({len(group.tasks)}个任务)")
                for child in group.children:
                    _print_group_structure(child, indent + 4)
            except Exception as e:
                print(f"❌ 打印结构时发生错误: {e}")

        _print_group_structure(self.group_manager.root_group)

        # 获取当前分组的任务列表
        try:
            tasks = self.group_manager.get_tasks_by_group(group_name)

            # 打印返回的任务详情
            print(f"📂 返回的任务列表 (共 {len(tasks)} 条):")
            if not tasks:
                print("⚠️ 该分组下没有任务")
            else:
                for t in tasks:
                    print(f" - {t.name} (ID: {t.id}, 分组: {t.group})")

            # 刷新任务表格
            self.update_task_list(tasks)
        except Exception as e:
            print(f"❌ 处理任务组 [{group_name}] 时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def _init_default_groups(self):
        daily = self.group_manager.create_group("日常任务")
        weekly = self.group_manager.create_group("周常任务")

        daily.tasks = [
            Task(name="每日签到", task_type="click", parameters={"location": [100, 200]}, group="日常任务"),
            Task(name="每日副本", task_type="match", parameters={"template": "daily.png"}, group="日常任务")
        ]

        weekly.tasks = [
            Task(name="周常副本", task_type="match", parameters={"template": "weekly.png"}, group="周常任务"),
            Task(name="周常挑战", task_type="click", parameters={"location": [300, 400]}, group="周常任务")
        ]

        print("✅ 默认任务组初始化完成")
        for group in self.group_manager.get_all_groups():
            print(f" - {group.name}：{len(group.tasks)} 个任务")

    def _get_all_tasks(self):
        """获取所有任务（包括子组）"""
        logger.debug("📊 开始收集所有任务")

        def collect(group):
            logger.debug(f"🔍 收集任务组 [{group.name}] 的任务（{len(group.tasks)} 个）")
            tasks = group.tasks.copy()

            # 验证每个任务的ID是否存在
            for task in tasks:
                if not hasattr(task, 'id'):
                    logger.warning(f"⚠️ 发现任务缺少ID: {task.name}")
                    task.id = Task.generate_unique_id()

            for child in group.children:
                logger.debug(f"👉 进入子组: {child.name}")
                child_tasks = collect(child)
                tasks.extend(child_tasks)

            return tasks

        result = collect(self.group_manager.root_group)
        logger.info(f"📊 共计获取任务数量: {len(result)}")

        # 添加调试日志，显示部分任务信息
        if result and len(result) > 0:
            logger.debug(f"📌 样本任务信息 - 第一个任务ID: {result[0].id}, 最后一个任务ID: {result[-1].id}")

        return result

    def _edit_selected_task(self):
        """编辑当前选中的任务"""
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        indexes = self.task_table.selectedIndexes()

        if not indexes:
            print("❌ 编辑失败：未选中任何任务")
            return

        row = proxy.mapToSource(indexes[0]).row()
        task_item = source.item(row, 0)

        if not task_item:
            print("❌ 获取任务失败：选中项为空")
            return

        task_id = task_item.text()
        task = self.find_task_by_id(task_id)

        if not task:
            print(f"❌ 找不到对应的任务 ID: {task_id}")
            return

        try:
            dialog = TaskEditDialog(self)
            dialog.name_input.setText(task.name)
            dialog.type_combo.setCurrentText(task.task_type)
            dialog.group_combo.setCurrentText(task.group or "")
            dialog.param_input.setText(str(task.parameters))

            if dialog.exec_() == TaskEditDialog.Accepted:
                import json
                data = dialog.get_task_data()
                params = json.loads(data["parameters"])

                task.name = data["name"]
                task.task_type = data["task_type"]
                task.parameters = params
                task.group = data["group"]

                print(f"✅ 任务 [{task.name}] 已更新")
                self.update_task_list(self._get_all_tasks())
        except Exception as e:
            print(f"❌ 更新任务失败: {e}")
            import traceback
            traceback.print_exc()

    def _delete_selected_task(self):
        """删除当前选中的任务"""
        proxy = self.task_table.model()
        source = proxy.sourceModel()
        indexes = self.task_table.selectedIndexes()

        if not indexes:
            print("❌ 删除失败：未选中任何任务")
            return

        row = proxy.mapToSource(indexes[0]).row()
        task_item = source.item(row, 0)

        if not task_item:
            print("❌ 获取任务失败：选中项为空")
            return

        task_id = task_item.text()
        task = self.find_task_by_id(task_id)

        if not task:
            print(f"❌ 找不到对应的任务 ID: {task_id}")
            return

        group_name = task.group
        if group_name:
            self.group_manager.remove_task_from_group(group_name, task_id)
            print(f"🗑️ 任务 [{task.name}] 已从分组 [{group_name}] 中删除")
            self.update_task_list(self._get_all_tasks())

    def find_task_by_id(self, task_id):
        """查找指定ID的任务"""
        logger.debug(f"🔍 开始查找任务 ID: {task_id}")

        all_tasks = self._get_all_tasks()
        for task in all_tasks:
            if task.id == task_id:
                logger.debug(f"✅ 找到任务 [{task.name}] (ID: {task.id})")
                return task

        logger.warning(f"❌ 未找到任务 ID: {task_id}")
        return None

    def _create_control_bar(self):
        """创建控制栏"""
        print("✅ 创建控制栏")
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

    def start_task_execution(self):
        """开始执行任务"""
        if not self.task_executor.isRunning():
            selected_group = self.group_combo.currentText()
            print(f"▶️ 开始执行任务，目标分组: {selected_group}")
            if selected_group == "全部分组":
                tasks = self._get_all_tasks()
            else:
                tasks = self.group_manager.get_tasks_by_group(selected_group)

            print(f"🎯 即将执行任务数: {len(tasks)}")
            self.task_executor.set_tasks(tasks)
            self.task_executor.start()

    def stop_task_execution(self):
        """停止任务执行"""
        if self.task_executor.isRunning():
            print("🛑 停止任务执行")
            self.task_executor.stop()

    def restore_window_state(self):
        """恢复窗口状态"""
        print("🔄 恢复窗口状态")
        if self.settings.contains("window/geometry"):
            geometry = self.settings.value("window/geometry")
            self.restoreGeometry(geometry)
        else:
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)

    def on_task_double_clicked(self, index):
        """双击任务进行编辑"""
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
            print(f"❌ 找不到对应的任务 ID: {task_id}")
            return

        try:
            dialog = TaskEditDialog(self)
            dialog.name_input.setText(task.name)
            dialog.type_combo.setCurrentText(task.task_type)
            dialog.group_combo.setCurrentText(task.group or "")
            dialog.param_input.setText(str(task.parameters))

            if dialog.exec_() == TaskEditDialog.Accepted:
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
            import traceback
            traceback.print_exc()

    def get_task_order(self, task):
        """获取任务的序号"""
        return getattr(task, 'order', 0)
