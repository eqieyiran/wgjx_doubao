from src.models.task import Task, TaskManager
from src.models.execution_log import LogManager
from src.models.settings import Settings
from src.services.task_executor import TaskExecutor
from src.services.image_processor import ImageProcessor

class MainController:
    def __init__(self, main_window):
        self.main_window = main_window
        
        # 初始化模型
        self.settings = Settings()
        self.task_manager = TaskManager(self.settings.get("task_path"))
        self.log_manager = LogManager(self.settings.get("log_path"))
        
        # 初始化服务
        self.task_executor = TaskExecutor(self.task_manager, self.log_manager, self.settings)
        
        # 加载数据
        self.load_data()
        
        # 连接视图事件
        self.connect_view_signals()
    
    def load_data(self):
        """加载应用数据"""
        # 加载设置
        self.load_settings()
        
        # 加载任务（如果设置为自动加载）
        if self.settings.get("auto_load_tasks", True):
            self.load_tasks()
        
        # 加载日志
        self.load_logs()
    
    def load_settings(self):
        """加载应用设置"""
        # 可以在这里添加设置加载逻辑
        pass
    
    def load_tasks(self):
        """加载所有任务"""
        tasks = self.task_manager.load_all_tasks()
        self.update_task_table(tasks)
        return len(tasks)
    
    def load_logs(self):
        """加载所有日志"""
        logs = self.log_manager.load_logs()
        self.update_log_display(logs)
        return len(logs)
    
    def update_task_table(self, tasks):
        """更新任务表格显示"""
        task_tab = self.main_window.task_manager_tab
        task_tab.task_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            task_tab.task_table.setItem(row, 0, QTableWidgetItem(task.id))
            task_tab.task_table.setItem(row, 1, QTableWidgetItem(task.name))
            task_tab.task_table.setItem(row, 2, QTableWidgetItem(task.image_path))
            task_tab.task_table.setItem(row, 3, QTableWidgetItem(task.match_action))
            task_tab.task_table.setItem(row, 4, QTableWidgetItem(task.fail_action))
            task_tab.task_table.setItem(row, 5, QTableWidgetItem(task.status))
    
    def update_log_display(self, logs):
        """更新日志显示"""
        log_tab = self.main_window.execution_log_tab
        log_text = ""
        
        for log in logs:
            status_color = "green" if log.status == "成功" else "red" if log.status == "失败" else "blue"
            match_text = "匹配成功" if log.matched else "匹配失败"
            
            log_entry = f"""
            <div style="border-bottom: 1px solid #eee; padding: 8px 0;">
                <div style="font-weight: bold; color: {status_color};">{log.task_name} - {log.status}</div>
                <div style="color: #666;">{log.start_time} - {log.end_time or ''}</div>
                <div>{log.message}</div>
                <div>{match_text} (得分: {log.match_score or 'N/A'})</div>
            </div>
            """
            log_text += log_entry
        
        log_tab.log_text.setHtml(log_text)
    
    def connect_view_signals(self):
        """连接视图组件的信号到控制器方法"""
        # 任务管理标签页信号
        task_tab = self.main_window.task_manager_tab
        task_tab.add_task_btn.clicked.connect(self.handle_add_task)
        task_tab.edit_task_btn.clicked.connect(self.handle_edit_task)
        task_tab.delete_task_btn.clicked.connect(self.handle_delete_task)
        task_tab.execute_task_btn.clicked.connect(self.handle_execute_task)
        task_tab.execute_all_btn.clicked.connect(self.handle_execute_all_tasks)
        task_tab.save_task_btn.clicked.connect(self.handle_save_task)
        
        # 日志标签页信号
        log_tab = self.main_window.execution_log_tab
        log_tab.apply_filter_btn.clicked.connect(self.handle_filter_logs)
        log_tab.clear_log_btn.clicked.connect(self.handle_clear_logs)
        log_tab.export_log_btn.clicked.connect(self.handle_export_logs)
        log_tab.refresh_log_btn.clicked.connect(self.handle_refresh_logs)
        
        # 设置标签页信号
        settings_tab = self.main_window.settings_tab
        settings_tab.save_settings_btn.clicked.connect(self.handle_save_settings)
    
    def handle_add_task(self):
        """处理添加任务事件"""
        # 获取表单数据
        name = self.main_window.task_manager_tab.task_name_input.text()
        image_path = self.main_window.task_manager_tab.image_path_input.text()
        match_action = self.main_window.task_manager_tab.match_action_input.text()
        fail_action = self.main_window.task_manager_tab.fail_action_input.text()
        threshold = float(self.main_window.task_manager_tab.threshold_input.text() or 0.8)
        recursive = self.main_window.task_manager_tab.recursive_checkbox.isChecked()
        
        # 创建新任务
        task = Task(
            name=name,
            image_path=image_path,
            match_action=match_action,
            fail_action=fail_action,
            threshold=threshold,
            recursive=recursive
        )
        
        # 添加任务
        self.task_manager.add_task(task)
        
        # 更新任务表格
        self.update_task_table(self.task_manager.get_all_tasks())
        
        # 清空表单
        self.clear_task_form()
    
    def handle_edit_task(self):
        """处理编辑任务事件"""
        # 获取选中的任务
        selected_row = self.main_window.task_manager_tab.task_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.main_window, "警告", "请先选择一个任务")
            return
        
        task_id = self.main_window.task_manager_tab.task_table.item(selected_row, 0).text()
        task = self.task_manager.get_task(task_id)
        
        if task:
            # 填充表单
            self.main_window.task_manager_tab.task_name_input.setText(task.name)
            self.main_window.task_manager_tab.image_path_input.setText(task.image_path)
            self.main_window.task_manager_tab.match_action_input.setText(task.match_action)
            self.main_window.task_manager_tab.fail_action_input.setText(task.fail_action)
            self.main_window.task_manager_tab.threshold_input.setText(str(task.threshold))
            self.main_window.task_manager_tab.recursive_checkbox.setChecked(task.recursive)
    
    def handle_delete_task(self):
        """处理删除任务事件"""
        # 获取选中的任务
        selected_row = self.main_window.task_manager_tab.task_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.main_window, "警告", "请先选择一个任务")
            return
        
        task_id = self.main_window.task_manager_tab.task_table.item(selected_row, 0).text()
        
        # 确认删除
        reply = QMessageBox.question(
            self.main_window, "确认删除",
            "确定要删除选中的任务吗?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除任务
            self.task_manager.delete_task(task_id)
            
            # 更新任务表格
            self.update_task_table(self.task_manager.get_all_tasks())
    
    def handle_execute_task(self):
        """处理执行任务事件"""
        # 获取选中的任务
        selected_row = self.main_window.task_manager_tab.task_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self.main_window, "警告", "请先选择一个任务")
            return
        
        task_id = self.main_window.task_manager_tab.task_table.item(selected_row, 0).text()
        
        # 执行任务
        success, message = self.task_executor.execute_task(task_id)
        
        if success:
            QMessageBox.information(self.main_window, "成功", "任务已开始执行")
        else:
            QMessageBox.critical(self.main_window, "错误", message)
    
    def handle_execute_all_tasks(self):
        """处理执行所有任务事件"""
        count = self.task_executor.execute_all_tasks()
        QMessageBox.information(self.main_window, "成功", f"已开始执行 {count} 个任务")
    
    def handle_save_task(self):
        """处理保存任务配置事件"""
        # 获取选中的任务
        selected_row = self.main_window.task_manager_tab.task_table.currentRow()
        if selected_row < 0:
            # 如果没有选中任务，则添加新任务
            self.handle_add_task()
            return
        
        task_id = self.main_window.task_manager_tab.task_table.item(selected_row, 0).text()
        
        # 获取表单数据
        updated_data = {
            "name": self.main_window.task_manager_tab.task_name_input.text(),
            "image_path": self.main_window.task_manager_tab.image_path_input.text(),
            "match_action": self.main_window.task_manager_tab.match_action_input.text(),
            "fail_action": self.main_window.task_manager_tab.fail_action_input.text(),
            "threshold": float(self.main_window.task_manager_tab.threshold_input.text() or 0.8),
            "recursive": self.main_window.task_manager_tab.recursive_checkbox.isChecked()
        }
        
        # 更新任务
        task = self.task_manager.update_task(task_id, updated_data)
        
        if task:
            QMessageBox.information(self.main_window, "成功", "任务已更新")
            # 更新任务表格
            self.update_task_table(self.task_manager.get_all_tasks())
        else:
            QMessageBox.critical(self.main_window, "错误", "更新任务失败")
    
    def handle_filter_logs(self):
        """处理过滤日志事件"""
        # 获取过滤条件
        task_id = self.main_window.execution_log_tab.task_filter.currentText()
        status = self.main_window.execution_log_tab.status_filter.currentText()
        start_time = self.main_window.execution_log_tab.start_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_time = self.main_window.execution_log_tab.end_time.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        
        # 过滤日志
        logs = self.log_manager.get_logs(
            task_id=task_id if task_id != "所有任务" else None,
            status=status if status != "所有状态" else None,
            start_time=start_time,
            end_time=end_time
        )
        
        # 更新日志显示
        self.update_log_display(logs)
    
    def handle_clear_logs(self):
        """处理清空日志事件"""
        # 确认清空
        reply = QMessageBox.question(
            self.main_window, "确认清空",
            "确定要清空所有日志吗? 此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 清空日志
            self.log_manager.logs = []
            # 清空日志文件
            log_dir = self.settings.get("log_path", "logs")
            if os.path.exists(log_dir):
                for root, dirs, files in os.walk(log_dir):
                    for file in files:
                        os.remove(os.path.join(root, file))
            
            # 更新日志显示
            self.update_log_display([])
            QMessageBox.information(self.main_window, "成功", "日志已清空")
    
    def handle_export_logs(self):
        """处理导出日志事件"""
        # 实现日志导出逻辑
        pass
    
    def handle_refresh_logs(self):
        """处理刷新日志事件"""
        self.load_logs()
        QMessageBox.information(self.main_window, "成功", "日志已刷新")
    
    def handle_save_settings(self):
        """处理保存设置事件"""
        # 获取设置表单数据
        settings_data = {
            "task_path": self.main_window.settings_tab.task_path_input.text(),
            "log_path": self.main_window.settings_tab.log_path_input.text(),
            "auto_save_interval": self.main_window.settings_tab.auto_save_spinbox.value(),
            "auto_load_tasks": self.main_window.settings_tab.auto_load_tasks.isChecked(),
            "image_algorithm": self.main_window.settings_tab.algorithm_combo.currentText(),
            "thread_count": self.main_window.settings_tab.thread_spinbox.value(),
            "batch_size": self.main_window.settings_tab.batch_size_spinbox.value(),
            "preprocess_image": self.main_window.settings_tab.preprocess_checkbox.isChecked()
        }
        
        # 保存设置
        success = self.settings.update(settings_data)
        
        if success:
            QMessageBox.information(self.main_window, "成功", "设置已保存")
        else:
            QMessageBox.critical(self.main_window, "错误", "保存设置失败")
    
    def clear_task_form(self):
        """清空任务表单"""
        self.main_window.task_manager_tab.task_name_input.clear()
        self.main_window.task_manager_tab.image_path_input.clear()
        self.main_window.task_manager_tab.match_action_input.clear()
        self.main_window.task_manager_tab.fail_action_input.clear()
        self.main_window.task_manager_tab.threshold_input.setText("0.8")
        self.main_window.task_manager_tab.recursive_checkbox.setChecked(True)    