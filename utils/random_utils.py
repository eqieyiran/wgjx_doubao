import random
import time


def random_click_offset(coordinates, pixel_range=5):
    """生成随机点击偏移"""
    offset_x = random.randint(-pixel_range, pixel_range)
    offset_y = random.randint(-pixel_range, pixel_range)

    # 确保坐标不为负数
    new_x = max(0, coordinates[0] + offset_x)
    new_y = max(0, coordinates[1] + offset_y)

    return (new_x, new_y)


def random_delay(min_ms=1, max_ms=3000):
    """随机延迟"""
    delay = random.randint(min_ms, max_ms)
    time.sleep(delay / 1000.0)
    return delay


def random_typing_delay(base_delay):
    """字符输入间隔随机化"""
    variation = random.uniform(0.8, 1.2)  # ±20% 变化
    return base_delay * variation


def generate_random_direction():
    """生成随机方向（上、下、左、右）"""
    return random.choice(['up', 'down', 'left', 'right'])
