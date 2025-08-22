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
    max_frames: int = 20
) -> str:
    """提取视频关键帧供LLM分析
    
    Args:
        video_path: 视频文件的完整路径
        sample_rate: 采样率，每N帧提取一帧
        max_frames: 最大提取帧数，防止视频过长
        
    Returns:
        JSON字符串，包含提取的帧信息
        格式: {"frames": [{"frame_id": 1, "timestamp": 0.5, "image_path": "/tmp/frame_1.jpg"}]}
    """
    try:
        frames = video_processor.extract_frames(video_path, sample_rate, max_frames)
        
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