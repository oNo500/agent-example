#!/usr/bin/env python3
"""
Video Agent Demo - 演示程序

这个演示程序展示了如何使用Video Agent进行视频处理
"""

import asyncio
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import VideoAgent
from tools.video_tools import *  # 注册视频处理工具

async def demo_basic_usage():
    """演示基本用法"""
    print("🎬 Video Agent 基本用法演示")
    print("="*50)
    
    try:
        # 初始化Agent
        print("1. 初始化Video Agent...")
        agent = VideoAgent()
        print(f"   ✅ 初始化成功，可用工具: {agent.list_tools()}")
        
        # 展示工具信息
        print("\n2. 可用工具详情:")
        for tool_name in agent.list_tools():
            tool_info = agent.get_tool_info(tool_name)
            print(f"   • {tool_name}")
            print(f"     描述: {tool_info['description']}")
            print(f"     参数: {list(tool_info['parameters'].keys())}")
        
        # 模拟处理请求（需要真实视频文件）
        print("\n3. 处理流程演示:")
        sample_request = "对视频中的手机进行打码"
        print(f"   请求: {sample_request}")
        print("   注意: 需要提供真实的视频文件路径才能执行")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")

async def demo_tool_registration():
    """演示工具注册机制"""
    print("\n🔧 工具注册机制演示")
    print("="*50)
    
    try:
        agent = VideoAgent()
        
        # 注册自定义工具
        @agent.register_tool
        def custom_video_info(video_path: str, include_metadata: bool = False) -> str:
            """自定义视频信息获取工具
            
            Args:
                video_path: 视频文件路径
                include_metadata: 是否包含元数据
                
            Returns:
                自定义格式的视频信息
            """
            return f"自定义信息: {video_path} (元数据: {include_metadata})"
        
        print("1. 注册自定义工具:")
        print("   ✅ custom_video_info 工具已注册")
        
        print("\n2. 更新后的工具列表:")
        for tool_name in agent.list_tools():
            if tool_name == "custom_video_info":
                print(f"   • {tool_name} (自定义)")
            else:
                print(f"   • {tool_name}")
        
        print("\n3. 测试自定义工具:")
        result = agent.tool_registry.execute_tool(
            "custom_video_info", 
            video_path="test.mp4", 
            include_metadata=True
        )
        print(f"   结果: {result}")
        
    except Exception as e:
        print(f"❌ 工具注册演示失败: {e}")

async def demo_error_handling():
    """演示错误处理"""
    print("\n⚠️  错误处理演示")
    print("="*50)
    
    try:
        agent = VideoAgent()
        
        print("1. 测试不存在的视频文件:")
        try:
            result = agent.tool_registry.execute_tool(
                "get_video_info", 
                video_path="nonexistent.mp4"
            )
        except Exception as e:
            print(f"   ✅ 正确捕获错误: {type(e).__name__}: {e}")
        
        print("\n2. 测试不存在的工具:")
        try:
            result = agent.tool_registry.execute_tool("nonexistent_tool")
        except Exception as e:
            print(f"   ✅ 正确捕获错误: {type(e).__name__}: {e}")
        
        print("\n3. 测试工具参数错误:")
        try:
            result = agent.tool_registry.execute_tool(
                "extract_video_frames"
                # 缺少必需参数
            )
        except Exception as e:
            print(f"   ✅ 正确捕获错误: {type(e).__name__}: {e}")
            
    except Exception as e:
        print(f"❌ 错误处理演示失败: {e}")

def demo_configuration():
    """演示配置管理"""
    print("\n⚙️  配置管理演示")
    print("="*50)
    
    try:
        from config import Config
        
        config = Config()
        
        print("1. 当前配置:")
        print(f"   • Gemini模型: {config.GEMINI_MODEL}")
        print(f"   • 最大视频时长: {config.MAX_VIDEO_DURATION}秒")
        print(f"   • 默认采样率: {config.DEFAULT_SAMPLE_RATE}")
        print(f"   • 最大帧数: {config.MAX_FRAMES_PER_REQUEST}")
        print(f"   • 输出目录: {config.OUTPUT_DIR}")
        print(f"   • 临时目录: {config.TEMP_DIR}")
        print(f"   • 日志级别: {config.LOG_LEVEL}")
        
        print("\n2. 目录创建:")
        print(f"   • 输出目录是否存在: {os.path.exists(config.OUTPUT_DIR)}")
        print(f"   • 临时目录是否存在: {os.path.exists(config.TEMP_DIR)}")
        
    except Exception as e:
        print(f"❌ 配置演示失败: {e}")

async def main():
    """主演示函数"""
    print("🚀 Video Agent MVP 演示程序")
    print("🤖 基于LLM+工具函数的视频处理Agent")
    print("📅 " + "="*50)
    
    # 运行各种演示
    await demo_basic_usage()
    await demo_tool_registration()
    await demo_error_handling()
    demo_configuration()
    
    print("\n🎉 演示完成!")
    print("\n💡 要开始实际使用，请:")
    print("   1. 设置 GEMINI_API_KEY 环境变量")
    print("   2. 运行: python main.py --video your_video.mp4 --request 'your_request'")
    print("   3. 或运行: python main.py --interactive")

if __name__ == "__main__":
    asyncio.run(main())