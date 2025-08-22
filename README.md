# Video Agent MVP

基于 LLM+工具函数的视频处理智能代理，采用 MVP 原则实现视频内容分析和自动化处理。

## 项目特点

- **职责分离**: LLM 负责理解分析，工具函数负责执行处理
- **MVP 优先**: 核心功能先行，性能优化后续迭代
- **模块化设计**: 便于添加新功能和维护
- **工具注册系统**: 装饰器方式灵活注册处理工具

## 快速开始

### 环境要求

- Python 3.12+
- 内存: 建议 8GB+
- 硬盘: 处理视频需要足够临时空间

### 安装依赖

使用 uv (推荐):

```bash
# 安装uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 初始化项目
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

或使用传统方式:

```bash
pip install -r requirements.txt
```

### 配置环境

```bash
# 复制配置文件
cp .env.example .env

# 编辑.env文件，添加API密钥
GEMINI_API_KEY=your_api_key_here
```

### 使用方法

#### 命令行模式

```bash
# 基本用法
python main.py --video path/to/video.mp4 --request "对视频中的手机进行打码"

# 交互模式
python main.py --interactive

# 列出可用工具
python main.py --list-tools
```

#### 编程方式

```python
from core.agent import VideoAgent
from tools.video_tools import *  # 注册视频工具

async def example():
    # 初始化Agent
    agent = VideoAgent()

    # 处理视频
    result = await agent.process_request(
        "对视频中的手机进行打码",
        "path/to/video.mp4"
    )
    print(result)
```

## 核心功能

### 视频处理工具

- `extract_video_frames`: 智能提取关键帧
- `mosaic_video_regions`: 指定区域马赛克处理
- `get_video_info`: 获取视频基本信息
- `validate_video_file`: 验证视频文件有效性
- `list_supported_formats`: 列出支持格式

### LLM 分析能力

- 视频内容理解和对象识别
- 用户意图分析和任务分解
- 智能工具选择和参数优化

## 项目架构

```
video_agent_mvp/
├── core/                     # 核心模块
│   ├── agent.py              # Agent主类
│   ├── llm_client.py         # LLM客户端封装
│   └── exceptions.py         # 自定义异常
├── tools/                    # 工具函数模块
│   ├── registry.py           # 工具注册机制
│   └── video_tools.py        # 视频处理工具
├── utils/                    # 工具模块
│   └── video_processor.py    # 视频处理核心
├── examples/                 # 示例和演示
│   └── demo.py               # 演示程序
├── config.py                 # 配置管理
└── main.py                   # 程序入口
```

## 工具注册机制

使用装饰器注册新工具:

```python
from tools.registry import tool_registry

@tool_registry.register
def my_custom_tool(param1: str, param2: int = 10) -> str:
    """自定义工具描述

    Args:
        param1: 参数1描述
        param2: 参数2描述，有默认值

    Returns:
        返回值描述
    """
    # 工具实现
    return f"处理结果: {param1} with {param2}"
```

## 使用示例

### 视频打码

```bash
python main.py --video demo.mp4 --request "对视频中的手机进行打码"
```

### 人脸模糊

```bash
python main.py --video demo.mp4 --request "对视频中的人脸进行马赛克处理"
```

### 交互模式

```bash
python main.py --interactive
```

## 演示程序

运行演示程序了解功能:

```bash
python examples/demo.py
```

演示内容包括:

- 基本用法展示
- 工具注册机制
- 错误处理
- 配置管理

## 配置说明

主要配置项 (config.py):

- `GEMINI_API_KEY`: Gemini API 密钥
- `GEMINI_MODEL`: 使用的模型版本
- `MAX_VIDEO_DURATION`: 最大支持视频时长(秒)
- `DEFAULT_SAMPLE_RATE`: 默认帧采样率
- `MAX_FRAMES_PER_REQUEST`: 单次 LLM 请求最大帧数
- `OUTPUT_DIR`: 输出目录
- `TEMP_DIR`: 临时文件目录

## 测试

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_tools.py
```

## 开发状态

这是一个 MVP 版本，当前实现了:

✅ 核心架构和工具注册系统  
✅ 基础视频处理工具  
✅ LLM 客户端封装  
✅ 命令行和交互界面

计划中的功能:

- [ ] 更多视频处理效果
- [ ] 性能优化和追踪
- [ ] Web API 接口
- [ ] 插件系统
