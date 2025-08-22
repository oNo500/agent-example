# Video Agent MVP

基于 LLM+工具函数的视频处理智能代理，采用 MVP 原则实现视频内容分析和自动化处理。

## 项目特点

- **职责分离**: LLM 负责理解分析，工具函数负责执行处理
- **MVP 优先**: 核心功能先行，性能优化后续迭代
- **模块化设计**: 便于添加新功能和维护
- **工具注册系统**: 装饰器方式灵活注册处理工具
- **现代化技术栈**: Google Gen AI SDK + Pydantic V2 + 最新依赖
- **类型安全**: 完整的类型注解和 Pydantic 模型验证
- **配置管理**: 使用 Pydantic Settings 进行环境配置

## 快速开始

### 环境要求

- Python 3.12+
- 内存: 建议 8GB+
- 硬盘: 处理视频需要足够临时空间

### 安装依赖

使用 uv 管理项目依赖:

```bash
# 安装uv (如果未安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

### 配置环境

创建 `.env` 文件并配置必要的环境变量：

```bash
# 创建配置文件
cat > .env << EOF
# LLM配置
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# 视频处理配置
MAX_VIDEO_DURATION=300
DEFAULT_SAMPLE_RATE=30
MAX_FRAMES_PER_REQUEST=20

# 输出配置
OUTPUT_DIR=output
TEMP_DIR=temp
LOG_LEVEL=INFO

# 性能配置
MAX_MEMORY_MB=2048
ENABLE_GPU=true
CONCURRENT_WORKERS=4
EOF
```

### 使用方法

#### 命令行模式

```bash
# 基本用法
uv run python main.py --video path/to/video.mp4 --request "对视频中的手机进行打码"

# 交互模式
uv run python main.py --interactive

# 列出可用工具
uv run python main.py --list-tools
```

#### 编程方式

```python
import asyncio
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

# 运行示例
if __name__ == "__main__":
    asyncio.run(example())
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
uv run python main.py --video demo.mp4 --request "对视频中的手机进行打码"
```

### 人脸模糊

```bash
uv run python main.py --video demo.mp4 --request "对视频中的人脸进行马赛克处理"
```

### 交互模式

```bash
uv run python main.py --interactive
```

## 演示程序

运行演示程序了解功能:

```bash
uv run python examples/demo.py
```

演示内容包括:

- 基本用法展示
- 工具注册机制
- 错误处理
- 配置管理

## 配置说明

使用 Pydantic Settings 进行配置管理，支持 `.env` 文件和环境变量：

### LLM 配置

- `GEMINI_API_KEY`: Gemini API 密钥 (必需)
- `GEMINI_MODEL`: 使用的模型版本 (默认: gemini-2.0-flash-exp)

### 视频处理配置

- `MAX_VIDEO_DURATION`: 最大支持视频时长(秒) (默认: 300)
- `DEFAULT_SAMPLE_RATE`: 默认帧采样率 (默认: 30)
- `MAX_FRAMES_PER_REQUEST`: 单次 LLM 请求最大帧数 (默认: 20)

### 输出配置

- `OUTPUT_DIR`: 输出目录 (默认: output)
- `TEMP_DIR`: 临时文件目录 (默认: temp)
- `LOG_LEVEL`: 日志级别 (DEBUG/INFO/WARNING/ERROR, 默认: INFO)

### 性能配置

- `MAX_MEMORY_MB`: 最大内存使用 (默认: 2048)
- `ENABLE_GPU`: 是否启用 GPU 加速 (默认: true)
- `CONCURRENT_WORKERS`: 并发工作线程数 (默认: 4)

## 测试

```bash
# 运行测试
pytest

# 运行特定测试
pytest tests/test_tools.py
```

## 开发状态

这是一个 **MVP 开发项目**，专注于核心功能实现，**不用于打包发布**。

### v0.2.0 - 现代化升级 ✅

✅ **Google Gen AI SDK**: 迁移到官方统一 SDK  
✅ **Pydantic V2**: 完整的数据模型和验证  
✅ **现代化依赖**: 所有依赖升级到最新版本  
✅ **配置管理**: Pydantic Settings + 环境变量  
✅ **类型安全**: 完整类型注解和验证  
✅ **代码质量**: 统一代码风格和错误处理

### v0.1.0 - 基础实现 ✅

✅ 核心架构和工具注册系统  
✅ 基础视频处理工具  
✅ LLM 客户端封装  
✅ 命令行和交互界面

### 计划中的功能

- [ ] 更多视频处理效果
- [ ] 性能优化和追踪
- [ ] Web API 接口
- [ ] 插件系统
- [ ] 单元测试覆盖
- [ ] 由于跟踪打码效果还比较差，需要完整的验证流程

## 技术栈

### 核心依赖

- **google-genai** (v0.3.0+): Google 官方统一的生成式 AI SDK
- **opencv-python** (v4.10.0+): 计算机视觉和视频处理
- **pillow** (v11.0.0+): 图像处理库
- **numpy** (v2.0.0+): 数值计算库
- **python-dotenv** (v1.0.0+): 环境变量管理
- **pydantic** (v2.9.0+): 数据验证和设置管理
- **pydantic-settings** (v2.6.0+): Pydantic 配置管理
- **fastapi** (v0.115.0+): 现代 Python Web 框架 (用于未来 API)
- **matplotlib** (v3.10.5+): 数据可视化库

### 开发工具

- **uv**: 现代 Python 包管理器
- **pytest** (v7.4.0+): 测试框架
- **pytest-asyncio** (v0.21.0+): 异步测试支持
- **black** (v23.0.0+): 代码格式化工具
- **ruff** (v0.1.0+): 代码检查和格式化工具

## 使用注意

- 项目仅用于开发和学习，不进行打包分发
- 依赖通过 `pyproject.toml` 管理，使用 uv 工具
- 所有运行命令都使用 `uv run` 前缀
- 需要配置 Gemini API 密钥才能正常运行
- 使用最新的 Google Gen AI SDK，确保 API 密钥有效
