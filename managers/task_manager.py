import os
import re
from models.task_model import Task, TaskGroup
from utils.file_utils import scan_directory_recursive


class TaskManager:
    def __init__(self):
        self.groups = {}
        self.current_group = None
        self.tasks = {}

    def create_single_task(self, name, task_type, parameters, group=None):
        """创建单个任务"""
        task = Task(name, task_type, parameters, group)
        self.tasks[task.id] = task

        if group:
            if group not in self.groups:
                self.create_group(group)
            self.groups[group].add_task(task)

        return task

    def create_group(self, name):
        """创建任务组"""
        if name in self.groups:
            raise ValueError(f"组 '{name}' 已存在")

        group = TaskGroup(name)
        self.groups[name] = group
        return group

    def batch_create_tasks(self, folder_path, template_extension=".png"):
        """批量创建任务"""
        files = scan_directory_recursive(folder_path, lambda f: f.endswith(template_extension))

        for file_path in files:
            dir_name = os.path.basename(os.path.dirname(file_path))
            file_name = os.path.splitext(os.path.basename(file_path))[0]

            # 使用文件名排序规则
            task_name = f"{dir_name}_{file_name}"

            # 创建任务
            task = self.create_single_task(
                name=task_name,
                task_type="click",  # 默认任务类型
                parameters={"template_path": file_path},
                group=dir_name
            )

        return len(files)

    def execute_tasks(self, tasks=None):
        """执行任务序列"""
        tasks_to_run = tasks or [t for t in self.tasks.values() if t.status == "pending"]

        for task in sorted(tasks_to_run, key=lambda t: (t.group, getattr(t, 'order', 0))):
            yield from self._execute_with_retry(task)

    def _execute_with_retry(self, task):
        """带重试机制的任务执行"""
        retry_count = 0
        current_task = task

        while retry_count <= task.retry_count:
            try:
                # 执行任务
                result = current_task.execute()

                if result:
                    task.status = "completed"
                    task.completed_at = datetime.now()
                    yield {"task_id": task.id, "status": "success"}
                    break

                retry_count += 1

                if retry_count > task.retry_count and task.backup_tasks:
                    # 尝试备份任务链
                    for backup_task in task.backup_tasks:
                        yield from self._execute_with_retry(backup_task)
                        if backup_task.status == "completed":
                            break

            except TimeoutError:
                # 时间窗口超时
                task.status = "failed"
                yield {"task_id": task.id, "status": "error", "code": "ERR_003"}
                break

    def sort_tasks(self, tasks):
        """按分组>执行序号排序"""
        return sorted(tasks, key=lambda t: (t.group, getattr(t, 'order', 0)))
