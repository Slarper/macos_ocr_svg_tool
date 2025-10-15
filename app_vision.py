import gradio as gr
import svgwrite
import base64
from PIL import Image
import numpy as np
import io

# 引入 macOS 原生框架的库
import objc
from Vision import VNRecognizeTextRequest, VNImageRequestHandler
from Quartz import CGImageSourceCreateWithData, CGImageSourceCreateImageAtIndex
from Foundation import NSData

# 定义最大宽度，超过这个宽度则按比例缩小
MAX_WIDTH = 1000  # 假设我们将最大宽度设置为 1000 像素


# --- 辅助函数 ---
def pil_to_cgimage(pil_image):
    """将 PIL Image 转换为 Vision API 需要的 CGImage"""
    with io.BytesIO() as output:
        try:
            pil_image = pil_image.convert("RGB")
        except Exception:
            return None
        pil_image.save(output, format="PNG")
        data = NSData.dataWithBytes_length_(output.getvalue(), len(output.getvalue()))

    img_source = CGImageSourceCreateWithData(data, None)
    if img_source is None:
        return None
    cg_image = CGImageSourceCreateImageAtIndex(img_source, 0, None)
    return cg_image


def pil_to_base64(pil_image):
    """将 PIL 图像编码为 base64 字符串"""
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


# ❗ 修正：函数现在接收 PIL 图像对象
def create_svg_with_ocr(pil_image):
    """主逻辑：Vision OCR + 坐标转换 + 生成 SVG"""

    if pil_image is None:
        return "<p style='color:red'>请上传图片。</p>"

    # ❗ 修正的核心：在函数内部统一进行缩放，确保用于 OCR 和 SVG 的尺寸一致
    original_width, original_height = pil_image.size

    if original_width > MAX_WIDTH:
        # 计算缩放比例
        scale_factor = MAX_WIDTH / original_width
        new_width = MAX_WIDTH
        new_height = int(original_height * scale_factor)

        # 使用缩放后的图像
        processed_image = pil_image.resize((new_width, new_height), Image.LANCZOS)
    else:
        # 图像足够小，不缩放
        processed_image = pil_image

    # 确定最终用于 SVG 和 OCR 的尺寸
    width, height = processed_image.size

    cg_image = pil_to_cgimage(processed_image)
    if cg_image is None:
        return "<p style='color:red'>无法处理图像文件。</p>"

    # 1. 设置 Vision 识别请求 (保持不变)
    request = VNRecognizeTextRequest.alloc().init()
    request.setUsesLanguageCorrection_(True)
    request.setRecognitionLevel_(0)
    language_list = ["zh-Hans", "en-US"]
    request.setRecognitionLanguages_(language_list)

    # 2. 创建图像处理句柄
    handler = VNImageRequestHandler.alloc().initWithCGImage_options_(cg_image, {})

    # 3. 执行 OCR 请求 (保持不变)
    success = handler.performRequests_error_([request], None)

    if not success or not request.results():
        return "<p style='color:red'>识别失败或未检测到文本。</p>"

    text_results = []

    # 4. 处理结果并转换坐标 (保持不变，因为 width/height 已经是 processed_image 的尺寸)
    for observation in request.results():
        candidates = observation.topCandidates_(1)
        if not candidates:
            continue

        text = candidates[0].string()
        box = observation.boundingBox()

        # 转换归一化坐标到像素坐标
        x_pixel = int(box.origin.x * width)
        y_norm_top_edge = 1.0 - box.origin.y
        y_pixel = int(y_norm_top_edge * height)

        text_results.append((text, x_pixel, y_pixel))

    # 5. 构造 SVG (使用 processed_image 的尺寸)
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))

    # 嵌入图片 (使用 processed_image)
    dwg.add(
        dwg.image(
            href=pil_to_base64(processed_image), insert=(0, 0), size=(width, height)
        )
    )

    # 叠加文字 (保持不变)
    for text, x_pos, y_pos in text_results:
        dwg.add(
            dwg.text(
                text,
                insert=(x_pos, y_pos),
                font_size="14px",
                fill="red",
                style="font-family: Arial, sans-serif; cursor: pointer;",
                class_="copy-text",
            )
        )

    svg_str = dwg.tostring()

    # 加上复制功能脚本 (保持不变)
    html_output = f"""
    <div style="width:{width}px; height:{height}px;">
        {svg_str}
    </div>
    <script>
    // ... (JS 脚本保持不变)
    function copyText(event) {{
        const target = event.target;
        if (target.classList.contains('copy-text')) {{
            const textToCopy = target.textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {{
                console.log('文本已复制 (Vision): ' + textToCopy);
                target.style.fill = 'blue';
                setTimeout(() => {{ target.style.fill = 'red'; }}, 500);
            }}).catch(err => {{
                console.error('复制失败: ', err);
            }});
        }}
    }}

    document.addEventListener('click', function(e) {{
        let currentElement = e.target;
        while (currentElement) {{
            if (currentElement.tagName === 'text' && currentElement.classList.contains('copy-text')) {{
                copyText({{ target: currentElement }});
                break; 
            }}
            if (currentElement.tagName === 'svg' || currentElement.tagName === 'BODY') {{
                break;
            }}
            currentElement = currentElement.parentElement;
        }}
    }});
    </script>
    """

    return html_output


# Gradio 页面搭建
with gr.Blocks(title="图像文字识别 SVG 工具 (macOS Vision API)") as demo:
    gr.Markdown(
        f"## 🧠 图像 OCR + SVG 标注 (macOS Vision API)\n上传或粘贴图像，右侧显示带可复制文字的 SVG 结果。\n**注意：** 为避免 Gradio 缩放问题，图片宽度超过 {MAX_WIDTH}px 将被按比例缩小。"
    )

    # CSS 保持不变 (解决 Gradio 容器拉伸问题)
    demo.css = """
    /* 确保外部容器允许内容决定大小，并防止拉伸 */
    #svg-container {
        max-width: fit-content !important; 
        max-height: fit-content !important; 
    }
    /* 确保 SVG 元素本身不被父容器强制拉伸 */
    #svg-container svg {
        display: block; /* 移除可能的内联元素空白 */
        width: auto !important;
        height: auto !important;
    }
    """

    with gr.Row():
        with gr.Column():
            # ❗ 保持 type="pil"，但函数内部处理尺寸
            image_input = gr.Image(
                label="上传或粘贴图片",
                sources=["upload", "clipboard"],
                type="pil",
                # 可以设置一个最大宽高，进一步限制 Gradio 的默认缩放行为
                # width=1000
            )
        with gr.Column():
            svg_output = gr.HTML(label="识别结果 SVG", elem_id="svg-container")

    image_input.change(fn=create_svg_with_ocr, inputs=image_input, outputs=svg_output)

demo.launch(inbrowser=True)
