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
    """从文件加载任务组结构（包含任务）"""
    import os
    import json
    from models.task_model import TaskGroup, Task

    if not os.path.exists("tasks.json"):
        return None

    with open("tasks.json", 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if "root_group" not in data:
                print("文件中缺少 'root_group' 字段")
                return None

            def dict_to_group(d):
                group = TaskGroup(d["name"])
                group.id = d.get("id", group.id)
                group.tasks = [Task(**t) for t in d.get("tasks", [])]
                group.children = [dict_to_group(child) for child in d.get("children", [])]
                return group

            return dict_to_group(data["root_group"])
        except json.JSONDecodeError:
            print("无法解析 JSON 文件内容")
            return None