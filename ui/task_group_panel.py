from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PyQt5.QtCore import Qt
from utils.input_dialog import InputDialog

class TaskGroupPanel(QTreeWidget):
    def __init__(self, group_manager):
        super().__init__()
        self.group_manager = group_manager
        self.setHeaderLabel("任务组")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.refresh()

    def refresh(self):
        """刷新任务组面板"""
        self.clear()
        root_item = QTreeWidgetItem([self.group_manager.root_group.name])
        self.addTopLevelItem(root_item)
        self._build_tree(self.group_manager.root_group, root_item)

    def _build_tree(self, group, parent_item):
        """递归构建任务组树"""
        for child in group.children:
            item = QTreeWidgetItem([child.name])
            parent_item.addChild(item)
            self._build_tree(child, item)

    def show_context_menu(self, position):
        menu = QMenu()
        create_action = menu.addAction("新建任务组")
        rename_action = menu.addAction("重命名")
        delete_action = menu.addAction("删除")

        action = menu.exec_(self.viewport().mapToGlobal(position))
        item = self.itemAt(position)
        selected_name = item.text(0) if item else ""

        if action == create_action:
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
