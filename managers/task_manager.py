import os
import datetime
from models.task_model import Task, TaskGroup
from utils.file_utils import scan_directory_recursive  # 确保正确导入
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TaskManager:
    def __init__(self):
        logging.info("初始化 TaskManager")
        self.groups = {}
        self.current_group = None
        self.tasks = {}

    def create_single_task(self, name, task_type, parameters, group=None):
        """创建单个任务"""
        logging.info(f"创建任务 [{name}] 类型: {task_type}, 分组: {group or '无'}")
        task = Task(name, task_type, parameters, group)
        self.tasks[task.id] = task

        if group:
            if group not in self.groups:
                logging.warning(f"分组 [{group}] 不存在，正在创建")
                self.create_group(group)
            self.groups[group].add_task(task)
            logging.info(f"任务 [{name}] 成功加入分组 [{group}]")

        return task

    def create_group(self, name):
        """创建任务组"""
        if name in self.groups:
            raise ValueError(f"组 '{name}' 已存在")

        logging.info(f"创建任务组 [{name}]")
        group = TaskGroup(name)
        self.groups[name] = group
        logging.info(f"任务组 [{name}] 创建成功")
        return group

    def batch_create_tasks(self, folder_path, template_extension=".png"):
        """批量创建任务"""
        logging.info(f"开始从目录 [{folder_path}] 批量创建任务（扩展名：{template_extension}）")
        files = scan_directory_recursive(folder_path, lambda f: f.endswith(template_extension))

        created_count = 0
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
            created_count += 1

        logging.info(f"完成批量创建任务，共创建 {created_count} 个任务")
        return created_count

    def execute_tasks(self, tasks=None):
        """执行任务序列"""
        tasks_to_run = tasks or [t for t in self.tasks.values() if t.status == "pending"]
        logging.info(f"开始执行任务队列，共 {len(tasks_to_run)} 个任务")

        for task in sorted(tasks_to_run, key=lambda t: (t.group, getattr(t, 'order', 0))):
            logging.info(f"正在处理任务 [{task.name}], ID: {task.id}")
            yield from self._execute_with_retry(task)

    def _execute_with_retry(self, task):
        """带重试机制的任务执行"""
        retry_count = 0
        current_task = task
        logging.info(f"任务 [{task.name}] 最多重试 {task.retry_count} 次")

        while retry_count <= task.retry_count:
            try:
                logging.info(f"第 {retry_count + 1} 次尝试执行任务 [{task.name}]")
                result = current_task.execute()

                if result:
                    task.status = "completed"
                    task.completed_at = datetime.datetime.now()
                    logging.info(f"任务 [{task.name}] 成功完成")
                    yield {"task_id": task.id, "status": "success"}
                    break

                retry_count += 1

                if retry_count > task.retry_count and task.backup_tasks:
                    logging.info("超过最大重试次数，开始执行备份任务链")
                    for backup_task in task.backup_tasks:
                        yield from self._execute_with_retry(backup_task)
                        if backup_task.status == "completed":
                            logging.info(f"备份任务 [{backup_task.name}] 成功")
                            break

            except TimeoutError:
                task.status = "failed"
                logging.error(f"任务 [{task.name}] 超时失败")
                yield {"task_id": task.id, "status": "error", "code": "ERR_003"}
                break

    @staticmethod  # 标记为静态方法
    def sort_tasks(tasks):
        """按分组>执行序号排序"""
        logging.info(f"开始对 {len(tasks)} 个任务进行排序")
        sorted_tasks = sorted(tasks, key=lambda t: (t.group, getattr(t, 'order', 0)))
        logging.info(f"任务排序完成，返回 {len(sorted_tasks)} 个已排序任务")
        return sorted_tasks
