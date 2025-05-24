import cv2
import numpy as np
from utils.random_utils import random_delay
from core.cache_manager import LRUCache
from exceptions.error_handler import TemplateNotFoundError  # 添加这行导入

class ImageMatcher:
    def __init__(self, threshold=0.8, scale_range=(0.5, 1.5), enable_random_delay=True):
        self.threshold = threshold
        self.scale_range = scale_range
        self.enable_random_delay = enable_random_delay
        self.template_cache = LRUCache(max_size=2 * 1024 * 1024 * 1024, ttl=7200)

    def match_template(self, screen_img, template_img):
        """基于OpenCV的等比缩放模板匹配"""
        if template_img is None:
            raise TemplateNotFoundError("模板图片不存在")

        if str(template_img) in self.template_cache:
            return self.template_cache[str(template_img)]

        best_match = None
        best_score = -1

        scales = np.linspace(self.scale_range[0], self.scale_range[1], 10)

        for scale in scales:
            resized_template = cv2.resize(template_img, None, fx=scale, fy=scale)

            if self.enable_random_delay:
                random_delay(1, 3000)

            result = cv2.matchTemplate(screen_img, resized_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val > best_score:
                best_score = max_val
                best_match = (max_loc, resized_template.shape[::-1])

        if best_score >= self.threshold * 0.8:  # 考虑动态阈值调整
            return best_match
        else:
            return None

    def set_threshold(self, value):
        """设置匹配阈值（0-100%）"""
        self.threshold = value / 100.0

    def set_scale_range(self, min_scale, max_scale):
        """设置缩放比例范围"""
        self.scale_range = (min_scale, max_scale)
