# ui/task_group_panel.py
from PyQt5.QtCore import QSortFilterProxyModel
import logging
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction, QComboBox, QMessageBox
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

        # 移除所有与拖放相关的设置
        # 删除了以下配置：
        # - setAcceptDrops
        # - setDragEnabled
        # - setSelectionMode
        # - setDropIndicatorShown
        # - setDragDropMode

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

    # 完全移除了 startDrag 和 dropEvent 方法
    # 这两个方法负责处理拖放操作

    def move_task_between_groups(self, source_group, target_group, task_id):
        """实际执行任务在任务组之间的移动"""
        logger.debug(f"尝试移动任务: {task_id} -> {source_group} => {target_group}")

        source_group_obj = self.group_manager.find_group_by_name(source_group)
        target_group_obj = self.group_manager.find_group_by_name(target_group)

        if not source_group_obj:
            logger.error(f"源任务组 [{source_group}] 不存在")
            return False
        if not target_group_obj:
            logger.error(f"目标任务组 [{target_group}] 不存在")
            return False

        moved = False
        for i, task in enumerate(source_group_obj.tasks):
            if task.id == task_id:
                logger.info(f"找到任务 [{task.name}], 准备移动")

                # 从源组移除任务
                moved_task = source_group_obj.tasks.pop(i)

                # 更新任务的分组属性
                moved_task.group = target_group

                # 添加到目标组
                target_group_obj.tasks.append(moved_task)

                # 保持任务顺序
                target_group_obj.tasks.sort(key=lambda t: getattr(t, 'order', 0))

                moved = True
                break

        if moved:
            logger.info(f"任务 [{task_id}] 已成功移动到 [{target_group}]")
            return True
        else:
            logger.warning(f"任务 [{task_id}] 在 [{source_group}] 中未找到")
            return False

    def on_move_to_group(self, target_group_name, task_ids):
        logger.info(f"用户请求将任务 {task_ids} 移动到分组 [{target_group_name}]")

        if not task_ids or not target_group_name:
            logger.warning("⚠️ 参数错误：task_ids 或 target_group_name 为空")
            return False

        target_group = self.group_manager.find_group_by_name(target_group_name)
        if not target_group:
            logger.error(f"❌ 目标分组不存在: {target_group_name}")
            return False

        moved_tasks = []

        for task_id in task_ids:
            source_group_name = self._find_source_group_name(task_id)
            if not source_group_name:
                continue

            source_group = self.group_manager.find_group_by_name(source_group_name)
            if not source_group or not hasattr(source_group, 'tasks'):
                continue

            found = False
            for i, task in enumerate(source_group.tasks):
                if task.id == task_id:
                    try:
                        moved_task = source_group.tasks.pop(i)

                        # 更新任务的分组属性
                        moved_task.group = target_group_name

                        moved_tasks.append(moved_task)
                        logger.info(f"✅ 任务 [{task_id}] 已从 [{source_group_name}] 移出")

                        found = True
                        break
                    except IndexError:
                        logger.exception(f"❌ 删除任务 [{task_id}] 时索引越界")
                        break

            if not found:
                logger.warning(f"⚠️ 任务 [{task_id}] 在 [{source_group_name}] 中未找到")

        if moved_tasks:
            # 将任务添加到目标组，保留原有任务并维护顺序
            target_group.tasks.extend(moved_tasks)

            # 重新排序目标组任务
            target_group.tasks.sort(key=lambda t: getattr(t, 'order', 0))

            # 强制刷新两个分组的任务列表
            self.main_window.update_task_list(
                self.group_manager.get_tasks_by_group(target_group_name)
            )

            logger.info(f"✅ 共 {len(moved_tasks)} 个任务已移动至 [{target_group_name}]")
            return True

        logger.warning("⚠️ 没有任务被移动")
        return False

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.itemAt(position)
        if not item:
            logger.warning("右键点击位置无效")
            return

        menu = QMenu(self)
        selected_name = item.text(0)

        # 创建新建任务动作
        new_task_action = menu.addAction("新建任务")
        new_task_action.triggered.connect(lambda: self.on_new_task(group_name=selected_name))

        menu.addSeparator()

        # 创建新建任务组动作
        new_group_action = menu.addAction("新建任务组")
        new_group_action.triggered.connect(lambda _: self.on_new_group(selected_name))

        # 如果不是根任务组，添加删除功能
        if selected_name != "根任务组":
            # 创建删除任务组动作
            delete_group_action = menu.addAction("删除任务组")
            delete_group_action.triggered.connect(lambda: self.on_delete_group(selected_name))

        # 显示菜单并处理选择
        action = menu.exec_(self.viewport().mapToGlobal(position))

    def _find_source_group_name(self, task_id):
        """查找任务所属的任务组名"""
        for group in self.group_manager.get_all_groups():
            for task in group.tasks:
                if task.id == task_id:
                    return group.name
        logger.warning(f"⚠️ 找不到任务 [{task_id}] 的源分组")
        return None

    def on_delete_group(self, group_name):
        """删除任务组的回调函数"""
        logger.info(f"用户请求删除任务组: {group_name}")

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
