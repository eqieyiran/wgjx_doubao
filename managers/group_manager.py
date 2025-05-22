# managers/group_manager.py

from models.task_model import TaskGroup
from utils.persistence import save_task_groups


class GroupManager:
    def __init__(self):
        self.root_group = TaskGroup("根任务组")

    def find_group_by_name(self, group_name):
        def _search(group):
            if group.name == group_name:
                return group
            for child in group.children:
                result = _search(child)
                if result:
                    return result
            return None

        return _search(self.root_group)

    def create_group(self, name, parent_name="根任务组"):
        parent = self.find_group_by_name(parent_name)
        if not parent:
            raise ValueError(f"找不到父组 '{parent_name}'")
        new_group = TaskGroup(name, parent=parent)
        parent.add_child(new_group)
        return new_group

    def get_all_groups(self):
        def collect(group):
            groups = [group]
            for child in group.children:
                groups.extend(collect(child))
            return groups

        return collect(self.root_group)

    def get_tasks_by_group(self, group_name):
        group = self.find_group_by_name(group_name)
        return group.tasks if group else []

    def set_tasks_for_group(self, group_name, tasks):
        group = self.find_group_by_name(group_name)
        if group:
            group.tasks = tasks
            return True
        return False

    def add_task_to_group(self, group_name, task):
        group = self.find_group_by_name(group_name)
        if group:
            task.group = group_name
            group.tasks.append(task)
            return True
        return False

    def save_to_file(self, file_path="tasks.json"):
        return save_task_groups(self, file_path)
