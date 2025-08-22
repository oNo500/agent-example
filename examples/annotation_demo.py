#!/usr/bin/env python3
"""
智能追踪视频标注演示脚本

此脚本展示了如何使用改进后的LLM智能追踪视频处理工具进行打码工作流：
1. 智能关键帧提取（多帧运动检测）
2. 创建可视化标注界面
3. 手动标注种子区域（仅需标注一帧）
4. LLM多帧分析追踪目标运动轨迹
5. 智能打码处理（适应目标位置变化）

技术优势：
- 只需手动标注1帧，LLM自动追踪15帧
- 真正的智能追踪，适应目标移动、旋转、缩放
- 结合手动标注精确度和LLM追踪能力

使用方法:
uv run python examples/annotation_demo.py
"""

import asyncio
import json
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)  # 确保工作目录正确

from core.agent import VideoAgent
from core.exceptions import VideoAgentException


async def main():
    """智能追踪标注流程演示"""
    print("🎬 LLM智能追踪视频标注演示")
    print("=" * 50)
    
    try:
        # 初始化智能追踪代理
        print("🤖 初始化LLM智能追踪代理...")
        agent = VideoAgent()
        
        # 视频文件路径
        video_path = "./assets/test1.mp4"
        target_description = "手机"
        
        if not os.path.exists(video_path):
            print(f"❌ 视频文件不存在: {video_path}")
            print("💡 请将测试视频放置在 assets/test1.mp4")
            return
        
        print(f"📹 视频路径: {video_path}")
        print(f"🎯 目标描述: {target_description}")
        print("🔧 追踪模式: LLM多帧分析 (15帧)")
        print()
        
        # 使用智能追踪处理流程
        print("🚀 启动智能追踪处理流程...")
        print("   1️⃣ 提取关键帧（运动检测优化）")
        print("   2️⃣ 创建标注界面（种子标注）") 
        print("   3️⃣ LLM分析多帧追踪轨迹")
        print("   4️⃣ 智能打码处理")
        print()
        
        result = await agent.process_request(
            user_input=f"为视频中的{target_description}进行智能追踪打码处理",
            video_path=video_path
        )
        
        print(result)
        
        # 如果是工作流创建消息，说明需要手动种子标注
        if "工作流已创建" in result:
            print()
            print("🌱 种子标注阶段 - 请在浏览器中完成标注...")
            print("📋 操作指引:")
            print("   • 在浏览器中只需标注一张图片上的目标")
            print("   • 点击'保存标注数据'下载regions.json") 
            print("   • 重新运行此脚本，LLM将智能追踪到整个视频")
            print()
            print("💡 技术说明: 您的标注将作为'种子'，LLM会分析其他帧中目标的位置变化")
            return
        
    except VideoAgentException as e:
        print(f"❌ 处理失败: {e}")
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"💥 未预期的错误: {e}")


def demo_tracking_analysis():
    """演示LLM追踪分析功能"""
    print("\n🔍 LLM智能追踪分析演示")
    print("=" * 40)
    
    print("🎯 模拟种子标注数据:")
    # 模拟用户标注的种子帧信息
    seed_annotation = {
        "frame_id": 1,
        "object_type": "phone", 
        "bbox": [100, 100, 200, 150],
        "confidence": 1.0,
        "description": "手机区域 - 手动标注"
    }
    print(f"   帧ID: {seed_annotation['frame_id']}")
    print(f"   位置: ({seed_annotation['bbox'][0]}, {seed_annotation['bbox'][1]})")
    print(f"   大小: {seed_annotation['bbox'][2]}x{seed_annotation['bbox'][3]}")
    print()
    
    print("🤖 LLM追踪分析过程:")
    print("   1️⃣ 提取视频关键帧 (运动检测优化)")
    print("   2️⃣ 将种子标注作为参考点")  
    print("   3️⃣ LLM分析目标在其他帧中的位置变化")
    print("   4️⃣ 生成完整追踪轨迹数据")
    print("   5️⃣ 应用智能打码 (适应位置变化)")
    print()
    
    print("💡 技术优势:")
    print("   • 单帧标注 + 多帧追踪 = 最佳效率")
    print("   • 适应目标移动、旋转、缩放变化")  
    print("   • 结合人工精确度和AI追踪能力")
    print("   • 处理遮挡和重新出现场景")
    print()
    
    print("📊 预期结果:")
    print("   种子区域: 1个 (手动标注)")
    print("   追踪区域: ~15个 (LLM分析)")
    print("   总处理帧: 整个视频长度")
    print("   追踪精度: 高 (种子+LLM结合)")


if __name__ == "__main__":
    print("🎬 LLM智能追踪视频标注系统")
    print("=" * 50)
    print("选择演示模式:")
    print("1. 智能追踪标注工作流（推荐）")
    print("2. 技术原理分析演示")
    print()
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "2":
        demo_tracking_analysis()
    else:
        print()
        asyncio.run(main())