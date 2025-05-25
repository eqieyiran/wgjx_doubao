# managers/group_manager.py
import logging
from models.task_model import TaskGroup
from utils.persistence import save_task_groups
# 定义本模块专用 logger
logger = logging.getLogger(__name__)

class GroupManager:
    def __init__(self):
        self.root_group = TaskGroup("根任务组")
        print("✅ 初始化任务组管理器，创建根任务组")

    def find_group_by_name(self, group_name):
        """根据名称查找任务组"""
        print(f"🔍 查找任务组 [{group_name}]")
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
        """创建新任务组并加入父组"""
        print(f"🆕 创建任务组 [{name}], 父组: {parent_name}")
        parent = self.find_group_by_name(parent_name)
        if not parent:
            raise ValueError(f"找不到父组 '{parent_name}'")
        new_group = TaskGroup(name, parent=parent)
        parent.add_child(new_group)
        return new_group

    def get_all_groups(self):
        """获取所有任务组"""
        print("📊 开始收集所有任务组")
        def collect(group):
            groups = [group]
            print(f"📌 收集任务组: {group.name}")
            for child in group.children:
                groups.extend(collect(child))
            return groups
        result = collect(self.root_group)
        print(f"📊 共计获取 {len(result)} 个任务组")
        return result

    def get_tasks_by_group(self, group_name):
        """获取指定分组的任务列表"""
        print(f"📂 获取任务组 [{group_name}] 的任务")
        group = self.find_group_by_name(group_name)
        if group:
            print(f"📦 共获取 {len(group.tasks)} 条任务")
            return group.tasks
        print("❌ 未找到对应任务组")
        return []

    def set_tasks_for_group(self, group_name, tasks):
        """设置指定分组的任务列表"""
        print(f"📝 设置任务组 [{group_name}] 的任务")
        group = self.find_group_by_name(group_name)
        if group:
            for idx, task in enumerate(tasks):
                task.group = group_name
                task.order = idx  # 更新任务的序号
            group.tasks = tasks
            print(f"✅ 成功设置任务组 [{group_name}] 的任务数量: {len(tasks)}")
            return True
        print(f"❌ 设置失败：未找到任务组 [{group_name}]")
        return False

    def add_task_to_group(self, group_name, task):
        """向指定任务组中添加一个任务"""
        print(f"📎 向任务组 [{group_name}] 添加任务 [{task.name}]")
        group = self.find_group_by_name(group_name)
        if group:
            task.group = group_name
            task.order = len(group.tasks)  # 新增代码
            group.tasks.append(task)
            print(f"✅ 任务 [{task.name}] 已加入 [{group_name}]")
            return True
        print(f"❌ 添加失败：未找到任务组 [{group_name}]")
        return False

    def remove_task_from_group(self, group_name, task_id):
        """从指定任务组中删除一个任务"""
        print(f"🗑️ 删除任务组 [{group_name}] 中的任务 ID: {task_id}")
        group = self.find_group_by_name(group_name)
        if group:
            before_count = len(group.tasks)
            group.tasks = [t for t in group.tasks if t.id != task_id]
            removed = before_count != len(group.tasks)
            if removed:
                print(f"✅ 任务 ID: {task_id} 已从 [{group_name}] 中移除")
            else:
                print(f"⚠️ 任务 ID: {task_id} 在 [{group_name}] 中不存在")
            return removed
        print(f"❌ 删除失败：未找到任务组 [{group_name}]")
        return False

    def save_to_file(self, file_path="tasks.json"):
        """保存当前配置到文件"""
        print(f"💾 正在保存任务组到文件: {file_path}")
        return save_task_groups(self, file_path)

    def remove_group(self, group_name):
        """删除指定名称的任务组及其下所有任务"""
        print(f"🗑️ 开始删除任务组 [{group_name}]")

        if group_name == "根任务组":
            print("❌ 禁止删除根任务组")
            return False

        # 查找目标组
        group = self.find_group_by_name(group_name)
        if not group:
            print(f"❌ 未找到任务组 [{group_name}]")
            return False

        parent = group.parent
        if not parent:
            print(f"❌ 无法删除 [{group_name}]：没有父组")
            return False

        # 从父组中移除该子组
        parent.children = [g for g in parent.children if g.name != group_name]
        print(f"✅ 成功删除任务组 [{group_name}]")
        return True

