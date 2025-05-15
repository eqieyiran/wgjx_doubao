import os
import json
import uuid
from datetime import datetime

class Task:
    def __init__(self, name="", image_path="", match_action="", 
                 fail_action="", threshold=0.8, recursive=True, 
                 task_id=None, status="就绪", created_at=None, 
                 last_run=None):
        self.id = task_id or str(uuid.uuid4())
        self.name = name
        self.image_path = image_path
        self.match_action = match_action
        self.fail_action = fail_action
        self.threshold = threshold
        self.recursive = recursive
        self.status = status
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_run = last_run
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "image_path": self.image_path,
            "match_action": self.match_action,
            "fail_action": self.fail_action,
            "threshold": self.threshold,
            "recursive": self.recursive,
            "status": self.status,
            "created_at": self.created_at,
            "last_run": self.last_run
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            task_id=data.get("id"),
            name=data.get("name"),
            image_path=data.get("image_path"),
            match_action=data.get("match_action"),
            fail_action=data.get("fail_action"),
            threshold=data.get("threshold", 0.8),
            recursive=data.get("recursive", True),
            status=data.get("status", "就绪"),
            created_at=data.get("created_at"),
            last_run=data.get("last_run")
        )

class TaskManager:
    def __init__(self, tasks_dir="tasks"):
        self.tasks_dir = tasks_dir
        self.tasks = []
        
        # 创建任务目录（如果不存在）
        if not os.path.exists(tasks_dir):
            os.makedirs(tasks_dir)
    
    def add_task(self, task):
        self.tasks.append(task)
        self.save_task(task)
        return task
    
    def update_task(self, task_id, updated_data):
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                # 更新任务属性
                for key, value in updated_data.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # 保存更新后的任务
                self.save_task(task)
                return task
        return None
    
    def delete_task(self, task_id):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        task_file = os.path.join(self.tasks_dir, f"{task_id}.json")
        if os.path.exists(task_file):
            os.remove(task_file)
    
    def get_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_all_tasks(self):
        return self.tasks
    
    def save_task(self, task):
        task_file = os.path.join(self.tasks_dir, f"{task.id}.json")
        with open(task_file, "w") as f:
            json.dump(task.to_dict(), f, indent=4)
    
    def load_all_tasks(self):
        self.tasks = []
        for filename in os.listdir(self.tasks_dir):
            if filename.endswith(".json"):
                task_path = os.path.join(self.tasks_dir, filename)
                try:
                    with open(task_path, "r") as f:
                        task_data = json.load(f)
                        task = Task.from_dict(task_data)
                        self.tasks.append(task)
                except Exception as e:
                    print(f"Error loading task {filename}: {e}")
        return self.tasks    