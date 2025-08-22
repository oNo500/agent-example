import cv2
import os
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import asdict
from core.llm_client import FrameInfo, DetectionRegion
from core.exceptions import VideoProcessingError
from config import Config

class VideoProcessor:
    """视频处理核心功能"""
    
    def __init__(self):
        self.config = Config()
    
    def extract_frames(
        self, 
        video_path: str, 
        sample_rate: int = None, 
        max_frames: int = None,
        use_motion_detection: bool = True
    ) -> List[FrameInfo]:
        """提取视频关键帧
        
        Args:
            video_path: 视频文件路径
            sample_rate: 采样率，每N帧提取一帧
            max_frames: 最大提取帧数
            use_motion_detection: 是否使用运动检测优化帧选择
            
        Returns:
            帧信息列表
        """
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        sample_rate = sample_rate or self.config.DEFAULT_SAMPLE_RATE
        max_frames = max_frames or self.config.MAX_FRAMES_PER_REQUEST
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise VideoProcessingError(f"Cannot open video file: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            frames = []
            frame_count = 0
            extracted_count = 0
            
            # 确保临时目录存在
            temp_dir = os.path.join(self.config.TEMP_DIR, "frames")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 运动检测相关变量
            prev_frame = None
            motion_threshold = 1000  # 运动检测阈值
            
            while cap.isOpened() and extracted_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 智能帧提取：结合采样率和运动检测
                should_extract = False
                
                # 基础采样率检查
                if frame_count % sample_rate == 0:
                    should_extract = True
                    
                    # 如果启用运动检测，进行额外验证
                    if use_motion_detection and prev_frame is not None:
                        motion_score = self._calculate_motion_score(prev_frame, frame)
                        
                        # 如果运动量太小，可能跳过这一帧（除非是第一帧）
                        if motion_score < motion_threshold and extracted_count > 0:
                            should_extract = False
                
                if should_extract:
                    timestamp = frame_count / fps
                    frame_filename = f"frame_{extracted_count + 1}.jpg"
                    frame_path = os.path.join(temp_dir, frame_filename)
                    
                    # 保存帧图片
                    cv2.imwrite(frame_path, frame)
                    
                    frame_info = FrameInfo(
                        frame_id=extracted_count + 1,
                        timestamp=timestamp,
                        image_path=frame_path,
                        width=width,
                        height=height
                    )
                    frames.append(frame_info)
                    extracted_count += 1
                    
                    # 更新前一帧用于运动检测
                    if use_motion_detection:
                        prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                frame_count += 1
            
            cap.release()
            return frames
            
        except Exception as e:
            raise VideoProcessingError(f"Frame extraction failed: {str(e)}") from e
    
    def apply_mosaic_regions(
        self, 
        video_path: str, 
        regions: List[DetectionRegion], 
        mosaic_strength: int = 15,
        output_path: str = None
    ) -> str:
        """对指定区域应用打码效果
        
        Args:
            video_path: 源视频文件路径
            regions: 检测区域列表
            mosaic_strength: 打码强度(5-50)
            output_path: 输出文件路径
            
        Returns:
            处理后的视频文件路径
        """
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        if not regions:
            raise VideoProcessingError("No regions provided for mosaic processing")
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise VideoProcessingError(f"Cannot open video file: {video_path}")
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 准备输出路径
            if not output_path:
                output_dir = self.config.OUTPUT_DIR
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(video_path))[0]
                output_path = os.path.join(output_dir, f"{base_name}_mosaic.mp4")
            
            # 设置视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # 按帧处理视频
            frame_regions_map = self._group_regions_by_frame(regions)
            
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 如果当前帧有需要打码的区域
                frame_id = self._frame_count_to_frame_id(frame_count, regions)
                if frame_id in frame_regions_map:
                    frame = self._apply_mosaic_to_frame(
                        frame, frame_regions_map[frame_id], mosaic_strength
                    )
                
                out.write(frame)
                frame_count += 1
            
            cap.release()
            out.release()
            
            return output_path
            
        except Exception as e:
            raise VideoProcessingError(f"Mosaic application failed: {str(e)}") from e
    
    def _group_regions_by_frame(self, regions: List[DetectionRegion]) -> Dict[int, List[DetectionRegion]]:
        """按帧ID分组区域"""
        frame_regions = {}
        for region in regions:
            frame_id = region.frame_id
            if frame_id not in frame_regions:
                frame_regions[frame_id] = []
            frame_regions[frame_id].append(region)
        return frame_regions
    
    def _frame_count_to_frame_id(self, frame_count: int, regions: List[DetectionRegion]) -> int:
        """将帧计数转换为帧ID"""
        # 简单实现：假设frame_id就是帧序号
        # 在实际应用中可能需要更复杂的映射逻辑
        return frame_count + 1
    
    def _apply_mosaic_to_frame(
        self, 
        frame: np.ndarray, 
        regions: List[DetectionRegion], 
        strength: int
    ) -> np.ndarray:
        """对单帧应用马赛克效果"""
        for region in regions:
            x, y, w, h = region.bbox
            
            # 确保坐标在有效范围内
            x = max(0, min(x, frame.shape[1] - 1))
            y = max(0, min(y, frame.shape[0] - 1))
            w = max(1, min(w, frame.shape[1] - x))
            h = max(1, min(h, frame.shape[0] - y))
            
            # 提取区域
            roi = frame[y:y+h, x:x+w]
            
            # 应用马赛克效果
            mosaic_size = max(1, min(strength, min(w, h) // 2))
            small = cv2.resize(roi, (mosaic_size, mosaic_size), interpolation=cv2.INTER_LINEAR)
            mosaic = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
            
            # 替换原区域
            frame[y:y+h, x:x+w] = mosaic
        
        return frame
    
    def get_video_info(self, video_path: str) -> Dict:
        """获取视频基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频信息字典
        """
        if not os.path.exists(video_path):
            raise VideoProcessingError(f"Video file not found: {video_path}")
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise VideoProcessingError(f"Cannot open video file: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # 获取文件大小
            file_size = os.path.getsize(video_path)
            
            return {
                "path": video_path,
                "duration": duration,
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "resolution": f"{width}x{height}",
                "file_size": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            raise VideoProcessingError(f"Failed to get video info: {str(e)}") from e
    
    def _calculate_motion_score(self, prev_frame: np.ndarray, current_frame: np.ndarray) -> float:
        """计算两帧之间的运动得分
        
        Args:
            prev_frame: 前一帧（灰度图）
            current_frame: 当前帧（彩色图）
            
        Returns:
            运动得分，数值越大表示运动越明显
        """
        try:
            # 转换当前帧为灰度图
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            # 计算帧差
            frame_diff = cv2.absdiff(prev_frame, current_gray)
            
            # 应用阈值化
            _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
            
            # 计算运动区域的像素数量作为运动得分
            motion_pixels = cv2.countNonZero(thresh)
            
            return float(motion_pixels)
            
        except Exception as e:
            # 如果运动检测失败，返回高分以确保帧被提取
            return 10000.0