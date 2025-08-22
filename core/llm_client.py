from typing import List, Dict, Any, Optional
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from core.exceptions import LLMAnalysisError, ConfigurationError
from config import Config

class FrameInfo(BaseModel):
    """视频帧信息模型"""
    frame_id: int = Field(..., description="帧ID")
    timestamp: float = Field(..., description="时间戳")
    image_path: str = Field(..., description="图片路径")
    width: int = Field(..., description="帧宽度")
    height: int = Field(..., description="帧高度")

class DetectionRegion(BaseModel):
    """检测区域模型"""
    frame_id: int = Field(..., description="帧ID")
    object_type: str = Field(..., description="对象类型")
    bbox: tuple[int, int, int, int] = Field(..., description="边界框 (x, y, width, height)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    description: str = Field(..., description="描述")
    track_id: Optional[int] = Field(None, description="跟踪ID")

class GeminiClient:
    """Gemini LLM客户端封装"""
    
    def __init__(self, api_key: str = None):
        config = Config()
        self.api_key = api_key or config.gemini_api_key
        self.model_name = config.gemini_model
        
        if not self.api_key:
            raise ConfigurationError("GEMINI_API_KEY is required")
        
        # 配置Google Gen AI客户端
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(api_version='v1beta')
        )
    
    async def analyze_video_frames(
        self, 
        frames: List[FrameInfo], 
        target_description: str
    ) -> List[DetectionRegion]:
        """分析视频帧，返回检测结果
        
        Args:
            frames: 视频帧信息列表
            target_description: 目标描述
            
        Returns:
            检测区域列表
        """
        try:
            # 构建分析prompt
            prompt = self._build_analysis_prompt(target_description, frames)
            
            # 准备图片数据
            contents = [prompt]
            for frame in frames:
                try:
                    contents.append(types.File(
                        file=frame.image_path,
                        mime_type='image/jpeg'
                    ))
                except Exception as e:
                    raise LLMAnalysisError(f"Failed to load frame {frame.frame_id}: {str(e)}")
            
            # 调用Google Gen AI API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            
            # 解析响应
            return self._parse_detection_response(response.text)
            
        except Exception as e:
            raise LLMAnalysisError(f"Video frame analysis failed: {str(e)}") from e
    
    async def decompose_task(
        self, 
        user_request: str, 
        available_tools: List[Dict],
        video_info: Dict = None
    ) -> List[Dict]:
        """分解用户任务为执行步骤
        
        Args:
            user_request: 用户请求
            available_tools: 可用工具列表
            video_info: 视频信息
            
        Returns:
            执行步骤列表
        """
        try:
            prompt = self._build_task_decomposition_prompt(
                user_request, available_tools, video_info
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return self._parse_task_response(response.text)
            
        except Exception as e:
            raise LLMAnalysisError(f"Task decomposition failed: {str(e)}") from e
    
    def _build_analysis_prompt(self, target_description: str, frames: List[FrameInfo]) -> str:
        """构建视频分析prompt"""
        frame_data = []
        for frame in frames:
            frame_data.append({
                "frame_id": frame.frame_id,
                "timestamp": frame.timestamp,
                "dimensions": f"{frame.width}x{frame.height}"
            })
        
        return f"""你是一个专业的视频内容分析助手。请仔细分析提供的视频帧，准确识别用户指定的目标对象。

任务要求:
1. 识别目标: {target_description}
2. 返回精确的边界框坐标
3. 评估检测置信度
4. 标注对象在不同帧间的变化

输出格式要求:
必须返回JSON格式，结构如下:
{{
  "detections": [
    {{
      "frame_id": 1,
      "objects": [
        {{
          "type": "目标类型",
          "bbox": [x, y, width, height],
          "confidence": 0.95,
          "description": "具体描述"
        }}
      ]
    }}
  ],
  "summary": "整体分析总结"
}}

视频帧信息:
{json.dumps(frame_data, indent=2, ensure_ascii=False)}

请开始分析:"""
    
    def _build_task_decomposition_prompt(
        self, 
        user_request: str, 
        available_tools: List[Dict],
        video_info: Dict = None
    ) -> str:
        """构建任务分解prompt"""
        video_info_str = json.dumps(video_info, indent=2, ensure_ascii=False) if video_info else "无"
        tools_str = json.dumps(available_tools, indent=2, ensure_ascii=False)
        
        return f"""用户请求: {user_request}
视频信息: {video_info_str}

请将用户请求分解为具体的执行步骤，并选择合适的工具函数。

可用工具:
{tools_str}

请返回执行计划的JSON格式:
{{
  "steps": [
    {{
      "step_id": 1,
      "description": "步骤描述",
      "tool_name": "工具函数名",
      "parameters": {{"param1": "value1"}}
    }}
  ]
}}"""
    
    def _parse_detection_response(self, response_text: str) -> List[DetectionRegion]:
        """解析检测响应"""
        try:
            # 尝试提取JSON部分
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise LLMAnalysisError("No valid JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            
            regions = []
            for detection in data.get("detections", []):
                frame_id = detection["frame_id"]
                for obj in detection.get("objects", []):
                    region = DetectionRegion(
                        frame_id=frame_id,
                        object_type=obj["type"],
                        bbox=tuple(obj["bbox"]),
                        confidence=obj["confidence"],
                        description=obj["description"]
                    )
                    regions.append(region)
            
            return regions
            
        except json.JSONDecodeError as e:
            raise LLMAnalysisError(f"Failed to parse detection response: {str(e)}")
        except KeyError as e:
            raise LLMAnalysisError(f"Missing required field in response: {str(e)}")
    
    def _parse_task_response(self, response_text: str) -> List[Dict]:
        """解析任务分解响应"""
        try:
            # 尝试提取JSON部分
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise LLMAnalysisError("No valid JSON found in task response")
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            
            return data.get("steps", [])
            
        except json.JSONDecodeError as e:
            raise LLMAnalysisError(f"Failed to parse task response: {str(e)}")
        except KeyError as e:
            raise LLMAnalysisError(f"Missing required field in task response: {str(e)}")