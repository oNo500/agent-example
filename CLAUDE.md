# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an early-stage agent development project focused on creating video processing intelligent agents. The project follows MVP principles and emphasizes modular architecture for LLM-driven automation tasks.

## Architecture Concepts

### Core Architecture Pattern
This project implements a **separation of concerns** architecture where:
- **LLM (Gemini)** handles intent understanding, task decomposition, and content analysis
- **Tool Functions** handle execution and processing (video processing, image manipulation)
- **Registry System** manages tool registration and coordination

### Key Components (Planned)
- **Agent Core**: Main orchestration class that coordinates LLM and tools
- **Tool Registry**: Decorator-based system for registering and managing tool functions
- **Video Processor**: Core video processing utilities using OpenCV
- **LLM Client**: Gemini API wrapper for content analysis

### Planned Project Structure
```
video_agent_mvp/
├── core/                     # Core agent logic
│   ├── agent.py              # Main Agent class
│   ├── llm_client.py         # LLM API wrapper
│   └── exceptions.py         # Custom exceptions
├── tools/                    # Tool function modules
│   ├── registry.py           # Tool registration system
│   ├── video_tools.py        # Video processing tools
│   └── image_tools.py        # Image processing tools
├── utils/                    # Utility modules
│   ├── video_processor.py    # Core video processing
│   ├── file_manager.py       # File management
│   └── logger.py             # Logging utilities
├── tests/                    # Test modules
└── examples/                 # Demo and API examples
```

## Development Guidelines

### Tool Function Standards
All tool functions should follow this pattern:
```python
@tool_registry.register
def tool_function_name(param1: type, param2: type = default_value) -> return_type:
    """Clear functional description
    
    Args:
        param1: Detailed parameter description
        param2: Parameter with default value description
        
    Returns:
        Detailed return value description
        
    Raises:
        SpecificException: Exception description
    """
    # Implementation logic
```

### Data Structure Standards
Use dataclasses for structured data:
- **FrameInfo**: Video frame metadata (frame_id, timestamp, image_path, dimensions)
- **DetectionRegion**: Object detection results (frame_id, object_type, bbox, confidence)
- **ProcessingTask**: Task management (task_id, video_path, target_description, regions, status)

### Error Handling
Implement custom exception hierarchy:
- `VideoAgentException` (base)
- `VideoProcessingError` (video-specific)
- `LLMAnalysisError` (LLM-specific)
- `ToolExecutionError` (tool-specific)

## Technology Stack

### Planned Dependencies
- **LLM**: `google-genai==0.3.2` (Gemini 2.0 Flash)
- **Video Processing**: `opencv-python==4.8.1.78`
- **Image Processing**: `pillow>=10.1.0`
- **Data**: `numpy>=1.24.3`
- **Validation**: `pydantic>=2.5.0`
- **Environment**: `python-dotenv>=1.0.0`
- **API (Optional)**: `fastapi>=0.104.1`

### Development Tools
- **Package Manager**: uv (preferred for Python 3.12+)
- **Testing**: pytest with asyncio support
- **Code Quality**: black, ruff

## Development Workflow

### Environment Setup
```bash
# Initialize with uv
uv init video-agent-mvp
cd video-agent-mvp
uv python pin 3.12
uv sync

# Or traditional setup
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Configuration
Create `.env` file with:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.0-flash
MAX_VIDEO_DURATION=300
DEFAULT_SAMPLE_RATE=30
```

### Core Development Patterns

#### Agent Workflow
1. **Input Processing**: Standardize user requests
2. **Intent Understanding**: LLM analyzes request and video context
3. **Task Decomposition**: Break down into executable steps
4. **Tool Coordination**: Execute appropriate tool functions
5. **Result Integration**: Combine results and provide feedback

#### Video Processing Pipeline
1. **Frame Extraction**: Smart sampling based on content and duration
2. **LLM Analysis**: Content understanding and object detection
3. **Region Processing**: Apply modifications (mosaic, blur, etc.)
4. **Video Reconstruction**: Reassemble processed frames

#### Performance Considerations
- **Smart Sampling**: Adaptive frame sampling based on video duration and content type
- **Memory Management**: Process large videos in chunks
- **Tracking Optimization**: Interpolate between keyframes to reduce LLM calls
- **Resource Cleanup**: Automatic temporary file management

## Project Status

This is a **design and planning phase** project. The current repository contains:
- Architecture documentation (技术架构.md)
- Product requirements (prd.md)
- Basic project structure concepts

## Future Development Areas

1. **Core Implementation**: Build the Agent class and tool registry
2. **Video Processing**: Implement OpenCV-based video manipulation
3. **LLM Integration**: Develop robust Gemini API interaction
4. **Performance Optimization**: Implement smart sampling and tracking
5. **Testing Framework**: Comprehensive test coverage
6. **API Layer**: FastAPI service for HTTP access
7. **Plugin System**: Extensible tool loading mechanism