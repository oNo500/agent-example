import os
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """应用配置类，使用Pydantic Settings"""
    
    # LLM配置
    gemini_api_key: str = Field(default="", description="Gemini API密钥")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", description="使用的Gemini模型")
    
    # 视频处理配置
    max_video_duration: int = Field(default=300, description="最大视频时长（秒）")
    DEFAULT_SAMPLE_RATE: int = Field(default=30, description="默认采样率")
    MAX_FRAMES_PER_REQUEST: int = Field(default=20, description="每次请求最大帧数")
    
    # 输出配置
    OUTPUT_DIR: str = Field(default="output", description="输出目录")
    TEMP_DIR: str = Field(default="temp", description="临时目录")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="日志级别"
    )
    
    # 性能配置
    max_memory_mb: int = Field(default=2048, description="最大内存使用（MB）")
    enable_gpu: bool = Field(default=True, description="是否启用GPU加速")
    concurrent_workers: int = Field(default=4, description="并发工作线程数")
    
    # 用户界面配置
    auto_open_browser: bool = Field(default=True, description="是否自动打开浏览器标注界面")
    
    @field_validator("max_video_duration")
    @classmethod
    def validate_max_video_duration(cls, v):
        if v <= 0 or v > 3600:  # 最大1小时
            raise ValueError("视频时长必须在1秒到3600秒之间")
        return v
    
    @field_validator("concurrent_workers")
    @classmethod
    def validate_concurrent_workers(cls, v):
        if v < 1 or v > 16:
            raise ValueError("并发工作线程数必须在1到16之间")
        return v
    
    def model_post_init(self, __context) -> None:
        """初始化后处理"""
        # 确保必需的目录存在
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False
        # 支持旧的大写环境变量名
        env_file_encoding = "utf-8"