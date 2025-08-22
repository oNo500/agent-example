"""
视频追踪验证演示
展示完整的验证流程和可视化功能
"""

import os
import sys
import json
import asyncio

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.video_processor import VideoProcessor
from utils.tracking_validator import TrackingValidator
from utils.visualization_helper import VisualizationHelper
from core.agent import VideoAgent
from core.llm_client import FrameInfo, DetectionRegion
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_frame_extraction_validation():
    """演示帧提取验证"""
    print("🔍 1. 帧提取验证演示")
    print("=" * 50)
    
    video_path = "./assets/test1.mp4"
    if not os.path.exists(video_path):
        print("❌ 测试视频不存在，请确保 ./assets/test1.mp4 存在")
        return
    
    # 初始化处理器和验证器
    processor = VideoProcessor()
    processor.enable_validation(True)
    
    # 提取帧（会自动触发验证）
    print("📹 正在提取关键帧...")
    frames = processor.extract_frames(
        video_path=video_path,
        sample_rate=15,
        max_frames=24,
        use_motion_detection=True
    )
    
    print(f"✅ 提取完成，共 {len(frames)} 帧")
    
    # 生成可视化
    if processor.visualizer:
        print("📊 正在生成关键帧分布图...")
        viz_path = processor.visualizer.visualize_keyframe_distribution(
            video_path, frames
        )
        if viz_path:
            print(f"📈 关键帧分布图已保存: {viz_path}")
    
    return frames


async def demo_detection_validation():
    """演示检测结果验证"""
    print("\n🎯 2. 检测结果验证演示")
    print("=" * 50)
    
    # 使用真实的视频帧提取
    import cv2
    from utils.video_processor import VideoProcessor
    
    # 检查是否有测试视频文件
    test_video_path = "./assets/test1.mp4"  # 使用现有的测试视频
    if not os.path.exists(test_video_path):
        print(f"❌ 测试视频文件不存在: {test_video_path}")
        print("💡 请将测试视频文件放在 assets/ 目录下，或修改 test_video_path 变量")
        return []
    
    print(f"📹 正在从真实视频提取关键帧: {test_video_path}")
    processor = VideoProcessor()
    frames = processor.extract_frames(
        video_path=test_video_path,
        sample_rate=30,  # 每30帧提取一帧
        max_frames=10    # 最多提取10帧用于演示
    )
    
    print(f"✅ 成功提取 {len(frames)} 个关键帧")
    
    # 使用真实的LLM检测
    from core.agent import VideoAgent
    
    print("🤖 正在调用LLM进行真实检测...")
    agent = VideoAgent()
    
    # 调用LLM分析视频内容
    target_description = "手机"  # 检测目标
    llm_detections = await agent.analyze_video_content(test_video_path, target_description)
    
    print(f"✅ LLM检测完成，共检测到 {len(llm_detections)} 个目标")
    
    # 显示LLM检测结果
    for detection in llm_detections:
        print(f"   帧{detection.frame_id}: {detection.object_type} at ({detection.bbox[0]},{detection.bbox[1]},{detection.bbox[2]},{detection.bbox[3]}) - {detection.confidence:.2f}")
    
    sample_detections = llm_detections
    
    # 获取真实视频信息
    cap = cv2.VideoCapture(test_video_path)
    video_info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
    }
    cap.release()
    
    print(f"📊 视频信息: {video_info['width']}x{video_info['height']}, {video_info['fps']:.1f}fps")
    
    # 初始化验证器
    validator = TrackingValidator()
    
    print("🤖 正在验证LLM检测结果...")
    validation_result = validator.validate_llm_detection(
        frames=frames,  # 使用真实的帧信息
        detections=sample_detections,
        video_info=video_info
    )
    
    print(f"📋 验证状态: {validation_result.status}")
    print(f"📝 验证信息: {validation_result.message}")
    
    # 生成可视化（需要实际帧文件）
    visualizer = VisualizationHelper()
    
    print("📊 正在生成追踪轨迹图...")
    trajectory_path = visualizer.visualize_tracking_trajectory(
        sample_detections, video_info
    )
    if trajectory_path:
        print(f"📈 追踪轨迹图已保存: {trajectory_path}")
    
    return sample_detections


def demo_interpolation_validation():
    """演示插值验证"""
    print("\n🔄 3. 追踪插值验证演示")  
    print("=" * 50)
    
    # 使用前面的检测结果
    sample_detections = [
        DetectionRegion(frame_id=15, object_type="手机", bbox=(1000, 500, 200, 400), confidence=0.98, description="手机设备"),
        DetectionRegion(frame_id=45, object_type="手机", bbox=(1200, 600, 220, 420), confidence=0.99, description="手机设备"),
        DetectionRegion(frame_id=75, object_type="手机", bbox=(1100, 550, 210, 410), confidence=0.97, description="手机设备"),
    ]
    
    # 创建插值函数（简化版）
    def simple_interpolation_func(frame_id, frame_regions_map, sorted_frame_ids):
        """简化的插值函数用于测试"""
        if frame_id in frame_regions_map:
            return frame_regions_map[frame_id]
        
        # 找最近的帧
        closest_frame_id = min(sorted_frame_ids, key=lambda x: abs(x - frame_id))
        return frame_regions_map[closest_frame_id]
    
    # 验证插值逻辑
    validator = TrackingValidator()
    test_frame_ids = [10, 20, 30, 40, 50, 60, 70, 80]  # 测试帧
    
    print("🔄 正在验证插值逻辑...")
    validation_result = validator.validate_tracking_interpolation(
        regions=sample_detections,
        test_frame_ids=test_frame_ids,
        interpolation_func=simple_interpolation_func,
        total_video_frames=360
    )
    
    print(f"📋 验证状态: {validation_result.status}")
    print(f"📝 验证信息: {validation_result.message}")
    
    if validation_result.details:
        stats = validation_result.details.get("interpolation_stats", {})
        print(f"📊 插值统计: 覆盖率 {stats.get('coverage_rate', 'N/A')}")


def demo_coverage_visualization():
    """演示覆盖率可视化"""
    print("\n📈 4. 覆盖率可视化演示")
    print("=" * 50)
    
    # 模拟数据
    total_frames = 360
    detected_frames = [15, 45, 75, 105, 135, 165, 195, 225, 255, 285, 315, 345]
    interpolated_frames = list(range(1, 361))  # 假设所有帧都有插值
    
    visualizer = VisualizationHelper()
    
    print("📊 正在生成覆盖率统计图...")
    coverage_path = visualizer.visualize_coverage_statistics(
        total_frames=total_frames,
        detected_frames=detected_frames,
        interpolated_frames=interpolated_frames
    )
    
    if coverage_path:
        print(f"📈 覆盖率统计图已保存: {coverage_path}")
        coverage_rate = len(set(detected_frames + interpolated_frames)) / total_frames
        print(f"📊 总覆盖率: {coverage_rate:.1%}")


def demo_validation_dashboard():
    """演示验证仪表板"""
    print("\n🎛️ 5. 验证仪表板演示")
    print("=" * 50)
    
    # 创建模拟验证结果
    from utils.tracking_validator import ValidationResult
    
    mock_results = [
        ValidationResult("frame_extraction", "pass", "帧提取验证通过"),
        ValidationResult("llm_detection", "pass", "LLM检测验证通过"), 
        ValidationResult("coordinate_conversion", "warning", "坐标转换存在轻微偏差"),
        ValidationResult("tracking_interpolation", "fail", "插值覆盖率过低"),
        ValidationResult("mosaic_application", "pass", "打码应用验证通过"),
    ]
    
    visualizer = VisualizationHelper()
    
    print("🎛️ 正在生成验证仪表板...")
    dashboard_path = visualizer.create_validation_dashboard(mock_results)
    
    if dashboard_path:
        print(f"📊 验证仪表板已保存: {dashboard_path}")
        
        # 统计信息
        total = len(mock_results)
        passed = sum(1 for r in mock_results if r.status == "pass")
        failed = sum(1 for r in mock_results if r.status == "fail")
        warnings = sum(1 for r in mock_results if r.status == "warning")
        
        print(f"📈 验证摘要: {passed}/{total} 通过, {failed} 失败, {warnings} 警告")


async def demo_end_to_end_validation():
    """演示端到端验证（需要真实视频处理）"""
    print("\n🎯 6. 端到端验证演示")
    print("=" * 50)
    
    video_path = "./assets/test1.mp4"
    if not os.path.exists(video_path):
        print("❌ 测试视频不存在，跳过端到端验证")
        return
    
    try:
        # 初始化代理（启用验证模式）
        agent = VideoAgent()
        
        print("🎬 正在执行完整的视频处理流程...")
        print("   这可能需要几分钟时间...")
        
        # 执行完整的追踪打码流程
        result = await agent.process_request(
            "为视频中的手机进行智能追踪打码处理",
            video_path
        )
        
        print("✅ 端到端处理完成")
        print("📋 处理结果:")
        print(result[:200] + "..." if len(result) > 200 else result)
        
    except Exception as e:
        print(f"❌ 端到端验证失败: {str(e)}")


async def main():
    """主演示函数"""
    print("🔍 视频追踪验证系统演示")
    print("=" * 60)
    print("本演示将展示完整的验证流程，包括：")
    print("• 帧提取验证")
    print("• 检测结果验证") 
    print("• 追踪插值验证")
    print("• 覆盖率可视化")
    print("• 验证仪表板")
    print("• 端到端验证")
    print()
    
    # 确保输出目录存在
    output_dirs = ["./output", "./output/validation", "./output/visualization"]
    for dir_path in output_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    try:
        # 执行各个演示
        demo_frame_extraction_validation()
        await demo_detection_validation()
        demo_interpolation_validation()
        demo_coverage_visualization()
        demo_validation_dashboard()
        
        # 端到端验证（可选，需要时间）
        print("\n❓ 是否执行端到端验证？（需要较长时间）")
        choice = input("输入 'y' 执行，其他键跳过: ").strip().lower()
        if choice == 'y':
            asyncio.run(demo_end_to_end_validation())
        else:
            print("⏭️ 跳过端到端验证")
        
        print("\n🎉 所有验证演示完成！")
        print("📁 验证结果和可视化图片已保存在 ./output/ 目录中")
        print("📊 请查看生成的图片和JSON报告以了解验证结果")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断演示")
    except Exception as e:
        print(f"\n❌ 演示过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())