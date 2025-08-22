from typing import Dict, List, Any, Optional
import logging
import asyncio
from dataclasses import dataclass
from core.llm_client import GeminiClient, FrameInfo, DetectionRegion
from tools.registry import ToolRegistry
from core.exceptions import VideoAgentException, ConfigurationError
from config import Config

@dataclass
class ProcessingTask:
    task_id: str
    video_path: str
    target_description: str
    regions: List[DetectionRegion]
    status: str
    output_path: Optional[str] = None

class VideoAgent:
    """视频处理智能代理核心类"""
    
    def __init__(self, api_key: str = None):
        """初始化VideoAgent
        
        Args:
            api_key: Gemini API密钥，如果不提供则从环境变量读取
        """
        self.config = Config()
        self.llm_client = GeminiClient(api_key)
        self.tool_registry = ToolRegistry()
        self.logger = self._setup_logger()
        
        # 注册默认工具
        self._register_default_tools()
        
        self.logger.info("VideoAgent initialized successfully")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志配置"""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _register_default_tools(self):
        """注册默认工具函数"""
        # 这里将注册默认的视频处理工具
        # 具体工具实现将在后续步骤中添加
        pass
    
    async def process_request(self, user_input: str, video_path: str) -> str:
        """处理用户请求的主流程
        
        Args:
            user_input: 用户输入的处理需求
            video_path: 视频文件路径
            
        Returns:
            处理结果描述
            
        Raises:
            VideoAgentException: 处理过程中的各种异常
        """
        try:
            self.logger.info(f"Processing request: {user_input}")
            self.logger.info(f"Video path: {video_path}")
            
            # 步骤1: 获取视频基本信息
            video_info = await self._get_video_info(video_path)
            self.logger.info(f"Video info: {video_info}")
            
            # 步骤2: 分解任务
            available_tools = self.tool_registry.get_tool_descriptions()
            task_steps = await self.llm_client.decompose_task(
                user_input, available_tools, video_info
            )
            self.logger.info(f"Task decomposed into {len(task_steps)} steps")
            
            # 步骤3: 执行任务步骤
            result = await self._execute_task_steps(task_steps, video_path, user_input)
            
            self.logger.info("Request processed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process request: {str(e)}")
            raise VideoAgentException(f"Processing failed: {str(e)}") from e
    
    async def _get_video_info(self, video_path: str) -> Dict:
        """获取视频基本信息"""
        try:
            if self.tool_registry.has_tool("get_video_info"):
                info_str = self.tool_registry.execute_tool("get_video_info", video_path=video_path)
                import json
                return json.loads(info_str)
            else:
                # 如果没有注册工具，返回基本信息
                return {
                    "path": video_path,
                    "status": "info_unavailable"
                }
        except Exception as e:
            self.logger.warning(f"Failed to get video info: {str(e)}")
            return {"path": video_path, "error": str(e)}
    
    async def _execute_task_steps(
        self, 
        task_steps: List[Dict], 
        video_path: str, 
        user_input: str
    ) -> str:
        """执行任务步骤
        
        Args:
            task_steps: 任务步骤列表
            video_path: 视频路径
            user_input: 用户输入
            
        Returns:
            执行结果
        """
        results = []
        
        for i, step in enumerate(task_steps):
            try:
                self.logger.info(f"Executing step {i+1}: {step.get('description', 'Unknown')}")
                
                tool_name = step.get("tool_name")
                parameters = step.get("parameters", {})
                
                if not tool_name:
                    self.logger.warning(f"Step {i+1} has no tool name, skipping")
                    continue
                
                if not self.tool_registry.has_tool(tool_name):
                    self.logger.warning(f"Tool '{tool_name}' not found, skipping step {i+1}")
                    continue
                
                # 执行工具
                result = self.tool_registry.execute_tool(tool_name, **parameters)
                results.append(result)
                
                self.logger.info(f"Step {i+1} completed successfully")
                
            except Exception as e:
                self.logger.error(f"Step {i+1} failed: {str(e)}")
                results.append(f"Step {i+1} failed: {str(e)}")
        
        # 汇总结果
        if results:
            final_result = results[-1]  # 通常最后一步的结果是最终结果
            return f"Processing completed. Result: {final_result}"
        else:
            return "Processing completed, but no results were generated."
    
    def register_tool(self, func, name: str = None, description: str = None):
        """注册新的工具函数
        
        Args:
            func: 工具函数
            name: 工具名称
            description: 工具描述
        """
        return self.tool_registry.register(func, name=name, description=description)
    
    def list_tools(self) -> List[str]:
        """列出所有可用工具"""
        return self.tool_registry.list_tools()
    
    def get_tool_info(self, tool_name: str) -> Dict:
        """获取工具信息"""
        return self.tool_registry.get_tool_info(tool_name)
    
    async def analyze_video_content(
        self, 
        video_path: str, 
        target_description: str
    ) -> List[DetectionRegion]:
        """分析视频内容，识别目标对象
        
        Args:
            video_path: 视频路径
            target_description: 目标描述
            
        Returns:
            检测区域列表
        """
        try:
            # 提取关键帧
            if not self.tool_registry.has_tool("extract_video_frames"):
                raise VideoAgentException("extract_video_frames tool not available")
            
            frames_info_str = self.tool_registry.execute_tool(
                "extract_video_frames", 
                video_path=video_path
            )
            
            import json
            frames_data = json.loads(frames_info_str)
            frames = [
                FrameInfo(
                    frame_id=f["frame_id"],
                    timestamp=f["timestamp"],
                    image_path=f["image_path"],
                    width=f.get("width", 1920),
                    height=f.get("height", 1080)
                )
                for f in frames_data["frames"]
            ]
            
            # LLM分析
            regions = await self.llm_client.analyze_video_frames(frames, target_description)
            
            return regions
            
        except Exception as e:
            raise VideoAgentException(f"Video content analysis failed: {str(e)}") from e