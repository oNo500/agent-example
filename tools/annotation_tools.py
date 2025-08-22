import json
import os
import webbrowser
from typing import List, Dict, Tuple, Optional
from tools.registry import tool_registry
from core.llm_client import FrameInfo, DetectionRegion
from core.exceptions import VideoProcessingError
from config import Config


@tool_registry.register
def create_annotation_session(
    video_path: str,
    frames_info: str,
    session_name: str = None
) -> str:
    """创建标注会话，生成可视化标注界面
    
    Args:
        video_path: 视频文件路径
        frames_info: 提取的帧信息JSON字符串
        session_name: 会话名称，默认使用视频文件名
        
    Returns:
        标注会话信息JSON字符串
    """
    try:
        config = Config()
        
        # 解析帧信息
        frames_data = json.loads(frames_info)
        frames = frames_data.get("frames", [])
        
        if not frames:
            raise VideoProcessingError("No frames provided for annotation")
        
        # 生成会话ID
        import uuid
        session_id = str(uuid.uuid4())[:8]
        
        if not session_name:
            session_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 创建标注会话目录
        annotation_dir = os.path.join(config.OUTPUT_DIR, "annotations", session_id)
        os.makedirs(annotation_dir, exist_ok=True)
        
        # 保存会话信息
        session_info = {
            "session_id": session_id,
            "session_name": session_name,
            "video_path": video_path,
            "frames": frames,
            "annotation_dir": annotation_dir,
            "status": "created",
            "created_at": str(pd.Timestamp.now()) if 'pd' in globals() else "unknown"
        }
        
        session_file = os.path.join(annotation_dir, "session.json")
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, ensure_ascii=False, indent=2)
        
        # 生成HTML标注界面
        html_content = _generate_annotation_html(session_info)
        html_file = os.path.join(annotation_dir, "annotation.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 自动打开浏览器（如果配置允许）
        browser_opened = False
        if config.auto_open_browser:
            try:
                webbrowser.open(f'file://{os.path.abspath(html_file)}')
                browser_opened = True
            except Exception as e:
                # 浏览器打开失败，继续执行但记录错误
                print(f"⚠️  无法自动打开浏览器: {e}")
        
        result = {
            "session_id": session_id,
            "annotation_file": html_file,
            "frames_count": len(frames),
            "status": "ready",
            "browser_opened": browser_opened,
            "instructions": "浏览器已自动打开标注界面" if browser_opened else "请手动打开annotation.html文件进行标注"
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        raise VideoProcessingError(f"Failed to create annotation session: {str(e)}")


@tool_registry.register
def load_annotation_data(session_id: str) -> str:
    """加载标注数据
    
    Args:
        session_id: 标注会话ID
        
    Returns:
        标注数据JSON字符串，可直接用于mosaic_video_regions
    """
    try:
        config = Config()
        annotation_dir = os.path.join(config.OUTPUT_DIR, "annotations", session_id)
        
        # 查找标注数据文件
        annotation_file = os.path.join(annotation_dir, "regions.json")
        
        if not os.path.exists(annotation_file):
            return json.dumps({
                "status": "no_annotation",
                "message": "No annotation data found. Please complete manual annotation first.",
                "regions": []
            }, ensure_ascii=False)
        
        # 读取标注数据
        with open(annotation_file, 'r', encoding='utf-8') as f:
            annotation_data = json.load(f)
        
        # 转换为工具兼容格式
        regions_data = {
            "regions": annotation_data.get("regions", [])
        }
        
        return json.dumps(regions_data, ensure_ascii=False)
        
    except Exception as e:
        raise VideoProcessingError(f"Failed to load annotation data: {str(e)}")


@tool_registry.register
def list_annotation_sessions() -> str:
    """列出所有标注会话
    
    Returns:
        会话列表JSON字符串
    """
    try:
        config = Config()
        annotations_base_dir = os.path.join(config.OUTPUT_DIR, "annotations")
        
        if not os.path.exists(annotations_base_dir):
            return json.dumps({"sessions": []}, ensure_ascii=False)
        
        sessions = []
        for session_id in os.listdir(annotations_base_dir):
            session_dir = os.path.join(annotations_base_dir, session_id)
            if os.path.isdir(session_dir):
                session_file = os.path.join(session_dir, "session.json")
                if os.path.exists(session_file):
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_info = json.load(f)
                        sessions.append(session_info)
                    except:
                        continue
        
        return json.dumps({"sessions": sessions}, ensure_ascii=False, indent=2)
        
    except Exception as e:
        raise VideoProcessingError(f"Failed to list annotation sessions: {str(e)}")


def _generate_annotation_html(session_info: Dict) -> str:
    """生成HTML标注界面"""
    frames = session_info["frames"]
    session_id = session_info["session_id"]
    
    html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>视频标注工具 - {session_info["session_name"]}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .frame-container {{
            margin: 20px 0;
            border: 2px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            position: relative;
        }}
        .frame-header {{
            background: #f8f9fa;
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        .frame-canvas {{
            position: relative;
            display: block;
            max-width: 100%;
            height: auto;
        }}
        .annotation-box {{
            position: absolute;
            border: 3px solid #ff4444;
            background: rgba(255, 68, 68, 0.2);
            cursor: move;
        }}
        .controls {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .btn {{
            padding: 8px 16px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-primary {{ background: #007bff; color: white; }}
        .btn-success {{ background: #28a745; color: white; }}
        .btn-warning {{ background: #ffc107; color: black; }}
        .btn-danger {{ background: #dc3545; color: white; }}
        .regions-list {{
            margin-top: 20px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 6px;
        }}
        .region-item {{
            padding: 8px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            border-left: 4px solid #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>视频标注工具</h1>
        <div class="controls">
            <h3>标注说明</h3>
            <p>1. 在每个关键帧上点击并拖拽来标注手机位置</p>
            <p>2. 可以为每个帧标注多个区域</p>
            <p>3. 完成标注后点击"保存标注数据"</p>
            
            <button class="btn btn-success" onclick="saveAnnotations()">保存标注数据</button>
            <button class="btn btn-warning" onclick="clearAnnotations()">清除所有标注</button>
            <button class="btn btn-primary" onclick="exportAnnotations()">导出JSON</button>
        </div>

        <div id="frames-container">
            {_generate_frames_html(frames)}
        </div>

        <div class="regions-list">
            <h3>标注区域列表</h3>
            <div id="regions-display"></div>
        </div>
    </div>

    <script>
        let annotations = [];
        let currentFrameId = null;
        let isDrawing = false;
        let startX, startY;

        function initializeFrameAnnotation(frameId) {{
            const canvas = document.getElementById('frame-' + frameId);
            const container = canvas.parentElement;
            
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', drawRectangle);
            canvas.addEventListener('mouseup', endDrawing);
            
            function startDrawing(e) {{
                isDrawing = true;
                currentFrameId = frameId;
                const rect = canvas.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
            }}
            
            function drawRectangle(e) {{
                if (!isDrawing) return;
                
                const rect = canvas.getBoundingClientRect();
                const currentX = e.clientX - rect.left;
                const currentY = e.clientY - rect.top;
                
                // 更新临时矩形显示
                updateTempRectangle(container, startX, startY, currentX, currentY);
            }}
            
            function endDrawing(e) {{
                if (!isDrawing) return;
                isDrawing = false;
                
                const rect = canvas.getBoundingClientRect();
                const endX = e.clientX - rect.left;
                const endY = e.clientY - rect.top;
                
                // 创建标注区域
                createAnnotation(frameId, startX, startY, endX, endY, canvas);
                removeTempRectangle(container);
            }}
        }}
        
        function createAnnotation(frameId, x1, y1, x2, y2, canvas) {{
            const x = Math.min(x1, x2);
            const y = Math.min(y1, y2);
            const width = Math.abs(x2 - x1);
            const height = Math.abs(y2 - y1);
            
            if (width < 10 || height < 10) return; // 忽略太小的区域
            
            // 转换为视频坐标（相对于原始视频尺寸）
            const scaleX = 1920 / canvas.offsetWidth;
            const scaleY = 1080 / canvas.offsetHeight;
            
            const annotation = {{
                frame_id: frameId,
                object_type: "phone",
                bbox: [
                    Math.round(x * scaleX),
                    Math.round(y * scaleY),
                    Math.round(width * scaleX),
                    Math.round(height * scaleY)
                ],
                confidence: 1.0,
                description: "手机区域 - 手动标注"
            }};
            
            annotations.push(annotation);
            updateRegionsDisplay();
            
            // 在画布上显示标注框
            showAnnotationBox(canvas.parentElement, x, y, width, height, annotations.length - 1);
        }}
        
        function showAnnotationBox(container, x, y, width, height, index) {{
            const box = document.createElement('div');
            box.className = 'annotation-box';
            box.style.left = x + 'px';
            box.style.top = y + 'px';
            box.style.width = width + 'px';
            box.style.height = height + 'px';
            box.title = '点击删除此标注';
            box.onclick = () => removeAnnotation(index, box);
            
            container.appendChild(box);
        }}
        
        function removeAnnotation(index, element) {{
            annotations.splice(index, 1);
            element.remove();
            updateRegionsDisplay();
        }}
        
        function updateTempRectangle(container, x1, y1, x2, y2) {{
            removeTempRectangle(container);
            
            const x = Math.min(x1, x2);
            const y = Math.min(y1, y2);
            const width = Math.abs(x2 - x1);
            const height = Math.abs(y2 - y1);
            
            const tempBox = document.createElement('div');
            tempBox.className = 'annotation-box';
            tempBox.id = 'temp-box';
            tempBox.style.left = x + 'px';
            tempBox.style.top = y + 'px';
            tempBox.style.width = width + 'px';
            tempBox.style.height = height + 'px';
            tempBox.style.borderColor = '#00ff00';
            
            container.appendChild(tempBox);
        }}
        
        function removeTempRectangle(container) {{
            const tempBox = container.querySelector('#temp-box');
            if (tempBox) tempBox.remove();
        }}
        
        function updateRegionsDisplay() {{
            const display = document.getElementById('regions-display');
            display.innerHTML = '';
            
            annotations.forEach((region, index) => {{
                const div = document.createElement('div');
                div.className = 'region-item';
                div.innerHTML = `
                    <strong>帧 ${{region.frame_id}}</strong> - ${{region.object_type}}
                    <br>位置: (${{region.bbox[0]}}, ${{region.bbox[1]}}) 
                    大小: ${{region.bbox[2]}}x${{region.bbox[3]}}
                    <button class="btn btn-danger" onclick="removeAnnotation(${{index}}, this.parentElement)">删除</button>
                `;
                display.appendChild(div);
            }});
        }}
        
        function saveAnnotations() {{
            const data = {{
                session_id: "{session_id}",
                regions: annotations
            }};
            
            // 这里需要实现保存逻辑，可以通过表单提交或者AJAX
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'regions.json';
            a.click();
            URL.revokeObjectURL(url);
            
            alert('标注数据已导出！请将regions.json文件放在标注会话目录中。');
        }}
        
        function clearAnnotations() {{
            if (confirm('确定要清除所有标注吗？')) {{
                annotations = [];
                document.querySelectorAll('.annotation-box').forEach(box => box.remove());
                updateRegionsDisplay();
            }}
        }}
        
        function exportAnnotations() {{
            const data = {{
                regions: annotations
            }};
            console.log('标注数据:', JSON.stringify(data, null, 2));
            alert('标注数据已输出到浏览器控制台');
        }}
        
        // 初始化所有帧的标注功能
        window.onload = function() {{
            {_generate_frame_init_js(frames)}
        }};
    </script>
</body>
</html>
    """
    
    return html_template


def _generate_frames_html(frames: List[Dict]) -> str:
    """生成帧HTML"""
    html_parts = []
    
    for frame in frames:
        frame_id = frame["frame_id"]
        image_path = frame["image_path"]
        timestamp = frame["timestamp"]
        
        # 转换为相对路径用于HTML显示
        relative_path = os.path.relpath(image_path)
        
        html_parts.append(f"""
        <div class="frame-container">
            <div class="frame-header">
                <strong>帧 {frame_id}</strong> - 时间: {timestamp:.2f}s
            </div>
            <div style="position: relative;">
                <img id="frame-{frame_id}" src="{relative_path}" class="frame-canvas" />
            </div>
        </div>
        """)
    
    return "".join(html_parts)


def _generate_frame_init_js(frames: List[Dict]) -> str:
    """生成帧初始化JavaScript"""
    js_parts = []
    for frame in frames:
        frame_id = frame["frame_id"]
        js_parts.append(f"initializeFrameAnnotation({frame_id});")
    
    return "\n            ".join(js_parts)


@tool_registry.register
def quick_annotate_phone_regions(
    frames_info: str,
    manual_regions: str
) -> str:
    """快速标注手机区域（用于测试和演示）
    
    Args:
        frames_info: 提取的帧信息JSON字符串
        manual_regions: 手动输入的区域信息，格式: "frame_id:x,y,w,h;frame_id:x,y,w,h"
        
    Returns:
        标注结果JSON字符串，可直接用于mosaic_video_regions
    """
    try:
        # 解析帧信息
        frames_data = json.loads(frames_info)
        frames = frames_data.get("frames", [])
        
        if not frames:
            raise VideoProcessingError("No frames provided")
        
        # 解析手动区域信息
        regions = []
        if manual_regions and manual_regions.strip():
            for region_str in manual_regions.split(';'):
                if ':' in region_str:
                    frame_part, coords_part = region_str.split(':', 1)
                    frame_id = int(frame_part.strip())
                    coords = [int(x.strip()) for x in coords_part.split(',')]
                    
                    if len(coords) == 4:
                        regions.append({
                            "frame_id": frame_id,
                            "object_type": "phone",
                            "bbox": coords,
                            "confidence": 1.0,
                            "description": "手机区域 - 手动标注"
                        })
        
        result = {
            "regions": regions
        }
        
        return json.dumps(result, ensure_ascii=False)
        
    except Exception as e:
        raise VideoProcessingError(f"Quick annotation failed: {str(e)}")