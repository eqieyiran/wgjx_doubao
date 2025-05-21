def adjust_coordinates(coordinates, max_offset=5):
    """坐标线性偏移"""
    offset_x = random.randint(-max_offset, max_offset)
    offset_y = random.randint(-max_offset, max_offset)

    adjusted_x = max(0, coordinates[0] + offset_x)
    adjusted_y = max(0, coordinates[1] + offset_y)

    return (adjusted_x, adjusted_y)


def validate_coordinates(coordinates, screen_size):
    """验证坐标是否在屏幕范围内"""
    x, y = coordinates
    width, height = screen_size

    if x < 0 or y < 0 or x >= width or y >= height:
        return False
    return True


def clamp_coordinates(coordinates, screen_size):
    """将坐标限制在屏幕范围内"""
    x, y = coordinates
    width, height = screen_size

    clamped_x = max(0, min(x, width - 1))
    clamped_y = max(0, min(y, height - 1))

    return (clamped_x, clamped_y)
