#!/bin/bash

# 语音安全检测系统 GUI 启动脚本

echo "正在启动语音安全检测系统..."

# 检查是否安装了gradio
if ! python -c "import gradio" 2>/dev/null; then
    echo "正在安装依赖..."
    pip install -r requirements_gui.txt
fi

# 启动GUI
python gui.py

