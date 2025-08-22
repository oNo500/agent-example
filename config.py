import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # LLM配置
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # 视频处理配置
    MAX_VIDEO_DURATION: int = int(os.getenv("MAX_VIDEO_DURATION", "300"))
    DEFAULT_SAMPLE_RATE: int = int(os.getenv("DEFAULT_SAMPLE_RATE", "30"))
    MAX_FRAMES_PER_REQUEST: int = int(os.getenv("MAX_FRAMES_PER_REQUEST", "20"))
    
    # 输出配置
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # 性能配置
    MAX_MEMORY_MB: int = int(os.getenv("MAX_MEMORY_MB", "2048"))
    ENABLE_GPU: bool = os.getenv("ENABLE_GPU", "true").lower() == "true"
    CONCURRENT_WORKERS: int = int(os.getenv("CONCURRENT_WORKERS", "4"))
    
    def __post_init__(self):
        # 确保必需的目录存在
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.TEMP_DIR, exist_ok=True)