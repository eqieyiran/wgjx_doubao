# utils/persistence.py

import os
import json
from PyQt5.QtWidgets import QMessageBox


TASKS_JSON_PATH = "tasks.json"


def save_task_groups(group_manager, file_path=TASKS_JSON_PATH):
    try:
        data = {
            "root_group": group_manager.root_group.to_dict()
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"✅ 任务组已保存至 {file_path}")
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False


def load_task_groups():
    if not os.path.exists(TASKS_JSON_PATH):
        print("✅ 文件不存在，使用默认任务组")
        return None

    try:
        with open(TASKS_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            root_group_data = data.get("root_group")
            if not root_group_data:
                print("⚠️ JSON 中缺少 'root_group' 字段")
                return None

            from models.task_model import TaskGroup
            return TaskGroup.from_dict(root_group_data)
    except json.JSONDecodeError as je:
        print(f"❌ JSON 解码失败: {je}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")

    print("⚠️ 使用默认任务组替代损坏配置")
    return None