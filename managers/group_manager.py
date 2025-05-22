from models.task_model import TaskGroup  # 缺失的导入语句
from utils.persistence import save_task_groups


class GroupManager:
    def __init__(self):
        self.root_group = TaskGroup("根任务组")

    def find_group_by_name(self, group_name):
        """
        根据名称查找任务组
        """

        def _search(group):
            if group.name == group_name:
                return group
            for child in group.children:
                result = _search(child)
                if result:
                    return result
            return None

        return _search(self.root_group)

    def create_group(self, name):
        group = TaskGroup(name, parent=self.root_group)
        self.root_group.add_child(group)
        return group

    def get_all_groups(self):
        def collect(group):
            groups = [group]
            for child in group.children:
                groups.extend(collect(child))
            return groups

        return collect(self.root_group)

    def get_tasks_by_group(self, group_name):
        def find(group):
            if group.name == group_name:
                return group.tasks
            for child in group.children:
                result = find(child)
                if result is not None:
                    return result
            return None

        return find(self.root_group) or []

    # 👇 新增方法：设置某个分组的任务列表
    def set_tasks_for_group(self, group_name, tasks):
        def find_and_update(group):
            if group.name == group_name:
                group.tasks = tasks
                return True
            for child in group.children:
                if find_and_update(child):
                    return True
            return False

        if not find_and_update(self.root_group):
            print(f"❌ 未找到名为 '{group_name}' 的任务组")





    # def create_group(self, name, parent_name=None):
    #     """创建新任务组，可指定父组名"""
    #     parent = self.root_group
    #     if parent_name and parent_name != "根任务组":
    #         parent = self.root_group.find_group(parent_name)
    #         if not parent:
    #             raise ValueError(f"找不到父组 '{parent_name}'")
    #     new_group = TaskGroup(name, parent=parent)
    #     parent.add_child(new_group)
    #     return new_group

    def delete_group(self, group_name):
        """删除指定名称的任务组"""
        if group_name == "根任务组":
            raise ValueError("不能删除根任务组")
        parent = self._find_parent_group(group_name)
        if parent:
            parent.remove_child(group_name)

    def _find_parent_group(self, group_name):
        """查找某个组的上级组"""
        def search(group):
            for child in group.children:
                if child.name == group_name:
                    return group
                found = search(child)
                if found:
                    return found
            return None

        return search(self.root_group)

    def rename_group(self, old_name, new_name):
        """重命名任务组"""
        group = self.root_group.find_group(old_name)
        if not group:
            raise ValueError(f"找不到任务组 '{old_name}'")
        group.rename(new_name)

    # def get_all_groups(self):
    #     """获取所有任务组（扁平化列表）"""
    #     groups = []
    #
    #     def traverse(group):
    #         groups.append(group)
    #         for child in group.children:
    #             traverse(child)
    #
    #     traverse(self.root_group)
    #     return groups

    def save_to_file(self, file_path="tasks.json"):
        """
        将当前任务组结构保存到文件
        """
        return save_task_groups(self, file_path)

    def _rename_temp_file(self, old_path, new_path):
        """辅助方法：重命名临时保存路径"""
        import shutil
        if old_path != new_path:
            shutil.copy(old_path, new_path)

    def _init_mock_data(self):
        """初始化一些模拟任务数据（用于演示）"""
        from models.task_model import Task

        daily_group = self.create_group("日常任务")
        weekly_group = self.create_group("周常任务")

        daily_group.tasks = [
            Task(
                tid="T001",
                name="每日签到",
                task_type="click",
                parameters={"location": (100, 200)},
                group="日常任务"
            ),
            Task(
                tid="T002",
                name="每日签到2",
                task_type="click",
                parameters={"location": (100, 200)},
                group="日常任务"
            )
        ]

        weekly_group.tasks = [
            Task(
                tid="T003",
                name="周常副本",
                task_type="match",
                parameters={"template": "weekly.png"},
                group="周常任务"
            ),
            Task(
                tid="T004",
                name="周常挑战",
                task_type="click",
                parameters={"location": (300, 400)},
                group="周常任务"
            )
        ]

    # def get_tasks_by_group(self, group_name):
    #     """根据任务组名获取任务列表"""
    #     group = self.root_group.find_group(group_name)
    #     if group:
    #         return group.tasks
    #     return []

    def add_task_to_group(self, group_name, task):
        """向指定任务组中添加任务"""
        group = self.root_group.find_group(group_name)
        if group:
            group.tasks.append(task)

    def update_task_order(self, group_name, ordered_task_ids):
        """根据传入的有序 ID 列表更新任务顺序"""
        group = self.root_group.find_group(group_name)
        if not group:
            return False

        # 保持原任务对象不变，只调整顺序
        ordered_tasks = []
        for task_id in ordered_task_ids:
            for task in group.tasks:
                if task.id == task_id:
                    ordered_tasks.append(task)
                    break

        group.tasks = ordered_tasks
        return True
