"""
可视化验证工具
提供追踪和打码结果的可视化验证功能
"""

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import List, Dict, Tuple, Optional
import json
from datetime import datetime

from core.llm_client import FrameInfo, DetectionRegion


class VisualizationHelper:
    """可视化验证助手"""
    
    def __init__(self, output_dir: str = "./output/visualization"):
        """初始化可视化助手
        
        Args:
            output_dir: 可视化结果输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 设置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def visualize_keyframe_distribution(
        self,
        video_path: str,
        extracted_frames: List[FrameInfo],
        save_path: str = None
    ) -> str:
        """可视化关键帧分布
        
        Args:
            video_path: 视频路径
            extracted_frames: 提取的关键帧
            save_path: 保存路径，默认自动生成
            
        Returns:
            生成的图片路径
        """
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"keyframe_distribution_{timestamp}.png")
        
        try:
            # 获取视频信息
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            # 提取帧信息
            frame_ids = [frame.frame_id for frame in extracted_frames]
            timestamps = [frame.timestamp for frame in extracted_frames]
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
            
            # 子图1: 帧ID分布
            ax1.scatter(frame_ids, [1] * len(frame_ids), alpha=0.7, s=50, c='blue')
            ax1.set_xlim(0, total_frames)
            ax1.set_ylim(0.5, 1.5)
            ax1.set_xlabel('帧ID')
            ax1.set_ylabel('关键帧')
            ax1.set_title(f'关键帧分布 - 总共{len(frame_ids)}帧 (视频总帧数: {total_frames})')
            ax1.grid(True, alpha=0.3)
            
            # 添加统计信息
            if len(frame_ids) > 1:
                intervals = [frame_ids[i+1] - frame_ids[i] for i in range(len(frame_ids)-1)]
                avg_interval = sum(intervals) / len(intervals)
                ax1.text(0.02, 0.98, f'平均间隔: {avg_interval:.1f}帧', 
                        transform=ax1.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # 子图2: 时间分布
            ax2.scatter(timestamps, [1] * len(timestamps), alpha=0.7, s=50, c='red')
            ax2.set_xlim(0, duration)
            ax2.set_ylim(0.5, 1.5)
            ax2.set_xlabel('时间 (秒)')
            ax2.set_ylabel('关键帧')
            ax2.set_title(f'时间分布 - 视频总时长: {duration:.2f}秒')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return save_path
            
        except Exception as e:
            print(f"关键帧分布可视化失败: {str(e)}")
            return None
    
    def visualize_detection_results(
        self,
        frames: List[FrameInfo],
        detections: List[DetectionRegion],
        max_frames: int = 6,
        save_path: str = None
    ) -> str:
        """可视化检测结果
        
        Args:
            frames: 帧信息列表
            detections: 检测结果列表
            max_frames: 最大显示帧数
            save_path: 保存路径，默认自动生成
            
        Returns:
            生成的图片路径
        """
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"detection_results_{timestamp}.png")
        
        try:
            # 按帧ID分组检测结果
            detections_by_frame = {}
            for det in detections:
                if det.frame_id not in detections_by_frame:
                    detections_by_frame[det.frame_id] = []
                detections_by_frame[det.frame_id].append(det)
            
            # 选择要显示的帧（有检测结果的前几帧）
            display_frames = []
            for frame in frames:
                if frame.frame_id in detections_by_frame:
                    display_frames.append(frame)
                if len(display_frames) >= max_frames:
                    break
            
            if not display_frames:
                print("没有找到有检测结果的帧")
                return None
            
            # 计算子图布局
            cols = min(3, len(display_frames))
            rows = (len(display_frames) + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3))
            if rows == 1 and cols == 1:
                axes = [axes]
            elif rows == 1 or cols == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()
            
            for i, frame in enumerate(display_frames):
                ax = axes[i] if len(display_frames) > 1 else axes[0]
                
                # 读取图片
                if not os.path.exists(frame.image_path):
                    ax.text(0.5, 0.5, '图片文件不存在', ha='center', va='center')
                    ax.set_title(f'帧 {frame.frame_id}')
                    continue
                
                img = cv2.imread(frame.image_path)
                if img is None:
                    ax.text(0.5, 0.5, '无法读取图片', ha='center', va='center')
                    ax.set_title(f'帧 {frame.frame_id}')
                    continue
                
                # 转换颜色空间
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                ax.imshow(img_rgb)
                
                # 绘制检测框
                frame_detections = detections_by_frame.get(frame.frame_id, [])
                for j, det in enumerate(frame_detections):
                    x, y, w, h = det.bbox
                    
                    # 坐标转换：从视频坐标系转到图片坐标系
                    img_height, img_width = img.shape[:2]
                    # 这里假设检测结果已经是图片坐标系，如果不是需要缩放
                    
                    rect = patches.Rectangle(
                        (x, y), w, h,
                        linewidth=2, 
                        edgecolor='red',
                        facecolor='none'
                    )
                    ax.add_patch(rect)
                    
                    # 添加标签
                    label = f"{det.object_type}\n{det.confidence:.2f}"
                    ax.text(x, y-10, label, fontsize=8, color='red', 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
                
                ax.set_title(f'帧 {frame.frame_id} - {len(frame_detections)}个检测')
                ax.axis('off')
            
            # 隐藏多余的子图
            for i in range(len(display_frames), len(axes)):
                axes[i].axis('off')
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return save_path
            
        except Exception as e:
            print(f"检测结果可视化失败: {str(e)}")
            return None
    
    def visualize_tracking_trajectory(
        self,
        detections: List[DetectionRegion],
        video_info: Dict,
        save_path: str = None
    ) -> str:
        """可视化追踪轨迹
        
        Args:
            detections: 检测结果列表
            video_info: 视频信息
            save_path: 保存路径，默认自动生成
            
        Returns:
            生成的图片路径
        """
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"tracking_trajectory_{timestamp}.png")
        
        try:
            video_width = video_info.get('width', 1920)
            video_height = video_info.get('height', 1080)
            
            # 按track_id分组（如果有的话）
            trajectories = {}
            for det in detections:
                track_id = getattr(det, 'track_id', 'default')
                if track_id not in trajectories:
                    trajectories[track_id] = []
                trajectories[track_id].append(det)
            
            # 按frame_id排序
            for track_id in trajectories:
                trajectories[track_id].sort(key=lambda x: x.frame_id)
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 子图1: 轨迹图（俯视图）
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown']
            for i, (track_id, trajectory) in enumerate(trajectories.items()):
                color = colors[i % len(colors)]
                
                # 提取中心点坐标
                centers_x = []
                centers_y = []
                for det in trajectory:
                    x, y, w, h = det.bbox
                    center_x = x + w // 2
                    center_y = y + h // 2
                    centers_x.append(center_x)
                    centers_y.append(center_y)
                
                # 绘制轨迹
                ax1.plot(centers_x, centers_y, color=color, marker='o', 
                        markersize=4, linewidth=2, alpha=0.7, 
                        label=f'Track {track_id}')
                
                # 标记起点和终点
                if centers_x:
                    ax1.plot(centers_x[0], centers_y[0], color=color, 
                            marker='s', markersize=8, label=f'起点 {track_id}')
                    ax1.plot(centers_x[-1], centers_y[-1], color=color, 
                            marker='^', markersize=8, label=f'终点 {track_id}')
            
            ax1.set_xlim(0, video_width)
            ax1.set_ylim(0, video_height)
            ax1.invert_yaxis()  # 翻转Y轴，匹配图像坐标系
            ax1.set_xlabel('X坐标')
            ax1.set_ylabel('Y坐标')
            ax1.set_title('目标追踪轨迹')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            
            # 子图2: 时间-位置图
            for i, (track_id, trajectory) in enumerate(trajectories.items()):
                color = colors[i % len(colors)]
                
                frame_ids = [det.frame_id for det in trajectory]
                centers_x = [det.bbox[0] + det.bbox[2]//2 for det in trajectory]
                centers_y = [det.bbox[1] + det.bbox[3]//2 for det in trajectory]
                
                ax2.plot(frame_ids, centers_x, color=color, marker='o', 
                        linewidth=2, alpha=0.7, label=f'X坐标 {track_id}')
                ax2.plot(frame_ids, centers_y, color=color, marker='s', 
                        linewidth=2, alpha=0.5, linestyle='--', label=f'Y坐标 {track_id}')
            
            ax2.set_xlabel('帧ID')
            ax2.set_ylabel('坐标值')
            ax2.set_title('位置随时间变化')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return save_path
            
        except Exception as e:
            print(f"追踪轨迹可视化失败: {str(e)}")
            return None
    
    def visualize_coverage_statistics(
        self,
        total_frames: int,
        detected_frames: List[int],
        interpolated_frames: List[int] = None,
        save_path: str = None
    ) -> str:
        """可视化覆盖率统计
        
        Args:
            total_frames: 视频总帧数
            detected_frames: 有检测结果的帧列表
            interpolated_frames: 插值帧列表（可选）
            save_path: 保存路径，默认自动生成
            
        Returns:
            生成的图片路径
        """
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"coverage_statistics_{timestamp}.png")
        
        try:
            # 创建覆盖率数组
            coverage_array = np.zeros(total_frames)
            
            # 标记检测帧
            for frame_id in detected_frames:
                if 1 <= frame_id <= total_frames:
                    coverage_array[frame_id - 1] = 1  # 检测帧标记为1
            
            # 标记插值帧
            if interpolated_frames:
                for frame_id in interpolated_frames:
                    if 1 <= frame_id <= total_frames and coverage_array[frame_id - 1] == 0:
                        coverage_array[frame_id - 1] = 0.5  # 插值帧标记为0.5
            
            # 创建图表
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 10))
            
            # 子图1: 覆盖率时序图
            frame_range = np.arange(1, total_frames + 1)
            ax1.fill_between(frame_range, coverage_array, alpha=0.6, color='blue', label='覆盖情况')
            ax1.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='检测帧')
            ax1.axhline(y=0.5, color='orange', linestyle='--', alpha=0.7, label='插值帧')
            ax1.set_xlim(1, total_frames)
            ax1.set_ylim(0, 1.1)
            ax1.set_xlabel('帧ID')
            ax1.set_ylabel('覆盖状态')
            ax1.set_title('帧覆盖情况时序图')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 子图2: 覆盖率统计饼图
            detected_count = len(detected_frames)
            interpolated_count = len(interpolated_frames) if interpolated_frames else 0
            uncovered_count = total_frames - detected_count - interpolated_count
            
            labels = ['检测帧', '插值帧', '未覆盖']
            sizes = [detected_count, interpolated_count, uncovered_count]
            colors = ['lightcoral', 'lightskyblue', 'lightgray']
            
            # 过滤掉为0的部分
            filtered_data = [(label, size, color) for label, size, color in zip(labels, sizes, colors) if size > 0]
            if filtered_data:
                labels, sizes, colors = zip(*filtered_data)
                ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax2.set_title('帧覆盖率分布')
            
            # 子图3: 覆盖间隔统计
            covered_frames = sorted(detected_frames + (interpolated_frames or []))
            if len(covered_frames) > 1:
                intervals = [covered_frames[i+1] - covered_frames[i] for i in range(len(covered_frames)-1)]
                ax3.hist(intervals, bins=min(20, max(intervals)), alpha=0.7, color='green')
                ax3.set_xlabel('帧间隔')
                ax3.set_ylabel('频次')
                ax3.set_title(f'覆盖间隔分布 (平均: {sum(intervals)/len(intervals):.1f}帧)')
                ax3.grid(True, alpha=0.3)
            else:
                ax3.text(0.5, 0.5, '覆盖帧数不足，无法生成间隔统计', 
                        ha='center', va='center', transform=ax3.transAxes)
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return save_path
            
        except Exception as e:
            print(f"覆盖率统计可视化失败: {str(e)}")
            return None
    
    def create_validation_dashboard(
        self,
        validation_results: List,
        save_path: str = None
    ) -> str:
        """创建验证仪表板
        
        Args:
            validation_results: 验证结果列表
            save_path: 保存路径，默认自动生成
            
        Returns:
            生成的图片路径
        """
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_dir, f"validation_dashboard_{timestamp}.png")
        
        try:
            # 统计结果
            total_tests = len(validation_results)
            passed = sum(1 for r in validation_results if r.status == "pass")
            failed = sum(1 for r in validation_results if r.status == "fail")
            warnings = sum(1 for r in validation_results if r.status == "warning")
            
            # 创建图表
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            
            # 子图1: 总体测试结果饼图
            if total_tests > 0:
                labels = []
                sizes = []
                colors = []
                
                if passed > 0:
                    labels.append(f'通过 ({passed})')
                    sizes.append(passed)
                    colors.append('lightgreen')
                
                if failed > 0:
                    labels.append(f'失败 ({failed})')
                    sizes.append(failed)
                    colors.append('lightcoral')
                
                if warnings > 0:
                    labels.append(f'警告 ({warnings})')
                    sizes.append(warnings)
                    colors.append('yellow')
                
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax1.set_title(f'验证结果总览 (总计: {total_tests})')
            else:
                ax1.text(0.5, 0.5, '无验证结果', ha='center', va='center')
                ax1.set_title('验证结果总览')
            
            # 子图2: 各阶段测试结果
            stages = [r.stage for r in validation_results]
            statuses = [r.status for r in validation_results]
            
            stage_names = list(set(stages))
            stage_results = {stage: {'pass': 0, 'fail': 0, 'warning': 0} for stage in stage_names}
            
            for stage, status in zip(stages, statuses):
                stage_results[stage][status] += 1
            
            # 创建堆叠柱状图
            if stage_names:
                passes = [stage_results[stage]['pass'] for stage in stage_names]
                fails = [stage_results[stage]['fail'] for stage in stage_names]
                warns = [stage_results[stage]['warning'] for stage in stage_names]
                
                x = np.arange(len(stage_names))
                width = 0.6
                
                ax2.bar(x, passes, width, label='通过', color='lightgreen')
                ax2.bar(x, fails, width, bottom=passes, label='失败', color='lightcoral')
                ax2.bar(x, warns, width, bottom=np.array(passes)+np.array(fails), 
                       label='警告', color='yellow')
                
                ax2.set_xlabel('验证阶段')
                ax2.set_ylabel('测试数量')
                ax2.set_title('各阶段验证结果')
                ax2.set_xticks(x)
                ax2.set_xticklabels(stage_names, rotation=45, ha='right')
                ax2.legend()
            
            # 子图3: 成功率趋势（如果有时间信息）
            success_rate = passed / total_tests * 100 if total_tests > 0 else 0
            ax3.bar(['当前验证'], [success_rate], color='lightblue', alpha=0.7)
            ax3.set_ylim(0, 100)
            ax3.set_ylabel('成功率 (%)')
            ax3.set_title(f'验证成功率: {success_rate:.1f}%')
            
            # 添加成功率文本
            ax3.text(0, success_rate + 2, f'{success_rate:.1f}%', 
                    ha='center', va='bottom', fontweight='bold')
            
            # 子图4: 问题分类统计
            all_issues = []
            for r in validation_results:
                if r.details and 'issues' in r.details:
                    all_issues.extend(r.details['issues'])
            
            if all_issues:
                # 简单的问题分类（基于关键词）
                categories = {
                    '坐标相关': 0,
                    '帧数相关': 0,
                    '检测相关': 0,
                    '其他': 0
                }
                
                for issue in all_issues:
                    issue_lower = issue.lower()
                    if '坐标' in issue_lower or '位置' in issue_lower:
                        categories['坐标相关'] += 1
                    elif '帧' in issue_lower or 'frame' in issue_lower:
                        categories['帧数相关'] += 1
                    elif '检测' in issue_lower or 'detection' in issue_lower:
                        categories['检测相关'] += 1
                    else:
                        categories['其他'] += 1
                
                # 过滤掉为0的类别
                filtered_categories = {k: v for k, v in categories.items() if v > 0}
                
                if filtered_categories:
                    ax4.bar(filtered_categories.keys(), filtered_categories.values(), 
                           color='lightpink', alpha=0.7)
                    ax4.set_ylabel('问题数量')
                    ax4.set_title('问题分类统计')
                    ax4.tick_params(axis='x', rotation=45)
                else:
                    ax4.text(0.5, 0.5, '无问题记录', ha='center', va='center')
                    ax4.set_title('问题分类统计')
            else:
                ax4.text(0.5, 0.5, '无问题记录', ha='center', va='center')
                ax4.set_title('问题分类统计')
            
            plt.tight_layout()
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            return save_path
            
        except Exception as e:
            print(f"验证仪表板创建失败: {str(e)}")
            return None