# macos_ocr_svg_tool

## 📝 What is it? (项目简介)

这是一个本地 **OCR（光学字符识别）** 工具，它利用 **Apple's Vision API** 的强大能力，在 macOS 系统上实现高效的文字识别。

**核心功能：**

* 利用 macOS 原生 API，实现快速、准确的离线 OCR。
* 通过 **Gradio** 驱动的浏览器界面作为前端，实现强大的跨平台兼容性（无需额外安装桌面应用）。

---

## 🚀 How to install and run it? (安装与运行)

### 前提条件

* 一台运行 **macOS** 的电脑（Apple Vision API 要求）。
* 已安装 **Git**。
* 建议安装 **Conda/Miniconda** 进行环境管理。

### 1. 克隆仓库

打开终端，将项目克隆到本地：

```bash
git clone https://github.com/Slarper/macos_ocr_svg_tool.git
cd macos_ocr_svg_tool
```

### 2. 创建 Conda 环境
确保你已安装 Conda，并运行以下命令：
```bash
# 检查 Conda 是否安装
conda -h

# 使用 environment.yml 文件创建环境
conda env create -f environment.yml

# 激活新创建的环境
# (假设 environment.yml 文件中 name: macos-ocr)
conda activate macos-ocr
```

### 3.运行工具
在激活的环境中，你可以运行主程序：
```
python app_vision.py
```
启动后，请在浏览器中打开终端显示的本地 URL 地址（通常是 http://127.0.0.1:7860）来使用工具。


