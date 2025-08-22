from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
from pydantic import BaseModel, Field
from core.llm_client import GeminiClient, FrameInfo, DetectionRegion
from tools.registry import tool_registry
from core.exceptions import VideoAgentException, ConfigurationError
from config import Config

class ProcessingTask(BaseModel):
    """处理任务模型"""
    task_id: str = Field(..., description="任务ID")
    video_path: str = Field(..., description="视频路径")
    target_description: str = Field(..., description="目标描述")
    regions: List[DetectionRegion] = Field(default_factory=list, description="检测区域列表")
    status: str = Field(..., description="任务状态")
    output_path: Optional[str] = Field(None, description="输出路径")

class VideoAgent:
    """视频处理智能代理核心类"""
    
    def __init__(self, api_key: str = None):
        """初始化VideoAgent
        
        Args:
            api_key: Gemini API密钥，如果不提供则从环境变量读取
        """
        self.config = Config()
        self.llm_client = GeminiClient(api_key)
        self.tool_registry = tool_registry  # 使用全局工具注册实例
        self.logger = self._setup_logger()
        
        # 注册默认工具
        self._register_default_tools()
        
        self.logger.info("VideoAgent initialized successfully")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志配置"""
        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, self.config.log_level))
        
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
        # 导入工具模块，触发工具注册
        try:
            from tools import video_tools
            from tools import annotation_tools
            tool_count = len(self.tool_registry.list_tools())
            self.logger.info(f"Registered {tool_count} video processing and annotation tools")
        except ImportError as e:
            self.logger.warning(f"Failed to import tools: {e}")
    
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
            
            # 检查是否是标注类任务（手机打码、物体遮挡等）
            annotation_keywords = ["打码", "遮挡", "马赛克", "隐私", "标注", "手机", "人脸"]
            is_annotation_task = any(keyword in user_input for keyword in annotation_keywords)
            
            if is_annotation_task:
                # 对于标注类任务，直接创建标注工作流
                self.logger.info("Detected annotation task, creating manual annotation workflow")
                
                # 提取目标描述
                target_description = "手机"  # 默认
                if "人脸" in user_input:
                    target_description = "人脸"
                elif "手机" in user_input:
                    target_description = "手机"
                
                # 先检查是否已有标注数据
                existing_sessions = self.tool_registry.execute_tool("list_annotation_sessions")
                sessions_data = json.loads(existing_sessions)
                
                # 查找相同视频的标注会话
                matching_session = None
                for session in sessions_data.get("sessions", []):
                    if session.get("video_path") == video_path:
                        matching_session = session
                        break
                
                if matching_session:
                    # 尝试加载现有标注数据
                    annotation_data = self.tool_registry.execute_tool(
                        "load_annotation_data", 
                        session_id=matching_session["session_id"]
                    )
                    annotation_result = json.loads(annotation_data)
                    
                    if annotation_result.get("status") != "no_annotation":
                        # 有标注数据，直接执行打码
                        self.logger.info("Found existing annotation data, applying mosaic")
                        regions_data = json.dumps({"regions": annotation_result.get("regions", [])})
                        output_path = self.tool_registry.execute_tool(
                            "mosaic_video_regions",
                            video_path=video_path,
                            regions_data=regions_data,
                            mosaic_strength=15
                        )
                        return f"✅ 打码处理完成！输出文件: {output_path}"
                
                # 没有现有标注数据，创建新的标注工作流
                workflow_result = await self.create_manual_annotation_workflow(
                    video_path, target_description
                )
                workflow_data = json.loads(workflow_result)
                return workflow_data.get("message", "标注工作流已创建")
            
            else:
                # 对于其他任务，使用原有的LLM分解流程
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
                video_path=video_path,
                use_motion_detection=True
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
    
    async def create_manual_annotation_workflow(
        self, 
        video_path: str, 
        target_description: str = "手机"
    ) -> str:
        """创建手动标注工作流
        
        Args:
            video_path: 视频路径
            target_description: 目标描述
            
        Returns:
            工作流信息和说明
        """
        try:
            if not self.tool_registry.has_tool("create_annotation_workflow"):
                raise VideoAgentException("create_annotation_workflow tool not available")
            
            workflow_result = self.tool_registry.execute_tool(
                "create_annotation_workflow",
                video_path=video_path,
                target_description=target_description
            )
            
            return workflow_result
            
        except Exception as e:
            raise VideoAgentException(f"Manual annotation workflow creation failed: {str(e)}") from e