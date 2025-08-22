import json
from typing import List, Dict
from tools.registry import tool_registry
from utils.video_processor import VideoProcessor
from core.llm_client import DetectionRegion
from core.exceptions import VideoProcessingError

# 创建视频处理器实例
video_processor = VideoProcessor()

@tool_registry.register
def extract_video_frames(
    video_path: str,
    sample_rate: int = 30,
    max_frames: int = 20,
    use_motion_detection: bool = True
) -> str:
    """提取视频关键帧供LLM分析
    
    Args:
        video_path: 视频文件的完整路径
        sample_rate: 采样率，每N帧提取一帧
        max_frames: 最大提取帧数，防止视频过长
        use_motion_detection: 是否使用运动检测优化帧选择
        
    Returns:
        JSON字符串，包含提取的帧信息
        格式: {"frames": [{"frame_id": 1, "timestamp": 0.5, "image_path": "/tmp/frame_1.jpg"}]}
    """
    try:
        frames = video_processor.extract_frames(video_path, sample_rate, max_frames, use_motion_detection)
        
        # 转换为JSON格式（使用Pydantic模型）
        frames_data = {
            "frames": [frame.model_dump() for frame in frames]
        }
        
        return json.dumps(frames_data, ensure_ascii=False)
        
    except Exception as e:
        raise VideoProcessingError(f"Frame extraction failed: {str(e)}")

@tool_registry.register
def mosaic_video_regions(
    video_path: str,
    regions_data: str,
    mosaic_strength: int = 15,
    tracking_enabled: bool = True
) -> str:
    """对视频指定区域进行打码处理
    
    Args:
        video_path: 源视频文件路径
        regions_data: LLM分析得到的区域信息，JSON格式字符串
        mosaic_strength: 打码强度(5-50)，数值越大越模糊
        tracking_enabled: 是否启用简单追踪优化
        
    Returns:
        处理后的视频文件路径
        
    Raises:
        VideoProcessingError: 视频处理失败时抛出
    """
    try:
        # 验证输入参数
        if not regions_data or regions_data.strip() == "":
            return json.dumps({
                "status": "skipped",
                "message": "No regions data provided. Manual annotation required.",
                "suggestion": "Use the annotation tool to mark phone locations in the extracted frames."
            }, ensure_ascii=False)
        
        # 解析区域数据
        regions_dict = json.loads(regions_data)
        
        # 转换为DetectionRegion对象
        regions = []
        for region_data in regions_dict.get("regions", []):
            region = DetectionRegion(
                frame_id=region_data["frame_id"],
                object_type=region_data.get("object_type", "unknown"),
                bbox=tuple(region_data["bbox"]),
                confidence=region_data.get("confidence", 1.0),
                description=region_data.get("description", ""),
                track_id=region_data.get("track_id")
            )
            regions.append(region)
        
        # 应用打码处理
        output_path = video_processor.apply_mosaic_regions(
            video_path, regions, mosaic_strength
        )
        
        return output_path
        
    except json.JSONDecodeError as e:
        raise VideoProcessingError(f"Invalid regions data format: {str(e)}")
    except Exception as e:
        raise VideoProcessingError(f"Mosaic processing failed: {str(e)}")

@tool_registry.register
def get_video_info(video_path: str) -> str:
    """获取视频基本信息
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        JSON格式的视频信息字符串
        包含: 时长、分辨率、帧率、文件大小等
    """
    try:
        info = video_processor.get_video_info(video_path)
        return json.dumps(info, ensure_ascii=False)
    except Exception as e:
        raise VideoProcessingError(f"Failed to get video info: {str(e)}")

@tool_registry.register
def validate_video_file(video_path: str) -> str:
    """验证视频文件是否有效
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        JSON格式的验证结果
    """
    try:
        import os
        
        result = {
            "is_valid": False,
            "exists": False,
            "readable": False,
            "error": None
        }
        
        # 检查文件是否存在
        if not os.path.exists(video_path):
            result["error"] = "File does not exist"
            return json.dumps(result, ensure_ascii=False)
        
        result["exists"] = True
        
        # 检查文件是否可读
        if not os.access(video_path, os.R_OK):
            result["error"] = "File is not readable"
            return json.dumps(result, ensure_ascii=False)
        
        result["readable"] = True
        
        # 尝试获取视频信息来验证文件格式
        try:
            video_processor.get_video_info(video_path)
            result["is_valid"] = True
        except Exception as e:
            result["error"] = f"Invalid video format: {str(e)}"
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        result = {
            "is_valid": False,
            "exists": False,
            "readable": False,
            "error": f"Validation failed: {str(e)}"
        }
        return json.dumps(result, ensure_ascii=False)

@tool_registry.register  
def list_supported_formats() -> str:
    """列出支持的视频格式
    
    Returns:
        JSON格式的支持格式列表
    """
    supported_formats = {
        "input_formats": [
            ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", 
            ".webm", ".m4v", ".3gp", ".ts", ".mts", ".m2ts"
        ],
        "output_formats": [
            ".mp4", ".avi", ".mov", ".mkv"
        ],
        "recommended_format": ".mp4",
        "notes": "MP4 format is recommended for best compatibility"
    }
    
    return json.dumps(supported_formats, ensure_ascii=False)


@tool_registry.register
def create_annotation_workflow(
    video_path: str,
    target_description: str = "手机",
    sample_rate: int = 30,
    max_frames: int = 20
) -> str:
    """创建完整的标注工作流，包含帧提取和标注界面生成
    
    Args:
        video_path: 视频文件路径
        target_description: 目标物体描述
        sample_rate: 采样率
        max_frames: 最大帧数
        
    Returns:
        工作流结果JSON，包含标注界面路径和使用说明
    """
    try:
        # 1. 提取关键帧
        frames_info = extract_video_frames(
            video_path=video_path,
            sample_rate=sample_rate,
            max_frames=max_frames,
            use_motion_detection=True
        )
        
        # 2. 创建标注会话
        from tools.annotation_tools import create_annotation_session
        session_info = create_annotation_session(
            video_path=video_path,
            frames_info=frames_info,
            session_name=f"{target_description}_annotation"
        )
        
        session_data = json.loads(session_info)
        frames_data = json.loads(frames_info)
        
        # 3. 生成使用说明
        browser_status = "🌐 浏览器已自动打开标注界面" if session_data.get("browser_opened") else "📁 请手动打开标注文件"
        
        result = {
            "status": "workflow_created", 
            "session_id": session_data["session_id"],
            "annotation_file": session_data["annotation_file"],
            "frames_extracted": len(frames_data["frames"]),
            "target_description": target_description,
            "browser_opened": session_data.get("browser_opened", False),
            "message": f"""
🎯 {target_description}标注工作流已创建！

{browser_status}
📊 已提取 {len(frames_data['frames'])} 个关键帧

📋 操作步骤:
  1. 在浏览器标注界面中拖拽选择{target_description}区域
  2. 可以为每个关键帧标注多个区域
  3. 完成后点击'保存标注数据'下载regions.json
  4. 重新运行处理程序，系统会自动加载标注数据进行打码

💡 下次处理提示: 完成标注后，重新输入相同的视频路径和需求即可自动应用打码
            """.strip(),
            "manual_next_steps": [
                "完成浏览器中的手动标注",
                "保存并下载regions.json文件", 
                "重新运行程序进行打码处理"
            ]
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        raise VideoProcessingError(f"Annotation workflow creation failed: {str(e)}")