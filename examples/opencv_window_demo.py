"""
OpenCV 窗口使用演示
展示如何创建、显示和管理 OpenCV 窗口
"""

import cv2
import numpy as np
from typing import Optional


def create_basic_window():
    """创建基本窗口示例"""
    print("🎯 1. 基本窗口示例")
    print("=" * 50)
    
    # 创建一个简单的图像
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    img[:] = (100, 150, 200)  # 蓝色背景
    
    # 在图像上绘制一些图形
    cv2.rectangle(img, (50, 50), (200, 150), (255, 0, 0), 2)  # 蓝色矩形
    cv2.circle(img, (300, 100), 50, (0, 255, 0), -1)  # 绿色圆形
    cv2.putText(img, "Hello OpenCV!", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # 创建窗口
    cv2.namedWindow("基本窗口", cv2.WINDOW_NORMAL)
    
    # 显示图像
    cv2.imshow("基本窗口", img)
    
    print("✅ 窗口已创建，按任意键关闭...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def create_resizable_window():
    """创建可调整大小的窗口"""
    print("\n🎯 2. 可调整大小窗口示例")
    print("=" * 50)
    
    # 创建图像
    img = np.random.randint(0, 255, (300, 400, 3), dtype=np.uint8)
    
    # 创建可调整大小的窗口
    cv2.namedWindow("可调整窗口", cv2.WINDOW_NORMAL)
    
    # 设置窗口大小
    cv2.resizeWindow("可调整窗口", 800, 600)
    
    # 显示图像
    cv2.imshow("可调整窗口", img)
    
    print("✅ 可调整大小窗口已创建，可以拖拽调整大小")
    print("   按 'q' 键关闭窗口")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()


def create_multiple_windows():
    """创建多个窗口示例"""
    print("\n🎯 3. 多个窗口示例")
    print("=" * 50)
    
    # 创建多个图像
    img1 = np.zeros((300, 400, 3), dtype=np.uint8)
    img1[:] = (255, 0, 0)  # 红色
    cv2.putText(img1, "窗口 1", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    img2 = np.zeros((300, 400, 3), dtype=np.uint8)
    img2[:] = (0, 255, 0)  # 绿色
    cv2.putText(img2, "窗口 2", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    img3 = np.zeros((300, 400, 3), dtype=np.uint8)
    img3[:] = (0, 0, 255)  # 蓝色
    cv2.putText(img3, "窗口 3", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # 创建多个窗口
    cv2.namedWindow("窗口1", cv2.WINDOW_NORMAL)
    cv2.namedWindow("窗口2", cv2.WINDOW_NORMAL)
    cv2.namedWindow("窗口3", cv2.WINDOW_NORMAL)
    
    # 设置窗口位置
    cv2.moveWindow("窗口1", 100, 100)
    cv2.moveWindow("窗口2", 550, 100)
    cv2.moveWindow("窗口3", 100, 450)
    
    # 显示图像
    cv2.imshow("窗口1", img1)
    cv2.imshow("窗口2", img2)
    cv2.imshow("窗口3", img3)
    
    print("✅ 三个窗口已创建，按任意键关闭...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def create_interactive_window():
    """创建交互式窗口示例"""
    print("\n🎯 4. 交互式窗口示例")
    print("=" * 50)
    
    # 创建图像
    img = np.zeros((400, 600, 3), dtype=np.uint8)
    
    # 鼠标回调函数
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # 左键点击绘制圆点
            cv2.circle(img, (x, y), 5, (0, 255, 255), -1)
            cv2.imshow("交互窗口", img)
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 右键点击清除图像
            img[:] = 0
            cv2.imshow("交互窗口", img)
    
    # 创建窗口
    cv2.namedWindow("交互窗口", cv2.WINDOW_NORMAL)
    
    # 设置鼠标回调
    cv2.setMouseCallback("交互窗口", mouse_callback)
    
    # 显示图像
    cv2.imshow("交互窗口", img)
    
    print("✅ 交互式窗口已创建")
    print("   左键点击: 绘制黄色圆点")
    print("   右键点击: 清除图像")
    print("   按 'q' 键关闭窗口")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    
    cv2.destroyAllWindows()


def create_annotation_window():
    """创建图片标注窗口"""
    print("\n🎯 5. 图片标注窗口示例")
    print("=" * 50)
    
    # 创建或加载图像
    img = np.zeros((500, 700, 3), dtype=np.uint8)
    img[:] = (50, 50, 50)  # 深灰色背景
    
    # 添加一些示例内容
    cv2.rectangle(img, (100, 100), (200, 200), (255, 0, 0), 2)  # 蓝色矩形
    cv2.circle(img, (400, 150), 30, (0, 255, 0), -1)  # 绿色圆形
    cv2.putText(img, "点击并拖拽绘制标注框", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "按 'c' 清除所有标注", (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(img, "按 's' 保存标注结果", (50, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    # 创建图像副本用于绘制
    drawing_img = img.copy()
    
    # 标注状态变量
    drawing = False
    start_point = None
    end_point = None
    annotations = []  # 存储所有标注框
    
    def annotation_callback(event, x, y, flags, param):
        nonlocal drawing, start_point, end_point, drawing_img
        
        if event == cv2.EVENT_LBUTTONDOWN:
            # 开始绘制
            drawing = True
            start_point = (x, y)
            drawing_img = img.copy()
            
            # 重新绘制之前的标注
            for i, (pt1, pt2, color, label) in enumerate(annotations):
                cv2.rectangle(drawing_img, pt1, pt2, color, 2)
                cv2.putText(drawing_img, f"对象{i+1}", (pt1[0], pt1[1]-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                # 更新绘制
                drawing_img = img.copy()
                
                # 重新绘制之前的标注
                for i, (pt1, pt2, color, label) in enumerate(annotations):
                    cv2.rectangle(drawing_img, pt1, pt2, color, 2)
                    cv2.putText(drawing_img, f"对象{i+1}", (pt1[0], pt1[1]-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # 绘制当前正在绘制的矩形
                cv2.rectangle(drawing_img, start_point, (x, y), (0, 255, 255), 2)
                
        elif event == cv2.EVENT_LBUTTONUP:
            # 结束绘制
            drawing = False
            end_point = (x, y)
            
            # 确保坐标正确（左上角和右下角）
            x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
            x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
            
            # 只有当矩形足够大时才添加标注
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                # 为每个标注分配不同颜色
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
                color = colors[len(annotations) % len(colors)]
                
                annotations.append(((x1, y1), (x2, y2), color, f"对象{len(annotations)+1}"))
                
                # 更新绘制图像
                drawing_img = img.copy()
                for i, (pt1, pt2, color, label) in enumerate(annotations):
                    cv2.rectangle(drawing_img, pt1, pt2, color, 2)
                    cv2.putText(drawing_img, label, (pt1[0], pt1[1]-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    
    # 创建窗口
    cv2.namedWindow("图片标注窗口", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("图片标注窗口", 800, 600)
    
    # 设置鼠标回调
    cv2.setMouseCallback("图片标注窗口", annotation_callback)
    
    # 显示图像
    cv2.imshow("图片标注窗口", drawing_img)
    
    print("✅ 图片标注窗口已创建")
    print("   左键拖拽: 绘制标注框")
    print("   按 'c' 键: 清除所有标注")
    print("   按 's' 键: 保存标注结果")
    print("   按 'q' 键: 关闭窗口")
    
    while True:
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c'):
            # 清除所有标注
            annotations.clear()
            drawing_img = img.copy()
            cv2.imshow("图片标注窗口", drawing_img)
            print("🗑️ 已清除所有标注")
        elif key == ord('s'):
            # 保存标注结果
            if annotations:
                # 创建带标注的图像副本
                result_img = img.copy()
                for i, (pt1, pt2, color, label) in enumerate(annotations):
                    cv2.rectangle(result_img, pt1, pt2, color, 2)
                    cv2.putText(result_img, label, (pt1[0], pt1[1]-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                # 保存图像
                import os
                os.makedirs("output", exist_ok=True)
                cv2.imwrite("output/annotated_image.jpg", result_img)
                
                # 保存标注数据
                annotation_data = []
                for i, (pt1, pt2, color, label) in enumerate(annotations):
                    annotation_data.append({
                        "id": i + 1,
                        "label": label,
                        "bbox": [pt1[0], pt1[1], pt2[0] - pt1[0], pt2[1] - pt1[1]],  # [x, y, width, height]
                        "color": color
                    })
                
                import json
                with open("output/annotations.json", "w", encoding="utf-8") as f:
                    json.dump(annotation_data, f, ensure_ascii=False, indent=2)
                
                print(f"💾 已保存 {len(annotations)} 个标注到 output/annotated_image.jpg 和 output/annotations.json")
            else:
                print("⚠️ 没有标注可保存")
    
    cv2.destroyAllWindows()


def create_video_window(video_path: Optional[str] = None):
    """创建视频播放窗口"""
    print("\n🎯 6. 视频播放窗口示例")
    print("=" * 50)
    
    if video_path is None:
        # 如果没有提供视频文件，创建一个模拟视频
        print("📹 创建模拟视频流...")
        
        cap = None
        frame_count = 0
        
        while frame_count < 100:  # 播放100帧
            # 创建动态图像
            img = np.zeros((400, 600, 3), dtype=np.uint8)
            img[:] = (frame_count * 2 % 255, 100, 150)
            
            # 添加动态文本
            cv2.putText(img, f"Frame: {frame_count}", (50, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 创建窗口（如果还没创建）
            if cap is None:
                cv2.namedWindow("视频窗口", cv2.WINDOW_NORMAL)
            
            # 显示图像
            cv2.imshow("视频窗口", img)
            
            # 检查按键
            key = cv2.waitKey(30) & 0xFF  # 30ms延迟
            if key == ord('q'):
                break
            
            frame_count += 1
    else:
        # 播放真实视频文件
        print(f"📹 播放视频文件: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"❌ 无法打开视频文件: {video_path}")
            return
        
        cv2.namedWindow("视频窗口", cv2.WINDOW_NORMAL)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 显示帧
            cv2.imshow("视频窗口", frame)
            
            # 检查按键
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q'):
                break
        
        cap.release()
    
    cv2.destroyAllWindows()
    print("✅ 视频播放完成")


def main():
    """主函数"""
    print("🚀 OpenCV 窗口使用演示")
    print("=" * 60)
    
    try:
        # 1. 基本窗口
        create_basic_window()
        
        # 2. 可调整大小窗口
        create_resizable_window()
        
        # 3. 多个窗口
        create_multiple_windows()
        
        # 4. 交互式窗口
        create_interactive_window()
        
        # 5. 图片标注窗口
        create_annotation_window()
        
        # 6. 视频播放窗口
        # 如果有测试视频文件，可以传入路径
        test_video_path = "./assets/test1.mp4"
        import os
        if os.path.exists(test_video_path):
            create_video_window(test_video_path)
        else:
            create_video_window()  # 使用模拟视频
        
        print("\n✅ 所有演示完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断演示")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
