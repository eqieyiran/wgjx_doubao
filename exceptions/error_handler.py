ERR_001 = "ERR_001"  # 模板图片不存在
ERR_002 = "ERR_002"  # 屏幕坐标越界
ERR_003 = "ERR_003"  # 时间窗口超时


class TemplateNotFoundError(Exception):
    pass


class CoordinateOutOfBoundsError(Exception):
    pass


class TaskTimeoutError(Exception):
    pass


class ErrorHandler:
    @staticmethod
    def handle(error_code, **kwargs):
        """统一异常处理"""
        if error_code == ERR_001:
            message = f"模板图片不存在: {kwargs.get('path', '未知路径')}"
            print(f"[ERROR] {message}")
            return {"error": error_code, "message": message}

        elif error_code == ERR_002:
            original = kwargs.get('original')
            corrected = kwargs.get('corrected')
            message = f"坐标越界修正: {original} -> {corrected}"
            print(f"[WARNING] {message}")
            return {"error": error_code, "message": message, "original": original, "corrected": corrected}

        elif error_code == ERR_003:
            group = kwargs.get('group')
            message = f"任务组 '{group}' 超时终止"
            print(f"[ERROR] {message}")
            return {"error": error_code, "message": message, "group": group}

        else:
            message = f"未知错误: {error_code}"
            print(f"[ERROR] {message}")
            return {"error": error_code, "message": message}
