"""
gemini-draw: 使用 Google Gemini 生成图片的 AI Agent 技能
通过隔离 profile + 后台 headless Chrome runtime 完成静默生成与原图下载
"""

from .gemini_draw import draw, GeminiDrawError

__all__ = ["draw", "GeminiDrawError"]
__version__ = "2.0.0"
