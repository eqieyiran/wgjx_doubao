import os
import cv2
import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from src.models.execution_log import ExecutionLog

class ImageProcessor:
    def __init__(self, settings):
        self.settings = settings
        self.thread_count = settings.get("thread_count", 4)
        self.batch_size = settings.get("batch_size", 10)
        self.preprocess = settings.get("preprocess_image", True)
        self.algorithm = settings.get("image_algorithm", "模板匹配")
    
    def process_task(self, task, log_manager):
        """处理单个任务，识别指定路径下的图片"""
        # 创建执行日志
        log = ExecutionLog(
            task_id=task.id,
            task_name=task.name,
            status="进行中",
            message="开始处理任务..."
        )
        log_manager.add_log(log)
        
        try:
            # 获取所有需要处理的图片路径
            image_paths = self._get_image_paths(task.image_path, task.recursive)
            
            if not image_paths:
                log.status = "失败"
                log.message = "未找到图片文件"
                log.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_manager.add_log(log)
                return False
            
            # 根据算法类型处理图片
            if self.algorithm == "模板匹配":
                results = self._process_with_template_matching(task, image_paths)
            elif self.algorithm == "特征点匹配":
                results = self._process_with_feature_matching(task, image_paths)
            elif self.algorithm == "深度学习":
                results = self._process_with_deep_learning(task, image_paths)
            else:
                results = []
            
            # 处理结果
            matched = any(result["matched"] for result in results)
            
            if matched:
                # 执行匹配成功动作
                self._execute_action(task.match_action)
                log.message = f"匹配成功！找到 {sum(1 for r in results if r['matched'])} 个匹配项"
            else:
                # 执行匹配失败动作
                self._execute_action(task.fail_action)
                log.message = "匹配失败！未找到符合条件的图片"
            
            # 更新任务状态和最后运行时间
            task.status = "已完成"
            task.last_run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 更新日志
            log.status = "成功"
            log.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.matched = matched
            log.match_score = max(result["score"] for result in results) if results else 0
            log.matched_image = next((result["path"] for result in results if result["matched"]), None)
            
            log_manager.add_log(log)
            return True
            
        except Exception as e:
            # 处理异常
            log.status = "失败"
            log.message = f"处理任务时出错: {str(e)}"
            log.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_manager.add_log(log)
            return False
    
    def _get_image_paths(self, path, recursive=True):
        """获取指定路径下的所有图片文件"""
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp']
        image_paths = []
        
        if os.path.isfile(path):
            if any(path.lower().endswith(ext) for ext in image_extensions):
                return [path]
            else:
                return []
        
        elif os.path.isdir(path):
            if recursive:
                for root, _, files in os.walk(path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in image_extensions):
                            image_paths.append(os.path.join(root, file))
            else:
                for file in os.listdir(path):
                    file_path = os.path.join(path, file)
                    if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in image_extensions):
                        image_paths.append(file_path)
        
        return image_paths
    
    def _process_with_template_matching(self, task, image_paths):
        """使用模板匹配算法处理图片"""
        results = []
        
        try:
            # 读取模板图片
            template = cv2.imread(task.image_path)
            if template is None:
                raise ValueError(f"无法读取模板图片: {task.image_path}")
            
            # 转换为灰度图（如果需要）
            if len(template.shape) == 3:
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                template_gray = template
            
            # 使用线程池并行处理图片
            with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
                futures = []
                
                # 分批处理图片
                for i in range(0, len(image_paths), self.batch_size):
                    batch = image_paths[i:i+self.batch_size]
                    futures.append(executor.submit(self._process_image_batch, batch, template_gray, task.threshold))
                
                # 收集结果
                for future in futures:
                    batch_results = future.result()
                    results.extend(batch_results)
        
        except Exception as e:
            print(f"模板匹配处理出错: {e}")
        
        return results
    
    def _process_image_batch(self, image_paths, template, threshold):
        """处理一批图片"""
        batch_results = []
        
        for img_path in image_paths:
            try:
                # 读取图片
                img = cv2.imread(img_path)
                if img is None:
                    batch_results.append({
                        "path": img_path,
                        "matched": False,
                        "score": 0,
                        "message": "无法读取图片"
                    })
                    continue
                
                # 转换为灰度图
                if len(img.shape) == 3:
                    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    img_gray = img
                
                # 图像预处理（如果需要）
                if self.preprocess:
                    img_gray = self._preprocess_image(img_gray)
                
                # 模板匹配
                result = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # 判断是否匹配
                matched = max_val >= threshold
                
                batch_results.append({
                    "path": img_path,
                    "matched": matched,
                    "score": max_val,
                    "message": "匹配成功" if matched else "匹配失败"
                })
                
            except Exception as e:
                batch_results.append({
                    "path": img_path,
                    "matched": False,
                    "score": 0,
                    "message": f"处理图片时出错: {str(e)}"
                })
        
        return batch_results
    
    def _preprocess_image(self, image):
        """图像预处理"""
        # 高斯模糊降噪
        image = cv2.GaussianBlur(image, (5, 5), 0)
        
        # 直方图均衡化增强对比度
        if len(image.shape) == 2:  # 灰度图
            image = cv2.equalizeHist(image)
        else:  # 彩色图
            ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
            channels = cv2.split(ycrcb)
            channels[0] = cv2.equalizeHist(channels[0])
            ycrcb = cv2.merge(channels)
            image = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
        
        return image
    
    def _process_with_feature_matching(self, task, image_paths):
        """使用特征点匹配算法处理图片"""
        # 实现特征点匹配逻辑
        results = []
        # ...
        return results
    
    def _process_with_deep_learning(self, task, image_paths):
        """使用深度学习算法处理图片"""
        # 实现深度学习匹配逻辑
        results = []
        # ...
        return results
    
    def _execute_action(self, action):
        """执行指定的动作"""
        if not action:
            return
        
        try:
            # 可以根据不同的动作类型执行不同的操作
            # 例如：执行系统命令、调用API、发送邮件等
            if action.startswith("cmd:"):
                # 执行系统命令
                command = action[4:].strip()
                os.system(command)
            elif action.startswith("api:"):
                # 调用API
                pass
            elif action.startswith("email:"):
                # 发送邮件
                pass
            else:
                # 默认执行系统命令
                os.system(action)
                
        except Exception as e:
            print(f"执行动作时出错: {e}")    