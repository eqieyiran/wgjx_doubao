# ui/task_group_panel.py

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction, QWidgetAction, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDrag
from utils.input_dialog import InputDialog
from ui.task_edit_dialog import TaskEditDialog


class TaskGroupPanel(QTreeWidget):
    def __init__(self, group_manager, main_window):
        super().__init__()
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

    def refresh(self):
        """刷新任务组面板"""
        self.clear()
        root_item = QTreeWidgetItem([self.group_manager.root_group.name])
        self.addTopLevelItem(root_item)
        self._build_tree(self.group_manager.root_group, root_item)

    def _build_tree(self, group, parent_item):
        for child in group.children:
            new_item = QTreeWidgetItem([child.name])
            parent_item.addChild(new_item)
            self._build_tree(child, new_item)

    def startDrag(self, supported_actions):
        drag = QDrag(self)
        mime_data = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)

    def dropEvent(self, event):
        super().dropEvent(event)
        source_index = self.selectedIndexes()[0]
        target_index = self.indexAt(event.pos())
        source_item = self.itemFromIndex(source_index)
        target_item = self.itemFromIndex(target_index)

        if not source_item or not target_item:
            print("❌ 源或目标为空")
            return

        source_group_name = source_item.parent().text(0) if source_item.parent() else "根任务组"
        target_group_name = target_item.text(0)

        task_id = source_item.text(0)
        self.move_task_between_groups(source_group_name, target_group_name, task_id)

    def move_task_between_groups(self, source_group, target_group, task_id):
        source_group_obj = self.group_manager.find_group_by_name(source_group)
        target_group_obj = self.group_manager.find_group_by_name(target_group)

        if source_group_obj and target_group_obj:
            for task in source_group_obj.tasks:
                if task.id == task_id:
                    source_group_obj.tasks.remove(task)
                    target_group_obj.tasks.append(task)
                    task.group = target_group
                    break

            self.main_window.update_task_list(self.group_manager.get_tasks_by_group(target_group))

    def show_context_menu(self, position):
        item = self.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        new_task_action = QAction("新建任务", self)
        menu.addAction(new_task_action)

        selected_name = item.text(0)
        if selected_name != "根任务组":
            menu.addSeparator()

            # 新建任务组
            new_group_action = menu.addAction("新建任务组")
            new_group_action.triggered.connect(lambda _: self.on_new_group(selected_name))

            # 删除任务组
            delete_group_action = menu.addAction("删除任务组")
            delete_group_action.triggered.connect(lambda: self.on_delete_group(selected_name))

            # 移动到其他分组
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
        """
        删除任务组回调函数
        :param group_name: 要删除的任务组名称
        """
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
                print(f"✅ 任务组 [{group_name}] 已删除并刷新界面")
            else:
                print(f"❌ 删除任务组 [{group_name}] 失败")

    def on_move_to_group(self, target_group_name, task_id):
        source_group_name = self.itemFromIndex(self.selectedIndexes()[0]).parent().text(0)
        self.move_task_between_groups(source_group_name, target_group_name, task_id)
        self.main_window.save_current_groups(force_dialog=False)

    def on_new_task(self, group_name):
        dialog = TaskEditDialog(self)
        dialog.set_default_group(group_name)  # 设置默认分组

        if dialog.exec_() == TaskEditDialog.Accepted:
            task_data = dialog.get_task_data()

            try:
                from models.task_model import Task
                import json

                # 校验参数是否为有效 JSON
                parameters_input = task_data["parameters"].strip()
                if not parameters_input:
                    raise ValueError("参数不能为空")

                parameters = json.loads(parameters_input)

                new_task = Task(
                    name=task_data["name"],
                    task_type=task_data["task_type"],
                    parameters=parameters,
                    group=task_data["group"]  # 使用用户选择的分组
                )

                self.group_manager.add_task_to_group(task_data["group"], new_task)
                self.main_window.update_task_list(self.group_manager.get_tasks_by_group(task_data["group"]))
            except json.JSONDecodeError as je:
                print(f"❌ JSON 解析错误: {je}")
            except Exception as e:
                print(f"❌ 新建任务失败: {e}")

    def on_new_group(self, parent_group_name):
        """
        新建任务组的回调函数
        :param parent_group_name: 父级任务组名称
        """
        group_name, ok = InputDialog.getText(
            self,
            "新建任务组",
            f"请输入新任务组名称 (父组: {parent_group_name}):",
            ""
        )
        if ok and group_name:
            try:
                # 调用 GroupManager 创建任务组
                new_group = self.group_manager.create_group(group_name, parent_group_name)
                print(f"✅ 成功创建任务组: {new_group.name}")
                self.refresh()  # 刷新 UI 显示
            except ValueError as e:
                print(f"❌ 创建失败: {e}")