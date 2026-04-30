import logging
import os
import sys
from datetime import datetime


def setup_logger(
    name: str = "crawl4ai",
    log_level: int = logging.INFO,
    log_dir: str = "logs\\crawl4ai",
    log_file: str = None,
) -> logging.Logger:
    """
    创建并配置一个日志记录器，同时输出到控制台和文件
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: 日志文件目录
        log_file: 日志文件名，如果为None则自动生成带时间戳的文件名
    
    Returns:
        配置好的 Logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成日志文件名
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"{name}_{timestamp}.log"
    
    log_path = os.path.join(log_dir, log_file)
    
    # 定义日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 1. 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    # 设置控制台编码为 UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    logger.addHandler(console_handler)
    
    # 2. 文件 Handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 创建默认的全局 logger 实例
# logger = setup_logger()


# if __name__ == "__main__":
#     # 测试日志
#     # test_logger = setup_logger("test_app")
#     logger.debug("这是一条调试信息")
#     logger.info("这是一条普通信息")
#     logger.warning("这是一条警告信息")
#     logger.error("这是一条错误信息")
#     logger.critical("这是一条严重错误信息")
