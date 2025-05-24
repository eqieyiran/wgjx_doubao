# exceptions/error_handler.py

import logging

# 设置本模块专用 logger
logger = logging.getLogger(__name__)

class TemplateNotFoundError(Exception):
    """当模板图片不存在时抛出该异常"""
    def __init__(self, message="模板图片未找到"):
        self.message = message
        logger.error(f"[TemplateNotFoundError] {message}")
        super().__init__(self.message)


class CoordinateOutOfBoundsError(Exception):
    """当坐标超出屏幕范围时抛出该异常"""
    def __init__(self, message="坐标超出屏幕边界"):
        self.message = message
        logger.error(f"[CoordinateOutOfBoundsError] {message}")
        super().__init__(self.message)


class ErrorHandler:
    """
    错误处理工具类，用于统一捕获、处理和记录错误
    """

    # 预设错误码常量
    ERR_001 = "ERR_001: 模板匹配失败"
    ERR_002 = "ERR_002: 坐标越界"
    ERR_003 = "ERR_003: 任务执行超时"
    ERR_004 = "ERR_004: 参数错误"

    @staticmethod
    def handle(error_code, **kwargs):
        """
        统一错误处理入口
        :param error_code: 错误码，例如 ERR_002
        :param kwargs: 可选参数，用于补充上下文信息
        """
        message = getattr(ErrorHandler, error_code, "未知错误")
        if isinstance(message, str):
            for key, value in kwargs.items():
                message += f", {key}={value}"
            logger.error(message)
        else:
            logger.error(f"未知错误码: {error_code}")


# 示例错误码常量导出（方便其他模块导入使用）
ERR_001 = ErrorHandler.ERR_001
ERR_002 = ErrorHandler.ERR_002
ERR_003 = ErrorHandler.ERR_003
ERR_004 = ErrorHandler.ERR_004
