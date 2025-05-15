import os
import json

class Settings:
    def __init__(self, settings_file="settings.json"):
        self.settings_file = settings_file
        self.default_settings = {
            "task_path": "tasks",
            "log_path": "logs",
            "auto_save_interval": 5,
            "auto_load_tasks": True,
            "image_algorithm": "模板匹配",
            "thread_count": 4,
            "batch_size": 10,
            "preprocess_image": True
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        # 如果设置文件存在，则加载
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        # 如果文件不存在或加载失败，则使用默认设置
        return self.default_settings
    
    def save_settings(self):
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value
        return self.save_settings()
    
    def get_all(self):
        return self.settings
    
    def update(self, settings_dict):
        self.settings.update(settings_dict)
        return self.save_settings()    