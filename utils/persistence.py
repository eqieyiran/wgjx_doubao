# utils/persistence.py

import os
import json


def save_task_groups(group_manager, file_path="tasks.json"):
    try:
        data = {"root_group": group_manager.root_group.to_dict()}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False


def load_task_groups(file_path="tasks.json"):
    if not os.path.exists(file_path):
        print("⚠️ 配置文件不存在，使用默认配置")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            from models.task_model import TaskGroup
            return TaskGroup.from_dict(data["root_group"])
    except Exception as e:
        print(f"加载失败: {e}")
        return None
