"""
gemini-draw 工具函数
路径处理、超时配置、日志格式等
"""

import os
import logging
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 日志配置
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """获取带中文格式的 logger"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ---------------------------------------------------------------------------
# 路径处理
# ---------------------------------------------------------------------------

DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads/gemini-draw-output")


def ensure_output_dir(output_dir: Optional[str] = None) -> Path:
    """确保输出目录存在，返回 Path 对象"""
    target = Path(output_dir) if output_dir else Path(DEFAULT_DOWNLOAD_DIR)
    target.mkdir(parents=True, exist_ok=True)
    return target


def sanitize_filename(prompt: str, max_len: int = 60) -> str:
    """将 prompt 清理为合法的文件名"""
    # 移除或替换非法字符
    illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']
    name = prompt
    for ch in illegal_chars:
        name = name.replace(ch, "_")
    name = name.strip(" _.-")
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0]
    return name or "gemini_image"


# ---------------------------------------------------------------------------
# 超时配置
# ---------------------------------------------------------------------------

# 图片生成等待超时（毫秒）
DEFAULT_GENERATION_TIMEOUT_MS = 120_000  # 120 秒

# CDP 命令超时（秒）
DEFAULT_CDP_TIMEOUT_SEC = 30

# 标签页导航超时（秒）
DEFAULT_NAVIGATION_TIMEOUT_SEC = 30

# DOM 查询重试间隔（毫秒）
DEFAULT_POLL_INTERVAL_MS = 500


# ---------------------------------------------------------------------------
# Gemini URL 常量
# ---------------------------------------------------------------------------

GEMINI_URL = "https://gemini.google.com"
GEMINI_URL_PATTERN = "gemini.google.com"
