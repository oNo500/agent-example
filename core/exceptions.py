class VideoAgentException(Exception):
    """Agent基础异常"""
    pass

class VideoProcessingError(VideoAgentException):
    """视频处理相关错误"""
    pass

class LLMAnalysisError(VideoAgentException):
    """LLM分析相关错误"""
    pass

class ToolExecutionError(VideoAgentException):
    """工具执行相关错误"""
    pass

class ConfigurationError(VideoAgentException):
    """配置相关错误"""
    pass