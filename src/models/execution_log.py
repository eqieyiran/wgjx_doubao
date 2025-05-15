import os
import json
from datetime import datetime

class ExecutionLog:
    def __init__(self, task_id, task_name, status, message="", 
                 start_time=None, end_time=None, matched=False, 
                 match_score=None, matched_image=None):
        self.task_id = task_id
        self.task_name = task_name
        self.status = status  # 成功, 失败, 进行中
        self.message = message
        self.start_time = start_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.end_time = end_time
        self.matched = matched
        self.match_score = match_score
        self.matched_image = matched_image
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status,
            "message": self.message,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "matched": self.matched,
            "match_score": self.match_score,
            "matched_image": self.matched_image
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            task_id=data.get("task_id"),
            task_name=data.get("task_name"),
            status=data.get("status"),
            message=data.get("message"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            matched=data.get("matched", False),
            match_score=data.get("match_score"),
            matched_image=data.get("matched_image")
        )

class LogManager:
    def __init__(self, logs_dir="logs"):
        self.logs_dir = logs_dir
        self.logs = []
        
        # 创建日志目录（如果不存在）
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    
    def add_log(self, log):
        self.logs.append(log)
        self.save_log(log)
        return log
    
    def get_logs(self, task_id=None, status=None, start_time=None, end_time=None):
        filtered_logs = self.logs
        
        if task_id:
            filtered_logs = [log for log in filtered_logs if log.task_id == task_id]
        
        if status:
            filtered_logs = [log for log in filtered_logs if log.status == status]
        
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.start_time >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if (log.end_time and log.end_time <= end_time)]
        
        return filtered_logs
    
    def save_log(self, log):
        # 按日期创建子目录
        date_dir = os.path.join(self.logs_dir, datetime.now().strftime("%Y-%m-%d"))
        if not os.path.exists(date_dir):
            os.makedirs(date_dir)
        
        # 使用时间戳作为文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        log_file = os.path.join(date_dir, f"{timestamp}.json")
        
        with open(log_file, "w") as f:
            json.dump(log.to_dict(), f, indent=4)
    
    def load_logs(self, date=None):
        self.logs = []
        
        # 如果没有指定日期，则加载所有日期的日志
        if not date:
            date_dirs = [os.path.join(self.logs_dir, d) for d in os.listdir(self.logs_dir) 
                         if os.path.isdir(os.path.join(self.logs_dir, d))]
        else:
            date_dirs = [os.path.join(self.logs_dir, date)]
            if not os.path.exists(date_dirs[0]):
                return []
        
        # 加载日志文件
        for date_dir in date_dirs:
            for filename in os.listdir(date_dir):
                if filename.endswith(".json"):
                    log_path = os.path.join(date_dir, filename)
                    try:
                        with open(log_path, "r") as f:
                            log_data = json.load(f)
                            log = ExecutionLog.from_dict(log_data)
                            self.logs.append(log)
                    except Exception as e:
                        print(f"Error loading log {filename}: {e}")
        
        # 按开始时间排序（最新的在前）
        self.logs.sort(key=lambda x: x.start_time, reverse=True)
        return self.logs    