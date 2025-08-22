from typing import Dict, List, Any, Optional
import logging
import asyncio
import json
import os
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
                    # 首先尝试自动保存下载的标注文件
                    self.logger.info("Trying to auto-save downloaded annotation file")
                    auto_save_result = self.tool_registry.execute_tool(
                        "auto_save_downloaded_regions",
                        session_id=matching_session["session_id"]
                    )
                    auto_save_data = json.loads(auto_save_result)
                    
                    if auto_save_data.get("status") == "success":
                        self.logger.info("Successfully auto-saved downloaded annotation file")
                    
                    # 尝试加载标注数据
                    annotation_data = self.tool_registry.execute_tool(
                        "load_annotation_data", 
                        session_id=matching_session["session_id"]
                    )
                    annotation_result = json.loads(annotation_data)
                    
                    # 检查是否有有效的标注数据
                    regions_list = annotation_result.get("regions", [])
                    has_valid_regions = (
                        annotation_result.get("status") != "no_annotation" and 
                        isinstance(regions_list, list) and 
                        len(regions_list) > 0
                    )
                    
                    if has_valid_regions:
                        # 有有效标注数据，使用LLM追踪增强后执行打码处理
                        self.logger.info(f"Found valid annotation data with {len(regions_list)} regions, enhancing with LLM tracking")
                        
                        # 转换为DetectionRegion对象作为种子
                        seed_regions = []
                        for region_data in regions_list:
                            seed_region = DetectionRegion(
                                frame_id=region_data["frame_id"],
                                object_type=region_data.get("object_type", target_description),
                                bbox=tuple(region_data["bbox"]),
                                confidence=region_data.get("confidence", 1.0),
                                description=region_data.get("description", f"{target_description}区域 - 手动标注")
                            )
                            seed_regions.append(seed_region)
                        
                        # 使用LLM追踪增强标注
                        enhanced_regions = await self.enhance_annotation_with_tracking(
                            video_path, seed_regions, target_description
                        )
                        
                        # 转换回JSON格式用于打码
                        enhanced_regions_data = {
                            "regions": [
                                {
                                    "frame_id": region.frame_id,
                                    "object_type": region.object_type,
                                    "bbox": list(region.bbox),
                                    "confidence": region.confidence,
                                    "description": region.description,
                                    "track_id": region.track_id
                                }
                                for region in enhanced_regions
                            ]
                        }
                        
                        self.logger.info(f"Enhanced tracking complete: {len(enhanced_regions)} total regions for mosaic processing")
                        regions_data = json.dumps(enhanced_regions_data)
                        output_path = self.tool_registry.execute_tool(
                            "mosaic_video_regions",
                            video_path=video_path,
                            regions_data=regions_data,
                            mosaic_strength=15
                        )
                        
                        # 提供完成后的友好提示
                        return f"""
✅ 智能追踪标注流程完成！

🎯 种子标注: {len(regions_list)} 个手动标注区域
🤖 LLM追踪: 共识别 {len(enhanced_regions)} 个追踪区域
📁 输出文件: {output_path}
🚀 使用了真正的LLM多帧分析技术，智能追踪目标运动轨迹

💡 技术优势: 结合手动标注精确度和LLM追踪能力，适应目标在视频中的位置变化！
                        """.strip()
                    else:
                        # 标注会话存在但没有完成标注，提供清晰指引
                        session_id = matching_session["session_id"]
                        annotation_file = os.path.join(
                            self.config.OUTPUT_DIR, 
                            "annotations", 
                            session_id, 
                            "annotation.html"
                        )
                        
                        return f"""
⏳ 发现已有标注会话但尚未完成标注

📋 会话ID: {session_id}
🎯 目标: {target_description}
📁 标注界面: {annotation_file}

📝 下一步操作:
1. 打开上述HTML文件（或重新运行程序自动打开）
2. 在图片上点击拖拽标注{target_description}区域
3. 点击"保存标注数据"下载regions.json文件
4. 将下载的文件复制到标注会话目录
5. 重新运行此程序完成打码处理

💡 提示: 只需标注一张图片，系统会自动应用到整个视频！
                        """.strip()
                
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
                sample_rate=15,  # 降低采样率，每15帧提取一帧
                max_frames=30,   # 增加关键帧数量，提高追踪精度
                use_motion_detection=True,
                single_best_frame=False
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
    
    async def enhance_annotation_with_tracking(
        self, 
        video_path: str, 
        seed_regions: List[DetectionRegion],
        target_description: str = "手机"
    ) -> List[DetectionRegion]:
        """使用种子标注增强LLM追踪分析
        
        Args:
            video_path: 视频路径
            seed_regions: 用户手动标注的种子区域
            target_description: 目标描述
            
        Returns:
            增强后的完整追踪区域列表
        """
        try:
            print(f"🌱 开始种子增强追踪，种子区域数量: {len(seed_regions)}")
            for i, seed in enumerate(seed_regions):
                print(f"   种子{i+1}: 帧{seed.frame_id}, 位置({seed.bbox[0]},{seed.bbox[1]}), 大小{seed.bbox[2]}x{seed.bbox[3]}")
            
            # 获取视频信息用于坐标验证
            if self.tool_registry.has_tool("get_video_info"):
                info_str = self.tool_registry.execute_tool("get_video_info", video_path=video_path)
                video_info = json.loads(info_str)
                print(f"📏 视频分辨率: {video_info.get('width', 'unknown')}x{video_info.get('height', 'unknown')}")
            else:
                print("⚠️  无法获取视频信息进行坐标验证")
            
            # 使用多帧LLM分析进行追踪
            llm_regions = await self.analyze_video_content(video_path, target_description)
            
            # 合并种子标注和LLM追踪结果
            enhanced_regions = []
            
            # 保留种子标注（用户标注优先级最高）
            for seed_region in seed_regions:
                enhanced_regions.append(seed_region)
            
            # 添加LLM发现的其他帧中的目标位置
            seed_frame_ids = {region.frame_id for region in seed_regions}
            llm_added_count = 0
            for llm_region in llm_regions:
                if llm_region.frame_id not in seed_frame_ids:
                    # 为LLM检测的区域添加追踪标识
                    llm_region.description = f"{llm_region.description} (LLM追踪)"
                    enhanced_regions.append(llm_region)
                    llm_added_count += 1
            
            print(f"📊 合并结果：{len(seed_regions)}个种子标注 + {llm_added_count}个LLM追踪 = {len(enhanced_regions)}个总区域")
            
            # 显示LLM追踪的坐标信息用于调试
            if llm_added_count > 0:
                print("🔍 LLM追踪坐标详情:")
                for region in enhanced_regions:
                    if "(LLM追踪)" in region.description:
                        print(f"   帧{region.frame_id}: 位置({region.bbox[0]},{region.bbox[1]}), 大小{region.bbox[2]}x{region.bbox[3]}")
            
            return enhanced_regions
            
        except Exception as e:
            # 如果LLM追踪失败，至少返回种子标注
            self.logger.warning(f"LLM tracking enhancement failed: {str(e)}, falling back to seed regions only")
            return seed_regions

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