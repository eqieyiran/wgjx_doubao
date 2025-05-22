# models/task_model.py

from datetime import datetime
import uuid


class TaskGroup:
    def __init__(self, name, parent=None):
        self.id = f"group_{hash(self)}"
        self.name = name
        self.parent = parent
        self.children = []
        self.tasks = []
        self.execution_rule = "continue"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self):
        return {
            "name": self.name,
            "children": [child.to_dict() for child in self.children],
            "tasks": [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, data, parent=None):
        group = cls(data["name"], parent)
        group.children = [cls.from_dict(child_data, group) for child_data in data.get("children", [])]
        group.tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        return group

    def add_child(self, child_group):
        child_group.parent = self
        self.children.append(child_group)
        self.updated_at = datetime.now()

    def remove_child(self, group_name):
        self.children = [g for g in self.children if g.name != group_name]
        self.updated_at = datetime.now()

    def find_group(self, group_name):
        if self.name == group_name:
            return self
        for child in self.children:
            found = child.find_group(group_name)
            if found:
                return found
        return None

    def rename(self, new_name):
        self.name = new_name
        self.updated_at = datetime.now()


class Task:
    def __init__(
        self,
        tid: str = None,
        name: str = "",
        task_type: str = "",
        parameters: dict = None,
        group: str = None,
        retry_count: int = 3,
        status: str = "就绪",
        timeout: int = 30,
        backup_tasks: list = None
    ):
        self.tid = tid or self.generate_unique_id()
        self.name = name
        self.task_type = task_type
        self.parameters = parameters or {}
        self.group = group
        self.retry_count = retry_count
        self.timeout = timeout
        self.backup_tasks = backup_tasks or []
        self.status = status
        self.id = self.tid  # 使用 tid 作为唯一标识符
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

    @staticmethod
    def generate_unique_id():
        """生成唯一任务 ID"""
        return str(uuid.uuid4())[:8]  # 示例：生成 8 位 UUID

    def to_dict(self):
        return {
            "id": self.id,
            "tid": self.tid,
            "name": self.name,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "group": self.group,
            "retry_count": self.retry_count,
            "timeout": self.timeout,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    def add_backup_task(self, task):
        self.backup_tasks.append(task)

    def remove_backup_task(self, task_id):
        self.backup_tasks = [t for t in self.backup_tasks if t.id != task_id]
    @classmethod
    def from_dict(cls, data):
        return cls(
            tid=data.get("tid"),
            name=data.get("name", ""),
            task_type=data.get("task_type", ""),
            parameters=data.get("parameters", {}),
            group=data.get("group"),
            retry_count=data.get("retry_count", 3),
            status=data.get("status", "就绪"),
            timeout=data.get("timeout", 30),
            backup_tasks=[cls.from_dict(bt) for bt in data.get("backup_tasks", [])]
        )
