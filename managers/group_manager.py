from models.task_model import TaskGroup  # 缺失的导入语句

class GroupManager:
    def __init__(self):
        self.root_group = TaskGroup("根任务组")
        self._init_mock_data()
    def create_group(self, name, parent_name=None):
        """创建新任务组，可指定父组名"""
        parent = self.root_group
        if parent_name and parent_name != "根任务组":
            parent = self.root_group.find_group(parent_name)
            if not parent:
                raise ValueError(f"找不到父组 '{parent_name}'")
        new_group = TaskGroup(name, parent=parent)
        parent.add_child(new_group)
        return new_group

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

    def get_all_groups(self):
        """获取所有任务组（扁平化列表）"""
        groups = []

        def traverse(group):
            groups.append(group)
            for child in group.children:
                traverse(child)

        traverse(self.root_group)
        return groups

    def save_to_file(self, file_path="tasks.json"):
        """将任务组结构和任务保存为 JSON 文件"""
        import json
        data = {
            "root_group": self.root_group.to_dict()
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True

    def _rename_temp_file(self, old_path, new_path):
        """辅助方法：重命名临时保存路径"""
        import shutil
        if old_path != new_path:
            shutil.copy(old_path, new_path)

    def _init_mock_data(self):
        # 初始化一些模拟任务数据（用于演示）
        from models.task_model import Task
        daily_group = self.create_group("日常任务")
        weekly_group = self.create_group("周常任务")

        daily_group.tasks = [
            Task("T001", "每日签到", "click", group="日常任务"),
            Task("T002", "每日副本", "match", group="日常任务")
        ]

        weekly_group.tasks = [
            Task("T003", "周常副本", "match", group="周常任务"),
            Task("T004", "周常挑战", "click", group="周常任务")
        ]

    def get_tasks_by_group(self, group_name):
        """根据任务组名获取任务列表"""
        group = self.root_group.find_group(group_name)
        if group:
            return group.tasks
        return []

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
