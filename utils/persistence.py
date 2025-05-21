import json
import os

TASKS_JSON_PATH = "tasks.json"

def save_task_groups(group_manager, file_path="tasks.json"):
    """将任务组结构保存到 JSON 文件"""
    def serialize_group(group):
        return {
            "name": group.name,
            "execution_rule": group.execution_rule,
            "children": [serialize_group(child) for child in group.children]
            # 可扩展保存更多字段如 tasks 列表等
        }


    root_data = serialize_group(group_manager.root_group)

    with open(TASKS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(root_data, f, ensure_ascii=False, indent=4)

def load_task_groups():
    """从 JSON 文件加载任务组结构"""
    if not os.path.exists(TASKS_JSON_PATH):
        return None

    from models.task_model import TaskGroup

    def build_group(data, parent=None):
        group = TaskGroup(data["name"], parent=parent)
        for child_data in data.get("children", []):
            child_group = build_group(child_data, parent=group)
            group.add_child(child_group)
        return group

    with open(TASKS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        return build_group(data)