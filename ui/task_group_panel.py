# ui/task_group_panel.py

import logging
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDrag
from utils.input_dialog import InputDialog
from ui.task_edit_dialog import TaskEditDialog

# 设置本文件专用 logger
logger = logging.getLogger(__name__)


class TaskGroupPanel(QTreeWidget):
    def __init__(self, group_manager, main_window):
        super().__init__()
        logger.debug("初始化 TaskGroupPanel 开始")

        self.group_manager = group_manager
        self.main_window = main_window

        self.setHeaderLabel("任务组")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # 拖放设置
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QTreeWidget.InternalMove)

        self.refresh()

        logger.debug("初始化 TaskGroupPanel 完成")

    def refresh(self):
        """刷新任务组面板"""
        logger.info("开始刷新任务组面板")

        self.clear()
        root_name = self.group_manager.root_group.name
        logger.debug(f"添加根任务组: {root_name}")

        root_item = QTreeWidgetItem([root_name])
        self.addTopLevelItem(root_item)
        self._build_tree(self.group_manager.root_group, root_item)

        logger.info("任务组面板刷新完成")

    def _build_tree(self, group, parent_item):
        """递归构建 UI 树状结构"""
        logger.debug(f"开始构建子树: {group.name} (父项: {parent_item.text(0)})")

        for child in group.children:
            logger.info(f"添加子任务组: {child.name}")
            new_item = QTreeWidgetItem([child.name])
            parent_item.addChild(new_item)
            self._build_tree(child, new_item)  # 递归构建下一级

        logger.debug(f"{group.name} 的子树构建完成")

    def startDrag(self, supported_actions):
        """开始拖动操作"""
        logger.debug(f"触发拖动事件: 支持的操作={supported_actions}")
        drag = QDrag(self)
        mime_data = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)
        logger.debug("拖动操作结束")

    def dropEvent(self, event):
        """处理放置事件"""
        logger.info("触发放置事件")

        super().dropEvent(event)
        source_index = self.selectedIndexes()[0]
        target_index = self.indexAt(event.pos())
        source_item = self.itemFromIndex(source_index)
        target_item = self.itemFromIndex(target_index)

        if not source_item or not target_item:
            logger.warning("源或目标为空，无法移动任务")
            return

        source_group = source_item.parent().text(0) if source_item.parent() else "根任务组"
        target_group = target_item.text(0)
        task_id = source_item.text(0)

        logger.info(f"请求将任务 [{task_id}] 从 [{source_group}] 移动到 [{target_group}]")
        self.move_task_between_groups(source_group, target_group, task_id)

    def move_task_between_groups(self, source_group, target_group, task_id):
        """实际执行任务在任务组之间的移动"""
        logger.debug(f"尝试移动任务: {task_id} -> {source_group} => {target_group}")

        source_group_obj = self.group_manager.find_group_by_name(source_group)
        target_group_obj = self.group_manager.find_group_by_name(target_group)

        if not source_group_obj:
            logger.error(f"源任务组 [{source_group}] 不存在")
            return
        if not target_group_obj:
            logger.error(f"目标任务组 [{target_group}] 不存在")
            return

        moved = False
        for task in source_group_obj.tasks:
            if task.id == task_id:
                logger.info(f"找到任务 [{task.name}], 准备移动")
                source_group_obj.tasks.remove(task)
                target_group_obj.tasks.append(task)
                task.group = target_group
                moved = True
                break

        if moved:
            logger.info(f"任务 [{task_id}] 已成功移动到 [{target_group}]")
            self.main_window.update_task_list(
                self.group_manager.get_tasks_by_group(target_group)
            )
        else:
            logger.warning(f"任务 [{task_id}] 在 [{source_group}] 中未找到")

    def show_context_menu(self, position):
        """显示右键菜单"""
        logger.debug("显示右键菜单")
        item = self.itemAt(position)
        if not item:
            logger.warning("右键点击位置无效")
            return

        menu = QMenu(self)

        new_task_action = menu.addAction("新建任务")
        selected_name = item.text(0)

        menu.addSeparator()

        new_group_action = menu.addAction("新建任务组")
        new_group_action.triggered.connect(lambda _: self.on_new_group(selected_name))

        if selected_name != "根任务组":
            delete_group_action = menu.addAction("删除任务组")
            delete_group_action.triggered.connect(lambda: self.on_delete_group(selected_name))

            move_to_submenu = menu.addMenu("移动到其他分组")
            all_groups = self.group_manager.get_all_groups()
            for group in all_groups:
                if group.name != selected_name:
                    action = move_to_submenu.addAction(group.name)
                    action.setData(group.name)

            move_to_submenu.triggered.connect(lambda act: self.on_move_to_group(act.data(), item.text(0)))

        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == new_task_action:
            self.on_new_task(group_name=item.text(0))

    def on_delete_group(self, group_name):
        """删除任务组的回调函数"""
        logger.info(f"用户请求删除任务组: {group_name}")

        from PyQt5.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除任务组 [{group_name}] 吗？\n该操作将删除该组下的所有任务。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.group_manager.remove_group(group_name)
            if success:
                self.refresh()
                self.main_window.update_task_list([])
                self.main_window.save_current_groups()
                logger.info(f"✅ 任务组 [{group_name}] 已删除并刷新界面")
            else:
                logger.error(f"❌ 删除任务组 [{group_name}] 失败")

    def on_move_to_group(self, target_group_name, task_id):
        """右键菜单中选择“移动到”后触发"""
        indexes = self.selectedIndexes()
        if not indexes:
            logger.warning("没有选中任何项，无法执行移动操作")
            return

        selected_item = self.itemFromIndex(indexes[0])
        if not selected_item:
            logger.warning("选中项无效，无法执行移动操作")
            return

        # 判断是否是任务项还是任务组项
        parent = selected_item.parent()
        if parent is None:
            # 如果是顶层任务组本身被选中（即要移动任务组）
            source_group_name = selected_item.text(0)
            logger.info(f"尝试将任务组 [{source_group_name}] 移动到 [{target_group_name}]")

            success = self.group_manager.move_group_to_new_parent(source_group_name, target_group_name)
            if success:
                self.refresh()
                self.main_window.update_task_list([])
                logger.info(f"✅ 任务组 [{source_group_name}] 成功移动到 [{target_group_name}]")
            else:
                logger.error(f"❌ 无法将任务组 [{source_group_name}] 移动到 [{target_group_name}]")
        else:
            # 如果是任务项
            source_group_name = parent.text(0)
            logger.info(f"请求将任务 [{task_id}] 从 [{source_group_name}] 移动到 [{target_group_name}]")
            self.move_task_between_groups(source_group_name, target_group_name, task_id)

        self.main_window.save_current_groups(force_dialog=False)

    def on_new_task(self, group_name):
        """创建新任务"""
        logger.info(f"用户请求在任务组 [{group_name}] 中新建任务")

        dialog = TaskEditDialog(self)
        dialog.set_default_group(group_name)

        if dialog.exec_() == TaskEditDialog.Accepted:
            task_data = dialog.get_task_data()
            logger.debug(f"用户输入的任务数据: {task_data}")

            try:
                from models.task_model import Task
                import json

                parameters_input = task_data["parameters"].strip()
                if not parameters_input:
                    raise ValueError("参数不能为空")

                parameters = json.loads(parameters_input)

                new_task = Task(
                    name=task_data["name"],
                    task_type=task_data["task_type"],
                    parameters=parameters,
                    group=task_data["group"]
                )

                self.group_manager.add_task_to_group(task_data["group"], new_task)
                self.main_window.update_task_list(
                    self.group_manager.get_tasks_by_group(task_data["group"])
                )
                logger.info(f"✅ 成功创建任务: {new_task.name} 到任务组 [{task_data['group']}]")
            except json.JSONDecodeError as je:
                logger.exception(f"❌ JSON 解析错误: {je}")
            except Exception as e:
                logger.exception(f"❌ 创建任务失败: {e}")

    def on_new_group(self, parent_group_name):
        """新建任务组"""
        logger.info(f"用户请求在 [{parent_group_name}] 下新建任务组")

        group_name, ok = InputDialog.getText(
            self,
            "新建任务组",
            f"请输入新任务组名称 (父组: {parent_group_name}):",
            ""
        )
        if ok and group_name:
            try:
                new_group = self.group_manager.create_group(group_name, parent_group_name)
                logger.info(f"✅ 成功创建任务组: {new_group.name}")
                self.refresh()
            except ValueError as e:
                logger.exception(f"❌ 创建失败: {e}")

    def select_group(self, item):
        """当用户点击某个任务组时触发更新任务列表"""
        logger.info(f"用户选择了任务组: {item.text(0)}")
        self.main_window.on_group_selected(item)
