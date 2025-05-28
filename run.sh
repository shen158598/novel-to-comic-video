#!/bin/bash
echo "正在启动小说转漫画应用..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "Python未安装，请先安装Python 3.8-3.10"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    echo "正在安装依赖..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动应用
echo "启动应用..."
python app.py
