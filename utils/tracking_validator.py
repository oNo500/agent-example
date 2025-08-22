"""
视频追踪验证工具
提供完整的验证流程，确保打码追踪系统的准确性和可靠性
"""

import os
import json
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from core.llm_client import FrameInfo, DetectionRegion
from core.exceptions import VideoProcessingError
from utils.html_visualizer import HTMLVisualizer


@dataclass
class ValidationResult:
    """验证结果数据结构"""
    stage: str
    status: str  # "pass", "fail", "warning"
    message: str
    details: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class TrackingValidator:
    """视频追踪系统验证器"""
    
    def __init__(self, output_dir: str = "./output/validation"):
        """初始化验证器
        
        Args:
            output_dir: 验证结果输出目录
        """
        self.output_dir = output_dir
        self.validation_results: List[ValidationResult] = []
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化HTML可视化器
        self.html_visualizer = HTMLVisualizer()
        
    def validate_frame_extraction(
        self, 
        video_path: str, 
        extracted_frames: List[FrameInfo],
        expected_count: int = None
    ) -> ValidationResult:
        """验证帧提取结果
        
        Args:
            video_path: 视频路径
            extracted_frames: 提取的帧信息列表
            expected_count: 预期帧数
            
        Returns:
            验证结果
        """
        try:
            # 获取视频基本信息
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return ValidationResult(
                    stage="frame_extraction",
                    status="fail", 
                    message=f"无法打开视频文件: {video_path}"
                )
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            # 验证提取结果
            issues = []
            
            # 检查1: 帧数量
            if expected_count and len(extracted_frames) != expected_count:
                issues.append(f"帧数量不匹配: 期望{expected_count}, 实际{len(extracted_frames)}")
            
            # 检查2: 帧ID范围
            frame_ids = [frame.frame_id for frame in extracted_frames]
            min_id, max_id = min(frame_ids), max(frame_ids)
            if min_id < 1 or max_id > total_frames:
                issues.append(f"帧ID超出范围: {min_id}-{max_id}, 视频总帧数{total_frames}")
            
            # 检查3: 时间戳合理性
            timestamps = [frame.timestamp for frame in extracted_frames]
            if any(t < 0 or t > duration for t in timestamps):
                issues.append(f"时间戳超出范围: 0-{duration}s")
            
            # 检查4: 文件存在性
            missing_files = []
            for frame in extracted_frames:
                if not os.path.exists(frame.image_path):
                    missing_files.append(frame.image_path)
            if missing_files:
                issues.append(f"缺失帧文件: {len(missing_files)}个")
            
            # 检查5: 帧分布均匀性
            if len(frame_ids) > 1:
                intervals = [frame_ids[i+1] - frame_ids[i] for i in range(len(frame_ids)-1)]
                avg_interval = sum(intervals) / len(intervals)
                max_deviation = max(abs(interval - avg_interval) for interval in intervals)
                if max_deviation > avg_interval * 0.5:  # 允许50%的偏差
                    issues.append(f"帧分布不均匀: 平均间隔{avg_interval:.1f}, 最大偏差{max_deviation:.1f}")
            
            status = "fail" if issues else "pass"
            message = "; ".join(issues) if issues else "帧提取验证通过"
            
            details = {
                "video_info": {
                    "total_frames": total_frames,
                    "fps": fps,
                    "duration": duration
                },
                "extraction_info": {
                    "extracted_count": len(extracted_frames),
                    "frame_id_range": f"{min_id}-{max_id}",
                    "timestamp_range": f"{min(timestamps):.2f}-{max(timestamps):.2f}s"
                },
                "issues": issues
            }
            
            result = ValidationResult(
                stage="frame_extraction",
                status=status,
                message=message,
                details=details
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                stage="frame_extraction",
                status="fail",
                message=f"验证过程出错: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_llm_detection(
        self,
        frames: List[FrameInfo],
        detections: List[DetectionRegion],
        video_info: Dict = None
    ) -> ValidationResult:
        """验证LLM检测结果
        
        Args:
            frames: 帧信息列表
            detections: 检测结果列表
            video_info: 视频信息
            
        Returns:
            验证结果
        """
        try:
            issues = []
            
            # 检查1: 检测数量合理性
            frame_count = len(frames)
            detection_count = len(detections)
            
            if detection_count == 0:
                issues.append("没有检测到任何目标")
            elif detection_count > frame_count * 3:  # 允许每帧最多3个目标
                issues.append(f"检测目标过多: {detection_count} 个目标在 {frame_count} 帧中")
            
            # 检查2: 帧覆盖率
            detected_frames = set(det.frame_id for det in detections)
            frame_ids = set(frame.frame_id for frame in frames)
            coverage_rate = len(detected_frames) / len(frame_ids) if frame_ids else 0
            
            if coverage_rate < 0.5:  # 至少50%的帧应该有检测结果
                issues.append(f"帧覆盖率过低: {coverage_rate:.1%}")
            
            # 检查3: 坐标范围验证
            if video_info:
                video_width = video_info.get('width', 1920)
                video_height = video_info.get('height', 1080)
                
                coord_issues = []
                for det in detections:
                    x, y, w, h = det.bbox
                    if x < 0 or y < 0 or x + w > video_width or y + h > video_height:
                        coord_issues.append(f"帧{det.frame_id}: ({x},{y},{w},{h})")
                
                if coord_issues:
                    issues.append(f"坐标超出视频范围 ({video_width}x{video_height}): {len(coord_issues)}个")
            
            # 检查4: 置信度分布
            confidences = [det.confidence for det in detections]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                low_confidence_count = sum(1 for c in confidences if c < 0.5)
                
                if avg_confidence < 0.7:
                    issues.append(f"平均置信度过低: {avg_confidence:.2f}")
                if low_confidence_count > len(confidences) * 0.3:
                    issues.append(f"低置信度检测过多: {low_confidence_count}/{len(confidences)}")
            
            # 检查5: 区域大小合理性
            if video_info:
                video_area = video_info.get('width', 1920) * video_info.get('height', 1080)
                large_regions = 0
                tiny_regions = 0
                
                for det in detections:
                    w, h = det.bbox[2], det.bbox[3]
                    area = w * h
                    area_ratio = area / video_area
                    
                    if area_ratio > 0.25:  # 超过视频面积25%
                        large_regions += 1
                    elif area_ratio < 0.001:  # 小于视频面积0.1%
                        tiny_regions += 1
                
                if large_regions > 0:
                    issues.append(f"检测区域过大: {large_regions}个")
                if tiny_regions > len(detections) * 0.2:
                    issues.append(f"检测区域过小: {tiny_regions}个")
            
            status = "fail" if issues else "pass"
            message = "; ".join(issues) if issues else "LLM检测验证通过"
            
            details = {
                "detection_stats": {
                    "total_detections": detection_count,
                    "frames_with_detection": len(detected_frames),
                    "coverage_rate": f"{coverage_rate:.1%}",
                    "avg_confidence": f"{sum(confidences)/len(confidences):.2f}" if confidences else "N/A"
                },
                "frame_distribution": dict(zip(*np.unique([det.frame_id for det in detections], return_counts=True))),
                "issues": issues
            }
            
            result = ValidationResult(
                stage="llm_detection",
                status=status,
                message=message,
                details=details
            )
            
            # 生成HTML可视化页面
            try:
                print("🌐 正在生成HTML可视化页面...")
                html_path = self.html_visualizer.create_detection_visualization(
                    frames=frames,
                    detections=detections,
                    title=f"LLM检测结果验证 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # 将HTML路径添加到结果详情中
                details["html_visualization"] = html_path
                result.details = details
                
                print(f"📊 HTML可视化页面已生成，可在浏览器中打开查看: {html_path}")
                
            except Exception as e:
                print(f"⚠️ HTML可视化生成失败: {e}")
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                stage="llm_detection",
                status="fail",
                message=f"验证过程出错: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_coordinate_conversion(
        self,
        detections: List[DetectionRegion],
        video_info: Dict,
        frame_info: List[FrameInfo]
    ) -> ValidationResult:
        """验证坐标转换的一致性
        
        Args:
            detections: 检测结果（视频坐标系）
            video_info: 视频信息
            frame_info: 帧信息（用于获取原始图片尺寸）
            
        Returns:
            验证结果
        """
        try:
            issues = []
            
            video_width = video_info.get('width', 1920)
            video_height = video_info.get('height', 1080)
            
            # 检查样本帧的坐标一致性
            sample_frame = frame_info[0] if frame_info else None
            if sample_frame and os.path.exists(sample_frame.image_path):
                # 读取提取帧的实际尺寸
                img = cv2.imread(sample_frame.image_path)
                if img is not None:
                    img_height, img_width = img.shape[:2]
                    
                    # 计算缩放因子
                    scale_x = video_width / img_width
                    scale_y = video_height / img_height
                    
                    # 检查缩放因子的合理性
                    if abs(scale_x - scale_y) > 0.1:  # 宽高比应该基本一致
                        issues.append(f"缩放因子不一致: X={scale_x:.2f}, Y={scale_y:.2f}")
                    
                    # 验证坐标转换结果
                    coord_errors = []
                    for det in detections[:5]:  # 检查前5个检测结果
                        x, y, w, h = det.bbox
                        
                        # 反向转换到图片坐标系
                        img_x = x / scale_x
                        img_y = y / scale_y
                        img_w = w / scale_x  
                        img_h = h / scale_y
                        
                        # 检查是否在图片范围内
                        if (img_x < 0 or img_y < 0 or 
                            img_x + img_w > img_width or 
                            img_y + img_h > img_height):
                            coord_errors.append(f"帧{det.frame_id}")
                    
                    if coord_errors:
                        issues.append(f"坐标转换错误: {len(coord_errors)}个检测结果")
                    
                    details = {
                        "video_resolution": f"{video_width}x{video_height}",
                        "frame_resolution": f"{img_width}x{img_height}",
                        "scale_factors": f"X={scale_x:.2f}, Y={scale_y:.2f}",
                        "sample_conversions": [
                            {
                                "frame_id": det.frame_id,
                                "video_coords": det.bbox,
                                "image_coords": [
                                    int(det.bbox[0]/scale_x), 
                                    int(det.bbox[1]/scale_y),
                                    int(det.bbox[2]/scale_x), 
                                    int(det.bbox[3]/scale_y)
                                ]
                            } for det in detections[:3]
                        ]
                    }
            else:
                issues.append("无法读取样本帧进行坐标验证")
                details = {}
            
            status = "fail" if issues else "pass"
            message = "; ".join(issues) if issues else "坐标转换验证通过"
            
            result = ValidationResult(
                stage="coordinate_conversion", 
                status=status,
                message=message,
                details=details
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                stage="coordinate_conversion",
                status="fail", 
                message=f"验证过程出错: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def generate_validation_report(self, output_file: str = None) -> str:
        """生成验证报告
        
        Args:
            output_file: 输出文件路径，默认在output_dir中
            
        Returns:
            报告内容字符串
        """
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.output_dir, f"validation_report_{timestamp}.json")
        
        # 统计结果
        total_tests = len(self.validation_results)
        passed_tests = sum(1 for r in self.validation_results if r.status == "pass")
        failed_tests = sum(1 for r in self.validation_results if r.status == "fail") 
        warning_tests = sum(1 for r in self.validation_results if r.status == "warning")
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "warnings": warning_tests,
                "success_rate": f"{passed_tests/total_tests:.1%}" if total_tests > 0 else "0%",
                "generated_at": datetime.now().isoformat()
            },
            "results": [
                {
                    "stage": r.stage,
                    "status": r.status, 
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                } for r in self.validation_results
            ],
            "recommendations": self._generate_recommendations()
        }
        
        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 生成文本摘要
        summary = f"""
🔍 视频追踪验证报告
==================
测试总数: {total_tests}
✅ 通过: {passed_tests} 
❌ 失败: {failed_tests}
⚠️  警告: {warning_tests}
成功率: {passed_tests/total_tests:.1%}

详细报告已保存至: {output_file}
        """.strip()
        
        return summary
    
    def validate_tracking_interpolation(
        self,
        regions: List[DetectionRegion], 
        test_frame_ids: List[int],
        interpolation_func,
        total_video_frames: int
    ) -> ValidationResult:
        """验证追踪插值逻辑
        
        Args:
            regions: 关键帧检测区域
            test_frame_ids: 测试帧ID列表
            interpolation_func: 插值函数
            total_video_frames: 视频总帧数
            
        Returns:
            验证结果
        """
        try:
            issues = []
            
            # 按帧ID分组区域
            frame_regions_map = {}
            for region in regions:
                if region.frame_id not in frame_regions_map:
                    frame_regions_map[region.frame_id] = []
                frame_regions_map[region.frame_id].append(region)
            
            sorted_frame_ids = sorted(frame_regions_map.keys())
            
            # 检查1: 关键帧分布
            if len(sorted_frame_ids) < 2:
                issues.append("关键帧数量过少，无法进行有效插值")
            else:
                # 计算关键帧间隔
                intervals = [sorted_frame_ids[i+1] - sorted_frame_ids[i] 
                           for i in range(len(sorted_frame_ids)-1)]
                max_interval = max(intervals)
                avg_interval = sum(intervals) / len(intervals)
                
                if max_interval > total_video_frames * 0.3:  # 最大间隔不应超过30%视频长度
                    issues.append(f"关键帧间隔过大: 最大{max_interval}帧")
            
            # 检查2: 插值结果验证
            interpolation_results = []
            coverage_gaps = []
            
            for test_frame_id in test_frame_ids:
                try:
                    result = interpolation_func(test_frame_id, frame_regions_map, sorted_frame_ids)
                    interpolation_results.append({
                        "frame_id": test_frame_id,
                        "result_count": len(result),
                        "has_result": len(result) > 0
                    })
                    
                    if len(result) == 0:
                        coverage_gaps.append(test_frame_id)
                        
                except Exception as e:
                    issues.append(f"插值函数在帧{test_frame_id}出错: {str(e)}")
            
            # 检查3: 覆盖率
            coverage_rate = sum(1 for r in interpolation_results if r["has_result"]) / len(interpolation_results)
            if coverage_rate < 0.9:  # 至少90%的帧应该有插值结果
                issues.append(f"插值覆盖率过低: {coverage_rate:.1%}")
            
            # 检查4: 连续性
            if len(coverage_gaps) > 0:
                # 检查是否存在连续的覆盖空白
                gap_groups = []
                current_group = [coverage_gaps[0]]
                
                for i in range(1, len(coverage_gaps)):
                    if coverage_gaps[i] - coverage_gaps[i-1] == 1:
                        current_group.append(coverage_gaps[i])
                    else:
                        gap_groups.append(current_group)
                        current_group = [coverage_gaps[i]]
                gap_groups.append(current_group)
                
                large_gaps = [g for g in gap_groups if len(g) > 5]  # 超过5帧的连续空白
                if large_gaps:
                    issues.append(f"存在大的覆盖空白: {len(large_gaps)}处")
            
            status = "fail" if issues else "pass"
            message = "; ".join(issues) if issues else "追踪插值验证通过"
            
            details = {
                "keyframe_stats": {
                    "total_keyframes": len(sorted_frame_ids),
                    "keyframe_range": f"{min(sorted_frame_ids)}-{max(sorted_frame_ids)}",
                    "avg_interval": f"{sum(intervals)/len(intervals):.1f}" if intervals else "N/A"
                },
                "interpolation_stats": {
                    "test_frames": len(test_frame_ids),
                    "coverage_rate": f"{coverage_rate:.1%}", 
                    "coverage_gaps": len(coverage_gaps)
                },
                "sample_results": interpolation_results[:10],  # 前10个结果作为样本
                "issues": issues
            }
            
            result = ValidationResult(
                stage="tracking_interpolation",
                status=status,
                message=message,
                details=details
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                stage="tracking_interpolation",
                status="fail",
                message=f"验证过程出错: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_mosaic_application(
        self,
        sample_frame_path: str,
        regions: List[DetectionRegion],
        mosaic_func,
        mosaic_strength: int = 15
    ) -> ValidationResult:
        """验证打码应用效果
        
        Args:
            sample_frame_path: 样本帧文件路径
            regions: 需要打码的区域
            mosaic_func: 打码函数
            mosaic_strength: 打码强度
            
        Returns:
            验证结果
        """
        try:
            issues = []
            
            # 检查1: 样本帧存在性和可读性
            if not os.path.exists(sample_frame_path):
                return ValidationResult(
                    stage="mosaic_application",
                    status="fail",
                    message=f"样本帧不存在: {sample_frame_path}"
                )
            
            original_frame = cv2.imread(sample_frame_path)
            if original_frame is None:
                return ValidationResult(
                    stage="mosaic_application",
                    status="fail", 
                    message=f"无法读取样本帧: {sample_frame_path}"
                )
            
            frame_height, frame_width = original_frame.shape[:2]
            
            # 检查2: 区域坐标有效性
            valid_regions = []
            invalid_regions = []
            
            for region in regions:
                x, y, w, h = region.bbox
                if (x >= 0 and y >= 0 and 
                    x + w <= frame_width and 
                    y + h <= frame_height and
                    w > 0 and h > 0):
                    valid_regions.append(region)
                else:
                    invalid_regions.append(region)
            
            if invalid_regions:
                issues.append(f"无效区域坐标: {len(invalid_regions)}个")
            
            if not valid_regions:
                return ValidationResult(
                    stage="mosaic_application",
                    status="fail",
                    message="没有有效的打码区域"
                )
            
            # 检查3: 应用打码效果
            try:
                processed_frame = original_frame.copy()
                for region in valid_regions:
                    processed_frame = mosaic_func(processed_frame, region.bbox, mosaic_strength)
                
                # 验证打码效果
                mosaic_applied = False
                for region in valid_regions:
                    x, y, w, h = region.bbox
                    
                    # 提取原始和处理后的区域
                    original_roi = original_frame[y:y+h, x:x+w]
                    processed_roi = processed_frame[y:y+h, x:x+w]
                    
                    # 计算差异
                    diff = cv2.absdiff(original_roi, processed_roi)
                    diff_score = np.mean(diff)
                    
                    if diff_score > 1.0:  # 有明显差异说明打码生效
                        mosaic_applied = True
                        break
                
                if not mosaic_applied:
                    issues.append("打码效果不明显，可能未正确应用")
                
                # 保存验证结果图片
                output_path = os.path.join(self.output_dir, "mosaic_validation_sample.jpg")
                
                # 绘制检测框和打码区域
                visualization = processed_frame.copy()
                for i, region in enumerate(valid_regions):
                    x, y, w, h = region.bbox
                    cv2.rectangle(visualization, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(visualization, f"Region {i+1}", (x, y-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                cv2.imwrite(output_path, visualization)
                
            except Exception as e:
                issues.append(f"打码应用失败: {str(e)}")
            
            status = "fail" if issues else "pass"
            message = "; ".join(issues) if issues else "打码应用验证通过"
            
            details = {
                "frame_info": {
                    "path": sample_frame_path,
                    "resolution": f"{frame_width}x{frame_height}"
                },
                "regions_info": {
                    "total_regions": len(regions),
                    "valid_regions": len(valid_regions), 
                    "invalid_regions": len(invalid_regions)
                },
                "mosaic_settings": {
                    "strength": mosaic_strength,
                    "applied": mosaic_applied if 'mosaic_applied' in locals() else False
                },
                "output_sample": output_path if 'output_path' in locals() else None,
                "issues": issues
            }
            
            result = ValidationResult(
                stage="mosaic_application",
                status=status,
                message=message, 
                details=details
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                stage="mosaic_application",
                status="fail",
                message=f"验证过程出错: {str(e)}"
            )
            self.validation_results.append(result)
            return result
    
    def validate_end_to_end_coverage(
        self,
        video_path: str,
        output_video_path: str, 
        sample_frames: List[int] = None
    ) -> ValidationResult:
        """验证端到端的帧覆盖情况
        
        Args:
            video_path: 原始视频路径
            output_video_path: 处理后视频路径
            sample_frames: 抽样检查的帧号列表，默认随机选择
            
        Returns:
            验证结果
        """
        try:
            issues = []
            
            # 打开原始和处理后的视频
            original_cap = cv2.VideoCapture(video_path)
            processed_cap = cv2.VideoCapture(output_video_path)
            
            if not original_cap.isOpened():
                return ValidationResult(
                    stage="end_to_end_coverage",
                    status="fail",
                    message=f"无法打开原始视频: {video_path}"
                )
            
            if not processed_cap.isOpened():
                return ValidationResult(
                    stage="end_to_end_coverage", 
                    status="fail",
                    message=f"无法打开处理后视频: {output_video_path}"
                )
            
            # 获取视频信息
            total_frames = int(original_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            processed_frames = int(processed_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames != processed_frames:
                issues.append(f"帧数不匹配: 原始{total_frames}, 处理后{processed_frames}")
            
            # 选择抽样帧
            if sample_frames is None:
                # 随机选择20帧进行检查
                sample_count = min(20, total_frames)
                sample_frames = sorted(np.random.choice(total_frames, sample_count, replace=False))
            
            # 逐帧比较
            frames_with_changes = 0
            frames_without_changes = 0
            comparison_results = []
            
            for frame_idx in sample_frames:
                # 定位到指定帧
                original_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                processed_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                
                ret1, orig_frame = original_cap.read()
                ret2, proc_frame = processed_cap.read()
                
                if not (ret1 and ret2):
                    continue
                
                # 计算帧差异
                diff = cv2.absdiff(orig_frame, proc_frame)
                diff_score = np.mean(diff)
                
                has_changes = diff_score > 1.0
                if has_changes:
                    frames_with_changes += 1
                else:
                    frames_without_changes += 1
                
                comparison_results.append({
                    "frame_id": frame_idx + 1,
                    "diff_score": float(diff_score),
                    "has_changes": has_changes
                })
            
            original_cap.release()
            processed_cap.release()
            
            # 分析结果
            total_sampled = len(comparison_results)
            change_rate = frames_with_changes / total_sampled if total_sampled > 0 else 0
            
            # 根据变化率判断是否合理
            if change_rate < 0.1:  # 小于10%的帧有变化
                issues.append(f"打码覆盖率过低: 只有{change_rate:.1%}的帧有变化")
            elif change_rate > 0.8:  # 超过80%的帧有变化
                issues.append(f"打码覆盖率过高: {change_rate:.1%}的帧有变化，可能存在误检")
            
            status = "fail" if issues else "pass"
            message = "; ".join(issues) if issues else "端到端覆盖验证通过"
            
            details = {
                "video_comparison": {
                    "original_frames": total_frames,
                    "processed_frames": processed_frames,
                    "sampled_frames": total_sampled
                },
                "coverage_analysis": {
                    "frames_with_changes": frames_with_changes,
                    "frames_without_changes": frames_without_changes, 
                    "change_rate": f"{change_rate:.1%}"
                },
                "sample_results": comparison_results[:10],  # 前10个结果作为样本
                "issues": issues
            }
            
            result = ValidationResult(
                stage="end_to_end_coverage",
                status=status,
                message=message,
                details=details
            )
            
            self.validation_results.append(result)
            return result
            
        except Exception as e:
            result = ValidationResult(
                stage="end_to_end_coverage",
                status="fail", 
                message=f"验证过程出错: {str(e)}"
            )
            self.validation_results.append(result)
            return result

    def _generate_recommendations(self) -> List[str]:
        """根据验证结果生成修复建议"""
        recommendations = []
        
        failed_stages = [r.stage for r in self.validation_results if r.status == "fail"]
        
        if "frame_extraction" in failed_stages:
            recommendations.append("建议检查帧提取参数，确保采样率和帧数设置合理")
        
        if "llm_detection" in failed_stages:
            recommendations.append("建议优化LLM检测提示词，或调整检测置信度阈值")
            
        if "coordinate_conversion" in failed_stages:
            recommendations.append("建议检查坐标转换逻辑，确保缩放因子计算正确")
            
        if "tracking_interpolation" in failed_stages:
            recommendations.append("建议优化插值算法，或增加关键帧密度")
            
        if "mosaic_application" in failed_stages:
            recommendations.append("建议检查打码函数实现，确保坐标和强度参数正确")
            
        if "end_to_end_coverage" in failed_stages:
            recommendations.append("建议进行完整的端到端测试，检查整个流程的一致性")
        
        return recommendations