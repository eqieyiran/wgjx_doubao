from PyQt5.QtCore import QThread, pyqtSignal


class TaskExecutor(QThread):
    log_signal = pyqtSignal(str, str)  # level, message
    task_status_updated = pyqtSignal(int)  # row index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.running = False
        self.paused = False

    def set_tasks(self, tasks):
        """设置要执行的任务列表"""
        self.tasks = tasks

    def run(self):
        """QThread 的入口函数"""
        if not self.tasks:
            self.log_signal.emit("WARNING", "没有可执行的任务")
            return

        self.running = True
        self.paused = False

        for idx, task in enumerate(self.tasks):
            if not self.running:
                break
            while self.paused:
                pass  # 暂停时等待

            try:
                self.log_signal.emit("INFO", f"正在执行任务: {task.name}")
                success = self._execute_task(task)
                status = "成功" if success else "失败"
                self.log_signal.emit("SUCCESS" if success else "ERROR", f"任务 [{task.name}] 执行 {status}")
                task.status = status
                self.task_status_updated.emit(idx)
            except Exception as e:
                task.status = "失败"
                self.task_status_updated.emit(idx)
                self.log_signal.emit("ERROR", f"执行任务 [{task.name}] 时出错: {str(e)}")

        self.log_signal.emit("INFO", "所有任务已执行完毕")

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False
        self.paused = False

    def _execute_task(self, task):
        """
        根据任务类型模拟执行
        实际开发中可以替换为真实操作，如图像识别、点击等
        """
        import time

        if task.task_type == "click":
            self.log_signal.emit("DEBUG", f"执行点击任务: {task.parameters.get('location', '未知位置')}")
        elif task.task_type == "match":
            template = task.parameters.get("template", "unknown.png")
            self.log_signal.emit("DEBUG", f"执行匹配任务: {template}")
        elif task.task_type == "type":
            text = task.parameters.get("text", "")
            self.log_signal.emit("DEBUG", f"执行输入任务: {text}")
        elif task.task_type == "swipe":
            path = task.parameters.get("path", [])
            self.log_signal.emit("DEBUG", f"执行滑动任务: {path}")

        # 模拟执行耗时
        time.sleep(1)  # ⚠️ 不要用 QThread.msleep，否则无法响应信号
        return True