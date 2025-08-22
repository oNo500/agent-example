#!/usr/bin/env python3
"""
Video Agent MVP - 视频处理智能代理主程序

使用方法:
    python main.py --video path/to/video.mp4 --request "对视频中的手机进行打码"
    python main.py --interactive  # 交互模式
"""

import argparse
import asyncio
import os
from core.agent import VideoAgent
from core.exceptions import VideoAgentException, ConfigurationError
from tools.video_tools import *  # 注册视频处理工具

async def main():
    parser = argparse.ArgumentParser(description="Video Agent MVP - 视频处理智能代理")
    parser.add_argument("--video", type=str, help="视频文件路径")
    parser.add_argument("--request", type=str, help="处理请求描述")
    parser.add_argument("--interactive", action="store_true", help="启动交互模式")
    parser.add_argument("--api-key", type=str, help="Gemini API密钥")
    parser.add_argument("--list-tools", action="store_true", help="列出所有可用工具")
    
    args = parser.parse_args()
    
    try:
        # 初始化Agent
        print("🤖 初始化Video Agent...")
        agent = VideoAgent(api_key=args.api_key)
        print(f"✅ Agent初始化成功，可用工具: {len(agent.list_tools())}个")
        
        # 列出工具
        if args.list_tools:
            print("\n📋 可用工具列表:")
            for tool_name in agent.list_tools():
                tool_info = agent.get_tool_info(tool_name)
                print(f"  • {tool_name}: {tool_info['description']}")
            return
        
        # 交互模式
        if args.interactive:
            await interactive_mode(agent)
            return
        
        # 批处理模式
        if not args.video or not args.request:
            print("❌ 批处理模式需要指定 --video 和 --request 参数")
            parser.print_help()
            return
        
        # 验证视频文件
        if not os.path.exists(args.video):
            print(f"❌ 视频文件不存在: {args.video}")
            return
        
        print(f"\n🎬 处理视频: {args.video}")
        print(f"📝 处理请求: {args.request}")
        print("⏳ 开始处理...")
        
        # 执行处理
        result = await agent.process_request(args.request, args.video)
        
        print(f"\n✅ 处理完成!")
        print(f"📄 结果: {result}")
        
    except ConfigurationError as e:
        print(f"❌ 配置错误: {e}")
        print("💡 请检查 .env 文件或设置环境变量 GEMINI_API_KEY")
    except VideoAgentException as e:
        print(f"❌ 处理失败: {e}")
    except KeyboardInterrupt:
        print("\n⏹️  用户中断操作")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()

async def interactive_mode(agent: VideoAgent):
    """交互模式"""
    print("\n🎯 进入交互模式")
    print("💡 输入 'help' 获取帮助，'quit' 退出")
    
    while True:
        try:
            print("\n" + "="*50)
            
            # 获取用户输入
            video_path = input("📹 请输入视频文件路径 (或 'quit' 退出): ").strip()
            
            if video_path.lower() in ['quit', 'exit', 'q']:
                print("👋 再见!")
                break
            
            if video_path.lower() == 'help':
                print_help()
                continue
            
            if video_path.lower() == 'tools':
                print("\n📋 可用工具列表:")
                for tool_name in agent.list_tools():
                    tool_info = agent.get_tool_info(tool_name)
                    print(f"  • {tool_name}: {tool_info['description']}")
                continue
            
            if not video_path:
                print("❌ 请输入有效的视频文件路径")
                continue
                
            if not os.path.exists(video_path):
                print(f"❌ 文件不存在: {video_path}")
                continue
            
            request = input("📝 请描述您的处理需求: ").strip()
            
            if not request:
                print("❌ 请输入处理需求")
                continue
            
            print("\n⏳ 正在处理...")
            
            # 执行处理
            result = await agent.process_request(request, video_path)
            
            print(f"\n✅ 处理完成!")
            print(f"📄 结果: {result}")
            
        except KeyboardInterrupt:
            print("\n⏹️  用户中断操作")
            break
        except Exception as e:
            print(f"❌ 处理出错: {e}")

def print_help():
    """打印帮助信息"""
    help_text = """
🆘 Video Agent 帮助信息

📋 可用命令:
  help     - 显示此帮助信息
  tools    - 列出所有可用工具
  quit     - 退出程序

💡 使用方法:
1. 输入视频文件路径
2. 描述处理需求，例如:
   • "对视频中的手机进行打码"
   • "给视频中的人脸加马赛克"
   • "识别并模糊视频中的车牌"

📝 请求示例:
  • "对视频中出现的所有手机进行打码处理"
  • "对视频中的人脸进行马赛克处理，强度设为20"
  • "识别视频中的文字并进行模糊处理"

⚠️  注意事项:
  • 支持常见视频格式 (mp4, avi, mov等)
  • 处理时间取决于视频长度和复杂度
  • 确保有足够的磁盘空间存储输出文件
"""
    print(help_text)

if __name__ == "__main__":
    asyncio.run(main())