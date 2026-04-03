"""
gemini-draw 异常体系
"""


class GeminiDrawError(Exception):
    """gemini-draw 基础异常"""
    pass


class ChromeConnectionError(GeminiDrawError):
    """无法连接到 Chrome CDP 端口"""
    pass


class NoGeminiTabError(GeminiDrawError):
    """找不到 Gemini 标签页且无法创建"""
    pass


class TabNavigationError(GeminiDrawError):
    """标签页导航失败（超时/URL 不匹配）"""
    pass


class ImageGenerationTimeout(GeminiDrawError):
    """图片生成超时"""
    pass


class ImageDownloadError(GeminiDrawError):
    """图片下载失败"""
    pass


class PromptSubmissionError(GeminiDrawError):
    """Prompt 提交失败"""
    pass


class DOMStateError(GeminiDrawError):
    """DOM 状态不符合预期"""
    pass
