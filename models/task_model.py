# models/task_model.py
import logging
import uuid
from datetime import datetime
from dateutil.parser import parse


# 在每个 .py 文件开头定义自己的 logger
logger = logging.getLogger(__name__)


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
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.order = 0
        self.id = self.tid  # 兼容性保留

    @staticmethod
    def generate_unique_id():
        """生成唯一任务ID"""
        return str(uuid.uuid4())

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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "order": self.order
        }

    @classmethod
    def from_dict(cls, data):
        task = cls(
            tid=data.get("tid"),
            name=data.get("name", ""),
            task_type=data.get("task_type", ""),
            parameters=data.get("parameters", {}),
            group=data.get("group"),
            retry_count=data.get("retry_count", 3),
            status=data.get("status", "就绪"),
            timeout=data.get("timeout", 30)
        )

        # 时间戳处理
        created_at_str = data.get("created_at")
        if created_at_str:
            try:
                task.created_at = parse(created_at_str)
            except Exception:
                task.created_at = datetime.now()
        else:
            task.created_at = datetime.now()

        started_at_str = data.get("started_at")
        if started_at_str:
            task.started_at = parse(started_at_str)

        completed_at_str = data.get("completed_at")
        if completed_at_str:
            task.completed_at = parse(completed_at_str)

        task.order = data.get("order", 0)
        return task


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
        """将 TaskGroup 对象序列化为字典"""
        return {
            "name": self.name,
            "children": [child.to_dict() for child in self.children],
            "tasks": [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, data):
        """从字典恢复任务对象"""
        if not data:
            return None

        group = cls(name=data.get("name", ""))

        # 处理时间戳
        created_at_str = data.get("created_at")
        if created_at_str:
            try:
                group.created_at = parse(created_at_str)
            except Exception:
                group.created_at = datetime.now()
        else:
            group.created_at = datetime.now()

        # 初始化子组和任务
        group.children = [cls.from_dict(child_data) for child_data in data.get("children", [])]
        group.tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]

        return group

    def add_child(self, child_group):
        """添加子任务组"""
        print(f"🔗 将 [{child_group.name}] 添加为 [{self.name}] 的子组")
        child_group.parent = self
        self.children.append(child_group)

    def find_group(self, group_name):
        """查找指定名称的任务组"""
        logger.debug(f"🔍 查找任务组 [{group_name}] 在 [{self.name}] 中是否存在")
        if self.name == group_name:
            logger.debug(f"🎯 找到任务组 [{group_name}]")
            return self
        for child in self.children:
            found = child.find_group(group_name)
            if found:
                return found
        logger.warning(f"❌ 未找到任务组 [{group_name}]")
        return None
