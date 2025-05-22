from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction
from PyQt5.QtGui import QDrag
from PyQt5.QtCore import Qt, QMimeData
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

        # 拖放支持
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

        # 构建整个树结构
        self._build_tree(self.group_manager.root_group, root_item)

    def _build_tree(self, group, parent_item):
        for child in group.children:
            existing_item = None
            for i in range(parent_item.childCount()):
                if parent_item.child(i).text(0) == child.name:
                    existing_item = parent_item.child(i)
                    break

            if existing_item:
                self._build_tree(child, existing_item)
            else:
                new_item = QTreeWidgetItem([child.name])
                parent_item.addChild(new_item)
                self._build_tree(child, new_item)

    def startDrag(self, supported_actions):
        """开始拖拽操作"""
        drag = QDrag(self)
        mime_data = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)

    def dropEvent(self, event):
        """处理拖放事件，实现跨组移动任务"""
        super().dropEvent(event)

        source_index = self.selectedIndexes()[0]
        target_index = self.indexAt(event.pos())

        source_item = self.itemFromIndex(source_index)
        target_item = self.itemFromIndex(target_index)

        if not source_item or not target_item:
            print("❌ 源或目标任务组为空")
            return

        source_group_name = source_item.parent().text(0) if source_item.parent() else "根任务组"
        target_group_name = target_item.text(0)

        task_id = source_item.text(0)  # 假设显示的是 task.id
        self.move_task_between_groups(source_group_name, target_group_name, task_id)

    def move_task_between_groups(self, source_group, target_group, task_id):
        """将任务从一个组移动到另一个组"""
        source_group_obj = self.group_manager.root_group.find_group(source_group)
        target_group_obj = self.group_manager.root_group.find_group(target_group)

        if source_group_obj and target_group_obj:
            for task in source_group_obj.tasks:
                if task.id == task_id:
                    source_group_obj.tasks.remove(task)
                    target_group_obj.tasks.append(task)
                    task.group = target_group
                    break

            # 刷新任务列表
            self.main_window.update_task_list(self.group_manager.get_tasks_by_group(target_group))

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # 总是显示“新建任务”
        new_task_action = QAction("新建任务", self)
        menu.addAction(new_task_action)

        selected_name = item.text(0)
        if selected_name != "根任务组":
            menu.addSeparator()
            create_action = menu.addAction("新建任务组")
            rename_action = menu.addAction("重命名")
            delete_action = menu.addAction("删除")
        else:
            create_action = rename_action = delete_action = None

        action = menu.exec_(self.viewport().mapToGlobal(position))

        if action == new_task_action:
            self.on_new_task(selected_name)
        elif action == create_action:
            parent_name = selected_name if item else "根任务组"
            new_name, ok = InputDialog.getText(self, "新建任务组", "请输入任务组名称:")
            if ok and new_name:
                self.group_manager.create_group(new_name, parent_name)
                self.refresh()
        elif action == rename_action:
            if selected_name == "根任务组":
                return
            new_name, ok = InputDialog.getText(self, "重命名任务组", "请输入新名称:", text=selected_name)
            if ok and new_name:
                try:
                    self.group_manager.rename_group(selected_name, new_name)
                    self.refresh()
                except Exception as e:
                    print(f"重命名失败: {e}")
        elif action == delete_action:
            if selected_name == "根任务组":
                return
            confirm = InputDialog.get_confirmation(self, "确认删除", f"确定要删除任务组 '{selected_name}' 吗？")
            if confirm:
                self.group_manager.delete_group(selected_name)
                self.refresh()

    def on_new_task(self, group_name):
        """处理新建任务操作"""
        dialog = TaskEditDialog(self)
        if dialog.exec_() == TaskEditDialog.Accepted:
            task_data = dialog.get_task_data()
            try:
                from models.task_model import Task
                import json
                parameters = json.loads(task_data["parameters"])

                new_task = Task(
                    name=task_data["name"],
                    task_type=task_data["task_type"],
                    parameters=parameters,
                    group=group_name
                )
                self.group_manager.add_task_to_group(group_name, new_task)

                try:
                    self.main_window.update_task_list(self.group_manager.get_tasks_by_group(group_name))
                except AttributeError:
                    print("MainWindow 中未定义 update_task_list 方法")
            except Exception as e:
                print(f"新建任务失败: {e}")
