"""
HTML可视化工具
用于在浏览器中显示关键帧和检测坐标
"""

import os
import json
import base64
from typing import List, Dict, Any
from datetime import datetime
from core.llm_client import FrameInfo, DetectionRegion


class HTMLVisualizer:
    """HTML可视化工具类"""
    
    def __init__(self, output_dir: str = "./output/html_visualization"):
        """初始化HTML可视化工具
        
        Args:
            output_dir: HTML输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_detection_visualization(
        self,
        frames: List[FrameInfo],
        detections: List[DetectionRegion],
        title: str = "LLM检测结果可视化"
    ) -> str:
        """创建检测结果可视化HTML页面
        
        Args:
            frames: 关键帧信息列表
            detections: 检测结果列表
            title: 页面标题
            
        Returns:
            HTML文件路径
        """
        # 按帧ID组织检测结果
        detections_by_frame = {}
        for detection in detections:
            frame_id = detection.frame_id
            if frame_id not in detections_by_frame:
                detections_by_frame[frame_id] = []
            detections_by_frame[frame_id].append(detection)
        
        # 创建帧数据
        frame_data = []
        for frame in frames:
            # 使用相对路径引用图片
            try:
                if os.path.exists(frame.image_path):
                    # 计算相对于HTML文件的路径
                    html_dir = os.path.abspath(self.output_dir)
                    image_abs_path = os.path.abspath(frame.image_path)
                    
                    # 计算相对路径 - 从HTML文件位置到图片文件的相对路径
                    html_file_dir = os.path.abspath(self.output_dir)
                    rel_path = os.path.relpath(image_abs_path, html_file_dir)
                    image_src = rel_path.replace('\\', '/')  # 确保使用正斜杠
                    print(f"✅ 成功引用图片: {frame.image_path} -> {image_src}")
                else:
                    print(f"❌ 图片文件不存在: {frame.image_path}")
                    image_src = ""
            except Exception as e:
                print(f"❌ 无法处理图片路径 {frame.image_path}: {e}")
                image_src = ""
            
            # 获取该帧的检测结果
            frame_detections = detections_by_frame.get(frame.frame_id, [])
            
            frame_info = {
                'frame_id': frame.frame_id,
                'timestamp': frame.timestamp,
                'image_src': image_src,
                'image_path': frame.image_path,
                'detections': [
                    {
                        'object_type': d.object_type,
                        'bbox': d.bbox,
                        'confidence': d.confidence,
                        'description': d.description,
                        'track_id': d.track_id
                    } for d in frame_detections
                ]
            }
            frame_data.append(frame_info)
        
        # 生成HTML内容
        html_content = self._generate_html_template(frame_data, title)
        
        # 保存HTML文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"detection_visualization_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML可视化页面已生成: {filepath}")
        return filepath
    
    def _generate_html_template(self, frame_data: List[Dict], title: str) -> str:
        """生成HTML模板"""
        
        # 转换frame_data为JSON字符串
        frame_data_json = json.dumps(frame_data, ensure_ascii=False, indent=2)
        
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .header h1 {{
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }}
        
        .header .subtitle {{
            color: #666;
            margin-top: 10px;
            font-size: 1.1em;
        }}
        
        .controls {{
            margin-bottom: 30px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .control-group label {{
            font-weight: 600;
            color: #555;
        }}
        
        select, input[type="range"] {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }}
        
        .frame-container {{
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            background: #fafafa;
        }}
        
        .frame-info {{
            margin-bottom: 15px;
            padding: 10px;
            background: #e8f4fd;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        }}
        
        .frame-info h3 {{
            margin: 0 0 5px 0;
            color: #1976D2;
        }}
        
        .frame-info p {{
            margin: 2px 0;
            color: #555;
        }}
        
        .image-container {{
            position: relative;
            display: inline-block;
            max-width: 100%;
            margin: 20px 0;
            border: 2px dashed #ddd;
            padding: 10px;
            background: #f9f9f9;
        }}
        
        .frame-image {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        
        .detection-box {{
            position: absolute;
            border: 3px solid;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(2px);
        }}
        
        .detection-label {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            top: -25px;
            left: 0;
        }}
        
        .detections-list {{
            margin-top: 20px;
        }}
        
        .detection-item {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .detection-item h4 {{
            margin: 0 0 8px 0;
            color: #333;
        }}
        
        .detection-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 14px;
        }}
        
        .detail-item {{
            display: flex;
            justify-content: space-between;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: #555;
        }}
        
        .detail-value {{
            color: #333;
        }}
        
        .no-detections {{
            text-align: center;
            color: #888;
            font-style: italic;
            padding: 20px;
        }}
        
        .navigation {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 30px;
        }}
        
        .nav-button {{
            padding: 10px 20px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }}
        
        .nav-button:hover {{
            background: #1976D2;
        }}
        
        .nav-button:disabled {{
            background: #ccc;
            cursor: not-allowed;
        }}
        
        .color-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .color-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .color-box {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 2px solid;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="subtitle">验证LLM检测结果的准确性</div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label for="frameSelect">选择帧:</label>
                <select id="frameSelect"></select>
            </div>
            <div class="control-group">
                <label for="scaleSlider">缩放:</label>
                <input type="range" id="scaleSlider" min="0.3" max="2" step="0.1" value="1">
                <span id="scaleValue">100%</span>
            </div>
            <div class="control-group">
                <label>
                    <input type="checkbox" id="showLabels" checked> 显示标签
                </label>
            </div>
        </div>
        
        <div class="frame-container">
            <div class="frame-info" id="frameInfo"></div>
            <div class="image-container" id="imageContainer"></div>
            <div class="detections-list" id="detectionsList"></div>
        </div>
        
        <div class="navigation">
            <button class="nav-button" id="prevButton">上一帧</button>
            <button class="nav-button" id="nextButton">下一帧</button>
        </div>
        
        <div class="color-legend" id="colorLegend"></div>
    </div>

    <script>
        // 帧数据
        const frameData = {frame_data_json};
        
        let currentFrameIndex = 0;
        const frameSelect = document.getElementById('frameSelect');
        const scaleSlider = document.getElementById('scaleSlider');
        const scaleValue = document.getElementById('scaleValue');
        const showLabels = document.getElementById('showLabels');
        const frameInfo = document.getElementById('frameInfo');
        const imageContainer = document.getElementById('imageContainer');
        const detectionsList = document.getElementById('detectionsList');
        const prevButton = document.getElementById('prevButton');
        const nextButton = document.getElementById('nextButton');
        const colorLegend = document.getElementById('colorLegend');
        
        // 颜色调色板
        const colors = [
            '#FF5722', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0',
            '#00BCD4', '#FFEB3B', '#795548', '#607D8B', '#E91E63'
        ];
        
        let objectTypeColors = {{}};
        
        // 初始化
        function init() {{
            // 填充帧选择器
            frameData.forEach((frame, index) => {{
                const option = document.createElement('option');
                option.value = index;
                option.textContent = `帧 ${{frame.frame_id}} (t=${{frame.timestamp.toFixed(2)}}s)`;
                frameSelect.appendChild(option);
            }});
            
            // 生成颜色映射
            const objectTypes = [...new Set(frameData.flatMap(f => f.detections.map(d => d.object_type)))];
            objectTypes.forEach((type, index) => {{
                objectTypeColors[type] = colors[index % colors.length];
            }});
            
            // 生成颜色图例
            updateColorLegend();
            
            // 事件监听
            frameSelect.addEventListener('change', (e) => {{
                currentFrameIndex = parseInt(e.target.value);
                updateDisplay();
            }});
            
            scaleSlider.addEventListener('input', (e) => {{
                const scale = parseFloat(e.target.value);
                scaleValue.textContent = Math.round(scale * 100) + '%';
                updateImageScale(scale);
            }});
            
            showLabels.addEventListener('change', updateDisplay);
            
            prevButton.addEventListener('click', () => {{
                if (currentFrameIndex > 0) {{
                    currentFrameIndex--;
                    frameSelect.value = currentFrameIndex;
                    updateDisplay();
                }}
            }});
            
            nextButton.addEventListener('click', () => {{
                if (currentFrameIndex < frameData.length - 1) {{
                    currentFrameIndex++;
                    frameSelect.value = currentFrameIndex;
                    updateDisplay();
                }}
            }});
            
            // 初始显示
            updateDisplay();
        }}
        
        function updateDisplay() {{
            const frame = frameData[currentFrameIndex];
            
            // 更新帧信息
            frameInfo.innerHTML = `
                <h3>帧 ${{frame.frame_id}}</h3>
                <p><strong>时间戳:</strong> ${{frame.timestamp.toFixed(2)}} 秒</p>
                <p><strong>图片路径:</strong> ${{frame.image_path}}</p>
                <p><strong>检测数量:</strong> ${{frame.detections.length}} 个目标</p>
            `;
            
            // 更新图片和检测框
            updateImage(frame);
            
            // 更新检测列表
            updateDetectionsList(frame.detections);
            
            // 更新导航按钮
            prevButton.disabled = currentFrameIndex === 0;
            nextButton.disabled = currentFrameIndex === frameData.length - 1;
        }}
        
        function updateImage(frame) {{
            const scale = parseFloat(scaleSlider.value);
            
            imageContainer.innerHTML = '';
            
            if (!frame.image_src) {{
                imageContainer.innerHTML = '<div class="no-detections">图片加载失败</div>';
                return;
            }}
            
            const img = document.createElement('img');
            img.src = frame.image_src;
            img.className = 'frame-image';
            img.style.transform = `scale(${{scale}})`;
            img.style.transformOrigin = 'top left';
            
            img.onload = () => {{
                // 计算图片的实际显示尺寸和缩放比例
                const imgRect = img.getBoundingClientRect();
                const originalWidth = img.naturalWidth;
                const originalHeight = img.naturalHeight;
                const displayWidth = imgRect.width;
                const displayHeight = imgRect.height;
                
                // 计算缩放比例
                const scaleX = displayWidth / originalWidth;
                const scaleY = displayHeight / originalHeight;
                
                // 绘制检测框
                frame.detections.forEach((detection, index) => {{
                    const [x, y, width, height] = detection.bbox;
                    const color = objectTypeColors[detection.object_type] || '#FF5722';
                    
                    const box = document.createElement('div');
                    box.className = 'detection-box';
                    box.style.left = (x * scaleX) + 'px';
                    box.style.top = (y * scaleY) + 'px';
                    box.style.width = (width * scaleX) + 'px';
                    box.style.height = (height * scaleY) + 'px';
                    box.style.borderColor = color;
                    
                    if (showLabels.checked) {{
                        const label = document.createElement('div');
                        label.className = 'detection-label';
                        label.style.backgroundColor = color;
                        label.textContent = `${{detection.object_type}} (${{(detection.confidence * 100).toFixed(1)}}%)`;
                        box.appendChild(label);
                    }}
                    
                    imageContainer.appendChild(box);
                }});
            }};
            
            imageContainer.appendChild(img);
        }}
        
        function updateImageScale(scale) {{
            const img = imageContainer.querySelector('.frame-image');
            if (img) {{
                img.style.transform = `scale(${{scale}})`;
                
                // 重新计算检测框位置
                const imgRect = img.getBoundingClientRect();
                const originalWidth = img.naturalWidth;
                const originalHeight = img.naturalHeight;
                const displayWidth = imgRect.width;
                const displayHeight = imgRect.height;
                
                const scaleX = displayWidth / originalWidth;
                const scaleY = displayHeight / originalHeight;
                
                const boxes = imageContainer.querySelectorAll('.detection-box');
                const frame = frameData[currentFrameIndex];
                
                boxes.forEach((box, index) => {{
                    const detection = frame.detections[index];
                    const [x, y, width, height] = detection.bbox;
                    
                    box.style.left = (x * scaleX) + 'px';
                    box.style.top = (y * scaleY) + 'px';
                    box.style.width = (width * scaleX) + 'px';
                    box.style.height = (height * scaleY) + 'px';
                }});
            }}
        }}
        
        function updateDetectionsList(detections) {{
            if (detections.length === 0) {{
                detectionsList.innerHTML = '<div class="no-detections">该帧无检测结果</div>';
                return;
            }}
            
            const html = detections.map((detection, index) => {{
                const color = objectTypeColors[detection.object_type] || '#FF5722';
                const [x, y, width, height] = detection.bbox;
                
                return `
                    <div class="detection-item" style="border-left: 4px solid ${{color}}">
                        <h4>${{detection.object_type}} #${{index + 1}}</h4>
                        <div class="detection-details">
                            <div class="detail-item">
                                <span class="detail-label">置信度:</span>
                                <span class="detail-value">${{(detection.confidence * 100).toFixed(1)}}%</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">边界框:</span>
                                <span class="detail-value">(${{x}}, ${{y}}, ${{width}}, ${{height}})</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">描述:</span>
                                <span class="detail-value">${{detection.description}}</span>
                            </div>
                            ${{detection.track_id ? `
                            <div class="detail-item">
                                <span class="detail-label">跟踪ID:</span>
                                <span class="detail-value">${{detection.track_id}}</span>
                            </div>
                            ` : ''}}
                        </div>
                    </div>
                `;
            }}).join('');
            
            detectionsList.innerHTML = html;
        }}
        
        function updateColorLegend() {{
            const html = Object.entries(objectTypeColors).map(([type, color]) => `
                <div class="color-item">
                    <div class="color-box" style="border-color: ${{color}}; background-color: ${{color}}20;"></div>
                    <span>${{type}}</span>
                </div>
            `).join('');
            
            colorLegend.innerHTML = html;
        }}
        
        // 启动应用
        init();
    </script>
</body>
</html>"""
        
        return html_template
