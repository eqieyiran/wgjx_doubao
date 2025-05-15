import os
import time
import threading
from datetime import datetime
from src.models.task import Task
from src.models.execution_log import ExecutionLog
from src.services.image_processor import ImageProcessor

class TaskExecutor:
    def __init__(self, task_manager, log_manager, settings):
        self.task_manager = task_manager
        self.log_manager = log_manager
        self.settings = settings
        self.image_processor = ImageProcessor(settings)
        self.running_tasks = {}  # 正在运行的任务
        self.stop_event = threading.Event()
        self.thread = None
    
    def execute_task(self, task_id):
        """执行单个任务"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return False, "任务不存在"
        
        if task_id in self.running_tasks:
            return False, "任务正在运行中"
        
        # 更新任务状态
        task.status = "运行中"
        self.task_manager.save_task(task)
        
        # 创建执行线程
        thread = threading.Thread(target=self._run_task, args=(task,))
        thread.daemon = True
        self.running_tasks[task_id] = thread
        thread.start()
        
        return True, "任务已开始执行"
    
    def execute_all_tasks(self):
        """执行所有任务"""
        tasks = self.task_manager.get_all_tasks()
        for task in tasks:
            self.execute_task(task.id)
        
        return len(tasks)
    
    def stop_task(self, task_id):
        """停止正在运行的任务"""
        if task_id in self.running_tasks:
            # 设置停止事件（如果任务支持）
            self.stop_event.set()
            
            # 等待线程结束
            self.running_tasks[task_id].join(timeout=5.0)
            
            # 如果线程仍在运行，则强制终止（Python没有直接的线程终止方法）
            if self.running_tasks[task_id].is_alive():
                # 可以在这里实现更复杂的任务终止逻辑
                pass
            
            del self.running_tasks[task_id]
            self.stop_event.clear()
            return True
        
        return False
    
    def stop_all_tasks(self):
        """停止所有正在运行的任务"""
        task_ids = list(self.running_tasks.keys())
        for task_id in task_ids:
            self.stop_task(task_id)
        
        return len(task_ids)
    
    def is_task_running(self, task_id):
        """检查任务是否正在运行"""
        return task_id in self.running_tasks
    
    def _run_task(self, task):
        """在线程中运行任务"""
        try:
            # 执行图像处理
            success = self.image_processor.process_task(task, self.log_manager)
            
            # 更新任务状态
            if success:
                task.status = "已完成"
            else:
                task.status = "失败"
            
        except Exception as e:
            print(f"执行任务时出错: {e}")
            task.status = "失败"
        finally:
            # 保存任务状态
            self.task_manager.save_task(task)
            
            # 从运行中任务列表中移除
            if task.id in self.running_tasks:
                del self.running_tasks[task.id]    