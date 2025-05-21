from datetime import datetime
import uuid

from datetime import datetime

class TaskGroup:
    def __init__(self, name, parent=None):
        self.id = f"group_{hash(self)}"
        self.name = name
        self.parent = parent
        self.children = []     # 子任务组列表
        self.tasks = []        # 组内任务ID列表（引用Task对象）
        self.execution_rule = "continue"  # 执行规则: continue / all_success / any_success
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_child(self, child_group):
        """添加子任务组"""
        child_group.parent = self
        self.children.append(child_group)
        self.updated_at = datetime.now()

    def remove_child(self, group_name):
        """移除指定名称的子组"""
        self.children = [g for g in self.children if g.name != group_name]
        self.updated_at = datetime.now()

    def find_group(self, group_name):
        """递归查找任务组"""
        if self.name == group_name:
            return self
        for child in self.children:
            found = child.find_group(group_name)
            if found:
                return found
        return None

    def rename(self, new_name):
        """重命名任务组"""
        self.name = new_name
        self.updated_at = datetime.now()

class Task:
    def __init__(self, name, task_type, parameters, group=None, retry_count=3,
                 timeout=300, backup_tasks=None):
        self.id = str(uuid.uuid4())[:8]  # 生成短ID
        self.name = name
        self.task_type = task_type  # click/drag/type/swipe
        self.parameters = parameters  # 操作参数字典
        self.group = group
        self.retry_count = retry_count
        self.timeout = timeout  # 超时时间（秒）
        self.backup_tasks = backup_tasks or []
        self.status = "pending"  # pending/running/completed/failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

    def add_backup_task(self, task):
        """添加备份任务"""
        self.backup_tasks.append(task)

    def remove_backup_task(self, task_id):
        """移除指定备份任务"""
        self.backup_tasks = [t for t in self.backup_tasks if t.id != task_id]


