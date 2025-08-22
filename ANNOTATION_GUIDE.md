# 视频标注使用指南

## 问题解决总结

✅ **已修复的问题**:
1. 配置属性访问错误 (`TEMP_DIR`, `DEFAULT_SAMPLE_RATE`等)
2. 空数据处理导致的JSON解析错误
3. 缺乏手动标注工具和交互界面

## 新增功能

### 1. 智能关键帧提取
- **运动检测**: 自动跳过静态场景，提取运动明显的关键帧
- **采样优化**: 结合固定采样率和运动分析
- **资源控制**: 智能限制提取帧数避免过多LLM调用

### 2. 可视化标注界面
- **Web界面**: 浏览器中直接标注，拖拽操作简单直观  
- **实时预览**: 标注框实时显示，支持多个区域标注
- **数据导出**: 一键导出标注结果为JSON格式

### 3. 工作流集成
- **自动化流程**: 一键创建从帧提取到标注界面的完整工作流
- **数据持久化**: 标注结果自动保存，支持会话管理
- **错误恢复**: 优雅处理各种异常情况

## 使用方法

### 方法1: 使用改进后的主程序
```bash
python main.py
# 输入视频路径: ./assets/test1.mp4  
# 输入处理需求: 对视频中的手机打码
```

系统现在会：
1. 智能提取关键帧（跳过重复场景）
2. 在失败时提供清晰的错误信息和建议
3. 引导用户使用手动标注工具

### 方法2: 使用标注工作流
```bash
python examples/annotation_demo.py
# 选择: 1 (完整标注工作流)
```

### 方法3: 手动调用工具函数
```python
from core.agent import VideoAgent
import asyncio

async def annotate_video():
    agent = VideoAgent()
    
    # 创建标注工作流
    result = await agent.create_manual_annotation_workflow(
        video_path="./assets/test1.mp4", 
        target_description="手机"
    )
    print(result)

asyncio.run(annotate_video())
```

## 标注界面使用说明

1. **打开标注文件**: 
   - 运行工作流后，在`output/annotations/[session_id]/annotation.html`
   - 用浏览器打开HTML文件

2. **标注操作**:
   - 在关键帧上点击并拖拽选择手机区域
   - 可以为每帧标注多个区域
   - 标注框会实时显示，点击可删除

3. **保存数据**:
   - 点击"保存标注数据"按钮
   - 下载`regions.json`文件
   - 将文件保存到标注会话目录中

4. **应用打码**:
   ```python
   # 加载标注数据并应用打码
   regions_data = agent.tool_registry.execute_tool("load_annotation_data", session_id="your_session_id")
   result = agent.tool_registry.execute_tool("mosaic_video_regions", 
       video_path="./assets/test1.mp4", 
       regions_data=regions_data,
       mosaic_strength=15)
   ```

## 快速测试方法

如果想快速测试打码功能，可以使用快速标注：

```python
from tools.registry import tool_registry

# 提取帧
frames_info = tool_registry.execute_tool("extract_video_frames", 
    video_path="./assets/test1.mp4")

# 快速标注（手动指定坐标）
regions_data = tool_registry.execute_tool("quick_annotate_phone_regions",
    frames_info=frames_info,
    manual_regions="1:500,300,200,150;3:520,310,180,140")

# 应用打码
result = tool_registry.execute_tool("mosaic_video_regions",
    video_path="./assets/test1.mp4",
    regions_data=regions_data)

print(f"处理完成，输出文件: {result}")
```

## 技术改进点

1. **配置管理**: 统一属性命名，避免大小写不一致
2. **错误处理**: 空数据时提供有意义的提示而非崩溃
3. **运动检测**: 智能帧选择，提高标注效率
4. **用户体验**: 可视化界面降低标注门槛
5. **工作流集成**: 端到端自动化减少手动步骤

现在您可以重新运行视频处理，系统会正常工作并提供标注界面！