from models.task_model import TaskGroup  # 缺失的导入语句

class GroupManager:
    def __init__(self):
        self.root_group = TaskGroup("根任务组")

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
        """将任务组结构保存到指定路径"""
        from utils.persistence import save_task_groups
        try:
            # 临时替换默认路径保存
            original_path = "tasks.json"
            if file_path != original_path:
                self._rename_temp_file(original_path, file_path)
            save_task_groups(self)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def _rename_temp_file(self, old_path, new_path):
        """辅助方法：重命名临时保存路径"""
        import shutil
        if old_path != new_path:
            shutil.copy(old_path, new_path)