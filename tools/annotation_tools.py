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
    session_name: str = None,
    video_info: dict = None
) -> str:
    """创建标注会话，生成可视化标注界面
    
    Args:
        video_path: 视频文件路径
        frames_info: 提取的帧信息JSON字符串
        session_name: 会话名称，默认使用视频文件名
        video_info: 视频信息字典，包含分辨率等信息
        
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
            "video_info": video_info or {},
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
    
    # 先生成帧HTML和初始化JS
    frames_html = _generate_frames_html(frames, session_info)
    frame_init_js = _generate_frame_init_js(frames)
    
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
            user-select: none;
            transition: all 0.1s ease;
        }}
        .annotation-box:hover {{
            border-color: #cc0000;
            background: rgba(255, 68, 68, 0.3);
        }}
        #temp-box {{
            border-color: #00ff00 !important;
            background: rgba(0, 255, 0, 0.1) !important;
            pointer-events: none;
            z-index: 1000;
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
        <h1>智能追踪视频标注工具</h1>
        <div class="controls">
            <h3>标注说明（智能追踪版）</h3>
            <p><strong>视频信息:</strong> {session_info.get("video_info", {}).get("resolution", "未知")} | 时长: {session_info.get("video_info", {}).get("duration", "未知")}s</p>
            <p>1. 在下方图片上点击并拖拽来标注目标区域（种子标注）</p>
            <p>2. 可以标注多个区域，完成后点击"保存标注数据"</p>
            <p>3. 系统会使用LLM智能追踪应用到整个视频</p>
            
            <button class="btn btn-success" onclick="saveAnnotations()">保存标注数据</button>
            <button class="btn btn-warning" onclick="clearAnnotations()">清除所有标注</button>
            <button class="btn btn-primary" onclick="exportAnnotations()">导出JSON</button>
        </div>

        <div id="frames-container">
            {frames_html}
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
        let tempRectangle = null;

        function initializeFrameAnnotation(frameId) {{
            const canvas = document.getElementById('frame-' + frameId);
            const container = canvas.parentElement;
            
            // 创建一个持久的临时矩形元素
            createPersistentTempRectangle(container);
            
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', drawRectangle);
            canvas.addEventListener('mouseup', endDrawing);
            canvas.addEventListener('mouseleave', cancelDrawing);
            
            // 改善用户体验的样式
            canvas.style.cursor = 'crosshair';
            
            function startDrawing(e) {{
                e.preventDefault();
                isDrawing = true;
                currentFrameId = frameId;
                const rect = canvas.getBoundingClientRect();
                startX = e.clientX - rect.left;
                startY = e.clientY - rect.top;
                
                // 显示临时矩形
                showTempRectangle(container);
            }}
            
            function drawRectangle(e) {{
                if (!isDrawing) return;
                e.preventDefault();
                
                const rect = canvas.getBoundingClientRect();
                const currentX = e.clientX - rect.left;
                const currentY = e.clientY - rect.top;
                
                // 优化的矩形更新 - 只更新CSS属性
                updateTempRectanglePosition(container, startX, startY, currentX, currentY);
            }}
            
            function endDrawing(e) {{
                if (!isDrawing) return;
                e.preventDefault();
                isDrawing = false;
                
                const rect = canvas.getBoundingClientRect();
                const endX = e.clientX - rect.left;
                const endY = e.clientY - rect.top;
                
                // 创建标注区域
                createAnnotation(frameId, startX, startY, endX, endY, canvas);
                hideTempRectangle(container);
            }}
            
            function cancelDrawing(e) {{
                if (isDrawing) {{
                    isDrawing = false;
                    hideTempRectangle(container);
                }}
            }}
        }}
        
        function createAnnotation(frameId, x1, y1, x2, y2, canvas) {{
            const x = Math.min(x1, x2);
            const y = Math.min(y1, y2);
            const width = Math.abs(x2 - x1);
            const height = Math.abs(y2 - y1);
            
            if (width < 10 || height < 10) return; // 忽略太小的区域
            
            // 转换为视频坐标（相对于原始视频尺寸）
            const videoWidth = {session_info.get("video_info", {}).get("width", 1920)};
            const videoHeight = {session_info.get("video_info", {}).get("height", 1080)};
            const scaleX = videoWidth / canvas.offsetWidth;
            const scaleY = videoHeight / canvas.offsetHeight;
            
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
        
        function createPersistentTempRectangle(container) {{
            if (tempRectangle) return; // 避免重复创建
            
            tempRectangle = document.createElement('div');
            tempRectangle.className = 'annotation-box';
            tempRectangle.id = 'temp-box';
            tempRectangle.style.borderColor = '#00ff00';
            tempRectangle.style.background = 'rgba(0, 255, 0, 0.1)';
            tempRectangle.style.display = 'none';
            tempRectangle.style.pointerEvents = 'none'; // 防止鼠标事件干扰
            
            container.appendChild(tempRectangle);
        }}
        
        function showTempRectangle(container) {{
            if (tempRectangle) {{
                tempRectangle.style.display = 'block';
            }}
        }}
        
        function hideTempRectangle(container) {{
            if (tempRectangle) {{
                tempRectangle.style.display = 'none';
            }}
        }}
        
        function updateTempRectanglePosition(container, x1, y1, x2, y2) {{
            if (!tempRectangle) return;
            
            const x = Math.min(x1, x2);
            const y = Math.min(y1, y2);
            const width = Math.abs(x2 - x1);
            const height = Math.abs(y2 - y1);
            
            // 只更新CSS属性，避免DOM重建
            tempRectangle.style.left = x + 'px';
            tempRectangle.style.top = y + 'px';
            tempRectangle.style.width = width + 'px';
            tempRectangle.style.height = height + 'px';
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
            if (annotations.length === 0) {{
                alert('请先标注至少一个区域！');
                return;
            }}
            
            const data = {{
                session_id: "{session_id}",
                regions: annotations
            }};
            
            // 自动下载标注文件
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'regions.json';
            a.click();
            URL.revokeObjectURL(url);
            
            // 提供清晰的下一步指示
            alert(`✅ 标注完成！共标注了 ${{annotations.length}} 个区域。
            
📁 regions.json 文件已下载到您的下载文件夹
📋 请将该文件复制到标注会话目录中
🎯 然后重新运行程序，系统将自动应用打码到整个视频
            
💡 提示：您也可以直接重新运行 python examples/annotation_demo.py`);
            
            // 自动复制会话ID到剪贴板（如果浏览器支持）
            if (navigator.clipboard) {{
                navigator.clipboard.writeText("{session_id}");
            }}
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
            {frame_init_js}
        }};
    </script>
</body>
</html>
    """
    
    return html_template


def _generate_frames_html(frames: List[Dict], session_info: Dict) -> str:
    """生成帧HTML，优化单帧显示"""
    html_parts = []
    
    for i, frame in enumerate(frames):
        frame_id = frame["frame_id"]
        image_path = frame["image_path"]
        timestamp = frame["timestamp"]
        
        # 转换为相对路径用于HTML显示（相对于HTML文件位置）
        html_dir = session_info["annotation_dir"]
        relative_path = os.path.relpath(image_path, html_dir)
        
        # 如果是单帧模式，优化显示
        frame_title = "最佳关键帧" if len(frames) == 1 else f"帧 {frame_id}"
        
        html_parts.append(f"""
        <div class="frame-container">
            <div class="frame-header">
                <strong>{frame_title}</strong> - 时间: {timestamp:.2f}s
                {' <span style="color: #28a745;">（点击并拖拽标注目标区域）</span>' if len(frames) == 1 else ''}
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
def auto_save_downloaded_regions(
    session_id: str,
    download_path: str = None
) -> str:
    """自动保存下载的标注数据到正确位置
    
    Args:
        session_id: 标注会话ID
        download_path: 下载文件路径，默认在用户下载文件夹查找
        
    Returns:
        操作结果JSON字符串
    """
    try:
        import os
        import shutil
        from pathlib import Path
        
        config = Config()
        annotation_dir = os.path.join(config.OUTPUT_DIR, "annotations", session_id)
        target_path = os.path.join(annotation_dir, "regions.json")
        
        # 如果没有指定下载路径，尝试在常见下载目录查找
        if not download_path:
            common_download_dirs = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/下载"),
                os.path.expanduser("~/Desktop")
            ]
            
            for download_dir in common_download_dirs:
                potential_file = os.path.join(download_dir, "regions.json")
                if os.path.exists(potential_file):
                    download_path = potential_file
                    break
        
        if not download_path or not os.path.exists(download_path):
            return json.dumps({
                "status": "not_found",
                "message": "未找到下载的regions.json文件，请手动复制到标注目录",
                "target_directory": annotation_dir
            }, ensure_ascii=False)
        
        # 复制文件到目标位置
        shutil.copy2(download_path, target_path)
        
        # 删除下载文件夹中的原文件
        try:
            os.remove(download_path)
        except:
            pass  # 删除失败不影响主流程
        
        return json.dumps({
            "status": "success", 
            "message": "标注数据已自动保存到正确位置",
            "target_path": target_path
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"自动保存失败: {str(e)}",
            "manual_instruction": f"请手动将regions.json复制到: {annotation_dir}"
        }, ensure_ascii=False)


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