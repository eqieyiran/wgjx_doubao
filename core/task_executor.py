import time
import random
from utils.random_utils import random_click_offset, random_typing_delay
from utils.coordinate_utils import adjust_coordinates
from exceptions.error_handler import ErrorHandler, ERR_002
from exceptions.error_handler import CoordinateOutOfBoundsError, ERR_002  # 替换掉之前的未定义错误

class TaskExecutor:
    def __init__(self, random_offset=True, dynamic_delay=True):
        self.random_offset = random_offset
        self.dynamic_delay = dynamic_delay
        self.current_coordinates = None

    def execute_click(self, coordinates, count=1, interval=100, hold_time=0):
        """执行点击操作"""
        try:
            adjusted_coords = coordinates

            if self.random_offset:
                adjusted_coords = random_click_offset(coordinates, 5)

            for _ in range(count):
                self._perform_click(adjusted_coords)
                delay = random_typing_delay(interval) if self.dynamic_delay else interval
                time.sleep(delay / 1000.0)

            return True
        except CoordinateOutOfBoundsError as e:
            ErrorHandler.handle(ERR_002, original=coordinates, corrected=adjusted_coords)
            return False

    def execute_drag(self, start_coords, end_coords, direction, distance, duration=500):
        """执行拖拽操作"""
        try:
            if self.random_offset:
                start_coords = adjust_coordinates(start_coords, 5)
                end_coords = adjust_coordinates(end_coords, 5)

            linear_path = self._calculate_linear_path(start_coords, end_coords, direction, distance)

            self._perform_drag_start(start_coords)

            for point in linear_path:
                self._perform_drag_move(point)
                if self.dynamic_delay:
                    delay = random.uniform(10, 50)
                    time.sleep(delay / 1000.0)

            self._perform_drag_end(end_coords)

            return True
        except Exception as e:
            # 错误处理逻辑...
            return False

    def execute_typing(self, text, interval=100):
        """执行文本输入操作"""
        for char in text:
            self._perform_type(char)
            delay = random_typing_delay(interval) if self.dynamic_delay else interval
            time.sleep(delay / 1000.0)

    def execute_swipe(self, start_coords, end_coords, duration=500):
        """执行滑动操作"""
        velocity_variation = random.uniform(0.9, 1.1)  # 速度波动10%
        adjusted_duration = int(duration * velocity_variation)

        path = self._generate_swipe_path(start_coords, end_coords)

        self._perform_swipe_start(start_coords)

        for point in path:
            self._perform_swipe_move(point)
            time.sleep(adjusted_duration / 1000.0 / len(path))

        self._perform_swipe_end(end_coords)

    # 私有方法模拟具体操作
    def _perform_click(self, coords):
        print(f"Clicking at {coords}")

    def _perform_drag_start(self, coords):
        print(f"Drag start at {coords}")

    def _perform_drag_move(self, coords):
        print(f"Drag move to {coords}")

    def _perform_drag_end(self, coords):
        print(f"Drag end at {coords}")

    def _perform_type(self, char):
        print(f"Typing '{char}'")

    def _perform_swipe_start(self, coords):
        print(f"Swipe start at {coords}")

    def _perform_swipe_move(self, coords):
        print(f"Swipe move to {coords}")

    def _perform_swipe_end(self, coords):
        print(f"Swipe end at {coords}")

    def _calculate_linear_path(self, start, end, direction, distance):
        # 实现线性偏移路径计算
        return [start, end]

    def _generate_swipe_path(self, start, end):
        # 实现滑动路径生成
        return [start, end]
