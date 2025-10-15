import gradio as gr
import svgwrite
import base64
from PIL import Image
import io
import easyocr
import numpy as np

# 初始化 OCR 模型（只加载一次）
# 推荐的参数：'ch_sim' 表示中文简化字，'en' 表示英文
# 首次运行会下载模型文件。
# lang_list 可以根据需求调整，如果只需要英文，可以只用 ['en']。
ocr_reader = easyocr.Reader(['ch_sim', 'en'], gpu=False) 


def pil_to_base64(pil_image):
    """将 PIL 图像编码为 base64 字符串"""
    buffered = io.BytesIO()
    # 转换为 RGB 确保兼容性，虽然easyocr也能处理四通道
    pil_image = pil_image.convert("RGB") 
    pil_image.save(buffered, format="PNG")
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def create_svg_with_ocr(pil_image):
    """主逻辑：OCR + 生成 SVG"""

    # 将 PIL 图像转换为 numpy 数组，easyocr 的标准输入
    img_np = np.array(pil_image.convert("RGB"))

    # 执行 OCR
    # result: list of [bbox, text, confidence]
    # bbox 是一个包含四个点的列表：[[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    result = ocr_reader.readtext(img_np)
    
    if not result:
        return "<p style='color:red'>识别失败或未检测到文本。</p>"

    # 提取文字和位置
    text_list = [item[1] for item in result]
    bbox_list = [item[0] for item in result]

    # 取左上角坐标作为文字位置 (bbox的第一个点)
    pos_list = [(int(box[0][0]), int(box[0][1])) for box in bbox_list]

    # 构造 SVG
    width, height = pil_image.size
    dwg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))

    # 嵌入图片
    dwg.add(
        dwg.image(href=pil_to_base64(pil_image), insert=(0, 0), size=(width, height))
    )

    # 叠加文字
    for text, pos in zip(text_list, pos_list):
        # 注意：这里我们使用了一个相对固定的字体大小14px，您可能需要根据实际需求调整
        dwg.add(
            dwg.text(
                text,
                insert=pos,
                font_size="14px", # 增大字体以提高可读性
                fill="red",
                style="font-family: Arial, sans-serif; cursor: pointer;",
                class_="copy-text",
            )
        )

    svg_str = dwg.tostring()

    # --- 加上 CSS + JS 脚本以实现复制功能 ---
    # 由于 SVG 中的 text 元素默认难以选中，我们添加一个小的JS脚本来实现点击复制
    html_output = f"""
    <div style="width:{width}px; height:{height}px;">
        {svg_str}
    </div>
    <script>
    function copyText(event) {{
        const target = event.target;
        if (target.classList.contains('copy-text')) {{
            const textToCopy = target.textContent;
            navigator.clipboard.writeText(textToCopy).then(() => {{
                console.log('文本已复制: ' + textToCopy);
                // 简单的视觉反馈
                target.style.fill = 'blue';
                setTimeout(() => {{ target.style.fill = 'red'; }}, 500);
            }}).catch(err => {{
                console.error('复制失败: ', err);
            }});
        }}
    }}

    document.addEventListener('click', function(e) {{
        // 尝试找到 SVG 内部的 text 元素
        let currentElement = e.target;
        while (currentElement) {{
            if (currentElement.tagName === 'text' && currentElement.classList.contains('copy-text')) {{
                copyText({{ target: currentElement }});
                break; 
            }}
            // 限制查找范围在合理的层级内
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
with gr.Blocks(title="图像文字识别 SVG 工具") as demo:
    gr.Markdown(
        "## 🧠 图像 OCR + SVG 标注 (easyocr/CPU)\n上传或粘贴图像，右侧显示带可复制文字的 SVG 结果。\n**提示：** 结果中的红色文字可以点击复制。"
    )

    with gr.Row():
        with gr.Column():
            image_input = gr.Image(
                label="上传或粘贴图片", sources=["upload", "clipboard"], type="pil"
            )
        with gr.Column():
            # 使用 gr.HTML 作为输出，并设置可滚动
            svg_output = gr.HTML(label="识别结果 SVG", elem_id="svg-container")

    image_input.change(fn=create_svg_with_ocr, inputs=image_input, outputs=svg_output)

# 在 Mac 上运行通常需要设置 `share=False`
demo.launch(inbrowser=True)
