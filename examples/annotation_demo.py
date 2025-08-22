#!/usr/bin/env python3
"""
视频标注演示脚本

此脚本展示了如何使用改进后的视频处理工具进行手机打码工作流：
1. 智能关键帧提取（带运动检测）
2. 创建可视化标注界面
3. 手动标注目标区域
4. 应用打码处理

使用方法:
python examples/annotation_demo.py
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
    """主演示流程"""
    print("🎬 视频标注演示")
    print("=" * 50)
    
    try:
        # 初始化代理
        print("📱 初始化视频处理代理...")
        agent = VideoAgent()
        
        # 视频文件路径
        video_path = "./assets/test1.mp4"
        target_description = "手机"
        
        if not os.path.exists(video_path):
            print(f"❌ 视频文件不存在: {video_path}")
            return
        
        print(f"📹 视频路径: {video_path}")
        print(f"🎯 目标描述: {target_description}")
        print()
        
        # 步骤1: 创建标注工作流
        print("🔧 创建标注工作流...")
        workflow_result = await agent.create_manual_annotation_workflow(
            video_path=video_path,
            target_description=target_description
        )
        
        workflow_data = json.loads(workflow_result)
        print("✅ 工作流创建成功!")
        print(f"   会话ID: {workflow_data['session_id']}")
        print(f"   提取帧数: {workflow_data['frames_extracted']}")
        print(f"   标注文件: {workflow_data['annotation_file']}")
        print()
        
        # 步骤2: 显示使用说明
        print("📋 使用说明:")
        instructions = workflow_data["instructions"]
        for step, instruction in instructions.items():
            print(f"   {step}: {instruction}")
        print()
        
        # 步骤3: 等待用户完成标注
        print("⏳ 请按照说明完成手动标注，然后按回车继续...")
        input()
        
        # 步骤4: 尝试加载标注数据
        print("📥 加载标注数据...")
        session_id = workflow_data['session_id']
        
        if agent.tool_registry.has_tool("load_annotation_data"):
            annotation_result = agent.tool_registry.execute_tool(
                "load_annotation_data",
                session_id=session_id
            )
            
            annotation_data = json.loads(annotation_result)
            
            if annotation_data.get("status") == "no_annotation":
                print("⚠️  未找到标注数据，请确保已完成标注并保存了regions.json文件")
                print("💡 或者使用快速标注功能进行测试：")
                print("   quick_annotate_phone_regions(frames_info, '1:100,100,200,150;2:120,110,180,140')")
                return
            
            regions = annotation_data.get("regions", [])
            print(f"✅ 成功加载 {len(regions)} 个标注区域")
            
            # 步骤5: 应用打码处理
            if regions:
                print("🎨 应用打码处理...")
                mosaic_result = agent.tool_registry.execute_tool(
                    "mosaic_video_regions",
                    video_path=video_path,
                    regions_data=json.dumps({"regions": regions}),
                    mosaic_strength=15
                )
                
                print("✅ 打码处理完成!")
                print(f"   输出文件: {mosaic_result}")
            else:
                print("⚠️  没有找到有效的标注区域")
        
    except VideoAgentException as e:
        print(f"❌ 处理失败: {e}")
    except KeyboardInterrupt:
        print("\n👋 用户取消操作")
    except Exception as e:
        print(f"💥 未预期的错误: {e}")


def demo_quick_annotation():
    """演示快速标注功能"""
    print("\n🚀 快速标注演示")
    print("=" * 30)
    
    # 模拟帧信息
    frames_info = json.dumps({
        "frames": [
            {"frame_id": 1, "timestamp": 1.0, "image_path": "./temp/frames/frame_1.jpg"},
            {"frame_id": 2, "timestamp": 2.0, "image_path": "./temp/frames/frame_2.jpg"}
        ]
    })
    
    # 手动区域信息（示例）
    manual_regions = "1:100,100,200,150;2:120,110,180,140"
    
    try:
        agent = VideoAgent()
        if agent.tool_registry.has_tool("quick_annotate_phone_regions"):
            result = agent.tool_registry.execute_tool(
                "quick_annotate_phone_regions",
                frames_info=frames_info,
                manual_regions=manual_regions
            )
            
            print("✅ 快速标注结果:")
            print(json.dumps(json.loads(result), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 快速标注失败: {e}")


if __name__ == "__main__":
    print("选择演示模式:")
    print("1. 完整标注工作流")
    print("2. 快速标注演示")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "2":
        demo_quick_annotation()
    else:
        asyncio.run(main())