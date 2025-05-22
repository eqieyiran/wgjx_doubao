# models/task_model.py

import uuid
from datetime import datetime


class Task:
    def __init__(
        self, tid=None, name="", task_type="", parameters=None,
        group=None, retry_count=3, status="就绪", timeout=30,
        backup_tasks=None
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
        self.id = self.tid
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

    @staticmethod
    def generate_unique_id():
        return str(uuid.uuid4())[:8]

    def to_dict(self):
        return {
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

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


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

    def find_group(self, group_name):
        if self.name == group_name:
            return self
        for child in self.children:
            found = child.find_group(group_name)
            if found:
                return found
        return None
